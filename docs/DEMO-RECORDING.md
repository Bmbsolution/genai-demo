# Demo recording runbook — the 3 moments

Copy-paste scripts to record each demo moment for the **"Orchestrer l'intelligence"** talk.

**How recording works:** Claude can't capture your screen — use **Win+G (Game Bar)** to record
this Claude Code window. Record **each moment as a separate clip**. Lines starting with `!` are
shell commands typed into Claude Code; everything else is a prompt to Claude.

**Recommended order:** record **M2 first** (zero prep, can't fail), then M1, then M3.

**Once per session, before anything:**
```
!git checkout main && git pull
```

> **Check your version first:** the live colored subagent panel needs **Claude Code ≥ 2.1.139**
> (`claude --version`; update with `claude update`). Rehearse the panel once so you know it renders
> on your machine — exact keys vary by version.

The specialist team shows up color-coded in the panel:
🔴 `security-auditor` · 🔵 `code-reviewer` · 🟢 `test-writer` · 🟣 `frontend-reviewer` · 🟠 `migration-reviewer`

---

## 🎬 Moment 2 — Resilience  *(ready, ~4 min)*
*The team catches itself: the security-auditor flags a planted cross-tenant leak; the fix loop heals it.*

### 1 · No prep needed — the vuln is already staged on a branch.

### 2 · ▶️ Start recording, then type these three in order:
```
!git fetch origin && git checkout demo/m2-guest-list-leak
```
```
Use the security-auditor subagent to audit this branch's changes (git diff main...HEAD) against our S1–S8 guards.
```
*(🔴 security-auditor flags the **CRITICAL S2** guest-list leak + a bonus **S5** missing-audit finding)*
```
Now fix the findings: route the endpoint back through the service layer with the owner check, add the audit guard, and re-run the security-auditor until it's CLEAN.
```

### 3 · What to say
*"The auditor is a separate specialist — read-only tools, its own context. It can't change the code and can't be argued out of a finding. It caught the leak before any human saw it — zero humans."*

### 4 · Reset for a re-take
```
!git checkout -- gatherly-be/src/gatherly/routers/guests.py
```

---

## 🎬 Moment 1 — The team assembles  *(~8 min — needs 1 prep step)*
*One command; the orchestrator builds a feature and fans out to the specialists in parallel.*

### 1 · Prep (NOT recorded) — type this prompt, wait for "done":
```
On a new branch demo/m1-live off main, remove the waitlist auto-promotion feature so /implement can rebuild it from scratch:
- in gatherly-be/src/gatherly/services/rsvp.py, delete the `_promote_from_waitlist` method AND the block that calls it (the "confirmed guest gave up their seat" check: `if was_attending and status is not RsvpStatus.YES: await self._promote_from_waitlist(event)`).
- delete tests/test_waitlist_promote.py, and remove any waitlist-promotion assertions from tests/test_event_depth.py.
Then run `make lint` to confirm it's clean. Do NOT re-add the feature — stop once the branch is clean and the feature is gone. Commit it as "demo prep: remove waitlist promotion".
```

### 2 · ▶️ Start recording, then type exactly:
```
/implement auto-promote the next waitlisted guest when a confirmed guest cancels
```

### 3 · What you'll see / say
- Plans (AC-1…AC-6) → explores → implements the promotion logic.
- **The wow:** a panel drops below your prompt with the colored specialists running **in parallel** —
  🔴 security-auditor · 🔵 code-reviewer · 🟢 test-writer. They come back green → gate passes → PR.
- Press **`Space`** on a specialist row mid-run to peek at its work, then `Esc` back.
- *Say:* "One command. This top session is the orchestrator — I never told it which specialist to use; it assembled the team and ran them at once. That's not autocomplete, that's a team."

### 4 · Reset for a re-take
```
!git checkout main && git branch -D demo/m1-live
```
…then re-run the **Prep** prompt.

---

## 🎬 Moment 3 — Full autonomy, overnight  *(~10 min, sped up ~6×)*
*The team clears a backlog unsupervised — and honestly escalates the one it can't crack.*

### 1 · Prep (NOT recorded) — type this prompt, wait for "done":
```
Prep Moment 3: create 6 small, realistic open GitHub issues in Bmbsolution/genai-demo for Gatherly backend gaps — e.g. missing input validation on an endpoint, a thin/missing test, a missing DB index, a missing rate-limit guard, an inconsistent error response. Label them so /work-issues can pick them up. Make ONE of them deliberately hard/ambiguous so the agent escalates it (marks needs-human) after 3 attempts. Then STOP — do not work them yet.
```

### 2 · ▶️ Start recording, then type exactly:
```
/work-issues
```

### 3 · What you'll see / say
- It picks the highest-priority issue, runs the full loop (with the specialist team), opens a PR, moves on.
- Let it clear **3–4** issues, then hit the hard one → it **stops and tags `needs-human`** with a trace.
- **Speed this clip ~6×** into the "timelapse." End on the escalation.
- *Say:* "Eight gaps, eight hours, no supervision. Seven fixed and PR'd. One it couldn't crack — so it stopped and tagged a human. The escalation is the point: a system that knows when to stop is the only one you can deploy."

### 4 · Reset for a re-take
```
Close the demo issues and PRs that /work-issues created, and delete their branches.
```

---

## Recording tips
- Big terminal font; dark theme reads well on a projector.
- Do the prep prompt and **wait for "done" before hitting record**.
- The permission allowlist already covers `make` / `pytest` / `ruff` / `gh` / `git`, so the loops shouldn't stall on prompts.
- Keep each clip to one moment. Pause ~2s on each specialist's green verdict.
- Have all three clips on disk as **backups** — if a live run misbehaves on stage, cut to the recording.
