"""Per-event analytics and a readiness checklist.

ServiceCat scores services against rulesets; Gatherly does the small, host-facing
analogue: it reads an event plus its guest list and reports the numbers a host
cares about, plus a checklist of "is this event ready to go" signals. Both are
read-only and prove ownership first (via EventService.get → 404).
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

from gatherly.models import RsvpStatus
from gatherly.repositories.guests import GuestRepository
from gatherly.services.events import EventService

if TYPE_CHECKING:
    import uuid

    from sqlalchemy.ext.asyncio import AsyncSession

# Fraction of invited guests who must have responded for the event to look healthy.
_HEALTHY_RESPONSE_RATE = 0.5
_RESPONDED = frozenset(
    {
        RsvpStatus.YES.value,
        RsvpStatus.NO.value,
        RsvpStatus.MAYBE.value,
        RsvpStatus.WAITLISTED.value,
    },
)


@dataclass(frozen=True, slots=True)
class EventInsights:
    """Headline numbers for one event's guest list."""

    total_guests: int
    responded: int
    response_rate: float  # 0.0 to 1.0; 0 when no guests
    attending: int  # confirmed "yes"
    waitlisted: int
    plus_ones: int
    checked_in: int
    dietary_notes: int
    capacity: int | None
    remaining_capacity: int | None  # null when uncapped
    status_counts: dict[str, int]


@dataclass(frozen=True, slots=True)
class ReadinessCheck:
    """One pass/fail signal in the readiness checklist."""

    key: str
    passed: bool
    severity: str  # high | medium | low


@dataclass(frozen=True, slots=True)
class EventReadiness:
    """The checklist plus a roll-up: ``ready`` iff every high-severity check passes."""

    ready: bool
    passed: int
    total: int
    checks: list[ReadinessCheck]


class InsightsService:
    """Compute read-only insights and readiness for an owned event."""

    def __init__(self, db: AsyncSession) -> None:
        self._events = EventService(db)
        self._guests = GuestRepository(db)

    async def get_insights(self, *, event_id: uuid.UUID, owner_id: uuid.UUID) -> EventInsights:
        event = await self._events.get(event_id, owner_id)  # 404 if not the owner's event
        guests = await self._guests.list_for_event(event_id)

        status_counts: dict[str, int] = {}
        for guest in guests:
            status_counts[guest.rsvp_status] = status_counts.get(guest.rsvp_status, 0) + 1

        total = len(guests)
        responded = sum(1 for g in guests if g.rsvp_status in _RESPONDED)
        attending = status_counts.get(RsvpStatus.YES.value, 0)
        remaining = None if event.capacity is None else max(event.capacity - attending, 0)

        return EventInsights(
            total_guests=total,
            responded=responded,
            response_rate=(responded / total) if total else 0.0,
            attending=attending,
            waitlisted=status_counts.get(RsvpStatus.WAITLISTED.value, 0),
            plus_ones=sum(1 for g in guests if g.plus_one),
            checked_in=sum(1 for g in guests if g.checked_in_at is not None),
            dietary_notes=sum(1 for g in guests if g.dietary_notes),
            capacity=event.capacity,
            remaining_capacity=remaining,
            status_counts=status_counts,
        )

    async def get_readiness(self, *, event_id: uuid.UUID, owner_id: uuid.UUID) -> EventReadiness:
        event = await self._events.get(event_id, owner_id)  # 404 if not the owner's event
        insights = await self.get_insights(event_id=event_id, owner_id=owner_id)

        within_capacity = event.capacity is None or insights.attending <= event.capacity
        healthy_rate = (
            insights.total_guests > 0 and insights.response_rate >= _HEALTHY_RESPONSE_RATE
        )
        checks = [
            ReadinessCheck("has_guests", insights.total_guests > 0, "high"),
            ReadinessCheck("within_capacity", within_capacity, "high"),
            ReadinessCheck("has_location", bool(event.location), "high"),
            ReadinessCheck("published", event.status == "published", "medium"),
            ReadinessCheck("healthy_response_rate", healthy_rate, "medium"),
            ReadinessCheck("has_description", bool(event.description), "low"),
            ReadinessCheck("has_cover_image", bool(event.cover_image_url), "low"),
            ReadinessCheck("has_end_time", event.ends_at is not None, "low"),
        ]
        ready = all(check.passed for check in checks if check.severity == "high")
        return EventReadiness(
            ready=ready,
            passed=sum(1 for check in checks if check.passed),
            total=len(checks),
            checks=checks,
        )
