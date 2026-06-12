"""Waitlist auto-promotion: when a confirmed guest cancels, the longest-waiting
guest is promoted off the waitlist (FIFO) and notified."""

from __future__ import annotations

from tests.conftest import create_host, login


async def _host(client, sessions, email="promote@gatherly.app"):
    await create_host(sessions, email=email)
    return await login(client, email)


async def _capped_event(client, headers, capacity=1):
    return (
        await client.post(
            "/api/v1/events",
            json={"title": "Tiny", "starts_at": "2026-09-01T18:00:00Z", "capacity": capacity},
            headers=headers,
        )
    ).json()["data"]["id"]


async def _invite(client, headers, event_id, name):
    return (
        await client.post(
            f"/api/v1/events/{event_id}/guests",
            json={"name": name, "email": f"{name.lower()}@example.com"},
            headers=headers,
        )
    ).json()["data"]["invite_token"]


async def _status(client, event_id, headers, name):
    guests = (await client.get(f"/api/v1/events/{event_id}/guests", headers=headers)).json()["data"]
    return next(g["rsvp_status"] for g in guests if g["name"] == name)


async def test_cancel_promotes_the_waitlisted_guest(client, sessions):
    headers = await _host(client, sessions)
    event_id = await _capped_event(client, headers, capacity=1)
    first = await _invite(client, headers, event_id, "First")
    second = await _invite(client, headers, event_id, "Second")

    await client.post(f"/api/v1/rsvp/{first}", json={"rsvp_status": "yes"})
    waitlisted = await client.post(f"/api/v1/rsvp/{second}", json={"rsvp_status": "yes"})
    assert waitlisted.json()["data"]["rsvp_status"] == "waitlisted"

    # The confirmed guest cancels → the waitlisted guest is promoted.
    await client.post(f"/api/v1/rsvp/{first}", json={"rsvp_status": "no"})
    assert await _status(client, event_id, headers, "Second") == "yes"


async def test_promotion_is_fifo(client, sessions):
    headers = await _host(client, sessions)
    event_id = await _capped_event(client, headers, capacity=1)
    first = await _invite(client, headers, event_id, "First")
    second = await _invite(client, headers, event_id, "Second")
    third = await _invite(client, headers, event_id, "Third")

    await client.post(f"/api/v1/rsvp/{first}", json={"rsvp_status": "yes"})
    await client.post(f"/api/v1/rsvp/{second}", json={"rsvp_status": "yes"})  # waitlisted
    await client.post(f"/api/v1/rsvp/{third}", json={"rsvp_status": "yes"})  # waitlisted

    await client.post(f"/api/v1/rsvp/{first}", json={"rsvp_status": "no"})

    assert await _status(client, event_id, headers, "Second") == "yes"  # oldest first
    assert await _status(client, event_id, headers, "Third") == "waitlisted"


async def test_no_waitlist_means_no_promotion(client, sessions):
    headers = await _host(client, sessions)
    event_id = await _capped_event(client, headers, capacity=1)
    first = await _invite(client, headers, event_id, "First")

    await client.post(f"/api/v1/rsvp/{first}", json={"rsvp_status": "yes"})
    cancelled = await client.post(f"/api/v1/rsvp/{first}", json={"rsvp_status": "no"})
    assert cancelled.json()["data"]["rsvp_status"] == "no"  # nothing to promote, no error


async def test_uncapped_event_never_waitlists_or_promotes(client, sessions):
    headers = await _host(client, sessions)
    event_id = (
        await client.post(
            "/api/v1/events",
            json={"title": "Open", "starts_at": "2026-09-01T18:00:00Z"},
            headers=headers,
        )
    ).json()["data"]["id"]
    a = await _invite(client, headers, event_id, "Ada")
    b = await _invite(client, headers, event_id, "Bo")

    await client.post(f"/api/v1/rsvp/{a}", json={"rsvp_status": "yes"})
    second = await client.post(f"/api/v1/rsvp/{b}", json={"rsvp_status": "yes"})
    assert second.json()["data"]["rsvp_status"] == "yes"  # no cap → no waitlist

    await client.post(f"/api/v1/rsvp/{a}", json={"rsvp_status": "no"})
    assert await _status(client, event_id, headers, "Bo") == "yes"  # unchanged
