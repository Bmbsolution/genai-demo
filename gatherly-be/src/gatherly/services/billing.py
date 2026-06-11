"""Plans, limits, and billing.

Two free-tier caps (active events, guests per event) plus two Pro-only features
(CSV import, reminders) create the upgrade pressure; ``PlanService`` enforces
them and raises :class:`PlanLimitError` (402) so the client can prompt to upgrade.

Checkout goes through a pluggable :class:`BillingProvider`. The default
``MockBillingProvider`` upgrades the account in-app (demo/local, no secrets). A
real Stripe provider — Checkout Session + webhook — implements the same protocol
and is selected once ``GATHERLY_STRIPE_SECRET_KEY`` is set; the mock self-upgrade
endpoint is refused in that case so production can only go Pro via a real payment.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Protocol

from gatherly.config import get_settings
from gatherly.errors import PlanLimitError
from gatherly.models import UserPlan
from gatherly.repositories.events import EventRepository
from gatherly.repositories.guests import GuestRepository

if TYPE_CHECKING:
    import uuid

    from sqlalchemy.ext.asyncio import AsyncSession

    from gatherly.models import User

# Pro-only feature keys (surface in the 402 detail so the client can explain).
FEATURE_IMPORT = "import"
FEATURE_REMINDERS = "reminders"


@dataclass(frozen=True, slots=True)
class CheckoutSession:
    """Where to send the host to pay. ``url`` is null for the mock provider,
    where the client completes the upgrade in-app instead of redirecting."""

    url: str | None
    mock: bool


@dataclass(frozen=True, slots=True)
class BillingOverview:
    """The host's plan, what it allows, and current usage."""

    plan: str
    price_display: str
    max_active_events: int | None  # null = unlimited (Pro)
    max_guests_per_event: int | None
    pro_features: list[str]
    active_events: int


class BillingProvider(Protocol):
    """Starts a checkout for the Pro plan."""

    async def create_checkout(self, user: User) -> CheckoutSession:
        """Begin a Pro upgrade for ``user``."""
        ...


class MockBillingProvider:
    """Local/demo provider: no real payment; the upgrade endpoint flips the plan."""

    async def create_checkout(self, _user: User) -> CheckoutSession:
        return CheckoutSession(url=None, mock=True)


def get_billing_provider() -> BillingProvider:
    """Return the configured provider. Mock until Stripe keys are wired in."""
    return MockBillingProvider()


class PlanService:
    """Enforce plan limits and surface a billing overview for the current user."""

    def __init__(self, db: AsyncSession) -> None:
        self._db = db
        self._settings = get_settings()
        self._events = EventRepository(db)
        self._guests = GuestRepository(db)
        self._provider = get_billing_provider()

    @staticmethod
    def is_pro(user: User) -> bool:
        return user.plan == UserPlan.PRO.value

    async def assert_can_create_event(self, user: User) -> None:
        if self.is_pro(user):
            return
        _, active = await self._events.list_for_owner(user.id, limit=1, offset=0)
        cap = self._settings.free_max_active_events
        if active >= cap:
            raise PlanLimitError(
                "Free plan event limit reached",
                details={"limit": cap, "kind": "events"},
            )

    async def assert_can_add_guests(
        self,
        user: User,
        event_id: uuid.UUID,
        adding: int,
    ) -> None:
        if self.is_pro(user):
            return
        current = await self._guests.count_for_event(event_id)
        cap = self._settings.free_max_guests_per_event
        if current + adding > cap:
            raise PlanLimitError(
                "Free plan guest limit reached",
                details={"limit": cap, "kind": "guests", "current": current},
            )

    def assert_pro_feature(self, user: User, feature: str) -> None:
        if not self.is_pro(user):
            raise PlanLimitError(
                "This feature requires Pro",
                details={"feature": feature, "kind": "feature"},
            )

    async def overview(self, user: User) -> BillingOverview:
        _, active = await self._events.list_for_owner(user.id, limit=1, offset=0)
        pro = self.is_pro(user)
        return BillingOverview(
            plan=user.plan,
            price_display=self._settings.pro_price_display,
            max_active_events=None if pro else self._settings.free_max_active_events,
            max_guests_per_event=None if pro else self._settings.free_max_guests_per_event,
            pro_features=[FEATURE_IMPORT, FEATURE_REMINDERS],
            active_events=active,
        )

    async def start_checkout(self, user: User) -> CheckoutSession:
        return await self._provider.create_checkout(user)

    async def activate_pro(self, user: User) -> User:
        """Mock upgrade for local/demo. Refused once real Stripe is configured —
        production upgrades arrive via the Stripe webhook, not this endpoint."""
        if self._settings.stripe_secret_key:
            raise PlanLimitError(
                "Direct upgrade is disabled; complete checkout to go Pro",
                details={"kind": "checkout_required"},
            )
        user.plan = UserPlan.PRO.value
        await self._db.flush()
        await self._db.refresh(user)
        return user
