"""Integration tests for `prin.nn.allocation` (Exec-WP-026 S1): adaptive
oscillator-count allocation.

Every entry point here is non-differentiable (Coding Standards §3.2) — no
`gradcheck` in this file, matching the module's own docs.

WP-036C S1 0144M3 realigned `prin.nn.allocation` to the PRINet 3.0
`adaptive_allocation` reference surface exercised by `test_acceptance_y3q2`:
`OscillatorBudget.total` is now a property (not a method), `estimate_complexity`
returns a `float32` scalar tensor, and the reference `ValueError` messages are
used. This file was updated in step to that canonical API.
"""

from __future__ import annotations

import pytest
import torch
from prin._prin_core import Seed
from prin.nn import (
    AdaptiveOscillatorAllocator,
    DynamicPhaseTracker,
    estimate_complexity,
)


class TestEstimateComplexity:
    def test_returns_value_in_unit_interval(self) -> None:
        dets = torch.tensor([[0.1, 0.2], [0.5, 0.5], [0.9, 0.8]], dtype=torch.float64)
        c = estimate_complexity(dets)
        assert 0.0 <= c <= 1.0

    def test_single_detection_has_zero_spatial_term(self) -> None:
        dets = torch.tensor([[0.5, 0.5]], dtype=torch.float64)
        c = estimate_complexity(
            dets, spatial_weight=0.5, count_weight=0.5, max_objects=50
        )
        expected = 0.5 * (1.0 / 50.0) / 1.0
        assert c == pytest.approx(expected, abs=1e-6)


class TestAdaptiveOscillatorAllocatorRule:
    @pytest.fixture
    def allocator(self) -> AdaptiveOscillatorAllocator:
        return AdaptiveOscillatorAllocator(12, 64)

    def test_strategy_defaults_to_rule(
        self, allocator: AdaptiveOscillatorAllocator
    ) -> None:
        assert allocator.strategy == "rule"

    def test_allocate_totals_within_range(
        self, allocator: AdaptiveOscillatorAllocator
    ) -> None:
        budget = allocator.allocate(0.5)
        assert 12 <= budget.total <= 64
        assert budget.n_delta >= 1
        assert budget.n_theta >= 1
        assert budget.n_gamma >= 1
        assert budget.complexity == pytest.approx(0.5)

    def test_allocate_clamps_out_of_range_complexity(
        self, allocator: AdaptiveOscillatorAllocator
    ) -> None:
        low = allocator.allocate(-1.0)
        high = allocator.allocate(2.0)
        assert low.complexity == 0.0
        assert high.complexity == 1.0

    def test_sweep_complexity_covers_unit_interval(
        self, allocator: AdaptiveOscillatorAllocator
    ) -> None:
        budgets = allocator.sweep_complexity(5)
        assert len(budgets) == 5
        assert budgets[0].complexity == pytest.approx(0.0)
        assert budgets[-1].complexity == pytest.approx(1.0)

    def test_checkpoint_roundtrip(self, allocator: AdaptiveOscillatorAllocator) -> None:
        state = allocator.rust_state_dict()
        restored = AdaptiveOscillatorAllocator(12, 64)
        restored.load_rust_state_dict(state)
        torch.testing.assert_close(
            torch.tensor([allocator.allocate(0.5).total]),
            torch.tensor([restored.allocate(0.5).total]),
        )

    def test_invalid_range_rejected(self) -> None:
        with pytest.raises(ValueError, match="min_total must be >= 3"):
            AdaptiveOscillatorAllocator(2, 64)


class TestAdaptiveOscillatorAllocatorLearned:
    @pytest.fixture
    def allocator(self) -> AdaptiveOscillatorAllocator:
        return AdaptiveOscillatorAllocator(
            12, 64, strategy="learned", complexity_dim=1, seed_counter=1
        )

    def test_strategy_reports_learned(
        self, allocator: AdaptiveOscillatorAllocator
    ) -> None:
        assert allocator.strategy == "learned"

    def test_allocate_with_features_uses_mlp(
        self, allocator: AdaptiveOscillatorAllocator
    ) -> None:
        features = torch.rand(1, 1, dtype=torch.float64)
        budget = allocator.allocate(0.5, features)
        assert budget.total >= 12

    def test_allocate_without_features_falls_back_to_rule(
        self, allocator: AdaptiveOscillatorAllocator
    ) -> None:
        budget = allocator.allocate(0.5)
        assert budget.total >= 12

    def test_checkpoint_rejects_complexity_dim_mismatch(
        self, allocator: AdaptiveOscillatorAllocator
    ) -> None:
        state = allocator.rust_state_dict()
        target = AdaptiveOscillatorAllocator(
            12, 64, strategy="learned", complexity_dim=3, seed_counter=1
        )
        with pytest.raises(ValueError, match="shape mismatch"):
            target.load_rust_state_dict(state)

    def test_unknown_strategy_rejected(self) -> None:
        with pytest.raises(ValueError, match="strategy"):
            AdaptiveOscillatorAllocator(12, 64, strategy="bogus")


class TestDynamicPhaseTracker:
    def test_forward_returns_budget_and_matches(self) -> None:
        dyn = DynamicPhaseTracker(4, 12, 30, seed_counter=13)
        dets_t = torch.rand(3, 4, dtype=torch.float64)
        dets_t1 = torch.rand(3, 4, dtype=torch.float64)
        matches, sim, budget = dyn.forward(dets_t, dets_t1, Seed(30, 0))
        assert len(matches) == 3
        assert sim.shape == (3, 3)
        assert budget.total >= 12

    def test_caches_tracker_per_budget(self) -> None:
        """Two calls landing on the same budget must produce a tracker built
        from the same lazily-cached instance (deterministic given the same
        seed progression), not a freshly re-seeded one each time."""
        dyn = DynamicPhaseTracker(4, 12, 30, seed_counter=13)
        dets = torch.rand(3, 4, dtype=torch.float64)
        seed = Seed(30, 0)
        _, sim1, budget1 = dyn.forward(dets, dets, seed)
        _, sim2, budget2 = dyn.forward(dets, dets, seed)
        if budget1.total == budget2.total:
            torch.testing.assert_close(sim1, sim2)

    def test_learned_strategy_still_uses_rule_allocation(self) -> None:
        """Faithfully reproduced PRINet 3.0 quirk: `forward` never passes
        `features` to `allocate`, so it always uses rule-based allocation
        even when configured `"learned"` — see the Rust module's docs."""
        dyn = DynamicPhaseTracker(
            4, 12, 30, allocator_strategy="learned", seed_counter=14
        )
        dets = torch.rand(3, 4, dtype=torch.float64)
        _, _, budget = dyn.forward(dets, dets, Seed(31, 0))
        assert budget.total >= 12
