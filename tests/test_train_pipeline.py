"""Integration tests for `prin.train.train_phase_tracker` (WP-027):
the Python-callable trainable API entry point wrapping the Rust-native
temporal CLEVR-N training pipeline end to end.
"""

from __future__ import annotations

import pytest
import torch
from prin.nn import PhaseTracker
from prin.train import TrainingResult, train_phase_tracker


class TestTrainPhaseTracker:
    def test_returns_trained_phase_tracker_and_result(self) -> None:
        tracker, result = train_phase_tracker(
            4,
            n_delta=2,
            n_theta=3,
            n_gamma=4,
            n_discrete_steps=2,
            match_threshold=0.1,
            n_objects=3,
            n_frames=6,
            train_seqs=4,
            val_seqs=2,
            max_epochs=3,
            patience=3,
            warmup_epochs=1,
            smoothing_window=2,
        )

        assert isinstance(tracker, PhaseTracker)
        assert isinstance(result, TrainingResult)
        assert tracker.n_osc == 9
        assert result.total_epochs >= 1
        assert len(result.train_losses) == result.total_epochs
        assert len(result.val_losses) == result.total_epochs
        assert len(result.val_ips) == result.total_epochs
        assert 0.0 <= result.final_val_ip <= 1.0
        assert result.final_train_loss == pytest.approx(result.train_losses[-1])

    def test_returned_tracker_is_usable_like_a_fresh_one(self) -> None:
        tracker, _result = train_phase_tracker(
            4,
            n_delta=2,
            n_theta=3,
            n_gamma=4,
            n_discrete_steps=2,
            match_threshold=0.1,
            n_objects=3,
            n_frames=6,
            train_seqs=3,
            val_seqs=2,
            max_epochs=2,
            patience=2,
            warmup_epochs=1,
            smoothing_window=1,
        )

        dets = torch.rand(3, 4, dtype=torch.float64, requires_grad=True)
        phase, _amp = tracker.encode(dets)
        assert phase.shape == (3, 9)
        phase.sum().backward()
        assert dets.grad is not None

        frames = [torch.rand(3, 4, dtype=torch.float64) for _ in range(4)]
        tracking = tracker.track_sequence(frames)
        assert 0.0 <= tracking.identity_preservation <= 1.0

    def test_invalid_hyperparameter_raises_value_error(self) -> None:
        with pytest.raises(ValueError):
            train_phase_tracker(4, max_epochs=0)

    def test_reproducible_for_same_seeds(self) -> None:
        kwargs = dict(
            n_delta=2,
            n_theta=3,
            n_gamma=4,
            n_discrete_steps=2,
            match_threshold=0.1,
            n_objects=3,
            n_frames=6,
            train_seqs=3,
            val_seqs=2,
            max_epochs=2,
            patience=2,
            warmup_epochs=1,
            smoothing_window=1,
            dataset_seed=7,
            model_seed=3,
        )
        _tracker_a, result_a = train_phase_tracker(4, **kwargs)
        _tracker_b, result_b = train_phase_tracker(4, **kwargs)
        assert result_a.train_losses == result_b.train_losses
        assert result_a.val_ips == result_b.val_ips
