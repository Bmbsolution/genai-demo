# Gatherly — backend

Plan events, invite guests, collect RSVPs. FastAPI + SQLAlchemy (async) on
SQLite — zero external infra, one command to run.

This is the **demo application** for the "Orchestrer l'intelligence" talk: a
relatable domain (everyone understands an RSVP app) that still carries the same
engineering rigor as ServiceCat — the 5 security guards, repository/service
layering, typed errors, and the response envelope.

## Run

```bash
# from gatherly-be/, using the shared ServiceCat venv interpreter
python -m gatherly.scripts.seed          # create the demo host + events
python -m uvicorn gatherly.main:app --port 8002
```

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
python -m pytest          # functional + isolation + rsvp suites
make lint                 # ruff + ruff format + mypy --strict
```
