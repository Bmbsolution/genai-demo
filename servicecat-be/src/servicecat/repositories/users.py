"""Data access for users (a global, non-workspace-scoped table)."""

from __future__ import annotations

from typing import TYPE_CHECKING, cast

from sqlalchemy import select

from servicecat.models import User

if TYPE_CHECKING:
    import uuid

    from sqlalchemy.ext.asyncio import AsyncSession


class UserRepository:
    """All user reads/writes go through here (never db.execute from a router)."""

    def __init__(self, db: AsyncSession) -> None:
        self._db = db

    async def get_by_email(self, email: str) -> User | None:
        return cast("User | None", await self._db.scalar(select(User).where(User.email == email)))

    async def get_by_id(self, user_id: uuid.UUID) -> User | None:
        # session.get() is typed as returning Any in this SQLAlchemy version.
        return cast("User | None", await self._db.get(User, user_id))
