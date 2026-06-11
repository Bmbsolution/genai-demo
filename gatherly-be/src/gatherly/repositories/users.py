"""Data access for users (global table, no tenant scoping)."""

from __future__ import annotations

from typing import TYPE_CHECKING

from sqlalchemy import select

from gatherly.models import User

if TYPE_CHECKING:
    import uuid

    from sqlalchemy.ext.asyncio import AsyncSession


class UserRepository:
    """Reads/writes the global users table."""

    def __init__(self, db: AsyncSession) -> None:
        self._db = db

    async def add(self, user: User) -> None:
        self._db.add(user)
        await self._db.flush()

    async def get_by_id(self, user_id: uuid.UUID) -> User | None:
        return await self._db.get(User, user_id)

    async def get_by_email(self, email: str) -> User | None:
        result = await self._db.scalar(select(User).where(User.email == email))
        return result if isinstance(result, User) else None
