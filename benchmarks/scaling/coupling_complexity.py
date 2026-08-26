"""Coupling-mode complexity comparison: O(N) mean-field vs. O(N log N) sparse
k-NN vs. O(N^2) full pairwise, at matched oscillator counts.

Rust-backed successor to PRINet 3.0's `coupling_complexity_benchmark.py`,
`on_vs_onlogn_benchmark.py`, `pairwise_coupling_scaling.py`, and
`scientific_coupling_benchmark.py`.
"""

from __future__ import annotations

from typing import Any

from prin.dynamics import (
    CouplingMode,
    KuramotoOscillator,
    OscillatorState,
    RK4Integrator,
    Seed,
)

from benchmarks._common.config import BenchmarkConfig
from benchmarks._common.registry import register
from benchmarks._common.timing import timed_run

_DEFAULT_SIZES: tuple[int, ...] = (64, 256)
_DEFAULT_N_STEPS = 20
_DEFAULT_DT = 0.01
_DEFAULT_K_NEIGHBORS = 8
_MODES: tuple[str, ...] = ("mean_field", "sparse_knn", "full")


def _coupling_mode(name: str, k_neighbors: int) -> CouplingMode:
    if name == "mean_field":
        return CouplingMode.mean_field()
    if name == "sparse_knn":
        return CouplingMode.sparse_knn(k_neighbors)
    if name == "full":
        return CouplingMode.full()
    raise ValueError(f"unknown coupling mode {name!r}")


def _run_once(
    n: int, mode_name: str, k_neighbors: int, n_steps: int, dt: float, seed: Seed
) -> None:
    model = KuramotoOscillator(
        n_oscillators=n,
        coupling_strength=2.0 / n,
        decay_rate=0.1,
        freq_adaptation_rate=0.0,
        coupling_mode=_coupling_mode(mode_name, k_neighbors),
    )
    state = OscillatorState.create_random(n, (0.5, 1.5), seed)
    RK4Integrator().integrate_fixed(model, state, n_steps, dt)


@register(
    "scaling",
    "coupling_complexity",
    summary="Wall time vs. N for mean_field/sparse_knn/full coupling modes",
)
def coupling_complexity_scaling(config: BenchmarkConfig) -> dict[str, Any]:
    """Sweep N for each coupling mode; asymptotic behavior is visible in
    ``wall_time_s`` growth across ``modes[*].scales``.

    ``config.params`` may override ``sizes``, ``n_steps``, ``dt``, and
    ``k_neighbors``.
    """
    sizes: tuple[int, ...] = tuple(config.params.get("sizes", _DEFAULT_SIZES))
    n_steps: int = int(config.params.get("n_steps", _DEFAULT_N_STEPS))
    dt: float = float(config.params.get("dt", _DEFAULT_DT))
    k_neighbors: int = int(config.params.get("k_neighbors", _DEFAULT_K_NEIGHBORS))
    seed = Seed(config.seed_counter, config.seed_key)

    modes: list[dict[str, Any]] = []
    for mode_name in _MODES:
        scales: list[dict[str, Any]] = []
        for n in sizes:
            k = min(k_neighbors, n - 1) if n > 1 else 0
            stats, _ = timed_run(
                lambda n=n, mode_name=mode_name, k=k: _run_once(
                    n, mode_name, k, n_steps, dt, seed
                ),
                iterations=config.iterations,
                warmup=config.warmup,
            )
            scales.append(
                {
                    "N": n,
                    "wall_time_s": stats.median_s,
                    "timing": stats.to_dict(),
                }
            )
        modes.append({"coupling_mode": mode_name, "scales": scales})

    return {
        "benchmark": "coupling_complexity_scaling",
        "backend": "host CPU",
        "dtype": "f64",
        "n_steps": n_steps,
        "dt": dt,
        "modes": modes,
    }
