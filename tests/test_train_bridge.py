"""Integration tests for the WP-025 production Torch autograd bridge.

Covers `prin.nn.ResonanceLayer` and `prin.nn.GatedPhaseActivation`: DLPack
marshalling correctness, `torch.autograd.gradcheck` (float64), checkpoint
round-trips, batched-call independence, and typed-error boundaries. See
`crates/prin-py/src/bindings/train.rs` for the Rust bridge implementation and
the WP-025 S1 handoff (`DOCS/experiments/0097-wp025-s1-handoff.md`) for the
acceptance-criterion evidence map.
"""

from __future__ import annotations

import pytest
import torch
from prin.nn import GatedPhaseActivation, ResonanceLayer

# DV-018: burn-tensor's default `sigmoid` op downcasts through f32
# internally, an ~1e-7-relative precision floor inherited by
# GatedPhaseActivation's forward pass. The crate's own gradient tests
# (`activations.rs::gate_bias_gradient_matches_central_finite_difference`)
# establish eps=1e-4 as the smallest step that clears this floor; reused here
# for gradcheck rather than the library's default eps=1e-6.
_GATED_PHASE_ACTIVATION_GRADCHECK_EPS = 1e-4
_GATED_PHASE_ACTIVATION_GRADCHECK_ATOL = 1e-3


@pytest.fixture
def resonance_layer() -> ResonanceLayer:
    """A small deterministic `ResonanceLayer` for correctness tests."""
    return ResonanceLayer(4, 3, n_steps=3, dt=0.01, seed_counter=11)


@pytest.fixture
def gated_phase_activation() -> GatedPhaseActivation:
    """A small `GatedPhaseActivation` for correctness tests."""
    return GatedPhaseActivation(3)


class TestResonanceLayerShapeAndDeterminism:
    """Bridge marshalling correctness: shape, dtype, determinism."""

    def test_forward_output_shape_and_dtype(
        self, resonance_layer: ResonanceLayer
    ) -> None:
        x = torch.randn(5, 3, dtype=torch.float64)
        y = resonance_layer(x)
        assert y.shape == (5, 4)
        assert y.dtype == torch.float64

    def test_forward_is_deterministic(self, resonance_layer: ResonanceLayer) -> None:
        x = torch.randn(2, 3, dtype=torch.float64)
        y1 = resonance_layer(x)
        y2 = resonance_layer(x)
        torch.testing.assert_close(y1, y2)

    def test_same_seed_gives_identical_layers(self) -> None:
        x = torch.randn(2, 3, dtype=torch.float64)
        a = ResonanceLayer(4, 3, seed_counter=42, seed_key=7)
        b = ResonanceLayer(4, 3, seed_counter=42, seed_key=7)
        torch.testing.assert_close(a(x), b(x))

    def test_different_seed_gives_different_layers(self) -> None:
        x = torch.randn(2, 3, dtype=torch.float64)
        a = ResonanceLayer(4, 3, seed_counter=1)
        b = ResonanceLayer(4, 3, seed_counter=2)
        assert not torch.allclose(a(x), b(x))

    def test_batch_rows_are_independent(self, resonance_layer: ResonanceLayer) -> None:
        """One batched call must match looping the layer over single rows."""
        x = torch.randn(6, 3, dtype=torch.float64)
        batched = resonance_layer(x)
        looped = torch.cat([resonance_layer(x[i : i + 1]) for i in range(6)], dim=0)
        torch.testing.assert_close(batched, looped)

    def test_output_amplitudes_within_documented_clamp_range(
        self, resonance_layer: ResonanceLayer
    ) -> None:
        x = torch.randn(8, 3, dtype=torch.float64) * 5
        y = resonance_layer(x)
        assert torch.all(y >= 1e-6 - 1e-12)
        assert torch.all(y <= 10.0 + 1e-9)
        assert torch.all(torch.isfinite(y))


class TestResonanceLayerGradients:
    """The mandatory acceptance criterion: gradcheck in float64."""

    def test_gradcheck_float64(self, resonance_layer: ResonanceLayer) -> None:
        x = torch.randn(3, 3, dtype=torch.float64, requires_grad=True)
        assert torch.autograd.gradcheck(resonance_layer, (x,), eps=1e-6, atol=1e-4)

    def test_gradcheck_single_oscillator(self) -> None:
        """N=1 oscillator: no coupling partners (edge case)."""
        layer = ResonanceLayer(1, 2, n_steps=2, seed_counter=3)
        x = torch.randn(2, 2, dtype=torch.float64, requires_grad=True)
        assert torch.autograd.gradcheck(layer, (x,), eps=1e-6, atol=1e-4)

    def test_gradcheck_single_step(self) -> None:
        """n_steps=1: minimal integration."""
        layer = ResonanceLayer(3, 2, n_steps=1, seed_counter=5)
        x = torch.randn(2, 2, dtype=torch.float64, requires_grad=True)
        assert torch.autograd.gradcheck(layer, (x,), eps=1e-6, atol=1e-4)

    def test_backward_is_repeatable_against_the_same_forward_pass(
        self, resonance_layer: ResonanceLayer
    ) -> None:
        """`retain_graph=True` must call the Rust context's backward() more
        than once and get consistent results (required by gradcheck's own
        analytical-Jacobian machinery, which does exactly this).
        """
        x = torch.randn(2, 3, dtype=torch.float64, requires_grad=True)
        loss = resonance_layer(x).sum()
        loss.backward(retain_graph=True)
        first = x.grad.clone()
        x.grad = None
        loss.backward(retain_graph=True)
        second = x.grad.clone()
        torch.testing.assert_close(first, second)

    def test_gradient_flows_through_a_larger_torch_computation(
        self, resonance_layer: ResonanceLayer
    ) -> None:
        """The bridge composes inside an ordinary torch autograd graph."""
        x = torch.randn(2, 3, dtype=torch.float64, requires_grad=True)
        w = torch.randn(4, 4, dtype=torch.float64, requires_grad=True)
        y = resonance_layer(x)
        z = (y @ w).sum()
        z.backward()
        assert x.grad is not None and torch.all(torch.isfinite(x.grad))
        assert w.grad is not None and torch.all(torch.isfinite(w.grad))


class TestResonanceLayerCheckpoint:
    """Checkpoint (`rust_state_dict`/`load_rust_state_dict`) round trips."""

    def test_checkpoint_round_trip_preserves_forward_output(self) -> None:
        a = ResonanceLayer(4, 3, seed_counter=1)
        b = ResonanceLayer(4, 3, seed_counter=999)  # different initial params
        x = torch.randn(3, 3, dtype=torch.float64)
        assert not torch.allclose(a(x), b(x))

        state = a.rust_state_dict()
        b.load_rust_state_dict(state)
        torch.testing.assert_close(a(x), b(x))

    def test_checkpoint_bytes_are_nonempty(
        self, resonance_layer: ResonanceLayer
    ) -> None:
        assert isinstance(resonance_layer.rust_state_dict(), bytes)
        assert len(resonance_layer.rust_state_dict()) > 0

    def test_load_invalid_checkpoint_raises_value_error(
        self, resonance_layer: ResonanceLayer
    ) -> None:
        with pytest.raises(ValueError, match="checkpoint deserialization failed"):
            resonance_layer.load_rust_state_dict(b"not a valid record")

    def test_load_shape_mismatched_checkpoint_raises_value_error(
        self, resonance_layer: ResonanceLayer
    ) -> None:
        """WP025-F1 regression: a well-formed checkpoint from a
        differently-configured layer (different `n_oscillators`) must raise
        a typed `ValueError` naming the mismatch, never panic, and must
        leave the target layer's parameters unchanged.
        """
        donor = ResonanceLayer(6, 3, seed_counter=42)
        state = donor.rust_state_dict()

        x = torch.randn(2, 3, dtype=torch.float64)
        before = resonance_layer(x)

        with pytest.raises(ValueError, match="checkpoint shape mismatch"):
            resonance_layer.load_rust_state_dict(state)

        assert resonance_layer.n_oscillators == 4
        assert resonance_layer.n_dims == 3
        torch.testing.assert_close(resonance_layer(x), before)


class TestResonanceLayerErrors:
    """Typed-error boundaries: dtype/shape validation."""

    def test_float32_input_accepted(self, resonance_layer: ResonanceLayer) -> None:
        x = torch.randn(2, 3, dtype=torch.float32)
        out = resonance_layer(x)
        assert out.dtype == torch.float32
        assert torch.isfinite(out).all()

    def test_wrong_feature_width_rejected(
        self, resonance_layer: ResonanceLayer
    ) -> None:
        x = torch.randn(2, 5, dtype=torch.float64)
        with pytest.raises(ValueError, match=r"expected x shape \[batch, 3\]"):
            resonance_layer(x)

    def test_1d_input_rejected(self, resonance_layer: ResonanceLayer) -> None:
        x = torch.randn(3, dtype=torch.float64)
        with pytest.raises(ValueError, match="expected a 2-D tensor"):
            resonance_layer(x)

    def test_non_contiguous_input_accepted(
        self, resonance_layer: ResonanceLayer
    ) -> None:
        x = torch.randn(3, 6, dtype=torch.float64)[:, ::2]
        assert not x.is_contiguous()
        out = resonance_layer(x)
        assert out.shape == (3, 4)
        assert torch.isfinite(out).all()

    def test_zero_oscillators_rejected(self) -> None:
        with pytest.raises(ValueError, match="requires at least one oscillator"):
            ResonanceLayer(0, 3)

    def test_zero_dims_rejected(self) -> None:
        with pytest.raises(ValueError, match="requires at least one oscillator"):
            ResonanceLayer(3, 0)


class TestGatedPhaseActivationShapeAndRange:
    """Bridge marshalling correctness for the second (elementwise) bridge."""

    def test_forward_output_shape_dtype_and_range(
        self, gated_phase_activation: GatedPhaseActivation
    ) -> None:
        z = torch.randn(4, 3, dtype=torch.float64) * 10
        y = gated_phase_activation(z)
        assert y.shape == (4, 3)
        assert y.dtype == torch.float64
        assert torch.all(torch.isfinite(y))
        # sigmoid gate in [0, 1] times phase_activation in [0, 2*pi).
        import math

        assert torch.all(y >= -1e-12)
        assert torch.all(y <= math.tau + 1e-9)

    def test_zero_init_gate_is_one_half(
        self, gated_phase_activation: GatedPhaseActivation
    ) -> None:
        """Zero-initialized gate weight/bias => sigmoid(0) = 0.5 everywhere,
        matching PRINet 3.0's `nn.Parameter(torch.zeros(n_dims))` init.
        """
        z = torch.tensor([[0.4, -1.1, 2.3]], dtype=torch.float64)
        y = gated_phase_activation(z)
        assert torch.all(y >= -1e-12)


class TestGatedPhaseActivationGradients:
    def test_gradcheck_float64(
        self, gated_phase_activation: GatedPhaseActivation
    ) -> None:
        """DV-018: burn-tensor's sigmoid f32 downcast needs a looser eps than
        the crate default (see the module-level comment above).
        """
        z = torch.randn(3, 3, dtype=torch.float64, requires_grad=True)
        assert torch.autograd.gradcheck(
            gated_phase_activation,
            (z,),
            eps=_GATED_PHASE_ACTIVATION_GRADCHECK_EPS,
            atol=_GATED_PHASE_ACTIVATION_GRADCHECK_ATOL,
        )

    def test_backward_is_repeatable_against_the_same_forward_pass(
        self, gated_phase_activation: GatedPhaseActivation
    ) -> None:
        z = torch.randn(2, 3, dtype=torch.float64, requires_grad=True)
        loss = gated_phase_activation(z).sum()
        loss.backward(retain_graph=True)
        first = z.grad.clone()
        z.grad = None
        loss.backward(retain_graph=True)
        second = z.grad.clone()
        torch.testing.assert_close(first, second)


class TestGatedPhaseActivationCheckpoint:
    def test_checkpoint_round_trip_preserves_forward_output(self) -> None:
        a = GatedPhaseActivation(3)
        # Perturb `a`'s gate parameters away from zero-init via a manual
        # gradient step so a and a fresh `b` genuinely differ before restore.
        z = torch.randn(2, 3, dtype=torch.float64, requires_grad=True)
        a(z).sum().backward()

        b = GatedPhaseActivation(3)
        state = a.rust_state_dict()
        b.load_rust_state_dict(state)
        torch.testing.assert_close(a(z), b(z))

    def test_load_shape_mismatched_checkpoint_raises_value_error(self) -> None:
        """WP025-F1 regression: a well-formed checkpoint from a
        differently-configured layer (different `n_dims`) must raise a
        typed `ValueError` naming the mismatch, never panic (this is the
        path that panicked uncaught before the WP025-F1 fix), and must
        leave the target layer's parameters unchanged.
        """
        donor = GatedPhaseActivation(5)
        state = donor.rust_state_dict()

        target = GatedPhaseActivation(3)
        z = torch.randn(2, 3, dtype=torch.float64)
        before = target(z)

        with pytest.raises(ValueError, match="checkpoint shape mismatch"):
            target.load_rust_state_dict(state)

        assert target.n_dims == 3
        torch.testing.assert_close(target(z), before)


class TestGatedPhaseActivationErrors:
    def test_wrong_feature_width_rejected(
        self, gated_phase_activation: GatedPhaseActivation
    ) -> None:
        z = torch.randn(2, 5, dtype=torch.float64)
        with pytest.raises(ValueError, match=r"expected z shape \[batch, 3\]"):
            gated_phase_activation(z)

    def test_zero_dims_rejected(self) -> None:
        with pytest.raises(ValueError, match="requires at least one oscillator"):
            GatedPhaseActivation(0)


@pytest.mark.slow
class TestTrainBridgeBenchmarks:
    """Microbenchmarks: the WP-025 `<5%` boundary-overhead evidence.

    Compares the full Python `torch.autograd.Function` round trip (forward +
    backward, both crossing DLPack) against the Rust-only baseline measured
    independently in `crates/prin-train/benches/resonance_layer_bridge.rs`
    (same two named shapes — keep both files' shapes in sync). See the
    WP-025 S1 handoff for the combined evidence and overhead computation —
    this test records the Python-side number, it does not itself assert a
    cross-process overhead bound (Benchmarking Standards §2.3: no scientific
    conclusion claims from pilot evidence without a stored baseline).
    """

    def test_resonance_layer_forward_backward_round_trip_latency_small(
        self,
        benchmark: pytest.Fixture,  # pytest-benchmark fixture
    ) -> None:
        """Shape `small_32osc_16dims_8batch`."""
        layer = ResonanceLayer(32, 16, n_steps=10, dt=0.01, seed_counter=1)
        x = torch.randn(8, 16, dtype=torch.float64, requires_grad=True)

        def round_trip() -> torch.Tensor:
            y = layer(x)
            y.sum().backward()
            return y

        result = benchmark(round_trip)
        assert result.shape == (8, 32)

    def test_resonance_layer_forward_backward_round_trip_latency_moderate(
        self,
        benchmark: pytest.Fixture,
    ) -> None:
        """Shape `moderate_128osc_64dims_32batch`."""
        layer = ResonanceLayer(128, 64, n_steps=10, dt=0.01, seed_counter=1)
        x = torch.randn(32, 64, dtype=torch.float64, requires_grad=True)

        def round_trip() -> torch.Tensor:
            y = layer(x)
            y.sum().backward()
            return y

        result = benchmark(round_trip)
        assert result.shape == (32, 128)
