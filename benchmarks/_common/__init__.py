"""Shared benchmark driver infrastructure: config, environment capture,
timing harness, registry, and result serialization.

Every category package (`scaling/`, `chimera/`, `mot/`, `ablations/`,
`kernels/`, `integrators/`, `training/`, `daemon/`, `adversarial/`) is built
on this module instead of re-implementing iteration/warmup policy,
environment capture, or JSON output.
"""

from __future__ import annotations

from benchmarks._common.config import (
    MIN_MEASURED_ITERATIONS,
    BenchmarkConfig,
    BenchmarkConfigError,
)
from benchmarks._common.environment import capture_environment
from benchmarks._common.registry import (
    CATEGORIES,
    BenchmarkSpec,
    RegistryError,
    get,
    list_specs,
    register,
)
from benchmarks._common.result import (
    ArtefactExistsError,
    OutputPathError,
    write_json_exclusive,
    write_result,
)
from benchmarks._common.timing import TimingStats, timed_run

__all__ = [
    "CATEGORIES",
    "MIN_MEASURED_ITERATIONS",
    "ArtefactExistsError",
    "BenchmarkConfig",
    "BenchmarkConfigError",
    "BenchmarkSpec",
    "OutputPathError",
    "RegistryError",
    "TimingStats",
    "capture_environment",
    "get",
    "list_specs",
    "register",
    "timed_run",
    "write_json_exclusive",
    "write_result",
]
