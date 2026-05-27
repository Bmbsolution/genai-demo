"""Arq worker that executes queued scorecard runs in the background.

Run with: ``arq servicecat.workers.scorecard.WorkerSettings``.
"""

from __future__ import annotations

import uuid
from typing import TYPE_CHECKING

from arq import create_pool
from arq.connections import RedisSettings

from servicecat.config import get_settings
from servicecat.db import get_sessionmaker, set_workspace_context
from servicecat.services.scorecard_runner import execute_run

if TYPE_CHECKING:
    from collections.abc import Awaitable, Callable

# Defer so the triggering request commits the queued run before the worker reads it.
_ENQUEUE_DEFER_SECONDS = 2


def _redis_settings() -> RedisSettings:
    return RedisSettings.from_dsn(get_settings().redis_url)


async def run_scorecard_task(_ctx: dict[str, object], run_id: str, workspace_id: str) -> None:
    """Arq task: execute a run within its workspace's RLS context."""
    async with get_sessionmaker()() as session, session.begin():
        await set_workspace_context(session, uuid.UUID(workspace_id))
        await execute_run(session, uuid.UUID(run_id))


async def enqueue_scorecard_run(run_id: uuid.UUID, workspace_id: uuid.UUID) -> None:
    """Enqueue a run for the worker (deferred so the request commits first)."""
    pool = await create_pool(_redis_settings())
    try:
        await pool.enqueue_job(
            "run_scorecard_task",
            str(run_id),
            str(workspace_id),
            _defer_by=_ENQUEUE_DEFER_SECONDS,
        )
    finally:
        await pool.aclose()


def get_enqueue() -> Callable[[uuid.UUID, uuid.UUID], Awaitable[None]]:
    """FastAPI dependency returning the enqueue callable (overridable in tests)."""
    return enqueue_scorecard_run


class WorkerSettings:
    """Arq entrypoint configuration."""

    functions = (run_scorecard_task,)
    redis_settings = _redis_settings()
