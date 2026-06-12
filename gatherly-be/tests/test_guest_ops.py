"""P3: guest operations — CSV import/export, check-in, search/filter, reminders."""

from __future__ import annotations

from tests.conftest import create_host, login


async def _host(client, sessions, email="ops@gatherly.app"):
    await create_host(sessions, email=email)
    return await login(client, email)


async def _event(client, headers, title="Ops Night"):
    resp = await client.post(
        "/api/v1/events",
        json={"title": title, "starts_at": "2026-09-01T18:00:00Z"},
        headers=headers,
    )
    return resp.json()["data"]["id"]


async def test_import_csv_creates_skips_dupes_and_invalid(client, sessions):
    headers = await _host(client, sessions)
    event_id = await _event(client, headers)
    # Pre-seed one guest so the CSV row for the same email is a duplicate.
    await client.post(
        f"/api/v1/events/{event_id}/guests",
        json={"name": "Existing", "email": "existing@example.com"},
        headers=headers,
    )
    csv = (
        "name,email\n"
        "Alice,alice@example.com\n"
        "Bob,bob@example.com\n"
        "Existing,existing@example.com\n"  # duplicate of seeded
        "Carol,not-an-email\n"  # invalid
        "Dup,alice@example.com\n"  # duplicate within file
    )
    resp = await client.post(
        f"/api/v1/events/{event_id}/guests/import",
        json={"csv": csv},
        headers=headers,
    )
    assert resp.status_code == 200, resp.text
    data = resp.json()["data"]
    assert data["created"] == 2
    assert data["skipped_duplicate"] == 2
    assert data["skipped_invalid"] == 1

    listed = await client.get(f"/api/v1/events/{event_id}/guests", headers=headers)
    assert len(listed.json()["data"]) == 3  # existing + alice + bob


async def test_export_csv_has_header_and_rows(client, sessions):
    headers = await _host(client, sessions)
    event_id = await _event(client, headers)
    await client.post(
        f"/api/v1/events/{event_id}/guests",
        json={"name": "Zoe", "email": "zoe@example.com"},
        headers=headers,
    )
    resp = await client.get(f"/api/v1/events/{event_id}/guests/export", headers=headers)
    assert resp.status_code == 200
    assert resp.headers["content-type"].startswith("text/csv")
    lines = resp.text.strip().splitlines()
    assert lines[0] == "name,email,rsvp_status,plus_one,dietary_notes,checked_in"
    assert "zoe@example.com" in lines[1]


async def test_check_in_and_undo(client, sessions):
    headers = await _host(client, sessions)
    event_id = await _event(client, headers)
    guest_id = (
        await client.post(
            f"/api/v1/events/{event_id}/guests",
            json={"name": "Ned", "email": "ned@example.com"},
            headers=headers,
        )
    ).json()["data"]["id"]

    checked = await client.patch(
        f"/api/v1/events/{event_id}/guests/{guest_id}/check-in",
        json={"checked_in": True},
        headers=headers,
    )
    assert checked.status_code == 200
    assert checked.json()["data"]["checked_in_at"] is not None

    undone = await client.patch(
        f"/api/v1/events/{event_id}/guests/{guest_id}/check-in",
        json={"checked_in": False},
        headers=headers,
    )
    assert undone.json()["data"]["checked_in_at"] is None


async def test_list_filters_by_status_and_query(client, sessions):
    headers = await _host(client, sessions)
    event_id = await _event(client, headers)
    token = (
        await client.post(
            f"/api/v1/events/{event_id}/guests",
            json={"name": "Yara", "email": "yara@example.com"},
            headers=headers,
        )
    ).json()["data"]["invite_token"]
    await client.post(
        f"/api/v1/events/{event_id}/guests",
        json={"name": "Walt", "email": "walt@example.com"},
        headers=headers,
    )
    await client.post(f"/api/v1/rsvp/{token}", json={"rsvp_status": "yes"})

    by_status = await client.get(
        f"/api/v1/events/{event_id}/guests",
        params={"status": "yes"},
        headers=headers,
    )
    rows = by_status.json()["data"]
    assert len(rows) == 1
    assert rows[0]["name"] == "Yara"

    by_query = await client.get(
        f"/api/v1/events/{event_id}/guests",
        params={"q": "walt"},
        headers=headers,
    )
    found = by_query.json()["data"]
    assert len(found) == 1
    assert found[0]["email"] == "walt@example.com"


async def test_send_reminders_counts_pending_only(client, sessions):
    headers = await _host(client, sessions)
    event_id = await _event(client, headers)
    token = (
        await client.post(
            f"/api/v1/events/{event_id}/guests",
            json={"name": "Responder", "email": "responder@example.com"},
            headers=headers,
        )
    ).json()["data"]["invite_token"]
    await client.post(
        f"/api/v1/events/{event_id}/guests",
        json={"name": "Silent", "email": "silent@example.com"},
        headers=headers,
    )
    await client.post(f"/api/v1/rsvp/{token}", json={"rsvp_status": "yes"})

    resp = await client.post(f"/api/v1/events/{event_id}/reminders", headers=headers)
    assert resp.status_code == 200
    assert resp.json()["data"]["sent"] == 1  # only the still-pending guest


async def test_guest_ops_require_ownership(client, sessions):
    """A different host cannot import/export/check-in on someone else's event."""
    owner_headers = await _host(client, sessions, email="owner@gatherly.app")
    event_id = await _event(client, owner_headers)
    other_headers = await _host(client, sessions, email="intruder@gatherly.app")

    imp = await client.post(
        f"/api/v1/events/{event_id}/guests/import",
        json={"csv": "name,email\nMallory,mallory@example.com\n"},
        headers=other_headers,
    )
    assert imp.status_code == 404

    exp = await client.get(f"/api/v1/events/{event_id}/guests/export", headers=other_headers)
    assert exp.status_code == 404
