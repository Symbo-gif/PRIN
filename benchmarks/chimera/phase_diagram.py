"""Chimera phase diagram: order parameter, chimera index, strength of
incoherence, and metastability across a coupling-strength sweep on a ring
topology.

Rust-backed successor to PRINet 3.0's `phase_diagram.py` (Kuramoto
bifurcation analysis) and `desync_catastrophe.py`.
"""

from __future__ import annotations

import numpy as np
from prin.dynamics import (
    CouplingMode,
    KuramotoOscillator,
    OscillatorState,
    RK4Integrator,
    Seed,
)
from prin.metrics import (
    build_phase_knn,
    chimera_index,
    kuramoto_order_parameter,
    metastability,
    strength_of_incoherence,
)

from benchmarks._common.config import BenchmarkConfig
from benchmarks._common.registry import register
from benchmarks._common.timing import timed_run

_DEFAULT_N = 64
_DEFAULT_K_NEIGHBORS = 8
_DEFAULT_N_STEPS = 100
_DEFAULT_DT = 0.01
_DEFAULT_COUPLING_STRENGTHS: tuple[float, ...] = (0.5, 1.0, 2.0, 4.0)


def _run_once(
    n: int,
    k_neighbors: int,
    coupling_strength: float,
    n_steps: int,
    dt: float,
    seed: Seed,
) -> tuple[float, float, float, float]:
    """Integrate one sparse-k-NN Kuramoto system.

    Returns:
        ``(R, chimera_index, strength_of_incoherence, metastability)``.
    """
    model = KuramotoOscillator(
        n_oscillators=n,
        coupling_strength=coupling_strength,
        decay_rate=0.1,
        freq_adaptation_rate=0.0,
        coupling_mode=CouplingMode.sparse_knn(k_neighbors),
    )
    state = OscillatorState.create_random(n, (0.9, 1.1), seed)
    final_state, trajectory = RK4Integrator().integrate_fixed(
        model, state, n_steps, dt, record_trajectory=True
    )
    assert trajectory is not None

    neighbors = build_phase_knn(final_state.phase, k_neighbors)
    r = kuramoto_order_parameter(final_state.phase)
    chi = chimera_index(final_state.phase, neighbors, 0.5)
    si = strength_of_incoherence(final_state.phase, max(2, n // 8))
    flat_traj = np.concatenate([s.phase for s in trajectory])
    meta = metastability(flat_traj, n)
    return r, chi, si, meta


@register(
    "chimera",
    "phase_diagram",
    summary="R/chimera-index/SI/metastability vs. coupling strength (k-NN Kuramoto)",
)
def phase_diagram_sweep(config: BenchmarkConfig) -> dict[str, object]:
    """Sweep coupling strength K; report order parameter and chimera metrics.

    ``config.params`` may override ``n``, ``k_neighbors``,
    ``coupling_strengths``, ``n_steps``, and ``dt``.
    """
    n: int = int(config.params.get("n", _DEFAULT_N))
    k_neighbors: int = int(config.params.get("k_neighbors", _DEFAULT_K_NEIGHBORS))
    coupling_strengths: tuple[float, ...] = tuple(
        config.params.get("coupling_strengths", _DEFAULT_COUPLING_STRENGTHS)
    )
    n_steps: int = int(config.params.get("n_steps", _DEFAULT_N_STEPS))
    dt: float = float(config.params.get("dt", _DEFAULT_DT))
    seed = Seed(config.seed_counter, config.seed_key)

    points: list[dict[str, object]] = []
    for k in coupling_strengths:
        stats, (r, chi, si, meta) = timed_run(
            lambda k=k: _run_once(n, k_neighbors, k, n_steps, dt, seed),
            iterations=config.iterations,
            warmup=config.warmup,
        )
        points.append(
            {
                "coupling_strength": k,
                "order_parameter": r,
                "chimera_index": chi,
                "strength_of_incoherence": si,
                "metastability": meta,
                "timing": stats.to_dict(),
            }
        )

    return {
        "benchmark": "chimera_phase_diagram",
        "backend": "host CPU",
        "dtype": "f64",
        "n": n,
        "k_neighbors": k_neighbors,
        "n_steps": n_steps,
        "dt": dt,
        "points": points,
    }
