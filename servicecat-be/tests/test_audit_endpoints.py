"""HTTP tests for GET /audit/logs — all five guards: admin allowed, viewer 403."""

from __future__ import annotations

import uuid
from http import HTTPStatus
from typing import TYPE_CHECKING

from servicecat.models import User, Workspace, WorkspaceMembership
from servicecat.services.security import hash_password

if TYPE_CHECKING:
    from httpx import AsyncClient
    from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

PW = "audit-endpoint-pw0rd"


async def _seed_member(
    sm: async_sessionmaker[AsyncSession],
    *,
    workspace_id: uuid.UUID,
    user_id: uuid.UUID,
    email: str,
    role: str,
) -> None:
    async with sm() as session, session.begin():
        session.add_all(
            [
                Workspace(id=workspace_id, name="W", slug=email.split("@", maxsplit=1)[0]),
                User(id=user_id, email=email, full_name="U", hashed_password=hash_password(PW)),
            ],
        )
        await session.flush()
        session.add(WorkspaceMembership(workspace_id=workspace_id, user_id=user_id, role=role))


async def _login(client: AsyncClient, email: str) -> str:
    resp = await client.post("/api/v1/auth/login", json={"email": email, "password": PW})
    token: str = resp.json()["access_token"]
    return token


async def test_admin_can_list_and_request_is_audited(
    auth_client: AsyncClient,
    rls_sessionmaker: async_sessionmaker[AsyncSession],
) -> None:
    workspace_id, user_id = uuid.uuid4(), uuid.uuid4()
    await _seed_member(
        rls_sessionmaker,
        workspace_id=workspace_id,
        user_id=user_id,
        email="admin@example.com",
        role="admin",
    )
    token = await _login(auth_client, "admin@example.com")
    resp = await auth_client.get(
        "/api/v1/audit/logs",
        headers={"Authorization": f"Bearer {token}", "X-Workspace-Id": str(workspace_id)},
    )
    assert resp.status_code == HTTPStatus.OK
    # S5: the read itself was recorded (and is visible read-your-writes).
    assert any(entry["action"] == "audit.list" for entry in resp.json()["data"])


async def test_viewer_is_forbidden(
    auth_client: AsyncClient,
    rls_sessionmaker: async_sessionmaker[AsyncSession],
) -> None:
    workspace_id, user_id = uuid.uuid4(), uuid.uuid4()
    await _seed_member(
        rls_sessionmaker,
        workspace_id=workspace_id,
        user_id=user_id,
        email="viewer@example.com",
        role="viewer",
    )
    token = await _login(auth_client, "viewer@example.com")
    resp = await auth_client.get(
        "/api/v1/audit/logs",
        headers={"Authorization": f"Bearer {token}", "X-Workspace-Id": str(workspace_id)},
    )
    assert resp.status_code == HTTPStatus.FORBIDDEN
