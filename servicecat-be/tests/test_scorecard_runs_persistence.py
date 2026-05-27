"""Persistence + RLS tests for scorecard runs and findings."""

from __future__ import annotations

import uuid
from typing import TYPE_CHECKING

from servicecat.db import set_workspace_context
from servicecat.models import Finding, ScorecardRun, ScorecardRunStatus, Workspace
from servicecat.repositories.scorecard_runs import FindingRepository, ScorecardRunRepository

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

WS_A = uuid.UUID("f0000000-0000-0000-0000-0000000000a1")
WS_B = uuid.UUID("f0000000-0000-0000-0000-0000000000b2")
ACTOR = uuid.UUID("f0000000-0000-0000-0000-0000000000c3")
SERVICE = uuid.UUID("f0000000-0000-0000-0000-0000000000d4")


async def _seed_workspaces(sm: async_sessionmaker[AsyncSession]) -> None:
    async with sm() as session, session.begin():
        session.add_all(
            [Workspace(id=WS_A, name="A", slug="a"), Workspace(id=WS_B, name="B", slug="b")],
        )


def _new_run(workspace_id: uuid.UUID) -> ScorecardRun:
    return ScorecardRun(
        workspace_id=workspace_id,
        scorecard="documentation",
        status=ScorecardRunStatus.QUEUED,
        triggered_by=ACTOR,
        target_service_ids=[str(SERVICE)],
    )


async def test_run_and_findings_round_trip(
    rls_sessionmaker: async_sessionmaker[AsyncSession],
) -> None:
    await _seed_workspaces(rls_sessionmaker)
    async with rls_sessionmaker() as session, session.begin():
        await set_workspace_context(session, WS_A)
        run = _new_run(WS_A)
        await ScorecardRunRepository(session).add(run)
        await FindingRepository(session).add_all(
            [
                Finding(
                    workspace_id=WS_A,
                    run_id=run.id,
                    service_id=SERVICE,
                    criterion_id="doc.readme_present",
                    severity="high",
                    remediation="Add a README.",
                ),
            ],
        )
        fetched = await ScorecardRunRepository(session).get(run.id)
        count = await FindingRepository(session).count_for_run(run.id)
    assert fetched is not None
    assert fetched.scorecard == "documentation"
    assert count == 1


async def test_runs_are_workspace_isolated(
    rls_sessionmaker: async_sessionmaker[AsyncSession],
) -> None:
    await _seed_workspaces(rls_sessionmaker)
    async with rls_sessionmaker() as session, session.begin():
        await set_workspace_context(session, WS_A)
        run = _new_run(WS_A)
        await ScorecardRunRepository(session).add(run)
    # Under workspace B's context the run from A is invisible.
    async with rls_sessionmaker() as session, session.begin():
        await set_workspace_context(session, WS_B)
        assert await ScorecardRunRepository(session).get(run.id) is None
