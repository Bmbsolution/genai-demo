"""Guest — an invitee on an event, with their RSVP.

NOTE: ``plus_one`` and ``dietary_notes`` are intentionally ABSENT here. They are
the feature built live during the conference demo ("add a +1 / dietary field"),
so the baseline guest carries only name, email, and an RSVP status.
"""

from __future__ import annotations

import enum
import uuid

from sqlalchemy import ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column

from gatherly.models.base import Base, TimestampMixin, UUIDPrimaryKeyMixin


class RsvpStatus(enum.StrEnum):
    """A guest's response to the invitation."""

    PENDING = "pending"
    YES = "yes"
    NO = "no"
    MAYBE = "maybe"


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
