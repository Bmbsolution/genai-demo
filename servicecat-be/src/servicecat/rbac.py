"""Role-based access control: the capability vocabulary and per-role grants.

This is the single source of truth for which role may do what. The matrix is
mirrored (for humans) in CLAUDE.md, but code must read it from here.
"""

from __future__ import annotations

import enum

from servicecat.models import WorkspaceRole


class Capability(enum.StrEnum):
    """A fine-grained permission. Values match the API/CLAUDE.md vocabulary."""

    SERVICE_READ = "service:read"
    SERVICE_WRITE = "service:write"
    SERVICE_DELETE = "service:delete"
    SCORECARD_READ = "scorecard:read"
    SCORECARD_WRITE = "scorecard:write"
    SCORECARD_RUN = "scorecard:run"
    FINDING_READ = "finding:read"
    FINDING_ASSIGN = "finding:assign"
    FINDING_RESOLVE = "finding:resolve"
    TEMPLATE_READ = "template:read"
    TEMPLATE_WRITE = "template:write"
    TEAM_READ = "team:read"
    TEAM_MANAGE = "team:manage"
    WORKSPACE_SETTINGS = "workspace:settings"
    WORKSPACE_BILLING = "workspace:billing"
    AUDIT_READ = "audit:read"


# Viewer: read-only across the catalog. Maintainer: operate services, scorecards,
# findings, templates. Admin: everything (workspace settings, billing, team
# management, audit, deletes).
_VIEWER: frozenset[Capability] = frozenset(
    {
        Capability.SERVICE_READ,
        Capability.SCORECARD_READ,
        Capability.FINDING_READ,
        Capability.TEMPLATE_READ,
        Capability.TEAM_READ,
    },
)
_MAINTAINER: frozenset[Capability] = _VIEWER | {
    Capability.SERVICE_WRITE,
    Capability.SCORECARD_WRITE,
    Capability.SCORECARD_RUN,
    Capability.FINDING_ASSIGN,
    Capability.FINDING_RESOLVE,
    Capability.TEMPLATE_WRITE,
}
_ADMIN: frozenset[Capability] = frozenset(Capability)

ROLE_CAPABILITIES: dict[WorkspaceRole, frozenset[Capability]] = {
    WorkspaceRole.VIEWER: _VIEWER,
    WorkspaceRole.MAINTAINER: _MAINTAINER,
    WorkspaceRole.ADMIN: _ADMIN,
}


def role_has_capability(role: WorkspaceRole, capability: Capability) -> bool:
    """Return True iff ``role`` grants ``capability``."""
    return capability in ROLE_CAPABILITIES[role]
