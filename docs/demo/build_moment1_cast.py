"""Generate the Demo · Moment 1 asciinema cast (v2).

Reconstructs the real `/implement` orchestration that built the waitlist
auto-promote feature (PR #7) into a replayable terminal recording. Outputs from
the genuine build are used verbatim (47 passed, ruff/mypy clean, the file list).

Run:  python docs/demo/build_moment1_cast.py
Play: asciinema play docs/demo/moment-1-waitlist-promote.cast
"""

from __future__ import annotations

import json
from pathlib import Path

# --- ANSI helpers ---------------------------------------------------------
R = "\x1b[0m"
B = "\x1b[1m"
DIM = "\x1b[2m"
GRN = "\x1b[32m"
YEL = "\x1b[33m"
BLU = "\x1b[34m"
CYN = "\x1b[36m"
MAG = "\x1b[35m"
WHT = "\x1b[97m"

WIDTH, HEIGHT = 100, 34
TIMESTAMP = 1_781_000_000  # fixed (June 2026); cosmetic only

events: list[list[object]] = []
clock = 0.0


def emit(text: str, gap: float = 0.0) -> None:
    """Advance the clock by ``gap`` then write one output event."""
    global clock
    clock = round(clock + gap, 3)
    events.append([clock, "o", text])


def line(text: str = "", gap: float = 0.35) -> None:
    emit(text + "\r\n", gap)


def typed(text: str, gap: float = 0.045) -> None:
    """Type a string out character-by-character, then newline."""
    for ch in text:
        emit(ch, gap)
    emit("\r\n", 0.25)


# --- session --------------------------------------------------------------
emit(f"{DIM}gatherly ~ orchestrated build{R}\r\n", 0.0)
emit(f"{B}{GRN}${R} ", 0.6)
typed("claude")
line("", 0.4)
emit(f"{DIM}  Claude Code · /implement{R}\r\n", 0.5)
emit(f"{B}{CYN}❯{R} ", 0.7)
typed("/implement auto-promote the next waitlisted guest when a confirmed guest cancels", 0.035)
line("", 0.8)


def phase(title: str, agent: str = "", gap: float = 0.9) -> None:
    tag = f"  {DIM}({agent}){R}" if agent else ""
    line(f"{B}{MAG}●{R} {B}{WHT}{title}{R}{tag}", gap)


def step(symbol: str, text: str, color: str = DIM, gap: float = 0.3) -> None:
    line(f"  {color}{symbol}{R} {DIM}{text}{R}", gap)


def ok(text: str, gap: float = 0.35) -> None:
    line(f"  {GRN}✓{R} {text}", gap)


phase("Plan", "plan-feature")
step("◦", "read CLAUDE.md · WORKFLOW.md · the scorecard contract")
step("◦", "spec: a confirmed guest cancels on a capped event → promote oldest waitlisted")
ok("acceptance criteria AC-1…AC-6 generated", 0.7)

phase("Explore", "explore-codebase")
step("◦", "services/rsvp.py — respond() already does YES-overflow → WAITLISTED")
step("◦", "repositories/guests.py — count_attending present; need oldest_waitlisted (FIFO)")
step("◦", "services/email.py — EmailSender ready for the promotion notice")
ok("3 files in scope · no API contract change", 0.7)

phase("Implement")
line(f"  {GRN}+{R} repositories/guests.py        {DIM}oldest_waitlisted() — FIFO by created_at{R}", 0.5)
line(f"  {YEL}~{R} services/rsvp.py              {DIM}freed-seat detect → _promote_from_waitlist() + email{R}", 0.5)
line(f"  {GRN}+{R} tests/test_waitlist_promote.py {DIM}4 cases{R}", 0.7)

phase("Test", "pytest")
emit(f"  {DIM}", 0.5)
emit("...............................................", 1.4)
line(f"{R} {GRN}47 passed{R} {DIM}in 3.07s{R}", 0.4)
ok("coverage on new code: 100%", 0.7)

phase("Review", "review-pr")
step("⚠", "race: two simultaneous cancels could promote past capacity", YEL, 0.6)
ok("guarded — _promote_from_waitlist re-counts attendance before promoting", 0.4)
ok("no blocking findings", 0.7)

phase("Audit", "audit-security")
step("◦", "S1–S8 on the RSVP path — token-scoped, no cross-guest access")
ok("clean", 0.7)

phase("Lint & types")
ok(f"ruff check {DIM}— all checks passed{R}", 0.3)
ok(f"mypy --strict {DIM}— no issues in 47 source files{R}", 0.7)

phase("Commit & PR")
ok(f"{DIM}feat(gatherly-be): auto-promote the next waitlisted guest…{R}", 0.4)
ok(f"{DIM}pushed{R} feat/waitlist-auto-promote", 0.4)
ok(f"PR {B}#7{R} opened → {BLU}github.com/Bmbsolution/genai-demo/pull/7{R}", 0.9)

line("", 0.6)
line(f"  {DIM}8 specialists · 1 orchestrator · ~8 min · CI green{R}", 0.6)
line(f"  {B}{WHT}nobody picked the specialists — the routing is in the system.{R}", 1.2)
line("", 0.3)

header = {
    "version": 2,
    "width": WIDTH,
    "height": HEIGHT,
    "timestamp": TIMESTAMP,
    "title": "Gatherly · Moment 1 — /implement waitlist auto-promote",
    "env": {"SHELL": "/bin/zsh", "TERM": "xterm-256color"},
}

out = Path(__file__).with_name("moment-1-waitlist-promote.cast")
with out.open("w", encoding="utf-8", newline="\n") as fh:
    fh.write(json.dumps(header) + "\n")
    for ev in events:
        fh.write(json.dumps(ev, ensure_ascii=False) + "\n")

print(f"wrote {out}  ({len(events)} events, {clock:.1f}s runtime)")
