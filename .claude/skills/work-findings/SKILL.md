---
name: work-findings
description: Autonomous worker that picks up auto-fixable findings from readiness-checklist runs and proposes fixes via PR back to source repos. Use when the user wants to clear the findings backlog hands-free, typically after `/audit-service` has produced findings.
allowed-tools: Read, Write, Edit, Bash, Grep, Glob
---

# /work-findings

> **Local setup:** the read→fix loop works locally — findings come from readiness-checklist runs in the local DB. The "open a PR back to the source repo" and Slack-summary steps need a remote + Slack MCP; locally, commit fixes to a feature branch and skip the Slack summary.

You are an autonomous worker. Your job: pick up open readiness findings, propose fixes, and open PRs back to the source repositories. You work in priority order, you escalate when stuck, and you never merge.

## Invocation patterns

```
/work-findings                                # Pick top P0/P1 finding, work it, then loop
/work-findings --priority=P0,P1               # Restrict to high priorities
/work-findings --event=summer-launch-party    # Restrict to one event
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
│ 3. Clone the event's source repo (read-only first)       │
├─────────────────────────────────────────────────────────┤
│ 4. Branch: fix/ga-finding-<finding-id>                   │
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
│    - Title: "fix(gatherly): <check title>"               │
│    - Body: see PR template below                          │
│    - Tag the event host for review                        │
│    - Mark finding.status='pr_opened', finding.pr_url=...  │
├─────────────────────────────────────────────────────────┤
│ 9. (Escalation path) Mark finding 'needs-human'           │
│    - Comment on the original finding with what was tried │
│    - Add label 'needs-human' to GitHub issue              │
│    - Send Slack notification to the event host            │
├─────────────────────────────────────────────────────────┤
│ 10. Loop to step 1                                        │
└─────────────────────────────────────────────────────────┘
```

## PR Template

```markdown
## Gatherly Auto-Fix — <check_title>

**Finding ID:** GA-FINDING-<id>
**Event:** <event-name>
**Severity:** <severity>
**Checklist:** Event Readiness

### What this PR does
<one-sentence description of the change>

### Why
<the original finding evidence, verbatim>

### How to verify
<concrete test steps, e.g.:>
1. `pnpm install`
2. `pnpm test`
3. Hit `GET /api/v1/events/{id}/readiness` — the check should now pass
4. Confirm the event reports `ready: true` once all high-severity checks pass

### What was NOT changed
<explicit list of things the fix deliberately did not touch>

### How this was generated
This PR was generated automatically by Gatherly's `/work-findings` agent.
The full reasoning trace is at: <link to agent log>

A human reviewer must approve before merge — no auto-merge is enabled.
```

## Decision rules

### When to escalate (status = 'needs-human')

- Three consecutive fix attempts failed
- The remediation requires a judgment call only the host can make (e.g., "raise the capacity or move guests to the waitlist")
- The repo's tests fail in ways unrelated to the change (don't break what isn't yours)
- The remediation requires credentials or secrets you don't have
- The check is `auto_fixable=true` but the specific finding's evidence makes the fix non-trivial

### When to skip (status = 'skipped', requeue tomorrow)

- Repo clone failed (transient)
- The event host's GitHub org is not connected
- Branch protection rules prevent the bot from pushing — escalate with a clear "ask the team to add `dev-gatherly` to bypass list"

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

Run **one finding at a time**. Findings on different events are independent, but findings on the same event can conflict (same files touched). Sequential processing eliminates that risk for free.

If multiple `/work-findings` instances are started: the database row lock on `findings.status` prevents two workers from claiming the same finding. The second one moves on.

## Reporting

After each finding, append to a session report:

```
Gatherly /work-findings session — 2026-05-12 22:00 to 2026-05-13 06:30

✅ GA-F-1042  summer-launch-party   [readiness] has_location             PR #87
✅ GA-F-1051  q3-allhands           [readiness] has_description          PR #88
✅ GA-F-1063  design-review-dinner  [readiness] has_cover_image          PR #89
✅ GA-F-1077  customer-roundtable   [readiness] has_end_time             PR #90
✅ GA-F-1082  founders-mixer        [readiness] published                PR #91
✅ GA-F-1095  onboarding-brunch     [readiness] has_description          PR #92
✅ GA-F-1108  partner-summit        [readiness] has_cover_image          PR #93
⚠️ GA-F-1124  annual-gala           [readiness] within_capacity          needs-human (3 attempts)

7 PRs opened, 1 escalated.
Total runtime: 8h 30m.
Slack notifications: 7 (sent to host channels).
```

## What you must NOT do

- **Never merge a PR.** Human review is mandatory.
- **Never push to `main` directly.** Always go through a branch and PR.
- **Never disable tests** to make a fix pass. If tests fail, fix the cause, not the symptom.
- **Never use `--no-verify`, `--force`, or `--force-with-lease`.** If you can't push cleanly, escalate.
- **Never invent the remediation.** Use the finding's stored remediation. If it's vague, that's a sign the check needs better authoring — escalate.
- **Never work findings on an event you don't own.** Cross-owner contamination = security incident.
- **Never skip the audit log entry.** Every PR opened, every escalation, every skip — all logged.

## On a clean run

When the queue is empty:
- Send a Slack summary to `#gatherly-ops`
- Update the `/work-findings` dashboard widget
- Exit with code 0

## On a session timeout

If the user gave a deadline (e.g., `--timeout=8h`):
- Finish the current finding cleanly
- Don't start the next one
- Produce the partial report
- Exit with code 0

The system is designed for honest stopping. Pretending to finish more than you actually did is the worst possible failure mode.
