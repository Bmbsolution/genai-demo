"""In-memory refresh-token revocation store (single-process demo).

ServiceCat backs this with Redis; Gatherly keeps it in-process to stay
zero-infra. Same contract: ``revoke_once`` is the atomic check-and-set that
makes refresh-token rotation safe against replay.
"""

from __future__ import annotations

import time
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    import uuid


class TokenRevocationStore:
    """Tracks revoked refresh-token JTIs until their natural expiry."""

    def __init__(self) -> None:
        self._revoked: dict[str, float] = {}

    def _purge(self, now: float) -> None:
        for jti in [jti for jti, exp in self._revoked.items() if exp <= now]:
            del self._revoked[jti]

    def revoke_once(self, jti: uuid.UUID, ttl_seconds: int) -> bool:
        """Atomically revoke ``jti``. Returns False if it was already revoked.

        This is the rotation gate: a refresh token may be exchanged exactly
        once. A replayed (already-consumed) token returns False → reject.
        """
        now = time.time()
        self._purge(now)
        key = str(jti)
        if key in self._revoked:
            return False
        self._revoked[key] = now + max(ttl_seconds, 0)
        return True

    def revoke(self, jti: uuid.UUID, ttl_seconds: int) -> None:
        """Revoke ``jti`` (idempotent) — used by logout."""
        self._revoked[str(jti)] = time.time() + max(ttl_seconds, 0)

    def is_revoked(self, jti: uuid.UUID) -> bool:
        """Return True iff ``jti`` is currently revoked."""
        now = time.time()
        self._purge(now)
        return str(jti) in self._revoked


_store = TokenRevocationStore()


def get_revocation_store() -> TokenRevocationStore:
    """Return the process-wide revocation store singleton."""
    return _store
