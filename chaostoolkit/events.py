"""
Live progress of a run as newline-delimited JSON events.

Enabled with `chaos run --events-file PATH`. Every line is one JSON object
with at least a `type` and a `timestamp`. This is meant to be tailed while a
run is in progress; the final verdict belongs to the journal and, for agents,
to the report produced with `--output agent`.
"""

import json
import threading
from datetime import UTC, datetime
from typing import IO, Any

from chaoslib.run import RunEventHandler
from chaoslib.types import Activity, Experiment, Journal, Run

from chaostoolkit import encoder

__all__ = [
    "MAX_OUTPUT_SIZE",
    "EventFile",
    "bounded_output",
    "safe_encoder",
]

# activity outputs larger than this, once serialized, are left to the journal
MAX_OUTPUT_SIZE = 4096


class EventFile(RunEventHandler):
    """Appends the execution's lifecycle as NDJSON events to a file."""

    def __init__(self, path: str) -> None:
        self.path = path
        self._lock = threading.Lock()
        # closed explicitly once the run is over
        self._stream: IO[str] = open(path, "w", encoding="utf-8")  # noqa: SIM115

    def close(self) -> None:
        with self._lock:
            if not self._stream.closed:
                self._stream.close()

    def emit(self, event_type: str, **payload: Any) -> None:
        event = {
            "type": event_type,
            "timestamp": datetime.now(UTC).isoformat(),
            **payload,
        }
        line = json.dumps(event, ensure_ascii=False, default=safe_encoder)
        with self._lock:
            if self._stream.closed:
                return
            self._stream.write(line + "\n")
            self._stream.flush()

    def started(self, experiment: Experiment, journal: Journal) -> None:
        self.emit("run-started", title=experiment.get("title"))

    def finish(self, journal: Journal) -> None:
        self.emit(
            "run-finished",
            status=journal.get("status"),
            deviated=journal.get("deviated", False),
        )

    def interrupted(self, experiment: Experiment, journal: Journal) -> None:
        self.emit("run-interrupted")

    def signal_exit(self) -> None:
        self.emit("run-signal-exit")

    def start_hypothesis_before(self, experiment: Experiment) -> None:
        self.emit("hypothesis-started", phase="before")

    def hypothesis_before_completed(
        self, experiment: Experiment, state: dict[str, Any], journal: Journal
    ) -> None:
        self.emit("hypothesis-completed", phase="before", **_state(state))

    def start_hypothesis_after(self, experiment: Experiment) -> None:
        self.emit("hypothesis-started", phase="after")

    def hypothesis_after_completed(
        self, experiment: Experiment, state: dict[str, Any], journal: Journal
    ) -> None:
        self.emit("hypothesis-completed", phase="after", **_state(state))

    def start_continuous_hypothesis(self, frequency: int) -> None:
        self.emit("hypothesis-started", phase="during", frequency=frequency)

    def continuous_hypothesis_iteration(
        self, iteration_index: int, state: Any
    ) -> None:
        self.emit(
            "hypothesis-completed",
            phase="during",
            iteration=iteration_index,
            **_state(state),
        )

    def start_method(self, experiment: Experiment) -> None:
        self.emit("method-started")

    def method_completed(
        self, experiment: Experiment, state: Any = None
    ) -> None:
        self.emit("method-completed")

    def start_rollbacks(self, experiment: Experiment) -> None:
        self.emit("rollbacks-started")

    def rollbacks_completed(
        self, experiment: Experiment, journal: Journal
    ) -> None:
        self.emit("rollbacks-completed")

    def start_activity(self, activity: Activity) -> None:
        self.emit(
            "activity-started",
            name=activity.get("name"),
            activity_type=activity.get("type"),
            background=bool(activity.get("background", False)),
        )

    def activity_completed(self, activity: Activity, run: Run) -> None:
        payload = {
            "name": activity.get("name"),
            "activity_type": activity.get("type"),
            "status": run.get("status"),
            "duration": run.get("duration"),
            **bounded_output(run.get("output")),
        }
        if run.get("exception"):
            payload["error"] = "".join(run["exception"]).strip()
        self.emit("activity-completed", **payload)


def bounded_output(output: Any) -> dict[str, Any]:
    """
    Return `{"output": ...}` when the output is small enough, otherwise a
    marker telling the reader to look into the journal.
    """
    serialized = json.dumps(output, ensure_ascii=False, default=safe_encoder)
    if len(serialized) > MAX_OUTPUT_SIZE:
        return {"output_truncated": True, "output_size": len(serialized)}
    return {"output": json.loads(serialized)}


def safe_encoder(o: object) -> Any:
    try:
        return encoder(o)
    except TypeError:
        return repr(o)


def _state(state: dict[str, Any] | None) -> dict[str, Any]:
    if not state:
        return {"met": None, "probes": []}
    return {
        "met": state.get("steady_state_met"),
        "probes": [
            {
                "name": (p.get("activity") or {}).get("name"),
                "status": p.get("status"),
                "tolerance_met": p.get("tolerance_met"),
                **bounded_output(p.get("output")),
            }
            for p in state.get("probes") or []
        ],
    }
