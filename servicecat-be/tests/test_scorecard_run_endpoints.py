"""HTTP tests for scorecard run trigger/status: guards, 202, validation, RLS."""

from __future__ import annotations

import uuid
from http import HTTPStatus
from typing import TYPE_CHECKING

from servicecat.models import Service, User, Workspace, WorkspaceMembership
from servicecat.services.security import hash_password

if TYPE_CHECKING:
    from httpx import AsyncClient
    from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

PW = "runs-pw0rd"
WS = uuid.UUID("a1110000-0000-0000-0000-0000000000a1")
WS_OTHER = uuid.UUID("b2220000-0000-0000-0000-0000000000b2")
SERVICE = uuid.UUID("c3330000-0000-0000-0000-0000000000c3")
MAINT_EMAIL, MAINT_ID = "maint@example.com", uuid.UUID("00000000-0000-0000-0000-0000000000e1")
VIEWER_EMAIL, VIEWER_ID = "viewer@example.com", uuid.UUID("00000000-0000-0000-0000-0000000000e2")
OTHER_EMAIL, OTHER_ID = "other@example.com", uuid.UUID("00000000-0000-0000-0000-0000000000e3")


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
                Service(
                    id=SERVICE, workspace_id=WS, name="svc", repo_url="https://e.com/r", tier=1
                ),
            ],
        )


async def _token(client: AsyncClient, email: str) -> str:
    resp = await client.post("/api/v1/auth/login", json={"email": email, "password": PW})
    token: str = resp.json()["access_token"]
    return token


def _headers(token: str, workspace_id: uuid.UUID = WS) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}", "X-Workspace-Id": str(workspace_id)}


async def test_maintainer_triggers_run_and_reads_status(
    auth_client: AsyncClient,
    rls_sessionmaker: async_sessionmaker[AsyncSession],
) -> None:
    await _seed(rls_sessionmaker)
    token = await _token(auth_client, MAINT_EMAIL)
    resp = await auth_client.post(
        "/api/v1/scorecards/documentation/runs",
        headers=_headers(token),
        json={"target_service_ids": [str(SERVICE)]},
    )
    assert resp.status_code == HTTPStatus.ACCEPTED
    run = resp.json()
    assert run["status"] == "queued"
    status_resp = await auth_client.get(
        f"/api/v1/scorecards/runs/{run['id']}",
        headers=_headers(token),
    )
    assert status_resp.status_code == HTTPStatus.OK
    assert status_resp.json()["finding_count"] == 0


async def test_viewer_cannot_trigger_run(
    auth_client: AsyncClient,
    rls_sessionmaker: async_sessionmaker[AsyncSession],
) -> None:
    await _seed(rls_sessionmaker)
    token = await _token(auth_client, VIEWER_EMAIL)
    resp = await auth_client.post(
        "/api/v1/scorecards/documentation/runs",
        headers=_headers(token),
        json={"target_service_ids": [str(SERVICE)]},
    )
    assert resp.status_code == HTTPStatus.FORBIDDEN


async def test_unknown_scorecard_returns_404(
    auth_client: AsyncClient,
    rls_sessionmaker: async_sessionmaker[AsyncSession],
) -> None:
    await _seed(rls_sessionmaker)
    token = await _token(auth_client, MAINT_EMAIL)
    resp = await auth_client.post(
        "/api/v1/scorecards/nope/runs",
        headers=_headers(token),
        json={"target_service_ids": [str(SERVICE)]},
    )
    assert resp.status_code == HTTPStatus.NOT_FOUND


async def test_empty_targets_returns_422(
    auth_client: AsyncClient,
    rls_sessionmaker: async_sessionmaker[AsyncSession],
) -> None:
    await _seed(rls_sessionmaker)
    token = await _token(auth_client, MAINT_EMAIL)
    resp = await auth_client.post(
        "/api/v1/scorecards/documentation/runs",
        headers=_headers(token),
        json={"target_service_ids": []},
    )
    assert resp.status_code == HTTPStatus.UNPROCESSABLE_ENTITY


async def test_run_is_workspace_isolated(
    auth_client: AsyncClient,
    rls_sessionmaker: async_sessionmaker[AsyncSession],
) -> None:
    await _seed(rls_sessionmaker)
    maint = await _token(auth_client, MAINT_EMAIL)
    created = (
        await auth_client.post(
            "/api/v1/scorecards/documentation/runs",
            headers=_headers(maint),
            json={"target_service_ids": [str(SERVICE)]},
        )
    ).json()
    other = await _token(auth_client, OTHER_EMAIL)
    resp = await auth_client.get(
        f"/api/v1/scorecards/runs/{created['id']}",
        headers=_headers(other, WS_OTHER),
    )
    assert resp.status_code == HTTPStatus.NOT_FOUND


# Note: the S4 rate limiter is covered deterministically in test_redis_guards.py
# (unique key, direct call). An HTTP "11th request -> 429" test here would be
# flaky because the fixed window is wall-clock-minute-aligned and a burst can
# straddle a minute boundary.
