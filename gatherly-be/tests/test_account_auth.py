"""Registration, Google sign-in (token verify mocked), and account management."""

from __future__ import annotations

import pytest

from gatherly.errors import AuthenticationError, DomainValidationError
from gatherly.services import google_auth
from gatherly.services.google_auth import GoogleAuthService
from tests.conftest import create_host, login


class _FakeKey:
    key = "unused"


class _FakeJwks:
    def get_signing_key_from_jwt(self, _token):
        return _FakeKey()


_REG = {"email": "new@gatherly.app", "password": "supersecret123", "display_name": "New Host"}


async def test_register_then_use_token(client):
    resp = await client.post("/api/v1/auth/register", json=_REG)
    assert resp.status_code == 201, resp.text
    token = resp.json()["access_token"]
    me = await client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert me.status_code == 200
    body = me.json()["data"]
    assert body["email"] == "new@gatherly.app"
    assert body["auth_provider"] == "password"
    assert body["timezone"] == "UTC"


async def test_register_duplicate_email_conflicts(client, sessions):
    await create_host(sessions, email="taken@gatherly.app")
    resp = await client.post(
        "/api/v1/auth/register",
        json={"email": "taken@gatherly.app", "password": "supersecret123", "display_name": "X"},
    )
    assert resp.status_code == 409


async def test_register_short_password_422(client):
    resp = await client.post(
        "/api/v1/auth/register",
        json={"email": "x@gatherly.app", "password": "short", "display_name": "X"},
    )
    assert resp.status_code == 422


async def test_google_sign_in_creates_account(client, monkeypatch):
    claims = {
        "sub": "google-sub-123",
        "email": "guser@gatherly.app",
        "email_verified": True,
        "name": "Google User",
        "picture": "https://example.com/avatar.png",
    }
    monkeypatch.setattr(GoogleAuthService, "_verify", lambda *_args: claims)

    resp = await client.post("/api/v1/auth/google", json={"id_token": "any-token"})
    assert resp.status_code == 200, resp.text
    token = resp.json()["access_token"]
    me = (await client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {token}"})).json()
    assert me["data"]["email"] == "guser@gatherly.app"
    assert me["data"]["auth_provider"] == "google"
    assert me["data"]["avatar_url"] == "https://example.com/avatar.png"


async def test_update_profile(client):
    token = (await client.post("/api/v1/auth/register", json=_REG)).json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    resp = await client.patch(
        "/api/v1/auth/me",
        json={"display_name": "Renamed", "timezone": "America/Toronto"},
        headers=headers,
    )
    assert resp.status_code == 200
    assert resp.json()["data"]["display_name"] == "Renamed"
    assert resp.json()["data"]["timezone"] == "America/Toronto"


async def test_change_password_then_login_with_new(client):
    await client.post("/api/v1/auth/register", json=_REG)
    headers = await login(client, _REG["email"], _REG["password"])
    changed = await client.post(
        "/api/v1/auth/change-password",
        json={"current_password": _REG["password"], "new_password": "brandnewpw456"},
        headers=headers,
    )
    assert changed.status_code == 204
    # Old password rejected, new one works.
    assert (
        await client.post(
            "/api/v1/auth/login",
            json={"email": _REG["email"], "password": _REG["password"]},
        )
    ).status_code == 401
    assert (
        await client.post(
            "/api/v1/auth/login",
            json={"email": _REG["email"], "password": "brandnewpw456"},
        )
    ).status_code == 200


async def test_change_password_wrong_current_is_401(client):
    token = (await client.post("/api/v1/auth/register", json=_REG)).json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    resp = await client.post(
        "/api/v1/auth/change-password",
        json={"current_password": "wrongwrong", "new_password": "brandnewpw456"},
        headers=headers,
    )
    assert resp.status_code == 401


async def test_delete_account_removes_user_and_events(client):
    token = (await client.post("/api/v1/auth/register", json=_REG)).json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    event_id = (
        await client.post(
            "/api/v1/events",
            json={"title": "Doomed", "starts_at": "2026-07-01T18:00:00Z"},
            headers=headers,
        )
    ).json()["data"]["id"]
    await client.post(
        f"/api/v1/events/{event_id}/guests",
        json={"name": "G", "email": "g@example.com"},
        headers=headers,
    )

    deleted = await client.delete("/api/v1/auth/account", headers=headers)
    assert deleted.status_code == 204
    # The session no longer resolves to a user.
    assert (await client.get("/api/v1/auth/me", headers=headers)).status_code == 401


async def test_google_verify_rejects_when_unconfigured(client, sessions, monkeypatch):
    async with sessions() as session:
        svc = GoogleAuthService(session)
        monkeypatch.setattr(svc._settings, "google_client_id", "")
        with pytest.raises(DomainValidationError):
            svc._verify("any-token")


async def test_google_verify_rejects_unverified_email(client, sessions, monkeypatch):
    monkeypatch.setattr(google_auth, "_jwks_client", _FakeJwks)
    monkeypatch.setattr(
        google_auth.jwt,
        "decode",
        lambda *_a, **_k: {
            "sub": "s",
            "email": "e@example.com",
            "email_verified": False,
            "iss": "accounts.google.com",
        },
    )
    async with sessions() as session:
        svc = GoogleAuthService(session)
        monkeypatch.setattr(svc._settings, "google_client_id", "test-client-id")
        with pytest.raises(AuthenticationError):
            svc._verify("any-token")
