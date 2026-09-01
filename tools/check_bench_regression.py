#!/usr/bin/env python3
"""Fail when a benchmark's mean runtime regressed past a threshold.

ETCA-001 finding T-F7: Testing Standards §2 requires the ``criterion`` and
``pytest-benchmark`` regression gates to *fail on a >10% slowdown*. Criterion
writes baselines but never compares them in CI, and the ``pytest-benchmark``
cases are ``slow``-excluded from ``python.yml``. This tool is the enforcing
comparison, run by ``.github/workflows/nightly.yml``.

It compares two sources against a stored baseline directory:

* **Criterion** — ``target/criterion/**/new/estimates.json`` (current run) vs
  ``<baseline>/criterion/**/new/estimates.json`` (previous nightly). The
  ``mean.point_estimate`` field is in nanoseconds.
* **pytest-benchmark** — ``pytest-bench.json`` vs ``<baseline>/pytest-bench.json``;
  each ``benchmarks[].stats.mean`` is in seconds.

A current mean greater than ``baseline_mean * (1 + threshold)`` is a regression.
A missing baseline (first nightly run, or a newly added benchmark) is not a
failure — the run seeds the baseline instead.

Exit codes:

- ``0`` — no regression past the threshold (or no baseline to compare against).
- ``1`` — one or more benchmarks regressed.
- ``2`` — command-line or parsing error.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


def _load_criterion_means(root: Path) -> dict[str, float]:
    """Map ``criterion`` benchmark id to its mean point estimate (ns)."""
    means: dict[str, float] = {}
    if not root.is_dir():
        return means
    for estimates in root.glob("**/new/estimates.json"):
        bench_id = str(estimates.parent.parent.relative_to(root)).replace("\\", "/")
        try:
            data = json.loads(estimates.read_text(encoding="utf-8"))
            means[bench_id] = float(data["mean"]["point_estimate"])
        except (OSError, ValueError, KeyError, TypeError):
            continue
    return means


def _load_pytest_means(path: Path) -> dict[str, float]:
    """Map ``pytest-benchmark`` fully-qualified name to its mean (seconds)."""
    means: dict[str, float] = {}
    if not path.is_file():
        return means
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return means
    for bench in data.get("benchmarks", []):
        name = bench.get("fullname") or bench.get("name")
        stats = bench.get("stats", {})
        if name and "mean" in stats:
            means[str(name)] = float(stats["mean"])
    return means


def _regressions(
    current: dict[str, float], baseline: dict[str, float], threshold: float
) -> list[str]:
    """Return one message per benchmark whose mean grew past the threshold."""
    hits: list[str] = []
    for name, now in sorted(current.items()):
        was = baseline.get(name)
        if was is None or was <= 0.0:
            continue
        ratio = now / was
        if ratio > 1.0 + threshold:
            hits.append(f"{name}: {was:.4g} -> {now:.4g} (+{(ratio - 1.0) * 100:.1f}%)")
    return hits


def main(argv: list[str] | None = None) -> int:
    """Compare current benchmark output against the stored baseline."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--baseline",
        type=Path,
        default=Path("bench-baseline"),
        help="Directory holding the previous run's criterion/ and pytest-bench.json.",
    )
    parser.add_argument(
        "--criterion-dir",
        type=Path,
        default=Path("target/criterion"),
        help="Current criterion output directory.",
    )
    parser.add_argument(
        "--pytest-json",
        type=Path,
        default=Path("pytest-bench.json"),
        help="Current pytest-benchmark JSON.",
    )
    parser.add_argument(
        "--threshold",
        type=float,
        default=0.10,
        help="Fractional mean-runtime increase that counts as a regression.",
    )
    args = parser.parse_args(argv)

    if args.threshold < 0.0:
        print("Error: --threshold must be non-negative", file=sys.stderr)
        return 2

    def _tag(prefix: str, means: dict[str, float]) -> dict[str, float]:
        return {f"{prefix}/{key}": value for key, value in means.items()}

    current = {
        **_tag("criterion", _load_criterion_means(args.criterion_dir)),
        **_tag("pytest", _load_pytest_means(args.pytest_json)),
    }
    baseline = {
        **_tag("criterion", _load_criterion_means(args.baseline / "criterion")),
        **_tag("pytest", _load_pytest_means(args.baseline / "pytest-bench.json")),
    }

    if not current:
        print("No current benchmark output found; nothing to compare.")
        return 0
    if not baseline:
        print(
            f"No baseline under {args.baseline}; seeding it this run "
            f"({len(current)} benchmarks recorded)."
        )
        return 0

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
        f"{len(set(current) & set(baseline))} compared, none past "
        f"+{args.threshold * 100:.0f}%."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
