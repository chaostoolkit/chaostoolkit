import re
import subprocess
from importlib import import_module
from pathlib import Path
from unittest.mock import MagicMock

import pytest
from click.testing import CliRunner

from chaostoolkit.cli import cli

skills_command = import_module("chaostoolkit.commands.skills")

BASE_ARGS = ["--no-version-check", "--no-log-file", "skills"]
SKILLS = ["chaostoolkit-experiment", "chaostoolkit-network-faults"]


def _invoke(*args):
    return CliRunner().invoke(cli, [*BASE_ARGS, *args])


@pytest.fixture
def no_fault(monkeypatch):
    monkeypatch.setattr(skills_command.shutil, "which", lambda _: None)


@pytest.fixture
def workspace(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    return tmp_path


def test_list():
    result = _invoke("list")
    assert result.exit_code == 0
    names = [line.split("\t")[0] for line in result.stdout.splitlines()]
    assert names == SKILLS
    assert all("\t" in line for line in result.stdout.splitlines())


def test_show():
    result = _invoke("show", "chaostoolkit-experiment")
    assert result.exit_code == 0
    assert result.stdout.startswith("---\nname: chaostoolkit-experiment\n")


def test_show_unknown():
    result = _invoke("show", "nope")
    assert result.exit_code == 2


def test_bundled_skills_are_well_formed():
    for name, skill in skills_command._bundled().items():
        content = skill.joinpath("SKILL.md").read_text(encoding="utf-8")
        assert content.startswith(f"---\nname: {name}\ndescription: ")
        for link in re.findall(r"\]\(((?:assets|references)/[^)]+)\)", content):
            assert skill.joinpath(link).is_file(), f"{name}: {link}"


def test_bundled_yaml_assets_parse():
    import yaml

    for name, skill in skills_command._bundled().items():
        assets = skill.joinpath("assets")
        if not assets.is_dir():
            continue
        for entry in assets.iterdir():
            if entry.name.endswith((".yaml", ".yml")):
                assert isinstance(yaml.safe_load(entry.read_text()), dict), (
                    f"{name}/{entry.name}"
                )


@pytest.mark.parametrize(
    "target,base",
    [("claude", ".claude"), ("codex", ".agents"), ("opencode", ".opencode")],
)
def test_install_workspace(workspace, no_fault, target, base):
    result = _invoke("install", "--target", target, "--scope", "workspace")

    assert result.exit_code == 0, result.output
    root = workspace / base / "skills"
    assert sorted(p.name for p in root.iterdir()) == SKILLS
    assert (root / "chaostoolkit-experiment" / "SKILL.md").is_file()
    assert (
        root / "chaostoolkit-experiment" / "references" / "agent-report.md"
    ).is_file()
    assert (
        root / "chaostoolkit-network-faults" / "assets" / "fault_control.py"
    ).is_file()
    assert "fault was not found on PATH" in result.stderr


def test_install_is_idempotent_and_protects_changes(workspace, no_fault):
    args = ["install", "--target", "claude", "--scope", "workspace"]
    assert _invoke(*args).exit_code == 0

    result = _invoke(*args)
    assert result.exit_code == 0
    assert result.stdout.count("unchanged") == 2

    skill_md = workspace / ".claude/skills/chaostoolkit-experiment/SKILL.md"
    original = skill_md.read_text()
    skill_md.write_text("edited")
    extra = skill_md.parent / "notes.md"
    extra.write_text("mine")

    result = _invoke(*args)
    assert result.exit_code == 1
    assert "use --force" in result.stderr
    assert skill_md.read_text() == "edited"

    result = _invoke(*args, "--force")
    assert result.exit_code == 0
    assert skill_md.read_text() == original
    assert not extra.exists()


def test_install_single_skill(workspace, no_fault):
    result = _invoke(
        "install",
        "--target",
        "claude",
        "--scope",
        "workspace",
        "--skill",
        "chaostoolkit-experiment",
    )
    assert result.exit_code == 0
    root = workspace / ".claude" / "skills"
    assert [p.name for p in root.iterdir()] == ["chaostoolkit-experiment"]


def test_install_unknown_skill(workspace, no_fault):
    result = _invoke(
        "install", "--target", "claude", "--scope", "workspace", "--skill", "x"
    )
    assert result.exit_code == 2


def test_install_requires_scope_without_terminal(workspace, no_fault):
    result = _invoke("install", "--target", "claude")
    assert result.exit_code == 2
    assert "--scope workspace or --scope home" in result.output


@pytest.mark.parametrize(
    "target,env,expected",
    [
        ("claude", {}, "home/.claude/skills"),
        ("codex", {}, "home/.codex/skills"),
        ("codex", {"CODEX_HOME": "codex"}, "codex/skills"),
        ("opencode", {}, "home/.config/opencode/skills"),
        ("opencode", {"XDG_CONFIG_HOME": "xdg"}, "xdg/opencode/skills"),
    ],
)
def test_home_roots(tmp_path, monkeypatch, target, env, expected):
    monkeypatch.setenv("HOME", str(tmp_path / "home"))
    for name in ("CODEX_HOME", "XDG_CONFIG_HOME", "APPDATA"):
        monkeypatch.delenv(name, raising=False)
    for name, value in env.items():
        monkeypatch.setenv(name, str(tmp_path / value))

    assert skills_command.skills_root(target, "home") == tmp_path / expected


def _fault(monkeypatch, version, install_returncode=0):
    monkeypatch.setattr(
        skills_command.shutil, "which", lambda _: "/usr/bin/fault"
    )
    calls = []

    def run(command, **kwargs):
        calls.append(command)
        if command[1] == "--version":
            return subprocess.CompletedProcess(command, 0, version, "")
        return subprocess.CompletedProcess(
            command, install_returncode, "installed fault skill", "boom"
        )

    monkeypatch.setattr(
        skills_command.subprocess, "run", MagicMock(side_effect=run)
    )
    return calls


def test_install_delegates_to_fault(workspace, monkeypatch):
    calls = _fault(monkeypatch, "fault 1.0.0\n")

    result = _invoke(
        "install", "--target", "opencode", "--scope", "home", "--force"
    )

    assert result.exit_code == 0
    assert calls[-1] == [
        "/usr/bin/fault",
        "skill",
        "install",
        "--target",
        "opencode",
        "--scope",
        "home",
        "--force",
    ]
    assert "installed fault skill" in result.stdout


def test_install_skips_old_fault(workspace, monkeypatch):
    calls = _fault(monkeypatch, "fault-cli 0.17.1\n")

    result = _invoke("install", "--target", "claude", "--scope", "workspace")

    assert result.exit_code == 0
    assert len(calls) == 1
    assert "is not fault 1.0 or later" in result.stderr


def test_install_reports_fault_failure(workspace, monkeypatch):
    _fault(monkeypatch, "fault 1.0.0\n", install_returncode=1)

    result = _invoke("install", "--target", "claude", "--scope", "workspace")

    assert result.exit_code == 0
    assert "could not install the fault-network-injection skill" in (
        result.stderr
    )


def test_no_fault_flag(workspace, monkeypatch):
    calls = _fault(monkeypatch, "fault 1.0.0\n")

    result = _invoke(
        "install", "--target", "claude", "--scope", "workspace", "--no-fault"
    )

    assert result.exit_code == 0
    assert calls == []
    assert Path(workspace / ".claude/skills").is_dir()
