import logging
import os
import shutil
import signal
import subprocess
import sys
import threading
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

# signals relayed to the runtime child so it interrupts the experiment
# gracefully, plays the rollbacks and still reports
FORWARDED_SIGNALS = tuple(
    getattr(signal, name)
    for name in ("SIGINT", "SIGTERM")
    if hasattr(signal, name)
)

# time left to the runtime child to finish its rollbacks when the supervisor
# must stop it
ROLLBACK_GRACE_PERIOD = 60


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
    capture_stdout: bool = False,
) -> Generator[subprocess.Popen]:
    command = build_runtime_command(runtime, argv)
    logger.info("Preparing experiment dependencies with uv")

    try:
        # in its own session, a terminal Ctrl-C reaches the supervisor only,
        # which relays it once: a second signal would cut the rollbacks short
        process = subprocess.Popen(
            command,
            cwd=invocation_cwd,
            stdout=subprocess.PIPE if capture_stdout else None,
            text=True if capture_stdout else None,
            start_new_session=os.name == "posix",
        )
    except OSError as exc:
        raise PythonRuntimeError(f"Failed to start uv: {exc}") from exc

    previous = _forward_signals(process)
    try:
        yield process
    finally:
        _restore_signals(previous)
        if process.poll() is None:
            process.terminate()
        try:
            process.wait(timeout=ROLLBACK_GRACE_PERIOD)
        except subprocess.TimeoutExpired:
            process.kill()
            process.wait()


def _forward_signals(process: subprocess.Popen) -> dict[int, Any]:
    """
    Relay interruption signals to the runtime child instead of letting them
    stop the supervisor, which keeps waiting for the child to finish.
    """
    if threading.current_thread() is not threading.main_thread():
        return {}

    def forward(signum: int, frame: Any) -> None:
        if process.poll() is None:
            logger.warning(
                f"Relaying {signal.Signals(signum).name} to the experiment "
                "runtime, waiting for it to finish"
            )
            process.send_signal(signum)

    previous = {}
    for signum in FORWARDED_SIGNALS:
        previous[signum] = signal.signal(signum, forward)
    return previous


def _restore_signals(previous: dict[int, Any]) -> None:
    for signum, handler in previous.items():
        signal.signal(signum, handler)


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
