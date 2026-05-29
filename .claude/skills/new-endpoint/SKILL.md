---
name: new-endpoint
description: Scaffold a new FastAPI endpoint with all 5 security guards, repository pattern, service layer, schemas, and tests. Use when adding any HTTP endpoint to the backend.
allowed-tools: Read, Write, Edit, Bash, Grep
---

# /new-endpoint

You scaffold a complete FastAPI endpoint following the project's layered architecture. The endpoint is non-negotiably wired with all 5 security guards. Match the patterns already in `servicecat-be/src/servicecat/routers/services.py` — read it first; it is the canonical reference.

## Invocation

```
/new-endpoint POST /scorecards/{id}/runs
/new-endpoint GET /services/{id}/dependencies
/new-endpoint PATCH /findings/{id} --capability=finding:assign
```

## Conventions that are easy to get wrong (verify against live code)

- Code lives under the package dir: `servicecat-be/src/servicecat/<layer>/` (NOT `src/<layer>/`).
- Guards use `Annotated[T, Depends(...)]` with **module-level precomputed** guard objects — not inline `= Depends(...)` defaults.
- Capabilities are the `Capability` enum from `servicecat.rbac` (e.g. `Capability.SERVICE_WRITE`), not bare strings.
- Every success response is wrapped: single resource → `DataResponse[T]`; paginated list → a `*ListResponse` (`{data, meta}`); simple list → `DataResponse[list[T]]`. Auth token endpoints are the only flat exception. See CLAUDE.md → API Conventions.
- The router is thin: parse → call service → wrap response. No business logic, no `db.execute()` in the router.
- `get_db` owns the transaction (`async with session.begin()`); repositories call `db.flush()`, never `db.commit()`.

## What you produce

### 1. The route handler — `servicecat-be/src/servicecat/routers/<resource>.py`

```python
import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from servicecat.deps import (
    WorkspaceContext,
    audit_action,
    get_current_workspace,
    get_db,
    rate_limit,
    require_capability,
)
from servicecat.rbac import Capability
from servicecat.schemas.base import DataResponse
from servicecat.schemas.scorecard_run import ScorecardRunCreateRequest, ScorecardRunResponse
from servicecat.services.scorecard_runner import ScorecardRunService

router = APIRouter(prefix="/api/v1/scorecards", tags=["scorecards"])

# Precomputed so the Depends() defaults hold a reference, not a nested call.
_run_cap = require_capability(Capability.SCORECARD_RUN)
_run_rl = rate_limit(per_minute=10, key="scorecard:run")

WorkspaceDep = Annotated[WorkspaceContext, Depends(get_current_workspace)]
DbDep = Annotated[AsyncSession, Depends(get_db)]


@router.post("/{scorecard_name}/runs", status_code=status.HTTP_202_ACCEPTED)
async def trigger_scorecard_run(
    scorecard_name: str,
    payload: ScorecardRunCreateRequest,
    context: WorkspaceDep,                                      # S1 (user) + S2 (workspace, sets RLS)
    db: DbDep,
    _cap: Annotated[None, Depends(_run_cap)],                   # S3
    _rl: Annotated[None, Depends(_run_rl)],                     # S4
    _audit: Annotated[None, Depends(audit_action("scorecard.run"))],  # S5
) -> DataResponse[ScorecardRunResponse]:
    run = await ScorecardRunService(db).trigger(
        workspace_id=context.workspace.id,
        scorecard_name=scorecard_name,
        target_service_ids=payload.target_service_ids,
        triggered_by=context.user.id,
    )
    return DataResponse(data=ScorecardRunResponse.model_validate(run))
```

`get_current_workspace` resolves the caller (S1) and the active workspace from `X-Workspace-Id` (S2, and sets the RLS `app.workspace_id`). `context.user` and `context.workspace` are available from it, so no separate `get_current_user` dep is needed when you already take `WorkspaceDep`.

### 2. The Pydantic schemas — `servicecat-be/src/servicecat/schemas/<resource>.py`

```python
from __future__ import annotations

import uuid
from datetime import datetime

from servicecat.schemas.base import ServiceCatBaseModel


class ScorecardRunCreateRequest(ServiceCatBaseModel):
    target_service_ids: list[uuid.UUID]


class ScorecardRunResponse(ServiceCatBaseModel):
    id: uuid.UUID
    scorecard: str
    status: str
    triggered_by: uuid.UUID
    created_at: datetime
```

All request/response models inherit `ServiceCatBaseModel`. The `{data}` envelope comes from `DataResponse[T]` in `servicecat.schemas.base` (don't hand-roll it). Paginated lists define their own `{data, meta}` model using `PageMeta` (see `schemas/service.py`).

### 3. The service layer — `servicecat-be/src/servicecat/services/<resource>_*.py`

```python
class ScorecardRunService:
    def __init__(self, db: AsyncSession) -> None:
        self._db = db
        self._runs = ScorecardRunRepository(db)

    async def trigger(self, *, workspace_id, scorecard_name, target_service_ids, triggered_by):
        # Validate inputs; raise typed errors from servicecat.errors
        # (NotFoundError -> 404, ConflictError -> 409, DomainValidationError -> 422).
        # NEVER raise HTTPException here — only routers map errors to HTTP, and a
        # global handler turns ServiceCatError into the {error:{code,message}} body.
        ...
```

### 4. The repository — `servicecat-be/src/servicecat/repositories/<resource>.py`

Thin wrapper around SQLAlchemy. The only place `select(...)`, `db.scalar/db.scalars`, and `db.flush()` are called. **No `db.commit()`** — `get_db` opens `session.begin()` and commits/rolls back per request. RLS scopes every query to the active workspace, so you don't hand-write `workspace_id` filters for reads of RLS-protected tables (but the column + policy must exist).

### 5. The tests — flat in `servicecat-be/tests/test_<resource>_endpoints.py`

Tests run against a real migrated Postgres with RLS. Use the `auth_client` and `rls_sessionmaker` fixtures from `tests/conftest.py`. Seed users/workspaces/memberships via `rls_sessionmaker`, get a token from `POST /api/v1/auth/login` (flat `{access_token}`), and send `Authorization: Bearer …` + `X-Workspace-Id`. **Read bodies via `resp.json()["data"]`** (the envelope).

Required cases for every endpoint:

| Test | Verifies |
|------|----------|
| `test_<role>_happy_path` | 2xx + correct `["data"]` body |
| `test_unauthenticated_returns_401` | S1 |
| `test_cross_workspace_probe_returns_404` | S2 (RLS hides other workspaces) |
| `test_viewer_cannot_<write>` → 403 | S3 |
| `test_invalid_payload_returns_422` | Pydantic validation |
| `test_<resource>_not_found_returns_404` | path params / typed NotFoundError |
| `test_duplicate_returns_409` | only if a unique constraint applies |
| (S4) | covered deterministically in `tests/test_redis_guards.py`, not per-endpoint HTTP |
| (S5) | assert the action appears in `GET /api/v1/audit/logs` `["data"]` |

### 6. Router registration — `servicecat-be/src/servicecat/main.py`

In `create_app()`:
```python
app.include_router(<resource>.router)
```

### 7. Finish

Run `make lint && make test` (backend). Then if the response shape changed, regenerate frontend types:
```
✅ Endpoint scaffolded.
Next (frontend): cd servicecat-fe && pnpm openapi:gen   # API must be running on :8000
```

## What you must NOT do

- Skip any of the 5 guards. Even read-only endpoints need S1+S2; sensitive reads also need S3/S5.
- Return a bare model. Wrap single resources in `DataResponse(data=...)`.
- Put business logic in the router, or call `db.execute()` from it.
- Raise `HTTPException` from a service — raise a typed error from `servicecat.errors`.
- Use `db.commit()` in a repository, or raw interpolated SQL.
- Forget to register the router in `main.py`, or to add the new capability to `servicecat/rbac.py` if one is needed.
