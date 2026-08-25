//! PyO3 orchestration entry point for
//! [`prin_train::trainer::train_phase_tracker`] (WP-027).
//!
//! This is the "trainable API acceptance" entry point the session mission
//! calls for: a single Python-callable function that constructs a
//! [`prin_train::phase_tracker::PhaseTracker`], generates temporal CLEVR-N
//! training/validation data, and runs the full Rust-native training loop
//! (`crates/prin-train/src/trainer.rs`) end to end — no numerics live in
//! Python (Project Plan §4 rule 2); this module only converts Rust results
//! to Python types.

use pyo3::prelude::*;

use prin_dynamics::Seed;
use prin_train::dataset::{generate_dataset, TemporalClevrNConfig};
use prin_train::phase_tracker::PhaseTrackerConfig;
use prin_train::trainer::{
    train_phase_tracker as run_temporal_trainer, TemporalTrainerConfig, TrainingResult,
};

use super::phase_tracker::PyPhaseTrackerBridge;
use super::train_support::{device, train_err_to_py, BridgeBackend};

/// Python-facing mirror of [`prin_train::trainer::TrainingResult`].
#[pyclass(name = "TrainingResult", module = "prin._prin_core", get_all)]
pub struct PyTrainingResult {
    /// Final epoch's mean training loss.
    final_train_loss: f64,
    /// Final (best-restored) validation loss.
    final_val_loss: f64,
    /// Final (best-restored) validation identity preservation, `[0, 1]`.
    final_val_ip: f64,
    /// Best smoothed validation loss observed.
    best_val_loss: f64,
    /// Epoch at which the best smoothed validation loss was observed.
    best_epoch: usize,
    /// Total epochs actually run (may be less than `max_epochs` on early
    /// stop).
    total_epochs: usize,
    /// Per-epoch mean training loss.
    train_losses: Vec<f64>,
    /// Per-epoch validation loss.
    val_losses: Vec<f64>,
    /// Per-epoch validation identity preservation.
    val_ips: Vec<f64>,
}

impl From<TrainingResult> for PyTrainingResult {
    fn from(r: TrainingResult) -> Self {
        Self {
            final_train_loss: r.final_train_loss,
            final_val_loss: r.final_val_loss,
            final_val_ip: r.final_val_ip,
            best_val_loss: r.best_val_loss,
            best_epoch: r.best_epoch,
            total_epochs: r.total_epochs,
            train_losses: r.train_losses,
            val_losses: r.val_losses,
            val_ips: r.val_ips,
        }
    }
}

/// Construct a [`PhaseTracker`](prin_train::phase_tracker::PhaseTracker),
/// generate temporal CLEVR-N training/validation data, and train it end to
/// end via [`prin_train::trainer::train_phase_tracker`].
///
/// Returns `(trained_bridge, result)`: the trained model (usable for further
/// inference/checkpointing exactly like a freshly-constructed
/// `PhaseTrackerBridge`) and the full training history.
///
/// Dataset perturbations (occlusion/swap/reversal/noise) are fixed at the
/// PRINet 3.0 reference's defaults (disabled) to match the registered
/// validation protocol; callers needing perturbed sequences should use the
/// lower-level Rust API (`prin_train::dataset`) directly — a deliberate,
/// documented scope boundary for this convenience entry point, not a
/// silently dropped capability.
///
/// # Errors
///
/// Raises `ValueError` if any hyperparameter is invalid (see
/// [`PhaseTrackerConfig::with_params`], [`TemporalClevrNConfig::with_params`],
/// [`TemporalTrainerConfig::validate`]).
#[allow(clippy::too_many_arguments)]
#[pyfunction]
#[pyo3(name = "train_phase_tracker")]
#[pyo3(signature = (
    detection_dim,
    n_delta=4, n_theta=8, n_gamma=16, n_discrete_steps=5, match_threshold=0.3,
    n_objects=4, n_frames=20, det_dim=4,
    train_seqs=50, val_seqs=10, dataset_seed=42,
    lr=3e-4, weight_decay=0.0, max_epochs=100, patience=10, smoothing_window=5,
    warmup_epochs=5, grad_clip=1.0, model_seed=0,
))]
fn py_train_phase_tracker(
    py: Python<'_>,
    detection_dim: usize,
    n_delta: usize,
    n_theta: usize,
    n_gamma: usize,
    n_discrete_steps: usize,
    match_threshold: f64,
    n_objects: usize,
    n_frames: usize,
    det_dim: usize,
    train_seqs: usize,
    val_seqs: usize,
    dataset_seed: u64,
    lr: f64,
    weight_decay: f64,
    max_epochs: usize,
    patience: usize,
    smoothing_window: usize,
    warmup_epochs: usize,
    grad_clip: f64,
    model_seed: u64,
) -> PyResult<(Py<PyPhaseTrackerBridge>, PyTrainingResult)> {
    let tracker_config = PhaseTrackerConfig::with_params(
        detection_dim,
        n_delta,
        n_theta,
        n_gamma,
        n_discrete_steps,
        match_threshold,
    )
    .map_err(train_err_to_py)?;
    let mut init_seed = Seed::new(model_seed as u128, 1);
    let model = tracker_config.init::<BridgeBackend>(&device(), &mut init_seed);

    let dataset_config = TemporalClevrNConfig::with_params(
        n_objects,
        n_frames,
        det_dim,
        (0.5, 2.0),
        0.0,
        0.0,
        0,
        0.0,
    )
    .map_err(train_err_to_py)?;
    let train_data = generate_dataset(train_seqs, &dataset_config, dataset_seed as u128);
    let val_data = generate_dataset(val_seqs, &dataset_config, dataset_seed as u128 + 9000);

    let trainer_config = TemporalTrainerConfig {
        lr,
        weight_decay,
        max_epochs,
        patience,
        smoothing_window,
        warmup_epochs,
        grad_clip,
        ..TemporalTrainerConfig::default()
    };

    let mut train_seed = Seed::new(model_seed as u128, 2);
    let (trained, result) = run_temporal_trainer(
        model,
        &trainer_config,
        &train_data,
        &val_data,
        &device(),
        &mut train_seed,
    )
    .map_err(train_err_to_py)?;

    let bridge = PyPhaseTrackerBridge::from_tracker(trained);
    Ok((Py::new(py, bridge)?, PyTrainingResult::from(result)))
}

pub(crate) fn register(m: &Bound<'_, PyModule>) -> PyResult<()> {
    m.add_class::<PyTrainingResult>()?;
    m.add_function(wrap_pyfunction!(py_train_phase_tracker, m)?)?;
    Ok(())
}
