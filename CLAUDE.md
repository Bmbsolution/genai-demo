# ServiceCat — Project Rules for Claude

> **What is ServiceCat?**
> An Internal Developer Portal: service catalog, dependency graphs, automated compliance scorecards, and ownership-based finding routing. Teams register services, and ServiceCat continuously audits them against ruleset scorecards (Security, Observability, Documentation, Reliability) and opens PRs to fix gaps.

This file is the project contract. Every agent that operates on this codebase reads this first. Read it carefully, then act accordingly.

---

## Tech Stack

| Layer | Choice | Notes |
|-------|--------|-------|
| Backend | FastAPI + Python 3.12 | `servicecat-be/` |
| Frontend | Next.js 14 + Tailwind + shadcn/ui | `servicecat-fe/` |
| Database | PostgreSQL 16 with Row-Level Security | Workspace isolation enforced at row level |
| Cache / queues | Redis 7 | Rate limit counters, scorecard run queue |
| Auth | JWT (access + refresh) | RS256, 15min access / 7d refresh |
| Background workers | Arq (Redis-backed) | Scorecard runs, repo fetches |
| Repo analysis | GitPython + Tree-sitter | Read-only clones to ephemeral storage |
| LLM provider | Anthropic API (Claude Sonnet 4) | For agent-powered scorecards |
| Infra (local) | Docker Compose | One command to spin up |
| Infra (CI) | GitHub Actions | Lint, test, build, deploy |
| Observability | Prometheus + Grafana (compose) | Local dashboards |

---

## Domain Model

### Core Entities

```
Workspace ──┬── User ──── TeamMembership ──── Team
            │                                   │
            ├── Service ────────── Component   │
            │      │                            │
            │      ├── Dependency (→ Service) ──┘
            │      │
            │      └── Owner (→ Team)
            │
            ├── Scorecard ─── ScorecardCriterion
            │      │
            │      └── ScorecardRun ─── Score ─── Finding
            │                                       │
            │                                       └── AssignedTo (→ Team)
            │
            ├── Template
            │
            ├── Incident
            │
            └── AuditLog (immutable)
```

### Roles

| Role | Capabilities |
|------|--------------|
| **Admin** | All capabilities. Can create scorecards, manage workspace settings, manage users. |
| **Maintainer** | Can register/edit services, run scorecards, triage findings, create templates. |
| **Viewer** | Read-only. Can view catalog, scores, findings. Cannot trigger runs. |

### Key Capabilities (RBAC fine-grain)

```
service:read              service:write              service:delete
scorecard:read            scorecard:write            scorecard:run
finding:read              finding:assign             finding:resolve
template:read             template:write
team:read                 team:manage
workspace:settings        workspace:billing
audit:read
```

### Role → Capability Matrix

Source of truth: `servicecat-be/src/servicecat/rbac.py` (`ROLE_CAPABILITIES`).
Enforced per request by `require_capability` (S3) after `get_current_workspace`
(S2) resolves the caller's role in the active workspace.

| Capability | Viewer | Maintainer | Admin |
|------------|:------:|:----------:|:-----:|
| `service:read` `scorecard:read` `finding:read` `template:read` `team:read` | ✅ | ✅ | ✅ |
| `service:write` `scorecard:write` `scorecard:run` `finding:assign` `finding:resolve` `template:write` | — | ✅ | ✅ |
| `service:delete` `team:manage` `workspace:settings` `workspace:billing` `audit:read` | — | — | ✅ |

Roles nest: Viewer ⊂ Maintainer ⊂ Admin. The active workspace is selected by
the `X-Workspace-Id` request header; a workspace the caller is not a member of
is reported as 404 (no existence leak).

---

## Security Model — The 5 Guards

**Every endpoint must include all 5 dependency guards.** No exceptions. `/audit-security` enforces this.

```python
from fastapi import Depends
from servicecat.deps import (
    get_db, get_current_user, get_current_workspace,
    require_capability, rate_limit, audit_action
)

@router.post("/services")
async def create_service(
    payload: CreateServiceRequest,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),                    # S1: Auth
    ws: Workspace = Depends(get_current_workspace),            # S2: Tenant isolation
    _cap = Depends(require_capability("service:write")),       # S3: RBAC
    _rl = Depends(rate_limit(per_minute=30)),                  # S4: Rate limit
    _audit = Depends(audit_action("service.create")),          # S5: Audit log
):
    ...
```

### What each guard enforces

| Guard | Violation Code | Catches |
|-------|---------------|---------|
| **S1: Auth** | S1 | Unauthenticated access to non-public endpoint |
| **S2: Tenant isolation** | S2 | Cross-workspace data leakage; missing `workspace_id` filter |
| **S3: RBAC** | S3 | Missing capability check; viewer-triggered mutations; under-privileged actions on protected resources |
| **S4: Rate limit** | S4 | Unbounded request volume; expensive operations without throttle (e.g., scorecard runs) |
| **S5: Audit log** | S5 | State-changing operation with no audit trail; PII access without log entry |

### Additional Security Rules

- **S6:** No raw SQL with string interpolation. Use SQLAlchemy parameterized queries only.
- **S7:** Secrets only via environment variables. Never hardcoded, never in `.env.example` with real values.
- **S8:** All external HTTP calls timeout at 30s and use the shared `httpx.AsyncClient` from `servicecat.http`.

---

## Code Conventions

### Backend (Python)

- **Format:** `ruff format` (line length 100)
- **Lint:** `ruff check` with `--select ALL --ignore D,ANN101,ANN102`
- **Type checking:** `mypy --strict` on `servicecat-be/src/`
- **Async by default:** All I/O is async. No sync DB calls. No `requests` library — use `httpx.AsyncClient`.
- **Repository pattern:** Persistence in `servicecat-be/src/repositories/`. Never call `db.execute()` from a router.
- **Service layer:** Business logic in `servicecat-be/src/services/`. Routers stay thin (parse → call service → format response).
- **Pydantic v2:** All request/response models inherit from `ServiceCatBaseModel` in `servicecat-be/src/schemas/base.py`.
- **Errors:** Raise typed exceptions from `servicecat.errors`. Never raise `HTTPException` directly from services — only routers translate domain errors to HTTP status codes.

### Frontend (TypeScript / Next.js)

- **Format:** Prettier with project config
- **Lint:** ESLint with the team config in `servicecat-fe/.eslintrc.json`
- **Components:** shadcn/ui primitives only. No raw `<button>` — always `<Button>`.
- **State:** Server state via TanStack Query. Client state via Zustand for global, `useState` for local.
- **Forms:** React Hook Form + Zod schemas (shared with backend via OpenAPI codegen).
- **Routing:** App Router. Each route folder must contain `page.tsx`, `loading.tsx`, and `error.tsx`.
- **i18n:** `next-intl`. Every user-visible string must be in a translation file (en + fr at minimum).
- **Dark mode:** All components must work in both themes. Tailwind `dark:` prefix everywhere.

### Naming

| Thing | Convention | Example |
|-------|-----------|---------|
| Python module | `snake_case.py` | `scorecard_runner.py` |
| Python class | `PascalCase` | `ScorecardRunner` |
| Python function | `snake_case` | `run_scorecard_against_service()` |
| TypeScript file (component) | `PascalCase.tsx` | `ServiceCard.tsx` |
| TypeScript file (logic) | `kebab-case.ts` | `format-score.ts` |
| TypeScript hook | `useCamelCase` | `useServiceById` |
| API route | `kebab-case` plural | `POST /services`, `GET /scorecards/{id}/runs` |
| Database table | `snake_case` plural | `scorecard_runs`, `service_dependencies` |
| Migration filename | `YYYYMMDD_HHMM_description.py` | `20260520_1430_add_scorecard_versioning.py` |

---

## What NEVER Goes in Code

- **Tokens, keys, secrets** — JWT tokens, API keys, OAuth client secrets, DB connection strings with credentials
- **Customer service data** — even in fixtures or seed scripts. Use clearly fake names like `acme-corp`, `payment-svc`, `alice@example.com`.
- **`--no-verify` on git commits** — pre-commit hooks exist for a reason
- **`# noqa` without a code** — always specify which rule, e.g., `# noqa: E501`
- **`any` type in TypeScript** — use `unknown` and narrow, or define the type properly
- **`console.log` in committed frontend code** — use the `logger` from `@/lib/logger`

---

## Acceptance Criteria — AC-1 through AC-6

**Every feature is incomplete until all six pass.** `/plan-feature` and `/implement` generate these automatically.

| AC | Category | What Must Pass |
|----|----------|----------------|
| **AC-1** | Functional | All described behaviors work — happy path + at least 2 edge cases |
| **AC-2** | Tests | Unit tests + router/integration tests + security tests all pass with ≥80% coverage on new code |
| **AC-3** | Security | `/audit-security` clean — all 5 guards present, S6-S8 satisfied |
| **AC-4** | Quality | `/simplify` clean — no duplication, follows repository/service pattern, no orphaned helpers |
| **AC-5** | Lint & Build | `make lint` (ruff + mypy) and `pnpm lint && pnpm build` pass |
| **AC-6** | Frontend | Types generated from OpenAPI, hooks via TanStack Query, i18n keys added, dark mode verified, `/frontend-design` used |

---

## The Inner Fix Loop

When AC-1, AC-2, AC-3, AC-4, or AC-5 fails, Claude does NOT proceed. The loop runs:

```
Test/audit fails
    ↓
Read the error completely (don't skim)
    ↓
Identify the root cause (not the symptom)
    ↓
Apply the minimal fix
    ↓
Re-run the failing check
    ↓
    ├── Passes → continue to next phase
    └── Still fails →
            ↓
        ── Attempt 2: rethink approach
            ↓
        ── Attempt 3: try alternative
            ↓
        After 3 failed attempts: STOP. Ask the human.
            Don't keep guessing. Don't commit broken code.
```

---

## Repository Layout

```
servicecat/
├── servicecat-be/                  # FastAPI backend
│   ├── src/
│   │   ├── routers/                # HTTP endpoints (thin)
│   │   ├── services/               # Business logic
│   │   ├── repositories/           # Data access
│   │   ├── models/                 # SQLAlchemy ORM
│   │   ├── schemas/                # Pydantic
│   │   ├── deps.py                 # The 5 guards
│   │   ├── errors.py               # Typed exceptions
│   │   ├── scorecards/             # Scorecard runners (one per type)
│   │   │   ├── base.py
│   │   │   ├── security.py
│   │   │   ├── observability.py
│   │   │   ├── documentation.py
│   │   │   └── reliability.py
│   │   └── workers/                # Background workers (Arq)
│   ├── tests/
│   ├── migrations/                 # Alembic
│   ├── pyproject.toml
│   └── Makefile
│
├── servicecat-fe/                  # Next.js 14 frontend
│   ├── app/                        # App Router
│   ├── components/                 # UI components (shadcn-based)
│   ├── lib/
│   ├── hooks/
│   ├── messages/                   # i18n translations
│   │   ├── en.json
│   │   └── fr.json
│   ├── package.json
│   └── next.config.js
│
├── docker-compose.yml              # Local dev stack
├── .github/workflows/              # CI/CD
├── .claude/                        # Claude Code config
│   ├── settings.json
│   └── skills/
├── docs/
├── CLAUDE.md                       # This file
├── WORKFLOW.md                     # How the team uses Claude Code
└── README.md
```

---

## Database Conventions

### Workspace Isolation (Row-Level Security)

Every multi-tenant table has a `workspace_id UUID NOT NULL` column with an index. RLS policy enforces:

```sql
CREATE POLICY workspace_isolation ON {table}
    USING (workspace_id = current_setting('app.workspace_id')::uuid);
```

The `get_current_workspace` dependency sets `app.workspace_id` per request. Migrations enable RLS on every new table by default.

### Audit Log

```sql
CREATE TABLE audit_logs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    workspace_id UUID NOT NULL,
    actor_id UUID NOT NULL,         -- The user who performed the action
    action TEXT NOT NULL,           -- e.g., "service.create", "scorecard.run"
    resource_type TEXT NOT NULL,    -- e.g., "Service", "Scorecard"
    resource_id UUID,               -- May be NULL for fleet-wide actions
    payload JSONB,                  -- Snapshot of relevant input
    ip INET,
    user_agent TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);
```

The audit log is **append-only**. There is no UPDATE or DELETE policy. Attempts to modify it raise an error in the database.

### Migrations

- Alembic only. No manual SQL outside migrations.
- Every migration must be reversible (`downgrade()` actually works).
- Migration that touches data and schema in the same revision: split into two revisions.
- New tables get RLS enabled in the same migration that creates them.

---

## API Conventions

### URL Structure

```
GET    /api/v1/services                 # List (paginated, workspace-scoped)
POST   /api/v1/services                 # Create
GET    /api/v1/services/{id}            # Read
PATCH  /api/v1/services/{id}            # Partial update
DELETE /api/v1/services/{id}            # Soft delete (sets deleted_at)

GET    /api/v1/services/{id}/scores         # Sub-resources nested
POST   /api/v1/scorecards/{id}/runs          # Action-style for non-CRUD
```

### Response Format

Every success response is wrapped in a `data` envelope. The shape depends on
the resource kind:

**Single resource** — `{ "data": { ... } }`:
```json
{ "data": { "id": "…", "name": "payment-svc", "tier": 1 } }
```

**Paginated collection** — `{ "data": [ ... ], "meta": { ... } }`:
```json
{ "data": [ { "id": "…" } ], "meta": { "limit": 50, "offset": 0, "total": 42 } }
```

**Simple (non-paginated) collection** — `{ "data": [ ... ] }` (no `meta`):
```json
{ "data": [ { "id": "…", "slug": "acme-corp" } ] }
```

Implemented with the generic `DataResponse[T]` envelope
(`servicecat-be/src/servicecat/schemas/base.py`) for single resources and
simple lists; paginated collections use their own `{data, meta}` models (e.g.
`ServiceListResponse`).

**Exception — auth token endpoints.** `POST /auth/login` and `POST /auth/refresh`
return the flat OAuth2 token shape, **not** enveloped:
```json
{ "access_token": "…", "refresh_token": "…", "token_type": "bearer" }
```
This is deliberate (OAuth2 convention; clients read these fields at the top level).

Error:
```json
{ "error": { "code": "S3_RBAC_DENIED", "message": "...", "details": {...} } }
```

### Pagination

Cursor-based by default for list endpoints. Query params: `?cursor=...&limit=50` (max 200).

### Versioning

`/api/v1/...` always. Breaking changes go to `/api/v2/...` with `/v1/...` deprecated for 6 months minimum.

---

## Scorecard Plugin Architecture

Each scorecard type is a class extending `BaseScorecard`:

```python
# servicecat-be/src/scorecards/base.py
from abc import ABC, abstractmethod
from typing import Iterable

class BaseScorecard(ABC):
    name: str
    version: str
    description: str

    @abstractmethod
    async def evaluate(self, service: Service, repo_path: Path) -> Iterable[Finding]:
        """Yields findings. Empty iterable means service passes."""
```

To add a new scorecard type, use `/new-scorecard <name>` — it scaffolds the class, the criteria definitions, the registration, and a starter test.

Each finding includes:
- `criterion_id` (which criterion failed)
- `severity` (CRITICAL / HIGH / MEDIUM / LOW)
- `evidence` (file path, line number, snippet)
- `remediation` (concrete suggestion the agent can act on)
- `auto_fixable` (boolean — used by `/work-findings`)

---

## Memory & Continuity

Claude maintains personal auto-memory in `~/.claude/projects/servicecat/memory/`. Mistakes Claude makes and corrections from the team are stored here so they're not repeated.

**If Claude makes the same mistake twice:** call it out, correct it, and the correction should be added to memory.

---

## What Counts as "Production-Ready"

A PR is production-ready when:

1. All AC-1 through AC-6 pass — verified, not assumed
2. The feature works end-to-end with a real user click-through (or curl chain for API-only)
3. Migrations have been tested forward AND backward
4. Error states are handled in the UI (loading, empty, error, success)
5. The PR description tells a reviewer exactly how to test it

**Claude never merges.** A human teammate must approve.

---

## When in Doubt

1. **Read the relevant skill** in `.claude/skills/` before deciding how to proceed.
2. **Check the existing patterns** — `/explore-codebase` is cheap; guessing is expensive.
3. **Ask the human** rather than guess. Three failed fix attempts = stop and ask.
4. **The audit beats the test** — a passing test on insecure code is worse than failing tests on secure code.

---

## Project Identity

When committing, Claude uses the identity `dev-servicecat <dev@servicecat.local>`. The git hook in `.claude/settings.json` sets this automatically on session start.
