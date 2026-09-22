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
  shadowing horizon, and H2b records, per case and per metric, the raw
  beyond-horizon ``order_parameter``/``mean_phase_coherence`` pairs **and the
  one predefined paired summary** (the case's mean paired difference) that is
  the registered unit of analysis — post-horizon steps of one trajectory are
  serially dependent and are never treated as independent observations. E3
  (this module's ``main``) only records them; E4 adjudicates them with
  :func:`adjudicate_h2b`, the single implementation of the registered
  per-metric equivalence predicate (see :func:`compare_fuzz_case`).
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
definition of valid fuzz-case space — but draws every value directly from
``prin._prin_core.Seed(seed_counter, seed_key)``, the campaign's single
registered randomness authority, rather than from Hypothesis's internal
engine or from a NumPy ``Generator`` (Project Plan §4 rule 3; campaign plan
§6.1, "no experiment may introduce a second RNG path"). An earlier revision
derived a NumPy PCG64 stream from the registered pair; it reproduced
deterministically but was literally that second RNG path, and is gone
(preregistration §5.12).

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
from prin.parity.schema import (
    CaseArrays,
    CaseSpec,
    CorpusValidationError,
    Coupling,
    Integrator,
    Model,
)
from prin.y4q1_tools import bootstrap_ci, cohens_d, welch_t_test
from torch.utils.dlpack import from_dlpack

from benchmarks._common.environment import capture_environment
from benchmarks._common.result import (
    ArtefactExistsError,
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
#: ``RUN-<UTC yyyymmddThhmmssZ>-<short git SHA>-<label>``. Anchored with
#: ``\Z``, not ``$``: Python's ``$`` (without ``re.MULTILINE``) matches at the
#: end of the string *or* just before a trailing ``\n`` — confirmed
#: empirically, ``re.match(r"...\$", "safe\n")`` succeeds — so a name with a
#: trailing newline would otherwise pass this "safe filename" check and reach
#: ``mkdir()``/``write_json_exclusive`` with a literal control character in
#: it (Copilot). ``\Z`` matches only the true end of the string.
_RUN_ID_RE = re.compile(
    r"^RUN-(?P<utc>\d{8}T\d{6}Z)-(?P<sha>[0-9a-f]{7,40})-(?P<label>[A-Za-z0-9][A-Za-z0-9._-]*)\Z"
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
#: CodeRabbit + Copilot). Anchored with ``\Z`` for the same reason as
#: :data:`_RUN_ID_RE` — ``$`` alone admits a trailing-newline label.
_LABEL_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]*\Z")

#: The four registered run modes, each producing exactly one result artefact
#: named ``<mode>_<label>.json`` (preregistration §5.3). ``<label>`` matches
#: :data:`_LABEL_RE`, which excludes ``_``, so the mode is recoverable from a
#: result filename by splitting on the first ``_`` — the basis on which
#: :func:`check_run_complete` checks that a sidecar's hypothesis tags are the
#: ones registered for the mode that actually produced the file.
_MODE_HYPOTHESIS: dict[str, list[str]] = {
    "corpus": ["H1"],
    "repeatability": ["H3"],
    "fuzz": ["H2"],
    "kernel-path": ["H4"],
}

#: One ``campaign-metadata.json`` ``artefacts`` entry value: a list of the
#: hypothesis tags the result bears on, or — for a GPU result — an object
#: additionally carrying ``timing_method`` (campaign plan §7.2).
ArtefactEntry = list[str] | dict[str, Any]

#: Every hypothesis tag EXP-001 registers (preregistration §2). A sidecar tag
#: outside this set is rejected rather than coerced.
_VALID_HYPOTHESES: frozenset[str] = frozenset({"H1", "H2", "H3", "H4"})

#: Modes whose result is a GPU entry, and which therefore additionally carry
#: ``timing_method`` in the sidecar (campaign plan §7.2).
_GPU_MODES: frozenset[str] = frozenset({"kernel-path"})

#: ``timing_method`` values this driver accepts. ``device-event`` and
#: ``system-synced`` are campaign plan §7.2's registered pair (DV-003 /
#: Project Plan amendment #44). ``not-timed`` is an EXP-001 **pre-execution
#: extension** (preregistration §5.12): H4 is a correctness comparison that
#: performs no timing measurement at all (preregistration §5.1, "No H2/H3/H4
#: case is timed"), so neither registered value describes it truthfully, and
#: recording either would assert a timing method that was never used. The
#: extension widened a frozen plan enum and so required maintainer
#: ratification (campaign plan §14.2) before E3; **ratified 2026-09-22**
#: (campaign plan §11.5, §14.2 amendment row 2) — this is not an open gate.
KERNEL_PATH_TIMING_METHOD = "not-timed"
_TIMING_METHODS: frozenset[str] = frozenset(
    {"device-event", "system-synced", KERNEL_PATH_TIMING_METHOD}
)

#: Required ``campaign-metadata.json`` top-level fields (campaign plan §7.2).
_REQUIRED_SIDECAR_FIELDS: tuple[str, ...] = (
    "exp_id",
    "run_id",
    "session",
    "operator",
    "artefacts",
)

#: Required ``environment`` block fields (campaign plan §7.2; Benchmarking and
#: Reproducibility Standards §1.4). A ``null`` in any of these for a
#: configuration the run requires is a registered abort, not a result
#: (campaign plan §10.1 item 3 / preregistration §4 item 3).
_REQUIRED_ENV_FIELDS: tuple[str, ...] = (
    "prin_version",
    "git_commit",
    "rust_version",
    "python_version",
    "platform",
    "processor",
    "logical_cpus",
    "backend",
    "dtype",
    "seed",
)

#: Environment fields additionally required on a GPU leg — campaign plan
#: §10.1 item 3 names ``gpu`` null on a GPU leg as its own example.
_GPU_REQUIRED_ENV_FIELDS: tuple[str, ...] = ("gpu", "gpu_vram_mb")

#: Required ``config`` envelope fields (campaign plan §7.2).
_REQUIRED_CONFIG_FIELDS: tuple[str, ...] = (
    "iterations",
    "warmup",
    "seed_counter",
    "seed_key",
    "out_dir",
)

#: Registered confirmatory fuzz batch size (preregistration §7: "≥1,000
#: fuzzed cases"). A batch below this is published with
#: ``config.fuzz_batch_class == "pilot"`` so it can never be read as the
#: registered confirmatory H2 evidence; see :func:`main`.
REGISTERED_FUZZ_BATCH_MIN = 1000

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

#: Registered per-metric equivalence margins for H2b (preregistration §5.12).
#: Each is **1 % of the metric's own bounded range** — ``order_parameter``
#: lives in ``[0, 1]`` and ``mean_phase_coherence`` in ``[-1, 1]`` — the
#: domain justification being that a mean beyond-horizon difference below one
#: percent of a bounded coherence measure's range cannot move a synchronised/
#: incoherent classification or a phase-boundary location, which is what the
#: C1 replication target actually is (campaign plan §2.1). The margins are
#: metric-specific and are never applied to a pooled cross-metric sample.
H2B_EQUIVALENCE_MARGIN: dict[str, float] = {
    "order_parameter_traj": 0.01,
    "mean_phase_coherence_traj": 0.02,
}

#: Minimum number of contributing cases for a valid H2b sample
#: (preregistration §5.12). Below this the metric is ``INCONCLUSIVE`` for lack
#: of information rather than adjudicated on a bootstrap the sample cannot
#: support. The registered ≥1,000-case batch draws ``n_steps`` uniformly in
#: ``[5, 50]``, so ~60 % of cases clear ``T_STAR`` and this floor is not a
#: practical constraint on a conforming confirmatory run.
H2B_MIN_CASES = 30

#: Bootstrap parameters for H2b (preregistration §7; campaign plan §9.1
#: "≥ 10,000 resamples, seeded"). ``prin.y4q1_tools.bootstrap_ci`` delegates
#: to the Rust owner ``y4q1_stats::bootstrap_ci``.
H2B_BOOTSTRAP_RESAMPLES = 10_000
H2B_BOOTSTRAP_SEED = 42
H2B_ALPHA = 0.05

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


def _validate_case_ids(case_ids: Sequence[str] | None) -> None:
    """Reject a repeated ``--case-id`` value.

    Every mode that accepts ``--case-id`` (``corpus``, ``repeatability``,
    ``kernel-path``) treats the count of records it produces as meaningful:
    the preregistration §8 adjudication rule reads a mode's ``len(cases)``
    (via the artefact's non-aborted count) against a *registered denominator*
    (504 for H1, 14 for H3, 72 for H4). Nothing else in this module requires
    ``case_ids`` to be a set — an operator (or a scripting bug) repeating one
    passing ID 504 times would produce an H1-tagged artefact with 504
    records that are not 504 distinct corpus cases, satisfying the naive
    count check without covering the registered corpus at all (Copilot).
    There is no legitimate reason to name the same corpus case twice within
    one invocation, so the smallest safe fix is to reject the duplicate
    outright rather than build a separate "confirmatory vs. subset" artefact
    classification.

    Raises:
        DriverMetadataError: If ``case_ids`` contains a duplicate.
    """
    if case_ids is None:
        return
    seen: set[str] = set()
    duplicates: set[str] = set()
    for cid in case_ids:
        if cid in seen:
            duplicates.add(cid)
        seen.add(cid)
    if duplicates:
        raise DriverMetadataError(
            f"--case-id repeated for {', '.join(sorted(duplicates))}; each --case-id "
            "must name a distinct corpus case, since the registered "
            "denominator (preregistration §8) counts records, not requests"
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


def _is_json_name(name: str) -> bool:
    """True iff ``name`` is *recognised* as a JSON file, case-insensitively.

    Recognition is case-insensitive while the canonical spelling required by
    :func:`_declared_name_violation` is lowercase ``.json``:
    ``pathlib.Path.glob("*.json")`` — which
    ``tools.reproduce.append_manifest``/``verify_manifest`` use to inventory a
    run directory — is **case-insensitive on Windows and case-sensitive on
    Linux** (verified empirically; both platforms are in this project's CI
    matrix). A ``rogue.JSON`` is therefore manifested on one platform and
    invisible on the other. Recognising it here regardless of case, and then
    rejecting the non-canonical spelling explicitly, makes the closure and
    manifest contract deterministic instead of inheriting the host
    filesystem's behaviour.

    No non-empty-stem requirement: ``glob("*.json")`` matches the bare name
    ``.json`` too (``*`` matches an empty prefix, verified empirically), so a
    top-level ``.json`` file would otherwise be manifested while invisible to
    this recognition check — a declared ``.json`` is still rejected downstream
    by :func:`_result_name_mode` (an empty ``mode`` before the ``_`` never
    matches a registered mode), so relaxing this check does not admit it as a
    valid declared artefact.
    """
    _stem, dot, suffix = name.rpartition(".")
    return bool(dot) and suffix.casefold() == "json"


def _result_name_mode(name: str) -> str | None:
    """Return the run mode a canonical ``<mode>_<label>.json`` name encodes.

    ``main`` writes exactly one result per invocation, named
    ``f"{mode}_{label}.json"`` (preregistration §5.3), and :data:`_LABEL_RE`
    excludes ``_`` from a label, so the first ``_`` separates the two
    unambiguously. Returns ``None`` if ``name`` is not such a name.
    """
    stem, dot, suffix = name.rpartition(".")
    if not dot or suffix != "json":
        return None
    mode, sep, label = stem.partition("_")
    if not sep or mode not in _MODE_HYPOTHESIS or _LABEL_RE.match(label) is None:
        return None
    return mode


def _declared_name_violation(name: str, infrastructure: frozenset[str]) -> str | None:
    """Return why ``name`` is not an acceptable declared artefact, else ``None``."""
    if not _is_safe_artefact_name(name):
        return (
            "is not a plain filename directly in run_dir (no path separators "
            "or '.'/'..' segments)"
        )
    if name.casefold() in infrastructure:
        return (
            "is a reserved run-directory infrastructure name "
            f"({', '.join(sorted(infrastructure))}, matched case-insensitively)"
        )
    if not _is_json_name(name):
        return (
            "does not have a '.json' suffix; the run manifest inventories "
            "'*.json' only (campaign plan §7.2), so a non-JSON artefact could "
            "never be covered by it"
        )
    if not name.endswith(".json"):
        return (
            "spells its suffix in a non-canonical case; Path.glob('*.json') "
            "matches it on Windows but not on Linux, so it must be written "
            "lowercase to be manifested deterministically on both"
        )
    if _result_name_mode(name) is None:
        return (
            "is not a registered '<mode>_<label>.json' result name (modes: "
            f"{', '.join(sorted(_MODE_HYPOTHESIS))}; the label carries no "
            "'_' and matches the campaign plan §7.1 label charset)"
        )
    return None


def _declared_tags_violation(mode: str, value: object) -> tuple[list[str], str | None]:
    """Validate one sidecar ``artefacts`` entry value against its result mode.

    Returns ``(hypotheses, violation)``. The hypothesis list is meaningful
    only when ``violation`` is ``None``; a malformed value is never coerced
    into a valid-looking one. In particular the entry is **not** rebuilt with
    ``[str(tag) for tag in value]``, which silently splats the string
    ``"H9"`` into the two "tags" ``["H", "9"]`` instead of rejecting it.

    A GPU entry (campaign plan §7.2: "GPU result entries additionally carry
    ``timing_method``") is an object with ``hypotheses`` and
    ``timing_method``; every other entry is a bare list of hypothesis tags.
    """
    if mode in _GPU_MODES:
        if not isinstance(value, dict):
            return [], (
                "must be an object {'hypotheses': [...], 'timing_method': ...} "
                "— a GPU result entry additionally carries timing_method "
                "(campaign plan §7.2)"
            )
        unexpected = sorted(set(value) - {"hypotheses", "timing_method"})
        if unexpected:
            return [], f"has unexpected key(s) {', '.join(unexpected)}"
        timing_method = value.get("timing_method")
        if not isinstance(timing_method, str) or timing_method not in _TIMING_METHODS:
            return [], (
                f"has timing_method {timing_method!r}, not one of "
                f"{', '.join(sorted(_TIMING_METHODS))}"
            )
        raw_tags: object = value.get("hypotheses")
    else:
        if isinstance(value, dict):
            return [], (
                "must be a list of hypothesis tags; only GPU result entries "
                f"({', '.join(sorted(_GPU_MODES))}) use the object form"
            )
        raw_tags = value
    if not isinstance(raw_tags, list) or not raw_tags:
        return [], (
            f"has hypothesis tags {raw_tags!r}, which is not a non-empty list "
            "(a bare string is not a tag list)"
        )
    if not all(isinstance(tag, str) for tag in raw_tags):
        return [], f"has non-string hypothesis tag(s) in {raw_tags!r}"
    tags = [str(tag) for tag in raw_tags]
    unknown = sorted(set(tags) - _VALID_HYPOTHESES)
    if unknown:
        return [], (
            f"names unregistered hypothesis tag(s) {', '.join(unknown)} "
            f"(registered: {', '.join(sorted(_VALID_HYPOTHESES))})"
        )
    registered = _MODE_HYPOTHESIS[mode]
    if sorted(tags) != sorted(registered):
        return [], (
            f"is tagged {tags} but a {mode!r} result bears {registered} "
            "(preregistration §5.3)"
        )
    return tags, None


def _envelope_violation(path: Path, run_dir: Path, mode: str) -> str | None:
    """Return why a declared result's envelope is unacceptable, else ``None``.

    Campaign plan §7.2 fixes the result envelope: an ``environment`` block
    carrying the Benchmarking and Reproducibility Standards §1.4 fields and a
    ``config`` block carrying ``iterations``, ``warmup``, ``seed_counter``,
    ``seed_key``, and ``out_dir``. Closure validates that schema and
    cross-checks the two values that tie an envelope to the sidecar it is
    being closed against: ``config.out_dir`` must resolve to this run
    directory, and a GPU entry's ``environment.backend`` must be the ``cuda``
    backend that entry asserts.

    The required-field set and the null/empty rule mirror
    :func:`_validate_environment` exactly — a GPU mode additionally requires
    :data:`_GPU_REQUIRED_ENV_FIELDS`, and a field present but ``None``/``""``
    is treated as absent — so closure can never accept a result ``main``
    itself would have refused to publish. A field that is legitimately
    falsy-but-present (``config.warmup == 0``, ``config.iterations == 0``) is
    unaffected: ``0`` is neither ``None`` nor ``""``.
    """
    try:
        document = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError) as exc:
        return f"is not readable as JSON ({exc})"
    if not isinstance(document, dict):
        return "is not a JSON object"
    for block_name, required in (
        ("environment", _REQUIRED_ENV_FIELDS),
        ("config", _REQUIRED_CONFIG_FIELDS),
    ):
        block = document.get(block_name)
        if not isinstance(block, dict):
            return f"has no {block_name!r} object (campaign plan §7.2 envelope)"
        if block_name == "environment" and mode in _GPU_MODES:
            required = (*required, *_GPU_REQUIRED_ENV_FIELDS)
        incomplete = [field for field in required if block.get(field) in (None, "")]
        if incomplete:
            return (
                f"{block_name!r} is missing or has null/empty required "
                f"field(s) {', '.join(incomplete)}"
            )
    config = document["config"]
    environment = document["environment"]
    out_dir = config["out_dir"]
    if not isinstance(out_dir, str) or Path(out_dir).resolve() != run_dir:
        return (
            f"declares config.out_dir {out_dir!r}, which does not resolve to "
            f"the run directory being closed ({run_dir})"
        )
    if mode in _GPU_MODES and environment.get("backend") != "cuda":
        return (
            f"declares environment.backend {environment.get('backend')!r}, not "
            "the 'cuda' backend a GPU result entry asserts (campaign plan §5.2)"
        )
    return None


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
    was written by a conforming invocation of this driver); a sidecar
    naming its own infrastructure filename (itself, or ``manifest.json``,
    matched case-insensitively so a differently-cased name can't alias the
    same on-disk file on Windows/macOS) as one of its artefacts, which would
    otherwise pass both the missing-file check (the file exists — it just
    isn't a result) and the unlisted-file check (it is excluded from
    ``present`` precisely because it is infrastructure) for the wrong reason
    (Copilot, CodeRabbit); or a declared artefact — or the sidecar itself —
    that is a symbolic link to a file outside ``run_dir``, since
    ``Path.is_file()`` and ``Path.read_text()`` both follow symlinks and
    would otherwise treat linked-to content as if it were written directly
    into ``run_dir`` by this run (CWE-59, CodeRabbit). E3 must call this
    before ``append_manifest`` (see ``benchmarks/results/EXP-001/README.md``
    and preregistration §5.3).

    The whole campaign plan §7.2 sidecar schema is validated, not only the
    ``artefacts`` key: ``exp_id`` must be exactly :data:`EXP_ID`, ``run_id``
    must equal ``run_dir.name``, ``session`` and ``operator`` must be
    non-empty strings, ``artefacts`` must be a non-empty object, and every
    entry must name a canonical ``<mode>_<label>.json`` result carrying
    exactly the hypothesis tags registered for that mode — plus, for a GPU
    entry, a registered ``timing_method``. Each declared result's own
    envelope is validated against campaign plan §7.2 and cross-checked
    against the sidecar (``config.out_dir`` resolves to this directory; a GPU
    entry's ``environment.backend`` is ``cuda``). Nothing is coerced: a
    malformed value is a closure failure, never repaired into a
    valid-looking one.

    Returns:
        The sidecar's artefact name → hypothesis-tag mapping, for the
        caller's log.

    Raises:
        IncompleteRunError: If the sidecar is missing, a symbolic link, or
            malformed; if it names an unsafe, reserved, mis-tagged,
            symlinked, or absent artefact path; if a declared result's
            envelope is missing or disagrees with the sidecar; or if the
            directory holds a result JSON the sidecar does not name.
    """
    resolved_run_dir = run_dir.resolve()
    sidecar = run_dir / "campaign-metadata.json"
    # Checked with is_symlink() (no-follow) *before* is_file()/read_text(),
    # both of which follow the link: a symlinked sidecar would otherwise let
    # a campaign-metadata document living outside run_dir decide what this
    # run published (CWE-59 — the same class already closed below for
    # declared result artefacts).
    if sidecar.is_symlink():
        raise IncompleteRunError(
            f"{sidecar} is a symbolic link, not a regular file written "
            "directly into the run directory; not a closable run"
        )
    if not sidecar.is_file():
        raise IncompleteRunError(
            f"{run_dir} has no campaign-metadata.json; not a closable run "
            "(campaign plan §7.2)"
        )
    try:
        payload = json.loads(sidecar.read_text(encoding="utf-8"))
    except (OSError, ValueError) as exc:
        raise IncompleteRunError(
            f"{sidecar} is malformed ({exc}); not a closable run"
        ) from exc
    if not isinstance(payload, dict):
        raise IncompleteRunError(f"{sidecar} is not a JSON object; not a closable run")
    absent = [field for field in _REQUIRED_SIDECAR_FIELDS if field not in payload]
    if absent:
        raise IncompleteRunError(
            f"{sidecar} is missing required field(s) {', '.join(absent)} "
            "(campaign plan §7.2); not a closable run"
        )
    if payload["exp_id"] != EXP_ID:
        raise IncompleteRunError(
            f"{sidecar} declares exp_id {payload['exp_id']!r}, not {EXP_ID!r}; "
            "not a closable run for this experiment"
        )
    if payload["run_id"] != run_dir.name:
        raise IncompleteRunError(
            f"{sidecar} declares run_id {payload['run_id']!r} but lives in "
            f"{run_dir.name!r} (campaign plan §7.1/§7.2); not a closable run"
        )
    for field in ("session", "operator"):
        value = payload[field]
        if not isinstance(value, str) or not value:
            raise IncompleteRunError(
                f"{sidecar} declares {field} {value!r}, not a non-empty "
                "string; not a closable run"
            )
    raw_artefacts = payload["artefacts"]
    if not isinstance(raw_artefacts, dict) or not raw_artefacts:
        raise IncompleteRunError(
            f"{sidecar} declares artefacts {raw_artefacts!r}, not a non-empty "
            "object; not a closable run"
        )
    # Run-directory infrastructure the campaign-metadata artefacts mapping
    # never legitimately names: the sidecar always exists (it is what this
    # function is reading), and manifest.json is written by append_manifest
    # *after* this check (it may already exist if this is called again on an
    # already-closed directory). A sidecar naming either as one of its own
    # artefacts would otherwise pass both checks below for the wrong reason —
    # not because a real result was written, but because the infrastructure
    # file it is impersonating as a result already happens to exist. Matched
    # case-insensitively: on a case-insensitive filesystem (default on
    # Windows and macOS, both in this project's CI matrix), a name that
    # differs from the sidecar's only in case still resolves to the same
    # on-disk file, so an exact-string comparison would miss it (CodeRabbit).
    infrastructure = frozenset({sidecar.name.casefold(), "manifest.json".casefold()})
    # manifest.json itself is excluded from the result inventory as
    # infrastructure (below), but that must not exempt it from the same
    # no-follow symlink discipline the sidecar and every declared artefact
    # already get: append_manifest resolves its destination before writing,
    # so a dangling or in-root symlink named manifest.json would make the
    # *next* closure step publish this run's manifest somewhere outside
    # run_dir (Copilot, CWE-59 class). Checked here, before this directory is
    # ever declared closable, not inside append_manifest itself (a governed
    # shared tool this driver does not modify).
    manifest_path = run_dir / "manifest.json"
    if manifest_path.is_symlink():
        raise IncompleteRunError(
            f"{manifest_path} is a symbolic link, not run-generated "
            "infrastructure — refusing to treat as a closable run"
        )
    artefacts: dict[str, list[str]] = {}
    modes: dict[str, str] = {}
    violations: list[str] = []
    for name, value in raw_artefacts.items():
        if not isinstance(name, str):
            violations.append(f"{name!r}: artefact key is not a string")
            continue
        name_violation = _declared_name_violation(name, infrastructure)
        if name_violation is not None:
            violations.append(f"{name!r} {name_violation}")
            continue
        mode = _result_name_mode(name)
        if mode is None:  # pragma: no cover - guaranteed by the check above
            violations.append(f"{name!r} is not a registered result name")
            continue
        tags, tag_violation = _declared_tags_violation(mode, value)
        if tag_violation is not None:
            violations.append(f"{name!r} {tag_violation}")
            continue
        artefacts[name] = tags
        modes[name] = mode
    if violations:
        raise IncompleteRunError(
            f"{sidecar} declares invalid artefact entr(ies): "
            + "; ".join(sorted(violations))
            + " — refusing to treat as a closable run"
        )
    collisions = sorted(
        name
        for name in artefacts
        if sum(1 for other in artefacts if other.casefold() == name.casefold()) > 1
    )
    if collisions:
        raise IncompleteRunError(
            f"{sidecar} declares artefact name(s) {', '.join(collisions)} that "
            "differ only in case and would alias the same file on a "
            "case-insensitive filesystem; not a closable run"
        )
    # A declared artefact that is a symbolic link is never trusted, even if
    # it resolves to a regular file: Path.is_file() below follows symlinks,
    # so a link to a file outside run_dir would otherwise pass the
    # missing-file check and be manifested as if it were written directly
    # into run_dir by this run (CWE-59, CodeRabbit). Checked with
    # is_symlink() (no-follow) before any is_file() call runs.
    symlinked = sorted(name for name in artefacts if (run_dir / name).is_symlink())
    if symlinked:
        raise IncompleteRunError(
            f"{sidecar} names artefact path(s) {', '.join(symlinked)} that "
            "are symbolic links, not regular files written directly by this "
            "run — refusing to treat as a closable run"
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
    envelope_violations = sorted(
        f"{name!r} {violation}"
        for name, violation in (
            (name, _envelope_violation(run_dir / name, resolved_run_dir, modes[name]))
            for name in artefacts
        )
        if violation is not None
    )
    if envelope_violations:
        raise IncompleteRunError(
            f"{run_dir} holds declared result(s) whose campaign plan §7.2 "
            "envelope is invalid or disagrees with campaign-metadata.json: "
            + "; ".join(envelope_violations)
            + " — refusing to treat as a closable run"
        )
    # `present` uses the case-insensitive suffix test so a `rogue.JSON` is
    # *seen* on every platform (see :func:`_is_json_name`), is compared
    # case-insensitively against the declared set so it cannot alias a
    # declared lowercase name on a case-insensitive filesystem, and is then
    # required to spell its own suffix canonically so the closure inventory
    # and `append_manifest`'s glob agree on both Windows and Linux.
    present = {
        path.name
        for path in run_dir.iterdir()
        if path.is_file()
        and _is_json_name(path.name)
        and path.name.casefold() not in infrastructure
    }
    declared_folded = {name.casefold() for name in artefacts}
    unlisted = sorted(
        name for name in present if name.casefold() not in declared_folded
    )
    if unlisted:
        raise IncompleteRunError(
            f"{run_dir} holds result file(s) {', '.join(unlisted)} that "
            "campaign-metadata.json does not name in its artefacts mapping "
            "— refusing to treat as a closable run"
        )
    non_canonical = sorted(name for name in present if not name.endswith(".json"))
    if non_canonical:
        raise IncompleteRunError(
            f"{run_dir} holds file(s) {', '.join(non_canonical)} whose '.json' "
            "suffix is not spelled in canonical lowercase; Path.glob('*.json') "
            "manifests them on Windows but not on Linux — refusing to treat as "
            "a closable run"
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


def _seed_uniform(stream: _prin_core.Seed, lo: float, hi: float) -> float:
    """Draw one f64 uniformly in ``[lo, hi)`` from the registered Seed stream."""
    return float(stream.next_f64_range(lo, hi))


def _seed_integer(stream: _prin_core.Seed, lo: int, hi: int) -> int:
    """Draw one integer uniformly in ``[lo, hi)`` from the registered Seed stream.

    ``Seed`` exposes ``next_f64``/``next_f64_range``/``next_u64``; the f64
    form is used rather than ``next_u64() % span`` because modulo of a 64-bit
    draw is biased for a span that does not divide ``2**64``. ``next_f64``
    returns a value in ``[0, 1)``, so ``lo + int(u * span)`` is already in
    range; the ``min`` only guards against a hypothetical rounding artefact
    at the top of the interval.
    """
    if hi <= lo:
        raise ValueError(f"empty integer range [{lo}, {hi})")
    span = hi - lo
    return min(lo + int(stream.next_f64() * span), hi - 1)


def _seed_choice(stream: _prin_core.Seed, options: tuple[str, ...]) -> str:
    """Draw one element of ``options`` uniformly from the registered Seed stream."""
    return options[_seed_integer(stream, 0, len(options))]


def _seed_vector(
    stream: _prin_core.Seed, lo: float, hi: float, size: int
) -> NDArray[np.float64]:
    """Assemble a length-``size`` f64 vector of ``[lo, hi)`` Seed draws."""
    return np.ascontiguousarray(
        [stream.next_f64_range(lo, hi) for _ in range(size)], dtype=np.float64
    )


def draw_fuzz_spec(stream: _prin_core.Seed) -> dict[str, Any]:
    """Deterministically draw a valid case spec from the registered ``Seed``.

    Mirrors the value ranges declared in ``prin.parity.strategies`` (the
    canonical definition of valid fuzz-case space): 3 models, coupling modes
    valid for the drawn model, 2 basic integrators, ``n_oscillators`` in
    ``[8, 64]``, ``n_steps`` in ``[5, 50]``, ``dt`` in ``[0.001, 0.05]``,
    ``coupling_strength`` in ``[0.1, 4.0]``, and model-specific parameter
    ranges.

    Every draw comes from ``prin._prin_core.Seed`` — the campaign's single
    registered randomness authority (Project Plan §4 rule 3; campaign plan
    §6.1, "No experiment may introduce a second RNG path"). Neither
    Hypothesis's internal engine nor a NumPy ``Generator`` is used: an
    earlier revision of this driver derived a NumPy PCG64 stream from
    ``(seed_counter, seed_key)``, which reproduced deterministically but was
    literally the second RNG path §6.1 forbids, and made the case stream
    depend on NumPy's bit-generator implementation rather than on the
    registered ``Seed`` (preregistration §5.12).
    """
    model = _seed_choice(stream, _FUZZ_MODELS)
    coupling = (
        Coupling.FULL.value
        if model == Model.STUART_LANDAU.value
        else _seed_choice(stream, _FUZZ_COUPLINGS)
    )
    integrator = _seed_choice(stream, _FUZZ_INTEGRATORS)
    n_oscillators = _seed_integer(stream, 8, 65)
    n_steps = _seed_integer(stream, 5, 51)
    dt = _seed_uniform(stream, 0.001, 0.05)
    parameters: dict[str, Any] = {
        "coupling_strength": _seed_uniform(stream, 0.1, 4.0),
    }
    if coupling == Coupling.SPARSE_KNN.value:
        parameters["sparse_k"] = _seed_integer(stream, 2, min(13, n_oscillators))
    if model == Model.KURAMOTO.value:
        parameters["decay_rate"] = _seed_uniform(stream, 0.0, 0.5)
        parameters["freq_adaptation_rate"] = _seed_uniform(stream, 0.0, 0.05)
    elif model == Model.HOPF.value:
        parameters["bifurcation_param"] = _seed_uniform(stream, -0.5, 2.0)
        parameters["freq_adaptation_rate"] = _seed_uniform(stream, 0.0, 0.05)
    elif model == Model.STUART_LANDAU.value:
        parameters["bifurcation_param"] = _seed_uniform(stream, -0.5, 2.0)
    return {
        "model": model,
        "coupling": coupling,
        "integrator": integrator,
        "n_oscillators": n_oscillators,
        "n_steps": n_steps,
        "dt": dt,
        "parameters": parameters,
    }


def draw_fuzz_initial(
    stream: _prin_core.Seed, n_oscillators: int
) -> tuple[NDArray[np.float64], NDArray[np.float64], NDArray[np.float64]]:
    """Draw an explicit ``(phase, amplitude, frequency)`` initial condition.

    Fed identically into both PRINet 3.0 and PRIN so the two implementations
    are compared from the same input rather than each drawing its own
    (implementation-specific) random state. Drawn from the same registered
    ``Seed`` stream as :func:`draw_fuzz_spec`.
    """
    return (
        _seed_vector(stream, 0.0, 2.0 * np.pi, n_oscillators),
        _seed_vector(stream, 0.5, 1.5, n_oscillators),
        _seed_vector(stream, -1.0, 1.0, n_oscillators),
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
    T_STAR``, ``beyond_horizon`` carries, per metric, the raw paired
    ``order_parameter``/``mean_phase_coherence`` values at every step past the
    horizon **plus that case's one predefined paired summary**
    (``mean_paired_difference``; :func:`_beyond_horizon_record`), else
    ``None``. E4 adjudicates H2b from those per-case summaries via
    :func:`adjudicate_h2b`; this function stores the data, it does not
    adjudicate (E3 executes, E4 analyzes).

    Args:
        spec: A dict from :func:`draw_fuzz_spec`, plus ``"case_index"`` (this
            draw's 0-based position in the stream, carried into the returned
            record's identity fields) and ``"seed_stream"`` (the
            ``prin._prin_core.Seed`` used to draw the shared initial
            condition via :func:`draw_fuzz_initial`; kept out of the returned
            record — the registered ``Seed`` authority, not a NumPy
            ``Generator``; preregistration §5.12 item 15).

    Returns:
        A JSON-serializable record: identifying fields, an ``"aborted"``
        flag, and either ``"abort_reason"`` or the H2a/H2b fields above.

    Raises:
        PrinetUnavailableError: If PRINet 3.0 is not importable.
    """
    stream: _prin_core.Seed = spec["seed_stream"]
    phase, amplitude, frequency = draw_fuzz_initial(stream, spec["n_oscillators"])
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
        "case_index": spec["case_index"],
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
            name: _beyond_horizon_record(
                getattr(reference, name)[horizon + 1 :],
                getattr(produced, name)[horizon + 1 :],
            )
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

    The stream is ``prin._prin_core.Seed(seed_counter, seed_key)`` — the
    campaign's single registered randomness authority, constructed directly
    from the registered pair (campaign plan §6.1/§6.2/§6.3) with no
    intermediate derivation — so a given pair always reproduces the same
    sequence of drawn cases, and the reproducibility contract is the
    ``Seed`` type's own rather than NumPy's bit-generator versioning.

    Each record's ``case_index`` is its 0-based position in that stream,
    which (with ``seed_counter``/``seed_key``, recorded in the artefact's
    ``config`` envelope) is what actually determines the case. The earlier
    per-case ``"seed"`` field did not: it was an integer drawn from the
    stream and then consumed by nothing, since both implementations run from
    the explicitly drawn initial condition rather than re-seeding themselves
    (preregistration §5.12).

    Raises:
        PrinetUnavailableError: If PRINet 3.0 is not importable.
    """
    stream = _prin_core.Seed(seed_counter, seed_key)
    records = []
    for case_index in range(n_cases):
        spec = draw_fuzz_spec(stream)
        spec["case_index"] = case_index
        spec["seed_stream"] = stream
        records.append(compare_fuzz_case(spec))
    return records


def _beyond_horizon_record(
    reference: NDArray[np.float64], produced: NDArray[np.float64]
) -> dict[str, Any]:
    """Pack one case's beyond-horizon values for one metric, plus its summary.

    The raw per-step arrays are kept for transparency and for E4's
    regeneration path, but the **registered unit of analysis is the per-case
    summary**, not the individual time points: values at successive steps of
    one trajectory are serially dependent, so pooling every post-horizon step
    across cases as if it were an independent observation would understate
    the variance of any interval computed from them. ``mean_paired_difference``
    is that predefined per-case paired summary (preregistration §5.12); cases
    are drawn independently from the registered ``Seed`` stream, so the
    per-case summaries are the independent sample H2b adjudicates.
    """
    n_points = int(reference.size)
    difference = produced - reference
    return {
        "reference": reference.tolist(),
        "produced": produced.tolist(),
        "n_points": n_points,
        "reference_mean": float(np.mean(reference)) if n_points else 0.0,
        "produced_mean": float(np.mean(produced)) if n_points else 0.0,
        "mean_paired_difference": float(np.mean(difference)) if n_points else 0.0,
    }


def h2b_case_summaries(
    cases: Sequence[dict[str, Any]], metric: str
) -> list[dict[str, float]]:
    """Collect one paired summary per contributing fuzz case, for ``metric``.

    A case contributes iff it is non-aborted and carries a ``beyond_horizon``
    block (i.e. ``n_steps > T_STAR``). Aborted cases are excluded entirely,
    never counted as a pass or a failure (preregistration §8).
    """
    summaries: list[dict[str, float]] = []
    for case in cases:
        if case.get("aborted", True):
            continue
        beyond = case.get("beyond_horizon")
        if not isinstance(beyond, dict) or metric not in beyond:
            continue
        record = beyond[metric]
        if not isinstance(record, dict) or not record.get("n_points"):
            continue
        summaries.append(
            {
                "reference_mean": float(record["reference_mean"]),
                "produced_mean": float(record["produced_mean"]),
                "mean_paired_difference": float(record["mean_paired_difference"]),
            }
        )
    return summaries


def adjudicate_h2b_metric(
    cases: Sequence[dict[str, Any]], metric: str
) -> dict[str, Any]:
    """Apply H2b's registered equivalence predicate to one metric.

    The predicate (preregistration §2/§4/§5.12/§8, stated identically in all
    four): the metric is ``CONFIRMED`` iff **both endpoints** of the 95 %
    bootstrap CI on the mean per-case paired difference lie strictly inside
    ``±`` that metric's registered equivalence margin
    (:data:`H2B_EQUIVALENCE_MARGIN`). A CI that merely *contains* zero does
    not establish equivalence — a wide interval can contain zero and, at the
    same time, differences large enough to reverse a scientific conclusion —
    which is why the earlier ``|Cohen's d| < 0.2`` **and** ``CI contains 0``
    combination was replaced (preregistration §5.12).

    Cohen's *d* and Welch's *t* are computed and reported for transparency
    but gate nothing: on a paired sample whose within-sample variance is tiny,
    a physically negligible difference can produce an arbitrarily large ``d``
    and an arbitrarily small *p*, so neither is a sound equivalence criterion.

    A sample with fewer than :data:`H2B_MIN_CASES` contributing cases (or
    none at all) is ``INCONCLUSIVE``, never ``REFUTED``.

    Every statistic comes from ``prin.y4q1_tools`` → the Rust
    ``y4q1_stats`` owner (campaign plan §9.2, the only permitted statistical
    code paths); this function performs only the paired-summary arithmetic
    already materialised by :func:`_beyond_horizon_record`.
    """
    margin = H2B_EQUIVALENCE_MARGIN[metric]
    summaries = h2b_case_summaries(cases, metric)
    differences = [s["mean_paired_difference"] for s in summaries]
    reference_means = [s["reference_mean"] for s in summaries]
    produced_means = [s["produced_mean"] for s in summaries]
    base: dict[str, Any] = {
        "metric": metric,
        "equivalence_margin": margin,
        "n_cases": len(summaries),
        "min_cases": H2B_MIN_CASES,
    }
    if len(summaries) < H2B_MIN_CASES:
        return {
            **base,
            "verdict": "INCONCLUSIVE",
            "reason": (
                f"{len(summaries)} contributing case(s) is below the registered "
                f"minimum of {H2B_MIN_CASES}; no valid beyond-horizon sample "
                "(preregistration §5.12)"
            ),
        }
    interval = bootstrap_ci(
        differences,
        n_bootstrap=H2B_BOOTSTRAP_RESAMPLES,
        alpha=H2B_ALPHA,
        seed=H2B_BOOTSTRAP_SEED,
    )
    ci_lower = float(interval["ci_lower"])
    ci_upper = float(interval["ci_upper"])
    equivalent = -margin < ci_lower and ci_upper < margin
    return {
        **base,
        "verdict": "CONFIRMED" if equivalent else "REFUTED",
        "mean_paired_difference": float(interval["mean"]),
        "ci_lower": ci_lower,
        "ci_upper": ci_upper,
        "within_margin": equivalent,
        "descriptive": {
            "cohens_d": float(cohens_d(produced_means, reference_means)),
            "welch": {
                key: float(value)
                for key, value in welch_t_test(produced_means, reference_means).items()
            },
        },
    }


def adjudicate_h2b(cases: Sequence[dict[str, Any]]) -> dict[str, Any]:
    """Adjudicate H2b over both registered metrics, independently.

    ``CONFIRMED`` iff both metrics are ``CONFIRMED``; ``REFUTED`` if either
    is ``REFUTED``; otherwise ``INCONCLUSIVE`` (preregistration §4/§8). The
    two metrics are never pooled into one combined sample: they are different
    physical quantities on different ranges, and opposite effects in the two
    would cancel if pooled.

    E3 (this driver's ``main``) does not call this — it stores the data; E4
    calls it on the published artefact's ``cases`` payload. It lives here, not
    in the analysis session's own code, so exactly one implementation of the
    registered predicate exists and is covered by this module's tests.
    """
    metrics = {
        metric: adjudicate_h2b_metric(cases, metric)
        for metric in _BEYOND_HORIZON_ARRAY_NAMES
    }
    verdicts = {result["verdict"] for result in metrics.values()}
    if "REFUTED" in verdicts:
        overall = "REFUTED"
    elif "INCONCLUSIVE" in verdicts:
        overall = "INCONCLUSIVE"
    else:
        overall = "CONFIRMED"
    return {"verdict": overall, "metrics": metrics}


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
            any of the three returned capsules does not confirm true CUDA
            execution (see note below).
        DriverMetadataError: If ``case_id`` does not name a
            ``kuramoto``/``sparse_knn`` case — an operator error that aborts
            the run, not an unexpected programming fault.

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
        raise DriverMetadataError(
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
    # Every returned capsule is checked, not just the first: the three
    # derivative outputs are separate DLPack capsules and nothing in the
    # binding's contract guarantees they share a device, so validating only
    # ``dphase`` would let a CPU-resident ``damplitude``/``dfrequency`` be
    # consumed and compared as if it were the CUDA result (preregistration
    # §4 item 6). The check runs on all three before any value is read.
    gpu_raw = {
        "dphase": from_dlpack(gpu_dphase_capsule),
        "damplitude": from_dlpack(gpu_damplitude_capsule),
        "dfrequency": from_dlpack(gpu_dfrequency_capsule),
    }
    non_cuda = sorted(
        f"{name}={tensor.device.type!r}"
        for name, tensor in gpu_raw.items()
        if tensor.device.type != "cuda"
    )
    if non_cuda:
        raise GpuBindingUnavailableError(
            "GpuSparseKuramoto.compute_derivatives returned non-CUDA-resident "
            f"result(s) ({', '.join(non_cuda)}) for case {case_id!r}, not the "
            "zero-copy kDLCUDA capsule the true CUDA device-resident path "
            "returns. This means the call did not actually dispatch through "
            "CUDA here — a --features wgpu-only build, or a CUDA client that "
            "failed to initialise and fell back to prin-sim's host-slice path "
            "— so H4 aborts rather than record a non-CUDA result as cuda "
            "(preregistration §5.1)"
        )
    gpu_dphase_raw = gpu_raw["dphase"]
    gpu_damplitude_raw = gpu_raw["damplitude"]
    gpu_dfrequency_raw = gpu_raw["dfrequency"]

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


class EnvironmentIncompleteError(DriverError):
    """Raised when required ``environment`` fields are absent for a run's mode.

    Campaign plan §10.1 item 3 / preregistration §4 item 3: "Environment
    capture incomplete (any ``environment`` field ``null`` that the
    configuration requires — e.g. ``gpu`` null on a GPU leg)" is a **run
    abort**, not an H1/H2/H3/H4 pass/fail result. ``capture_environment`` returns
    ``None`` for anything it cannot determine (no ``git``/``rustc`` on
    ``PATH``, no ``nvidia-smi``) rather than raising, so the requirement has
    to be enforced by the caller — here, before anything is published.
    """


def _validate_environment(mode: str, environment: dict[str, Any]) -> None:
    """Raise :class:`EnvironmentIncompleteError` if ``environment`` is incomplete.

    The required-field set is per mode: :data:`_REQUIRED_ENV_FIELDS` for every
    run, plus :data:`_GPU_REQUIRED_ENV_FIELDS` (``gpu``, ``gpu_vram_mb``) on a
    GPU leg. No value is ever substituted or invented — a missing field aborts
    the run so that a retry under a new ``RUN-`` ID can capture it for real.
    """
    required = list(_REQUIRED_ENV_FIELDS)
    if mode in _GPU_MODES:
        required += list(_GPU_REQUIRED_ENV_FIELDS)
    incomplete = [field for field in required if environment.get(field) in (None, "")]
    if incomplete:
        raise EnvironmentIncompleteError(
            f"environment capture is incomplete for --mode {mode}: "
            f"{', '.join(incomplete)} missing or null. Campaign plan §10.1 "
            "item 3 makes this a run abort, not a result — record the run as "
            "aborted (never delete its directory), provision the missing "
            "tooling, and retry under a new RUN- ID."
        )


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
    artefacts: dict[str, ArtefactEntry],
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


def _positive_int(raw: str) -> int:
    """argparse type for a strictly positive integer count.

    ``--n-fuzz-cases 0`` (or a negative value) would otherwise draw an empty
    batch and publish an H2 artefact whose every "all cases pass" predicate is
    vacuously true. A zero-case run is rejected at parse time rather than
    published (preregistration §5.12).
    """
    try:
        value = int(raw)
    except ValueError as exc:
        raise argparse.ArgumentTypeError(f"{raw!r} is not an integer") from exc
    if value <= 0:
        raise argparse.ArgumentTypeError(
            f"must be a positive integer, got {value}: a zero- or "
            "negative-case fuzz batch would publish an empty H2 artefact"
        )
    return value


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
        type=_positive_int,
        default=REGISTERED_FUZZ_BATCH_MIN,
        help=(
            "Number of hypothesis-fuzzed cases to draw (--mode fuzz). Must be "
            f"> 0. The registered confirmatory batch size is "
            f">= {REGISTERED_FUZZ_BATCH_MIN} (preregistration §7); a smaller "
            "batch is published with config.fuzz_batch_class = 'pilot' and "
            "can never be adjudicated as confirmatory H2 evidence."
        ),
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
    """Run the requested comparison and write its artefact + metadata sidecar.

    Every *expected* operational failure — a contract violation this driver
    or the corpus loader detects, an output path outside the declared roots,
    or an artefact that already exists — is reported as a one-line ``ABORT:``
    diagnostic on stderr and exit code 2, never as a Python traceback. The
    handler lists those exception types explicitly rather than catching
    ``Exception``: an unexpected programming error must still surface with
    its traceback rather than be disguised as an orderly campaign abort.
    """
    args = _parser().parse_args(argv)
    run_dir: Path = args.out.resolve()
    run_id = run_dir.name
    result_path = run_dir

    # Fuzz mode records which PRINet reference it actually compared against;
    # empty for the other modes, whose reference is the stored golden corpus.
    reference: dict[str, str] = {}
    try:
        _validate_metadata(EXP_ID, run_id, args.session, args.operator)
        _validate_label(args.label)
        _validate_case_ids(args.case_ids)
        _reserve_run_dir(run_dir)
        batch: dict[str, Any] = {}
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
            # The registered confirmatory batch size is >= 1,000
            # (preregistration §7). A smaller batch is still a legitimate
            # pilot/smoke invocation, but it is labelled as one in the
            # published envelope so neither E4 nor run closure can read it as
            # the registered confirmatory H2 evidence (preregistration §5.12).
            batch = {
                "fuzz_batch_class": (
                    "confirmatory"
                    if args.n_fuzz_cases >= REGISTERED_FUZZ_BATCH_MIN
                    else "pilot"
                ),
                "fuzz_batch_confirmatory_minimum": REGISTERED_FUZZ_BATCH_MIN,
                "n_fuzz_cases_requested": args.n_fuzz_cases,
            }

        backend, dtype = ("cuda", "f32") if args.mode in _GPU_MODES else ("cpu", "f64")
        # A GPU leg records backend "cuda", which compare_kernel_path_case
        # proves per case by checking the raw DLPack capsules' device. With
        # no case there is no such proof, so an empty GPU batch must not
        # publish an unbacked "cuda" claim.
        if args.mode in _GPU_MODES and not cases:
            raise DriverMetadataError(
                f"--mode {args.mode} selected no cases, so nothing proved this "
                "run dispatched through CUDA; refusing to publish a "
                'backend "cuda" artefact with an empty payload'
            )
        environment = capture_environment(
            backend=backend, dtype=dtype, seed=args.seed_counter
        )
        _validate_environment(args.mode, environment)
        config = {
            "iterations": len(cases),
            "warmup": 0,
            "seed_counter": args.seed_counter,
            "seed_key": args.seed_key,
            "out_dir": str(run_dir),
            **batch,
            **reference,
        }
        result_name = f"{args.mode}_{args.label}.json"
        result_path = run_dir / result_name

        # Fast fail on a *pre-existing* result (a stale artefact from an
        # earlier invocation targeting this same run directory/label, e.g. a
        # retry). This is only a cheap check, not a reservation — a concurrent
        # writer can still create the path between here and `write_result`
        # below, which is what the rollback further down actually closes.
        if result_path.exists():
            raise ArtefactExistsError(
                f"{result_path} already exists; raw benchmark artefacts are "
                "append-only (Experimentation Standards §4) — write to a new "
                "run directory instead"
            )

        artefact_entry: ArtefactEntry = _MODE_HYPOTHESIS[args.mode]
        if args.mode in _GPU_MODES:
            artefact_entry = {
                "hypotheses": _MODE_HYPOTHESIS[args.mode],
                "timing_method": KERNEL_PATH_TIMING_METHOD,
            }

        # The sidecar/result pair is published transactionally with respect
        # to the failures this process handles: either both land or neither
        # does. That guarantee does *not* extend to process termination
        # (SIGKILL, power loss, TerminateProcess) between the two writes,
        # which leaves a sidecar-only directory; `check_run_complete` is what
        # refuses to manifest one (see its docstring and
        # benchmarks/results/EXP-001/README.md).
        #
        # The sidecar goes first because campaign plan §7.2 only accepts a
        # result that carries its provenance — writing the result first would
        # let a sidecar failure strand unprovenanced evidence. The mirror risk
        # (a sidecar naming a result this invocation never published, e.g.
        # because a concurrent writer won the result path first) is closed by
        # rolling the sidecar back on any failure below. That rollback can only
        # ever remove *this* invocation's own sidecar: `write_campaign_metadata`
        # publishes via exclusive-create and raises if one already exists, so
        # reaching this point proves we created it.
        metadata_path = write_campaign_metadata(
            run_dir,
            exp_id=EXP_ID,
            run_id=run_id,
            session=args.session,
            operator=args.operator,
            artefacts={result_name: artefact_entry},
        )
        try:
            result_path = write_result(
                result_path,
                environment=environment,
                config=config,
                payload={"cases": cases},
            )
        except BaseException:
            metadata_path.unlink(missing_ok=True)
            raise
    except (DriverError, CorpusValidationError, OutputPathError) as exc:
        print(f"ABORT: {exc}", file=sys.stderr)
        return 2
    print(f"Wrote {result_path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
