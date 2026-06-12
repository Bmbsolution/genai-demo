"""Authentication: login, refresh-token rotation, and logout."""

from __future__ import annotations

import datetime as dt
import secrets
from dataclasses import dataclass
from typing import TYPE_CHECKING

from sqlalchemy.exc import IntegrityError

from gatherly.config import get_settings
from gatherly.errors import AuthenticationError, ConflictError
from gatherly.models import User
from gatherly.repositories.users import UserRepository
from gatherly.security import (
    TokenType,
    create_token,
    decode_token,
    hash_password,
    verify_password,
)

if TYPE_CHECKING:
    import uuid

    from sqlalchemy.ext.asyncio import AsyncSession

    from gatherly.token_store import TokenRevocationStore

# A valid argon2 hash verified against on the user-missing path so login takes
# constant time regardless of whether the email exists (defeats enumeration).
_DUMMY_PASSWORD_HASH = hash_password(secrets.token_urlsafe(32))


@dataclass(frozen=True)
class TokenPair:
    """A freshly issued access + refresh token pair."""

    access_token: str
    refresh_token: str


def issue_token_pair(subject: uuid.UUID) -> TokenPair:
    """Mint an access + refresh pair for ``subject`` (shared by all login paths)."""
    settings = get_settings()
    access, _ = create_token(
        subject=subject,
        token_type=TokenType.ACCESS,
        ttl_seconds=settings.access_token_ttl_seconds,
        secret=settings.jwt_secret,
    )
    refresh, _ = create_token(
        subject=subject,
        token_type=TokenType.REFRESH,
        ttl_seconds=settings.refresh_token_ttl_seconds,
        secret=settings.jwt_secret,
    )
    return TokenPair(access_token=access, refresh_token=refresh)


class AuthService:
    """Password login and refresh-token lifecycle (rotation + revocation)."""

    def __init__(self, *, db: AsyncSession, revocations: TokenRevocationStore) -> None:
        self._users = UserRepository(db)
        self._revocations = revocations
        self._settings = get_settings()

    async def register(self, *, email: str, password: str, display_name: str) -> TokenPair:
        """Create a password account and issue a token pair, or 409 if taken."""
        if await self._users.get_by_email(email) is not None:
            raise ConflictError(
                "An account with this email already exists.",
                details={"field": "email"},
            )
        user = User(
            email=email,
            display_name=display_name,
            hashed_password=hash_password(password),
            auth_provider="password",
        )
        try:
            await self._users.add(user)
        except IntegrityError as exc:  # unique email — lost the check/insert race
            raise ConflictError(
                "An account with this email already exists.",
                details={"field": "email"},
            ) from exc
        return self._issue_pair(user.id)

    async def login(self, email: str, password: str) -> TokenPair:
        """Verify credentials and issue a token pair, or raise 401."""
        user = await self._users.get_by_email(email)
        stored_hash = (
            user.hashed_password if user and user.hashed_password else _DUMMY_PASSWORD_HASH
        )
        password_ok = verify_password(password, stored_hash)
        if user is None or user.hashed_password is None or not user.is_active or not password_ok:
            raise AuthenticationError("Invalid credentials")
        return self._issue_pair(user.id)

    async def refresh(self, refresh_token: str) -> TokenPair:
        """Rotate a refresh token: consume the presented one, issue a new pair."""
        decoded = decode_token(
            refresh_token,
            secret=self._settings.jwt_secret,
            expected_type=TokenType.REFRESH,
        )
        if not self._revocations.revoke_once(decoded.jti, self._remaining(decoded.expires_at)):
            raise AuthenticationError("Refresh token has already been used or revoked")
        user = await self._users.get_by_id(decoded.subject)
        if user is None or not user.is_active:
            raise AuthenticationError("User is inactive")
        return self._issue_pair(user.id)

    async def logout(self, refresh_token: str) -> None:
        """Revoke a refresh token so it can no longer be exchanged."""
        decoded = decode_token(
            refresh_token,
            secret=self._settings.jwt_secret,
            expected_type=TokenType.REFRESH,
        )
        self._revocations.revoke(decoded.jti, self._remaining(decoded.expires_at))

    def _issue_pair(self, subject: uuid.UUID) -> TokenPair:
        return issue_token_pair(subject)

    @staticmethod
    def _remaining(expires_at: dt.datetime) -> int:
        return int((expires_at - dt.datetime.now(dt.UTC)).total_seconds())
