"""SQLAlchemy ORM models.

Import every model module here so ``Base.metadata`` is fully populated before
Alembic compares or autogenerates migrations. Model modules are added by their
owning backlog issues (#1 workspaces/users, #3 teams, #4 services, ...).
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from servicecat.models.base import Base

if TYPE_CHECKING:
    from sqlalchemy import MetaData


def metadata_for_migrations() -> MetaData:
    """Return the fully-populated metadata object for Alembic."""
    return Base.metadata


__all__ = ["Base", "metadata_for_migrations"]
