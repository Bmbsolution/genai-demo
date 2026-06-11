"""Roles and fine-grained capabilities (S3).

A host manages their own events and guests; an admin can additionally delete
events. ``role_has_capability`` is the single source of truth the
``require_capability`` guard consults.
"""

from __future__ import annotations

import enum


class Role(enum.StrEnum):
    """A user's role. Admin ⊃ Host."""

    HOST = "host"
    ADMIN = "admin"


class Capability(enum.StrEnum):
    """Fine-grained permissions checked per request."""

    EVENT_READ = "event:read"
    EVENT_WRITE = "event:write"
    EVENT_DELETE = "event:delete"
    GUEST_READ = "guest:read"
    GUEST_WRITE = "guest:write"


_HOST_CAPS = frozenset(
    {
        Capability.EVENT_READ,
        Capability.EVENT_WRITE,
        Capability.GUEST_READ,
        Capability.GUEST_WRITE,
    },
)

ROLE_CAPABILITIES: dict[Role, frozenset[Capability]] = {
    Role.HOST: _HOST_CAPS,
    Role.ADMIN: _HOST_CAPS | {Capability.EVENT_DELETE},
}


def role_has_capability(role: Role, capability: Capability) -> bool:
    """Return True iff ``role`` is granted ``capability``."""
    return capability in ROLE_CAPABILITIES.get(role, frozenset())
