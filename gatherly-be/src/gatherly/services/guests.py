"""Business logic for inviting guests and listing an event's guest list.

Every method first proves the caller owns the event (via EventService.get,
which raises 404 otherwise) — that ownership check is the privacy boundary.
"""

from __future__ import annotations

import secrets
from typing import TYPE_CHECKING

from gatherly.models import Guest
from gatherly.repositories.guests import GuestRepository
from gatherly.services.events import EventService

if TYPE_CHECKING:
    import uuid
    from collections.abc import Sequence

    from sqlalchemy.ext.asyncio import AsyncSession

    from gatherly.schemas.guest import GuestCreateRequest


class GuestService:
    """Invite guests to, and list guests of, an owned event."""

    def __init__(self, db: AsyncSession) -> None:
        self._guests = GuestRepository(db)
        self._events = EventService(db)

    async def invite(
        self,
        *,
        event_id: uuid.UUID,
        owner_id: uuid.UUID,
        payload: GuestCreateRequest,
    ) -> Guest:
        await self._events.get(event_id, owner_id)  # 404 if not the owner's event
        guest = Guest(
            event_id=event_id,
            name=payload.name,
            email=payload.email,
            invite_token=secrets.token_urlsafe(24),
        )
        await self._guests.add(guest)
        return guest

    async def list_for_event(
        self,
        *,
        event_id: uuid.UUID,
        owner_id: uuid.UUID,
    ) -> Sequence[Guest]:
        await self._events.get(event_id, owner_id)  # 404 if not the owner's event
        return await self._guests.list_for_event(event_id)
