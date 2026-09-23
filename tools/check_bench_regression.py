#!/usr/bin/env python3
"""Fail when a benchmark's mean runtime regressed past a threshold.

ETCA-001 finding T-F7: Testing Standards §2 requires the ``criterion`` and
``pytest-benchmark`` regression gates to fail on a >10% slowdown. The
DV-036 correction compares fresh reference and candidate measurements from
one runner job, not timings cached from an unrelated hosted machine.

Criterion means come from ``**/new/estimates.json`` (nanoseconds); pytest
means come from ``benchmarks[].stats.mean`` (seconds). Both sources must be
nonempty in every run and contain exactly matching benchmark identities.
Missing, malformed, duplicate, non-finite, or nonpositive observations are
input errors, never a baseline-seeding success or a partial comparison.

DV036-F4: each arm may be measured more than once (the nightly uses the
counterbalanced order reference, candidate, candidate, reference) and an
arm's mean is the arithmetic mean of its runs, which cancels linear host
drift. ``--advisory`` identity prefixes are compared and reported but never
fail the gate; every prefix must be nonblank and match a benchmark.

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


def _load_arm(run: Path) -> dict[str, float]:
    """Load one run's mandatory sources with disjoint identity prefixes."""
    return {
        **{
            f"criterion/{key}": value
            for key, value in _load_criterion_means(run / "criterion").items()
        },
        **{
            f"pytest/{key}": value
            for key, value in _load_pytest_means(run / "pytest-bench.json").items()
        },
    }


def _require_same_identities(
    first: dict[str, float], other: dict[str, float], context: str
) -> None:
    """Reject two measurement sets that do not name exactly the same cases."""
    if first.keys() != other.keys():
        missing = sorted(first.keys() - other.keys())
        extra = sorted(other.keys() - first.keys())
        raise BenchmarkInputError(
            f"Benchmark identities differ ({context}): missing={missing}; "
            f"unexpected={extra}"
        )


def _load_arm_runs(runs: list[Path]) -> dict[str, float]:
    """Average every benchmark mean over all runs of one arm."""
    loaded = [_load_arm(run) for run in runs]
    for run, means in zip(runs[1:], loaded[1:], strict=True):
        _require_same_identities(loaded[0], means, f"{runs[0]} vs {run}")
    return {
        name: math.fsum(means[name] for means in loaded) / len(loaded)
        for name in loaded[0]
    }


def _split_advisory(names: set[str], prefixes: list[str]) -> tuple[set[str], set[str]]:
    """Partition identities into gated and advisory by nonblank, used prefixes."""
    advisory: set[str] = set()
    for prefix in prefixes:
        if not prefix.strip():
            raise BenchmarkInputError("--advisory prefix must be nonblank")
        matched = {name for name in names if name.startswith(prefix)}
        if not matched:
            raise BenchmarkInputError(f"--advisory prefix matches nothing: {prefix}")
        advisory |= matched
    return names - advisory, advisory


def main(argv: list[str] | None = None) -> int:
    """Compare complete, matched measurements from the reference and candidate."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--reference",
        type=Path,
        nargs="+",
        required=True,
        help="Reference run directories, each with criterion/ and pytest-bench.json.",
    )
    parser.add_argument(
        "--candidate",
        type=Path,
        nargs="+",
        required=True,
        help="Candidate run directories, each with criterion/ and pytest-bench.json.",
    )
    parser.add_argument(
        "--threshold",
        type=float,
        default=0.10,
        help="Fractional mean-runtime increase that counts as a regression.",
    )
    parser.add_argument(
        "--advisory",
        action="append",
        default=[],
        help="Identity prefix compared and reported but not gating (repeatable).",
    )
    args = parser.parse_args(argv)
    if not math.isfinite(args.threshold) or args.threshold < 0.0:
        print("Error: --threshold must be finite and non-negative", file=sys.stderr)
        return 2
    try:
        current = _load_arm_runs(args.candidate)
        baseline = _load_arm_runs(args.reference)
        _require_same_identities(baseline, current, "reference vs candidate")
        gated, advisory = _split_advisory(set(current), args.advisory)
    except BenchmarkInputError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 2
    for name in sorted(current):
        ratio = current[name] / baseline[name]
        tag = "  ADVISORY" if name in advisory else ""
        print(f"{ratio:7.3f}  {baseline[name]:.4g} -> {current[name]:.4g}  {name}{tag}")
    advisory_hits = _regressions(
        {name: current[name] for name in advisory}, baseline, args.threshold
    )
    for line in advisory_hits:
        print(f"ADVISORY (not gating) past threshold: {line}")
    regressions = _regressions(
        {name: current[name] for name in gated}, baseline, args.threshold
    )
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
        f"Benchmark regression check passed: {len(current)} benchmarks "
        f"({len(gated)} gated, {len(advisory)} advisory), none gated past "
        f"+{args.threshold * 100:.0f}%; {len(args.reference)} reference and "
        f"{len(args.candidate)} candidate runs."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
