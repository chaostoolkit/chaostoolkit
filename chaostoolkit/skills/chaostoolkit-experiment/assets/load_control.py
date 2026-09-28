"""
Keep a load generator running for the lifetime of a Chaos Toolkit
experiment.

Copy this module next to the scenario and make it importable through
PYTHONPATH. Declare it as an experiment-level control, after the fault
control if there is one:

    controls:
      - name: load
        provider:
          type: python
          module: load_control
          arguments:
            url: http://127.0.0.1:8080/checkout
            rate: 50            # requests per second, from real traffic
            connections: 10
            warmup: 20          # seconds before the baseline is measured
            run_dir: /abs/path/runs/<timestamp>

By default the load is generated with `oha`. Pass `command` to use another
tool instead: a list of arguments, run as is. It must keep running until
interrupted with SIGINT.

The load starts before the baseline steady-state hypothesis, so the baseline
is measured under the same load as the rest of the experiment, and stops
after the rollbacks. The generator's output is written to `run_dir` and a
summary is added to the journal under `load`.
"""

import contextlib
import json
import logging
import os
import shutil
import signal
import subprocess
import threading
import time
from collections.abc import Iterator
from typing import Any

from chaoslib.exceptions import InterruptExecution, InvalidControl

__all__ = [
    "after_experiment_control",
    "before_experiment_control",
    "cleanup_control",
    "validate_control",
]

# oha stops at this duration at the latest, the control stops it earlier
MAX_DURATION = "6h"

logger = logging.getLogger("chaostoolkit")

_state: dict[str, Any] = {}


def validate_control(control: dict[str, Any]) -> None:
    arguments = control.get("provider", {}).get("arguments", {})
    command = arguments.get("command")
    if command is None and not arguments.get("url"):
        raise InvalidControl("load control requires `url` or `command`")
    binary = command[0] if command else "oha"
    if "${" not in binary and not shutil.which(binary):
        raise InvalidControl(f"the load generator '{binary}' is not on PATH")


def before_experiment_control(
    context: dict[str, Any],
    run_dir: str,
    url: str | None = None,
    rate: float | None = None,
    connections: int = 10,
    warmup: float = 0,
    command: list[str] | None = None,
    experiment: dict[str, Any] | None = None,
    **kwargs: Any,
) -> None:
    cleanup_control()
    _state.pop("start_error", None)
    try:
        _start(run_dir, url, rate, connections, warmup, command, experiment)
    except InterruptExecution as x:
        _state["start_error"] = str(x)
        raise


def _start(
    run_dir: str,
    url: str | None,
    rate: float | None,
    connections: int,
    warmup: float,
    command: list[str] | None,
    experiment: dict[str, Any] | None,
) -> None:
    dry = (experiment or {}).get("dry")
    if dry:
        # never generate load while only checking the plumbing
        logger.info(
            f"Dry run ({getattr(dry, 'value', dry)}), no load generated"
        )
        return
    if command is None:
        command = [
            "oha",
            "--no-tui",
            "-j",
            "-z",
            MAX_DURATION,
            "-c",
            str(connections),
        ]
        if rate:
            command += ["-q", str(rate)]
        command.append(url)

    binary = shutil.which(command[0])
    if not binary:
        raise InterruptExecution(f"'{command[0]}' is not on PATH")

    os.makedirs(run_dir, exist_ok=True)
    out_path = os.path.join(run_dir, "load-output.json")
    err_path = os.path.join(run_dir, "load-stderr.log")
    out = open(out_path, "w", encoding="utf-8")  # noqa: SIM115
    err = open(err_path, "w", encoding="utf-8")  # noqa: SIM115
    try:
        with _sigint_not_ignored():
            process = subprocess.Popen(
                [binary, *command[1:]],
                stdin=subprocess.DEVNULL,
                stdout=out,
                stderr=err,
            )
    except OSError as x:
        out.close()
        err.close()
        raise InterruptExecution(f"load generator could not start: {x}") from x

    _state.update(
        process=process,
        files=(out, err),
        command=command,
        out_path=out_path,
        err_path=err_path,
        started=time.time(),
    )

    deadline = time.monotonic() + warmup
    while time.monotonic() < deadline:
        if process.poll() is not None:
            cleanup_control()
            raise InterruptExecution(
                f"load generator exited with {process.returncode}, "
                f"see {err_path}"
            )
        time.sleep(0.2)


@contextlib.contextmanager
def _sigint_not_ignored() -> Iterator[None]:
    """
    chaos may run in the background with SIGINT ignored, which a child
    process would inherit, so the generator could not be stopped with it. A
    caught signal is reset to its default on exec, an ignored one is not:
    catch SIGINT while the generator is spawned.
    """
    ignored = (
        threading.current_thread() is threading.main_thread()
        and signal.getsignal(signal.SIGINT) is signal.SIG_IGN
    )
    if ignored:
        signal.signal(signal.SIGINT, signal.default_int_handler)
    try:
        yield
    finally:
        if ignored:
            signal.signal(signal.SIGINT, signal.SIG_IGN)


def after_experiment_control(
    context: dict[str, Any], state: dict[str, Any] | None = None, **kwargs: Any
) -> None:
    summary = _stop()
    if not isinstance(state, dict):
        return
    if summary is not None:
        state["load"] = summary
    if _state.get("start_error") and not state.get("interruption"):
        state["interruption"] = {
            "kind": "control",
            "name": "load",
            "reason": _state["start_error"],
        }


def cleanup_control() -> None:
    _stop()


def _stop(timeout: float = 15.0) -> dict[str, Any] | None:
    process = _state.pop("process", None)
    if process is None:
        return None
    if process.poll() is None:
        try:
            process.send_signal(
                signal.CTRL_C_EVENT if os.name == "nt" else signal.SIGINT
            )
            process.wait(timeout=timeout)
        except subprocess.TimeoutExpired:
            process.kill()
            process.wait()
    for f in _state.pop("files", ()):
        f.close()

    summary = {
        "command": _state.get("command"),
        "duration": round(time.time() - _state.get("started", time.time()), 1),
        "exit_code": process.returncode,
        "output_path": _state.get("out_path"),
        "stderr_path": _state.get("err_path"),
    }
    summary.update(_oha_summary(_state.get("out_path")))
    return summary


def _oha_summary(path: str | None) -> dict[str, Any]:
    try:
        with open(path, encoding="utf-8") as f:
            data = json.load(f)
    except (OSError, TypeError, ValueError):
        return {}
    if not isinstance(data, dict) or "summary" not in data:
        return {}
    s = data["summary"]
    p = data.get("latencyPercentiles") or {}
    return {
        "requests_per_second": s.get("requestsPerSec"),
        "success_rate": s.get("successRate"),
        "latency_s": {k: p.get(k) for k in ("p50", "p95", "p99")},
        "status_codes": data.get("statusCodeDistribution"),
        "errors": data.get("errorDistribution"),
    }
