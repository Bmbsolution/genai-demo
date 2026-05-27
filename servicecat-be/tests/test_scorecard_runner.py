"""Tests for the scorecard run executor (clone -> evaluate -> persist)."""

from __future__ import annotations

import contextlib
import uuid
from typing import TYPE_CHECKING

from servicecat.db import set_workspace_context
from servicecat.models import ScorecardRun, ScorecardRunStatus, Service, Workspace
from servicecat.repositories.scorecard_runs import FindingRepository, ScorecardRunRepository
from servicecat.services.scorecard_runner import execute_run

if TYPE_CHECKING:
    from collections.abc import AsyncIterator
    from pathlib import Path

    from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

WS = uuid.UUID("11110000-0000-0000-0000-000000000011")
SERVICE = uuid.UUID("22220000-0000-0000-0000-000000000022")
ACTOR = uuid.UUID("33330000-0000-0000-0000-000000000033")


def _clone_factory(repo_root: Path):  # noqa: ANN202 - returns an async CM factory
    @contextlib.asynccontextmanager
    async def _clone(repo_url: str) -> AsyncIterator[Path]:
        del repo_url
        yield repo_root

    return _clone


async def test_execute_run_persists_findings_and_completes(
    rls_sessionmaker: async_sessionmaker[AsyncSession],
    tmp_path: Path,
) -> None:
    # Repo with only a README -> openapi/runbook/changelog/codeowners missing (4 findings).
    (tmp_path / "README.md").write_text("# svc\n", encoding="utf-8")

    async with rls_sessionmaker() as session, session.begin():
        session.add(Workspace(id=WS, name="W", slug="w"))
        await session.flush()
        await set_workspace_context(session, WS)
        session.add(
            Service(id=SERVICE, workspace_id=WS, name="svc", repo_url="https://e.com/r", tier=1),
        )
        run = ScorecardRun(
            workspace_id=WS,
            scorecard="documentation",
            status=ScorecardRunStatus.QUEUED,
            triggered_by=ACTOR,
            target_service_ids=[str(SERVICE)],
        )
        await ScorecardRunRepository(session).add(run)

        await execute_run(session, run.id, clone=_clone_factory(tmp_path))
        count = await FindingRepository(session).count_for_run(run.id)

    assert run.status == ScorecardRunStatus.COMPLETED
    assert run.finding_count == 4
    assert count == 4
