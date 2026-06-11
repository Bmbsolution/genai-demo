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
    plus_one: bool
    dietary_notes: str | None
    checked_in_at: dt.datetime | None
    invite_token: str
    created_at: dt.datetime


class CheckInRequest(GatherlyBaseModel):
    """Mark a guest as arrived (or undo it) at the door."""

    checked_in: bool


class GuestImportRequest(GatherlyBaseModel):
    """Bulk-add guests from pasted/uploaded CSV with ``name,email`` rows."""

    csv: str = Field(min_length=1, max_length=200_000)


class GuestImportResponse(GatherlyBaseModel):
    """Outcome of a CSV import: what was added, and what was skipped and why."""

    created: int
    skipped_duplicate: int
    skipped_invalid: int
    errors: list[str]


class ReminderResponse(GatherlyBaseModel):
    """How many pending guests were sent a reminder."""

    sent: int
