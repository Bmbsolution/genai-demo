# Conference Demo Runbook — "Orchestrer l'intelligence"

Stage-ready script for the ServiceCat live demo. **30-minute talk**, deck:
`orchestrer-intelligence.pptx`. This is the operator's cheat sheet — exact
commands, timings, what to say, and what to do when something fails.

> **Golden rule of live demos:** every live moment has a recorded fallback.
> If anything stalls past ~15s, cut to the recording and keep narrating. The
> audience remembers the story, not the spinner.

---

## 0. Timing map (matches the trimmed deck)

| Block | Slides | Budget |
|-------|--------|--------|
| The plateau (intro) | 1–6 | 3 min |
| The four pillars | 7–22 (6 hidden) | 8 min |
| **The demo** | 23–30 (27–28 hidden) | **12 min** |
| Patterns for Monday | 31–40 | 6 min |
| Q&A | 41–42 | ~1 min |

Demo internal budget (12 min): **Moment 1 live ≈ 7 min**, **Moment 2 (autonomy)
recorded ≈ 3 min**, **2 min slack** for narration/transitions.

> Optional upgrade: if you can find ~3 min, run the **resilience** scenario
> (Section 4b) live between the two — it's the most persuasive *and* the most
> deterministic demo. It currently lives on hidden slides 27–28; un-hide them.

---

## 1. Pre-flight (night before)

- [ ] **Record a fallback** of every live moment (Moment 1, and resilience if used). Screen-record at the resolution you'll present at.
- [ ] Pull latest, clean branch: `git -C ServiceCat status` shows a clean tree on a known commit.
- [ ] Dry-run the **whole** demo once end to end, timing each moment with a stopwatch.
- [ ] Snapshot a known-good DB state for fast reset (Section 6).
- [ ] Charge laptop, disable notifications/Slack/email, set terminal + editor font large (≥18pt).
- [ ] Confirm conference Wi-Fi or tether a hotspot — the orchestrator needs the API.

## 2. Pre-flight (T-15 min, at the venue)

Bring the stack up in this order. All commands are PowerShell from the repo root.

```powershell
# 1. Datastores (Postgres :5440, Redis :6380)
docker compose up -d
docker compose ps   # both should read "healthy"

# 2. Migrate (only if a fresh volume)
Push-Location servicecat-be
.\.venv\Scripts\python.exe -m alembic upgrade head
Pop-Location

# 3. Backend API on :8001  (NOT :8000 — that port is taken by another project)
Push-Location servicecat-be
$env:SERVICECAT_DATABASE_URL='postgresql+asyncpg://servicecat:servicecat@localhost:5440/servicecat'
Start-Process .\.venv\Scripts\python.exe '-m uvicorn servicecat.main:app --port 8001'
Pop-Location

# 4. Arq worker (runs scorecards; clones repos on the host)
Push-Location servicecat-be
$env:SERVICECAT_DATABASE_URL='postgresql+asyncpg://servicecat:servicecat@localhost:5440/servicecat'
Start-Process .\.venv\Scripts\python.exe '-m arq servicecat.workers.scorecard.WorkerSettings'
Pop-Location

# 5. Frontend on :3001  (.env.local must point NEXT_PUBLIC_API_URL at :8001)
pnpm --dir servicecat-fe dev -p 3001

# 6. Demo repo for scorecard runs (temp cleanups delete it)
$repo = "$env:TEMP\servicecat-demo-repo"
if (-not (Test-Path "$repo\.git")) {
  New-Item -ItemType Directory -Force $repo | Out-Null
  Push-Location $repo; git init -q; 'print("hi")' | Out-File -Encoding utf8 app.py
  git add .; git -c user.email='dev@servicecat.local' -c user.name='dev-servicecat' commit -q -m init
  Pop-Location
}
```

**Smoke test (T-5 min):**
```powershell
(Invoke-WebRequest http://127.0.0.1:8001/health -UseBasicParsing).Content   # {"data":{"status":"ok"...}}
(Test-NetConnection localhost -Port 3001 -WarningAction SilentlyContinue).TcpTestSucceeded   # True
```
Then open `http://localhost:3001/login` and sign in once to prime the cache:
**`admin@servicecat.local` / `servicecat-admin`**. Log back out for the demo.

---

## 3. Slide 23–24 — set the stage (narration, no commands)

- Slide 23: "ServiceCat — an internal developer portal that audits itself."
- Slide 24 (architecture): point at the three layers (catalog → audit worker →
  PR agent). Stack line: FastAPI · Next.js · Postgres+RLS · Claude Sonnet 4.6.
- One sentence to set up the demo: *"Everything you're about to see runs on this
  real codebase — same repo, same guards, same tests."*

---

## 4a. Moment 1 (LIVE) — Total orchestration  ·  slides 25–26  ·  ~7 min

**Goal the audience should take away:** one orchestrator drove 7 specialists
through plan→PR and *never asked which one to use*.

In Claude Code at the repo root, run:

```
/implement add scorecard versioning with side-by-side comparison
```

**Beats to narrate as they scroll by** (don't read the output — point at the shape):
1. **Plan** — acceptance criteria AC-1…AC-6 written *before* any code.
2. **Explore** — it reads existing patterns instead of guessing.
3. **Implement** — repository → service → router, the 5 guards on the endpoint.
4. **Test** — unit + router + security tests, ≥80% on new code.
5. **Review** — `/review-pr` bug-hunts; ideally it catches something here.
6. **Audit** — `/audit-security` confirms the 5 guards + S6–S8.
7. **Commit + PR** — opens a PR, CI goes green.

**Landing line (slide 26):** *"Eight minutes. Seven specialists. The orchestrator
picked each one — I never did. That's the difference between an assistant and a
system."*

**If it stalls / goes sideways (>15s of nothing, or a wrong turn):**
- Say: *"This is a live model on conference Wi-Fi — here's the run I captured last night,"* and cut to the recording.
- Do **not** debug on stage. The fallback IS the plan.

**Smaller-scope alternative** (if you want a tighter, more predictable live run):
```
/new-endpoint GET /services/{id}/score-history
```
Scaffolds one guarded endpoint + tests in ~3–4 min — lower wow, lower risk.

---

## 4b. Resilience (LIVE, OPTIONAL but recommended)  ·  slides 27–28  ·  ~3 min

The most persuasive moment for a skeptical engineering crowd: **the system
catches its own security mistake before a human sees the code.** Near-deterministic
because the audit reliably flags a missing guard.

**Pre-stage (before the talk):** on a throwaway branch, add an endpoint that is
*missing the S3 RBAC guard* (`require_capability(...)`). Keep the diff tiny and
on screen. Example shape:

```python
@router.post("/services/{id}/promote")
async def promote(
    id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),          # S1 ✓
    ws: Workspace = Depends(get_current_workspace),  # S2 ✓
    # S3 require_capability(...) MISSING  ← the planted bug
    _rl = Depends(rate_limit(per_minute=10)),        # S4 ✓
    _audit = Depends(audit_action("service.promote")),  # S5 ✓
):
    ...
```

**Live on stage:**
```
/audit-security
```
- It flags the **S3** violation in seconds (a viewer could trigger a privileged action).
- The inner fix loop adds the missing `require_capability(...)`.
- Re-run `/audit-security` → clean → commit.

**Landing line:** *"Three failed attempts and it escalates; an unfixable audit
blocks the commit. The system policed itself — zero humans in the loop."*

**Authentic upgrade:** instead of a planted bug, tell the **real** story from this
project's hardening week (see Section 8) — a genuine bug the loop caught is more
credible than a staged one.

---

## 5. Moment 2 of 2 (RECORDED) — Full autonomy  ·  slides 29–30  ·  ~3 min

Play the **timelapse** (don't run live — it's an 8-hour job).

- Cue: *"Eight findings in the queue, eight hours overnight, no supervision."*
- Result slide: **7 PRs opened, 1 escalation** (`needs-human`).
- **The point is the escalation, not the 7 successes:** the agent tried 3× to
  refactor a config loader, failed honestly, left a full trace, tagged the team
  on Slack, and moved on.
- Landing line: *"An agent that knows what it can't do is the only one worth
  deploying."*

If you have the autonomous worker wired and want to *show* it (not run to
completion), you can kick off and immediately cut away:
```
/work-findings
```

---

## 6. Reset between rehearsal and showtime

Make every run identical. After a dry-run, restore state:

```powershell
# Drop demo branches / uncommitted work created by /implement
git -C ServiceCat checkout main
git -C ServiceCat branch | Select-String -NotMatch '\* main' | ForEach-Object {
  git -C ServiceCat branch -D ($_.ToString().Trim())
}
git -C ServiceCat reset --hard <known-good-commit>

# Reseed the database to a known catalog + findings
Push-Location servicecat-be
$env:SERVICECAT_DATABASE_URL='postgresql+asyncpg://servicecat:servicecat@localhost:5440/servicecat'
.\.venv\Scripts\python.exe -m servicecat.scripts.seed
Pop-Location

# Recreate the demo repo (see Section 2, step 6)
```

> Keep `<known-good-commit>` written on a sticky note. Re-stage the resilience
> branch (4b) after each reset if you're using that moment.

---

## 7. Fallback cheat sheet

| Symptom | Cause | Fix on stage |
|---|---|---|
| FE shows CORS / network error | API not on `:8001`, or `.env.local` wrong | Don't debug — cut to recording. (Backstage: API must be `:8001`; `:8000` is another project.) |
| `wslrelay` owns a port | a Docker container holds it | `docker ps` — it's not the ServiceCat API. Cut to recording. |
| Scorecard run "FAILED: not a git repository" | temp demo repo got cleaned | Recreate it (Section 2 step 6) — but mid-talk, cut to recording. |
| `/implement` hangs or wanders | model/network on the day | Cut to recording. Never debug live. |
| Login rejects credentials | DB not seeded | Reseed (Section 6). Backstage only. |
| EADDRINUSE on 3001 | orphaned node | Kill the specific node PID on 3001, relaunch. Backstage only. |

---

## 8. Real war stories (use these for authenticity)

During this project's hardening week, by actually *running* ServiceCat (not just
reading code), the agent loop caught real issues — far more credible to narrate
than a staged break:

- **Password leaked into the URL** — submitting the login form before React
  hydrated fell back to a native GET, putting the password in the query string.
  Caught by clicking through in a *real browser*, not by static review.
- **Findings duplicated across runs** — every scorecard re-run appended rows; a
  detail page showed 25 findings for 5 criteria. Fixed to scope to the latest
  completed run.
- **Dead on arrival** — the app's API was pointing at a port another project's
  container had taken; the "CORS error" was a different service answering. The
  agent debugged the *environment*, not just the code.

These map cleanly onto the talk's thesis: the value isn't raw intelligence, it's
the orchestration, the guards, and knowing when to stop.

---

## 9. Quick reference

| Thing | Value |
|---|---|
| Login | `admin@servicecat.local` / `servicecat-admin` |
| Frontend | http://localhost:3001 |
| Backend API | http://127.0.0.1:8001 (health: `/health`) |
| Postgres / Redis | localhost:5440 / localhost:6380 (docker compose) |
| Demo repo | `%TEMP%\servicecat-demo-repo` |
| Git identity | `dev-servicecat <dev@servicecat.local>` |
| Deck | `orchestrer-intelligence.pptx` (30 min) |
| Key skills | `/implement` · `/audit-security` · `/review-pr` · `/work-findings` · `/new-endpoint` |
