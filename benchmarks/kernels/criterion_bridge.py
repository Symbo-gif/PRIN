"""Subprocess bridge to the `prin-kernels` `criterion` benches.

Runs `cargo bench -p prin-kernels`, then republishes each bench's
`target/criterion/<group>/<function>/new/estimates.json` under the unified
`benchrunner` envelope. No numerical computation happens in this module --
every measured nanosecond comes from `criterion`.
"""

from __future__ import annotations

import json
import shutil
import subprocess
from pathlib import Path
from typing import Any, NamedTuple

from benchmarks._common.config import (
    MIN_MEASURED_ITERATIONS,
    BenchmarkConfig,
    BenchmarkConfigError,
)
from benchmarks._common.registry import register

_REPO_ROOT = Path(__file__).resolve().parents[2]
_CRITERION_DIR = _REPO_ROOT / "target" / "criterion"


class CriterionBenchNotFoundError(RuntimeError):
    """Raised when `cargo` is unavailable or a bench produces no estimates.json."""


class CriterionBenchTarget(NamedTuple):
    """One `criterion` `(group, function)` pair inside a bench binary."""

    binary: str
    group: str
    function: str


#: The CPU-backend `criterion` targets currently defined in
#: `crates/prin-kernels/benches/*.rs` (grep-verified against
#: `benchmark_group`/`bench_function` calls). `wgpu`/`cuda` targets exist in
#: the same files but require GPU hardware/features not assumed here,
#: matching the established `rust.yml --features cpu` CI convention.
CPU_TARGETS: tuple[CriterionBenchTarget, ...] = (
    CriterionBenchTarget("mean_field_rk4_bench", "mean_field_rk4_n1m", "cpu_native"),
    CriterionBenchTarget(
        "discrete_step_bench", "discrete_step_3band", "fused_cpu_native"
    ),
    CriterionBenchTarget(
        "discrete_step_bench", "discrete_step_3band", "unfused_cpu_native"
    ),
    CriterionBenchTarget("sparse_knn_bench", "sparse_knn_n16k_k14", "cpu_native"),
)


def _cargo_path() -> str:
    cargo = shutil.which("cargo")
    if cargo is None:
        raise CriterionBenchNotFoundError("cargo executable not found on PATH")
    return cargo


def criterion_args(
    binary: str, *, sample_size: int, warmup_s: float, measurement_s: float
) -> list[str]:
    """Build the `cargo bench` argument list for one bench binary.

    Pure function (no subprocess execution) so its shape is independently
    testable.
    """
    return [
        _cargo_path(),
        "bench",
        "-p",
        "prin-kernels",
        "--features",
        "cpu",
        "--bench",
        binary,
        "--",
        "--sample-size",
        str(sample_size),
        "--warm-up-time",
        str(warmup_s),
        "--measurement-time",
        str(measurement_s),
    ]


def run_cargo_bench(
    binary: str, *, sample_size: int, warmup_s: float, measurement_s: float
) -> None:
    """Run one `criterion` bench binary to completion via a real subprocess.

    Raises:
        CriterionBenchNotFoundError: If `cargo` is missing or exits non-zero.
    """
    args = criterion_args(
        binary, sample_size=sample_size, warmup_s=warmup_s, measurement_s=measurement_s
    )
    completed = subprocess.run(
        args, cwd=_REPO_ROOT, capture_output=True, text=True, check=False
    )
    if completed.returncode != 0:
        raise CriterionBenchNotFoundError(
            f"cargo bench -p prin-kernels --bench {binary} failed "
            f"(exit {completed.returncode}): {completed.stderr[-2000:]}"
        )


def _estimates_path(target: CriterionBenchTarget) -> Path:
    return _CRITERION_DIR / target.group / target.function / "new" / "estimates.json"


def parse_estimates(path: Path) -> dict[str, Any]:
    """Extract the fields this bridge republishes from a `criterion` `estimates.json`.

    Raises:
        CriterionBenchNotFoundError: If ``path`` does not exist.
    """
    if not path.is_file():
        raise CriterionBenchNotFoundError(f"no criterion estimates at {path}")
    raw = json.loads(path.read_text(encoding="utf-8"))
    return {
        "mean_ns": raw["mean"]["point_estimate"],
        "median_ns": raw["median"]["point_estimate"],
        "std_dev_ns": raw["std_dev"]["point_estimate"],
    }


@register(
    "kernels",
    "criterion_suite",
    summary="Republish prin-kernels criterion (CPU) results in the benchrunner schema",
)
def kernel_criterion_suite(config: BenchmarkConfig) -> dict[str, Any]:
    """Run every CPU `criterion` target in :data:`CPU_TARGETS` and collect results.

    ``config.iterations`` maps to criterion's ``--sample-size`` (criterion's
    own minimum is 10, matching Benchmarking Standards §2.2).
    ``config.params`` may override ``warmup_s`` and ``measurement_s`` (both
    seconds), which otherwise default to criterion's own defaults (3s/5s).

    Raises:
        BenchmarkConfigError: If ``config.iterations < MIN_MEASURED_ITERATIONS``.
    """
    if config.iterations < MIN_MEASURED_ITERATIONS:
        raise BenchmarkConfigError(
            f"iterations must be >= {MIN_MEASURED_ITERATIONS}, got {config.iterations}"
        )
    warmup_s = float(config.params.get("warmup_s", 3.0))
    measurement_s = float(config.params.get("measurement_s", 5.0))

    results: dict[str, Any] = {}
    for target in CPU_TARGETS:
        run_cargo_bench(
            target.binary,
            sample_size=config.iterations,
            warmup_s=warmup_s,
            measurement_s=measurement_s,
        )
        results[f"{target.group}/{target.function}"] = parse_estimates(
            _estimates_path(target)
        )

    return {
        "benchmark": "kernel_criterion_suite",
        "backend": "cpu",
        "dtype": "f32/f64 (per-kernel; see crates/prin-kernels)",
        "targets": results,
    }
