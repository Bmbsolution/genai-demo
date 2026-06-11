"""Auth request/response schemas. Token responses stay flat (OAuth2 convention)."""

from __future__ import annotations

import uuid

from pydantic import EmailStr, Field

from gatherly.schemas.base import GatherlyBaseModel


class LoginRequest(GatherlyBaseModel):
    """Email + password login."""

    email: EmailStr
    password: str


class RegisterRequest(GatherlyBaseModel):
    """Create a password-based account."""

    email: EmailStr
    password: str = Field(min_length=8, max_length=128)
    display_name: str = Field(min_length=1, max_length=120)


class GoogleAuthRequest(GatherlyBaseModel):
    """Exchange a Google ID token (from GIS) for our token pair."""

    id_token: str


class ProfileUpdateRequest(GatherlyBaseModel):
    """Partial update of the signed-in user's profile."""

    display_name: str | None = Field(default=None, min_length=1, max_length=120)
    timezone: str | None = Field(default=None, max_length=64)
    avatar_url: str | None = Field(default=None, max_length=1024)


class ChangePasswordRequest(GatherlyBaseModel):
    """Change the password for a password-based account."""

    current_password: str
    new_password: str = Field(min_length=8, max_length=128)


class RefreshRequest(GatherlyBaseModel):
    """Exchange a refresh token for a new pair."""

    refresh_token: str


class TokenPairResponse(GatherlyBaseModel):
    """Flat OAuth2-style token response (not enveloped)."""

    access_token: str
    refresh_token: str
    token_type: str = "bearer"  # noqa: S105 - OAuth2 token_type label, not a secret


class UserResponse(GatherlyBaseModel):
    """The authenticated user (``/auth/me``)."""

    id: uuid.UUID
    email: EmailStr
    display_name: str
    role: str
    avatar_url: str | None
    timezone: str
    auth_provider: str
