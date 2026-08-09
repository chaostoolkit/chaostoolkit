import json
import os
import subprocess
import sys
from importlib import import_module
from pathlib import Path
from unittest.mock import MagicMock, Mock

import pytest
from click.testing import CliRunner

import chaostoolkit.commands
from chaostoolkit import __main__
from chaostoolkit.cli import cli
from chaostoolkit.commands import root
from chaostoolkit.runtime import PythonRuntime, runtime_child_invocation

run_command = import_module("chaostoolkit.commands.run")
validate_command = import_module("chaostoolkit.commands.validate")


def _write_experiment(path, runtime=None):
    experiment = {
        "version": "1.0.0",
        "title": "Runtime test",
        "description": "Runtime test",
        "method": [],
    }
    if runtime is not None:
        experiment["runtime"] = runtime
    path.write_text(json.dumps(experiment))


def _runtime_child(status):
    run_child = MagicMock()
    child = run_child.return_value.__enter__.return_value
    child.wait.return_value = status
    return run_child


def _python_runtime(*, isolated=False):
    return {
        "python": {
            "dependencies": ["chaostoolkit-example>=1"],
            "isolated": isolated,
        }
    }


def test_refactor_preserves_public_cli_identity_and_commands():
    assert chaostoolkit.commands.cli is root.cli is cli is __main__.cli
    assert chaostoolkit.commands.__all__ == ["cli"]
    assert {
        "discover",
        "info",
        "init",
        "run",
        "settings",
        "validate",
    }.issubset(cli.commands)
    for command_name in (
        "discover_cli",
        "info_cli",
        "init_cli",
        "run_cli",
        "settings_cli",
        "validate_cli",
    ):
        assert getattr(chaostoolkit.commands, command_name) is getattr(
            root, command_name
        )


def test_plugin_can_import_cli_while_it_is_registered(tmp_path):
    (tmp_path / "compatibility_plugin.py").write_text(
        "from chaostoolkit.commands import cli\n"
        "import click\n"
        "@click.command(name='compatibility-plugin')\n"
        "def command():\n"
        "    assert cli.name == 'cli'\n"
        "    click.echo('plugin-compatible')\n"
    )
    dist_info = tmp_path / "compatibility_plugin-1.0.dist-info"
    dist_info.mkdir()
    (dist_info / "METADATA").write_text(
        "Metadata-Version: 2.1\nName: compatibility-plugin\nVersion: 1.0\n"
    )
    (dist_info / "entry_points.txt").write_text(
        "[chaostoolkit.cli_plugins]\n"
        "compatibility-plugin = compatibility_plugin:command\n"
    )
    env = os.environ.copy()
    env["PYTHONPATH"] = os.pathsep.join(
        filter(None, (os.fspath(tmp_path), env.get("PYTHONPATH")))
    )
    script = (
        "from chaostoolkit.cli import cli; "
        "cli.main(args=['--no-version-check', '--no-log-file', "
        "'compatibility-plugin'])"
    )

    result = subprocess.run(
        [sys.executable, "-c", script],
        check=False,
        capture_output=True,
        env=env,
        text=True,
    )

    assert result.returncode == 0, result.stderr
    assert result.stdout.strip() == "plugin-compatible"


def test_runtime_child_does_not_repeat_version_check(monkeypatch):
    check_newer_version = Mock()
    monkeypatch.setattr(root, "check_newer_version", check_newer_version)

    with runtime_child_invocation():
        result = CliRunner().invoke(
            cli,
            ["--no-log-file", "info", "core"],
        )

    assert result.exit_code == 0
    check_newer_version.assert_not_called()


def test_legacy_runtime_does_not_start_child(tmp_path, monkeypatch):
    experiment = tmp_path / "experiment.json"
    _write_experiment(
        experiment,
        runtime={
            "rollbacks": {"strategy": "always"},
            "hypothesis": {"strategy": "before-method-only"},
        },
    )
    run_child = Mock(side_effect=AssertionError("unexpected runtime child"))
    ensure_valid = Mock()
    monkeypatch.setattr(validate_command, "supervised_runtime", run_child)
    monkeypatch.setattr(
        validate_command,
        "ensure_experiment_is_valid",
        ensure_valid,
    )
    monkeypatch.setattr(validate_command, "notify", Mock())

    result = CliRunner().invoke(
        cli,
        [
            "--no-version-check",
            "--no-log-file",
            "validate",
            os.fspath(experiment),
        ],
    )

    assert result.exit_code == 0
    ensure_valid.assert_called_once()
    run_child.assert_not_called()


@pytest.mark.parametrize("status", [0, 23])
def test_validate_runtime_child_status_stops_validation(
    status, tmp_path, monkeypatch
):
    experiment = tmp_path / "experiment.json"
    _write_experiment(experiment, runtime=_python_runtime(isolated=True))
    run_child = _runtime_child(status)
    notify = Mock()
    ensure_valid = Mock()
    monkeypatch.setattr(validate_command, "supervised_runtime", run_child)
    monkeypatch.setattr(validate_command, "notify", notify)
    monkeypatch.setattr(
        validate_command,
        "ensure_experiment_is_valid",
        ensure_valid,
    )
    arguments = [
        "--no-version-check",
        "--no-log-file",
        "validate",
        os.fspath(experiment),
    ]

    result = CliRunner().invoke(cli, arguments)

    assert result.exit_code == status
    run_child.assert_called_once_with(
        PythonRuntime(("chaostoolkit-example>=1",), isolated=True),
        argv=tuple(arguments),
        invocation_cwd=os.getcwd(),
    )
    notify.assert_not_called()
    ensure_valid.assert_not_called()


@pytest.mark.parametrize("status", [0, 23])
def test_supervised_runtime_status_stops_execution(
    status, tmp_path, monkeypatch
):
    experiment = tmp_path / "experiment.json"
    _write_experiment(experiment, runtime=_python_runtime())
    run_child = _runtime_child(status)
    notify = Mock()
    ensure_valid = Mock()
    execute = Mock()
    monkeypatch.setattr(run_command, "supervised_runtime", run_child)
    monkeypatch.setattr(run_command, "notify", notify)
    monkeypatch.setattr(
        run_command,
        "ensure_experiment_is_valid",
        ensure_valid,
    )
    monkeypatch.setattr(run_command, "run_experiment", execute)
    arguments = [
        "--no-version-check",
        "--no-log-file",
        "run",
        os.fspath(experiment),
    ]

    result = CliRunner().invoke(cli, arguments)

    assert result.exit_code == status
    run_child.assert_called_once_with(
        PythonRuntime(("chaostoolkit-example>=1",)),
        argv=tuple(arguments),
        invocation_cwd=os.getcwd(),
    )
    notify.assert_not_called()
    ensure_valid.assert_not_called()
    execute.assert_not_called()


def test_validate_runtime_child_preserves_argv_and_invocation_directory(
    tmp_path, monkeypatch
):
    run_child = _runtime_child(23)
    notify = Mock()
    ensure_valid = Mock()
    monkeypatch.setattr(validate_command, "supervised_runtime", run_child)
    monkeypatch.setattr(validate_command, "notify", notify)
    monkeypatch.setattr(
        validate_command,
        "ensure_experiment_is_valid",
        ensure_valid,
    )
    runner = CliRunner()
    arguments = [
        "--no-version-check",
        "--no-log-file",
        "--change-dir",
        "work",
        "validate",
        "experiment.json",
    ]

    with runner.isolated_filesystem(temp_dir=tmp_path) as invocation_cwd:
        work = Path(invocation_cwd) / "work"
        work.mkdir()
        _write_experiment(
            work / "experiment.json",
            runtime=_python_runtime(),
        )
        result = runner.invoke(cli, arguments)

    assert result.exit_code == 23
    run_child.assert_called_once_with(
        PythonRuntime(("chaostoolkit-example>=1",)),
        argv=tuple(arguments),
        invocation_cwd=invocation_cwd,
    )
    notify.assert_not_called()
    ensure_valid.assert_not_called()


def test_marked_validate_child_executes_without_recursing(
    tmp_path, monkeypatch
):
    experiment = tmp_path / "experiment.json"
    _write_experiment(experiment, runtime=_python_runtime())
    run_child = Mock(side_effect=AssertionError("recursive runtime child"))
    ensure_valid = Mock()
    monkeypatch.setattr(validate_command, "supervised_runtime", run_child)
    monkeypatch.setattr(validate_command, "notify", Mock())
    monkeypatch.setattr(
        validate_command,
        "ensure_experiment_is_valid",
        ensure_valid,
    )

    with runtime_child_invocation():
        result = CliRunner().invoke(
            cli,
            [
                "--no-version-check",
                "--no-log-file",
                "validate",
                os.fspath(experiment),
            ],
        )

    assert result.exit_code == 0
    run_child.assert_not_called()
    ensure_valid.assert_called_once()


def test_marked_run_child_executes_without_recursing(tmp_path, monkeypatch):
    experiment_path = tmp_path / "experiment.json"
    journal_path = tmp_path / "journal.json"
    _write_experiment(experiment_path, runtime=_python_runtime())
    run_child = Mock(side_effect=AssertionError("recursive runtime child"))
    ensure_valid = Mock()
    journal = {
        "status": "completed",
        "deviated": False,
        "experiment": {},
    }
    execute = Mock(return_value=journal)
    monkeypatch.setattr(run_command, "supervised_runtime", run_child)
    monkeypatch.setattr(run_command, "notify", Mock())
    monkeypatch.setattr(
        run_command,
        "ensure_experiment_is_valid",
        ensure_valid,
    )
    monkeypatch.setattr(run_command, "run_experiment", execute)

    with runtime_child_invocation():
        result = CliRunner().invoke(
            cli,
            [
                "--no-version-check",
                "--no-log-file",
                "run",
                "--journal-path",
                os.fspath(journal_path),
                os.fspath(experiment_path),
            ],
        )

    assert result.exit_code == 0
    run_child.assert_not_called()
    ensure_valid.assert_called_once()
    execute.assert_called_once()
    assert json.loads(journal_path.read_text()) == journal
