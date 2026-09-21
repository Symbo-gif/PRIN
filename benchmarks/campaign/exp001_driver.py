"""Campaign driver for EXP-001 — golden-trajectory numerical parity.

Named by ``DOCS/experiments/EXP-001-golden-trajectory-numerical-parity/
preregistration.md`` (campaign plan §7.2, §12.1). Performs three pre-registered
comparisons, all against the actual PRIN (Rust) numerical core:

* **Corpus parity** (H1): re-integrate every golden-corpus case from its
  stored initial state through ``prin.dynamics`` and compare the produced
  trajectory/metric arrays against the PRINet-3.0-authored reference arrays
  with ``prin.parity.harness.compare_case``.
* **Bit-level repeatability** (H3): run a case twice from the same stored
  initial state and require byte-identical output arrays.
* **Hypothesis-fuzzed parity** (H2): draw a random-but-valid case spec and an
  explicit initial condition, run *both* PRINet 3.0 and PRIN from that
  identical input, and compare.
* **GPU kernel-path tolerance-identity** (H4): for every ``kuramoto_sparse_knn_*``
  corpus case, evaluate one derivative step through the CPU (f64 Rust) path
  and the GPU (f32 CubeCL) ``prin._prin_core.GpuSparseKuramoto`` kernel via
  ``prin._torch_compat.KuramotoOscillator``, and compare within the
  registered GPU-kernel tolerance.

The fuzz sampler (:func:`draw_fuzz_spec`, :func:`draw_fuzz_initial`) mirrors
the value ranges declared in ``prin.parity.strategies`` — the canonical
definition of valid fuzz-case space — but draws from the single registered
``Seed`` authority (a ``numpy.random.Generator`` seeded from the registered
``(seed_counter, seed_key)`` pair) rather than Hypothesis's own internal
engine, per Project Plan §4 rule 3 and campaign plan §6.1 ("no experiment may
introduce a second RNG path").

All numerical authority for the PRIN side lives in ``prin.dynamics``
(``prin._prin_core``, float64, CPU); this module performs no numerics of its
own beyond assembling arrays and invoking that authority and the tolerance-
aware comparison already implemented in ``prin.parity.harness``. H4's GPU
kernel-path comparison instead goes through ``prin._torch_compat`` (the
facade the GPU dispatch hook is defined on), since ``prin._prin_core.
GpuSparseKuramoto`` is a single-step derivative kernel, not a trajectory
integrator; the comparison tolerance is the registered f32 GPU-kernel bound
(``KERNEL_RTOL``/``KERNEL_ATOL`` below), not ``prin.parity.harness``'s f64
trajectory/metric tolerances.
"""

from __future__ import annotations

import argparse
import json
import sys
from collections.abc import Sequence
from pathlib import Path
from typing import Any

import numpy as np
import torch
from numpy.typing import NDArray
from prin import _prin_core
from prin._prin_core import kuramoto_order_parameter, mean_phase_coherence
from prin._torch_compat import KuramotoOscillator as TorchKuramotoOscillator
from prin._torch_compat import OscillatorState as TorchOscillatorState
from prin.dynamics import (
    CouplingMode,
    EulerIntegrator,
    HopfOscillator,
    KuramotoOscillator,
    OscillatorState,
    RK4Integrator,
    StuartLandauOscillator,
)
from prin.parity.harness import ComparisonResult, compare_case
from prin.parity.loader import CorpusLoader
from prin.parity.schema import CaseArrays, CaseSpec, Coupling, Integrator, Model

from benchmarks._common.environment import capture_environment
from benchmarks._common.result import ArtefactExistsError, write_result

EXP_ID = "EXP-001"

#: GPU sparse-k-NN kernel-path tolerance (H4; Testing Standards §3;
#: ``prin_kernels::equivalence::{DEFAULT_RTOL, DEFAULT_ATOL}``) — the fused
#: CubeCL kernel computes in f32, so this is *not* the f64 trajectory/metric
#: tolerance used elsewhere in this module.
KERNEL_RTOL = 1e-5
KERNEL_ATOL = 1e-6

#: Oscillator model classes, keyed by :class:`~prin.parity.schema.Model` value.
_PRIN_INTEGRATORS: dict[str, type[EulerIntegrator] | type[RK4Integrator]] = {
    Integrator.EULER.value: EulerIntegrator,
    Integrator.RK4.value: RK4Integrator,
}

_FUZZ_MODELS: tuple[str, ...] = (
    Model.KURAMOTO.value,
    Model.HOPF.value,
    Model.STUART_LANDAU.value,
)
_FUZZ_COUPLINGS: tuple[str, ...] = (
    Coupling.MEAN_FIELD.value,
    Coupling.FULL.value,
    Coupling.SPARSE_KNN.value,
)
_FUZZ_INTEGRATORS: tuple[str, ...] = (Integrator.EULER.value, Integrator.RK4.value)


class DriverError(RuntimeError):
    """Base class for EXP-001 driver failures (all are run aborts, not results)."""


class DriverMetadataError(DriverError):
    """Raised when required campaign metadata (campaign plan §7.2) is missing."""


class PrinetUnavailableError(DriverError):
    """Raised when fuzz mode is requested but PRINet 3.0 is not importable.

    Per campaign plan §10.1 item 3, environment capture incomplete for a
    configuration the run requires is an abort, not a negative result.
    """


def _coupling_mode(coupling: str, parameters: dict[str, Any]) -> CouplingMode:
    """Build the Rust-backed coupling mode matching a case's coupling field."""
    if coupling == Coupling.MEAN_FIELD.value:
        return CouplingMode.mean_field()
    if coupling == Coupling.FULL.value:
        return CouplingMode.full()
    if coupling == Coupling.SPARSE_KNN.value:
        sparse_k = parameters.get("sparse_k")
        if sparse_k is None:
            raise DriverMetadataError(
                "sparse_knn coupling requires an explicit 'sparse_k' parameter"
            )
        return CouplingMode.sparse_knn(k=int(sparse_k))
    raise ValueError(f"unknown coupling mode: {coupling}")


def build_prin_model(
    model: str, coupling: str, n_oscillators: int, parameters: dict[str, Any]
) -> KuramotoOscillator | HopfOscillator | StuartLandauOscillator:
    """Construct the PRIN (Rust) oscillator model matching a corpus case spec."""
    mode = _coupling_mode(coupling, parameters)
    if model == Model.KURAMOTO.value:
        return KuramotoOscillator(
            n_oscillators,
            float(parameters["coupling_strength"]),
            float(parameters.get("decay_rate", 0.0)),
            float(parameters.get("freq_adaptation_rate", 0.0)),
            mode,
        )
    if model == Model.HOPF.value:
        return HopfOscillator(
            n_oscillators,
            float(parameters["coupling_strength"]),
            float(parameters.get("bifurcation_param", 1.0)),
            float(parameters.get("freq_adaptation_rate", 0.0)),
            mode,
        )
    if model == Model.STUART_LANDAU.value:
        return StuartLandauOscillator(
            n_oscillators,
            float(parameters["coupling_strength"]),
            float(parameters.get("bifurcation_param", 1.0)),
            mode,
        )
    raise ValueError(f"unknown model: {model}")


def _initial_state(
    phase: NDArray[np.float64],
    amplitude: NDArray[np.float64],
    frequency: NDArray[np.float64],
) -> OscillatorState:
    return OscillatorState(
        phase=np.ascontiguousarray(phase, dtype=np.float64),
        amplitude=np.ascontiguousarray(amplitude, dtype=np.float64),
        frequency=np.ascontiguousarray(frequency, dtype=np.float64),
    )


def _states_to_case_arrays(
    initial: OscillatorState,
    states: Sequence[OscillatorState],
) -> CaseArrays:
    """Pack an initial state plus the full post-step state sequence into a case.

    Args:
        initial: The state at step 0.
        states: States at steps ``1..n_steps`` (i.e. the integrator's
            ``trajectory`` output; length ``n_steps``).

    Returns:
        A :class:`CaseArrays` with the same schema as the golden corpus,
        including PRIN-computed ``order_parameter_traj`` /
        ``mean_phase_coherence_traj``.
    """
    all_states = [initial, *states]
    phase_traj = np.stack([s.phase for s in all_states])
    amplitude_traj = np.stack([s.amplitude for s in all_states])
    frequency_traj = np.stack([s.frequency for s in all_states])
    order_traj = np.array(
        [kuramoto_order_parameter(s.phase) for s in all_states], dtype=np.float64
    )
    coherence_traj = np.array(
        [mean_phase_coherence(s.phase) for s in all_states], dtype=np.float64
    )
    final = all_states[-1]
    return CaseArrays(
        phase_init=np.ascontiguousarray(initial.phase, dtype=np.float64),
        amplitude_init=np.ascontiguousarray(initial.amplitude, dtype=np.float64),
        frequency_init=np.ascontiguousarray(initial.frequency, dtype=np.float64),
        phase_final=np.ascontiguousarray(final.phase, dtype=np.float64),
        amplitude_final=np.ascontiguousarray(final.amplitude, dtype=np.float64),
        frequency_final=np.ascontiguousarray(final.frequency, dtype=np.float64),
        phase_traj=np.ascontiguousarray(phase_traj, dtype=np.float64),
        amplitude_traj=np.ascontiguousarray(amplitude_traj, dtype=np.float64),
        frequency_traj=np.ascontiguousarray(frequency_traj, dtype=np.float64),
        order_parameter_traj=order_traj,
        mean_phase_coherence_traj=coherence_traj,
    )


def run_prin_trajectory(
    model: str,
    coupling: str,
    integrator: str,
    n_oscillators: int,
    n_steps: int,
    dt: float,
    parameters: dict[str, Any],
    phase_init: NDArray[np.float64],
    amplitude_init: NDArray[np.float64],
    frequency_init: NDArray[np.float64],
) -> CaseArrays:
    """Integrate the actual PRIN (Rust) implementation from an explicit initial state.

    This is the single execution path used by corpus, repeatability, and
    fuzz comparisons: only the initial condition and case parameters vary.
    """
    integrator_cls = _PRIN_INTEGRATORS.get(integrator)
    if integrator_cls is None:
        raise ValueError(f"unknown integrator: {integrator}")
    built_model = build_prin_model(model, coupling, n_oscillators, parameters)
    state = _initial_state(phase_init, amplitude_init, frequency_init)
    final, trajectory = integrator_cls().integrate_fixed(
        built_model, state, n_steps, dt, record_trajectory=True
    )
    del final  # the last element of `trajectory` is equivalent; avoid ambiguity
    return _states_to_case_arrays(state, trajectory or [])


def run_prin_case(spec: CaseSpec, initial: CaseArrays) -> CaseArrays:
    """Run :func:`run_prin_trajectory` from a :class:`CaseSpec` and initial arrays."""
    return run_prin_trajectory(
        model=spec.model,
        coupling=spec.coupling,
        integrator=spec.integrator,
        n_oscillators=spec.n_oscillators,
        n_steps=spec.n_steps,
        dt=spec.dt,
        parameters=dict(spec.parameters),
        phase_init=initial.phase_init,
        amplitude_init=initial.amplitude_init,
        frequency_init=initial.frequency_init,
    )


def compare_corpus_case(loader: CorpusLoader, case_id: str) -> dict[str, Any]:
    """Compare one golden-corpus case's PRIN reproduction against its reference.

    Returns:
        A JSON-serializable per-case record: identifying fields, the overall
        ``within_tolerance`` verdict, and every array-level
        :class:`~prin.parity.harness.ComparisonResult`.
    """
    loaded = loader.load(case_id)
    produced = run_prin_case(loaded.spec, loaded.arrays)
    comparisons = compare_case(loaded.arrays, produced, loaded.spec.model)
    return _corpus_case_record(loaded.spec, comparisons)


def _corpus_case_record(
    spec: CaseSpec, comparisons: list[ComparisonResult]
) -> dict[str, Any]:
    return {
        "case_id": spec.case_id,
        "model": spec.model,
        "coupling": spec.coupling,
        "integrator": spec.integrator,
        "n_oscillators": spec.n_oscillators,
        "n_steps": spec.n_steps,
        "dt": spec.dt,
        "seed": spec.seed,
        "within_tolerance": all(c.within_tolerance for c in comparisons),
        "comparisons": [c.to_dict() for c in comparisons],
    }


def compare_corpus_subset(
    loader: CorpusLoader, case_ids: Sequence[str]
) -> list[dict[str, Any]]:
    """Compare every case in ``case_ids`` (see :func:`compare_corpus_case`)."""
    return [compare_corpus_case(loader, case_id) for case_id in case_ids]


def check_repeatability(loader: CorpusLoader, case_id: str) -> dict[str, Any]:
    """Run a corpus case's PRIN reproduction twice and require bit-identity.

    Implements the campaign plan §6.5 repeatability gate for one configuration:
    identical scientific inputs must produce byte-identical outputs.
    """
    loaded = loader.load(case_id)
    first = run_prin_case(loaded.spec, loaded.arrays)
    second = run_prin_case(loaded.spec, loaded.arrays)
    mismatched = [
        name
        for name in CaseArrays._ARRAY_NAMES
        if not np.array_equal(getattr(first, name), getattr(second, name))
    ]
    return {
        "case_id": case_id,
        "bit_identical": not mismatched,
        "mismatched_arrays": mismatched,
    }


def draw_fuzz_spec(rng: np.random.Generator) -> dict[str, Any]:
    """Deterministically draw a valid case spec from the registered ``Seed`` RNG.

    Mirrors the value ranges declared in ``prin.parity.strategies`` (the
    canonical definition of valid fuzz-case space): 3 models, coupling modes
    valid for the drawn model, 2 basic integrators, ``n_oscillators`` in
    ``[8, 64]``, ``n_steps`` in ``[5, 50]``, ``dt`` in ``[0.001, 0.05]``,
    ``coupling_strength`` in ``[0.1, 4.0]``, and model-specific parameter
    ranges. Draws from ``rng`` rather than Hypothesis's own engine so the
    campaign's single registered ``Seed`` remains the only randomness source
    (Project Plan §4 rule 3).
    """
    model = str(rng.choice(_FUZZ_MODELS))
    coupling = (
        Coupling.FULL.value
        if model == Model.STUART_LANDAU.value
        else str(rng.choice(_FUZZ_COUPLINGS))
    )
    integrator = str(rng.choice(_FUZZ_INTEGRATORS))
    n_oscillators = int(rng.integers(8, 65))
    n_steps = int(rng.integers(5, 51))
    dt = float(rng.uniform(0.001, 0.05))
    seed = int(rng.integers(0, 2_147_483_648))
    parameters: dict[str, Any] = {
        "coupling_strength": float(rng.uniform(0.1, 4.0)),
    }
    if coupling == Coupling.SPARSE_KNN.value:
        parameters["sparse_k"] = int(rng.integers(2, min(13, n_oscillators)))
    if model == Model.KURAMOTO.value:
        parameters["decay_rate"] = float(rng.uniform(0.0, 0.5))
        parameters["freq_adaptation_rate"] = float(rng.uniform(0.0, 0.05))
    elif model == Model.HOPF.value:
        parameters["bifurcation_param"] = float(rng.uniform(-0.5, 2.0))
        parameters["freq_adaptation_rate"] = float(rng.uniform(0.0, 0.05))
    elif model == Model.STUART_LANDAU.value:
        parameters["bifurcation_param"] = float(rng.uniform(-0.5, 2.0))
    return {
        "model": model,
        "coupling": coupling,
        "integrator": integrator,
        "n_oscillators": n_oscillators,
        "n_steps": n_steps,
        "dt": dt,
        "seed": seed,
        "parameters": parameters,
    }


def draw_fuzz_initial(
    rng: np.random.Generator, n_oscillators: int
) -> tuple[NDArray[np.float64], NDArray[np.float64], NDArray[np.float64]]:
    """Draw an explicit ``(phase, amplitude, frequency)`` initial condition.

    Fed identically into both PRINet 3.0 and PRIN so the two implementations
    are compared from the same input rather than each drawing its own
    (implementation-specific) random state.
    """
    phase = rng.uniform(0.0, 2.0 * np.pi, size=n_oscillators)
    amplitude = rng.uniform(0.5, 1.5, size=n_oscillators)
    frequency = rng.uniform(-1.0, 1.0, size=n_oscillators)
    return (
        np.ascontiguousarray(phase, dtype=np.float64),
        np.ascontiguousarray(amplitude, dtype=np.float64),
        np.ascontiguousarray(frequency, dtype=np.float64),
    )


def run_prinet_trajectory(
    model: str,
    coupling: str,
    integrator: str,
    n_oscillators: int,
    n_steps: int,
    dt: float,
    parameters: dict[str, Any],
    phase_init: NDArray[np.float64],
    amplitude_init: NDArray[np.float64],
    frequency_init: NDArray[np.float64],
) -> CaseArrays:
    """Integrate PRINet 3.0 (the reference implementation) from an explicit state.

    Imports ``prinet``/``torch`` lazily so corpus/repeatability mode (which
    never needs the reference implementation, since the golden corpus already
    stores its output) does not require them installed.

    Raises:
        PrinetUnavailableError: If ``prinet`` or ``torch`` is not importable.
    """
    try:
        import torch
        from prinet.core.measurement import (
            kuramoto_order_parameter as prinet_order_parameter,
        )
        from prinet.core.measurement import (
            mean_phase_coherence as prinet_coherence,
        )
        from prinet.core.propagation import OscillatorState as PrinetOscillatorState
    except ImportError as exc:
        raise PrinetUnavailableError(
            "fuzz-mode parity requires the archived PRINet 3.0.0 reference "
            "implementation ('prinet') and 'torch' installed; environment "
            "incomplete (campaign plan §10.1 item 3) — aborting"
        ) from exc

    from parity.generate_corpus import _build_model as _build_prinet_model

    torch_model = _build_prinet_model(model, coupling, n_oscillators, parameters)
    initial = PrinetOscillatorState(
        phase=torch.tensor(phase_init, dtype=torch.float64),
        amplitude=torch.tensor(amplitude_init, dtype=torch.float64),
        frequency=torch.tensor(frequency_init, dtype=torch.float64),
    )
    final, trajectory = torch_model.integrate(
        initial, n_steps=n_steps, dt=dt, method=integrator, record_trajectory=True
    )
    del final
    states = [initial, *trajectory]
    phase_traj = np.stack([s.phase.detach().cpu().numpy() for s in states])
    amplitude_traj = np.stack([s.amplitude.detach().cpu().numpy() for s in states])
    frequency_traj = np.stack([s.frequency.detach().cpu().numpy() for s in states])
    order_traj = np.array(
        [float(prinet_order_parameter(s.phase)) for s in states], dtype=np.float64
    )
    coherence_traj = np.array(
        [float(prinet_coherence(s.phase)) for s in states], dtype=np.float64
    )
    return CaseArrays(
        phase_init=np.ascontiguousarray(phase_init, dtype=np.float64),
        amplitude_init=np.ascontiguousarray(amplitude_init, dtype=np.float64),
        frequency_init=np.ascontiguousarray(frequency_init, dtype=np.float64),
        phase_final=np.ascontiguousarray(phase_traj[-1], dtype=np.float64),
        amplitude_final=np.ascontiguousarray(amplitude_traj[-1], dtype=np.float64),
        frequency_final=np.ascontiguousarray(frequency_traj[-1], dtype=np.float64),
        phase_traj=np.ascontiguousarray(phase_traj, dtype=np.float64),
        amplitude_traj=np.ascontiguousarray(amplitude_traj, dtype=np.float64),
        frequency_traj=np.ascontiguousarray(frequency_traj, dtype=np.float64),
        order_parameter_traj=order_traj,
        mean_phase_coherence_traj=coherence_traj,
    )


def compare_fuzz_case(spec: dict[str, Any]) -> dict[str, Any]:
    """Run one fuzz-drawn case spec through both implementations and compare.

    Args:
        spec: A dict from :func:`draw_fuzz_spec`, plus an ``"rng"`` key
            (``numpy.random.Generator``) used to draw the shared initial
            condition (kept out of the returned record).

    Returns:
        A JSON-serializable record analogous to :func:`compare_corpus_case`.

    Raises:
        PrinetUnavailableError: If PRINet 3.0 is not importable.
    """
    rng: np.random.Generator = spec["rng"]
    phase, amplitude, frequency = draw_fuzz_initial(rng, spec["n_oscillators"])
    reference = run_prinet_trajectory(
        model=spec["model"],
        coupling=spec["coupling"],
        integrator=spec["integrator"],
        n_oscillators=spec["n_oscillators"],
        n_steps=spec["n_steps"],
        dt=spec["dt"],
        parameters=spec["parameters"],
        phase_init=phase,
        amplitude_init=amplitude,
        frequency_init=frequency,
    )
    produced = run_prin_trajectory(
        model=spec["model"],
        coupling=spec["coupling"],
        integrator=spec["integrator"],
        n_oscillators=spec["n_oscillators"],
        n_steps=spec["n_steps"],
        dt=spec["dt"],
        parameters=spec["parameters"],
        phase_init=phase,
        amplitude_init=amplitude,
        frequency_init=frequency,
    )
    comparisons = compare_case(reference, produced, spec["model"])
    return {
        "seed": spec["seed"],
        "model": spec["model"],
        "coupling": spec["coupling"],
        "integrator": spec["integrator"],
        "n_oscillators": spec["n_oscillators"],
        "n_steps": spec["n_steps"],
        "dt": spec["dt"],
        "within_tolerance": all(c.within_tolerance for c in comparisons),
        "comparisons": [c.to_dict() for c in comparisons],
    }


def run_fuzz_batch(
    seed_counter: int, seed_key: int, n_cases: int
) -> list[dict[str, Any]]:
    """Draw and compare ``n_cases`` fuzzed cases from the registered ``Seed``.

    The RNG stream is seeded deterministically from ``(seed_counter,
    seed_key)`` (campaign plan §6.2/§6.3) so a given pair always reproduces
    the same sequence of drawn cases.

    Raises:
        PrinetUnavailableError: If PRINet 3.0 is not importable.
    """
    rng = np.random.default_rng(seed_key * 1_000_000_007 + seed_counter)
    records = []
    for _ in range(n_cases):
        spec = draw_fuzz_spec(rng)
        spec["rng"] = rng
        records.append(compare_fuzz_case(spec))
    return records


class GpuBindingUnavailableError(DriverError):
    """Raised when H4 kernel-path mode runs without a ``cuda``-feature build.

    Per preregistration §4 item 6 / campaign plan §10.1 item 6, an extension
    built without ``prin._prin_core.GpuSparseKuramoto`` is a build-
    configuration abort (reported ``NOT EXECUTED — cuda feature not built``,
    verdict ``INCONCLUSIVE``), not a negative result.
    """


def _compare_kernel_array(
    name: str, reference: NDArray[np.float64], test: NDArray[np.float64]
) -> dict[str, Any]:
    """Compare one derivative array at the registered GPU-kernel tolerance (H4).

    Mirrors ``prin.parity.harness.compare_arrays``' allclose statistics, but
    against the fixed ``KERNEL_RTOL``/``KERNEL_ATOL`` bound rather than a
    ``Quantity``-derived f64 tolerance (the GPU kernel computes in f32).
    """
    diff = np.abs(reference - test)
    with np.errstate(invalid="ignore", divide="ignore"):
        rel = diff / (np.abs(reference) + 1e-300)
    close = np.isclose(reference, test, rtol=KERNEL_RTOL, atol=KERNEL_ATOL)
    return {
        "array_name": name,
        "within_tolerance": bool(np.all(close)),
        "max_abs_diff": float(np.max(diff)) if diff.size else 0.0,
        "max_rel_diff": float(np.max(rel)) if rel.size else 0.0,
        "failed_count": int(np.size(close) - int(np.count_nonzero(close))),
        "total_count": int(reference.size),
    }


def compare_kernel_path_case(loader: CorpusLoader, case_id: str) -> dict[str, Any]:
    """Compare the GPU sparse-k-NN derivative kernel against the CPU reference (H4).

    Builds a ``prin._torch_compat.KuramotoOscillator`` from one
    ``kuramoto_sparse_knn_*`` corpus case's stored parameters and initial
    state, evaluates one derivative step through the CPU (f64 Rust) path and
    the GPU (f32 CubeCL) ``GpuSparseKuramoto`` kernel via the model's
    ``_compute_derivatives_gpu`` dispatch hook (WP-036D), and compares within
    the registered ``KERNEL_RTOL``/``KERNEL_ATOL`` tolerance.

    Raises:
        GpuBindingUnavailableError: If the extension lacks
            ``GpuSparseKuramoto`` (no ``cuda``-feature build), or the
            dispatch hook otherwise declines to run (unexpected for a
            ``sparse_knn`` case).
        ValueError: If ``case_id`` does not name a ``kuramoto``/``sparse_knn``
            case.
    """
    if not hasattr(_prin_core, "GpuSparseKuramoto"):
        raise GpuBindingUnavailableError(
            "prin._prin_core.GpuSparseKuramoto is absent (extension built "
            "without --features cuda); H4 kernel-path mode aborts"
        )
    loaded = loader.load(case_id)
    spec = loaded.spec
    if spec.model != Model.KURAMOTO.value or spec.coupling != Coupling.SPARSE_KNN.value:
        raise ValueError(
            "H4 kernel-path mode requires a kuramoto/sparse_knn case, got "
            f"model={spec.model!r} coupling={spec.coupling!r} (case {case_id})"
        )
    parameters: dict[str, Any] = dict(spec.parameters)
    model = TorchKuramotoOscillator(
        spec.n_oscillators,
        coupling_strength=float(parameters["coupling_strength"]),
        decay_rate=float(parameters.get("decay_rate", 0.0)),
        freq_adaptation_rate=float(parameters.get("freq_adaptation_rate", 0.0)),
        coupling_mode="sparse_knn",
        sparse_k=int(parameters["sparse_k"]),
    )
    state = TorchOscillatorState(
        phase=torch.tensor(loaded.arrays.phase_init, dtype=torch.float64),
        amplitude=torch.tensor(loaded.arrays.amplitude_init, dtype=torch.float64),
        frequency=torch.tensor(loaded.arrays.frequency_init, dtype=torch.float64),
    )
    cpu_dphase, cpu_damplitude, cpu_dfrequency = model.compute_derivatives(state)
    gpu = model._compute_derivatives_gpu(state)
    if gpu is None:
        raise GpuBindingUnavailableError(
            "GpuSparseKuramoto is present but the dispatch hook declined to "
            f"run for case {case_id} (unexpected for a sparse_knn case)"
        )
    gpu_dphase, gpu_damplitude, gpu_dfrequency = gpu
    comparisons = [
        _compare_kernel_array(
            name,
            cpu.detach().to(dtype=torch.float64, device="cpu").numpy(),
            gpu_val.detach().to(dtype=torch.float64, device="cpu").numpy(),
        )
        for name, cpu, gpu_val in (
            ("dphase", cpu_dphase, gpu_dphase),
            ("damplitude", cpu_damplitude, gpu_damplitude),
            ("dfrequency", cpu_dfrequency, gpu_dfrequency),
        )
    ]
    return {
        "case_id": case_id,
        "model": spec.model,
        "coupling": spec.coupling,
        "n_oscillators": spec.n_oscillators,
        "sparse_k": int(parameters["sparse_k"]),
        "within_tolerance": all(c["within_tolerance"] for c in comparisons),
        "comparisons": comparisons,
    }


def compare_kernel_path_subset(
    loader: CorpusLoader, case_ids: Sequence[str]
) -> list[dict[str, Any]]:
    """Compare every case in ``case_ids`` (see :func:`compare_kernel_path_case`)."""
    return [compare_kernel_path_case(loader, case_id) for case_id in case_ids]


def _validate_metadata(exp_id: str, run_id: str, session: str, operator: str) -> None:
    """Raise :class:`DriverMetadataError` if any required field is empty."""
    missing = [
        name
        for name, value in (
            ("exp_id", exp_id),
            ("run_id", run_id),
            ("session", session),
            ("operator", operator),
        )
        if not value
    ]
    if missing:
        raise DriverMetadataError(
            f"missing required campaign metadata: {', '.join(missing)}"
        )


def write_campaign_metadata(
    run_dir: Path,
    *,
    exp_id: str,
    run_id: str,
    session: str,
    operator: str,
    artefacts: dict[str, list[str]],
) -> Path:
    """Write the ``campaign-metadata.json`` sidecar (campaign plan §7.2).

    Raises:
        DriverMetadataError: If required metadata is missing.
        ArtefactExistsError: If the sidecar already exists (append-only).
    """
    _validate_metadata(exp_id, run_id, session, operator)
    path = run_dir / "campaign-metadata.json"
    if path.exists():
        raise ArtefactExistsError(
            f"{path} already exists; campaign metadata is append-only "
            "(campaign plan §7.3) — write to a new run directory instead"
        )
    payload = {
        "exp_id": exp_id,
        "run_id": run_id,
        "session": session,
        "operator": operator,
        "artefacts": artefacts,
    }
    run_dir.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(payload, indent=2, sort_keys=True, ensure_ascii=False),
        encoding="utf-8",
    )
    return path


#: Hypothesis tag recorded in ``campaign-metadata.json`` per run mode
#: (campaign plan §7.2).
_MODE_HYPOTHESIS: dict[str, list[str]] = {
    "corpus": ["H1"],
    "repeatability": ["H3"],
    "fuzz": ["H2"],
    "kernel-path": ["H4"],
}


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--mode",
        choices=("corpus", "repeatability", "fuzz", "kernel-path"),
        required=True,
        help="Which pre-registered comparison to run.",
    )
    parser.add_argument(
        "--corpus-dir",
        type=Path,
        default=Path("parity") / "corpus",
        help="Golden-trajectory corpus directory (default: parity/corpus).",
    )
    parser.add_argument(
        "--case-id",
        action="append",
        default=None,
        dest="case_ids",
        help="Corpus case ID to include (repeatable). Default: every case "
        "in the corpus manifest for --mode corpus; required for "
        "--mode repeatability.",
    )
    parser.add_argument(
        "--n-fuzz-cases",
        type=int,
        default=1000,
        help="Number of hypothesis-fuzzed cases to draw (--mode fuzz).",
    )
    parser.add_argument("--seed-counter", type=int, default=0)
    parser.add_argument("--seed-key", type=int, default=1, help="EXP-001 = 1.")
    parser.add_argument("--out", type=Path, required=True, help="Run directory.")
    parser.add_argument("--label", required=True)
    parser.add_argument("--session", required=True)
    parser.add_argument("--operator", required=True)
    return parser


def main(argv: list[str] | None = None) -> int:
    """Run the requested comparison and write its artefact + metadata sidecar."""
    args = _parser().parse_args(argv)
    run_dir: Path = args.out.resolve()
    run_id = run_dir.name

    try:
        _validate_metadata(EXP_ID, run_id, args.session, args.operator)
        if args.mode == "corpus":
            loader = CorpusLoader(args.corpus_dir)
            case_ids = args.case_ids or [
                record.case_id for record in loader.manifest.cases
            ]
            cases = compare_corpus_subset(loader, case_ids)
        elif args.mode == "repeatability":
            if not args.case_ids:
                raise DriverMetadataError(
                    "--mode repeatability requires at least one --case-id"
                )
            loader = CorpusLoader(args.corpus_dir)
            cases = [check_repeatability(loader, cid) for cid in args.case_ids]
        elif args.mode == "kernel-path":
            loader = CorpusLoader(args.corpus_dir)
            case_ids = args.case_ids or [
                record.case_id
                for record in loader.manifest.cases
                if record.model == Model.KURAMOTO.value
                and record.coupling == Coupling.SPARSE_KNN.value
            ]
            cases = compare_kernel_path_subset(loader, case_ids)
        else:
            cases = run_fuzz_batch(args.seed_counter, args.seed_key, args.n_fuzz_cases)
    except DriverError as exc:
        print(f"ABORT: {exc}", file=sys.stderr)
        return 2

    backend, dtype = ("cuda", "f32") if args.mode == "kernel-path" else ("cpu", "f64")
    environment = capture_environment(
        backend=backend, dtype=dtype, seed=args.seed_counter
    )
    config = {
        "iterations": len(cases),
        "warmup": 0,
        "seed_counter": args.seed_counter,
        "seed_key": args.seed_key,
        "out_dir": str(run_dir),
    }
    result_name = f"{args.mode}_{args.label}.json"
    result_path = write_result(
        run_dir / result_name,
        environment=environment,
        config=config,
        payload={"cases": cases},
    )
    write_campaign_metadata(
        run_dir,
        exp_id=EXP_ID,
        run_id=run_id,
        session=args.session,
        operator=args.operator,
        artefacts={result_name: _MODE_HYPOTHESIS[args.mode]},
    )
    print(f"Wrote {result_path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
