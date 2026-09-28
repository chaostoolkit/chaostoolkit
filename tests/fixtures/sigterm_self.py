import os
import signal
import time


def sigterm_self_then_wait(seconds: float = 5.0) -> None:
    """Send SIGTERM to this process while the run is in progress."""
    os.kill(os.getpid(), signal.SIGTERM)
    time.sleep(seconds)
