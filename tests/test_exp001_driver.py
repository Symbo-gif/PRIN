"""Tests for the EXP-001 campaign driver (tests in tandem, Coding Standards §5).

Covers the four comparisons the EXP-001 pre-registration names: corpus parity
(H1), hypothesis-fuzzed parity (H2), bit-level repeatability (H3), and the
GPU sparse-k-NN kernel-path comparison (H4), plus the campaign-metadata
sidecar and CLI wiring (campaign plan §7.2). H4's tests are ``skipif``-guarded
on ``prin._prin_core.GpuSparseKuramoto`` being present (a build-configuration
gate, not hardware — the extension must be built with ``--features cuda``),
mirroring ``tests/test_wp036d_gpu_dispatch.py``'s existing convention.
"""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pytest
from prin import _prin_core
from prin.dynamics import HopfOscillator, StuartLandauOscillator
from prin.parity.loader import CorpusLoader
from prin.parity.schema import CaseArrays, Coupling, Model

from benchmarks._common import result as result_module
from benchmarks.campaign import exp001_driver as driver

pytestmark = [pytest.mark.parity]

_CORPUS_DIR = Path(__file__).resolve().parents[1] / "parity" / "corpus"

# One representative case per (model, coupling) combination, reused from
# parity/test_parity_differential.py's representative subset.
_REPRESENTATIVE_CASES = [
    "kuramoto_mean_field_euler_n8_s20_dt0_005_K0_5_seed1000000",
    "kuramoto_full_rk4_n8_s20_dt0_005_K0_5_seed1300000",
    "hopf_sparse_knn_rk4_n8_s20_dt0_005_K0_5_seed2100000",
    "stuart_landau_full_euler_n8_s20_dt0_005_K0_5_seed2200000",
]

# GpuSparseKuramoto is only present when the extension is built with
# `--features cuda` (the maintainer host and the `[gpu]` CI leg); absent on
# the plain `python.yml` matrix. Same reference-guard class as
# test_wp036d_gpu_dispatch.py's `_needs_gpu_binding`.
_GPU_SPARSE_KNN_BUILT = hasattr(_prin_core, "GpuSparseKuramoto")
_needs_gpu_binding = pytest.mark.skipif(
    not _GPU_SPARSE_KNN_BUILT,
    reason=(
        "prin._prin_core.GpuSparseKuramoto absent "
        "(extension built without --features cuda)"
    ),
)

_KURAMOTO_SPARSE_KNN_CASES = [
    "kuramoto_sparse_knn_euler_n8_s20_dt0_005_K0_5_seed1400000",
    "kuramoto_sparse_knn_rk4_n24_s20_dt0_005_K1_seed1500030",
]


@pytest.fixture
def loader() -> CorpusLoader:
    """Load the real golden-trajectory corpus."""
    return CorpusLoader(_CORPUS_DIR)


class TestBuildPrinModel:
    """build_prin_model constructs the correct Rust-backed model class."""

    def test_kuramoto_mean_field(self) -> None:
        model = driver.build_prin_model(
            Model.KURAMOTO.value,
            Coupling.MEAN_FIELD.value,
            8,
            {"coupling_strength": 1.0, "decay_rate": 0.1, "freq_adaptation_rate": 0.01},
        )
        assert model.n_oscillators == 8
        assert model.coupling_strength == 1.0

    def test_hopf_full(self) -> None:
        model = driver.build_prin_model(
            Model.HOPF.value,
            Coupling.FULL.value,
            4,
            {
                "coupling_strength": 0.5,
                "bifurcation_param": 1.0,
                "freq_adaptation_rate": 0.0,
            },
        )
        assert isinstance(model, HopfOscillator)
        assert model.bifurcation_param == 1.0

    def test_stuart_landau(self) -> None:
        model = driver.build_prin_model(
            Model.STUART_LANDAU.value,
            Coupling.FULL.value,
            4,
            {"coupling_strength": 1.0, "bifurcation_param": 0.5},
        )
        assert isinstance(model, StuartLandauOscillator)
        assert model.bifurcation_param == 0.5

    def test_sparse_knn_requires_sparse_k(self) -> None:
        with pytest.raises(driver.DriverMetadataError):
            driver.build_prin_model(
                Model.KURAMOTO.value,
                Coupling.SPARSE_KNN.value,
                8,
                {
                    "coupling_strength": 1.0,
                    "decay_rate": 0.1,
                    "freq_adaptation_rate": 0.0,
                },
            )

    def test_unknown_model_raises(self) -> None:
        with pytest.raises(ValueError, match="unknown model"):
            driver.build_prin_model("nonexistent", Coupling.FULL.value, 4, {})


class TestCorpusParity:
    """H1: PRIN reproduces every representative golden-corpus case."""

    @pytest.mark.parametrize("case_id", _REPRESENTATIVE_CASES)
    def test_representative_cases_within_tolerance(
        self, loader: CorpusLoader, case_id: str
    ) -> None:
        record = driver.compare_corpus_case(loader, case_id)
        assert record["within_tolerance"] is True
        assert record["case_id"] == case_id
        assert len(record["comparisons"]) == len(CaseArrays._ARRAY_NAMES)

    def test_compare_corpus_subset_matches_individual_calls(
        self, loader: CorpusLoader
    ) -> None:
        subset = driver.compare_corpus_subset(loader, _REPRESENTATIVE_CASES)
        assert [r["case_id"] for r in subset] == _REPRESENTATIVE_CASES
        assert all(r["within_tolerance"] for r in subset)

    def test_unknown_case_id_raises(self, loader: CorpusLoader) -> None:
        from prin.parity.schema import CorpusValidationError

        with pytest.raises(CorpusValidationError):
            driver.compare_corpus_case(loader, "does-not-exist")


class TestRepeatability:
    """H3: two PRIN runs from the same stored initial state are bit-identical."""

    @pytest.mark.parametrize("case_id", _REPRESENTATIVE_CASES)
    def test_bit_identical_on_rerun(self, loader: CorpusLoader, case_id: str) -> None:
        record = driver.check_repeatability(loader, case_id)
        assert record["bit_identical"] is True
        assert record["mismatched_arrays"] == []


class TestFuzzSampler:
    """draw_fuzz_spec/draw_fuzz_initial produce valid, deterministic draws."""

    def test_deterministic_given_same_rng_state(self) -> None:
        rng1 = np.random.default_rng(42)
        rng2 = np.random.default_rng(42)
        assert driver.draw_fuzz_spec(rng1) == driver.draw_fuzz_spec(rng2)

    def test_stuart_landau_always_full_coupling(self) -> None:
        rng = np.random.default_rng(0)
        for _ in range(50):
            spec = driver.draw_fuzz_spec(rng)
            if spec["model"] == Model.STUART_LANDAU.value:
                assert spec["coupling"] == Coupling.FULL.value

    def test_sparse_knn_specs_carry_sparse_k(self) -> None:
        rng = np.random.default_rng(7)
        found_sparse = False
        for _ in range(200):
            spec = driver.draw_fuzz_spec(rng)
            if spec["coupling"] == Coupling.SPARSE_KNN.value:
                found_sparse = True
                assert "sparse_k" in spec["parameters"]
                assert 2 <= spec["parameters"]["sparse_k"] < spec["n_oscillators"]
        assert found_sparse, "expected at least one sparse_knn draw in 200 samples"

    def test_bounds(self) -> None:
        rng = np.random.default_rng(123)
        for _ in range(100):
            spec = driver.draw_fuzz_spec(rng)
            assert 8 <= spec["n_oscillators"] <= 64
            assert 5 <= spec["n_steps"] <= 50
            assert 0.001 <= spec["dt"] <= 0.05
            assert 0.1 <= spec["parameters"]["coupling_strength"] <= 4.0

    def test_draw_fuzz_initial_shapes(self) -> None:
        rng = np.random.default_rng(0)
        phase, amplitude, frequency = driver.draw_fuzz_initial(rng, 10)
        assert phase.shape == (10,)
        assert amplitude.shape == (10,)
        assert frequency.shape == (10,)
        assert np.all(amplitude > 0.0)


@pytest.mark.slow
class TestFuzzComparison:
    """H2: fuzzed cases run through both PRINet 3.0 and PRIN agree (mostly).

    Requires the archived PRINet 3.0.0 reference implementation, matching the
    existing convention in ``parity/test_parity_differential.py``.
    """

    def test_run_fuzz_batch_returns_structured_records(self) -> None:
        pytest.importorskip("prinet")
        records = driver.run_fuzz_batch(seed_counter=0, seed_key=1, n_cases=3)
        assert len(records) == 3
        for record in records:
            assert isinstance(record["within_tolerance"], bool)
            assert len(record["comparisons"]) == len(CaseArrays._ARRAY_NAMES)

    def test_run_fuzz_batch_deterministic(self) -> None:
        pytest.importorskip("prinet")
        first = driver.run_fuzz_batch(seed_counter=5, seed_key=1, n_cases=2)
        second = driver.run_fuzz_batch(seed_counter=5, seed_key=1, n_cases=2)
        assert [r["model"] for r in first] == [r["model"] for r in second]
        assert [r["within_tolerance"] for r in first] == [
            r["within_tolerance"] for r in second
        ]

    def test_fuzz_unavailable_without_prinet(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """compare_fuzz_case raises a clear abort when prinet is missing."""
        import builtins

        real_import = builtins.__import__

        def _blocked(name: str, *args: object, **kwargs: object) -> object:
            if name == "prinet" or name.startswith("prinet."):
                raise ImportError("blocked for test")
            return real_import(name, *args, **kwargs)  # type: ignore[arg-type]

        monkeypatch.setattr(builtins, "__import__", _blocked)
        rng = np.random.default_rng(0)
        spec = driver.draw_fuzz_spec(rng)
        spec["rng"] = rng
        with pytest.raises(driver.PrinetUnavailableError):
            driver.compare_fuzz_case(spec)


class TestKernelPath:
    """H4: the GPU sparse-k-NN derivative kernel agrees with the CPU reference."""

    @_needs_gpu_binding
    @pytest.mark.parametrize("case_id", _KURAMOTO_SPARSE_KNN_CASES)
    def test_representative_cases_within_tolerance(
        self, loader: CorpusLoader, case_id: str
    ) -> None:
        record = driver.compare_kernel_path_case(loader, case_id)
        assert record["within_tolerance"] is True
        assert record["case_id"] == case_id
        assert {c["array_name"] for c in record["comparisons"]} == {
            "dphase",
            "damplitude",
            "dfrequency",
        }

    @_needs_gpu_binding
    def test_all_sparse_knn_corpus_cases_pass(self, loader: CorpusLoader) -> None:
        """Exhaustive over the corpus's 72 kuramoto/sparse_knn cases (§5.1)."""
        case_ids = [
            record.case_id
            for record in loader.manifest.cases
            if record.model == Model.KURAMOTO.value
            and record.coupling == Coupling.SPARSE_KNN.value
        ]
        assert len(case_ids) == 72
        records = driver.compare_kernel_path_subset(loader, case_ids)
        assert all(r["within_tolerance"] for r in records)

    @_needs_gpu_binding
    def test_non_sparse_knn_case_raises(self, loader: CorpusLoader) -> None:
        with pytest.raises(ValueError, match="kuramoto/sparse_knn"):
            driver.compare_kernel_path_case(loader, _REPRESENTATIVE_CASES[0])

    def test_missing_binding_raises(
        self, loader: CorpusLoader, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """A build without the cuda feature aborts, not silently skips (§4 item 6)."""
        monkeypatch.delattr(_prin_core, "GpuSparseKuramoto", raising=False)
        with pytest.raises(driver.GpuBindingUnavailableError):
            driver.compare_kernel_path_case(loader, _KURAMOTO_SPARSE_KNN_CASES[0])


class TestCampaignMetadata:
    """write_campaign_metadata validates required fields and is append-only."""

    def test_missing_field_raises(self, tmp_path: Path) -> None:
        with pytest.raises(driver.DriverMetadataError):
            driver.write_campaign_metadata(
                tmp_path,
                exp_id="EXP-001",
                run_id="",
                session="0156",
                operator="tester",
                artefacts={},
            )

    def test_writes_expected_schema(self, tmp_path: Path) -> None:
        run_dir = tmp_path / "RUN-20260921T000000Z-abc1234-smoke"
        path = driver.write_campaign_metadata(
            run_dir,
            exp_id="EXP-001",
            run_id=run_dir.name,
            session="0156",
            operator="tester",
            artefacts={"corpus_smoke.json": ["H1"]},
        )
        payload = json.loads(path.read_text(encoding="utf-8"))
        assert payload == {
            "exp_id": "EXP-001",
            "run_id": run_dir.name,
            "session": "0156",
            "operator": "tester",
            "artefacts": {"corpus_smoke.json": ["H1"]},
        }

    def test_append_only(self, tmp_path: Path) -> None:
        run_dir = tmp_path / "RUN-race"
        driver.write_campaign_metadata(
            run_dir,
            exp_id="EXP-001",
            run_id="RUN-race",
            session="0156",
            operator="tester",
            artefacts={},
        )
        with pytest.raises(result_module.ArtefactExistsError):
            driver.write_campaign_metadata(
                run_dir,
                exp_id="EXP-001",
                run_id="RUN-race",
                session="0156",
                operator="tester",
                artefacts={"x": ["H1"]},
            )


class TestCli:
    """End-to-end CLI: metadata validation, artefact + sidecar writes."""

    def test_corpus_mode_writes_artefact_and_sidecar(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.setattr(result_module, "_ALLOWED_ROOTS", (tmp_path.resolve(),))
        run_dir = tmp_path / "RUN-20260921T000000Z-abc1234-smoke"
        case_id_flags = [
            flag for cid in _REPRESENTATIVE_CASES for flag in ("--case-id", cid)
        ]
        argv = [
            "--mode",
            "corpus",
            "--corpus-dir",
            str(_CORPUS_DIR),
            *case_id_flags,
            "--out",
            str(run_dir),
            "--label",
            "smoke",
            "--session",
            "0156",
            "--operator",
            "tester",
        ]
        assert driver.main(argv) == 0
        result_path = run_dir / "corpus_smoke.json"
        assert result_path.is_file()
        payload = json.loads(result_path.read_text(encoding="utf-8"))
        assert len(payload["cases"]) == len(_REPRESENTATIVE_CASES)
        assert payload["config"]["seed_key"] == 1
        sidecar = json.loads(
            (run_dir / "campaign-metadata.json").read_text(encoding="utf-8")
        )
        assert sidecar["exp_id"] == "EXP-001"
        assert sidecar["session"] == "0156"
        assert sidecar["artefacts"] == {"corpus_smoke.json": ["H1"]}

    def test_repeatability_mode_tags_artefact_h3(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Regression test: repeatability runs must tag H3, not H1 (§8)."""
        monkeypatch.setattr(result_module, "_ALLOWED_ROOTS", (tmp_path.resolve(),))
        run_dir = tmp_path / "RUN-repeatability-smoke"
        argv = [
            "--mode",
            "repeatability",
            "--corpus-dir",
            str(_CORPUS_DIR),
            "--case-id",
            _REPRESENTATIVE_CASES[0],
            "--out",
            str(run_dir),
            "--label",
            "smoke",
            "--session",
            "0156",
            "--operator",
            "tester",
        ]
        assert driver.main(argv) == 0
        sidecar = json.loads(
            (run_dir / "campaign-metadata.json").read_text(encoding="utf-8")
        )
        assert sidecar["artefacts"] == {"repeatability_smoke.json": ["H3"]}

    @_needs_gpu_binding
    def test_kernel_path_mode_writes_artefact_and_sidecar(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.setattr(result_module, "_ALLOWED_ROOTS", (tmp_path.resolve(),))
        run_dir = tmp_path / "RUN-kernel-path-smoke"
        case_id_flags = [
            flag for cid in _KURAMOTO_SPARSE_KNN_CASES for flag in ("--case-id", cid)
        ]
        argv = [
            "--mode",
            "kernel-path",
            "--corpus-dir",
            str(_CORPUS_DIR),
            *case_id_flags,
            "--out",
            str(run_dir),
            "--label",
            "smoke",
            "--session",
            "0156",
            "--operator",
            "tester",
        ]
        assert driver.main(argv) == 0
        result_path = run_dir / "kernel-path_smoke.json"
        payload = json.loads(result_path.read_text(encoding="utf-8"))
        assert len(payload["cases"]) == len(_KURAMOTO_SPARSE_KNN_CASES)
        assert payload["environment"]["backend"] == "cuda"
        assert payload["environment"]["dtype"] == "f32"
        assert all(c["within_tolerance"] for c in payload["cases"])
        sidecar = json.loads(
            (run_dir / "campaign-metadata.json").read_text(encoding="utf-8")
        )
        assert sidecar["artefacts"] == {"kernel-path_smoke.json": ["H4"]}

    def test_missing_operator_aborts_without_writing(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.setattr(result_module, "_ALLOWED_ROOTS", (tmp_path.resolve(),))
        run_dir = tmp_path / "RUN-abort"
        argv = [
            "--mode",
            "corpus",
            "--corpus-dir",
            str(_CORPUS_DIR),
            "--case-id",
            _REPRESENTATIVE_CASES[0],
            "--out",
            str(run_dir),
            "--label",
            "smoke",
            "--session",
            "0156",
            "--operator",
            "",
        ]
        assert driver.main(argv) == 2
        assert not run_dir.exists()

    def test_repeatability_mode_without_case_id_aborts(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.setattr(result_module, "_ALLOWED_ROOTS", (tmp_path.resolve(),))
        run_dir = tmp_path / "RUN-no-case"
        argv = [
            "--mode",
            "repeatability",
            "--corpus-dir",
            str(_CORPUS_DIR),
            "--out",
            str(run_dir),
            "--label",
            "smoke",
            "--session",
            "0156",
            "--operator",
            "tester",
        ]
        assert driver.main(argv) == 2
