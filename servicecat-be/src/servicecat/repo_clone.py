"""Read-only shallow clones of service repos into ephemeral storage.

The clone lands in a temp directory that is deleted when the context exits, so
no clone outlives the run that needs it (the runner's "ephemeral storage").
"""

from __future__ import annotations

import asyncio
import contextlib
import shutil
import tempfile
from pathlib import Path
from typing import TYPE_CHECKING

from git import Repo

if TYPE_CHECKING:
    from collections.abc import AsyncIterator

_CLONE_DEPTH = 1


def _clone(repo_url: str, dest: str) -> None:
    Repo.clone_from(repo_url, dest, depth=_CLONE_DEPTH)


@contextlib.asynccontextmanager
async def clone_repo(repo_url: str) -> AsyncIterator[Path]:
    """Shallow-clone ``repo_url`` into a temp dir, yield it, then delete it."""
    tmpdir = tempfile.mkdtemp(prefix="servicecat-clone-")
    try:
        await asyncio.to_thread(_clone, repo_url, tmpdir)
        yield Path(tmpdir)
    finally:
        await asyncio.to_thread(shutil.rmtree, tmpdir, ignore_errors=True)
