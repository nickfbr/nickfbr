"""Per-user sliding-window rate limiter for the parse endpoint.

In-memory only — fine for a single process. For multi-worker / multi-instance
deployments, back this with Redis (same interface). Bounds LLM cost and abuse
per §6.
"""

import threading
import time

from app.config import get_settings
from app.errors import AppError


class SlidingWindowRateLimiter:
    def __init__(self, limit: int, window_seconds: int) -> None:
        self._limit = limit
        self._window = window_seconds
        self._hits: dict[str, list[float]] = {}
        self._lock = threading.Lock()

    def check(self, key: str) -> None:
        """Record a hit for `key`; raise AppError(429) if over the limit."""
        now = time.monotonic()
        cutoff = now - self._window
        with self._lock:
            hits = [t for t in self._hits.get(key, []) if t > cutoff]
            if len(hits) >= self._limit:
                retry_in = int(hits[0] + self._window - now) + 1
                raise AppError(
                    "RATE_LIMITED",
                    f"Too many import requests. Try again in about {retry_in}s.",
                    status_code=429,
                )
            hits.append(now)
            self._hits[key] = hits


_settings = get_settings()
parse_rate_limiter = SlidingWindowRateLimiter(
    limit=_settings.parse_rate_limit_per_hour, window_seconds=3600
)
