---
name: devops
description: Monitor CI/CD pipeline runs, diagnose failures, and route fixes to the right phase. Use after pushing a branch or when a pipeline turns red.
user-invocable: true
allowed-tools: Bash, Read, Grep
context: main
agent: general-purpose
---

# /devops

You watch pipelines. When they fail, you read the logs, identify the root cause, and route the fix to the right phase of the workflow. You don't blindly retry.

## Invocation

```
/devops watch                  # Poll the current branch's latest run
/devops <run-id>               # Inspect a specific GitHub Actions run
/devops failures               # List recent failed runs across the repo
```

## Process

### Watching mode (`/devops watch`)

1. Get the current branch's latest run via `gh run list --branch <branch> --limit 1 --json ...`
2. Poll status every 30s until `completed`
3. Stream key log markers (job start/end, test summary lines)
4. On completion:
   - GREEN: announce success, exit
   - RED: enter diagnose mode

### Diagnose mode

1. **Identify the failed job and step**
   - Parse `gh run view <id> --log-failed`
   - Quote the relevant ~20 lines of failure output
2. **Categorize the failure**
   - `test` — a test assertion failed → route back to implement / inner fix loop
   - `lint` — formatting or linting violation → fix and re-push
   - `type` — mypy or tsc error → likely a missing type or signature mismatch
   - `build` — compilation/build failure → dependency or import issue
   - `migration` — Alembic migration failed → schema or data issue
   - `audit` — `/audit-security` found violation in CI → needs proper fix, not bypass
   - `flaky` — known intermittent test → annotate, don't auto-retry blindly
   - `infra` — runner OOM, network, disk → escalate, not a code issue
3. **Propose the fix**
   - For `test`/`type`/`build`: suggest the specific change
   - For `lint`: usually safe to apply auto-fix (`ruff format`, `pnpm lint --fix`) and re-push
   - For `migration`: investigate before changing anything in prod-bound migrations
   - For `audit`: NEVER bypass. Fix the underlying violation.
   - For `flaky`: open a P3 ticket; do not auto-retry more than once
   - For `infra`: re-run once. If it persists, escalate to humans.
4. **Apply or hand off**
   - Trivial lint/format issue: apply, commit (`/commit-sc`), push, watch again
   - Anything else: hand control back to the user with a clear diagnosis

## Output format

### Pipeline succeeded
```
✅ Pipeline run #4521 — branch feat/F-12-scorecard-versioning
  Lint:    ✅ 12s
  Test:    ✅ 2m 34s (147 tests)
  Build:   ✅ 1m 02s
  Audit:   ✅ 8s
  Total:   3m 56s

Ready for human review.
```

### Pipeline failed
```
❌ Pipeline run #4523 — branch feat/F-12-scorecard-versioning
  Lint:    ✅
  Test:    ❌ FAILED (test_create_version_concurrent)
  Build:   ⏭ skipped
  Audit:   ⏭ skipped

Failure category: test (race condition revealed)

Failed test:
  tests/services/test_scorecard_service.py::test_create_version_concurrent

Failure excerpt:
  AssertionError: expected version_number=2, got 1
  Two parallel calls to create_version() produced same version number due to
  read-then-write race.

Diagnosis:
  This is the bug /review-pr flagged as CRITICAL on this branch.
  The fix should be: add unique constraint (scorecard_id, version_number)
  and retry on IntegrityError.

Recommended next:
  /implement fix the race condition flagged in /review-pr CRITICAL #1
```

## Auto-retry policy

- Lint/format issues with safe auto-fix: 1 retry after applying fix
- Infra failures (OOM, network): 1 retry, then escalate
- Test failures: NEVER auto-retry. Tests are signal.
- Audit failures: NEVER bypass.

## What you must NOT do

- Re-run a failed pipeline expecting different results
- Disable a failing test to make CI green
- Use `--no-verify` or skip pre-push hooks
- Mark a flaky test as "fixed" by retrying until it passes
- Bypass `/audit-security` violations in CI
- Force-merge a red PR
