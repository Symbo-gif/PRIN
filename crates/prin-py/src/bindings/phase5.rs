//! Phase 5 evaluation and experiment-tooling bindings.

use pyo3::exceptions::PyValueError;
use pyo3::prelude::*;

use prin_daemon::mot::{iou_distance_matrix, BBox, MotAccumulator};
use prin_dynamics::Seed;
use prin_train::adversarial::{
    adversarial_evaluate_phase_tracker, adversarial_evaluate_temporal_slot_attention_mot,
    AdversarialEvalResult, AttackKind,
};
use prin_train::dataset::{generate_dataset, TemporalClevrNConfig};
use prin_train::stats::{bootstrap_ci, cohens_d, compute_p_value, welch_t_test};
use prin_train::temporal_metrics::{
    binding_robustness_score, compute_full_temporal_metrics, identity_overcount, identity_switches,
    mostly_tracked_lost, recovery_speed, temporal_smoothness, track_duration_stats,
    track_fragmentation_rate,
};

use super::daemon::daemon_err_to_py;
use super::phase_tracker::PyPhaseTrackerBridge;
use super::slot_attention::PyTemporalSlotAttentionMOTBridge;
use super::train_support::{device, train_err_to_py};

/// Python-facing CLEAR-MOT/IDF1 summary.
#[pyclass(
    name = "MotSummary",
    module = "prin._prin_core",
    get_all,
    frozen,
    skip_from_py_object
)]
#[derive(Clone)]
pub struct PyMotSummary {
    mota: f64,
    motp: f64,
    idf1: f64,
    num_matches: u64,
    num_switches: u64,
    num_misses: u64,
    num_false_positives: u64,
    num_objects: u64,
}

/// Python-facing MOT event accumulator.
#[pyclass(name = "MotAccumulator", module = "prin._prin_core")]
pub struct PyMotAccumulator {
    inner: MotAccumulator,
}

#[pymethods]
impl PyMotAccumulator {
    /// Create an empty accumulator.
    #[new]
    #[pyo3(signature = (max_switch_time=None))]
    fn new(max_switch_time: Option<u64>) -> Self {
        Self {
            inner: max_switch_time
                .map_or_else(MotAccumulator::new, MotAccumulator::with_max_switch_time),
        }
    }

    /// Record one frame of object/hypothesis distances.
    fn update(
        &mut self,
        frame_id: u64,
        object_ids: Vec<u64>,
        hypothesis_ids: Vec<u64>,
        distances: Vec<Vec<f64>>,
    ) -> PyResult<()> {
        self.inner
            .update(frame_id, &object_ids, &hypothesis_ids, &distances)
            .map_err(daemon_err_to_py)
    }

    /// Compute metrics over all recorded frames.
    fn summary(&self) -> PyMotSummary {
        let value = self.inner.summary();
        PyMotSummary {
            mota: value.mota,
            motp: value.motp,
            idf1: value.idf1,
            num_matches: value.num_matches,
            num_switches: value.num_switches,
            num_misses: value.num_misses,
            num_false_positives: value.num_false_positives,
            num_objects: value.num_objects,
        }
    }
}

/// Compute an IoU distance matrix from `(x, y, width, height)` boxes.
#[pyfunction(name = "iou_distance_matrix")]
#[pyo3(signature = (objects, hypotheses, max_iou_distance=0.5))]
fn py_iou_distance_matrix(
    objects: Vec<(f64, f64, f64, f64)>,
    hypotheses: Vec<(f64, f64, f64, f64)>,
    max_iou_distance: f64,
) -> Vec<Vec<f64>> {
    let objects = objects
        .into_iter()
        .map(|(x, y, w, h)| BBox::new(x, y, w, h))
        .collect::<Vec<_>>();
    let hypotheses = hypotheses
        .into_iter()
        .map(|(x, y, w, h)| BBox::new(x, y, w, h))
        .collect::<Vec<_>>();
    iou_distance_matrix(&objects, &hypotheses, max_iou_distance)
}

/// Python-facing aggregate of temporal tracking metrics.
#[pyclass(
    name = "TemporalMetrics",
    module = "prin._prin_core",
    get_all,
    frozen,
    skip_from_py_object
)]
#[derive(Clone)]
pub struct PyTemporalMetrics {
    ip: f64,
    idsw: i64,
    temporal_smoothness: f64,
    track_fragmentation_rate: f64,
    identity_overcount: f64,
    mostly_tracked: f64,
    mostly_lost: f64,
    mean_track_duration: f64,
    median_track_duration: f64,
    recovery_speed: f64,
    binding_robustness: f64,
}

/// Compute all temporal tracking metrics in Rust.
#[pyfunction]
#[pyo3(signature = (matches_history, n_objects, positions=None, occlusion_mask=None, ip_baseline=None))]
fn py_compute_full_temporal_metrics(
    matches_history: Vec<Vec<i64>>,
    n_objects: usize,
    positions: Option<Vec<Vec<(f64, f64)>>>,
    occlusion_mask: Option<Vec<Vec<bool>>>,
    ip_baseline: Option<f64>,
) -> PyTemporalMetrics {
    let positions = positions.map(|frames| {
        frames
            .into_iter()
            .map(|frame| frame.into_iter().map(|(x, y)| [x, y]).collect())
            .collect::<Vec<Vec<[f64; 2]>>>()
    });
    let value = compute_full_temporal_metrics(
        &matches_history,
        n_objects,
        positions.as_deref(),
        occlusion_mask.as_deref(),
        ip_baseline,
    );
    PyTemporalMetrics {
        ip: value.ip,
        idsw: value.idsw,
        temporal_smoothness: value.temporal_smoothness,
        track_fragmentation_rate: value.track_fragmentation_rate,
        identity_overcount: value.identity_overcount,
        mostly_tracked: value.mostly_tracked,
        mostly_lost: value.mostly_lost,
        mean_track_duration: value.mean_track_duration,
        median_track_duration: value.median_track_duration,
        recovery_speed: value.recovery_speed,
        binding_robustness: value.binding_robustness,
    }
}

/// Count identity switches in a match history.
#[pyfunction(name = "identity_switches")]
fn py_identity_switches(matches_history: Vec<Vec<i64>>, n_objects: usize) -> i64 {
    identity_switches(&matches_history, n_objects)
}

/// Compute track fragments per object.
#[pyfunction(name = "track_fragmentation_rate")]
fn py_track_fragmentation_rate(matches_history: Vec<Vec<i64>>, n_objects: usize) -> f64 {
    track_fragmentation_rate(&matches_history, n_objects)
}

/// Compute unique predicted identities per object.
#[pyfunction(name = "identity_overcount")]
fn py_identity_overcount(matches_history: Vec<Vec<i64>>, n_objects: usize) -> f64 {
    identity_overcount(&matches_history, n_objects)
}

/// Compute mostly-tracked and mostly-lost fractions.
#[pyfunction(name = "mostly_tracked_lost")]
#[pyo3(signature = (matches_history, n_objects, tracked_threshold=0.8, lost_threshold=0.2))]
fn py_mostly_tracked_lost(
    matches_history: Vec<Vec<i64>>,
    n_objects: usize,
    tracked_threshold: f64,
    lost_threshold: f64,
) -> (f64, f64) {
    mostly_tracked_lost(
        &matches_history,
        n_objects,
        tracked_threshold,
        lost_threshold,
    )
}

/// Compute mean and median maintained-identity duration.
#[pyfunction(name = "track_duration_stats")]
fn py_track_duration_stats(matches_history: Vec<Vec<i64>>, n_objects: usize) -> (f64, f64) {
    track_duration_stats(&matches_history, n_objects)
}

/// Compute mean re-binding delay after occlusion.
#[pyfunction(name = "recovery_speed")]
fn py_recovery_speed(
    matches_history: Vec<Vec<i64>>,
    occlusion_mask: Vec<Vec<bool>>,
    n_objects: usize,
) -> f64 {
    recovery_speed(&matches_history, &occlusion_mask, n_objects)
}

/// Compute mean second-difference norm over tracked positions.
#[pyfunction(name = "temporal_smoothness")]
fn py_temporal_smoothness(positions: Vec<Vec<(f64, f64)>>) -> f64 {
    let positions = positions
        .into_iter()
        .map(|frame| frame.into_iter().map(|(x, y)| [x, y]).collect())
        .collect::<Vec<Vec<[f64; 2]>>>();
    temporal_smoothness(&positions)
}

/// Compute perturbed-to-baseline identity-preservation ratio.
#[pyfunction(name = "binding_robustness_score")]
fn py_binding_robustness_score(ip_perturbed: f64, ip_baseline: f64) -> f64 {
    binding_robustness_score(ip_perturbed, ip_baseline)
}

/// Python-facing percentile bootstrap confidence interval.
#[pyclass(
    name = "BootstrapCi",
    module = "prin._prin_core",
    get_all,
    frozen,
    skip_from_py_object
)]
#[derive(Clone)]
pub struct PyBootstrapCi {
    mean: f64,
    ci_lower: f64,
    ci_upper: f64,
    ci_width: f64,
    se: f64,
}

/// Compute a deterministic percentile bootstrap confidence interval.
#[pyfunction]
#[pyo3(signature = (values, n_bootstrap=10_000, alpha=0.05, seed_counter=0, seed_key=0))]
fn py_bootstrap_ci(
    values: Vec<f64>,
    n_bootstrap: usize,
    alpha: f64,
    seed_counter: u64,
    seed_key: u64,
) -> PyResult<PyBootstrapCi> {
    let mut seed = Seed::new(seed_counter as u128, seed_key as u128);
    let value = bootstrap_ci(&values, n_bootstrap, alpha, &mut seed).map_err(train_err_to_py)?;
    Ok(PyBootstrapCi {
        mean: value.mean,
        ci_lower: value.ci_lower,
        ci_upper: value.ci_upper,
        ci_width: value.ci_width,
        se: value.se,
    })
}

/// Python-facing Welch unequal-variance t-test result.
#[pyclass(
    name = "WelchTTest",
    module = "prin._prin_core",
    get_all,
    frozen,
    skip_from_py_object
)]
#[derive(Clone)]
pub struct PyWelchTTest {
    t_stat: f64,
    p_value: f64,
    cohens_d: f64,
    mean_diff: f64,
}

/// Compute Welch's unequal-variance t-test and Cohen's d.
#[pyfunction]
fn py_welch_t_test(group_a: Vec<f64>, group_b: Vec<f64>) -> PyResult<PyWelchTTest> {
    let value = welch_t_test(&group_a, &group_b).map_err(train_err_to_py)?;
    Ok(PyWelchTTest {
        t_stat: value.t_stat,
        p_value: value.p_value,
        cohens_d: value.cohens_d,
        mean_diff: value.mean_diff,
    })
}

/// Compute Cohen's pooled-standard-deviation effect size.
#[pyfunction(name = "cohens_d")]
fn py_cohens_d(group_a: Vec<f64>, group_b: Vec<f64>) -> f64 {
    cohens_d(&group_a, &group_b)
}

/// Compute the two-tailed Welch-test p-value only.
#[pyfunction(name = "compute_p_value")]
fn py_compute_p_value(group_a: Vec<f64>, group_b: Vec<f64>) -> PyResult<f64> {
    compute_p_value(&group_a, &group_b).map_err(train_err_to_py)
}

/// Python-facing adversarial evaluation result.
#[pyclass(
    name = "AdversarialEvalResult",
    module = "prin._prin_core",
    get_all,
    frozen,
    skip_from_py_object
)]
#[derive(Clone)]
pub struct PyAdversarialEvalResult {
    clean_ip: f64,
    adv_ip: f64,
    degradation: f64,
    per_seq_clean: Vec<f64>,
    per_seq_adv: Vec<f64>,
}

fn attack_kind(name: &str, pgd_steps: usize) -> PyResult<AttackKind> {
    match name.trim().to_ascii_lowercase().as_str() {
        "fgsm" => Ok(AttackKind::Fgsm),
        "pgd" if pgd_steps > 0 => Ok(AttackKind::Pgd { steps: pgd_steps }),
        "pgd" => Err(PyValueError::new_err("pgd_steps must be positive")),
        _ => Err(PyValueError::new_err("attack must be 'fgsm' or 'pgd'")),
    }
}

fn evaluation_dataset(
    n_sequences: usize,
    n_objects: usize,
    n_frames: usize,
    detection_dim: usize,
    seed: u64,
) -> PyResult<Vec<prin_train::dataset::SequenceData>> {
    if n_sequences == 0 {
        return Err(PyValueError::new_err("n_sequences must be positive"));
    }
    let config = TemporalClevrNConfig::with_params(
        n_objects,
        n_frames,
        detection_dim,
        (0.5, 2.0),
        0.0,
        0.0,
        0,
        0.0,
    )
    .map_err(train_err_to_py)?;
    Ok(generate_dataset(n_sequences, &config, seed as u128))
}

fn adversarial_result(value: AdversarialEvalResult) -> PyAdversarialEvalResult {
    PyAdversarialEvalResult {
        clean_ip: value.clean_ip,
        adv_ip: value.adv_ip,
        degradation: value.degradation,
        per_seq_clean: value.per_seq_clean,
        per_seq_adv: value.per_seq_adv,
    }
}

/// Evaluate a PhaseTracker on deterministic synthetic sequences under attack.
#[pyfunction]
#[pyo3(signature = (
    tracker,
    epsilon,
    attack="fgsm",
    pgd_steps=20,
    n_sequences=4,
    n_objects=4,
    n_frames=20,
    detection_dim=4,
    seed=0,
))]
#[allow(clippy::too_many_arguments)]
fn py_adversarial_evaluate_phase_tracker(
    tracker: &PyPhaseTrackerBridge,
    epsilon: f64,
    attack: &str,
    pgd_steps: usize,
    n_sequences: usize,
    n_objects: usize,
    n_frames: usize,
    detection_dim: usize,
    seed: u64,
) -> PyResult<PyAdversarialEvalResult> {
    let dataset = evaluation_dataset(n_sequences, n_objects, n_frames, detection_dim, seed)?;
    adversarial_evaluate_phase_tracker(
        tracker.tracker(),
        &dataset,
        epsilon,
        attack_kind(attack, pgd_steps)?,
        seed,
        &device(),
    )
    .map(adversarial_result)
    .map_err(train_err_to_py)
}

/// Evaluate a TemporalSlotAttentionMOT on synthetic sequences under attack.
#[pyfunction]
#[pyo3(signature = (
    tracker,
    epsilon,
    attack="fgsm",
    pgd_steps=20,
    n_sequences=4,
    n_objects=4,
    n_frames=20,
    detection_dim=4,
    seed=0,
))]
#[allow(clippy::too_many_arguments)]
fn py_adversarial_evaluate_slot_attention(
    tracker: &PyTemporalSlotAttentionMOTBridge,
    epsilon: f64,
    attack: &str,
    pgd_steps: usize,
    n_sequences: usize,
    n_objects: usize,
    n_frames: usize,
    detection_dim: usize,
    seed: u64,
) -> PyResult<PyAdversarialEvalResult> {
    let dataset = evaluation_dataset(n_sequences, n_objects, n_frames, detection_dim, seed)?;
    adversarial_evaluate_temporal_slot_attention_mot(
        tracker.tracker(),
        &dataset,
        epsilon,
        attack_kind(attack, pgd_steps)?,
        seed,
        &device(),
    )
    .map(adversarial_result)
    .map_err(train_err_to_py)
}

/// Register Phase 5 evaluation and experiment-tooling bindings.
pub(crate) fn register(m: &Bound<'_, PyModule>) -> PyResult<()> {
    m.add_class::<PyMotSummary>()?;
    m.add_class::<PyMotAccumulator>()?;
    m.add_class::<PyTemporalMetrics>()?;
    m.add_class::<PyBootstrapCi>()?;
    m.add_class::<PyWelchTTest>()?;
    m.add_class::<PyAdversarialEvalResult>()?;
    m.add_function(wrap_pyfunction!(py_iou_distance_matrix, m)?)?;
    m.add_function(wrap_pyfunction!(py_compute_full_temporal_metrics, m)?)?;
    m.add_function(wrap_pyfunction!(py_identity_switches, m)?)?;
    m.add_function(wrap_pyfunction!(py_track_fragmentation_rate, m)?)?;
    m.add_function(wrap_pyfunction!(py_identity_overcount, m)?)?;
    m.add_function(wrap_pyfunction!(py_mostly_tracked_lost, m)?)?;
    m.add_function(wrap_pyfunction!(py_track_duration_stats, m)?)?;
    m.add_function(wrap_pyfunction!(py_recovery_speed, m)?)?;
    m.add_function(wrap_pyfunction!(py_temporal_smoothness, m)?)?;
    m.add_function(wrap_pyfunction!(py_binding_robustness_score, m)?)?;
    m.add_function(wrap_pyfunction!(py_bootstrap_ci, m)?)?;
    m.add_function(wrap_pyfunction!(py_welch_t_test, m)?)?;
    m.add_function(wrap_pyfunction!(py_cohens_d, m)?)?;
    m.add_function(wrap_pyfunction!(py_compute_p_value, m)?)?;
    m.add_function(wrap_pyfunction!(py_adversarial_evaluate_phase_tracker, m)?)?;
    m.add_function(wrap_pyfunction!(py_adversarial_evaluate_slot_attention, m)?)?;
    Ok(())
}
