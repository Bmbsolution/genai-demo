"""Public RSVP schemas (guest-facing, keyed by invite token).

Deliberately minimal: a guest sees their own invite and the event basics, and
can set only their RSVP status. No other guest's data is ever exposed here.
"""

from __future__ import annotations

import datetime as dt

from gatherly.models.guest import RsvpStatus
from gatherly.schemas.base import GatherlyBaseModel


class RsvpEventInfo(GatherlyBaseModel):
    """The public-safe view of the event a guest is invited to."""

    title: str
    starts_at: dt.datetime
    location: str | None


class RsvpView(GatherlyBaseModel):
    """What the guest-facing RSVP page shows."""

    guest_name: str
    rsvp_status: str
    event: RsvpEventInfo


class RsvpUpdateRequest(GatherlyBaseModel):
    """A guest setting their attendance."""

    rsvp_status: RsvpStatus
