"""Public RSVP schemas (guest-facing, keyed by invite token).

A guest sees their own invite and the event basics, and can set their RSVP
status plus whether they're bringing a +1 and any dietary notes. No other
guest's data is ever exposed here.
"""

from __future__ import annotations

import datetime as dt

from pydantic import Field

from gatherly.models.guest import RsvpStatus
from gatherly.schemas.base import GatherlyBaseModel


class RsvpEventInfo(GatherlyBaseModel):
    """The public-safe view of the event a guest is invited to."""

    title: str
    description: str | None
    starts_at: dt.datetime
    ends_at: dt.datetime | None
    location: str | None
    cover_image_url: str | None


class RsvpView(GatherlyBaseModel):
    """What the guest-facing RSVP page shows."""

    guest_name: str
    rsvp_status: str
    plus_one: bool
    dietary_notes: str | None
    event: RsvpEventInfo


class RsvpUpdateRequest(GatherlyBaseModel):
    """A guest setting their attendance and details."""

    rsvp_status: RsvpStatus
    plus_one: bool = False
    dietary_notes: str | None = Field(default=None, max_length=500)
