from chaoslib.exceptions import ActivityFailed


def kaboom() -> None:
    raise ActivityFailed()
