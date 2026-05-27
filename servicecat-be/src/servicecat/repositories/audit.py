"""Data access for the append-only audit log (workspace-scoped, RLS)."""

from __future__ import annotations

from typing import TYPE_CHECKING

from sqlalchemy import select

from servicecat.models import AuditLog

if TYPE_CHECKING:
    from collections.abc import Sequence

    from sqlalchemy.ext.asyncio import AsyncSession


class AuditLogRepository:
    """Appends and reads audit entries. RLS scopes reads to the active workspace."""

    def __init__(self, db: AsyncSession) -> None:
        self._db = db

    async def record(self, entry: AuditLog) -> None:
        """Append one entry (flushed now; committed with the request)."""
        self._db.add(entry)
        await self._db.flush()

    async def list_for_workspace(
        self,
        *,
        action: str | None = None,
        resource_type: str | None = None,
        limit: int = 50,
    ) -> Sequence[AuditLog]:
        """Return entries in the RLS-active workspace, newest first."""
        stmt = select(AuditLog).order_by(AuditLog.created_at.desc())
        if action is not None:
            stmt = stmt.where(AuditLog.action == action)
        if resource_type is not None:
            stmt = stmt.where(AuditLog.resource_type == resource_type)
        result = await self._db.scalars(stmt.limit(limit))
        return result.all()
