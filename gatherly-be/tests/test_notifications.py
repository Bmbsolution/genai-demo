"""In-app notification endpoints: list/unread-count/mark-read happy paths,
idempotency, the S2 privacy boundary, and auth/RBAC guards.

Notifications are created server-side, so tests seed them through the service
layer (the same path other backend code uses) and then drive the HTTP API.
"""

from __future__ import annotations

import datetime as dt
import uuid
from typing import TYPE_CHECKING

from gatherly.models import Event, NotificationType
from gatherly.rbac import Role
from gatherly.services.notifications import NotificationService
from tests.conftest import create_host, login

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker


async def _seed_notification(
    sessions: async_sessionmaker[AsyncSession],
    *,
    owner_id: uuid.UUID,
    title: str = "You have a new RSVP",
    kind: NotificationType = NotificationType.GUEST_RSVP,
    **extra: object,
) -> uuid.UUID:
    async with sessions() as session, session.begin():
        notification = await NotificationService(session).create(
            owner_id=owner_id,
            title=title,
            kind=kind,
            **extra,  # type: ignore[arg-type]
        )
    return notification.id


async def _seed_event(
    sessions: async_sessionmaker[AsyncSession],
    *,
    owner_id: uuid.UUID,
    title: str = "Summer Rooftop Party",
) -> uuid.UUID:
    """Insert a minimal owned event so a notification can link back to it."""
    event = Event(
        owner_id=owner_id,
        title=title,
        starts_at=dt.datetime(2030, 1, 1, 18, 0, tzinfo=dt.UTC),
    )
    async with sessions() as session, session.begin():
        session.add(event)
    return event.id


async def test_list_and_unread_count(client, sessions):
    host = await create_host(sessions, email="host@gatherly.app")
    headers = await login(client, "host@gatherly.app")
    await _seed_notification(sessions, owner_id=host.id, title="First")
    await _seed_notification(sessions, owner_id=host.id, title="Second")

    listed = await client.get("/api/v1/notifications", headers=headers)
    assert listed.status_code == 200, listed.text
    body = listed.json()
    assert body["meta"]["total"] == 2
    # Newest first.
    assert body["data"][0]["title"] == "Second"

    count = await client.get("/api/v1/notifications/unread-count", headers=headers)
    assert count.status_code == 200
    assert count.json()["data"]["unread"] == 2


async def test_mark_one_read_is_idempotent(client, sessions):
    host = await create_host(sessions, email="host@gatherly.app")
    headers = await login(client, "host@gatherly.app")
    notif_id = await _seed_notification(sessions, owner_id=host.id)

    first = await client.patch(f"/api/v1/notifications/{notif_id}/read", headers=headers)
    assert first.status_code == 200, first.text
    read_at = first.json()["data"]["read_at"]
    assert read_at is not None

    # Re-marking is a no-op and keeps the original read_at.
    second = await client.patch(f"/api/v1/notifications/{notif_id}/read", headers=headers)
    assert second.status_code == 200
    assert second.json()["data"]["read_at"] == read_at

    count = await client.get("/api/v1/notifications/unread-count", headers=headers)
    assert count.json()["data"]["unread"] == 0


async def test_unread_only_filter(client, sessions):
    host = await create_host(sessions, email="host@gatherly.app")
    headers = await login(client, "host@gatherly.app")
    read_me = await _seed_notification(sessions, owner_id=host.id, title="Read")
    await _seed_notification(sessions, owner_id=host.id, title="Unread")
    await client.patch(f"/api/v1/notifications/{read_me}/read", headers=headers)

    resp = await client.get("/api/v1/notifications?unread_only=true", headers=headers)
    assert resp.status_code == 200
    data = resp.json()["data"]
    assert len(data) == 1
    assert data[0]["title"] == "Unread"


async def test_mark_all_read(client, sessions):
    host = await create_host(sessions, email="host@gatherly.app")
    headers = await login(client, "host@gatherly.app")
    await _seed_notification(sessions, owner_id=host.id)
    await _seed_notification(sessions, owner_id=host.id)

    resp = await client.post("/api/v1/notifications/read-all", headers=headers)
    assert resp.status_code == 200, resp.text
    assert resp.json()["data"]["marked"] == 2

    # Already all read — second sweep marks nothing.
    again = await client.post("/api/v1/notifications/read-all", headers=headers)
    assert again.json()["data"]["marked"] == 0

    count = await client.get("/api/v1/notifications/unread-count", headers=headers)
    assert count.json()["data"]["unread"] == 0


async def test_other_host_cannot_read_or_mark_notification(client, sessions):
    # Host A owns the notification.
    alice = await create_host(sessions, email="alice@gatherly.app")
    notif_id = await _seed_notification(sessions, owner_id=alice.id, title="Alice only")

    # Host B is fully authenticated but must NOT touch it — 404, no leak (S2).
    await create_host(sessions, email="bob@gatherly.app")
    headers_b = await login(client, "bob@gatherly.app")

    marked = await client.patch(f"/api/v1/notifications/{notif_id}/read", headers=headers_b)
    assert marked.status_code == 404  # ← S2 boundary enforcement

    # And B's own list / count never sees A's notification.
    listed = await client.get("/api/v1/notifications", headers=headers_b)
    assert listed.json()["meta"]["total"] == 0
    count = await client.get("/api/v1/notifications/unread-count", headers=headers_b)
    assert count.json()["data"]["unread"] == 0


async def test_notifications_require_auth(client):
    # S1: every endpoint rejects an unauthenticated caller.
    assert (await client.get("/api/v1/notifications")).status_code == 401
    assert (await client.get("/api/v1/notifications/unread-count")).status_code == 401
    assert (await client.post("/api/v1/notifications/read-all")).status_code == 401
    bogus = uuid.uuid4()
    assert (await client.patch(f"/api/v1/notifications/{bogus}/read")).status_code == 401


async def test_pagination_windows_and_total_is_unpaginated(client, sessions):
    # Total reflects every matching row; data is just the requested window.
    host = await create_host(sessions, email="host@gatherly.app")
    headers = await login(client, "host@gatherly.app")
    for i in range(5):
        await _seed_notification(sessions, owner_id=host.id, title=f"N{i}")

    page = await client.get("/api/v1/notifications?limit=2&offset=1", headers=headers)
    assert page.status_code == 200, page.text
    body = page.json()
    assert body["meta"] == {"limit": 2, "offset": 1, "total": 5}
    # Newest first => N4, N3, N2, N1, N0; offset 1 limit 2 => N3, N2.
    assert [n["title"] for n in body["data"]] == ["N3", "N2"]

    # An offset past the end yields an empty window but the true total.
    tail = await client.get("/api/v1/notifications?limit=2&offset=10", headers=headers)
    tail_body = tail.json()
    assert tail_body["data"] == []
    assert tail_body["meta"]["total"] == 5


async def test_total_respects_unread_only_filter(client, sessions):
    # With ?unread_only the total counts only unread rows, not all rows.
    host = await create_host(sessions, email="host@gatherly.app")
    headers = await login(client, "host@gatherly.app")
    read_me = await _seed_notification(sessions, owner_id=host.id, title="Read")
    await _seed_notification(sessions, owner_id=host.id, title="Unread-1")
    await _seed_notification(sessions, owner_id=host.id, title="Unread-2")
    await client.patch(f"/api/v1/notifications/{read_me}/read", headers=headers)

    resp = await client.get("/api/v1/notifications?unread_only=true&limit=1", headers=headers)
    body = resp.json()
    assert body["meta"]["total"] == 2  # only the two unread, despite limit=1
    assert len(body["data"]) == 1

    # Without the filter, all three count.
    allrows = await client.get("/api/v1/notifications", headers=headers)
    assert allrows.json()["meta"]["total"] == 3


async def test_list_query_param_bounds_are_validated(client, sessions):
    await create_host(sessions, email="host@gatherly.app")
    headers = await login(client, "host@gatherly.app")

    assert (await client.get("/api/v1/notifications?limit=201", headers=headers)).status_code == 422
    assert (await client.get("/api/v1/notifications?limit=0", headers=headers)).status_code == 422
    assert (await client.get("/api/v1/notifications?offset=-1", headers=headers)).status_code == 422
    # The inclusive bounds are accepted.
    assert (await client.get("/api/v1/notifications?limit=200", headers=headers)).status_code == 200
    assert (await client.get("/api/v1/notifications?offset=0", headers=headers)).status_code == 200


async def test_mark_read_unknown_id_is_404(client, sessions):
    # A well-formed but non-existent UUID is a 404, never a 500 (S2: no leak).
    await create_host(sessions, email="host@gatherly.app")
    headers = await login(client, "host@gatherly.app")

    missing = uuid.uuid4()
    resp = await client.patch(f"/api/v1/notifications/{missing}/read", headers=headers)
    assert resp.status_code == 404, resp.text


async def test_mark_read_malformed_uuid_is_422(client, sessions):
    await create_host(sessions, email="host@gatherly.app")
    headers = await login(client, "host@gatherly.app")

    resp = await client.patch("/api/v1/notifications/not-a-uuid/read", headers=headers)
    assert resp.status_code == 422


async def test_mark_read_sets_read_at_and_decrements_unread(client, sessions):
    # Reading one notification flips exactly one row and decrements the badge.
    host = await create_host(sessions, email="host@gatherly.app")
    headers = await login(client, "host@gatherly.app")
    target = await _seed_notification(sessions, owner_id=host.id, title="Target")
    await _seed_notification(sessions, owner_id=host.id, title="Untouched")

    before = await client.get("/api/v1/notifications/unread-count", headers=headers)
    assert before.json()["data"]["unread"] == 2

    marked = await client.patch(f"/api/v1/notifications/{target}/read", headers=headers)
    payload = marked.json()["data"]
    assert payload["read_at"] is not None
    # The timestamp must parse as a real datetime, not an empty/placeholder string.
    assert dt.datetime.fromisoformat(payload["read_at"]).year >= 2026

    after = await client.get("/api/v1/notifications/unread-count", headers=headers)
    assert after.json()["data"]["unread"] == 1

    # The other row is still unread in the unread-only view.
    unread = await client.get("/api/v1/notifications?unread_only=true", headers=headers)
    titles = [n["title"] for n in unread.json()["data"]]
    assert titles == ["Untouched"]


async def test_list_orders_newest_first_with_three_rows(client, sessions):
    # Ordering is by created_at desc; seed three rows with explicit, spaced times.
    host = await create_host(sessions, email="host@gatherly.app")
    headers = await login(client, "host@gatherly.app")

    base = dt.datetime(2026, 1, 1, 12, 0, tzinfo=dt.UTC)
    async with sessions() as session, session.begin():
        svc = NotificationService(session)
        for offset_minutes, title in ((0, "oldest"), (5, "middle"), (10, "newest")):
            notif = await svc.create(owner_id=host.id, title=title)
            notif.created_at = base + dt.timedelta(minutes=offset_minutes)

    resp = await client.get("/api/v1/notifications", headers=headers)
    assert [n["title"] for n in resp.json()["data"]] == ["newest", "middle", "oldest"]


async def test_event_id_and_body_round_trip_in_response(client, sessions):
    # A notification linked to an owned event surfaces that event_id + body.
    host = await create_host(sessions, email="host@gatherly.app")
    headers = await login(client, "host@gatherly.app")
    event_id = await _seed_event(sessions, owner_id=host.id)
    await _seed_notification(
        sessions,
        owner_id=host.id,
        title="RSVP for your event",
        kind=NotificationType.GUEST_RSVP,
        body="Alice said yes (+1).",
        event_id=event_id,
    )

    resp = await client.get("/api/v1/notifications", headers=headers)
    item = resp.json()["data"][0]
    assert item["event_id"] == str(event_id)
    assert item["body"] == "Alice said yes (+1)."
    assert item["type"] == NotificationType.GUEST_RSVP.value
    assert item["owner_id"] == str(host.id)


async def test_system_notification_has_null_event_id_and_body(client, sessions):
    # Non-event notifications round-trip with explicit nulls (not omitted keys).
    host = await create_host(sessions, email="host@gatherly.app")
    headers = await login(client, "host@gatherly.app")
    await _seed_notification(
        sessions,
        owner_id=host.id,
        title="Welcome to Gatherly",
        kind=NotificationType.SYSTEM,
    )

    item = (await client.get("/api/v1/notifications", headers=headers)).json()["data"][0]
    assert item["event_id"] is None
    assert item["body"] is None
    assert item["read_at"] is None


async def test_host_role_has_notification_capabilities(client, sessions):
    # Both host and admin are granted notification:read/write — a plain HOST
    # (not admin) can list and mark read without an S3 denial.
    host = await create_host(sessions, email="host@gatherly.app", role=Role.HOST)
    headers = await login(client, "host@gatherly.app")
    notif_id = await _seed_notification(sessions, owner_id=host.id, title="For a host")

    listed = await client.get("/api/v1/notifications", headers=headers)
    assert listed.status_code == 200, listed.text
    assert listed.json()["meta"]["total"] == 1

    marked = await client.patch(f"/api/v1/notifications/{notif_id}/read", headers=headers)
    assert marked.status_code == 200, marked.text

    sweep = await client.post("/api/v1/notifications/read-all", headers=headers)
    assert sweep.status_code == 200, sweep.text


async def test_mark_all_read_is_owner_scoped(client, sessions):
    # read-all must only touch the caller's rows, never another host's.
    alice = await create_host(sessions, email="alice@gatherly.app")
    bob = await create_host(sessions, email="bob@gatherly.app")
    await _seed_notification(sessions, owner_id=alice.id, title="Alice unread")
    await _seed_notification(sessions, owner_id=bob.id, title="Bob unread")

    headers_b = await login(client, "bob@gatherly.app")
    sweep = await client.post("/api/v1/notifications/read-all", headers=headers_b)
    assert sweep.json()["data"]["marked"] == 1  # only Bob's row

    # Alice's notification is untouched.
    headers_a = await login(client, "alice@gatherly.app")
    count_a = await client.get("/api/v1/notifications/unread-count", headers=headers_a)
    assert count_a.json()["data"]["unread"] == 1
