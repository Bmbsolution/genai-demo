"""Auth endpoints. Public login/refresh/logout (rate-limited); /me requires auth.

No ``from __future__ import annotations``: FastAPI resolves the ``Annotated[...]``
dependency hints at runtime, so the annotated types must be real imports.
"""

from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from gatherly.deps import audit_action, get_current_user, get_db, rate_limit
from gatherly.models import User
from gatherly.schemas.auth import (
    ChangePasswordRequest,
    GoogleAuthRequest,
    LoginRequest,
    ProfileUpdateRequest,
    RefreshRequest,
    RegisterRequest,
    TokenPairResponse,
    UserResponse,
)
from gatherly.schemas.base import DataResponse
from gatherly.services.account import AccountService
from gatherly.services.auth_service import AuthService
from gatherly.services.google_auth import GoogleAuthService
from gatherly.token_store import get_revocation_store

router = APIRouter(prefix="/api/v1/auth", tags=["auth"])


@router.post("/register", status_code=201)
async def register(
    payload: RegisterRequest,
    db: Annotated[AsyncSession, Depends(get_db)],
    _rl: Annotated[None, Depends(rate_limit(per_minute=10, key="auth:register"))],
) -> TokenPairResponse:
    pair = await AuthService(db=db, revocations=get_revocation_store()).register(
        email=payload.email,
        password=payload.password,
        display_name=payload.display_name,
    )
    return TokenPairResponse(access_token=pair.access_token, refresh_token=pair.refresh_token)


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


@router.post("/google")
async def google(
    payload: GoogleAuthRequest,
    db: Annotated[AsyncSession, Depends(get_db)],
    _rl: Annotated[None, Depends(rate_limit(per_minute=20, key="auth:google"))],
) -> TokenPairResponse:
    pair = await GoogleAuthService(db).authenticate(payload.id_token)
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


@router.patch("/me")
async def update_me(
    payload: ProfileUpdateRequest,
    db: Annotated[AsyncSession, Depends(get_db)],
    user: Annotated[User, Depends(get_current_user)],
    _rl: Annotated[None, Depends(rate_limit(per_minute=30, key="account:update"))],
    _audit: Annotated[None, Depends(audit_action("account.update"))],
) -> DataResponse[UserResponse]:
    updated = await AccountService(db).update_profile(user, payload)
    return DataResponse(data=UserResponse.model_validate(updated))


@router.post("/change-password", status_code=204)
async def change_password(
    payload: ChangePasswordRequest,
    db: Annotated[AsyncSession, Depends(get_db)],
    user: Annotated[User, Depends(get_current_user)],
    _rl: Annotated[None, Depends(rate_limit(per_minute=10, key="account:password"))],
    _audit: Annotated[None, Depends(audit_action("account.change_password"))],
) -> None:
    await AccountService(db).change_password(user, payload.current_password, payload.new_password)


@router.delete("/account", status_code=204)
async def delete_account(
    db: Annotated[AsyncSession, Depends(get_db)],
    user: Annotated[User, Depends(get_current_user)],
    _rl: Annotated[None, Depends(rate_limit(per_minute=5, key="account:delete"))],
    _audit: Annotated[None, Depends(audit_action("account.delete"))],
) -> None:
    await AccountService(db).delete_account(user)
