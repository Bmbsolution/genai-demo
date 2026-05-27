"""Request dependencies, including the five security guards (S1-S5).

Every mutating endpoint depends on all five:

* **S1 Auth** - ``get_current_user`` resolves the JWT subject (F-02).
* **S2 Tenant isolation** - ``get_current_workspace`` validates the active
  workspace and sets the RLS context (F-03).
* **S3 RBAC** - ``require_capability`` enforces a fine-grained capability (F-03).
* **S4 Rate limit** - ``rate_limit`` throttles per user/route (Redis limiter).
* **S5 Audit log** - ``audit_action`` writes an append-only audit entry (F-10).

Only ``get_db`` is wired at the scaffold stage; the other guards arrive with
their owning backlog issues so routers depend on a stable import surface.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from servicecat.db import get_sessionmaker

if TYPE_CHECKING:
    from collections.abc import AsyncIterator

    from sqlalchemy.ext.asyncio import AsyncSession


async def get_db() -> AsyncIterator[AsyncSession]:
    """Yield a single async database session per request."""
    async with get_sessionmaker()() as session:
        yield session
