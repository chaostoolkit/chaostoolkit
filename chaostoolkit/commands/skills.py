import logging
import os
import re
import shutil
import subprocess
from importlib.resources import files
from importlib.resources.abc import Traversable
from pathlib import Path

import click

__all__ = ["skills"]

logger = logging.getLogger("chaostoolkit")

TARGETS = ("claude", "codex", "opencode")
SCOPES = ("workspace", "home")
FAULT_SKILL = "fault-network-injection"
MIN_FAULT_MAJOR = 1


@click.group()
def skills() -> None:
    """Install skills guiding coding agents to run experiments."""


@skills.command(name="list")
def list_skills() -> None:
    """List the bundled skills."""
    for name, skill in sorted(_bundled().items()):
        click.echo(f"{name}\t{_description(skill)}")


@skills.command()
@click.argument("name")
def show(name: str) -> None:
    """Print the SKILL.md of the bundled skill NAME."""
    skill = _bundled().get(name)
    if skill is None:
        raise click.BadParameter(
            f"unknown skill, choose from: {', '.join(sorted(_bundled()))}",
            param_hint="NAME",
        )
    click.echo(skill.joinpath("SKILL.md").read_text(encoding="utf-8"), nl=False)


@skills.command()
@click.option(
    "--target",
    type=click.Choice(TARGETS),
    required=True,
    help="Agent to install the skills for.",
)
@click.option(
    "--scope",
    type=click.Choice(SCOPES),
    help="Install in the current workspace or in your home directory. "
    "Prompted for when omitted in an interactive terminal.",
)
@click.option(
    "--skill",
    "names",
    multiple=True,
    help="Install only this skill. Can be repeated. Defaults to all.",
)
@click.option(
    "--force",
    is_flag=True,
    help="Replace installed skills that differ from the bundled ones.",
)
@click.option(
    "--with-fault/--no-fault",
    default=True,
    show_default=True,
    help="Also install fault's own skill, which describes fault semantics, "
    "with `fault skill install` when fault 1.0 or later is on PATH.",
)
@click.pass_context
def install(
    ctx: click.Context,
    target: str,
    scope: str | None,
    names: tuple[str, ...],
    force: bool,
    with_fault: bool,
) -> None:
    """Install the bundled skills for a coding agent."""
    bundled = _bundled()
    unknown = sorted(set(names) - set(bundled))
    if unknown:
        raise click.BadParameter(
            f"unknown skill {', '.join(unknown)}, choose from: "
            f"{', '.join(sorted(bundled))}",
            param_hint="--skill",
        )
    scope = scope or _prompt_scope()
    root = skills_root(target, scope)

    selected = names or tuple(sorted(bundled))
    conflicts = []
    for name in selected:
        destination = root / name
        state = _compare(bundled[name], destination)
        if state == "same":
            click.echo(f"unchanged {name} at {destination}")
            continue
        if state == "different" and not force:
            conflicts.append(destination)
            continue
        _copy(bundled[name], destination)
        click.echo(f"installed {name} at {destination}")

    if with_fault:
        _install_fault_skill(target, scope, force)

    if conflicts:
        for destination in conflicts:
            click.echo(
                f"{destination} differs from the bundled skill; use --force "
                "to replace it",
                err=True,
            )
        ctx.exit(1)


def skills_root(target: str, scope: str) -> Path:
    """Directory in which the target agent looks for skills."""
    if scope == "workspace":
        base = {
            "codex": Path(".agents"),
            "claude": Path(".claude"),
            "opencode": Path(".opencode"),
        }[target]
        return Path.cwd() / base / "skills"

    home = Path.home()
    if target == "codex":
        return Path(_env("CODEX_HOME") or home / ".codex") / "skills"
    if target == "claude":
        return home / ".claude" / "skills"
    config = _env("XDG_CONFIG_HOME") or _env("APPDATA") or home / ".config"
    return Path(config) / "opencode" / "skills"


###############################################################################
# Internals
###############################################################################
def _bundled() -> dict[str, Traversable]:
    root = files("chaostoolkit").joinpath("skills")
    return {
        entry.name: entry
        for entry in root.iterdir()
        if entry.is_dir() and entry.joinpath("SKILL.md").is_file()
    }


def _description(skill: Traversable) -> str:
    content = skill.joinpath("SKILL.md").read_text(encoding="utf-8")
    m = re.search(r"^description:\s*(.+)$", content, re.MULTILINE)
    return m.group(1).strip() if m else ""


def _files(skill: Traversable, prefix: Path = Path()) -> dict[Path, bytes]:
    found = {}
    for entry in skill.iterdir():
        if entry.name == "__pycache__":
            continue
        path = prefix / entry.name
        if entry.is_dir():
            found.update(_files(entry, path))
        else:
            found[path] = entry.read_bytes()
    return found


def _compare(skill: Traversable, destination: Path) -> str:
    if not destination.exists():
        return "missing"
    installed = {
        p.relative_to(destination): p.read_bytes()
        for p in destination.rglob("*")
        if p.is_file() and "__pycache__" not in p.parts
    }
    return "same" if installed == _files(skill) else "different"


def _copy(skill: Traversable, destination: Path) -> None:
    if destination.exists():
        shutil.rmtree(destination)
    for path, content in _files(skill).items():
        target = destination / path
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(content)


def _prompt_scope() -> str:
    if not (click.get_text_stream("stdin").isatty()):
        raise click.UsageError(
            "installation scope is required without an interactive "
            "terminal; pass --scope workspace or --scope home"
        )
    return click.prompt(
        "Install the skills for this workspace or your home directory?",
        type=click.Choice(SCOPES),
        err=True,
    )


def _install_fault_skill(target: str, scope: str, force: bool) -> None:
    fault = shutil.which("fault")
    if not fault:
        click.echo(
            f"fault was not found on PATH, its {FAULT_SKILL} skill was not "
            "installed: see https://github.com/fault-project/fault/releases",
            err=True,
        )
        return

    version = _fault_version(fault)
    if version is None or version < MIN_FAULT_MAJOR:
        click.echo(
            f"{fault} is not fault 1.0 or later, its {FAULT_SKILL} skill was "
            "not installed: see https://github.com/fault-project/fault/releases",
            err=True,
        )
        return

    command = [fault, "skill", "install", "--target", target, "--scope", scope]
    if force:
        command.append("--force")
    try:
        proc = subprocess.run(
            command, capture_output=True, text=True, timeout=30, check=False
        )
    except (OSError, subprocess.SubprocessError) as x:
        click.echo(f"could not install the {FAULT_SKILL} skill: {x}", err=True)
        return

    output = (proc.stdout + proc.stderr).strip()
    if proc.returncode != 0:
        click.echo(
            f"could not install the {FAULT_SKILL} skill: {output}", err=True
        )
        return
    click.echo(output or f"installed {FAULT_SKILL}")


def _fault_version(fault: str) -> int | None:
    try:
        out = subprocess.run(
            [fault, "--version"],
            capture_output=True,
            text=True,
            timeout=10,
            check=False,
        ).stdout
    except (OSError, subprocess.SubprocessError):
        return None
    m = re.search(r"(\d+)\.\d+\.\d+", out)
    return int(m.group(1)) if m else None


def _env(name: str) -> str | None:
    value = os.environ.get(name)
    return value or None
