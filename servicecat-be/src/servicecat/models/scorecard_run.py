"""ScorecardRun — one execution of a scorecard against target services."""

from __future__ import annotations

import enum
import uuid
from datetime import datetime

from sqlalchemy import CheckConstraint, DateTime, ForeignKey, Integer, Text, text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from servicecat.models.base import Base, TimestampMixin, UUIDPrimaryKeyMixin


class ScorecardRunStatus(enum.StrEnum):
    """Lifecycle of a scorecard run."""

    QUEUED = "queued"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"


_STATUS_SQL_VALUES = ", ".join(f"'{status.value}'" for status in ScorecardRunStatus)


class ScorecardRun(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """A queued/running/finished scorecard execution. Workspace-scoped (RLS)."""

    __tablename__ = "scorecard_runs"

    workspace_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("workspaces.id", ondelete="CASCADE"),
        index=True,
    )
    scorecard: Mapped[str] = mapped_column(Text)
    status: Mapped[str] = mapped_column(Text, server_default=text("'queued'"))
    triggered_by: Mapped[uuid.UUID]
    target_service_ids: Mapped[list[str]] = mapped_column(JSONB)
    finding_count: Mapped[int] = mapped_column(Integer, server_default=text("0"))
    error: Mapped[str | None] = mapped_column(Text, default=None)
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), default=None)
    finished_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), default=None)

    __table_args__ = (
        CheckConstraint(f"status IN ({_STATUS_SQL_VALUES})", name="ck_scorecard_runs_status"),
    )
