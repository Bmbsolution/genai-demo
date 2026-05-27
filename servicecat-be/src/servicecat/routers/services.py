"""Service catalog endpoints (CRUD), each wired with all five guards.

S1+S2 arrive via get_current_workspace (which the cap/audit guards depend on and
which sets the RLS scope); S3 require_capability, S4 rate_limit, S5 audit_action
are explicit. write needs Maintainer+, delete needs Admin.
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
from servicecat.rbac import Capability
from servicecat.schemas.service import (
    PageMeta,
    ServiceCreateRequest,
    ServiceListResponse,
    ServiceResponse,
    ServiceUpdateRequest,
)
from servicecat.services.catalog import ServiceCatalog

router = APIRouter(prefix="/api/v1/services", tags=["services"])

_read_cap = require_capability(Capability.SERVICE_READ)
_write_cap = require_capability(Capability.SERVICE_WRITE)
_delete_cap = require_capability(Capability.SERVICE_DELETE)
_rl_read = rate_limit(per_minute=120, key="service:read")
_rl_write = rate_limit(per_minute=30, key="service:write")
_rl_delete = rate_limit(per_minute=30, key="service:delete")

WorkspaceDep = Annotated[WorkspaceContext, Depends(get_current_workspace)]
DbDep = Annotated[AsyncSession, Depends(get_db)]


@router.post("", status_code=status.HTTP_201_CREATED)
async def create_service(
    payload: ServiceCreateRequest,
    context: WorkspaceDep,
    db: DbDep,
    _cap: Annotated[None, Depends(_write_cap)],
    _rl: Annotated[None, Depends(_rl_write)],
    _audit: Annotated[None, Depends(audit_action("service.create"))],
) -> ServiceResponse:
    service = await ServiceCatalog(db).create(workspace_id=context.workspace.id, payload=payload)
    return ServiceResponse.model_validate(service)


@router.get("")
async def list_services(
    db: DbDep,
    _cap: Annotated[None, Depends(_read_cap)],
    _rl: Annotated[None, Depends(_rl_read)],
    _audit: Annotated[None, Depends(audit_action("service.list"))],
    tier: Annotated[int | None, Query(ge=1, le=3)] = None,
    owner_team_id: Annotated[uuid.UUID | None, Query()] = None,
    limit: Annotated[int, Query(ge=1, le=200)] = 50,
    offset: Annotated[int, Query(ge=0)] = 0,
) -> ServiceListResponse:
    items, total = await ServiceCatalog(db).list_services(
        tier=tier,
        owner_team_id=owner_team_id,
        limit=limit,
        offset=offset,
    )
    return ServiceListResponse(
        data=[ServiceResponse.model_validate(item) for item in items],
        meta=PageMeta(limit=limit, offset=offset, total=total),
    )


@router.get("/{service_id}")
async def get_service(
    service_id: uuid.UUID,
    db: DbDep,
    _cap: Annotated[None, Depends(_read_cap)],
    _rl: Annotated[None, Depends(_rl_read)],
    _audit: Annotated[None, Depends(audit_action("service.read"))],
) -> ServiceResponse:
    service = await ServiceCatalog(db).get(service_id)
    return ServiceResponse.model_validate(service)


@router.patch("/{service_id}")
async def update_service(
    service_id: uuid.UUID,
    payload: ServiceUpdateRequest,
    db: DbDep,
    _cap: Annotated[None, Depends(_write_cap)],
    _rl: Annotated[None, Depends(_rl_write)],
    _audit: Annotated[None, Depends(audit_action("service.update"))],
) -> ServiceResponse:
    service = await ServiceCatalog(db).update(service_id, payload)
    return ServiceResponse.model_validate(service)


@router.delete("/{service_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_service(
    service_id: uuid.UUID,
    db: DbDep,
    _cap: Annotated[None, Depends(_delete_cap)],
    _rl: Annotated[None, Depends(_rl_delete)],
    _audit: Annotated[None, Depends(audit_action("service.delete"))],
) -> None:
    await ServiceCatalog(db).soft_delete(service_id)
