"""HTTP test for workspace discovery (GET /api/v1/workspaces)."""

from __future__ import annotations

import uuid
from http import HTTPStatus
from typing import TYPE_CHECKING

from servicecat.models import User, Workspace, WorkspaceMembership
from servicecat.services.security import hash_password

if TYPE_CHECKING:
    from httpx import AsyncClient
    from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

PW = "ws-pw0rd"
WS1 = uuid.UUID("d1110000-0000-0000-0000-0000000000d1")
WS2 = uuid.UUID("d2220000-0000-0000-0000-0000000000d2")
USER = uuid.UUID("d3330000-0000-0000-0000-0000000000d3")
EMAIL = "member@example.com"


async def _seed(sm: async_sessionmaker[AsyncSession]) -> None:
    async with sm() as session, session.begin():
        session.add_all(
            [
                Workspace(id=WS1, name="Alpha", slug="alpha"),
                Workspace(id=WS2, name="Beta", slug="beta"),
                User(id=USER, email=EMAIL, full_name="U", hashed_password=hash_password(PW)),
            ],
        )
        await session.flush()
        session.add_all(
            [
                WorkspaceMembership(workspace_id=WS1, user_id=USER, role="admin"),
                WorkspaceMembership(workspace_id=WS2, user_id=USER, role="viewer"),
            ],
        )


async def test_lists_the_users_workspaces(
    auth_client: AsyncClient,
    rls_sessionmaker: async_sessionmaker[AsyncSession],
) -> None:
    await _seed(rls_sessionmaker)
    tokens = (
        await auth_client.post("/api/v1/auth/login", json={"email": EMAIL, "password": PW})
    ).json()
    resp = await auth_client.get(
        "/api/v1/workspaces",
        headers={"Authorization": f"Bearer {tokens['access_token']}"},
    )
    assert resp.status_code == HTTPStatus.OK
    body = resp.json()
    assert {row["slug"] for row in body} == {"alpha", "beta"}
    assert {row["role"] for row in body} == {"admin", "viewer"}


async def test_requires_authentication(auth_client: AsyncClient) -> None:
    resp = await auth_client.get("/api/v1/workspaces")
    assert resp.status_code == HTTPStatus.UNAUTHORIZED
