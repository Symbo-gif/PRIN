//! PyO3 bridge for [`prin_train::allocation`] (Exec-WP-026 S1): adaptive
//! oscillator-count allocation.
//!
//! Every entry point here is **non-differentiable** (Coding Standards §3.2
//! governs "trainable ops"; oscillator *counts* are discrete outputs derived
//! via `floor`/`round`, not a differentiable computation to begin with — see
//! [`prin_train::allocation::OscillatorBudget`]'s own module docs). Bridged
//! as plain PyO3 methods, not `torch.autograd.Function`s.

use pyo3::exceptions::PyValueError;
use pyo3::prelude::*;
use pyo3::types::PyBytes;

use burn::module::Module;
use prin_dynamics::Seed;
use prin_train::allocation::{
    estimate_complexity, AdaptiveOscillatorAllocator, AdaptiveOscillatorAllocatorConfig,
    AllocatorStrategy, DynamicPhaseTracker, OscillatorBudget,
};

use super::state::PySeed;
use super::train_support::{
    device, export_tensor, load_checkpoint_record, record_to_bytes, tensor_from_dlpack,
    train_err_to_py, BridgeBackend,
};

fn parse_strategy(strategy: &str) -> PyResult<AllocatorStrategy> {
    match strategy {
        "rule" => Ok(AllocatorStrategy::Rule),
        "learned" => Ok(AllocatorStrategy::Learned),
        other => Err(PyValueError::new_err(format!(
            "unknown allocator strategy {other:?}, expected \"rule\" or \"learned\""
        ))),
    }
}

fn strategy_name(strategy: AllocatorStrategy) -> &'static str {
    match strategy {
        AllocatorStrategy::Rule => "rule",
        AllocatorStrategy::Learned => "learned",
    }
}

/// Python-facing mirror of [`OscillatorBudget`]: allocated oscillator counts
/// per frequency band, plus the complexity value that produced them.
#[pyclass(
    name = "OscillatorBudget",
    module = "prin._prin_core",
    get_all,
    skip_from_py_object
)]
#[derive(Clone)]
pub struct PyOscillatorBudget {
    /// Delta-band (1-4 Hz) oscillators.
    n_delta: usize,
    /// Theta-band (4-8 Hz) oscillators.
    n_theta: usize,
    /// Gamma-band (30-100 Hz) oscillators.
    n_gamma: usize,
    /// Estimated scene complexity in `[0, 1]`.
    complexity: f64,
}

#[pymethods]
impl PyOscillatorBudget {
    /// Total oscillator count across all bands.
    fn total(&self) -> usize {
        self.n_delta + self.n_theta + self.n_gamma
    }

    fn __repr__(&self) -> String {
        format!(
            "OscillatorBudget(n_delta={}, n_theta={}, n_gamma={}, complexity={})",
            self.n_delta, self.n_theta, self.n_gamma, self.complexity
        )
    }
}

impl From<OscillatorBudget> for PyOscillatorBudget {
    fn from(b: OscillatorBudget) -> Self {
        Self {
            n_delta: b.n_delta,
            n_theta: b.n_theta,
            n_gamma: b.n_gamma,
            complexity: b.complexity,
        }
    }
}

/// Estimate scene complexity from detection features, a scalar in `[0, 1]`.
/// `detections` is `[n, d]` with `d >= 2` (first two columns treated as a
/// spatial centroid). **Non-differentiable** — see
/// [`prin_train::allocation::estimate_complexity`]'s docs.
///
/// # Errors
///
/// Raises `ValueError` on a non-`float64`/non-CPU/non-contiguous input or a
/// shape other than rank 2.
#[pyfunction(name = "estimate_complexity")]
#[pyo3(signature = (detections, spatial_weight=0.5, count_weight=0.5, max_objects=50))]
pub fn py_estimate_complexity(
    detections: &Bound<'_, PyAny>,
    spatial_weight: f64,
    count_weight: f64,
    max_objects: usize,
) -> PyResult<f64> {
    let detections = tensor_from_dlpack::<2>(detections)?;
    Ok(estimate_complexity(
        &detections,
        spatial_weight,
        count_weight,
        max_objects,
    ))
}

/// [`AdaptiveOscillatorAllocator`], bridged to Python.
#[pyclass(
    name = "AdaptiveOscillatorAllocatorBridge",
    module = "prin._prin_core",
    unsendable
)]
pub struct PyAdaptiveOscillatorAllocatorBridge {
    allocator: AdaptiveOscillatorAllocator<BridgeBackend>,
}

#[pymethods]
impl PyAdaptiveOscillatorAllocatorBridge {
    /// Construct with seeded-random parameters (the learned-strategy MLP
    /// only; the rule strategy has none). `strategy` is `"rule"` or
    /// `"learned"`.
    ///
    /// # Errors
    ///
    /// Raises `ValueError` for invalid hyperparameters or an unknown
    /// `strategy`.
    #[new]
    #[pyo3(signature = (
        min_total, max_total, delta_ratio=0.1, theta_ratio=0.2, strategy="rule",
        complexity_dim=1, seed_counter=0, seed_key=0,
    ))]
    #[allow(clippy::too_many_arguments)]
    fn new(
        min_total: usize,
        max_total: usize,
        delta_ratio: f64,
        theta_ratio: f64,
        strategy: &str,
        complexity_dim: usize,
        seed_counter: u64,
        seed_key: u64,
    ) -> PyResult<Self> {
        let strategy = parse_strategy(strategy)?;
        let cfg = AdaptiveOscillatorAllocatorConfig::with_params(
            min_total,
            max_total,
            delta_ratio,
            theta_ratio,
            strategy,
            complexity_dim,
        )
        .map_err(train_err_to_py)?;
        let mut seed = Seed::new(seed_counter as u128, seed_key as u128);
        let allocator = cfg.init::<BridgeBackend>(&device(), &mut seed);
        Ok(Self { allocator })
    }

    /// The configured allocation strategy (`"rule"` or `"learned"`).
    #[getter]
    fn strategy(&self) -> &'static str {
        strategy_name(self.allocator.strategy())
    }

    /// Compute an oscillator budget for `complexity` (clamped to `[0, 1]`).
    /// Uses the learned MLP only when [`Self::strategy`] is `"learned"`
    /// **and** `features` is supplied; falls back to the rule-based formula
    /// otherwise.
    ///
    /// # Errors
    ///
    /// Raises `ValueError` if `features` is supplied with an invalid shape.
    #[pyo3(signature = (complexity, features=None))]
    fn allocate(
        &self,
        complexity: f64,
        features: Option<&Bound<'_, PyAny>>,
    ) -> PyResult<PyOscillatorBudget> {
        let features = features.map(tensor_from_dlpack::<2>).transpose()?;
        Ok(self.allocator.allocate(complexity, features).into())
    }

    /// Generate budgets for `steps` evenly-spaced complexity values in
    /// `[0, 1]`.
    fn sweep_complexity(&self, steps: usize) -> Vec<PyOscillatorBudget> {
        self.allocator
            .sweep_complexity(steps)
            .into_iter()
            .map(PyOscillatorBudget::from)
            .collect()
    }

    /// Serialize parameters to checkpoint bytes (empty for the rule
    /// strategy, which has no learnable parameters).
    fn state_dict<'py>(&self, py: Python<'py>) -> PyResult<Bound<'py, PyBytes>> {
        let bytes = record_to_bytes(&self.allocator)?;
        Ok(PyBytes::new(py, &bytes))
    }

    /// Restore parameters previously produced by [`Self::state_dict`],
    /// rejecting a shape mismatch and leaving `self` unchanged on failure
    /// (see [`prin_train::allocation::AdaptiveOscillatorAllocator::validate_shapes`]
    /// for the scope of what this catches).
    ///
    /// # Errors
    ///
    /// Raises `ValueError` if `bytes` does not decode to a valid record, or
    /// decodes to a learned-strategy MLP whose shape does not match this
    /// allocator's `complexity_dim`.
    fn load_state_dict(&mut self, bytes: &[u8]) -> PyResult<()> {
        let record = load_checkpoint_record::<AdaptiveOscillatorAllocator<BridgeBackend>>(bytes)?;
        let candidate = self.allocator.clone().load_record(record);
        candidate
            .validate_shapes()
            .map_err(|e| PyValueError::new_err(format!("checkpoint shape mismatch: {e}")))?;
        self.allocator = candidate;
        Ok(())
    }
}

/// [`DynamicPhaseTracker`], bridged to Python: a [`super::phase_tracker::PyPhaseTrackerBridge`]-class
/// tracker with an oscillator budget adapted to estimated scene complexity,
/// lazily built and cached per distinct budget.
///
/// Not a checkpointable `Module` in Rust either (see the Rust type's own
/// module docs: its whole purpose is to lazily cache a *different*
/// `PhaseTracker` per budget, which has no fixed parameter set to describe) —
/// no `state_dict`/`load_state_dict` here.
#[pyclass(
    name = "DynamicPhaseTrackerBridge",
    module = "prin._prin_core",
    unsendable
)]
pub struct PyDynamicPhaseTrackerBridge {
    tracker: DynamicPhaseTracker<BridgeBackend>,
}

#[pymethods]
impl PyDynamicPhaseTrackerBridge {
    /// Construct over a rule- or learned-strategy allocator with the given
    /// oscillator range. Individual `PhaseTracker` instances are built
    /// lazily (and seeded from this constructor's `seed`) the first time a
    /// given budget is requested by [`Self::forward`].
    ///
    /// # Errors
    ///
    /// Raises `ValueError` for invalid hyperparameters or an unknown
    /// `allocator_strategy`.
    #[new]
    #[pyo3(signature = (
        detection_dim, min_total, max_total, n_discrete_steps=5, match_threshold=0.3,
        allocator_strategy="rule", max_objects=50, seed_counter=0, seed_key=0,
    ))]
    #[allow(clippy::too_many_arguments)]
    fn new(
        detection_dim: usize,
        min_total: usize,
        max_total: usize,
        n_discrete_steps: usize,
        match_threshold: f64,
        allocator_strategy: &str,
        max_objects: usize,
        seed_counter: u64,
        seed_key: u64,
    ) -> PyResult<Self> {
        let strategy = parse_strategy(allocator_strategy)?;
        let mut seed = Seed::new(seed_counter as u128, seed_key as u128);
        let tracker = DynamicPhaseTracker::new(
            detection_dim,
            min_total,
            max_total,
            n_discrete_steps,
            match_threshold,
            strategy,
            max_objects,
            &device(),
            &mut seed,
        )
        .map_err(train_err_to_py)?;
        Ok(Self { tracker })
    }

    /// Match detections with an oscillator budget adapted to the estimated
    /// complexity of `detections_t`. **Non-differentiable**. `seed` is
    /// consumed (advanced) — a newly-required budget lazily seeds and caches
    /// a fresh `PhaseTracker`.
    ///
    /// **Faithfully reproduced quirk**: always uses rule-based allocation,
    /// even if this tracker's allocator is `"learned"` (see the Rust
    /// module's docs — a real PRINet 3.0 behavior, preserved intentionally,
    /// not silently "fixed").
    ///
    /// # Errors
    ///
    /// Raises `ValueError` on a shape mismatch.
    fn forward(
        &self,
        py: Python<'_>,
        detections_t: &Bound<'_, PyAny>,
        detections_t1: &Bound<'_, PyAny>,
        seed: &mut PySeed,
    ) -> PyResult<(Vec<i64>, Py<PyAny>, PyOscillatorBudget)> {
        let detections_t = tensor_from_dlpack::<2>(detections_t)?;
        let detections_t1 = tensor_from_dlpack::<2>(detections_t1)?;
        let (matches, sim, budget) = self
            .tracker
            .forward(detections_t, detections_t1, &mut seed.inner)
            .map_err(train_err_to_py)?;
        Ok((matches, export_tensor::<2>(py, sim.inner())?, budget.into()))
    }
}

pub(crate) fn register(m: &Bound<'_, PyModule>) -> PyResult<()> {
    m.add_function(pyo3::wrap_pyfunction!(py_estimate_complexity, m)?)?;
    m.add_class::<PyOscillatorBudget>()?;
    m.add_class::<PyAdaptiveOscillatorAllocatorBridge>()?;
    m.add_class::<PyDynamicPhaseTrackerBridge>()?;
    Ok(())
}
