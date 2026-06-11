"""Data access for guests + RSVPs."""

from __future__ import annotations

from typing import TYPE_CHECKING

from sqlalchemy import func, select

from gatherly.models import Guest

if TYPE_CHECKING:
    import uuid
    from collections.abc import Sequence

    from sqlalchemy.ext.asyncio import AsyncSession


class GuestRepository:
    """Reads/writes guests for an event."""

    def __init__(self, db: AsyncSession) -> None:
        self._db = db

    async def add(self, guest: Guest) -> None:
        self._db.add(guest)
        await self._db.flush()

    async def list_for_event(self, event_id: uuid.UUID) -> Sequence[Guest]:
        page = await self._db.scalars(
            select(Guest).where(Guest.event_id == event_id).order_by(Guest.created_at.asc()),
        )
        return page.all()

    async def count_for_event(self, event_id: uuid.UUID) -> int:
        return (
            await self._db.scalar(
                select(func.count()).select_from(Guest).where(Guest.event_id == event_id),
            )
            or 0
        )

    async def get_by_token(self, invite_token: str) -> Guest | None:
        """Resolve a guest by their per-invite secret (the public RSVP key)."""
        result = await self._db.scalar(select(Guest).where(Guest.invite_token == invite_token))
        return result if isinstance(result, Guest) else None
