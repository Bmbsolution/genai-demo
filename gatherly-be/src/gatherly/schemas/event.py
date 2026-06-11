"""Event request/response schemas."""

from __future__ import annotations

import datetime as dt
import uuid

from pydantic import Field

from gatherly.models.event import EventStatus
from gatherly.schemas.base import GatherlyBaseModel, PageMeta


class EventCreateRequest(GatherlyBaseModel):
    """Create an event."""

    title: str = Field(min_length=1, max_length=200)
    description: str | None = Field(default=None, max_length=4000)
    starts_at: dt.datetime
    location: str | None = Field(default=None, max_length=300)
    capacity: int | None = Field(default=None, ge=1, le=100_000)


class EventUpdateRequest(GatherlyBaseModel):
    """Partial update of an event."""

    title: str | None = Field(default=None, min_length=1, max_length=200)
    description: str | None = Field(default=None, max_length=4000)
    starts_at: dt.datetime | None = None
    location: str | None = Field(default=None, max_length=300)
    capacity: int | None = Field(default=None, ge=1, le=100_000)
    status: EventStatus | None = None


class EventResponse(GatherlyBaseModel):
    """An event as returned to its host."""

    id: uuid.UUID
    owner_id: uuid.UUID
    title: str
    description: str | None
    starts_at: dt.datetime
    location: str | None
    capacity: int | None
    status: str
    created_at: dt.datetime


class EventListResponse(GatherlyBaseModel):
    """Paginated list of events."""

    data: list[EventResponse]
    meta: PageMeta
