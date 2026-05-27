"""Unit tests for the scorecard plugin contract and registry (no DB)."""

from __future__ import annotations

from typing import TYPE_CHECKING, ClassVar

import pytest

from servicecat.errors import NotFoundError
from servicecat.scorecards import BaseScorecard, Evidence, Finding, Severity, get_scorecard
from servicecat.scorecards.base import SCORECARD_REGISTRY

if TYPE_CHECKING:
    from collections.abc import AsyncIterator
    from pathlib import Path

    from servicecat.models import Service


class _DummyScorecard(BaseScorecard):
    name: ClassVar[str] = "dummy"
    version: ClassVar[str] = "1.0.0"
    description: ClassVar[str] = "A test scorecard."

    async def evaluate(self, service: Service, repo_path: Path) -> AsyncIterator[Finding]:
        del service, repo_path
        yield Finding(
            criterion_id="dummy.always_fails",
            severity=Severity.LOW,
            remediation="Fix it.",
        )


def test_severity_values() -> None:
    assert {s.value for s in Severity} == {"critical", "high", "medium", "low"}


def test_finding_to_dict_serializes_enum_and_evidence() -> None:
    finding = Finding(
        criterion_id="doc.readme_present",
        severity=Severity.HIGH,
        remediation="Add a README.md.",
        evidence=Evidence(file_path="README.md", line=1, snippet="missing"),
        auto_fixable=True,
    )
    data = finding.to_dict()
    assert data["severity"] == "high"
    assert data["criterion_id"] == "doc.readme_present"
    assert data["auto_fixable"] is True
    assert data["evidence"] == {"file_path": "README.md", "line": 1, "snippet": "missing"}


def test_finding_without_evidence_serializes_none() -> None:
    data = Finding(criterion_id="x", severity=Severity.LOW, remediation="y").to_dict()
    assert data["evidence"] is None


def test_concrete_scorecard_auto_registers() -> None:
    assert SCORECARD_REGISTRY.get("dummy") is _DummyScorecard
    assert get_scorecard("dummy") is _DummyScorecard


def test_get_unknown_scorecard_raises() -> None:
    with pytest.raises(NotFoundError, match="Unknown scorecard"):
        get_scorecard("does-not-exist")


def test_base_scorecard_cannot_be_instantiated() -> None:
    with pytest.raises(TypeError):
        BaseScorecard()  # type: ignore[abstract]


async def test_evaluate_yields_findings() -> None:
    findings = [
        finding
        async for finding in _DummyScorecard().evaluate(service=None, repo_path=None)  # type: ignore[arg-type]
    ]
    assert len(findings) == 1
    assert findings[0].criterion_id == "dummy.always_fails"
