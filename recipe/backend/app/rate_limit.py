"""Per-user rate limiting for the parse endpoint (spec §6).

Bounds LLM cost and abuse. Two interchangeable implementations behind one
`check(key)` interface:

- **RedisRateLimiter** — a sliding-window counter enforced *globally* across all
  workers and instances via an atomic Lua script. Used when `REDIS_URL` is set.
- **InMemoryRateLimiter** — process-local sliding window. The default when no
  Redis is configured (single-process dev, tests).

Behavior (defaults): at most `PARSE_RATE_LIMIT_PER_HOUR` (20) parse requests per
user per rolling 3600s. Over the limit → `AppError("RATE_LIMITED", 429)` with a
human "try again in ~Ns" hint derived from the oldest request in the window.

Failure mode: if Redis is unreachable, the limiter **fails open** (allows the
request) and logs a warning — availability of the feature is preferred over
hard-blocking when the limiter backend is down. The LLM provider's own limits
still apply as a backstop.
"""

import logging
import threading
import time
import uuid
from typing import Protocol

from app.config import get_settings
from app.errors import AppError

logger = logging.getLogger("recipe.rate_limit")

_KEY_PREFIX = "parse_rl:"


def _too_many(retry_after: int) -> AppError:
    hint = f" Try again in about {retry_after}s." if retry_after > 0 else ""
    return AppError(
        "RATE_LIMITED",
        f"Too many import requests.{hint}",
        status_code=429,
    )


class RateLimiter(Protocol):
    def check(self, key: str) -> None: ...
    def reset(self) -> None: ...


class InMemoryRateLimiter:
    """Process-local sliding-window limiter."""

    def __init__(self, limit: int, window_seconds: int) -> None:
        self._limit = limit
        self._window = window_seconds
        self._hits: dict[str, list[float]] = {}
        self._lock = threading.Lock()

    def check(self, key: str) -> None:
        now = time.monotonic()
        cutoff = now - self._window
        with self._lock:
            hits = [t for t in self._hits.get(key, []) if t > cutoff]
            if len(hits) >= self._limit:
                retry_in = int(hits[0] + self._window - now) + 1
                raise _too_many(retry_in)
            hits.append(now)
            self._hits[key] = hits

    def reset(self) -> None:
        with self._lock:
            self._hits.clear()


# Atomic sliding-window check: drop entries older than the window, count what
# remains, and either record this hit or report how long until the oldest entry
# expires. Returns {allowed (1/0), retry_after_seconds}.
_LUA_SLIDING_WINDOW = """
local key = KEYS[1]
local now = tonumber(ARGV[1])
local window = tonumber(ARGV[2])
local limit = tonumber(ARGV[3])
local member = ARGV[4]
redis.call('ZREMRANGEBYSCORE', key, 0, now - window)
local count = redis.call('ZCARD', key)
if count >= limit then
  local oldest = redis.call('ZRANGE', key, 0, 0, 'WITHSCORES')
  local retry = 0
  if oldest[2] then
    retry = math.ceil((tonumber(oldest[2]) + window - now) / 1000)
  end
  return {0, retry}
end
redis.call('ZADD', key, now, member)
redis.call('PEXPIRE', key, window)
return {1, 0}
"""


class RedisRateLimiter:
    """Sliding-window limiter shared across all workers/instances via Redis."""

    def __init__(self, redis_url: str, limit: int, window_seconds: int) -> None:
        self._url = redis_url
        self._limit = limit
        self._window_ms = window_seconds * 1000
        self._client = None
        self._script = None
        self._lock = threading.Lock()

    def _ensure_client(self):
        if self._client is None:
            with self._lock:
                if self._client is None:
                    import redis  # lazy import; only needed when Redis is used

                    client = redis.Redis.from_url(
                        self._url, socket_timeout=2, socket_connect_timeout=2
                    )
                    self._script = client.register_script(_LUA_SLIDING_WINDOW)
                    self._client = client
        return self._client

    def check(self, key: str) -> None:
        full_key = _KEY_PREFIX + key
        now_ms = int(time.time() * 1000)
        member = f"{now_ms}-{uuid.uuid4().hex}"
        try:
            self._ensure_client()
            allowed, retry_after = self._script(  # type: ignore[misc]
                keys=[full_key],
                args=[now_ms, self._window_ms, self._limit, member],
            )
        except Exception as exc:  # Redis down / network error -> fail open
            logger.warning("Rate limiter unavailable, allowing request: %s", exc)
            return
        if int(allowed) == 0:
            raise _too_many(int(retry_after))

    def reset(self) -> None:
        try:
            client = self._ensure_client()
            for k in client.scan_iter(match=_KEY_PREFIX + "*"):
                client.delete(k)
        except Exception:  # best-effort (used in tests)
            pass


def build_rate_limiter() -> RateLimiter:
    settings = get_settings()
    if settings.redis_url:
        logger.info("Using Redis-backed parse rate limiter.")
        return RedisRateLimiter(
            settings.redis_url,
            limit=settings.parse_rate_limit_per_hour,
            window_seconds=3600,
        )
    logger.info("Using in-memory parse rate limiter (set REDIS_URL for global limits).")
    return InMemoryRateLimiter(
        limit=settings.parse_rate_limit_per_hour, window_seconds=3600
    )


parse_rate_limiter: RateLimiter = build_rate_limiter()
