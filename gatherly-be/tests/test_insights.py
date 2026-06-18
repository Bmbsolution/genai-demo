"""P4: per-event insights and the readiness checklist."""

from __future__ import annotations

from tests.conftest import create_host, login


async def _host(client, sessions, email="insights@gatherly.app"):
    await create_host(sessions, email=email)
    return await login(client, email)


async def _event(client, headers, **overrides: object):
    payload = {"title": "Gala", "starts_at": "2026-09-01T18:00:00Z", **overrides}
    resp = await client.post("/api/v1/events", json=payload, headers=headers)
    return resp.json()["data"]["id"]


async def _invite(client, headers, event_id, name, email):
    resp = await client.post(
        f"/api/v1/events/{event_id}/guests",
        json={"name": name, "email": email},
        headers=headers,
    )
    return resp.json()["data"]["invite_token"]


async def test_insights_counts_responses_and_attendance(client, sessions):
    headers = await _host(client, sessions)
    event_id = await _event(client, headers, capacity=10)
    yes_token = await _invite(client, headers, event_id, "Yes Guest", "yes@example.com")
    await _invite(client, headers, event_id, "Quiet Guest", "quiet@example.com")
    await client.post(
        f"/api/v1/rsvp/{yes_token}",
        json={"rsvp_status": "yes", "plus_one": True, "dietary_notes": "Vegan"},
    )

    resp = await client.get(f"/api/v1/events/{event_id}/insights", headers=headers)
    assert resp.status_code == 200, resp.text
    data = resp.json()["data"]
    assert data["total_guests"] == 2
    assert data["responded"] == 1
    assert data["response_rate"] == 0.5
    assert data["attending"] == 1
    assert data["plus_ones"] == 1
    assert data["dietary_notes"] == 1
    assert data["capacity"] == 10
    assert data["remaining_capacity"] == 9


async def test_insights_empty_event_has_zero_rate(client, sessions):
    headers = await _host(client, sessions)
    event_id = await _event(client, headers)
    resp = await client.get(f"/api/v1/events/{event_id}/insights", headers=headers)
    data = resp.json()["data"]
    assert data["total_guests"] == 0
    assert data["response_rate"] == 0.0
    assert data["remaining_capacity"] is None  # uncapped


async def test_readiness_flags_missing_high_severity_checks(client, sessions):
    headers = await _host(client, sessions)
    # No location, no guests → two high-severity checks fail → not ready.
    event_id = await _event(client, headers)
    resp = await client.get(f"/api/v1/events/{event_id}/readiness", headers=headers)
    assert resp.status_code == 200
    data = resp.json()["data"]
    assert data["ready"] is False
    by_key = {check["key"]: check for check in data["checks"]}
    assert by_key["has_guests"]["passed"] is False
    assert by_key["has_location"]["passed"] is False
    assert by_key["has_location"]["severity"] == "high"


async def test_readiness_ready_when_high_checks_pass(client, sessions):
    headers = await _host(client, sessions)
    event_id = await _event(client, headers, location="Grand Hall", capacity=5)
    token = await _invite(client, headers, event_id, "A", "a@example.com")
    await client.post(f"/api/v1/rsvp/{token}", json={"rsvp_status": "yes"})

    resp = await client.get(f"/api/v1/events/{event_id}/readiness", headers=headers)
    data = resp.json()["data"]
    by_key = {check["key"]: check["passed"] for check in data["checks"]}
    assert by_key["has_guests"] is True
    assert by_key["has_location"] is True
    assert by_key["within_capacity"] is True
    assert data["ready"] is True  # all high-severity checks pass


async def test_readiness_flags_past_start_time(client, sessions):
    headers = await _host(client, sessions, email="past@gatherly.app")
    event_id = await _event(client, headers, starts_at="2020-01-01T18:00:00Z")
    resp = await client.get(f"/api/v1/events/{event_id}/readiness", headers=headers)
    assert resp.status_code == 200
    by_key = {check["key"]: check for check in resp.json()["data"]["checks"]}
    assert by_key["starts_in_future"]["passed"] is False
    assert by_key["starts_in_future"]["severity"] == "medium"


async def test_readiness_passes_starts_in_future_when_upcoming(client, sessions):
    headers = await _host(client, sessions, email="future@gatherly.app")
    event_id = await _event(client, headers, starts_at="2099-01-01T18:00:00Z")
    resp = await client.get(f"/api/v1/events/{event_id}/readiness", headers=headers)
    by_key = {check["key"]: check["passed"] for check in resp.json()["data"]["checks"]}
    assert by_key["starts_in_future"] is True


async def test_readiness_past_start_does_not_flip_ready_rollup(client, sessions):
    # An event with all high-severity checks satisfied but a past start time:
    # starts_in_future is medium, so it must NOT drag `ready` to False.
    headers = await _host(client, sessions, email="rollup@gatherly.app")
    event_id = await _event(
        client, headers, location="Grand Hall", capacity=5, starts_at="2020-01-01T18:00:00Z"
    )
    token = await _invite(client, headers, event_id, "A", "a@example.com")
    await client.post(f"/api/v1/rsvp/{token}", json={"rsvp_status": "yes"})

    resp = await client.get(f"/api/v1/events/{event_id}/readiness", headers=headers)
    data = resp.json()["data"]
    by_key = {check["key"]: check["passed"] for check in data["checks"]}
    assert by_key["starts_in_future"] is False  # medium check failing
    assert by_key["has_guests"] is True
    assert by_key["has_location"] is True
    assert by_key["within_capacity"] is True
    assert data["ready"] is True  # medium failure does not flip the high-severity roll-up


async def test_insights_requires_ownership(client, sessions):
    owner_headers = await _host(client, sessions, email="owner2@gatherly.app")
    event_id = await _event(client, owner_headers)
    intruder = await _host(client, sessions, email="intruder2@gatherly.app")
    resp = await client.get(f"/api/v1/events/{event_id}/insights", headers=intruder)
    assert resp.status_code == 404
