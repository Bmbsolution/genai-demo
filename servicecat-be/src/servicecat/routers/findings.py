"""Findings dashboard endpoint. All five guards; read needs finding:read."""

import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from servicecat.deps import audit_action, get_db, rate_limit, require_capability
from servicecat.rbac import Capability
from servicecat.repositories.scorecard_runs import FindingRepository
from servicecat.schemas.finding import FindingListResponse, FindingResponse
from servicecat.schemas.service import PageMeta

router = APIRouter(prefix="/api/v1/findings", tags=["findings"])

_read_cap = require_capability(Capability.FINDING_READ)
_read_rl = rate_limit(per_minute=120, key="finding:read")


@router.get("")
async def list_findings(
    db: Annotated[AsyncSession, Depends(get_db)],
    _cap: Annotated[None, Depends(_read_cap)],
    _rl: Annotated[None, Depends(_read_rl)],
    _audit: Annotated[None, Depends(audit_action("finding.list"))],
    service_id: Annotated[uuid.UUID | None, Query()] = None,
    severity: Annotated[str | None, Query()] = None,
    limit: Annotated[int, Query(ge=1, le=200)] = 50,
    offset: Annotated[int, Query(ge=0)] = 0,
) -> FindingListResponse:
    items, total = await FindingRepository(db).list_for_workspace(
        service_id=service_id,
        severity=severity,
        limit=limit,
        offset=offset,
    )
    return FindingListResponse(
        data=[FindingResponse.model_validate(item) for item in items],
        meta=PageMeta(limit=limit, offset=offset, total=total),
    )
