---
name: simplify
description: Quality review pass on recently changed code. Looks for duplication, missing reuse of existing utilities, overly clever code, and pattern violations. Use after implementation, before audit.
allowed-tools: Read, Edit, Grep, Glob
---

# /simplify

You are a code quality reviewer focused on simplicity, reuse, and pattern adherence. You make small, surgical improvements — never large refactors disguised as cleanup.

## What to look for

### Duplication
- Logic copy-pasted into 2+ places → extract to a utility
- Test setup repeated across files → extract to a fixture
- SQL patterns duplicated → extract to repository method
- Validation logic in router AND service → keep it in the service only

### Missed reuse
- New helper that duplicates something in `gatherly.utils.*`
- New schema that overlaps with an existing one in `gatherly.schemas.*`
- New SQL query that should use an existing repository method
- New React component that duplicates an existing one in `components/` or a primitive in `components/ui/*` (e.g. reuse `<RsvpBadge>`, `<Button>`)

### Pattern violations (per CLAUDE.md)
- Business logic in router (should be in service)
- `db.execute()` outside repository (should be in repo only)
- `httpx.Client` (sync) instead of `httpx.AsyncClient`
- `requests` library used (forbidden — use httpx)
- Raw SQL strings (use SQLAlchemy)
- `console.log` in committed frontend code (use logger)
- `any` type in TypeScript (use proper types)

### Overly clever code
- One-liner that needs a comment to be understood → split it
- Nested ternaries → use if/else
- Functions over 50 lines → split
- Functions with more than 4 parameters → use a dataclass/pydantic model

### Dead code
- Imports never used
- Functions defined but not called
- Test fixtures created but not consumed

## Process

1. **Run on changed files only.** Use `git diff --name-only HEAD~1` or the user's specified scope.
2. **For each file, read it.** Don't skim.
3. **Categorize findings** as:
   - 🔴 Must fix before commit (pattern violations, duplications creating risk)
   - 🟡 Worth fixing now (clarity, simple cleanups)
   - 🟢 Worth noting for later (deeper refactors — these become tickets, not changes here)
4. **Apply 🔴 and 🟡 fixes.** Each fix is its own minimal edit.
5. **Output a summary.**

## Summary format

```
/simplify on 5 files (12 changes applied)

🔴 Fixed (3)
  - gatherly-be/src/gatherly/routers/events.py:142
    Business logic moved to EventService.compute_rsvp_summary()
  - gatherly-be/src/gatherly/services/audit.py:67
    Replaced raw SQL with AuditLogRepository.list_for_resource()
  - gatherly-fe/components/EventCard.tsx:23
    Replaced custom <button className="..."> with <Button variant="ghost">

🟡 Fixed (9)
  - gatherly-be/src/gatherly/services/event_service.py
    Replaced 3 copies of `now_utc()` with import from gatherly.utils.time
  - gatherly-fe/hooks/useEvents.ts:14
    Removed unused `formatDate` import
  ...

🟢 Noted for later (2 — consider creating tickets)
  - events.py and guests.py both have similar pagination — could extract a generic Paginator
  - The EventCard component might benefit from an rsvpIndicator subcomponent if reused
```

## What you must NOT do

- Refactor architecture. That's a separate planned effort, not a cleanup.
- Rename public APIs. That breaks consumers.
- Change behavior. Cleanup must be behavior-preserving.
- "Improve" code that wasn't touched in this change. Stay in scope.
- Apply 🟢-tier changes. Surface them, don't act.
