"""Data access for notifications. Owner-scoped reads enforce tenant isolation (S2)."""

from __future__ import annotations

from typing import TYPE_CHECKING

from sqlalchemy import func, select, update

from gatherly.models import Notification

if TYPE_CHECKING:
    import datetime as dt
    import uuid
    from collections.abc import Sequence

    from sqlalchemy.ext.asyncio import AsyncSession


class NotificationRepository:
    """Reads/writes notifications, scoping every read to the recipient."""

    def __init__(self, db: AsyncSession) -> None:
        self._db = db

    async def add(self, notification: Notification) -> None:
        self._db.add(notification)
        await self._db.flush()

    async def get_for_owner(
        self,
        notification_id: uuid.UUID,
        owner_id: uuid.UUID,
    ) -> Notification | None:
        """Return the notification only if it belongs to ``owner_id``.

        This owner filter is the tenant-isolation boundary (S2): drop it and any
        host could read or mark another host's notifications.
        """
        result = await self._db.scalar(
            select(Notification).where(
                Notification.id == notification_id,
                Notification.owner_id == owner_id,
            ),
        )
        return result if isinstance(result, Notification) else None

    async def list_for_owner(
        self,
        owner_id: uuid.UUID,
        *,
        unread_only: bool = False,
        limit: int = 50,
        offset: int = 0,
    ) -> tuple[Sequence[Notification], int]:
        """Return (page of the owner's notifications, total), newest first."""
        base = select(Notification).where(Notification.owner_id == owner_id)
        if unread_only:
            base = base.where(Notification.read_at.is_(None))
        total = await self._db.scalar(select(func.count()).select_from(base.subquery())) or 0
        page = await self._db.scalars(
            base.order_by(Notification.created_at.desc()).limit(limit).offset(offset),
        )
        return page.all(), total

    async def count_unread(self, owner_id: uuid.UUID) -> int:
        """Return how many of the owner's notifications are still unread."""
        total = await self._db.scalar(
            select(func.count())
            .select_from(Notification)
            .where(Notification.owner_id == owner_id, Notification.read_at.is_(None)),
        )
        return total or 0

    async def mark_all_read(self, owner_id: uuid.UUID, *, now: dt.datetime) -> int:
        """Mark every unread notification for ``owner_id`` read; return the count."""
        count = await self.count_unread(owner_id)
        if count:
            await self._db.execute(
                update(Notification)
                .where(Notification.owner_id == owner_id, Notification.read_at.is_(None))
                .values(read_at=now),
            )
        return count
