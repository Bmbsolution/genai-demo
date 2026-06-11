"""Data access for events. Owner-scoped reads enforce tenant isolation (S2)."""

from __future__ import annotations

from typing import TYPE_CHECKING

from sqlalchemy import func, select

from gatherly.models import Event

if TYPE_CHECKING:
    import uuid
    from collections.abc import Sequence

    from sqlalchemy.ext.asyncio import AsyncSession


class EventRepository:
    """Reads/writes events, scoping every host-facing read to the owner."""

    def __init__(self, db: AsyncSession) -> None:
        self._db = db

    async def add(self, event: Event) -> None:
        self._db.add(event)
        await self._db.flush()

    async def get_for_owner(self, event_id: uuid.UUID, owner_id: uuid.UUID) -> Event | None:
        """Return the event only if it belongs to ``owner_id`` and is live.

        This owner filter is the tenant-isolation boundary (S2): drop it and any
        host could read any other host's event.
        """
        result = await self._db.scalar(
            select(Event).where(
                Event.id == event_id,
                Event.owner_id == owner_id,
                Event.deleted_at.is_(None),
            ),
        )
        return result if isinstance(result, Event) else None

    async def get_internal(self, event_id: uuid.UUID) -> Event | None:
        """Fetch an event without an owner filter — for internal/token paths
        (e.g. the public RSVP view) where ownership is enforced elsewhere."""
        result = await self._db.scalar(
            select(Event).where(Event.id == event_id, Event.deleted_at.is_(None)),
        )
        return result if isinstance(result, Event) else None

    async def list_for_owner(
        self,
        owner_id: uuid.UUID,
        *,
        limit: int = 50,
        offset: int = 0,
    ) -> tuple[Sequence[Event], int]:
        """Return (page of the owner's active events, total)."""
        base = select(Event).where(Event.owner_id == owner_id, Event.deleted_at.is_(None))
        total = await self._db.scalar(select(func.count()).select_from(base.subquery())) or 0
        page = await self._db.scalars(
            base.order_by(Event.starts_at.asc()).limit(limit).offset(offset),
        )
        return page.all(), total
