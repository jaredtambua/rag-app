"""Small in-memory rate limiter (one process, cleared on restart).

Each action (ask, upload) is limited per visitor, per network address and
in total. The totals are the cost ceiling, because visitor IDs are made by
the browser and can be rotated.
"""

import math
import threading
from collections import deque

import clock
import config

BUSY_MESSAGE = "The demo is very busy. Please try again later."


class RateLimited(Exception):
    def __init__(self, message: str, retry_after: int):
        super().__init__(message)
        self.message = message
        self.retry_after = retry_after


def client_ip(request) -> str:
    """The address Render's proxy saw: the LAST X-Forwarded-For entry.

    The first entries are client-made and can be forged, so they are never
    used. Falls back to the socket address.
    """
    forwarded = request.headers.get("x-forwarded-for", "")
    entries = [part.strip() for part in forwarded.split(",") if part.strip()]

    if entries:
        return entries[-1][:64]

    if request.client and request.client.host:
        return request.client.host[:64]

    return "unknown"


def _wait_text(seconds: int) -> str:
    minutes = max(1, math.ceil(seconds / 60))
    return f"{minutes} minute{'s' if minutes != 1 else ''}"


class Limiter:
    def __init__(self):
        self._hits: dict[str, deque] = {}
        self._lock = threading.Lock()

    def reset(self):
        with self._lock:
            self._hits.clear()

    def _recent(self, key: str, now: float) -> deque:
        """Hits for key inside the window, oldest first (old ones dropped)."""
        hits = self._hits.setdefault(key, deque())
        cutoff = now - config.RATE_WINDOW_SECONDS

        while hits and hits[0] <= cutoff:
            hits.popleft()

        return hits

    def check_and_record(self, scopes):
        """Count one use against every scope, or raise RateLimited.

        scopes is a list of (key, limit, message). Nothing is recorded
        unless every scope has room, so a refusal costs nothing.
        """
        now = clock.now()

        with self._lock:
            for key, limit, message in scopes:
                hits = self._recent(key, now)

                if len(hits) >= limit:
                    oldest = hits[0] if hits else now
                    wait = max(1, math.ceil(oldest + config.RATE_WINDOW_SECONDS - now))
                    raise RateLimited(message.format(wait=_wait_text(wait)), wait)

            for key, _, _ in scopes:
                self._hits[key].append(now)

    def prune(self):
        """Drop keys with no hits left in the window (bounds memory)."""
        now = clock.now()

        with self._lock:
            for key in list(self._hits):
                if not self._recent(key, now):
                    del self._hits[key]


limiter = Limiter()


def check_ask(visitor_id: str, ip: str):
    limiter.check_and_record(
        [
            (
                f"ask:visitor:{visitor_id}",
                config.ASK_LIMIT_PER_VISITOR,
                f"You have reached the limit of {config.ASK_LIMIT_PER_VISITOR} "
                "questions per hour. Please try again in {wait}.",
            ),
            (f"ask:ip:{ip}", config.ASK_LIMIT_PER_IP, BUSY_MESSAGE),
            ("ask:total", config.ASK_LIMIT_TOTAL, BUSY_MESSAGE),
        ]
    )


def check_upload(visitor_id: str, ip: str):
    limiter.check_and_record(
        [
            (
                f"upload:visitor:{visitor_id}",
                config.UPLOAD_LIMIT_PER_VISITOR,
                f"You have reached the limit of {config.UPLOAD_LIMIT_PER_VISITOR} "
                "uploads per hour. Please try again in {wait}.",
            ),
            (f"upload:ip:{ip}", config.UPLOAD_LIMIT_PER_IP, BUSY_MESSAGE),
            ("upload:total", config.UPLOAD_LIMIT_TOTAL, BUSY_MESSAGE),
        ]
    )
