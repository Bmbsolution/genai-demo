"""Documentation scorecard: baseline docs every service should ship with.

Each criterion is a private method that inspects the cloned repo at
``repo_path`` and returns a Finding when the doc is missing (None when present).
``evaluate`` yields the non-None findings; an empty result means the service
passes. The five criteria here mirror the rows seeded into scorecard_criteria
by migration 0006.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, ClassVar

from servicecat.scorecards.base import BaseScorecard, Evidence, Finding, Severity

if TYPE_CHECKING:
    from collections.abc import AsyncIterator, Callable
    from pathlib import Path

    from servicecat.models import Service


class DocumentationScorecard(BaseScorecard):
    """Scores a repository on five baseline documentation criteria."""

    name: ClassVar[str] = "documentation"
    version: ClassVar[str] = "1.0.0"
    description: ClassVar[str] = "Checks a service repository for baseline documentation."

    async def evaluate(self, service: Service, repo_path: Path) -> AsyncIterator[Finding]:
        del service  # documentation checks depend only on the repository contents
        checks: tuple[Callable[[Path], Finding | None], ...] = (
            self._readme,
            self._openapi,
            self._runbook,
            self._changelog,
            self._codeowners,
        )
        for check in checks:
            finding = check(repo_path)
            if finding is not None:
                yield finding

    @staticmethod
    def _readme(repo_path: Path) -> Finding | None:
        if (repo_path / "README.md").is_file():
            return None
        return Finding(
            criterion_id="doc.readme_present",
            severity=Severity.HIGH,
            remediation="Add a README.md at the repository root describing the service.",
            evidence=Evidence(file_path="README.md"),
            auto_fixable=True,
        )

    @staticmethod
    def _openapi(repo_path: Path) -> Finding | None:
        if any(
            (repo_path / name).is_file() for name in ("openapi.yaml", "openapi.yml", "openapi.json")
        ):
            return None
        return Finding(
            criterion_id="doc.openapi_spec",
            severity=Severity.MEDIUM,
            remediation="Commit an openapi.yaml/openapi.json (or expose /openapi.json).",
            evidence=Evidence(file_path="openapi.yaml"),
        )

    @staticmethod
    def _runbook(repo_path: Path) -> Finding | None:
        if (repo_path / "RUNBOOK.md").is_file() or (repo_path / "docs" / "runbook.md").is_file():
            return None
        return Finding(
            criterion_id="doc.runbook",
            severity=Severity.MEDIUM,
            remediation="Add a RUNBOOK.md (or docs/runbook.md) with on-call procedures.",
            evidence=Evidence(file_path="RUNBOOK.md"),
        )

    @staticmethod
    def _changelog(repo_path: Path) -> Finding | None:
        if (repo_path / "CHANGELOG.md").is_file():
            return None
        return Finding(
            criterion_id="doc.changelog",
            severity=Severity.LOW,
            remediation="Add a CHANGELOG.md (or publish semver release tags).",
            evidence=Evidence(file_path="CHANGELOG.md"),
            auto_fixable=True,
        )

    @staticmethod
    def _codeowners(repo_path: Path) -> Finding | None:
        if (repo_path / ".github" / "CODEOWNERS").is_file():
            return None
        return Finding(
            criterion_id="doc.codeowners",
            severity=Severity.MEDIUM,
            remediation="Add a .github/CODEOWNERS file mapping paths to owning teams.",
            evidence=Evidence(file_path=".github/CODEOWNERS"),
            auto_fixable=True,
        )
