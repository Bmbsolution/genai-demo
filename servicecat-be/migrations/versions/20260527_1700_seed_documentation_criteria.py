"""seed the documentation scorecard's criteria (data-only)

Revision ID: 0006_seed_doc_criteria
Revises: 0005_scorecard_criteria
Create Date: 2026-05-27 17:00

"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0006_seed_doc_criteria"
down_revision: str | None = "0005_scorecard_criteria"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

_SCORECARD = "documentation"
_CRITERIA = (
    ("doc.readme_present", "README present", "A README.md exists at the repo root.", "high", True),
    ("doc.openapi_spec", "OpenAPI spec", "An OpenAPI document is committed or served.", "medium", False),
    ("doc.runbook", "Runbook", "A RUNBOOK.md (or docs/runbook.md) exists.", "medium", False),
    ("doc.changelog", "Changelog", "A CHANGELOG.md exists or semver tags are published.", "low", True),
    ("doc.codeowners", "CODEOWNERS", "A .github/CODEOWNERS file exists.", "medium", True),
)


def _criteria_table() -> sa.Table:
    return sa.table(
        "scorecard_criteria",
        sa.column("scorecard", sa.Text),
        sa.column("criterion_id", sa.Text),
        sa.column("title", sa.Text),
        sa.column("description", sa.Text),
        sa.column("default_severity", sa.Text),
        sa.column("auto_fixable", sa.Boolean),
    )


def upgrade() -> None:
    op.bulk_insert(
        _criteria_table(),
        [
            {
                "scorecard": _SCORECARD,
                "criterion_id": criterion_id,
                "title": title,
                "description": description,
                "default_severity": severity,
                "auto_fixable": auto_fixable,
            }
            for criterion_id, title, description, severity, auto_fixable in _CRITERIA
        ],
    )


def downgrade() -> None:
    op.execute("DELETE FROM scorecard_criteria WHERE scorecard = 'documentation'")
