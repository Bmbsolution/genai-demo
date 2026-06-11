"""Guest endpoints: list and invite, nested under an event.

The GET handler is the one the demo's privacy bug targets: the baseline below
is correct — it goes through GuestService, which proves event ownership first.

No ``from __future__ import annotations``: FastAPI resolves ``Annotated[...]``
dependency hints at runtime, so the annotated types must be real imports.
"""

import uuid
from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from gatherly.deps import audit_action, get_current_user, get_db, rate_limit, require_capability
from gatherly.models import User
from gatherly.rbac import Capability
from gatherly.schemas.base import DataResponse
from gatherly.schemas.guest import GuestCreateRequest, GuestResponse
from gatherly.services.guests import GuestService

router = APIRouter(prefix="/api/v1/events", tags=["guests"])

_read = require_capability(Capability.GUEST_READ)
_write = require_capability(Capability.GUEST_WRITE)
_read_rl = rate_limit(per_minute=120, key="guest:read")
_write_rl = rate_limit(per_minute=60, key="guest:write")


@router.get("/{event_id}/guests")
async def list_guests(
    event_id: uuid.UUID,
    db: Annotated[AsyncSession, Depends(get_db)],
    user: Annotated[User, Depends(get_current_user)],
    _cap: Annotated[None, Depends(_read)],
    _rl: Annotated[None, Depends(_read_rl)],
) -> DataResponse[list[GuestResponse]]:
    guests = await GuestService(db).list_for_event(event_id=event_id, owner_id=user.id)
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
