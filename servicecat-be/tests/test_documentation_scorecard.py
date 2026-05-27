"""Tests for the Documentation scorecard's five criteria, over fixture repos."""

from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

from servicecat.scorecards import DocumentationScorecard, Finding

if TYPE_CHECKING:
    from pathlib import Path

ALL_CRITERIA = {
    "doc.readme_present",
    "doc.openapi_spec",
    "doc.runbook",
    "doc.changelog",
    "doc.codeowners",
}


def _write_passing_repo(root: Path) -> None:
    (root / "README.md").write_text("# Service\n", encoding="utf-8")
    (root / "openapi.yaml").write_text("openapi: 3.1.0\n", encoding="utf-8")
    (root / "RUNBOOK.md").write_text("# Runbook\n", encoding="utf-8")
    (root / "CHANGELOG.md").write_text("# Changelog\n", encoding="utf-8")
    (root / ".github").mkdir()
    (root / ".github" / "CODEOWNERS").write_text("* @team\n", encoding="utf-8")


async def _evaluate(root: Path) -> list[Finding]:
    scorecard = DocumentationScorecard()
    return [finding async for finding in scorecard.evaluate(service=None, repo_path=root)]  # type: ignore[arg-type]


async def test_fully_documented_repo_passes(tmp_path: Path) -> None:
    _write_passing_repo(tmp_path)
    assert await _evaluate(tmp_path) == []


async def test_empty_repo_fails_every_criterion(tmp_path: Path) -> None:
    findings = await _evaluate(tmp_path)
    assert {finding.criterion_id for finding in findings} == ALL_CRITERIA


@pytest.mark.parametrize(
    ("missing_path", "expected_criterion"),
    [
        ("README.md", "doc.readme_present"),
        ("openapi.yaml", "doc.openapi_spec"),
        ("RUNBOOK.md", "doc.runbook"),
        ("CHANGELOG.md", "doc.changelog"),
        (".github/CODEOWNERS", "doc.codeowners"),
    ],
)
async def test_missing_single_file_yields_its_finding(
    tmp_path: Path,
    missing_path: str,
    expected_criterion: str,
) -> None:
    _write_passing_repo(tmp_path)
    (tmp_path / missing_path).unlink()
    findings = await _evaluate(tmp_path)
    assert [finding.criterion_id for finding in findings] == [expected_criterion]


async def test_openapi_json_alternative_passes(tmp_path: Path) -> None:
    _write_passing_repo(tmp_path)
    (tmp_path / "openapi.yaml").unlink()
    (tmp_path / "openapi.json").write_text("{}", encoding="utf-8")
    findings = await _evaluate(tmp_path)
    assert all(finding.criterion_id != "doc.openapi_spec" for finding in findings)


async def test_docs_runbook_alternative_passes(tmp_path: Path) -> None:
    _write_passing_repo(tmp_path)
    (tmp_path / "RUNBOOK.md").unlink()
    (tmp_path / "docs").mkdir()
    (tmp_path / "docs" / "runbook.md").write_text("# Runbook\n", encoding="utf-8")
    findings = await _evaluate(tmp_path)
    assert all(finding.criterion_id != "doc.runbook" for finding in findings)
