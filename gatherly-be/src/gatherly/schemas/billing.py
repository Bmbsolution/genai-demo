"""Billing request/response schemas (host-facing)."""

from __future__ import annotations

from gatherly.schemas.base import GatherlyBaseModel


class BillingOverviewResponse(GatherlyBaseModel):
    """The host's plan, its limits, and current usage."""

    plan: str
    price_display: str
    max_active_events: int | None
    max_guests_per_event: int | None
    pro_features: list[str]
    active_events: int


class CheckoutResponse(GatherlyBaseModel):
    """Where to send the host to upgrade. ``mock`` means complete it in-app."""

    url: str | None
    mock: bool
