import importlib
import sys
from unittest.mock import Mock

import pytest

from chaostoolkit import runtime
from chaostoolkit.runtime import (
    PythonRuntime,
    PythonRuntimeError,
    get_python_runtime_info,
    in_runtime_child,
    runtime_child_invocation,
    supervised_runtime,
)


@pytest.mark.parametrize(
    "experiment",
    [
        {},
        {"runtime": None},
        {"runtime": {}},
        {"runtime": {"python": None}},
        {"runtime": {"python": {}}},
        {"runtime": {"python": {"dependencies": []}}},
        {"runtime": {"rollbacks": {"strategy": "always"}}},
    ],
)
def test_experiment_without_dependencies_has_no_python_runtime(experiment):
    assert get_python_runtime_info(experiment) is None


def test_python_runtime_is_read_from_the_experiment():
    experiment = {
        "runtime": {
            "python": {
                "version": " 3.14 ",
                "dependencies": ["alpha>=1", " beta==2 "],
            }
        }
    }

    assert get_python_runtime_info(experiment) == PythonRuntime(
        ("alpha>=1", "beta==2"), isolated=True, version="3.14"
    )


def test_python_version_is_a_runtime_without_dependencies():
    experiment = {"runtime": {"python": {"version": "3.14"}}}

    assert get_python_runtime_info(experiment) == PythonRuntime(
        (), isolated=True, version="3.14"
    )


@pytest.mark.parametrize(
    "python_runtime",
    [
        {"dependencies": "httpx"},
        {"dependencies": [None]},
        {"dependencies": [""]},
        {"dependencies": ["httpx"], "isolated": "true"},
        {"dependencies": ["httpx"], "version": ""},
        {"dependencies": ["httpx"], "version": 3.14},
    ],
)
def test_invalid_python_runtime_is_rejected(python_runtime):
    with pytest.raises(PythonRuntimeError):
        get_python_runtime_info({"runtime": {"python": python_runtime}})


def test_runtime_child_command_layers_dependencies(monkeypatch):
    monkeypatch.setattr(runtime.shutil, "which", lambda _: "/opt/uv")
    monkeypatch.setattr(runtime.sys, "executable", "/venv/python")
    argv = ["--verbose", "run", "experiment with spaces.json"]

    command = runtime.build_runtime_command(
        PythonRuntime(("alpha>=1", "beta==2")), argv
    )

    assert command == [
        "/opt/uv",
        "run",
        "--no-project",
        "--python",
        "/venv/python",
        "--with",
        "alpha>=1",
        "--with",
        "beta==2",
        "--",
        "python",
        "-m",
        "chaostoolkit.runner",
        "--",
        *argv,
    ]


def test_isolated_runtime_includes_chaostoolkit(monkeypatch):
    monkeypatch.setattr(runtime.shutil, "which", lambda _: "/opt/uv")
    monkeypatch.setattr(runtime, "__version__", "1.20.0")

    command = runtime.build_runtime_command(
        PythonRuntime(("provider",), isolated=True),
        ["validate", "experiment.json"],
    )

    assert command[:4] == ["/opt/uv", "run", "--no-project", "--isolated"]
    assert ["--with", "chaostoolkit==1.20.0"] == command[6:8]


def test_python_version_selects_python_and_forces_isolation(monkeypatch):
    monkeypatch.setattr(runtime.shutil, "which", lambda _: "/opt/uv")
    monkeypatch.setattr(runtime, "__version__", "1.20.0")

    command = runtime.build_runtime_command(
        PythonRuntime(("provider",), version="3.14"),
        ["validate", "experiment.json"],
    )

    assert command[:7] == [
        "/opt/uv",
        "run",
        "--no-project",
        "--isolated",
        "--python",
        "3.14",
        "--with",
    ]


def test_missing_uv_is_reported(monkeypatch):
    monkeypatch.setattr(runtime.shutil, "which", lambda _: None)

    with pytest.raises(PythonRuntimeError, match="uv was not found"):
        runtime.build_runtime_command(PythonRuntime(("provider",)), [])


def test_runtime_child_is_terminated_when_the_context_fails(
    tmp_path, monkeypatch
):
    command = [sys.executable, "-c", "import time; time.sleep(30)"]
    monkeypatch.setattr(runtime, "build_runtime_command", lambda *_: command)
    process = None

    with (
        pytest.raises(RuntimeError, match="stop"),
        supervised_runtime(PythonRuntime(("provider",)), [], tmp_path) as child,
    ):
        process = child
        raise RuntimeError("stop")

    assert process is not None
    assert process.poll() is not None


def test_runtime_child_marker_is_scoped():
    assert in_runtime_child() is False
    with runtime_child_invocation():
        assert in_runtime_child() is True
    assert in_runtime_child() is False


def test_internal_child_marks_the_cli_invocation(monkeypatch):
    child_module = importlib.import_module("chaostoolkit.runner")
    cli_module = importlib.import_module("chaostoolkit.cli")
    cli = Mock()
    cli.main.side_effect = lambda **_: in_runtime_child()
    monkeypatch.setattr(cli_module, "cli", cli)

    assert child_module.main(["--", "validate", "experiment.json"]) is True
    assert in_runtime_child() is False


def test_internal_child_rejects_direct_use(capsys):
    child_module = importlib.import_module("chaostoolkit.runner")

    assert child_module.main(["validate", "experiment.json"]) == 2
    assert "internal command" in capsys.readouterr().err
