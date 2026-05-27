"""Data access for workspace memberships (workspace-scoped, RLS-protected)."""

from __future__ import annotations

from typing import TYPE_CHECKING

from sqlalchemy import select

from servicecat.models import WorkspaceMembership

if TYPE_CHECKING:
    import uuid

    from sqlalchemy.ext.asyncio import AsyncSession


class MembershipRepository:
    """Reads memberships. RLS scopes every query to the active workspace."""

    def __init__(self, db: AsyncSession) -> None:
        self._db = db

    async def get_role(self, user_id: uuid.UUID) -> str | None:
        """Return ``user_id``'s role in the RLS-active workspace, or None.

        Relies on the workspace RLS context being set first (so the row is only
        visible when the user belongs to the active workspace).
        """
        role = await self._db.scalar(
            select(WorkspaceMembership.role).where(WorkspaceMembership.user_id == user_id),
        )
        return str(role) if role is not None else None
