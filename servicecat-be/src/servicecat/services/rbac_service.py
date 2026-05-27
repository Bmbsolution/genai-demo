"""Workspace-aware capability checks usable outside the request path."""

from __future__ import annotations

from typing import TYPE_CHECKING

from servicecat.db import set_workspace_context
from servicecat.models import WorkspaceRole
from servicecat.rbac import role_has_capability
from servicecat.repositories.memberships import MembershipRepository

if TYPE_CHECKING:
    import uuid

    from sqlalchemy.ext.asyncio import AsyncSession

    from servicecat.rbac import Capability


async def user_has_capability(
    db: AsyncSession,
    user_id: uuid.UUID,
    workspace_id: uuid.UUID,
    capability: Capability,
) -> bool:
    """Return True iff ``user_id`` has ``capability`` in ``workspace_id``.

    Sets the RLS workspace context on ``db`` as a side effect, so call it inside
    a transaction (e.g. from a worker that isn't behind get_current_workspace).
    """
    await set_workspace_context(db, workspace_id)
    role = await MembershipRepository(db).get_role(user_id)
    if role is None:
        return False
    return role_has_capability(WorkspaceRole(role), capability)
