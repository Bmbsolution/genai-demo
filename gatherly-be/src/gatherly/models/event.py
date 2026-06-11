"""Event — something a host is planning that guests RSVP to."""

from __future__ import annotations

import datetime as dt
import enum
import uuid

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from gatherly.models.base import Base, TimestampMixin, UUIDPrimaryKeyMixin


class EventStatus(enum.StrEnum):
    """Whether the event is still a draft or live for guests."""

    DRAFT = "draft"
    PUBLISHED = "published"


class Event(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """A host-owned event. Tenant isolation is by ``owner_id`` (S2)."""

    __tablename__ = "events"

    owner_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        index=True,
    )
    title: Mapped[str] = mapped_column(String(200))
    description: Mapped[str | None] = mapped_column(Text, default=None)
    starts_at: Mapped[dt.datetime] = mapped_column(DateTime(timezone=True))
    location: Mapped[str | None] = mapped_column(String(300), default=None)
    capacity: Mapped[int | None] = mapped_column(Integer, default=None)
    status: Mapped[str] = mapped_column(String(20), default=EventStatus.DRAFT.value)
    deleted_at: Mapped[dt.datetime | None] = mapped_column(DateTime(timezone=True), default=None)
