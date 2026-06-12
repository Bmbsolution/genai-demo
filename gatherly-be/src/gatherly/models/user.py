"""User — a Gatherly host (or admin) who owns events."""

from __future__ import annotations

import enum

from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column

from gatherly.models.base import Base, TimestampMixin, UUIDPrimaryKeyMixin
from gatherly.rbac import Role


class UserPlan(enum.StrEnum):
    """A host's billing plan. Pro lifts the free-tier caps and unlocks
    import/reminders."""

    FREE = "free"
    PRO = "pro"


class User(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """An authenticated account. Global (not scoped to any event)."""

    __tablename__ = "users"

    email: Mapped[str] = mapped_column(String(320), unique=True, index=True)
    # Null for accounts created via Google (no local password).
    hashed_password: Mapped[str | None] = mapped_column(String(255), default=None)
    display_name: Mapped[str] = mapped_column(String(120))
    role: Mapped[str] = mapped_column(String(20), default=Role.HOST.value)
    is_active: Mapped[bool] = mapped_column(default=True)
    avatar_url: Mapped[str | None] = mapped_column(String(1024), default=None)
    timezone: Mapped[str] = mapped_column(String(64), default="UTC")
    # "password" or "google" — how the account first authenticated.
    auth_provider: Mapped[str] = mapped_column(String(20), default="password")
    # Google's stable subject id, set when the account links Google.
    google_sub: Mapped[str | None] = mapped_column(String(64), unique=True, default=None)
    # Billing plan — "free" or "pro". New accounts start free.
    plan: Mapped[str] = mapped_column(String(20), default=UserPlan.FREE.value)
