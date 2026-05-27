# servicecat-be

FastAPI backend for ServiceCat. Python 3.12+, SQLAlchemy 2 (async), Alembic,
PostgreSQL 16 with Row-Level Security.

## Layout

```
src/servicecat/
  config.py        # env-driven settings
  db.py            # async engine, session factory, RLS context helper
  deps.py          # the 5 security guards (S1-S5)
  errors.py        # typed domain exceptions
  http.py          # shared httpx.AsyncClient (rule S8)
  main.py          # FastAPI app factory
  models/          # SQLAlchemy ORM (Base + mixins)
  schemas/         # Pydantic (ServiceCatBaseModel)
  routers/ services/ repositories/ scorecards/ workers/
migrations/        # Alembic (async env)
tests/
```

## Row-Level Security (workspace isolation)

Tenant isolation is enforced in the database, not just the application. Every
workspace-scoped table has a `workspace_id` and an RLS policy:

```sql
CREATE POLICY workspace_isolation ON <table>
    USING      (workspace_id = NULLIF(current_setting('app.workspace_id', true), '')::uuid)
    WITH CHECK (workspace_id = NULLIF(current_setting('app.workspace_id', true), '')::uuid);
```

`NULLIF(..., '')` makes an unset *or* blank GUC evaluate to `NULL`, so the
default is **deny** (zero rows), never an error.

### Why a separate role

The bootstrap database user (`servicecat`) is a **superuser**, and Postgres
superusers and table owners *bypass* RLS — even with the policy in place. So the
app never runs workspace queries as that user. Migration `0001` provisions a
non-privileged `servicecat_app` role, and every request does, inside its
transaction:

```sql
SET LOCAL ROLE servicecat_app;                          -- drop the bypass
SELECT set_config('app.workspace_id', '<uuid>', true);  -- pin the workspace
```

Both are transaction-local (`SET LOCAL` / `is_local => true`), so a pooled
connection never leaks workspace context to the next request. This is wrapped by
`servicecat.db.set_workspace_context(session, workspace_id)`; the
`get_current_workspace` guard (F-03) calls it per request. Tables also get
`FORCE ROW LEVEL SECURITY` as defence-in-depth.

The migration also `GRANT`s `servicecat_app` to the connecting user, so `SET
ROLE` keeps working if that user is later stripped of `SUPERUSER`. Creating or
deleting a *workspace* is a privileged operation (you can't be "in" a workspace
that doesn't exist yet), so the app role holds only `SELECT, UPDATE` on
`workspaces` — provisioning happens via an admin path.

### Adding a new scoped table

Add the columns in your model, then in the migration enable RLS and grant the
app role (the `script.py.mako` template carries the exact snippet). RLS
behaviour is regression-tested in `tests/test_rls.py`.

## Local development

```bash
docker compose up -d postgres redis      # from the repo root
make install                             # editable install + dev tools
make migrate                             # alembic upgrade head
make dev                                 # uvicorn on :8000
```

On Windows without `make`, call the underlying commands directly, e.g.
`.venv/Scripts/python -m pytest`.

## Checks (AC-5)

```bash
make lint      # ruff check + ruff format --check + mypy
make test      # pytest
make test-cov  # pytest with coverage, fails under 80%
```
