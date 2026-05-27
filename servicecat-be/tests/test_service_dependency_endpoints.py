"""HTTP tests for service dependencies: declare, cycles, traversal, guards, RLS."""

from __future__ import annotations

import uuid
from http import HTTPStatus
from typing import TYPE_CHECKING

from servicecat.models import Service, User, Workspace, WorkspaceMembership
from servicecat.services.security import hash_password

if TYPE_CHECKING:
    from httpx import AsyncClient
    from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

PW = "deps-pw0rd"
WS = uuid.UUID("a5550000-0000-0000-0000-0000000000a5")
WS_OTHER = uuid.UUID("b5550000-0000-0000-0000-0000000000b5")
SVC_A = uuid.UUID("00000000-0000-0000-0000-00000000000a")
SVC_B = uuid.UUID("00000000-0000-0000-0000-00000000000b")
SVC_C = uuid.UUID("00000000-0000-0000-0000-00000000000c")
MAINT_EMAIL, MAINT_ID = "maint@example.com", uuid.UUID("00000000-0000-0000-0000-0000000000f1")
VIEWER_EMAIL, VIEWER_ID = "viewer@example.com", uuid.UUID("00000000-0000-0000-0000-0000000000f2")
OTHER_EMAIL, OTHER_ID = "other@example.com", uuid.UUID("00000000-0000-0000-0000-0000000000f3")


def _service(service_id: uuid.UUID, name: str, workspace_id: uuid.UUID = WS) -> Service:
    return Service(
        id=service_id,
        workspace_id=workspace_id,
        name=name,
        repo_url="https://e.com/r",
        tier=1,
    )


async def _seed(sm: async_sessionmaker[AsyncSession]) -> None:
    async with sm() as session, session.begin():
        session.add_all(
            [
                Workspace(id=WS, name="Main", slug="main"),
                Workspace(id=WS_OTHER, name="Other", slug="other"),
                User(
                    id=MAINT_ID, email=MAINT_EMAIL, full_name="M", hashed_password=hash_password(PW)
                ),
                User(
                    id=VIEWER_ID,
                    email=VIEWER_EMAIL,
                    full_name="V",
                    hashed_password=hash_password(PW),
                ),
                User(
                    id=OTHER_ID, email=OTHER_EMAIL, full_name="O", hashed_password=hash_password(PW)
                ),
            ],
        )
        await session.flush()
        session.add_all(
            [
                WorkspaceMembership(workspace_id=WS, user_id=MAINT_ID, role="maintainer"),
                WorkspaceMembership(workspace_id=WS, user_id=VIEWER_ID, role="viewer"),
                WorkspaceMembership(workspace_id=WS_OTHER, user_id=OTHER_ID, role="admin"),
                _service(SVC_A, "a"),
                _service(SVC_B, "b"),
                _service(SVC_C, "c"),
            ],
        )


async def _token(client: AsyncClient, email: str) -> str:
    resp = await client.post("/api/v1/auth/login", json={"email": email, "password": PW})
    token: str = resp.json()["access_token"]
    return token


def _headers(token: str, workspace_id: uuid.UUID = WS) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}", "X-Workspace-Id": str(workspace_id)}


async def _add(
    client: AsyncClient,
    token: str,
    service_id: uuid.UUID,
    depends_on: uuid.UUID,
) -> object:
    return await client.post(
        f"/api/v1/services/{service_id}/dependencies",
        headers=_headers(token),
        json={
            "depends_on_service_id": str(depends_on),
            "criticality": "hard",
            "direction": "consumes",
        },
    )


async def test_maintainer_adds_dependency(
    auth_client: AsyncClient,
    rls_sessionmaker: async_sessionmaker[AsyncSession],
) -> None:
    await _seed(rls_sessionmaker)
    token = await _token(auth_client, MAINT_EMAIL)
    resp = await _add(auth_client, token, SVC_A, SVC_B)
    assert resp.status_code == HTTPStatus.CREATED
    body = resp.json()
    assert body["depends_on_service_id"] == str(SVC_B)
    assert body["depth"] == 1


async def test_viewer_cannot_add(
    auth_client: AsyncClient,
    rls_sessionmaker: async_sessionmaker[AsyncSession],
) -> None:
    await _seed(rls_sessionmaker)
    token = await _token(auth_client, VIEWER_EMAIL)
    resp = await _add(auth_client, token, SVC_A, SVC_B)
    assert resp.status_code == HTTPStatus.FORBIDDEN


async def test_self_dependency_rejected(
    auth_client: AsyncClient,
    rls_sessionmaker: async_sessionmaker[AsyncSession],
) -> None:
    await _seed(rls_sessionmaker)
    token = await _token(auth_client, MAINT_EMAIL)
    resp = await _add(auth_client, token, SVC_A, SVC_A)
    assert resp.status_code == HTTPStatus.UNPROCESSABLE_ENTITY


async def test_duplicate_rejected(
    auth_client: AsyncClient,
    rls_sessionmaker: async_sessionmaker[AsyncSession],
) -> None:
    await _seed(rls_sessionmaker)
    token = await _token(auth_client, MAINT_EMAIL)
    assert (await _add(auth_client, token, SVC_A, SVC_B)).status_code == HTTPStatus.CREATED
    assert (await _add(auth_client, token, SVC_A, SVC_B)).status_code == HTTPStatus.CONFLICT


async def test_cycle_rejected(
    auth_client: AsyncClient,
    rls_sessionmaker: async_sessionmaker[AsyncSession],
) -> None:
    await _seed(rls_sessionmaker)
    token = await _token(auth_client, MAINT_EMAIL)
    assert (await _add(auth_client, token, SVC_A, SVC_B)).status_code == HTTPStatus.CREATED
    assert (await _add(auth_client, token, SVC_B, SVC_C)).status_code == HTTPStatus.CREATED
    # C -> A would close the cycle A -> B -> C -> A.
    assert (
        await _add(auth_client, token, SVC_C, SVC_A)
    ).status_code == HTTPStatus.UNPROCESSABLE_ENTITY


async def test_list_depth_one_and_two(
    auth_client: AsyncClient,
    rls_sessionmaker: async_sessionmaker[AsyncSession],
) -> None:
    await _seed(rls_sessionmaker)
    token = await _token(auth_client, MAINT_EMAIL)
    await _add(auth_client, token, SVC_A, SVC_B)
    await _add(auth_client, token, SVC_B, SVC_C)

    depth1 = await auth_client.get(
        f"/api/v1/services/{SVC_A}/dependencies?depth=1",
        headers=_headers(token),
    )
    assert {edge["depends_on_service_id"] for edge in depth1.json()} == {str(SVC_B)}

    depth2 = await auth_client.get(
        f"/api/v1/services/{SVC_A}/dependencies?depth=2",
        headers=_headers(token),
    )
    assert {edge["depends_on_service_id"] for edge in depth2.json()} == {str(SVC_B), str(SVC_C)}


async def test_remove_dependency(
    auth_client: AsyncClient,
    rls_sessionmaker: async_sessionmaker[AsyncSession],
) -> None:
    await _seed(rls_sessionmaker)
    token = await _token(auth_client, MAINT_EMAIL)
    created = (await _add(auth_client, token, SVC_A, SVC_B)).json()
    deleted = await auth_client.delete(
        f"/api/v1/services/{SVC_A}/dependencies/{created['id']}",
        headers=_headers(token),
    )
    assert deleted.status_code == HTTPStatus.NO_CONTENT
    listed = await auth_client.get(
        f"/api/v1/services/{SVC_A}/dependencies",
        headers=_headers(token),
    )
    assert listed.json() == []


async def test_cross_workspace_add_returns_404(
    auth_client: AsyncClient,
    rls_sessionmaker: async_sessionmaker[AsyncSession],
) -> None:
    await _seed(rls_sessionmaker)
    other = await _token(auth_client, OTHER_EMAIL)
    # Other admin (workspace B) cannot touch workspace A's service.
    resp = await auth_client.post(
        f"/api/v1/services/{SVC_A}/dependencies",
        headers=_headers(other, WS_OTHER),
        json={
            "depends_on_service_id": str(SVC_B),
            "criticality": "hard",
            "direction": "consumes",
        },
    )
    assert resp.status_code == HTTPStatus.NOT_FOUND
