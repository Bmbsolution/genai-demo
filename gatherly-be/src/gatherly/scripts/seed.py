"""Seed a demo host with a couple of events and guests.

Run: ``python -m gatherly.scripts.seed`` (uses the configured GATHERLY_DATABASE_URL,
SQLite by default). Idempotent: re-running won't duplicate the host or events.
"""

from __future__ import annotations

import asyncio
import datetime as dt
import secrets

from sqlalchemy import select

from gatherly.db import get_sessionmaker, init_db
from gatherly.models import Event, EventStatus, EventVisibility, Guest, RsvpStatus, User, UserPlan
from gatherly.rbac import Role
from gatherly.security import hash_password

HOST_EMAIL = "host@gatherly.app"
HOST_PASSWORD = "gatherly-host"  # noqa: S105 - clearly-fake local dev credential

_SEED_GUESTS = [
    ("Marie Dubois", "marie@example.com", RsvpStatus.YES),
    ("Sam Patel", "sam@example.com", RsvpStatus.PENDING),
    ("Jordan Lee", "jordan@example.com", RsvpStatus.MAYBE),
    ("Priya Nair", "priya@example.com", RsvpStatus.YES),
]


async def seed() -> None:
    """Create the demo host, events, and guests if absent."""
    await init_db()
    async with get_sessionmaker()() as session, session.begin():
        host = await session.scalar(select(User).where(User.email == HOST_EMAIL))
        if host is None:
            host = User(
                email=HOST_EMAIL,
                display_name="Alex Rivera",
                role=Role.ADMIN.value,
                hashed_password=hash_password(HOST_PASSWORD),
                plan=UserPlan.PRO.value,  # established demo customer — Pro features on
            )
            session.add(host)
            await session.flush()

        already = await session.scalar(select(Event).where(Event.owner_id == host.id))
        if already is None:
            now = dt.datetime.now(dt.UTC)
            offsite = Event(
                owner_id=host.id,
                title="Team Offsite 2026",
                description="Two days in the mountains: planning, hiking, and a long dinner.",
                starts_at=now + dt.timedelta(days=21),
                ends_at=now + dt.timedelta(days=23),
                location="Mont-Tremblant, QC",
                cover_image_url="https://images.unsplash.com/photo-1519681393784-d120267933ba?w=1200",
                capacity=40,
                visibility=EventVisibility.PUBLIC.value,
                status=EventStatus.PUBLISHED.value,
            )
            # Intentionally missing a location → an "event readiness" gap to fix.
            launch = Event(
                owner_id=host.id,
                title="Product Launch Party",
                description="Drinks and demos to celebrate the launch.",
                starts_at=now + dt.timedelta(days=7),
                location=None,
                capacity=None,
                status=EventStatus.DRAFT.value,
            )
            session.add_all([offsite, launch])
            await session.flush()
            for name, email, rsvp in _SEED_GUESTS:
                session.add(
                    Guest(
                        event_id=offsite.id,
                        name=name,
                        email=email,
                        rsvp_status=rsvp.value,
                        invite_token=secrets.token_urlsafe(24),
                    ),
                )

    print(f"Seeded host '{HOST_EMAIL}' / '{HOST_PASSWORD}'")  # noqa: T201


def main() -> None:
    """CLI entrypoint."""
    asyncio.run(seed())


if __name__ == "__main__":
    main()
