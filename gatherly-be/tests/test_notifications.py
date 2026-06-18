"""In-app notification endpoints: list/unread-count/mark-read happy paths,
idempotency, the S2 privacy boundary, and auth/RBAC guards.

Notifications are created server-side, so tests seed them through the service
layer (the same path other backend code uses) and then drive the HTTP API.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from gatherly.models import NotificationType
from gatherly.services.notifications import NotificationService
from tests.conftest import create_host, login

if TYPE_CHECKING:
    import uuid

    from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker


async def _seed_notification(
    sessions: async_sessionmaker[AsyncSession],
    *,
    owner_id: uuid.UUID,
    title: str = "You have a new RSVP",
    kind: NotificationType = NotificationType.GUEST_RSVP,
) -> uuid.UUID:
    async with sessions() as session, session.begin():
        notification = await NotificationService(session).create(
            owner_id=owner_id,
            title=title,
            kind=kind,
        )
    return notification.id


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
