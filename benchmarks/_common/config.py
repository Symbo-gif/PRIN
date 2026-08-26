"""Shared benchmark configuration.

A single, serializable configuration type threaded through every category
module and the ``benchrunner`` CLI, so iteration/warmup/seed policy is
defined once (Mission: "shared configuration/environment capture").
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

#: Benchmarking and Reproducibility Standards §2.2: "report median and p95
#: over >=10 measured iterations".
MIN_MEASURED_ITERATIONS = 10

DEFAULT_RESULTS_DIR = Path("benchmarks") / "results"


class BenchmarkConfigError(ValueError):
    """Raised when a :class:`BenchmarkConfig` violates a Benchmarking Standard."""


@dataclass(frozen=True)
class BenchmarkConfig:
    """Configuration shared by every benchmark function.

    Attributes:
        iterations: Measured iteration count. Must be ``>= MIN_MEASURED_ITERATIONS``
            (Benchmarking Standards §2.2).
        warmup: Warmup iterations executed and discarded before timing starts.
        seed_counter: Counter half of the deterministic ``Seed``.
        seed_key: Key half of the deterministic ``Seed``.
        out_dir: Directory results are written to. Must resolve inside the
            repository's declared output roots (Coding Standards §6.1).
        params: Category-specific parameters (problem sizes, coupling mode,
            etc.), opaque to the shared infrastructure.
    """

    iterations: int = MIN_MEASURED_ITERATIONS
    warmup: int = 2
    seed_counter: int = 0
    seed_key: int = 0
    out_dir: Path = DEFAULT_RESULTS_DIR
    params: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if self.iterations < MIN_MEASURED_ITERATIONS:
            raise BenchmarkConfigError(
                f"iterations must be >= {MIN_MEASURED_ITERATIONS} "
                f"(Benchmarking and Reproducibility Standards §2.2), "
                f"got {self.iterations}"
            )
        if self.warmup < 0:
            raise BenchmarkConfigError(f"warmup must be >= 0, got {self.warmup}")
