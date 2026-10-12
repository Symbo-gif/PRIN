"""Read-only measurement of tracked-byte totals against the registered EXP-002 caps."""

from __future__ import annotations

import subprocess
from pathlib import Path

MIB = 1048576
REPO = Path(r"C:\dev\PRIN")


def size(root: Path) -> int:
    return sum(
        p.stat().st_size
        for p in root.rglob("*")
        if p.is_file() and "__pycache__" not in p.parts
    )


raw = REPO / "benchmarks/results/EXP-002"
rec = REPO / "DOCS/experiments/EXP-002-api-benchmark-result-and-reproduction-parity"
runs = sorted(p for p in raw.iterdir() if p.is_dir())
total_runs = 0
print("Per-run tracked bytes (registered cap: 2 MiB = 2,097,152 B per run):")
for run in runs:
    s = size(run)
    total_runs += s
    print(
        f"  {run.name}: {s:,} B ({s / MIB:.4f} MiB), {sum(1 for _ in run.iterdir())} entries, "
        f"headroom {2 * MIB - s:,} B"
    )
print(f"New raw run records, all five legs: {total_runs:,} B ({total_runs / MIB:.4f} MiB)")
print(f"EXP-002 raw root (runs + README.md): {size(raw):,} B ({size(raw) / MIB:.4f} MiB)")
print(f"EXP-002 record root (incl. log.md at this instant): {size(rec):,} B ({size(rec) / MIB:.4f} MiB)")
both = size(raw) + size(rec)
print(
    f"Driver closure measure, raw root + record root: {both:,} B ({both / MIB:.4f} MiB) "
    f"vs cap 10 MiB = {10 * MIB:,} B; headroom {10 * MIB - both:,} B"
)
campaign = sum(size(r) for r in (REPO / "benchmarks/results").glob("EXP-*") if r.is_dir())
print(
    f"Campaign total benchmarks/results/EXP-*: {campaign:,} B ({campaign / MIB:.3f} MiB) "
    f"vs cap 64 MiB; headroom {(64 * MIB - campaign) / MIB:.3f} MiB"
)
print("  of which EXP-001:", f"{size(REPO / 'benchmarks/results/EXP-001'):,} B")
print("log.md bytes at this instant:", f"{(rec / 'log.md').stat().st_size:,}")
# What git would track (new files = everything under the raw root and record root that is untracked)
untracked = subprocess.run(
    ["git", "ls-files", "--others", "--exclude-standard", "--", "benchmarks/results/EXP-002", str(rec.relative_to(REPO)).replace("\\", "/")],
    cwd=REPO,
    capture_output=True,
    text=True,
    check=True,
).stdout.split()
new_bytes = sum((REPO / p).stat().st_size for p in untracked)
print(f"Currently untracked new files in those roots: {len(untracked)} files, {new_bytes:,} B ({new_bytes / MIB:.4f} MiB) vs new-tracked-artefacts cap 10 MiB")
