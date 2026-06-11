"""Public RSVP endpoints, keyed by a guest's invite token. No auth; rate-limited.

The token scopes everything to one guest — these handlers can never surface
another guest's data.

No ``from __future__ import annotations``: FastAPI resolves ``Annotated[...]``
dependency hints at runtime, so the annotated types must be real imports.
"""

from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from gatherly.deps import get_db, rate_limit
from gatherly.models import Event, Guest
from gatherly.schemas.base import DataResponse
from gatherly.schemas.rsvp import RsvpEventInfo, RsvpUpdateRequest, RsvpView
from gatherly.services.rsvp import RsvpService

router = APIRouter(prefix="/api/v1/rsvp", tags=["rsvp"])

_view_rl = rate_limit(per_minute=60, key="rsvp:view")
_respond_rl = rate_limit(per_minute=30, key="rsvp:respond")


def _to_view(guest: Guest, event: Event) -> RsvpView:
    return RsvpView(
        guest_name=guest.name,
        rsvp_status=guest.rsvp_status,
        plus_one=guest.plus_one,
        dietary_notes=guest.dietary_notes,
        event=RsvpEventInfo(
            title=event.title,
            description=event.description,
            starts_at=event.starts_at,
            ends_at=event.ends_at,
            location=event.location,
            cover_image_url=event.cover_image_url,
        ),
    )


@router.get("/{invite_token}")
async def view_rsvp(
    invite_token: str,
    db: Annotated[AsyncSession, Depends(get_db)],
    _rl: Annotated[None, Depends(_view_rl)],
) -> DataResponse[RsvpView]:
    guest, event = await RsvpService(db).view(invite_token)
    return DataResponse(data=_to_view(guest, event))


@router.post("/{invite_token}")
async def respond_rsvp(
    invite_token: str,
    payload: RsvpUpdateRequest,
    db: Annotated[AsyncSession, Depends(get_db)],
    _rl: Annotated[None, Depends(_respond_rl)],
) -> DataResponse[RsvpView]:
    guest, event = await RsvpService(db).respond(invite_token, payload)
    return DataResponse(data=_to_view(guest, event))
