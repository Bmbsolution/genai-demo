"""Business logic for the service catalog. Routers stay thin; this layer
raises typed domain errors that routers translate to HTTP status codes.
"""

from __future__ import annotations

import datetime as dt
from typing import TYPE_CHECKING

from sqlalchemy.exc import IntegrityError

from servicecat.errors import ConflictError, NotFoundError
from servicecat.models import Service
from servicecat.repositories.services import ServiceRepository

if TYPE_CHECKING:
    import uuid
    from collections.abc import Sequence

    from sqlalchemy.ext.asyncio import AsyncSession

    from servicecat.schemas.service import ServiceCreateRequest, ServiceUpdateRequest

# PostgreSQL SQLSTATE for unique_violation; the services table has a
# uq_services_workspace_id_name constraint (one name per workspace).
_PG_UNIQUE_VIOLATION = "23505"


def _name_conflict(exc: IntegrityError, name: str) -> ConflictError | None:
    """Map a unique-constraint violation to a typed 409; return None otherwise."""
    if getattr(exc.orig, "sqlstate", None) != _PG_UNIQUE_VIOLATION:
        return None
    return ConflictError(
        f"A service named '{name}' already exists in this workspace.",
        details={"field": "name", "value": name},
    )


class ServiceCatalog:
    """Create, read, update, and soft-delete services in the active workspace."""

    def __init__(self, db: AsyncSession) -> None:
        self._db = db
        self._repo = ServiceRepository(db)

    async def create(self, *, workspace_id: uuid.UUID, payload: ServiceCreateRequest) -> Service:
        service = Service(
            workspace_id=workspace_id,
            name=payload.name,
            description=payload.description,
            repo_url=payload.repo_url,
            tier=payload.tier,
            owner_team_id=payload.owner_team_id,
        )
        try:
            await self._repo.add(service)
        except IntegrityError as exc:
            raise _name_conflict(exc, payload.name) or exc from exc
        return service

    async def get(self, service_id: uuid.UUID) -> Service:
        service = await self._repo.get(service_id)
        if service is None:
            raise NotFoundError("Service not found")
        return service

    async def list_services(
        self,
        *,
        tier: int | None = None,
        owner_team_id: uuid.UUID | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> tuple[Sequence[Service], int]:
        return await self._repo.list_active(
            tier=tier,
            owner_team_id=owner_team_id,
            limit=limit,
            offset=offset,
        )

    async def update(self, service_id: uuid.UUID, payload: ServiceUpdateRequest) -> Service:
        service = await self.get(service_id)
        for field, value in payload.model_dump(exclude_unset=True).items():
            setattr(service, field, value)
        try:
            await self._db.flush()
        except IntegrityError as exc:
            # Use payload.name, not service.name: a failed flush expires the ORM
            # attributes, so reading them here would emit SQL on a dead transaction.
            raise _name_conflict(exc, payload.name or "service") or exc from exc
        # Reload server-side onupdate values (e.g. updated_at) so the response
        # doesn't lazy-load them in pydantic's sync context (MissingGreenlet).
        await self._db.refresh(service)
        return service

    async def soft_delete(self, service_id: uuid.UUID) -> None:
        service = await self.get(service_id)
        service.deleted_at = dt.datetime.now(dt.UTC)
        await self._db.flush()
