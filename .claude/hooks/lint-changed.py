#!/usr/bin/env python3
"""PostToolUse hook: lint the Python file Claude just edited (best-effort).

Reads the hook JSON from stdin, finds the edited file, and runs ruff on it when
it's backend Python. Design rule: the hook must NEVER break the workflow — if ruff
isn't installed or anything goes wrong, it exits 0 silently. When ruff finds
problems it writes them to stderr and exits 2 so Claude sees them and fixes them in
its inner loop.

(Frontend lint stays in the workflow via `pnpm lint` — eslint can't cleanly
distinguish lint errors from config errors per-file, so we don't run it here.)
"""
import json
import os
import shutil
import subprocess
import sys


def find_ruff():
    exe = shutil.which("ruff")
    if exe:
        return [exe]
    root = os.environ.get("CLAUDE_PROJECT_DIR", ".")
    for rel in (".venv/Scripts/ruff.exe", ".venv/bin/ruff"):
        cand = os.path.join(root, "gatherly-be", rel)
        if os.path.isfile(cand):
            return [cand]
    return None


def main():
    try:
        data = json.load(sys.stdin)
    except Exception:
        return 0
    fp = (data.get("tool_input") or {}).get("file_path") or ""
    if not fp or not os.path.isfile(fp):
        return 0
    p = fp.replace("\\", "/")
    if not (p.endswith(".py") and "gatherly-be" in p):
        return 0

    ruff = find_ruff()
    if not ruff:
        return 0  # linter not available — no-op
    try:
        r = subprocess.run(ruff + ["check", fp], capture_output=True, text=True, timeout=120)
    except (FileNotFoundError, subprocess.TimeoutExpired, OSError):
        return 0
    if r.returncode != 0:
        sys.stderr.write("ruff found issues in the file just edited:\n")
        sys.stderr.write((r.stdout or "") + (r.stderr or ""))
        return 2  # surface to Claude
    return 0


if __name__ == "__main__":
    sys.exit(main())
