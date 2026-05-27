"""Unit tests for the role -> capability matrix (no DB)."""

from __future__ import annotations

from servicecat.models import WorkspaceRole
from servicecat.rbac import ROLE_CAPABILITIES, Capability, role_has_capability


def test_admin_has_every_capability() -> None:
    assert ROLE_CAPABILITIES[WorkspaceRole.ADMIN] == frozenset(Capability)


def test_viewer_is_read_only() -> None:
    viewer = ROLE_CAPABILITIES[WorkspaceRole.VIEWER]
    assert Capability.SERVICE_READ in viewer
    assert Capability.SERVICE_WRITE not in viewer
    assert all(capability.value.endswith(":read") for capability in viewer)


def test_maintainer_can_operate_but_not_administer() -> None:
    assert role_has_capability(WorkspaceRole.MAINTAINER, Capability.SERVICE_WRITE)
    assert role_has_capability(WorkspaceRole.MAINTAINER, Capability.SCORECARD_RUN)
    assert not role_has_capability(WorkspaceRole.MAINTAINER, Capability.SERVICE_DELETE)
    assert not role_has_capability(WorkspaceRole.MAINTAINER, Capability.WORKSPACE_SETTINGS)


def test_role_capabilities_are_nested() -> None:
    viewer = ROLE_CAPABILITIES[WorkspaceRole.VIEWER]
    maintainer = ROLE_CAPABILITIES[WorkspaceRole.MAINTAINER]
    admin = ROLE_CAPABILITIES[WorkspaceRole.ADMIN]
    assert viewer < maintainer < admin
