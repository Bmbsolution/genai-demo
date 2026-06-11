"""User — a Gatherly host (or admin) who owns events."""

from __future__ import annotations

from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column

from gatherly.models.base import Base, TimestampMixin, UUIDPrimaryKeyMixin
from gatherly.rbac import Role


class User(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """An authenticated account. Global (not scoped to any event)."""

    __tablename__ = "users"

    email: Mapped[str] = mapped_column(String(320), unique=True, index=True)
    hashed_password: Mapped[str | None] = mapped_column(String(255), default=None)
    display_name: Mapped[str] = mapped_column(String(120))
    role: Mapped[str] = mapped_column(String(20), default=Role.HOST.value)
    is_active: Mapped[bool] = mapped_column(default=True)
