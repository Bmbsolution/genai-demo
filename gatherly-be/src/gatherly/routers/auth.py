"""Auth endpoints. Public login/refresh/logout (rate-limited); /me requires auth.

No ``from __future__ import annotations``: FastAPI resolves the ``Annotated[...]``
dependency hints at runtime, so the annotated types must be real imports.
"""

from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from gatherly.deps import get_current_user, get_db, rate_limit
from gatherly.models import User
from gatherly.schemas.auth import LoginRequest, RefreshRequest, TokenPairResponse, UserResponse
from gatherly.schemas.base import DataResponse
from gatherly.services.auth_service import AuthService
from gatherly.token_store import get_revocation_store

router = APIRouter(prefix="/api/v1/auth", tags=["auth"])


@router.post("/login")
async def login(
    payload: LoginRequest,
    db: Annotated[AsyncSession, Depends(get_db)],
    _rl: Annotated[None, Depends(rate_limit(per_minute=10, key="auth:login"))],
) -> TokenPairResponse:
    pair = await AuthService(db=db, revocations=get_revocation_store()).login(
        payload.email,
        payload.password,
    )
    return TokenPairResponse(access_token=pair.access_token, refresh_token=pair.refresh_token)


@router.post("/refresh")
async def refresh(
    payload: RefreshRequest,
    db: Annotated[AsyncSession, Depends(get_db)],
    _rl: Annotated[None, Depends(rate_limit(per_minute=30, key="auth:refresh"))],
) -> TokenPairResponse:
    pair = await AuthService(db=db, revocations=get_revocation_store()).refresh(
        payload.refresh_token
    )
    return TokenPairResponse(access_token=pair.access_token, refresh_token=pair.refresh_token)


@router.post("/logout", status_code=204)
async def logout(
    payload: RefreshRequest,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> None:
    await AuthService(db=db, revocations=get_revocation_store()).logout(payload.refresh_token)


@router.get("/me")
async def me(user: Annotated[User, Depends(get_current_user)]) -> DataResponse[UserResponse]:
    return DataResponse(data=UserResponse.model_validate(user))
