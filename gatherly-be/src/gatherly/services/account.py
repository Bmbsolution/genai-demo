"""Account management: profile updates, password change, account deletion."""

from __future__ import annotations

from typing import TYPE_CHECKING

from gatherly.errors import AuthenticationError, DomainValidationError
from gatherly.repositories.users import UserRepository
from gatherly.security import hash_password, verify_password

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import AsyncSession

    from gatherly.models import User
    from gatherly.schemas.auth import ProfileUpdateRequest


class AccountService:
    """Operates on the signed-in user's own account."""

    def __init__(self, db: AsyncSession) -> None:
        self._db = db
        self._users = UserRepository(db)

    async def update_profile(self, user: User, payload: ProfileUpdateRequest) -> User:
        for field, value in payload.model_dump(exclude_unset=True).items():
            setattr(user, field, value)
        await self._db.flush()
        await self._db.refresh(user)
        return user

    async def change_password(self, user: User, current_password: str, new_password: str) -> None:
        if user.hashed_password is None:
            raise DomainValidationError(
                "This account signs in with Google; there is no password to change.",
            )
        if not verify_password(current_password, user.hashed_password):
            raise AuthenticationError("Current password is incorrect")
        user.hashed_password = hash_password(new_password)
        await self._db.flush()

    async def delete_account(self, user: User) -> None:
        await self._users.delete(user)
