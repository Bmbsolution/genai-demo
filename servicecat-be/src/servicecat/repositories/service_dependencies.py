"""Data access for service dependency edges (workspace-scoped, RLS)."""

from __future__ import annotations

from typing import TYPE_CHECKING

from sqlalchemy import select

from servicecat.models import ServiceDependency

if TYPE_CHECKING:
    import uuid
    from collections.abc import Sequence

    from sqlalchemy.ext.asyncio import AsyncSession


class ServiceDependencyRepository:
    """Reads/writes dependency edges in the active workspace."""

    def __init__(self, db: AsyncSession) -> None:
        self._db = db

    async def add(self, dependency: ServiceDependency) -> None:
        self._db.add(dependency)
        await self._db.flush()

    async def get(self, dependency_id: uuid.UUID) -> ServiceDependency | None:
        result = await self._db.scalar(
            select(ServiceDependency).where(ServiceDependency.id == dependency_id),
        )
        return result if isinstance(result, ServiceDependency) else None

    async def delete(self, dependency: ServiceDependency) -> None:
        await self._db.delete(dependency)
        await self._db.flush()

    async def all_edges(self) -> Sequence[ServiceDependency]:
        """Every edge in the active workspace (small graphs; loaded for traversal)."""
        result = await self._db.scalars(select(ServiceDependency))
        return result.all()
