"""Public RSVP flow keyed by invite token."""

from __future__ import annotations

from tests.conftest import create_host, login

_EVENT = {"title": "Spring Gala", "starts_at": "2026-07-01T18:00:00Z", "location": "Grand Hall"}


async def test_guest_can_view_and_respond_via_token(client, sessions):
    await create_host(sessions, email="alex@gatherly.app")
    headers = await login(client, "alex@gatherly.app")
    event_id = (await client.post("/api/v1/events", json=_EVENT, headers=headers)).json()["data"][
        "id"
    ]
    guest = (
        await client.post(
            f"/api/v1/events/{event_id}/guests",
            json={"name": "Dana Cruz", "email": "dana@example.com"},
            headers=headers,
        )
    ).json()["data"]
    token = guest["invite_token"]

    view = await client.get(f"/api/v1/rsvp/{token}")
    assert view.status_code == 200
    body = view.json()["data"]
    assert body["guest_name"] == "Dana Cruz"
    assert body["event"]["title"] == "Spring Gala"
    assert body["rsvp_status"] == "pending"

    responded = await client.post(f"/api/v1/rsvp/{token}", json={"rsvp_status": "yes"})
    assert responded.status_code == 200
    assert responded.json()["data"]["rsvp_status"] == "yes"


async def test_unknown_token_is_404(client):
    assert (await client.get("/api/v1/rsvp/not-a-real-token")).status_code == 404
