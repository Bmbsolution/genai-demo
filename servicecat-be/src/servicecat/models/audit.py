"""AuditLog — an append-only record of state-changing actions (and PII reads)."""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any

from sqlalchemy import DateTime, Text, func
from sqlalchemy.dialects.postgresql import INET, JSONB
from sqlalchemy.orm import Mapped, mapped_column

from servicecat.models.base import Base, UUIDPrimaryKeyMixin


class AuditLog(UUIDPrimaryKeyMixin, Base):
    """Immutable audit entry. No ``updated_at`` — rows are never modified.

    Append-only is enforced in the database (BEFORE UPDATE/DELETE triggers),
    not just by convention. ``actor_id``/``resource_id`` are plain UUIDs (no FK)
    so the log never blocks or cascades with the entities it records.
    """

    __tablename__ = "audit_logs"

    workspace_id: Mapped[uuid.UUID] = mapped_column(index=True)
    actor_id: Mapped[uuid.UUID]
    action: Mapped[str] = mapped_column(Text)
    resource_type: Mapped[str] = mapped_column(Text)
    resource_id: Mapped[uuid.UUID | None] = mapped_column(default=None)
    payload: Mapped[dict[str, Any] | None] = mapped_column(JSONB, default=None)
    ip: Mapped[str | None] = mapped_column(INET, default=None)
    user_agent: Mapped[str | None] = mapped_column(Text, default=None)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
    )
