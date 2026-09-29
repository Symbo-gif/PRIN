"""Measurement driver for the EXP-001-r1 pre-registration.

This is a new experiment identity, using the corrected Euler/RK4 default.
The predecessor's driver, corpus and run artefacts retain their meaning.
DV-007 explanations require positive float64-reference evidence at unchanged
tolerances. The fixed ill-conditioned population is characterized, never
reported as pointwise parity. This module collects evidence at E3; its
statistical adjudicator is called only at E4.

E1 tests use synthetic arrays and mocked runners. Do not execute the registered
workloads before the maintainer's E2 approval and resolution of the execution
gates in the pre-registration.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import os
import sys
from collections.abc import Sequence
from contextlib import AbstractContextManager
from pathlib import Path
from typing import Any

import numpy as np
from numpy.typing import NDArray
from prin import _prin_core
from prin.dynamics import EulerIntegrator, RK4Integrator
from prin.parity.harness import ComparisonResult, compare_arrays, compare_case
from prin.parity.loader import CorpusLoader
from prin.parity.schema import (
    CaseArrays,
    CaseSpec,
    CorpusValidationError,
    validate_case_arrays,
)
from prin.y4q1_tools import bootstrap_ci, cohens_d, welch_t_test

from benchmarks._common.environment import capture_environment
from benchmarks._common.result import OutputPathError, write_result
from benchmarks.campaign import exp001_driver as legacy

EXP_ID = "EXP-001-r1"
SESSION_ID = "EXP-001-r1-E3"
PROTOCOL_REVISION = 1
N_FUZZ_CASES = 1000
CORPUS_SHA256 = "fcbaad1cb16edb3445c9b9ce122131bf4361d9c4ce17c4bc67edd74c62edd2cf"
STREAM_SHA256 = "9804fc09e4a510ef0c34dfa5b58c6639a62baf15cf4f38f481ed1c8b854cff76"
REFERENCE_SOURCE_SHA256 = (
    "89d19734c714e31f355d018d7b5889e48f4787841dc15c43df6abdad9d77d4b9"
)
INSTRUMENT_SHA256 = "c6972d5f1ca1380f0d80249034479ed2974a34d20c27b295ddf90f441c1631c2"

# Approved by the maintainer at E2 (2026-09-28 UTC; campaign plan §14.2
# amendment #7, DOCS/experiments/campaign-plan.md §11.8): the shared
# `benchmarks/results/EXP-001/` root (original + new r1 runs) is capped at
# 16 MiB; new r1 runs additionally have their own 8 MiB sub-allocation,
# checked only against `RUN-*-r1-*/` directories; the r1 fuzz leg gets the
# same 6 MiB per-run exception the predecessor's amendment 6 granted its own
# fuzz leg; every other r1 run keeps the generic 2 MiB per-run cap.
RAW_ROOT_CAP_BYTES = 16 * 1024 * 1024
R1_ROOT_CAP_BYTES = 8 * 1024 * 1024
RUN_CAP_BYTES = 2 * 1024 * 1024
FUZZ_RUN_CAP_BYTES = 6 * 1024 * 1024
CAMPAIGN_CAP_BYTES = 64 * 1024 * 1024
MANIFEST_RESERVE_BYTES = 64 * 1024

# Fixed before r1 execution, from the correction's committed reference-only
# sensitivity evidence. Never expand this set in response to a PRIN residual.
ILL_CONDITIONED = frozenset(
    {
        50,
        76,
        90,
        270,
        310,
        330,
        334,
        362,
        385,
        398,
        399,
        415,
        456,
        522,
        621,
        623,
        653,
        691,
        734,
        841,
        867,
        878,
    }
)

# Lexicographically first case ID in each (model, coupling, integrator) cell.
# Selection uses manifest metadata only, not a trajectory or a prior verdict.
REPEATABILITY_CASES = (
    "hopf_full_euler_n12_s20_dt0_005_K0_5_seed1800009",
    "hopf_full_rk4_n12_s20_dt0_005_K0_5_seed1900009",
    "hopf_mean_field_euler_n12_s20_dt0_005_K0_5_seed1600009",
    "hopf_mean_field_rk4_n12_s20_dt0_005_K0_5_seed1700009",
    "hopf_sparse_knn_euler_n12_s20_dt0_005_K0_5_seed2000009",
    "hopf_sparse_knn_rk4_n12_s20_dt0_005_K0_5_seed2100009",
    "kuramoto_full_euler_n12_s20_dt0_005_K0_5_seed1200009",
    "kuramoto_full_rk4_n12_s20_dt0_005_K0_5_seed1300009",
    "kuramoto_mean_field_euler_n12_s20_dt0_005_K0_5_seed1000009",
    "kuramoto_mean_field_rk4_n12_s20_dt0_005_K0_5_seed1100009",
    "kuramoto_sparse_knn_euler_n12_s20_dt0_005_K0_5_seed1400009",
    "kuramoto_sparse_knn_rk4_n12_s20_dt0_005_K0_5_seed1500009",
    "stuart_landau_full_euler_n12_s20_dt0_005_K0_5_seed2200009",
    "stuart_landau_full_rk4_n12_s20_dt0_005_K0_5_seed2300009",
)
LABELS: dict[str, tuple[str, ...]] = {
    "corpus": ("r1-corpus-cpu",),
    "fuzz": ("r1-fuzz-cpu",),
    "repeatability": ("r1-repeatability-cpu", "r1-seedrep0-cpu"),
    "kernel-path": ("r1-kernel-path-cuda", "r1-kernel-path-wgpu"),
}
DENOMINATORS = {"corpus": 504, "fuzz": 1000, "repeatability": 14, "kernel-path": 72}

# Seed(0, 1).next_u64(), explicitly derived from the campaign authority.
# The existing Rust bootstrap implementation domain-separates internally with
# Seed(seed, 0x626f6f74); no NumPy/Python random generator is introduced.
BOOTSTRAP_SEED = 12455822396014146421
_Initial = tuple[NDArray[np.float64], NDArray[np.float64], NDArray[np.float64]]
_StreamCase = tuple[
    dict[str, Any], NDArray[np.float64], NDArray[np.float64], NDArray[np.float64]
]


def _float64_context() -> AbstractContextManager[None]:
    """Return the process-local, restoring float64 reference instrument."""
    from parity.prinet_f64 import f64_corrected_reference

    return f64_corrected_reference()


def _dv007(spec: dict[str, Any]) -> bool:
    """Identify the three adjudicated complex64 derivative paths."""
    # Identical path predicate to parity.prinet_f64.on_dv007_path, without an
    # eager PRINet import in a synthetic test or a CPU-only closure operation.
    return spec["model"] == "stuart_landau" or (
        spec["model"] in ("kuramoto", "hopf") and spec["coupling"] == "mean_field"
    )


def _spec_kwargs(spec: CaseSpec) -> dict[str, Any]:
    """Extract the identical model/integration inputs for both runners."""
    return {
        "model": spec.model,
        "coupling": spec.coupling,
        "integrator": spec.integrator,
        "n_oscillators": spec.n_oscillators,
        "n_steps": spec.n_steps,
        "dt": spec.dt,
        "parameters": dict(spec.parameters),
    }


def _reference(spec: dict[str, Any], initial: _Initial) -> CaseArrays:
    """Run the registered native or context-instrumented reference."""
    return legacy.run_prinet_trajectory(
        **spec,
        phase_init=initial[0],
        amplitude_init=initial[1],
        frequency_init=initial[2],
    )


def _array_violation(
    label: str, spec: dict[str, Any], arrays: CaseArrays
) -> str | None:
    """Return the registered shape, dtype, finiteness or envelope violation."""
    try:
        validate_case_arrays(CaseSpec(case_id="validation", seed=0, **spec), arrays)
    except CorpusValidationError as exc:
        return f"{label}: {exc}"
    violation = legacy._case_arrays_hazard_violation(label, arrays)
    if violation is not None:
        return violation
    for name in ("amplitude_init", "amplitude_final", "amplitude_traj"):
        if np.any(getattr(arrays, name) < 0.0):
            return f"{label}: negative amplitude under the NonNegative guard ({name})"
    for name in ("phase_init", "phase_final"):
        phase = getattr(arrays, name)
        if np.any(phase < 0.0) or np.any(phase >= 2.0 * np.pi):
            return f"{label}: {name} outside the wrapped [0, 2*pi) range"
    return None


def _comparisons(
    reference: CaseArrays,
    produced: CaseArrays,
    model: str,
    horizon: int | None,
) -> list[ComparisonResult]:
    """Compare all corpus arrays or the registered within-horizon subset."""
    if horizon is None:
        return compare_case(reference, produced, model)
    return [
        compare_arrays(getattr(reference, name), getattr(produced, name), name, model)
        for name in ("phase_init", "amplitude_init", "frequency_init")
    ] + [
        compare_arrays(
            getattr(reference, name)[: horizon + 1],
            getattr(produced, name)[: horizon + 1],
            name,
            model,
        )
        for name in legacy._TRAJ_ARRAY_NAMES
    ]


def _pointwise_record(
    identity: dict[str, Any],
    spec: dict[str, Any],
    initial: _Initial,
    native: CaseArrays,
    produced: CaseArrays,
    horizon: int | None,
    *,
    ill_conditioned: bool = False,
) -> dict[str, Any]:
    """Retain native residuals and any positive exception evidence."""
    for label, arrays in (("native-reference", native), ("produced", produced)):
        violation = _array_violation(label, spec, arrays)
        if violation is not None:
            return {**identity, "aborted": True, "abort_reason": violation}
    comparisons = _comparisons(native, produced, spec["model"], horizon)
    native_ok = all(c.within_tolerance for c in comparisons)
    record: dict[str, Any] = {
        **identity,
        "aborted": False,
        "pointwise_eligible": True,
        "native_within_tolerance": native_ok,
        "comparisons": [c.to_dict() for c in comparisons],
        "f64_comparisons": None,
        "accepted": native_ok,
        "classification": "native-parity" if native_ok else "unexplained-breach",
    }
    if not ill_conditioned and (native_ok or not _dv007(spec)):
        return record
    with _float64_context():
        corrected = _reference(spec, initial)
        nudged = None
        if ill_conditioned:
            nudged = _reference(
                spec, (np.nextafter(initial[0], np.inf), initial[1], initial[2])
            )
    for label, candidate in (
        ("float64-reference", corrected),
        ("one-ulp-reference", nudged),
    ):
        if candidate is not None:
            violation = _array_violation(label, spec, candidate)
            if violation is not None:
                return {**identity, "aborted": True, "abort_reason": violation}
    residual = _comparisons(corrected, produced, spec["model"], horizon)
    record["f64_comparisons"] = [c.to_dict() for c in residual]
    if ill_conditioned:
        if nudged is None:
            raise legacy.DriverError("missing registered one-ulp reference")
        sensitivity = _comparisons(corrected, nudged, spec["model"], horizon)
        sensitive = any(not c.within_tolerance for c in sensitivity)
        if not sensitive:
            return {
                **identity,
                "aborted": True,
                "abort_reason": "registered reference sensitivity was not reproduced",
                "comparisons": record["comparisons"],
                "f64_comparisons": record["f64_comparisons"],
                "sensitivity_comparisons": [c.to_dict() for c in sensitivity],
            }
        record.update(
            pointwise_eligible=False,
            accepted=None,
            classification="ill-conditioned-characterization",
            sensitivity_reproduced=True,
            sensitivity_comparisons=[c.to_dict() for c in sensitivity],
        )
    else:
        corrected_ok = all(c.within_tolerance for c in residual)
        record.update(
            accepted=corrected_ok,
            classification="explained-dv007" if corrected_ok else "unexplained-breach",
        )
    return record


def compare_corpus_case(loader: CorpusLoader, case_id: str) -> dict[str, Any]:
    """Collect native and, when needed, corrected-reference evidence for H1.

    Args:
        loader: Validated golden-corpus loader.
        case_id: Registered corpus case identifier.

    Returns:
        Native comparison and, when applicable, corrected-reference evidence.

    Raises:
        legacy.DriverError: If the required reference cannot execute.
    """
    loaded = loader.load(case_id)
    spec = _spec_kwargs(loaded.spec)
    initial = (
        loaded.arrays.phase_init,
        loaded.arrays.amplitude_init,
        loaded.arrays.frequency_init,
    )
    return _pointwise_record(
        {**legacy._case_identity(loaded.spec), "parameters": spec["parameters"]},
        spec,
        initial,
        loaded.arrays,
        legacy.run_prin_case(loaded.spec, loaded.arrays),
        None,
    )


def compare_fuzz_case(
    spec: dict[str, Any], initial: _Initial, case_index: int
) -> dict[str, Any]:
    """Collect H2 evidence from identical explicit inputs, retaining every case.

    Args:
        spec: Model and integrator inputs from the pinned sampler.
        initial: Shared phase, amplitude and frequency arrays, each shape (N,).
        case_index: Zero-based index in the registered stream.

    Returns:
        One case record, including abort state and paired post-horizon metrics.

    Raises:
        legacy.DriverError: If a required numerical runner cannot execute.
    """
    native = _reference(spec, initial)
    produced = legacy.run_prin_trajectory(
        **spec,
        phase_init=initial[0],
        amplitude_init=initial[1],
        frequency_init=initial[2],
    )
    horizon = min(legacy.T_STAR, spec["n_steps"])
    record = _pointwise_record(
        {
            **spec,
            "case_index": case_index,
            "input_sha256": legacy.h2a_stream_digest([(spec, *initial)]),
            "horizon": horizon,
        },
        spec,
        initial,
        native,
        produced,
        horizon,
        ill_conditioned=case_index in ILL_CONDITIONED,
    )
    if not record["aborted"]:
        record["beyond_horizon"] = (
            {
                name: legacy._beyond_horizon_record(
                    getattr(native, name)[legacy.T_STAR + 1 :],
                    getattr(produced, name)[legacy.T_STAR + 1 :],
                )
                for name in legacy._BEYOND_HORIZON_ARRAY_NAMES
            }
            if spec["n_steps"] > legacy.T_STAR
            else None
        )
    return record


def _draw_stream() -> list[_StreamCase]:
    """Draw the complete registered input stream without integrating it."""
    stream = _prin_core.Seed(0, 1)
    cases = []
    for _ in range(N_FUZZ_CASES):
        spec = legacy.draw_fuzz_spec(stream)
        cases.append((spec, *legacy.draw_fuzz_initial(stream, spec["n_oscillators"])))
    return cases


def run_fuzz_batch() -> list[dict[str, Any]]:
    """Replay the pinned 1,000 inputs; reject drift before any trajectory runs.

    Returns:
        Exactly 1,000 case records in registered order.

    Raises:
        legacy.DriverMetadataError: If the input stream fingerprint changes.
    """
    stream = _draw_stream()
    if len(stream) != N_FUZZ_CASES or legacy.h2a_stream_digest(stream) != STREAM_SHA256:
        raise legacy.DriverMetadataError("registered fuzz input fingerprint mismatch")
    return [
        compare_fuzz_case(spec, (phase, amplitude, frequency), index)
        for index, (spec, phase, amplitude, frequency) in enumerate(stream)
    ]


def _array_hashes(arrays: CaseArrays) -> dict[str, str]:
    """Hash each array's dtype, shape and contiguous bytes for H3 evidence."""
    hashes = {}
    for name in CaseArrays._ARRAY_NAMES:
        array = getattr(arrays, name)
        digest = hashlib.sha256(
            json.dumps({"dtype": array.dtype.str, "shape": array.shape}).encode("utf-8")
        )
        digest.update(np.ascontiguousarray(array).tobytes())
        hashes[name] = digest.hexdigest()
    return hashes


def check_repeatability(loader: CorpusLoader, case_id: str) -> dict[str, Any]:
    """Compare actual bytes twice and retain array digests for separate-run checks.

    Args:
        loader: Validated golden-corpus loader.
        case_id: One of the 14 registered representative identifiers.

    Returns:
        Byte-comparison status and the two sets of array digests.
    """
    loaded = loader.load(case_id)
    outputs = [legacy.run_prin_case(loaded.spec, loaded.arrays) for _ in range(2)]
    for label, arrays in zip(("first", "second"), outputs, strict=True):
        violation = _array_violation(label, _spec_kwargs(loaded.spec), arrays)
        if violation is not None:
            return {"case_id": case_id, "aborted": True, "abort_reason": violation}
    mismatched = [
        name
        for name in CaseArrays._ARRAY_NAMES
        if not legacy._bit_identical(
            getattr(outputs[0], name), getattr(outputs[1], name)
        )
    ]
    return {
        "case_id": case_id,
        "aborted": False,
        "bit_identical": not mismatched,
        "mismatched_arrays": mismatched,
        "first_array_sha256": _array_hashes(outputs[0]),
        "second_array_sha256": _array_hashes(outputs[1]),
    }


def adjudicate_h2b_metric(
    cases: Sequence[dict[str, Any]], metric: str
) -> dict[str, Any]:
    """Apply the r1 three-way interval rule; E3 never invokes this E4 function.

    Args:
        cases: Validated E3 case records; used only during E4.
        metric: One of the two registered coherence metric names.

    Returns:
        The per-metric verdict, interval and descriptive statistics.

    Raises:
        legacy.DriverError: If the statistical interval is invalid.
    """
    margin = legacy.H2B_EQUIVALENCE_MARGIN[metric]
    summaries = legacy.h2b_case_summaries(cases, metric)
    result: dict[str, Any] = {
        "metric": metric,
        "equivalence_margin": margin,
        "n_cases": len(summaries),
        "min_cases": legacy.H2B_MIN_CASES,
    }
    if (
        any(case.get("aborted", True) for case in cases)
        or len(summaries) < legacy.H2B_MIN_CASES
    ):
        return {
            **result,
            "verdict": "INCONCLUSIVE",
            "reason": "aborted case or fewer than 30 contributing cases",
        }
    interval = bootstrap_ci(
        [s["mean_paired_difference"] for s in summaries],
        n_bootstrap=legacy.H2B_BOOTSTRAP_RESAMPLES,
        alpha=legacy.H2B_ALPHA,
        seed=BOOTSTRAP_SEED,
    )
    lo, hi = float(interval["ci_lower"]), float(interval["ci_upper"])
    if (
        not all(
            math.isfinite(float(interval[key]))
            for key in ("mean", "ci_lower", "ci_upper")
        )
        or lo > hi
    ):
        raise legacy.DriverError("invalid bootstrap interval")
    if -margin < lo and hi < margin:
        verdict = "CONFIRMED"
    elif lo > margin or hi < -margin:
        verdict = "REFUTED"
    else:
        verdict = "INCONCLUSIVE"
    reference = [s["reference_mean"] for s in summaries]
    produced = [s["produced_mean"] for s in summaries]
    # A degenerate descriptive statistic is not evidence of either equivalence
    # or non-equivalence. Strict JSON stores null instead of NaN or Infinity.
    descriptive = {
        "cohens_d": float(cohens_d(produced, reference)),
        **{
            f"welch_{k}": float(v) for k, v in welch_t_test(produced, reference).items()
        },
    }
    return {
        **result,
        "verdict": verdict,
        "mean_paired_difference": float(interval["mean"]),
        "ci_lower": lo,
        "ci_upper": hi,
        "bootstrap_seed": BOOTSTRAP_SEED,
        "descriptive": {
            k: v if math.isfinite(v) else None for k, v in descriptive.items()
        },
        "undefined_descriptive": [
            k for k, v in descriptive.items() if not math.isfinite(v)
        ],
    }


def adjudicate_h2b(cases: Sequence[dict[str, Any]]) -> dict[str, Any]:
    """Require both independently evaluated metric intervals to establish
    equivalence.

    Args:
        cases: Validated E3 case records; used only during E4.

    Returns:
        Joint verdict and both separate metric results.
    """
    metrics = {
        metric: adjudicate_h2b_metric(cases, metric)
        for metric in legacy._BEYOND_HORIZON_ARRAY_NAMES
    }
    verdicts = {m["verdict"] for m in metrics.values()}
    verdict = (
        "REFUTED"
        if "REFUTED" in verdicts
        else "INCONCLUSIVE"
        if "INCONCLUSIVE" in verdicts
        else "CONFIRMED"
    )
    return {"verdict": verdict, "metrics": metrics}


def preflight(mode: str, corpus_dir: Path) -> dict[str, Any]:
    """Validate the registered corpus, guard policy and reference instrument.

    Args:
        mode: One of the four registered modes (kernel-path has two GPU labels).
        corpus_dir: Directory containing the registered manifest and cases.

    Returns:
        Input and extension provenance to include in the result envelope.

    Raises:
        legacy.DriverMetadataError: If a registered fingerprint, guard or
            instrument check fails.
    """
    manifest = corpus_dir / "manifest.json"
    if hashlib.sha256(manifest.read_bytes()).hexdigest() != CORPUS_SHA256:
        raise legacy.DriverMetadataError(
            "registered corpus manifest fingerprint mismatch"
        )
    loader = CorpusLoader(corpus_dir)
    if len(loader) != 504:
        raise legacy.DriverMetadataError("registered corpus must contain 504 cases")
    if any(
        getattr(cls(), "guard", None) != "non_negative"
        for cls in (EulerIntegrator, RK4Integrator)
    ):
        raise legacy.DriverMetadataError(
            "extension lacks corrected NonNegative defaults"
        )
    metadata: dict[str, Any] = {
        "guard_policy": "non_negative",
        "corpus_manifest_sha256": CORPUS_SHA256,
        "prin_extension": str(Path(_prin_core.__file__).resolve()),
        "prin_extension_sha256": hashlib.sha256(
            Path(_prin_core.__file__).read_bytes()
        ).hexdigest(),
    }
    if mode in ("corpus", "fuzz"):
        metadata.update(legacy.prinet_reference_provenance())
        from prinet.core.propagation import oscillator_models

        from parity import prinet_f64

        source_hash = hashlib.sha256(
            Path(oscillator_models.__file__).read_bytes()
        ).hexdigest()
        instrument_hash = hashlib.sha256(
            Path(prinet_f64.__file__).read_bytes()
        ).hexdigest()
        if (
            source_hash != REFERENCE_SOURCE_SHA256
            or instrument_hash != INSTRUMENT_SHA256
        ):
            raise legacy.DriverMetadataError(
                "registered reference/instrument fingerprint mismatch"
            )
        try:
            prinet_f64.assert_replacements_match_reference()
        except AssertionError as exc:
            raise legacy.DriverMetadataError(
                f"reference instrument AST mismatch: {exc}"
            ) from exc
        metadata.update(
            reference_source_sha256=source_hash, instrument_sha256=instrument_hash
        )
    if mode == "fuzz":
        metadata["stream_sha256"] = STREAM_SHA256
    return metadata


def collect_cases(
    mode: str, corpus_dir: Path, *, backend: str = "cuda"
) -> list[dict[str, Any]]:
    """Collect precisely the registered case population for one implemented leg.

    Args:
        mode: One of the four registered modes (kernel-path has two GPU labels).
        corpus_dir: Registered corpus directory.
        backend: GPU backend name for the ``kernel-path`` leg
            (``"cuda"`` or ``"wgpu"``).

    Returns:
        The selected population, including any per-case abort records.

    Raises:
        legacy.DriverMetadataError: If the requested mode or backend is
            unregistered.
    """
    if mode not in LABELS:
        raise legacy.DriverMetadataError(f"unregistered mode: {mode}")
    if backend not in ("cuda", "wgpu"):
        raise legacy.DriverMetadataError(f"unregistered GPU backend: {backend}")
    if mode == "fuzz":
        return run_fuzz_batch()
    loader = CorpusLoader(corpus_dir)
    if mode == "corpus":
        return [
            compare_corpus_case(loader, row.case_id) for row in loader.manifest.cases
        ]
    if mode == "repeatability":
        return [check_repeatability(loader, case_id) for case_id in REPEATABILITY_CASES]
    case_ids = [
        row.case_id
        for row in loader.manifest.cases
        if row.model == "kuramoto" and row.coupling == "sparse_knn"
    ]
    if backend == "wgpu":
        return legacy.compare_kernel_path_subset(loader, case_ids, backend="wgpu")
    return legacy.compare_kernel_path_subset(loader, case_ids)


def _storage_check(
    run_dir: Path, result: dict[str, Any], sidecar: dict[str, Any], mode: str = ""
) -> None:
    """Reject publication that would exceed the currently approved byte caps.

    Args:
        run_dir: The new run's directory (not yet created when checked).
        result: The result payload pending publication.
        sidecar: The campaign-metadata sidecar pending publication.
        mode: The registered leg name (``"fuzz"`` gets the approved 6 MiB
            per-run exception; every other leg keeps the generic 2 MiB cap).
    """

    def encoded_size(payload: dict[str, Any]) -> int:
        """Estimate the exact platform-newline JSON bytes before publication."""
        try:
            text = json.dumps(
                payload, indent=2, sort_keys=True, ensure_ascii=False, allow_nan=False
            )
        except (TypeError, ValueError) as exc:
            raise legacy.DriverMetadataError("result is not finite JSON") from exc
        return len(text.replace("\n", os.linesep).encode("utf-8"))

    new_bytes = encoded_size(result) + encoded_size(sidecar) + MANIFEST_RESERVE_BYTES
    run_cap = FUZZ_RUN_CAP_BYTES if mode == "fuzz" else RUN_CAP_BYTES
    root_bytes = sum(
        p.stat().st_size for p in run_dir.parent.glob("RUN-*/*") if p.is_file()
    )
    r1_bytes = sum(
        p.stat().st_size for p in run_dir.parent.glob("RUN-*-r1-*/*") if p.is_file()
    )
    campaign_bytes = sum(
        p.stat().st_size
        for p in run_dir.parent.parent.glob("EXP-*/RUN-*/*")
        if p.is_file()
    )
    if (
        new_bytes > run_cap
        or root_bytes + new_bytes > RAW_ROOT_CAP_BYTES
        or ("-r1-" in run_dir.name and r1_bytes + new_bytes > R1_ROOT_CAP_BYTES)
        or campaign_bytes + new_bytes > CAMPAIGN_CAP_BYTES
    ):
        raise legacy.DriverMetadataError(
            "registered storage cap would be exceeded (campaign plan §14.2 "
            "amendment #7 limits)"
        )


def close_run(run_dir: Path, *, expected_backend: str = "cuda") -> None:
    """Validate the r1 identity, then manifest and verify this new run only.

    Args:
        run_dir: Fresh run directory containing the result and metadata sidecar.
        expected_backend: GPU backend name the result label and envelope must
            carry (``"cuda"`` or ``"wgpu"``).

    Raises:
        legacy.IncompleteRunError: If the declared experiment identity or
            closure contract is invalid.
    """
    from tools.reproduce import append_manifest, verify_manifest

    legacy.check_run_complete(
        run_dir, expected_exp_id=EXP_ID, expected_backend=expected_backend
    )
    append_manifest(results_dir=run_dir, manifest_path=run_dir / "manifest.json")
    verify_manifest(results_dir=run_dir, manifest_path=run_dir / "manifest.json")


def _parser() -> argparse.ArgumentParser:
    """Build the CLI for four modes and six registered r1 run directories."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--mode", choices=tuple(LABELS), required=True)
    parser.add_argument("--corpus-dir", type=Path, default=Path("parity/corpus"))
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--label", required=True)
    parser.add_argument("--session", required=True)
    parser.add_argument("--operator", required=True)
    return parser


def main(argv: list[str] | None = None) -> int:
    """Collect one registered leg under a fresh r1 identity; do not adjudicate it.

    Args:
        argv: Explicit CLI arguments, or None to read process arguments.

    Returns:
        Zero after publication and manifest verification, or two on an abort.
    """
    args = _parser().parse_args(argv)
    run_dir = args.out.resolve()
    try:
        if args.session != SESSION_ID or args.label not in LABELS[args.mode]:
            raise legacy.DriverMetadataError(
                "session/label is not registered for EXP-001-r1"
            )
        if not args.operator.strip():
            raise legacy.DriverMetadataError("operator must be non-empty")
        legacy._validate_label(args.label)
        gpu_backend = (
            ("wgpu" if args.label == "r1-kernel-path-wgpu" else "cuda")
            if args.mode == "kernel-path"
            else None
        )
        metadata = preflight(args.mode, args.corpus_dir)
        backend = gpu_backend if gpu_backend is not None else "cpu"
        dtype = "f32" if gpu_backend is not None else "f64"
        environment = capture_environment(backend=backend, dtype=dtype, seed=0)
        legacy._validate_environment(args.mode, environment)
        match = legacy._RUN_ID_RE.fullmatch(run_dir.name)
        if (
            match is None
            or match["label"] != args.label
            or not str(environment["git_commit"]).startswith(match["sha"])
        ):
            raise legacy.DriverMetadataError(
                "run ID must match this code SHA and registered label"
            )
        legacy._reserve_run_dir(run_dir)
        if gpu_backend == "wgpu":
            cases = collect_cases(args.mode, args.corpus_dir, backend="wgpu")
        else:
            cases = collect_cases(args.mode, args.corpus_dir)
        if len(cases) != DENOMINATORS[args.mode]:
            raise legacy.DriverMetadataError("incomplete registered case population")
        config = {
            "experiment_id": EXP_ID,
            "protocol_revision": PROTOCOL_REVISION,
            "mode": args.mode,
            "iterations": len(cases),
            "warmup": 0,
            "seed_counter": 0,
            "seed_key": 1,
            "out_dir": str(run_dir),
            **metadata,
        }
        result_name = f"{args.mode}_{args.label}.json"
        entry: legacy.ArtefactEntry = legacy._MODE_HYPOTHESIS[args.mode]
        if args.mode == "kernel-path":
            entry = {"hypotheses": ["H4"], "timing_method": "not-timed"}
        sidecar = {
            "exp_id": EXP_ID,
            "run_id": run_dir.name,
            "session": args.session,
            "operator": args.operator,
            "artefacts": {result_name: entry},
        }
        _storage_check(
            run_dir,
            {"environment": environment, "config": config, "cases": cases},
            sidecar,
            mode=args.mode,
        )
        metadata_path = legacy.write_campaign_metadata(run_dir, **sidecar)
        try:
            write_result(
                run_dir / result_name,
                environment=environment,
                config=config,
                payload={"cases": cases},
            )
        except BaseException:
            metadata_path.unlink(missing_ok=True)
            raise
        if gpu_backend == "wgpu":
            close_run(run_dir, expected_backend="wgpu")
        else:
            close_run(run_dir)
        abort_count = sum(case.get("aborted") is True for case in cases)
        if abort_count:
            raise legacy.DriverError(
                f"{abort_count} registered case(s) aborted; "
                f"invalid run evidence retained at {run_dir}"
            )
    except (legacy.DriverError, CorpusValidationError, OutputPathError, OSError) as exc:
        print(f"ABORT: {exc}", file=sys.stderr)
        return 2
    print(f"Wrote and manifested {run_dir}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
