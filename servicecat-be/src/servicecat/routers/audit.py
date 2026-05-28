"""Audit log endpoints. The first surface wired with all five guards.

S1 (auth) + S2 (tenant isolation, sets the RLS scope) arrive via
get_current_workspace, which both _cap and _audit depend on; S3 (RBAC), S4
(rate limit), and S5 (audit) are the three explicit guards below.
"""

from typing import Annotated

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from servicecat.deps import audit_action, get_db, rate_limit, require_capability
from servicecat.rbac import Capability
from servicecat.repositories.audit import AuditLogRepository
from servicecat.schemas.audit import AuditLogResponse
from servicecat.schemas.base import DataResponse

router = APIRouter(prefix="/api/v1/audit", tags=["audit"])

_list_rl = rate_limit(per_minute=60, key="audit:list")
_require_audit_read = require_capability(Capability.AUDIT_READ)
_audit_list = audit_action("audit.list")


@router.get("/logs")
async def list_audit_logs(
    db: Annotated[AsyncSession, Depends(get_db)],
    _cap: Annotated[None, Depends(_require_audit_read)],
    _rl: Annotated[None, Depends(_list_rl)],
    _audit: Annotated[None, Depends(_audit_list)],
    action: Annotated[str | None, Query()] = None,
    resource_type: Annotated[str | None, Query()] = None,
    limit: Annotated[int, Query(ge=1, le=200)] = 50,
) -> DataResponse[list[AuditLogResponse]]:
    logs = await AuditLogRepository(db).list_for_workspace(
        action=action,
        resource_type=resource_type,
        limit=limit,
    )
    return DataResponse(data=[AuditLogResponse.model_validate(log) for log in logs])
