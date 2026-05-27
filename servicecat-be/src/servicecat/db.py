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

# Non-privileged role the application runs queries as. The bootstrap DB user is
# a superuser and would *bypass* RLS, so each request switches into this role
# (created by migration 0001) before touching workspace-scoped tables.
APP_DB_ROLE = "servicecat_app"

# SET ROLE takes an identifier, not a bind parameter; the value is a trusted
# constant defined here, never user input.
_SET_APP_ROLE = text(f"SET LOCAL ROLE {APP_DB_ROLE}")
_SET_WORKSPACE_GUC = text("SELECT set_config('app.workspace_id', :workspace_id, true)")


@lru_cache(maxsize=1)
def get_engine() -> AsyncEngine:
    """Return the process-wide async engine."""
    return create_async_engine(get_settings().database_url, pool_pre_ping=True)


@lru_cache(maxsize=1)
def get_sessionmaker() -> async_sessionmaker[AsyncSession]:
    """Return the process-wide async session factory."""
    return async_sessionmaker(get_engine(), expire_on_commit=False, class_=AsyncSession)


async def set_workspace_context(session: AsyncSession, workspace_id: uuid.UUID) -> None:
    """Enter the RLS context for ``workspace_id`` on the current transaction.

    Two transaction-local effects (both reset on commit/rollback, so a pooled
    connection never leaks state to the next request):

    1. ``SET LOCAL ROLE servicecat_app`` — drop superuser privileges so the
       RLS policies are actually enforced.
    2. ``set_config('app.workspace_id', ..., is_local => true)`` — the GUC the
       ``workspace_isolation`` policies compare against.

    Must be called inside an open transaction (``SET LOCAL`` requires one).
    """
    await session.execute(_SET_APP_ROLE)
    await session.execute(_SET_WORKSPACE_GUC, {"workspace_id": str(workspace_id)})
