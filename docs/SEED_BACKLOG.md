# ServiceCat — Seed Backlog

> Use these as your initial GitHub issues for Phase 1 development. Each issue is sized to be implementable end-to-end via `/implement` in 1-3 hours.

## How to use this file

1. Create a GitHub repo for ServiceCat
2. For each issue below, run: `gh issue create --title "..." --body "..." --label "..."`
3. Add the labels referenced (one-time setup): `priority:P0`, `priority:P1`, `priority:P2`, `priority:P3`, `area:auth`, `area:scorecards`, `area:findings`, `area:frontend`, `area:db`, `area:infra`, `type:feat`, `type:fix`, `type:security`, `type:docs`, `type:tech-debt`, `auto-fixable`, `needs-human`

The full backlog: 14 issues spanning Phase 1 foundation work. Phase 2-4 issues should be added as you complete each phase.

---

## #1 — Set up Postgres with workspace RLS

**Labels:** `priority:P1`, `area:db`, `area:infra`, `type:feat`

### Summary
Set up Postgres 16 in docker-compose with Row-Level Security configured for workspace isolation across all multi-tenant tables.

### Context
ServiceCat is multi-tenant. Every multi-tenant table needs `workspace_id UUID NOT NULL` with an RLS policy that filters by the per-request `app.workspace_id` setting. This is foundational — no feature can ship without it.

### Acceptance Criteria
- [ ] AC-1: docker-compose up brings Postgres 16 healthy
- [ ] AC-1: Initial migration creates `workspaces`, `users`, `workspace_memberships` tables with RLS
- [ ] AC-1: Test fixtures verify RLS by attempting cross-workspace access
- [ ] AC-2: `make test` includes RLS verification suite
- [ ] AC-3: Migration template documents the RLS pattern for future tables
- [ ] AC-4: README includes RLS section
- [ ] AC-5: lint + build green

### Source
Foundation requirement.

---

## #2 — JWT auth with access/refresh tokens

**Labels:** `priority:P1`, `area:auth`, `type:feat`

### Summary
Implement JWT auth: RS256, 15-minute access token, 7-day refresh token, refresh rotation, blacklist on logout.

### Acceptance Criteria
- [ ] AC-1: POST /api/v1/auth/login returns access + refresh tokens
- [ ] AC-1: POST /api/v1/auth/refresh rotates the refresh token
- [ ] AC-1: POST /api/v1/auth/logout blacklists the refresh token
- [ ] AC-1: get_current_user dependency parses access token, raises 401 on invalid/expired
- [ ] AC-2: Tests cover happy path, expired tokens, invalid signatures, blacklisted refresh
- [ ] AC-3: All 5 guards on each auth endpoint (S5 for audit trail)
- [ ] AC-3: No secrets in code; keys via env vars

---

## #3 — Workspace and user models with RBAC capabilities

**Labels:** `priority:P1`, `area:auth`, `area:db`, `type:feat`

### Summary
Define Workspace, User, WorkspaceMembership models. Role enum: Admin / Maintainer / Viewer. Capability lookup function `user_has_capability(user_id, workspace_id, capability) -> bool`.

### Acceptance Criteria
- [ ] AC-1: Models defined with proper constraints
- [ ] AC-1: Default capability map per role (documented in CLAUDE.md)
- [ ] AC-1: `require_capability(cap)` dependency raises 403 with clear message
- [ ] AC-2: Tests for each role's capability set + boundary cases
- [ ] AC-3: Audit log entry on membership changes

---

## #4 — Service catalog: register and list services

**Labels:** `priority:P1`, `area:scorecards`, `type:feat`

### Summary
First catalog feature: register a service (name, description, repo URL, tier 1-3, owner team) and list services in the workspace.

### Acceptance Criteria
- [ ] AC-1: POST /api/v1/services creates a service (Maintainer+)
- [ ] AC-1: GET /api/v1/services lists services with pagination, filtering by tier and owner
- [ ] AC-1: GET /api/v1/services/{id} returns single service
- [ ] AC-1: PATCH /api/v1/services/{id} partial update
- [ ] AC-1: DELETE /api/v1/services/{id} soft-deletes (sets deleted_at)
- [ ] AC-2: Cross-workspace probe test
- [ ] AC-3: All 5 guards on every endpoint
- [ ] AC-6: Frontend list page with sortable table + create modal

---

## #5 — Service dependency declaration

**Labels:** `priority:P2`, `area:scorecards`, `type:feat`

### Summary
Allow services to declare dependencies on other services. Each dependency has criticality (HARD / SOFT) and direction (consumes / produces).

### Acceptance Criteria
- [ ] AC-1: POST /api/v1/services/{id}/dependencies adds a dependency
- [ ] AC-1: DELETE /api/v1/services/{id}/dependencies/{dep_id} removes
- [ ] AC-1: GET /api/v1/services/{id}/dependencies lists with depth=1 and depth=2 transitivity
- [ ] AC-1: Cycle detection — reject creating a dep that creates a cycle
- [ ] AC-2: Tests for cycle detection edge cases
- [ ] AC-6: Frontend: dependency list view in service detail page

---

## #6 — BaseScorecard plugin architecture

**Labels:** `priority:P1`, `area:scorecards`, `type:feat`

### Summary
Define `BaseScorecard` abstract class, `Finding` dataclass, `Severity` enum, `ScorecardCriterion` model, `SCORECARD_REGISTRY`. This is the plugin contract every scorecard implements.

### Acceptance Criteria
- [ ] AC-1: BaseScorecard with `name`, `version`, `description`, `evaluate(service, repo_path) -> AsyncIterator[Finding]`
- [ ] AC-1: Finding includes `criterion_id`, `severity`, `evidence`, `remediation`, `auto_fixable`
- [ ] AC-1: Registry auto-populates from `servicecat-be/src/scorecards/__init__.py`
- [ ] AC-1: ScorecardCriterion table seeded via migration
- [ ] AC-2: Tests for the registry, base class contract, and Finding serialization

---

## #7 — First scorecard: Documentation (5 criteria)

**Labels:** `priority:P1`, `area:scorecards`, `type:feat`

### Summary
Implement the Documentation scorecard with 5 criteria:
1. `doc.readme_present` — README.md exists at repo root
2. `doc.openapi_spec` — openapi.yaml or openapi.json exists OR FastAPI app generates one at /openapi.json
3. `doc.runbook` — RUNBOOK.md exists or docs/runbook.md exists
4. `doc.changelog` — CHANGELOG.md exists OR semver tags present in last 90 days
5. `doc.codeowners` — .github/CODEOWNERS exists

### Acceptance Criteria
- [ ] AC-1: All 5 criteria implemented as private methods on `DocumentationScorecard`
- [ ] AC-1: Each yields specific findings with concrete remediation
- [ ] AC-2: Test fixtures: 5 pass repos, 5 fail repos
- [ ] AC-3: Scorecard runner uses ephemeral repo storage with TTL
- [ ] AC-6: UI shows scorecard score with sparkline trend (when run history exists)

---

## #8 — POST /scorecards/{id}/runs endpoint

**Labels:** `priority:P1`, `area:scorecards`, `type:feat`

### Summary
Trigger a scorecard run for a list of target services. Run is async (Arq job). Returns 202 with run_id immediately.

### Acceptance Criteria
- [ ] AC-1: Returns 202 with run_id
- [ ] AC-1: Capability `scorecard:run` required (Maintainer+, NOT Viewer)
- [ ] AC-1: Tight rate limit: 10/minute (expensive operation)
- [ ] AC-1: Worker fetches repo, runs scorecard, persists findings, updates run status
- [ ] AC-1: GET /api/v1/scorecards/runs/{run_id} returns status and findings count
- [ ] AC-2: Cross-workspace probe; viewer-blocked test; rate-limit test
- [ ] AC-3: All 5 guards (this is THE endpoint for the live demo bug Moment 2)

### Note for demo prep
This endpoint is intentionally where Moment 2's pre-staged bug lives. The capability check `scorecard:run` is correctly added in this issue, but a future "promote-to-prod" endpoint will be where the missing-RBAC bug lives.

---

## #9 — Findings dashboard

**Labels:** `priority:P2`, `area:findings`, `area:frontend`, `type:feat`

### Summary
A dashboard listing all open findings across the workspace, filterable by severity, scorecard, service, and owner team.

### Acceptance Criteria
- [ ] AC-1: Table view with columns: severity, criterion, service, owner, age, auto-fixable, status
- [ ] AC-1: Filters: severity (multi), scorecard, service, owner team, auto-fixable, status
- [ ] AC-1: Bulk actions: assign, mark resolved, queue for /work-findings
- [ ] AC-2: Component tests for filter combinations
- [ ] AC-6: i18n + dark mode + empty/loading/error states

---

## #10 — Audit log table and audit_action dependency

**Labels:** `priority:P1`, `area:auth`, `area:db`, `type:security`

### Summary
Append-only audit_logs table. Database trigger that prevents UPDATE and DELETE. `audit_action(action_name)` FastAPI dependency that captures actor, action, resource, payload, IP, user-agent.

### Acceptance Criteria
- [ ] AC-1: audit_logs table with all columns, RLS by workspace
- [ ] AC-1: BEFORE UPDATE/DELETE triggers raise an error
- [ ] AC-1: audit_action dependency works with both sync and async handlers
- [ ] AC-1: GET /api/v1/audit/logs (admin only) lists logs with filtering
- [ ] AC-2: Test that UPDATE/DELETE actually fails on the table
- [ ] AC-2: Test that every state-changing endpoint creates a log entry

---

## #11 — Slack notification routing

**Labels:** `priority:P2`, `area:findings`, `type:feat`

### Summary
Route finding alerts to the owner team's Slack channel. Team config has `slack_channel` field. Fallback to `#servicecat-orphans` if missing.

### Acceptance Criteria
- [ ] AC-1: Team model has `slack_channel` optional field
- [ ] AC-1: When a finding is created with severity HIGH or CRITICAL, send Slack notification
- [ ] AC-1: Notification includes: severity, service, criterion, evidence, remediation, link to finding
- [ ] AC-1: If team has no channel configured, fallback channel + warning log
- [ ] AC-2: Test that notifications are sent (mocking Slack MCP)
- [ ] AC-2: Test fallback path

---

## #12 — Service detail page

**Labels:** `priority:P2`, `area:frontend`, `type:feat`

### Summary
Service detail page showing: metadata, current scores per scorecard, dependency graph (depth 1), recent findings, owner team.

### Acceptance Criteria
- [ ] AC-1: Route /services/{slug}
- [ ] AC-1: Score cards with delta indicators (▲/▼ vs previous run)
- [ ] AC-1: Dependency mini-graph (depth 1, both directions)
- [ ] AC-1: Last 10 findings with severity badges
- [ ] AC-1: "Run audit" button (calls /audit-service)
- [ ] AC-2: Component tests
- [ ] AC-6: i18n + dark mode

---

## #13 — CI/CD pipeline

**Labels:** `priority:P1`, `area:infra`, `type:infra`

### Summary
GitHub Actions workflow: lint, test, build, audit-security, deploy to staging on main.

### Acceptance Criteria
- [ ] AC-1: PR pipeline runs lint + test + build for both BE and FE
- [ ] AC-1: Main pipeline additionally runs /audit-security and deploys to staging
- [ ] AC-1: Postgres + Redis services in CI
- [ ] AC-1: Coverage reports uploaded as artifacts
- [ ] AC-1: Pipeline runtime <8 minutes for PRs
- [ ] AC-3: Secrets via GitHub Actions secrets, never in YAML

---

## #14 — Workspace settings page

**Labels:** `priority:P3`, `area:auth`, `area:frontend`, `type:feat`

### Summary
Admin-only settings page: workspace name, default branch for service repos, default scorecard set, Slack workspace connection.

### Acceptance Criteria
- [ ] AC-1: Route /settings/workspace (Admin only)
- [ ] AC-1: Form for editable fields with proper validation
- [ ] AC-1: Slack connection via OAuth (link to OAuth consent flow)
- [ ] AC-2: Capability test (Maintainer/Viewer redirected)
- [ ] AC-6: i18n + dark mode

---

## Phase 1 milestone

When issues #1 through #13 are merged, you have a working ServiceCat foundation:
- Auth + workspaces + RBAC
- Service catalog with dependencies
- Documentation scorecard runs end-to-end
- Findings dashboard
- CI/CD green
- Slack alerts working

Phase 2 issues (versioning, multiple scorecards, comparison views) come next — and that's where Moment 1's live `/implement` demo lives.
