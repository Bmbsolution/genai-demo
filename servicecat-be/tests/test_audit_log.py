"""DB-level guarantees for audit_logs: append-only + workspace RLS."""

from __future__ import annotations

import uuid
from typing import TYPE_CHECKING

import pytest
from sqlalchemy import select, text
from sqlalchemy.exc import DBAPIError

from servicecat.db import set_workspace_context
from servicecat.models import AuditLog, Workspace

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

WS_A = uuid.UUID("a0000000-0000-0000-0000-0000000000a1")
WS_B = uuid.UUID("b0000000-0000-0000-0000-0000000000b2")


async def _seed(sm: async_sessionmaker[AsyncSession]) -> None:
    async with sm() as session, session.begin():
        session.add_all(
            [Workspace(id=WS_A, name="A", slug="a"), Workspace(id=WS_B, name="B", slug="b")],
        )
        await session.flush()
        session.add_all(
            [
                AuditLog(
                    workspace_id=WS_A, actor_id=uuid.uuid4(), action="x.do", resource_type="x"
                ),
                AuditLog(
                    workspace_id=WS_B, actor_id=uuid.uuid4(), action="y.do", resource_type="y"
                ),
            ],
        )


async def test_update_is_blocked(rls_sessionmaker: async_sessionmaker[AsyncSession]) -> None:
    await _seed(rls_sessionmaker)

    async def _update() -> None:
        async with rls_sessionmaker() as session, session.begin():
            await session.execute(text("UPDATE audit_logs SET action = 'tampered'"))

    with pytest.raises(DBAPIError, match="append-only"):
        await _update()


async def test_delete_is_blocked(rls_sessionmaker: async_sessionmaker[AsyncSession]) -> None:
    await _seed(rls_sessionmaker)

    async def _delete() -> None:
        async with rls_sessionmaker() as session, session.begin():
            await session.execute(text("DELETE FROM audit_logs"))

    with pytest.raises(DBAPIError, match="append-only"):
        await _delete()


async def test_rls_isolates_audit_logs_by_workspace(
    rls_sessionmaker: async_sessionmaker[AsyncSession],
) -> None:
    await _seed(rls_sessionmaker)
    async with rls_sessionmaker() as session, session.begin():
        await set_workspace_context(session, WS_A)
        actions = (await session.execute(select(AuditLog.action))).scalars().all()
    assert actions == ["x.do"]
