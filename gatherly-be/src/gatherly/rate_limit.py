"""In-memory fixed-window rate limiter (single-process demo).

Gatherly keeps this in-process to stay zero-infra (back it with Redis or another
shared store when running more than one process). Fixed-window semantics, per
``identity`` + ``key``.
"""

from __future__ import annotations

import time

_WINDOW_SECONDS = 60
# bucket key -> (window_index, hits)
_counters: dict[str, tuple[int, int]] = {}


def check_rate_limit(*, identity: str, key: str, per_minute: int) -> bool:
    """Record a hit and return True iff the caller is still within the limit."""
    window = int(time.time()) // _WINDOW_SECONDS
    bucket = f"{key}:{identity}"
    cur_window, hits = _counters.get(bucket, (window, 0))
    if cur_window != window:
        cur_window, hits = window, 0
    hits += 1
    _counters[bucket] = (cur_window, hits)
    return hits <= per_minute


def reset() -> None:
    """Clear all counters (test helper)."""
    _counters.clear()
