---
name: commit-sc
description: Commit changes with the dev-gatherly git identity using Conventional Commits format. Use after every atomic step in the REPL loop.
allowed-tools: Bash, Read
---

# /commit-sc

You commit the current staged (or unstaged) changes with the project's git identity and a properly formatted Conventional Commits message.

## Process

1. **Verify identity is set** — `git config user.name` should be `dev-gatherly`. The session-start hook sets this; if missing, set it now.
2. **Check the diff** — `git diff --staged` (or `git diff` if nothing staged). Refuse to commit empty or accidentally massive diffs (>500 lines without explicit confirmation).
3. **Determine the commit type** based on the diff:
   - `feat` — new user-facing capability
   - `fix` — bug fix
   - `refactor` — code restructure with no behavior change
   - `test` — tests only
   - `docs` — documentation only
   - `chore` — tooling, dependencies, configs
   - `perf` — performance improvement
   - `ci` — CI/CD changes
   - `security` — security-related fix or hardening
4. **Determine the scope** — typically one of: `be`, `fe`, `db`, `infra`, `events`, `guests`, `rsvp`, `billing`, `auth`, `audit`, `docs`.
5. **Write the message:**

```
<type>(<scope>): <imperative subject, ≤72 chars>

<optional body — explain WHY, not what. Wrap at 80 chars.>

Refs: F-12

Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>
```

The `Co-Authored-By` trailer is required on every commit. The `Refs:`/issue
trailer is optional in this local-only setup (no GitHub remote/issues).

6. **Commit and verify** — commit, then show the resulting hash. The session-start
   hook sets the identity; if it didn't run, pass it explicitly:
   `git -c user.name='dev-gatherly' -c user.email='dev@gatherly.local' commit -F <msgfile>`.
   Use a `-F` message file (or a here-doc) for multi-line bodies.

## Examples

```
feat(events): add event capacity limits with waitlist

Hosts can cap an event's headcount. Once full, new RSVPs land on a
waitlist and are promoted automatically when a guest cancels. The
guest-list endpoint paginates.

Refs: F-12

Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>
```

```
fix(rsvp): handle duplicate RSVP submissions for the same guest

A guest hitting the public RSVP link twice previously created two rows.
The handler now upserts on (event_id, email) and returns the existing
RSVP unchanged.

Refs: F-08, fixes #143
```

```
security(be): require admin capability for event deletion

Deletion was previously gated only by capability event:write, which
Hosts have. This adds the explicit event:delete capability check (Admin
only) and updates the default role bindings.

Refs: F-15, audit finding GA-A-2026-05-12-44
```

## Refusing to commit

You refuse if:

- `--no-verify` is in the message or any flag
- The branch is `main` or `master` and the user isn't explicitly overriding
- Tests are failing locally (run the backend test suite to check — `.venv/bin/python -m pytest` on macOS/Linux, since the Makefile is Windows-only; if it fails, refuse)
- Audit-security has not been run on the changes

## What you must NOT do

- Use `--no-verify`. Pre-commit hooks exist for a reason.
- Force-push.
- Commit code containing `console.log`, `print()` debug statements, or `TODO: remove before commit`.
- Commit changes unrelated to the stated work. If the diff includes an unrelated drive-by edit, ask the user to split.
- Sign the commit as anyone other than `dev-gatherly`.
