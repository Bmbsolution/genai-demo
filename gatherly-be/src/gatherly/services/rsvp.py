"""Public RSVP logic, keyed by a guest's per-invite token.

The token scopes everything to a single guest: there is no way, through this
service, to read or change any guest other than the token's owner.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from gatherly.errors import NotFoundError
from gatherly.models import RsvpStatus
from gatherly.repositories.events import EventRepository
from gatherly.repositories.guests import GuestRepository

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import AsyncSession

    from gatherly.models import Event, Guest
    from gatherly.schemas.rsvp import RsvpUpdateRequest


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

    async def respond(self, invite_token: str, payload: RsvpUpdateRequest) -> tuple[Guest, Event]:
        guest, event = await self.view(invite_token)
        status = payload.rsvp_status

        # If the event is at capacity, a new "yes" lands on the waitlist instead.
        if status is RsvpStatus.YES and event.capacity is not None:
            attending = await self._guests.count_attending(event.id)
            already_counted = 1 if guest.rsvp_status == RsvpStatus.YES.value else 0
            if attending - already_counted >= event.capacity:
                status = RsvpStatus.WAITLISTED

        guest.rsvp_status = status.value
        guest.plus_one = payload.plus_one
        guest.dietary_notes = payload.dietary_notes
        await self._db.flush()
        await self._db.refresh(guest)
        return guest, event
