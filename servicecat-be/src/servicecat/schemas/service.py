"""Service catalog request/response schemas."""

from __future__ import annotations

import uuid
from datetime import datetime

from pydantic import Field

from servicecat.schemas.base import ServiceCatBaseModel

_MIN_TIER = 1
_MAX_TIER = 3


class ServiceCreateRequest(ServiceCatBaseModel):
    name: str = Field(min_length=1, max_length=200)
    description: str | None = None
    repo_url: str = Field(min_length=1)
    tier: int = Field(ge=_MIN_TIER, le=_MAX_TIER)
    owner_team_id: uuid.UUID | None = None


class ServiceUpdateRequest(ServiceCatBaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=200)
    description: str | None = None
    repo_url: str | None = Field(default=None, min_length=1)
    tier: int | None = Field(default=None, ge=_MIN_TIER, le=_MAX_TIER)
    owner_team_id: uuid.UUID | None = None


class ServiceResponse(ServiceCatBaseModel):
    id: uuid.UUID
    workspace_id: uuid.UUID
    name: str
    description: str | None
    repo_url: str
    tier: int
    owner_team_id: uuid.UUID | None
    created_at: datetime
    updated_at: datetime


class PageMeta(ServiceCatBaseModel):
    limit: int
    offset: int
    total: int


class ServiceListResponse(ServiceCatBaseModel):
    data: list[ServiceResponse]
    meta: PageMeta
