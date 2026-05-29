---
name: new-scorecard
description: Scaffold a new scorecard plugin (BaseScorecard subclass + criteria checks + registration + tests). Use when the user asks to add a new scorecard type like Security, Observability, Documentation, Reliability, or a custom one.
allowed-tools: Read, Write, Edit, Grep, Glob, Bash
---

# /new-scorecard

You scaffold a new scorecard plugin. A scorecard is a **pure-code plugin**: it subclasses `BaseScorecard`, evaluates a service's cloned repo against criteria, and yields `Finding`s. There is **no** per-criterion DB table, no seed migration, and no UI config form — read `servicecat-be/src/servicecat/scorecards/documentation.py`; it is the canonical reference, and `base.py` defines the contract.

## Invocation

```
/new-scorecard observability
/new-scorecard security
```

## The contract (from scorecards/base.py — verify before writing)

- Subclass `BaseScorecard`; set the `name`, `version`, `description` ClassVars.
- Implement `async def evaluate(self, service, repo_path) -> AsyncIterator[Finding]` — yield one `Finding` per failed criterion; yield nothing if the service passes.
- Concrete subclasses **auto-register** via `__init_subclass__` keyed on `name` — you do NOT edit a registry dict. You only need to import the module so the class body runs.
- `Finding(criterion_id, severity, remediation, evidence=None, auto_fixable=False)`.
- `severity` is the `Severity` StrEnum (`CRITICAL/HIGH/MEDIUM/LOW`).
- `evidence` is the `Evidence` dataclass `(file_path, line=None, snippet=None)` — **not** a string.

## What you produce (3 artifacts — that's all)

### 1. The scorecard class — `servicecat-be/src/servicecat/scorecards/<name>.py`

Match documentation.py's shape: small static check methods returning `Finding | None`, and `evaluate` iterating them.

```python
"""Observability scorecard: is the service observable in production?"""

from __future__ import annotations

from typing import TYPE_CHECKING

from servicecat.scorecards.base import BaseScorecard, Evidence, Finding, Severity

if TYPE_CHECKING:
    from collections.abc import AsyncIterator, Callable
    from pathlib import Path

    from servicecat.models import Service


class ObservabilityScorecard(BaseScorecard):
    name = "observability"
    version = "1.0.0"
    description = "Service is observable in production: metrics, structured logs, alerts."

    async def evaluate(self, service: Service, repo_path: Path) -> AsyncIterator[Finding]:  # noqa: ARG002
        checks: tuple[Callable[[Path], Finding | None], ...] = (
            self._metrics_endpoint,
            self._structured_logging,
            # ...one method per criterion
        )
        for check in checks:
            finding = check(repo_path)
            if finding is not None:
                yield finding

    @staticmethod
    def _metrics_endpoint(repo_path: Path) -> Finding | None:
        for candidate in (*repo_path.rglob("*.py"), *repo_path.rglob("*.ts")):
            text = candidate.read_text(errors="ignore")
            if "/metrics" in text and "prometheus" in text.lower():
                return None  # criterion passes
        return Finding(
            criterion_id="obs.metrics_endpoint",
            severity=Severity.HIGH,
            remediation=(
                "Expose a /metrics endpoint in Prometheus format "
                "(FastAPI: prometheus-fastapi-instrumentator; Express: prom-client)."
            ),
            evidence=Evidence(file_path="(repo)"),
            auto_fixable=True,
        )
```

Keep criteria **automatable** (read concrete files) and remediations **concrete** ("add /metrics with prometheus-fastapi-instrumentator", not "improve observability"). Set `auto_fixable` honestly — `false` if `/work-findings` couldn't reasonably generate the fix.

### 2. Registration — `servicecat-be/src/servicecat/scorecards/__init__.py`

Importing the module triggers `__init_subclass__`. Add the import and the export:

```python
from servicecat.scorecards.observability import ObservabilityScorecard
# ...
__all__ = [..., "ObservabilityScorecard", ...]
```

That's the whole registration — no dict edits, no migration. Confirm it's discoverable: `get_scorecard("observability")` should return the class, and `POST /api/v1/scorecards/observability/runs` should accept it.

### 3. Tests — `servicecat-be/tests/test_<name>_scorecard.py`

Mirror `tests/test_documentation_scorecard.py`. For each criterion, drive `evaluate` over a `tmp_path` repo and assert on the yielded `criterion_id`s:

```python
async def _findings(scorecard, repo: Path) -> list[Finding]:
    service = Service(workspace_id=uuid.uuid4(), name="svc", repo_url="file://x", tier=1)
    return [f async for f in scorecard.evaluate(service, repo)]

async def test_flags_missing_metrics(tmp_path: Path) -> None:
    findings = await _findings(ObservabilityScorecard(), tmp_path)
    assert any(f.criterion_id == "obs.metrics_endpoint" for f in findings)

async def test_passes_when_metrics_present(tmp_path: Path) -> None:
    (tmp_path / "app.py").write_text("from prometheus_client import ...\n@app.get('/metrics')")
    findings = await _findings(ObservabilityScorecard(), tmp_path)
    assert not any(f.criterion_id == "obs.metrics_endpoint" for f in findings)
```

## Default criterion sets (offer these if the user doesn't specify)

- **security**: tls_enforced, no_secrets_in_repo, dependencies_updated, security_headers, vulnerability_scan
- **observability**: metrics_endpoint, structured_logging, distributed_tracing, alert_definitions, runbook
- **reliability**: ci_config, healthcheck, rollback_strategy, retry_strategy, sla_defined

## Process

1. Confirm the name (snake_case) and the criterion list with the user if not given.
2. Write the class, add the import/export in `__init__.py`, write the tests.
3. `make lint && make test` — fix until green (inner fix loop, max 3 attempts).
4. `/commit-sc` → `feat(scorecards): add <name> scorecard with N criteria`.

## What you must NOT do

- Invent a `scorecard_criteria` table, a seed migration, or a UI config form — none exist here.
- Edit a registry dict by hand — registration is automatic via `__init_subclass__`.
- Use a string for `evidence` — it's the `Evidence` dataclass.
- Skip tests, or invent criteria the user didn't approve.
