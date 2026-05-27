"""The scorecard plugin contract.

A scorecard type subclasses ``BaseScorecard``, sets ``name``/``version``/
``description``, and implements ``evaluate`` as an async generator of
``Finding``s (no findings means the service passes the scorecard). Concrete
subclasses register themselves in ``SCORECARD_REGISTRY`` on definition.
"""

from __future__ import annotations

import enum
from abc import ABC, abstractmethod
from dataclasses import asdict, dataclass
from typing import TYPE_CHECKING, ClassVar

from servicecat.errors import NotFoundError

if TYPE_CHECKING:
    from collections.abc import AsyncIterator
    from pathlib import Path

    from servicecat.models import Service


class Severity(enum.StrEnum):
    """How bad a finding is. Drives routing and ordering."""

    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


@dataclass(frozen=True, slots=True)
class Evidence:
    """Where a finding was observed in the repo."""

    file_path: str
    line: int | None = None
    snippet: str | None = None


@dataclass(frozen=True, slots=True)
class Finding:
    """A single failed criterion produced by a scorecard."""

    criterion_id: str
    severity: Severity
    remediation: str
    evidence: Evidence | None = None
    auto_fixable: bool = False

    def to_dict(self) -> dict[str, object]:
        """JSON-ready dict (enum -> its value) for persistence/serialization."""
        data: dict[str, object] = asdict(self)
        data["severity"] = self.severity.value
        return data


SCORECARD_REGISTRY: dict[str, type[BaseScorecard]] = {}


class BaseScorecard(ABC):
    """Abstract scorecard. Concrete subclasses auto-register by ``name``."""

    name: ClassVar[str]
    version: ClassVar[str]
    description: ClassVar[str]

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        # Register only concrete scorecards (those that declared a name).
        if getattr(cls, "name", None):
            SCORECARD_REGISTRY[cls.name] = cls

    @abstractmethod
    def evaluate(self, service: Service, repo_path: Path) -> AsyncIterator[Finding]:
        """Yield a Finding per failed criterion. No yields => the service passes."""


def get_scorecard(name: str) -> type[BaseScorecard]:
    """Look up a registered scorecard class by name, or raise NotFoundError."""
    try:
        return SCORECARD_REGISTRY[name]
    except KeyError as exc:
        raise NotFoundError(f"Unknown scorecard: {name}") from exc
