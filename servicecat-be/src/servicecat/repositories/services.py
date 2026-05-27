"""Data access for catalog services (workspace-scoped via RLS, soft-deleted)."""

from __future__ import annotations

from typing import TYPE_CHECKING

from sqlalchemy import func, select

from servicecat.models import Service

if TYPE_CHECKING:
    import uuid
    from collections.abc import Sequence

    from sqlalchemy.ext.asyncio import AsyncSession


class ServiceRepository:
    """Reads/writes services. RLS scopes every query to the active workspace."""

    def __init__(self, db: AsyncSession) -> None:
        self._db = db

    async def add(self, service: Service) -> None:
        self._db.add(service)
        await self._db.flush()

    async def get(self, service_id: uuid.UUID) -> Service | None:
        """Return an active (non-deleted) service, or None."""
        result = await self._db.scalar(
            select(Service).where(Service.id == service_id, Service.deleted_at.is_(None)),
        )
        return result if isinstance(result, Service) else None

    async def list_active(
        self,
        *,
        tier: int | None = None,
        owner_team_id: uuid.UUID | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> tuple[Sequence[Service], int]:
        """Return (page of active services, total matching count)."""
        filtered = select(Service).where(Service.deleted_at.is_(None))
        if tier is not None:
            filtered = filtered.where(Service.tier == tier)
        if owner_team_id is not None:
            filtered = filtered.where(Service.owner_team_id == owner_team_id)
        total = await self._db.scalar(select(func.count()).select_from(filtered.subquery()))
        page = await self._db.scalars(
            filtered.order_by(Service.created_at.desc()).limit(limit).offset(offset),
        )
        return page.all(), total or 0
