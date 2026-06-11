"""Business logic for guest operations: invite, list/filter, CSV import/export,
door check-in, and pending-guest reminders.

Every method first proves the caller owns the event (via EventService.get,
which raises 404 otherwise) — that ownership check is the privacy boundary.
"""

from __future__ import annotations

import csv
import datetime as dt
import io
import secrets
from dataclasses import dataclass
from typing import TYPE_CHECKING

from pydantic import EmailStr, TypeAdapter, ValidationError

from gatherly.errors import OwnershipError
from gatherly.models import Guest, RsvpStatus
from gatherly.repositories.guests import GuestRepository
from gatherly.services.billing import FEATURE_IMPORT, FEATURE_REMINDERS, PlanService
from gatherly.services.email import EmailMessage, get_email_sender
from gatherly.services.events import EventService

if TYPE_CHECKING:
    import uuid
    from collections.abc import Sequence

    from sqlalchemy.ext.asyncio import AsyncSession

    from gatherly.models import User
    from gatherly.schemas.guest import GuestCreateRequest

_email_adapter: TypeAdapter[str] = TypeAdapter(EmailStr)
_MAX_IMPORT_ROWS = 1000
_MIN_CSV_COLUMNS = 2


@dataclass(frozen=True, slots=True)
class ImportResult:
    """Outcome of a CSV import."""

    created: int
    skipped_duplicate: int
    skipped_invalid: int
    errors: list[str]


class GuestService:
    """Invite, list, import, export, check in, and remind an owned event's guests."""

    def __init__(self, db: AsyncSession) -> None:
        self._guests = GuestRepository(db)
        self._events = EventService(db)
        self._plan = PlanService(db)
        self._email = get_email_sender()

    async def invite(
        self,
        *,
        event_id: uuid.UUID,
        user: User,
        payload: GuestCreateRequest,
    ) -> Guest:
        await self._events.get(event_id, user.id)  # 404 if not the owner's event
        await self._plan.assert_can_add_guests(user, event_id, 1)
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
        status: str | None = None,
        query: str | None = None,
    ) -> Sequence[Guest]:
        await self._events.get(event_id, owner_id)  # 404 if not the owner's event
        return await self._guests.list_for_event(event_id, status=status, query=query)

    async def set_check_in(
        self,
        *,
        event_id: uuid.UUID,
        guest_id: uuid.UUID,
        owner_id: uuid.UUID,
        checked_in: bool,
    ) -> Guest:
        await self._events.get(event_id, owner_id)  # 404 if not the owner's event
        guest = await self._guests.get_for_event(event_id, guest_id)
        if guest is None:
            raise OwnershipError("Guest not found")
        guest.checked_in_at = dt.datetime.now(dt.UTC) if checked_in else None
        return guest

    async def import_csv(
        self,
        *,
        event_id: uuid.UUID,
        user: User,
        csv_text: str,
    ) -> ImportResult:
        """Add guests from ``name,email`` CSV rows (Pro feature).

        Skips rows that are malformed, have an invalid email, duplicate an email
        already on the event, or duplicate another row in the same upload.
        """
        await self._events.get(event_id, user.id)  # 404 if not the owner's event
        self._plan.assert_pro_feature(user, FEATURE_IMPORT)
        seen = await self._guests.existing_emails(event_id)

        created: list[Guest] = []
        skipped_duplicate = 0
        skipped_invalid = 0
        errors: list[str] = []

        for index, row in enumerate(self._iter_rows(csv_text), start=1):
            if index > _MAX_IMPORT_ROWS:
                errors.append(f"Stopped at {_MAX_IMPORT_ROWS} rows; remaining rows ignored.")
                break
            name, email = row
            if not name or not email:
                skipped_invalid += 1
                continue
            try:
                normalized = _email_adapter.validate_python(email)
            except ValidationError:
                skipped_invalid += 1
                errors.append(f"Row {index}: invalid email {email!r}.")
                continue
            key = normalized.lower()
            if key in seen:
                skipped_duplicate += 1
                continue
            seen.add(key)
            created.append(
                Guest(
                    event_id=event_id,
                    name=name,
                    email=normalized,
                    invite_token=secrets.token_urlsafe(24),
                ),
            )

        if created:
            await self._guests.add_many(created)

        return ImportResult(
            created=len(created),
            skipped_duplicate=skipped_duplicate,
            skipped_invalid=skipped_invalid,
            errors=errors,
        )

    async def export_csv(self, *, event_id: uuid.UUID, owner_id: uuid.UUID) -> str:
        """Render the full guest list as a CSV document (with header row)."""
        await self._events.get(event_id, owner_id)  # 404 if not the owner's event
        guests = await self._guests.list_for_event(event_id)
        buffer = io.StringIO()
        writer = csv.writer(buffer)
        writer.writerow(["name", "email", "rsvp_status", "plus_one", "dietary_notes", "checked_in"])
        for guest in guests:
            writer.writerow(
                [
                    guest.name,
                    guest.email,
                    guest.rsvp_status,
                    "yes" if guest.plus_one else "no",
                    guest.dietary_notes or "",
                    "yes" if guest.checked_in_at else "no",
                ],
            )
        return buffer.getvalue()

    async def send_reminders(self, *, event_id: uuid.UUID, user: User) -> int:
        """Email a reminder to every guest who hasn't responded yet (Pro feature).
        Returns the number sent."""
        event = await self._events.get(event_id, user.id)  # 404 if not the owner's event
        self._plan.assert_pro_feature(user, FEATURE_REMINDERS)
        pending = await self._guests.list_for_event(event_id, status=RsvpStatus.PENDING.value)
        for guest in pending:
            await self._email.send(
                EmailMessage(
                    to=guest.email,
                    subject=f"Reminder: please RSVP to {event.title}",
                    body=(
                        f"Hi {guest.name}, {event.title} is coming up — "
                        f"let the host know if you can make it."
                    ),
                ),
            )
        return len(pending)

    @staticmethod
    def _iter_rows(csv_text: str) -> list[tuple[str, str]]:
        """Parse CSV into (name, email) pairs, tolerating an optional header."""
        rows: list[tuple[str, str]] = []
        for raw in csv.reader(io.StringIO(csv_text)):
            if len(raw) < _MIN_CSV_COLUMNS:
                continue
            name, email = raw[0].strip(), raw[1].strip()
            if name.lower() == "name" and email.lower() == "email":
                continue  # header row
            rows.append((name, email))
        return rows
