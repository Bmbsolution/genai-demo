"""Finding — a persisted scorecard finding produced by a run (workspace-scoped).

Distinct from servicecat.scorecards.base.Finding, which is the transient
dataclass a scorecard yields during evaluation; this is the stored record.
"""

from __future__ import annotations

import uuid
from typing import Any

from sqlalchemy import ForeignKey, Text, text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from servicecat.models.base import Base, TimestampMixin, UUIDPrimaryKeyMixin


class Finding(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """A failed criterion recorded against a service in a scorecard run."""

    __tablename__ = "findings"

    workspace_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("workspaces.id", ondelete="CASCADE"),
        index=True,
    )
    run_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("scorecard_runs.id", ondelete="CASCADE"),
        index=True,
    )
    service_id: Mapped[uuid.UUID]
    criterion_id: Mapped[str] = mapped_column(Text)
    severity: Mapped[str] = mapped_column(Text)
    remediation: Mapped[str] = mapped_column(Text)
    evidence: Mapped[dict[str, Any] | None] = mapped_column(JSONB, default=None)
    auto_fixable: Mapped[bool] = mapped_column(server_default=text("false"))
