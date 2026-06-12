"""Data access for guests + RSVPs."""

from __future__ import annotations

from typing import TYPE_CHECKING

from sqlalchemy import func, or_, select

from gatherly.models import Guest, RsvpStatus

if TYPE_CHECKING:
    import uuid
    from collections.abc import Iterable, Sequence

    from sqlalchemy.ext.asyncio import AsyncSession


class GuestRepository:
    """Reads/writes guests for an event."""

    def __init__(self, db: AsyncSession) -> None:
        self._db = db

    async def add(self, guest: Guest) -> None:
        self._db.add(guest)
        await self._db.flush()

    async def add_many(self, guests: Iterable[Guest]) -> None:
        self._db.add_all(list(guests))
        await self._db.flush()

    async def list_for_event(
        self,
        event_id: uuid.UUID,
        *,
        status: str | None = None,
        query: str | None = None,
    ) -> Sequence[Guest]:
        """Guests for an event, optionally filtered by RSVP ``status`` and a
        free-text ``query`` over name/email (case-insensitive substring)."""
        stmt = select(Guest).where(Guest.event_id == event_id)
        if status is not None:
            stmt = stmt.where(Guest.rsvp_status == status)
        if query:
            like = f"%{query.lower()}%"
            stmt = stmt.where(
                or_(
                    func.lower(Guest.name).like(like),
                    func.lower(Guest.email).like(like),
                ),
            )
        page = await self._db.scalars(stmt.order_by(Guest.created_at.asc()))
        return page.all()

    async def get_for_event(self, event_id: uuid.UUID, guest_id: uuid.UUID) -> Guest | None:
        """One guest, scoped to its event (so a stray id can't cross events)."""
        result = await self._db.scalar(
            select(Guest).where(Guest.id == guest_id, Guest.event_id == event_id),
        )
        return result if isinstance(result, Guest) else None

    async def existing_emails(self, event_id: uuid.UUID) -> set[str]:
        """Lower-cased emails already on the event (for import de-duplication)."""
        rows = await self._db.scalars(select(Guest.email).where(Guest.event_id == event_id))
        return {email.lower() for email in rows.all()}

    async def count_checked_in(self, event_id: uuid.UUID) -> int:
        return (
            await self._db.scalar(
                select(func.count())
                .select_from(Guest)
                .where(Guest.event_id == event_id, Guest.checked_in_at.is_not(None)),
            )
            or 0
        )

    async def count_for_event(self, event_id: uuid.UUID) -> int:
        return (
            await self._db.scalar(
                select(func.count()).select_from(Guest).where(Guest.event_id == event_id),
            )
            or 0
        )

    async def count_attending(self, event_id: uuid.UUID) -> int:
        """Number of guests with a confirmed 'yes' (for capacity / waitlist)."""
        return (
            await self._db.scalar(
                select(func.count())
                .select_from(Guest)
                .where(Guest.event_id == event_id, Guest.rsvp_status == RsvpStatus.YES.value),
            )
            or 0
        )

    async def oldest_waitlisted(self, event_id: uuid.UUID) -> Guest | None:
        """The longest-waiting guest on the waitlist — promoted first (FIFO)."""
        result = await self._db.scalar(
            select(Guest)
            .where(
                Guest.event_id == event_id,
                Guest.rsvp_status == RsvpStatus.WAITLISTED.value,
            )
            .order_by(Guest.created_at.asc())
            .limit(1),
        )
        return result if isinstance(result, Guest) else None

    async def get_by_token(self, invite_token: str) -> Guest | None:
        """Resolve a guest by their per-invite secret (the public RSVP key)."""
        result = await self._db.scalar(select(Guest).where(Guest.invite_token == invite_token))
        return result if isinstance(result, Guest) else None
