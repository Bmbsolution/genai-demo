"""Auth request/response schemas."""

from __future__ import annotations

import uuid

from servicecat.schemas.base import ServiceCatBaseModel


class LoginRequest(ServiceCatBaseModel):
    email: str
    password: str


class RefreshRequest(ServiceCatBaseModel):
    refresh_token: str


class TokenPairResponse(ServiceCatBaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"  # noqa: S105 — OAuth2 token_type literal, not a secret


class UserResponse(ServiceCatBaseModel):
    id: uuid.UUID
    email: str
    full_name: str
    is_active: bool
