"""Differential parity: PRIN vs PRINet 3.0.0 subconscious controller.

Installs nothing and mocks nothing — it imports the archived ``prinet`` 3.0.0
package alongside the new build and compares them end to end:

1. ``SubconsciousState.to_tensor`` — asserted **bit-exactly** (identical
   IEEE-754 binary32 patterns), because the packing is pure arithmetic with no
   iteration and no accumulation.
2. ``ControlSignals.from_tensor`` — asserted **exactly** on every field,
   including the clamp behaviour and ``preferred_regime`` tie-breaking.
3. The full inference pipeline (state encode → ONNX session → control decode)
   — asserted **bit-exactly** on the CPU execution provider, since both
   implementations feed identical float32 input to the same graph in the same
   runtime.
4. Backend selection — PRIN's priority order and provider chains are compared
   against ``prinet.utils.npu_backend``'s, with PRIN's deliberate improvement
   (a deterministic fallback ladder instead of a raise or a silent
   substitution) asserted explicitly.

Run with ``pytest parity/test_parity_subconscious.py``; every test skips
cleanly when the archived reference is not importable.
"""

from __future__ import annotations

import numpy as np
import pytest

prinet = pytest.importorskip("prinet")

from prinet.core import subconscious as ref_subconscious
from prinet.utils import npu_backend as ref_backend

from prin.daemon import (
    ControlSignals,
    SubconsciousController,
    SubconsciousState,
    backend_priority,
    backend_provider_names,
    create_session,
    default_model_path,
    select_backend,
)

pytestmark = pytest.mark.parity

CPU = "CPUExecutionProvider"


def _telemetry_cases(count: int = 48) -> list[dict[str, object]]:
    """Deterministic telemetry keyword sets shared by both implementations."""
    rng = np.random.default_rng(1090280)
    regimes = ["mean_field", "sparse_knn", "full", "chimera"]
    cases: list[dict[str, object]] = []
    for index in range(count):
        cases.append(
            {
                "r_per_band": [float(x) for x in rng.random(3)],
                "r_global": float(rng.random()),
                "loss_ema": float(rng.normal() * 2.0),
                "loss_variance": float(rng.random()),
                "grad_norm_ema": float(rng.random() * 10.0),
                "lr_current": float(rng.random() * 1e-2),
                "scalr_alpha": float(rng.random() * 2.0),
                "gpu_temp": float(rng.random() * 100.0),
                "gpu_util": float(rng.random()),
                "vram_pct": float(rng.random()),
                "cpu_util": float(rng.random()),
                "step_latency_p50": float(rng.random()),
                "step_latency_p95": float(rng.random()),
                "throughput": float(rng.random() * 1e5),
                "epoch": int(rng.integers(0, 10_000)),
                # Index 3 is an unrecognised regime name, exercising the
                # reference's silent fall-back to index 0.
                "regime": regimes[index % 4],
                "timestamp": float(rng.random() * 2e9 - 5e8),
            }
        )
    return cases


CASES = _telemetry_cases()

EDGE_CASES: list[dict[str, object]] = [
    {},
    {"r_per_band": []},
    {"r_per_band": [0.5]},
    {"r_per_band": [0.1, 0.2, 0.3, 0.4]},
    {"timestamp": -1.0},
    {"timestamp": 0.0},
    {"timestamp": 86_399.999},
    {"epoch": -5},
    {"gpu_temp": 100.0, "throughput": 1e4},
    {"regime": "sparse_knn"},
    {"regime": "full"},
    {"regime": "not_a_regime"},
]


class TestStateEncoding:
    """Reference-vs-PRIN comparison of `SubconsciousState.to_tensor`."""

    @pytest.mark.parametrize("case", CASES, ids=range(len(CASES)))
    def test_state_vector_is_bit_identical(self, case):
        """Random telemetry packs to identical float32 bit patterns."""
        reference = ref_subconscious.SubconsciousState(**case).to_tensor()
        actual = SubconsciousState(**case).to_tensor()
        assert actual.dtype == reference.dtype == np.float32
        assert actual.shape == reference.shape
        assert np.array_equal(actual.view(np.uint32), reference.view(np.uint32)), (
            f"bit pattern differs: {actual!r} vs {reference!r}"
        )

    @pytest.mark.parametrize("case", EDGE_CASES, ids=range(len(EDGE_CASES)))
    def test_edge_cases_are_bit_identical(self, case):
        """Padding, band-length, regime, and timestamp edges agree exactly."""
        reference = ref_subconscious.SubconsciousState(**case).to_tensor()
        actual = SubconsciousState(**case).to_tensor()
        assert np.array_equal(actual.view(np.uint32), reference.view(np.uint32))

    def test_dimension_constants_match(self):
        """STATE_DIM and CONTROL_DIM match the reference module."""
        assert SubconsciousState().to_tensor().shape[0] == ref_subconscious.STATE_DIM
        assert ref_subconscious.STATE_DIM == 32
        assert ref_subconscious.CONTROL_DIM == 8

    def test_default_states_agree(self):
        """The default dataclass packs identically in both implementations."""
        reference = ref_subconscious.SubconsciousState().to_tensor()
        assert np.array_equal(
            SubconsciousState().to_tensor().view(np.uint32),
            reference.view(np.uint32),
        )


class TestControlDecoding:
    """Reference-vs-PRIN comparison of `ControlSignals.from_tensor`."""

    @staticmethod
    def _fields(control) -> list[float]:
        return [
            control.suggested_K_min,
            control.suggested_K_max,
            control.lr_multiplier,
            control.regime_mf_weight,
            control.regime_sk_weight,
            control.regime_full_weight,
            control.alert_level,
            control.coupling_mode_suggestion,
        ]

    def test_random_outputs_decode_identically(self):
        """Random controller outputs decode to identical field values."""
        rng = np.random.default_rng(28)
        for _ in range(128):
            raw = (rng.random(8, dtype=np.float64) * 24.0 - 12.0).astype(np.float32)
            reference = ref_subconscious.ControlSignals.from_tensor(raw)
            actual = ControlSignals.from_tensor(raw.astype(np.float64))
            assert self._fields(actual) == self._fields(reference)
            assert actual.preferred_regime == reference.preferred_regime
            assert actual.is_finite() == reference.is_finite()

    @pytest.mark.parametrize(
        "raw",
        [
            [0.0] * 8,
            [0.25, 9.75, 42.0, 0.2, 0.3, 0.5, 7.5, -3.25],
            [-1.0, 0.0, -5.0, 0.1, 0.1, 0.8, -0.5, 2.0],
            [0.1, 3.3, 0.9999, 1 / 3, 1 / 3, 1 / 3, 0.6666666, 1e-8],
            [1.0, 1.0, 0.1, 0.5, 0.5, 0.5, 1.0, 0.0],
            [1.0, 1.0, 10.0, 0.0, 0.0, 0.0, 0.0, 0.0],
        ],
    )
    def test_clamps_and_ties_decode_identically(self, raw):
        """Clamped channels and regime ties resolve the same way."""
        array = np.asarray(raw, dtype=np.float32)
        reference = ref_subconscious.ControlSignals.from_tensor(array)
        actual = ControlSignals.from_tensor(array.astype(np.float64))
        assert self._fields(actual) == self._fields(reference)
        assert actual.preferred_regime == reference.preferred_regime

    def test_non_finite_outputs_decode_identically(self):
        """NaN and infinity propagate identically through the decode."""
        raw = np.array(
            [np.nan, np.inf, np.nan, 0.0, 0.0, 0.0, np.nan, -np.inf],
            dtype=np.float32,
        )
        reference = ref_subconscious.ControlSignals.from_tensor(raw)
        actual = ControlSignals.from_tensor(raw.astype(np.float64))
        for a, e in zip(self._fields(actual), self._fields(reference), strict=True):
            assert (np.isnan(a) and np.isnan(e)) or a == e
        assert actual.is_finite() == reference.is_finite() is False

    def test_short_arrays_are_rejected_by_both(self):
        """Both implementations reject an under-width control tensor."""
        short = np.zeros(7, dtype=np.float32)
        with pytest.raises(ValueError):
            ref_subconscious.ControlSignals.from_tensor(short)
        with pytest.raises(ValueError):
            ControlSignals.from_tensor(short.astype(np.float64))

    def test_defaults_agree(self):
        """The default control signals match field for field."""
        reference = ref_subconscious.ControlSignals()
        actual = ControlSignals()
        assert self._fields(actual) == self._fields(reference)
        assert actual.preferred_regime == reference.preferred_regime


class TestInferencePipeline:
    """End-to-end: identical encode, identical graph, identical decode."""

    @staticmethod
    @pytest.fixture(scope="class")
    def reference_session():
        """A PRINet 3.0.0 CPU session over the committed controller graph."""
        return ref_backend.create_session(str(default_model_path()), "cpu")

    @staticmethod
    @pytest.fixture(scope="class")
    def controller():
        """A PRIN controller pinned to the same CPU provider."""
        return SubconsciousController(backend="cpu")

    def test_reference_session_runs_on_cpu(self, reference_session):
        """The reference session used for comparison is CPU-backed."""
        assert reference_session.get_providers() == [CPU]

    def test_graph_io_names_agree(self, reference_session, controller):
        """Both implementations see the same graph input/output names."""
        assert [i.name for i in reference_session.get_inputs()] == [
            spec["name"] for spec in controller.graph["inputs"]
        ]
        assert [o.name for o in reference_session.get_outputs()] == [
            spec["name"] for spec in controller.graph["outputs"]
        ]

    def test_pipeline_outputs_are_bit_identical_on_cpu(
        self, reference_session, controller
    ):
        """The whole encode/run pipeline agrees bit-for-bit on CPU."""
        for case in CASES:
            ref_state = ref_subconscious.SubconsciousState(**case)
            ref_vector = ref_state.to_tensor().reshape(1, -1)
            ref_raw = reference_session.run(None, {"state_vector": ref_vector})[0]

            prin_state = SubconsciousState(**case)
            prin_raw = controller.run(prin_state.to_tensor().reshape(1, -1))

            assert np.array_equal(prin_raw.view(np.uint32), ref_raw.view(np.uint32)), (
                "controller output bit patterns differ on the CPU provider"
            )

    def test_decoded_control_signals_are_identical_on_cpu(
        self, reference_session, controller
    ):
        """Decoded control signals agree field for field on CPU."""
        fields = TestControlDecoding._fields
        for case in CASES:
            ref_state = ref_subconscious.SubconsciousState(**case)
            ref_raw = reference_session.run(
                None, {"state_vector": ref_state.to_tensor().reshape(1, -1)}
            )[0]
            ref_control = ref_subconscious.ControlSignals.from_tensor(ref_raw)

            prin_control = controller.predict(SubconsciousState(**case))
            assert fields(prin_control) == fields(ref_control)
            assert prin_control.preferred_regime == ref_control.preferred_regime


class TestBackendSelectionParity:
    """Reference-vs-PRIN comparison of execution-provider selection."""

    def test_provider_names_agree(self):
        """Provider names match the reference's ONNX Runtime identifiers."""
        assert backend_provider_names("npu") == [
            "VitisAIExecutionProvider",
            CPU,
        ]
        assert backend_provider_names("directml") == ["DmlExecutionProvider", CPU]
        assert backend_provider_names("cpu") == [CPU]

    def test_provider_chains_match_the_reference_builder(self):
        """Each provider chain matches `_build_provider_list`."""
        for backend in backend_priority():
            ref_providers, _ = ref_backend._build_provider_list(backend)
            assert list(backend_provider_names(backend)) == list(ref_providers)

    def test_priority_order_matches_the_reference(self):
        """Auto-detection follows the reference's VitisAI/DirectML/CPU order."""
        # prinet's detect_best_backend: VitisAI, then DirectML, then CPU.
        assert backend_priority() == ["npu", "directml", "cpu"]
        combinations = [
            (["VitisAIExecutionProvider", "DmlExecutionProvider", CPU], "npu"),
            (["DmlExecutionProvider", CPU], "directml"),
            ([CPU], "cpu"),
        ]
        for providers, expected in combinations:
            assert select_backend(providers).backend == expected

    def test_vitisai_option_keys_match_the_reference(self, tmp_path, monkeypatch):
        """VitisAI provider-option keys and values match the reference."""
        firmware = tmp_path / "1x4.xclbin"
        firmware.write_bytes(b"overlay")
        monkeypatch.setenv("XLNX_VART_FIRMWARE", str(firmware))
        _, ref_options = ref_backend._build_provider_list("npu")
        from prin.daemon import backend_provider_options

        options = backend_provider_options(
            "npu", tmp_path, firmware, tmp_path / "cache", "X1"
        )
        assert list(options[0]) == list(ref_options[0])
        assert options[0]["target"] == ref_options[0]["target"]
        assert options[0]["cache_key"] == ref_options[0]["cache_key"]

    def test_prin_falls_back_where_the_reference_raises(self):
        """PRIN's documented improvement over the reference.

        ``prinet.utils.npu_backend.create_session`` has no fallback: if the
        chosen provider cannot execute the graph it propagates the ONNX
        Runtime error, and if the provider is merely unregistered it silently
        produces a CPU session under an ``npu`` label. PRIN walks a
        deterministic ladder and reports the backend it actually landed on.
        """
        providers = ref_backend._available_eps()
        if "DmlExecutionProvider" not in providers:
            pytest.skip("DirectML is not registered on this host")

        reference_failed = False
        try:
            ref_backend.create_session(str(default_model_path()), "directml")
        except Exception:  # any ONNX Runtime provider failure counts here
            reference_failed = True
        if not reference_failed:
            pytest.skip("DirectML executes this graph on this host")

        _, backend, active = create_session(default_model_path(), "directml")
        assert backend == "cpu"
        assert active == [CPU]

    def test_prin_reports_a_degraded_selection_where_the_reference_is_silent(self):
        """An unregistered request is reported as degraded, not silently substituted."""
        providers = ref_backend._available_eps()
        if "VitisAIExecutionProvider" in providers:
            pytest.skip("the VitisAI provider is registered on this host")

        # The reference builds a session labelled "npu" that silently runs on
        # CPU; PRIN records the degradation in the selection itself.
        selection = select_backend(providers, "npu")
        assert selection.is_degraded
        assert selection.reason == "requested_unavailable"
        assert selection.backend != "npu"
