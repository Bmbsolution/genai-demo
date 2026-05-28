"""Service dependency endpoints: declare, remove, and traverse edges.

All five guards. POST/DELETE need service:write (Maintainer+); GET needs
service:read. Cycle rejection and depth-limited traversal live in the service.
"""

import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from servicecat.deps import (
    WorkspaceContext,
    audit_action,
    get_current_workspace,
    get_db,
    rate_limit,
    require_capability,
)
from servicecat.models import ServiceDependency
from servicecat.rbac import Capability
from servicecat.schemas.base import DataResponse
from servicecat.schemas.service_dependency import (
    ServiceDependencyCreateRequest,
    ServiceDependencyResponse,
)
from servicecat.services.dependencies import ServiceDependencyService

router = APIRouter(prefix="/api/v1/services", tags=["services"])

_write_cap = require_capability(Capability.SERVICE_WRITE)
_read_cap = require_capability(Capability.SERVICE_READ)
_rl_write = rate_limit(per_minute=30, key="service:dep:write")
_rl_read = rate_limit(per_minute=120, key="service:dep:read")

WorkspaceDep = Annotated[WorkspaceContext, Depends(get_current_workspace)]
DbDep = Annotated[AsyncSession, Depends(get_db)]


def _response(dependency: ServiceDependency, depth: int) -> ServiceDependencyResponse:
    return ServiceDependencyResponse(
        id=dependency.id,
        service_id=dependency.service_id,
        depends_on_service_id=dependency.depends_on_service_id,
        criticality=dependency.criticality,
        direction=dependency.direction,
        depth=depth,
    )


@router.post("/{service_id}/dependencies", status_code=status.HTTP_201_CREATED)
async def add_dependency(
    service_id: uuid.UUID,
    payload: ServiceDependencyCreateRequest,
    context: WorkspaceDep,
    db: DbDep,
    _cap: Annotated[None, Depends(_write_cap)],
    _rl: Annotated[None, Depends(_rl_write)],
    _audit: Annotated[None, Depends(audit_action("service.dependency.create"))],
) -> DataResponse[ServiceDependencyResponse]:
    dependency = await ServiceDependencyService(db).add(
        workspace_id=context.workspace.id,
        service_id=service_id,
        depends_on_service_id=payload.depends_on_service_id,
        criticality=payload.criticality,
        direction=payload.direction,
    )
    return DataResponse(data=_response(dependency, depth=1))


@router.delete(
    "/{service_id}/dependencies/{dependency_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def remove_dependency(
    service_id: uuid.UUID,
    dependency_id: uuid.UUID,
    db: DbDep,
    _cap: Annotated[None, Depends(_write_cap)],
    _rl: Annotated[None, Depends(_rl_write)],
    _audit: Annotated[None, Depends(audit_action("service.dependency.delete"))],
) -> None:
    await ServiceDependencyService(db).remove(service_id, dependency_id)


@router.get("/{service_id}/dependencies")
async def list_dependencies(
    service_id: uuid.UUID,
    db: DbDep,
    _cap: Annotated[None, Depends(_read_cap)],
    _rl: Annotated[None, Depends(_rl_read)],
    _audit: Annotated[None, Depends(audit_action("service.dependency.list"))],
    depth: Annotated[int, Query(ge=1, le=2)] = 1,
) -> DataResponse[list[ServiceDependencyResponse]]:
    edges = await ServiceDependencyService(db).list_dependencies(service_id, depth=depth)
    return DataResponse(data=[_response(edge.dependency, edge.depth) for edge in edges])
