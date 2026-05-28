"""Scorecard run endpoints: trigger a run (202) and read its status.

All five guards: S1+S2 via get_current_workspace, S3 require_capability
(scorecard:run to trigger, scorecard:read to view), S4 rate_limit (tight 10/min
on the expensive trigger), S5 audit_action.
"""

import uuid
from collections.abc import Awaitable, Callable
from typing import Annotated

from fastapi import APIRouter, Depends, status
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
from servicecat.schemas.base import DataResponse
from servicecat.schemas.scorecard_run import ScorecardRunCreateRequest, ScorecardRunResponse
from servicecat.services.scorecard_runner import ScorecardRunService
from servicecat.workers.scorecard import get_enqueue

router = APIRouter(prefix="/api/v1/scorecards", tags=["scorecards"])

_run_cap = require_capability(Capability.SCORECARD_RUN)
_read_cap = require_capability(Capability.SCORECARD_READ)
_run_rl = rate_limit(per_minute=10, key="scorecard:run")
_read_rl = rate_limit(per_minute=120, key="scorecard:read")

WorkspaceDep = Annotated[WorkspaceContext, Depends(get_current_workspace)]
DbDep = Annotated[AsyncSession, Depends(get_db)]
EnqueueDep = Annotated[Callable[[uuid.UUID, uuid.UUID], Awaitable[None]], Depends(get_enqueue)]


@router.post("/{scorecard_name}/runs", status_code=status.HTTP_202_ACCEPTED)
async def trigger_scorecard_run(
    scorecard_name: str,
    payload: ScorecardRunCreateRequest,
    context: WorkspaceDep,
    db: DbDep,
    enqueue: EnqueueDep,
    _cap: Annotated[None, Depends(_run_cap)],
    _rl: Annotated[None, Depends(_run_rl)],
    _audit: Annotated[None, Depends(audit_action("scorecard.run"))],
) -> DataResponse[ScorecardRunResponse]:
    run = await ScorecardRunService(db).trigger(
        workspace_id=context.workspace.id,
        scorecard_name=scorecard_name,
        target_service_ids=payload.target_service_ids,
        triggered_by=context.user.id,
    )
    await enqueue(run.id, context.workspace.id)
    return DataResponse(data=ScorecardRunResponse.model_validate(run))


@router.get("/runs/{run_id}")
async def get_scorecard_run(
    run_id: uuid.UUID,
    db: DbDep,
    _cap: Annotated[None, Depends(_read_cap)],
    _rl: Annotated[None, Depends(_read_rl)],
    _audit: Annotated[None, Depends(audit_action("scorecard.run.read"))],
) -> DataResponse[ScorecardRunResponse]:
    run = await ScorecardRunService(db).get(run_id)
    return DataResponse(data=ScorecardRunResponse.model_validate(run))
