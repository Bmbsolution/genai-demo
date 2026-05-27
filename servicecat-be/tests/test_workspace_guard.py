"""Integration tests for S2 (get_current_workspace) and S3 (require_capability)."""

from __future__ import annotations

import uuid
from typing import TYPE_CHECKING

import pytest

from servicecat.deps import get_current_workspace, require_capability
from servicecat.errors import AuthorizationError, WorkspaceIsolationError
from servicecat.models import User, Workspace, WorkspaceMembership, WorkspaceRole
from servicecat.rbac import Capability
from servicecat.services.rbac_service import user_has_capability

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

WS_A = uuid.UUID("aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa")
WS_B = uuid.UUID("bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb")
USER_ID = uuid.UUID("cccccccc-cccc-cccc-cccc-cccccccccccc")


async def _seed(sm: async_sessionmaker[AsyncSession]) -> None:
    """User is a MAINTAINER in workspace A and not a member of workspace B."""
    async with sm() as session, session.begin():
        session.add_all(
            [
                Workspace(id=WS_A, name="Acme", slug="acme"),
                Workspace(id=WS_B, name="Beta", slug="beta"),
                User(id=USER_ID, email="u@example.com", full_name="U"),
            ],
        )
        await session.flush()
        session.add(
            WorkspaceMembership(workspace_id=WS_A, user_id=USER_ID, role="maintainer"),
        )


def _user() -> User:
    return User(id=USER_ID, email="u@example.com", full_name="U")


async def test_resolves_role_for_member(
    rls_sessionmaker: async_sessionmaker[AsyncSession],
) -> None:
    await _seed(rls_sessionmaker)
    async with rls_sessionmaker() as session, session.begin():
        ctx = await get_current_workspace(user=_user(), db=session, workspace_id=WS_A)
        assert ctx.role is WorkspaceRole.MAINTAINER
        assert ctx.workspace.id == WS_A


async def test_rejects_non_member_workspace(
    rls_sessionmaker: async_sessionmaker[AsyncSession],
) -> None:
    await _seed(rls_sessionmaker)
    async with rls_sessionmaker() as session, session.begin():
        with pytest.raises(WorkspaceIsolationError):
            await get_current_workspace(user=_user(), db=session, workspace_id=WS_B)


async def test_require_capability_allows_then_denies(
    rls_sessionmaker: async_sessionmaker[AsyncSession],
) -> None:
    await _seed(rls_sessionmaker)
    async with rls_sessionmaker() as session, session.begin():
        ctx = await get_current_workspace(user=_user(), db=session, workspace_id=WS_A)
        # Maintainer has service:write ...
        await require_capability(Capability.SERVICE_WRITE)(context=ctx)
        # ... but not workspace:settings.
        with pytest.raises(AuthorizationError):
            await require_capability(Capability.WORKSPACE_SETTINGS)(context=ctx)


async def test_user_has_capability_respects_role_and_membership(
    rls_sessionmaker: async_sessionmaker[AsyncSession],
) -> None:
    await _seed(rls_sessionmaker)
    async with rls_sessionmaker() as session, session.begin():
        assert await user_has_capability(session, USER_ID, WS_A, Capability.SERVICE_READ) is True
        assert await user_has_capability(session, USER_ID, WS_A, Capability.SERVICE_DELETE) is False
        # Not a member of workspace B -> no capability at all.
        assert await user_has_capability(session, USER_ID, WS_B, Capability.SERVICE_READ) is False
