"""Guest endpoints: invite, list/filter, CSV import/export, check-in, reminders.

All are nested under an event and go through GuestService, which proves event
ownership first (the privacy boundary).

No ``from __future__ import annotations``: FastAPI resolves ``Annotated[...]``
dependency hints at runtime, so the annotated types must be real imports.
"""

import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, Query
from fastapi.responses import PlainTextResponse
from sqlalchemy.ext.asyncio import AsyncSession

from gatherly.deps import audit_action, get_current_user, get_db, rate_limit, require_capability
from gatherly.models import User
from gatherly.rbac import Capability
from gatherly.schemas.base import DataResponse
from gatherly.schemas.guest import (
    CheckInRequest,
    GuestCreateRequest,
    GuestImportRequest,
    GuestImportResponse,
    GuestResponse,
    ReminderResponse,
)
from gatherly.services.guests import GuestService

router = APIRouter(prefix="/api/v1/events", tags=["guests"])

_read = require_capability(Capability.GUEST_READ)
_write = require_capability(Capability.GUEST_WRITE)
_read_rl = rate_limit(per_minute=120, key="guest:read")
_write_rl = rate_limit(per_minute=60, key="guest:write")
# Import and reminders fan out work per guest; throttle them harder.
_bulk_rl = rate_limit(per_minute=10, key="guest:bulk")


@router.get("/{event_id}/guests")
async def list_guests(
    event_id: uuid.UUID,
    db: Annotated[AsyncSession, Depends(get_db)],
    user: Annotated[User, Depends(get_current_user)],
    _cap: Annotated[None, Depends(_read)],
    _rl: Annotated[None, Depends(_read_rl)],
    status: Annotated[str | None, Query(max_length=20)] = None,
    q: Annotated[str | None, Query(max_length=200)] = None,
) -> DataResponse[list[GuestResponse]]:
    guests = await GuestService(db).list_for_event(
        event_id=event_id,
        owner_id=user.id,
        status=status,
        query=q,
    )
    return DataResponse(data=[GuestResponse.model_validate(guest) for guest in guests])


@router.post("/{event_id}/guests", status_code=201)
async def invite_guest(
    event_id: uuid.UUID,
    payload: GuestCreateRequest,
    db: Annotated[AsyncSession, Depends(get_db)],
    user: Annotated[User, Depends(get_current_user)],
    _cap: Annotated[None, Depends(_write)],
    _rl: Annotated[None, Depends(_write_rl)],
    _audit: Annotated[None, Depends(audit_action("guest.invite"))],
) -> DataResponse[GuestResponse]:
    guest = await GuestService(db).invite(event_id=event_id, owner_id=user.id, payload=payload)
    return DataResponse(data=GuestResponse.model_validate(guest))


@router.post("/{event_id}/guests/import")
async def import_guests(
    event_id: uuid.UUID,
    payload: GuestImportRequest,
    db: Annotated[AsyncSession, Depends(get_db)],
    user: Annotated[User, Depends(get_current_user)],
    _cap: Annotated[None, Depends(_write)],
    _rl: Annotated[None, Depends(_bulk_rl)],
    _audit: Annotated[None, Depends(audit_action("guest.import"))],
) -> DataResponse[GuestImportResponse]:
    result = await GuestService(db).import_csv(
        event_id=event_id,
        owner_id=user.id,
        csv_text=payload.csv,
    )
    return DataResponse(data=GuestImportResponse.model_validate(result))


@router.get("/{event_id}/guests/export")
async def export_guests(
    event_id: uuid.UUID,
    db: Annotated[AsyncSession, Depends(get_db)],
    user: Annotated[User, Depends(get_current_user)],
    _cap: Annotated[None, Depends(_read)],
    _rl: Annotated[None, Depends(_read_rl)],
    _audit: Annotated[None, Depends(audit_action("guest.export"))],
) -> PlainTextResponse:
    body = await GuestService(db).export_csv(event_id=event_id, owner_id=user.id)
    return PlainTextResponse(
        content=body,
        media_type="text/csv",
        headers={"content-disposition": 'attachment; filename="guests.csv"'},
    )


@router.patch("/{event_id}/guests/{guest_id}/check-in")
async def check_in_guest(
    event_id: uuid.UUID,
    guest_id: uuid.UUID,
    payload: CheckInRequest,
    db: Annotated[AsyncSession, Depends(get_db)],
    user: Annotated[User, Depends(get_current_user)],
    _cap: Annotated[None, Depends(_write)],
    _rl: Annotated[None, Depends(_write_rl)],
    _audit: Annotated[None, Depends(audit_action("guest.check_in"))],
) -> DataResponse[GuestResponse]:
    guest = await GuestService(db).set_check_in(
        event_id=event_id,
        guest_id=guest_id,
        owner_id=user.id,
        checked_in=payload.checked_in,
    )
    return DataResponse(data=GuestResponse.model_validate(guest))


@router.post("/{event_id}/reminders")
async def send_reminders(
    event_id: uuid.UUID,
    db: Annotated[AsyncSession, Depends(get_db)],
    user: Annotated[User, Depends(get_current_user)],
    _cap: Annotated[None, Depends(_write)],
    _rl: Annotated[None, Depends(_bulk_rl)],
    _audit: Annotated[None, Depends(audit_action("guest.remind"))],
) -> DataResponse[ReminderResponse]:
    sent = await GuestService(db).send_reminders(event_id=event_id, owner_id=user.id)
    return DataResponse(data=ReminderResponse(sent=sent))
