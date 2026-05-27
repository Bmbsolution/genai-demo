"""SQLAlchemy ORM models.

Import every model module here so ``Base.metadata`` is fully populated before
Alembic compares or autogenerates migrations. Model modules are added by their
owning backlog issues (#1 workspaces/users, #3 teams, #4 services, ...).
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from servicecat.models.audit import AuditLog
from servicecat.models.base import Base
from servicecat.models.membership import WorkspaceMembership, WorkspaceRole
from servicecat.models.scorecard import ScorecardCriterion
from servicecat.models.service import Service
from servicecat.models.user import User
from servicecat.models.workspace import Workspace

if TYPE_CHECKING:
    from sqlalchemy import MetaData


def metadata_for_migrations() -> MetaData:
    """Return the fully-populated metadata object for Alembic."""
    return Base.metadata


__all__ = [
    "AuditLog",
    "Base",
    "ScorecardCriterion",
    "Service",
    "User",
    "Workspace",
    "WorkspaceMembership",
    "WorkspaceRole",
    "metadata_for_migrations",
]
