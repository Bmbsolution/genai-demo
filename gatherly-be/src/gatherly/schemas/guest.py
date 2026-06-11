"""Guest request/response schemas (host-facing)."""

from __future__ import annotations

import datetime as dt
import uuid

from pydantic import EmailStr, Field

from gatherly.schemas.base import GatherlyBaseModel


class GuestCreateRequest(GatherlyBaseModel):
    """Invite a guest to an event."""

    name: str = Field(min_length=1, max_length=200)
    email: EmailStr


class GuestResponse(GatherlyBaseModel):
    """A guest row as the host sees it (includes the private invite token)."""

    id: uuid.UUID
    event_id: uuid.UUID
    name: str
    email: EmailStr
    rsvp_status: str
    invite_token: str
    created_at: dt.datetime
