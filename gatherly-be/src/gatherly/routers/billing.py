"""Billing endpoints: view the plan, start checkout, and (mock) activate Pro.

No ``from __future__ import annotations``: FastAPI resolves ``Annotated[...]``
dependency hints at runtime, so the annotated types must be real imports.
"""

from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from gatherly.deps import audit_action, get_current_user, get_db, rate_limit
from gatherly.models import User
from gatherly.schemas.auth import UserResponse
from gatherly.schemas.base import DataResponse
from gatherly.schemas.billing import BillingOverviewResponse, CheckoutResponse
from gatherly.services.billing import PlanService

router = APIRouter(prefix="/api/v1/billing", tags=["billing"])

_read_rl = rate_limit(per_minute=60, key="billing:read")
_write_rl = rate_limit(per_minute=10, key="billing:write")


@router.get("")
async def get_billing(
    db: Annotated[AsyncSession, Depends(get_db)],
    user: Annotated[User, Depends(get_current_user)],
    _rl: Annotated[None, Depends(_read_rl)],
) -> DataResponse[BillingOverviewResponse]:
    overview = await PlanService(db).overview(user)
    return DataResponse(data=BillingOverviewResponse.model_validate(overview))


@router.post("/checkout")
async def start_checkout(
    db: Annotated[AsyncSession, Depends(get_db)],
    user: Annotated[User, Depends(get_current_user)],
    _rl: Annotated[None, Depends(_write_rl)],
    _audit: Annotated[None, Depends(audit_action("billing.checkout"))],
) -> DataResponse[CheckoutResponse]:
    session = await PlanService(db).start_checkout(user)
    return DataResponse(data=CheckoutResponse(url=session.url, mock=session.mock))


@router.post("/upgrade")
async def upgrade(
    db: Annotated[AsyncSession, Depends(get_db)],
    user: Annotated[User, Depends(get_current_user)],
    _rl: Annotated[None, Depends(_write_rl)],
    _audit: Annotated[None, Depends(audit_action("billing.upgrade"))],
) -> DataResponse[UserResponse]:
    upgraded = await PlanService(db).activate_pro(user)
    return DataResponse(data=UserResponse.model_validate(upgraded))
