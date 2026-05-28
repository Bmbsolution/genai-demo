"""Workspace discovery endpoint.

GET /api/v1/workspaces lists the workspaces the caller belongs to. It is a
bootstrap endpoint (like /auth/me): authenticated (S1) and rate-limited (S4),
but with no workspace context yet — so no S2/S3, and S5 audit (which needs a
workspace) is not applied here.
"""

from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from servicecat.deps import get_current_user, get_db, rate_limit
from servicecat.models import User
from servicecat.repositories.workspaces import WorkspaceRepository
from servicecat.schemas.workspace import WorkspaceResponse

router = APIRouter(prefix="/api/v1/workspaces", tags=["workspaces"])

_list_rl = rate_limit(per_minute=120, key="workspaces:list")


@router.get("")
async def list_my_workspaces(
    user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
    _rl: Annotated[None, Depends(_list_rl)],
) -> list[WorkspaceResponse]:
    rows = await WorkspaceRepository(db).list_for_user(user.id)
    return [
        WorkspaceResponse(id=workspace.id, name=workspace.name, slug=workspace.slug, role=role)
        for workspace, role in rows
    ]
