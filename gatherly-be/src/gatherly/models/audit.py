"""AuditLog — append-only record of host actions (S5)."""

from __future__ import annotations

import datetime as dt
import uuid

from sqlalchemy import DateTime, String, Text, Uuid
from sqlalchemy.orm import Mapped, mapped_column

from gatherly.models.base import Base, UUIDPrimaryKeyMixin, _utcnow


class AuditLog(UUIDPrimaryKeyMixin, Base):
    """One immutable entry per state-changing action. Append-only: the
    repository exposes no update or delete."""

    __tablename__ = "audit_logs"

    actor_id: Mapped[uuid.UUID] = mapped_column(Uuid, index=True)
    action: Mapped[str] = mapped_column(String(100))
    resource_type: Mapped[str] = mapped_column(String(50))
    resource_id: Mapped[uuid.UUID | None] = mapped_column(Uuid, default=None)
    ip: Mapped[str | None] = mapped_column(String(64), default=None)
    user_agent: Mapped[str | None] = mapped_column(Text, default=None)
    created_at: Mapped[dt.datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)
