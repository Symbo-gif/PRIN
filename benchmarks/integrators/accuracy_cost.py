"""Integrator accuracy/cost: wall time and final-state agreement across
Euler, RK4, adaptive RK45, exponential, and multi-rate integrators on the
same mean-field Kuramoto system.

`RK45Integrator.integrate_adaptive`'s accepted/rejected step counts are
reported directly from Rust; "accuracy" here is each integrator's final
order parameter compared against the tight-tolerance RK45 reference, not an
independent numerical implementation.
"""

from __future__ import annotations

from typing import Any

from prin.dynamics import (
    CouplingMode,
    EulerIntegrator,
    ExponentialIntegrator,
    KuramotoOscillator,
    MultiRateIntegrator,
    OscillatorState,
    RK4Integrator,
    RK45Integrator,
    Seed,
)
from prin.metrics import kuramoto_order_parameter

from benchmarks._common.config import BenchmarkConfig
from benchmarks._common.registry import register
from benchmarks._common.timing import timed_run

_DEFAULT_N = 64
_DEFAULT_N_STEPS = 50
_DEFAULT_DT = 0.01


def _model(n: int) -> KuramotoOscillator:
    return KuramotoOscillator(
        n_oscillators=n,
        coupling_strength=2.0 / n,
        decay_rate=0.1,
        freq_adaptation_rate=0.0,
        coupling_mode=CouplingMode.mean_field(),
    )


def _reference_r(n: int, t_span: float, seed_state: OscillatorState) -> float:
    result = RK45Integrator(rtol=1e-10, atol=1e-12).integrate_adaptive(
        _model(n), seed_state, t_span, t_span / 100.0
    )
    return float(kuramoto_order_parameter(result.final_state.phase))


@register(
    "integrators",
    "accuracy_cost",
    summary="Wall time/final-R vs. reference: Euler/RK4/RK45/exponential/multi-rate",
)
def integrator_accuracy_cost(config: BenchmarkConfig) -> dict[str, Any]:
    """Compare integrators on wall time and agreement with a tight-tolerance
    RK45 reference.

    ``config.params`` may override ``n``, ``n_steps``, and ``dt``.
    """
    n = int(config.params.get("n", _DEFAULT_N))
    n_steps = int(config.params.get("n_steps", _DEFAULT_N_STEPS))
    dt = float(config.params.get("dt", _DEFAULT_DT))
    t_span = n_steps * dt
    seed = Seed(config.seed_counter, config.seed_key)
    initial_state = OscillatorState.create_random(n, (0.9, 1.1), seed)
    reference_r = _reference_r(n, t_span, initial_state)

    results: dict[str, Any] = {}

    def _fixed(integrator: Any, method: str) -> float:
        step_fn = (
            integrator.integrate_fixed
            if method == "integrate_fixed"
            else integrator.integrate
        )
        final_state, _ = step_fn(_model(n), initial_state, n_steps, dt)
        return kuramoto_order_parameter(final_state.phase)

    for name, integrator, method in (
        ("euler", EulerIntegrator(), "integrate_fixed"),
        ("rk4", RK4Integrator(), "integrate_fixed"),
        ("exponential", ExponentialIntegrator(dim=3 * n), "integrate"),
        ("multi_rate", MultiRateIntegrator(sub_steps=4, method="rk4"), "integrate"),
    ):
        stats, r = timed_run(
            lambda integrator=integrator, method=method: _fixed(integrator, method),
            iterations=config.iterations,
            warmup=config.warmup,
        )
        results[name] = {
            "final_order_param": r,
            "abs_error_vs_reference": abs(r - reference_r),
            "timing": stats.to_dict(),
        }

    def _adaptive() -> Any:
        return RK45Integrator().integrate_adaptive(_model(n), initial_state, t_span, dt)

    stats, adaptive_result = timed_run(
        _adaptive, iterations=config.iterations, warmup=config.warmup
    )
    adaptive_r = kuramoto_order_parameter(adaptive_result.final_state.phase)
    results["rk45_adaptive"] = {
        "final_order_param": adaptive_r,
        "abs_error_vs_reference": abs(adaptive_r - reference_r),
        "accepted_steps": adaptive_result.accepted_steps,
        "rejected_steps": adaptive_result.rejected_steps,
        "final_dt": adaptive_result.final_dt,
        "timing": stats.to_dict(),
    }

    return {
        "benchmark": "integrator_accuracy_cost",
        "backend": "host CPU",
        "dtype": "f64",
        "n": n,
        "n_steps": n_steps,
        "dt": dt,
        "reference_order_param": reference_r,
        "reference_method": "RK45 rtol=1e-10 atol=1e-12",
        "integrators": results,
    }
