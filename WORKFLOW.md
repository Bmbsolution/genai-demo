# Gatherly Team Workflow with Claude Code

> **Portable workflow** — clone the repo, run `claude`, everything loads automatically.

## Quick Start

```bash
git clone <repo-url> && cd gatherly
claude                    # Everything auto-configures
```

What loads automatically:
- `CLAUDE.md` — Project rules, security model, code conventions
- `.claude/settings.json` — Team permissions, hooks (git identity auto-set)
- `.claude/skills/` — team slash commands
- `.mcp.json` — Team MCP servers (Slack, GitHub, Google Drive)
- `.claudeignore` — Protects secrets from Claude context

---

## The REPL Loop (Core Workflow)

Every feature follows the same loop. Each step produces a working, testable, committed unit.

```
                    ┌──────────────────┐
                    │   /plan-feature   │  Define AC-1..AC-6
                    │   (Phase 0)      │  before writing ANY code
                    └────────┬─────────┘
                             │
              ┌──────────────▼──────────────┐
              │    FOR EACH STEP IN PLAN:    │
              │                              │
              │  ┌────────────────────────┐  │
              │  │ 1. EXPLORE             │  │
              │  │    /explore-codebase   │  │
              │  └──────────┬─────────────┘  │
              │             ↓                │
              │  ┌────────────────────────┐  │
              │  │ 2. IMPLEMENT           │  │
              │  │    /new-endpoint       │  │
              │  │    /new-scorecard      │  │
              │  │    /frontend-design    │  │
              │  └──────────┬─────────────┘  │
              │             ↓                │
              │  ┌────────────────────────┐  │
              │  │ 3. TEST               ◄──┐│
              │  │    ruff + mypy         │  ││
              │  │    pytest              │  ││
              │  │    pnpm lint/build     │  ││
              │  └──────────┬─────────────┘  ││
              │             │ fail? ─────────┘│
              │             ↓ pass             │
              │  ┌────────────────────────┐   │
              │  │ 4. REVIEW              │   │
              │  │    /simplify           │   │
              │  └──────────┬─────────────┘   │
              │             ↓                 │
              │  ┌────────────────────────┐   │
              │  │ 5. AUDIT               │   │
              │  │    /audit-security     │   │
              │  └──────────┬─────────────┘   │
              │             ↓                 │
              │  ┌────────────────────────┐   │
              │  │ 6. COMMIT              │   │
              │  │    /commit-sc          │   │
              │  └──────────┬─────────────┘   │
              │             ↓                 │
              │     Next step in plan...      │
              └──────────────┬────────────────┘
                             ↓
                    ┌────────────────────┐
                    │  ACCEPTANCE GATE   │
                    │  AC-1 through AC-6 │
                    │  All must pass     │
                    └────────┬───────────┘
                             ↓
                    ┌────────────────────┐
                    │  CLAUDE PR REVIEW  │  /review-pr
                    │  Bug hunt + fix    │  Fix critical/high
                    │  before humans see │  bugs, loop until
                    │  the code          │  review is clean
                    └────────┬───────────┘
                             ↓
                    ┌────────────────────┐
                    │  CREATE PR         │  /create-pr
                    │  Clear description │  What, why, how to test
                    └────────┬───────────┘
                             ↓
                    ┌────────────────────┐
                    │  PIPELINE MONITOR  │  /devops watch
                    │  Watch CI/CD run   │  Catch errors, fix,
                    │  Fix → re-push     │  re-push until GREEN
                    └────────┬───────────┘
                             ↓
                    ┌────────────────────┐
                    │  HUMAN REVIEW      │  Team member must
                    │  (MANDATORY)       │  approve before merge
                    │  Never auto-merge  │
                    └────────────────────┘
```

### Using the Loop

**Option A: Full automation** — Let Claude orchestrate everything:
```
/implement add a capacity waitlist that auto-promotes the next guest when a confirmed guest cancels
```
Claude plans, explores, implements, tests, reviews, audits, commits, and creates the PR.

**Option B: Step by step** — Drive each phase manually:
```
/plan-feature add a capacity waitlist with auto-promotion
  → Review and approve the plan
/explore-codebase how does the RSVP status flow work today?
  → Write code
/simplify
/audit-security gatherly-be/src/gatherly/routers/guests.py
/commit-sc feat(be): auto-promote next waitlisted guest on cancel
```

**Option C: Just start coding** — For small changes (1-2 files):
```
Write code, then:
/simplify → /audit-security → /commit-sc
```

---

## Team Skills (Slash Commands)

| Command | Phase | Purpose |
|---------|-------|---------|
| `/implement` | **Full loop** | Orchestrate plan → implement → test → review → audit → commit → PR |
| `/plan-feature` | Plan | Design implementation with AC-1 through AC-6 |
| `/explore-codebase` | Explore | Deep-dive into code before modifying |
| `/new-endpoint` | Implement | Scaffold a FastAPI endpoint with all the security guards |
| `/new-scorecard` | Implement | Scaffold a new readiness check / scorecard (checks + scorer + UI) |
| `/frontend-design` | Implement | Build production-grade UI with shadcn/ui |
| `/run-app` | Verify | Launch and drive the app locally (backend + frontend) |
| `/simplify` | Review | Check code quality, reuse, efficiency |
| `/audit-security` | Audit | Scan for S1-S8 violations |
| `/audit-service` | Domain | Run the readiness audit against an event |
| `/commit-sc` | Commit | Commit with dev-gatherly identity + Conventional Commits |
| `/review-pr` | PR Review | Claude bug hunt — find issues + produce fix plan |
| `/create-pr` | Ship | Create production-ready PR with clear description |
| `/devops` | Pipeline | Monitor CI/CD, diagnose failures, route fixes |
| `/triage` | Issue creation | Classify bug/task, assign priority, create GitHub issue |
| `/work-issues` | Autonomous worker | Pick highest priority issue, implement, PR, pick next |
| `/work-findings` | Autonomous worker | Pick up readiness findings, propose fixes via PR |
| `/write-docs` | Documentation | Write docs and publish to Google Drive as Google Docs |
| `/notify` | Communication | Send Slack messages, alert the team |

### Examples

```bash
# Full feature (Claude handles the entire loop)
/implement add a +1 and dietary-preferences field to the RSVP form

# Plan only
/plan-feature add a capacity waitlist with auto-promotion

# Explore first
/explore-codebase how does the readiness checklist compute its checks?

# Scaffold a new endpoint
/new-endpoint POST /events/{id}/guests

# Scaffold a new readiness check
/new-scorecard reminders-sent

# Build UI
/frontend-design build the guest check-in view with arrival counts

# Quality + security
/simplify
/audit-security gatherly-be/src/gatherly/routers/

# Commit
/commit-sc feat(be): add capacity waitlist

# Review PR before human sees it
/review-pr 42

# Ship
/create-pr

# Watch CI
/devops watch
```

---

## Acceptance Criteria

Every `/plan-feature` and `/implement` generates AC-1 through AC-6. The feature is NOT done until all six pass.

| AC | Category | Pass Condition |
|----|----------|----------------|
| **AC-1** | Functional | All behaviors work — happy path + edge cases |
| **AC-2** | Tests | Unit + router + security tests pass; ≥80% coverage on new code |
| **AC-3** | Security | `/audit-security` clean — guards present |
| **AC-4** | Quality | `/simplify` clean — no duplication, proper patterns |
| **AC-5** | Lint & Build | `ruff` + `mypy --strict` + `pnpm lint && pnpm build` pass |
| **AC-6** | Frontend | Types, hooks, i18n, dark mode, `/frontend-design` used |

### The Inner Fix Loop

When TEST or AUDIT fails, Claude doesn't proceed. It loops:

```
Test fails → Read error → Fix root cause → Re-run → Pass? → Continue
                                                  → Fail? → Retry (max 3)
                                                  → Still failing → Ask human
```

After 3 failed attempts, Claude STOPS and asks. No guessing. No commits with broken code.

---

## Common Workflows

### Add a new readiness check

```bash
/plan-feature add a "reminders sent" readiness check
/new-scorecard reminders-sent
# Implement the check, wire it into InsightsService.get_readiness
/simplify
/audit-security
/commit-sc feat(be): add reminders-sent readiness check
/create-pr
```

### Audit events for readiness

```bash
/audit-service all                       # Run the readiness audit on every event
/audit-service "Summer Rooftop Party"    # Audit one event
```

### Triage findings

```bash
/triage finding-1234                     # Classify severity, assign owner
/work-findings --priority=P0,P1          # Autonomous worker on top priority
```

### Fix a bug

```bash
/triage bug: guest list leaks across hosts when owner scope is dropped
# Returns issue #87 with priority P0
/implement #87
```

---

## Auto-triage from other agents

Other skills automatically feed `/triage` when they find problems:

| Source | Creates Issue As |
|--------|-----------------|
| `/devops` pipeline failure | P1 bug or infra |
| `/audit-security` violation | P0-P1 security |
| `/audit-service` finding | P1-P3 (severity-mapped) |
| `/review-pr` finding | P2 bug |
| Nightly readiness sweep | P2-P3 debt |

---

## Priority Order

| Priority | Criteria | Example |
|----------|----------|---------|
| **P0** | Production down, security breach, data leak | Cross-owner guest-list leakage (S2) |
| **P1** | Security violation, failing tests on main | S3 RBAC bypass (host deleting events) |
| **P2** | Bug in feature, missing validation | RSVP count wrong when a guest cancels |
| **P3** | Tech debt, refactor, minor UI | Code duplication, cleanup |

---

## Configuration: Shared vs Personal

| File | In Git | Purpose |
|------|:------:|---------|
| `CLAUDE.md` | Yes | Project rules — security, patterns, conventions |
| `.claude/settings.json` | Yes | Team permissions, hooks, deny-list |
| `.claude/skills/` | Yes | Team slash commands |
| `.mcp.json` | Yes | Team MCP servers |
| `.claudeignore` | Yes | Protect secrets and ephemeral data |
| `WORKFLOW.md` | Yes | This guide |
| `.claude/settings.local.json` | **No** | Your machine-specific paths, personal keys |

### Personal Settings (`.claude/settings.local.json`)

For machine-specific configs that shouldn't be shared:

```json
{
  "permissions": {
    "allow": [
      "Bash(GATHERLY_DATABASE_URL=\"...\" python:*)",
      "Bash(PYTHONPATH=src python:*)",
      "WebFetch(domain:your-internal-tool.com)"
    ]
  }
}
```

---

## Hooks (Auto-Configured)

| Hook | Event | What It Does |
|------|-------|--------------|
| Git identity | Session start | Sets `user.name=dev-gatherly` and `user.email` automatically |

The team `settings.json` includes hooks that run without manual setup.

---

## Agent Strategies

| Agent Type | Speed | Access | When to Use |
|------------|-------|--------|-------------|
| **Explore** | Fast | Read-only | Find files, understand code, trace data flow |
| **Plan** | Medium | Read-only | Design implementation plans, architecture decisions |
| **Forked** | Varies | Isolated context | Skills with `context: fork` — don't pollute main conversation |

Skills using forked context: `/audit-security`, `/audit-service`, `/explore-codebase`, `/plan-feature`.

---

## PR Lifecycle

```
Code complete → /review-pr → Fix bugs → /create-pr → Human review → Merge
```

### PR Rules (Non-Negotiable)

1. **Production-ready** — Every PR can be deployed. No broken builds, no failing tests.
2. **Testable** — PR description includes specific test steps a reviewer can follow.
3. **Usable** — The feature works end-to-end. A real user can use it.
4. **Claude-reviewed** — `/review-pr` run before creating. All CRITICAL/HIGH bugs fixed.
5. **Human-approved** — A team member MUST approve before merge. Claude never merges.

### Branch Naming

```
<type>/<feature-id>-<short-description>
```
Examples: `feat/waitlist-auto-promote`, `fix/guest-list-owner-scope`, `security/audit-log-immutability`

### PR Description Format

Every PR answers:
- **What** was implemented? (concrete deliverables)
- **Why** was it implemented? (problem it solves, feature ID)
- **How** to test it? (specific steps)

---

## MCP Servers (Team-Shared)

Configured in `.mcp.json` (credentials via env vars, never hardcoded):

| Server | Package | Purpose |
|--------|---------|---------|
| **Slack** | `@modelcontextprotocol/server-slack` | Post messages, read channels, react |
| **GitHub** | `@modelcontextprotocol/server-github` | Issues, PRs, repo content |
| **Google Drive** | `@piotr-agier/google-drive-mcp` | Read/write Google Docs |

**Required env vars:**
```bash
export SLACK_BOT_TOKEN="xoxb-..."
export SLACK_TEAM_ID="T..."
export GITHUB_TOKEN="ghp_..."
export GOOGLE_CLIENT_ID="...apps.googleusercontent.com"
export GOOGLE_CLIENT_SECRET="GOCSPX-..."
```

---

## Troubleshooting

| Problem | Solution |
|---------|----------|
| Skills not showing | Restart `claude` — skills load from `.claude/skills/` |
| Permission denied | Add to `.claude/settings.local.json` (personal) or `.claude/settings.json` (team) |
| Git identity wrong | Hook auto-sets; manually: `git config user.name 'dev-gatherly'` |
| Claude reading sensitive files | Add patterns to `.claudeignore` |
| Claude repeating mistakes | Correct it — feedback saves to auto-memory |
| Too many permission prompts | Add safe commands to `allow` in `settings.json` |
| Backend won't start | Recreate the venv and reseed; the Makefile is Windows-only — call `.venv/bin/python` directly (or `/run-app`) |
