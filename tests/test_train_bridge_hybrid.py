"""Integration tests for `prin.nn.HybridPRINetV2` (Exec-WP-026 S1).

Covers DLPack marshalling, `torch.autograd.gradcheck` (float64), checkpoint
round-trips, and the `dropout != 0.0` rejection.
"""

from __future__ import annotations

import pytest
import torch
from prin.nn import HybridPRINetV2


@pytest.fixture
def net() -> HybridPRINetV2:
    return HybridPRINetV2(
        6,
        3,
        d_model=8,
        n_heads=2,
        n_layers=1,
        n_delta=2,
        n_theta=2,
        n_gamma=2,
        n_discrete_steps=1,
        seed_counter=2,
    )


class TestHybridPRINetV2ShapeAndDeterminism:
    def test_forward_output_shape_and_dtype(self, net: HybridPRINetV2) -> None:
        x = torch.randn(2, 6, dtype=torch.float64)
        y = net(x)
        assert y.shape == (2, 3)
        assert y.dtype == torch.float64

    def test_forward_returns_log_probabilities(self, net: HybridPRINetV2) -> None:
        x = torch.randn(4, 6, dtype=torch.float64)
        y = net(x)
        row_sums = y.exp().sum(dim=1)
        torch.testing.assert_close(
            row_sums, torch.ones(4, dtype=torch.float64), atol=1e-6, rtol=0
        )

    def test_forward_is_deterministic(self, net: HybridPRINetV2) -> None:
        x = torch.randn(2, 6, dtype=torch.float64)
        torch.testing.assert_close(net(x), net(x))

    def test_nonzero_dropout_rejected(self) -> None:
        with pytest.raises(ValueError, match="dropout"):
            HybridPRINetV2(6, 3, d_model=8, n_heads=2, dropout=0.1, seed_counter=1)

    def test_accessors_report_configured_sizes(self, net: HybridPRINetV2) -> None:
        assert net.n_input == 6
        assert net.n_classes == 3
        assert net.n_tokens == 6  # n_delta + n_theta + n_gamma = 2+2+2


class TestHybridPRINetV2Gradients:
    def test_gradcheck_float64(self, net: HybridPRINetV2) -> None:
        x = torch.randn(2, 6, dtype=torch.float64, requires_grad=True)
        assert torch.autograd.gradcheck(lambda t: net(t), (x,), eps=1e-6, atol=1e-4)

    def test_backward_is_repeatable_against_the_same_forward_pass(
        self, net: HybridPRINetV2
    ) -> None:
        x = torch.randn(2, 6, dtype=torch.float64, requires_grad=True)
        y = net(x)
        grad_out = torch.ones_like(y)
        y.backward(grad_out, retain_graph=True)
        first = x.grad.clone()
        x.grad = None
        y.backward(grad_out, retain_graph=True)
        torch.testing.assert_close(first, x.grad)


class TestHybridPRINetV2Checkpoint:
    def test_roundtrip_preserves_output(self, net: HybridPRINetV2) -> None:
        x = torch.randn(2, 6, dtype=torch.float64)
        before = net(x)
        state = net.rust_state_dict()
        restored = HybridPRINetV2(
            6,
            3,
            d_model=8,
            n_heads=2,
            n_layers=1,
            n_delta=2,
            n_theta=2,
            n_gamma=2,
            n_discrete_steps=1,
            seed_counter=99,
        )
        restored.load_rust_state_dict(state)
        torch.testing.assert_close(before, restored(x))

    def test_rejects_shape_mismatch_and_leaves_self_unchanged(
        self, net: HybridPRINetV2
    ) -> None:
        state = net.rust_state_dict()
        target = HybridPRINetV2(
            6,
            4,
            d_model=8,
            n_heads=2,
            n_layers=1,
            n_delta=2,
            n_theta=2,
            n_gamma=2,
            n_discrete_steps=1,
            seed_counter=1,
        )
        x = torch.randn(2, 6, dtype=torch.float64)
        before = target(x)
        with pytest.raises(ValueError, match="shape mismatch"):
            target.load_rust_state_dict(state)
        torch.testing.assert_close(before, target(x))
