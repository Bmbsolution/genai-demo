---
name: work-issues
description: Autonomous worker that picks the highest-priority open GitHub issue, implements it through the full REPL loop, opens a PR, and moves to the next. Use for hands-free backlog clearing.
allowed-tools: Read, Write, Edit, Bash, Grep, Glob
---

# /work-issues

> **Local setup:** requires GitHub issues + `gh`, not available in this local-only repo. For hands-free work here, use `/work-findings` (it reads scorecard findings from the local DB).

You autonomously clear the backlog. You pick the top-priority open issue, drive it through `/implement`, create a PR, and move on. You stop when the queue is empty or your time budget runs out. You never merge.

## Invocation

```
/work-issues                                # Pick top issue, work it, loop
/work-issues --priority=P0,P1               # Restrict by priority
/work-issues --label=area:scorecards        # Restrict by label
/work-issues --max=5                        # Cap PRs opened
/work-issues --timeout=8h                   # Soft deadline
/work-issues --dry-run                      # Show plan without acting
```

## The loop

```
1. Query open issues
   - WHERE state='open' AND assignee IS NULL
   - AND NOT label='needs-human'
   - AND NOT label='human-only'
   - ORDER BY priority ASC, created_at ASC
   - LIMIT 1

2. Claim the issue
   - Assign to dev-gatherly
   - Add label 'in-progress'
   - Comment: "Picked up by /work-issues at <timestamp>"

3. Run /implement on the issue
   - This handles plan → explore → implement → test → review → audit → commit → PR
   - The PR description references the issue (Closes #N)

4. On success:
   - Remove 'in-progress' label
   - Add label 'pr-opened'
   - Move issue card to "In Review" column on project board

5. On escalation (3 inner-loop failures):
   - Remove 'in-progress' label
   - Add label 'needs-human'
   - Comment with: what was tried, where it failed, what input is needed
   - Move issue card back to "Ready"
   - Move to next issue

6. Loop to step 1
```

## Stopping conditions

- Queue is empty (no eligible issues)
- `--max` PRs opened
- `--timeout` reached (finish current issue, don't start next)
- Three consecutive escalations (something is systematically wrong; stop and ask)

## Reporting

After each issue, append to a session log. At end of session:

```
/work-issues session — 2026-05-12 22:00 to 2026-05-13 06:30

Worked: 6 issues
✅ #128  P1  fix: scorecard runner times out on large repos      PR #87
✅ #131  P2  feat: add p99 latency to metrics dashboard          PR #88
✅ #134  P2  fix: dependency graph misses cycles                 PR #89
✅ #137  P2  feat: add Slack notification on policy promotion    PR #90
✅ #140  P3  refactor: extract pagination helper                 PR #91
⚠️ #143  P2  refactor: rewrite config loader as plugin system    needs-human (3 attempts)

5 PRs opened, 1 escalated.
Average time per issue: 1h 16m.
```

## Skip rules

Do not pick up an issue if:

- It has label `needs-human` or `human-only`
- It has label `discussion` or `rfc` (these need group decision)
- It is already assigned to someone
- It is in a milestone marked "blocked"
- Its description has fewer than 30 words (insufficient context — flag with `needs-clarification`)
- It depends on another open issue (check `Depends on:` references in body)

## Concurrency

One issue at a time. Multiple instances? Database/issue locks via assignee + label prevent collisions. The second worker just moves to the next issue.

## What you must NOT do

- Pick up issues outside the configured priority/label scope
- Modify another worker's in-progress work
- Auto-merge anything (humans approve)
- Mark an issue closed yourself (the PR closes it on merge, by humans)
- Override priority order to "make progress" — if the queue is all P0 and you can't do P0, escalate
- Open more than one PR per issue
- Ignore CI failures on the PRs you opened — `/devops watch` each one
- Hide failures. Honest "1 escalated of 6" is better than fake "6 of 6 done"
