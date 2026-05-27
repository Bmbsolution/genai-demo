"""add users.hashed_password

Revision ID: 0002_user_password
Revises: 0001_init_rls
Create Date: 2026-05-27 13:00

"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0002_user_password"
down_revision: str | None = "0001_init_rls"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column("users", sa.Column("hashed_password", sa.Text(), nullable=True))


def downgrade() -> None:
    op.drop_column("users", "hashed_password")
