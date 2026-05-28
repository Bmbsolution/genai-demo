"""Read access for the workspaces a user belongs to (cross-workspace bootstrap).

This runs without an RLS workspace context (the caller is discovering which
workspaces exist for them), so queries see all of the *user's own* memberships.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from sqlalchemy import select

from servicecat.models import Workspace, WorkspaceMembership

if TYPE_CHECKING:
    import uuid
    from collections.abc import Sequence

    from sqlalchemy import Row
    from sqlalchemy.ext.asyncio import AsyncSession


class WorkspaceRepository:
    """Looks up the workspaces (and the caller's role) a user is a member of."""

    def __init__(self, db: AsyncSession) -> None:
        self._db = db

    async def list_for_user(
        self,
        user_id: uuid.UUID,
    ) -> Sequence[Row[tuple[Workspace, str]]]:
        stmt = (
            select(Workspace, WorkspaceMembership.role)
            .join(WorkspaceMembership, WorkspaceMembership.workspace_id == Workspace.id)
            .where(WorkspaceMembership.user_id == user_id)
            .order_by(Workspace.name)
        )
        result = await self._db.execute(stmt)
        return result.all()
