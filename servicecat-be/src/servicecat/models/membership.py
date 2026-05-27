"""WorkspaceMembership — ties a user to a workspace with a role."""

from __future__ import annotations

import enum
import uuid

from sqlalchemy import CheckConstraint, ForeignKey, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from servicecat.models.base import Base, TimestampMixin, UUIDPrimaryKeyMixin


class WorkspaceRole(enum.StrEnum):
    """Coarse role on a workspace. Capability mapping is added in F-03."""

    ADMIN = "admin"
    MAINTAINER = "maintainer"
    VIEWER = "viewer"


# Single source of truth for the role check constraint, e.g. "'admin', ...".
_ROLE_SQL_VALUES = ", ".join(f"'{role.value}'" for role in WorkspaceRole)


class WorkspaceMembership(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """Membership of a user in a workspace, with a role. Workspace-scoped (RLS)."""

    __tablename__ = "workspace_memberships"

    workspace_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("workspaces.id", ondelete="CASCADE"),
        index=True,
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        index=True,
    )
    role: Mapped[str] = mapped_column(Text)

    __table_args__ = (
        UniqueConstraint(
            "workspace_id",
            "user_id",
            name="uq_workspace_memberships_workspace_id_user_id",
        ),
        CheckConstraint(
            f"role IN ({_ROLE_SQL_VALUES})",
            name="ck_workspace_memberships_role",
        ),
    )
