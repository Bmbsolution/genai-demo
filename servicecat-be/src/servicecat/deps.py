"""Request dependencies, including the five security guards (S1-S5).

Every mutating endpoint depends on all five:

* **S1 Auth** - ``get_current_user`` resolves the JWT subject (F-02c).
* **S2 Tenant isolation** - ``get_current_workspace`` validates the active
  workspace and sets the RLS context (F-03).
* **S3 RBAC** - ``require_capability`` enforces a fine-grained capability (F-03).
* **S4 Rate limit** - ``rate_limit`` throttles per client/route (below).
* **S5 Audit log** - ``audit_action`` writes an append-only audit entry (F-10).

This module deliberately does NOT use ``from __future__ import annotations``:
FastAPI resolves dependency parameter type hints at runtime, so ``Request`` and
``Redis`` must be real imports, not type-checking-only ones.
"""

import time
import uuid
from collections.abc import AsyncIterator, Awaitable, Callable
from dataclasses import dataclass
from typing import cast

from fastapi import Depends, Header, Request
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from redis.asyncio import Redis
from sqlalchemy.ext.asyncio import AsyncSession

from servicecat.db import get_sessionmaker, set_workspace_context
from servicecat.errors import (
    AuthenticationError,
    AuthorizationError,
    RateLimitError,
    WorkspaceIsolationError,
)
from servicecat.jwt_keys import get_jwt_public_key
from servicecat.models import User, Workspace, WorkspaceRole
from servicecat.rbac import Capability, role_has_capability
from servicecat.redis_client import get_redis
from servicecat.repositories.memberships import MembershipRepository
from servicecat.repositories.users import UserRepository
from servicecat.services.security import TokenType, decode_token

_RATE_LIMIT_WINDOW_SECONDS = 60
_bearer = HTTPBearer(auto_error=False)


async def get_db() -> AsyncIterator[AsyncSession]:
    """Yield a single async database session per request."""
    async with get_sessionmaker()() as session:
        yield session


async def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(_bearer),
    db: AsyncSession = Depends(get_db),
    public_key: str = Depends(get_jwt_public_key),
) -> User:
    """S1: resolve the authenticated user from the Bearer access token.

    Raises AuthenticationError (401) when the header is missing, the token is
    invalid/expired/not an access token, or the user is unknown or inactive.
    """
    if credentials is None:
        raise AuthenticationError("Not authenticated")
    decoded = decode_token(
        credentials.credentials,
        public_key=public_key,
        expected_type=TokenType.ACCESS,
    )
    user = await UserRepository(db).get_by_id(decoded.subject)
    if user is None or not user.is_active:
        raise AuthenticationError("User not found or inactive")
    return user


def rate_limit(*, per_minute: int, key: str) -> Callable[..., Awaitable[None]]:
    """S4: fixed-window rate limit, per client IP + ``key``, backed by Redis.

    Returns a FastAPI dependency. The first request in a window sets the bucket
    TTL; the ``per_minute + 1``-th request in the same window raises
    ``RateLimitError`` (→ HTTP 429).

    Follow-up hardening (deployment-dependent): behind a reverse proxy the
    client IP must come from a trusted ``X-Forwarded-For``, and login should
    additionally throttle per account to resist IP-rotating brute force.
    """

    async def _enforce(request: Request, redis: Redis = Depends(get_redis)) -> None:
        identity = request.client.host if request.client else "unknown"
        window = int(time.time()) // _RATE_LIMIT_WINDOW_SECONDS
        bucket = f"ratelimit:{key}:{identity}:{window}"
        hits = await redis.incr(bucket)
        if hits == 1:
            await redis.expire(bucket, _RATE_LIMIT_WINDOW_SECONDS)
        if hits > per_minute:
            raise RateLimitError(
                "Rate limit exceeded",
                details={"limit_per_minute": per_minute, "key": key},
            )

    return _enforce


@dataclass(frozen=True)
class WorkspaceContext:
    """The active workspace and the caller's role within it (the S2 result)."""

    workspace: Workspace
    role: WorkspaceRole
    user: User


async def get_current_workspace(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    workspace_id: uuid.UUID = Header(alias="X-Workspace-Id"),
) -> WorkspaceContext:
    """S2: resolve + authorize the active workspace and set the RLS context.

    The workspace comes from the ``X-Workspace-Id`` header. We set the RLS
    context to it, then read the caller's membership *through* RLS — a workspace
    the user doesn't belong to simply yields no row (404), never revealing
    whether it exists.
    """
    await set_workspace_context(db, workspace_id)
    role = await MembershipRepository(db).get_role(user.id)
    if role is None:
        raise WorkspaceIsolationError("Workspace not found")
    workspace = cast("Workspace | None", await db.get(Workspace, workspace_id))
    if workspace is None:  # pragma: no cover - membership implies the workspace exists
        raise WorkspaceIsolationError("Workspace not found")
    return WorkspaceContext(workspace=workspace, role=WorkspaceRole(role), user=user)


def require_capability(capability: Capability) -> Callable[..., Awaitable[None]]:
    """S3: dependency factory requiring ``capability`` in the active workspace."""

    async def _require(context: WorkspaceContext = Depends(get_current_workspace)) -> None:
        if not role_has_capability(context.role, capability):
            raise AuthorizationError(
                "Missing required capability",
                details={"required": capability.value, "role": context.role.value},
            )

    return _require
