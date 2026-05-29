---
name: plan-feature
description: Design a feature implementation with acceptance criteria AC-1 through AC-6 before any code is written. Use when starting work on a new feature, bug, or refactor.
allowed-tools: Read, Grep, Glob
---

# /plan-feature

You produce a concrete, reviewable plan with explicit acceptance criteria. No code is written in this phase. The output of this skill is the contract that subsequent phases will fulfill.

## Required output

```markdown
# F-XX: <Feature Title>

## Problem
<2-3 sentences: what isn't working today, who is affected>

## Proposed Solution
<3-5 sentences: what you will build, why this approach>

## Affected files
<bullet list of files to be created or modified, with brief reason for each>

## Implementation Steps
1. <step description> — files: <list>
2. ...

## Data Model Changes
<New tables, columns, or relationships, with migration strategy. "None" if not applicable.>

## API Surface Changes
<New or modified endpoints, with method/path/request/response shapes. "None" if not applicable.>

## UI Changes
<New screens, modified screens, new components. "None" if not applicable.>

## Acceptance Criteria

### AC-1 — Functional
- [ ] <specific behavior 1>
- [ ] <specific behavior 2>
- [ ] <edge case 1>
- [ ] <edge case 2>

### AC-2 — Tests
- [ ] Unit tests for service layer (≥80% coverage on new code)
- [ ] Router tests for each new endpoint (happy path + 403 + 404 + 422)
- [ ] Security tests covering capability checks
- [ ] Frontend component tests for interactive elements

### AC-3 — Security
- [ ] All 5 guards present on every new endpoint
- [ ] `/audit-security` clean
- [ ] No secrets, tokens, or PII in code or logs
- [ ] Workspace isolation verified (cross-workspace probe in tests)

### AC-4 — Quality
- [ ] `/simplify` clean — no duplication
- [ ] Repository pattern used for data access
- [ ] Service layer holds business logic (routers stay thin)
- [ ] No orphaned helpers; reuse existing utilities

### AC-5 — Lint & Build
- [ ] `make lint` (ruff + mypy) and `make test` (or `make test-cov` for the ≥80% gate) green
- [ ] `pnpm lint`, `pnpm exec tsc --noEmit`, `pnpm test`, and `pnpm build` green
- [ ] No new ignored warnings

### AC-6 — Frontend
- [ ] OpenAPI types regenerated and used
- [ ] TanStack Query hooks for new endpoints
- [ ] i18n keys added to en.json AND fr.json
- [ ] Dark mode verified (manual screenshot)
- [ ] `/frontend-design` used for new components

## Risks
<bullet list of things that might go wrong, with mitigations>

## Out of scope
<bullet list of things this PR will NOT do>

## Estimated commits
<integer — typically 3-10>
```

## Process

1. **Read the request carefully.** If essential information is missing (success metric, scope boundary, rollback plan), ask before planning.
2. **Read the relevant code.** Use Grep/Glob to find what exists. Don't plan in a vacuum.
3. **Check CLAUDE.md** for conventions that apply.
4. **Identify integration points** — what other code will need to change?
5. **Surface risks honestly.** A 3-line "risks: none" is rarely true.
6. **Output the plan** in the exact format above.

## What you must NOT do

- Write code. This is a planning phase.
- Skip any AC section. All 6 are mandatory.
- Hand-wave acceptance criteria. "Tests pass" is not an AC; "POST /scorecards/{id}/versions returns 201 with version body, 403 for viewers, 404 for missing scorecard" is an AC.
- Plan beyond the requested scope. If the user asks for X, plan X — don't slip in Y as a "while we're here."
