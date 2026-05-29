---
name: audit-service
description: Run all (or selected) scorecards against a registered service. Fetches the repo, evaluates criteria, produces findings, routes them to owners. Use when the user asks to audit, score, or check compliance of a service.
allowed-tools: Read, Bash, Grep, Glob
---

# /audit-service

> **Local setup:** runs fully against the local stack (API on :8000 + the Arq worker). The optional Slack notification step is skipped unless the Slack MCP is configured.

You are running scorecards against a service in the ServiceCat catalog. Your job is to produce a complete, actionable audit report — not a vague summary.

## Invocation patterns

```
/audit-service <service-name>                      # All scorecards
/audit-service <service-name> --scorecard=<name>   # One specific scorecard
/audit-service all                                  # All services, all scorecards (fleet sweep)
/audit-service all --scorecard=security             # All services, one scorecard
```

## Process

### 1. Resolve the service(s)
- For `<service-name>`: query the catalog. If not found, fail with a clear message and a list of similar names.
- For `all`: list every active service in the workspace.

### 2. Fetch repo content
Use the `/audit-service` worker (already wired in `servicecat-be/src/workers/audit_runner.py`) to:
- Clone the repo to ephemeral storage with a 5-minute TTL
- Use a shallow clone (`--depth 50`)
- Verify the service's branch (defaults to `main`)
- If clone fails: produce a `runtime_error` finding and skip

### 3. Run scorecards
For each scorecard:
- Instantiate from `SCORECARD_REGISTRY`
- Run `evaluate(service, repo_path)` and collect findings
- Capture the run in `scorecard_runs` table with start/end timestamps and total finding count

### 4. Route findings to owners
For each finding:
- Look up the service's owner team
- Set `assigned_to_team_id` on the finding
- If the team has Slack channel configured: enqueue `/notify` with the finding summary
- If the finding's `auto_fixable=true` and severity is HIGH or CRITICAL: tag for `/work-findings`

### 5. Produce the report
Output a structured report:

```
ServiceCat Audit — payment-svc
Run ID: r-2026-05-12-1430
Scorecards: security, observability, documentation, reliability

Score: 72 / 100  (▼ 8 from last run)

CRITICAL (1)
  [security] secrets_in_repo
    Evidence: servicecat-be/src/config.py:34 — "API_KEY = 'sk-prod...'"
    Remediation: Move to environment variable. See docs/secrets.md.
    Owner: payments-team   Auto-fixable: NO (requires team review)

HIGH (3)
  [security] no_security_headers
    Evidence: nginx/default.conf — missing X-Frame-Options, CSP
    Remediation: Add the standard security headers block from templates/nginx-secure.conf
    Owner: payments-team   Auto-fixable: YES   → queued for /work-findings

  [observability] no_metrics_endpoint
    Evidence: No Prometheus instrumentation found in 47 Python files
    Remediation: Add prometheus-fastapi-instrumentator to main.py
    Owner: payments-team   Auto-fixable: YES   → queued for /work-findings

  [documentation] no_runbook
    Evidence: No RUNBOOK.md or docs/runbook.md
    Remediation: Run `/draft-runbook payment-svc` to generate one from code
    Owner: payments-team   Auto-fixable: YES   → queued for /work-findings

MEDIUM (4)
  ...

LOW (2)
  ...

Summary: 1 CRITICAL, 3 HIGH, 4 MEDIUM, 2 LOW
Auto-fixable: 6 / 10
PRs queued: 6
Slack notifications sent: 1 (#payments-team)
```

### 6. Persist
- All findings written to `findings` table with `scorecard_run_id` foreign key
- Score recorded in `scores` table (denormalized aggregate per service per scorecard)
- Run completion event published to `audit_log`

## Output rules

- **Always sort findings by severity** (CRITICAL → HIGH → MEDIUM → LOW), then alphabetically by `criterion_id`.
- **Never produce findings without evidence** — if a check can't actually verify something, it shouldn't yield a finding.
- **Severity is from the criterion definition**, not invented per-run. If a criterion's `default_severity` is HIGH, every finding from it is HIGH.
- **Don't summarize remediations** — copy them verbatim from the criterion definition. They were written carefully.
- **If a service has no recent commits** (>180 days inactive), prepend a warning to the report: "⚠ Service may be abandoned — last commit X days ago."

## Failure modes to handle

| Failure | Behavior |
|---------|----------|
| Service not in catalog | Fail clearly, list similar names |
| Repo clone fails | Produce a `runtime.repo_unreachable` finding (severity HIGH); continue with no other scorecards |
| Scorecard raises exception | Capture in run record; log to Sentry; continue with other scorecards; produce a `runtime.scorecard_error` finding |
| Owner team has no Slack channel | Skip notification, log a warning, continue |
| Fleet sweep finds 100+ services | Process in batches of 10 with progress reports |

## What you must NOT do

- Do not auto-create PRs from this skill. That's `/work-findings`'s job.
- Do not modify the service's actual repository — clones are read-only.
- Do not run scorecards for which the user lacks `scorecard:run` capability. Surface a clear permission error.
- Do not skip the audit log entry. Every audit run must be logged.
