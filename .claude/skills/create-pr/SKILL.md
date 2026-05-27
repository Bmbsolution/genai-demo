---
name: create-pr
description: Push the current branch and create a production-ready PR with a complete description (What, Why, How to test). Runs /review-pr first if not already done. Use when implementation is complete.
user-invocable: true
allowed-tools: Bash, Read
context: main
agent: general-purpose
---

# /create-pr

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
cd servicecat-be
make migrate
make dev

# Frontend (in another terminal)
cd servicecat-fe
pnpm dev
```

Then:
1. Log in as `admin@acme.dev` (password: `dev`)
2. Navigate to /scorecards
3. Click on the "Production Readiness" scorecard
4. Click "Create new version"
5. Modify a criterion's threshold and save
6. Click "Compare versions" — verify the diff view shows the change

## Acceptance Criteria

- [x] AC-1 Functional: All 3 user behaviors verified
- [x] AC-2 Tests: 12 new tests, all pass; coverage 87% on new code
- [x] AC-3 Security: /audit-security clean
- [x] AC-4 Quality: /simplify clean
- [x] AC-5 Lint & Build: green
- [x] AC-6 Frontend: types regenerated, i18n added, dark mode verified

## Screenshots

<screenshots of new UI in light AND dark mode if frontend changed>

## Migrations

<List any new migrations and whether they're safe to run on prod (idempotent? long-running? downtime?)>

- `20260512_1430_add_scorecard_versions.py` — adds two tables, idempotent, no data migration. Safe to run live.

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
✅ PR created: https://github.com/<org>/servicecat/pull/87

Title: feat(be): add scorecard versioning with side-by-side comparison
Branch: feat/F-12-scorecard-versioning → main
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
