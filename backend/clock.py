"""Injectable clock so tests can move time without waiting."""

import time

_now = time.time


def now() -> float:
    return _now()


def set_clock(fn) -> None:
    """Replace the clock (tests). Pass None to restore the real clock."""
    global _now
    _now = fn or time.time
