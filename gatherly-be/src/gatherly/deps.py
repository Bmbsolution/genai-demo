"""Request dependencies, including the security guards.

The five guards, Gatherly-style:

* **S1 Auth** - ``get_current_user`` resolves the Bearer access token.
* **S2 Tenant isolation** - enforced in the service/repository layer: every
  host-facing query is scoped to ``owner_id`` (see EventRepository.get_for_owner).
  Routers pass ``user.id`` as the owner; dropping that scope is the planted
  demo bug.
* **S3 RBAC** - ``require_capability`` checks the caller's role.
* **S4 Rate limit** - ``rate_limit`` throttles per client IP + route.
* **S5 Audit log** - ``audit_action`` appends an immutable audit entry.

No ``from __future__ import annotations`` here: FastAPI resolves dependency
parameter hints at runtime, so ``Request`` must be a real import.
"""

from collections.abc import AsyncIterator, Awaitable, Callable

from fastapi import Depends, Request
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.ext.asyncio import AsyncSession

from gatherly.config import get_settings
from gatherly.errors import AuthenticationError, AuthorizationError, RateLimitError
from gatherly.models import AuditLog, User
from gatherly.rate_limit import check_rate_limit
from gatherly.rbac import Capability, Role, role_has_capability
from gatherly.repositories.audit import AuditLogRepository
from gatherly.repositories.users import UserRepository
from gatherly.security import TokenType, decode_token

_bearer = HTTPBearer(auto_error=False)


async def get_db() -> AsyncIterator[AsyncSession]:
    """Yield a request-scoped session; commit on success, roll back on error."""
    from gatherly.db import get_sessionmaker  # noqa: PLC0415

    async with get_sessionmaker()() as session, session.begin():
        yield session


async def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(_bearer),
    db: AsyncSession = Depends(get_db),
) -> User:
    """S1: resolve the authenticated user from the Bearer access token."""
    if credentials is None:
        raise AuthenticationError("Not authenticated")
    decoded = decode_token(
        credentials.credentials,
        secret=get_settings().jwt_secret,
        expected_type=TokenType.ACCESS,
    )
    user = await UserRepository(db).get_by_id(decoded.subject)
    if user is None or not user.is_active:
        raise AuthenticationError("User not found or inactive")
    return user


def require_capability(capability: Capability) -> Callable[..., Awaitable[None]]:
    """S3: dependency factory requiring ``capability`` for the caller's role."""

    async def _require(user: User = Depends(get_current_user)) -> None:
        if not role_has_capability(Role(user.role), capability):
            raise AuthorizationError(
                "Missing required capability",
                details={"required": capability.value, "role": user.role},
            )

    return _require


def rate_limit(*, per_minute: int, key: str) -> Callable[..., Awaitable[None]]:
    """S4: fixed-window rate limit per client IP + ``key`` (in-memory)."""

    async def _enforce(request: Request) -> None:
        identity = request.client.host if request.client else "unknown"
        if not check_rate_limit(identity=identity, key=key, per_minute=per_minute):
            raise RateLimitError(
                "Rate limit exceeded",
                details={"limit_per_minute": per_minute, "key": key},
            )

    return _enforce


def audit_action(action: str) -> Callable[..., Awaitable[None]]:
    """S5: append an immutable audit entry for ``action`` (e.g. event.create)."""

    async def _record(
        request: Request,
        user: User = Depends(get_current_user),
        db: AsyncSession = Depends(get_db),
    ) -> None:
        entry = AuditLog(
            actor_id=user.id,
            action=action,
            resource_type=action.split(".", 1)[0],
            ip=request.client.host if request.client else None,
            user_agent=request.headers.get("user-agent"),
        )
        await AuditLogRepository(db).record(entry)

    return _record
