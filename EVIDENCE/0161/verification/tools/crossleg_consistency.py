"""Cross-leg consistency of run METADATA (abort criteria 4.2.1/4.2.3). Scratch tool.

Compares only environment, renderer/font-stack capture, source/protocol/input identity and
the non-path config across the five records. It never opens or compares any observation
payload: no API row, claim case, or publication file record is read or compared here, so
this cannot adjudicate H1-H4.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

RAW = Path(sys.argv[1])
RUNS = {
    "api": ("api.json", sys.argv[2]),
    "conclusions": ("conclusions.json", sys.argv[3]),
    "reference": ("reproduction.json", sys.argv[4]),
    "prin": ("reproduction.json", sys.argv[5]),
    "repeatability": ("reproduction.json", sys.argv[6]),
}


def load(mode: str) -> dict:
    name, run = RUNS[mode]
    return json.loads((RAW / run / name).read_text(encoding="utf-8"))


docs = {mode: load(mode) for mode in RUNS}
failures = 0


def report(label: str, ok: bool, detail: str = "") -> None:
    global failures
    failures += 0 if ok else 1
    print(f"{'PASS' if ok else 'FAIL'}  {label}{('  [' + detail + ']') if detail else ''}")


def same(label: str, values: dict) -> None:
    dumped = {k: json.dumps(v, sort_keys=True) for k, v in values.items()}
    report(label, len(set(dumped.values())) == 1, f"legs={sorted(values)}")


same("environment identical on all five legs (hardware, OS, interpreter, backend, dtype, SHA)",
     {m: d["environment"] for m, d in docs.items()})
same("source/protocol/input identity identical on all five legs",
     {m: {k: v for k, v in d["identity"].items()} for m, d in docs.items()})
same("config identical on all five legs apart from out_dir",
     {m: {k: v for k, v in d["config"].items() if k != "out_dir"} for m, d in docs.items()})
same("seed pair (counter,key) == (0,2) on all five legs",
     {m: [d["config"]["seed_counter"], d["config"]["seed_key"]] for m, d in docs.items()})
report("seed pair value", all((d["config"]["seed_counter"], d["config"]["seed_key"]) == (0, 2) for d in docs.values()))
same("renderer / font-stack capture identical on the three publication legs (reference, prin, repeatability)",
     {m: docs[m]["observations"]["renderer"] for m in ("reference", "prin", "repeatability")})
runs_sorted = sorted(Path(r).name for _, r in RUNS.values())
report("five distinct run directories", len(set(runs_sorted)) == 5, ", ".join(runs_sorted))
stamps = [Path(r).name.split("-")[1] for _, r in RUNS.values()]
report("run UTC stamps strictly increase in registered order", stamps == sorted(stamps) and len(set(stamps)) == 5, ", ".join(stamps))
print(f"SUMMARY: {failures} failed")
sys.exit(1 if failures else 0)
