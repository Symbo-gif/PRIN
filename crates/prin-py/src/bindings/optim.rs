//! PyO3 bridges for PRIN's oscillator-aware optimizers (WP-027):
//! [`SyncGd`], [`Scalr`], [`Rip`] — the `torch.optim.Optimizer`-wrapper
//! scope declared in PSR-026 §6, mirroring the reference's
//! `nn/optimizers.py` mapping ("SCALR/RIP/SyncGD need order-parameter
//! feedback → Rust computes metrics, Python optimizer classes stay thin").
//!
//! # Differentiability
//!
//! Every method here is **non-differentiable** by design: an optimizer step
//! consumes an already-computed gradient and produces the next parameter
//! value — it is not itself part of the autograd graph, exactly as a custom
//! `torch.optim.Optimizer.step()` operates on `param.data`/`param.grad`
//! rather than `param` directly. No `torch.autograd.Function` bridge is
//! needed (contrast `train.rs`/`phase_tracker.rs`, whose bridged methods
//! *are* differentiable forward ops).
//!
//! # Rank convention
//!
//! [`SyncGd`]/[`Scalr`] are generic per-parameter optimizers in
//! `prin-train` (any tensor rank `D`); this bridge fixes `D = 1` — the
//! Python `torch.optim.Optimizer` wrapper (`python/prin/nn/optimizers.py`)
//! flattens each parameter to 1-D before calling `step` and reshapes the
//! result back, the standard flatten/update/reshape pattern for wrapping a
//! per-element optimizer over arbitrary-shaped parameters. [`Rip`] is
//! inherently rank-2 (a square `n_oscillators x n_oscillators` coupling
//! matrix, fixed at construction) and needs no flattening.
//!
//! # Checkpointing scope
//!
//! `state_dict`/`load_state_dict` round-trip each optimizer's scalar/history
//! [`OscillatorOptimizer::State`] (step counters, order-parameter history,
//! adaptive thresholds) as JSON — the same non-tensor state Rust's own
//! `state_round_trips_through_json` tests cover. The momentum buffer
//! (`SyncGd`/`Scalr`, non-empty only when `momentum != 0.0`, not PRINet
//! 3.0's default) is **not** included in this MVP checkpoint scope — a
//! documented, non-silent boundary: full momentum-buffer persistence is
//! deferred to a future WP if a workload actually needs
//! `momentum != 0.0` resume fidelity.

use pyo3::exceptions::PyValueError;
use pyo3::prelude::*;

use prin_train::feedback::{OscillatorOptimizer, StepFeedback};
use prin_train::rip::{Rip, RipConfig};
use prin_train::scalr::{Scalr, ScalrConfig};
use prin_train::sync_gd::{SyncGd, SyncGdConfig};

use super::train_support::{export_tensor, tensor_from_dlpack, train_err_to_py, BridgeBackend};

fn state_to_json<S: serde::Serialize>(state: &S) -> PyResult<String> {
    serde_json::to_string(state)
        .map_err(|e| PyValueError::new_err(format!("optimizer state serialization failed: {e}")))
}

fn state_from_json<S: serde::de::DeserializeOwned>(json: &str) -> PyResult<S> {
    serde_json::from_str(json)
        .map_err(|e| PyValueError::new_err(format!("optimizer state deserialization failed: {e}")))
}

// --- SyncGd --------------------------------------------------------------

/// PyO3 bridge for [`SyncGd`] (SGD with a Kuramoto-order-parameter
/// synchronization-barrier penalty), fixed at rank `D = 1` — see module
/// docs.
#[pyclass(name = "SyncGdBridge", module = "prin._prin_core", unsendable)]
pub struct PySyncGdBridge {
    inner: SyncGd<BridgeBackend, 1>,
}

#[pymethods]
impl PySyncGdBridge {
    /// Construct with PRINet 3.0's default hyperparameters unless
    /// overridden (see [`SyncGdConfig::with_params`]).
    #[new]
    #[pyo3(signature = (lr=0.01, momentum=0.0, weight_decay=0.0, sync_penalty=0.1, critical_order=0.5, dampening=0.0))]
    fn new(
        lr: f64,
        momentum: f64,
        weight_decay: f64,
        sync_penalty: f64,
        critical_order: f64,
        dampening: f64,
    ) -> PyResult<Self> {
        let config = SyncGdConfig::with_params(
            lr,
            momentum,
            weight_decay,
            sync_penalty,
            critical_order,
            dampening,
        )
        .map_err(train_err_to_py)?;
        Ok(Self {
            inner: config.init::<BridgeBackend, 1>(),
        })
    }

    /// Apply one update to a 1-D `param` tensor given its gradient (`None`
    /// skips the update, matching `if p.grad is None: continue`) and an
    /// optional Kuramoto order parameter. Returns the updated parameter.
    ///
    /// # Errors
    ///
    /// Raises `ValueError` on a shape mismatch between `param` and `grad`.
    #[pyo3(signature = (param, grad=None, order_parameter=None))]
    fn step(
        &mut self,
        py: Python<'_>,
        param: &Bound<'_, PyAny>,
        grad: Option<&Bound<'_, PyAny>>,
        order_parameter: Option<f64>,
    ) -> PyResult<Py<PyAny>> {
        let param_t = tensor_from_dlpack::<1>(param)?;
        let grad_t = grad.map(tensor_from_dlpack::<1>).transpose()?;
        let feedback = match order_parameter {
            Some(r) => StepFeedback::order(r),
            None => StepFeedback::none(),
        };
        let updated = self
            .inner
            .step(param_t, grad_t, &feedback)
            .map_err(train_err_to_py)?;
        export_tensor::<1>(py, updated.inner())
    }

    /// Serialize the optimizer's scalar/history state to JSON (see module
    /// docs for the momentum-buffer scope boundary).
    fn state_dict(&self) -> PyResult<String> {
        state_to_json(&self.inner.state_dict())
    }

    /// Restore state previously produced by [`Self::state_dict`].
    ///
    /// # Errors
    ///
    /// Raises `ValueError` on malformed JSON or invalid hyperparameters.
    fn load_state_dict(&mut self, json: &str) -> PyResult<()> {
        let state = state_from_json(json)?;
        self.inner.load_state_dict(state).map_err(train_err_to_py)
    }
}

// --- Scalr -----------------------------------------------------------------

/// PyO3 bridge for [`Scalr`] (Synchronization-Coupled Adaptive Learning
/// Rate), fixed at rank `D = 1` — see module docs.
#[pyclass(name = "ScalrBridge", module = "prin._prin_core", unsendable)]
pub struct PyScalrBridge {
    inner: Scalr<BridgeBackend, 1>,
}

#[pymethods]
impl PyScalrBridge {
    /// Construct with PRINet 3.0's default hyperparameters unless
    /// overridden (see [`ScalrConfig::with_params`]).
    #[new]
    #[allow(clippy::too_many_arguments)]
    #[pyo3(signature = (
        lr=0.01, momentum=0.0, weight_decay=0.0, r_min=0.1, alpha=1.0,
        warmup_steps=0, oscillation_window=20, oscillation_threshold=0.01,
        oscillation_decay=0.95, adaptive_r_min=false, r_min_ema_alpha=0.1,
    ))]
    fn new(
        lr: f64,
        momentum: f64,
        weight_decay: f64,
        r_min: f64,
        alpha: f64,
        warmup_steps: usize,
        oscillation_window: usize,
        oscillation_threshold: f64,
        oscillation_decay: f64,
        adaptive_r_min: bool,
        r_min_ema_alpha: f64,
    ) -> PyResult<Self> {
        let config = ScalrConfig::with_params(
            lr,
            momentum,
            weight_decay,
            r_min,
            alpha,
            warmup_steps,
            oscillation_window,
            oscillation_threshold,
            oscillation_decay,
            adaptive_r_min,
            r_min_ema_alpha,
        )
        .map_err(train_err_to_py)?;
        Ok(Self {
            inner: config.init::<BridgeBackend, 1>(),
        })
    }

    /// Apply one update to a 1-D `param` tensor given its gradient (`None`
    /// skips the update) and an optional Kuramoto order parameter. Returns
    /// the updated parameter.
    ///
    /// # Errors
    ///
    /// Raises `ValueError` on a shape mismatch between `param` and `grad`.
    #[pyo3(signature = (param, grad=None, order_parameter=None))]
    fn step(
        &mut self,
        py: Python<'_>,
        param: &Bound<'_, PyAny>,
        grad: Option<&Bound<'_, PyAny>>,
        order_parameter: Option<f64>,
    ) -> PyResult<Py<PyAny>> {
        let param_t = tensor_from_dlpack::<1>(param)?;
        let grad_t = grad.map(tensor_from_dlpack::<1>).transpose()?;
        let feedback = match order_parameter {
            Some(r) => StepFeedback::order(r),
            None => StepFeedback::none(),
        };
        let updated = self
            .inner
            .step(param_t, grad_t, &feedback)
            .map_err(train_err_to_py)?;
        export_tensor::<1>(py, updated.inner())
    }

    /// Serialize the optimizer's scalar/history state to JSON (see module
    /// docs for the momentum-buffer scope boundary).
    fn state_dict(&self) -> PyResult<String> {
        state_to_json(&self.inner.state_dict())
    }

    /// Restore state previously produced by [`Self::state_dict`].
    ///
    /// # Errors
    ///
    /// Raises `ValueError` on malformed JSON or invalid hyperparameters.
    fn load_state_dict(&mut self, json: &str) -> PyResult<()> {
        let state = state_from_json(json)?;
        self.inner.load_state_dict(state).map_err(train_err_to_py)
    }
}

// --- Rip -------------------------------------------------------------------

/// PyO3 bridge for [`Rip`] (Resonance-Induced Plasticity: a Hebbian
/// coupling-matrix update driven by phase coherence). Always rank-2 — see
/// module docs.
#[pyclass(name = "RipBridge", module = "prin._prin_core", unsendable)]
pub struct PyRipBridge {
    inner: Rip<BridgeBackend>,
    n_oscillators: usize,
}

#[pymethods]
impl PyRipBridge {
    /// Construct with PRINet 3.0's default hyperparameters unless
    /// overridden (see [`RipConfig::with_params`]).
    #[new]
    #[pyo3(signature = (n_oscillators, lr=0.01, target_amplitude=1.0))]
    fn new(n_oscillators: usize, lr: f64, target_amplitude: f64) -> PyResult<Self> {
        let config =
            RipConfig::with_params(n_oscillators, lr, target_amplitude).map_err(train_err_to_py)?;
        Ok(Self {
            inner: config.init::<BridgeBackend>(),
            n_oscillators,
        })
    }

    /// Number of oscillators the coupling matrix couples.
    #[getter]
    fn n_oscillators(&self) -> usize {
        self.n_oscillators
    }

    /// Apply one Hebbian(+optional gradient) update to the `[n, n]`
    /// `coupling` matrix, given an optional gradient and optional
    /// `(phase, amplitude)` feedback (each `[batch, n]`). Returns the
    /// updated coupling matrix.
    ///
    /// # Errors
    ///
    /// Raises `ValueError` on a shape mismatch.
    #[pyo3(signature = (coupling, grad=None, phase=None, amplitude=None))]
    fn step(
        &mut self,
        py: Python<'_>,
        coupling: &Bound<'_, PyAny>,
        grad: Option<&Bound<'_, PyAny>>,
        phase: Option<&Bound<'_, PyAny>>,
        amplitude: Option<&Bound<'_, PyAny>>,
    ) -> PyResult<Py<PyAny>> {
        let coupling_t = tensor_from_dlpack::<2>(coupling)?;
        let grad_t = grad.map(tensor_from_dlpack::<2>).transpose()?;
        let feedback = match (phase, amplitude) {
            (Some(p), Some(a)) => StepFeedback::phase_amplitude(
                tensor_from_dlpack::<2>(p)?,
                tensor_from_dlpack::<2>(a)?,
            ),
            (None, None) => StepFeedback::none(),
            _ => {
                return Err(PyValueError::new_err(
                    "phase and amplitude must be supplied together",
                ))
            }
        };
        let updated = self
            .inner
            .step(coupling_t, grad_t, &feedback)
            .map_err(train_err_to_py)?;
        export_tensor::<2>(py, updated.inner())
    }

    /// Serialize the optimizer's configuration to JSON. `Rip` holds no
    /// step-dependent state beyond its hyperparameters.
    fn state_dict(&self) -> PyResult<String> {
        state_to_json(&self.inner.state_dict())
    }

    /// Restore state previously produced by [`Self::state_dict`].
    ///
    /// # Errors
    ///
    /// Raises `ValueError` on malformed JSON or invalid hyperparameters.
    fn load_state_dict(&mut self, json: &str) -> PyResult<()> {
        let state = state_from_json(json)?;
        self.inner.load_state_dict(state).map_err(train_err_to_py)
    }
}

pub(crate) fn register(m: &Bound<'_, PyModule>) -> PyResult<()> {
    m.add_class::<PySyncGdBridge>()?;
    m.add_class::<PyScalrBridge>()?;
    m.add_class::<PyRipBridge>()?;
    Ok(())
}
