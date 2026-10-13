"""Redis client factory (queue, cache and rate-limit backend)."""

from functools import lru_cache

import redis

from app.core.config import get_settings


@lru_cache
def get_redis() -> redis.Redis:
    """Return a process-wide Redis client built from `REDIS_URL`."""
    return redis.Redis.from_url(get_settings().redis_url)
