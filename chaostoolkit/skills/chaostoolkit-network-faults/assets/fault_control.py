"""
Drive fault's engine from a Chaos Toolkit experiment.

Uses `faultlib`, fault's Python binding, which requires Python 3.14+. Declare
it in the scenario:

    runtime:
      python:
        version: "3.14"
        dependencies: ["faultlib>=1.0"]

Copy this module next to the scenario, make it importable through PYTHONPATH
and declare it once as an experiment-level control:

    controls:
      - name: fault
        provider:
          type: python
          module: fault_control
          arguments:
            run_dir: /abs/path/runs/<timestamp>
            proxies:
              - name: database
                protocol: tcp
                listen: 127.0.0.1:15432
                upstream: database:5432

The control binds the proxies, healthy, before the baseline steady-state
hypothesis and shuts them down after the rollbacks. The method changes fault
chains when it decides to, with the activities of this module:

    set_faults(faults)            replace the chains of the named proxies
    clear_faults(proxies=None)    make proxies healthy again, all by default
    ensure_traffic_impacted(...)  fail unless traffic crossed a fault
    fault_status()                live transport counters

Fault specifications use the same shapes as fault's run schema. Every change
is timestamped. Per-stream and per-exchange records are written to
`run_dir/fault-records.ndjson` and a summary is added to the journal under
`fault`.
"""

import asyncio
import dataclasses
import json
import logging
import os
import threading
from datetime import UTC, datetime
from typing import Any

from chaoslib.exceptions import (
    ActivityFailed,
    InterruptExecution,
    InvalidControl,
)

__all__ = [
    "after_experiment_control",
    "before_experiment_control",
    "cleanup_control",
    "clear_faults",
    "ensure_traffic_impacted",
    "fault_status",
    "set_faults",
    "validate_control",
]

logger = logging.getLogger("chaostoolkit")

CALL_TIMEOUT = 30.0


class _Bridge:
    def __init__(self) -> None:
        self.lock = threading.Lock()
        self.loop: asyncio.AbstractEventLoop | None = None
        self.thread: threading.Thread | None = None
        self.engine: Any = None
        self.recorder: Any = None
        self.proxies: list[str] = []
        self.endpoints: dict[str, list[str]] = {}
        self.changes: list[dict[str, Any]] = []
        self.records_path: str | None = None
        self.changes_path: str | None = None
        self.records: dict[str, int] = {}
        self.start_error: str | None = None

    def call(self, coro: Any, timeout: float = CALL_TIMEOUT) -> Any:
        return asyncio.run_coroutine_threadsafe(coro, self.loop).result(timeout)


_bridge = _Bridge()


###############################################################################
# Control
###############################################################################
def validate_control(control: dict[str, Any]) -> None:
    arguments = control.get("provider", {}).get("arguments", {})
    proxies = arguments.get("proxies")
    if not proxies or not isinstance(proxies, list):
        raise InvalidControl("fault control requires a list of `proxies`")
    for proxy in proxies:
        missing = {"name", "protocol", "listen", "upstream"} - set(proxy)
        if missing:
            raise InvalidControl(
                f"fault proxy {proxy.get('name', proxy)} misses "
                f"{', '.join(sorted(missing))}"
            )
    if not arguments.get("run_dir"):
        raise InvalidControl("fault control requires a `run_dir`")
    try:
        import faultlib  # noqa: F401
    except ImportError as x:
        raise InvalidControl(
            "faultlib is not importable: declare runtime.python.version "
            "'3.14' and 'faultlib>=1.0' in runtime.python.dependencies"
        ) from x


def before_experiment_control(
    context: dict[str, Any],
    proxies: list[dict[str, Any]],
    run_dir: str,
    experiment: dict[str, Any] | None = None,
    **kwargs: Any,
) -> None:
    dry = getattr((experiment or {}).get("dry"), "value", None)
    if dry == "activities":
        # no activity will use the proxies
        return

    try:
        from faultlib import Engine
    except ImportError as x:
        _bridge.start_error = (
            "faultlib is not importable, it requires Python 3.14+"
        )
        raise InterruptExecution(_bridge.start_error) from x

    _shutdown()
    _bridge.start_error = None
    os.makedirs(run_dir, exist_ok=True)
    b = _bridge
    b.records_path = os.path.join(run_dir, "fault-records.ndjson")
    b.changes_path = os.path.join(run_dir, "fault-changes.ndjson")
    b.proxies = [p["name"] for p in proxies]
    b.changes = []
    b.records = {}
    b.loop = asyncio.new_event_loop()
    b.thread = threading.Thread(target=b.loop.run_forever, daemon=True)
    b.thread.start()

    run = {
        "schema_version": 1,
        "name": (experiment or {}).get("title") or "chaostoolkit",
        "proxies": proxies,
        "phases": [{"name": "healthy", "proxies": []}],
    }
    try:

        async def start() -> Any:
            engine = Engine(run)
            endpoints = await engine.start()
            return engine, endpoints

        b.engine, endpoints = b.call(start())
    except Exception as x:
        _shutdown()
        b.start_error = f"fault could not start: {x}"
        raise InterruptExecution(b.start_error) from x

    b.endpoints = {"tcp": list(endpoints.tcp), "udp": list(endpoints.udp)}
    b.recorder = asyncio.run_coroutine_threadsafe(_record(b.engine), b.loop)
    logger.info(f"fault proxies listening on {b.endpoints}")


def after_experiment_control(
    context: dict[str, Any], state: dict[str, Any] | None = None, **kwargs: Any
) -> None:
    summary = _shutdown()
    if not isinstance(state, dict):
        return
    if summary is not None:
        state["fault"] = summary
    if _bridge.start_error and not state.get("interruption"):
        state["interruption"] = {
            "kind": "control",
            "name": "fault",
            "reason": _bridge.start_error,
        }


def cleanup_control() -> None:
    _shutdown()


###############################################################################
# Activities
###############################################################################
def set_faults(faults: dict[str, list[dict[str, Any]]]) -> dict[str, Any]:
    """
    Replace the fault chain of every named proxy, in that order. Proxies not
    named keep their current chain. An empty list makes a proxy healthy.
    """
    engine = _engine()
    unknown = sorted(set(faults) - set(_bridge.proxies))
    if unknown:
        raise ActivityFailed(f"unknown fault proxies: {', '.join(unknown)}")
    for proxy, chain in faults.items():
        try:
            _bridge.call(engine.set_faults(proxy, chain))
        except Exception as x:
            raise ActivityFailed(
                f"fault rejected the chain for '{proxy}': {x}"
            ) from x
    return _record_change(faults)


def clear_faults(proxies: list[str] | None = None) -> dict[str, Any]:
    """
    Make the given proxies, or all of them, healthy. Safe to call as a
    rollback, including when fault is not running.
    """
    if _bridge.engine is None:
        return {"applied_at": _now(), "faults": {}, "running": False}
    names = proxies or _bridge.proxies
    return set_faults({name: [] for name in names})


def fault_status() -> dict[str, Any]:
    """Live transport counters of the fault engine."""
    status = _bridge.call(_engine().status())
    return {
        **_to_json(status),
        "records_by_proxy": dict(_bridge.records),
    }


def ensure_traffic_impacted(minimum: int = 1) -> dict[str, Any]:
    """
    Fail unless at least `minimum` TCP streams or UDP exchanges were impacted
    by a fault since the proxies started. A failure means the application
    does not route through fault, so the perturbation never happened.
    """
    status = fault_status()
    impacted = status["tcp"]["impacted"] + status["udp"]["impacted"]
    if impacted < minimum:
        raise ActivityFailed(
            f"only {impacted} streams or exchanges were impacted by a fault, "
            f"expected at least {minimum}: is the application routed "
            f"through {_bridge.endpoints}?"
        )
    return status


###############################################################################
# Internals
###############################################################################
def _engine() -> Any:
    if _bridge.engine is None:
        raise ActivityFailed("fault is not running, is the control declared?")
    return _bridge.engine


def _record_change(faults: dict[str, list[dict[str, Any]]]) -> dict[str, Any]:
    change = {"applied_at": _now(), "faults": faults}
    with _bridge.lock:
        _bridge.changes.append(change)
        with open(_bridge.changes_path, "a", encoding="utf-8") as f:
            f.write(json.dumps(change) + "\n")
    return change


async def _record(engine: Any) -> None:
    # small appends on the bridge's own loop thread, never on the hot path
    with open(_bridge.records_path, "w", encoding="utf-8") as f:  # noqa: ASYNC230
        while True:
            record = await engine.next_record()
            if record is None:
                return
            f.write(json.dumps(_to_json(record)) + "\n")
            f.flush()
            proxy = getattr(record, "proxy", None)
            with _bridge.lock:
                _bridge.records[proxy] = _bridge.records.get(proxy, 0) + 1


def _shutdown() -> dict[str, Any] | None:
    b = _bridge
    if b.loop is None:
        return None

    summary = None
    if b.engine is not None:
        try:
            final = b.call(b.engine.shutdown())
            summary = {
                "endpoints": b.endpoints,
                "changes": b.changes,
                "status": _to_json(final.status),
                "records_by_proxy": dict(b.records),
                "records_path": b.records_path,
                "changes_path": b.changes_path,
            }
        except Exception:
            logger.debug(
                "fault engine did not shut down cleanly", exc_info=True
            )
    if b.recorder is not None:
        try:
            b.recorder.result(timeout=5)
        except Exception:
            logger.debug(
                "fault record stream did not end cleanly", exc_info=True
            )
            b.recorder.cancel()

    b.loop.call_soon_threadsafe(b.loop.stop)
    if b.thread:
        b.thread.join(timeout=5)
    b.loop.close()
    b.loop = b.thread = b.engine = b.recorder = None
    return summary


def _to_json(value: Any) -> Any:
    if dataclasses.is_dataclass(value):
        value = dataclasses.asdict(value)
    return json.loads(json.dumps(value, default=str))


def _now() -> str:
    return datetime.now(UTC).isoformat()
