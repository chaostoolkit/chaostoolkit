"""
Record which signal interrupted a run.

chaoslib installs its own SIGTERM handler when the run starts. This event
handler wraps it, and Python's SIGINT handler, to note the signal before
delegating to them unchanged. When the run ends interrupted, the journal
records it under `interruption`.
"""

import signal
import threading
from typing import Any

from chaoslib.run import RunEventHandler
from chaoslib.types import Experiment, Journal

__all__ = ["SignalRecorder"]

RECORDED_SIGNALS = tuple(
    getattr(signal, name)
    for name in ("SIGTERM", "SIGINT")
    if hasattr(signal, name)
)


class SignalRecorder(RunEventHandler):
    def __init__(self) -> None:
        self.received: str | None = None
        self._previous: dict[int, Any] = {}

    def started(self, experiment: Experiment, journal: Journal) -> None:
        if threading.current_thread() is not threading.main_thread():
            return
        for signum in RECORDED_SIGNALS:
            previous = signal.getsignal(signum)
            if not callable(previous):
                # ignored or default: nothing to delegate to, leave as is
                continue
            self._previous[signum] = previous
            signal.signal(signum, self._recorder(previous))

    def finish(self, journal: Journal) -> None:
        for signum, previous in self._previous.items():
            # chaoslib restores SIGTERM itself when the run ends, only put
            # back what is still ours
            if getattr(signal.getsignal(signum), "_ctk_recorder", False):
                signal.signal(signum, previous)
        self._previous = {}

        if (
            self.received
            and journal.get("status") == "interrupted"
            and not journal.get("interruption")
        ):
            journal["interruption"] = {
                "kind": "signal",
                "name": self.received,
                "reason": f"received {self.received}",
            }

    def _recorder(self, previous: Any) -> Any:
        def record(signum: int, frame: Any) -> Any:
            if self.received is None:
                self.received = signal.Signals(signum).name
            return previous(signum, frame)

        record._ctk_recorder = True
        return record
