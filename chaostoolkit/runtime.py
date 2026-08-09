import logging
import os
import shutil
import subprocess
import sys
from collections.abc import Generator, Mapping, Sequence
from contextlib import contextmanager
from contextvars import ContextVar
from dataclasses import dataclass
from typing import Any

from chaostoolkit import __version__

__all__ = [
    "RUNTIME_ARGUMENTS_META_KEY",
    "RUNTIME_INVOCATION_CWD_META_KEY",
    "PythonRuntime",
    "PythonRuntimeError",
    "get_python_runtime_info",
    "in_runtime_child",
    "supervised_runtime",
]

logger = logging.getLogger("chaostoolkit")

RUNTIME_ARGUMENTS_META_KEY = "chaostoolkit.runtime.arguments"
RUNTIME_INVOCATION_CWD_META_KEY = "chaostoolkit.runtime.invocation_cwd"

runtime_child_state = ContextVar("chaostoolkit_in_runtime_child", default=False)


class PythonRuntimeError(Exception):
    pass


@dataclass(frozen=True)
class PythonRuntime:
    dependencies: tuple[str, ...]
    isolated: bool = False
    version: str | None = None


def get_python_runtime_info(
    experiment: Mapping[str, Any],
) -> PythonRuntime | None:
    if not isinstance(experiment, Mapping):
        return None

    runtime = experiment.get("runtime")
    if not isinstance(runtime, Mapping):
        return None

    python = runtime.get("python")
    if not isinstance(python, Mapping):
        return None

    dependencies = python.get("dependencies")
    if dependencies is None:
        dependencies = []
    if not isinstance(dependencies, list):
        raise PythonRuntimeError("runtime.python.dependencies must be a list")

    normalized = []
    for dependency in dependencies:
        if not isinstance(dependency, str) or not dependency.strip():
            raise PythonRuntimeError(
                "runtime.python.dependencies must contain package names"
            )
        normalized.append(dependency.strip())

    isolated = python.get("isolated", False)
    if not isinstance(isolated, bool):
        raise PythonRuntimeError("runtime.python.isolated must be a boolean")

    version = python.get("version")
    if version is not None:
        if not isinstance(version, str) or not version.strip():
            raise PythonRuntimeError(
                "runtime.python.version must be a Python version"
            )
        version = version.strip()

    if not normalized and version is None:
        return None

    return PythonRuntime(
        tuple(normalized),
        isolated=isolated or version is not None,
        version=version,
    )


def in_runtime_child() -> bool:
    return runtime_child_state.get()


@contextmanager
def runtime_child_invocation() -> Generator[None]:
    marker = runtime_child_state.set(True)
    try:
        yield
    finally:
        runtime_child_state.reset(marker)


@contextmanager
def supervised_runtime(
    runtime: PythonRuntime,
    argv: Sequence[str],
    invocation_cwd: str | os.PathLike[str],
) -> Generator[subprocess.Popen]:
    command = build_runtime_command(runtime, argv)
    logger.info("Preparing experiment dependencies with uv")

    try:
        process = subprocess.Popen(command, cwd=invocation_cwd)
    except OSError as exc:
        raise PythonRuntimeError(f"Failed to start uv: {exc}") from exc

    try:
        yield process
    finally:
        if process.poll() is None:
            process.terminate()
        try:
            process.wait(timeout=5)
        except subprocess.TimeoutExpired:
            process.kill()
            process.wait()


def build_runtime_command(
    runtime: PythonRuntime, argv: Sequence[str]
) -> list[str]:
    uv = shutil.which("uv")
    if uv is None:
        raise PythonRuntimeError("uv was not found on PATH")

    command = [os.path.abspath(uv), "run", "--no-project"]
    isolated = runtime.isolated or runtime.version is not None
    if isolated:
        logger.info("Running in an isolated environment")
        command.append("--isolated")
    command.extend(("--python", runtime.version or sys.executable))

    if isolated:
        command.extend(("--with", f"chaostoolkit=={__version__}"))

    for dependency in runtime.dependencies:
        command.extend(("--with", dependency))

    command.extend(
        (
            "--",
            "python",
            "-m",
            "chaostoolkit.runner",
            "--",
            *argv,
        )
    )
    return command
