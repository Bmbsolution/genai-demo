"""Event CRUD happy paths + auth requirement."""

from __future__ import annotations

from tests.conftest import create_host, login

_EVENT = {"title": "Birthday Bash", "starts_at": "2026-07-01T18:00:00Z", "location": "The Loft"}


async def _host_headers(client, sessions, email="host@gatherly.app"):
    await create_host(sessions, email=email)
    return await login(client, email)


async def test_create_list_get_event(client, sessions):
    headers = await _host_headers(client, sessions)

    created = await client.post("/api/v1/events", json=_EVENT, headers=headers)
    assert created.status_code == 201, created.text
    event_id = created.json()["data"]["id"]

    listed = await client.get("/api/v1/events", headers=headers)
    assert listed.status_code == 200
    assert listed.json()["meta"]["total"] == 1

    fetched = await client.get(f"/api/v1/events/{event_id}", headers=headers)
    assert fetched.status_code == 200
    assert fetched.json()["data"]["title"] == "Birthday Bash"


async def test_update_and_soft_delete_event(client, sessions):
    headers = await _host_headers(client, sessions)
    event_id = (await client.post("/api/v1/events", json=_EVENT, headers=headers)).json()["data"][
        "id"
    ]

    patched = await client.patch(
        f"/api/v1/events/{event_id}",
        json={"location": "Rooftop Garden"},
        headers=headers,
    )
    assert patched.status_code == 200
    assert patched.json()["data"]["location"] == "Rooftop Garden"

    deleted = await client.delete(f"/api/v1/events/{event_id}", headers=headers)
    assert deleted.status_code == 204

    # Soft-deleted: no longer listed or fetchable.
    assert (await client.get("/api/v1/events", headers=headers)).json()["meta"]["total"] == 0
    assert (await client.get(f"/api/v1/events/{event_id}", headers=headers)).status_code == 404


async def test_events_require_auth(client):
    assert (await client.get("/api/v1/events")).status_code == 401
