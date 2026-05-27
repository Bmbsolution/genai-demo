"""Refresh-token revocation list, backed by Redis.

Refresh tokens are stateful: on rotation or logout their ``jti`` is recorded
here with a TTL equal to the token's remaining lifetime, so a revoked token is
forgotten automatically once it would have expired anyway.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    import uuid

    from redis.asyncio import Redis

_REVOKED_PREFIX = "revoked:refresh:"


class TokenRevocationStore:
    """Records and checks revoked refresh-token identifiers."""

    def __init__(self, redis: Redis) -> None:
        self._redis = redis

    async def revoke(self, jti: uuid.UUID, ttl_seconds: int) -> None:
        """Mark ``jti`` revoked for at least ``ttl_seconds`` (min 1s)."""
        await self._redis.set(f"{_REVOKED_PREFIX}{jti}", "1", ex=max(ttl_seconds, 1))

    async def revoke_once(self, jti: uuid.UUID, ttl_seconds: int) -> bool:
        """Atomically revoke ``jti`` exactly once.

        Returns True if this call performed the revocation, False if it was
        already revoked. Uses ``SET NX`` so concurrent refreshes of the same
        token cannot both succeed (closes the check-then-revoke TOCTOU).
        """
        was_set = await self._redis.set(
            f"{_REVOKED_PREFIX}{jti}",
            "1",
            ex=max(ttl_seconds, 1),
            nx=True,
        )
        return bool(was_set)

    async def is_revoked(self, jti: uuid.UUID) -> bool:
        """Return True iff ``jti`` has been revoked and not yet expired."""
        return bool(await self._redis.exists(f"{_REVOKED_PREFIX}{jti}"))
