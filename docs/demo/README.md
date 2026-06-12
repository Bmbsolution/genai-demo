# Demo · Moment 1 — terminal recording

`moment-1-waitlist-promote.cast` is an [asciinema](https://asciinema.org) v2
recording for **Demo · Moment 1** (slide 15): the orchestrator running

```
/implement auto-promote the next waitlisted guest when a confirmed guest cancels
```

It's a **reconstruction from the real build** — the feature was actually
implemented, tested, and shipped (PR #7), and this cast replays that session
with the genuine output (47 tests passing, ruff/mypy clean, the real file list).
Regenerate it anytime with `python build_moment1_cast.py`.

## Play it

```bash
asciinema play moment-1-waitlist-promote.cast      # full speed (~30s)
asciinema play -s 0.6 moment-1-waitlist-promote.cast   # slower, easier to narrate
asciinema play -i 0.4 moment-1-waitlist-promote.cast   # cap idle pauses
```

Press space to pause, `.` to step — handy when narrating live.

## Put it on a slide / screen

- **`moment-1-waitlist-promote.svg`** — a **pre-rendered animated SVG** (crisp at
  any size, plays on loop in any browser or slide that accepts SVG). Drop it
  straight onto the Moment 1 slide. Regenerate with:
  `npx svg-term-cli --in moment-1-waitlist-promote.cast --out moment-1-waitlist-promote.svg --window --padding 18`
- **Full-screen terminal:** run `asciinema play` in a maximized terminal and
  screen-share that window during Moment 1.
- **GIF** (for embedding): `agg moment-1-waitlist-promote.cast moment-1.gif`
  ([agg](https://github.com/asciinema/agg)).
- **Web embed:** host the `.cast` and use
  [asciinema-player](https://github.com/asciinema/asciinema-player).

The replay is ~50s — long enough to narrate, short enough to keep moving. Adjust
`SPEED` in `build_moment1_cast.py` and regenerate to taste.
