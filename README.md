# ServiceCat — Conference Demo Starter Pack

> Companion project for the talk **"Orchestrer l'intelligence : vers des systèmes multi-agents autonomes et collaboratifs"**

ServiceCat is an **Internal Developer Portal** with automated compliance scorecards, dependency graphs, and ownership-routed findings. It is designed as a demo vehicle for showcasing multi-agent orchestration patterns to a developer audience.

---

## What's in this Starter Pack

| File | Purpose |
|------|---------|
| `CLAUDE.md` | Project rules — domain, security model, conventions, AC framework |
| `WORKFLOW.md` | Team workflow guide — REPL loop, skills, PR lifecycle |
| `.claude/settings.json` | Team permissions, hooks, deny-list |
| `.claude/skills/*/SKILL.md` | 18 slash-command skills |
| `docs/SEED_BACKLOG.md` | 14 GitHub issues to seed Phase 1 |
| `docs/SEED_FINDINGS.md` | 8 findings for the autonomy demo (Moment 3) |

---

## Demo Architecture

### Three Demo Moments

1. **Total Orchestration** *(8 min)* — `/implement` builds a full feature live (scorecard versioning + comparison)
2. **Resilience** *(8 min)* — `/audit-security` catches a missing RBAC check; inner fix loop self-heals
3. **Full Autonomy** *(9 min)* — `/work-findings` runs overnight on 8 findings, opens 7 PRs, escalates 1

### Live Demo Magic

ServiceCat audits real GitHub repositories. During the talk you can:
1. Point it at a real public repo
2. Watch agents fetch, analyze, score, and produce findings live
3. Trigger `/work-findings` on a finding
4. See a real PR opened on GitHub

This is the proof the audience can click on — no smoke and mirrors.

---

## Build Timeline (~6 weeks to June 18, 2026)

| Weeks | Focus |
|-------|-------|
| 1-2 | Foundation: auth, workspaces, RBAC, service catalog, 1 working scorecard, CI green |
| 3-4 | Lifecycle: scorecard versioning, multi-scorecard, findings dashboard, Slack alerts |
| 4-5 | Discovery: dependency graph, search, templates |
| 5 | Demo rehearsal: record autonomy timelapse, record live `/implement` backup |
| 6 | Polish: 2 full dry runs, slide integration, backup videos |

---

## Tech Stack

- **Backend:** FastAPI + Python 3.12
- **Frontend:** Next.js 14 + Tailwind + shadcn/ui
- **Database:** PostgreSQL 16 with workspace RLS
- **Cache:** Redis 7
- **Workers:** Arq (Redis-backed)
- **LLM:** Anthropic Claude Sonnet 4
- **Local:** Docker Compose
- **CI:** GitHub Actions

---

## Quick Start (once the codebase is built)

```bash
git clone <your-repo> servicecat
cd servicecat
docker compose up -d                     # Postgres, Redis, Prometheus, Grafana
cd servicecat-be && make install && make migrate && make seed && make dev &
cd servicecat-fe && pnpm install && pnpm dev &
claude                                    # Skills auto-load
```

Open `http://localhost:3000`.

---

## Team Identity

When committing, Claude uses `dev-servicecat <dev@servicecat.local>`. This is set automatically by the session-start hook in `.claude/settings.json`.

---

## License

Internal demo project. Do not redistribute the codebase, but the workflow patterns are intended to be shared and reused.
