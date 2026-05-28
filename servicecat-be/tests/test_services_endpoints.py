"""HTTP tests for the service catalog: guards, validation, soft delete, RLS."""

from __future__ import annotations

import uuid
from http import HTTPStatus
from typing import TYPE_CHECKING

from servicecat.models import User, Workspace, WorkspaceMembership
from servicecat.services.security import hash_password

if TYPE_CHECKING:
    from httpx import AsyncClient
    from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

PW = "catalog-pw0rd"
WS = uuid.UUID("d0000000-0000-0000-0000-00000000000d")
WS_OTHER = uuid.UUID("e0000000-0000-0000-0000-00000000000e")
ADMIN_EMAIL, ADMIN_ID = "admin@example.com", uuid.UUID("00000000-0000-0000-0000-0000000000a1")
MAINT_EMAIL, MAINT_ID = "maint@example.com", uuid.UUID("00000000-0000-0000-0000-0000000000a2")
VIEWER_EMAIL, VIEWER_ID = "viewer@example.com", uuid.UUID("00000000-0000-0000-0000-0000000000a3")
OTHER_EMAIL, OTHER_ID = "other@example.com", uuid.UUID("00000000-0000-0000-0000-0000000000b1")


async def _seed(sm: async_sessionmaker[AsyncSession]) -> None:
    async with sm() as session, session.begin():
        session.add_all(
            [
                Workspace(id=WS, name="Main", slug="main"),
                Workspace(id=WS_OTHER, name="Other", slug="other"),
                User(
                    id=ADMIN_ID, email=ADMIN_EMAIL, full_name="A", hashed_password=hash_password(PW)
                ),
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
                WorkspaceMembership(workspace_id=WS, user_id=ADMIN_ID, role="admin"),
                WorkspaceMembership(workspace_id=WS, user_id=MAINT_ID, role="maintainer"),
                WorkspaceMembership(workspace_id=WS, user_id=VIEWER_ID, role="viewer"),
                WorkspaceMembership(workspace_id=WS_OTHER, user_id=OTHER_ID, role="admin"),
            ],
        )


async def _token(client: AsyncClient, email: str) -> str:
    resp = await client.post("/api/v1/auth/login", json={"email": email, "password": PW})
    token: str = resp.json()["access_token"]
    return token


def _headers(token: str, workspace_id: uuid.UUID = WS) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}", "X-Workspace-Id": str(workspace_id)}


async def _create(
    client: AsyncClient, token: str, *, name: str = "payments", tier: int = 1
) -> object:
    return await client.post(
        "/api/v1/services",
        headers=_headers(token),
        json={"name": name, "repo_url": "https://example.com/repo", "tier": tier},
    )


async def test_maintainer_creates_service(
    auth_client: AsyncClient,
    rls_sessionmaker: async_sessionmaker[AsyncSession],
) -> None:
    await _seed(rls_sessionmaker)
    resp = await _create(auth_client, await _token(auth_client, MAINT_EMAIL))
    assert resp.status_code == HTTPStatus.CREATED
    body = resp.json()["data"]
    assert body["name"] == "payments"
    assert body["tier"] == 1
    assert body["workspace_id"] == str(WS)


async def test_viewer_cannot_create(
    auth_client: AsyncClient,
    rls_sessionmaker: async_sessionmaker[AsyncSession],
) -> None:
    await _seed(rls_sessionmaker)
    resp = await _create(auth_client, await _token(auth_client, VIEWER_EMAIL))
    assert resp.status_code == HTTPStatus.FORBIDDEN


async def test_create_invalid_tier_returns_422(
    auth_client: AsyncClient,
    rls_sessionmaker: async_sessionmaker[AsyncSession],
) -> None:
    await _seed(rls_sessionmaker)
    resp = await _create(auth_client, await _token(auth_client, MAINT_EMAIL), tier=9)
    assert resp.status_code == HTTPStatus.UNPROCESSABLE_ENTITY


async def test_list_returns_created_service(
    auth_client: AsyncClient,
    rls_sessionmaker: async_sessionmaker[AsyncSession],
) -> None:
    await _seed(rls_sessionmaker)
    token = await _token(auth_client, ADMIN_EMAIL)
    await _create(auth_client, token, name="svc-a")
    resp = await auth_client.get("/api/v1/services", headers=_headers(token))
    assert resp.status_code == HTTPStatus.OK
    body = resp.json()
    assert body["meta"]["total"] >= 1
    assert any(item["name"] == "svc-a" for item in body["data"])


async def test_get_missing_returns_404(
    auth_client: AsyncClient,
    rls_sessionmaker: async_sessionmaker[AsyncSession],
) -> None:
    await _seed(rls_sessionmaker)
    token = await _token(auth_client, ADMIN_EMAIL)
    resp = await auth_client.get(f"/api/v1/services/{uuid.uuid4()}", headers=_headers(token))
    assert resp.status_code == HTTPStatus.NOT_FOUND


async def test_maintainer_updates_service(
    auth_client: AsyncClient,
    rls_sessionmaker: async_sessionmaker[AsyncSession],
) -> None:
    await _seed(rls_sessionmaker)
    token = await _token(auth_client, MAINT_EMAIL)
    created = (await _create(auth_client, token)).json()["data"]
    resp = await auth_client.patch(
        f"/api/v1/services/{created['id']}",
        headers=_headers(token),
        json={"tier": 3},
    )
    assert resp.status_code == HTTPStatus.OK
    assert resp.json()["data"]["tier"] == 3


async def test_admin_soft_deletes_then_404(
    auth_client: AsyncClient,
    rls_sessionmaker: async_sessionmaker[AsyncSession],
) -> None:
    await _seed(rls_sessionmaker)
    token = await _token(auth_client, ADMIN_EMAIL)
    created = (await _create(auth_client, token)).json()["data"]
    deleted = await auth_client.delete(f"/api/v1/services/{created['id']}", headers=_headers(token))
    assert deleted.status_code == HTTPStatus.NO_CONTENT
    after = await auth_client.get(f"/api/v1/services/{created['id']}", headers=_headers(token))
    assert after.status_code == HTTPStatus.NOT_FOUND


async def test_maintainer_cannot_delete(
    auth_client: AsyncClient,
    rls_sessionmaker: async_sessionmaker[AsyncSession],
) -> None:
    await _seed(rls_sessionmaker)
    token = await _token(auth_client, MAINT_EMAIL)
    created = (await _create(auth_client, token)).json()["data"]
    resp = await auth_client.delete(f"/api/v1/services/{created['id']}", headers=_headers(token))
    assert resp.status_code == HTTPStatus.FORBIDDEN


async def test_cross_workspace_probe_returns_404(
    auth_client: AsyncClient,
    rls_sessionmaker: async_sessionmaker[AsyncSession],
) -> None:
    await _seed(rls_sessionmaker)
    created = (await _create(auth_client, await _token(auth_client, ADMIN_EMAIL))).json()["data"]
    other_token = await _token(auth_client, OTHER_EMAIL)
    # Other admin, scoped to WS_OTHER, cannot see WS's service: RLS hides it (404).
    resp = await auth_client.get(
        f"/api/v1/services/{created['id']}",
        headers=_headers(other_token, WS_OTHER),
    )
    assert resp.status_code == HTTPStatus.NOT_FOUND


async def test_list_filters_by_tier_and_owner(
    auth_client: AsyncClient,
    rls_sessionmaker: async_sessionmaker[AsyncSession],
) -> None:
    await _seed(rls_sessionmaker)
    token = await _token(auth_client, ADMIN_EMAIL)
    team = uuid.uuid4()
    await auth_client.post(
        "/api/v1/services",
        headers=_headers(token),
        json={
            "name": "owned",
            "repo_url": "https://e.com/r",
            "tier": 2,
            "owner_team_id": str(team),
        },
    )
    await _create(auth_client, token, name="plain", tier=1)

    by_tier = await auth_client.get("/api/v1/services?tier=2", headers=_headers(token))
    assert [item["name"] for item in by_tier.json()["data"]] == ["owned"]

    by_owner = await auth_client.get(
        f"/api/v1/services?owner_team_id={team}",
        headers=_headers(token),
    )
    assert [item["name"] for item in by_owner.json()["data"]] == ["owned"]


async def test_duplicate_name_returns_409(
    auth_client: AsyncClient,
    rls_sessionmaker: async_sessionmaker[AsyncSession],
) -> None:
    await _seed(rls_sessionmaker)
    token = await _token(auth_client, MAINT_EMAIL)
    first = await _create(auth_client, token, name="dupe")
    assert first.status_code == HTTPStatus.CREATED
    again = await _create(auth_client, token, name="dupe")
    assert again.status_code == HTTPStatus.CONFLICT
    assert again.json()["error"]["code"] == "CONFLICT"


async def test_rename_to_existing_name_returns_409(
    auth_client: AsyncClient,
    rls_sessionmaker: async_sessionmaker[AsyncSession],
) -> None:
    await _seed(rls_sessionmaker)
    token = await _token(auth_client, MAINT_EMAIL)
    await _create(auth_client, token, name="alpha")
    beta = (await _create(auth_client, token, name="beta")).json()["data"]
    resp = await auth_client.patch(
        f"/api/v1/services/{beta['id']}",
        headers=_headers(token),
        json={"name": "alpha"},
    )
    assert resp.status_code == HTTPStatus.CONFLICT
    assert resp.json()["error"]["code"] == "CONFLICT"
