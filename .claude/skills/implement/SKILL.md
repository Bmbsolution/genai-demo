---
name: implement
description: Full REPL loop orchestrator. Runs plan → explore → implement → convene the specialist team (review/audit/test) → acceptance gate → PR for a feature request. Use when the user wants a feature implemented end-to-end.
allowed-tools: Read, Write, Edit, Bash, Grep, Glob, Task
---

# /implement

You are the orchestrator. Given a feature request, you drive the entire REPL loop from
plan to PR. You delegate to specialist skills and, for review/audit/test, to a **team of
specialist subagents** — each in its own context window. You never skip a phase.

## Process

### Phase 0 — Plan
- Run `/plan-feature` with the user's request
- Capture AC-1 through AC-6
- If the plan affects more than 5 files or 200 lines: pause and confirm with user before proceeding
- If the user provided a feature ID (e.g., F-12), use it; otherwise generate one

### Phase 1 — Implement (per step)
For each step in the plan, run the inner cycle:

1. `/explore-codebase` — read what exists; note conventions, neighbors, integration points
2. **Implement** — use `/new-endpoint` for backend routes, `/new-scorecard` for readiness checks, `/frontend-design` for UI. Otherwise edit directly following CLAUDE.md conventions.
3. `ruff check && mypy --strict src && pytest` (backend); `pnpm lint && pnpm build && pnpm test` (frontend)
4. If anything fails: enter the inner fix loop (max 3 attempts, then escalate)
5. `/simplify` — quality pass
6. `/commit-sc` — atomic commit per step

### Phase 1.5 — Convene the specialist team (parallel)
Once the feature's steps are implemented, **spin up the specialists in parallel** — in a
single message, launch every relevant subagent via the `Task` tool so they run at once,
each in its own isolated context:

- **always:** `code-reviewer` (adversarial bug hunt) + `security-auditor` (S1–S8 guards) + `test-writer` (AC-2 tests)
- **if `gatherly-fe/**` changed:** also `frontend-reviewer`
- **if a model or schema changed:** also `migration-reviewer`

Collect every report. These are your senior reviewers: a CRITICAL/HIGH finding from any of
them, or a failing test the `test-writer` surfaced, is a **stop** — feed it into the inner
fix loop (max 3 attempts), then **re-convene** the affected specialists until they come back
clean. Read-only specialists never touch code; you apply the fixes.

### Phase 2 — Acceptance Gate
- Verify all 6 ACs pass — not "I think they pass," verify by running the checks
- Security-auditor verdict must be `CLEAN`; code-reviewer `LGTM`; tests green at ≥80% on new code
- If any AC fails or any specialist still flags a blocker: return to the relevant phase

### Phase 3 — PR
- `/create-pr` — generates a production-ready PR with What/Why/How
- `/devops watch` — monitor the CI pipeline; route a red pipeline to the right phase

> **Local-only setup:** if `/create-pr` / `/devops` can't run (no remote/CI), stop after the
> acceptance gate, leave the work on its feature branch, and hand it to a human. Never merge.

## Output format

Stream progress. After each step and each specialist, output one line:
```
[F-12 step 3/7] ✅ Implemented POST /events/{id}/waitlist/promote  (commit a1b2c3d)
[F-12 team]     🔬 code-reviewer · 🔒 security-auditor · 🧪 test-writer  → running in parallel
[F-12 team]     ✅ code-reviewer LGTM · ✅ security-auditor CLEAN · ✅ tests 92% on new code
```

After the full cycle:
```
F-12 — Auto-promote the next waitlisted guest on cancellation
  ✅ Plan generated (AC-1..AC-6 set)
  ✅ N steps implemented
  ✅ Specialist team convened (review · security · tests) — all green
  ✅ All ACs pass
  ✅ PR opened: <link>
Ready for human review.
```

## What you must NOT do

- Skip a phase. The loop is a contract.
- Commit broken code. The inner fix loop catches this — trust it.
- Merge anything. Human approval is mandatory.
- Run the loop *phases* in parallel — they're sequential. (Phase 1.5 is the exception: the
  review/audit/test specialists are independent critics, so they fan out at once.)
- Hide failures. If something failed and you couldn't recover, say so plainly.
