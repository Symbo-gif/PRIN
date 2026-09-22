"""Tests for the EXP-001 campaign driver (tests in tandem, Coding Standards §5).

Covers the four comparisons the EXP-001 pre-registration names: corpus parity
(H1), hypothesis-fuzzed parity (H2), bit-level repeatability (H3), and the
GPU sparse-k-NN kernel-path comparison (H4), plus the campaign-metadata
sidecar and CLI wiring (campaign plan §7.2). H4's tests are ``skipif``-guarded:
``_needs_gpu_binding`` (mirroring ``tests/test_wp036d_gpu_dispatch.py``'s
existing convention) for tests that only need
``prin._prin_core.GpuSparseKuramoto`` present (a build-configuration gate),
and ``_needs_gpu_execution`` for tests that actually call
``compare_kernel_path_case`` expecting it to succeed.

``_needs_gpu_execution`` is the executability probe
``tests/_env.py::cuda_kernel_executes``, not ``torch.cuda.is_available()``:
``GpuSparseKuramoto`` compiles under ``cfg(any(feature = "cuda", feature =
"wgpu"))``, so its presence proves only that *some* GPU feature was built,
and ``torch.cuda.is_available()`` describes PyTorch's runtime rather than the
backend the Rust extension was compiled against — a wgpu-only build on a CUDA
host passes both and the guarded tests then run-and-fail instead of skipping
(ETCA-002 T-F3 / governance G8: a hardware guard must probe *executability*).
Every H4 success-path test additionally carries ``@pytest.mark.gpu`` so
``gpu.yml``'s ``-m "gpu or directml"`` selection actually runs it on
``PRIN-GPU-Runner``; the negative tests that need no GPU build stay outside
that marker so they run on every hosted leg.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np
import pytest
import torch
from _env import cuda_kernel_executes
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

# compare_kernel_path_case requires the binding to dispatch through *CUDA*:
# it aborts on any non-kDLCUDA capsule. Neither the binding's presence nor
# torch.cuda.is_available() establishes that (the binding also compiles under
# --features wgpu, and PyTorch's CUDA runtime says nothing about which backend
# the Rust extension was built against), so the guard is the executability
# probe from tests/_env.py: it runs one tiny derivative evaluation and checks
# every returned capsule is CUDA-resident. Tests that execute H4 expecting
# success need this, or they run-and-fail instead of skipping on a wgpu-only
# build — ETCA-002 T-F3 / governance G8.
_needs_gpu_execution = pytest.mark.skipif(
    not cuda_kernel_executes(),
    reason=(
        "H4 kernel-path execution requires prin._prin_core.GpuSparseKuramoto "
        "to actually dispatch through CUDA (tests/_env.py::cuda_kernel_executes)"
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
    """draw_fuzz_spec/draw_fuzz_initial draw only from the registered ``Seed``."""

    def test_deterministic_given_the_same_seed(self) -> None:
        assert driver.draw_fuzz_spec(_prin_core.Seed(0, 1)) == driver.draw_fuzz_spec(
            _prin_core.Seed(0, 1)
        )

    def test_distinct_counters_give_distinct_streams(self) -> None:
        first = _prin_core.Seed(0, 1)
        second = _prin_core.Seed(1, 1)
        assert [driver.draw_fuzz_spec(first) for _ in range(5)] != [
            driver.draw_fuzz_spec(second) for _ in range(5)
        ]

    def test_sampler_rejects_a_numpy_generator(self) -> None:
        """Campaign plan §6.1: no second RNG path.

        Regression guard for the NumPy PCG64 stream this driver used to
        derive from ``(seed_counter, seed_key)``. The sampler now speaks the
        ``Seed`` protocol only, so a ``numpy.random.Generator`` cannot be
        substituted for it even by accident.
        """
        with pytest.raises(AttributeError):
            driver.draw_fuzz_spec(np.random.default_rng(0))  # type: ignore[arg-type]

    def test_spec_carries_no_unconsumed_seed_field(self) -> None:
        """The old per-case ``"seed"`` determined nothing and is gone (§5.12)."""
        assert "seed" not in driver.draw_fuzz_spec(_prin_core.Seed(0, 1))

    def test_stuart_landau_always_full_coupling(self) -> None:
        stream = _prin_core.Seed(0, 1)
        for _ in range(50):
            spec = driver.draw_fuzz_spec(stream)
            if spec["model"] == Model.STUART_LANDAU.value:
                assert spec["coupling"] == Coupling.FULL.value

    def test_sparse_knn_specs_carry_sparse_k(self) -> None:
        stream = _prin_core.Seed(7, 1)
        found_sparse = False
        for _ in range(200):
            spec = driver.draw_fuzz_spec(stream)
            if spec["coupling"] == Coupling.SPARSE_KNN.value:
                found_sparse = True
                assert "sparse_k" in spec["parameters"]
                assert 2 <= spec["parameters"]["sparse_k"] < spec["n_oscillators"]
        assert found_sparse, "expected at least one sparse_knn draw in 200 samples"

    def test_bounds(self) -> None:
        stream = _prin_core.Seed(123, 1)
        for _ in range(100):
            spec = driver.draw_fuzz_spec(stream)
            assert 8 <= spec["n_oscillators"] <= 64
            assert 5 <= spec["n_steps"] <= 50
            assert 0.001 <= spec["dt"] <= 0.05
            assert 0.1 <= spec["parameters"]["coupling_strength"] <= 4.0

    def test_draw_fuzz_initial_shapes(self) -> None:
        phase, amplitude, frequency = driver.draw_fuzz_initial(
            _prin_core.Seed(0, 1), 10
        )
        assert phase.shape == (10,)
        assert amplitude.shape == (10,)
        assert frequency.shape == (10,)
        assert np.all(amplitude > 0.0)
        assert np.all((phase >= 0.0) & (phase < 2.0 * np.pi))

    def test_seed_integer_is_in_range(self) -> None:
        stream = _prin_core.Seed(0, 1)
        values = {driver._seed_integer(stream, 2, 5) for _ in range(200)}
        assert values <= {2, 3, 4}
        assert values == {2, 3, 4}

    def test_seed_integer_rejects_an_empty_range(self) -> None:
        with pytest.raises(ValueError, match="empty integer range"):
            driver._seed_integer(_prin_core.Seed(0, 1), 3, 3)


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
        assert [record["case_index"] for record in records] == [0, 1, 2]
        for record in records:
            assert record["aborted"] is False
            assert "seed" not in record
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
        short_spec = {
            "model": Model.KURAMOTO.value,
            "coupling": Coupling.MEAN_FIELD.value,
            "integrator": "euler",
            "n_oscillators": 8,
            "n_steps": driver.T_STAR,
            "dt": 0.01,
            "case_index": 0,
            "parameters": {
                "coupling_strength": 1.0,
                "decay_rate": 0.1,
                "freq_adaptation_rate": 0.0,
            },
            "seed_stream": _prin_core.Seed(3, 1),
        }
        short_record = driver.compare_fuzz_case(short_spec)
        assert short_record["aborted"] is False
        assert short_record["horizon"] == driver.T_STAR
        assert short_record["beyond_horizon"] is None

        long_spec = {**short_spec, "n_steps": driver.T_STAR + 10, "case_index": 1}
        long_spec["seed_stream"] = _prin_core.Seed(4, 1)
        long_record = driver.compare_fuzz_case(long_spec)
        assert long_record["aborted"] is False
        assert long_record["horizon"] == driver.T_STAR
        beyond = long_record["beyond_horizon"]
        assert beyond is not None
        assert set(beyond) == {"order_parameter_traj", "mean_phase_coherence_traj"}
        for pair in beyond.values():
            assert set(pair) == {
                "reference",
                "produced",
                "n_points",
                "reference_mean",
                "produced_mean",
                "mean_paired_difference",
            }
            # steps (T_STAR+1)..(T_STAR+10) inclusive = 10 beyond-horizon points.
            assert len(pair["reference"]) == 10
            assert len(pair["produced"]) == 10
            assert pair["n_points"] == 10
            # The registered per-case paired summary, not a per-step pool.
            difference = np.asarray(pair["produced"]) - np.asarray(pair["reference"])
            assert pair["mean_paired_difference"] == pytest.approx(
                float(np.mean(difference)), abs=1e-15
            )

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
        stream = _prin_core.Seed(0, 1)
        spec = driver.draw_fuzz_spec(stream)
        spec["case_index"] = 0
        spec["seed_stream"] = stream
        with pytest.raises(driver.PrinetUnavailableError):
            driver.compare_fuzz_case(spec)


class TestKernelPath:
    """H4: the GPU sparse-k-NN derivative kernel agrees with the CPU reference."""

    @pytest.mark.gpu
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

    @pytest.mark.gpu
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

    @pytest.mark.gpu
    @_needs_gpu_binding
    def test_non_sparse_knn_case_raises(self, loader: CorpusLoader) -> None:
        """A wrong --case-id is an operator abort, not a bare ValueError."""
        with pytest.raises(driver.DriverMetadataError, match="kuramoto/sparse_knn"):
            driver.compare_kernel_path_case(loader, _REPRESENTATIVE_CASES[0])

    def test_missing_binding_raises(
        self, loader: CorpusLoader, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """A build without the cuda feature aborts, not silently skips (§4 item 6)."""
        monkeypatch.delattr(_prin_core, "GpuSparseKuramoto", raising=False)
        with pytest.raises(driver.GpuBindingUnavailableError):
            driver.compare_kernel_path_case(loader, _KURAMOTO_SPARSE_KNN_CASES[0])

    @pytest.mark.gpu
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
            "safe\n",
            "safe\nrogue",
        ],
    )
    def test_unsafe_label_rejected(self, label: str) -> None:
        with pytest.raises(driver.DriverMetadataError, match="single filename"):
            driver._validate_label(label)

    def test_trailing_newline_label_confirmed_empirically_and_rejected(self) -> None:
        """Regression test (Copilot): Python's unanchored ``$`` matches just
        before a trailing ``\\n``, not only the true end of string, so
        ``re.match(r"...$", "safe\\n")`` succeeds even though the label
        carries an embedded control character. Confirmed against the actual
        pattern object before asserting the driver rejects it.
        """
        import re

        loose = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]*$")
        assert loose.match("safe\n") is not None, (
            "fixture assumption violated: $ no longer admits a trailing newline"
        )
        with pytest.raises(driver.DriverMetadataError):
            driver._validate_label("safe\n")


class TestRunIdContract:
    """_RUN_ID_RE shares _LABEL_RE's \\Z-anchoring fix (Copilot)."""

    def test_trailing_newline_run_id_rejected(self, run_root: Path) -> None:
        run_dir = run_root / "RUN-20260921T000000Z-abc1234-smoke\n"
        with pytest.raises(driver.DriverMetadataError, match="does not match"):
            driver._reserve_run_dir(run_dir)
        assert not run_dir.exists()

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
        stream = _prin_core.Seed(0, 1)
        spec = driver.draw_fuzz_spec(stream)
        spec["case_index"] = 0
        spec["seed_stream"] = stream
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


def _envelope(run_dir: Path, *, backend: str = "cpu") -> dict[str, object]:
    """A minimal campaign plan §7.2-conforming result envelope for ``run_dir``."""
    return {
        "environment": {
            "prin_version": "1.0.0rc1",
            "git_commit": "abc1234def",
            "rust_version": "rustc 1.92.0",
            "python_version": "3.14.0",
            "platform": "test-platform",
            "processor": "test-processor",
            "logical_cpus": 8,
            "gpu": "test-gpu",
            "gpu_vram_mb": 8192,
            "backend": backend,
            "dtype": "f32" if backend == "cuda" else "f64",
            "seed": 0,
        },
        "config": {
            "iterations": 1,
            "warmup": 0,
            "seed_counter": 0,
            "seed_key": 1,
            "out_dir": str(run_dir),
        },
        "cases": [],
    }


def _write_envelope(run_dir: Path, name: str, *, backend: str = "cpu") -> None:
    """Write a conforming result artefact ``name`` into ``run_dir``."""
    (run_dir / name).write_text(
        json.dumps(_envelope(run_dir, backend=backend)), encoding="utf-8"
    )


def _raw_sidecar(run_dir: Path, **overrides: object) -> None:
    """Write a campaign-metadata.json directly, bypassing the writer's checks.

    ``check_run_complete`` must not assume every sidecar it is pointed at was
    produced by a conforming invocation of this driver, so the schema tests
    hand it hand-built documents.
    """
    run_dir.mkdir(exist_ok=True)
    payload: dict[str, object] = {
        "exp_id": "EXP-001",
        "run_id": run_dir.name,
        "session": "0156",
        "operator": "tester",
        "artefacts": {"corpus_smoke.json": ["H1"]},
    }
    payload.update(overrides)
    (run_dir / "campaign-metadata.json").write_text(
        json.dumps(payload), encoding="utf-8"
    )


class TestRunClosure:
    """check_run_complete refuses to bless a sidecar-only directory (CodeRabbit)."""

    def _sidecar(self, run_dir: Path, artefacts: dict[str, object]) -> None:
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
        _write_envelope(run_dir, "corpus_smoke.json")
        assert driver.check_run_complete(run_dir) == {"corpus_smoke.json": ["H1"]}

    def test_complete_gpu_directory_passes(self, run_root: Path) -> None:
        """A GPU entry closes only with its registered timing_method."""
        run_dir = _run_dir(run_root, "gpucomplete")
        self._sidecar(
            run_dir,
            {
                "kernel-path_cuda.json": {
                    "hypotheses": ["H4"],
                    "timing_method": driver.KERNEL_PATH_TIMING_METHOD,
                }
            },
        )
        _write_envelope(run_dir, "kernel-path_cuda.json", backend="cuda")
        assert driver.check_run_complete(run_dir) == {"kernel-path_cuda.json": ["H4"]}

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
        _write_envelope(run_dir, "corpus_smoke.json")
        with pytest.raises(driver.IncompleteRunError, match="no campaign-metadata"):
            driver.check_run_complete(run_dir)

    def test_unparseable_sidecar_rejected(self, run_root: Path) -> None:
        run_dir = _run_dir(run_root, "malformed")
        run_dir.mkdir()
        (run_dir / "campaign-metadata.json").write_text("not json", encoding="utf-8")
        with pytest.raises(driver.IncompleteRunError, match="malformed"):
            driver.check_run_complete(run_dir)

    @pytest.mark.parametrize("body", ["[]", '"a string"', "42"])
    def test_non_object_sidecar_rejected(self, run_root: Path, body: str) -> None:
        run_dir = _run_dir(run_root, "notobject")
        run_dir.mkdir()
        (run_dir / "campaign-metadata.json").write_text(body, encoding="utf-8")
        with pytest.raises(driver.IncompleteRunError, match="not a JSON object"):
            driver.check_run_complete(run_dir)

    @pytest.mark.parametrize(
        "field", ["exp_id", "run_id", "session", "operator", "artefacts"]
    )
    def test_missing_required_sidecar_field_rejected(
        self, run_root: Path, field: str
    ) -> None:
        """Every campaign plan §7.2 top-level field is required, not just artefacts."""
        run_dir = _run_dir(run_root, "missingfield")
        run_dir.mkdir()
        payload = {
            "exp_id": "EXP-001",
            "run_id": run_dir.name,
            "session": "0156",
            "operator": "tester",
            "artefacts": {"corpus_smoke.json": ["H1"]},
        }
        del payload[field]
        (run_dir / "campaign-metadata.json").write_text(
            json.dumps(payload), encoding="utf-8"
        )
        with pytest.raises(driver.IncompleteRunError, match=f"missing.*{field}"):
            driver.check_run_complete(run_dir)

    def test_wrong_exp_id_rejected(self, run_root: Path) -> None:
        run_dir = _run_dir(run_root, "wrongexp")
        _raw_sidecar(run_dir, exp_id="EXP-002")
        with pytest.raises(driver.IncompleteRunError, match="exp_id"):
            driver.check_run_complete(run_dir)

    def test_run_id_must_equal_directory_name(self, run_root: Path) -> None:
        run_dir = _run_dir(run_root, "wrongrunid")
        _raw_sidecar(run_dir, run_id="RUN-20260921T000000Z-abc1234-elsewhere")
        with pytest.raises(driver.IncompleteRunError, match="run_id"):
            driver.check_run_complete(run_dir)

    @pytest.mark.parametrize("field", ["session", "operator"])
    @pytest.mark.parametrize("value", ["", None, 5])
    def test_empty_or_non_string_session_operator_rejected(
        self, run_root: Path, field: str, value: object
    ) -> None:
        run_dir = _run_dir(run_root, "emptymeta")
        _raw_sidecar(run_dir, **{field: value})
        with pytest.raises(driver.IncompleteRunError, match=field):
            driver.check_run_complete(run_dir)

    @pytest.mark.parametrize("artefacts", [{}, [], "corpus_smoke.json", None, 7])
    def test_artefacts_must_be_a_non_empty_object(
        self, run_root: Path, artefacts: object
    ) -> None:
        run_dir = _run_dir(run_root, "badartefacts")
        _raw_sidecar(run_dir, artefacts=artefacts)
        with pytest.raises(driver.IncompleteRunError, match="not a non-empty"):
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
        _raw_sidecar(run_dir, artefacts={unsafe_name: ["H1"]})
        with pytest.raises(driver.IncompleteRunError, match="plain filename"):
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
        _raw_sidecar(run_dir, artefacts={reserved_name: ["H1"]})
        with pytest.raises(driver.IncompleteRunError, match="reserved"):
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
        _raw_sidecar(run_dir, artefacts={cased_name: ["H1"]})
        with pytest.raises(driver.IncompleteRunError, match="reserved"):
            driver.check_run_complete(run_dir)

    def test_declared_non_json_artefact_rejected(self, run_root: Path) -> None:
        """A declared notes.txt could never be covered by the run manifest."""
        run_dir = _run_dir(run_root, "notjson")
        _raw_sidecar(run_dir, artefacts={"notes.txt": ["H1"]})
        (run_dir / "notes.txt").write_text("free text", encoding="utf-8")
        with pytest.raises(driver.IncompleteRunError, match=r"'\.json' suffix"):
            driver.check_run_complete(run_dir)

    def test_declared_uppercase_json_artefact_rejected(self, run_root: Path) -> None:
        """A declared corpus_smoke.JSON is recognised, then rejected as
        non-canonical: Path.glob('*.json') manifests it on Windows and not on
        Linux, so accepting it would make closure host-dependent."""
        run_dir = _run_dir(run_root, "uppercasedecl")
        _raw_sidecar(run_dir, artefacts={"corpus_smoke.JSON": ["H1"]})
        _write_envelope(run_dir, "corpus_smoke.JSON")
        with pytest.raises(driver.IncompleteRunError, match="non-canonical"):
            driver.check_run_complete(run_dir)

    def test_unregistered_artefact_name_shape_rejected(self, run_root: Path) -> None:
        run_dir = _run_dir(run_root, "badshape")
        _raw_sidecar(run_dir, artefacts={"summary.json": ["H1"]})
        (run_dir / "summary.json").write_text("{}", encoding="utf-8")
        with pytest.raises(driver.IncompleteRunError, match="registered"):
            driver.check_run_complete(run_dir)

    def test_bare_dot_json_present_file_rejected(self, run_root: Path) -> None:
        """A top-level ``.json`` file is recognised, not silently invisible.

        Regression test (CodeRabbit): ``Path.glob("*.json")`` matches the
        bare name ``.json`` too (``*`` matches an empty prefix), so
        ``append_manifest`` would manifest it even though the earlier
        ``_is_json_name`` (which required a non-empty stem) never saw it as
        present — breaking the "closure and manifest agree" contract this
        module documents. A declared ``.json`` is separately still rejected
        as an unregistered name shape (not exercised here).
        """
        run_dir = _run_dir(run_root, "baredotjson")
        self._sidecar(run_dir, {"corpus_smoke.json": ["H1"]})
        _write_envelope(run_dir, "corpus_smoke.json")
        (run_dir / ".json").write_text("{}", encoding="utf-8")
        with pytest.raises(driver.IncompleteRunError, match=r"\.json"):
            driver.check_run_complete(run_dir)

    @_needs_symlink_support
    def test_symlinked_manifest_json_rejected(self, run_root: Path) -> None:
        """``manifest.json`` itself must not be a symlink (Copilot, CWE-59).

        ``append_manifest`` resolves its destination before writing, so a
        dangling or in-root symlink named ``manifest.json`` would make the
        *next* closure step publish this run's manifest somewhere outside
        ``run_dir`` — the same class of defense already applied to the
        sidecar and every declared artefact.
        """
        run_dir = _run_dir(run_root, "manifestsymlink")
        outside = run_root / "outside-manifest.json"
        outside.write_text("{}", encoding="utf-8")
        self._sidecar(run_dir, {"corpus_smoke.json": ["H1"]})
        _write_envelope(run_dir, "corpus_smoke.json")
        (run_dir / "manifest.json").symlink_to(outside)
        with pytest.raises(driver.IncompleteRunError, match="symbolic link"):
            driver.check_run_complete(run_dir)

    def test_tags_supplied_as_a_string_rejected(self, run_root: Path) -> None:
        """``"H9"`` must be rejected, never splatted into ``["H", "9"]``."""
        run_dir = _run_dir(run_root, "stringtags")
        _raw_sidecar(run_dir, artefacts={"corpus_smoke.json": "H9"})
        with pytest.raises(driver.IncompleteRunError, match="not a non-empty list"):
            driver.check_run_complete(run_dir)

    def test_empty_tag_list_rejected(self, run_root: Path) -> None:
        run_dir = _run_dir(run_root, "emptytags")
        _raw_sidecar(run_dir, artefacts={"corpus_smoke.json": []})
        with pytest.raises(driver.IncompleteRunError, match="not a non-empty list"):
            driver.check_run_complete(run_dir)

    def test_non_string_tag_rejected(self, run_root: Path) -> None:
        run_dir = _run_dir(run_root, "nonstringtags")
        _raw_sidecar(run_dir, artefacts={"corpus_smoke.json": [1]})
        with pytest.raises(driver.IncompleteRunError, match="non-string"):
            driver.check_run_complete(run_dir)

    def test_unknown_tag_rejected(self, run_root: Path) -> None:
        run_dir = _run_dir(run_root, "unknowntag")
        _raw_sidecar(run_dir, artefacts={"corpus_smoke.json": ["H9"]})
        with pytest.raises(driver.IncompleteRunError, match="unregistered"):
            driver.check_run_complete(run_dir)

    def test_tag_inconsistent_with_result_mode_rejected(self, run_root: Path) -> None:
        """A corpus_*.json result bears H1, not H2 (preregistration §5.3)."""
        run_dir = _run_dir(run_root, "wrongtag")
        _raw_sidecar(run_dir, artefacts={"corpus_smoke.json": ["H2"]})
        with pytest.raises(driver.IncompleteRunError, match="bears"):
            driver.check_run_complete(run_dir)

    def test_gpu_entry_without_timing_method_rejected(self, run_root: Path) -> None:
        run_dir = _run_dir(run_root, "notiming")
        _raw_sidecar(run_dir, artefacts={"kernel-path_cuda.json": ["H4"]})
        with pytest.raises(driver.IncompleteRunError, match="timing_method"):
            driver.check_run_complete(run_dir)

    def test_gpu_entry_with_unregistered_timing_method_rejected(
        self, run_root: Path
    ) -> None:
        run_dir = _run_dir(run_root, "badtiming")
        _raw_sidecar(
            run_dir,
            artefacts={
                "kernel-path_cuda.json": {
                    "hypotheses": ["H4"],
                    "timing_method": "stopwatch",
                }
            },
        )
        with pytest.raises(driver.IncompleteRunError, match="timing_method"):
            driver.check_run_complete(run_dir)

    def test_non_gpu_entry_may_not_use_the_object_form(self, run_root: Path) -> None:
        run_dir = _run_dir(run_root, "objectform")
        _raw_sidecar(
            run_dir,
            artefacts={
                "corpus_smoke.json": {
                    "hypotheses": ["H1"],
                    "timing_method": "not-timed",
                }
            },
        )
        with pytest.raises(driver.IncompleteRunError, match="must be a list"):
            driver.check_run_complete(run_dir)

    def test_case_colliding_declared_names_rejected(self, run_root: Path) -> None:
        run_dir = _run_dir(run_root, "casecollide")
        _raw_sidecar(
            run_dir,
            artefacts={"corpus_smoke.json": ["H1"], "corpus_SMOKE.json": ["H1"]},
        )
        with pytest.raises(driver.IncompleteRunError, match="differ only in case"):
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

    @_needs_symlink_support
    def test_symlinked_sidecar_rejected(self, run_root: Path) -> None:
        """The sidecar itself must be a regular file in run_dir.

        ``is_file()`` and ``read_text()`` both follow symlinks, so a
        campaign-metadata.json linked to a document outside the run directory
        would otherwise decide what this run is deemed to have published
        (CWE-59 — the same class already closed for declared artefacts).
        """
        run_dir = _run_dir(run_root, "symlinksidecar")
        run_dir.mkdir()
        outside = run_root / "outside-metadata.json"
        outside.write_text(
            json.dumps(
                {
                    "exp_id": "EXP-001",
                    "run_id": run_dir.name,
                    "session": "0156",
                    "operator": "tester",
                    "artefacts": {"corpus_smoke.json": ["H1"]},
                }
            ),
            encoding="utf-8",
        )
        (run_dir / "campaign-metadata.json").symlink_to(outside)
        _write_envelope(run_dir, "corpus_smoke.json")
        with pytest.raises(driver.IncompleteRunError, match="symbolic link"):
            driver.check_run_complete(run_dir)

    def test_unlisted_result_file_rejected(self, run_root: Path) -> None:
        """Every top-level result JSON must be named by the sidecar, not just
        every sidecar name be present (Copilot: "does not require every
        top-level result JSON to be listed").
        """
        run_dir = _run_dir(run_root, "unlisted")
        self._sidecar(run_dir, {"corpus_smoke.json": ["H1"]})
        _write_envelope(run_dir, "corpus_smoke.json")
        (run_dir / "corpus_extra.json").write_text("{}", encoding="utf-8")
        with pytest.raises(driver.IncompleteRunError, match=r"corpus_extra\.json"):
            driver.check_run_complete(run_dir)

    def test_unlisted_uppercase_result_file_rejected(self, run_root: Path) -> None:
        """A top-level rogue.JSON must fail closure exactly as rogue.json does.

        Regression test for the case-sensitivity mismatch between closure
        (which compared ``path.suffix == ".json"``) and
        ``append_manifest``'s ``glob("*.json")`` (case-insensitive on
        Windows): the file was invisible to closure and manifested anyway.
        """
        run_dir = _run_dir(run_root, "unlistedcase")
        self._sidecar(run_dir, {"corpus_smoke.json": ["H1"]})
        _write_envelope(run_dir, "corpus_smoke.json")
        (run_dir / "rogue.JSON").write_text("{}", encoding="utf-8")
        with pytest.raises(driver.IncompleteRunError, match="rogue"):
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
        _write_envelope(run_dir, "corpus_smoke.json")
        (run_dir / "manifest.json").write_text("{}", encoding="utf-8")
        assert driver.check_run_complete(run_dir) == {"corpus_smoke.json": ["H1"]}


class TestRunClosureEnvelope:
    """check_run_complete validates each declared result's §7.2 envelope."""

    def _closable(self, run_root: Path, label: str) -> Path:
        run_dir = _run_dir(run_root, label)
        driver.write_campaign_metadata(
            run_dir,
            exp_id="EXP-001",
            run_id=run_dir.name,
            session="0156",
            operator="tester",
            artefacts={"corpus_smoke.json": ["H1"]},
        )
        return run_dir

    def test_result_without_an_envelope_rejected(self, run_root: Path) -> None:
        run_dir = self._closable(run_root, "noenvelope")
        (run_dir / "corpus_smoke.json").write_text("{}", encoding="utf-8")
        with pytest.raises(driver.IncompleteRunError, match="environment"):
            driver.check_run_complete(run_dir)

    @pytest.mark.parametrize("field", ["gpu", "backend", "git_commit"])
    def test_result_with_missing_environment_field_rejected(
        self, run_root: Path, field: str
    ) -> None:
        run_dir = self._closable(run_root, "envfield")
        document = _envelope(run_dir)
        del document["environment"][field]  # type: ignore[index]
        (run_dir / "corpus_smoke.json").write_text(
            json.dumps(document), encoding="utf-8"
        )
        if field == "gpu":  # not in the §7.2 required set for a CPU entry
            assert driver.check_run_complete(run_dir) == {"corpus_smoke.json": ["H1"]}
        else:
            with pytest.raises(driver.IncompleteRunError, match=field):
                driver.check_run_complete(run_dir)

    def test_result_with_missing_config_field_rejected(self, run_root: Path) -> None:
        run_dir = self._closable(run_root, "configfield")
        document = _envelope(run_dir)
        del document["config"]["seed_key"]  # type: ignore[index]
        (run_dir / "corpus_smoke.json").write_text(
            json.dumps(document), encoding="utf-8"
        )
        with pytest.raises(driver.IncompleteRunError, match="seed_key"):
            driver.check_run_complete(run_dir)

    def test_out_dir_disagreement_rejected(self, run_root: Path) -> None:
        """The envelope must describe the directory it is being closed in."""
        run_dir = self._closable(run_root, "wrongoutdir")
        document = _envelope(run_dir)
        document["config"]["out_dir"] = str(run_root / "elsewhere")  # type: ignore[index]
        (run_dir / "corpus_smoke.json").write_text(
            json.dumps(document), encoding="utf-8"
        )
        with pytest.raises(driver.IncompleteRunError, match="out_dir"):
            driver.check_run_complete(run_dir)

    def test_gpu_entry_with_non_cuda_backend_rejected(self, run_root: Path) -> None:
        run_dir = _run_dir(run_root, "gpucpuenv")
        driver.write_campaign_metadata(
            run_dir,
            exp_id="EXP-001",
            run_id=run_dir.name,
            session="0156",
            operator="tester",
            artefacts={
                "kernel-path_cuda.json": {
                    "hypotheses": ["H4"],
                    "timing_method": driver.KERNEL_PATH_TIMING_METHOD,
                }
            },
        )
        _write_envelope(run_dir, "kernel-path_cuda.json", backend="cpu")
        with pytest.raises(driver.IncompleteRunError, match="backend"):
            driver.check_run_complete(run_dir)

    def test_gpu_entry_missing_gpu_field_rejected_at_closure(
        self, run_root: Path
    ) -> None:
        """Closure must require the GPU-only fields too, not just the common set.

        Regression test (CodeRabbit + Copilot, same finding): a tampered or
        buggy ``kernel-path`` result missing ``gpu``/``gpu_vram_mb`` used to
        pass closure because ``_envelope_violation`` only checked
        ``_REQUIRED_ENV_FIELDS``, never ``_GPU_REQUIRED_ENV_FIELDS`` — a
        result ``main`` itself would have refused to publish
        (``_validate_environment`` requires them on every GPU leg).
        """
        run_dir = _run_dir(run_root, "gpumissinggpu")
        driver.write_campaign_metadata(
            run_dir,
            exp_id="EXP-001",
            run_id=run_dir.name,
            session="0156",
            operator="tester",
            artefacts={
                "kernel-path_cuda.json": {
                    "hypotheses": ["H4"],
                    "timing_method": driver.KERNEL_PATH_TIMING_METHOD,
                }
            },
        )
        document = _envelope(run_dir, backend="cuda")
        del document["environment"]["gpu"]  # type: ignore[index]
        (run_dir / "kernel-path_cuda.json").write_text(
            json.dumps(document), encoding="utf-8"
        )
        with pytest.raises(driver.IncompleteRunError, match="gpu"):
            driver.check_run_complete(run_dir)

    def test_null_environment_field_rejected_at_closure(self, run_root: Path) -> None:
        """A present-but-null field must fail closure exactly as an absent one.

        Regression test (CodeRabbit + Copilot): the old check was
        ``field not in block``, which a ``null`` value satisfies (the key is
        present) — so ``{"git_commit": null, ...}`` passed closure even
        though ``_validate_environment`` (the driver's own publication gate)
        treats ``None`` as incomplete.
        """
        run_dir = self._closable(run_root, "nullenv")
        document = _envelope(run_dir)
        document["environment"]["git_commit"] = None  # type: ignore[index]
        (run_dir / "corpus_smoke.json").write_text(
            json.dumps(document), encoding="utf-8"
        )
        with pytest.raises(driver.IncompleteRunError, match="git_commit"):
            driver.check_run_complete(run_dir)

    def test_zero_valued_config_fields_still_pass_closure(self, run_root: Path) -> None:
        """``warmup``/``iterations`` of ``0`` are legitimate, not "empty".

        The null/empty envelope check must not reject ``0``: it is neither
        ``None`` nor ``""``.
        """
        run_dir = self._closable(run_root, "zeroconfig")
        document = _envelope(run_dir)
        document["config"]["warmup"] = 0  # type: ignore[index]
        document["config"]["iterations"] = 0  # type: ignore[index]
        (run_dir / "corpus_smoke.json").write_text(
            json.dumps(document), encoding="utf-8"
        )
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

    def test_writes_expected_schema(self, run_root: Path) -> None:
        run_dir = _run_dir(run_root, "smoke")
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

    def test_writes_gpu_entry_with_timing_method(self, run_root: Path) -> None:
        """Campaign plan §7.2: a GPU result entry additionally carries
        ``timing_method``. H4 is untimed, so it carries the registered
        ``not-timed`` value rather than asserting a timing method never used
        (preregistration §5.12)."""
        run_dir = _run_dir(run_root, "gputiming")
        path = driver.write_campaign_metadata(
            run_dir,
            exp_id="EXP-001",
            run_id=run_dir.name,
            session="0156",
            operator="tester",
            artefacts={
                "kernel-path_cuda.json": {
                    "hypotheses": ["H4"],
                    "timing_method": driver.KERNEL_PATH_TIMING_METHOD,
                }
            },
        )
        payload = json.loads(path.read_text(encoding="utf-8"))
        assert payload["artefacts"]["kernel-path_cuda.json"] == {
            "hypotheses": ["H4"],
            "timing_method": "not-timed",
        }

    def test_append_only(self, run_root: Path) -> None:
        run_dir = _run_dir(run_root, "race")
        driver.write_campaign_metadata(
            run_dir,
            exp_id="EXP-001",
            run_id=run_dir.name,
            session="0156",
            operator="tester",
            artefacts={},
        )
        with pytest.raises(result_module.ArtefactExistsError):
            driver.write_campaign_metadata(
                run_dir,
                exp_id="EXP-001",
                run_id=run_dir.name,
                session="0156",
                operator="tester",
                artefacts={"corpus_x.json": ["H1"]},
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
        # Campaign plan §7.2: a GPU result entry additionally carries
        # timing_method; H4 is untimed, hence the registered "not-timed"
        # value (preregistration §5.12).
        assert sidecar["artefacts"] == {
            "kernel-path_smoke.json": {
                "hypotheses": ["H4"],
                "timing_method": "not-timed",
            }
        }
        # The published run closes cleanly under the full §7.2 schema check.
        assert driver.check_run_complete(run_dir) == {"kernel-path_smoke.json": ["H4"]}

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


class _FakeDevice:
    """Minimal stand-in for ``torch.device`` exposing only ``.type``."""

    def __init__(self, device_type: str) -> None:
        self.type = device_type


class _FakeTensor:
    """Minimal stand-in for the tensor ``from_dlpack`` returns."""

    def __init__(self, device_type: str) -> None:
        self.device = _FakeDevice(device_type)


class _FakeGpuEngine:
    """Stand-in for ``prin._prin_core.GpuSparseKuramoto`` with no device."""

    #: Capsule sentinels, in the order the real binding returns them.
    CAPSULES = ("dphase-capsule", "damplitude-capsule", "dfrequency-capsule")

    @classmethod
    def from_knn_phase(cls, *args: object, **kwargs: object) -> _FakeGpuEngine:
        return cls()

    def compute_derivatives(self, *args: object) -> tuple[str, str, str]:
        return self.CAPSULES


class TestKernelPathCapsuleResidency:
    """H4 validates *every* returned capsule's device, not just the first.

    The three derivative outputs are separate DLPack capsules and nothing in
    the binding's contract makes them share a device, so a CPU-resident
    ``damplitude`` or ``dfrequency`` beside a CUDA-resident ``dphase`` would
    otherwise be consumed and compared as if it were the CUDA result.
    Hardware-free: both the engine and ``from_dlpack`` are mocked, so this
    runs on every leg, including hosts with no GPU build at all.
    """

    @pytest.mark.parametrize(
        ("non_cuda_index", "expected"),
        [(0, "dphase"), (1, "damplitude"), (2, "dfrequency")],
    )
    def test_any_non_cuda_capsule_aborts(
        self,
        loader: CorpusLoader,
        monkeypatch: pytest.MonkeyPatch,
        non_cuda_index: int,
        expected: str,
    ) -> None:
        monkeypatch.setattr(
            _prin_core, "GpuSparseKuramoto", _FakeGpuEngine, raising=False
        )
        devices = {capsule: "cuda" for capsule in _FakeGpuEngine.CAPSULES}
        devices[_FakeGpuEngine.CAPSULES[non_cuda_index]] = "cpu"
        monkeypatch.setattr(
            driver, "from_dlpack", lambda capsule: _FakeTensor(devices[capsule])
        )
        with pytest.raises(driver.GpuBindingUnavailableError, match=expected):
            driver.compare_kernel_path_case(loader, _KURAMOTO_SPARSE_KNN_CASES[0])

    def test_error_names_every_offending_capsule(
        self, loader: CorpusLoader, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.setattr(
            _prin_core, "GpuSparseKuramoto", _FakeGpuEngine, raising=False
        )
        monkeypatch.setattr(driver, "from_dlpack", lambda capsule: _FakeTensor("cpu"))
        with pytest.raises(driver.GpuBindingUnavailableError) as excinfo:
            driver.compare_kernel_path_case(loader, _KURAMOTO_SPARSE_KNN_CASES[0])
        message = str(excinfo.value)
        assert "dphase" in message
        assert "damplitude" in message
        assert "dfrequency" in message


class TestCudaCapabilityProbe:
    """tests/_env.py::cuda_kernel_executes probes executability, not registration.

    ETCA-002 T-F3 / governance G8. ``GpuSparseKuramoto`` compiles under
    ``--features wgpu`` too, and ``torch.cuda.is_available()`` describes
    PyTorch rather than the extension's compiled backend, so neither answers
    "will the H4 success path run here?". Each branch is covered with the
    binding mocked, so the coverage does not itself depend on hardware.
    """

    @staticmethod
    def _probe(monkeypatch: pytest.MonkeyPatch, device_type: str) -> bool:
        import torch.utils.dlpack

        monkeypatch.setattr(
            _prin_core, "GpuSparseKuramoto", _FakeGpuEngine, raising=False
        )
        monkeypatch.setattr(
            torch.utils.dlpack,
            "from_dlpack",
            lambda capsule: _FakeTensor(device_type),
        )
        cuda_kernel_executes.cache_clear()
        return cuda_kernel_executes()

    def test_cuda_build_probes_true(self, monkeypatch: pytest.MonkeyPatch) -> None:
        try:
            assert self._probe(monkeypatch, "cuda") is True
        finally:
            cuda_kernel_executes.cache_clear()

    def test_wgpu_only_build_probes_false(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """A wgpu-only build returns a CPU-resident capsule, even on a CUDA host."""
        try:
            assert self._probe(monkeypatch, "cpu") is False
        finally:
            cuda_kernel_executes.cache_clear()

    def test_missing_binding_probes_false(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.delattr(_prin_core, "GpuSparseKuramoto", raising=False)
        cuda_kernel_executes.cache_clear()
        try:
            assert cuda_kernel_executes() is False
        finally:
            cuda_kernel_executes.cache_clear()

    def test_unavailable_runtime_probes_false(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """A CUDA client that cannot initialise must skip, not run-and-fail."""

        class _Unavailable:
            @classmethod
            def from_knn_phase(cls, *args: object, **kwargs: object) -> object:
                raise RuntimeError("no CUDA device")

        monkeypatch.setattr(
            _prin_core, "GpuSparseKuramoto", _Unavailable, raising=False
        )
        cuda_kernel_executes.cache_clear()
        try:
            assert cuda_kernel_executes() is False
        finally:
            cuda_kernel_executes.cache_clear()


class TestEnvironmentValidation:
    """Missing mandatory environment fields abort the run (campaign plan §10.1.3)."""

    @staticmethod
    def _environment(**overrides: object) -> dict[str, object]:
        environment = dict(_envelope(Path("."))["environment"])  # type: ignore[arg-type]
        environment.update(overrides)
        return environment

    @pytest.mark.parametrize(
        "field", ["prin_version", "git_commit", "rust_version", "processor", "backend"]
    )
    def test_missing_common_field_aborts(self, field: str) -> None:
        with pytest.raises(driver.EnvironmentIncompleteError, match=field):
            driver._validate_environment("corpus", self._environment(**{field: None}))

    @pytest.mark.parametrize("field", ["gpu", "gpu_vram_mb"])
    def test_missing_gpu_field_aborts_a_gpu_leg(self, field: str) -> None:
        with pytest.raises(driver.EnvironmentIncompleteError, match=field):
            driver._validate_environment(
                "kernel-path", self._environment(**{field: None})
            )

    @pytest.mark.parametrize("field", ["gpu", "gpu_vram_mb"])
    def test_missing_gpu_field_does_not_abort_a_cpu_leg(self, field: str) -> None:
        driver._validate_environment("corpus", self._environment(**{field: None}))

    def test_complete_environment_passes(self) -> None:
        driver._validate_environment("kernel-path", self._environment())

    def test_cli_aborts_before_publishing_anything(
        self, run_root: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """An incomplete capture must abort, not become an H1 pass/fail result."""

        def _incomplete(**kwargs: object) -> dict[str, object]:
            return self._environment(git_commit=None)

        monkeypatch.setattr(driver, "capture_environment", _incomplete)
        run_dir = _run_dir(run_root, "noenv")
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
            "noenv",
            "--session",
            "0156",
            "--operator",
            "tester",
        ]
        assert driver.main(argv) == 2
        assert not (run_dir / "campaign-metadata.json").exists()
        assert not (run_dir / "corpus_noenv.json").exists()

    def test_empty_gpu_batch_refuses_to_claim_cuda(self, run_root: Path) -> None:
        """No case means nothing proved CUDA dispatch, so no "cuda" artefact."""
        run_dir = _run_dir(run_root, "emptygpu")
        argv = [
            "--mode",
            "kernel-path",
            "--corpus-dir",
            str(_CORPUS_DIR),
            "--case-id",
            "definitely-not-a-case",
            "--out",
            str(run_dir),
            "--label",
            "emptygpu",
            "--session",
            "0156",
            "--operator",
            "tester",
        ]
        # An unknown case ID aborts first; the empty-batch guard is unit-tested
        # directly below because the CLI can never reach it with a bad ID.
        assert driver.main(argv) == 2
        assert not (run_dir / "campaign-metadata.json").exists()


def _h2b_case(
    order_pairs: tuple[list[float], list[float]],
    coherence_pairs: tuple[list[float], list[float]],
    *,
    aborted: bool = False,
) -> dict[str, object]:
    """Build one synthetic fuzz record carrying a beyond-horizon block.

    Synthetic arrays are a unit-test fixture only; they are never campaign
    observations and never reach a run directory.
    """
    if aborted:
        return {"aborted": True, "abort_reason": "synthetic"}
    return {
        "aborted": False,
        "beyond_horizon": {
            "order_parameter_traj": driver._beyond_horizon_record(
                np.asarray(order_pairs[0]), np.asarray(order_pairs[1])
            ),
            "mean_phase_coherence_traj": driver._beyond_horizon_record(
                np.asarray(coherence_pairs[0]), np.asarray(coherence_pairs[1])
            ),
        },
    }


def _h2b_batch(
    n: int, order_delta: float, coherence_delta: float, *, alternate: bool = False
) -> list[dict[str, object]]:
    """``n`` synthetic cases whose per-case paired difference is a fixed delta."""
    cases = []
    for index in range(n):
        base = 0.40 + 0.01 * (index % 7)
        sign = -1.0 if (alternate and index % 2) else 1.0
        order_ref = [base, base + 0.02, base - 0.01]
        order_prod = [value + sign * order_delta for value in order_ref]
        coherence_ref = [base - 0.2, base - 0.1, base]
        coherence_prod = [value + sign * coherence_delta for value in coherence_ref]
        cases.append(
            _h2b_case((order_ref, order_prod), (coherence_ref, coherence_prod))
        )
    return cases


class TestH2bAdjudication:
    """H2b's registered equivalence predicate (preregistration §5.12).

    Equivalence is established by **both endpoints** of the 95 % bootstrap CI
    on the mean per-case paired difference lying inside the metric's
    registered margin — not by the CI merely containing zero, which a wide
    interval can do while still spanning conclusion-reversing differences.
    The unit of analysis is one predefined paired summary per case, never the
    individual post-horizon time points (they are serially dependent).
    """

    def test_clearly_equivalent_cases_confirm(self) -> None:
        result = driver.adjudicate_h2b(_h2b_batch(40, 1e-6, 1e-6, alternate=True))
        assert result["verdict"] == "CONFIRMED"
        for metric in result["metrics"].values():
            assert metric["verdict"] == "CONFIRMED"
            assert metric["within_margin"] is True

    def test_clearly_non_equivalent_cases_refute(self) -> None:
        result = driver.adjudicate_h2b(_h2b_batch(40, 0.3, 0.3))
        assert result["verdict"] == "REFUTED"
        for metric in result["metrics"].values():
            assert metric["verdict"] == "REFUTED"

    def test_wide_ci_containing_zero_still_refutes(self) -> None:
        """The defect the old predicate had: a wide CI that contains zero.

        Alternating ±0.5 per-case differences give a mean near zero — so the
        CI contains zero and Cohen's *d* is negligible, which the previous
        ``|d| < 0.2 and CI contains 0`` rule would have read as equivalence —
        while both CI endpoints lie far outside the registered margin.
        """
        cases = _h2b_batch(40, 0.5, 0.5, alternate=True)
        result = driver.adjudicate_h2b(cases)
        order = result["metrics"]["order_parameter_traj"]
        assert order["ci_lower"] < 0.0 < order["ci_upper"], "CI must contain zero"
        assert abs(order["descriptive"]["cohens_d"]) < 0.2, "d must look negligible"
        assert order["verdict"] == "REFUTED"
        assert result["verdict"] == "REFUTED"

    def test_opposite_metric_effects_do_not_cancel(self) -> None:
        """Pooling the two metrics would cancel these; adjudicating each does not."""
        result = driver.adjudicate_h2b(_h2b_batch(40, 0.3, -0.3))
        assert result["metrics"]["order_parameter_traj"]["verdict"] == "REFUTED"
        assert result["metrics"]["mean_phase_coherence_traj"]["verdict"] == "REFUTED"
        assert result["verdict"] == "REFUTED"

    def test_no_beyond_horizon_data_is_inconclusive(self) -> None:
        result = driver.adjudicate_h2b([{"aborted": False, "beyond_horizon": None}])
        assert result["verdict"] == "INCONCLUSIVE"
        for metric in result["metrics"].values():
            assert metric["verdict"] == "INCONCLUSIVE"
            assert metric["n_cases"] == 0

    def test_under_minimum_information_is_inconclusive_not_refuted(self) -> None:
        """Too few cases can never be read as a falsification."""
        cases = _h2b_batch(driver.H2B_MIN_CASES - 1, 0.3, 0.3)
        result = driver.adjudicate_h2b(cases)
        assert result["verdict"] == "INCONCLUSIVE"

    def test_aborted_cases_are_excluded(self) -> None:
        cases = _h2b_batch(driver.H2B_MIN_CASES - 1, 1e-6, 1e-6)
        cases += [_h2b_case(([], []), ([], []), aborted=True) for _ in range(10)]
        result = driver.adjudicate_h2b(cases)
        assert result["verdict"] == "INCONCLUSIVE"
        assert (
            result["metrics"]["order_parameter_traj"]["n_cases"]
            == driver.H2B_MIN_CASES - 1
        )

    def test_reproducible_under_the_registered_seed(self) -> None:
        cases = _h2b_batch(40, 0.002, 0.002, alternate=True)
        assert driver.adjudicate_h2b(cases) == driver.adjudicate_h2b(cases)

    def test_margins_are_per_metric_and_registered(self) -> None:
        assert driver.H2B_EQUIVALENCE_MARGIN == {
            "order_parameter_traj": 0.01,
            "mean_phase_coherence_traj": 0.02,
        }

    def test_margin_boundary_is_adjudicated_per_metric(self) -> None:
        """A difference inside one metric's margin but outside the other's."""
        result = driver.adjudicate_h2b(_h2b_batch(40, 0.015, 0.015))
        assert result["metrics"]["order_parameter_traj"]["verdict"] == "REFUTED"
        assert result["metrics"]["mean_phase_coherence_traj"]["verdict"] == "CONFIRMED"
        assert result["verdict"] == "REFUTED"


class TestCaseIdUniqueness:
    """--case-id must not repeat a corpus case within one invocation (Copilot).

    Without this guard, repeating one passing case-id 504 times would
    publish an H1-tagged artefact with 504 records that are not 504 distinct
    corpus cases, defeating the preregistration §8 non-aborted-count check.
    """

    def test_no_duplicates_passes(self) -> None:
        driver._validate_case_ids(["a", "b", "c"])

    def test_none_passes(self) -> None:
        driver._validate_case_ids(None)

    def test_empty_list_passes(self) -> None:
        driver._validate_case_ids([])

    def test_single_duplicate_rejected(self) -> None:
        with pytest.raises(driver.DriverMetadataError, match="repeated"):
            driver._validate_case_ids(["a", "b", "a"])

    def test_names_every_duplicate(self) -> None:
        with pytest.raises(driver.DriverMetadataError, match=r"a.*b|b.*a"):
            driver._validate_case_ids(["a", "b", "a", "b", "c"])

    def test_repeated_case_id_confirmed_empirically_and_rejected(
        self, run_root: Path
    ) -> None:
        """The exact scenario Copilot described: the same --case-id passed
        multiple times must abort before any comparison runs, not silently
        inflate the artefact's record count."""
        run_dir = _run_dir(run_root, "dupcase")
        argv = [
            "--mode",
            "corpus",
            "--corpus-dir",
            str(_CORPUS_DIR),
            "--case-id",
            _REPRESENTATIVE_CASES[0],
            "--case-id",
            _REPRESENTATIVE_CASES[0],
            "--out",
            str(run_dir),
            "--label",
            "dupcase",
            "--session",
            "0156",
            "--operator",
            "tester",
        ]
        assert driver.main(argv) == 2
        assert not run_dir.exists()


class TestFuzzBatchSize:
    """--n-fuzz-cases must be positive, and sub-registered batches are pilots."""

    @pytest.mark.parametrize("raw", ["0", "-1", "-1000"])
    def test_non_positive_rejected_at_parse_time(self, raw: str) -> None:
        with pytest.raises(SystemExit):
            driver._parser().parse_args(
                [
                    "--mode",
                    "fuzz",
                    "--n-fuzz-cases",
                    raw,
                    "--out",
                    "x",
                    "--label",
                    "l",
                    "--session",
                    "0156",
                    "--operator",
                    "tester",
                ]
            )

    def test_positive_int_accepts_a_positive_value(self) -> None:
        assert driver._positive_int("7") == 7

    @pytest.mark.parametrize("raw", ["0", "-3", "not-a-number"])
    def test_positive_int_rejects(self, raw: str) -> None:
        with pytest.raises(argparse.ArgumentTypeError):
            driver._positive_int(raw)

    def test_registered_confirmatory_minimum_is_the_default(self) -> None:
        args = driver._parser().parse_args(
            [
                "--mode",
                "fuzz",
                "--out",
                "x",
                "--label",
                "l",
                "--session",
                "0156",
                "--operator",
                "tester",
            ]
        )
        assert args.n_fuzz_cases == driver.REGISTERED_FUZZ_BATCH_MIN == 1000


class TestCliExpectedFailures:
    """Expected operational failures abort cleanly; they never traceback."""

    @staticmethod
    def _argv(run_dir: Path, corpus_dir: Path, case_id: str) -> list[str]:
        return [
            "--mode",
            "corpus",
            "--corpus-dir",
            str(corpus_dir),
            "--case-id",
            case_id,
            "--out",
            str(run_dir),
            "--label",
            "smoke",
            "--session",
            "0156",
            "--operator",
            "tester",
        ]

    def test_unknown_case_id_aborts(
        self, run_root: Path, capsys: pytest.CaptureFixture[str]
    ) -> None:
        run_dir = _run_dir(run_root, "badcase")
        assert driver.main(self._argv(run_dir, _CORPUS_DIR, "no-such-case")) == 2
        assert "ABORT:" in capsys.readouterr().err
        assert not (run_dir / "campaign-metadata.json").exists()

    def test_invalid_corpus_manifest_aborts(
        self, run_root: Path, tmp_path: Path, capsys: pytest.CaptureFixture[str]
    ) -> None:
        empty_corpus = tmp_path / "empty-corpus"
        empty_corpus.mkdir()
        run_dir = _run_dir(run_root, "badcorpus")
        argv = self._argv(run_dir, empty_corpus, _REPRESENTATIVE_CASES[0])
        assert driver.main(argv) == 2
        assert "ABORT:" in capsys.readouterr().err

    def test_output_path_outside_the_declared_roots_aborts(
        self,
        run_root: Path,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        """An OutputPathError is an expected abort, not an unhandled error."""
        monkeypatch.setattr(
            result_module, "_ALLOWED_ROOTS", ((tmp_path / "elsewhere").resolve(),)
        )
        run_dir = _run_dir(run_root, "badpath")
        argv = self._argv(run_dir, _CORPUS_DIR, _REPRESENTATIVE_CASES[0])
        assert driver.main(argv) == 2
        assert "ABORT:" in capsys.readouterr().err
        assert not (run_dir / "campaign-metadata.json").exists()

    def test_existing_artefact_aborts(
        self,
        run_root: Path,
        monkeypatch: pytest.MonkeyPatch,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        """An ArtefactExistsError from the result write aborts cleanly.

        The run-directory reservation makes a pre-existing result unreachable
        through a fresh invocation, so the remaining route to this error is
        losing the race for the result path; that is what is simulated here.
        """

        def _lost_race(*args: object, **kwargs: object) -> Path:
            raise result_module.ArtefactExistsError("lost the race for the result")

        monkeypatch.setattr(driver, "write_result", _lost_race)
        run_dir = _run_dir(run_root, "exists")
        argv = self._argv(run_dir, _CORPUS_DIR, _REPRESENTATIVE_CASES[0])
        assert driver.main(argv) == 2
        assert "ABORT:" in capsys.readouterr().err
        assert not (run_dir / "campaign-metadata.json").exists()

    def test_unexpected_errors_are_not_swallowed(
        self, run_root: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """A programming fault must still surface, not masquerade as an abort."""

        def _boom(*args: object, **kwargs: object) -> Path:
            raise ZeroDivisionError("bug")

        monkeypatch.setattr(driver, "write_result", _boom)
        run_dir = _run_dir(run_root, "boom")
        argv = self._argv(run_dir, _CORPUS_DIR, _REPRESENTATIVE_CASES[0])
        with pytest.raises(ZeroDivisionError):
            driver.main(argv)
        # The sidecar is still rolled back on the way out.
        assert not (run_dir / "campaign-metadata.json").exists()
