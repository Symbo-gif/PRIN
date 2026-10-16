r"""Filter a Snyk Code SARIF report for the files this audit actually governs.

Companion to the ``snyk code test . --severity-threshold=low
--sarif-file-output=…`` leg. Two properties of Snyk Code's SARIF output shape
this tool, and both were established by inspecting a real report rather than
assumed:

1. **The SARIF carries no severity.** Every ``result.level`` is ``"note"``, and
   neither ``result.properties`` (only ``isAutofixable``, ``priorityScore``,
   ``priorityScoreFactors``) nor ``rule.properties`` (only ``tags``,
   ``categories``, ``precision``, ``cwe``, example fixes) contains a severity
   name or a ``security-severity`` score. The authoritative severity breakdown
   is therefore the CLI's own ``Test Summary`` block
   (``Open issues: N [ X HIGH  Y MEDIUM  Z LOW ]``), which must be transcribed
   from the console output and cannot be derived from the SARIF. This tool says
   so rather than reporting ``note`` as if it were a severity.
2. **``snyk code test .`` scans the filesystem, not git.** On this workstation
   the repository directory also holds gitignored agent worktrees
   (``.claude/worktrees/…``, ``.kilo/worktrees/…``), so the same logical file is
   reported once per copy — ``tools/reproduce.py`` appears three times, for
   example. A repo-wide total is therefore **not** a census of tracked files,
   and two totals taken at different times are only comparable if the on-disk
   worktree set is the same. This tool reports both the raw total and the
   total restricted to paths ``git ls-files`` knows about.

The two buckets this audit cares about are reported separately: the four
first-party files the correction changed (S2 brief item f), and the six S2 audit
instruments (finding ``EXP002D1-S2-F8``).

Run from the repository root with the project venv::

    python EVIDENCE/exp002-d1-s2/snyk_sarif_filter.py <report.sarif>

Exit status is ``0`` when the report was read and filtered, ``2`` when it is
missing or unreadable. A non-zero status here means the leg is **blocked**, and
must never be reported as a clean scan.
"""

from __future__ import annotations

import json
import subprocess  # nosec B404
import sys
from collections import Counter
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]

#: The four first-party source files the EXP-002 D1 correction added or changed.
CHANGED_FILES: tuple[str, ...] = (
    "python/prin/reporting/figure_generation.py",
    "tests/test_publication_figure_arguments.py",
    "parity/test_parity_publication.py",
    "EVIDENCE/exp002-d1-s1/root_cause_decomposition.py",
)

#: The six audit instruments this S2 session added under its own evidence dir.
S2_INSTRUMENTS: tuple[str, ...] = (
    "EVIDENCE/exp002-d1-s2/ast_spec_validation.py",
    "EVIDENCE/exp002-d1-s2/artist_level_equivalence.py",
    "EVIDENCE/exp002-d1-s2/decomposition_rerun_check.py",
    "EVIDENCE/exp002-d1-s2/both_policies_post_fix.py",
    "EVIDENCE/exp002-d1-s2/fast_gate_divergence_coverage.py",
    "EVIDENCE/exp002-d1-s2/changed_line_coverage.py",
)


def normalise(uri: str) -> str:
    """Return a SARIF artifact URI as a repository-relative POSIX path."""
    return uri.replace("\\", "/").lstrip("/")


def tracked_paths() -> set[str]:
    """Return every path ``git ls-files`` reports, normalised for comparison."""
    completed = subprocess.run(  # nosec B603 B607
        ["git", "ls-files"],  # noqa: S607
        capture_output=True,
        text=True,
        check=True,
        cwd=ROOT,
    )
    return {normalise(line) for line in completed.stdout.splitlines() if line}


def iter_findings(report: dict[str, Any]) -> list[dict[str, Any]]:
    """Flatten a SARIF document into one record per located finding."""
    out: list[dict[str, Any]] = []
    for run in report.get("runs", []):
        driver = run.get("tool", {}).get("driver", {})
        tool_name = f"{driver.get('name')} {driver.get('version')}"
        for result in run.get("results", []):
            rule_id = str(result.get("ruleId") or "?")
            level = str(result.get("level") or "?")
            locations = result.get("locations") or [{}]
            for location in locations:
                physical = location.get("physicalLocation", {})
                uri = physical.get("artifactLocation", {}).get("uri", "")
                region = physical.get("region", {})
                out.append(
                    {
                        "tool": tool_name,
                        "rule": rule_id,
                        "level": level,
                        "path": normalise(uri),
                        "line": region.get("startLine"),
                        "message": (result.get("message") or {}).get("text", ""),
                    }
                )
    return out


def report_bucket(
    findings: list[dict[str, Any]], label: str, group: tuple[str, ...]
) -> int:
    """Print the findings that land in one governed file group; return the count."""
    print(f"=== {label} ===")
    hits = [f for f in findings if f["path"] in group]
    if not hits:
        print("  NONE (0 findings)")
    for hit in sorted(hits, key=lambda f: (f["path"], f["line"] or 0)):
        print(f"  {hit['rule']:16s} {hit['path']}:{hit['line']}")
        print(f"      level={hit['level']}  (SARIF carries no severity; see above)")
    print(f"  -> {len(hits)} finding(s)")
    print()
    return len(hits)


def main(argv: list[str]) -> int:
    """Filter a Snyk Code SARIF report and print the governed buckets.

    Args:
        argv: A single element, the path to the SARIF report.

    Returns:
        ``0`` when the report was read and filtered, ``2`` when it is missing.
    """
    if len(argv) != 1:
        print(__doc__)
        print("usage: snyk_sarif_filter.py <report.sarif>")
        return 2
    sarif_path = Path(argv[0])
    if not sarif_path.is_file():
        print(f"SARIF MISSING at {sarif_path}")
        print("The CLI leg produced no machine-readable result: record it as")
        print("BLOCKED, never as a clean scan.")
        return 2

    report: dict[str, Any] = json.loads(sarif_path.read_text("utf-8"))
    findings = iter_findings(report)
    tracked = tracked_paths()

    tools = sorted({f["tool"] for f in findings})
    levels = Counter(f["level"] for f in findings)
    rules = Counter(f["rule"] for f in findings)

    print(f"SARIF report   : {sarif_path}")
    print(f"tool           : {', '.join(tools) or '(none)'}")
    print(f"total findings : {len(findings)}")
    print(f"result.level   : {dict(levels)}")
    print()
    print("NOTE: Snyk Code's SARIF sets result.level='note' for every finding and")
    print("carries NO severity in result.properties or rule.properties. The")
    print("authoritative severity breakdown is the CLI's own 'Test Summary' block,")
    print("which is transcribed verbatim in snyk-code-cli.txt.")
    print()

    on_disk_only = [f for f in findings if f["path"] not in tracked]
    tracked_findings = [f for f in findings if f["path"] in tracked]
    print(f"findings in git-TRACKED paths      : {len(tracked_findings)}")
    print(f"findings in untracked on-disk paths: {len(on_disk_only)}")
    untracked_roots = Counter(f["path"].split("/")[0] for f in on_disk_only)
    print(f"  untracked top-level roots: {dict(untracked_roots)}")
    print("  (snyk scans the filesystem, not git, so gitignored agent worktrees")
    print("   are counted; the same logical file is reported once per copy.)")
    print()

    print("=== rules observed ===")
    for rule, count in rules.most_common():
        print(f"  {count:4d}  {rule}")
    print()

    print("=== top 15 files by finding count ===")
    per_file = Counter(f["path"] for f in findings)
    for name, count in per_file.most_common(15):
        marker = "" if name in tracked else "   [untracked copy]"
        print(f"  {count:4d}  {name}{marker}")
    print()

    changed_hits = report_bucket(
        findings,
        "the four changed first-party source files (brief item f)",
        CHANGED_FILES,
    )
    instrument_hits = report_bucket(
        findings,
        "the six S2 audit instruments (finding EXP002D1-S2-F8)",
        S2_INSTRUMENTS,
    )

    print("=" * 74)
    print(f"changed first-party files : {changed_hits} finding(s)")
    print(f"S2 audit instruments      : {instrument_hits} finding(s)")
    print(f"repository total (raw)    : {len(findings)}")
    print(f"repository total (tracked): {len(tracked_findings)}")
    print("Severity is NOT derivable from this SARIF; read the CLI Test Summary.")
    print("=" * 74)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
