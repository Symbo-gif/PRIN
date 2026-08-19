"""Integration tests for `prin.nn.PhaseTracker` (Exec-WP-026 S1).

Covers the differentiable `encode`/`evolve`/`phase_similarity` bridges
(gradcheck, float64) and the non-differentiable `match_frames`/
`track_sequence` evaluation utilities, plus checkpoint round-trip and
WP025-F1-class shape-mismatch rejection.
"""

from __future__ import annotations

import pytest
import torch
from prin.nn import PhaseTracker


@pytest.fixture
def tracker() -> PhaseTracker:
    return PhaseTracker(
        4, n_delta=2, n_theta=3, n_gamma=4, n_discrete_steps=2, seed_counter=3
    )


class TestPhaseTrackerShapeAndDeterminism:
    def test_n_osc_is_band_sum(self, tracker: PhaseTracker) -> None:
        assert tracker.n_osc == 9

    def test_match_threshold_accessor(self, tracker: PhaseTracker) -> None:
        assert tracker.match_threshold == pytest.approx(0.3)

    def test_encode_output_shape(self, tracker: PhaseTracker) -> None:
        dets = torch.rand(3, 4, dtype=torch.float64)
        phase, amp = tracker.encode(dets)
        assert phase.shape == (3, 9)
        assert amp.shape == (3, 9)

    def test_evolve_output_shape(self, tracker: PhaseTracker) -> None:
        phase = torch.randn(3, 9, dtype=torch.float64)
        amp = torch.rand(3, 9, dtype=torch.float64) + 0.1
        phase_out, amp_out = tracker.evolve(phase, amp)
        assert phase_out.shape == (3, 9)
        assert amp_out.shape == (3, 9)

    def test_phase_similarity_output_shape(self, tracker: PhaseTracker) -> None:
        a = torch.randn(2, 9, dtype=torch.float64)
        b = torch.randn(4, 9, dtype=torch.float64)
        sim = tracker.phase_similarity(a, b)
        assert sim.shape == (2, 4)


class TestPhaseTrackerGradients:
    def test_encode_gradcheck(self, tracker: PhaseTracker) -> None:
        # `encode`'s detection-encoder MLP applies `relu`, which has a
        # non-differentiable kink at 0; an unseeded random input occasionally
        # (empirically observed ~1-in-5 unseeded runs during this session)
        # lands a pre-activation value close enough to that kink for the
        # eps=1e-4 finite-difference probe to straddle it, producing a
        # spurious mismatch unrelated to the bridge's correctness. A local
        # `Generator` (not `torch.manual_seed`, which would leak into other
        # tests' global RNG state) pins a draw already confirmed clear of the
        # kink across repeated reruns — the same class of
        # gradcheck-input-selection issue, not a bridge defect.
        gen = torch.Generator().manual_seed(0)
        dets = torch.rand(2, 4, dtype=torch.float64, generator=gen).requires_grad_()
        assert torch.autograd.gradcheck(
            lambda d: tracker.encode(d), (dets,), eps=1e-4, atol=3e-3
        )

    def test_evolve_gradcheck(self, tracker: PhaseTracker) -> None:
        phase = torch.randn(3, 9, dtype=torch.float64, requires_grad=True)
        amp = torch.rand(3, 9, dtype=torch.float64, requires_grad=True) + 0.1
        assert torch.autograd.gradcheck(
            lambda p, a: tracker.evolve(p, a), (phase, amp), eps=1e-4, atol=3e-3
        )

    def test_phase_similarity_gradcheck(self, tracker: PhaseTracker) -> None:
        a = torch.randn(2, 9, dtype=torch.float64, requires_grad=True)
        b = torch.randn(3, 9, dtype=torch.float64, requires_grad=True)
        assert torch.autograd.gradcheck(
            lambda x, y: tracker.phase_similarity(x, y), (a, b), eps=1e-6, atol=1e-4
        )


class TestPhaseTrackerNonDifferentiable:
    """`match_frames`/`track_sequence`: non-differentiable evaluation
    utilities — see `crates/prin-py/src/bindings/phase_tracker.rs`'s module
    docs. No gradcheck here: there is no gradient to check.
    """

    def test_match_frames_returns_matches_and_similarity(
        self, tracker: PhaseTracker
    ) -> None:
        dets_t = torch.rand(3, 4, dtype=torch.float64)
        dets_t1 = torch.rand(3, 4, dtype=torch.float64)
        matches, sim = tracker.match_frames(dets_t, dets_t1)
        assert len(matches) == 3
        assert all(m == -1 or 0 <= m < 3 for m in matches)
        assert sim.shape == (3, 3)
        assert not sim.requires_grad

    def test_track_sequence_returns_consistent_result(
        self, tracker: PhaseTracker
    ) -> None:
        frames = [torch.rand(3, 4, dtype=torch.float64) for _ in range(4)]
        result = tracker.track_sequence(frames)
        assert len(result.phase_history) == 4
        assert all(p.shape == (3, 9) for p in result.phase_history)
        assert len(result.identity_matches) == 3
        assert 0.0 <= result.identity_preservation <= 1.0
        assert len(result.per_frame_similarity) == 3
        assert len(result.per_frame_phase_correlation) == 3


class TestPhaseTrackerCheckpoint:
    def test_roundtrip_preserves_output(self, tracker: PhaseTracker) -> None:
        dets = torch.rand(2, 4, dtype=torch.float64)
        before, _ = tracker.encode(dets)
        state = tracker.rust_state_dict()
        restored = PhaseTracker(
            4, n_delta=2, n_theta=3, n_gamma=4, n_discrete_steps=2, seed_counter=99
        )
        restored.load_rust_state_dict(state)
        after, _ = restored.encode(dets)
        torch.testing.assert_close(before, after)

    def test_rejects_shape_mismatch_and_leaves_self_unchanged(
        self, tracker: PhaseTracker
    ) -> None:
        state = tracker.rust_state_dict()
        target = PhaseTracker(
            4, n_delta=2, n_theta=3, n_gamma=5, n_discrete_steps=2, seed_counter=1
        )
        assert target.n_osc == 10
        with pytest.raises(ValueError, match="shape mismatch"):
            target.load_rust_state_dict(state)
        assert target.n_osc == 10
