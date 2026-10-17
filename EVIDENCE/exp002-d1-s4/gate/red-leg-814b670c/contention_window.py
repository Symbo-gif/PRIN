"""Measure host contention in the window where the required-leg assertion failed.

Testing Standards section 7 item 3 forbids recording a guessed attribution as
cause, so this reads the sampler that ran alongside pytest and reports the
samples bracketing the failure window, plus the whole-leg distribution.

Usage: python contention_window.py <samples.jsonl> <start HH:MM:SS> <end HH:MM:SS>
"""

from __future__ import annotations

import json
import statistics
import sys
from pathlib import Path


def hhmmss(stamp: str) -> str:
    return stamp[11:19]


def main(argv: list[str]) -> int:
    path = Path(argv[0])
    lo, hi = argv[1], argv[2]
    rows = [json.loads(line) for line in path.read_text("utf-8").splitlines() if line]
    rows.sort(key=lambda r: r["utc"])

    print(f"source: {path}")
    print(f"samples: {len(rows)}  span {hhmmss(rows[0]['utc'])} .. {hhmmss(rows[-1]['utc'])}")

    cpu = [r["host"]["cpu_percent"] for r in rows]
    eff = [
        r["pytest"]["cpu_seconds"] / r["t"]
        for r in rows
        if r.get("pytest") and r["t"] > 0
    ]
    print()
    print("== whole-leg host contention ==")
    print(f"  host cpu_percent : median {statistics.median(cpu):.1f}  "
          f"mean {statistics.mean(cpu):.1f}  max {max(cpu):.1f}")
    print(f"  samples >= 90%   : {sum(1 for c in cpu if c >= 90.0)} / {len(cpu)}")
    print(f"  samples >= 95%   : {sum(1 for c in cpu if c >= 95.0)} / {len(cpu)}")
    if eff:
        print(f"  pytest cpu-s/wall-s: median {statistics.median(eff):.3f}")

    print()
    print(f"== samples bracketing the failure window {lo} .. {hi} ==")
    window = [r for r in rows if lo <= hhmmss(r["utc"]) <= hi]
    if not window:
        print("  (no sample fell inside the window; showing nearest before/after)")
        before = [r for r in rows if hhmmss(r["utc"]) < lo]
        after = [r for r in rows if hhmmss(r["utc"]) > hi]
        window = ([before[-1]] if before else []) + ([after[0]] if after else [])
    for r in window:
        h = r["host"]
        p = r.get("pytest") or {}
        k = r.get("kernels") or []
        print(f"  {hhmmss(r['utc'])}Z t={r['t']:.0f}s "
              f"host_cpu={h['cpu_percent']:.1f}% avail_mb={h['available_mb']:.0f} "
              f"mem={h['memory_percent']:.1f}%")
        print(f"      pytest: procs={p.get('processes')} "
              f"cpu_s={p.get('cpu_seconds')} threads={p.get('threads')}")
        if k:
            print(f"      jupyter kernels live: {len(k)} "
                  f"cpu_s={[round(x['cpu_seconds'], 1) for x in k]}")
        others = r.get("top_other_cpu_since_last_sample") or []
        top = ", ".join(f"{o['name']}={o['cpu_seconds']:.1f}s" for o in others[:5])
        print(f"      other cpu since last sample: {top}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
