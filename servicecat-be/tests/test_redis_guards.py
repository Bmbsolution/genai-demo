"""Tests for the Redis-backed S4 rate limiter and refresh-token revocation."""

from __future__ import annotations

import uuid
from types import SimpleNamespace
from typing import TYPE_CHECKING

import pytest

from servicecat.deps import rate_limit
from servicecat.errors import RateLimitError
from servicecat.services.token_store import TokenRevocationStore

if TYPE_CHECKING:
    from redis.asyncio import Redis


async def test_token_revocation_roundtrip(redis_client: Redis) -> None:
    store = TokenRevocationStore(redis_client)
    jti = uuid.uuid4()
    other = uuid.uuid4()
    assert await store.is_revoked(jti) is False
    await store.revoke(jti, ttl_seconds=60)
    assert await store.is_revoked(jti) is True
    assert await store.is_revoked(other) is False


async def test_rate_limit_blocks_after_threshold(redis_client: Redis) -> None:
    enforce = rate_limit(per_minute=3, key=f"test:{uuid.uuid4()}")
    request = SimpleNamespace(client=SimpleNamespace(host=str(uuid.uuid4())))
    for _ in range(3):
        await enforce(request, redis=redis_client)
    with pytest.raises(RateLimitError, match="Rate limit exceeded"):
        await enforce(request, redis=redis_client)
