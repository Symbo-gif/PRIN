//! Temporal tracking-quality metrics beyond identity preservation (WP-031):
//! a direct port of PRINet 3.0's `temporal_metrics.py` (`utils/temporal_metrics.py`),
//! all 8 functions plus the `TemporalMetrics` dataclass.
//!
//! These metrics operate on the same `matches_history`/`occlusion_mask`
//! shapes [`crate::phase_tracker::PhaseTracker::track_sequence`] and
//! [`crate::slot_attention::TemporalSlotAttentionMOT::track_sequence`]
//! already return (`Vec<Vec<i64>>` identity matches per transition,
//! `Vec<Vec<bool>>` visibility from [`crate::dataset::SequenceData`]) — no
//! new tensor types are introduced, only host-side, non-differentiable
//! post-processing over already-computed match indices, matching the
//! reference's own `.item()`-per-element bookkeeping style (the same class
//! as `crate::support::greedy_match_by_similarity`).
//!
//! Distinct from `prin-daemon`'s `mot` module's `MotAccumulator` (WP-030, a
//! different reference file, `nn/mot_evaluation.py`): that module computes
//! MOTA/MOTP/IDF1 from IoU-matched bounding-box detections for the daemon's
//! runtime evaluation pipeline; this module computes fragmentation/duration/
//! recovery statistics directly from a tracker's own identity-match history,
//! for training-time (`TemporalTrainer.evaluate`) and offline experiment
//! reporting.

/// Container for all temporal coherence metrics, matching the reference
/// `TemporalMetrics` dataclass (`temporal_metrics.py:34-62`) field-for-field,
/// including its non-zero defaults (`track_fragmentation_rate`/
/// `identity_overcount`/`binding_robustness` default to `1.0` — "no
/// fragmentation/overcount/degradation" — not `0.0`).
#[derive(Clone, Copy, Debug, PartialEq)]
pub struct TemporalMetrics {
    /// Identity Preservation, `[0, 1]`.
    pub ip: f64,
    /// Total identity switch count.
    pub idsw: i64,
    /// Motion field consistency (lower = smoother); `0.0` if not requested.
    pub temporal_smoothness: f64,
    /// Fragments per ground-truth object (`1.0` = perfect).
    pub track_fragmentation_rate: f64,
    /// Unique predicted IDs / ground-truth objects (`1.0` = optimal).
    pub identity_overcount: f64,
    /// Fraction of objects tracked `>= 80%` of their lifetime.
    pub mostly_tracked: f64,
    /// Fraction of objects tracked `<= 20%` of their lifetime.
    pub mostly_lost: f64,
    /// Mean frames per maintained identity.
    pub mean_track_duration: f64,
    /// Median frames per maintained identity.
    pub median_track_duration: f64,
    /// Mean frames to re-bind after occlusion; `NaN` if no occlusion events
    /// (or not requested).
    pub recovery_speed: f64,
    /// `ip_perturbed / ip_baseline`; `1.0` if not requested.
    pub binding_robustness: f64,
}

impl Default for TemporalMetrics {
    fn default() -> Self {
        Self {
            ip: 0.0,
            idsw: 0,
            temporal_smoothness: 0.0,
            track_fragmentation_rate: 1.0,
            identity_overcount: 1.0,
            mostly_tracked: 0.0,
            mostly_lost: 0.0,
            mean_track_duration: 0.0,
            median_track_duration: 0.0,
            recovery_speed: f64::NAN,
            binding_robustness: 1.0,
        }
    }
}

/// Compute temporal smoothness of tracked positions: the mean L2 norm of
/// position *acceleration* (second difference) across `positions`, a
/// `T`-length sequence of per-object `(x, y)` pairs (the same shape as
/// [`crate::dataset::SequenceData::positions`]).
///
/// Direct port of `temporal_smoothness` (`temporal_metrics.py:65-100`).
/// Returns `0.0` for `T < 3` (no acceleration is defined).
pub fn temporal_smoothness(positions: &[Vec<[f64; 2]>]) -> f64 {
    let t = positions.len();
    if t < 3 {
        return 0.0;
    }
    let mut sum = 0.0;
    let mut count = 0usize;
    for frame in 0..(t - 2) {
        let (p0, p1, p2) = (
            &positions[frame],
            &positions[frame + 1],
            &positions[frame + 2],
        );
        for ((a, b), c) in p0.iter().zip(p1.iter()).zip(p2.iter()) {
            let v0 = [b[0] - a[0], b[1] - a[1]];
            let v1 = [c[0] - b[0], c[1] - b[1]];
            let accel = [v1[0] - v0[0], v1[1] - v0[1]];
            sum += (accel[0] * accel[0] + accel[1] * accel[1]).sqrt();
            count += 1;
        }
    }
    if count == 0 {
        0.0
    } else {
        sum / count as f64
    }
}

/// Count total identity switches: an object matched to predicted ID `i` at
/// frame `t` becoming matched to predicted ID `j != i` at frame `t+1`.
///
/// Direct port of `identity_switches` (`temporal_metrics.py:103-135`).
pub fn identity_switches(matches_history: &[Vec<i64>], n_objects: usize) -> i64 {
    if matches_history.len() < 2 {
        return 0;
    }
    let mut switches = 0i64;
    for t in 1..matches_history.len() {
        let prev = &matches_history[t - 1];
        let curr = &matches_history[t];
        let n = prev.len().min(curr.len()).min(n_objects);
        for i in 0..n {
            let (p, c) = (prev[i], curr[i]);
            if p >= 0 && c >= 0 && p != c {
                switches += 1;
            }
        }
    }
    switches
}

/// Compute track fragmentation rate: `total_fragments / n_objects`. Perfect
/// tracking gives `1.0` (one fragment per object); higher values indicate
/// more fragmented tracks.
///
/// Direct port of `track_fragmentation_rate` (`temporal_metrics.py:138-181`).
pub fn track_fragmentation_rate(matches_history: &[Vec<i64>], n_objects: usize) -> f64 {
    if matches_history.is_empty() || n_objects == 0 {
        return 1.0;
    }
    let mut total_fragments = 0usize;
    for obj_id in 0..n_objects {
        let mut fragments = 0usize;
        let mut in_fragment = false;
        for m in matches_history {
            let is_matched = obj_id < m.len() && m[obj_id] >= 0;
            if is_matched && !in_fragment {
                fragments += 1;
                in_fragment = true;
            } else if !is_matched {
                in_fragment = false;
            }
        }
        total_fragments += fragments.max(1);
    }
    total_fragments as f64 / n_objects as f64
}

/// Compute identity overcount: `|unique predicted IDs assigned| / n_objects`.
/// `1.0` is optimal; `> 1.0` means the tracker creates spurious IDs.
///
/// Direct port of `identity_overcount` (`temporal_metrics.py:184-210`).
pub fn identity_overcount(matches_history: &[Vec<i64>], n_objects: usize) -> f64 {
    if matches_history.is_empty() || n_objects == 0 {
        return 1.0;
    }
    let mut unique_ids = std::collections::HashSet::new();
    for m in matches_history {
        for &v in m {
            if v >= 0 {
                unique_ids.insert(v);
            }
        }
    }
    unique_ids.len() as f64 / n_objects.max(1) as f64
}

/// Compute Mostly Tracked (MT) and Mostly Lost (ML) fractions:
/// `MT = fraction of objects tracked >= tracked_threshold of their lifetime`,
/// `ML = fraction of objects tracked <= lost_threshold of their lifetime`.
///
/// Direct port of `mostly_tracked_lost` (`temporal_metrics.py:213-258`); the
/// reference's defaults are `tracked_threshold=0.8, lost_threshold=0.2`.
pub fn mostly_tracked_lost(
    matches_history: &[Vec<i64>],
    n_objects: usize,
    tracked_threshold: f64,
    lost_threshold: f64,
) -> (f64, f64) {
    if matches_history.is_empty() || n_objects == 0 {
        return (0.0, 1.0);
    }
    let t = matches_history.len();
    let mut mt_count = 0usize;
    let mut ml_count = 0usize;
    for obj_id in 0..n_objects {
        let tracked_frames = matches_history
            .iter()
            .filter(|m| obj_id < m.len() && m[obj_id] >= 0)
            .count();
        let frac = tracked_frames as f64 / t.max(1) as f64;
        if frac >= tracked_threshold {
            mt_count += 1;
        }
        if frac <= lost_threshold {
            ml_count += 1;
        }
    }
    (
        mt_count as f64 / n_objects as f64,
        ml_count as f64 / n_objects as f64,
    )
}

/// Compute mean and median track duration: the number of consecutive frames
/// an identity is maintained without interruption.
///
/// Direct port of `track_duration_stats` (`temporal_metrics.py:261-316`).
pub fn track_duration_stats(matches_history: &[Vec<i64>], n_objects: usize) -> (f64, f64) {
    if matches_history.is_empty() || n_objects == 0 {
        return (0.0, 0.0);
    }
    let mut durations: Vec<i64> = Vec::new();
    for obj_id in 0..n_objects {
        let mut run_length = 0i64;
        let mut prev_match = -1i64;
        for m in matches_history {
            let val = if obj_id < m.len() { m[obj_id] } else { -1 };
            if val >= 0 && (prev_match < 0 || val == prev_match) {
                run_length += 1;
            } else {
                if run_length > 0 {
                    durations.push(run_length);
                }
                run_length = if val >= 0 { 1 } else { 0 };
            }
            prev_match = val;
        }
        if run_length > 0 {
            durations.push(run_length);
        }
    }
    if durations.is_empty() {
        return (0.0, 0.0);
    }
    let mean = durations.iter().sum::<i64>() as f64 / durations.len() as f64;
    let mut sorted = durations.clone();
    sorted.sort_unstable();
    let n = sorted.len();
    let median = if n % 2 == 1 {
        sorted[n / 2] as f64
    } else {
        (sorted[n / 2 - 1] + sorted[n / 2]) as f64 / 2.0
    };
    (mean, median)
}

/// Measure the average number of frames to re-bind after occlusion ends: for
/// each occlusion event (object goes from occluded to visible), count how
/// many frames until the tracker re-establishes a match.
///
/// Direct port of `recovery_speed` (`temporal_metrics.py:319-365`).
/// `occlusion_mask[t][i]` is `true` when visible (matching
/// [`crate::dataset::SequenceData::occlusion_mask`]'s convention — the
/// reference's `>= 0.5` visible / `< 0.5` occluded tensor encoding of the
/// same boolean). Returns `NaN` if no occlusion events occurred.
pub fn recovery_speed(
    matches_history: &[Vec<i64>],
    occlusion_mask: &[Vec<bool>],
    n_objects: usize,
) -> f64 {
    let t = occlusion_mask.len();
    let n_check = n_objects.min(occlusion_mask.first().map_or(0, Vec::len));
    let mut recovery_frames: Vec<i64> = Vec::new();

    for obj_id in 0..n_check {
        for frame in 1..t {
            let was_occluded = !occlusion_mask[frame - 1][obj_id];
            let is_visible = occlusion_mask[frame][obj_id];
            if was_occluded && is_visible {
                let mut frames_to_rebind = 0i64;
                for m in matches_history
                    .iter()
                    .skip(frame - 1)
                    .take(matches_history.len().min(t).saturating_sub(frame - 1))
                {
                    let val = if obj_id < m.len() { m[obj_id] } else { -1 };
                    frames_to_rebind += 1;
                    if val >= 0 {
                        break;
                    }
                }
                recovery_frames.push(frames_to_rebind);
            }
        }
    }

    if recovery_frames.is_empty() {
        f64::NAN
    } else {
        recovery_frames.iter().sum::<i64>() as f64 / recovery_frames.len() as f64
    }
}

/// Compute binding robustness score: `IP_perturbed / IP_baseline`. `1.0` =
/// no degradation. Returns `0.0` if `ip_baseline <= 0.0`.
///
/// Direct port of `binding_robustness_score` (`temporal_metrics.py:368-385`).
pub fn binding_robustness_score(ip_perturbed: f64, ip_baseline: f64) -> f64 {
    if ip_baseline <= 0.0 {
        0.0
    } else {
        ip_perturbed / ip_baseline
    }
}

/// Compute all temporal coherence metrics in one call.
///
/// Direct port of `compute_full_temporal_metrics` (`temporal_metrics.py:388-451`).
/// `positions`/`occlusion_mask`/`ip_baseline` are optional: omitting each
/// leaves the corresponding [`TemporalMetrics`] field at its reference
/// default (`temporal_smoothness=0.0`, `recovery_speed=NaN`,
/// `binding_robustness=1.0`).
pub fn compute_full_temporal_metrics(
    matches_history: &[Vec<i64>],
    n_objects: usize,
    positions: Option<&[Vec<[f64; 2]>]>,
    occlusion_mask: Option<&[Vec<bool>]>,
    ip_baseline: Option<f64>,
) -> TemporalMetrics {
    let mut total_matched = 0usize;
    let mut total_possible = 0usize;
    for m in matches_history {
        let n = m.len().min(n_objects);
        total_matched += m[..n].iter().filter(|&&v| v >= 0).count();
        total_possible += n;
    }
    let ip = total_matched as f64 / total_possible.max(1) as f64;

    let idsw = identity_switches(matches_history, n_objects);
    let tfr = track_fragmentation_rate(matches_history, n_objects);
    let ioc = identity_overcount(matches_history, n_objects);
    let (mt, ml) = mostly_tracked_lost(matches_history, n_objects, 0.8, 0.2);
    let (mean_dur, median_dur) = track_duration_stats(matches_history, n_objects);
    let ts = positions.map_or(0.0, temporal_smoothness);
    let rs = occlusion_mask.map_or(f64::NAN, |om| {
        recovery_speed(matches_history, om, n_objects)
    });
    let brs = match ip_baseline {
        Some(baseline) if baseline > 0.0 => binding_robustness_score(ip, baseline),
        _ => 1.0,
    };

    TemporalMetrics {
        ip,
        idsw,
        temporal_smoothness: ts,
        track_fragmentation_rate: tfr,
        identity_overcount: ioc,
        mostly_tracked: mt,
        mostly_lost: ml,
        mean_track_duration: mean_dur,
        median_track_duration: median_dur,
        recovery_speed: rs,
        binding_robustness: brs,
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    fn m(rows: &[&[i64]]) -> Vec<Vec<i64>> {
        rows.iter().map(|r| r.to_vec()).collect()
    }

    // --- temporal_smoothness ---

    #[test]
    fn temporal_smoothness_constant_velocity_gives_zero() {
        // Constant velocity => zero acceleration => zero smoothness metric.
        let positions: Vec<Vec<[f64; 2]>> = (0..5).map(|t| vec![[t as f64, 0.0]]).collect();
        assert!(temporal_smoothness(&positions).abs() < 1e-12);
    }

    #[test]
    fn temporal_smoothness_hand_computed_single_kink() {
        // One object: positions 0,1,2,4 (constant velocity 1, then a jump to
        // +2). v = [1,1,2]; accel = [0,1]; mean |accel| = (0+1)/2 = 0.5.
        let positions: Vec<Vec<[f64; 2]>> = vec![
            vec![[0.0, 0.0]],
            vec![[1.0, 0.0]],
            vec![[2.0, 0.0]],
            vec![[4.0, 0.0]],
        ];
        let ts = temporal_smoothness(&positions);
        assert!((ts - 0.5).abs() < 1e-9, "ts={ts}");
    }

    #[test]
    fn temporal_smoothness_short_sequence_gives_zero() {
        let positions: Vec<Vec<[f64; 2]>> = vec![vec![[0.0, 0.0]], vec![[1.0, 0.0]]];
        assert_eq!(temporal_smoothness(&positions), 0.0);
    }

    // --- identity_switches ---

    #[test]
    fn identity_switches_counts_only_actual_swaps() {
        let history = m(&[&[0, 1], &[1, 0], &[1, 0]]);
        // t=0->1: both objects switch (0->1, 1->0) = 2 switches.
        // t=1->2: no switches.
        assert_eq!(identity_switches(&history, 2), 2);
    }

    #[test]
    fn identity_switches_ignores_unmatched() {
        let history = m(&[&[0, -1], &[-1, -1], &[1, -1]]);
        assert_eq!(identity_switches(&history, 2), 0);
    }

    #[test]
    fn identity_switches_needs_at_least_two_frames() {
        assert_eq!(identity_switches(&m(&[&[0, 1]]), 2), 0);
        assert_eq!(identity_switches(&[], 2), 0);
    }

    // --- track_fragmentation_rate ---

    #[test]
    fn fragmentation_rate_perfect_tracking_is_one() {
        let history = m(&[&[0, 1], &[0, 1], &[0, 1]]);
        assert!((track_fragmentation_rate(&history, 2) - 1.0).abs() < 1e-12);
    }

    #[test]
    fn fragmentation_rate_counts_broken_runs() {
        // Object 0: matched, unmatched, matched -> 2 fragments.
        let history = m(&[&[0], &[-1], &[0]]);
        assert!((track_fragmentation_rate(&history, 1) - 2.0).abs() < 1e-12);
    }

    #[test]
    fn fragmentation_rate_never_matched_counts_as_one_fragment() {
        let history = m(&[&[-1], &[-1]]);
        assert!((track_fragmentation_rate(&history, 1) - 1.0).abs() < 1e-12);
    }

    #[test]
    fn fragmentation_rate_empty_history_or_zero_objects_is_one() {
        assert_eq!(track_fragmentation_rate(&[], 3), 1.0);
        assert_eq!(track_fragmentation_rate(&m(&[&[0]]), 0), 1.0);
    }

    // --- identity_overcount ---

    #[test]
    fn identity_overcount_optimal_case_is_one() {
        let history = m(&[&[0, 1], &[0, 1]]);
        assert!((identity_overcount(&history, 2) - 1.0).abs() < 1e-12);
    }

    #[test]
    fn identity_overcount_spurious_ids_exceeds_one() {
        let history = m(&[&[0, 1], &[2, 3]]);
        assert!((identity_overcount(&history, 2) - 2.0).abs() < 1e-12);
    }

    // --- mostly_tracked_lost ---

    #[test]
    fn mostly_tracked_lost_hand_computed() {
        // Object 0 tracked 4/4 frames (MT), object 1 tracked 0/4 (ML).
        let history = m(&[&[0, -1], &[0, -1], &[0, -1], &[0, -1]]);
        let (mt, ml) = mostly_tracked_lost(&history, 2, 0.8, 0.2);
        assert!((mt - 0.5).abs() < 1e-12);
        assert!((ml - 0.5).abs() < 1e-12);
    }

    #[test]
    fn mostly_tracked_lost_empty_returns_reference_defaults() {
        assert_eq!(mostly_tracked_lost(&[], 3, 0.8, 0.2), (0.0, 1.0));
    }

    // --- track_duration_stats ---

    #[test]
    fn track_duration_stats_hand_computed_single_run() {
        let history = m(&[&[0], &[0], &[0]]);
        let (mean, median) = track_duration_stats(&history, 1);
        assert!((mean - 3.0).abs() < 1e-12);
        assert!((median - 3.0).abs() < 1e-12);
    }

    #[test]
    fn track_duration_stats_id_switch_breaks_run() {
        // val goes 0 -> 1 (a switch, not just unmatched): breaks the run.
        let history = m(&[&[0], &[1], &[1]]);
        let (mean, _median) = track_duration_stats(&history, 1);
        // Two runs: length 1 (id 0) and length 2 (id 1) -> mean 1.5.
        assert!((mean - 1.5).abs() < 1e-12);
    }

    #[test]
    fn track_duration_stats_even_count_median_averages_middle_two() {
        // Two objects with run lengths 1 and 3 -> sorted [1,3] -> median 2.0.
        let history = m(&[&[0, 1], &[-1, 1], &[-1, 1]]);
        let (_mean, median) = track_duration_stats(&history, 2);
        assert!((median - 2.0).abs() < 1e-12);
    }

    #[test]
    fn track_duration_stats_empty_is_zero() {
        assert_eq!(track_duration_stats(&[], 2), (0.0, 0.0));
    }

    // --- recovery_speed ---

    #[test]
    fn recovery_speed_hand_computed_immediate_rebind() {
        // Object occluded at t=0, visible from t=1; matched at t=1. The
        // reference's inner scan starts at t2=t-1 (the occluded frame's own
        // match entry, still -1) and only breaks once it finds a match, so
        // this counts 2 frames (t2=0: -1, t2=1: 0 -> break), not 1.
        let occ = vec![vec![false], vec![true], vec![true]];
        let matches = m(&[&[-1], &[0], &[0]]);
        let rs = recovery_speed(&matches, &occ, 1);
        assert!((rs - 2.0).abs() < 1e-9, "rs={rs}");
    }

    #[test]
    fn recovery_speed_delayed_rebind() {
        // Same start-at-(t-1) convention as above: the scan begins at the
        // occluded frame itself (t2=0, val=-1) and walks forward to t2=3
        // (val=0) before breaking, counting 4 frames, not 3.
        let occ = vec![vec![false], vec![true], vec![true], vec![true]];
        let matches = m(&[&[-1], &[-1], &[-1], &[0]]);
        let rs = recovery_speed(&matches, &occ, 1);
        assert!((rs - 4.0).abs() < 1e-9, "rs={rs}");
    }

    #[test]
    fn recovery_speed_no_occlusion_events_gives_nan() {
        let occ = vec![vec![true], vec![true], vec![true]];
        let matches = m(&[&[0], &[0]]);
        assert!(recovery_speed(&matches, &occ, 1).is_nan());
    }

    // --- binding_robustness_score ---

    #[test]
    fn binding_robustness_score_hand_computed() {
        assert!((binding_robustness_score(0.5, 1.0) - 0.5).abs() < 1e-12);
        assert_eq!(binding_robustness_score(0.5, 0.0), 0.0);
        assert_eq!(binding_robustness_score(0.5, -1.0), 0.0);
    }

    // --- compute_full_temporal_metrics ---

    #[test]
    fn compute_full_temporal_metrics_orchestrates_all_fields() {
        let history = m(&[&[0, 1], &[0, 1], &[0, -1]]);
        let positions: Vec<Vec<[f64; 2]>> = vec![
            vec![[0.0, 0.0], [0.0, 0.0]],
            vec![[1.0, 0.0], [0.0, 0.0]],
            vec![[2.0, 0.0], [0.0, 0.0]],
            vec![[3.0, 0.0], [0.0, 0.0]],
        ];
        let occ = vec![
            vec![true, true],
            vec![true, true],
            vec![true, false],
            vec![true, true],
        ];
        let metrics =
            compute_full_temporal_metrics(&history, 2, Some(&positions), Some(&occ), Some(0.9));

        assert!((0.0..=1.0).contains(&metrics.ip));
        assert_eq!(metrics.idsw, identity_switches(&history, 2));
        assert!(
            (metrics.track_fragmentation_rate - track_fragmentation_rate(&history, 2)).abs()
                < 1e-12
        );
        assert!(metrics.temporal_smoothness.abs() < 1e-9); // constant velocity for object 0
        assert_eq!(
            metrics.binding_robustness,
            binding_robustness_score(metrics.ip, 0.9)
        );
    }

    #[test]
    fn compute_full_temporal_metrics_defaults_without_optional_inputs() {
        let history = m(&[&[0], &[0]]);
        let metrics = compute_full_temporal_metrics(&history, 1, None, None, None);
        assert_eq!(metrics.temporal_smoothness, 0.0);
        assert!(metrics.recovery_speed.is_nan());
        assert_eq!(metrics.binding_robustness, 1.0);
    }
}
