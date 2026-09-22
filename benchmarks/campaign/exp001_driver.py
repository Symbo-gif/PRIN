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
  identical input; H2a compares pointwise within the ``T_STAR``-step
  shadowing horizon, and H2b records the raw beyond-horizon
  ``order_parameter``/``mean_phase_coherence`` pairs for E4's pooled
  Welch-t/Cohen's-d/bootstrap-CI analysis (this driver does not compute that
  statistic itself — see :func:`compare_fuzz_case`).
* **GPU kernel-path tolerance-identity** (H4): for every ``kuramoto_sparse_knn_*``
  corpus case, evaluate one derivative step through the CPU (f64 Rust) path
  (``prin._torch_compat.KuramotoOscillator.compute_derivatives``) and the GPU
  (f32 CubeCL) ``prin._prin_core.GpuSparseKuramoto`` kernel — called
  **directly**, not through ``prin._torch_compat``'s
  ``_compute_derivatives_gpu`` dispatch hook — and compare within the
  registered GPU-kernel tolerance. The direct call is required, not
  stylistic: it is the only way to inspect the raw DLPack result's device
  and so confirm the kernel actually dispatched through CUDA rather than
  wgpu or a host-slice fallback (see :func:`compare_kernel_path_case`). Do
  not reroute this path back through the dispatch hook — doing so silently
  removes that CUDA-residency check.

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
aware comparison already implemented in ``prin.parity.harness``. H4 is the
exception to the *trajectory* framing: ``prin._prin_core.GpuSparseKuramoto``
is a single-step derivative kernel, not a trajectory integrator, so H4
compares one derivative evaluation — its CPU reference through
``prin._torch_compat``, its GPU side through the raw ``prin._prin_core``
binding (above) — at the registered f32 GPU-kernel bound
(``KERNEL_RTOL``/``KERNEL_ATOL`` below), not ``prin.parity.harness``'s f64
trajectory/metric tolerances.

Every per-case comparison first checks the produced (and, for fuzz mode, the
reference) arrays against the registered hazard envelope (preregistration §4
item 1 / campaign plan §10.1 item 1: NaN/Inf, ``order_parameter`` outside
``[0, 1]``, ``mean_phase_coherence`` outside ``[-1, 1]``, phase outside its
wrapped range). A breach marks that case ``"aborted": True`` with an
``"abort_reason"`` instead of an ordinary ``within_tolerance`` verdict, so
an invalid run is never silently reported as a scientific refutation — the
batch continues over the remaining cases (preregistration §10: a run may mix
aborted and non-aborted cases). An
amplitude/derivative *clamp trip* is not independently observable from
Python (``prin-dynamics::clamp_derivative`` exposes no trip signal) and is
not checked here; this is a disclosed limitation, not silently skipped.
"""

from __future__ import annotations

import argparse
import json
import re
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
from prin.parity.harness import compare_arrays, compare_case
from prin.parity.loader import CorpusLoader
from prin.parity.schema import CaseArrays, CaseSpec, Coupling, Integrator, Model
from torch.utils.dlpack import from_dlpack

from benchmarks._common.environment import capture_environment
from benchmarks._common.result import (
    OutputPathError,
    write_json_exclusive,
    write_result,
)

EXP_ID = "EXP-001"

#: The PRINet reference implementation H2 compares against (preregistration
#: §6 "Baselines"; corpus ``manifest.json`` ``generator_version``). Fuzz mode
#: aborts if the importable ``prinet`` reports any other version, so a parity
#: result can never be silently produced against a different reference.
PRINET_REFERENCE_VERSION = "3.0.0"

#: Every run directory must be a direct child of this root (campaign plan
#: §7.1 layout). Tests point it at a temp directory.
_RUN_ROOT = Path(__file__).resolve().parents[2] / "benchmarks" / "results" / EXP_ID

#: Canonical run-directory name, campaign plan §7.1:
#: ``RUN-<UTC yyyymmddThhmmssZ>-<short git SHA>-<label>``.
_RUN_ID_RE = re.compile(
    r"^RUN-(?P<utc>\d{8}T\d{6}Z)-(?P<sha>[0-9a-f]{7,40})-(?P<label>[A-Za-z0-9][A-Za-z0-9._-]*)$"
)

#: A ``--label`` must be exactly one safe filename component — the same
#: charset ``_RUN_ID_RE``'s ``<label>`` group accepts. ``main`` embeds it
#: directly into ``result_name = f"{mode}_{label}.json"``, which becomes both
#: a real filesystem path under ``run_dir`` and a key in the
#: ``campaign-metadata.json`` sidecar that ``check_run_complete`` later
#: trusts; an unvalidated label containing ``/``, ``\``, or ``..`` segments
#: can move the resulting path outside ``run_dir`` — confirmed empirically:
#: label ``"x/../../../EXP-002/foreign"`` resolves into a *different*
#: experiment's directory while still passing
#: ``benchmarks._common.result``'s allowed-roots check, since that check only
#: confirms containment under ``benchmarks/results/`` as a whole (CWE-22,
#: CodeRabbit + Copilot).
_LABEL_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]*$")

#: GPU sparse-k-NN kernel-path tolerance (H4; Testing Standards §3;
#: ``prin_kernels::equivalence::{DEFAULT_RTOL, DEFAULT_ATOL}``) — the fused
#: CubeCL kernel computes in f32, so this is *not* the f64 trajectory/metric
#: tolerance used elsewhere in this module.
KERNEL_RTOL = 1e-5
KERNEL_ATOL = 1e-6

#: Shadowing horizon T* (preregistration §6): H2a requires pointwise
#: agreement only through this step (bounded to ``min(T_STAR, n_steps)`` for
#: cases shorter than the horizon); H2b pools ``order_parameter``/
#: ``mean_phase_coherence`` values at every step beyond it. Equal to the
#: golden corpus's own validated trajectory length.
T_STAR = 20

#: Trajectory-shaped arrays H2a's within-horizon pointwise check covers.
_TRAJ_ARRAY_NAMES: tuple[str, ...] = (
    "phase_traj",
    "amplitude_traj",
    "frequency_traj",
    "order_parameter_traj",
    "mean_phase_coherence_traj",
)

#: Arrays H2b pools beyond the horizon (preregistration §2: order-parameter
#: and mean-phase-coherence only — phase/amplitude/frequency beyond the
#: horizon are adjudicated by neither H2a nor H2b).
_BEYOND_HORIZON_ARRAY_NAMES: tuple[str, ...] = (
    "order_parameter_traj",
    "mean_phase_coherence_traj",
)

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
    """Raised when required campaign metadata (campaign plan §7.2) is missing
    or a run directory violates the §7.1 layout contract."""


class PrinetUnavailableError(DriverError):
    """Raised when fuzz mode is requested but the registered PRINet 3.0.0
    reference is not importable, or the importable ``prinet`` is a different
    version.

    Per campaign plan §10.1 item 3, environment capture incomplete for a
    configuration the run requires is an abort, not a negative result.
    """


class IncompleteRunError(DriverError):
    """Raised at run closure when ``campaign-metadata.json`` names an artefact
    that is not present in the run directory.

    The sidecar/result pair is published transactionally only with respect to
    failures the driver itself handles (an exception after the sidecar is
    written rolls the sidecar back). A process kill between the two writes is
    outside that guarantee and leaves a sidecar-only directory; this error is
    how run closure (:func:`check_run_complete`) refuses to manifest one. Per
    preregistration §10 such a directory is recorded as an aborted run — never
    deleted — and the run is retried under a new ``RUN-`` ID.
    """


def prinet_reference_provenance() -> dict[str, str]:
    """Import the PRINet reference and confirm it is the registered 3.0.0.

    Returns:
        ``{"prinet_version": ..., "prinet_source": ...}`` — recorded into the
        fuzz run's ``config`` envelope so the H2 artefact states which
        reference it was actually compared against, rather than assuming it.

    Raises:
        PrinetUnavailableError: If ``prinet`` is not importable, or its
            ``__version__`` is not :data:`PRINET_REFERENCE_VERSION`. Catching
            only ``ImportError`` would let a manually run H2 silently compare
            against whatever ``prinet`` happens to be on ``sys.path`` while the
            artefact still described itself as a PRINet 3.0.0 parity result.
    """
    try:
        import prinet
    except ImportError as exc:
        raise PrinetUnavailableError(
            "fuzz-mode parity requires the archived PRINet 3.0.0 reference "
            "implementation ('prinet') installed; environment incomplete "
            "(campaign plan §10.1 item 3) — aborting"
        ) from exc
    version = str(getattr(prinet, "__version__", ""))
    if version != PRINET_REFERENCE_VERSION:
        raise PrinetUnavailableError(
            f"the importable 'prinet' reports version {version!r}, not the "
            f"registered reference {PRINET_REFERENCE_VERSION!r} "
            f"(preregistration §6) — refusing to produce a parity result "
            "against a different reference; environment incomplete "
            "(campaign plan §10.1 item 3) — aborting"
        )
    return {
        "prinet_version": version,
        "prinet_source": str(Path(str(prinet.__file__)).resolve().parent),
    }


def _validate_label(label: str) -> None:
    """Reject a ``--label`` that is not a single safe filename component.

    See :data:`_LABEL_RE`'s docstring for why: an unvalidated label can move
    ``result_name`` outside ``run_dir`` (CWE-22).

    Raises:
        DriverMetadataError: If ``label`` does not match :data:`_LABEL_RE`.
    """
    if _LABEL_RE.match(label) is None:
        raise DriverMetadataError(
            f"--label {label!r} must be a single filename component "
            "(letters, digits, '.', '_', '-' only, no path separators or "
            "'..' segments) — campaign plan §7.1 <label> convention"
        )


def _reserve_run_dir(run_dir: Path) -> None:
    """Validate and atomically reserve the campaign plan §7.1 run directory.

    A run directory must (1) be named ``RUN-<UTC yyyymmddThhmmssZ>-<short
    SHA>-<label>``, (2) be a direct child of :data:`_RUN_ROOT`
    (``benchmarks/results/EXP-001/``), and (3) not already exist — "a run
    directory is never reused: a re-run, a retry after an abort, or a
    corrected run gets a new RUN- directory". Name and parent are checked up
    front, before any comparison runs, so a typo or accidental retry fails
    fast rather than appending a valid-looking artefact to an unrelated or
    reused directory.

    The directory is then created **here**, via a bare exclusive-create
    ``mkdir()`` (no ``exist_ok``) — not left to
    ``benchmarks._common.result.write_json_exclusive``'s later
    ``mkdir(parents=True, exist_ok=True)`` call, which is a no-op if the
    directory already exists. Deferring creation that way leaves a window in
    which two concurrent invocations can both pass an ``exists()`` check and
    the later one publish into a directory it never reserved, violating the
    never-reused contract (CodeRabbit) — the same TOCTOU class already
    closed for individual files (§5.5/§5.7) applies to the directory itself.
    On failure the reserved directory is **not** removed: a run directory,
    once created, is never reused or deleted (preregistration §10); a failed
    run's directory is left for inspection, and any retry gets a new RUN- ID.

    Raises:
        DriverMetadataError: On a name/parent violation, if the raw-artefact
            root does not exist, or if the directory already exists.
    """
    if _RUN_ID_RE.match(run_dir.name) is None:
        raise DriverMetadataError(
            f"run directory name {run_dir.name!r} does not match the campaign "
            "plan §7.1 form RUN-<UTC yyyymmddThhmmssZ>-<short git SHA>-<label>"
        )
    if run_dir.parent != _RUN_ROOT:
        raise DriverMetadataError(
            f"run directory {run_dir} must be a direct child of {_RUN_ROOT} "
            "(campaign plan §7.1 raw-artefact root for this experiment)"
        )
    if not run_dir.parent.is_dir():
        raise DriverMetadataError(
            f"{run_dir.parent} does not exist; cannot create a run directory "
            "under a missing raw-artefact root"
        )
    try:
        run_dir.mkdir()
    except FileExistsError as exc:
        raise DriverMetadataError(
            f"run directory {run_dir} already exists; a run directory is never "
            "reused (campaign plan §7.1) — re-runs, retries, and corrections "
            "get a new RUN- ID"
        ) from exc


def _is_safe_artefact_name(name: str) -> bool:
    """True iff ``name`` is a plain filename: no separators, no ``.``/``..``."""
    return (
        bool(name) and name not in (".", "..") and "/" not in name and "\\" not in name
    )


def check_run_complete(run_dir: Path) -> dict[str, list[str]]:
    """Run-closure precondition: the sidecar and the directory's result files
    name each other exactly, with no path escapes either way.

    ``tools.reproduce.append_manifest`` inventories every ``*.json`` in a
    directory without reading ``campaign-metadata.json``, so on its own it
    would happily manifest: a sidecar-only directory left by a process kill
    between the sidecar and result writes (missing-artefact case, below); a
    directory holding a result JSON the sidecar never named (unlisted-file
    case, below — the corresponding gap CodeRabbit's finding does not cover
    but Copilot's does: "does not... require every top-level result JSON to
    be listed"); or, if the sidecar's ``artefacts`` mapping were ever
    tampered with or malformed, a name containing ``..`` that resolves
    outside ``run_dir`` entirely (Copilot; the same CWE-22 class as
    :data:`_LABEL_RE`, defended here independently of label validation since
    this function must not trust that every sidecar it is ever pointed at
    was written by a conforming invocation of this driver); or a sidecar
    naming its own infrastructure filename (itself, or ``manifest.json``) as
    one of its artefacts, which would otherwise pass both the missing-file
    check (the file exists — it just isn't a result) and the unlisted-file
    check (it is excluded from ``present`` precisely because it is
    infrastructure) for the wrong reason (Copilot). E3 must call this before
    ``append_manifest`` (see ``benchmarks/results/EXP-001/README.md`` and
    preregistration §5.3).

    Returns:
        The sidecar's ``artefacts`` mapping, for the caller's log.

    Raises:
        IncompleteRunError: If the sidecar is missing or malformed, names an
            unsafe, reserved, or absent artefact path, or the directory
            holds a result JSON the sidecar does not name.
    """
    sidecar = run_dir / "campaign-metadata.json"
    if not sidecar.is_file():
        raise IncompleteRunError(
            f"{run_dir} has no campaign-metadata.json; not a closable run "
            "(campaign plan §7.2)"
        )
    try:
        payload = json.loads(sidecar.read_text(encoding="utf-8"))
        raw = payload["artefacts"]
        if not isinstance(raw, dict) or not raw:
            raise TypeError("artefacts must be a non-empty mapping")
        artefacts = {
            str(name): [str(tag) for tag in tags] for name, tags in raw.items()
        }
    except (ValueError, KeyError, TypeError) as exc:
        raise IncompleteRunError(
            f"{sidecar} is malformed ({exc}); not a closable run"
        ) from exc
    # Run-directory infrastructure the campaign-metadata artefacts mapping
    # never legitimately names: the sidecar always exists (it is what this
    # function is reading), and manifest.json is written by append_manifest
    # *after* this check (it may already exist if this is called again on an
    # already-closed directory). A sidecar naming either as one of its own
    # artefacts would otherwise pass both checks below for the wrong reason —
    # not because a real result was written, but because the infrastructure
    # file it is impersonating as a result already happens to exist.
    infrastructure = {sidecar.name, "manifest.json"}
    unsafe = sorted(
        name
        for name in artefacts
        if not _is_safe_artefact_name(name) or name in infrastructure
    )
    if unsafe:
        raise IncompleteRunError(
            f"{sidecar} names unsafe or reserved artefact path(s) "
            f"{', '.join(unsafe)} (must be a plain filename directly in "
            f"run_dir, no path separators or '..' segments, and not one of "
            f"the reserved infrastructure names {sorted(infrastructure)}) — "
            "refusing to treat as a closable run"
        )
    missing = sorted(name for name in artefacts if not (run_dir / name).is_file())
    if missing:
        raise IncompleteRunError(
            f"{run_dir} is incomplete: campaign-metadata.json names "
            f"{', '.join(missing)} but the file(s) are not present — the run "
            "was interrupted between the sidecar and result writes. Record it "
            "as aborted (preregistration §10; never delete it) and retry under "
            "a new RUN- ID; do not manifest it."
        )
    present = {
        path.name
        for path in run_dir.iterdir()
        if path.is_file() and path.suffix == ".json" and path.name not in infrastructure
    }
    unlisted = sorted(present - set(artefacts))
    if unlisted:
        raise IncompleteRunError(
            f"{run_dir} holds result file(s) {', '.join(unlisted)} that "
            "campaign-metadata.json does not name in its artefacts mapping "
            "— refusing to treat as a closable run"
        )
    return artefacts


def _case_arrays_hazard_violation(label: str, arrays: CaseArrays) -> str | None:
    """Return a human-readable abort reason if ``arrays`` breaches the
    registered hazard envelope, or ``None`` if clean.

    Checks (preregistration §4 item 1 / campaign plan §10.1 item 1): NaN/Inf
    in any array; ``order_parameter_traj`` outside ``[0, 1]``
    (``kuramoto_order_parameter`` = ``norm().min(1.0)`` of the complex mean
    field, `crates/prin-metrics/src/order.rs`); ``mean_phase_coherence_traj``
    outside ``[-1, 1]`` (a mean pairwise cosine, clamped to that range —
    *not* ``[0, 1]``, `crates/prin-metrics/src/coherence.rs`); ``phase_traj``
    outside the wrapped ``[0, 2*pi)`` range. Does **not** check for an
    amplitude/derivative clamp trip — ``prin-dynamics::clamp_derivative``
    exposes no trip signal to Python, so that sub-criterion is not
    mechanically detectable here; it is a disclosed limitation
    (preregistration §4 item 1 note), not a silent skip.
    """
    for name in CaseArrays._ARRAY_NAMES:
        if not np.all(np.isfinite(getattr(arrays, name))):
            return f"{label}: non-finite value(s) in {name} (NaN/Inf hazard guard trip)"
    if np.any(arrays.order_parameter_traj < 0.0) or np.any(
        arrays.order_parameter_traj > 1.0
    ):
        return f"{label}: order_parameter_traj outside the registered [0, 1] range"
    if np.any(arrays.mean_phase_coherence_traj < -1.0) or np.any(
        arrays.mean_phase_coherence_traj > 1.0
    ):
        return (
            f"{label}: mean_phase_coherence_traj outside the registered [-1, 1] range"
        )
    if np.any(arrays.phase_traj < 0.0) or np.any(arrays.phase_traj >= 2.0 * np.pi):
        return f"{label}: phase_traj outside the wrapped [0, 2*pi) range"
    return None


def _finite_violation(label: str, name: str, array: NDArray[np.float64]) -> str | None:
    """Return an abort reason if ``array`` has a non-finite value, else ``None``.

    Used for H4's raw derivative arrays, which are not :class:`CaseArrays`
    (no order-parameter/phase-wrap concept applies to a derivative).
    """
    if not np.all(np.isfinite(array)):
        return f"{label}: non-finite value(s) in {name} (NaN/Inf hazard guard trip)"
    return None


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


def _case_identity(spec: CaseSpec) -> dict[str, Any]:
    """Return the identifying fields shared by every corpus-derived record."""
    return {
        "case_id": spec.case_id,
        "model": spec.model,
        "coupling": spec.coupling,
        "integrator": spec.integrator,
        "n_oscillators": spec.n_oscillators,
        "n_steps": spec.n_steps,
        "dt": spec.dt,
        "seed": spec.seed,
    }


def compare_corpus_case(loader: CorpusLoader, case_id: str) -> dict[str, Any]:
    """Compare one golden-corpus case's PRIN reproduction against its reference.

    Returns:
        A JSON-serializable per-case record: identifying fields, an
        ``"aborted"`` flag, and — when not aborted — the overall
        ``within_tolerance`` verdict and every array-level
        :class:`~prin.parity.harness.ComparisonResult`. An aborted record
        carries ``"abort_reason"`` instead (campaign plan §10.1 item 1): a
        hazard-envelope breach is never silently reported as a tolerance
        failure.
    """
    loaded = loader.load(case_id)
    spec = loaded.spec
    identity = _case_identity(spec)
    produced = run_prin_case(spec, loaded.arrays)
    violation = _case_arrays_hazard_violation("produced", produced)
    if violation is not None:
        return {**identity, "aborted": True, "abort_reason": violation}
    comparisons = compare_case(loaded.arrays, produced, spec.model)
    return {
        **identity,
        "aborted": False,
        "within_tolerance": all(c.within_tolerance for c in comparisons),
        "comparisons": [c.to_dict() for c in comparisons],
    }


def compare_corpus_subset(
    loader: CorpusLoader, case_ids: Sequence[str]
) -> list[dict[str, Any]]:
    """Compare every case in ``case_ids`` (see :func:`compare_corpus_case`)."""
    return [compare_corpus_case(loader, case_id) for case_id in case_ids]


def _bit_identical(a: NDArray[Any], b: NDArray[Any]) -> bool:
    """Return ``True`` iff ``a`` and ``b`` share dtype, shape, and raw bytes.

    Stricter than ``numpy.array_equal``, which compares element values only:
    it does not check ``dtype`` and (with its default ``equal_nan=False``)
    still permits distinct byte patterns that compare equal as values (e.g.
    signed-zero). H3 claims *bit-level* repeatability, so the check compares
    the actual memory representation.
    """
    return (
        a.dtype == b.dtype
        and a.shape == b.shape
        and np.ascontiguousarray(a).tobytes() == np.ascontiguousarray(b).tobytes()
    )


def check_repeatability(loader: CorpusLoader, case_id: str) -> dict[str, Any]:
    """Run a corpus case's PRIN reproduction twice and require bit-identity.

    Implements the campaign plan §6.5 repeatability gate for one configuration:
    identical scientific inputs must produce byte-identical outputs.
    """
    loaded = loader.load(case_id)
    first = run_prin_case(loaded.spec, loaded.arrays)
    second = run_prin_case(loaded.spec, loaded.arrays)
    for label, arrays in (("first", first), ("second", second)):
        violation = _case_arrays_hazard_violation(label, arrays)
        if violation is not None:
            return {"case_id": case_id, "aborted": True, "abort_reason": violation}
    mismatched = [
        name
        for name in CaseArrays._ARRAY_NAMES
        if not _bit_identical(getattr(first, name), getattr(second, name))
    ]
    return {
        "case_id": case_id,
        "aborted": False,
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
        PrinetUnavailableError: If ``prinet`` or ``torch`` is not importable,
            or the importable ``prinet`` is not the registered
            :data:`PRINET_REFERENCE_VERSION` (checked via
            :func:`prinet_reference_provenance` on every call — cheap, and it
            keeps this function correct even when invoked outside ``main``).
    """
    prinet_reference_provenance()
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

    Implements the H2a/H2b split (preregistration §2, §6): ``within_tolerance``/
    ``comparisons`` are H2a's pointwise verdict, bounded to steps
    ``0..min(T_STAR, n_steps)`` inclusive (:data:`_TRAJ_ARRAY_NAMES` plus the
    ``_init`` arrays; ``_final`` is excluded — beyond the horizon it names a
    step no hypothesis adjudicates pointwise, and within it it duplicates the
    corresponding ``_traj`` array's last included row). When ``n_steps >
    T_STAR``, ``beyond_horizon`` carries the raw paired
    ``order_parameter``/``mean_phase_coherence`` values at every step past the
    horizon (else ``None``) for E4 to pool across cases and compute H2b's
    Welch-t/Cohen's-d/bootstrap-CI verdict — this driver stores the data, it
    does not compute that pooled statistic itself (E3 executes, E4 analyzes).

    Args:
        spec: A dict from :func:`draw_fuzz_spec`, plus an ``"rng"`` key
            (``numpy.random.Generator``) used to draw the shared initial
            condition (kept out of the returned record).

    Returns:
        A JSON-serializable record: identifying fields, an ``"aborted"``
        flag, and either ``"abort_reason"`` or the H2a/H2b fields above.

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
    identity = {
        "seed": spec["seed"],
        "model": spec["model"],
        "coupling": spec["coupling"],
        "integrator": spec["integrator"],
        "n_oscillators": spec["n_oscillators"],
        "n_steps": spec["n_steps"],
        "dt": spec["dt"],
    }
    for label, arrays in (("reference", reference), ("produced", produced)):
        violation = _case_arrays_hazard_violation(label, arrays)
        if violation is not None:
            return {**identity, "aborted": True, "abort_reason": violation}

    n_steps = spec["n_steps"]
    horizon = min(T_STAR, n_steps)
    h2a_comparisons = [
        compare_arrays(
            getattr(reference, name), getattr(produced, name), name, spec["model"]
        )
        for name in ("phase_init", "amplitude_init", "frequency_init")
    ] + [
        compare_arrays(
            getattr(reference, name)[: horizon + 1],
            getattr(produced, name)[: horizon + 1],
            name,
            spec["model"],
        )
        for name in _TRAJ_ARRAY_NAMES
    ]
    beyond_horizon = None
    if n_steps > T_STAR:
        beyond_horizon = {
            name: {
                "reference": getattr(reference, name)[horizon + 1 :].tolist(),
                "produced": getattr(produced, name)[horizon + 1 :].tolist(),
            }
            for name in _BEYOND_HORIZON_ARRAY_NAMES
        }
    return {
        **identity,
        "aborted": False,
        "horizon": horizon,
        "within_tolerance": all(c.within_tolerance for c in h2a_comparisons),
        "comparisons": [c.to_dict() for c in h2a_comparisons],
        "beyond_horizon": beyond_horizon,
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
    state for the CPU (f64 Rust) reference, and calls
    ``prin._prin_core.GpuSparseKuramoto`` directly (not through
    ``prin._torch_compat``'s ``_compute_derivatives_gpu`` dispatch hook) for
    the GPU (f32 CubeCL) side, so the raw DLPack result can be inspected for
    its true device before any placement-normalizing ``.to()`` call — see the
    note below. Compares within the registered ``KERNEL_RTOL``/
    ``KERNEL_ATOL`` tolerance.

    Raises:
        GpuBindingUnavailableError: If the extension lacks
            ``GpuSparseKuramoto`` (no ``cuda``/``wgpu``-feature build), or if
            the GPU call does not confirm true CUDA execution (see note
            below).
        ValueError: If ``case_id`` does not name a ``kuramoto``/``sparse_knn``
            case.

    Note:
        ``GpuSparseKuramoto`` compiles under ``cfg(any(feature = "cuda",
        feature = "wgpu"))`` (``crates/prin-py/src/bindings/mod.rs``), and its
        backend (``cubecl-cuda`` vs. ``cubecl-wgpu``) is a compile-time
        choice. Even a ``--features cuda`` build silently falls back to a
        host-slice (CPU) compute path when ``try_create_client()`` cannot
        initialise a device (``crates/prin-sim/src/gpu.rs``) — so neither
        the binding's presence nor ``torch.cuda.is_available()`` proves this
        call actually dispatched through CUDA. The true CUDA device-resident
        path is the only one that returns a zero-copy ``kDLCUDA`` capsule
        (WP-036E Q3); everything else (wgpu, CPU-SIMD, host-slice fallback)
        returns a CPU-resident capsule (module docstring,
        ``crates/prin-py/src/bindings/gpu.rs``). This function therefore
        calls the binding directly and checks the *raw* result's
        ``.device.type`` — the only ground-truth signal — instead of relying
        on ``prin._torch_compat``'s dispatch hook, whose ``_from_gpu`` always
        normalizes the result to the input tensor's device and would hide
        this distinction either way.
    """
    if not hasattr(_prin_core, "GpuSparseKuramoto"):
        raise GpuBindingUnavailableError(
            "prin._prin_core.GpuSparseKuramoto is absent (extension built "
            "without --features cuda or --features wgpu); H4 kernel-path "
            "mode aborts"
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

    phase_f32 = torch.as_tensor(
        loaded.arrays.phase_init, dtype=torch.float32
    ).contiguous()
    amplitude_f32 = torch.as_tensor(
        loaded.arrays.amplitude_init, dtype=torch.float32
    ).contiguous()
    frequency_f32 = torch.as_tensor(
        loaded.arrays.frequency_init, dtype=torch.float32
    ).contiguous()
    engine = _prin_core.GpuSparseKuramoto.from_knn_phase(
        spec.n_oscillators,
        int(parameters["sparse_k"]),
        float(parameters["coupling_strength"]),
        float(parameters.get("decay_rate", 0.0)),
        float(parameters.get("freq_adaptation_rate", 0.0)),
        phase_f32,
    )
    gpu_dphase_capsule, gpu_damplitude_capsule, gpu_dfrequency_capsule = (
        engine.compute_derivatives(phase_f32, amplitude_f32, frequency_f32)
    )
    gpu_dphase_raw = from_dlpack(gpu_dphase_capsule)
    if gpu_dphase_raw.device.type != "cuda":
        raise GpuBindingUnavailableError(
            "GpuSparseKuramoto.compute_derivatives returned a "
            f"{gpu_dphase_raw.device.type!r}-resident result for case "
            f"{case_id!r}, not the zero-copy kDLCUDA capsule the true CUDA "
            "device-resident path returns. This means the call did not "
            "actually dispatch through CUDA here — a --features wgpu-only "
            "build, or a CUDA client that failed to initialise and fell "
            "back to prin-sim's host-slice path — so H4 aborts rather than "
            "record a non-CUDA result as cuda (preregistration §5.1)"
        )
    gpu_damplitude_raw = from_dlpack(gpu_damplitude_capsule)
    gpu_dfrequency_raw = from_dlpack(gpu_dfrequency_capsule)

    identity = {
        "case_id": case_id,
        "model": spec.model,
        "coupling": spec.coupling,
        "n_oscillators": spec.n_oscillators,
        "sparse_k": int(parameters["sparse_k"]),
    }
    pairs = [
        (
            "dphase",
            cpu_dphase.detach().to(dtype=torch.float64, device="cpu").numpy(),
            gpu_dphase_raw.detach().to(dtype=torch.float64, device="cpu").numpy(),
        ),
        (
            "damplitude",
            cpu_damplitude.detach().to(dtype=torch.float64, device="cpu").numpy(),
            gpu_damplitude_raw.detach().to(dtype=torch.float64, device="cpu").numpy(),
        ),
        (
            "dfrequency",
            cpu_dfrequency.detach().to(dtype=torch.float64, device="cpu").numpy(),
            gpu_dfrequency_raw.detach().to(dtype=torch.float64, device="cpu").numpy(),
        ),
    ]
    for label, cpu_arr, gpu_arr in pairs:
        for source, arr in (("cpu", cpu_arr), ("gpu", gpu_arr)):
            violation = _finite_violation(source, label, arr)
            if violation is not None:
                return {**identity, "aborted": True, "abort_reason": violation}
    comparisons = [
        _compare_kernel_array(name, cpu_arr, gpu_arr)
        for name, cpu_arr, gpu_arr in pairs
    ]
    return {
        **identity,
        "aborted": False,
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

    Delegates the path-safety check and the stage-then-exclusive-create
    write to ``benchmarks._common.result.write_json_exclusive`` (DV-038): a
    check-then-write is not atomic, so two concurrent invocations could both
    pass an ``exists()`` check and the later one silently overwrite the
    earlier sidecar. Sharing that primitive with ``write_result`` (rather
    than reimplementing the same ``json.dump``/``os.link`` sequence here)
    keeps one place responsible for confining and safely publishing every
    operator-supplied output path in this driver.

    Raises:
        DriverMetadataError: If required metadata is missing.
        OutputPathError: If ``run_dir`` resolves outside the declared output
            roots (Coding Standards §6.1).
        ArtefactExistsError: If the sidecar already exists (append-only).
    """
    _validate_metadata(exp_id, run_id, session, operator)
    path = run_dir / "campaign-metadata.json"
    payload = {
        "exp_id": exp_id,
        "run_id": run_id,
        "session": session,
        "operator": operator,
        "artefacts": artefacts,
    }
    return write_json_exclusive(
        path,
        payload,
        conflict_message=(
            f"{path.resolve()} already exists; campaign metadata is "
            "append-only (campaign plan §7.3) — write to a new run "
            "directory instead"
        ),
    )


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
    parser.add_argument(
        "--out",
        type=Path,
        required=True,
        help="Run directory: a NEW, not-yet-existing direct child of "
        "benchmarks/results/EXP-001/ named "
        "RUN-<UTC yyyymmddThhmmssZ>-<short git SHA>-<label> (campaign plan "
        "§7.1). Rejected otherwise, before any comparison runs.",
    )
    parser.add_argument(
        "--label",
        required=True,
        help="Short pre-registered tag (e.g. corpus-cpu, seedrep0). A single "
        "filename component: letters, digits, '.', '_', '-' only — no path "
        "separators or '..' segments (campaign plan §7.1).",
    )
    parser.add_argument("--session", required=True)
    parser.add_argument("--operator", required=True)
    return parser


def main(argv: list[str] | None = None) -> int:
    """Run the requested comparison and write its artefact + metadata sidecar."""
    args = _parser().parse_args(argv)
    run_dir: Path = args.out.resolve()
    run_id = run_dir.name

    # Fuzz mode records which PRINet reference it actually compared against;
    # empty for the other modes, whose reference is the stored golden corpus.
    reference: dict[str, str] = {}
    try:
        _validate_metadata(EXP_ID, run_id, args.session, args.operator)
        _validate_label(args.label)
        _reserve_run_dir(run_dir)
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
            # Validate the reference *before* the batch so a wrong/missing
            # prinet aborts in milliseconds, not after 1,000 integrations.
            reference = prinet_reference_provenance()
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
        **reference,
    }
    result_name = f"{args.mode}_{args.label}.json"
    result_path = run_dir / result_name

    # Fast fail on a *pre-existing* result (a stale artefact from an earlier
    # invocation targeting this same run directory/label, e.g. a retry).
    # This is only a cheap check, not a reservation — a concurrent writer can
    # still create the path between here and `write_result` below, which is
    # what the rollback further down actually closes.
    if result_path.exists():
        print(
            f"ABORT: {result_path} already exists; raw benchmark artefacts "
            "are append-only (Experimentation Standards §4) — write to a "
            "new run directory instead",
            file=sys.stderr,
        )
        return 2

    # The sidecar/result pair is published transactionally: either both land
    # or neither does.
    #
    # The sidecar goes first because campaign plan §7.2 only accepts a result
    # that carries its provenance — writing the result first would let a
    # sidecar failure strand unprovenanced evidence. The mirror risk (a
    # sidecar naming a result this invocation never published, e.g. because a
    # concurrent writer won the result path first) is closed by rolling the
    # sidecar back on any failure below. That rollback can only ever remove
    # *this* invocation's own sidecar: `write_campaign_metadata` publishes via
    # exclusive-create and raises if one already exists, so reaching this
    # point proves we created it.
    metadata_path = write_campaign_metadata(
        run_dir,
        exp_id=EXP_ID,
        run_id=run_id,
        session=args.session,
        operator=args.operator,
        artefacts={result_name: _MODE_HYPOTHESIS[args.mode]},
    )
    try:
        result_path = write_result(
            result_path,
            environment=environment,
            config=config,
            payload={"cases": cases},
        )
    except OutputPathError as exc:
        metadata_path.unlink(missing_ok=True)
        print(f"ABORT: {exc}", file=sys.stderr)
        return 2
    except BaseException:
        metadata_path.unlink(missing_ok=True)
        raise
    print(f"Wrote {result_path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
