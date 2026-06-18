"""Notification endpoints. All host-facing; each carries the relevant guards.

No ``from __future__ import annotations``: FastAPI resolves the ``Annotated[...]``
dependency hints at runtime, so the annotated types must be real imports.
"""

import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from gatherly.deps import audit_action, get_current_user, get_db, rate_limit, require_capability
from gatherly.models import User
from gatherly.rbac import Capability
from gatherly.schemas.base import DataResponse, PageMeta
from gatherly.schemas.notification import (
    MarkAllReadResponse,
    NotificationListResponse,
    NotificationResponse,
    UnreadCountResponse,
)
from gatherly.services.notifications import NotificationService

router = APIRouter(prefix="/api/v1/notifications", tags=["notifications"])

_read = require_capability(Capability.NOTIFICATION_READ)
_write = require_capability(Capability.NOTIFICATION_WRITE)
_read_rl = rate_limit(per_minute=120, key="notification:read")
_write_rl = rate_limit(per_minute=60, key="notification:write")


@router.get("")
async def list_notifications(
    db: Annotated[AsyncSession, Depends(get_db)],
    user: Annotated[User, Depends(get_current_user)],
    _cap: Annotated[None, Depends(_read)],
    _rl: Annotated[None, Depends(_read_rl)],
    unread_only: Annotated[bool, Query()] = False,  # noqa: FBT002
    limit: Annotated[int, Query(ge=1, le=200)] = 50,
    offset: Annotated[int, Query(ge=0)] = 0,
) -> NotificationListResponse:
    items, total = await NotificationService(db).list_for_owner(
        user.id,
        unread_only=unread_only,
        limit=limit,
        offset=offset,
    )
    return NotificationListResponse(
        data=[NotificationResponse.model_validate(item) for item in items],
        meta=PageMeta(limit=limit, offset=offset, total=total),
    )


@router.get("/unread-count")
async def get_unread_count(
    db: Annotated[AsyncSession, Depends(get_db)],
    user: Annotated[User, Depends(get_current_user)],
    _cap: Annotated[None, Depends(_read)],
    _rl: Annotated[None, Depends(_read_rl)],
) -> DataResponse[UnreadCountResponse]:
    unread = await NotificationService(db).count_unread(user.id)
    return DataResponse(data=UnreadCountResponse(unread=unread))


@router.patch("/{notification_id}/read")
async def mark_notification_read(
    notification_id: uuid.UUID,
    db: Annotated[AsyncSession, Depends(get_db)],
    user: Annotated[User, Depends(get_current_user)],
    _cap: Annotated[None, Depends(_write)],
    _rl: Annotated[None, Depends(_write_rl)],
    _audit: Annotated[None, Depends(audit_action("notification.read"))],
) -> DataResponse[NotificationResponse]:
    notification = await NotificationService(db).mark_read(notification_id, user.id)
    return DataResponse(data=NotificationResponse.model_validate(notification))


@router.post("/read-all")
async def mark_all_notifications_read(
    db: Annotated[AsyncSession, Depends(get_db)],
    user: Annotated[User, Depends(get_current_user)],
    _cap: Annotated[None, Depends(_write)],
    _rl: Annotated[None, Depends(_write_rl)],
    _audit: Annotated[None, Depends(audit_action("notification.read_all"))],
) -> DataResponse[MarkAllReadResponse]:
    marked = await NotificationService(db).mark_all_read(user.id)
    return DataResponse(data=MarkAllReadResponse(marked=marked))
