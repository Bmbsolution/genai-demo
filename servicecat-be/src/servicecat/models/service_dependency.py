"""ServiceDependency — a directed dependency edge between two services."""

from __future__ import annotations

import enum
import uuid

from sqlalchemy import CheckConstraint, ForeignKey, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from servicecat.models.base import Base, TimestampMixin, UUIDPrimaryKeyMixin


class DependencyCriticality(enum.StrEnum):
    """How critical a dependency is to the dependent service."""

    HARD = "hard"
    SOFT = "soft"


class DependencyDirection(enum.StrEnum):
    """Whether the service consumes from or produces for the dependency."""

    CONSUMES = "consumes"
    PRODUCES = "produces"


class ServiceDependency(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """Edge: ``service_id`` depends on ``depends_on_service_id``. RLS-scoped."""

    __tablename__ = "service_dependencies"

    workspace_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("workspaces.id", ondelete="CASCADE"),
        index=True,
    )
    service_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("services.id", ondelete="CASCADE"),
        index=True,
    )
    depends_on_service_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("services.id", ondelete="CASCADE"),
        index=True,
    )
    criticality: Mapped[str] = mapped_column(Text)
    direction: Mapped[str] = mapped_column(Text)

    __table_args__ = (
        UniqueConstraint(
            "service_id",
            "depends_on_service_id",
            name="uq_service_dependencies_edge",
        ),
        CheckConstraint(
            "service_id <> depends_on_service_id",
            name="ck_service_dependencies_no_self",
        ),
        CheckConstraint(
            "criticality IN ('hard', 'soft')",
            name="ck_service_dependencies_criticality",
        ),
        CheckConstraint(
            "direction IN ('consumes', 'produces')",
            name="ck_service_dependencies_direction",
        ),
    )
