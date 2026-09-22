"""Tests for the EXP-001 campaign driver (tests in tandem, Coding Standards §5).

Covers the four comparisons the EXP-001 pre-registration names: corpus parity
(H1), hypothesis-fuzzed parity (H2), bit-level repeatability (H3), and the
GPU sparse-k-NN kernel-path comparison (H4), plus the campaign-metadata
sidecar and CLI wiring (campaign plan §7.2). H4's tests are ``skipif``-guarded:
``_needs_gpu_binding`` (mirroring ``tests/test_wp036d_gpu_dispatch.py``'s
existing convention) for tests that only need
``prin._prin_core.GpuSparseKuramoto`` present (a build-configuration gate),
and ``_needs_gpu_execution`` (additionally requiring
``torch.cuda.is_available()``) for tests that actually call
``compare_kernel_path_case`` expecting it to run — since that function also
requires a live CUDA device (§5.5 remediation: the binding alone compiles
under ``--features wgpu`` too), a binding-only guard would let those tests
run-and-fail rather than skip on a hypothetical wgpu-only build.
"""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pytest
import torch
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
# `--features cuda` or `--features wgpu` (the maintainer host and the `[gpu]`
# CI leg); absent on the plain `python.yml` matrix. Same reference-guard class
# as test_wp036d_gpu_dispatch.py's `_needs_gpu_binding`.
_GPU_SPARSE_KNN_BUILT = hasattr(_prin_core, "GpuSparseKuramoto")
_needs_gpu_binding = pytest.mark.skipif(
    not _GPU_SPARSE_KNN_BUILT,
    reason=(
        "prin._prin_core.GpuSparseKuramoto absent "
        "(extension built without --features cuda/--features wgpu)"
    ),
)

# compare_kernel_path_case additionally requires a live CUDA device (§5.5):
# the binding alone can't distinguish a wgpu-only build from a cuda build, so
# it aborts unless torch.cuda.is_available(). Tests that actually execute it
# expecting success need this stronger guard, not just binding presence,
# or they would run-and-fail (instead of skip) on a hypothetical
# --features wgpu-only build.
_needs_gpu_execution = pytest.mark.skipif(
    not (_GPU_SPARSE_KNN_BUILT and torch.cuda.is_available()),
    reason=(
        "H4 kernel-path execution requires both prin._prin_core."
        "GpuSparseKuramoto and a live CUDA device (torch.cuda.is_available())"
    ),
)

_KURAMOTO_SPARSE_KNN_CASES = [
    "kuramoto_sparse_knn_euler_n8_s20_dt0_005_K0_5_seed1400000",
    "kuramoto_sparse_knn_rk4_n24_s20_dt0_005_K1_seed1500030",
]


def _probe_symlink_support() -> bool:
    """True iff this process can create a symlink in a temp directory.

    Symlink creation requires elevated privilege or Developer Mode on
    Windows (unlike GitHub-hosted `windows-latest` runners, which run as
    Administrator, an arbitrary local or self-hosted Windows environment may
    not), so the regression test for the symlinked-artefact rejection
    (§5.10 remediation) is gated on this rather than assumed available.
    """
    import tempfile

    with tempfile.TemporaryDirectory() as raw:
        d = Path(raw)
        target = d / "target"
        target.write_text("x", encoding="utf-8")
        link = d / "link"
        try:
            link.symlink_to(target)
        except OSError:
            return False
        return True


_needs_symlink_support = pytest.mark.skipif(
    not _probe_symlink_support(),
    reason="creating symlinks is not permitted in this environment",
)


@pytest.fixture
def loader() -> CorpusLoader:
    """Load the real golden-trajectory corpus."""
    return CorpusLoader(_CORPUS_DIR)


@pytest.fixture
def run_root(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    """Point both write gates at a temp directory for CLI tests.

    ``benchmarks._common.result._ALLOWED_ROOTS`` confines where any artefact
    may be written; ``exp001_driver._RUN_ROOT`` is the campaign plan §7.1
    raw-artefact root every run directory must be a direct child of. Both are
    narrowed to ``tmp_path`` so the CLI's real contract checks still run,
    just against a scratch root. Test run directories must still use the
    canonical ``RUN-<UTC>-<SHA>-<label>`` name (see :func:`_run_dir`).
    """
    root = tmp_path.resolve()
    monkeypatch.setattr(result_module, "_ALLOWED_ROOTS", (root,))
    monkeypatch.setattr(driver, "_RUN_ROOT", root)
    return root


def _run_dir(root: Path, label: str) -> Path:
    """A canonically named, not-yet-created run directory under ``root``."""
    return root / f"RUN-20260921T000000Z-abc1234-{label}"


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
        assert record["aborted"] is False
        assert record["within_tolerance"] is True
        assert record["case_id"] == case_id
        assert len(record["comparisons"]) == len(CaseArrays._ARRAY_NAMES)

    def test_compare_corpus_subset_matches_individual_calls(
        self, loader: CorpusLoader
    ) -> None:
        subset = driver.compare_corpus_subset(loader, _REPRESENTATIVE_CASES)
        assert [r["case_id"] for r in subset] == _REPRESENTATIVE_CASES
        assert all(r["aborted"] is False for r in subset)
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
        assert record["aborted"] is False
        assert record["bit_identical"] is True
        assert record["mismatched_arrays"] == []


def _make_case_arrays(
    *,
    n: int = 4,
    steps: int = 3,
    phase_traj: np.ndarray | None = None,
    order_parameter_traj: np.ndarray | None = None,
    mean_phase_coherence_traj: np.ndarray | None = None,
) -> CaseArrays:
    """Build a minimal, otherwise-clean :class:`CaseArrays` for hazard tests."""
    zeros_n = np.zeros(n, dtype=np.float64)
    ones_n = np.ones(n, dtype=np.float64)
    zeros_traj = np.zeros((steps + 1, n), dtype=np.float64)
    zeros_scalar = np.zeros(steps + 1, dtype=np.float64)
    return CaseArrays(
        phase_init=zeros_n.copy(),
        amplitude_init=ones_n.copy(),
        frequency_init=zeros_n.copy(),
        phase_final=zeros_n.copy(),
        amplitude_final=ones_n.copy(),
        frequency_final=zeros_n.copy(),
        phase_traj=zeros_traj.copy() if phase_traj is None else phase_traj,
        amplitude_traj=np.ones((steps + 1, n), dtype=np.float64),
        frequency_traj=zeros_traj.copy(),
        order_parameter_traj=(
            zeros_scalar.copy()
            if order_parameter_traj is None
            else order_parameter_traj
        ),
        mean_phase_coherence_traj=(
            zeros_scalar.copy()
            if mean_phase_coherence_traj is None
            else mean_phase_coherence_traj
        ),
    )


class TestHazardEnvelope:
    """_case_arrays_hazard_violation/_finite_violation detect registered breaches."""

    def test_clean_arrays_pass(self) -> None:
        assert (
            driver._case_arrays_hazard_violation("produced", _make_case_arrays())
            is None
        )

    def test_nan_detected(self) -> None:
        bad = _make_case_arrays(phase_traj=np.full((4, 4), np.nan))
        violation = driver._case_arrays_hazard_violation("produced", bad)
        assert violation is not None
        assert "non-finite" in violation
        assert "phase_traj" in violation

    def test_inf_detected(self) -> None:
        traj = np.zeros((4, 4))
        traj[0, 0] = np.inf
        violation = driver._case_arrays_hazard_violation(
            "produced", _make_case_arrays(phase_traj=traj)
        )
        assert violation is not None and "non-finite" in violation

    def test_order_parameter_above_one_detected(self) -> None:
        bad = _make_case_arrays(order_parameter_traj=np.array([0.5, 1.5, 0.9, 0.1]))
        violation = driver._case_arrays_hazard_violation("produced", bad)
        assert violation is not None
        assert "order_parameter_traj" in violation
        assert "[0, 1]" in violation

    def test_order_parameter_negative_detected(self) -> None:
        bad = _make_case_arrays(order_parameter_traj=np.array([0.5, -0.1, 0.9, 0.1]))
        violation = driver._case_arrays_hazard_violation("produced", bad)
        assert violation is not None and "order_parameter_traj" in violation

    def test_mean_phase_coherence_allows_negative(self) -> None:
        """mean_phase_coherence's true range is [-1, 1], not [0, 1] (a mean
        pairwise cosine, `crates/prin-metrics/src/coherence.rs`) — a negative
        value alone must not trip the hazard guard."""
        ok = _make_case_arrays(
            mean_phase_coherence_traj=np.array([-0.9, -0.5, 0.0, 0.3])
        )
        assert driver._case_arrays_hazard_violation("produced", ok) is None

    def test_mean_phase_coherence_below_negative_one_detected(self) -> None:
        bad = _make_case_arrays(
            mean_phase_coherence_traj=np.array([-1.5, 0.0, 0.0, 0.0])
        )
        violation = driver._case_arrays_hazard_violation("produced", bad)
        assert violation is not None
        assert "mean_phase_coherence_traj" in violation
        assert "[-1, 1]" in violation

    def test_mean_phase_coherence_above_one_detected(self) -> None:
        bad = _make_case_arrays(
            mean_phase_coherence_traj=np.array([1.5, 0.0, 0.0, 0.0])
        )
        violation = driver._case_arrays_hazard_violation("produced", bad)
        assert violation is not None and "mean_phase_coherence_traj" in violation

    def test_phase_outside_wrapped_range_detected(self) -> None:
        traj = np.zeros((4, 4))
        traj[0, 0] = 7.0  # > 2*pi
        violation = driver._case_arrays_hazard_violation(
            "produced", _make_case_arrays(phase_traj=traj)
        )
        assert violation is not None
        assert "phase_traj" in violation
        assert "wrapped" in violation

    def test_negative_phase_detected(self) -> None:
        traj = np.zeros((4, 4))
        traj[0, 0] = -0.1
        violation = driver._case_arrays_hazard_violation(
            "produced", _make_case_arrays(phase_traj=traj)
        )
        assert violation is not None and "wrapped" in violation

    def test_label_is_included(self) -> None:
        bad = _make_case_arrays(phase_traj=np.full((4, 4), np.nan))
        violation = driver._case_arrays_hazard_violation("reference", bad)
        assert violation is not None and violation.startswith("reference:")

    def test_finite_violation_clean(self) -> None:
        assert driver._finite_violation("cpu", "dphase", np.array([0.1, 0.2])) is None

    def test_finite_violation_detects_nan(self) -> None:
        violation = driver._finite_violation("gpu", "dphase", np.array([0.1, np.nan]))
        assert violation is not None
        assert "gpu" in violation
        assert "dphase" in violation


class TestBitIdentical:
    """_bit_identical is stricter than numpy.array_equal (dtype + raw bytes)."""

    def test_identical_arrays(self) -> None:
        a = np.array([1.0, 2.0, 3.0])
        assert driver._bit_identical(a, a.copy()) is True

    def test_different_values(self) -> None:
        a = np.array([1.0, 2.0, 3.0])
        b = np.array([1.0, 2.0, 3.0000001])
        assert driver._bit_identical(a, b) is False

    def test_different_dtype_same_values(self) -> None:
        a = np.array([1.0, 2.0], dtype=np.float64)
        b = np.array([1.0, 2.0], dtype=np.float32)
        assert driver._bit_identical(a, b) is False

    def test_different_shape(self) -> None:
        a = np.array([1.0, 2.0])
        b = np.array([[1.0, 2.0]])
        assert driver._bit_identical(a, b) is False


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

    #: 3 init + 5 trajectory-shaped arrays — H2a excludes the 3 ``_final``
    #: arrays (redundant within the horizon, out of scope beyond it; see
    #: compare_fuzz_case's docstring).
    _H2A_ARRAY_COUNT = 8

    def test_run_fuzz_batch_returns_structured_records(self) -> None:
        pytest.importorskip("prinet")
        records = driver.run_fuzz_batch(seed_counter=0, seed_key=1, n_cases=3)
        assert len(records) == 3
        for record in records:
            assert record["aborted"] is False
            assert isinstance(record["within_tolerance"], bool)
            assert len(record["comparisons"]) == self._H2A_ARRAY_COUNT
            assert record["horizon"] == min(driver.T_STAR, record["n_steps"])

    def test_run_fuzz_batch_deterministic(self) -> None:
        pytest.importorskip("prinet")
        first = driver.run_fuzz_batch(seed_counter=5, seed_key=1, n_cases=2)
        second = driver.run_fuzz_batch(seed_counter=5, seed_key=1, n_cases=2)
        assert [r["model"] for r in first] == [r["model"] for r in second]
        assert [r["within_tolerance"] for r in first] == [
            r["within_tolerance"] for r in second
        ]

    def test_beyond_horizon_present_only_when_n_steps_exceeds_t_star(self) -> None:
        """H2b's raw pairs are recorded iff n_steps > T_STAR (preregistration §2)."""
        pytest.importorskip("prinet")
        rng = np.random.default_rng(3)
        short_spec = {
            "model": Model.KURAMOTO.value,
            "coupling": Coupling.MEAN_FIELD.value,
            "integrator": "euler",
            "n_oscillators": 8,
            "n_steps": driver.T_STAR,
            "dt": 0.01,
            "seed": 1,
            "parameters": {
                "coupling_strength": 1.0,
                "decay_rate": 0.1,
                "freq_adaptation_rate": 0.0,
            },
            "rng": rng,
        }
        short_record = driver.compare_fuzz_case(short_spec)
        assert short_record["aborted"] is False
        assert short_record["horizon"] == driver.T_STAR
        assert short_record["beyond_horizon"] is None

        long_spec = {**short_spec, "n_steps": driver.T_STAR + 10, "seed": 2}
        long_spec["rng"] = np.random.default_rng(4)
        long_record = driver.compare_fuzz_case(long_spec)
        assert long_record["aborted"] is False
        assert long_record["horizon"] == driver.T_STAR
        beyond = long_record["beyond_horizon"]
        assert beyond is not None
        assert set(beyond) == {"order_parameter_traj", "mean_phase_coherence_traj"}
        for pair in beyond.values():
            assert set(pair) == {"reference", "produced"}
            # steps (T_STAR+1)..(T_STAR+10) inclusive = 10 beyond-horizon points.
            assert len(pair["reference"]) == 10
            assert len(pair["produced"]) == 10

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

    @_needs_gpu_execution
    @pytest.mark.parametrize("case_id", _KURAMOTO_SPARSE_KNN_CASES)
    def test_representative_cases_within_tolerance(
        self, loader: CorpusLoader, case_id: str
    ) -> None:
        record = driver.compare_kernel_path_case(loader, case_id)
        assert record["aborted"] is False
        assert record["within_tolerance"] is True
        assert record["case_id"] == case_id
        assert {c["array_name"] for c in record["comparisons"]} == {
            "dphase",
            "damplitude",
            "dfrequency",
        }

    @_needs_gpu_execution
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
        assert all(r["aborted"] is False for r in records)
        assert all(r["within_tolerance"] for r in records)

    @_needs_gpu_execution
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

    @_needs_gpu_binding
    def test_non_cuda_resident_result_raises(
        self, loader: CorpusLoader, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """A non-CUDA-resident GPU result aborts rather than counting as cuda.

        Regression test for the bug where ``compare_kernel_path_case`` only
        checked ``hasattr(_prin_core, "GpuSparseKuramoto")`` (later,
        ``torch.cuda.is_available()``) — neither proves the call actually
        dispatched through CUDA: ``GpuSparseKuramoto`` also compiles under
        ``--features wgpu`` alone, and even a ``--features cuda`` build
        silently falls back to a host-slice (CPU) path when its CUDA client
        fails to initialise (``crates/prin-sim/src/gpu.rs``). Both failure
        modes return a CPU-resident DLPack capsule instead of the true CUDA
        path's zero-copy ``kDLCUDA`` one, so this simulates that directly.
        """
        monkeypatch.setattr(
            driver, "from_dlpack", lambda capsule: torch.zeros(1, device="cpu")
        )
        with pytest.raises(driver.GpuBindingUnavailableError, match="cuda"):
            driver.compare_kernel_path_case(loader, _KURAMOTO_SPARSE_KNN_CASES[0])


class TestRunDirectoryContract:
    """_reserve_run_dir enforces campaign plan §7.1 before any write (Copilot,
    CodeRabbit)."""

    def test_canonical_new_child_of_root_passes_and_creates_it(
        self, run_root: Path
    ) -> None:
        run_dir = _run_dir(run_root, "corpus-cpu")
        assert not run_dir.exists()
        driver._reserve_run_dir(run_dir)
        assert run_dir.is_dir()

    @pytest.mark.parametrize(
        "name",
        [
            "RUN-race",
            "RUN-20260921T000000Z-smoke",
            "RUN-20260921T000000Z-abc1234-",
            "RUN-2026-09-21T00:00:00Z-abc1234-smoke",
            "RUN-20260921T000000Z-ABC1234-smoke",
            "RUN-20260921T000000Z-xyz-smoke",
            "corpus-cpu",
        ],
    )
    def test_non_canonical_name_rejected(self, run_root: Path, name: str) -> None:
        target = run_root / name
        with pytest.raises(driver.DriverMetadataError, match=r"§7\.1 form"):
            driver._reserve_run_dir(target)
        assert not target.exists()

    def test_wrong_parent_rejected(self, run_root: Path, tmp_path: Path) -> None:
        elsewhere = tmp_path / "EXP-002"
        elsewhere.mkdir()
        target = _run_dir(elsewhere, "corpus-cpu")
        with pytest.raises(driver.DriverMetadataError, match="direct child"):
            driver._reserve_run_dir(target)
        assert not target.exists()

    def test_existing_directory_rejected(self, run_root: Path) -> None:
        """A run directory is never reused (campaign plan §7.1)."""
        run_dir = _run_dir(run_root, "retry")
        run_dir.mkdir()
        with pytest.raises(driver.DriverMetadataError, match="never"):
            driver._reserve_run_dir(run_dir)

    def test_concurrent_reservation_only_one_wins(self, run_root: Path) -> None:
        """Regression test: exists()-then-write is a TOCTOU race (CodeRabbit).

        The check is now an atomic exclusive-create ``mkdir()``: simulating
        two invocations racing for the same directory, exactly one succeeds
        and the other sees it as already existing, rather than both passing
        a check and one silently publishing into the other's directory.
        """
        run_dir = _run_dir(run_root, "race")
        driver._reserve_run_dir(run_dir)  # first invocation wins
        with pytest.raises(driver.DriverMetadataError, match="never"):
            driver._reserve_run_dir(run_dir)  # second invocation loses

    def test_missing_root_rejected(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        missing_root = tmp_path / "does-not-exist"
        monkeypatch.setattr(driver, "_RUN_ROOT", missing_root)
        with pytest.raises(driver.DriverMetadataError, match="does not exist"):
            driver._reserve_run_dir(_run_dir(missing_root, "smoke"))

    def test_cli_rejects_before_any_comparison(
        self, run_root: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """The contract is checked up front, so a bad --out never runs cases."""
        calls: list[str] = []

        def _record(*args: object, **kwargs: object) -> list[dict[str, object]]:
            calls.append("ran")
            return []

        monkeypatch.setattr(driver, "compare_corpus_subset", _record)
        argv = [
            "--mode",
            "corpus",
            "--corpus-dir",
            str(_CORPUS_DIR),
            "--out",
            str(run_root / "RUN-typo"),
            "--label",
            "smoke",
            "--session",
            "0156",
            "--operator",
            "tester",
        ]
        assert driver.main(argv) == 2
        assert calls == []
        assert not (run_root / "RUN-typo").exists()


class TestLabelContract:
    """_validate_label rejects a --label that could escape run_dir (CWE-22,
    CodeRabbit + Copilot)."""

    @pytest.mark.parametrize(
        "label", ["corpus-cpu", "seedrep0", "knn16k.cuda", "a", "A1_2-3.4"]
    )
    def test_safe_label_passes(self, label: str) -> None:
        driver._validate_label(label)

    @pytest.mark.parametrize(
        "label",
        [
            "",
            "..",
            "x/../../../EXP-002/foreign",
            "a/b",
            "a\\b",
            "/etc/passwd",
            "..\\..\\foreign",
            ".hidden",
        ],
    )
    def test_unsafe_label_rejected(self, label: str) -> None:
        with pytest.raises(driver.DriverMetadataError, match="single filename"):
            driver._validate_label(label)

    def test_traversal_label_confirmed_empirically_and_rejected(
        self, run_root: Path
    ) -> None:
        """The exact scenario CodeRabbit/Copilot demonstrated: proves the
        traversal is real (would escape run_dir if unvalidated) *and* that
        the CLI rejects it before writing anything, anywhere."""
        run_dir = _run_dir(run_root, "smoke")
        label = "x/../../../EXP-002/foreign"
        result_name = f"corpus_{label}.json"
        escaped = (run_dir / result_name).resolve()
        assert run_root.resolve() not in escaped.parents, (
            "fixture assumption violated: this label no longer escapes run_dir"
        )

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
            label,
            "--session",
            "0156",
            "--operator",
            "tester",
        ]
        assert driver.main(argv) == 2
        assert not escaped.exists()
        assert not run_dir.exists()


class TestReferenceProvenance:
    """prinet_reference_provenance pins and records the H2 reference (Copilot)."""

    def test_registered_version_passes_and_reports_source(self) -> None:
        pytest.importorskip("prinet")
        provenance = driver.prinet_reference_provenance()
        assert provenance["prinet_version"] == driver.PRINET_REFERENCE_VERSION
        assert Path(provenance["prinet_source"]).is_dir()

    def test_other_version_aborts(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """A different prinet on sys.path must never yield a '3.0.0' result."""
        prinet = pytest.importorskip("prinet")
        monkeypatch.setattr(prinet, "__version__", "3.1.0")
        with pytest.raises(driver.PrinetUnavailableError, match=r"3\.1\.0"):
            driver.prinet_reference_provenance()
        # The per-case path is guarded too, not just main().
        rng = np.random.default_rng(0)
        spec = driver.draw_fuzz_spec(rng)
        spec["rng"] = rng
        with pytest.raises(driver.PrinetUnavailableError, match=r"3\.1\.0"):
            driver.compare_fuzz_case(spec)

    @pytest.mark.slow
    def test_fuzz_artefact_records_reference(self, run_root: Path) -> None:
        pytest.importorskip("prinet")
        run_dir = _run_dir(run_root, "fuzz")
        argv = [
            "--mode",
            "fuzz",
            "--n-fuzz-cases",
            "1",
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
        payload = json.loads((run_dir / "fuzz_smoke.json").read_text(encoding="utf-8"))
        assert payload["config"]["prinet_version"] == driver.PRINET_REFERENCE_VERSION
        assert "prinet_source" in payload["config"]

    def test_corpus_artefact_does_not_claim_a_reference(self, run_root: Path) -> None:
        """Corpus mode's reference is the stored corpus, not a live prinet."""
        run_dir = _run_dir(run_root, "corpus")
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
            "tester",
        ]
        assert driver.main(argv) == 0
        payload = json.loads(
            (run_dir / "corpus_smoke.json").read_text(encoding="utf-8")
        )
        assert "prinet_version" not in payload["config"]


class TestRunClosure:
    """check_run_complete refuses to bless a sidecar-only directory (CodeRabbit)."""

    def _sidecar(self, run_dir: Path, artefacts: dict[str, list[str]]) -> None:
        driver.write_campaign_metadata(
            run_dir,
            exp_id="EXP-001",
            run_id=run_dir.name,
            session="0156",
            operator="tester",
            artefacts=artefacts,
        )

    def test_complete_directory_passes(self, run_root: Path) -> None:
        run_dir = _run_dir(run_root, "complete")
        self._sidecar(run_dir, {"corpus_smoke.json": ["H1"]})
        (run_dir / "corpus_smoke.json").write_text("{}", encoding="utf-8")
        assert driver.check_run_complete(run_dir) == {"corpus_smoke.json": ["H1"]}

    def test_sidecar_only_directory_rejected(self, run_root: Path) -> None:
        """The kill-between-writes case: sidecar present, result absent.

        ``tools.reproduce.append_manifest`` would inventory this directory's
        single JSON file and ``verify_manifest`` would then accept the
        manifest; this is the check E3 must run first.
        """
        run_dir = _run_dir(run_root, "killed")
        self._sidecar(run_dir, {"corpus_smoke.json": ["H1"]})
        with pytest.raises(driver.IncompleteRunError, match=r"corpus_smoke\.json"):
            driver.check_run_complete(run_dir)

    def test_missing_sidecar_rejected(self, run_root: Path) -> None:
        run_dir = _run_dir(run_root, "nosidecar")
        run_dir.mkdir()
        (run_dir / "corpus_smoke.json").write_text("{}", encoding="utf-8")
        with pytest.raises(driver.IncompleteRunError, match="no campaign-metadata"):
            driver.check_run_complete(run_dir)

    @pytest.mark.parametrize(
        "body",
        ["not json", "{}", '{"artefacts": {}}', '{"artefacts": {"x.json": 5}}'],
    )
    def test_malformed_sidecar_rejected(self, run_root: Path, body: str) -> None:
        run_dir = _run_dir(run_root, "malformed")
        run_dir.mkdir()
        (run_dir / "campaign-metadata.json").write_text(body, encoding="utf-8")
        with pytest.raises(driver.IncompleteRunError, match="malformed"):
            driver.check_run_complete(run_dir)

    @pytest.mark.parametrize(
        "unsafe_name",
        ["../../foreign.json", "sub/inner.json", "..", ".", "a\\b.json"],
    )
    def test_unsafe_artefact_name_rejected(
        self, run_root: Path, unsafe_name: str
    ) -> None:
        """A tampered or malformed sidecar naming a traversal path must never
        be trusted, independent of --label validation upstream (Copilot).
        """
        run_dir = _run_dir(run_root, "unsafe")
        run_dir.mkdir()
        (run_dir / "campaign-metadata.json").write_text(
            json.dumps({"artefacts": {unsafe_name: ["H1"]}}), encoding="utf-8"
        )
        with pytest.raises(driver.IncompleteRunError, match="unsafe or reserved"):
            driver.check_run_complete(run_dir)

    @pytest.mark.parametrize(
        "reserved_name", ["campaign-metadata.json", "manifest.json"]
    )
    def test_reserved_infrastructure_name_rejected_as_artefact(
        self, run_root: Path, reserved_name: str
    ) -> None:
        """A sidecar naming itself or manifest.json as an artefact would
        otherwise pass both the missing-file check (the file exists — it
        just isn't a result) and the unlisted-file check (it is excluded
        from `present` precisely because it is infrastructure) for the
        wrong reason (Copilot).
        """
        run_dir = _run_dir(run_root, "reserved")
        run_dir.mkdir()
        (run_dir / "campaign-metadata.json").write_text(
            json.dumps({"artefacts": {reserved_name: ["H1"]}}), encoding="utf-8"
        )
        with pytest.raises(driver.IncompleteRunError, match="unsafe or reserved"):
            driver.check_run_complete(run_dir)

    @pytest.mark.parametrize(
        "cased_name",
        ["CAMPAIGN-METADATA.JSON", "Campaign-Metadata.Json", "MANIFEST.JSON"],
    )
    def test_reserved_infrastructure_name_rejected_case_insensitively(
        self, run_root: Path, cased_name: str
    ) -> None:
        """A case-varying alias of a reserved name must be rejected too: on
        a case-insensitive filesystem (Windows/macOS, both in this
        project's CI matrix), `CAMPAIGN-METADATA.JSON` resolves to the same
        on-disk file as `campaign-metadata.json`, so an exact-string
        comparison would miss it (CodeRabbit).
        """
        run_dir = _run_dir(run_root, "reservedcase")
        run_dir.mkdir()
        (run_dir / "campaign-metadata.json").write_text(
            json.dumps({"artefacts": {cased_name: ["H1"]}}), encoding="utf-8"
        )
        with pytest.raises(driver.IncompleteRunError, match="unsafe or reserved"):
            driver.check_run_complete(run_dir)

    @_needs_symlink_support
    def test_symlinked_artefact_rejected(self, run_root: Path) -> None:
        """A declared artefact that is a symlink to a file outside run_dir
        must never be trusted: Path.is_file() follows symlinks, so this
        would otherwise pass the missing-file check and be manifested as if
        it were written directly into run_dir by this run (CodeRabbit,
        CWE-59).
        """
        run_dir = _run_dir(run_root, "symlinked")
        outside = run_root / "outside_secret.json"
        outside.write_text('{"not": "a real result"}', encoding="utf-8")
        self._sidecar(run_dir, {"corpus_h1.json": ["H1"]})
        (run_dir / "corpus_h1.json").symlink_to(outside)
        with pytest.raises(driver.IncompleteRunError, match="symbolic link"):
            driver.check_run_complete(run_dir)

    def test_unlisted_result_file_rejected(self, run_root: Path) -> None:
        """Every top-level result JSON must be named by the sidecar, not just
        every sidecar name be present (Copilot: "does not require every
        top-level result JSON to be listed").
        """
        run_dir = _run_dir(run_root, "unlisted")
        self._sidecar(run_dir, {"corpus_smoke.json": ["H1"]})
        (run_dir / "corpus_smoke.json").write_text("{}", encoding="utf-8")
        (run_dir / "corpus_extra.json").write_text("{}", encoding="utf-8")
        with pytest.raises(driver.IncompleteRunError, match=r"corpus_extra\.json"):
            driver.check_run_complete(run_dir)

    def test_manifest_json_is_not_treated_as_an_unlisted_result(
        self, run_root: Path
    ) -> None:
        """manifest.json is run-directory infrastructure (written by
        append_manifest, the step *after* this check), not a result artefact
        the sidecar would ever name — so its presence must not trip the
        unlisted-file check. This also makes check_run_complete safe to call
        again on an already-closed directory."""
        run_dir = _run_dir(run_root, "withmanifest")
        self._sidecar(run_dir, {"corpus_smoke.json": ["H1"]})
        (run_dir / "corpus_smoke.json").write_text("{}", encoding="utf-8")
        (run_dir / "manifest.json").write_text("{}", encoding="utf-8")
        assert driver.check_run_complete(run_dir) == {"corpus_smoke.json": ["H1"]}


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

    def test_corpus_mode_writes_artefact_and_sidecar(self, run_root: Path) -> None:
        run_dir = _run_dir(run_root, "smoke")
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

    def test_preexisting_result_aborts_before_writing_metadata(
        self, run_root: Path
    ) -> None:
        """A stale result at the target path aborts before any write (CodeRabbit).

        Regression test: a result left over from an earlier invocation
        (e.g. a retry reusing the same --out/--label) must never receive a
        *fresh* campaign-metadata.json sidecar claiming provenance over it.
        (Since the §7.1 never-reused rule was enforced, this now trips the
        run-directory-exists check even earlier — same outcome: exit 2,
        nothing written.)
        """
        run_dir = _run_dir(run_root, "stale")
        run_dir.mkdir()
        stale_result = run_dir / "corpus_smoke.json"
        stale_result.write_text('{"stale": true}', encoding="utf-8")
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
            "tester",
        ]
        assert driver.main(argv) == 2
        assert stale_result.read_text(encoding="utf-8") == '{"stale": true}'
        assert not (run_dir / "campaign-metadata.json").exists()

    def test_result_write_failure_rolls_back_the_sidecar(
        self, run_root: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """A lost race for the result path leaves no orphan sidecar (Copilot).

        The ``exists()`` fast-fail above is only a check, not a reservation:
        a concurrent writer can still take the result path between it and
        ``write_result``. Simulated here by having ``write_result`` raise
        ``ArtefactExistsError`` as it would in that race. The sidecar this
        invocation already published must then be rolled back, so it never
        claims provenance over a result this invocation did not write.
        """
        run_dir = _run_dir(run_root, "lostrace")
        sidecar = run_dir / "campaign-metadata.json"
        sidecar_existed_at_result_write = False

        def _lost_race(*args: object, **kwargs: object) -> Path:
            nonlocal sidecar_existed_at_result_write
            sidecar_existed_at_result_write = sidecar.exists()
            raise result_module.ArtefactExistsError("lost the race for the result")

        monkeypatch.setattr(driver, "write_result", _lost_race)
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
            "tester",
        ]
        assert driver.main(argv) == 2
        assert sidecar_existed_at_result_write, "sidecar must be published first"
        assert not sidecar.exists(), "sidecar must be rolled back on failure"

    def test_repeatability_mode_tags_artefact_h3(self, run_root: Path) -> None:
        """Regression test: repeatability runs must tag H3, not H1 (§8)."""
        run_dir = _run_dir(run_root, "repeatability")
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

    @_needs_gpu_execution
    def test_kernel_path_mode_writes_artefact_and_sidecar(self, run_root: Path) -> None:
        run_dir = _run_dir(run_root, "kernel-path")
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

    def test_missing_operator_aborts_without_writing(self, run_root: Path) -> None:
        run_dir = _run_dir(run_root, "abort")
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

    def test_repeatability_mode_without_case_id_aborts(self, run_root: Path) -> None:
        run_dir = _run_dir(run_root, "nocase")
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
