# Gatherly — Conference Demo Starter Pack

> Companion project for the talk **"Orchestrer l'intelligence : vers des systèmes multi-agents autonomes et collaboratifs"** — Montréal · 18 June 2026.

**Gatherly** is an event-management platform: create events, invite guests, and collect RSVPs in real time — waitlists, +1s, dietary needs, and door check-in. What makes it a demo vehicle is that the system **audits its own events** — it checks each event's readiness, flags what's missing, and drafts the fixes — showcasing multi-agent orchestration on a real, working product instead of a toy.

🔗 **Live frontend:** https://gatherly-events-app.netlify.app

---

## What's in this Starter Pack

| Path | Purpose |
|------|---------|
| `CLAUDE.md` | Project contract — domain model, the 5 security guards, conventions, AC-1…AC-6 framework |
| `WORKFLOW.md` | Team workflow — the `plan → explore → implement → test → review → audit → commit → PR` loop |
| `.claude/settings.json` | Team permissions, hooks, deny-list |
| `.claude/skills/*/SKILL.md` | 18 slash-command skills — one specialist, one contract each |
| `gatherly-be/` | FastAPI backend (Python 3.12) |
| `gatherly-fe/` | Next.js 14 frontend |
| `deploy/` | Terraform (GCP) + deployment runbooks |

---

## The Demo — Three Moments

1. **Total orchestration** — `/implement` builds a full feature live: *auto-promote the next waitlisted guest when a confirmed guest cancels*. One command; the orchestrator routes ~7 specialists through plan → tests → audit → PR, with acceptance criteria defined up front and verified at the end.
2. **Resilience** — a pre-staged bug (a guest could read **another host's** guest list) is caught by `/audit-security` in seconds. The inner fix loop restores the missing ownership check, re-audits clean, and commits — zero humans involved. The system catches its own mistake before anyone sees the code.
3. **Full autonomy** — `/work-findings` runs **overnight on 8 readiness gaps**: 7 PRs opened (missing locations, capacity waitlists, reminder emails, cover images, schedule blocks, dietary summaries) and **1 escalation** — a double-booked venue, marked `needs-human` with a full trace after 3 failed attempts. The escalation is the point.

---

## Tech Stack

- **Backend:** FastAPI + Python 3.12 (`gatherly-be/`) — deployed on GCP Cloud Run
- **Frontend:** Next.js 14 + Tailwind + shadcn/ui (`gatherly-fe/`) — deployed on Netlify
- **Database:** SQLite by default (zero infra); Postgres in production (Cloud SQL). Tenant isolation by owner scoping
- **Auth:** JWT access/refresh + Google Sign-In
- **LLM:** Anthropic Claude Sonnet 4.6 (agent-powered event audits)
- **CI/CD:** GitHub Actions (CI + backend → Cloud Run); Netlify (frontend)

---

## Quick Start

```bash
git clone https://github.com/Bmbsolution/genai-demo.git gatherly
cd gatherly

# Backend — FastAPI on SQLite, no external infra (port 8002)
cd gatherly-be
python3 -m venv .venv && .venv/bin/python -m pip install -e .
.venv/bin/python -m gatherly.scripts.seed
.venv/bin/python -m uvicorn gatherly.main:app --port 8002 &

# Frontend (port 3000)
cd ../gatherly-fe && pnpm install && pnpm dev &

claude                               # skills auto-load from .claude/skills/
```

Open `http://localhost:3000`. Demo host: `host@gatherly.app` / `gatherly-host`.
(Or just run `/run-app` inside `claude` to launch and drive both.)

---

## The Pattern, Not Just the App

The point isn't Gatherly — it's the **orchestration around it**: one `CLAUDE.md` the agents read every session, a folder of single-contract skills, machine-checkable acceptance criteria, and honest stopping (3 retries → escalate to a human). You don't need a multi-agent platform — you need a `CLAUDE.md` and a folder of skills.

**Start Monday:** pick one workflow you do weekly (PR review, triage, audit), write its `SKILL.md` (~50 lines), use it on Tuesday's real work, then iterate the *skill* — not the prompt. The asset compounds with every use.

---

## License

Internal demo project. The code is not for redistribution, but the workflow patterns — `CLAUDE.md`, the skills, the acceptance-gate model — are meant to be shared and reused.
