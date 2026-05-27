"""service_dependencies (workspace-isolated dependency edges)

Revision ID: 0008_service_deps
Revises: 0007_runs_findings
Create Date: 2026-05-27 19:00

"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0008_service_deps"
down_revision: str | None = "0007_runs_findings"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

APP_ROLE = "servicecat_app"
_PREDICATE = "workspace_id = NULLIF(current_setting('app.workspace_id', true), '')::uuid"


def upgrade() -> None:
    op.create_table(
        "service_dependencies",
        sa.Column("id", sa.Uuid(), server_default=sa.text("gen_random_uuid()"), nullable=False),
        sa.Column("workspace_id", sa.Uuid(), nullable=False),
        sa.Column("service_id", sa.Uuid(), nullable=False),
        sa.Column("depends_on_service_id", sa.Uuid(), nullable=False),
        sa.Column("criticality", sa.Text(), nullable=False),
        sa.Column("direction", sa.Text(), nullable=False),
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
        sa.PrimaryKeyConstraint("id", name="pk_service_dependencies"),
        sa.ForeignKeyConstraint(
            ["workspace_id"],
            ["workspaces.id"],
            name="fk_service_dependencies_workspace_id_workspaces",
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["service_id"],
            ["services.id"],
            name="fk_service_dependencies_service_id_services",
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["depends_on_service_id"],
            ["services.id"],
            name="fk_service_dependencies_depends_on_service_id_services",
            ondelete="CASCADE",
        ),
        sa.UniqueConstraint(
            "service_id",
            "depends_on_service_id",
            name="uq_service_dependencies_edge",
        ),
        sa.CheckConstraint(
            "service_id <> depends_on_service_id",
            name="ck_service_dependencies_no_self",
        ),
        sa.CheckConstraint(
            "criticality IN ('hard', 'soft')",
            name="ck_service_dependencies_criticality",
        ),
        sa.CheckConstraint(
            "direction IN ('consumes', 'produces')",
            name="ck_service_dependencies_direction",
        ),
    )
    op.create_index(
        "ix_service_dependencies_workspace_id",
        "service_dependencies",
        ["workspace_id"],
    )
    op.create_index(
        "ix_service_dependencies_service_id",
        "service_dependencies",
        ["service_id"],
    )
    op.create_index(
        "ix_service_dependencies_depends_on_service_id",
        "service_dependencies",
        ["depends_on_service_id"],
    )

    op.execute("ALTER TABLE service_dependencies ENABLE ROW LEVEL SECURITY")
    op.execute("ALTER TABLE service_dependencies FORCE ROW LEVEL SECURITY")
    op.execute(
        f"CREATE POLICY workspace_isolation ON service_dependencies "
        f"USING ({_PREDICATE}) WITH CHECK ({_PREDICATE})"
    )
    op.execute(f"GRANT SELECT, INSERT, DELETE ON service_dependencies TO {APP_ROLE}")


def downgrade() -> None:
    op.drop_table("service_dependencies")
