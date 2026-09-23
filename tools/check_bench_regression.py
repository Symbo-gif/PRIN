#!/usr/bin/env python3
"""Fail when a benchmark's mean runtime regressed past a threshold.

ETCA-001 finding T-F7: Testing Standards §2 requires the ``criterion`` and
``pytest-benchmark`` regression gates to fail on a >10% slowdown. The
DV-036 correction compares fresh reference and candidate measurements from
one runner job, not timings cached from an unrelated hosted machine.

Criterion means come from ``**/new/estimates.json`` (nanoseconds); pytest
means come from ``benchmarks[].stats.mean`` (seconds). Both sources must be
nonempty in both arms and contain exactly matching benchmark identities.
Missing, malformed, duplicate, non-finite, or nonpositive observations are
input errors, never a baseline-seeding success or a partial comparison.

Exit codes: 0 for a complete passing comparison, 1 for a regression, and 2
for invalid arguments or evidence. A missing baseline never passes.
"""

from __future__ import annotations

import argparse
import json
import math
import sys
from pathlib import Path
from typing import Any


class BenchmarkInputError(ValueError):
    """Raised when benchmark evidence cannot support a complete comparison."""


def _read_object(path: Path) -> dict[str, Any]:
    """Read a benchmark JSON object without silently discarding bad input."""
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, ValueError) as exc:
        raise BenchmarkInputError(f"Cannot read {path}: {exc}") from exc
    if not isinstance(data, dict):
        raise BenchmarkInputError(f"{path}: expected a JSON object")
    return data


def _positive_mean(value: object, location: str) -> float:
    """Validate a measured mean as a finite, positive JSON number."""
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise BenchmarkInputError(f"{location}: mean must be a number")
    try:
        mean = float(value)
    except OverflowError as exc:
        raise BenchmarkInputError(f"{location}: mean is out of range") from exc
    if not math.isfinite(mean) or mean <= 0.0:
        raise BenchmarkInputError(f"{location}: mean must be finite and positive")
    return mean


def _load_criterion_means(root: Path) -> dict[str, float]:
    """Map every Criterion benchmark identity to its validated mean (ns)."""
    paths = sorted(root.glob("**/new/estimates.json")) if root.is_dir() else []
    if not paths:
        raise BenchmarkInputError(f"No Criterion measurements under {root}")
    means: dict[str, float] = {}
    for estimates in paths:
        bench_id = estimates.parent.parent.relative_to(root).as_posix()
        data = _read_object(estimates)
        mean = data.get("mean")
        if not isinstance(mean, dict):
            raise BenchmarkInputError(f"{estimates}: missing mean object")
        means[bench_id] = _positive_mean(mean.get("point_estimate"), str(estimates))
    return means


def _load_pytest_means(path: Path) -> dict[str, float]:
    """Map unique pytest-benchmark identities to validated means (seconds)."""
    data = _read_object(path)
    benchmarks = data.get("benchmarks")
    if not isinstance(benchmarks, list) or not benchmarks:
        raise BenchmarkInputError(f"{path}: benchmarks must be a nonempty list")
    means: dict[str, float] = {}
    for bench in benchmarks:
        if not isinstance(bench, dict):
            raise BenchmarkInputError(f"{path}: benchmark must be an object")
        name = bench.get("fullname") or bench.get("name")
        if not isinstance(name, str) or not name.strip():
            raise BenchmarkInputError(f"{path}: benchmark identity is missing")
        if name in means:
            raise BenchmarkInputError(f"{path}: duplicate benchmark {name}")
        stats = bench.get("stats")
        if not isinstance(stats, dict):
            raise BenchmarkInputError(f"{path}: {name} has no stats object")
        means[name] = _positive_mean(stats.get("mean"), f"{path}: {name}")
    return means


def _regressions(
    current: dict[str, float], baseline: dict[str, float], threshold: float
) -> list[str]:
    """Return each mean-runtime increase exceeding the registered threshold."""
    hits: list[str] = []
    for name, now in sorted(current.items()):
        was = baseline[name]
        ratio = now / was
        if ratio > 1.0 + threshold:
            hits.append(f"{name}: {was:.4g} -> {now:.4g} (+{(ratio - 1.0) * 100:.1f}%)")
    return hits


def _load_arm(criterion_dir: Path, pytest_json: Path) -> dict[str, float]:
    """Load both mandatory measurement sources with disjoint identity prefixes."""
    return {
        **{
            f"criterion/{key}": value
            for key, value in _load_criterion_means(criterion_dir).items()
        },
        **{
            f"pytest/{key}": value
            for key, value in _load_pytest_means(pytest_json).items()
        },
    }


def main(argv: list[str] | None = None) -> int:
    """Compare complete, matched measurements from the reference and candidate."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--baseline",
        type=Path,
        default=Path("bench-baseline"),
        help="Reference directory containing criterion/ and pytest-bench.json.",
    )
    parser.add_argument(
        "--criterion-dir",
        type=Path,
        default=Path("target/criterion"),
        help="Fresh candidate Criterion output directory.",
    )
    parser.add_argument(
        "--pytest-json",
        type=Path,
        default=Path("pytest-bench.json"),
        help="Fresh candidate pytest-benchmark JSON.",
    )
    parser.add_argument(
        "--threshold",
        type=float,
        default=0.10,
        help="Fractional mean-runtime increase that counts as a regression.",
    )
    args = parser.parse_args(argv)
    if not math.isfinite(args.threshold) or args.threshold < 0.0:
        print("Error: --threshold must be finite and non-negative", file=sys.stderr)
        return 2
    try:
        current = _load_arm(args.criterion_dir, args.pytest_json)
        baseline = _load_arm(
            args.baseline / "criterion", args.baseline / "pytest-bench.json"
        )
        if current.keys() != baseline.keys():
            missing = sorted(baseline.keys() - current.keys())
            extra = sorted(current.keys() - baseline.keys())
            raise BenchmarkInputError(
                f"Benchmark identities differ: missing candidate={missing}; "
                f"missing reference={extra}"
            )
    except BenchmarkInputError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 2
    regressions = _regressions(current, baseline, args.threshold)
    if regressions:
        print(
            f"Benchmark regression check FAILED "
            f"(threshold +{args.threshold * 100:.0f}% mean runtime):",
            file=sys.stderr,
        )
        for line in regressions:
            print(f"  - {line}", file=sys.stderr)
        return 1
    print(
        f"Benchmark regression check passed: {len(current)} benchmarks, "
        f"{len(current)} compared, none past +{args.threshold * 100:.0f}%."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
