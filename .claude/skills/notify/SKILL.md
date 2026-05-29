---
name: notify
description: Send Slack messages, alerts, and notifications. Use for routing finding alerts to owner teams, broadcasting CI failures, or announcing PR-ready status.
allowed-tools: Bash, Read
---

# /notify

> **Local setup:** requires the Slack MCP (`SLACK_BOT_TOKEN`, `SLACK_TEAM_ID`), not configured in this repo. Without it, surface the message text in the conversation instead of posting.

You send Slack messages on behalf of ServiceCat. Messages are concise, actionable, and routed to the right channel.

## Invocation

```
/notify <channel> <message>
/notify finding SC-F-1234              # Send a finding alert to the owner team
/notify pr <pr-number>                  # Announce a PR-ready status
/notify ci-fail <run-id>                # Broadcast a CI failure
/notify deploy <env>                    # Announce a deployment
```

## Templates

### Finding alert (auto-routing)
```
🟠 New HIGH severity finding on `payment-svc`

Scorecard: Security
Criterion: no_security_headers
Evidence: nginx/default.conf — missing X-Frame-Options, CSP

Auto-fixable: ✅ — queued for /work-findings
Track: <link to finding>
```

### CI failure
```
🚨 CI failed on `feat/F-12-scorecard-versioning`

Job: test (run #4523)
Failed: tests/services/test_scorecard_service.py::test_create_version_concurrent
Cause: race condition in version creation

Diagnostics: <link to /devops report>
Triggered by: @<user>
```

### PR ready for review
```
👀 PR ready for review

#87 — feat(be): add scorecard versioning with comparison
Branch: feat/F-12-scorecard-versioning
Tests: ✅ 147 pass | Audit: ✅ clean | Review: ✅ no critical bugs

→ <PR link>
```

### Deployment
```
🚀 Deployed to `staging`

Commit: a1b2c3d feat(be): add scorecard versioning
By: @dev-servicecat (auto)
Pipeline: <link>
Rollback: gh workflow run rollback.yml -F env=staging
```

### Escalation (P0/P1)
```
🔴 P0 — production incident

Issue: cross-workspace data leakage in scoring API
Detected by: /audit-security (finding SC-A-2026-05-12-44)
Triage: <issue link>
Page on-call: <pagerduty link>
```

## Channel routing

| Source | Default channel |
|--------|-----------------|
| Finding for service `<svc>` | `#<owner-team-slack>` (from team config) |
| CI failure on main | `#servicecat-alerts` |
| PR ready | `#servicecat-prs` |
| Deployment | `#servicecat-deploys` |
| P0/P1 incident | `#servicecat-alerts` AND `#incidents` |
| General announcement | `#servicecat-team` |

If the owner team has no Slack channel configured: fall back to `#servicecat-orphans` and add a note that the finding needs ownership routing setup.

## Message rules

- **One actionable thing per message.** No mega-digests.
- **Always include a link** to the source (PR, finding, run, issue).
- **Use thread replies for follow-ups**, not new top-level messages.
- **No @here or @channel** without explicit user approval — these are for genuine emergencies.
- **No emoji floods.** One status emoji at the start is enough.
- **Quiet hours** — if the channel has off-hours configured, queue non-urgent messages for the next business hour. P0/P1 always send immediately.

## What you must NOT do

- Spam channels with status updates that nobody reads
- Use `@here` or `@channel` for routine notifications
- Forward unrelated content to channels
- Send PII or secrets in messages (even in private channels)
- Cross-post the same message to multiple channels (link from one to the other instead)
- Send messages on behalf of users who didn't authorize it
