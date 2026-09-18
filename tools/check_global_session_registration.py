#!/usr/bin/env python3
"""Flag Executive Audit reports with no matching Session Register row.

This tool implements EDA-002 finding D-F1's durable-guard recommendation
(ETCA-002 G8: a recurring finding needs a class-level regression guard, not
just an instance fix). Every Executive Audit (EA), Executive Mathematical
Audit (EMA), Executive Documentation Audit (EDA), and Executive Testing and
CI Audit (ETCA) session's own closing checklist requires it to register
itself in ``DOCS/sessions/SESSION_REGISTER.md``'s "Global sessions" tables
(and in ``CHANGELOG.md``, which is free-form prose and not mechanically
checked here). That requirement has been missed three times without a
mechanical check: EMA-001 (self-corrected the same session), EMA-003
(corrected retroactively by EMA-004), and EMA-007 (corrected by this
tool's own introducing session, EDA-002 remediation) — each time the gap
was found only by a later audit session reading the register by hand.

It scans ``DOCS/audits/`` for report filenames matching the four Executive
Audit types' naming convention (``EXECUTIVE_AUDIT_REPORT_NNN.md`` -> EA-NNN,
``EXECUTIVE_MATH_AUDIT_REPORT_NNN.md`` -> EMA-NNN,
``EXECUTIVE_DOCUMENTATION_AUDIT_REPORT_NNN.md`` -> EDA-NNN,
``EXECUTIVE_TESTING_AND_CI_AUDIT_REPORT_NNN.md`` -> ETCA-NNN), derives each
report's session ID, and confirms a table row beginning with that exact ID
exists somewhere in the session register. Non-report files in the same
directory (templates, the EMA preparation document, per-WP audit reports
named ``NNN-wpNNN-audit.md``) do not match this naming convention and are
correctly ignored.

Exit codes:

- ``0`` — every report has a matching register row.
- ``1`` — one or more reports have no matching register row.
- ``2`` — command-line or parsing error.
"""

from __future__ import annotations

import argparse
import re
import sys
from dataclasses import dataclass
from pathlib import Path

_REPORT_PATTERNS: tuple[tuple[re.Pattern[str], str], ...] = (
    (re.compile(r"^EXECUTIVE_DOCUMENTATION_AUDIT_REPORT_(\d+)\.md$"), "EDA"),
    (re.compile(r"^EXECUTIVE_TESTING_AND_CI_AUDIT_REPORT_(\d+)\.md$"), "ETCA"),
    (re.compile(r"^EXECUTIVE_MATH_AUDIT_REPORT_(\d+)\.md$"), "EMA"),
    (re.compile(r"^EXECUTIVE_AUDIT_REPORT_(\d+)\.md$"), "EA"),
)


@dataclass(frozen=True)
class AuditReport:
    """One discovered Executive Audit report and its derived session ID."""

    filename: str
    session_id: str


def derive_session_id(filename: str) -> str | None:
    """Return the session ID (e.g. ``"EMA-007"``) a report filename implies.

    Patterns are checked most-specific first (``EXECUTIVE_DOCUMENTATION_
    AUDIT_REPORT_*`` and ``EXECUTIVE_TESTING_AND_CI_AUDIT_REPORT_*`` before
    the plain ``EXECUTIVE_AUDIT_REPORT_*``/``EXECUTIVE_MATH_AUDIT_REPORT_*``)
    so a longer prefix is never mistaken for a shorter one. Returns ``None``
    for filenames that do not match any Executive Audit report convention
    (templates, the EMA preparation document, per-WP audit reports).
    """
    for pattern, prefix in _REPORT_PATTERNS:
        match = pattern.match(filename)
        if match is not None:
            return f"{prefix}-{match.group(1)}"
    return None


def find_reports(audits_dir: Path) -> list[AuditReport]:
    """Discover every Executive Audit report in ``audits_dir``."""
    reports: list[AuditReport] = []
    for path in sorted(audits_dir.iterdir()):
        if not path.is_file():
            continue
        session_id = derive_session_id(path.name)
        if session_id is not None:
            reports.append(AuditReport(filename=path.name, session_id=session_id))
    return reports


def registered_session_ids(session_register: Path) -> set[str]:
    """Return every global-session ID with its own row in the register.

    Matches any Markdown table row whose first cell is exactly the ID (e.g.
    ``| EMA-007 | ...``) — deliberately table-agnostic, since the four audit
    types each have their own "Global sessions" table but share the same
    row format, and a report's row must exist in *some* table, not
    necessarily positioned perfectly (a misplaced-but-present row is a
    separate, lower-severity defect this tool does not adjudicate).
    """
    text = session_register.read_text(encoding="utf-8")
    ids: set[str] = set()
    row_re = re.compile(r"^\|\s*((?:EA|EMA|EDA|ETCA)-\d+)\s*\|")
    for raw_line in text.splitlines():
        match = row_re.match(raw_line.strip())
        if match is not None:
            ids.add(match.group(1))
    return ids


def find_violations(reports: list[AuditReport], registered_ids: set[str]) -> list[str]:
    """Flag reports whose derived session ID has no register row."""
    violations: list[str] = []
    for report in reports:
        if report.session_id not in registered_ids:
            violations.append(
                f"{report.filename}: no SESSION_REGISTER.md row for {report.session_id}"
            )
    return violations


def find_repository_root() -> Path:
    """Locate the repository root from the script's location."""
    return Path(__file__).resolve().parents[1]


def main(argv: list[str] | None = None) -> int:
    """Entry point for the global-session-registration checker."""
    repo_root = find_repository_root()
    parser = argparse.ArgumentParser(
        description=(
            "Detect Executive Audit reports (EA/EMA/EDA/ETCA) with no "
            "matching row in SESSION_REGISTER.md's Global sessions tables."
        )
    )
    parser.add_argument(
        "audits_dir",
        type=Path,
        nargs="?",
        default=repo_root / "DOCS" / "audits",
        help="Audits directory (default: the repository's own).",
    )
    parser.add_argument(
        "session_register",
        type=Path,
        nargs="?",
        default=repo_root / "DOCS" / "sessions" / "SESSION_REGISTER.md",
        help="Session register (default: the repository's own).",
    )
    args = parser.parse_args(argv)

    try:
        reports = find_reports(args.audits_dir)
        registered_ids = registered_session_ids(args.session_register)
    except OSError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 2

    violations = find_violations(reports, registered_ids)

    if violations:
        print("Global-session registration check failed:", file=sys.stderr)
        for violation in violations:
            print(f"  - {violation}", file=sys.stderr)
        return 1

    print("Global-session registration check passed.")
    print(f"  Checked {len(reports)} Executive Audit reports.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
