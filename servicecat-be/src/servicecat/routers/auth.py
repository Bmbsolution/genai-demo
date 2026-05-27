"""Authentication endpoints: login, refresh, logout, and the current user.

login/refresh/logout are public — you cannot present S1/S2/S3 credentials
before authenticating — so they carry S4 (rate limit). /me is S1-protected.
S5 (audit) is wired once the audit_logs table lands in F-10.
"""

from typing import Annotated

from fastapi import APIRouter, Depends, status
from redis.asyncio import Redis
from sqlalchemy.ext.asyncio import AsyncSession

from servicecat.deps import get_current_user, get_db, rate_limit
from servicecat.jwt_keys import get_jwt_private_key, get_jwt_public_key
from servicecat.models import User
from servicecat.redis_client import get_redis
from servicecat.schemas.auth import (
    LoginRequest,
    RefreshRequest,
    TokenPairResponse,
    UserResponse,
)
from servicecat.services.auth_service import AuthService

router = APIRouter(prefix="/api/v1/auth", tags=["auth"])

# Precomputed so the Depends() defaults hold a reference, not a nested call.
_login_rl = rate_limit(per_minute=10, key="auth:login")
_refresh_rl = rate_limit(per_minute=30, key="auth:refresh")
_logout_rl = rate_limit(per_minute=30, key="auth:logout")
_me_rl = rate_limit(per_minute=60, key="auth:me")


def get_auth_service(
    db: Annotated[AsyncSession, Depends(get_db)],
    redis: Annotated[Redis, Depends(get_redis)],
    private_key: Annotated[str, Depends(get_jwt_private_key)],
    public_key: Annotated[str, Depends(get_jwt_public_key)],
) -> AuthService:
    """Construct an AuthService from the request-scoped session, Redis, and keys."""
    return AuthService(db=db, redis=redis, private_key=private_key, public_key=public_key)


AuthServiceDep = Annotated[AuthService, Depends(get_auth_service)]


@router.post("/login")
async def login(
    payload: LoginRequest,
    service: AuthServiceDep,
    _rl: Annotated[None, Depends(_login_rl)],
) -> TokenPairResponse:
    pair = await service.login(payload.email, payload.password)
    return TokenPairResponse(access_token=pair.access_token, refresh_token=pair.refresh_token)


@router.post("/refresh")
async def refresh(
    payload: RefreshRequest,
    service: AuthServiceDep,
    _rl: Annotated[None, Depends(_refresh_rl)],
) -> TokenPairResponse:
    pair = await service.refresh(payload.refresh_token)
    return TokenPairResponse(access_token=pair.access_token, refresh_token=pair.refresh_token)


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
async def logout(
    payload: RefreshRequest,
    service: AuthServiceDep,
    _rl: Annotated[None, Depends(_logout_rl)],
) -> None:
    await service.logout(payload.refresh_token)


@router.get("/me")
async def me(
    user: Annotated[User, Depends(get_current_user)],
    _rl: Annotated[None, Depends(_me_rl)],
) -> UserResponse:
    return UserResponse.model_validate(user)
