"""Waitlist position: a waitlisted guest's 1-based FIFO spot, shown on the RSVP
page (their own) and in the host's guest list (everyone's)."""

from __future__ import annotations

from tests.conftest import create_host, login


async def _host(client, sessions, email="position@gatherly.app"):
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


async def _guest(client, event_id, headers, name):
    guests = (await client.get(f"/api/v1/events/{event_id}/guests", headers=headers)).json()["data"]
    return next(g for g in guests if g["name"] == name)


async def test_rsvp_view_exposes_the_guests_own_position(client, sessions):
    headers = await _host(client, sessions)
    event_id = await _capped_event(client, headers, capacity=1)
    first = await _invite(client, headers, event_id, "First")
    second = await _invite(client, headers, event_id, "Second")

    confirmed = await client.post(f"/api/v1/rsvp/{first}", json={"rsvp_status": "yes"})
    waitlisted = await client.post(f"/api/v1/rsvp/{second}", json={"rsvp_status": "yes"})

    # The confirmed guest has no waitlist position; the waitlisted one is #1.
    assert confirmed.json()["data"]["waitlist_position"] is None
    assert waitlisted.json()["data"]["rsvp_status"] == "waitlisted"
    assert waitlisted.json()["data"]["waitlist_position"] == 1

    # GET reflects the same position.
    view = await client.get(f"/api/v1/rsvp/{second}")
    assert view.json()["data"]["waitlist_position"] == 1


async def test_host_list_positions_are_fifo(client, sessions):
    headers = await _host(client, sessions)
    event_id = await _capped_event(client, headers, capacity=1)
    first = await _invite(client, headers, event_id, "First")
    second = await _invite(client, headers, event_id, "Second")
    third = await _invite(client, headers, event_id, "Third")

    await client.post(f"/api/v1/rsvp/{first}", json={"rsvp_status": "yes"})
    await client.post(f"/api/v1/rsvp/{second}", json={"rsvp_status": "yes"})  # waitlisted #1
    await client.post(f"/api/v1/rsvp/{third}", json={"rsvp_status": "yes"})  # waitlisted #2

    assert (await _guest(client, event_id, headers, "First"))["waitlist_position"] is None
    assert (await _guest(client, event_id, headers, "Second"))["waitlist_position"] == 1
    assert (await _guest(client, event_id, headers, "Third"))["waitlist_position"] == 2


async def test_positions_shift_up_after_a_promotion(client, sessions):
    headers = await _host(client, sessions)
    event_id = await _capped_event(client, headers, capacity=1)
    first = await _invite(client, headers, event_id, "First")
    second = await _invite(client, headers, event_id, "Second")
    third = await _invite(client, headers, event_id, "Third")

    await client.post(f"/api/v1/rsvp/{first}", json={"rsvp_status": "yes"})
    await client.post(f"/api/v1/rsvp/{second}", json={"rsvp_status": "yes"})  # #1
    await client.post(f"/api/v1/rsvp/{third}", json={"rsvp_status": "yes"})  # #2

    # First cancels → Second is promoted, Third moves up to #1.
    await client.post(f"/api/v1/rsvp/{first}", json={"rsvp_status": "no"})

    assert (await _guest(client, event_id, headers, "Second"))["waitlist_position"] is None
    assert (await _guest(client, event_id, headers, "Third"))["waitlist_position"] == 1
    assert (await client.get(f"/api/v1/rsvp/{third}")).json()["data"]["waitlist_position"] == 1


async def test_non_waitlisted_guests_have_no_position(client, sessions):
    headers = await _host(client, sessions)
    event_id = await _capped_event(client, headers, capacity=5)  # room to spare
    going = await _invite(client, headers, event_id, "Going")
    await _invite(client, headers, event_id, "Pending")  # never responds

    await client.post(f"/api/v1/rsvp/{going}", json={"rsvp_status": "yes"})

    assert (await _guest(client, event_id, headers, "Going"))["waitlist_position"] is None
    assert (await _guest(client, event_id, headers, "Pending"))["waitlist_position"] is None
