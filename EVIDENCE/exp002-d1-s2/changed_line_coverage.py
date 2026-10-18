r"""Measure coverage of the lines this correction actually changed.

This is the S2 audit instrument for checklist item A3's ">=95% coverage on
new/changed code" gate.

Two things make the repository's existing tooling unsuitable here:

* ``tools/coverage_changed_lines.py`` unions ``cargo-llvm-cov`` **lcov** runs
  for the feature-gated Rust GPU crates. It takes a positional ``BASE_REF``,
  one or more ``.lcov`` files and a ``-- FILE`` list; it does not read Python
  coverage data.
* The ``--cov=prin`` module form fails on this host with the PyO3 "cannot load
  module more than once" error (DV-033), which is why the path form
  ``--cov=python/prin/reporting`` is used instead.

So this instrument takes a ``coverage`` JSON report produced with the path
form, recomputes the added-line set from ``git diff -U0 <base-ref>`` for the
changed source file, and reports coverage over exactly those lines that carry
executable statements -- the same added-line algorithm the Rust tool uses, so
the two stay comparable.

Run from the repository root with the project venv, after::

    .venv/Scripts/python -m pytest tests/test_publication_figure_arguments.py \
        tests/test_publication_generation.py parity/test_parity_publication.py \
        --cov=python/prin/reporting --cov-report=json:<out>.json \
        --basetemp=.pytest_basetemp

then::

    python EVIDENCE/exp002-d1-s2/changed_line_coverage.py <out>.json \
        fd8854ed python/prin/reporting/figure_generation.py

Exit status is ``0`` when every changed executable line is covered, else ``1``.
"""

from __future__ import annotations

import hashlib
import json
import os
import subprocess  # nosec B404
import sys
import tempfile
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]

#: The gate from Testing Standards section 4 and audit checklist A3.
THRESHOLD = 95.0


def allowed_roots() -> tuple[Path, ...]:
    """Return the roots a caller-supplied input path may resolve inside.

    Returns:
        The repository root, the platform temporary root, and — when set —
        the directory named by ``PRIN_S2_SCRATCH``, each fully resolved.
    """
    roots = [ROOT, Path(tempfile.gettempdir()).resolve()]
    extra = os.environ.get("PRIN_S2_SCRATCH")
    if extra:
        roots.append(Path(extra).resolve())
    return tuple(roots)


def is_within(path: Path, root: Path) -> bool:
    """Return whether ``path`` is ``root`` itself or lives beneath it."""
    return path == root or root in path.parents


def guarded_input_path(raw: str, role: str) -> Path:
    """Resolve a caller-supplied input path safely and return it.

    Snyk Code flags an unsanitised ``argv`` path flowing into
    :class:`pathlib.Path` as CWE-23 path traversal. For an
    **evidence-producing** tool the sharper risk is integrity, not
    confidentiality: ``Path.is_file`` and ``Path.read_text`` follow symbolic
    links, so a linked input would be measured while the evidence named a
    different file — the "content verified, path provenance not" failure mode
    that audit finding ``PR23-F1`` fixed in ``tools/reproduce.py``. This guard
    therefore mirrors that module's no-follow discipline and additionally
    confines the *resolved* path to :func:`allowed_roots`, so a symlinked
    parent directory pointing outside is also refused.

    Args:
        raw: The path exactly as passed on the command line.
        role: Human-readable role used in any failure message.

    Returns:
        The resolved, confined path to a regular file.

    Raises:
        SystemExit: If the path is a symbolic link, is not a regular file, or
            resolves outside every allowed root.
    """
    candidate = Path(raw)
    if ".." in raw.replace("\\", "/").split("/"):
        raise SystemExit(f"{role}: refusing a path containing a '..' component: {raw}")
    if candidate.is_symlink():
        raise SystemExit(f"{role}: refusing symbolic link {candidate}")
    if candidate.exists() and not candidate.is_file():
        raise SystemExit(f"{role}: {candidate} is not a regular file")
    resolved = candidate.resolve()
    roots = allowed_roots()
    if not any(is_within(resolved, root) for root in roots):
        listed = ", ".join(str(root) for root in roots)
        raise SystemExit(f"{role}: {resolved} is outside the allowed roots ({listed})")
    if not resolved.is_file():
        raise SystemExit(f"{role}: no regular file at {resolved}")
    return resolved


def added_lines(base_ref: str, relative_path: str) -> set[int]:
    """Return the line numbers ``git diff -U0`` reports as added or changed.

    Args:
        base_ref: The diff base, normally the branch point.
        relative_path: The repository-relative file to diff.

    Returns:
        The set of added line numbers in the post-image.
    """
    completed = subprocess.run(  # noqa: S603  # nosec B603 B607
        ["git", "diff", "-U0", base_ref, "--", relative_path],  # noqa: S607
        capture_output=True,
        text=True,
        check=True,
        cwd=ROOT,
    )
    out: set[int] = set()
    current: int | None = None
    for line in completed.stdout.splitlines():
        if line.startswith("@@"):
            plus = line.split("+", 1)[1].split("@@", 1)[0].strip()
            current = int(plus.split(",", 1)[0])
        elif line.startswith("+") and not line.startswith("+++"):
            if current is not None:
                out.add(current)
                current += 1
        elif line.startswith(" ") and current is not None:
            current += 1
    return out


def sha256(path: Path) -> str:
    """Return the SHA-256 of a file's bytes, to tie evidence to exact content."""
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load_report(path: Path) -> dict[str, Any]:
    """Return a coverage JSON report parsed into a dictionary."""
    payload: dict[str, Any] = json.loads(path.read_text("utf-8"))
    return payload


def find_file_entry(report: dict[str, Any], relative_path: str) -> dict[str, Any]:
    """Return the coverage report entry for ``relative_path``.

    Args:
        report: A parsed coverage JSON report.
        relative_path: The repository-relative source file.

    Returns:
        That file's entry from the report's ``files`` mapping.

    Raises:
        SystemExit: If the file carries no coverage data at all.
    """
    files: dict[str, Any] = report.get("files", {})
    wanted = relative_path.replace("\\", "/")
    for key, value in files.items():
        if key.replace("\\", "/").endswith(wanted):
            entry: dict[str, Any] = value
            return entry
    raise SystemExit(
        f"no coverage data for {relative_path}; report covers {sorted(files)}"
    )


def main(argv: list[str]) -> int:
    """Report changed-line coverage and return non-zero below the threshold.

    Args:
        argv: ``<coverage-json> <base-ref> <relative-source-path>``.

    Returns:
        ``0`` when changed executable lines are fully covered, else ``1``.
    """
    if len(argv) != 3:
        print(__doc__)
        print("usage: changed_line_coverage.py <coverage.json> <base-ref> <path>")
        return 2
    base_ref, relative_path = argv[1], argv[2]
    report_path = guarded_input_path(argv[0], "coverage report")
    if not report_path.is_file():
        print(f"ABORT: coverage report not found at {report_path}")
        return 2

    report = load_report(report_path)
    entry = find_file_entry(report, relative_path)
    summary = entry.get("summary", {})
    executed: set[int] = set(entry.get("executed_lines", []))
    missing: set[int] = set(entry.get("missing_lines", []))
    excluded: set[int] = set(entry.get("excluded_lines", []))

    changed = added_lines(base_ref, relative_path)
    instrumented = {n for n in changed if n in executed or n in missing}
    covered = changed & executed
    uncovered = sorted(changed & missing)
    non_executable = sorted(changed - instrumented - excluded)

    print(f"coverage report : {report_path}")
    print(f"  resolved+confined, no symlink followed; sha256 {sha256(report_path)}")
    print(f"source file     : {relative_path}")
    print(f"diff base       : {base_ref}")
    print()
    print("=== whole-file coverage (as reported) ===")
    print(f"  num_statements : {summary.get('num_statements')}")
    print(f"  covered_lines  : {summary.get('covered_lines')}")
    print(f"  missing_lines  : {summary.get('missing_lines')}")
    print(f"  percent_covered: {summary.get('percent_covered')}")
    print(f"  missing line numbers: {sorted(missing)}")
    print()
    print("=== changed-line coverage (the A3 gate) ===")
    print(f"  lines added/changed by the diff : {len(changed)}")
    print(f"  of those, executable statements : {len(instrumented)}")
    print(f"  executed                        : {len(covered)}")
    print(f"  NOT executed                    : {len(uncovered)} {uncovered or ''}")
    print(
        f"  non-executable (docstring/blank/"
        f"continuation/decorator): {len(non_executable)}"
    )
    if instrumented:
        percent = 100.0 * len(covered) / len(instrumented)
    else:
        percent = 100.0
    print(f"  changed-executable coverage     : {percent:.2f}% (gate >= {THRESHOLD}%)")
    print()
    print("=" * 74)
    ok = percent >= THRESHOLD and not uncovered
    print(
        f"RESULT: {'PASS' if ok else 'FAIL'} -- {len(covered)}/{len(instrumented)} "
        f"changed executable lines covered ({percent:.2f}%)"
    )
    print("=" * 74)
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
