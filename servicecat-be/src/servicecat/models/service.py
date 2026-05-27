"""Service — a registered catalog service (workspace-scoped, soft-deletable)."""

from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import CheckConstraint, DateTime, ForeignKey, Integer, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from servicecat.models.base import Base, TimestampMixin, UUIDPrimaryKeyMixin


class Service(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """A service in the catalog. Soft-deleted by setting ``deleted_at``."""

    __tablename__ = "services"

    workspace_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("workspaces.id", ondelete="CASCADE"),
        index=True,
    )
    name: Mapped[str] = mapped_column(Text)
    description: Mapped[str | None] = mapped_column(Text, default=None)
    repo_url: Mapped[str] = mapped_column(Text)
    tier: Mapped[int] = mapped_column(Integer)
    # FK to a future teams table; kept as a bare UUID until that table exists.
    owner_team_id: Mapped[uuid.UUID | None] = mapped_column(default=None)
    deleted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), default=None)

    __table_args__ = (
        UniqueConstraint("workspace_id", "name", name="uq_services_workspace_id_name"),
        CheckConstraint("tier BETWEEN 1 AND 3", name="ck_services_tier"),
    )
