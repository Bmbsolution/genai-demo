"""Business logic for in-app notifications.

Notifications originate server-side: other services call :meth:`create` to emit
one (e.g. when a guest RSVPs). The host then lists them, sees an unread count,
and marks them read. Every host-facing method is scoped to ``owner_id`` — that
owner scope is the tenant-isolation boundary (S2).
"""

from __future__ import annotations

import datetime as dt
from typing import TYPE_CHECKING

from gatherly.errors import OwnershipError
from gatherly.models import Notification, NotificationType
from gatherly.repositories.notifications import NotificationRepository

if TYPE_CHECKING:
    import uuid
    from collections.abc import Sequence

    from sqlalchemy.ext.asyncio import AsyncSession


class NotificationService:
    """Emit, list, count, and mark-read a host's own notifications."""

    def __init__(self, db: AsyncSession) -> None:
        self._db = db
        self._repo = NotificationRepository(db)

    async def create(
        self,
        *,
        owner_id: uuid.UUID,
        title: str,
        kind: NotificationType = NotificationType.SYSTEM,
        body: str | None = None,
        event_id: uuid.UUID | None = None,
    ) -> Notification:
        """Emit a notification to ``owner_id``. Called by other services."""
        notification = Notification(
            owner_id=owner_id,
            type=kind.value,
            title=title,
            body=body,
            event_id=event_id,
        )
        await self._repo.add(notification)
        return notification

    async def get(self, notification_id: uuid.UUID, owner_id: uuid.UUID) -> Notification:
        """Return the host's own notification, or raise 404 (never leak existence)."""
        notification = await self._repo.get_for_owner(notification_id, owner_id)
        if notification is None:
            raise OwnershipError("Notification not found")
        return notification

    async def list_for_owner(
        self,
        owner_id: uuid.UUID,
        *,
        unread_only: bool = False,
        limit: int = 50,
        offset: int = 0,
    ) -> tuple[Sequence[Notification], int]:
        return await self._repo.list_for_owner(
            owner_id,
            unread_only=unread_only,
            limit=limit,
            offset=offset,
        )

    async def count_unread(self, owner_id: uuid.UUID) -> int:
        return await self._repo.count_unread(owner_id)

    async def mark_read(self, notification_id: uuid.UUID, owner_id: uuid.UUID) -> Notification:
        """Mark one notification read. Idempotent: re-marking is a no-op."""
        notification = await self.get(notification_id, owner_id)
        if notification.read_at is None:
            notification.read_at = dt.datetime.now(dt.UTC)
            await self._db.flush()
            await self._db.refresh(notification)
        return notification

    async def mark_all_read(self, owner_id: uuid.UUID) -> int:
        """Mark all of the owner's unread notifications read; return how many."""
        return await self._repo.mark_all_read(owner_id, now=dt.datetime.now(dt.UTC))
