"""Generate the versioned PRINet 3.0 golden-trajectory corpus.

This script is a one-time Phase 0 deliverable. It runs PRINet 3.0.0 (the
archived reference implementation) to produce seeded float64 trajectories for
every model x coupling mode x basic integrator, writes them as compressed
``.npz`` files, and emits a SHA-256 manifest.
"""

from __future__ import annotations

import argparse
import math
import sys
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import numpy as np
import prinet
import torch
from prin.parity.manifest import create_manifest
from prin.parity.schema import CaseArrays, CaseSpec, Coupling, Integrator, Model
from prinet.core.measurement import (
    kuramoto_order_parameter,
    mean_phase_coherence,
)
from prinet.core.propagation import (
    HopfOscillator,
    KuramotoOscillator,
    OscillatorState,
    StuartLandauOscillator,
)

_CORPUS_MODELS: list[tuple[str, str]] = [
    (Model.KURAMOTO.value, Coupling.MEAN_FIELD.value),
    (Model.KURAMOTO.value, Coupling.FULL.value),
    (Model.KURAMOTO.value, Coupling.SPARSE_KNN.value),
    (Model.HOPF.value, Coupling.MEAN_FIELD.value),
    (Model.HOPF.value, Coupling.FULL.value),
    (Model.HOPF.value, Coupling.SPARSE_KNN.value),
    (Model.STUART_LANDAU.value, Coupling.FULL.value),
]

_INTEGRATORS = [Integrator.EULER.value, Integrator.RK4.value]

_N_OSCILLATORS = [8, 12, 16, 24]
_COUPLING_STRENGTHS = [0.5, 1.0, 2.0]
_DT = [0.005, 0.01, 0.02]
_N_STEPS = 20


def _model_specific_parameters(model: str, variant: int) -> dict[str, Any]:
    """Return a small set of model-specific parameters indexed by ``variant``."""
    if model == Model.KURAMOTO.value:
        return {
            0: {"decay_rate": 0.01, "freq_adaptation_rate": 0.0},
            1: {"decay_rate": 0.01, "freq_adaptation_rate": 0.01},
            2: {"decay_rate": 0.1, "freq_adaptation_rate": 0.0},
            3: {"decay_rate": 0.1, "freq_adaptation_rate": 0.01},
        }[variant % 4]
    if model == Model.HOPF.value:
        return {
            0: {"bifurcation_param": 0.5, "freq_adaptation_rate": 0.0},
            1: {"bifurcation_param": 0.5, "freq_adaptation_rate": 0.01},
            2: {"bifurcation_param": 1.0, "freq_adaptation_rate": 0.0},
            3: {"bifurcation_param": 1.0, "freq_adaptation_rate": 0.01},
        }[variant % 4]
    if model == Model.STUART_LANDAU.value:
        return {"bifurcation_param": [0.5, 1.0, 0.5, 1.0][variant % 4]}
    raise ValueError(f"unknown model: {model}")


def _sparse_k(n: int) -> int:
    """Default sparse k-NN count for ``n`` oscillators (mirrors PRINet 3.0)."""
    return max(1, min(math.ceil(math.log2(n)), n - 1))


def _build_model(
    model: str,
    coupling: str,
    n_oscillators: int,
    parameters: dict[str, Any],
) -> Any:
    """Construct a PRINet 3.0 oscillator model from a case spec."""
    kwargs: dict[str, Any] = {
        "n_oscillators": n_oscillators,
        "coupling_strength": parameters["coupling_strength"],
        "dtype": torch.float64,
    }

    if model == Model.KURAMOTO.value:
        kwargs["coupling_mode"] = coupling
        kwargs["decay_rate"] = parameters.get("decay_rate", 0.1)
        kwargs["freq_adaptation_rate"] = parameters.get("freq_adaptation_rate", 0.01)
        if coupling == Coupling.SPARSE_KNN.value:
            kwargs["sparse_k"] = parameters.get("sparse_k", _sparse_k(n_oscillators))
        return KuramotoOscillator(**kwargs)

    if model == Model.HOPF.value:
        kwargs["coupling_mode"] = coupling
        kwargs["bifurcation_param"] = parameters.get("bifurcation_param", 1.0)
        kwargs["freq_adaptation_rate"] = parameters.get("freq_adaptation_rate", 0.01)
        if coupling == Coupling.SPARSE_KNN.value:
            kwargs["sparse_k"] = parameters.get("sparse_k", _sparse_k(n_oscillators))
        return HopfOscillator(**kwargs)

    if model == Model.STUART_LANDAU.value:
        kwargs["bifurcation_param"] = parameters.get("bifurcation_param", 1.0)
        return StuartLandauOscillator(**kwargs)

    raise ValueError(f"unknown model: {model}")


def _require_f64(array: np.ndarray, name: str) -> np.ndarray:
    """Return a contiguous float64 NumPy array."""
    return np.ascontiguousarray(array, dtype=np.float64)


def _run_case(
    model: str,
    coupling: str,
    integrator: str,
    n_oscillators: int,
    n_steps: int,
    dt: float,
    seed: int,
    parameters: dict[str, Any],
) -> tuple[CaseSpec, CaseArrays]:
    """Generate one golden case against PRINet 3.0.0."""
    torch_model = _build_model(model, coupling, n_oscillators, parameters)
    initial = OscillatorState.create_random(
        n_oscillators,
        seed=seed,
        dtype=torch.float64,
    )
    final, trajectory = torch_model.integrate(
        initial,
        n_steps=n_steps,
        dt=dt,
        method=integrator,
        record_trajectory=True,
    )

    states = [initial, *trajectory]
    phase_traj = np.stack([s.phase.detach().cpu().numpy() for s in states])
    amplitude_traj = np.stack([s.amplitude.detach().cpu().numpy() for s in states])
    frequency_traj = np.stack([s.frequency.detach().cpu().numpy() for s in states])

    order_traj = np.array(
        [float(kuramoto_order_parameter(s.phase)) for s in states],
        dtype=np.float64,
    )
    coherence_traj = np.array(
        [float(mean_phase_coherence(s.phase)) for s in states],
        dtype=np.float64,
    )

    arrays = CaseArrays(
        phase_init=_require_f64(initial.phase.detach().cpu().numpy(), "phase_init"),
        amplitude_init=_require_f64(
            initial.amplitude.detach().cpu().numpy(), "amplitude_init"
        ),
        frequency_init=_require_f64(
            initial.frequency.detach().cpu().numpy(), "frequency_init"
        ),
        phase_final=_require_f64(final.phase.detach().cpu().numpy(), "phase_final"),
        amplitude_final=_require_f64(
            final.amplitude.detach().cpu().numpy(), "amplitude_final"
        ),
        frequency_final=_require_f64(
            final.frequency.detach().cpu().numpy(), "frequency_final"
        ),
        phase_traj=_require_f64(phase_traj, "phase_traj"),
        amplitude_traj=_require_f64(amplitude_traj, "amplitude_traj"),
        frequency_traj=_require_f64(frequency_traj, "frequency_traj"),
        order_parameter_traj=_require_f64(order_traj, "order_parameter_traj"),
        mean_phase_coherence_traj=_require_f64(
            coherence_traj, "mean_phase_coherence_traj"
        ),
    )

    spec_parameters = dict(parameters)
    if coupling == Coupling.SPARSE_KNN.value:
        spec_parameters["sparse_k"] = _sparse_k(n_oscillators)

    case_id = (
        f"{model}_{coupling}_{integrator}_n{n_oscillators}_s{n_steps}_"
        f"dt{dt:g}_K{parameters['coupling_strength']:g}_seed{seed}"
    )
    case_id = case_id.replace(".", "_")
    spec = CaseSpec(
        case_id=case_id,
        model=model,
        coupling=coupling,
        integrator=integrator,
        n_oscillators=n_oscillators,
        n_steps=n_steps,
        dt=dt,
        seed=seed,
        parameters=spec_parameters,
    )
    return spec, arrays


def _case_grid() -> list[tuple[str, str, str]]:
    """Return the full model x coupling x integrator grid."""
    grid: list[tuple[str, str, str]] = []
    for model, coupling in _CORPUS_MODELS:
        for integrator in _INTEGRATORS:
            grid.append((model, coupling, integrator))
    return grid


def _parameter_sweep() -> list[tuple[int, float, float]]:
    """Return the (N, K, dt) parameter sweep used for every combo."""
    sweep: list[tuple[int, float, float]] = []
    for n in _N_OSCILLATORS:
        for k in _COUPLING_STRENGTHS:
            for dt in _DT:
                sweep.append((n, k, dt))
    return sweep


def generate_corpus(
    out_dir: Path,
    limit: int | None = None,
    *,
    seed_base: int = 1_000_000,
) -> list[tuple[CaseSpec, Path]]:
    """Generate golden-trajectory cases and write them to ``out_dir``.

    Args:
        out_dir: Destination for ``cases/*.npz`` and ``manifest.json``.
        limit: If given, stop after ``limit`` cases (for pilots/tests).
        seed_base: Integer added to every case seed for reproducibility.

    Returns:
        List of ``(CaseSpec, npz_path)`` pairs written to disk.
    """
    out_dir = out_dir.resolve()
    cases_dir = out_dir / "cases"
    cases_dir.mkdir(parents=True, exist_ok=True)

    written: list[tuple[CaseSpec, Path]] = []
    grid = _case_grid()
    sweep = _parameter_sweep()

    for combo_index, (model, coupling, integrator) in enumerate(grid):
        for case_index, (n, k, dt) in enumerate(sweep):
            if limit is not None and len(written) >= limit:
                return written
            seed = seed_base + combo_index * 100_000 + case_index
            variant = case_index
            parameters: dict[str, Any] = {
                "coupling_strength": k,
                **_model_specific_parameters(model, variant),
            }
            if coupling == Coupling.SPARSE_KNN.value:
                parameters["sparse_k"] = _sparse_k(n)
            spec, arrays = _run_case(
                model=model,
                coupling=coupling,
                integrator=integrator,
                n_oscillators=n,
                n_steps=_N_STEPS,
                dt=dt,
                seed=seed,
                parameters=parameters,
            )
            path = cases_dir / f"{spec.case_id}.npz"
            arrays.to_npz(path)
            written.append((spec, path))

    return written


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--out",
        type=Path,
        default=Path(__file__).resolve().parent / "corpus",
        help="Output directory for the corpus (default: parity/corpus).",
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=None,
        help="Generate at most LIMIT cases (useful for smoke tests).",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    """Generate the corpus and write the manifest."""
    args = _parser().parse_args(argv)
    out_dir: Path = args.out.resolve()
    cases = generate_corpus(out_dir, limit=args.limit)
    reference_source = (
        "DOCS/archive and reference from PRINet 3.0/PRINet-3.0.0-main (prinet==3.0.0)"
    )
    create_manifest(
        corpus_dir=out_dir,
        cases=cases,
        generator="prinet",
        generator_version=str(getattr(prinet, "__version__", "3.0.0")),
        prin_version="0.1.0",
        reference_source=reference_source,
    )
    manifest_path = out_dir / "manifest.json"
    print(
        f"Generated {len(cases)} cases in {out_dir}\n"
        f"Manifest: {manifest_path}\n"
        f"Created: {datetime.now(UTC).isoformat()}"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
