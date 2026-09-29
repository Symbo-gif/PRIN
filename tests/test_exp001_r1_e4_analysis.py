"""Tests for the committed EXP-001-r1 E4 analysis module.

The module lives under the experiment's record root, which campaign plan §7.4
item 2 names as a permitted location for analysis code, and whose directory
name is not a legal Python identifier — so it is loaded here by path through
``importlib`` rather than imported. Keeping the tests under ``tests/`` puts them
inside the repository's authoritative pytest gate, which is the compensating
control DV-040 records for a record-root analysis module.

What these tests pin is the frozen pre-registration §8 decision rule and the
fail-closed posture around it: the abort-exclusion rule, "a partial denominator
can never confirm", H2a's non-reducible ``978 + 22`` denominators, H3's
projection comparison, H4's two-backend non-pooling, §8 rule 2's
re-evaluation of every stored decision from the retained per-array records,
the §8 rule 1 provenance/inventory checks, the write-destination containment,
and byte-for-byte determinism of every generated output (campaign plan §7.4
step 5).
"""

from __future__ import annotations

import copy
import hashlib
import importlib.util
import json
import sys
import tempfile
from pathlib import Path
from typing import Any

import pytest

_REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
_MODULE_PATH = (
    _REPOSITORY_ROOT
    / "DOCS"
    / "experiments"
    / "EXP-001-r1-golden-trajectory-numerical-parity"
    / "analysis"
    / "exp001_r1_e4_analysis.py"
)


def _load_module() -> Any:
    """Load the analysis module by path, as its directory name is not importable."""
    spec = importlib.util.spec_from_file_location("exp001_r1_e4_analysis", _MODULE_PATH)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


analysis = _load_module()


# --------------------------------------------------------------------------
# Synthetic record builders
# --------------------------------------------------------------------------


def _comparison(
    name: str,
    *,
    ok: bool = True,
    abs_diff: float = 0.0,
    rel_diff: float | None = None,
    total: int = 8,
    quantity: str | None = "auto",
    atol: float = 1e-8,
) -> dict[str, Any]:
    """Build one comparison record shaped like the driver's output."""
    if quantity == "auto":
        quantity = analysis._quantity_for(name)
    record: dict[str, Any] = {
        "array_name": name,
        "within_tolerance": ok,
        # A breach must carry max_abs_diff > atol or the driver's own isclose
        # rule could not have produced it; the analysis checks that.
        "max_abs_diff": abs_diff if ok else max(abs_diff, atol * 10.0),
        "max_rel_diff": (abs_diff if rel_diff is None else rel_diff)
        if ok
        else max(abs_diff if rel_diff is None else rel_diff, atol * 10.0),
        "failed_count": 0 if ok else 1,
        "total_count": total,
    }
    if quantity is not None:
        record["quantity"] = quantity
    return record


def _totals(*, fuzz: bool = False) -> dict[str, int]:
    """Return the registered per-array element counts for the synthetic cases."""
    return analysis._expected_totals(8, 20, with_final=not fuzz)


def _corpus_case(
    case_id: str,
    *,
    classification: str = "native-parity",
    aborted: bool = False,
    model: str = "kuramoto",
    coupling: str = "mean_field",
    integrator: str = "euler",
) -> dict[str, Any]:
    """Build one corpus case record consistent with its own classification."""
    if aborted:
        return {
            "case_id": case_id,
            "model": model,
            "coupling": coupling,
            "integrator": integrator,
            "n_steps": 20,
            "aborted": True,
            "abort_reason": "nan-guard",
        }
    totals = _totals()
    native_ok = classification == "native-parity"
    explained = classification == "explained-dv007"

    def comparisons(ok: bool) -> list[dict[str, Any]]:
        """Build one full 11-array comparison list at the registered shapes."""
        return [
            _comparison(name, ok=ok, total=totals[name])
            for name in analysis.CORPUS_ARRAY_NAMES
        ]

    case: dict[str, Any] = {
        "case_id": case_id,
        "model": model,
        "coupling": coupling,
        "integrator": integrator,
        "n_oscillators": 8,
        "n_steps": 20,
        "dt": 0.005,
        "aborted": False,
        "native_within_tolerance": native_ok,
        "pointwise_eligible": classification != "ill-conditioned-characterization",
        "accepted": None
        if classification == "ill-conditioned-characterization"
        else classification != "unexplained-breach",
        "classification": classification,
        "comparisons": comparisons(native_ok),
        "f64_comparisons": None,
    }
    if explained or classification == "unexplained-breach":
        case["f64_comparisons"] = comparisons(explained)
    if classification == "ill-conditioned-characterization":
        case["sensitivity_reproduced"] = True
        case["sensitivity_comparisons"] = comparisons(False)
    return case


def _run(
    label: str, cases: list[dict[str, Any]], payload: dict[str, Any] | None = None
) -> Any:
    """Build one ``LoadedRun`` around synthetic cases."""
    leg = next(leg for leg in analysis.RUN_LEGS if leg.label == label)
    if payload is None:
        payload = {"cases": cases, "config": {}, "environment": {}}
    return analysis.LoadedRun(
        leg=leg,
        payload=payload,
        cases=cases,
        sidecar={},
        files=[{"path": leg.artefact, "bytes": 1, "sha256": "0" * 64}],
        manifest_bytes=1,
        manifest_sha256="0" * 64,
    )


def _kernel_case(case_id: str, *, ok: bool = True, n: int = 8) -> dict[str, Any]:
    """Build one H4 kernel-path case record with its retained backend proof."""
    return {
        "case_id": case_id,
        "model": "kuramoto",
        "coupling": "sparse_knn",
        "n_oscillators": n,
        "sparse_k": 3,
        "aborted": False,
        "within_tolerance": ok,
        "dlpack_devices": {name: "cuda" for name in analysis.KERNEL_ARRAY_NAMES},
        "comparisons": [
            _comparison(
                name, ok=ok, total=n, quantity=None, atol=analysis.legacy.KERNEL_ATOL
            )
            for name in analysis.KERNEL_ARRAY_NAMES
        ],
    }


def _repeatability_case(case_id: str, *, identical: bool = True) -> dict[str, Any]:
    """Build one H3 case record whose digests agree with its own claim."""
    names = analysis._array_digest_names()
    first = {name: hashlib.sha256(name.encode()).hexdigest() for name in names}
    second = dict(first)
    if not identical:
        second["phase_traj"] = hashlib.sha256(b"other").hexdigest()
    mismatched = [] if identical else ["phase_traj"]
    return {
        "case_id": case_id,
        "aborted": False,
        "bit_identical": identical,
        "mismatched_arrays": mismatched,
        "first_array_sha256": first,
        "second_array_sha256": second,
    }


def _repeatability_run(label: str, *, identical: bool = True, digest: str = "x") -> Any:
    """Build one H3 run with a payload whose projection is controllable."""
    cases = [
        _repeatability_case(case_id, identical=identical)
        for case_id in analysis.r1.REPEATABILITY_CASES
    ]
    payload = {
        "cases": cases,
        "config": {
            "experiment_id": analysis.EXPERIMENT_ID,
            "mode": "repeatability",
            "out_dir": f"C:\\execution\\checkout\\{label}",
            "marker": digest,
        },
        "environment": {"git_commit": analysis.EXECUTION_COMMIT, "backend": "cpu"},
    }
    return _run(label, cases, payload)


# --------------------------------------------------------------------------
# Index and constant invariants
# --------------------------------------------------------------------------


def test_run_index_is_six_distinct_r1_runs_with_one_label_per_backend():
    """§8 rule 1 requires six distinct r1 run IDs, one per kernel-path backend."""
    assert len(analysis.RUN_LEGS) == 6
    run_ids = [leg.run_id for leg in analysis.RUN_LEGS]
    assert len(set(run_ids)) == 6
    labels = [leg.label for leg in analysis.RUN_LEGS]
    assert len(set(labels)) == 6
    assert labels.count("r1-kernel-path-wgpu") == 1
    assert labels.count("r1-kernel-path-cuda") == 1
    assert all(label.startswith("r1-") for label in labels)


def test_run_index_modes_match_the_registered_denominators():
    """Each indexed leg's mode is one of the four the r1 driver registers."""
    assert sorted({leg.mode for leg in analysis.RUN_LEGS}) == [
        "corpus",
        "fuzz",
        "kernel-path",
        "repeatability",
    ]
    assert len([leg for leg in analysis.RUN_LEGS if leg.mode == "repeatability"]) == 2
    assert len([leg for leg in analysis.RUN_LEGS if leg.mode == "kernel-path"]) == 2


def test_extension_hashes_are_distinct_and_bound_to_their_own_backend_label():
    """§5.1: two feature-exclusive builds, each verified against its own entry."""
    assert analysis.WGPU_EXTENSION_SHA256 != analysis.CUDA_EXTENSION_SHA256
    by_label = {leg.label: leg for leg in analysis.RUN_LEGS}
    assert (
        by_label["r1-kernel-path-wgpu"].extension_sha256
        == analysis.WGPU_EXTENSION_SHA256
    )
    assert (
        by_label["r1-kernel-path-cuda"].extension_sha256
        == analysis.CUDA_EXTENSION_SHA256
    )
    # Runs 2-6 executed under the leg-2 (cuda) build, per log.md.
    for label in (
        "r1-corpus-cpu",
        "r1-repeatability-cpu",
        "r1-seedrep0-cpu",
        "r1-fuzz-cpu",
    ):
        assert by_label[label].extension_sha256 == analysis.CUDA_EXTENSION_SHA256


def test_main_baseline_and_execution_commit_are_distinct():
    """§5.1 keeps M, R and F as distinct roles that are never casually equated."""
    assert analysis.MAIN_BASELINE != analysis.EXECUTION_COMMIT
    assert analysis.FREEZE_COMMIT == analysis.EXECUTION_COMMIT
    assert len(analysis.MAIN_BASELINE) == 40
    assert len(analysis.EXECUTION_COMMIT) == 40


def test_h2a_denominators_sum_to_the_registered_stream():
    """§2 H2a: 978 eligible + 22 characterized, never 1,000 pointwise."""
    assert (
        analysis.H2A_ELIGIBLE_DENOMINATOR + analysis.H2A_CHARACTERIZED_DENOMINATOR
        == analysis.H2A_DENOMINATOR
    )
    assert len(analysis.r1.ILL_CONDITIONED) == analysis.H2A_CHARACTERIZED_DENOMINATOR
    assert all(0 <= index < 1000 for index in analysis.r1.ILL_CONDITIONED)


def test_expected_results_cover_every_registered_hypothesis():
    """§3's frozen predictions are quoted for all five hypotheses."""
    assert [row[0] for row in analysis.EXPECTED_RESULTS] == [
        "H1",
        "H2a",
        "H2b",
        "H3",
        "H4",
    ]


def test_generated_filenames_match_the_registered_output_table():
    """§8's fixed output table names exactly four generated files."""
    assert sorted(analysis.GENERATED_FILENAMES) == [
        "case-comparisons.json",
        "error-distributions.json",
        "summary.json",
        "summary.md",
    ]


# --------------------------------------------------------------------------
# Comparator-record consistency (§8 rule 7's necessary conditions)
# --------------------------------------------------------------------------


def test_comparison_violation_accepts_a_consistent_pass():
    """A record whose decision and counts agree is internally consistent."""
    record = _comparison("phase_traj", ok=True, abs_diff=1e-12, total=168)
    assert (
        analysis._comparison_violation(
            record,
            expected_name="phase_traj",
            expected_total=168,
            expected_quantity="trajectory",
            atol=1e-8,
            context="case x",
        )
        is None
    )


def test_comparison_violation_rejects_within_tolerance_contradicting_failed_count():
    """within_tolerance must equal failed_count == 0."""
    record = _comparison("phase_traj", ok=True, total=168)
    record["failed_count"] = 3
    violation = analysis._comparison_violation(
        record,
        expected_name="phase_traj",
        expected_total=168,
        expected_quantity="trajectory",
        atol=1e-8,
        context="case x",
    )
    assert violation is not None and "contradicts failed_count" in violation


def test_comparison_violation_rejects_a_breach_below_atol():
    """A breach implies some element exceeded atol + rtol*|operand| >= atol."""
    record = _comparison("phase_traj", ok=False, total=168)
    record["max_abs_diff"] = 1e-12
    violation = analysis._comparison_violation(
        record,
        expected_name="phase_traj",
        expected_total=168,
        expected_quantity="trajectory",
        atol=1e-8,
        context="case x",
    )
    assert violation is not None and "cannot produce" in violation


def test_comparison_violation_rejects_a_wrong_element_count():
    """total_count must be the count the registered case shape implies."""
    record = _comparison("phase_traj", ok=True, total=168)
    violation = analysis._comparison_violation(
        record,
        expected_name="phase_traj",
        expected_total=189,
        expected_quantity="trajectory",
        atol=1e-8,
        context="case x",
    )
    assert violation is not None and "total_count" in violation


def test_comparison_violation_rejects_a_wrong_quantity_label():
    """The metric arrays carry the metric tolerance, not the trajectory one."""
    record = _comparison(
        "order_parameter_traj", ok=True, total=21, quantity="trajectory"
    )
    violation = analysis._comparison_violation(
        record,
        expected_name="order_parameter_traj",
        expected_total=21,
        expected_quantity="metric",
        atol=1e-12,
        context="case x",
    )
    assert violation is not None and "quantity" in violation
    record["quantity"] = "metric"
    assert (
        analysis._comparison_violation(
            record,
            expected_name="order_parameter_traj",
            expected_total=21,
            expected_quantity="metric",
            atol=1e-12,
            context="case x",
        )
        is None
    )


def test_comparison_violation_rejects_non_finite_and_negative_magnitudes():
    """§8 rule 1 rejects non-finite scientific fields."""
    for value in (float("nan"), float("inf"), -1.0):
        record = _comparison("phase_traj", ok=True, total=168)
        record["max_abs_diff"] = value
        violation = analysis._comparison_violation(
            record,
            expected_name="phase_traj",
            expected_total=168,
            expected_quantity="trajectory",
            atol=1e-8,
            context="case x",
        )
        assert violation is not None


def test_comparison_violation_rejects_zero_abs_with_nonzero_rel():
    """A zero maximum absolute difference forces every relative difference to zero."""
    record = _comparison("phase_traj", ok=True, abs_diff=0.0, total=168)
    record["max_rel_diff"] = 1e-9
    violation = analysis._comparison_violation(
        record,
        expected_name="phase_traj",
        expected_total=168,
        expected_quantity="trajectory",
        atol=1e-8,
        context="case x",
    )
    assert violation is not None and "nonzero max_rel_diff" in violation


def test_expected_totals_encode_the_registered_array_shapes():
    """Trajectories are N*(steps+1); bounded metrics are steps+1."""
    totals = analysis._expected_totals(12, 20, with_final=True)
    assert totals["phase_init"] == 12
    assert totals["phase_final"] == 12
    assert totals["phase_traj"] == 12 * 21
    assert totals["order_parameter_traj"] == 21
    horizon = analysis._expected_totals(26, 20, with_final=False)
    assert "phase_final" not in horizon
    assert horizon["phase_traj"] == 26 * 21
    assert horizon["mean_phase_coherence_traj"] == 21


# --------------------------------------------------------------------------
# §8 rule 2 — re-evaluation from retained per-array records
# --------------------------------------------------------------------------


def test_reclassify_reproduces_native_parity():
    """All-native pass classifies native-parity and is accepted."""
    case = _corpus_case("c")
    assert analysis._reclassify_pointwise(case, ill_conditioned=False) == {
        "pointwise_eligible": True,
        "accepted": True,
        "classification": "native-parity",
        "native_within_tolerance": True,
    }


def test_reclassify_reproduces_explained_dv007():
    """An eligible-path native breach the float64 reference explains is accepted."""
    case = _corpus_case("c", classification="explained-dv007")
    recomputed = analysis._reclassify_pointwise(case, ill_conditioned=False)
    assert recomputed["classification"] == "explained-dv007"
    assert recomputed["accepted"] is True
    assert recomputed["native_within_tolerance"] is False


def test_reclassify_reproduces_unexplained_breach_off_the_dv007_paths():
    """A breach off the eligible paths is unexplained whatever the history."""
    case = _corpus_case("c", classification="unexplained-breach", coupling="sparse_knn")
    case["f64_comparisons"] = None
    recomputed = analysis._reclassify_pointwise(case, ill_conditioned=False)
    assert recomputed["classification"] == "unexplained-breach"
    assert recomputed["accepted"] is False


def test_reclassify_reproduces_unexplained_breach_on_an_eligible_path():
    """An eligible-path breach the float64 reference does not fix is unexplained."""
    case = _corpus_case("c", classification="unexplained-breach")
    recomputed = analysis._reclassify_pointwise(case, ill_conditioned=False)
    assert recomputed["classification"] == "unexplained-breach"
    assert recomputed["accepted"] is False


def test_reclassify_refuses_an_eligible_breach_with_no_corrected_reference():
    """§5.3 step 5 cannot be evaluated without the retained f64 comparison."""
    case = _corpus_case("c", classification="unexplained-breach")
    case["f64_comparisons"] = None
    with pytest.raises(analysis.AnalysisError, match="float64-reference"):
        analysis._reclassify_pointwise(case, ill_conditioned=False)


def test_reclassify_characterizes_an_ill_conditioned_case():
    """The fixed-22 stratum is characterized, never counted as pointwise parity."""
    case = _corpus_case("c", classification="ill-conditioned-characterization")
    recomputed = analysis._reclassify_pointwise(case, ill_conditioned=True)
    assert recomputed == {
        "pointwise_eligible": False,
        "accepted": None,
        "classification": "ill-conditioned-characterization",
        "native_within_tolerance": False,
        "sensitivity_reproduced": True,
    }


def test_reclassify_refuses_a_missing_sensitivity_witness():
    """§4.2 item 2: an unavailable witness is never silently counted as a pass."""
    case = _corpus_case("c", classification="ill-conditioned-characterization")
    case["sensitivity_comparisons"] = None
    with pytest.raises(analysis.AnalysisError, match="unavailable"):
        analysis._reclassify_pointwise(case, ill_conditioned=True)


def test_reclassify_reports_an_unreproduced_sensitivity_witness():
    """A sensitivity comparison that does not breach is not a witness."""
    case = _corpus_case("c", classification="ill-conditioned-characterization")
    case["sensitivity_comparisons"] = [
        _comparison(name, ok=True) for name in analysis.CORPUS_ARRAY_NAMES
    ]
    recomputed = analysis._reclassify_pointwise(case, ill_conditioned=True)
    assert recomputed["sensitivity_reproduced"] is False


def test_verify_pointwise_case_rejects_a_stored_classification_the_records_contradict():
    """§8 rule 2 re-evaluates; a disagreeing stored field fails closed."""
    case = _corpus_case("c", classification="native-parity")
    case["classification"] = "explained-dv007"
    with pytest.raises(analysis.AnalysisError, match="not reproduced"):
        analysis._verify_pointwise_case(case, ill_conditioned=False, fuzz=False)


def test_verify_pointwise_case_rejects_a_contradicted_accepted_flag():
    """accepted is a claim; the retained comparisons are the evidence."""
    case = _corpus_case("c", classification="native-parity")
    case["accepted"] = False
    with pytest.raises(analysis.AnalysisError, match="accepted"):
        analysis._verify_pointwise_case(case, ill_conditioned=False, fuzz=False)


def test_verify_pointwise_case_rejects_contradicting_float64_evidence():
    """f64 evidence exists exactly on an eligible breached path or a fixed-22 case."""
    case = _corpus_case("c", classification="native-parity")
    totals = _totals()
    case["f64_comparisons"] = [
        _comparison(name, ok=True, total=totals[name])
        for name in analysis.CORPUS_ARRAY_NAMES
    ]
    with pytest.raises(analysis.AnalysisError, match="float64-reference evidence"):
        analysis._verify_pointwise_case(case, ill_conditioned=False, fuzz=False)


def test_verify_pointwise_case_rejects_sensitivity_evidence_outside_the_fixed_stratum():
    """Sensitivity evidence is present exactly for the registered 22 indices."""
    case = _corpus_case("c", classification="native-parity")
    totals = _totals()
    case["sensitivity_comparisons"] = [
        _comparison(name, ok=False, total=totals[name])
        for name in analysis.CORPUS_ARRAY_NAMES
    ]
    with pytest.raises(analysis.AnalysisError, match="sensitivity evidence"):
        analysis._verify_pointwise_case(case, ill_conditioned=False, fuzz=False)


def test_verify_pointwise_case_accepts_an_aborted_case_with_a_reason():
    """An aborted case is reported through its reason, not adjudicated."""
    case = _corpus_case("c", aborted=True)
    analysis._verify_pointwise_case(case, ill_conditioned=False, fuzz=False)
    case.pop("abort_reason")
    with pytest.raises(analysis.AnalysisError, match="abort_reason"):
        analysis._verify_pointwise_case(case, ill_conditioned=False, fuzz=False)


def test_verify_pointwise_case_requires_the_registered_horizon_for_fuzz():
    """The within-horizon comparison covers steps 0..min(20, n_steps)."""
    case = _corpus_case("c", classification="native-parity")
    case.pop("f64_comparisons")
    case["case_index"] = 0
    case["horizon"] = 20
    totals = _totals(fuzz=True)
    case["comparisons"] = [
        _comparison(name, ok=True, total=totals[name])
        for name in analysis.FUZZ_ARRAY_NAMES
    ]
    analysis._verify_pointwise_case(case, ill_conditioned=False, fuzz=True)
    case["horizon"] = 19
    with pytest.raises(analysis.AnalysisError, match="horizon"):
        analysis._verify_pointwise_case(case, ill_conditioned=False, fuzz=True)


# --------------------------------------------------------------------------
# H1 (§8 rule 3)
# --------------------------------------------------------------------------


def _corpus_run(classifications: list[str]) -> Any:
    """Build an H1 run from one classification per case."""
    return _run(
        "r1-corpus-cpu",
        [
            _corpus_case(f"case-{index:04d}", classification=classification)
            for index, classification in enumerate(classifications)
        ],
    )


def test_h1_confirms_only_with_the_full_504_valid_accepted_denominator():
    """504 accepted, native and explained published separately, confirms H1."""
    classifications = ["native-parity"] * 485 + ["explained-dv007"] * 19
    record = analysis.adjudicate_h1(_corpus_run(classifications))
    assert record["verdict"] == "CONFIRMED"
    assert record["n_accepted"] == 504
    assert record["n_native_parity"] == 485
    assert record["n_explained_dv007"] == 19
    assert record["n_unexplained_breach"] == 0
    assert record["full_denominator"] == 504


def test_h1_refutes_on_a_single_valid_unexplained_breach():
    """§4.1: one valid unexplained breach refutes, and is a D1."""
    classifications = ["native-parity"] * 503 + ["unexplained-breach"]
    record = analysis.adjudicate_h1(_corpus_run(classifications))
    assert record["verdict"] == "REFUTED"
    assert record["n_unexplained_breach"] == 1
    assert record["n_failing"] == 1
    assert record["breaches"]["breaching_arrays"]
    assert analysis.is_d1({"H1": record})


def test_h1_is_inconclusive_when_an_abort_leaves_a_partial_denominator():
    """A partial denominator cannot confirm a hypothesis."""
    classifications = ["native-parity"] * 503
    run = _corpus_run(classifications)
    run.cases.append(_corpus_case("case-abort", aborted=True))
    record = analysis.adjudicate_h1(run)
    assert record["verdict"] == "INCONCLUSIVE"
    assert record["n_aborted"] == 1
    assert record["abort_reasons"] == ["nan-guard"]
    assert not analysis.is_d1({"H1": record})


def test_h1_is_inconclusive_when_extra_cases_exceed_the_denominator():
    """More total cases than the denominator is not a confirmation either."""
    run = _corpus_run(["native-parity"] * 504)
    run.cases.append(_corpus_case("case-extra", aborted=True))
    assert analysis.adjudicate_h1(run)["verdict"] == "INCONCLUSIVE"


# --------------------------------------------------------------------------
# H2a (§8 rule 4)
# --------------------------------------------------------------------------


def _fuzz_case(
    index: int, *, classification: str, aborted: bool = False
) -> dict[str, Any]:
    """Build one fuzz case record at a registered stream index."""
    case = _corpus_case(f"fuzz-{index}", classification=classification, aborted=aborted)
    case.pop("case_id")
    case["case_index"] = index
    case["horizon"] = 20
    return case


def _fuzz_run(
    *,
    characterized_aborted: int = 0,
    eligible_aborted: int = 0,
    breach: int | None = None,
) -> Any:
    """Build an H2a run over all 1,000 registered indices."""
    ill = sorted(analysis.r1.ILL_CONDITIONED)
    cases: list[dict[str, Any]] = []
    for index in range(1000):
        if index in analysis.r1.ILL_CONDITIONED:
            position = ill.index(index)
            if position < characterized_aborted:
                cases.append(
                    _fuzz_case(
                        index,
                        classification="ill-conditioned-characterization",
                        aborted=True,
                    )
                )
                continue
            cases.append(
                _fuzz_case(index, classification="ill-conditioned-characterization")
            )
            continue
        if eligible_aborted and index == 0:
            cases.append(
                _fuzz_case(index, classification="native-parity", aborted=True)
            )
            continue
        if breach is not None and index == breach:
            cases.append(_fuzz_case(index, classification="unexplained-breach"))
            continue
        cases.append(_fuzz_case(index, classification="native-parity"))
    return _run("r1-fuzz-cpu", cases)


def test_h2a_confirms_only_with_978_pointwise_plus_all_22_characterized():
    """§2 H2a reports 978 + 22, never 1,000 pointwise passes."""
    record = analysis.adjudicate_h2a(_fuzz_run())
    assert record["verdict"] == "CONFIRMED"
    assert record["n_eligible_accepted"] == 978
    assert record["n_valid_characterizations"] == 22
    assert record["reported_as"].startswith("978 pointwise + 22 characterized")
    assert record["eligible_denominator"] == 978
    assert record["characterized_denominator"] == 22


def test_h2a_refutes_on_one_valid_eligible_unexplained_breach():
    """§4.1: a breach outside the fixed 22-case set refutes H2a."""
    record = analysis.adjudicate_h2a(_fuzz_run(breach=123))
    assert record["verdict"] == "REFUTED"
    assert record["unexplained_breach_case_indices"] == [123]
    assert analysis.is_d1({"H2a": record})


def test_h2a_cannot_confirm_when_a_characterization_is_unavailable():
    """§8 rule 4: a missing witness cannot reduce the denominator to confirm."""
    record = analysis.adjudicate_h2a(_fuzz_run(characterized_aborted=1))
    assert record["verdict"] == "INCONCLUSIVE"
    assert record["n_valid_characterizations"] == 21
    assert record["n_aborted_characterized"] == 1
    assert not analysis.is_d1({"H2a": record})


def test_h2a_cannot_confirm_when_an_eligible_case_aborts():
    """An aborted eligible case leaves a partial pointwise denominator."""
    record = analysis.adjudicate_h2a(_fuzz_run(eligible_aborted=1))
    assert record["verdict"] == "INCONCLUSIVE"
    assert record["n_eligible_accepted"] == 977
    assert record["n_aborted_eligible"] == 1


def test_h2a_a_breach_inside_the_characterized_stratum_is_not_an_eligible_breach():
    """The fixed 22 are characterized, so they cannot refute the eligible arm."""
    run = _fuzz_run()
    index = sorted(analysis.r1.ILL_CONDITIONED)[0]
    case = next(c for c in run.cases if c["case_index"] == index)
    case["classification"] = "unexplained-breach"
    case["accepted"] = False
    case["pointwise_eligible"] = True
    record = analysis.adjudicate_h2a(run)
    assert record["verdict"] == "INCONCLUSIVE"
    assert record["n_failing"] == 0
    assert record["n_unexplained_breach"] == 1
    assert record["n_valid_characterizations"] == 21
    assert not analysis.is_d1({"H2a": record})


# --------------------------------------------------------------------------
# H3 (§8 rule 6)
# --------------------------------------------------------------------------


def test_h3_confirms_on_internal_byte_identity_and_equal_projections():
    """Both runs 14/14 byte-identical and their projections agree."""
    first = _repeatability_run("r1-repeatability-cpu")
    second = _repeatability_run("r1-seedrep0-cpu")
    record = analysis.adjudicate_h3(first, second)
    assert record["verdict"] == "CONFIRMED"
    assert record["projections_equal"] is True
    assert record["n_aborted"] == 0
    assert len(record["case_ids"]) == 14


def test_h3_refutes_on_a_valid_within_invocation_byte_mismatch():
    """§4.1: any valid within-invocation byte mismatch refutes H3."""
    first = _repeatability_run("r1-repeatability-cpu", identical=False)
    second = _repeatability_run("r1-seedrep0-cpu")
    record = analysis.adjudicate_h3(first, second)
    assert record["verdict"] == "REFUTED"
    assert record["internal_mismatches"]
    assert analysis.is_d1({"H3": record})


def test_h3_refutes_when_the_two_separate_invocations_disagree():
    """The canonical scientific projections must match across the two runs."""
    first = _repeatability_run("r1-repeatability-cpu", digest="a")
    second = _repeatability_run("r1-seedrep0-cpu", digest="b")
    record = analysis.adjudicate_h3(first, second)
    assert record["verdict"] == "REFUTED"
    assert record["projections_equal"] is False


def test_h3_projection_removes_only_the_three_registered_fields():
    """No scientific field and no array digest is removed from the projection."""
    run = _repeatability_run("r1-repeatability-cpu")
    projection = json.loads(analysis._repeatability_projection(run.payload))
    assert "environment" not in projection
    assert "out_dir" not in projection["config"]
    assert projection["config"]["marker"] == "x"
    assert projection["cases"] == run.payload["cases"]
    digests = projection["cases"][0]["first_array_sha256"]
    assert len(digests) == len(analysis.CORPUS_ARRAY_NAMES)


def test_h3_projection_strips_a_nested_run_id():
    """Any per-run run_id is removed wherever it appears."""
    run = _repeatability_run("r1-repeatability-cpu")
    run.payload["config"]["run_id"] = "RUN-x"
    run.payload["cases"][0]["run_id"] = "RUN-x"
    projection = json.loads(analysis._repeatability_projection(run.payload))
    assert "run_id" not in projection["config"]
    assert "run_id" not in projection["cases"][0]


def test_h3_is_inconclusive_when_a_case_aborts():
    """Missing or aborted coverage is inconclusive, not a refutation."""
    first = _repeatability_run("r1-repeatability-cpu")
    second = _repeatability_run("r1-seedrep0-cpu")
    for run in (first, second):
        run.cases[0] = {
            "case_id": run.cases[0]["case_id"],
            "aborted": True,
            "abort_reason": "envelope",
        }
        run.payload["cases"] = run.cases
    record = analysis.adjudicate_h3(first, second)
    assert record["verdict"] == "INCONCLUSIVE"
    assert record["n_aborted"] == 2
    assert record["projections_equal"] is True
    assert not analysis.is_d1({"H3": record})


def test_verify_repeatability_population_rejects_a_contradicted_bit_identity_claim():
    """The retained digests, not the stored flag, decide byte identity."""
    run = _repeatability_run("r1-repeatability-cpu")
    run.cases[0]["bit_identical"] = False
    with pytest.raises(analysis.AnalysisError, match="contradicts"):
        analysis.verify_repeatability_population(run)


def test_verify_repeatability_population_rejects_a_wrong_inventory():
    """Exactly the 14 registered representatives, no substitutions."""
    run = _repeatability_run("r1-repeatability-cpu")
    run.cases[0]["case_id"] = "some_other_case"
    with pytest.raises(analysis.AnalysisError, match="14 registered"):
        analysis.verify_repeatability_population(run)


# --------------------------------------------------------------------------
# H4 (§8 rule 7)
# --------------------------------------------------------------------------


def _kernel_run(label: str, *, failing: int = 0, total: int = 72) -> Any:
    """Build one H4 backend run with the required per-case proofs.

    The wgpu leg's *environment* backend is ``wgpu`` while its DLPack capsules
    are host-exported (``cpu``); the CUDA leg is ``cuda`` on both. That asymmetry
    is the binding's documented behaviour and is what §8 rule 1 registers.
    """
    wgpu = label.endswith("wgpu")
    backend = "wgpu" if wgpu else "cuda"
    device = "cpu" if wgpu else "cuda"
    cases = []
    for index in range(total):
        case = _kernel_case(f"knn-{index:03d}", ok=index >= failing)
        case["dlpack_devices"] = {name: device for name in analysis.KERNEL_ARRAY_NAMES}
        if wgpu:
            case["backend_name"] = "wgpu<wgsl>"
        cases.append(case)
    payload = {
        "cases": cases,
        "config": {"prin_extension_sha256": "e" * 64},
        "environment": {
            "backend": backend,
            "dtype": "f32",
            "gpu": "RTX",
            "gpu_vram_mb": 8,
        },
    }
    return _run(label, cases, payload)


def test_h4_confirms_only_when_both_backends_supply_their_full_denominator():
    """Confirmation requires all 72 non-aborted comparisons on both backends."""
    record = analysis.adjudicate_h4(
        _kernel_run("r1-kernel-path-wgpu"), _kernel_run("r1-kernel-path-cuda")
    )
    assert record["verdict"] == "CONFIRMED"
    assert record["pooled"] is False
    assert record["n_fail_total"] == 0
    assert record["backends"]["wgpu"]["n_pass"] == 72
    assert record["backends"]["cuda"]["n_pass"] == 72
    coverage = record["required_backend_coverage"]
    assert coverage["required"] == ["cuda", "wgpu"]
    assert len(coverage["distinct_run_ids"]) == 2
    assert coverage["distinct_environments"] == ["cuda", "wgpu"]
    assert record["re_evaluated_from_raw_arrays"] is False


def test_h4_refutes_on_one_valid_breach_on_either_backend():
    """§4.1: any valid derivative comparison failing the tolerance refutes H4."""
    for failing_leg in ("wgpu", "cuda"):
        wgpu = _kernel_run(
            "r1-kernel-path-wgpu", failing=1 if failing_leg == "wgpu" else 0
        )
        cuda = _kernel_run(
            "r1-kernel-path-cuda", failing=1 if failing_leg == "cuda" else 0
        )
        record = analysis.adjudicate_h4(wgpu, cuda)
        assert record["verdict"] == "REFUTED"
        assert record["n_fail_total"] == 1
        assert analysis.is_d1({"H4": record})


def test_h4_is_inconclusive_on_partial_coverage_without_a_breach():
    """Absent or partial coverage without a valid breach is inconclusive."""
    record = analysis.adjudicate_h4(
        _kernel_run("r1-kernel-path-wgpu", total=71),
        _kernel_run("r1-kernel-path-cuda"),
    )
    assert record["verdict"] == "INCONCLUSIVE"
    assert not analysis.is_d1({"H4": record})


def test_verify_kernel_cases_requires_the_registered_backend_proof():
    """A wgpu leg needs host-exported capsules and a wgpu backend_name."""
    run = _kernel_run("r1-kernel-path-wgpu")
    ids = [case["case_id"] for case in run.cases]
    analysis.verify_kernel_cases(run, ids)
    run.cases[0]["backend_name"] = "cpu-native"
    with pytest.raises(analysis.AnalysisError, match="backend_name"):
        analysis.verify_kernel_cases(run, ids)
    run.cases[0]["backend_name"] = "wgpu<wgsl>"
    del run.cases[1]["backend_name"]
    with pytest.raises(analysis.AnalysisError, match="backend_name"):
        analysis.verify_kernel_cases(run, ids)


def test_verify_kernel_cases_rejects_a_wrong_capsule_device():
    """A CUDA leg requires all three capsules to be CUDA-resident."""
    run = _kernel_run("r1-kernel-path-cuda")
    ids = [case["case_id"] for case in run.cases]
    analysis.verify_kernel_cases(run, ids)
    run.cases[0]["dlpack_devices"]["damplitude"] = "cpu"
    with pytest.raises(analysis.AnalysisError, match="dlpack_devices"):
        analysis.verify_kernel_cases(run, ids)


def test_verify_kernel_cases_rejects_a_missing_proof_key():
    """All three dlpack_devices keys must be retained for E4 to verify."""
    run = _kernel_run("r1-kernel-path-cuda")
    ids = [case["case_id"] for case in run.cases]
    del run.cases[0]["dlpack_devices"]["dfrequency"]
    with pytest.raises(analysis.AnalysisError, match="dlpack_devices"):
        analysis.verify_kernel_cases(run, ids)


def test_verify_kernel_cases_rejects_a_contradicted_case_decision():
    """The case-level flag must agree with its three retained comparator records."""
    run = _kernel_run("r1-kernel-path-cuda")
    ids = [case["case_id"] for case in run.cases]
    run.cases[0]["within_tolerance"] = False
    with pytest.raises(analysis.AnalysisError, match="contradicts"):
        analysis.verify_kernel_cases(run, ids)


def test_verify_kernel_cases_rejects_a_wgpu_proof_on_a_cuda_leg():
    """Never relabel: a CUDA record must not carry a wgpu backend_name."""
    run = _kernel_run("r1-kernel-path-cuda")
    ids = [case["case_id"] for case in run.cases]
    run.cases[0]["backend_name"] = "wgpu<wgsl>"
    with pytest.raises(analysis.AnalysisError, match="must not carry"):
        analysis.verify_kernel_cases(run, ids)


def test_verify_kernel_cases_rejects_a_substituted_inventory():
    """Exactly the registered 72 case IDs, in order, with no substitution."""
    run = _kernel_run("r1-kernel-path-cuda")
    with pytest.raises(analysis.AnalysisError, match="inventory does not match"):
        analysis.verify_kernel_cases(run, ["other"] * 72)
    short = _kernel_run("r1-kernel-path-cuda", total=71)
    with pytest.raises(analysis.AnalysisError, match="expected 72"):
        analysis.verify_kernel_cases(short, [case["case_id"] for case in short.cases])


# --------------------------------------------------------------------------
# H2b summary recomputation (§8 rule 2 / rule 5)
# --------------------------------------------------------------------------


def _beyond(n_steps: int, *, drift: float = 0.0, offset: float = 0.0) -> dict[str, Any]:
    """Build one case's stored beyond-horizon block from explicit arrays."""
    import numpy as np

    points = n_steps - analysis.legacy.T_STAR
    reference = [0.5 + 0.01 * step + offset for step in range(points)]
    produced = [value + drift for value in reference]

    def block(ref: list[float], prod: list[float]) -> dict[str, Any]:
        """Pack one metric's paired arrays and the summaries E3 stored."""
        ref_array = np.asarray(ref, dtype=np.float64)
        prod_array = np.asarray(prod, dtype=np.float64)
        return {
            "reference": ref,
            "produced": prod,
            "n_points": len(ref),
            "reference_mean": float(np.mean(ref_array)),
            "produced_mean": float(np.mean(prod_array)),
            "mean_paired_difference": float(np.mean(prod_array - ref_array)),
        }

    names = analysis.legacy._BEYOND_HORIZON_ARRAY_NAMES
    return {name: block(reference, produced) for name in names}


def _h2b_case(
    index: int, n_steps: int, *, drift: float = 0.0, offset: float = 0.0
) -> dict[str, Any]:
    """Build one fuzz case carrying a stored beyond-horizon block."""
    case = _fuzz_case(index, classification="native-parity")
    case["n_steps"] = n_steps
    case["beyond_horizon"] = (
        _beyond(n_steps, drift=drift, offset=offset) if n_steps > 20 else None
    )
    return case


def _h2b_cases(count: int = 40) -> list[dict[str, Any]]:
    """Build a contributing H2b sample with non-degenerate descriptive stats."""
    return [
        _h2b_case(
            index,
            25,
            drift=1e-6 * ((index % 5) - 2),
            offset=1e-3 * index,
        )
        for index in range(count)
    ]


def test_verify_h2b_summaries_reproduces_the_stored_summaries_exactly():
    """The registered summaries must be recomputable from the stored arrays."""
    cases = [_h2b_case(index, 25) for index in range(4)]
    assert analysis.verify_h2b_summaries(cases) == 4


def test_verify_h2b_summaries_rejects_a_tampered_mean():
    """A stored summary the paired arrays do not reproduce fails closed."""
    cases = [_h2b_case(index, 25) for index in range(4)]
    metric = analysis.legacy._BEYOND_HORIZON_ARRAY_NAMES[0]
    cases[2]["beyond_horizon"][metric]["mean_paired_difference"] = 1.5
    with pytest.raises(analysis.AnalysisError, match="not exactly reproduced"):
        analysis.verify_h2b_summaries(cases)


def test_verify_h2b_summaries_rejects_a_horizon_presence_contradiction():
    """beyond_horizon exists exactly when n_steps > T_STAR."""
    cases = [_h2b_case(0, 20)]
    cases[0]["beyond_horizon"] = _beyond(25)
    with pytest.raises(analysis.AnalysisError, match="beyond_horizon present"):
        analysis.verify_h2b_summaries(cases)


def test_verify_h2b_summaries_counts_only_contributors_and_skips_aborts():
    """Cases at or below the horizon contribute nothing to H2b."""
    cases = [_h2b_case(0, 25), _h2b_case(1, 20), _h2b_case(2, 50)]
    cases.append(_fuzz_case(3, classification="native-parity", aborted=True))
    assert analysis.verify_h2b_summaries(cases) == 2


def test_verify_h2b_summaries_rejects_a_non_finite_paired_value():
    """§8 rule 1 rejects non-finite scientific fields."""
    cases = [_h2b_case(0, 25)]
    metric = analysis.legacy._BEYOND_HORIZON_ARRAY_NAMES[0]
    cases[0]["beyond_horizon"][metric]["produced"][0] = float("nan")
    with pytest.raises(analysis.AnalysisError, match="non-finite"):
        analysis.verify_h2b_summaries(cases)


def test_adjudicate_h2b_leg_uses_the_committed_driver_adjudicator():
    """The registered predicate is delegated, never re-implemented here."""
    cases = _h2b_cases(40)
    run = _run("r1-fuzz-cpu", cases)
    record = analysis.adjudicate_h2b_leg(run, 40)
    assert record["adjudicator"].endswith("exp001_r1_driver.adjudicate_h2b")
    assert record["driver_verdict"] == "CONFIRMED"
    assert record["all_cases_accounted_for"] is False  # 40 cases, not 1,000
    assert record["n_contributors"] == 40
    assert record["bootstrap_seed"] == analysis.r1.BOOTSTRAP_SEED
    assert set(record["metrics"]) == set(analysis.legacy._BEYOND_HORIZON_ARRAY_NAMES)
    for metric in record["metrics"].values():
        assert metric["verdict"] == "CONFIRMED"
        assert abs(metric["ci_upper"]) < metric["equivalence_margin"]
        assert metric["undefined_descriptive"] == []


def test_adjudicate_h2b_leg_is_inconclusive_when_not_all_cases_are_accounted_for():
    """§8 rule 5 requires all 1,000 cases accounted for before inference."""
    record = analysis.adjudicate_h2b_leg(_run("r1-fuzz-cpu", _h2b_cases(40)), 40)
    assert record["driver_verdict"] == "CONFIRMED"
    assert record["verdict"] == "INCONCLUSIVE"


def test_adjudicate_h2b_leg_is_inconclusive_when_a_case_aborts():
    """§7 completeness: any case abort makes H2b inconclusive."""
    cases = _h2b_cases(40)
    cases[3] = _fuzz_case(3, classification="native-parity", aborted=True)
    record = analysis.adjudicate_h2b_leg(_run("r1-fuzz-cpu", cases), 39)
    assert record["verdict"] == "INCONCLUSIVE"
    assert (
        record["metrics"][analysis.legacy._BEYOND_HORIZON_ARRAY_NAMES[0]]["verdict"]
        == "INCONCLUSIVE"
    )


# --------------------------------------------------------------------------
# Envelope, sidecar, inventory and log verification (§8 rule 1)
# --------------------------------------------------------------------------


def _payload(**overrides: Any) -> dict[str, Any]:
    """Build a conforming result envelope for one indexed leg."""
    payload: dict[str, Any] = {
        "environment": {field: "x" for field in analysis.legacy._REQUIRED_ENV_FIELDS},
        "config": {},
        "cases": [],
    }
    payload["environment"].update(
        {
            "git_commit": analysis.EXECUTION_COMMIT,
            "backend": "cpu",
            "dtype": "f64",
            "seed": 0,
        }
    )
    payload["config"].update(
        {
            "experiment_id": analysis.EXPERIMENT_ID,
            "protocol_revision": 1,
            "mode": "corpus",
            "seed_counter": 0,
            "seed_key": 1,
            "guard_policy": "non_negative",
            "corpus_manifest_sha256": analysis.r1.CORPUS_SHA256,
            "prin_extension_sha256": analysis.CUDA_EXTENSION_SHA256,
            "prin_extension": "C:\\checkout\\python\\prin\\_prin_core.pyd",
            "iterations": 0,
            "out_dir": "C:\\checkout\\RUN-20260929T092619Z-5d5ae35-r1-corpus-cpu",
            "reference_source_sha256": analysis.r1.REFERENCE_SOURCE_SHA256,
            "instrument_sha256": analysis.r1.INSTRUMENT_SHA256,
            "prinet_version": analysis.legacy.PRINET_REFERENCE_VERSION,
        }
    )
    payload.update(overrides)
    return payload


def _corpus_leg() -> Any:
    """Return the indexed corpus leg."""
    return next(leg for leg in analysis.RUN_LEGS if leg.label == "r1-corpus-cpu")


def test_verify_envelope_accepts_a_conforming_corpus_leg():
    """A conforming envelope passes every §8 rule 1 identity check."""
    analysis._verify_envelope(_payload(), _corpus_leg())


def test_verify_envelope_rejects_a_foreign_execution_commit():
    """Every run must identify R, not M and not any other SHA."""
    payload = _payload()
    payload["environment"]["git_commit"] = analysis.MAIN_BASELINE
    with pytest.raises(analysis.AnalysisError, match="git_commit"):
        analysis._verify_envelope(payload, _corpus_leg())


def test_verify_envelope_rejects_a_wrong_extension_hash_for_the_leg():
    """Each leg is verified against its own E3 build-log hash."""
    payload = _payload()
    payload["config"]["prin_extension_sha256"] = analysis.WGPU_EXTENSION_SHA256
    with pytest.raises(analysis.AnalysisError, match="prin_extension_sha256"):
        analysis._verify_envelope(payload, _corpus_leg())


def test_verify_envelope_rejects_a_mismatched_backend_or_dtype():
    """The label/backend/dtype pairing is registered, not inferred."""
    for field, value in (("backend", "cuda"), ("dtype", "f32")):
        payload = _payload()
        payload["environment"][field] = value
        with pytest.raises(analysis.AnalysisError, match=field):
            analysis._verify_envelope(payload, _corpus_leg())


def test_verify_envelope_rejects_an_iteration_count_contradicting_the_cases():
    """config.iterations must equal the stored case count."""
    payload = _payload()
    payload["config"]["iterations"] = 504
    with pytest.raises(analysis.AnalysisError, match="iterations"):
        analysis._verify_envelope(payload, _corpus_leg())


def test_verify_envelope_checks_the_basename_of_the_execution_out_dir():
    """Only the basename is checked; the absolute prefix is E3's checkout."""
    payload = _payload()
    payload["config"]["out_dir"] = "D:\\elsewhere\\some-other-run"
    with pytest.raises(analysis.AnalysisError, match="out_dir"):
        analysis._verify_envelope(payload, _corpus_leg())


def test_verify_envelope_requires_the_fuzz_stream_fingerprint():
    """The fuzz leg must carry the registered stream digest."""
    leg = next(leg for leg in analysis.RUN_LEGS if leg.label == "r1-fuzz-cpu")
    payload = _payload()
    payload["config"]["mode"] = "fuzz"
    payload["config"]["out_dir"] = "C:\\c\\" + leg.run_id
    payload["config"]["reference_source_sha256"] = analysis.r1.REFERENCE_SOURCE_SHA256
    payload["config"]["instrument_sha256"] = analysis.r1.INSTRUMENT_SHA256
    payload["config"]["prinet_version"] = analysis.legacy.PRINET_REFERENCE_VERSION
    with pytest.raises(analysis.AnalysisError, match="stream_sha256"):
        analysis._verify_envelope(payload, leg)
    payload["config"]["stream_sha256"] = analysis.r1.STREAM_SHA256
    analysis._verify_envelope(payload, leg)


def test_verify_envelope_requires_gpu_metadata_on_a_kernel_leg():
    """§4.2 item 4: a GPU leg lacking GPU/VRAM metadata is an abort."""
    leg = next(leg for leg in analysis.RUN_LEGS if leg.label == "r1-kernel-path-cuda")
    payload = _payload()
    payload["config"]["mode"] = "kernel-path"
    payload["config"]["prin_extension_sha256"] = analysis.CUDA_EXTENSION_SHA256
    payload["config"]["out_dir"] = "C:\\c\\" + leg.run_id
    payload["environment"].update({"backend": "cuda", "dtype": "f32"})
    payload["environment"].pop("gpu", None)
    with pytest.raises(analysis.AnalysisError, match="GPU leg is missing"):
        analysis._verify_envelope(payload, leg)


def test_run_id_pattern_rejects_a_trailing_newline_label():
    """The grammar is anchored with \\Z, not $."""
    assert (
        analysis.RUN_ID_PATTERN.fullmatch("RUN-20260929T092619Z-5d5ae35-r1-x\n") is None
    )
    assert (
        analysis.RUN_ID_PATTERN.fullmatch("RUN-20260929T092619Z-5d5ae35-r1-x")
        is not None
    )


def test_verify_e3_log_requires_the_freeze_sha_on_line_one(tmp_path):
    """campaign plan §12.4 records the freeze by quoting F on log.md line 1."""
    record = tmp_path / "DOCS" / "experiments" / analysis.RECORD_ROOT.name
    record.mkdir(parents=True)
    (record / "log.md").write_text(
        f"Pre-registration freeze: `{analysis.FREEZE_COMMIT}`\n"
        f"R = {analysis.EXECUTION_COMMIT}\nM = {analysis.MAIN_BASELINE}\n"
        f"{analysis.WGPU_EXTENSION_SHA256}\n{analysis.CUDA_EXTENSION_SHA256}\n",
        encoding="utf-8",
    )
    provenance = analysis.verify_e3_log(tmp_path)
    assert provenance["execution_commit"] == analysis.EXECUTION_COMMIT
    assert provenance["main_baseline"] == analysis.MAIN_BASELINE
    (record / "log.md").write_text(
        "Pre-registration freeze: `deadbeef`\n", encoding="utf-8"
    )
    with pytest.raises(analysis.AnalysisError, match="line 1"):
        analysis.verify_e3_log(tmp_path)


def test_verify_e3_log_requires_every_registered_literal(tmp_path):
    """A log missing M or either extension hash is not admissible evidence."""
    record = tmp_path / "DOCS" / "experiments" / analysis.RECORD_ROOT.name
    record.mkdir(parents=True)
    for missing in (
        analysis.MAIN_BASELINE,
        analysis.WGPU_EXTENSION_SHA256,
        analysis.CUDA_EXTENSION_SHA256,
    ):
        lines = [
            f"freeze `{analysis.FREEZE_COMMIT}`",
            f"R {analysis.EXECUTION_COMMIT}",
            f"M {analysis.MAIN_BASELINE}",
            analysis.WGPU_EXTENSION_SHA256,
            analysis.CUDA_EXTENSION_SHA256,
        ]
        text = "\n".join(line for line in lines if missing not in line)
        (record / "log.md").write_text(text + "\n", encoding="utf-8")
        with pytest.raises(analysis.AnalysisError, match="does not record"):
            analysis.verify_e3_log(tmp_path)


def test_verify_e3_log_refuses_a_missing_log(tmp_path):
    """No E3 log means no admissible analysis."""
    with pytest.raises(analysis.AnalysisError, match="unreadable"):
        analysis.verify_e3_log(tmp_path)


# --------------------------------------------------------------------------
# Write-destination containment and determinism
# --------------------------------------------------------------------------


def test_canonical_bytes_rejects_a_non_finite_number():
    """A NaN in an output would make the committed digest unreproducible."""
    with pytest.raises(analysis.AnalysisError, match="not finite JSON"):
        analysis._canonical_bytes({"value": float("nan")})


def test_canonical_bytes_is_key_order_independent():
    """Sorted keys make the digest independent of insertion order."""
    assert analysis._canonical_bytes({"a": 1, "b": 2}) == analysis._canonical_bytes(
        {"b": 2, "a": 1}
    )


def test_checked_destination_refuses_the_record_root_for_generated_outputs():
    """--output-dir may not write the four generated files into the record root."""
    roots = analysis.allowed_generated_output_dirs(_REPOSITORY_ROOT)
    record_root = (_REPOSITORY_ROOT / analysis.RECORD_ROOT).resolve()
    with pytest.raises(analysis.AnalysisError, match="outside the permitted"):
        analysis._checked_destination(record_root, roots, "output directory")
    with pytest.raises(analysis.AnalysisError, match="outside the permitted"):
        analysis._checked_destination(
            record_root / "analysis", roots, "output directory"
        )


def test_checked_manifest_destination_refuses_any_other_record_root_path():
    """Only report-manifest.json may be written inside the frozen record root."""
    roots = analysis.allowed_output_roots(_REPOSITORY_ROOT)
    record_root = (_REPOSITORY_ROOT / analysis.RECORD_ROOT).resolve()
    canonical = record_root / "report-manifest.json"
    assert analysis._checked_manifest_destination(canonical, roots, record_root) == (
        canonical
    )
    for name in ("preregistration.md", "log.md", "analysis/exp001_r1_e4_analysis.py"):
        with pytest.raises(analysis.AnalysisError, match="frozen record root"):
            analysis._checked_manifest_destination(
                record_root / name, roots, record_root
            )


def test_generated_output_dir_excludes_the_record_root():
    """--output-dir may not write the four generated files into the record root."""
    generated = analysis.allowed_generated_output_dirs(_REPOSITORY_ROOT)
    record_root = (_REPOSITORY_ROOT / analysis.RECORD_ROOT).resolve()
    assert record_root not in generated
    assert record_root in analysis.allowed_output_roots(_REPOSITORY_ROOT)


def test_main_rejects_a_manifest_path_colliding_with_a_generated_output():
    """A collision would leave the committed manifest describing stale bytes."""
    # tempfile, not pytest's tmp_path: under the repository's documented
    # --basetemp=.pytest_basetemp a pytest scratch directory lives inside the
    # checkout and is not one of the governed roots, so it would be refused for
    # the wrong reason.
    with tempfile.TemporaryDirectory() as raw:
        output_dir = Path(raw) / "out"
        output_dir.mkdir()
        for name in analysis.GENERATED_FILENAMES:
            with pytest.raises(analysis.AnalysisError, match="collides"):
                analysis.main(
                    [
                        "--output-dir",
                        str(output_dir),
                        "--manifest-path",
                        str(output_dir / name),
                    ]
                )


def test_render_and_histogram_row_are_deterministic():
    """Fixed-width scientific notation and a fixed bucket order."""
    assert analysis._render(1.5e-7) == "1.500000e-07"
    assert analysis._render(0.0) == "0"
    assert analysis._render(None) == "null"
    assert analysis._render("CONFIRMED") == "CONFIRMED"
    assert analysis._histogram_row({}) == "—"
    assert analysis._histogram_row({"0": 2, "1e-7": 1}) == "`0`=2, `1e-7`=1"


def test_decade_histogram_orders_zero_first_and_non_finite_last():
    """Exact decade counts, no estimator."""
    histogram = analysis._decade_histogram([0.0, 1e-7, 2e-7, 1e3, float("nan")])
    assert list(histogram) == ["0", "1e-7", "1e3", "non-finite"]
    assert histogram["1e-7"] == 2


def test_summary_rows_and_expected_table_are_reproducible():
    """Two calls over the same adjudications produce identical Markdown."""
    adjudications = {
        "H1": analysis.adjudicate_h1(_corpus_run(["native-parity"] * 504)),
        "H2a": analysis.adjudicate_h2a(_fuzz_run()),
        "H2b": analysis.adjudicate_h2b_leg(_run("r1-fuzz-cpu", _h2b_cases(40)), 40),
        "H3": analysis.adjudicate_h3(
            _repeatability_run("r1-repeatability-cpu"),
            _repeatability_run("r1-seedrep0-cpu"),
        ),
        "H4": analysis.adjudicate_h4(
            _kernel_run("r1-kernel-path-wgpu"), _kernel_run("r1-kernel-path-cuda")
        ),
    }
    first = analysis._summary_rows(adjudications)
    assert first == analysis._summary_rows(copy.deepcopy(adjudications))
    observed = analysis._expected_vs_observed_rows(adjudications)
    assert len(observed) == 5
    assert all(row.startswith("| H") for row in observed)
    assert analysis._h4_rows(adjudications["H4"])
    assert analysis._h2b_rows(adjudications["H2b"])
    assert analysis._breach_rows(adjudications) == []


def test_breach_rows_appear_only_for_a_refuted_hypothesis():
    """The breach breakdown is emitted exactly when a hypothesis is refuted."""
    refuted = analysis.adjudicate_h1(
        _corpus_run(["native-parity"] * 503 + ["unexplained-breach"])
    )
    lines = analysis._breach_rows({"H1": refuted})
    assert lines and "Breach breakdown" in lines[1]
    assert "1 failing case(s)" in "\n".join(lines)


def test_write_report_manifest_digests_the_bytes_it_was_given(tmp_path):
    """The manifest records the written digests, never a reopened path."""
    data = analysis._canonical_bytes({"value": 1})
    outputs = [
        analysis.GeneratedOutput(
            path=tmp_path / analysis.SUMMARY_JSON_FILENAME,
            size=len(data),
            sha256=hashlib.sha256(data).hexdigest(),
        )
    ]
    corpus = _corpus_run(["native-parity"] * 504)
    runs = {leg.label: corpus for leg in analysis.RUN_LEGS}
    adjudications = {"H1": {"verdict": "CONFIRMED"}}
    manifest_path = tmp_path / "report-manifest.json"
    payload = analysis.write_report_manifest(
        outputs, runs, manifest_path, analysis.GENERATED_AT, adjudications
    )
    written = json.loads(manifest_path.read_text(encoding="utf-8"))
    assert written == payload
    assert written["experiment"] == analysis.EXPERIMENT_ID
    assert written["session"] == analysis.SESSION
    assert written["d1_flag"] is False
    assert written["verdicts"] == {"H1": "CONFIRMED"}
    assert written["outputs"][0]["sha256"] == outputs[0].sha256
    assert written["outputs"][0]["bytes"] == len(data)
    assert len(written["inputs"]) == len(analysis.RUN_LEGS)
    assert written["execution_commit"] == analysis.EXECUTION_COMMIT
    assert written["main_baseline"] == analysis.MAIN_BASELINE


def test_error_stratum_sorts_descending_and_breaks_ties_by_case():
    """Sorted per-case/array maxima, as §8's output table requires."""
    entries = [
        ("b", _comparison("phase_traj", ok=True, abs_diff=1e-9, total=21)),
        ("a", _comparison("phase_traj", ok=True, abs_diff=1e-9, total=21)),
        ("a", _comparison("phase_init", ok=True, abs_diff=1e-3, total=8)),
    ]
    stratum = analysis._error_stratum("s", "p", "native", entries)
    assert [item["case"] for item in stratum["per_array_sorted"]] == ["a", "a", "b"]
    assert [item["array_name"] for item in stratum["per_array_sorted"]][:2] == [
        "phase_init",
        "phase_traj",
    ]
    assert stratum["max_abs_diff"] == 1e-3
    assert stratum["n_cases"] == 2


def test_case_comparison_record_retains_every_comparison_list():
    """§8's third output keeps native, corrected and sensitivity evidence."""
    case = _corpus_case("c", classification="ill-conditioned-characterization")
    record = analysis._case_comparison_record(case, "h2a-fuzz-characterized")
    assert record["population"] == "h2a-fuzz-characterized"
    assert record["comparisons"] == case["comparisons"]
    assert record["sensitivity_comparisons"] == case["sensitivity_comparisons"]
    assert record["classification"] == "ill-conditioned-characterization"
    assert record["accepted"] is None
