"""P2: event richness (visibility/cover/end time), RSVP +1/dietary, waitlist."""

from __future__ import annotations

from tests.conftest import create_host, login


async def _host(client, sessions, email="depth@gatherly.app"):
    await create_host(sessions, email=email)
    return await login(client, email)


async def test_create_event_with_visibility_cover_and_end(client, sessions):
    headers = await _host(client, sessions)
    payload = {
        "title": "Launch Night",
        "starts_at": "2026-09-01T18:00:00Z",
        "ends_at": "2026-09-01T22:00:00Z",
        "location": "The Foundry",
        "cover_image_url": "https://example.com/cover.jpg",
        "capacity": 2,
        "visibility": "public",
    }
    resp = await client.post("/api/v1/events", json=payload, headers=headers)
    assert resp.status_code == 201, resp.text
    data = resp.json()["data"]
    assert data["visibility"] == "public"
    assert data["cover_image_url"] == "https://example.com/cover.jpg"
    assert data["ends_at"] == "2026-09-01T22:00:00Z"


async def test_visibility_defaults_to_private(client, sessions):
    headers = await _host(client, sessions)
    resp = await client.post(
        "/api/v1/events",
        json={"title": "Quiet One", "starts_at": "2026-09-01T18:00:00Z"},
        headers=headers,
    )
    assert resp.json()["data"]["visibility"] == "private"


async def test_rsvp_records_plus_one_and_dietary(client, sessions):
    headers = await _host(client, sessions)
    event_id = (
        await client.post(
            "/api/v1/events",
            json={"title": "Dinner", "starts_at": "2026-09-01T18:00:00Z"},
            headers=headers,
        )
    ).json()["data"]["id"]
    token = (
        await client.post(
            f"/api/v1/events/{event_id}/guests",
            json={"name": "Dana", "email": "dana@example.com"},
            headers=headers,
        )
    ).json()["data"]["invite_token"]

    resp = await client.post(
        f"/api/v1/rsvp/{token}",
        json={"rsvp_status": "yes", "plus_one": True, "dietary_notes": "Vegetarian"},
    )
    assert resp.status_code == 200
    body = resp.json()["data"]
    assert body["rsvp_status"] == "yes"
    assert body["plus_one"] is True
    assert body["dietary_notes"] == "Vegetarian"


async def test_yes_over_capacity_is_waitlisted(client, sessions):
    headers = await _host(client, sessions)
    event_id = (
        await client.post(
            "/api/v1/events",
            json={"title": "Tiny", "starts_at": "2026-09-01T18:00:00Z", "capacity": 1},
            headers=headers,
        )
    ).json()["data"]["id"]

    tokens = []
    for name in ("First", "Second"):
        guest = await client.post(
            f"/api/v1/events/{event_id}/guests",
            json={"name": name, "email": f"{name.lower()}@example.com"},
            headers=headers,
        )
        tokens.append(guest.json()["data"]["invite_token"])

    first = await client.post(f"/api/v1/rsvp/{tokens[0]}", json={"rsvp_status": "yes"})
    second = await client.post(f"/api/v1/rsvp/{tokens[1]}", json={"rsvp_status": "yes"})
    assert first.json()["data"]["rsvp_status"] == "yes"
    assert second.json()["data"]["rsvp_status"] == "waitlisted"
