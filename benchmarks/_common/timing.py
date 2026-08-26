"""Timing harness enforcing the Benchmarking Standards §2.2 methodology.

"Warmup iterations excluded; report median and p95 over >=10 measured
iterations." This module owns that rule in one place so every category
module gets it for free instead of re-implementing it.

Percentile/median arithmetic here is measurement-harness plumbing (the same
class of code as ``tools/wp029_control_buffer_pilot.py``'s ``_percentile``
helper), not a numerical primitive of the PRIN scientific model -- the
*measured quantities* (order parameters, tracker metrics, integration
results, ...) always come from the Rust-backed ``prin`` API.
"""

from __future__ import annotations

import time
from collections.abc import Callable
from dataclasses import dataclass
from typing import TypeVar

from benchmarks._common.config import MIN_MEASURED_ITERATIONS, BenchmarkConfigError

T = TypeVar("T")


@dataclass(frozen=True)
class TimingStats:
    """Wall-clock timing statistics over the measured (post-warmup) samples.

    Attributes:
        samples_s: Per-iteration wall-clock durations, in seconds, in
            execution order. Warmup iterations are not included.
        median_s: Median duration.
        p95_s: 95th-percentile duration (nearest-rank).
        min_s: Minimum duration.
        max_s: Maximum duration.
    """

    samples_s: tuple[float, ...]
    median_s: float
    p95_s: float
    min_s: float
    max_s: float

    def to_dict(self) -> dict[str, float | int]:
        """Serialize to the JSON-safe fields written into benchmark artefacts."""
        return {
            "iterations": len(self.samples_s),
            "median_s": self.median_s,
            "p95_s": self.p95_s,
            "min_s": self.min_s,
            "max_s": self.max_s,
        }


def _nearest_rank_percentile(sorted_samples: list[float], pct: float) -> float:
    """Nearest-rank percentile over already-sorted samples.

    Args:
        sorted_samples: Ascending samples.
        pct: Percentile in ``[0, 1]``.

    Returns:
        The sample at the nearest rank.
    """
    rank = round((len(sorted_samples) - 1) * pct)
    return sorted_samples[min(rank, len(sorted_samples) - 1)]


def timed_run(
    fn: Callable[[], T],
    *,
    iterations: int,
    warmup: int,
) -> tuple[TimingStats, T]:
    """Run ``fn`` under the Benchmarking Standards §2.2 protocol.

    Args:
        fn: Zero-argument callable to time. Called ``warmup + iterations``
            times total.
        iterations: Measured iteration count; must be
            ``>= MIN_MEASURED_ITERATIONS``.
        warmup: Warmup call count, excluded from the returned statistics.

    Returns:
        A ``(TimingStats, last_result)`` pair, where ``last_result`` is the
        return value of the final measured call (so callers can also inspect
        the measured quantity, not just its timing).

    Raises:
        BenchmarkConfigError: If ``iterations < MIN_MEASURED_ITERATIONS``.
    """
    if iterations < MIN_MEASURED_ITERATIONS:
        raise BenchmarkConfigError(
            f"iterations must be >= {MIN_MEASURED_ITERATIONS} "
            f"(Benchmarking and Reproducibility Standards §2.2), "
            f"got {iterations}"
        )

    for _ in range(warmup):
        fn()

    _unset = object()
    samples: list[float] = []
    result: T | object = _unset
    for _ in range(iterations):
        start = time.perf_counter()
        result = fn()
        samples.append(time.perf_counter() - start)

    sorted_samples = sorted(samples)
    n = len(sorted_samples)
    median = (
        sorted_samples[n // 2]
        if n % 2 == 1
        else (sorted_samples[n // 2 - 1] + sorted_samples[n // 2]) / 2.0
    )
    stats = TimingStats(
        samples_s=tuple(samples),
        median_s=median,
        p95_s=_nearest_rank_percentile(sorted_samples, 0.95),
        min_s=sorted_samples[0],
        max_s=sorted_samples[-1],
    )
    assert result is not _unset  # loop runs >= MIN_MEASURED_ITERATIONS > 0 times
    return stats, result  # type: ignore[return-value]  # narrowed by the assert above
