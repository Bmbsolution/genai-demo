"""Seed a demo workspace + admin user. Idempotent.

Run with ``python -m servicecat.scripts.seed`` (or ``make seed``). Inserts run
as the bootstrap superuser, so RLS is bypassed for setup.
"""

from __future__ import annotations

import asyncio

from sqlalchemy import select

from servicecat.db import get_sessionmaker
from servicecat.models import User, Workspace, WorkspaceMembership, WorkspaceRole
from servicecat.services.security import hash_password

WORKSPACE_SLUG = "acme-corp"
ADMIN_EMAIL = "admin@servicecat.local"
# Local-dev seed credential only (never a real secret).
ADMIN_PASSWORD = "servicecat-admin"  # noqa: S105


async def seed() -> None:
    """Create the demo workspace, admin user, and membership if absent."""
    async with get_sessionmaker()() as session, session.begin():
        workspace = await session.scalar(select(Workspace).where(Workspace.slug == WORKSPACE_SLUG))
        if workspace is None:
            workspace = Workspace(name="Acme Corp", slug=WORKSPACE_SLUG)
            session.add(workspace)
            await session.flush()

        user = await session.scalar(select(User).where(User.email == ADMIN_EMAIL))
        if user is None:
            user = User(
                email=ADMIN_EMAIL,
                full_name="Acme Admin",
                hashed_password=hash_password(ADMIN_PASSWORD),
            )
            session.add(user)
            await session.flush()

        membership = await session.scalar(
            select(WorkspaceMembership).where(
                WorkspaceMembership.workspace_id == workspace.id,
                WorkspaceMembership.user_id == user.id,
            ),
        )
        if membership is None:
            session.add(
                WorkspaceMembership(
                    workspace_id=workspace.id,
                    user_id=user.id,
                    role=WorkspaceRole.ADMIN,
                ),
            )

    print(f"Seeded workspace '{WORKSPACE_SLUG}' + admin '{ADMIN_EMAIL}' / '{ADMIN_PASSWORD}'")  # noqa: T201


def main() -> None:
    asyncio.run(seed())


if __name__ == "__main__":
    main()
