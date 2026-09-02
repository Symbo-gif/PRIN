#!/usr/bin/env python3
r"""Union changed-line coverage for the feature-gated Rust GPU crates.

``prin-kernels`` / ``prin-sim`` device code is feature-gated: a given
``#[cfg(feature = ...)]`` branch (the CUDA on-device ``f64`` finalize vs. the
host ``f64`` combine; the whole ``prin-sim::gpu`` module is
``#[cfg(any(cpu, wgpu, cuda))]``) is only reachable under the matching feature.
``cargo-llvm-cov`` measures one feature set per run, so this tool unions
several ``--lcov`` runs and reports coverage of the lines a diff range added.

Usage: run ``cargo llvm-cov ... --lcov --output-path <cell>.lcov`` once per
feature-matrix cell (nofeat / cpu / wgpu / cuda / cuda,wgpu), then::

    python tools/coverage_changed_lines.py BASE_REF \
        cov-nofeat.lcov cov-cpu.lcov cov-wgpu.lcov cov-cuda.lcov cov-cw.lcov \
        -- FILE [FILE ...]

Lines ``cargo-llvm-cov`` cannot instrument (``#[cube(launch)]`` kernel bodies,
DV-004) must be excluded by the caller when judging the >=95% gate; this tool
prints the raw union number and the per-file uncovered line list so that
exclusion stays auditable.
"""

from __future__ import annotations

import collections
import subprocess
import sys


def changed_lines(base_ref: str, path: str) -> set[int]:
    """Return added/changed line numbers in ``path`` vs ``base_ref`` (working tree)."""
    diff = subprocess.run(  # noqa: S603 - fixed argv, `git` resolved via PATH by design
        ["git", "diff", "-U0", base_ref, "--", path],  # noqa: S607
        capture_output=True,
        text=True,
        check=True,
    ).stdout
    out: set[int] = set()
    newln: int | None = None
    for line in diff.splitlines():
        if line.startswith("@@"):
            plus = line.split("+", 1)[1].split("@@", 1)[0].strip()
            newln = int(plus.split(",", 1)[0])
        elif line.startswith("+") and not line.startswith("+++"):
            if newln is not None:
                out.add(newln)
                newln += 1
        elif line.startswith(" ") and newln is not None:
            newln += 1
    return out


def lcov_hits(paths: list[str]) -> dict[str, dict[int, int]]:
    """Return the union of ``DA:`` records across ``paths``, keyed by source path."""
    hits: dict[str, dict[int, int]] = collections.defaultdict(dict)
    for lcov in paths:
        cur: str | None = None
        with open(lcov, encoding="utf-8") as handle:
            for raw in handle:
                line = raw.strip()
                if line.startswith("SF:"):
                    cur = line[3:].replace("\\", "/")
                elif line.startswith("DA:") and cur:
                    num, count = (int(x) for x in line[3:].split(",")[:2])
                    hits[cur][num] = max(hits[cur].get(num, 0), count)
    return hits


def main(argv: list[str]) -> int:
    """Print per-file and union changed-line coverage; return a process exit code."""
    if "--" not in argv:
        sys.exit(__doc__)
    split = argv.index("--")
    base_ref, *lcovs = argv[:split]
    files = argv[split + 1 :]
    if not base_ref or not lcovs or not files:
        sys.exit(__doc__)

    hits = lcov_hits(lcovs)

    def lookup(path: str) -> dict[int, int]:
        merged: dict[int, int] = {}
        for key, line_hits in hits.items():
            if key.endswith(path):
                for num, count in line_hits.items():
                    merged[num] = max(merged.get(num, 0), count)
        return merged

    total_cov = total_unc = 0
    for path in files:
        table = lookup(path)
        covered = uncovered = 0
        unc: list[int] = []
        for num in sorted(changed_lines(base_ref, path)):
            if num not in table:
                continue
            if table[num] > 0:
                covered += 1
            else:
                uncovered += 1
                unc.append(num)
        total_cov += covered
        total_unc += uncovered
        inst = covered + uncovered
        pct = 100.0 * covered / inst if inst else 100.0
        print(
            f"{path}: instrumentable={inst} covered={covered} "
            f"uncovered={uncovered}  {pct:.2f}%"
        )
        if unc:
            print(f"    uncovered: {unc}")

    inst = total_cov + total_unc
    pct = 100.0 * total_cov / inst if inst else 100.0
    print(
        f"\nUNION TOTAL instrumentable changed lines: {inst}  "
        f"covered={total_cov}  uncovered={total_unc}  {pct:.2f}%"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
