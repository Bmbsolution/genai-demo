---
name: implement
description: Full REPL loop orchestrator. Runs plan → explore → implement → test → review → audit → commit → PR for a feature request. Use when the user wants a feature implemented end-to-end.
user-invocable: true
allowed-tools: Read, Write, Edit, Bash, Grep, Glob
context: main
agent: general-purpose
---

# /implement

You are the orchestrator. Given a feature request, you drive the entire REPL loop from plan to PR. You delegate to specialist skills at each phase, never skipping any.

## Process

### Phase 0 — Plan
- Run `/plan-feature` with the user's request
- Capture AC-1 through AC-6
- If the plan affects more than 5 files or 200 lines: pause and confirm with user before proceeding
- If the user provided a feature ID (e.g., F-12), use it; otherwise generate one

### Phase 1 — Per Step
For each step in the plan, run the inner cycle:

1. `/explore-codebase` — read what exists; note conventions, neighbors, integration points
2. **Implement** — use `/new-endpoint` for backend routes, `/new-scorecard` for scorecards, `/frontend-design` for UI. Otherwise edit directly following CLAUDE.md conventions.
3. `make lint && make test` (backend); `pnpm lint && pnpm build && pnpm test` (frontend)
4. If anything fails: enter the inner fix loop (max 3 attempts, then escalate)
5. `/simplify` — quality pass
6. `/audit-security` on the touched files — must come back clean
7. `/commit-sc` — atomic commit per step

### Phase 2 — Acceptance Gate
- Verify all 6 ACs pass — not "I think they pass," verify by running the checks
- If any AC fails: return to the relevant phase

### Phase 3 — PR
- `/review-pr` on the current branch — fix any CRITICAL/HIGH bugs found
- `/create-pr` — generates production-ready PR with What/Why/How
- `/devops watch` — monitor the CI pipeline
- If CI fails: route the failure to the right phase (test → fix; audit → fix; lint → fix)

## Output format

Stream progress. After each step, output one line:
```
[F-12 step 3/7] ✅ Implemented POST /scorecards/{id}/versions  (commit a1b2c3d)
```

After the full cycle, output a summary:
```
F-12 — Add scorecard versioning with comparison view
  ✅ Plan generated (AC-1..AC-6 set)
  ✅ 7 steps implemented
  ✅ All ACs pass
  ✅ Reviewed: 0 critical, 0 high
  ✅ PR opened: <link>
  ✅ CI: green
  
Ready for human review.
```

## What you must NOT do

- Skip a phase. The loop is a contract.
- Commit broken code. The inner fix loop catches this — trust it.
- Merge anything. Human approval is mandatory.
- Run all phases in parallel. Sequential processing prevents subtle errors.
- Hide failures. If something failed and you couldn't recover, say so plainly.
