---
name: audit-service
description: Run the event-readiness checklist against an event. Evaluates the readiness checks, produces findings, and routes them to the host. Use when the user asks to audit, score, or check the readiness of an event.
allowed-tools: Read, Bash, Grep, Glob
---

# /audit-service

> **Local setup:** runs fully against the local stack (API on :8002). The optional Slack notification step is skipped unless the Slack MCP is configured.

You are running the event-readiness checklist against an event in Gatherly. Your job is to produce a complete, actionable readiness report — not a vague summary.

## Invocation patterns

```
/audit-service <event-name>                        # Full readiness checklist
/audit-service <event-name> --severity=high        # Only high-severity checks
/audit-service all                                  # All your events (fleet sweep)
/audit-service all --severity=high                  # All events, high-severity checks only
```

## Process

### 1. Resolve the event(s)
- For `<event-name>`: look up the caller's events by title. If not found, fail with a clear message and a list of similar names.
- For `all`: list every event the caller owns (ownership is scoped by `owner_id` — there are no workspaces).

### 2. Load the event and guest list
The readiness checklist is computed by `InsightsService.get_readiness` in `gatherly-be/src/gatherly/services/insights.py`:
- It calls `EventService.get(event_id, owner_id)` first — a non-owned event raises `OwnershipError` (`S2_NOT_OWNER`, surfaced as 404). Do not audit events you don't own.
- It reads the guest list and the event's `EventInsights` (counts, response rate, capacity).
- No repo clone, no background worker — it's a synchronous read against the local DB.

### 3. Run the readiness checks
- Call `GET /api/v1/events/{id}/readiness` (or `InsightsService.get_readiness` directly).
- This returns an `EventReadiness`: `ready`, `passed`, `total`, and the list of `ReadinessCheck(key, passed, severity)`.
- Each failed check (`passed=false`) becomes a finding. The event is `ready` iff every **high**-severity check passes.

### 4. Route findings to the host
For each failed check:
- The event's owner is its host (`owner_id`) — that's who the finding is routed to.
- If the host has a Slack channel configured: enqueue `/notify` with the finding summary.
- If the finding is `auto_fixable=true` and severity is `high`: tag for `/work-findings`.

### 5. Produce the report
Output a structured report:

```
Gatherly Readiness — summer-launch-party
Run at: 2026-05-12 14:30
Checklist: Event Readiness (8 checks)

Ready: NO   (5 / 8 checks passing)

HIGH (2)
  [readiness] has_location
    Evidence: event.location is empty
    Remediation: Set a venue/location on the event before publishing.
    Host: alice@example.com   Auto-fixable: YES   → queued for /work-findings

  [readiness] within_capacity
    Evidence: 142 RSVP=yes exceeds capacity of 120
    Remediation: Raise capacity, or move 22 guests to the waitlist.
    Host: alice@example.com   Auto-fixable: NO (requires host decision)

MEDIUM (1)
  [readiness] healthy_response_rate
    Evidence: response_rate 0.38 < 0.5 threshold
    Remediation: Send a reminder to the 62% of guests who haven't responded.
    Host: alice@example.com   Auto-fixable: YES   → queued for /work-findings

LOW (0)
  (all low-severity checks pass)

Summary: 2 HIGH, 1 MEDIUM, 0 LOW failing
Ready: NO (blocked by 2 high-severity checks)
Auto-fixable: 2 / 3
PRs queued: 2
Slack notifications sent: 1 (host: alice@example.com)
```

### 6. Persist
- The readiness run is recorded against the event (run timestamp, `ready` roll-up, `passed`/`total`).
- The action is written to the append-only `audit_logs` table via `audit_action`.

## Output rules

- **Always sort findings by severity** (high → medium → low), then alphabetically by check `key`.
- **Never produce findings without evidence** — show the concrete value that failed the check (e.g., `attending=142 > capacity=120`).
- **Severity is from the check definition**, not invented per-run. The `severity` on each `ReadinessCheck` is fixed in `get_readiness` (`high`/`medium`/`low`).
- **Don't summarize remediations** — keep them concrete and actionable ("set a location", "raise capacity or waitlist 22 guests").
- **If an event has already started** (`starts_at` in the past), prepend a warning to the report: "⚠ Event has already started — readiness is informational only."

## Failure modes to handle

| Failure | Behavior |
|---------|----------|
| Event not found for this owner | Fail clearly, list similar names |
| Caller is not the event's owner | `get_readiness` raises `OwnershipError` → 404; do not leak the event's existence |
| Readiness computation raises | Capture in the run record; continue with the other events in a fleet sweep |
| Host has no Slack channel | Skip notification, log a warning, continue |
| Fleet sweep finds 100+ events | Process in batches of 10 with progress reports |

## What you must NOT do

- Do not auto-create PRs from this skill. That's `/work-findings`'s job.
- Do not modify the event or its guest list — readiness is a read-only evaluation.
- Do not audit events the caller does not own — `get_readiness` enforces ownership and returns 404 otherwise.
- Do not skip the audit log entry. Every readiness run must be logged.
