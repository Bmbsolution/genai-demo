"""Scorecard run request/response schemas."""

from __future__ import annotations

import uuid
from datetime import datetime

from pydantic import Field

from servicecat.schemas.base import ServiceCatBaseModel


class ScorecardRunCreateRequest(ServiceCatBaseModel):
    target_service_ids: list[uuid.UUID] = Field(min_length=1)


class ScorecardRunResponse(ServiceCatBaseModel):
    id: uuid.UUID
    scorecard: str
    status: str
    triggered_by: uuid.UUID
    target_service_ids: list[uuid.UUID]
    finding_count: int
    error: str | None
    created_at: datetime
    started_at: datetime | None
    finished_at: datetime | None
