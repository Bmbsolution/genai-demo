"""Business logic for events. Routers stay thin; this layer raises typed
domain errors that routers translate to HTTP status codes."""

from __future__ import annotations

import datetime as dt
from typing import TYPE_CHECKING

from gatherly.errors import OwnershipError
from gatherly.models import Event
from gatherly.repositories.events import EventRepository

if TYPE_CHECKING:
    import uuid
    from collections.abc import Sequence

    from sqlalchemy.ext.asyncio import AsyncSession

    from gatherly.schemas.event import EventCreateRequest, EventUpdateRequest


class EventService:
    """Create, read, update, and soft-delete a host's own events."""

    def __init__(self, db: AsyncSession) -> None:
        self._db = db
        self._repo = EventRepository(db)

    async def create(self, *, owner_id: uuid.UUID, payload: EventCreateRequest) -> Event:
        event = Event(
            owner_id=owner_id,
            title=payload.title,
            description=payload.description,
            starts_at=payload.starts_at,
            location=payload.location,
            capacity=payload.capacity,
        )
        await self._repo.add(event)
        return event

    async def get(self, event_id: uuid.UUID, owner_id: uuid.UUID) -> Event:
        """Return the host's own event, or raise 404 (never leak existence)."""
        event = await self._repo.get_for_owner(event_id, owner_id)
        if event is None:
            raise OwnershipError("Event not found")
        return event

    async def list_for_owner(
        self,
        owner_id: uuid.UUID,
        *,
        limit: int = 50,
        offset: int = 0,
    ) -> tuple[Sequence[Event], int]:
        return await self._repo.list_for_owner(owner_id, limit=limit, offset=offset)

    async def update(
        self,
        event_id: uuid.UUID,
        owner_id: uuid.UUID,
        payload: EventUpdateRequest,
    ) -> Event:
        event = await self.get(event_id, owner_id)
        for field, value in payload.model_dump(exclude_unset=True).items():
            setattr(event, field, value)
        await self._db.flush()
        await self._db.refresh(event)
        return event

    async def soft_delete(self, event_id: uuid.UUID, owner_id: uuid.UUID) -> None:
        event = await self.get(event_id, owner_id)
        event.deleted_at = dt.datetime.now(dt.UTC)
        await self._db.flush()
