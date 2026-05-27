# ServiceCat Team Workflow with Claude Code

> **Portable workflow** — clone the repo, run `claude`, everything loads automatically.

## Quick Start

```bash
git clone <repo-url> && cd servicecat
claude                    # Everything auto-configures
```

What loads automatically:
- `CLAUDE.md` — Project rules, security model, code conventions
- `.claude/settings.json` — Team permissions, hooks (git identity auto-set)
- `.claude/skills/` — 18 team slash commands
- `.mcp.json` — Team MCP servers (Slack, GitHub, Google Drive)
- `.claudeignore` — Protects secrets and ephemeral repo clones from Claude context

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
              │  │    make lint           │  ││
              │  │    make test           │  ││
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
/implement F-12: add scorecard versioning with comparison view
```
Claude plans, explores, implements, tests, reviews, audits, commits, and creates the PR.

**Option B: Step by step** — Drive each phase manually:
```
/plan-feature F-12: add scorecard versioning
  → Review and approve the plan
/explore-codebase how does the current scoring pipeline work?
  → Write code
/simplify
/audit-security servicecat-be/src/routers/scorecards.py
/commit-sc feat(be): add scorecard version comparison
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
| `/new-endpoint` | Implement | Scaffold FastAPI endpoint with all 5 security guards |
| `/new-scorecard` | Implement | Scaffold a new scorecard plugin (model + criteria + scorer + UI form) |
| `/frontend-design` | Implement | Build production-grade UI with shadcn/ui |
| `/simplify` | Review | Check code quality, reuse, efficiency |
| `/audit-security` | Audit | Scan for S1-S8 violations |
| `/audit-service` | Domain | Run all scorecards against a registered service |
| `/commit-sc` | Commit | Commit with dev-servicecat identity + Conventional Commits |
| `/review-pr` | PR Review | Claude bug hunt — find issues + produce fix plan |
| `/create-pr` | Ship | Create production-ready PR with clear description |
| `/devops` | Pipeline | Monitor CI/CD, diagnose failures, route fixes |
| `/triage` | Issue creation | Classify bug/task, assign priority, create GitHub issue |
| `/work-issues` | Autonomous worker | Pick highest priority issue, implement, PR, pick next |
| `/work-findings` | Autonomous worker | Pick up scorecard findings, propose fixes via PR |
| `/write-docs` | Documentation | Write docs and publish to Google Drive as Google Docs |
| `/notify` | Communication | Send Slack messages, alert the team |

### Examples

```bash
# Full feature (Claude handles the entire loop)
/implement add IP allowlist policy type with CIDR validation

# Plan only
/plan-feature F-15: scorecard versioning with score comparison

# Explore first
/explore-codebase how do the scorecard runners chain criteria?

# Scaffold a new endpoint
/new-endpoint POST /scorecards/{id}/runs

# Scaffold a new scorecard
/new-scorecard observability

# Build UI
/frontend-design build the score comparison view with delta indicators

# Quality + security
/simplify
/audit-security servicecat-be/src/routers/

# Commit
/commit-sc feat(be): add scorecard versioning

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
| **AC-3** | Security | `/audit-security` clean — all 5 guards present |
| **AC-4** | Quality | `/simplify` clean — no duplication, proper patterns |
| **AC-5** | Lint & Build | `make lint` + `pnpm lint && pnpm build` pass |
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

### Add a new scorecard type

```bash
/plan-feature F-XX: add observability scorecard with 6 criteria
/new-scorecard observability
# Implement criteria one at a time
/simplify
/audit-security
/commit-sc feat(scorecards): add observability scorecard
/create-pr
```

### Run scorecards across the fleet

```bash
/audit-service all                       # Run all scorecards on every service
/audit-service payment-svc               # Run all scorecards on one service
/audit-service payment-svc --scorecard=security  # One scorecard, one service
```

### Triage findings

```bash
/triage finding-1234                     # Classify severity, assign team
/work-findings --priority=P0,P1          # Autonomous worker on top priority
```

### Fix a bug

```bash
/triage bug: scorecard runner times out on repos >1GB
# Returns issue #87 with priority P1
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
| Nightly fleet sweep | P2-P3 debt |

---

## Priority Order

| Priority | Criteria | Example |
|----------|----------|---------|
| **P0** | Production down, security breach, data leak | Cross-workspace data leakage in scoring API |
| **P1** | Security violation, failing tests on main | S3 RBAC bypass, broken migration |
| **P2** | Bug in feature, missing validation | Score chart wrong on negative deltas |
| **P3** | Tech debt, refactor, minor UI | Code duplication, cleanup |

---

## Configuration: Shared vs Personal

| File | In Git | Purpose |
|------|:------:|---------|
| `CLAUDE.md` | Yes | Project rules — security, patterns, conventions |
| `.claude/settings.json` | Yes | Team permissions, hooks, deny-list |
| `.claude/skills/` | Yes | Team slash commands (18 skills) |
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
      "Bash(TEST_DATABASE_URL=\"...\" python:*)",
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
| Git identity | Session start | Sets `user.name=dev-servicecat` and `user.email` automatically |

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
Examples: `feat/F-12-scorecard-versioning`, `fix/F-08-rbac-promotion`, `security/audit-log-immutability`

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
| Git identity wrong | Hook auto-sets; manually: `git config user.name 'dev-servicecat'` |
| Claude reading sensitive files | Add patterns to `.claudeignore` |
| Claude repeating mistakes | Correct it — feedback saves to auto-memory |
| Too many permission prompts | Add safe commands to `allow` in `settings.json` |
| Scorecard run hangs | Check Redis queue: `redis-cli LLEN scorecard:queue` |
