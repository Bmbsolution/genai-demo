"""The privacy boundary (S2): a host can never read another host's guest list.

This is the test the conference "resilience" moment is about — the planted demo
bug removes the ownership scope and turns this 404 into a 200 data leak.
"""

from __future__ import annotations

from tests.conftest import create_host, login

_EVENT = {"title": "Private Dinner", "starts_at": "2026-07-01T18:00:00Z"}
_GUEST = {"name": "Secret Guest", "email": "secret@example.com"}


async def test_owner_sees_own_guests(client, sessions):
    await create_host(sessions, email="alice@gatherly.app")
    headers = await login(client, "alice@gatherly.app")
    event_id = (await client.post("/api/v1/events", json=_EVENT, headers=headers)).json()["data"][
        "id"
    ]
    await client.post(f"/api/v1/events/{event_id}/guests", json=_GUEST, headers=headers)

    resp = await client.get(f"/api/v1/events/{event_id}/guests", headers=headers)
    assert resp.status_code == 200
    guests = resp.json()["data"]
    assert len(guests) == 1
    assert guests[0]["email"] == "secret@example.com"


async def test_other_host_cannot_read_guest_list(client, sessions):
    # Host A owns the event + guest.
    await create_host(sessions, email="alice@gatherly.app")
    headers_a = await login(client, "alice@gatherly.app")
    event_id = (await client.post("/api/v1/events", json=_EVENT, headers=headers_a)).json()["data"][
        "id"
    ]
    await client.post(f"/api/v1/events/{event_id}/guests", json=_GUEST, headers=headers_a)

    # Host B is fully authenticated but must NOT see A's guests — 404, no leak.
    await create_host(sessions, email="bob@gatherly.app")
    headers_b = await login(client, "bob@gatherly.app")
    resp = await client.get(f"/api/v1/events/{event_id}/guests", headers=headers_b)
    assert resp.status_code == 404
