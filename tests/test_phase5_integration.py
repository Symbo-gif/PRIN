"""Phase 5 daemon, evaluation, statistics, and adversarial integration tests."""

from __future__ import annotations

import gc
import time

import numpy as np
import pytest
from prin.daemon import SubconsciousController, SubconsciousDaemon, TrainingHooks
from prin.eval import (
    MotAccumulator,
    binding_robustness_score,
    compute_full_temporal_metrics,
    identity_overcount,
    identity_switches,
    iou_distance_matrix,
    mostly_tracked_lost,
    recovery_speed,
    temporal_smoothness,
    track_duration_stats,
    track_fragmentation_rate,
)
from prin.experiments import (
    adversarial_evaluate_phase_tracker,
    adversarial_evaluate_slot_attention,
    bootstrap_ci,
    cohens_d,
    compute_p_value,
    welch_t_test,
)
from prin.nn import PhaseTracker, TemporalSlotAttentionMOT


def _wait_for_inference(daemon: SubconsciousDaemon, timeout_s: float = 2.0) -> None:
    """Wait until one submitted state has completed inference."""
    deadline = time.monotonic() + timeout_s
    while daemon.inference_count == 0 and time.monotonic() < deadline:
        time.sleep(0.005)
    assert daemon.inference_count >= 1


def test_hooks_state_flows_through_native_daemon() -> None:
    """Training hooks feed a state through the native daemon callback seam."""
    hooks = TrainingHooks(loss_ema_alpha=0.1, latency_window=8)
    hooks.on_step_end(2.0, 0.5, [3.0, 4.0])
    state = hooks.on_epoch_end(
        epoch=1,
        r_per_band=[0.8, 0.6, 0.4],
        lr_current=1e-3,
        scalr_alpha=1.0,
        regime="sparse_knn",
    )

    def infer(packed: np.ndarray) -> np.ndarray:
        return np.full(8, packed[3], dtype=np.float32)

    daemon = SubconsciousDaemon(infer, interval_ms=5, warmup=False)
    daemon.submit_state(state)
    _wait_for_inference(daemon)
    control = daemon.get_control()
    assert control.suggested_K_min == pytest.approx(state.r_global, abs=1e-6)
    assert daemon.stop(timeout_ms=2_000)


def test_controller_runs_behind_the_native_daemon() -> None:
    """The ONNX controller composes with hooks and the native daemon."""
    controller = SubconsciousController(backend="cpu")
    daemon = controller.spawn_daemon(interval_ms=5, warmup=False)
    state = TrainingHooks().on_epoch_end(epoch=0, r_per_band=[0.5, 0.5, 0.5])
    daemon.submit_state(state)
    _wait_for_inference(daemon)
    assert daemon.get_control().is_finite()
    assert daemon.stop(timeout_ms=2_000)
    controller.close()


def test_native_daemon_releases_the_gil_while_stopping() -> None:
    """Stopping does not hold the GIL needed by an in-flight callback."""
    entered = False

    def infer(_: np.ndarray) -> np.ndarray:
        nonlocal entered
        entered = True
        time.sleep(0.02)
        return np.zeros(8, dtype=np.float32)

    daemon = SubconsciousDaemon(infer, interval_ms=1, warmup=False)
    daemon.submit_state(TrainingHooks().on_epoch_end(epoch=0))
    deadline = time.monotonic() + 1.0
    while not entered and time.monotonic() < deadline:
        time.sleep(0.001)
    assert entered
    assert daemon.stop(timeout_ms=2_000)


def test_mot_and_temporal_metrics_share_one_evaluation_surface() -> None:
    """MOT and temporal metrics can evaluate the same identity history."""
    accumulator = MotAccumulator()
    accumulator.update(0, [1, 2], [10, 20], [[0.0, np.nan], [np.nan, 0.0]])
    accumulator.update(1, [1, 2], [10, 20], [[0.0, np.nan], [np.nan, 0.0]])
    mot = accumulator.summary()
    temporal = compute_full_temporal_metrics([[0, 1], [0, 1]], 2)

    assert mot.mota == 1.0
    assert mot.motp == 0.0
    assert mot.idf1 == 1.0
    assert temporal.ip == 1.0
    assert temporal.idsw == 0
    assert temporal.track_fragmentation_rate == 1.0


def test_statistics_and_adversarial_evaluation_are_deterministic() -> None:
    """The experiment surface threads explicit seeds through stochastic work."""
    first = bootstrap_ci([1.0, 2.0, 3.0, 4.0], seed_counter=17, n_bootstrap=200)
    second = bootstrap_ci([1.0, 2.0, 3.0, 4.0], seed_counter=17, n_bootstrap=200)
    assert first.mean == second.mean
    assert first.ci_lower == second.ci_lower
    assert first.ci_upper == second.ci_upper
    assert first.se == second.se

    test = welch_t_test([1.0, 2.0, 3.0], [4.0, 5.0, 6.0])
    assert test.p_value < 0.05
    assert test.cohens_d == pytest.approx(-3.0)

    tracker = PhaseTracker(
        detection_dim=4,
        n_delta=1,
        n_theta=1,
        n_gamma=2,
        n_discrete_steps=1,
        seed_counter=7,
    )
    result_a = adversarial_evaluate_phase_tracker(
        tracker,
        epsilon=0.01,
        attack="fgsm",
        n_sequences=1,
        n_objects=2,
        n_frames=3,
        detection_dim=4,
        seed=23,
    )
    result_b = adversarial_evaluate_phase_tracker(
        tracker,
        epsilon=0.01,
        attack="fgsm",
        n_sequences=1,
        n_objects=2,
        n_frames=3,
        detection_dim=4,
        seed=23,
    )
    assert result_a.clean_ip == result_b.clean_ip
    assert result_a.adv_ip == result_b.adv_ip
    assert result_a.per_seq_clean == result_b.per_seq_clean
    assert result_a.per_seq_adv == result_b.per_seq_adv
    assert 0.0 <= result_a.clean_ip <= 1.0
    assert 0.0 <= result_a.adv_ip <= 1.0


def test_daemon_binding_validates_failures_and_lifecycle() -> None:
    """Typed validation and callback failures remain observable to Python."""
    with pytest.raises(ValueError, match="queue_size"):
        SubconsciousDaemon(lambda _: np.zeros(8, dtype=np.float32), queue_size=0)
    with pytest.raises(ValueError):
        TrainingHooks(loss_ema_alpha=0.0)
    with pytest.raises(ValueError):
        TrainingHooks(latency_window=0)

    hooks = TrainingHooks()
    with pytest.raises(ValueError, match="elapsed_ms"):
        hooks.on_step_end(float("nan"), 0.0)
    with pytest.raises(ValueError, match="elapsed_ms"):
        hooks.on_step_end(-1.0, 0.0)
    hooks.on_step_end(1.0, 2.0)
    assert hooks.loss_ema > 0.0
    assert hooks.grad_norm_ema == 0.0
    assert hooks.step_count == 1

    def fail(_: np.ndarray) -> np.ndarray:
        raise RuntimeError("intentional callback failure")

    daemon = SubconsciousDaemon(fail, interval_ms=1, warmup=True)
    daemon.submit_state(hooks.on_epoch_end(epoch=0))
    deadline = time.monotonic() + 2.0
    while daemon.error_count == 0 and time.monotonic() < deadline:
        time.sleep(0.005)
    assert daemon.error_count >= 1
    assert daemon.pending_states == 0
    assert daemon.stop()
    assert daemon.stop()
    with pytest.raises(ValueError, match="already stopped"):
        daemon.get_control()

    invalid_results = [
        lambda _: np.zeros(8, dtype=np.float64),
        lambda _: np.zeros(7, dtype=np.float32),
        lambda _: np.zeros(16, dtype=np.float32)[::2],
    ]
    for callback in invalid_results:
        invalid = SubconsciousDaemon(callback, interval_ms=1, warmup=False)
        invalid.submit_state(hooks.on_epoch_end(epoch=0))
        deadline = time.monotonic() + 2.0
        while invalid.error_count == 0 and time.monotonic() < deadline:
            time.sleep(0.005)
        assert invalid.error_count == 1
        assert invalid.stop()

    abandoned = SubconsciousDaemon(
        lambda _: np.zeros(8, dtype=np.float32), interval_ms=1, warmup=False
    )
    del abandoned
    gc.collect()
    time.sleep(0.01)


def test_evaluation_surface_validates_shapes_and_exposes_all_metrics() -> None:
    """Every evaluation wrapper delegates to its Rust numerical authority."""
    accumulator = MotAccumulator(max_switch_time=1)
    with pytest.raises(ValueError, match="shape mismatch"):
        accumulator.update(0, [1], [2], [])
    accumulator.update(0, [1], [2], [[0.25]])
    summary = accumulator.summary()
    assert summary.mota == 1.0
    assert summary.motp == 0.25
    assert summary.idf1 == 1.0
    assert summary.num_matches == 1
    assert summary.num_switches == 0
    assert summary.num_misses == 0
    assert summary.num_false_positives == 0
    assert summary.num_objects == 1

    distances = iou_distance_matrix([(0.0, 0.0, 1.0, 1.0)], [(0.0, 0.0, 1.0, 1.0)])
    assert distances == [[0.0]]

    history = [[0, 1], [1, 1], [-1, 1]]
    positions = [
        [(0.0, 0.0), (0.0, 1.0)],
        [(1.0, 0.0), (1.0, 1.0)],
        [(3.0, 0.0), (2.0, 1.0)],
    ]
    visibility = [[False, True], [True, True], [True, True]]
    metrics = compute_full_temporal_metrics(
        history,
        2,
        positions=positions,
        occlusion_mask=visibility,
        ip_baseline=0.5,
    )
    assert metrics.ip == pytest.approx(5.0 / 6.0)
    assert metrics.idsw == 1
    assert metrics.temporal_smoothness > 0.0
    assert metrics.track_fragmentation_rate >= 1.0
    assert metrics.identity_overcount == 1.0
    assert 0.0 <= metrics.mostly_tracked <= 1.0
    assert 0.0 <= metrics.mostly_lost <= 1.0
    assert metrics.mean_track_duration > 0.0
    assert metrics.median_track_duration > 0.0
    assert metrics.recovery_speed >= 1.0
    assert metrics.binding_robustness > 1.0

    assert identity_switches(history, 2) == 1
    assert track_fragmentation_rate(history, 2) >= 1.0
    assert identity_overcount(history, 2) == 1.0
    assert mostly_tracked_lost(history, 2) == (0.5, 0.0)
    assert track_duration_stats(history, 2)[0] > 0.0
    assert recovery_speed(history, visibility, 2) >= 1.0
    assert temporal_smoothness(positions) > 0.0
    assert binding_robustness_score(0.5, 0.25) == 2.0


def test_experiment_surface_validates_inputs_and_runs_both_trackers() -> None:
    """Statistical and attack wrappers cover success and typed-error paths."""
    ci = bootstrap_ci([1.0, 2.0, 3.0], n_bootstrap=100, alpha=0.1)
    assert ci.ci_lower <= ci.mean <= ci.ci_upper
    assert ci.ci_width >= 0.0
    assert ci.se >= 0.0
    with pytest.raises(ValueError):
        bootstrap_ci([], n_bootstrap=100)
    with pytest.raises(ValueError):
        bootstrap_ci([1.0], n_bootstrap=0)
    with pytest.raises(ValueError):
        bootstrap_ci([1.0], alpha=1.0)

    test = welch_t_test([1.0, 2.0], [3.0, 4.0])
    assert test.t_stat < 0.0
    assert 0.0 <= test.p_value <= 1.0
    assert test.cohens_d < 0.0
    assert test.mean_diff == -2.0
    assert cohens_d([1.0, 2.0, 3.0], [4.0, 5.0, 6.0]) == -3.0
    assert compute_p_value([1.0, 2.0], [3.0, 4.0]) == test.p_value
    with pytest.raises(ValueError):
        welch_t_test([1.0], [2.0, 3.0])

    tracker = PhaseTracker(4, 1, 1, 2, 1, seed_counter=1)
    with pytest.raises(ValueError, match="attack"):
        adversarial_evaluate_phase_tracker(tracker, 0.01, attack="unknown")
    with pytest.raises(ValueError, match="pgd_steps"):
        adversarial_evaluate_phase_tracker(tracker, 0.01, attack="pgd", pgd_steps=0)
    with pytest.raises(ValueError, match="n_sequences"):
        adversarial_evaluate_phase_tracker(tracker, 0.01, n_sequences=0)

    slot_tracker = TemporalSlotAttentionMOT(
        detection_dim=4,
        num_slots=2,
        slot_dim=4,
        num_iterations=1,
        seed_counter=2,
    )
    result = adversarial_evaluate_slot_attention(
        slot_tracker,
        epsilon=0.01,
        attack="fgsm",
        n_sequences=1,
        n_objects=2,
        n_frames=3,
        detection_dim=4,
        seed=5,
    )
    assert 0.0 <= result.clean_ip <= 1.0
    assert 0.0 <= result.adv_ip <= 1.0
    assert result.degradation == result.clean_ip - result.adv_ip
    assert len(result.per_seq_clean) == 1
    assert len(result.per_seq_adv) == 1
