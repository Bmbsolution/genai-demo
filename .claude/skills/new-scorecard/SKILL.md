---
name: new-scorecard
description: Add a new readiness check to the Gatherly event-readiness checklist (a ReadinessCheck in InsightsService.get_readiness + tests). Use when the user asks to add a new readiness signal like has_guests, within_capacity, has_location, published, or a custom one.
allowed-tools: Read, Write, Edit, Grep, Glob, Bash
---

# /new-scorecard

You add a new readiness check to Gatherly's event-readiness checklist. A check is a **pure-code signal**: it evaluates one fact about an event (and its guest list) and produces a pass/fail `ReadinessCheck`. There is **no** per-check DB table, no seed migration, and no UI config form — read `gatherly-be/src/gatherly/services/insights.py`; `InsightsService.get_readiness` is the canonical reference, and `ReadinessCheck` / `EventReadiness` define the contract.

## Invocation

```
/new-scorecard has_dietary_summary
/new-scorecard within_capacity
```

## The contract (from services/insights.py — verify before writing)

- A check is a `ReadinessCheck(key, passed, severity)` appended to the `checks` list in `get_readiness`.
- `key` is a stable `snake_case` identifier (e.g. `has_guests`, `within_capacity`, `has_location`).
- `passed` is a plain `bool` computed from the `event` and its `EventInsights` (guest counts, response rate, capacity, etc.).
- `severity` is one of the strings `"high"`, `"medium"`, `"low"`.
- The roll-up is fixed: an event is `ready` **iff every high-severity check passes**. Medium/low checks never block readiness — they are advisory. Choose severity accordingly.
- `get_readiness` already proves ownership via `EventService.get(event_id, owner_id)` (404 if not the owner's event). You do not re-check ownership.

## What you produce (2 artifacts — that's all)

### 1. The check — `gatherly-be/src/gatherly/services/insights.py`

Compute the boolean from `event` / `insights`, then append one `ReadinessCheck` to the `checks` list in `get_readiness`. Match the existing checks' shape:

```python
async def get_readiness(self, *, event_id: uuid.UUID, owner_id: uuid.UUID) -> EventReadiness:
    event = await self._events.get(event_id, owner_id)  # 404 if not the owner's event
    insights = await self.get_insights(event_id=event_id, owner_id=owner_id)

    within_capacity = event.capacity is None or insights.attending <= event.capacity
    healthy_rate = (
        insights.total_guests > 0 and insights.response_rate >= _HEALTHY_RESPONSE_RATE
    )
    checks = [
        ReadinessCheck("has_guests", insights.total_guests > 0, "high"),
        ReadinessCheck("within_capacity", within_capacity, "high"),
        ReadinessCheck("has_location", bool(event.location), "high"),
        ReadinessCheck("published", event.status == "published", "medium"),
        ReadinessCheck("healthy_response_rate", healthy_rate, "medium"),
        ReadinessCheck("has_description", bool(event.description), "low"),
        ReadinessCheck("has_cover_image", bool(event.cover_image_url), "low"),
        ReadinessCheck("has_end_time", event.ends_at is not None, "low"),
        # ...your new check here
    ]
    ready = all(check.passed for check in checks if check.severity == "high")
    return EventReadiness(
        ready=ready,
        passed=sum(1 for check in checks if check.passed),
        total=len(checks),
        checks=checks,
    )
```

Keep the predicate **decidable from data already loaded** (the `event` row and `EventInsights`) — don't add new I/O. If the fact you need isn't on `EventInsights` yet, add the field there first. Pick severity honestly: `high` only for things that genuinely block an event going live (guests, capacity, location); `medium`/`low` for nice-to-haves.

### 2. Tests — `gatherly-be/tests/test_insights.py`

Mirror the existing readiness tests. Drive the `GET /api/v1/events/{id}/readiness` endpoint and assert on the check's `key`/`passed`/`severity`:

```python
async def test_readiness_flags_missing_<key>(client, sessions):
    headers = await _host(client, sessions)
    event_id = await _event(client, headers)  # the condition is NOT met
    resp = await client.get(f"/api/v1/events/{event_id}/readiness", headers=headers)
    by_key = {check["key"]: check for check in resp.json()["data"]["checks"]}
    assert by_key["<key>"]["passed"] is False

async def test_readiness_passes_<key>_when_met(client, sessions):
    headers = await _host(client, sessions)
    event_id = await _event(client, headers, ...)  # set up so the condition holds
    resp = await client.get(f"/api/v1/events/{event_id}/readiness", headers=headers)
    by_key = {check["key"]: check["passed"] for check in resp.json()["data"]["checks"]}
    assert by_key["<key>"] is True
```

## Default check ideas (offer these if the user doesn't specify)

- **high** (blocks readiness): `has_guests`, `within_capacity`, `has_location`, `has_start_time`
- **medium**: `published`, `healthy_response_rate`, `rsvp_deadline_set`
- **low**: `has_description`, `has_cover_image`, `has_end_time`, `dietary_summary_collected`

## Process

1. Confirm the check `key` (snake_case) and its severity with the user if not given.
2. Add the `ReadinessCheck` (and any new `EventInsights` field it needs), write the tests.
3. `make lint && make test` — fix until green (inner fix loop, max 3 attempts).
4. `/commit-sc` → `feat(insights): add <key> readiness check (severity <level>)`.

## What you must NOT do

- Invent a `readiness_checks` table, a seed migration, or a UI config form — none exist here.
- Add a `high`-severity check casually — it can flip events from ready to not-ready; reserve it for true blockers.
- Add new I/O inside a check — compute from the already-loaded `event` and `EventInsights`.
- Skip tests, or invent checks the user didn't approve.
