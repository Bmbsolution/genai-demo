"""Authentication: login, refresh-token rotation, and logout.

Operates only on the global ``users`` table, so it needs no workspace/RLS
context. Keys and Redis are injected, keeping the service unit-testable.
"""

from __future__ import annotations

import datetime as dt
import secrets
from dataclasses import dataclass
from typing import TYPE_CHECKING

from servicecat.config import get_settings
from servicecat.errors import AuthenticationError
from servicecat.repositories.users import UserRepository
from servicecat.services.security import (
    TokenType,
    create_token,
    decode_token,
    hash_password,
    verify_password,
)
from servicecat.services.token_store import TokenRevocationStore

if TYPE_CHECKING:
    import uuid

    from redis.asyncio import Redis
    from sqlalchemy.ext.asyncio import AsyncSession

# A valid argon2 hash of a random secret, verified against on the user-missing
# path so login takes constant time regardless of whether the email exists
# (defeats timing-based user enumeration).
_DUMMY_PASSWORD_HASH = hash_password(secrets.token_urlsafe(32))


@dataclass(frozen=True)
class TokenPair:
    """A freshly issued access + refresh token pair."""

    access_token: str
    refresh_token: str


class AuthService:
    """Password login and refresh-token lifecycle (rotation + revocation)."""

    def __init__(
        self,
        *,
        db: AsyncSession,
        redis: Redis,
        private_key: str,
        public_key: str,
    ) -> None:
        self._users = UserRepository(db)
        self._revocations = TokenRevocationStore(redis)
        self._private_key = private_key
        self._public_key = public_key
        self._settings = get_settings()

    async def login(self, email: str, password: str) -> TokenPair:
        """Verify credentials and issue a token pair, or raise 401.

        Always runs a password verification (against a dummy hash when the user
        is missing/password-less) so the response time does not reveal whether
        an account exists.
        """
        user = await self._users.get_by_email(email)
        stored_hash = (
            user.hashed_password if user and user.hashed_password else _DUMMY_PASSWORD_HASH
        )
        password_ok = verify_password(password, stored_hash)
        if user is None or user.hashed_password is None or not user.is_active or not password_ok:
            raise AuthenticationError("Invalid credentials")
        return self._issue_pair(user.id)

    async def refresh(self, refresh_token: str) -> TokenPair:
        """Rotate a refresh token: revoke the presented one, issue a new pair."""
        decoded = decode_token(
            refresh_token,
            public_key=self._public_key,
            expected_type=TokenType.REFRESH,
        )
        # Atomically consume the token: if it was already used/revoked, reject.
        if not await self._revocations.revoke_once(
            decoded.jti, self._remaining(decoded.expires_at)
        ):
            raise AuthenticationError("Refresh token has already been used or revoked")
        user = await self._users.get_by_id(decoded.subject)
        if user is None or not user.is_active:
            raise AuthenticationError("User is inactive")
        return self._issue_pair(user.id)

    async def logout(self, refresh_token: str) -> None:
        """Revoke a refresh token so it can no longer be exchanged."""
        decoded = decode_token(
            refresh_token,
            public_key=self._public_key,
            expected_type=TokenType.REFRESH,
        )
        await self._revocations.revoke(decoded.jti, self._remaining(decoded.expires_at))

    def _issue_pair(self, subject: uuid.UUID) -> TokenPair:
        access, _ = create_token(
            subject=subject,
            token_type=TokenType.ACCESS,
            ttl_seconds=self._settings.access_token_ttl_seconds,
            private_key=self._private_key,
        )
        refresh, _ = create_token(
            subject=subject,
            token_type=TokenType.REFRESH,
            ttl_seconds=self._settings.refresh_token_ttl_seconds,
            private_key=self._private_key,
        )
        return TokenPair(access_token=access, refresh_token=refresh)

    @staticmethod
    def _remaining(expires_at: dt.datetime) -> int:
        return int((expires_at - dt.datetime.now(dt.UTC)).total_seconds())
