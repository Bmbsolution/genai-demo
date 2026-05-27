"""Row-Level Security: workspace isolation is actually enforced, not assumed."""

from __future__ import annotations

import uuid
from typing import TYPE_CHECKING

import pytest
from sqlalchemy import func, select, text
from sqlalchemy.exc import ProgrammingError

from servicecat.db import set_workspace_context
from servicecat.models import User, Workspace, WorkspaceMembership

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

WS_A = uuid.UUID("11111111-1111-1111-1111-111111111111")
WS_B = uuid.UUID("22222222-2222-2222-2222-222222222222")
USER_A = uuid.UUID("33333333-3333-3333-3333-333333333333")
USER_B = uuid.UUID("44444444-4444-4444-4444-444444444444")


async def _seed(sm: async_sessionmaker[AsyncSession]) -> None:
    """Plant one membership in each workspace as the superuser (RLS bypassed)."""
    async with sm() as session, session.begin():
        session.add_all(
            [
                Workspace(id=WS_A, name="Acme", slug="acme"),
                Workspace(id=WS_B, name="Beta", slug="beta"),
                User(id=USER_A, email="a@example.com", full_name="A"),
                User(id=USER_B, email="b@example.com", full_name="B"),
            ]
        )
        await session.flush()  # parents must land before the FK-bearing children
        session.add_all(
            [
                WorkspaceMembership(workspace_id=WS_A, user_id=USER_A, role="admin"),
                WorkspaceMembership(workspace_id=WS_B, user_id=USER_B, role="admin"),
            ]
        )


async def test_membership_visible_only_in_its_workspace(
    rls_sessionmaker: async_sessionmaker[AsyncSession],
) -> None:
    await _seed(rls_sessionmaker)
    async with rls_sessionmaker() as session, session.begin():
        await set_workspace_context(session, WS_A)
        rows = (await session.execute(select(WorkspaceMembership.workspace_id))).scalars().all()
    assert rows == [WS_A]


async def test_switching_workspace_changes_visibility(
    rls_sessionmaker: async_sessionmaker[AsyncSession],
) -> None:
    await _seed(rls_sessionmaker)
    async with rls_sessionmaker() as session, session.begin():
        await set_workspace_context(session, WS_B)
        count = await session.scalar(select(func.count()).select_from(WorkspaceMembership))
    assert count == 1


async def test_workspaces_table_isolated(
    rls_sessionmaker: async_sessionmaker[AsyncSession],
) -> None:
    await _seed(rls_sessionmaker)
    async with rls_sessionmaker() as session, session.begin():
        await set_workspace_context(session, WS_A)
        slugs = (await session.execute(select(Workspace.slug))).scalars().all()
    assert slugs == ["acme"]


async def test_no_workspace_context_denies_all(
    rls_sessionmaker: async_sessionmaker[AsyncSession],
) -> None:
    await _seed(rls_sessionmaker)
    async with rls_sessionmaker() as session, session.begin():
        # Enter the app role but set no workspace -> policy yields NULL -> deny.
        await session.execute(text("SET LOCAL ROLE servicecat_app"))
        count = await session.scalar(select(func.count()).select_from(WorkspaceMembership))
    assert count == 0


async def test_cross_workspace_insert_is_blocked(
    rls_sessionmaker: async_sessionmaker[AsyncSession],
) -> None:
    await _seed(rls_sessionmaker)

    async def _insert_into_foreign_workspace() -> None:
        async with rls_sessionmaker() as session, session.begin():
            await set_workspace_context(session, WS_A)
            session.add(
                WorkspaceMembership(workspace_id=WS_B, user_id=USER_A, role="viewer"),
            )
            await session.flush()

    with pytest.raises(ProgrammingError, match="row-level security"):
        await _insert_into_foreign_workspace()


async def test_app_role_is_unprivileged(
    rls_sessionmaker: async_sessionmaker[AsyncSession],
) -> None:
    # If the effective role were a superuser or had BYPASSRLS, the policies
    # would be silently void and every isolation test would pass by accident.
    async with rls_sessionmaker() as session, session.begin():
        await set_workspace_context(session, WS_A)
        current_user = await session.scalar(text("SELECT current_user"))
        bypasses_rls = await session.scalar(
            text("SELECT rolbypassrls FROM pg_roles WHERE rolname = current_user"),
        )
    assert current_user == "servicecat_app"
    assert bypasses_rls is False


async def test_insert_without_context_is_blocked(
    rls_sessionmaker: async_sessionmaker[AsyncSession],
) -> None:
    await _seed(rls_sessionmaker)

    async def _insert_with_no_workspace() -> None:
        async with rls_sessionmaker() as session, session.begin():
            await session.execute(text("SET LOCAL ROLE servicecat_app"))
            session.add(
                WorkspaceMembership(workspace_id=WS_A, user_id=USER_B, role="viewer"),
            )
            await session.flush()

    with pytest.raises(ProgrammingError, match="row-level security"):
        await _insert_with_no_workspace()
