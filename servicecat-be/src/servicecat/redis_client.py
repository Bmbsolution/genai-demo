"""Shared async Redis client (rate-limit counters, token revocation, queues)."""

from __future__ import annotations

from functools import lru_cache
from typing import cast

from redis.asyncio import Redis

from servicecat.config import get_settings


@lru_cache(maxsize=1)
def get_redis() -> Redis:
    """Return the process-wide async Redis client (decoded responses)."""
    return cast("Redis", Redis.from_url(get_settings().redis_url, decode_responses=True))


async def close_redis() -> None:
    """Close and reset the shared client (called on application shutdown)."""
    client = get_redis()
    await client.aclose()
    get_redis.cache_clear()
