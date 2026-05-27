---
name: new-endpoint
description: Scaffold a new FastAPI endpoint with all 5 security guards, repository pattern, service layer, schemas, and tests. Use when adding any HTTP endpoint to the backend.
user-invocable: true
allowed-tools: Read, Write, Edit, Bash, Grep
context: main
agent: general-purpose
---

# /new-endpoint

You scaffold a complete FastAPI endpoint following the project's layered architecture. The endpoint is non-negotiably wired with all 5 security guards.

## Invocation

```
/new-endpoint POST /scorecards/{id}/runs
/new-endpoint GET /services/{id}/dependencies
/new-endpoint PATCH /findings/{id} --capability=finding:assign
```

## What you produce

### 1. The route handler
File: `servicecat-be/src/routers/<resource>.py`

```python
from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession
from servicecat.deps import (
    get_db, get_current_user, get_current_workspace,
    require_capability, rate_limit, audit_action
)
from servicecat.schemas.scorecard import ScorecardRunCreateRequest, ScorecardRunResponse
from servicecat.services.scorecard_service import ScorecardService

router = APIRouter(prefix="/api/v1/scorecards", tags=["scorecards"])

@router.post(
    "/{scorecard_id}/runs",
    status_code=status.HTTP_202_ACCEPTED,
    response_model=ScorecardRunResponse,
)
async def trigger_scorecard_run(
    scorecard_id: UUID,
    payload: ScorecardRunCreateRequest,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
    ws: Workspace = Depends(get_current_workspace),
    _cap = Depends(require_capability("scorecard:run")),
    _rl = Depends(rate_limit(per_minute=10, key="scorecard:run")),
    _audit = Depends(audit_action("scorecard.run.trigger")),
) -> ScorecardRunResponse:
    service = ScorecardService(db)
    run = await service.trigger_run(
        workspace_id=ws.id,
        scorecard_id=scorecard_id,
        target_service_ids=payload.target_service_ids,
        triggered_by=user.id,
    )
    return ScorecardRunResponse.model_validate(run)
```

### 2. The Pydantic schemas
File: `servicecat-be/src/schemas/<resource>.py`

```python
from servicecat.schemas.base import ServiceCatBaseModel
from uuid import UUID
from typing import List

class ScorecardRunCreateRequest(ServiceCatBaseModel):
    target_service_ids: List[UUID]

class ScorecardRunResponse(ServiceCatBaseModel):
    id: UUID
    scorecard_id: UUID
    status: str
    triggered_by: UUID
    created_at: datetime
```

### 3. The service layer
File: `servicecat-be/src/services/<resource>_service.py`

```python
class ScorecardService:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db
        self.run_repo = ScorecardRunRepository(db)

    async def trigger_run(
        self,
        workspace_id: UUID,
        scorecard_id: UUID,
        target_service_ids: List[UUID],
        triggered_by: UUID,
    ) -> ScorecardRun:
        # Validate scorecard exists in workspace
        # Validate all target services exist in workspace
        # Enqueue background job
        # Persist run record
        ...
```

### 4. The repository
File: `servicecat-be/src/repositories/<resource>_repository.py` — thin wrapper around SQLAlchemy queries. Only place `db.execute()` and `db.commit()` are called.

### 5. The tests
Three test files:
- `tests/routers/test_<resource>.py` — HTTP-level tests
- `tests/services/test_<resource>_service.py` — service unit tests
- `tests/security/test_<resource>_security.py` — guard-by-guard verification

Required test cases for every endpoint:
| Test | What it verifies |
|------|------------------|
| `test_happy_path` | 2xx response with valid input |
| `test_unauthenticated_returns_401` | S1 |
| `test_other_workspace_returns_404` | S2 (cross-workspace access denied) |
| `test_viewer_returns_403` | S3 (capability check) |
| `test_rate_limit_returns_429` | S4 (only when rate limit is tight) |
| `test_creates_audit_log_entry` | S5 |
| `test_invalid_payload_returns_422` | Pydantic validation |
| `test_resource_not_found_returns_404` | Path params |

### 6. Router registration
Add the new router to `servicecat-be/src/main.py`:

```python
from servicecat.routers import scorecards
app.include_router(scorecards.router)
```

### 7. OpenAPI types regen reminder
Output a final reminder:
```
✅ Endpoint scaffolded.
Next: regenerate frontend types with `pnpm openapi:gen`.
```

## What you must NOT do

- Skip any of the 5 guards. Even read-only endpoints need S1, S2, S5.
- Put business logic in the router. Routers are thin.
- Skip the tests. An endpoint without tests is not done.
- Forget to register the router in `main.py`.
- Use raw SQL strings. Use SQLAlchemy.
