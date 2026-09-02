#!/usr/bin/env python3
"""Confirm ``origin/main`` CI is green for a given commit before a WP is closed.

ETCA-002 finding T-F1 / governance G2. ETCA-001 drove CI green and then, one
work-package cycle later, WP-036E + WP-036F were declared closed — PSR issued,
DV-006 DirectML half marked CLOSED, Project Plan amendment #13 marked
discharged — over a **red** push whose S4 documentation asserted "CI is green".
The remediation fixed the red gates but added no mechanism forcing a session to
*confirm* green after it pushes.

This tool is that mechanism. An S4 (or ETCA / EA) session runs it against its
own push SHA and pastes the output verbatim into the PSR verification block. A
WP cannot be declared CLOSED, a PSR issued, or a DV item / plan amendment
discharged while it reports non-green or "no run found" for a required
workflow.

It wraps ``gh run list --branch <branch> --json ...`` (GitHub CLI must be
authenticated) and checks that every workflow in ``--required`` has a
``completed`` run with ``conclusion == "success"`` for the target SHA.

Exit codes:

- ``0`` — every required workflow is green for the SHA.
- ``1`` — a required workflow is red, still running, or has no run for the SHA.
- ``2`` — command-line error, or ``gh`` unavailable / not authenticated.
"""

from __future__ import annotations

import argparse
import json
import subprocess  # nosec B404
import sys

# The push-triggered workflows that gate `main`. `gpu` runs on every push
# (amendment #45) but is intentionally not in this default set: it depends on
# the single self-hosted `PRIN-GPU-Runner` (DV-024 SPOF), so a session confirms
# it explicitly with `--required gpu` when the WP touched a GPU path, rather
# than blocking every close on runner uptime.
_DEFAULT_REQUIRED = ("rust", "python", "parity", "repro", "snyk")


def _gh_runs(branch: str, limit: int) -> list[dict[str, object]]:
    """Return recent workflow runs for ``branch`` as dicts, newest first."""
    fields = "headSha,workflowName,conclusion,status,databaseId,event"
    cmd = [
        "gh",
        "run",
        "list",
        "--branch",
        branch,
        "--limit",
        str(limit),
        "--json",
        fields,
    ]
    try:
        proc = subprocess.run(  # noqa: S603  # nosec B603 - fixed argv, `gh` resolved via PATH
            cmd, capture_output=True, text=True, check=True
        )
    except FileNotFoundError:
        print("error: the GitHub CLI (`gh`) is not installed", file=sys.stderr)
        raise SystemExit(2) from None
    except subprocess.CalledProcessError as exc:
        print(f"error: `gh run list` failed: {exc.stderr.strip()}", file=sys.stderr)
        raise SystemExit(2) from None
    parsed: list[dict[str, object]] = json.loads(proc.stdout)
    return parsed


def check(sha: str, branch: str, required: tuple[str, ...], limit: int) -> int:
    """Print a per-workflow verdict for ``sha`` and return the process exit code."""
    runs = _gh_runs(branch, limit)
    for_sha = [r for r in runs if str(r.get("headSha", "")).startswith(sha)]

    print(f"CI-green check — branch {branch!r}, commit {sha}")
    if not for_sha:
        print(f"  no workflow runs found for {sha} (not pushed, or CI not started)")
        return 1

    worst = 0
    for workflow in required:
        matching = [r for r in for_sha if r.get("workflowName") == workflow]
        if not matching:
            print(f"  {workflow:<10} MISSING   — no run for this commit")
            worst = 1
            continue
        run = matching[0]
        status = run.get("status")
        conclusion = run.get("conclusion")
        if status != "completed":
            print(f"  {workflow:<10} PENDING   — status={status}")
            worst = 1
        elif conclusion == "success":
            print(f"  {workflow:<10} green     — run {run.get('databaseId')}")
        else:
            print(f"  {workflow:<10} RED       — conclusion={conclusion}")
            worst = 1

    print("RESULT:", "all required workflows green" if worst == 0 else "NOT green")
    return worst


def main(argv: list[str] | None = None) -> int:
    """Parse arguments and run the CI-green check."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("sha", help="the commit SHA to verify (7+ chars)")
    parser.add_argument("--branch", default="main")
    parser.add_argument(
        "--required",
        nargs="+",
        default=list(_DEFAULT_REQUIRED),
        help="workflow names that must be green (default: the 5 hosted gates)",
    )
    parser.add_argument("--limit", type=int, default=60)
    args = parser.parse_args(argv)
    return check(args.sha, args.branch, tuple(args.required), args.limit)


if __name__ == "__main__":
    sys.exit(main())
