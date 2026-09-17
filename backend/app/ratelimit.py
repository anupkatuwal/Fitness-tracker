"""Per-user rate limiting for endpoints that call out to OpenFoodFacts.

Why this exists: `/macros/search` and `/macros/barcode` turn one inbound
request into one outbound request to a free public API. Without a limit, a
single logged-in user can drive unlimited traffic at OpenFoodFacts in our
name — a good way to get the server's IP blocked by them.

Scope and honest limitation
---------------------------
The window is held **in this process's memory**. With several Uvicorn workers
each worker keeps its own counter, so the effective limit is
``workers x limit``. That is a real weakening, not a rounding error: it still
bounds the traffic, but it is not an exact global limit. For an exact limit
across workers or hosts, move the counter into Redis and keep this interface.

State is bounded: callers idle for longer than the window are evicted on the
next sweep, so the dictionary cannot grow without limit.
"""

from __future__ import annotations

import threading
import time
from collections import defaultdict, deque

from fastapi import HTTPException, status

from app.config import settings
from app.deps import CurrentUser

# Sweep idle callers at most this often, so eviction is not O(n) per request.
_CLEANUP_INTERVAL_SECONDS = 300


class SlidingWindowRateLimiter:
    """Allows ``limit`` requests per ``window_seconds`` per key."""

    def __init__(self, limit: int, window_seconds: int) -> None:
        if limit < 1:
            raise ValueError("limit must be at least 1")
        if window_seconds < 1:
            raise ValueError("window_seconds must be at least 1")
        self.limit = limit
        self.window_seconds = window_seconds
        self._hits: dict[str, deque[float]] = defaultdict(deque)
        self._lock = threading.Lock()
        self._last_cleanup = time.monotonic()

    def _evict_idle(self, now: float) -> None:
        """Drop keys with no hits inside the window. Caller holds the lock."""
        if now - self._last_cleanup < _CLEANUP_INTERVAL_SECONDS:
            return
        cutoff = now - self.window_seconds
        stale = [key for key, hits in self._hits.items() if not hits or hits[-1] <= cutoff]
        for key in stale:
            del self._hits[key]
        self._last_cleanup = now

    def check(self, key: str) -> tuple[bool, int]:
        """Record a hit for ``key``.

        Returns ``(allowed, retry_after_seconds)``. ``retry_after_seconds`` is
        meaningful only when the request was refused.
        """
        now = time.monotonic()
        cutoff = now - self.window_seconds

        with self._lock:
            self._evict_idle(now)
            hits = self._hits[key]
            while hits and hits[0] <= cutoff:
                hits.popleft()

            if len(hits) >= self.limit:
                # The oldest hit leaving the window is when capacity frees up.
                retry_after = max(1, int(hits[0] + self.window_seconds - now) + 1)
                return False, retry_after

            hits.append(now)
            return True, 0

    def reset(self) -> None:
        """Clear all state. Used by tests."""
        with self._lock:
            self._hits.clear()
            self._last_cleanup = time.monotonic()


openfoodfacts_limiter = SlidingWindowRateLimiter(
    limit=settings.openfoodfacts_rate_limit_requests,
    window_seconds=settings.openfoodfacts_rate_limit_window_seconds,
)


def limit_openfoodfacts(current_user: CurrentUser) -> None:
    """FastAPI dependency guarding the outbound OpenFoodFacts endpoints.

    Keyed by user id, so one noisy account cannot spend everyone else's quota.
    """
    allowed, retry_after = openfoodfacts_limiter.check(f"user:{current_user.id}")
    if not allowed:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=(
                "Too many food searches. This limit protects the free "
                "OpenFoodFacts service. Please wait a moment and try again."
            ),
            headers={"Retry-After": str(retry_after)},
        )
