"""Data access for scorecard runs and their findings (workspace-scoped, RLS)."""

from __future__ import annotations

from typing import TYPE_CHECKING

from sqlalchemy import Text, case, cast, func, select
from sqlalchemy.orm import aliased

from servicecat.models import Finding, ScorecardRun, ScorecardRunStatus

if TYPE_CHECKING:
    import uuid
    from collections.abc import Sequence

    from sqlalchemy.ext.asyncio import AsyncSession

# Worst-first display order for the severity Text column.
_SEVERITY_RANK = case(
    {"critical": 0, "high": 1, "medium": 2, "low": 3},
    value=Finding.severity,
    else_=4,
)


class ScorecardRunRepository:
    """Reads/writes scorecard runs in the active workspace."""

    def __init__(self, db: AsyncSession) -> None:
        self._db = db

    async def add(self, run: ScorecardRun) -> None:
        self._db.add(run)
        await self._db.flush()

    async def get(self, run_id: uuid.UUID) -> ScorecardRun | None:
        result = await self._db.scalar(select(ScorecardRun).where(ScorecardRun.id == run_id))
        return result if isinstance(result, ScorecardRun) else None


class FindingRepository:
    """Appends and lists findings in the active workspace."""

    def __init__(self, db: AsyncSession) -> None:
        self._db = db

    async def add_all(self, findings: Sequence[Finding]) -> None:
        self._db.add_all(findings)
        await self._db.flush()

    async def list_for_workspace(
        self,
        *,
        service_id: uuid.UUID | None = None,
        severity: str | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> tuple[Sequence[Finding], int]:
        """Return (page of current findings, total matching).

        "Current" means findings produced by each service's most recent
        COMPLETED run of a given scorecard. Older runs' findings are
        superseded — without this, every re-run would pile duplicate rows
        onto the dashboard. A newer completed run with zero findings
        correctly hides the previous run's findings (the gap was fixed).
        """
        run = aliased(ScorecardRun)
        newer = aliased(ScorecardRun)
        superseded = (
            select(newer.id)
            .where(
                newer.status == ScorecardRunStatus.COMPLETED,
                newer.scorecard == run.scorecard,
                newer.started_at > run.started_at,
                newer.target_service_ids.op("@>")(
                    func.jsonb_build_array(cast(Finding.service_id, Text)),
                ),
            )
            .exists()
        )
        filtered = (
            select(Finding)
            .join(run, run.id == Finding.run_id)
            .where(run.status == ScorecardRunStatus.COMPLETED, ~superseded)
        )
        if service_id is not None:
            filtered = filtered.where(Finding.service_id == service_id)
        if severity is not None:
            filtered = filtered.where(Finding.severity == severity)
        total = await self._db.scalar(select(func.count()).select_from(filtered.subquery()))
        page = await self._db.scalars(
            filtered.order_by(_SEVERITY_RANK, Finding.created_at.desc())
            .limit(limit)
            .offset(offset),
        )
        return page.all(), total or 0
