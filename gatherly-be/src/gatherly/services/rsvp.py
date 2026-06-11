"""Public RSVP logic, keyed by a guest's per-invite token.

The token scopes everything to a single guest: there is no way, through this
service, to read or change any guest other than the token's owner.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from gatherly.errors import NotFoundError
from gatherly.repositories.events import EventRepository
from gatherly.repositories.guests import GuestRepository

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import AsyncSession

    from gatherly.models import Event, Guest, RsvpStatus


class RsvpService:
    """Resolve and update a guest's RSVP from their invite token."""

    def __init__(self, db: AsyncSession) -> None:
        self._db = db
        self._guests = GuestRepository(db)
        self._events = EventRepository(db)

    async def view(self, invite_token: str) -> tuple[Guest, Event]:
        guest = await self._guests.get_by_token(invite_token)
        if guest is None:
            raise NotFoundError("Invitation not found")
        event = await self._events.get_internal(guest.event_id)
        if event is None:
            raise NotFoundError("Invitation not found")
        return guest, event

    async def respond(self, invite_token: str, status: RsvpStatus) -> tuple[Guest, Event]:
        guest, event = await self.view(invite_token)
        guest.rsvp_status = status.value
        await self._db.flush()
        await self._db.refresh(guest)
        return guest, event
