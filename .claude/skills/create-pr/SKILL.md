---
name: create-pr
description: Push the current branch and create a production-ready PR with a complete description (What, Why, How to test). Runs /review-pr first if not already done. Use when implementation is complete.
allowed-tools: Bash, Read
---

# /create-pr

> **Local setup:** requires a GitHub remote + `gh` CLI, which aren't configured here (local-only git). With no remote, run `/review-pr`, leave the work on its feature branch, and hand it to a human for review/merge — never merge yourself.

You ship the current branch as a PR ready for human review. Production-ready means: tests pass, lint passes, audit-security clean, review-pr clean of CRITICAL/HIGH bugs.

## Process

1. **Verify branch state**
   - Not on `main` or `master`
   - All changes committed (no uncommitted/unstaged work)
   - Branch is up to date with `main` (rebase if needed; conflicts → ask user)
2. **Run quality gates**
   - `make lint && make test` (backend if touched)
   - `pnpm lint && pnpm build` (frontend if touched)
   - `/audit-security` on the changes
3. **Run `/review-pr`** if not already run for this branch
   - Fix any CRITICAL/HIGH findings before continuing
   - MEDIUM findings: ask user whether to fix now or in follow-up tickets
4. **Push the branch** — `git push -u origin <branch>`
5. **Create the PR** with `gh pr create` and the structured description below
6. **Output the PR URL** and a one-line summary

## PR description template

```markdown
## What

<2-3 sentences describing what this PR delivers, in user-facing terms.>

Closes #<issue-number> <if applicable>
Refs F-<feature-id>

## Why

<2-3 sentences explaining the problem this solves and why now.>

## How to test

<Step-by-step instructions a reviewer can follow on their machine.>

```bash
# Backend
cd gatherly-be
make dev

# Frontend (in another terminal)
cd gatherly-fe
pnpm dev
```

Then:
1. Log in as `admin@acme.dev` (password: `dev`)
2. Navigate to /events
3. Click on an event to open its detail page
4. Click "Edit event"
5. Modify the event title and save
6. Verify the updated title shows on the event detail page

## Acceptance Criteria

- [x] AC-1 Functional: All 3 user behaviors verified
- [x] AC-2 Tests: 12 new tests, all pass; coverage 87% on new code
- [x] AC-3 Security: /audit-security clean
- [x] AC-4 Quality: /simplify clean
- [x] AC-5 Lint & Build: green
- [x] AC-6 Frontend: types regenerated, i18n added, dark mode verified

## Screenshots

<screenshots of new UI in light AND dark mode if frontend changed>

## Schema changes

<List any DB schema changes (Gatherly uses SQLite, no Alembic migrations) and whether they're backward-compatible with existing data.>

- Added `events.location` column — nullable, backward-compatible with existing rows.

## Follow-up

<Optional: tickets created for non-blocking improvements>
- Created issue #142 for extracting pagination helper
```

## Refusing to create a PR

You refuse if:

- Tests are failing
- Audit-security has CRITICAL or HIGH violations
- The branch is `main`
- Uncommitted changes exist
- The diff is suspiciously empty or huge without explanation

## Output format

```
✅ PR created: https://github.com/<org>/gatherly/pull/87

Title: feat(be): add event editing from the detail page
Branch: feat/F-12-event-editing → main
Files: 11 changed, +487 / -23
Tests: 12 new, all green
Reviewers: @platform-team

Pipeline started. Use /devops watch to monitor.
```

## What you must NOT do

- Push with `--force` or `--force-with-lease` without explicit user approval
- Create a draft PR unless requested (we want full review)
- Auto-assign reviewers without checking the team conventions
- Skip the description fields. "Self-explanatory" is never an acceptable PR description.
- Merge the PR. Human approval is mandatory.
