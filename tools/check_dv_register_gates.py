#!/usr/bin/env python3
"""Flag DV register items whose named gate session completed unsatisfied.

This tool implements Phase 5 analytics recommendation R34, closing the
mechanical-enforcement gap Executive Audit 006 (finding E-F2) found by hand:
Phase 4's R28 recorded, in three separate places, that a dedicated
hotfix/correction session for DV-019 must run "before session 0109 (WP-028
S1) begins" — but nothing mechanically checked that precondition, and
Phase 5 fully executed and closed with it unsatisfied. EA-006's fix was a
hand-added "Hard gate" line in WP-033 S1's own session brief; this tool
generalizes that check so any future DV register item naming a specific
blocking session is caught automatically, before the gate is silently
missed a second time.

It parses ``DOCS/reports/DEFERRED_VALIDATION_REGISTER.md``'s "Active
deferred items" table for rows whose text names an explicit "before session
NNNN" (or "before WP-0NN S1 (session NNNN)") precondition, cross-references
``DOCS/sessions/SESSION_REGISTER.md`` for that session's status, and flags
any row where the named session is ``COMPLETE`` while the row's own Current
status cell does not show the item ``CLOSED``/``SATISFIED``.

Exit codes:

- ``0`` — no gate violations detected.
- ``1`` — one or more DV register items have a reached, unsatisfied gate.
- ``2`` — command-line or parsing error.
"""

from __future__ import annotations

import argparse
import re
import sys
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class DvRow:
    """One row of the Deferred Validation Register's active-items table."""

    dv_id: str
    prose: str
    current_status: str

    @property
    def gate_text(self) -> str:
        """Concatenated text of every column that may state a gate."""
        return "\n".join((self.prose, self.current_status))


_SATISFIED_RE = re.compile(r"\b(CLOSED|SATISFIED)\b")
_GATE_SESSION_RE = re.compile(
    r"before\s+(?:WP-\d+\s+S\d+\s+)?\(?session\s+(\d{4})\)?", re.IGNORECASE
)


def parse_dv_register(path: Path) -> list[DvRow]:
    r"""Parse the "Active deferred items" table from the DV register.

    The table's 6 declared columns (ID, Summary, Origin, Governing
    amendment, Re-audit gate, Current status) do not reliably split into 8
    ``"|"``-delimited cells: several live rows carry a genuinely missing
    middle column (e.g. DV-010 through DV-014, 7 cells) or an extra cell
    from a stray ``"|"`` inside inline-code prose (e.g. DV-020's
    ``grep -rl "PhaseAdam\|KuramotoOptimizer"``, 9 cells). Current status is
    always the last real column before the table's trailing empty cell, so
    it is extracted from the right (``cells[-2]``), which stays correct
    regardless of how many cells the earlier free-text columns produced;
    every other column is folded into one undifferentiated prose blob for
    gate-phrase scanning, where field identity does not matter.
    """
    text = path.read_text(encoding="utf-8")

    section_match = re.search(r"##\s*Active deferred items\s*\n", text)
    if section_match is None:
        raise ValueError(f"could not find '## Active deferred items' in {path}")

    start = section_match.end()
    remaining = text[start:]

    end_match = re.search(r"\n---", remaining)
    if end_match is not None:
        remaining = remaining[: end_match.start()]

    rows: list[DvRow] = []
    for raw_line in remaining.splitlines():
        line = raw_line.strip()
        if not line.startswith("|"):
            continue
        if line.startswith("|---") or re.match(r"\|\s*ID\s*\|", line):
            continue

        cells = [cell.strip() for cell in line.split("|")]
        # A well-formed row is at least: '', ID, ≥1 prose cell, status, ''.
        if len(cells) < 4:
            print(
                f"Warning: skipping malformed DV register row: {line[:80]!r}",
                file=sys.stderr,
            )
            continue

        dv_id = cells[1]
        if not dv_id or dv_id.lower() == "id":
            continue

        rows.append(
            DvRow(
                dv_id=dv_id,
                prose="\n".join(cells[2:-2]),
                current_status=cells[-2],
            )
        )

    return rows


def parse_session_register(path: Path) -> dict[str, str]:
    """Parse the numbered session table into ``{session_number: status}``."""
    text = path.read_text(encoding="utf-8")

    statuses: dict[str, str] = {}
    row_re = re.compile(r"^\|\s*(\d{4})\s*\|.*\|\s*([A-Z][A-Za-z ]*?)\s*\|\s*$")
    for raw_line in text.splitlines():
        match = row_re.match(raw_line.strip())
        if match is None:
            continue
        session_number, status = match.group(1), match.group(2)
        statuses[session_number] = status

    return statuses


def find_gate_sessions(row: DvRow) -> list[str]:
    """Return every session number a "before session NNNN" phrase names."""
    return sorted(set(_GATE_SESSION_RE.findall(row.gate_text)))


def is_satisfied(row: DvRow) -> bool:
    """Return True if the row's own Current status cell reads closed."""
    return bool(_SATISFIED_RE.search(row.current_status))


def find_violations(dv_rows: list[DvRow], session_status: dict[str, str]) -> list[str]:
    """Flag rows whose named gate session is COMPLETE but not satisfied."""
    violations: list[str] = []
    for row in dv_rows:
        if is_satisfied(row):
            continue
        for session in find_gate_sessions(row):
            status = session_status.get(session)
            if status == "COMPLETE":
                violations.append(
                    f"{row.dv_id}: gate session {session} is COMPLETE but "
                    f"the item is not closed/satisfied"
                )
    return violations


def find_repository_root() -> Path:
    """Locate the repository root from the script's location."""
    return Path(__file__).resolve().parents[1]


def main(argv: list[str] | None = None) -> int:
    """Entry point for the DV-register gate-enforcement checker."""
    repo_root = find_repository_root()
    parser = argparse.ArgumentParser(
        description=(
            "Detect DV register items whose named precondition session has "
            "been reached without the precondition being satisfied."
        )
    )
    parser.add_argument(
        "dv_register",
        type=Path,
        nargs="?",
        default=repo_root / "DOCS" / "reports" / "DEFERRED_VALIDATION_REGISTER.md",
        help="Deferred Validation Register (default: the repository's own).",
    )
    parser.add_argument(
        "session_register",
        type=Path,
        nargs="?",
        default=repo_root / "DOCS" / "sessions" / "SESSION_REGISTER.md",
        help="Session register (default: the repository's own).",
    )
    parser.add_argument(
        "--repo",
        type=Path,
        default=repo_root,
        help="Repository root (default: parent of tools/).",
    )
    args = parser.parse_args(argv)

    try:
        dv_rows = parse_dv_register(args.dv_register)
        session_status = parse_session_register(args.session_register)
    except (OSError, ValueError) as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 2

    violations = find_violations(dv_rows, session_status)

    if violations:
        print("DV-register gate check failed:", file=sys.stderr)
        for violation in violations:
            print(f"  - {violation}", file=sys.stderr)
        return 1

    print("DV-register gate check passed.")
    print(
        f"  Checked {len(dv_rows)} DV register rows against "
        f"{len(session_status)} session-register entries."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
