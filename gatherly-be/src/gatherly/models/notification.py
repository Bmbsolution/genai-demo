"""Notification — an in-app message addressed to a single host.

Notifications are owned directly by a user (``owner_id``): tenant isolation (S2)
is enforced by scoping every read/write to the recipient. The optional
``event_id`` links a notification back to the event it concerns; it is nullable
because some notifications (billing, system) are not about an event.
"""

from __future__ import annotations

import datetime as dt
import enum
import uuid

from sqlalchemy import DateTime, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from gatherly.models.base import Base, TimestampMixin, UUIDPrimaryKeyMixin


class NotificationType(enum.StrEnum):
    """What a notification is about — drives icon/copy on the client."""

    GUEST_RSVP = "guest.rsvp"
    GUEST_CHECKED_IN = "guest.checked_in"
    EVENT_READINESS = "event.readiness"
    SYSTEM = "system"


class Notification(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """An in-app notification for one host. Owned by ``owner_id`` (S2)."""

    __tablename__ = "notifications"

    owner_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        index=True,
    )
    type: Mapped[str] = mapped_column(String(40), default=NotificationType.SYSTEM.value)
    title: Mapped[str] = mapped_column(String(200))
    body: Mapped[str | None] = mapped_column(Text, default=None)
    event_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("events.id", ondelete="CASCADE"),
        default=None,
        index=True,
    )
    # Null = unread; set to the time the host first marked it read.
    read_at: Mapped[dt.datetime | None] = mapped_column(DateTime(timezone=True), default=None)
