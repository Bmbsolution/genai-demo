"""Auth flow: login, /me, refresh rotation."""

from __future__ import annotations

from tests.conftest import create_host, login


async def test_login_success_and_me(client, sessions):
    await create_host(sessions, email="a@gatherly.app")
    headers = await login(client, "a@gatherly.app")
    resp = await client.get("/api/v1/auth/me", headers=headers)
    assert resp.status_code == 200
    assert resp.json()["data"]["email"] == "a@gatherly.app"


async def test_login_wrong_password_is_401(client, sessions):
    await create_host(sessions, email="b@gatherly.app")
    resp = await client.post(
        "/api/v1/auth/login",
        json={"email": "b@gatherly.app", "password": "wrong"},
    )
    assert resp.status_code == 401


async def test_refresh_rotates_and_old_token_is_rejected(client, sessions):
    await create_host(sessions, email="c@gatherly.app")
    login_resp = await client.post(
        "/api/v1/auth/login",
        json={"email": "c@gatherly.app", "password": "pw-secret-123"},
    )
    old_refresh = login_resp.json()["refresh_token"]

    rotated = await client.post("/api/v1/auth/refresh", json={"refresh_token": old_refresh})
    assert rotated.status_code == 200
    assert rotated.json()["access_token"]

    # The consumed refresh token must not work a second time (rotation).
    replay = await client.post("/api/v1/auth/refresh", json={"refresh_token": old_refresh})
    assert replay.status_code == 401


async def test_me_requires_authentication(client):
    resp = await client.get("/api/v1/auth/me")
    assert resp.status_code == 401
