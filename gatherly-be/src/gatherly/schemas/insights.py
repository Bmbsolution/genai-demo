"""Insights & readiness response schemas (host-facing, read-only)."""

from __future__ import annotations

from gatherly.schemas.base import GatherlyBaseModel


class EventInsightsResponse(GatherlyBaseModel):
    """Headline numbers for one event's guest list."""

    total_guests: int
    responded: int
    response_rate: float
    attending: int
    waitlisted: int
    plus_ones: int
    checked_in: int
    dietary_notes: int
    capacity: int | None
    remaining_capacity: int | None
    status_counts: dict[str, int]


class ReadinessCheckResponse(GatherlyBaseModel):
    """One pass/fail readiness signal (label/hint live in the FE i18n by key)."""

    key: str
    passed: bool
    severity: str


class EventReadinessResponse(GatherlyBaseModel):
    """The readiness checklist plus its roll-up."""

    ready: bool
    passed: int
    total: int
    checks: list[ReadinessCheckResponse]
