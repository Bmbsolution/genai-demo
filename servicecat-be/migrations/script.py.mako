"""${message}

Revision ID: ${up_revision}
Revises: ${down_revision | comma,n}
Create Date: ${create_date}

"""

from __future__ import annotations

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa
${imports if imports else ""}

# --- Row-Level Security pattern (delete if this migration adds no scoped table) ---
# Every new workspace-scoped table MUST be isolated. After create_table(<t>):
#
#   op.execute("ALTER TABLE <t> ENABLE ROW LEVEL SECURITY")
#   op.execute("ALTER TABLE <t> FORCE ROW LEVEL SECURITY")
#   _p = "workspace_id = NULLIF(current_setting('app.workspace_id', true), '')::uuid"
#   op.execute(f"CREATE POLICY workspace_isolation ON <t> USING ({_p}) WITH CHECK ({_p})")
#   op.execute("GRANT SELECT, INSERT, UPDATE, DELETE ON <t> TO servicecat_app")
#
# Mirror the teardown in downgrade() (dropping the table drops its policy).
# Canonical example: 0001_init_rls. Requests enter the context via
# servicecat.db.set_workspace_context (SET LOCAL ROLE servicecat_app + GUC).

# revision identifiers, used by Alembic.
revision: str = ${repr(up_revision)}
down_revision: str | None = ${repr(down_revision)}
branch_labels: str | Sequence[str] | None = ${repr(branch_labels)}
depends_on: str | Sequence[str] | None = ${repr(depends_on)}


def upgrade() -> None:
    ${upgrades if upgrades else "pass"}


def downgrade() -> None:
    ${downgrades if downgrades else "pass"}
