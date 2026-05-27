"""HTTP-level tests for the auth endpoints and the S1 guard (/me)."""

from __future__ import annotations

from http import HTTPStatus
from typing import TYPE_CHECKING

from servicecat.models import User
from servicecat.services.security import hash_password

if TYPE_CHECKING:
    from httpx import AsyncClient
    from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

EMAIL = "carol@example.com"
PASSWORD = "endpoint-passw0rd"


async def _seed_user(sm: async_sessionmaker[AsyncSession]) -> None:
    async with sm() as session, session.begin():
        session.add(
            User(
                email=EMAIL,
                full_name="Carol",
                hashed_password=hash_password(PASSWORD),
                is_active=True,
            ),
        )


async def test_login_returns_tokens(
    auth_client: AsyncClient,
    rls_sessionmaker: async_sessionmaker[AsyncSession],
) -> None:
    await _seed_user(rls_sessionmaker)
    resp = await auth_client.post(
        "/api/v1/auth/login",
        json={"email": EMAIL, "password": PASSWORD},
    )
    assert resp.status_code == HTTPStatus.OK
    body = resp.json()
    assert body["access_token"]
    assert body["refresh_token"]
    assert body["token_type"] == "bearer"


async def test_login_bad_password_returns_401(
    auth_client: AsyncClient,
    rls_sessionmaker: async_sessionmaker[AsyncSession],
) -> None:
    await _seed_user(rls_sessionmaker)
    resp = await auth_client.post(
        "/api/v1/auth/login",
        json={"email": EMAIL, "password": "nope"},
    )
    assert resp.status_code == HTTPStatus.UNAUTHORIZED
    assert resp.json()["error"]["code"] == "S1_UNAUTHENTICATED"


async def test_me_requires_authentication(auth_client: AsyncClient) -> None:
    resp = await auth_client.get("/api/v1/auth/me")
    assert resp.status_code == HTTPStatus.UNAUTHORIZED


async def test_me_rejects_garbage_token(auth_client: AsyncClient) -> None:
    resp = await auth_client.get(
        "/api/v1/auth/me",
        headers={"Authorization": "Bearer not-a-jwt"},
    )
    assert resp.status_code == HTTPStatus.UNAUTHORIZED


async def test_login_then_me_returns_current_user(
    auth_client: AsyncClient,
    rls_sessionmaker: async_sessionmaker[AsyncSession],
) -> None:
    await _seed_user(rls_sessionmaker)
    tokens = (
        await auth_client.post(
            "/api/v1/auth/login",
            json={"email": EMAIL, "password": PASSWORD},
        )
    ).json()
    resp = await auth_client.get(
        "/api/v1/auth/me",
        headers={"Authorization": f"Bearer {tokens['access_token']}"},
    )
    assert resp.status_code == HTTPStatus.OK
    assert resp.json()["email"] == EMAIL


async def test_refresh_rotation_invalidates_old_token(
    auth_client: AsyncClient,
    rls_sessionmaker: async_sessionmaker[AsyncSession],
) -> None:
    await _seed_user(rls_sessionmaker)
    tokens = (
        await auth_client.post(
            "/api/v1/auth/login",
            json={"email": EMAIL, "password": PASSWORD},
        )
    ).json()
    refreshed = await auth_client.post(
        "/api/v1/auth/refresh",
        json={"refresh_token": tokens["refresh_token"]},
    )
    assert refreshed.status_code == HTTPStatus.OK
    reuse = await auth_client.post(
        "/api/v1/auth/refresh",
        json={"refresh_token": tokens["refresh_token"]},
    )
    assert reuse.status_code == HTTPStatus.UNAUTHORIZED


async def test_logout_then_refresh_returns_401(
    auth_client: AsyncClient,
    rls_sessionmaker: async_sessionmaker[AsyncSession],
) -> None:
    await _seed_user(rls_sessionmaker)
    tokens = (
        await auth_client.post(
            "/api/v1/auth/login",
            json={"email": EMAIL, "password": PASSWORD},
        )
    ).json()
    logout = await auth_client.post(
        "/api/v1/auth/logout",
        json={"refresh_token": tokens["refresh_token"]},
    )
    assert logout.status_code == HTTPStatus.NO_CONTENT
    after = await auth_client.post(
        "/api/v1/auth/refresh",
        json={"refresh_token": tokens["refresh_token"]},
    )
    assert after.status_code == HTTPStatus.UNAUTHORIZED
