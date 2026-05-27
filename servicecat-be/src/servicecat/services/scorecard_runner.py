"""Scorecard run lifecycle: trigger (request side) and execute (worker side)."""

from __future__ import annotations

import datetime as dt
import uuid
from dataclasses import asdict
from typing import TYPE_CHECKING

from servicecat.errors import DomainValidationError, NotFoundError
from servicecat.models import Finding, ScorecardRun, ScorecardRunStatus
from servicecat.repo_clone import clone_repo
from servicecat.repositories.scorecard_runs import ScorecardRunRepository
from servicecat.repositories.services import ServiceRepository
from servicecat.scorecards import get_scorecard

if TYPE_CHECKING:
    from collections.abc import Callable, Sequence
    from contextlib import AbstractAsyncContextManager
    from pathlib import Path

    from sqlalchemy.ext.asyncio import AsyncSession

    CloneFactory = Callable[[str], "AbstractAsyncContextManager[Path]"]


class ScorecardRunService:
    """Request-side: validate and create a queued run."""

    def __init__(self, db: AsyncSession) -> None:
        self._db = db
        self._runs = ScorecardRunRepository(db)
        self._services = ServiceRepository(db)

    async def trigger(
        self,
        *,
        workspace_id: uuid.UUID,
        scorecard_name: str,
        target_service_ids: Sequence[uuid.UUID],
        triggered_by: uuid.UUID,
    ) -> ScorecardRun:
        get_scorecard(scorecard_name)  # raises NotFoundError for an unknown scorecard
        for service_id in target_service_ids:
            if await self._services.get(service_id) is None:
                msg = f"Target service not found: {service_id}"
                raise DomainValidationError(msg)
        run = ScorecardRun(
            workspace_id=workspace_id,
            scorecard=scorecard_name,
            status=ScorecardRunStatus.QUEUED,
            triggered_by=triggered_by,
            target_service_ids=[str(service_id) for service_id in target_service_ids],
        )
        await self._runs.add(run)
        return run

    async def get(self, run_id: uuid.UUID) -> ScorecardRun:
        run = await self._runs.get(run_id)
        if run is None:
            raise NotFoundError("Scorecard run not found")
        return run


async def execute_run(
    db: AsyncSession,
    run_id: uuid.UUID,
    *,
    clone: CloneFactory | None = None,
) -> None:
    """Worker-side: run the scorecard for every target, persist findings.

    The caller must already have set the RLS workspace context on ``db``. The
    ``clone`` factory is injectable for tests; it defaults to ``clone_repo``.
    """
    clone_factory = clone_repo if clone is None else clone
    runs = ScorecardRunRepository(db)
    run = await runs.get(run_id)
    if run is None:
        return
    run.status = ScorecardRunStatus.RUNNING
    run.started_at = dt.datetime.now(dt.UTC)
    await db.flush()

    services = ServiceRepository(db)
    scorecard = get_scorecard(run.scorecard)()
    total = 0
    try:
        for service_id in run.target_service_ids:
            service = await services.get(uuid.UUID(service_id))
            if service is None:
                continue
            async with clone_factory(service.repo_url) as repo_path:
                async for result in scorecard.evaluate(service, repo_path):
                    db.add(
                        Finding(
                            workspace_id=run.workspace_id,
                            run_id=run.id,
                            service_id=service.id,
                            criterion_id=result.criterion_id,
                            severity=result.severity.value,
                            remediation=result.remediation,
                            evidence=asdict(result.evidence) if result.evidence else None,
                            auto_fixable=result.auto_fixable,
                        ),
                    )
                    total += 1
            await db.flush()
    except Exception as exc:  # noqa: BLE001 - any failure is captured into the run record
        run.status = ScorecardRunStatus.FAILED
        run.error = str(exc)
    else:
        run.status = ScorecardRunStatus.COMPLETED
    run.finished_at = dt.datetime.now(dt.UTC)
    run.finding_count = total
    await db.flush()
