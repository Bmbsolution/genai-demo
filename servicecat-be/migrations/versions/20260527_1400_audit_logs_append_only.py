"""audit_logs: append-only, workspace-isolated audit trail

Creates the audit_logs table with workspace RLS and DB-enforced immutability:
BEFORE UPDATE/DELETE triggers raise, so no role (not even a superuser, who
bypasses RLS but not triggers) can alter or remove an entry. The app role is
granted SELECT + INSERT only.

Revision ID: 0003_audit_logs
Revises: 0002_user_password
Create Date: 2026-05-27 14:00

"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0003_audit_logs"
down_revision: str | None = "0002_user_password"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

APP_ROLE = "servicecat_app"
_PREDICATE = "workspace_id = NULLIF(current_setting('app.workspace_id', true), '')::uuid"
_IMMUTABLE_FN = "servicecat_audit_logs_immutable"


def upgrade() -> None:
    op.create_table(
        "audit_logs",
        sa.Column(
            "id",
            sa.Uuid(),
            server_default=sa.text("gen_random_uuid()"),
            nullable=False,
        ),
        sa.Column("workspace_id", sa.Uuid(), nullable=False),
        sa.Column("actor_id", sa.Uuid(), nullable=False),
        sa.Column("action", sa.Text(), nullable=False),
        sa.Column("resource_type", sa.Text(), nullable=False),
        sa.Column("resource_id", sa.Uuid(), nullable=True),
        sa.Column("payload", postgresql.JSONB(), nullable=True),
        sa.Column("ip", postgresql.INET(), nullable=True),
        sa.Column("user_agent", sa.Text(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id", name="pk_audit_logs"),
    )
    op.create_index("ix_audit_logs_workspace_id", "audit_logs", ["workspace_id"])
    op.create_index(
        "ix_audit_logs_workspace_id_created_at",
        "audit_logs",
        ["workspace_id", "created_at"],
    )

    # Workspace isolation (read + insert).
    op.execute("ALTER TABLE audit_logs ENABLE ROW LEVEL SECURITY")
    op.execute("ALTER TABLE audit_logs FORCE ROW LEVEL SECURITY")
    op.execute(
        f"CREATE POLICY workspace_isolation ON audit_logs "
        f"USING ({_PREDICATE}) WITH CHECK ({_PREDICATE})"
    )
    op.execute(f"GRANT SELECT, INSERT ON audit_logs TO {APP_ROLE}")

    # Append-only: block UPDATE and DELETE for everyone (triggers are not
    # bypassed by superusers, unlike RLS).
    op.execute(
        f"CREATE OR REPLACE FUNCTION {_IMMUTABLE_FN}() RETURNS trigger "
        f"LANGUAGE plpgsql AS $$ BEGIN "
        f"RAISE EXCEPTION 'audit_logs is append-only (% blocked)', TG_OP; "
        f"END; $$;"
    )
    op.execute(
        f"CREATE TRIGGER audit_logs_block_update BEFORE UPDATE ON audit_logs "
        f"FOR EACH ROW EXECUTE FUNCTION {_IMMUTABLE_FN}()"
    )
    op.execute(
        f"CREATE TRIGGER audit_logs_block_delete BEFORE DELETE ON audit_logs "
        f"FOR EACH ROW EXECUTE FUNCTION {_IMMUTABLE_FN}()"
    )


def downgrade() -> None:
    op.execute("DROP TRIGGER IF EXISTS audit_logs_block_delete ON audit_logs")
    op.execute("DROP TRIGGER IF EXISTS audit_logs_block_update ON audit_logs")
    op.drop_table("audit_logs")
    op.execute(f"DROP FUNCTION IF EXISTS {_IMMUTABLE_FN}()")
