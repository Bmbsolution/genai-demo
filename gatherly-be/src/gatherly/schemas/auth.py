"""Auth request/response schemas. Token responses stay flat (OAuth2 convention)."""

from __future__ import annotations

import uuid

from pydantic import EmailStr

from gatherly.schemas.base import GatherlyBaseModel


class LoginRequest(GatherlyBaseModel):
    """Email + password login."""

    email: EmailStr
    password: str


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
