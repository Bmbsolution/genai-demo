"""Data access for scorecard runs and their findings (workspace-scoped, RLS)."""

from __future__ import annotations

from typing import TYPE_CHECKING

from sqlalchemy import func, select

from servicecat.models import Finding, ScorecardRun

if TYPE_CHECKING:
    import uuid
    from collections.abc import Sequence

    from sqlalchemy.ext.asyncio import AsyncSession


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
    """Appends and counts findings in the active workspace."""

    def __init__(self, db: AsyncSession) -> None:
        self._db = db

    async def add_all(self, findings: Sequence[Finding]) -> None:
        self._db.add_all(findings)
        await self._db.flush()

    async def count_for_run(self, run_id: uuid.UUID) -> int:
        total = await self._db.scalar(
            select(func.count()).select_from(Finding).where(Finding.run_id == run_id),
        )
        return total or 0

    async def list_for_workspace(
        self,
        *,
        service_id: uuid.UUID | None = None,
        severity: str | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> tuple[Sequence[Finding], int]:
        """Return (page of findings in the active workspace, total matching)."""
        filtered = select(Finding)
        if service_id is not None:
            filtered = filtered.where(Finding.service_id == service_id)
        if severity is not None:
            filtered = filtered.where(Finding.severity == severity)
        total = await self._db.scalar(select(func.count()).select_from(filtered.subquery()))
        page = await self._db.scalars(
            filtered.order_by(Finding.created_at.desc()).limit(limit).offset(offset),
        )
        return page.all(), total or 0
