# Gatherly — backend

Plan events, invite guests, collect RSVPs. FastAPI + SQLAlchemy (async) on
SQLite — zero external infra, one command to run.

This is the **demo application** for the "Orchestrer l'intelligence" talk: a
relatable domain (everyone understands an RSVP app) carrying real engineering
rigor — the 5 security guards, repository/service layering, typed errors, and the
response envelope.

## Run

```bash
# from gatherly-be/ — create a venv and install once:
#   python3 -m venv .venv && .venv/bin/python -m pip install -e .
.venv/bin/python -m gatherly.scripts.seed          # create the demo host + events
.venv/bin/python -m uvicorn gatherly.main:app --port 8002
```

> The `Makefile` targets assume a Windows interpreter path; on macOS/Linux call
> `.venv/bin/python` directly as shown above. Or just run `/run-app`.

Health: `GET http://127.0.0.1:8002/health`.
Demo host: `host@gatherly.app` / `gatherly-host`.

## The five guards

| Guard | Where |
|-------|-------|
| S1 Auth | `deps.get_current_user` (Bearer access token) |
| S2 Tenant isolation | service/repository layer — every host read scoped to `owner_id` (`EventRepository.get_for_owner`) |
| S3 RBAC | `deps.require_capability` (`rbac.ROLE_CAPABILITIES`) |
| S4 Rate limit | `deps.rate_limit` (in-memory fixed window) |
| S5 Audit log | `deps.audit_action` (append-only `audit_logs`) |

## Test

```bash
.venv/bin/python -m pytest        # functional + isolation + rsvp suites
.venv/bin/python -m ruff check src tests && .venv/bin/python -m mypy --strict src
```
