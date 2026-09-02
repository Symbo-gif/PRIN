"""Tests for the ONNX-backed :class:`prin.daemon.SubconsciousController`.

These require ONNX Runtime and the committed model artefacts. They cover the
end-to-end inference path, the deterministic fallback ladder against a real
runtime, and the cross-provider output comparison that WP-028's acceptance
criteria call for.
"""

from __future__ import annotations

import numpy as np
import pytest

ort = pytest.importorskip("onnxruntime")

from prin.daemon import (  # noqa: E402
    CONTROL_DIM,
    STATE_DIM,
    ControlSignals,
    SubconsciousController,
    SubconsciousState,
    available_providers,
    backend_priority,
    create_session,
    default_model_path,
    select_backend,
)

CPU = "CPUExecutionProvider"


def _executable_backends() -> list[str]:
    """Backends whose provider can actually run the controller graph here.

    A provider being *registered* does not mean it can execute this graph: on
    this project's Windows host DirectML fuses `Gemm`+`Relu` into a
    `DmlFusedGemm` node that rejects the two-input form the export produces
    (Project Plan amendment #13). Probing is therefore the only honest way to
    enumerate the providers a cross-provider comparison can use.
    """
    executable = []
    for backend in backend_priority():
        try:
            _, resolved, _ = create_session(default_model_path(), backend)
        except (ValueError, RuntimeError, OSError):
            continue
        if resolved == backend:
            executable.append(backend)
    return executable


@pytest.fixture(scope="module")
def controller() -> SubconsciousController:
    """A controller pinned to CPU so results are host-independent."""
    return SubconsciousController(backend="cpu")


@pytest.fixture(scope="module")
def sample_states() -> list[SubconsciousState]:
    """A deterministic spread of telemetry snapshots."""
    rng = np.random.default_rng(20260821)
    regimes = ["mean_field", "sparse_knn", "full"]
    states = []
    for index in range(24):
        states.append(
            SubconsciousState(
                r_per_band=[float(x) for x in rng.random(3)],
                r_global=float(rng.random()),
                loss_ema=float(rng.normal() * 2.0),
                loss_variance=float(rng.random()),
                grad_norm_ema=float(rng.random() * 10.0),
                lr_current=float(rng.random() * 1e-2),
                scalr_alpha=float(rng.random() * 2.0),
                gpu_temp=float(rng.random() * 100.0),
                gpu_util=float(rng.random()),
                vram_pct=float(rng.random()),
                cpu_util=float(rng.random()),
                step_latency_p50=float(rng.random()),
                step_latency_p95=float(rng.random()),
                throughput=float(rng.random() * 1e5),
                epoch=int(rng.integers(0, 10_000)),
                regime=regimes[index % 3],
                timestamp=float(rng.random() * 1e9),
            )
        )
    return states


class TestConstruction:
    def test_controller_validates_and_loads_the_committed_model(self, controller):
        assert controller.model_path == default_model_path()
        assert len(controller.sha256) == 64
        assert controller.backend in backend_priority()
        assert controller.active_providers

    def test_graph_metadata_is_exposed(self, controller):
        graph = controller.graph
        assert graph["graph_name"] == "main_graph"
        assert graph["inputs"][0]["shape"] == ["batch", STATE_DIM]
        assert graph["outputs"][0]["shape"] == ["batch", CONTROL_DIM]

    def test_repr_names_the_model_and_backend(self, controller):
        text = repr(controller)
        assert "subconscious_controller.onnx" in text
        assert controller.backend in text

    def test_an_explicit_wrong_digest_is_rejected(self):
        with pytest.raises(ValueError, match="SHA-256 mismatch"):
            SubconsciousController(expected_sha256="0" * 64)

    def test_a_missing_model_raises(self, tmp_path):
        with pytest.raises(OSError):
            SubconsciousController(tmp_path / "absent.onnx")


class TestInference:
    def test_predict_returns_finite_bounded_control_signals(
        self, controller, sample_states
    ):
        for state in sample_states:
            control = controller.predict(state)
            assert isinstance(control, ControlSignals)
            assert control.is_finite()
            assert 0.1 <= control.lr_multiplier <= 10.0
            assert 0.0 <= control.alert_level <= 1.0
            assert control.preferred_regime in {"mean_field", "sparse_knn", "full"}

    def test_regime_weights_form_a_probability_simplex(self, controller, sample_states):
        # The exported head applies Softmax over channels 3-5.
        for state in sample_states:
            control = controller.predict(state)
            total = (
                control.regime_mf_weight
                + control.regime_sk_weight
                + control.regime_full_weight
            )
            assert total == pytest.approx(1.0, abs=1e-6)

    def test_k_bounds_and_lr_multiplier_are_positive(self, controller, sample_states):
        # Channels 0-2 pass through Softplus in the exported head.
        for state in sample_states:
            control = controller.predict(state)
            assert control.suggested_K_min > 0.0
            assert control.suggested_K_max > 0.0
            assert control.lr_multiplier > 0.0

    def test_batch_prediction_matches_single_prediction(
        self, controller, sample_states
    ):
        # ONNX Runtime selects a different float32 GEMM path for a single-row
        # batch, so batch-size agreement is a registered tolerance rather than
        # equality. The observed spread on this graph is one float32 ULP
        # (max |diff| 1.19e-7, max relative 1.56e-7); the registered tolerance
        # is rtol=1e-6, atol=1e-7. See `test_only_the_single_row_batch_differs`
        # for the shape of the effect.
        batched = controller.predict_batch(sample_states)
        assert len(batched) == len(sample_states)
        for state, control in zip(sample_states, batched, strict=True):
            single = controller.predict(state)
            np.testing.assert_allclose(
                control.to_tensor(),
                single.to_tensor(),
                rtol=1e-6,
                atol=1e-7,
            )
            assert control.preferred_regime == single.preferred_regime

    def test_only_the_single_row_batch_differs(self, controller, sample_states):
        # Every batch size from 2 upwards is bit-identical to the full batch;
        # only B = 1 takes the divergent kernel path.
        batch = np.stack([s.to_tensor() for s in sample_states])
        full = controller.run(batch)
        for size in (2, 4, 8, 16, len(sample_states)):
            assert np.array_equal(controller.run(batch[:size]), full[:size])
        single = controller.run(batch[:1])
        np.testing.assert_allclose(single, full[:1], rtol=1e-6, atol=1e-7)

    def test_inference_is_deterministic(self, controller, sample_states):
        first = controller.predict(sample_states[0]).to_tensor()
        second = controller.predict(sample_states[0]).to_tensor()
        assert np.array_equal(first, second)

    def test_run_accepts_a_raw_batch(self, controller, sample_states):
        batch = np.stack([s.to_tensor() for s in sample_states])
        raw = controller.run(batch)
        assert raw.shape == (len(sample_states), CONTROL_DIM)
        assert raw.dtype == np.float32

    def test_run_accepts_float64_input(self, controller):
        batch = np.zeros((2, STATE_DIM), dtype=np.float64)
        assert controller.run(batch).shape == (2, CONTROL_DIM)

    def test_run_rejects_wrong_shapes(self, controller):
        with pytest.raises(ValueError, match=r"shape \(B, 32\)"):
            controller.run(np.zeros(STATE_DIM, dtype=np.float32))
        with pytest.raises(ValueError, match=r"shape \(B, 32\)"):
            controller.run(np.zeros((1, STATE_DIM - 1), dtype=np.float32))

    def test_predict_batch_rejects_an_empty_sequence(self, controller):
        with pytest.raises(ValueError, match="at least one snapshot"):
            controller.predict_batch([])

    def test_close_releases_the_session(self):
        controller = SubconsciousController(backend="cpu")
        controller.close()
        with pytest.raises(AttributeError):
            controller.run(np.zeros((1, STATE_DIM), dtype=np.float32))


class TestDeterministicFallback:
    def test_cpu_session_activates_the_cpu_provider(self):
        _, backend, active = create_session(default_model_path(), "cpu")
        assert backend == "cpu"
        assert active == [CPU]

    def test_requesting_an_unavailable_backend_falls_back_without_raising(self):
        providers = available_providers()
        _, backend, active = create_session(default_model_path(), "npu")
        selection = select_backend(providers, "npu")
        assert backend in selection.attempt_order
        assert active
        if "VitisAIExecutionProvider" not in providers:
            # No NPU here: the ladder must have degraded, and the CPU provider
            # must be doing the work.
            assert backend != "npu"
            assert CPU in active

    def test_the_fallback_always_terminates_on_an_executable_backend(self):
        for requested in backend_priority():
            _, backend, active = create_session(default_model_path(), requested)
            assert backend in backend_priority()
            assert active

    def test_every_backend_yields_a_usable_session(self):
        state = SubconsciousState(r_global=0.5, regime="full")
        for requested in backend_priority():
            controller = SubconsciousController(backend=requested)
            control = controller.predict(state)
            assert control.is_finite()


class TestCrossProviderAgreement:
    """WP-028 acceptance: outputs agree across every executable provider."""

    def test_at_least_the_cpu_provider_can_execute(self):
        assert "cpu" in _executable_backends()

    def test_outputs_agree_across_every_executable_provider(self, sample_states):
        executable = _executable_backends()
        batch = np.stack([s.to_tensor() for s in sample_states])
        reference = SubconsciousController(backend="cpu").run(batch)
        for backend in executable:
            other = SubconsciousController(backend=backend).run(batch)
            # Registered tolerance for cross-execution-provider float32
            # agreement on the controller graph. The CPU/CPU comparison is
            # exact; an accelerator provider may reassociate the Gemm
            # reductions, so the comparison is a tolerance, not equality.
            np.testing.assert_allclose(other, reference, rtol=1e-5, atol=1e-6)

    def test_decoded_signals_agree_across_every_executable_provider(
        self, sample_states
    ):
        executable = _executable_backends()
        reference = SubconsciousController(backend="cpu").predict_batch(sample_states)
        for backend in executable:
            other = SubconsciousController(backend=backend).predict_batch(sample_states)
            for expected, actual in zip(reference, other, strict=True):
                np.testing.assert_allclose(
                    actual.to_tensor(),
                    expected.to_tensor(),
                    rtol=1e-5,
                    atol=1e-6,
                )
                assert actual.preferred_regime == expected.preferred_regime

    @pytest.mark.skipif(
        "DmlExecutionProvider" not in ort.get_available_providers(),
        reason="DmlExecutionProvider is not registered on this host",
    )
    def test_directml_executes_the_reexported_graph(self, sample_states):
        """WP-036F: the re-exported three-input-Gemm graph runs on DirectML.

        Before WP-036F the controller graph's two-input ``Gemm`` nodes made
        DirectML reject it at load (``InvalidGraph``) and the cross-provider
        harness fell back to CPU only. The DV-006 DirectML half closes here:
        ``directml`` is now an executable backend and its outputs agree with
        CPU within Testing Standards §3's ``rtol=1e-5, atol=1e-6``.
        """
        assert "directml" in _executable_backends()
        batch = np.stack([s.to_tensor() for s in sample_states])
        cpu = SubconsciousController(backend="cpu").run(batch)
        dml_controller = SubconsciousController(backend="directml")
        assert dml_controller.backend == "directml"
        assert "DmlExecutionProvider" in dml_controller.active_providers
        np.testing.assert_allclose(dml_controller.run(batch), cpu, rtol=1e-5, atol=1e-6)
