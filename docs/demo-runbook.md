# Conference Demo Runbook — "Orchestrer l'intelligence"

Stage operator's cheat sheet for the **Gatherly** live demo (the relatable
event-RSVP app). 20-minute slot, deck: `orchestrer-intelligence-gatherly.pptx`.

> **Golden rule:** every live moment has a recorded fallback. If anything
> stalls past ~15s, cut to the recording and keep narrating. The audience
> remembers the story, not the spinner. Never debug on stage.

---

## 0. Why Gatherly (not ServiceCat)

The demo app is **Gatherly** — plan events, invite guests, collect RSVPs —
because a mixed (non-technical + technical) room grasps it in one sentence and
the stakes are visceral: *"a guest could see another guest's email."* Same
engineering rigor as ServiceCat (the 5 guards, tests, the loop), relatable
domain. Zero external infra (SQLite), so it runs with one command on stage.

---

## 1. Pre-flight (night before)

- [ ] **Record a fallback** of every live moment (Moment 1 build, Moment 2 fix).
- [ ] Dry-run the whole demo once, stopwatch each moment.
- [ ] Clean git tree on `main`; note the known-good commit on a sticky.
- [ ] Charge laptop, silence notifications, terminal + editor font ≥18pt.

## 2. Bring-up (T-10 min, from repo root)

```bash
# Backend on :8002 (SQLite, seeded). Uses the shared ServiceCat venv.
cd gatherly-be && PYTHONPATH=src ../servicecat-be/.venv/Scripts/python.exe -m gatherly.scripts.seed
PYTHONPATH=src ../servicecat-be/.venv/Scripts/python.exe -m uvicorn gatherly.main:app --port 8002 &

# Frontend on :3002 (.env.local already points NEXT_PUBLIC_API_URL at :8002).
cd ../gatherly-fe && pnpm dev -p 3002
```

**Smoke test (T-5):**
```bash
curl -s http://127.0.0.1:8002/health      # {"data":{"status":"ok",...}}
```
Open `http://localhost:3002/login`, sign in once to prime, then log out.
**Demo host:** `host@gatherly.app` / `gatherly-host`.

---

## 3. Slide 14 — set the stage (narration)

"Gatherly — the kind of app you'd actually ship: events, guest lists, RSVPs.
The agents are going to *extend* it and *audit* it, live."

---

## 4. Moment 1 (LIVE) — total orchestration · slide 15 · ~7 min

One command builds a complete, visible feature:
```
/implement add a +1 and dietary-preferences field to the RSVP form
```
Narrate the loop (plan → explore → implement → test → review → audit → commit →
PR). Payoff the audience SEES: a new "+1 / dietary" field appears on the guest
RSVP page and in the host's guest list.

**Landing line:** "One orchestrator, seven specialists — it never asked me which
one to use. That's the difference between an assistant and a system."

**Fallback:** cut to last night's recording.

## 4b. Moment 2 (LIVE) — resilience · slide 16 · ~3 min

The most persuasive moment for a mixed room: **the system catches its own
privacy leak.** Pre-staged on a branch.

```bash
git checkout demo/guest-privacy-bug      # ownership check dropped from the guest list
cd gatherly-be && PYTHONPATH=src ../servicecat-be/.venv/Scripts/python.exe -m pytest tests/test_guest_isolation.py
# -> test_other_host_cannot_read_guest_list FAILS: 200 instead of 404 (a guest leak)
```
Let the inner fix loop restore the ownership check, re-run → green. Then:
```bash
git checkout main                        # back to the correct code
```
**Stakes everyone feels:** "one host could read another host's guests — names,
emails. The system caught it before any human saw the code."

## 5. Moment 3 (RECORDED) — full autonomy · slides 17–18 · ~3 min

Play the timelapse: overnight, the agent fixes **event-readiness gaps** across
events — missing locations, capacity waitlists, unsent reminders. Result:
**7 fixes opened, 1 escalation** (a double-booked venue → `needs-human`).
**The escalation is the point** — a system that knows what it can't do.

---

## 6. Reset between runs

```bash
git checkout main && git reset --hard <known-good-commit>
cd gatherly-be && rm -f gatherly.db && PYTHONPATH=src ../servicecat-be/.venv/Scripts/python.exe -m gatherly.scripts.seed
```

## 7. Fallback cheat sheet

| Symptom | Fix on stage |
|---|---|
| FE shows network/CORS error | API not on :8002 — cut to recording |
| `/implement` hangs or wanders | cut to recording; never debug live |
| Login rejects creds | reseed (Section 6), backstage only |
| Port :3002 in use | kill the stray node PID, relaunch — backstage |

## 8. Quick reference

| Thing | Value |
|---|---|
| Login | `host@gatherly.app` / `gatherly-host` |
| Frontend | http://localhost:3002 |
| Backend API | http://127.0.0.1:8002 (health: `/health`) |
| Bug branch | `demo/guest-privacy-bug` (Moment 2) |
| Deck | `orchestrer-intelligence-gatherly.pptx` (26 slides) |
| Repo / starter pack | github.com/Bmbsolution/genai-demo |
