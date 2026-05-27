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
