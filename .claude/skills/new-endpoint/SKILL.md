---
name: new-endpoint
description: Scaffold a new FastAPI endpoint with all 5 security guards, repository pattern, service layer, schemas, and tests. Use when adding any HTTP endpoint to the backend.
allowed-tools: Read, Write, Edit, Bash, Grep
---

# /new-endpoint

You scaffold a complete FastAPI endpoint following the project's layered architecture. The endpoint is non-negotiably wired with all 5 security guards. Match the patterns already in `gatherly-be/src/gatherly/routers/events.py` — read it first; it is the canonical reference.

## Invocation

```
/new-endpoint POST /events/{id}/guests
/new-endpoint GET /events/{id}/guests
/new-endpoint PATCH /guests/{id} --capability=guest:write
```

## Conventions that are easy to get wrong (verify against live code)

- Code lives under the package dir: `gatherly-be/src/gatherly/<layer>/` (NOT `src/<layer>/`).
- Guards use `Annotated[T, Depends(...)]` with **module-level precomputed** guard objects — not inline `= Depends(...)` defaults.
- Capabilities are the `Capability` enum from `gatherly.rbac` (e.g. `Capability.EVENT_WRITE`), not bare strings.
- Every success response is wrapped: single resource → `DataResponse[T]`; paginated list → a `*ListResponse` (`{data, meta}`); simple list → `DataResponse[list[T]]`. Auth token endpoints are the only flat exception. See CLAUDE.md → API Conventions.
- The router is thin: parse → call service → wrap response. No business logic, no `db.execute()` in the router.
- `get_db` owns the transaction (`async with session.begin()`); repositories call `db.flush()`, never `db.commit()`.

## What you produce

### 1. The route handler — `gatherly-be/src/gatherly/routers/<resource>.py`

```python
import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from gatherly.deps import (
    audit_action,
    get_current_user,
    get_db,
    rate_limit,
    require_capability,
)
from gatherly.models import User
from gatherly.rbac import Capability
from gatherly.schemas.base import DataResponse
from gatherly.schemas.guest import GuestCreateRequest, GuestResponse
from gatherly.services.guest_service import GuestService

router = APIRouter(prefix="/api/v1/events", tags=["guests"])

# Precomputed so the Depends() defaults hold a reference, not a nested call.
_write_cap = require_capability(Capability.GUEST_WRITE)
_write_rl = rate_limit(per_minute=30, key="guest:write")

UserDep = Annotated[User, Depends(get_current_user)]
DbDep = Annotated[AsyncSession, Depends(get_db)]


@router.post("/{event_id}/guests", status_code=status.HTTP_201_CREATED)
async def add_guest(
    event_id: uuid.UUID,
    payload: GuestCreateRequest,
    user: UserDep,                                             # S1: authenticated caller
    db: DbDep,
    _cap: Annotated[None, Depends(_write_cap)],                # S3
    _rl: Annotated[None, Depends(_write_rl)],                  # S4
    _audit: Annotated[None, Depends(audit_action("guest.create"))],  # S5
) -> DataResponse[GuestResponse]:
    # S2 is enforced inside the service: the event is loaded scoped to owner_id == user.id,
    # so a caller who doesn't own the event gets a 404 (OwnershipError) — no existence leak.
    guest = await GuestService(db).add_guest(
        owner_id=user.id,
        event_id=event_id,
        payload=payload,
    )
    return DataResponse(data=GuestResponse.model_validate(guest))
```

`get_current_user` resolves the caller from the Bearer access token (S1). S2 (tenant isolation) is **not** a FastAPI dependency in Gatherly — there is no workspace and no Row-Level Security. Instead, every host-facing query is scoped to `owner_id == user.id` in the service/repository layer (e.g. `EventRepository.get_for_owner`). A resource the caller doesn't own is reported as 404 (`OwnershipError`, code `S2_NOT_OWNER`) so existence isn't leaked.

### 2. The Pydantic schemas — `gatherly-be/src/gatherly/schemas/<resource>.py`

```python
from __future__ import annotations

import uuid
from datetime import datetime

from gatherly.schemas.base import GatherlyBaseModel


class GuestCreateRequest(GatherlyBaseModel):
    name: str
    email: str


class GuestResponse(GatherlyBaseModel):
    id: uuid.UUID
    event_id: uuid.UUID
    name: str
    email: str
    rsvp_status: str
    created_at: datetime
```

All request/response models inherit `GatherlyBaseModel`. The `{data}` envelope comes from `DataResponse[T]` in `gatherly.schemas.base` (don't hand-roll it). Paginated lists define their own `{data, meta}` model using `PageMeta` (see `schemas/event.py`).

### 3. The service layer — `gatherly-be/src/gatherly/services/<resource>_*.py`

```python
class GuestService:
    def __init__(self, db: AsyncSession) -> None:
        self._db = db
        self._events = EventRepository(db)
        self._guests = GuestRepository(db)

    async def add_guest(self, *, owner_id, event_id, payload):
        # Load the parent event scoped to the owner. This is where S2 lives:
        # get_for_owner raises OwnershipError (-> 404) if the caller isn't the owner.
        # Validate inputs; raise typed errors from gatherly.errors
        # (NotFoundError -> 404, ConflictError -> 409, ValidationError -> 422).
        # NEVER raise HTTPException here — only routers map errors to HTTP, and a
        # global handler turns GatherlyError into the {error:{code,message}} body.
        ...
```

### 4. The repository — `gatherly-be/src/gatherly/repositories/<resource>.py`

Thin wrapper around SQLAlchemy. The only place `select(...)`, `db.scalar/db.scalars`, and `db.flush()` are called. **No `db.commit()`** — `get_db` opens `session.begin()` and commits/rolls back per request. There is no RLS, so owner-scoping is explicit: host-facing reads carry a `.where(Event.owner_id == owner_id)` clause (see `EventRepository.get_for_owner`).

### 5. The tests — flat in `gatherly-be/tests/test_<resource>_endpoints.py`

Tests run against a real SQLite database (`sqlite+aiosqlite`, zero external infra; schema is created via `Base.metadata.create_all` in `init_db()` — there is no migration tool). Use the `auth_client` and `sessionmaker` fixtures from `tests/conftest.py`. Seed users/events via the sessionmaker, get a token from `POST /api/v1/auth/login` (flat `{access_token}`), and send `Authorization: Bearer …`. **Read bodies via `resp.json()["data"]`** (the envelope).

Required cases for every endpoint:

| Test | Verifies |
|------|----------|
| `test_<role>_happy_path` | 2xx + correct `["data"]` body |
| `test_unauthenticated_returns_401` | S1 |
| `test_other_owner_probe_returns_404` | S2 (owner-scoping hides resources you don't own) |
| `test_host_cannot_delete` → 403 | S3 (only Admin has `event:delete`) |
| `test_invalid_payload_returns_422` | Pydantic validation |
| `test_<resource>_not_found_returns_404` | path params / typed NotFoundError |
| `test_duplicate_returns_409` | only if a unique constraint applies |
| (S4) | covered deterministically in `tests/test_rate_limit_guards.py`, not per-endpoint HTTP |
| (S5) | assert the action appears in `GET /api/v1/audit/logs` `["data"]` |

### 6. Router registration — `gatherly-be/src/gatherly/main.py`

In `create_app()`:
```python
app.include_router(<resource>.router)
```

### 7. Finish

Run lint and tests (backend). The Makefile is Windows-only (`.venv/Scripts/python.exe`); on macOS/Linux invoke `.venv/bin/python -m ruff check`, `.venv/bin/python -m mypy`, and `.venv/bin/python -m pytest` directly. Then if the response shape changed, regenerate frontend types:
```
✅ Endpoint scaffolded.
Next (frontend): cd gatherly-fe && pnpm openapi:gen   # API must be running on :8002
```

## What you must NOT do

- Skip any of the 5 guards. Even read-only endpoints need S1; owner-scoped reads must enforce S2 in the service; sensitive actions also need S3/S5.
- Return a bare model. Wrap single resources in `DataResponse(data=...)`.
- Put business logic in the router, or call `db.execute()` from it.
- Raise `HTTPException` from a service — raise a typed error from `gatherly.errors`.
- Use `db.commit()` in a repository, or raw interpolated SQL.
- Forget to register the router in `main.py`, or to add the new capability to `gatherly/rbac.py` if one is needed.
