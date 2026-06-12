"""P5: Free/Pro plans — limits, Pro-only features, and the upgrade flow."""

from __future__ import annotations

from gatherly.models import UserPlan
from tests.conftest import create_host, login


async def _free_host(client, sessions, email="free@gatherly.app"):
    await create_host(sessions, email=email, plan=UserPlan.FREE)
    return await login(client, email)


async def _make_event(client, headers, title="Event"):
    return await client.post(
        "/api/v1/events",
        json={"title": title, "starts_at": "2026-09-01T18:00:00Z"},
        headers=headers,
    )


async def test_billing_overview_reports_free_plan(client, sessions):
    headers = await _free_host(client, sessions)
    resp = await client.get("/api/v1/billing", headers=headers)
    assert resp.status_code == 200, resp.text
    data = resp.json()["data"]
    assert data["plan"] == "free"
    assert data["max_active_events"] == 2
    assert data["active_events"] == 0


async def test_me_includes_plan(client, sessions):
    headers = await _free_host(client, sessions)
    resp = await client.get("/api/v1/auth/me", headers=headers)
    assert resp.json()["data"]["plan"] == "free"


async def test_free_event_cap_enforced(client, sessions):
    headers = await _free_host(client, sessions)
    assert (await _make_event(client, headers, "One")).status_code == 201
    assert (await _make_event(client, headers, "Two")).status_code == 201
    third = await _make_event(client, headers, "Three")
    assert third.status_code == 402
    assert third.json()["error"]["code"] == "PLAN_LIMIT"


async def test_free_import_and_reminders_require_pro(client, sessions):
    headers = await _free_host(client, sessions)
    event_id = (await _make_event(client, headers)).json()["data"]["id"]

    imp = await client.post(
        f"/api/v1/events/{event_id}/guests/import",
        json={"csv": "name,email\nA,a@example.com\n"},
        headers=headers,
    )
    assert imp.status_code == 402
    assert imp.json()["error"]["details"]["feature"] == "import"

    rem = await client.post(f"/api/v1/events/{event_id}/reminders", headers=headers)
    assert rem.status_code == 402


async def test_upgrade_unlocks_pro_features(client, sessions):
    headers = await _free_host(client, sessions)
    # Hit the cap first.
    await _make_event(client, headers, "One")
    await _make_event(client, headers, "Two")
    assert (await _make_event(client, headers, "Three")).status_code == 402

    upgrade = await client.post("/api/v1/billing/upgrade", headers=headers)
    assert upgrade.status_code == 200
    assert upgrade.json()["data"]["plan"] == "pro"

    # Cap lifted + Pro features unlocked.
    assert (await _make_event(client, headers, "Three")).status_code == 201
    event_id = (await _make_event(client, headers, "Four")).json()["data"]["id"]
    imp = await client.post(
        f"/api/v1/events/{event_id}/guests/import",
        json={"csv": "name,email\nA,a@example.com\n"},
        headers=headers,
    )
    assert imp.status_code == 200
    assert imp.json()["data"]["created"] == 1


async def test_checkout_returns_mock_session(client, sessions):
    headers = await _free_host(client, sessions)
    resp = await client.post("/api/v1/billing/checkout", headers=headers)
    assert resp.status_code == 200
    data = resp.json()["data"]
    assert data["mock"] is True
    assert data["url"] is None


async def test_pro_host_has_no_event_cap(client, sessions):
    await create_host(sessions, email="pro@gatherly.app", plan=UserPlan.PRO)
    headers = await login(client, "pro@gatherly.app")
    for i in range(3):
        assert (await _make_event(client, headers, f"E{i}")).status_code == 201
    resp = await client.get("/api/v1/billing", headers=headers)
    assert resp.json()["data"]["max_active_events"] is None
