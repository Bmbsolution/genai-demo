"""User — a global identity that joins workspaces via memberships."""

from __future__ import annotations

from sqlalchemy import Text, text
from sqlalchemy.orm import Mapped, mapped_column

from servicecat.models.base import Base, TimestampMixin, UUIDPrimaryKeyMixin


class User(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """A person. Identity is global; workspace access is via WorkspaceMembership.

    Not workspace-scoped (no ``workspace_id``, no RLS): a single user may belong
    to several workspaces. Tenant isolation is enforced on the membership table.
    """

    __tablename__ = "users"

    email: Mapped[str] = mapped_column(Text, unique=True)
    full_name: Mapped[str] = mapped_column(Text)
    is_active: Mapped[bool] = mapped_column(server_default=text("true"))
    # Nullable: a user may be provisioned before setting a password (or via SSO
    # later). Password login requires it to be present (checked in AuthService).
    hashed_password: Mapped[str | None] = mapped_column(Text, default=None)
