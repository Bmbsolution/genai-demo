"""scorecard_criteria reference table (global, not workspace-scoped)

Revision ID: 0005_scorecard_criteria
Revises: 0004_services
Create Date: 2026-05-27 16:00

"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0005_scorecard_criteria"
down_revision: str | None = "0004_services"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

APP_ROLE = "servicecat_app"


def upgrade() -> None:
    op.create_table(
        "scorecard_criteria",
        sa.Column(
            "id",
            sa.Uuid(),
            server_default=sa.text("gen_random_uuid()"),
            nullable=False,
        ),
        sa.Column("scorecard", sa.Text(), nullable=False),
        sa.Column("criterion_id", sa.Text(), nullable=False),
        sa.Column("title", sa.Text(), nullable=False),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column("default_severity", sa.Text(), nullable=False),
        sa.Column(
            "auto_fixable",
            sa.Boolean(),
            server_default=sa.text("false"),
            nullable=False,
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id", name="pk_scorecard_criteria"),
        sa.UniqueConstraint("criterion_id", name="uq_scorecard_criteria_criterion_id"),
        sa.CheckConstraint(
            "default_severity IN ('critical', 'high', 'medium', 'low')",
            name="ck_scorecard_criteria_default_severity",
        ),
    )
    op.create_index("ix_scorecard_criteria_scorecard", "scorecard_criteria", ["scorecard"])
    # Global reference data (no RLS); the app reads criteria definitions.
    op.execute(f"GRANT SELECT ON scorecard_criteria TO {APP_ROLE}")


def downgrade() -> None:
    op.drop_table("scorecard_criteria")
