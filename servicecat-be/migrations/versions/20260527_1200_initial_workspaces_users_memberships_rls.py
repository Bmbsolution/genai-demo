"""initial: workspaces, users, workspace_memberships + workspace RLS

Creates the multi-tenant foundation and enforces workspace isolation with
Row-Level Security. Because the bootstrap database user is a superuser (and
superusers/table-owners bypass RLS), the application never queries these
tables directly as that user: migration 0001 also provisions a non-privileged
``servicecat_app`` role, and the app does ``SET LOCAL ROLE servicecat_app``
per request (see servicecat.db.set_workspace_context). FORCE ROW LEVEL
SECURITY is set as defence-in-depth so the policy applies even to the owner.

``users`` is a global identity table (a user may join many workspaces) and is
intentionally NOT workspace-scoped; isolation is enforced on the membership.

Revision ID: 0001_init_rls
Revises:
Create Date: 2026-05-27 12:00

"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0001_init_rls"
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

APP_ROLE = "servicecat_app"
SCOPED_TABLES = ("workspaces", "workspace_memberships")
# Per-table privileges for the app role. A workspace is provisioned/deleted via
# a privileged path (you cannot be "in" a workspace that does not exist yet), so
# the app role gets only SELECT/UPDATE on workspaces — never INSERT/DELETE.
TABLE_GRANTS = {
    "workspaces": "SELECT, UPDATE",
    "users": "SELECT, INSERT, UPDATE",
    "workspace_memberships": "SELECT, INSERT, UPDATE, DELETE",
}


def _timestamps() -> tuple[sa.Column[sa.DateTime], sa.Column[sa.DateTime]]:
    return (
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
    )


def upgrade() -> None:
    op.create_table(
        "workspaces",
        sa.Column(
            "id",
            sa.Uuid(),
            server_default=sa.text("gen_random_uuid()"),
            nullable=False,
        ),
        sa.Column("name", sa.Text(), nullable=False),
        sa.Column("slug", sa.Text(), nullable=False),
        *_timestamps(),
        sa.PrimaryKeyConstraint("id", name="pk_workspaces"),
        sa.UniqueConstraint("slug", name="uq_workspaces_slug"),
    )
    op.create_table(
        "users",
        sa.Column(
            "id",
            sa.Uuid(),
            server_default=sa.text("gen_random_uuid()"),
            nullable=False,
        ),
        sa.Column("email", sa.Text(), nullable=False),
        sa.Column("full_name", sa.Text(), nullable=False),
        sa.Column(
            "is_active",
            sa.Boolean(),
            server_default=sa.text("true"),
            nullable=False,
        ),
        *_timestamps(),
        sa.PrimaryKeyConstraint("id", name="pk_users"),
        sa.UniqueConstraint("email", name="uq_users_email"),
    )
    op.create_table(
        "workspace_memberships",
        sa.Column(
            "id",
            sa.Uuid(),
            server_default=sa.text("gen_random_uuid()"),
            nullable=False,
        ),
        sa.Column("workspace_id", sa.Uuid(), nullable=False),
        sa.Column("user_id", sa.Uuid(), nullable=False),
        sa.Column("role", sa.Text(), nullable=False),
        *_timestamps(),
        sa.PrimaryKeyConstraint("id", name="pk_workspace_memberships"),
        sa.ForeignKeyConstraint(
            ["workspace_id"],
            ["workspaces.id"],
            name="fk_workspace_memberships_workspace_id_workspaces",
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["user_id"],
            ["users.id"],
            name="fk_workspace_memberships_user_id_users",
            ondelete="CASCADE",
        ),
        sa.UniqueConstraint(
            "workspace_id",
            "user_id",
            name="uq_workspace_memberships_workspace_id_user_id",
        ),
        sa.CheckConstraint(
            "role IN ('admin', 'maintainer', 'viewer')",
            name="ck_workspace_memberships_role",
        ),
    )
    op.create_index(
        "ix_workspace_memberships_workspace_id",
        "workspace_memberships",
        ["workspace_id"],
    )
    op.create_index(
        "ix_workspace_memberships_user_id",
        "workspace_memberships",
        ["user_id"],
    )

    _provision_app_role()
    _enable_rls()


def downgrade() -> None:
    op.drop_table("workspace_memberships")
    op.drop_table("users")
    op.drop_table("workspaces")
    # The app role is cluster-global and shared with the test database, so it is
    # not dropped here; only this database's grants and the role membership are
    # revoked. (Dropping the tables already removed their table-level grants.)
    op.execute(
        f"DO $$ BEGIN "
        f"IF EXISTS (SELECT 1 FROM pg_roles WHERE rolname = '{APP_ROLE}') THEN "
        f"REVOKE USAGE ON SCHEMA public FROM {APP_ROLE}; "
        f"REVOKE {APP_ROLE} FROM CURRENT_USER; "
        f"END IF; END $$;"
    )


def _provision_app_role() -> None:
    op.execute(
        f"DO $$ BEGIN "
        f"IF NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = '{APP_ROLE}') THEN "
        f"CREATE ROLE {APP_ROLE} NOLOGIN NOSUPERUSER NOBYPASSRLS "
        f"NOCREATEDB NOCREATEROLE; "
        f"END IF; END $$;"
    )
    # Let the connecting/login role assume the app role even after it is later
    # stripped of SUPERUSER (SET ROLE needs role membership when not a superuser).
    op.execute(f"GRANT {APP_ROLE} TO CURRENT_USER")
    op.execute(f"GRANT USAGE ON SCHEMA public TO {APP_ROLE}")
    for table, privileges in TABLE_GRANTS.items():
        op.execute(f"GRANT {privileges} ON {table} TO {APP_ROLE}")


def _enable_rls() -> None:
    """Enable + force RLS and a workspace-isolation policy on scoped tables."""
    for table in SCOPED_TABLES:
        column = "id" if table == "workspaces" else "workspace_id"
        # NULLIF(..., '') so an unset OR blank GUC yields NULL -> deny (never an
        # "invalid uuid" error). current_setting(..., true) = missing_ok.
        predicate = (
            f"{column} = NULLIF(current_setting('app.workspace_id', true), '')::uuid"
        )
        op.execute(f"ALTER TABLE {table} ENABLE ROW LEVEL SECURITY")
        op.execute(f"ALTER TABLE {table} FORCE ROW LEVEL SECURITY")
        op.execute(
            f"CREATE POLICY workspace_isolation ON {table} "
            f"USING ({predicate}) WITH CHECK ({predicate})"
        )
