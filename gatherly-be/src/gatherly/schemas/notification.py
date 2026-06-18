"""Notification response schemas.

Notifications are created server-side (other services call
``NotificationService.create``), so there is no create/update request schema —
the host only ever reads them or marks them read.
"""

from __future__ import annotations

import datetime as dt
import uuid

from gatherly.schemas.base import GatherlyBaseModel, PageMeta


class NotificationResponse(GatherlyBaseModel):
    """A single notification as returned to its recipient."""

    id: uuid.UUID
    owner_id: uuid.UUID
    type: str
    title: str
    body: str | None
    event_id: uuid.UUID | None
    read_at: dt.datetime | None
    created_at: dt.datetime


class NotificationListResponse(GatherlyBaseModel):
    """Paginated list of notifications."""

    data: list[NotificationResponse]
    meta: PageMeta


class UnreadCountResponse(GatherlyBaseModel):
    """The recipient's unread-notification count (for the UI badge)."""

    unread: int


class MarkAllReadResponse(GatherlyBaseModel):
    """Result of marking every notification read: how many were updated."""

    marked: int
