"""Google Sign-In: verify a GIS ID token, upsert the user, issue our tokens.

We use the Identity-Services ID-token flow: the browser obtains a signed JWT
from Google; here we verify it against Google's published keys (RS256) and
trust the claims. No client secret is needed for this flow.
"""

from __future__ import annotations

from functools import lru_cache
from typing import TYPE_CHECKING, Any

import jwt
from jwt import PyJWKClient

from gatherly.config import get_settings
from gatherly.errors import AuthenticationError, DomainValidationError
from gatherly.models import User
from gatherly.repositories.users import UserRepository
from gatherly.services.auth_service import TokenPair, issue_token_pair

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import AsyncSession

import asyncio

_GOOGLE_CERTS_URL = "https://www.googleapis.com/oauth2/v3/certs"
_VALID_ISSUERS = {"accounts.google.com", "https://accounts.google.com"}


@lru_cache(maxsize=1)
def _jwks_client() -> PyJWKClient:
    return PyJWKClient(_GOOGLE_CERTS_URL)


class GoogleAuthService:
    """Verify a Google ID token and turn it into a Gatherly session."""

    def __init__(self, db: AsyncSession) -> None:
        self._users = UserRepository(db)
        self._settings = get_settings()

    def _verify(self, id_token: str) -> dict[str, Any]:
        """Verify signature, audience, issuer, expiry (sync — runs in a thread)."""
        client_id = self._settings.google_client_id
        if not client_id:
            raise DomainValidationError("Google sign-in is not configured.")
        try:
            signing_key = _jwks_client().get_signing_key_from_jwt(id_token)
            claims: dict[str, Any] = jwt.decode(
                id_token,
                signing_key.key,
                algorithms=["RS256"],
                audience=client_id,
                options={"require": ["exp", "iss", "sub", "aud"]},
            )
        except jwt.InvalidTokenError as exc:
            raise AuthenticationError("Invalid Google token") from exc
        if claims.get("iss") not in _VALID_ISSUERS:
            raise AuthenticationError("Untrusted Google token issuer")
        if not claims.get("email"):
            raise AuthenticationError("Google token has no email")
        if not claims.get("email_verified"):
            raise AuthenticationError("Google email is not verified")
        return claims

    async def authenticate(self, id_token: str) -> TokenPair:
        """Verify the token and return a session for the matched/created user."""
        claims = await asyncio.to_thread(self._verify, id_token)
        sub = str(claims["sub"])
        email = str(claims["email"])
        name = str(claims.get("name") or email.split("@", 1)[0])
        picture = claims.get("picture")
        avatar = str(picture) if picture else None

        user = await self._users.get_by_google_sub(sub)
        if user is None:
            user = await self._users.get_by_email(email)
        if user is None:
            user = User(
                email=email,
                display_name=name,
                auth_provider="google",
                google_sub=sub,
                avatar_url=avatar,
            )
            await self._users.add(user)
        else:
            # Link Google to an existing account and backfill the avatar.
            if user.google_sub is None:
                user.google_sub = sub
            if avatar and not user.avatar_url:
                user.avatar_url = avatar
        if not user.is_active:
            raise AuthenticationError("Account is inactive")
        return issue_token_pair(user.id)
