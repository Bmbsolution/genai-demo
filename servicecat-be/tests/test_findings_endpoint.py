"""HTTP tests for the findings dashboard (GET /api/v1/findings)."""

from __future__ import annotations

import uuid
from http import HTTPStatus
from typing import TYPE_CHECKING

from servicecat.models import (
    Finding,
    ScorecardRun,
    ScorecardRunStatus,
    Service,
    User,
    Workspace,
    WorkspaceMembership,
)
from servicecat.services.security import hash_password

if TYPE_CHECKING:
    from httpx import AsyncClient
    from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

PW = "findings-pw0rd"
WS = uuid.UUID("c1110000-0000-0000-0000-0000000000c1")
WS_OTHER = uuid.UUID("c2220000-0000-0000-0000-0000000000c2")
SVC = uuid.UUID("c3330000-0000-0000-0000-0000000000c3")
RUN = uuid.UUID("c4440000-0000-0000-0000-0000000000c4")
ADMIN_EMAIL, ADMIN_ID = "admin@example.com", uuid.UUID("00000000-0000-0000-0000-0000000000c5")
VIEWER_EMAIL, VIEWER_ID = "viewer@example.com", uuid.UUID("00000000-0000-0000-0000-0000000000c6")
OTHER_EMAIL, OTHER_ID = "other@example.com", uuid.UUID("00000000-0000-0000-0000-0000000000c7")


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
                WorkspaceMembership(workspace_id=WS, user_id=VIEWER_ID, role="viewer"),
                WorkspaceMembership(workspace_id=WS_OTHER, user_id=OTHER_ID, role="admin"),
                Service(id=SVC, workspace_id=WS, name="svc", repo_url="https://e.com/r", tier=1),
                ScorecardRun(
                    id=RUN,
                    workspace_id=WS,
                    scorecard="documentation",
                    status=ScorecardRunStatus.COMPLETED,
                    triggered_by=ADMIN_ID,
                    target_service_ids=[str(SVC)],
                    finding_count=2,
                ),
            ],
        )
        await session.flush()
        session.add_all(
            [
                Finding(
                    workspace_id=WS,
                    run_id=RUN,
                    service_id=SVC,
                    criterion_id="doc.readme_present",
                    severity="high",
                    remediation="Add a README.",
                ),
                Finding(
                    workspace_id=WS,
                    run_id=RUN,
                    service_id=SVC,
                    criterion_id="doc.codeowners",
                    severity="medium",
                    remediation="Add CODEOWNERS.",
                ),
            ],
        )


async def _token(client: AsyncClient, email: str) -> str:
    resp = await client.post("/api/v1/auth/login", json={"email": email, "password": PW})
    token: str = resp.json()["access_token"]
    return token


def _headers(token: str, workspace_id: uuid.UUID = WS) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}", "X-Workspace-Id": str(workspace_id)}


async def test_admin_lists_findings(
    auth_client: AsyncClient,
    rls_sessionmaker: async_sessionmaker[AsyncSession],
) -> None:
    await _seed(rls_sessionmaker)
    resp = await auth_client.get(
        "/api/v1/findings",
        headers=_headers(await _token(auth_client, ADMIN_EMAIL)),
    )
    assert resp.status_code == HTTPStatus.OK
    body = resp.json()
    assert body["meta"]["total"] == 2
    assert {row["criterion_id"] for row in body["data"]} == {"doc.readme_present", "doc.codeowners"}


async def test_filter_by_severity(
    auth_client: AsyncClient,
    rls_sessionmaker: async_sessionmaker[AsyncSession],
) -> None:
    await _seed(rls_sessionmaker)
    resp = await auth_client.get(
        "/api/v1/findings?severity=high",
        headers=_headers(await _token(auth_client, ADMIN_EMAIL)),
    )
    assert [row["criterion_id"] for row in resp.json()["data"]] == ["doc.readme_present"]


async def test_viewer_can_read_findings(
    auth_client: AsyncClient,
    rls_sessionmaker: async_sessionmaker[AsyncSession],
) -> None:
    await _seed(rls_sessionmaker)
    resp = await auth_client.get(
        "/api/v1/findings",
        headers=_headers(await _token(auth_client, VIEWER_EMAIL)),
    )
    assert resp.status_code == HTTPStatus.OK


async def test_findings_are_workspace_isolated(
    auth_client: AsyncClient,
    rls_sessionmaker: async_sessionmaker[AsyncSession],
) -> None:
    await _seed(rls_sessionmaker)
    resp = await auth_client.get(
        "/api/v1/findings",
        headers=_headers(await _token(auth_client, OTHER_EMAIL), WS_OTHER),
    )
    assert resp.status_code == HTTPStatus.OK
    assert resp.json()["meta"]["total"] == 0
