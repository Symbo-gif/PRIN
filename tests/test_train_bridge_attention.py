"""Integration tests for `prin.nn.OscillatoryAttention` (Exec-WP-026 S1).

Covers DLPack marshalling, `torch.autograd.gradcheck` (float64, with and
without an explicit `phase` input), checkpoint round-trips (including
WP025-F1-class shape-mismatch rejection), and the `dropout != 0.0` rejection
(see `crates/prin-py/src/bindings/attention.rs`'s module docs for why).
"""

from __future__ import annotations

import pytest
import torch
from prin.nn import OscillatoryAttention


@pytest.fixture
def attention() -> OscillatoryAttention:
    """A small deterministic `OscillatoryAttention` for correctness tests."""
    return OscillatoryAttention(8, 2, seed_counter=1)


class TestOscillatoryAttentionShapeAndDeterminism:
    def test_accessors_report_configured_sizes(
        self, attention: OscillatoryAttention
    ) -> None:
        assert attention.d_model == 8
        assert attention.n_heads == 2

    def test_forward_output_shape_and_dtype(
        self, attention: OscillatoryAttention
    ) -> None:
        x = torch.randn(2, 3, 8, dtype=torch.float64)
        y = attention(x)
        assert y.shape == (2, 3, 8)
        assert y.dtype == torch.float64

    def test_forward_with_explicit_phase(self, attention: OscillatoryAttention) -> None:
        x = torch.randn(2, 3, 8, dtype=torch.float64)
        phase = torch.randn(2, 3, 2, dtype=torch.float64)
        y = attention(x, phase)
        assert y.shape == (2, 3, 8)

    def test_forward_is_deterministic(self, attention: OscillatoryAttention) -> None:
        x = torch.randn(2, 3, 8, dtype=torch.float64)
        torch.testing.assert_close(attention(x), attention(x))

    def test_zero_dropout_default_accepted(self) -> None:
        OscillatoryAttention(8, 2, dropout=0.0, seed_counter=1)

    def test_nonzero_dropout_rejected(self) -> None:
        with pytest.raises(ValueError, match="dropout"):
            OscillatoryAttention(8, 2, dropout=0.1, seed_counter=1)

    def test_indivisible_heads_rejected(self) -> None:
        with pytest.raises(ValueError, match="divisible"):
            OscillatoryAttention(9, 2, seed_counter=1)


class TestOscillatoryAttentionGradients:
    def test_gradcheck_float64_no_phase(self, attention: OscillatoryAttention) -> None:
        x = torch.randn(2, 3, 8, dtype=torch.float64, requires_grad=True)
        assert torch.autograd.gradcheck(
            lambda t: attention(t), (x,), eps=1e-6, atol=1e-4
        )

    def test_gradcheck_float64_with_phase(
        self, attention: OscillatoryAttention
    ) -> None:
        x = torch.randn(2, 3, 8, dtype=torch.float64, requires_grad=True)
        phase = torch.randn(2, 3, 2, dtype=torch.float64, requires_grad=True)
        assert torch.autograd.gradcheck(
            lambda t, p: attention(t, p), (x, phase), eps=1e-6, atol=1e-4
        )

    def test_backward_is_repeatable_against_the_same_forward_pass(
        self, attention: OscillatoryAttention
    ) -> None:
        x = torch.randn(2, 3, 8, dtype=torch.float64, requires_grad=True)
        y = attention(x)
        grad_out = torch.ones_like(y)
        y.backward(grad_out, retain_graph=True)
        first = x.grad.clone()
        x.grad = None
        y.backward(grad_out, retain_graph=True)
        torch.testing.assert_close(first, x.grad)


class TestOscillatoryAttentionCheckpoint:
    def test_roundtrip_preserves_output(self, attention: OscillatoryAttention) -> None:
        x = torch.randn(2, 3, 8, dtype=torch.float64)
        before = attention(x)
        state = attention.rust_state_dict()
        restored = OscillatoryAttention(8, 2, seed_counter=99)
        restored.load_rust_state_dict(state)
        torch.testing.assert_close(before, restored(x))

    def test_rejects_shape_mismatch_and_leaves_self_unchanged(
        self, attention: OscillatoryAttention
    ) -> None:
        state = attention.rust_state_dict()
        target = OscillatoryAttention(8, 4, seed_counter=1)
        x = torch.randn(2, 3, 8, dtype=torch.float64)
        before = target(x)
        with pytest.raises(ValueError, match="shape mismatch"):
            target.load_rust_state_dict(state)
        torch.testing.assert_close(before, target(x))
