"""Integration tests for `prin.nn.optimizers` (WP-027): `SyncGd`/`Scalr`/
`Rip`, the `torch.optim.Optimizer` wrappers over PRIN's oscillator-aware
Rust optimizers.

These optimizers are **non-differentiable** step functions (see
`crates/prin-py/src/bindings/optim.rs`'s module docs) — no gradcheck here,
matching `test_train_bridge_allocation.py`'s precedent for
non-differentiable bridges.
"""

from __future__ import annotations

import pytest
import torch
from prin.nn import Rip, Scalr, SyncGd


class TestSyncGd:
    def test_step_reduces_loss_on_a_simple_quadratic(self) -> None:
        gen = torch.Generator().manual_seed(0)
        w = torch.randn(4, dtype=torch.float64, generator=gen, requires_grad=True)
        opt = SyncGd([w], lr=0.1, momentum=0.0)

        def loss_of(x: torch.Tensor) -> torch.Tensor:
            return (x**2).sum()

        loss_before = float(loss_of(w).item())
        opt.zero_grad()
        loss_of(w).backward()
        opt.step(order_parameter=0.9)
        loss_after = float(loss_of(w).item())

        assert loss_after < loss_before

    def test_step_skips_parameters_with_no_gradient(self) -> None:
        w = torch.ones(3, dtype=torch.float64, requires_grad=True)
        opt = SyncGd([w], lr=0.1)
        opt.step(order_parameter=0.5)  # no backward() called: w.grad is None
        torch.testing.assert_close(w, torch.ones(3, dtype=torch.float64))

    def test_works_without_order_parameter(self) -> None:
        w = torch.tensor([2.0, -2.0], dtype=torch.float64, requires_grad=True)
        opt = SyncGd([w], lr=0.1)
        (w**2).sum().backward()
        opt.step()  # order_parameter=None -> plain unscaled SGD
        assert w[0].item() < 2.0
        assert w[1].item() > -2.0

    def test_state_dict_round_trip(self) -> None:
        w = torch.tensor([1.0, 1.0], dtype=torch.float64, requires_grad=True)
        opt = SyncGd([w], lr=0.1, momentum=0.5)
        (w.sum() ** 2).backward()
        opt.step(order_parameter=0.5)
        states = opt.rust_state_dict()
        assert len(states) == 1

        w2 = torch.tensor([1.0, 1.0], dtype=torch.float64, requires_grad=True)
        opt2 = SyncGd([w2], lr=0.1, momentum=0.5)
        opt2.load_rust_state_dict(states)  # must not raise

    def test_load_rust_state_dict_rejects_wrong_length(self) -> None:
        w = torch.ones(2, dtype=torch.float64, requires_grad=True)
        opt = SyncGd([w], lr=0.1)
        with pytest.raises(ValueError, match="expected 1 states"):
            opt.load_rust_state_dict([])


class TestScalr:
    def test_step_reduces_loss_on_a_simple_quadratic(self) -> None:
        gen = torch.Generator().manual_seed(1)
        w = torch.randn(4, dtype=torch.float64, generator=gen, requires_grad=True)
        opt = Scalr([w], lr=0.1)

        def loss_of(x: torch.Tensor) -> torch.Tensor:
            return (x**2).sum()

        loss_before = float(loss_of(w).item())
        opt.zero_grad()
        loss_of(w).backward()
        opt.step(order_parameter=0.9)
        loss_after = float(loss_of(w).item())

        assert loss_after < loss_before

    def test_low_order_parameter_scales_down_the_update(self) -> None:
        w_high = torch.tensor([1.0, 1.0], dtype=torch.float64, requires_grad=True)
        w_low = torch.tensor([1.0, 1.0], dtype=torch.float64, requires_grad=True)
        opt_high = Scalr([w_high], lr=0.1, r_min=0.1)
        opt_low = Scalr([w_low], lr=0.1, r_min=0.1)

        (w_high.sum() ** 2).backward()
        (w_low.sum() ** 2).backward()
        opt_high.step(order_parameter=1.0)
        opt_low.step(order_parameter=0.0)

        # r=1.0 uses the full base lr; r=0.0 scales to r_min * lr -> a
        # smaller step, so w_low should have moved less than w_high.
        origin = torch.tensor([1.0, 1.0], dtype=torch.float64)
        moved_high = (origin - w_high).abs().sum()
        moved_low = (origin - w_low).abs().sum()
        assert moved_low < moved_high

    def test_state_dict_round_trip(self) -> None:
        w = torch.tensor([1.0], dtype=torch.float64, requires_grad=True)
        opt = Scalr([w], lr=0.1)
        (w**2).sum().backward()
        opt.step(order_parameter=0.5)
        states = opt.rust_state_dict()

        w2 = torch.tensor([1.0], dtype=torch.float64, requires_grad=True)
        opt2 = Scalr([w2], lr=0.1)
        opt2.load_rust_state_dict(states)  # must not raise


class TestRip:
    def test_requires_exactly_one_square_parameter(self) -> None:
        a = torch.zeros(3, 3, dtype=torch.float64, requires_grad=True)
        b = torch.zeros(3, 3, dtype=torch.float64, requires_grad=True)
        with pytest.raises(ValueError, match="exactly one"):
            Rip([a, b])

        non_square = torch.zeros(3, 4, dtype=torch.float64, requires_grad=True)
        with pytest.raises(ValueError, match="square"):
            Rip([non_square])

    def test_n_oscillators_matches_coupling_shape(self) -> None:
        coupling = torch.zeros(5, 5, dtype=torch.float64, requires_grad=True)
        opt = Rip([coupling])
        assert opt.n_oscillators == 5

    def test_hebbian_step_updates_coupling_and_zeroes_diagonal(self) -> None:
        n = 4
        coupling = torch.zeros(n, n, dtype=torch.float64, requires_grad=True)
        opt = Rip([coupling], lr=0.5, target_amplitude=1.0)

        gen = torch.Generator().manual_seed(2)
        phase = torch.rand(1, n, dtype=torch.float64, generator=gen) * 6.28
        amplitude = torch.full((1, n), 0.5, dtype=torch.float64)

        opt.step(phase=phase, amplitude=amplitude)

        assert torch.all(coupling.diagonal() == 0.0)
        assert not torch.all(coupling == 0.0)

    def test_step_without_phase_or_amplitude_is_plain_gradient_descent(self) -> None:
        # No Hebbian term applies without phase/amplitude feedback, so the
        # diagonal is *not* zeroed here (diagonal zeroing is specifically
        # part of the Hebbian update, per `crates/prin-train/src/rip.rs`'s
        # `step`) -- this is plain `param - lr * grad` on every entry.
        n = 3
        coupling = torch.ones(n, n, dtype=torch.float64, requires_grad=True)
        opt = Rip([coupling], lr=0.1)
        (coupling**2).sum().backward()
        before = coupling.detach().clone()
        opt.step()
        expected = before - 0.1 * (2.0 * before)
        torch.testing.assert_close(coupling, expected)

    def test_state_dict_round_trip(self) -> None:
        coupling = torch.zeros(3, 3, dtype=torch.float64, requires_grad=True)
        opt = Rip([coupling], lr=0.2, target_amplitude=1.5)
        state = opt.rust_state_dict()

        coupling2 = torch.zeros(3, 3, dtype=torch.float64, requires_grad=True)
        opt2 = Rip([coupling2])
        opt2.load_rust_state_dict(state)  # must not raise
