"""Guest — an invitee on an event, with their RSVP.

Carries the guest's RSVP plus the details a host needs to plan: whether they're
bringing a +1 and any dietary notes.
"""

from __future__ import annotations

import datetime as dt
import enum
import uuid

from sqlalchemy import Boolean, DateTime, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from gatherly.models.base import Base, TimestampMixin, UUIDPrimaryKeyMixin


class RsvpStatus(enum.StrEnum):
    """A guest's response to the invitation."""

    PENDING = "pending"
    YES = "yes"
    NO = "no"
    MAYBE = "maybe"
    WAITLISTED = "waitlisted"


class Guest(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """An invitee. The ``invite_token`` is the per-guest secret used by the
    public RSVP page — a guest can only ever see/update their own row."""

    __tablename__ = "guests"

    event_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("events.id", ondelete="CASCADE"),
        index=True,
    )
    name: Mapped[str] = mapped_column(String(200))
    email: Mapped[str] = mapped_column(String(320))
    rsvp_status: Mapped[str] = mapped_column(String(20), default=RsvpStatus.PENDING.value)
    invite_token: Mapped[str] = mapped_column(String(64), unique=True, index=True)
    plus_one: Mapped[bool] = mapped_column(Boolean, default=False)
    dietary_notes: Mapped[str | None] = mapped_column(Text, default=None)
    # Set when the host marks the guest as arrived at the door; null = not yet.
    checked_in_at: Mapped[dt.datetime | None] = mapped_column(
        DateTime(timezone=True),
        default=None,
    )
