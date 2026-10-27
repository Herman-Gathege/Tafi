"""Small fixed-window limiter for the public authentication endpoints."""

import hashlib
from collections import defaultdict, deque
from threading import Lock
from time import monotonic

from fastapi import HTTPException, status
from redis.exceptions import RedisError

from app.core.config import get_settings
from app.core.redis import get_redis

_memory_hits: defaultdict[str, deque[float]] = defaultdict(deque)
_memory_lock = Lock()


def clear_rate_limits() -> None:
    """Reset process-local counters. Used by the test suite."""
    with _memory_lock:
        _memory_hits.clear()


def _memory_allows(key: str, limit: int, window_seconds: int) -> bool:
    now = monotonic()
    cutoff = now - window_seconds
    with _memory_lock:
        hits = _memory_hits[key]
        while hits and hits[0] <= cutoff:
            hits.popleft()
        if len(hits) >= limit:
            return False
        hits.append(now)
        return True


def _redis_allows(key: str, limit: int, window_seconds: int) -> bool:
    # INCR and EXPIRE run atomically enough for a fixed window: the first caller
    # sets the expiry, and no request reaches this API until a Redis connection
    # has already been established.
    count = int(
        get_redis().eval(
            """
            local current = redis.call('INCR', KEYS[1])
            if current == 1 then
                redis.call('EXPIRE', KEYS[1], ARGV[1])
            end
            return current
            """,
            1,
            key,
            window_seconds,
        )
    )
    return count <= limit


def enforce_auth_rate_limit(scope: str, identity: str) -> None:
    """Reject a caller who exceeds the configured authentication rate."""
    settings = get_settings()
    limit = (
        settings.auth_signup_limit if scope == "signup" else settings.auth_sign_in_limit
    )
    window = settings.auth_rate_window_seconds
    digest = hashlib.sha256(identity.encode("utf-8")).hexdigest()
    key = f"tafi:rate:{scope}:{digest}"

    if settings.app_env == "local":
        allowed = _memory_allows(key, limit, window)
    else:
        try:
            allowed = _redis_allows(key, limit, window)
        except (RedisError, OSError):
            # Keep authentication available if Redis is temporarily unavailable;
            # the fallback is deliberately local to this process.
            allowed = _memory_allows(key, limit, window)

    if not allowed:
        raise HTTPException(
            status.HTTP_429_TOO_MANY_REQUESTS,
            "Too many attempts. Try again in a minute.",
            headers={"Retry-After": str(window)},
        )
