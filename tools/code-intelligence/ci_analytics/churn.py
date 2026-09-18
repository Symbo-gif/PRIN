"""Git-history-based churn heuristic (bounded, read-only, no shell).

Churn is computed by counting how many of the most recent N commits touched
each file (default N=1000, override via ``max_commits``), using the ``git``
executable directly with a list of arguments (never ``shell=True``), per
Coding Standards §6.1. This is a bounded, explicit-cost operation as
required by the task's execution-cost constraint.
"""

from __future__ import annotations

import shutil
import subprocess
from dataclasses import dataclass
from pathlib import Path

_DEFAULT_MAX_COMMITS = 1000
_GIT_TIMEOUT_SECONDS = 60


@dataclass
class ChurnResult:
    """Per-file commit-touch counts over a bounded recent history window.

    Attributes:
        counts: Repo-relative POSIX path -> number of touching commits.
        commits_examined: How many recent commits were scanned.
        available: False if ``git`` was not found or the repo has no
            history reachable from ``HEAD`` (e.g. a fresh checkout with one
            commit, or git unavailable) — callers must not silently treat
            an empty result as "zero churn everywhere".
    """

    counts: dict[str, int]
    commits_examined: int
    available: bool


def compute_churn(
    repo_root: Path, max_commits: int = _DEFAULT_MAX_COMMITS
) -> ChurnResult:
    """Count file-touch frequency over the last ``max_commits`` commits.

    Args:
        repo_root: Absolute repository root (must be a git worktree).
        max_commits: Bound on how many commits to scan (cost-bounded per
            the task's execution constraints).

    Returns:
        The churn counts, or an "unavailable" result if ``git`` cannot be
        run.
    """
    git_exe = shutil.which("git")
    if git_exe is None:
        return ChurnResult(counts={}, commits_examined=0, available=False)

    try:
        proc = subprocess.run(  # noqa: S603 - fixed absolute executable, list args, no shell
            [
                git_exe,
                "log",
                f"-n{max_commits}",
                "--name-only",
                "--pretty=format:__COMMIT__",
            ],
            cwd=str(repo_root),
            capture_output=True,
            text=True,
            timeout=_GIT_TIMEOUT_SECONDS,
            check=False,
        )
    except (OSError, subprocess.TimeoutExpired):
        return ChurnResult(counts={}, commits_examined=0, available=False)

    if proc.returncode != 0:
        return ChurnResult(counts={}, commits_examined=0, available=False)

    counts: dict[str, int] = {}
    commits_examined = 0
    for line in proc.stdout.splitlines():
        line = line.strip()
        if not line:
            continue
        if line == "__COMMIT__":
            commits_examined += 1
            continue
        rel = line.replace("\\", "/")
        counts[rel] = counts.get(rel, 0) + 1

    return ChurnResult(counts=counts, commits_examined=commits_examined, available=True)
