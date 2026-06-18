# Gatherly — Project Rules for Claude

> **What is Gatherly?**
> An event-management platform: create events, invite guests, and collect RSVPs
> in real time — waitlists, +1s, dietary needs, and door check-in. What makes it
> a demo vehicle is that the system **audits its own events** — it runs a
> readiness checklist on each event, flags what's missing, and drafts the fixes —
> showcasing multi-agent orchestration on a real, working product.

This file is the project contract. Every agent that operates on this codebase reads this first. Read it carefully, then act accordingly.

---

## Tech Stack

| Layer | Choice | Notes |
|-------|--------|-------|
| Backend | FastAPI + Python 3.12 | `gatherly-be/` |
| Frontend | Next.js 14 + Tailwind + shadcn/ui | `gatherly-fe/` |
| Database | SQLite (async, `aiosqlite`) by default | Zero external infra; point `GATHERLY_DATABASE_URL` at Postgres in production |
| ORM | SQLAlchemy 2.0 (async) | Schema created via `Base.metadata.create_all` on startup (SQLite demo — no migration tool) |
| Auth | JWT (access + refresh) + Google Sign-In | HS256, 15min access / 7d refresh; refresh-token rotation with in-process revocation store |
| Rate limiting | In-memory fixed window | Per client IP + route key; no Redis |
| Billing | Stripe (mock provider when unconfigured) | Free-tier caps; Pro lifts them |
| LLM provider | Anthropic API (Claude Sonnet 4.6) | For agent-powered event audits |
| Infra (deploy) | GCP Cloud Run (be) + Netlify (fe) | Terraform in `deploy/` |
| Infra (CI) | GitHub Actions | Lint, test, build, deploy |

> **No Docker, Postgres, or Redis required to run locally.** The backend runs on
> SQLite out of the box. To launch the app, use `/run-app`.

---

## Domain Model

### Core Entities

```
User (host / admin)
  │
  ├── Event ──────────── Guest (RSVP)
  │     │                  ├── rsvp_status (pending | yes | no | maybe | waitlisted)
  │     │                  ├── plus_one
  │     │                  ├── dietary_notes
  │     │                  └── checked_in_at
  │     │
  │     ├── status (draft | published)
  │     ├── visibility (private | unlisted | public)
  │     └── capacity
  │
  ├── plan (free | pro)        # billing
  │
  └── AuditLog (immutable, append-only)
```

Tenant isolation is **by owner**: every host-facing query is scoped to
`owner_id == user.id`. There is no workspace concept. Public guest access goes
through a per-guest `invite_token` on the `/rsvp/{token}` page — a guest can only
ever see or update their own row.

### Roles

| Role | Capabilities |
|------|--------------|
| **Admin** | All host capabilities, plus deleting events. |
| **Host** | Create/edit events, manage guests, run readiness/insights on their own events. |

Roles nest: **Host ⊂ Admin**.

### Key Capabilities (RBAC fine-grain)

Source of truth: `gatherly-be/src/gatherly/rbac.py` (`ROLE_CAPABILITIES`).

```
event:read        event:write        event:delete
guest:read        guest:write
```

### Role → Capability Matrix

Enforced per request by `require_capability` (S3) after `get_current_user` (S1)
resolves the caller. Ownership (S2) is enforced in the service/repository layer
by scoping to `owner_id`; a resource the caller doesn't own is reported as **404**
(no existence leak).

| Capability | Host | Admin |
|------------|:----:|:-----:|
| `event:read` `event:write` `guest:read` `guest:write` | ✅ | ✅ |
| `event:delete` | — | ✅ |

---

## Security Model — The 5 Guards

**Every host-facing endpoint must carry the relevant guards.** `/audit-security`
enforces this. S1/S3/S4/S5 are FastAPI dependencies; **S2 (ownership) is enforced
in the service/repository layer** by passing `user.id` as the owner — dropping
that scope is the classic planted bug.

```python
from typing import Annotated
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from gatherly.deps import audit_action, get_current_user, get_db, rate_limit, require_capability
from gatherly.models import User
from gatherly.rbac import Capability
from gatherly.schemas.base import DataResponse

router = APIRouter(prefix="/api/v1/events", tags=["events"])


@router.post("", status_code=201)
async def create_event(
    payload: EventCreateRequest,
    db: Annotated[AsyncSession, Depends(get_db)],
    user: Annotated[User, Depends(get_current_user)],                              # S1: Auth
    _cap: Annotated[None, Depends(require_capability(Capability.EVENT_WRITE))],    # S3: RBAC
    _rl: Annotated[None, Depends(rate_limit(per_minute=30, key="event:write"))],   # S4: Rate limit
    _audit: Annotated[None, Depends(audit_action("event.create"))],               # S5: Audit log
) -> DataResponse[EventResponse]:
    event = await EventService(db).create(owner_id=user.id, payload=payload)       # S2: owner-scoped
    return DataResponse(data=EventResponse.model_validate(event))
```

### What each guard enforces

| Guard | Violation Code | Catches |
|-------|---------------|---------|
| **S1: Auth** | S1 | Unauthenticated access to a non-public endpoint (`get_current_user`) |
| **S2: Ownership** | S2 | Cross-owner data leakage; a query not scoped to `owner_id` (surfaced as 404) |
| **S3: RBAC** | S3 | Missing capability check; host doing an admin-only action (e.g. delete) |
| **S4: Rate limit** | S4 | Unbounded request volume; expensive operations without throttle |
| **S5: Audit log** | S5 | State-changing operation with no audit trail |

### Additional Security Rules

- **S6:** No raw SQL with string interpolation. Use SQLAlchemy parameterized queries only.
- **S7:** Secrets only via environment variables (`GATHERLY_*` prefix). Never hardcoded, never real values in `.env.example`.
- **S8:** All external HTTP calls timeout at 30s and use the shared `httpx.AsyncClient`.

---

## Code Conventions

### Backend (Python)

- **Format:** `ruff format` (line length 100)
- **Lint:** `ruff check` with `--select ALL` (see `pyproject.toml` for the ignore list)
- **Type checking:** `mypy --strict` on `gatherly-be/src/`
- **Async by default:** All I/O is async. No sync DB calls. No `requests` library — use `httpx.AsyncClient`.
- **Repository pattern:** Persistence in `gatherly-be/src/gatherly/repositories/`. Never call `db.execute()` from a router.
- **Service layer:** Business logic in `gatherly-be/src/gatherly/services/`. Routers stay thin (parse → call service → format response).
- **Pydantic v2:** All request/response models inherit from `GatherlyBaseModel` in `gatherly-be/src/gatherly/schemas/base.py`.
- **Errors:** Raise typed exceptions from `gatherly.errors`. Never raise `HTTPException` directly from services — only routers (and the global handlers in `main.py`) translate domain errors to HTTP status codes.
- **Runtime hints:** Routers and `deps.py` omit `from __future__ import annotations` — FastAPI resolves dependency hints at runtime, so those types must be real imports.

### Frontend (TypeScript / Next.js)

- **Format:** Prettier with project config
- **Lint:** ESLint with the team config in `gatherly-fe/.eslintrc.json`
- **Components:** shadcn/ui primitives only. No raw `<button>` — always `<Button>`.
- **State:** Server state via TanStack Query. Client state via Zustand for global, `useState` for local.
- **Forms:** React Hook Form + Zod schemas (shared with backend via OpenAPI codegen — `pnpm openapi:gen`).
- **Routing:** App Router (`/login`, `/signup`, `/events`, `/events/[id]`, `/account`, `/rsvp/[token]`).
- **i18n:** `next-intl`. Every user-visible string must be in a translation file (en + fr at minimum).
- **Dark mode:** All components must work in both themes. Tailwind `dark:` prefix everywhere.

### Naming

| Thing | Convention | Example |
|-------|-----------|---------|
| Python module | `snake_case.py` | `auth_service.py` |
| Python class | `PascalCase` | `InsightsService` |
| Python function | `snake_case` | `list_for_owner()` |
| TypeScript file (component) | `PascalCase.tsx` | `EventCard.tsx` |
| TypeScript file (logic) | `kebab-case.ts` | `format-date.ts` |
| TypeScript hook | `useCamelCase` | `useEventById` |
| API route | `kebab-case` plural | `POST /events`, `GET /events/{id}/readiness` |
| Database table | `snake_case` plural | `events`, `guests`, `audit_logs` |

---

## What NEVER Goes in Code

- **Tokens, keys, secrets** — JWT secrets, API keys, Stripe keys, OAuth client secrets, DB connection strings with credentials
- **Real attendee / customer data** — even in fixtures or seed scripts. Use clearly fake names like `acme-corp`, `alice@example.com`, `host@gatherly.app`.
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
| **AC-3** | Security | `/audit-security` clean — guards present, S6-S8 satisfied |
| **AC-4** | Quality | `/simplify` clean — no duplication, follows repository/service pattern, no orphaned helpers |
| **AC-5** | Lint & Build | `ruff` + `mypy --strict` and `pnpm lint && pnpm build` pass |
| **AC-6** | Frontend | Types generated from OpenAPI, hooks via TanStack Query, i18n keys added (en+fr), dark mode verified, `/frontend-design` used |

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
gatherly/
├── gatherly-be/                    # FastAPI backend
│   ├── src/gatherly/
│   │   ├── routers/                # HTTP endpoints (thin): auth, events, guests, rsvp, billing
│   │   ├── services/               # Business logic (events, guests, rsvp, insights, billing, …)
│   │   ├── repositories/           # Data access (events, guests, users, audit)
│   │   ├── models/                 # SQLAlchemy ORM (user, event, guest, audit)
│   │   ├── schemas/                # Pydantic (base + per-resource)
│   │   ├── scripts/                # seed.py (demo host + events)
│   │   ├── deps.py                 # The security guards
│   │   ├── rbac.py                 # Roles + capabilities
│   │   ├── errors.py               # Typed domain exceptions
│   │   ├── security.py             # JWT encode/decode, password hashing
│   │   ├── rate_limit.py           # In-memory fixed-window limiter
│   │   ├── token_store.py          # Refresh-token revocation
│   │   ├── db.py                   # Async engine, sessionmaker, init_db
│   │   ├── config.py               # GATHERLY_* settings
│   │   └── main.py                 # App factory + global error handlers
│   ├── tests/
│   ├── pyproject.toml
│   └── Makefile                    # NOTE: Windows-only paths — on macOS/Linux call .venv/bin/python directly
│
├── gatherly-fe/                    # Next.js 14 frontend
│   ├── app/                        # App Router
│   ├── components/                 # UI components (shadcn-based)
│   ├── hooks/  lib/  i18n/
│   ├── messages/                   # i18n translations (en.json, fr.json)
│   └── package.json
│
├── deploy/                         # Terraform (GCP) + deployment runbooks
├── docs/                           # Demo runbook, conference prep, recordings
├── .github/workflows/              # CI/CD
├── .claude/                        # Claude Code config (settings.json, skills/)
├── CLAUDE.md                       # This file
├── WORKFLOW.md                     # How the team uses Claude Code
└── README.md
```

---

## Database Conventions

### Tenant Isolation (owner scoping)

There is no Row-Level Security and no workspace. Every host-owned table carries an
`owner_id` (events) or a parent FK (guests → events), and **every host-facing
read/write is scoped to the caller's `user.id`** in the service/repository layer
(e.g. `EventRepository.get_for_owner`). A resource the caller doesn't own surfaces
as `404` (`OwnershipError`, code `S2_NOT_OWNER`) so we never leak existence.

### Audit Log

```
audit_logs (
    id           UUID  PK
    actor_id     UUID  NOT NULL        -- the user who performed the action
    action       TEXT  NOT NULL        -- e.g. "event.create", "guest.update"
    resource_type TEXT NOT NULL        -- derived from action prefix
    resource_id  UUID                  -- may be NULL
    ip           TEXT
    user_agent   TEXT
    created_at   TIMESTAMP NOT NULL
)
```

The audit log is **append-only**: the repository exposes only `record(...)` — no
update, no delete.

### Schema & migrations

- SQLite by default; the schema is created via `Base.metadata.create_all` in
  `init_db()` on startup. There is **no Alembic migration tool** in the demo.
- Adding a column/table = add it to the SQLAlchemy model. Delete the local
  `gatherly.db` and re-seed to pick up schema changes.
- For a production Postgres deployment, introduce Alembic before relying on
  schema evolution — `create_all` only creates missing tables, it does not alter.
- Foreign keys cascade (`ON DELETE CASCADE`); SQLite FK enforcement is enabled
  per-connection in `db.py`.

---

## API Conventions

### URL Structure

```
GET    /api/v1/events                   # List (paginated, owner-scoped)
POST   /api/v1/events                   # Create
GET    /api/v1/events/{id}              # Read
PATCH  /api/v1/events/{id}              # Partial update
DELETE /api/v1/events/{id}             # Soft delete (sets deleted_at; admin only)

GET    /api/v1/events/{id}/insights      # Headline numbers for the guest list
GET    /api/v1/events/{id}/readiness     # The readiness checklist
POST   /api/v1/rsvp/{token}              # Public guest RSVP (no login)
```

### Response Format

Every success response is wrapped in a `data` envelope:

**Single resource** — `{ "data": { ... } }`:
```json
{ "data": { "id": "…", "title": "Summer Rooftop Party", "status": "published" } }
```

**Paginated collection** — `{ "data": [ ... ], "meta": { ... } }`:
```json
{ "data": [ { "id": "…" } ], "meta": { "limit": 50, "offset": 0, "total": 42 } }
```

Single resources and simple lists use the generic `DataResponse[T]` envelope
(`gatherly-be/src/gatherly/schemas/base.py`); paginated collections use their own
`{data, meta}` models (e.g. `EventListResponse`) with `PageMeta`.

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

Offset-based for list endpoints. Query params: `?limit=50&offset=0` (limit max 200).

### Versioning

`/api/v1/...` always. Breaking changes go to `/api/v2/...` with `/v1/...` deprecated for 6 months minimum.

---

## Event Readiness — the self-audit

Gatherly's "audit" is the event **readiness checklist** in
`gatherly-be/src/gatherly/services/insights.py` (`InsightsService.get_readiness`).
It reads an owned event plus its guest list (proving ownership first → 404) and
returns a set of pass/fail checks, each with a severity:

| Check | Severity |
|-------|----------|
| `has_guests`, `within_capacity`, `has_location` | high |
| `published`, `healthy_response_rate` | medium |
| `has_description`, `has_cover_image`, `has_end_time` | low |

An event is **ready** iff every *high*-severity check passes. The roll-up
(`ready`, `passed`, `total`, `checks`) is what the UI's "Event readiness" panel
renders and what the autonomy demo (`/work-findings`) acts on. Adding a new check
means adding a `ReadinessCheck` to that list — keep checks read-only and
ownership-scoped.

---

## Memory & Continuity

Claude maintains personal auto-memory in `~/.claude/projects/gatherly/memory/`.
Mistakes Claude makes and corrections from the team are stored here so they're not
repeated.

**If Claude makes the same mistake twice:** call it out, correct it, and the correction should be added to memory.

---

## What Counts as "Production-Ready"

A PR is production-ready when:

1. All AC-1 through AC-6 pass — verified, not assumed
2. The feature works end-to-end with a real user click-through (or curl chain for API-only)
3. Schema changes are reflected in the models and re-seed cleanly (and in Alembic, if/when introduced for Postgres)
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

When committing, Claude uses the identity `dev-gatherly <dev@gatherly.local>`. The git hook in `.claude/settings.json` sets this automatically on session start.
