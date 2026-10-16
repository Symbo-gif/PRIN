r"""Bucket a Snyk Code SARIF report for the S3 gate and the F8 re-check.

Companion to ``snyk code test . --severity-threshold=low --sarif-file-output=...``
for audit session S3. The report is read from **standard input**, so no
caller-supplied string is turned into a filesystem path::

    .venv/Scripts/python.exe -I EVIDENCE/exp002-d1-s3/snyk_s3_filter.py < report.sarif

Three properties shape this tool. The first corrects a conclusion S2 drew
(``EVIDENCE/exp002-d1-s2/snyk_sarif_filter.py``); the other two still hold:

1. **The SARIF ``result.level`` tracks severity coarsely.** S2 concluded that
   Snyk Code's SARIF carries no severity because every level in its report was
   ``"note"``; its report had no MEDIUM finding. S3's first scan had exactly one
   MEDIUM, and exactly one result carried ``"warning"`` (the other 97 LOW
   results carried ``"note"``, matching the console's ``0 HIGH 1 MEDIUM 97 LOW``).
   So ``note`` = LOW and ``warning`` = MEDIUM on the evidence; ``error`` = HIGH is
   the SARIF convention but has not been observed here. The CLI's own ``Test
   Summary`` block remains the authoritative breakdown and is transcribed from
   the console output, not derived here.
2. **``snyk code test .`` scans the filesystem, not git**, so gitignored agent
   worktrees are counted and the same logical file is reported once per copy.
   This tool therefore also reports the findings restricted to files git knows
   about (tracked, or untracked-but-not-ignored).
3. A missing or unreadable report means the leg is **blocked**, never clean.

The buckets are the S3 governance questions: (a) the first-party files S3
changed, (b) the instruments S3 added, and (c) the two S2 instruments that carry
the ratified residual ``EXP002D1-S2-F8``, which Coding Standards section 6.2
requires to be re-checked every cycle.

Exit status is 0 when the report was read and no git-known path has a finding
above LOW (the section 6.2 gate), 1 when one does, 2 when stdin was empty or not
SARIF (the leg is blocked, never clean). LOW findings are reported but do not
fail the run: they stay visible and are re-checked every cycle.
"""

from __future__ import annotations

import json
import shutil
import subprocess  # nosec B404 - fixed argv, no shell
import sys
from collections import Counter
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]

#: ``git`` resolved once to an absolute path (Coding Standards section 6.1:
#: "absolute executables"), as ``tools/check_deviation_ledger.py`` does.
_GIT = shutil.which("git")
if _GIT is None:
    raise SystemExit("git was not found on PATH")
GIT: str = _GIT

#: First-party source files S3 changed.
S3_CHANGED: tuple[str, ...] = (
    "python/prin/reporting/figure_generation.py",
    "tests/test_publication_figure_arguments.py",
)

#: Directory holding the instruments S3 added.
S3_INSTRUMENT_DIR = "EVIDENCE/exp002-d1-s3/"

#: Directory holding the S2 instruments.
S2_INSTRUMENT_DIR = "EVIDENCE/exp002-d1-s2/"

#: S2 instruments carrying the ratified residual EXP002D1-S2-F8.
S2_F8: tuple[str, ...] = (
    "EVIDENCE/exp002-d1-s2/changed_line_coverage.py",
    "EVIDENCE/exp002-d1-s2/decomposition_rerun_check.py",
)


def normalise(uri: str) -> str:
    """Return a SARIF artifact URI as a repository-relative POSIX path.

    Args:
        uri: The artifact location URI.

    Returns:
        The normalised path.
    """
    return uri.replace("\\", "/").lstrip("/")


def known_paths() -> set[str]:
    """Return every path git tracks or could add (untracked, not ignored).

    Returns:
        Repository-relative POSIX paths.
    """
    done = subprocess.run(  # noqa: S603  # nosec B603 - absolute git, fixed argv, no shell
        [GIT, "ls-files", "--cached", "--others", "--exclude-standard"],
        cwd=ROOT,
        capture_output=True,
        check=True,
    )
    return {
        normalise(line) for line in done.stdout.decode("utf-8").splitlines() if line
    }


def findings_of(report: dict[str, Any]) -> list[dict[str, Any]]:
    """Flatten a SARIF document into one record per located finding.

    Args:
        report: The parsed SARIF document.

    Returns:
        Records with ``rule``, ``level``, ``path`` and ``line``.
    """
    out: list[dict[str, Any]] = []
    for run in report.get("runs", []):
        for result in run.get("results", []):
            for location in result.get("locations") or [{}]:
                physical = location.get("physicalLocation", {})
                out.append(
                    {
                        "rule": str(result.get("ruleId") or "?"),
                        "level": str(result.get("level") or "?"),
                        "path": normalise(
                            physical.get("artifactLocation", {}).get("uri", "")
                        ),
                        "line": physical.get("region", {}).get("startLine"),
                    }
                )
    return out


def show(label: str, hits: list[dict[str, Any]]) -> None:
    """Print one bucket.

    Args:
        label: Bucket title.
        hits: The findings in the bucket.
    """
    print(f"=== {label}: {len(hits)} finding(s) ===")
    for hit in sorted(hits, key=lambda f: (f["path"], f["line"] or 0)):
        print(f"  {hit['rule']:14s} {hit['path']}:{hit['line']}")
    if not hits:
        print("  NONE")
    print()


def main() -> int:
    """Read a SARIF report on stdin and print the S3 buckets.

    Returns:
        The process exit status.
    """
    text = sys.stdin.read()
    try:
        report: dict[str, Any] = json.loads(text)
        findings = findings_of(report)
    except (json.JSONDecodeError, AttributeError):
        print("SARIF MISSING OR UNREADABLE on stdin: the leg is BLOCKED, not clean.")
        return 2
    known = known_paths()
    in_git = [f for f in findings if f["path"] in known]
    print(f"total findings (raw filesystem scan)      : {len(findings)}")
    print(f"findings in git-known paths               : {len(in_git)}")
    print(f"findings only in untracked on-disk copies : {len(findings) - len(in_git)}")
    levels = dict(Counter(f["level"] for f in findings))
    print(f"result.level values (note=LOW, warning=MEDIUM): {levels}")
    print()
    above_low = [f for f in in_git if f["level"] != "note"]
    show(
        "ABOVE LOW anywhere in git-known paths (section 6.2 gate: must be 0)", above_low
    )
    show(
        "S3-changed first-party files", [f for f in findings if f["path"] in S3_CHANGED]
    )
    show(
        f"S3-added instruments ({S3_INSTRUMENT_DIR})",
        [f for f in findings if f["path"].startswith(S3_INSTRUMENT_DIR)],
    )
    show(
        "F8 re-check: the two ratified S2 locations",
        [f for f in findings if f["path"] in S2_F8],
    )
    show(
        "F8 re-check: OTHER findings in S2 instruments (not in the F8 record)",
        [
            f
            for f in findings
            if f["path"].startswith(S2_INSTRUMENT_DIR) and f["path"] not in S2_F8
        ],
    )
    return 1 if above_low else 0


if __name__ == "__main__":
    raise SystemExit(main())
