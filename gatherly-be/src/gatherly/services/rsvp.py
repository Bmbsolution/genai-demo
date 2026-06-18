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
from gatherly.services.email import EmailMessage, get_email_sender

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
        self._email = get_email_sender()

    async def _load(self, invite_token: str) -> tuple[Guest, Event]:
        guest = await self._guests.get_by_token(invite_token)
        if guest is None:
            raise NotFoundError("Invitation not found")
        event = await self._events.get_internal(guest.event_id)
        if event is None:
            raise NotFoundError("Invitation not found")
        return guest, event

    async def _position(self, guest: Guest) -> int | None:
        """The guest's own waitlist spot, or ``None`` if they're not waitlisted."""
        if guest.rsvp_status != RsvpStatus.WAITLISTED.value:
            return None
        return await self._guests.waitlist_position(guest)

    async def view(self, invite_token: str) -> tuple[Guest, Event, int | None]:
        guest, event = await self._load(invite_token)
        return guest, event, await self._position(guest)

    async def respond(
        self,
        invite_token: str,
        payload: RsvpUpdateRequest,
    ) -> tuple[Guest, Event, int | None]:
        guest, event = await self._load(invite_token)
        was_attending = guest.rsvp_status == RsvpStatus.YES.value
        status = payload.rsvp_status

        # If the event is at capacity, a new "yes" lands on the waitlist instead.
        if status is RsvpStatus.YES and event.capacity is not None:
            attending = await self._guests.count_attending(event.id)
            already_counted = 1 if was_attending else 0
            if attending - already_counted >= event.capacity:
                status = RsvpStatus.WAITLISTED

        guest.rsvp_status = status.value
        guest.plus_one = payload.plus_one
        guest.dietary_notes = payload.dietary_notes
        await self._db.flush()

        # A confirmed guest just gave up their seat — promote the next in line.
        if was_attending and status is not RsvpStatus.YES:
            await self._promote_from_waitlist(event)

        await self._db.refresh(guest)
        return guest, event, await self._position(guest)

    async def _promote_from_waitlist(self, event: Event) -> None:
        """Move the longest-waiting guest off the waitlist when a seat frees up.

        Only promotes for capped events that now have room, and emails the
        promoted guest the good news. No-op when nobody is waiting.
        """
        if event.capacity is None:
            return
        if await self._guests.count_attending(event.id) >= event.capacity:
            return
        promoted = await self._guests.oldest_waitlisted(event.id)
        if promoted is None:
            return
        promoted.rsvp_status = RsvpStatus.YES.value
        await self._db.flush()
        await self._email.send(
            EmailMessage(
                to=promoted.email,
                subject=f"You're in! A spot opened up for {event.title}",
                body=(
                    f"Hi {promoted.name}, great news — a spot just opened for "
                    f"{event.title} and you're confirmed off the waitlist."
                ),
            ),
        )
