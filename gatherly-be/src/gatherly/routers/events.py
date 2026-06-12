"""Event endpoints. All host-facing; each carries the relevant guards.

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
from gatherly.schemas.event import (
    EventCreateRequest,
    EventListResponse,
    EventResponse,
    EventUpdateRequest,
)
from gatherly.schemas.insights import EventInsightsResponse, EventReadinessResponse
from gatherly.services.events import EventService
from gatherly.services.insights import InsightsService

router = APIRouter(prefix="/api/v1/events", tags=["events"])

_read = require_capability(Capability.EVENT_READ)
_write = require_capability(Capability.EVENT_WRITE)
_delete = require_capability(Capability.EVENT_DELETE)
_read_rl = rate_limit(per_minute=120, key="event:read")
_write_rl = rate_limit(per_minute=30, key="event:write")


@router.get("")
async def list_events(
    db: Annotated[AsyncSession, Depends(get_db)],
    user: Annotated[User, Depends(get_current_user)],
    _cap: Annotated[None, Depends(_read)],
    _rl: Annotated[None, Depends(_read_rl)],
    limit: Annotated[int, Query(ge=1, le=200)] = 50,
    offset: Annotated[int, Query(ge=0)] = 0,
) -> EventListResponse:
    items, total = await EventService(db).list_for_owner(user.id, limit=limit, offset=offset)
    return EventListResponse(
        data=[EventResponse.model_validate(item) for item in items],
        meta=PageMeta(limit=limit, offset=offset, total=total),
    )


@router.post("", status_code=201)
async def create_event(
    payload: EventCreateRequest,
    db: Annotated[AsyncSession, Depends(get_db)],
    user: Annotated[User, Depends(get_current_user)],
    _cap: Annotated[None, Depends(_write)],
    _rl: Annotated[None, Depends(_write_rl)],
    _audit: Annotated[None, Depends(audit_action("event.create"))],
) -> DataResponse[EventResponse]:
    event = await EventService(db).create(owner_id=user.id, payload=payload)
    return DataResponse(data=EventResponse.model_validate(event))


@router.get("/{event_id}")
async def get_event(
    event_id: uuid.UUID,
    db: Annotated[AsyncSession, Depends(get_db)],
    user: Annotated[User, Depends(get_current_user)],
    _cap: Annotated[None, Depends(_read)],
    _rl: Annotated[None, Depends(_read_rl)],
) -> DataResponse[EventResponse]:
    event = await EventService(db).get(event_id, user.id)
    return DataResponse(data=EventResponse.model_validate(event))


@router.patch("/{event_id}")
async def update_event(
    event_id: uuid.UUID,
    payload: EventUpdateRequest,
    db: Annotated[AsyncSession, Depends(get_db)],
    user: Annotated[User, Depends(get_current_user)],
    _cap: Annotated[None, Depends(_write)],
    _rl: Annotated[None, Depends(_write_rl)],
    _audit: Annotated[None, Depends(audit_action("event.update"))],
) -> DataResponse[EventResponse]:
    event = await EventService(db).update(event_id, user.id, payload)
    return DataResponse(data=EventResponse.model_validate(event))


@router.delete("/{event_id}", status_code=204)
async def delete_event(
    event_id: uuid.UUID,
    db: Annotated[AsyncSession, Depends(get_db)],
    user: Annotated[User, Depends(get_current_user)],
    _cap: Annotated[None, Depends(_delete)],
    _rl: Annotated[None, Depends(_write_rl)],
    _audit: Annotated[None, Depends(audit_action("event.delete"))],
) -> None:
    await EventService(db).soft_delete(event_id, user.id)


@router.get("/{event_id}/insights")
async def get_event_insights(
    event_id: uuid.UUID,
    db: Annotated[AsyncSession, Depends(get_db)],
    user: Annotated[User, Depends(get_current_user)],
    _cap: Annotated[None, Depends(_read)],
    _rl: Annotated[None, Depends(_read_rl)],
) -> DataResponse[EventInsightsResponse]:
    insights = await InsightsService(db).get_insights(event_id=event_id, owner_id=user.id)
    return DataResponse(data=EventInsightsResponse.model_validate(insights))


@router.get("/{event_id}/readiness")
async def get_event_readiness(
    event_id: uuid.UUID,
    db: Annotated[AsyncSession, Depends(get_db)],
    user: Annotated[User, Depends(get_current_user)],
    _cap: Annotated[None, Depends(_read)],
    _rl: Annotated[None, Depends(_read_rl)],
) -> DataResponse[EventReadinessResponse]:
    readiness = await InsightsService(db).get_readiness(event_id=event_id, owner_id=user.id)
    return DataResponse(data=EventReadinessResponse.model_validate(readiness))
