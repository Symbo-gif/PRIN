"""Oscillator-count scaling: wall time, throughput, and final order parameter
across a sweep of oscillator counts.

Rust-backed successor to PRINet 3.0's `oscillator_scaling.py` (Task 1.7:
10,000-oscillator scalability) and `on_stress_benchmark.py`/`gpu_benchmarks.py`'s
oscillator-scaling sweeps. Output schema is additively compatible with the
legacy `benchmark_y4q1_ring_scaling.json` shape (`benchmark`, `scales[]` with
`N`/`wall_time_s`/`throughput`/`final_order_param`); a `timing` block adds the
Benchmarking Standards §2.2 median/p95-over->=10-iterations envelope.
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
from prin.metrics import kuramoto_order_parameter

from benchmarks._common.config import BenchmarkConfig
from benchmarks._common.registry import register
from benchmarks._common.timing import timed_run

_DEFAULT_SIZES: tuple[int, ...] = (64, 256, 1024)
_DEFAULT_N_STEPS = 50
_DEFAULT_DT = 0.01


def _run_once(n: int, n_steps: int, dt: float, seed: Seed) -> float:
    """Integrate one N-oscillator mean-field system; return the final order param."""
    model = KuramotoOscillator(
        n_oscillators=n,
        coupling_strength=2.0 / n,
        decay_rate=0.1,
        freq_adaptation_rate=0.0,
        coupling_mode=CouplingMode.mean_field(),
    )
    state = OscillatorState.create_random(n, (0.5, 1.5), seed)
    integrator = RK4Integrator()
    final_state, _ = integrator.integrate_fixed(model, state, n_steps, dt)
    return float(kuramoto_order_parameter(final_state.phase))


@register(
    "scaling",
    "oscillator_count",
    summary="Wall time/throughput/R(t) vs. N (mean-field Kuramoto)",
)
def oscillator_count_scaling(config: BenchmarkConfig) -> dict[str, Any]:
    """Sweep oscillator count N and measure wall time, throughput, and R.

    ``config.params`` may override ``sizes`` (list[int]), ``n_steps``, and
    ``dt``.
    """
    sizes: tuple[int, ...] = tuple(config.params.get("sizes", _DEFAULT_SIZES))
    n_steps: int = int(config.params.get("n_steps", _DEFAULT_N_STEPS))
    dt: float = float(config.params.get("dt", _DEFAULT_DT))
    seed = Seed(config.seed_counter, config.seed_key)

    scales: list[dict[str, Any]] = []
    for n in sizes:
        stats, final_r = timed_run(
            lambda n=n: _run_once(n, n_steps, dt, seed),
            iterations=config.iterations,
            warmup=config.warmup,
        )
        scales.append(
            {
                "N": n,
                "n_steps": n_steps,
                "dt": dt,
                "coupling_mode": "mean_field",
                "wall_time_s": stats.median_s,
                "throughput": (n * n_steps) / stats.median_s
                if stats.median_s > 0
                else float("inf"),
                "final_order_param": final_r,
                "timing": stats.to_dict(),
            }
        )

    return {
        "benchmark": "oscillator_count_scaling",
        "backend": "host CPU",
        "dtype": "f64",
        "scales": scales,
    }
