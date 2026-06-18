---
name: run-app
description: Launch and drive the Gatherly app locally (FastAPI backend + Next.js frontend) and verify it renders. Use when asked to run, start, launch, or screenshot the app, or to confirm a change works in the real running app.
allowed-tools: Bash, Read, ToolSearch, mcp__plugin_playwright_playwright__browser_navigate, mcp__plugin_playwright_playwright__browser_snapshot, mcp__plugin_playwright_playwright__browser_take_screenshot, mcp__plugin_playwright_playwright__browser_click, mcp__plugin_playwright_playwright__browser_fill_form
---

# /run-app

Launch **Gatherly** — the runnable demo app — and drive it to a point where a
user would see something. "The app" is `gatherly-be/` + `gatherly-fe/`.

> The backend runs on **SQLite — no Docker, no Postgres, no Redis needed.**

## Prereqs (verified on macOS / darwin)

- Python 3.12, `pnpm`, `node` on PATH. No Docker required.
- **The Makefile is Windows-only** (`PY ?= .venv/Scripts/python.exe`). Do NOT
  use `make run`/`make seed` on macOS/Linux — invoke the venv python directly.

## Launch

### Backend — FastAPI on SQLite, port 8002

```bash
cd gatherly-be
python3 -m venv .venv                       # first time only
.venv/bin/python -m pip install -q -e .      # first time only
.venv/bin/python -m gatherly.scripts.seed    # seed demo host + events (idempotent)
.venv/bin/python -m uvicorn gatherly.main:app --port 8002 > /tmp/gatherly-be.log 2>&1 &
```

Smoke-test it's up:
```bash
curl -s http://127.0.0.1:8002/health        # -> {"data":{"status":"ok","environment":"local"}}
```

### Frontend — Next.js 14, port 3000

```bash
cd gatherly-fe
pnpm install                                 # first time only
pnpm dev > /tmp/gatherly-fe.log 2>&1 &
```

Wait until `curl -s -o /dev/null -w "%{http_code}" http://localhost:3000` is `200`
(first compile can take a few seconds).

## Drive it (don't just launch it)

Use the Playwright MCP browser tools (load via ToolSearch:
`select:mcp__plugin_playwright_playwright__browser_navigate,...`). **Look at the
screenshot — a blank frame is a failed launch.**

1. `browser_navigate` → `http://localhost:3000` — marketing landing renders
   (hero + a live event card). The big light gaps mid-page are scroll-reveal
   sections animating in on viewport entry — **not** an error.
2. Authenticated flow:
   - `browser_navigate` → `http://localhost:3000/login`
     (the route is **`/login`**, NOT `/sign-in` — `/sign-in` 404s).
   - `browser_snapshot`, then `browser_fill_form` Email + Password, click Sign in.
   - **Demo creds:** `host@gatherly.app` / `gatherly-host`
   - Lands on `/events` → 2 seeded events (*Product Launch Party* draft,
     *Team Offsite 2026* published). Click an event → detail page shows Insights,
     the **Event readiness** self-audit checklist (the demo centerpiece), and the
     guest list with RSVP statuses.

## Stop

```bash
pkill -f "uvicorn gatherly.main:app"
pkill -f "next dev"
```

## Gotchas that recur

- **Screenshots** land in `gatherly-fe/.playwright-mcp/` but the tool may report
  a relative path; if `Read` fails, `find . -name "<file>.png"` to locate it.
- **Controlled inputs**: use `browser_fill_form`/`browser_type`, not raw value
  assignment — React's onChange must fire.
- Backend and frontend ports (8002 / 3000) are fixed; the FE's API client and
  `openapi:gen` script both point at `http://127.0.0.1:8002`.
