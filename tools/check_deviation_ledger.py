#!/usr/bin/env python3
"""Validate cumulative deviation-ledger consistency across Project State Reports.

This tool implements Phase 2 analytics recommendation R17. It parses the
cumulative deviation-ledger table from one or two PRIN Project State Reports
(``DOCS/reports/NNN-project-state.md``) and checks:

1. Every commit hash referenced in a ledger row resolves via
   ``git cat-file -t``.
2. When two consecutive reports are compared, rows with the same finding ID
   have identical summary text. A changed summary without a new finding ID is
   the drift pattern that corrupted the ledger between PSR-013 and PSR-016
   (EA-003 finding E-F1).

Exit codes:

- ``0`` — no consistency problems detected.
- ``1`` — one or more ledger rows have unresolvable commit hashes, or a
  finding's summary changed between two reports without a corresponding new ID.
- ``2`` — command-line or parsing error.
"""

from __future__ import annotations

import argparse
import re
import shutil
import subprocess  # nosec B404
import sys
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class LedgerRow:
    """One row of a cumulative deviation-ledger table."""

    finding_id: str
    raised: str
    severity: str
    summary: str
    status: str
    reference: str
    source: str


COMMIT_RE = re.compile(r"\b[0-9a-f]{7,40}\b")


def parse_ledger(path: Path) -> list[LedgerRow]:
    """Parse the deviation-ledger table from a PSR file."""
    text = path.read_text(encoding="utf-8")

    # Locate the deviation-ledger section.
    section_match = re.search(r"##\s*3\.\s*Deviation ledger.*?\n", text)
    if section_match is None:
        raise ValueError(f"could not find '## 3. Deviation ledger' in {path}")

    start = section_match.end()
    remaining = text[start:]

    # The table ends at the next level-2 heading or a completely blank line
    # before one, or at the end of the file.
    end_match = re.search(r"\n##\s+", remaining)
    if end_match is not None:
        remaining = remaining[: end_match.start()]

    rows: list[LedgerRow] = []
    for raw_line in remaining.splitlines():
        line = raw_line.strip()
        if not line.startswith("|"):
            continue
        # Skip header and separator rows.
        if line.startswith("|---") or re.match(r"\|\s*ID\s*\|", line):
            continue

        cells = [cell.strip() for cell in line.split("|")]
        # Markdown tables yield an empty leading and trailing cell.
        if len(cells) < 7:
            continue

        finding_id = cells[1]
        if not finding_id or finding_id.lower() == "id":
            continue

        rows.append(
            LedgerRow(
                finding_id=finding_id,
                raised=cells[2],
                severity=cells[3],
                summary=cells[4],
                status=cells[5],
                reference=cells[6],
                source=str(path),
            )
        )

    return rows


def collect_commit_hashes(text: str) -> list[str]:
    """Return all candidate commit hashes found in a reference string."""
    return list(set(COMMIT_RE.findall(text.lower())))


_GIT_BIN = Path(shutil.which("git") or "git").resolve()
_COMMITISH_RE = re.compile(r"^[0-9a-f]{7,40}$")


def _is_valid_commitish(commitish: str) -> bool:
    """Return True if ``commitish`` is a plausible hex commit hash."""
    return bool(_COMMITISH_RE.match(commitish))


def git_object_exists(commitish: str, repo: Path) -> bool:
    """Return True if ``commitish`` resolves to a git object in ``repo``."""
    if not _is_valid_commitish(commitish):
        return False
    # commitish is validated as a hex string before use; _GIT_BIN is absolute.
    result = subprocess.run(  # noqa: S603  # nosec B603
        [str(_GIT_BIN), "cat-file", "-t", commitish],
        cwd=repo,
        capture_output=True,
        text=True,
    )
    return result.returncode == 0 and "commit" in result.stdout


def validate_commits(rows: list[LedgerRow], repo: Path) -> list[str]:
    """Validate that every commit hash in the ledger resolves in the repo."""
    errors: list[str] = []
    seen: set[str] = set()
    for row in rows:
        for commit in collect_commit_hashes(row.reference):
            if commit in seen:
                continue
            seen.add(commit)
            if not git_object_exists(commit, repo):
                errors.append(
                    f"{row.finding_id}: commit hash {commit!r} "
                    f"does not resolve in {repo}"
                )
    return errors


def diff_ledgers(prev: list[LedgerRow], curr: list[LedgerRow]) -> list[str]:
    """Compare two consecutive ledgers and flag unexpected summary drift."""
    errors: list[str] = []
    prev_by_id: dict[str, LedgerRow] = {r.finding_id: r for r in prev}
    curr_by_id: dict[str, LedgerRow] = {r.finding_id: r for r in curr}

    for finding_id, curr_row in curr_by_id.items():
        if finding_id not in prev_by_id:
            # New finding IDs are expected in the latest report.
            continue
        prev_row = prev_by_id[finding_id]
        if prev_row.summary != curr_row.summary:
            errors.append(
                f"{finding_id}: summary changed between {prev_row.source} "
                f"and {curr_row.source} without a new finding ID"
            )

    # Removed finding IDs are also suspicious, but the PSR template does not
    # expect removals; flag them explicitly.
    for finding_id in prev_by_id:
        if finding_id not in curr_by_id:
            errors.append(
                f"{finding_id}: present in previous ledger "
                f"but missing from {curr[0].source if curr else 'current ledger'}"
            )

    return errors


def find_repository_root() -> Path:
    """Locate the repository root from the script's location."""
    return Path(__file__).resolve().parents[1]


def main(argv: list[str] | None = None) -> int:
    """Entry point for the deviation-ledger consistency checker."""
    parser = argparse.ArgumentParser(
        description="Validate cumulative deviation-ledger consistency."
    )
    parser.add_argument(
        "previous",
        type=Path,
        help="Previous Project State Report (e.g., DOCS/reports/016-project-state.md).",
    )
    parser.add_argument(
        "current",
        type=Path,
        nargs="?",
        help=(
            "Current Project State Report. If omitted, only commit hashes "
            "in the previous report are validated."
        ),
    )
    parser.add_argument(
        "--repo",
        type=Path,
        default=find_repository_root(),
        help="Repository root for git object resolution (default: parent of tools/).",
    )
    args = parser.parse_args(argv)

    previous_rows = parse_ledger(args.previous)
    errors = validate_commits(previous_rows, args.repo)

    if args.current is not None:
        current_rows = parse_ledger(args.current)
        errors.extend(validate_commits(current_rows, args.repo))
        errors.extend(diff_ledgers(previous_rows, current_rows))

    if errors:
        print("Ledger consistency check failed:", file=sys.stderr)
        for error in errors:
            print(f"  - {error}", file=sys.stderr)
        return 1

    print("Ledger consistency check passed.")
    if args.current is not None:
        print(
            f"  Compared {len(previous_rows)} rows in {args.previous} "
            f"with {len(current_rows)} rows in {args.current}."
        )
    else:
        print(f"  Validated {len(previous_rows)} rows in {args.previous}.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
