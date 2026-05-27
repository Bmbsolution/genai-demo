---
name: new-scorecard
description: Scaffold a new scorecard plugin (model + criteria definitions + scorer class + UI form + tests). Use when the user asks to add a new scorecard type like Security, Observability, Documentation, Reliability, or a custom one.
user-invocable: true
allowed-tools: Read, Write, Edit, Grep, Glob, Bash
context: main
agent: general-purpose
---

# /new-scorecard

You are scaffolding a new scorecard plugin for ServiceCat. A scorecard evaluates services against a set of criteria and produces findings with severity, evidence, and remediation.

## What you must produce

Given an argument like `/new-scorecard observability`, you produce ALL of the following in one pass:

### 1. The scorecard class
File: `servicecat-be/src/scorecards/<name>.py`

```python
from pathlib import Path
from typing import AsyncIterator
from servicecat.scorecards.base import BaseScorecard, Finding, Severity
from servicecat.models import Service

class ObservabilityScorecard(BaseScorecard):
    name = "observability"
    version = "1.0.0"
    description = "Service is observable in production: logs, metrics, traces, alerts."

    async def evaluate(self, service: Service, repo_path: Path) -> AsyncIterator[Finding]:
        async for finding in self._check_has_metrics_endpoint(service, repo_path):
            yield finding
        async for finding in self._check_has_structured_logging(service, repo_path):
            yield finding
        # ... one private method per criterion
```

### 2. Criterion definitions
Each criterion is its own private method that:
- Reads concrete files from `repo_path`
- Yields `Finding` objects with `criterion_id`, `severity`, `evidence`, `remediation`, `auto_fixable`
- Returns nothing (empty iterator) if the criterion passes

Example:
```python
async def _check_has_metrics_endpoint(
    self, service: Service, repo_path: Path
) -> AsyncIterator[Finding]:
    """Service must expose /metrics for Prometheus scraping."""
    candidates = list(repo_path.rglob("*.py")) + list(repo_path.rglob("*.ts"))
    for candidate in candidates:
        content = candidate.read_text(errors="ignore")
        if "/metrics" in content and "prometheus" in content.lower():
            return  # Pass
    yield Finding(
        criterion_id="obs.metrics_endpoint",
        severity=Severity.HIGH,
        evidence=f"No /metrics endpoint found in {service.repo_url}",
        remediation="Add a /metrics endpoint exposing Prometheus-format metrics. "
                    "For FastAPI: use prometheus-fastapi-instrumentator. "
                    "For Express: use prom-client.",
        auto_fixable=True,
    )
```

### 3. Registration
Add the new scorecard to the registry in `servicecat-be/src/scorecards/__init__.py`:

```python
from servicecat.scorecards.observability import ObservabilityScorecard

SCORECARD_REGISTRY = {
    ...,
    "observability": ObservabilityScorecard,
}
```

### 4. Migration for criterion seed data
Generate an Alembic migration that inserts criterion rows into the `scorecard_criteria` table:

```python
"""Add observability scorecard criteria

Revision ID: <auto>
Revises: <prev>
Create Date: ...
"""
def upgrade() -> None:
    op.execute("""
        INSERT INTO scorecard_criteria (id, scorecard_name, criterion_id, title, description, default_severity)
        VALUES
            (gen_random_uuid(), 'observability', 'obs.metrics_endpoint',
             'Exposes /metrics endpoint',
             'Service must expose Prometheus-format metrics for scraping.',
             'HIGH'),
            ...;
    """)

def downgrade() -> None:
    op.execute("DELETE FROM scorecard_criteria WHERE scorecard_name = 'observability';")
```

### 5. Frontend form component
File: `servicecat-fe/components/scorecards/ObservabilityScorecardForm.tsx`

A shadcn-based form for configuring the scorecard's options at the workspace level (e.g., minimum log retention days, required alert channels). Use the existing `<ScorecardConfigForm>` wrapper.

### 6. Tests
File: `servicecat-be/tests/scorecards/test_observability.py`

For EACH criterion:
- One test with a fixture repo that PASSES the criterion (yields no finding)
- One test with a fixture repo that FAILS (yields the expected finding)
- Use `tests/fixtures/scorecard_repos/<scorecard_name>/<pass|fail>__<criterion>/` for fixture repos

### 7. Documentation
Append a section to `docs/scorecards.md` documenting:
- What the scorecard checks
- Each criterion's title, severity, and remediation hint
- Example output (a passing service and a failing service)

## Process

1. **Confirm the scorecard name** with the user if ambiguous. Convert to `snake_case`.
2. **Ask for the criterion list** if not provided. Default sets:
   - `security`: tls_enforced, no_secrets_in_repo, dependencies_updated, security_headers, secrets_rotated, vulnerability_scan
   - `observability`: metrics_endpoint, structured_logging, distributed_tracing, alert_definitions, dashboard, runbook
   - `documentation`: readme_present, openapi_spec, runbook, changelog, owner, codeowners
   - `reliability`: ci_green, deployment_automated, rollback_strategy, sla_defined, healthcheck, retry_strategy
3. **Scaffold all 7 artifacts** in order. Run lint and tests after generation.
4. **Verify with `/audit-security`** — the new scorecard endpoints (if any) must pass.
5. **Commit** via `/commit-sc`. Suggested message format: `feat(scorecards): add <name> scorecard with N criteria`.

## Quality bar

- Every criterion must be **automatable** — must read concrete files, never ask "is this service well-observed?" in vague terms.
- Every finding must have a **concrete remediation** — not "improve observability" but "add /metrics endpoint with prometheus-fastapi-instrumentator".
- The `auto_fixable` flag must be honest. If `/work-findings` cannot reasonably generate a fix, set it to `false`.

## What you must NOT do

- Do not invent criteria the user didn't approve.
- Do not skip tests. A new scorecard without tests is not done.
- Do not register the scorecard before all artifacts are in place — registration last.
- Do not generate migrations that touch existing scorecards.
