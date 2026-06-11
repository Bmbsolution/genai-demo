"""Password hashing (argon2id) and JWT creation/verification (HS256).

Pure functions: the secret and TTLs are passed in, so this module has no
dependency on settings or the database and is trivially unit-testable.
"""

from __future__ import annotations

import datetime as dt
import enum
import uuid
from dataclasses import dataclass

import jwt
from argon2 import PasswordHasher
from argon2.exceptions import InvalidHashError, VerifyMismatchError

from gatherly.errors import AuthenticationError

_hasher = PasswordHasher()


class TokenType(enum.StrEnum):
    """Kind of JWT. Refresh tokens are revocable; access tokens are not."""

    ACCESS = "access"
    REFRESH = "refresh"


@dataclass(frozen=True)
class DecodedToken:
    """The validated subset of claims callers rely on."""

    subject: uuid.UUID
    token_type: TokenType
    jti: uuid.UUID
    expires_at: dt.datetime


def hash_password(password: str) -> str:
    """Hash a plaintext password with argon2id."""
    return _hasher.hash(password)


def verify_password(password: str, hashed: str) -> bool:
    """Return True iff ``password`` matches ``hashed`` (never raises)."""
    try:
        return _hasher.verify(hashed, password)
    except (VerifyMismatchError, InvalidHashError):
        return False


def create_token(
    *,
    subject: uuid.UUID,
    token_type: TokenType,
    ttl_seconds: int,
    secret: str,
    algorithm: str = "HS256",
) -> tuple[str, uuid.UUID]:
    """Sign a JWT for ``subject``. Returns ``(encoded_token, jti)``."""
    now = dt.datetime.now(dt.UTC)
    jti = uuid.uuid4()
    payload = {
        "sub": str(subject),
        "type": token_type.value,
        "jti": str(jti),
        "iat": int(now.timestamp()),
        "exp": int((now + dt.timedelta(seconds=ttl_seconds)).timestamp()),
    }
    return jwt.encode(payload, secret, algorithm=algorithm), jti


def decode_token(
    token: str,
    *,
    secret: str,
    expected_type: TokenType | None = None,
    algorithm: str = "HS256",
) -> DecodedToken:
    """Verify signature + expiry and return structured claims.

    Raises ``AuthenticationError`` for any invalid, expired, malformed, or
    wrong-type token — never leaks a library-specific exception to callers.
    """
    try:
        claims = jwt.decode(token, secret, algorithms=[algorithm])
    except jwt.ExpiredSignatureError as exc:
        raise AuthenticationError("Token has expired") from exc
    except jwt.InvalidTokenError as exc:
        raise AuthenticationError("Invalid token") from exc

    try:
        subject = uuid.UUID(claims["sub"])
        actual_type = TokenType(claims["type"])
        jti = uuid.UUID(claims["jti"])
        expires_at = dt.datetime.fromtimestamp(claims["exp"], tz=dt.UTC)
    except (KeyError, ValueError) as exc:
        raise AuthenticationError("Malformed token claims") from exc

    if expected_type is not None and actual_type is not expected_type:
        raise AuthenticationError(f"Expected a {expected_type.value} token")

    return DecodedToken(subject=subject, token_type=actual_type, jti=jti, expires_at=expires_at)
