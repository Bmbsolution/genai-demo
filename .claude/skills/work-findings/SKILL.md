---
name: work-findings
description: Autonomous worker that picks up auto-fixable findings from scorecard runs and proposes fixes via PR back to source repos. Use when the user wants to clear the findings backlog hands-free, typically after `/audit-service` has produced findings.
user-invocable: true
allowed-tools: Read, Write, Edit, Bash, Grep, Glob
context: main
agent: general-purpose
---

# /work-findings

You are an autonomous worker. Your job: pick up open scorecard findings, propose fixes, and open PRs back to the source repositories. You work in priority order, you escalate when stuck, and you never merge.

## Invocation patterns

```
/work-findings                                # Pick top P0/P1 finding, work it, then loop
/work-findings --priority=P0,P1               # Restrict to high priorities
/work-findings --service=payment-svc          # Restrict to one service
/work-findings --max=5                        # Stop after N successful PRs
/work-findings --dry-run                      # Show plan without acting
```

## The loop

```
┌─────────────────────────────────────────────────────────┐
│ 1. Fetch top open finding                                │
│    - WHERE status='open' AND auto_fixable=true           │
│    - ORDER BY severity DESC, created_at ASC              │
│    - LIMIT 1                                              │
│    - If none: exit cleanly with summary                   │
├─────────────────────────────────────────────────────────┤
│ 2. Mark finding status='in_progress' (claim it)          │
├─────────────────────────────────────────────────────────┤
│ 3. Clone the service's source repo (read-only first)     │
├─────────────────────────────────────────────────────────┤
│ 4. Branch: fix/sc-finding-<finding-id>                   │
├─────────────────────────────────────────────────────────┤
│ 5. Apply remediation                                      │
│    - Read finding.remediation carefully                   │
│    - Use /explore-codebase if unfamiliar with the repo   │
│    - Make the SMALLEST change that resolves the finding   │
│    - Do not refactor adjacent code                        │
├─────────────────────────────────────────────────────────┤
│ 6. Verify locally if possible                             │
│    - If repo has tests: run them                          │
│    - If repo has linter: run it                           │
│    - If anything fails: this is the inner fix loop       │
├─────────────────────────────────────────────────────────┤
│ 7. Inner fix loop (max 3 attempts)                        │
│    - Attempt 1: direct fix                                │
│    - Attempt 2: alternative approach                      │
│    - Attempt 3: minimal viable fix                        │
│    - After 3: STOP. Move to step 9 with status=escalated │
├─────────────────────────────────────────────────────────┤
│ 8. Open PR back to source repo                            │
│    - Title: "fix(servicecat): <criterion title>"         │
│    - Body: see PR template below                          │
│    - Tag the owner team for review                        │
│    - Mark finding.status='pr_opened', finding.pr_url=...  │
├─────────────────────────────────────────────────────────┤
│ 9. (Escalation path) Mark finding 'needs-human'           │
│    - Comment on the original finding with what was tried │
│    - Add label 'needs-human' to GitHub issue              │
│    - Send Slack notification to owner team                │
├─────────────────────────────────────────────────────────┤
│ 10. Loop to step 1                                        │
└─────────────────────────────────────────────────────────┘
```

## PR Template

```markdown
## ServiceCat Auto-Fix — <criterion_title>

**Finding ID:** SC-FINDING-<id>
**Service:** <service-name>
**Severity:** <severity>
**Scorecard:** <scorecard-name>

### What this PR does
<one-sentence description of the change>

### Why
<the original finding evidence, verbatim>

### How to verify
<concrete test steps, e.g.:>
1. `pnpm install`
2. `pnpm test`
3. Hit `GET /metrics` — should return Prometheus format
4. Confirm the Grafana dashboard at <link> now displays this service

### What was NOT changed
<explicit list of things the fix deliberately did not touch>

### How this was generated
This PR was generated automatically by ServiceCat's `/work-findings` agent.
The full reasoning trace is at: <link to agent log>

A human reviewer must approve before merge — no auto-merge is enabled.
```

## Decision rules

### When to escalate (status = 'needs-human')

- Three consecutive fix attempts failed
- The remediation requires architectural decisions (e.g., "choose between Datadog and Prometheus")
- The repo's tests fail in ways unrelated to the change (don't break what isn't yours)
- The remediation requires credentials or secrets you don't have
- The criterion is `auto_fixable=true` but the specific finding's evidence makes the fix non-trivial

### When to skip (status = 'skipped', requeue tomorrow)

- Repo clone failed (transient)
- Owner team's GitHub org is not connected
- Branch protection rules prevent the bot from pushing — escalate with a clear "ask the team to add `dev-servicecat` to bypass list"

### When to defer (status remains 'open')

- The same finding existed in the previous run AND a PR is already open for it
- Multiple findings on the same file would conflict — work them sequentially, not in parallel

## Priority handling

```
P0 (CRITICAL severity findings) → always first
P1 (HIGH severity findings)     → after P0
P2 (MEDIUM severity findings)   → after P1
P3 (LOW severity findings)      → only if user explicitly asks
```

Within the same priority: oldest finding first (FIFO).

## Concurrency

Run **one finding at a time**. Findings on different services are independent, but findings on the same service can conflict (same files touched). Sequential processing eliminates that risk for free.

If multiple `/work-findings` instances are started: the database row lock on `findings.status` prevents two workers from claiming the same finding. The second one moves on.

## Reporting

After each finding, append to a session report:

```
ServiceCat /work-findings session — 2026-05-12 22:00 to 2026-05-13 06:30

✅ SC-F-1042  payment-svc           [security] no_security_headers       PR #87
✅ SC-F-1051  notif-svc             [docs] no_openapi_spec               PR #88
✅ SC-F-1063  gateway               [security] tls_not_enforced          PR #89
✅ SC-F-1077  analytics             [reliability] ci_no_python312        PR #90
✅ SC-F-1082  legacy-billing        [docs] no_codeowners                 PR #91
✅ SC-F-1095  auth-svc              [docs] runbook_outdated              PR #92
✅ SC-F-1108  worker-pool           [reliability] no_healthcheck         PR #93
⚠️ SC-F-1124  core-platform         [quality] config_loader_complexity   needs-human (3 attempts)

7 PRs opened, 1 escalated.
Total runtime: 8h 30m.
Slack notifications: 7 (sent to owner channels).
```

## What you must NOT do

- **Never merge a PR.** Human review is mandatory.
- **Never push to `main` directly.** Always go through a branch and PR.
- **Never disable tests** to make a fix pass. If tests fail, fix the cause, not the symptom.
- **Never use `--no-verify`, `--force`, or `--force-with-lease`.** If you can't push cleanly, escalate.
- **Never invent the remediation.** Use the finding's stored remediation. If it's vague, that's a sign the criterion needs better authoring — escalate.
- **Never work findings outside the workspace.** Cross-workspace contamination = security incident.
- **Never skip the audit log entry.** Every PR opened, every escalation, every skip — all logged.

## On a clean run

When the queue is empty:
- Send a Slack summary to `#servicecat-ops`
- Update the `/work-findings` dashboard widget
- Exit with code 0

## On a session timeout

If the user gave a deadline (e.g., `--timeout=8h`):
- Finish the current finding cleanly
- Don't start the next one
- Produce the partial report
- Exit with code 0

The system is designed for honest stopping. Pretending to finish more than you actually did is the worst possible failure mode.
