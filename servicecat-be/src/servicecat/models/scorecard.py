"""ScorecardCriterion — the definition of one check a scorecard performs.

Global reference data (like users, this is not workspace-scoped): the criteria
for a scorecard type are the same across every workspace. Rows are seeded by
each concrete scorecard's migration.
"""

from __future__ import annotations

from sqlalchemy import CheckConstraint, Text, text
from sqlalchemy.orm import Mapped, mapped_column

from servicecat.models.base import Base, TimestampMixin, UUIDPrimaryKeyMixin


class ScorecardCriterion(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """One criterion (e.g. ``doc.readme_present``) belonging to a scorecard."""

    __tablename__ = "scorecard_criteria"

    scorecard: Mapped[str] = mapped_column(Text)
    criterion_id: Mapped[str] = mapped_column(Text, unique=True)
    title: Mapped[str] = mapped_column(Text)
    description: Mapped[str] = mapped_column(Text)
    default_severity: Mapped[str] = mapped_column(Text)
    auto_fixable: Mapped[bool] = mapped_column(server_default=text("false"))

    __table_args__ = (
        CheckConstraint(
            "default_severity IN ('critical', 'high', 'medium', 'low')",
            name="ck_scorecard_criteria_default_severity",
        ),
    )
