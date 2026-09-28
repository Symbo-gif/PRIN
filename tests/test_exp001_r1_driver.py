"""Synthetic checks of the EXP-001-r1 protocol, never campaign observations.

Both oscillator implementations are replaced by explicit arrays. These tests
exercise the measurement and classification machinery without inspecting a
corpus or registered-fuzz outcome before E2 approval.
"""

from __future__ import annotations

import copy
import dataclasses
import hashlib
import json
import sys
from contextlib import nullcontext
from pathlib import Path
from types import ModuleType, SimpleNamespace
from typing import Any

import numpy as np
import pytest
from prin.parity.schema import CaseArrays, CaseSpec

from benchmarks._common import result as result_writer
from benchmarks.campaign import exp001_driver as legacy
from benchmarks.campaign import exp001_r1_driver as driver
from tools import reproduce


def _arrays(n_steps: int = 24) -> CaseArrays:
    """Build finite, bounded synthetic data with internally consistent endpoints."""
    values: dict[str, Any] = {}
    for name, value in (("phase", 1.0), ("amplitude", 1.0), ("frequency", 0.1)):
        values[f"{name}_init"] = np.full(8, value, dtype=np.float64)
        values[f"{name}_final"] = np.full(8, value, dtype=np.float64)
        values[f"{name}_traj"] = np.full((n_steps + 1, 8), value, dtype=np.float64)
    values["order_parameter_traj"] = np.full(n_steps + 1, 0.5, dtype=np.float64)
    values["mean_phase_coherence_traj"] = np.full(n_steps + 1, 0.1, dtype=np.float64)
    return CaseArrays(**values)


def _spec(coupling: str = "mean_field", n_steps: int = 24) -> dict[str, Any]:
    return {
        "model": "hopf",
        "coupling": coupling,
        "integrator": "rk4",
        "n_oscillators": 8,
        "n_steps": n_steps,
        "dt": 0.01,
        "parameters": {"coupling_strength": 0.5, "bifurcation_param": 1.0},
    }


def _loader(reference: CaseArrays, coupling: str = "mean_field") -> Any:
    spec = CaseSpec(case_id="synthetic", seed=0, **_spec(coupling, reference.n_steps))
    return SimpleNamespace(load=lambda _: SimpleNamespace(spec=spec, arrays=reference))


def _initial(arrays: CaseArrays) -> tuple[Any, Any, Any]:
    return arrays.phase_init, arrays.amplitude_init, arrays.frequency_init


def _phase_breach(arrays: CaseArrays, step: int = 1) -> CaseArrays:
    changed = copy.deepcopy(arrays)
    changed.phase_traj[step, 0] += 0.01
    return changed


@pytest.fixture
def synthetic_instrument(monkeypatch: pytest.MonkeyPatch) -> None:
    """Replace the reference instrument, without importing or executing PRINet."""
    monkeypatch.setattr(driver, "_float64_context", nullcontext)


@pytest.mark.parametrize("coupling", ["mean_field", "full"])
def test_native_corpus_pass_never_needs_an_explanation(
    monkeypatch: pytest.MonkeyPatch, coupling: str
) -> None:
    reference = _arrays()
    monkeypatch.setattr(legacy, "run_prin_case", lambda *_: reference)
    monkeypatch.setattr(
        legacy,
        "run_prinet_trajectory",
        lambda **_: pytest.fail("native parity must not need an exception"),
    )
    record = driver.compare_corpus_case(_loader(reference, coupling), "synthetic")
    assert record["accepted"] is True
    assert record["native_within_tolerance"] is True
    assert record["classification"] == "native-parity"
    assert record["f64_comparisons"] is None


@pytest.mark.usefixtures("synthetic_instrument")
@pytest.mark.parametrize("corrected_matches", [True, False])
def test_dv007_requires_positive_same_tolerance_float64_evidence(
    monkeypatch: pytest.MonkeyPatch, corrected_matches: bool
) -> None:
    native = _arrays()
    produced = _phase_breach(native)
    corrected = produced if corrected_matches else native
    monkeypatch.setattr(legacy, "run_prin_case", lambda *_: produced)
    monkeypatch.setattr(legacy, "run_prinet_trajectory", lambda **_: corrected)
    record = driver.compare_corpus_case(_loader(native), "synthetic")
    assert record["aborted"] is False
    assert record["native_within_tolerance"] is False
    assert record["accepted"] is corrected_matches
    assert any(not c["within_tolerance"] for c in record["comparisons"])
    assert all(c["within_tolerance"] for c in record["f64_comparisons"]) is (
        corrected_matches
    )


def test_off_path_breach_cannot_use_dv007(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    native = _arrays()
    monkeypatch.setattr(legacy, "run_prin_case", lambda *_: _phase_breach(native))
    monkeypatch.setattr(
        legacy, "run_prinet_trajectory", lambda **_: pytest.fail("off DV-007 path")
    )
    record = driver.compare_corpus_case(_loader(native, "full"), "synthetic")
    assert record["accepted"] is False
    assert record["classification"] == "unexplained-breach"


@pytest.mark.parametrize("problem", ["nan", "negative", "shape", "dtype"])
def test_invalid_output_is_aborted_instead_of_counted_as_a_pass(
    monkeypatch: pytest.MonkeyPatch, problem: str
) -> None:
    reference = _arrays()
    produced = copy.deepcopy(reference)
    if problem == "nan":
        produced.phase_traj[1, 0] = np.nan
    elif problem == "negative":
        produced.amplitude_traj[1, 0] = -1.0
    elif problem == "shape":
        produced = dataclasses.replace(produced, phase_traj=produced.phase_traj[:-1])
    else:
        produced = dataclasses.replace(
            produced, phase_traj=produced.phase_traj.astype(np.float32)
        )
    monkeypatch.setattr(legacy, "run_prin_case", lambda *_: produced)
    record = driver.compare_corpus_case(_loader(reference), "synthetic")
    assert record["aborted"] is True
    assert record["abort_reason"]
    assert "accepted" not in record


@pytest.mark.usefixtures("synthetic_instrument")
def test_invalid_corrected_reference_is_not_an_explained_divergence(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    native = _arrays()
    corrected = _phase_breach(native)
    corrected.order_parameter_traj[1] = 1.1
    monkeypatch.setattr(legacy, "run_prin_case", lambda *_: _phase_breach(native))
    monkeypatch.setattr(legacy, "run_prinet_trajectory", lambda **_: corrected)
    record = driver.compare_corpus_case(_loader(native), "synthetic")
    assert record["aborted"] is True
    assert "float64-reference" in record["abort_reason"]


def test_fuzz_horizon_keeps_post_horizon_metrics_but_not_pointwise_phase(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    reference = _arrays()
    produced = _phase_breach(reference, step=21)
    produced.order_parameter_traj[21:] += 0.002
    monkeypatch.setattr(legacy, "run_prinet_trajectory", lambda **_: reference)
    monkeypatch.setattr(legacy, "run_prin_trajectory", lambda **_: produced)
    record = driver.compare_fuzz_case(_spec("full"), _initial(reference), 0)
    assert record["accepted"] is True
    assert record["horizon"] == 20
    metric = record["beyond_horizon"]["order_parameter_traj"]
    assert metric["n_points"] == 4
    assert metric["mean_paired_difference"] == pytest.approx(0.002)
    assert record["parameters"] == _spec("full")["parameters"]
    assert len(record["input_sha256"]) == 64


@pytest.mark.usefixtures("synthetic_instrument")
@pytest.mark.parametrize("sensitive", [True, False])
def test_only_registered_cases_can_be_characterized_and_proof_is_repeated(
    monkeypatch: pytest.MonkeyPatch, sensitive: bool
) -> None:
    reference = _arrays()
    produced = _phase_breach(reference)
    calls: list[Any] = []

    def run_reference(**kwargs: Any) -> CaseArrays:
        calls.append(kwargs["phase_init"].copy())
        is_nudged = not np.array_equal(kwargs["phase_init"], reference.phase_init)
        return _phase_breach(reference) if is_nudged and sensitive else reference

    monkeypatch.setattr(legacy, "run_prinet_trajectory", run_reference)
    monkeypatch.setattr(legacy, "run_prin_trajectory", lambda **_: produced)
    record = driver.compare_fuzz_case(_spec("full"), _initial(reference), 50)
    assert np.array_equal(calls[-1], np.nextafter(reference.phase_init, np.inf))
    if sensitive:
        assert record["aborted"] is False
        assert record["pointwise_eligible"] is False
        assert record["accepted"] is None
        assert record["classification"] == "ill-conditioned-characterization"
        assert record["sensitivity_reproduced"] is True
        assert record["beyond_horizon"] is not None
        assert any(not c["within_tolerance"] for c in record["f64_comparisons"])
    else:
        assert record["aborted"] is True
        assert "sensitivity" in record["abort_reason"]


def test_unregistered_breach_never_becomes_a_new_exclusion(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    reference = _arrays()
    monkeypatch.setattr(legacy, "run_prinet_trajectory", lambda **_: reference)
    monkeypatch.setattr(
        legacy, "run_prin_trajectory", lambda **_: _phase_breach(reference)
    )
    record = driver.compare_fuzz_case(_spec("full"), _initial(reference), 51)
    assert record["pointwise_eligible"] is True
    assert record["accepted"] is False


def test_registered_stream_mismatch_aborts_before_any_integration(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    reference = _arrays()
    stream = [(_spec(), *_initial(reference))] * driver.N_FUZZ_CASES
    monkeypatch.setattr(driver, "_draw_stream", lambda: stream)
    monkeypatch.setattr(legacy, "h2a_stream_digest", lambda _: "0" * 64)
    monkeypatch.setattr(
        driver, "compare_fuzz_case", lambda *_: pytest.fail("must fail before outcomes")
    )
    with pytest.raises(legacy.DriverMetadataError, match="fingerprint"):
        driver.run_fuzz_batch()


def test_fuzz_batch_retains_all_cases_in_registered_order(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    reference = _arrays()
    stream = [(_spec(), *_initial(reference))] * driver.N_FUZZ_CASES
    monkeypatch.setattr(driver, "_draw_stream", lambda: stream)
    monkeypatch.setattr(legacy, "h2a_stream_digest", lambda _: driver.STREAM_SHA256)
    monkeypatch.setattr(
        driver, "compare_fuzz_case", lambda spec, initial, index: {"case_index": index}
    )
    cases = driver.run_fuzz_batch()
    assert [case["case_index"] for case in cases] == list(range(1000))


def test_repeatability_hashes_actual_arrays_and_detects_signed_zero(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    first = _arrays()
    second = copy.deepcopy(first)
    first.frequency_traj[1, 0] = 0.0
    second.frequency_traj[1, 0] = -0.0
    outputs = iter((first, second))
    monkeypatch.setattr(legacy, "run_prin_case", lambda *_: next(outputs))
    record = driver.check_repeatability(_loader(_arrays()), "synthetic")
    assert record["bit_identical"] is False
    assert record["mismatched_arrays"] == ["frequency_traj"]
    assert record["first_array_sha256"] != record["second_array_sha256"]


@pytest.mark.parametrize(
    ("lo", "hi", "expected"),
    [
        (-0.001, 0.001, "CONFIRMED"),
        (0.011, 0.012, "REFUTED"),
        (-0.012, -0.011, "REFUTED"),
        (0.005, 0.011, "INCONCLUSIVE"),
        (-0.011, 0.005, "INCONCLUSIVE"),
        (-0.01, 0.01, "INCONCLUSIVE"),
        (0.01, 0.012, "INCONCLUSIVE"),
    ],
)
def test_equivalence_distinguishes_refutation_from_insufficient_precision(
    monkeypatch: pytest.MonkeyPatch, lo: float, hi: float, expected: str
) -> None:
    summaries = [
        {
            "reference_mean": 0.5,
            "produced_mean": 0.501,
            "mean_paired_difference": 0.001,
        }
    ] * 30
    monkeypatch.setattr(legacy, "h2b_case_summaries", lambda *_: summaries)
    used: list[dict[str, Any]] = []

    def interval(values: Any, **kwargs: Any) -> dict[str, float]:
        used.append(kwargs)
        return {"mean": 0.001, "ci_lower": lo, "ci_upper": hi}

    monkeypatch.setattr(driver, "bootstrap_ci", interval)
    monkeypatch.setattr(driver, "cohens_d", lambda *_: 0.0)
    monkeypatch.setattr(driver, "welch_t_test", lambda *_: {"p_value": 1.0})
    result = driver.adjudicate_h2b_metric([], "order_parameter_traj")
    assert result["verdict"] == expected
    assert used == [{"n_bootstrap": 10000, "alpha": 0.05, "seed": 12455822396014146421}]


def test_statistical_abort_or_insufficient_information_cannot_confirm(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(legacy, "h2b_case_summaries", lambda *_: [])
    assert driver.adjudicate_h2b_metric([], "order_parameter_traj")["verdict"] == (
        "INCONCLUSIVE"
    )
    assert (
        driver.adjudicate_h2b_metric([{"aborted": True}], "order_parameter_traj")[
            "verdict"
        ]
        == "INCONCLUSIVE"
    )


@pytest.fixture
def publication(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> Path:
    """Exercise real publication and manifests with exclusively synthetic payloads."""
    monkeypatch.setattr(legacy, "_RUN_ROOT", tmp_path)
    monkeypatch.setattr(result_writer, "_ALLOWED_ROOTS", (tmp_path.resolve(),))
    environment = {field: "synthetic" for field in legacy._REQUIRED_ENV_FIELDS}
    environment.update(
        git_commit="0123456789abcdef0123456789abcdef01234567",
        backend="cpu",
        dtype="f64",
        seed=0,
        gpu="synthetic",
        gpu_vram_mb=1,
        logical_cpus=1,
    )
    monkeypatch.setattr(
        driver, "capture_environment", lambda **kwargs: {**environment, **kwargs}
    )
    monkeypatch.setattr(driver, "preflight", lambda *_: {"source": "synthetic"})
    return tmp_path


def _argv(root: Path, label: str = "r1-repeatability-cpu") -> list[str]:
    return [
        "--mode",
        "repeatability",
        "--out",
        str(root / f"RUN-20260928T010000Z-0123456-{label}"),
        "--label",
        label,
        "--session",
        "EXP-001-r1-E3",
        "--operator",
        "synthetic-test",
    ]


def test_cli_publishes_distinct_identity_without_mutating_old_runs(
    publication: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    cases = [{"case_id": cid, "aborted": False} for cid in driver.REPEATABILITY_CASES]
    monkeypatch.setattr(driver, "collect_cases", lambda *_: cases)
    # Manifest mechanics have their own tests; this test proves the call order.
    closed: list[str] = []
    monkeypatch.setattr(driver, "close_run", lambda *_: closed.append("closed"))
    args = _argv(publication)
    assert driver.main(args) == 0
    run_dir = Path(args[3])
    sidecar = json.loads((run_dir / "campaign-metadata.json").read_text())
    assert sidecar["exp_id"] == "EXP-001-r1"
    result = json.loads(
        (run_dir / "repeatability_r1-repeatability-cpu.json").read_text()
    )
    assert result["config"]["experiment_id"] == "EXP-001-r1"
    assert result["config"]["seed_key"] == 1
    assert closed == ["closed"]
    before = (run_dir / "campaign-metadata.json").read_bytes()
    assert driver.main(args) == 2
    assert (run_dir / "campaign-metadata.json").read_bytes() == before


def test_cli_retains_aborted_case_evidence_and_returns_failure(
    publication: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    monkeypatch.setattr(reproduce, "ALLOWED_MANIFEST_ROOTS", (publication.resolve(),))
    cases = [{"case_id": cid, "aborted": False} for cid in driver.REPEATABILITY_CASES]
    cases[0].update(aborted=True, abort_reason="synthetic invalid amplitude")
    monkeypatch.setattr(driver, "collect_cases", lambda *_: cases)
    args = _argv(publication)
    assert driver.main(args) == 2
    run_dir = Path(args[3])
    assert (run_dir / "campaign-metadata.json").is_file()
    assert (run_dir / "manifest.json").is_file()
    result = json.loads(
        (run_dir / "repeatability_r1-repeatability-cpu.json").read_text()
    )
    assert len(result["cases"]) == 14
    assert result["cases"][0]["abort_reason"] == "synthetic invalid amplitude"
    assert "ABORT: 1 registered case(s) aborted" in capsys.readouterr().err


@pytest.mark.parametrize(
    "field,value", [("--session", "0156"), ("--label", "corpus-cpu")]
)
def test_cli_rejects_predecessor_metadata_before_running(
    publication: Path,
    monkeypatch: pytest.MonkeyPatch,
    field: str,
    value: str,
) -> None:
    monkeypatch.setattr(driver, "collect_cases", lambda *_: pytest.fail("must not run"))
    args = _argv(publication)
    args[args.index(field) + 1] = value
    assert driver.main(args) == 2
    assert not list(publication.iterdir())


@pytest.fixture
def preflight_inputs(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    """Stub the input inventory and modules; keep actual hash/AST gates live."""
    manifest = tmp_path / "manifest.json"
    source = tmp_path / "reference.py"
    instrument_path = tmp_path / "instrument.py"
    extension = tmp_path / "extension.bin"
    for path in (manifest, source, instrument_path, extension):
        path.write_bytes(path.name.encode())
    monkeypatch.setattr(
        driver, "CORPUS_SHA256", hashlib.sha256(manifest.read_bytes()).hexdigest()
    )
    monkeypatch.setattr(
        driver,
        "REFERENCE_SOURCE_SHA256",
        hashlib.sha256(source.read_bytes()).hexdigest(),
    )
    monkeypatch.setattr(
        driver,
        "INSTRUMENT_SHA256",
        hashlib.sha256(instrument_path.read_bytes()).hexdigest(),
    )
    monkeypatch.setattr(driver, "CorpusLoader", lambda _: list(range(504)))
    monkeypatch.setattr(
        driver, "EulerIntegrator", lambda: SimpleNamespace(guard="non_negative")
    )
    monkeypatch.setattr(
        driver, "RK4Integrator", lambda: SimpleNamespace(guard="non_negative")
    )
    monkeypatch.setattr(driver, "_prin_core", SimpleNamespace(__file__=str(extension)))
    monkeypatch.setattr(
        legacy, "prinet_reference_provenance", lambda: {"prinet_version": "3.0.0"}
    )
    reference_module = ModuleType("prinet.core.propagation.oscillator_models")
    reference_module.__file__ = str(source)
    propagation = ModuleType("prinet.core.propagation")
    propagation.oscillator_models = reference_module
    for name in ("prinet", "prinet.core"):
        monkeypatch.setitem(sys.modules, name, ModuleType(name))
    monkeypatch.setitem(sys.modules, "prinet.core.propagation", propagation)
    measurement = ModuleType("parity.prinet_f64")
    measurement.__file__ = str(instrument_path)
    measurement.assert_replacements_match_reference = lambda: None
    measurement.f64_corrected_reference = nullcontext
    import parity

    monkeypatch.setattr(parity, "prinet_f64", measurement, raising=False)
    monkeypatch.setitem(sys.modules, "parity.prinet_f64", measurement)
    return tmp_path


def test_preflight_pins_inputs_and_instrument_without_outcome_execution(
    preflight_inputs: Path,
) -> None:
    metadata = driver.preflight("fuzz", preflight_inputs)
    assert metadata["stream_sha256"] == driver.STREAM_SHA256
    assert metadata["guard_policy"] == "non_negative"
    assert metadata["reference_source_sha256"] == driver.REFERENCE_SOURCE_SHA256
    assert len(metadata["prin_extension_sha256"]) == 64
    with driver._float64_context() as value:
        assert value is None


@pytest.mark.parametrize(
    "failure", ["manifest", "population", "guard", "reference", "instrument", "ast"]
)
def test_preflight_fails_closed_on_each_input_control(
    preflight_inputs: Path, monkeypatch: pytest.MonkeyPatch, failure: str
) -> None:
    if failure == "manifest":
        (preflight_inputs / "manifest.json").write_bytes(b"changed")
    elif failure == "population":
        monkeypatch.setattr(driver, "CorpusLoader", lambda _: [])
    elif failure == "guard":
        monkeypatch.setattr(
            driver, "RK4Integrator", lambda: SimpleNamespace(guard="bounded")
        )
    elif failure in ("reference", "instrument"):
        (preflight_inputs / f"{failure}.py").write_bytes(b"changed")
    else:
        import parity.prinet_f64 as instrument

        def drift() -> None:
            raise AssertionError("changed non-cast arithmetic")

        monkeypatch.setattr(instrument, "assert_replacements_match_reference", drift)
    with pytest.raises(legacy.DriverMetadataError):
        driver.preflight("corpus", preflight_inputs)


def test_draw_stream_uses_one_registered_seed_and_alternating_draws(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    seed = object()
    calls: list[Any] = []

    def make_seed(counter: int, key: int) -> Any:
        calls.append((counter, key))
        return seed

    def draw_spec(actual: Any) -> dict[str, Any]:
        assert actual is seed
        calls.append("spec")
        return _spec()

    def draw_initial(actual: Any, n: int) -> Any:
        assert actual is seed and n == 8
        calls.append("initial")
        return _initial(_arrays())

    monkeypatch.setattr(driver, "_prin_core", SimpleNamespace(Seed=make_seed))
    monkeypatch.setattr(legacy, "draw_fuzz_spec", draw_spec)
    monkeypatch.setattr(legacy, "draw_fuzz_initial", draw_initial)
    stream = driver._draw_stream()
    assert len(stream) == 1000
    assert calls == [(0, 1)] + ["spec", "initial"] * 1000


@pytest.mark.parametrize("mode", ["corpus", "repeatability", "fuzz", "kernel-path"])
def test_leg_dispatch_keeps_registered_selections(
    monkeypatch: pytest.MonkeyPatch, mode: str
) -> None:
    rows = [
        SimpleNamespace(case_id="sparse", model="kuramoto", coupling="sparse_knn"),
        SimpleNamespace(case_id="dense", model="hopf", coupling="full"),
    ]
    inventory = SimpleNamespace(manifest=SimpleNamespace(cases=rows))
    monkeypatch.setattr(driver, "CorpusLoader", lambda _: inventory)
    monkeypatch.setattr(driver, "compare_corpus_case", lambda _, cid: {"case_id": cid})
    monkeypatch.setattr(driver, "check_repeatability", lambda _, cid: {"case_id": cid})
    monkeypatch.setattr(driver, "run_fuzz_batch", lambda: [{"case_index": 0}])
    monkeypatch.setattr(
        legacy,
        "compare_kernel_path_subset",
        lambda _, ids: [{"case_id": cid} for cid in ids],
    )
    cases = driver.collect_cases(mode, Path("unused"))
    expected = {
        "corpus": ["sparse", "dense"],
        "repeatability": list(driver.REPEATABILITY_CASES),
        "fuzz": [0],
        "kernel-path": ["sparse"],
    }[mode]
    assert [case.get("case_id", case.get("case_index")) for case in cases] == expected
    with pytest.raises(legacy.DriverMetadataError, match="unregistered mode"):
        driver.collect_cases("invented", Path("unused"))


def test_repeatability_aborts_an_invalid_member(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    bad = _arrays()
    bad.amplitude_traj[1, 0] = -1.0
    monkeypatch.setattr(legacy, "run_prin_case", lambda *_: bad)
    record = driver.check_repeatability(_loader(_arrays()), "synthetic")
    assert record["aborted"] is True
    assert "bit_identical" not in record


@pytest.mark.parametrize("name", ["phase_init", "phase_final"])
def test_endpoint_phase_guards_are_checked(name: str) -> None:
    bad = _arrays()
    getattr(bad, name)[0] = -0.1
    assert driver._array_violation("produced", _spec(), bad) is not None


@pytest.mark.parametrize(
    ("verdicts", "expected"),
    [
        (["CONFIRMED", "CONFIRMED"], "CONFIRMED"),
        (["CONFIRMED", "REFUTED"], "REFUTED"),
        (["CONFIRMED", "INCONCLUSIVE"], "INCONCLUSIVE"),
    ],
)
def test_h2b_metrics_cannot_cancel_or_hide_an_inconclusive_leg(
    monkeypatch: pytest.MonkeyPatch, verdicts: list[str], expected: str
) -> None:
    values = iter(verdicts)
    monkeypatch.setattr(
        driver, "adjudicate_h2b_metric", lambda *_: {"verdict": next(values)}
    )
    assert driver.adjudicate_h2b([])["verdict"] == expected


@pytest.mark.parametrize(
    "bad_interval",
    [
        {"mean": float("nan"), "ci_lower": 0.0, "ci_upper": 0.01},
        {"mean": 0.0, "ci_lower": 0.02, "ci_upper": 0.01},
    ],
)
def test_invalid_statistical_interval_aborts(
    monkeypatch: pytest.MonkeyPatch, bad_interval: dict[str, float]
) -> None:
    rows = [
        {"reference_mean": 0.5, "produced_mean": 0.5, "mean_paired_difference": 0.0}
    ] * 30
    monkeypatch.setattr(legacy, "h2b_case_summaries", lambda *_: rows)
    monkeypatch.setattr(driver, "bootstrap_ci", lambda *_, **__: bad_interval)
    with pytest.raises(legacy.DriverError, match="invalid bootstrap interval"):
        driver.adjudicate_h2b_metric([], "order_parameter_traj")


def test_storage_caps_include_predecessor_files_and_reject_nonfinite_json(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    root = tmp_path / "EXP-001"
    root.mkdir()
    previous = root / "RUN-old"
    previous.mkdir()
    evidence = previous / "original.json"
    evidence.write_bytes(b"original")
    run_dir = root / "RUN-new"
    driver._storage_check(run_dir, {}, {})
    with pytest.raises(legacy.DriverMetadataError, match="finite JSON"):
        driver._storage_check(run_dir, {"value": float("nan")}, {})
    for limit in ("RUN_CAP_BYTES", "RAW_ROOT_CAP_BYTES", "CAMPAIGN_CAP_BYTES"):
        with monkeypatch.context() as patch:
            patch.setattr(driver, limit, 1)
            with pytest.raises(legacy.DriverMetadataError, match="storage cap"):
                driver._storage_check(run_dir, {}, {})
    assert evidence.read_bytes() == b"original"


def test_fuzz_leg_gets_the_approved_wider_per_run_cap(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Campaign plan §14.2 amendment #7: fuzz keeps its own 6 MiB run cap."""
    root = tmp_path / "EXP-001"
    root.mkdir()
    run_dir = root / "RUN-new-r1-fuzz-cpu"
    monkeypatch.setattr(driver, "RUN_CAP_BYTES", 1000)
    payload = {"value": "x" * 200}
    # The manifest reserve alone (64 KiB) already exceeds the patched generic
    # cap, so this payload only fits under the fuzz-specific 6 MiB exception.
    driver._storage_check(run_dir, payload, {}, mode="fuzz")
    with pytest.raises(legacy.DriverMetadataError, match="storage cap"):
        driver._storage_check(run_dir, payload, {}, mode="corpus")


def test_r1_subtree_cap_is_independent_of_the_shared_root_cap(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Campaign plan §14.2 amendment #7: the new 8 MiB r1 sub-allocation is
    checked only against ``RUN-*-r1-*`` directories, separately from the
    16 MiB shared-root cap that also covers the original EXP-001 runs."""
    root = tmp_path / "EXP-001"
    root.mkdir()
    original = root / "RUN-old-corpus-cpu"
    original.mkdir()
    (original / "original.json").write_bytes(b"0" * 100)
    prior_r1 = root / "RUN-prior-r1-corpus-cpu"
    prior_r1.mkdir()
    (prior_r1 / "prior.json").write_bytes(b"0" * 100)
    monkeypatch.setattr(driver, "R1_ROOT_CAP_BYTES", 150)
    with pytest.raises(legacy.DriverMetadataError, match="storage cap"):
        driver._storage_check(root / "RUN-new-r1-fuzz-cpu", {}, {}, mode="fuzz")
    # A non-r1 run directory of an equivalent size is unaffected by the r1 cap.
    driver._storage_check(root / "RUN-new-corpus-cpu", {}, {}, mode="corpus")


@pytest.mark.parametrize("failure", ["operator", "sha", "count", "write"])
def test_cli_operational_failures_never_publish_accepted_evidence(
    publication: Path, monkeypatch: pytest.MonkeyPatch, failure: str
) -> None:
    args = _argv(publication)
    cases = [{"case_id": cid, "aborted": False} for cid in driver.REPEATABILITY_CASES]
    monkeypatch.setattr(
        driver, "collect_cases", lambda *_: [] if failure == "count" else cases
    )
    monkeypatch.setattr(driver, "close_run", lambda *_: pytest.fail("must not close"))
    if failure == "operator":
        args[args.index("--operator") + 1] = " "
    elif failure == "sha":
        args[3] = args[3].replace("0123456", "9999999")
    elif failure == "write":

        def lost_write(*args: Any, **kwargs: Any) -> Any:
            raise result_writer.ArtefactExistsError("synthetic write conflict")

        monkeypatch.setattr(driver, "write_result", lost_write)
    assert driver.main(args) == 2
    assert not list(publication.rglob("campaign-metadata.json"))


def test_cuda_metadata_is_explicit_and_untimed(
    publication: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    args = _argv(publication, "r1-kernel-path-cuda")
    args[1] = "kernel-path"
    monkeypatch.setattr(
        driver,
        "collect_cases",
        lambda *_: [{"case_id": str(i), "aborted": False} for i in range(72)],
    )
    monkeypatch.setattr(driver, "close_run", lambda *_: None)
    assert driver.main(args) == 0
    run_dir = Path(args[3])
    metadata = json.loads((run_dir / "campaign-metadata.json").read_text())
    entry = metadata["artefacts"]["kernel-path_r1-kernel-path-cuda.json"]
    assert entry == {"hypotheses": ["H4"], "timing_method": "not-timed"}


def test_closure_invokes_identity_gate_then_manifest_then_verification(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    calls: list[str] = []

    def closure(path: Path, *, expected_exp_id: str) -> dict[str, list[str]]:
        assert path == tmp_path and expected_exp_id == "EXP-001-r1"
        calls.append("closure")
        return {}

    def append(**kwargs: Any) -> None:
        assert kwargs == {
            "results_dir": tmp_path,
            "manifest_path": tmp_path / "manifest.json",
        }
        calls.append("manifest")

    def verify(**kwargs: Any) -> None:
        assert kwargs == {
            "results_dir": tmp_path,
            "manifest_path": tmp_path / "manifest.json",
        }
        calls.append("verify")

    monkeypatch.setattr(legacy, "check_run_complete", closure)
    monkeypatch.setattr(reproduce, "append_manifest", append)
    monkeypatch.setattr(reproduce, "verify_manifest", verify)
    driver.close_run(tmp_path)
    assert calls == ["closure", "manifest", "verify"]
