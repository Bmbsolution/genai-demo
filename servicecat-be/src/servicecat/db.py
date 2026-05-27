"""Async database engine, session factory, and row-level-security helpers."""

from __future__ import annotations

from functools import lru_cache
from typing import TYPE_CHECKING

from sqlalchemy import text
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from servicecat.config import get_settings

if TYPE_CHECKING:
    import uuid


@lru_cache(maxsize=1)
def get_engine() -> AsyncEngine:
    """Return the process-wide async engine."""
    return create_async_engine(get_settings().database_url, pool_pre_ping=True)


@lru_cache(maxsize=1)
def get_sessionmaker() -> async_sessionmaker[AsyncSession]:
    """Return the process-wide async session factory."""
    return async_sessionmaker(get_engine(), expire_on_commit=False, class_=AsyncSession)


async def set_workspace_context(session: AsyncSession, workspace_id: uuid.UUID) -> None:
    """Pin the RLS workspace for the current transaction.

    Uses ``set_config(..., is_local => true)`` so the GUC is transaction-scoped
    and cleared automatically on commit or rollback — no leakage between
    requests that reuse a pooled connection.
    """
    await session.execute(
        text("SELECT set_config('app.workspace_id', :workspace_id, true)"),
        {"workspace_id": str(workspace_id)},
    )
