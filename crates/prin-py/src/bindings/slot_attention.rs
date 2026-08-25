//! PyO3 bridge for [`prin_train::slot_attention`] (Exec-WP-026 S1): the
//! non-oscillatory SlotAttention comparison baseline.
//!
//! **Per-call stochastic recompute hazard.** Unlike every other bridge in
//! this crate, [`prin_train::slot_attention::SlotAttentionModule::forward`]
//! and [`prin_train::slot_attention::TemporalSlotAttentionMOT::process_frame`]
//! draw fresh randomness from a caller-supplied `&mut Seed` on *every call*
//! (slot-initialization noise), not just once at construction. The
//! recompute-on-backward design (`train.rs`'s module docs) reruns the forward
//! pass inside `backward()` — if that recompute drew a *different* noise
//! realization than the original forward, the backward pass would silently
//! compute the gradient of the wrong function. [`prin_dynamics::Seed`] is
//! deterministic and `Clone` (its `Pcg64` state is captured exactly), so each
//! `*Ctx` snapshots a **clone of the `Seed` value as it stood immediately
//! before the original forward call** and re-clones that snapshot for every
//! `backward()` recompute — reproducing bit-identical noise, any number of
//! times, without consuming the caller's own `Seed` stream a second time.

use burn::module::Module;
use burn::tensor::Tensor;
use pyo3::exceptions::PyValueError;
use pyo3::prelude::*;
use pyo3::types::{PyBytes, PyList};

use prin_dynamics::Seed;
use prin_train::slot_attention::{
    SlotAttentionModule, SlotAttentionModuleConfig, TemporalSlotAttentionMOT,
    TemporalSlotAttentionMOTConfig,
};

use super::state::PySeed;
use super::train_support::{
    device, export_tensor, load_checkpoint_record, optional_tensor_from_dlpack_with_data,
    plain_tensor_from_dlpack, record_to_bytes, tensor_from_dlpack, tensor_from_dlpack_with_data,
    train_err_to_py, BridgeBackend,
};

fn leaf3(shape: &[usize], data: &[f64]) -> Tensor<BridgeBackend, 3> {
    Tensor::from_data(
        burn::tensor::TensorData::new(data.to_vec(), shape.to_vec()),
        &device(),
    )
    .require_grad()
}

// --- SlotAttentionModule bridge -------------------------------------------

/// Backward context for one [`PySlotAttentionModuleBridge::forward`] call.
#[pyclass(
    name = "SlotAttentionModuleCtx",
    module = "prin._prin_core",
    unsendable
)]
pub struct PySlotAttentionModuleCtx {
    module: SlotAttentionModule<BridgeBackend>,
    out_shape: [usize; 3],
    inputs_shape: Vec<usize>,
    inputs_data: Vec<f64>,
    seed_snapshot: Seed,
}

#[pymethods]
impl PySlotAttentionModuleCtx {
    /// Run the Rust backward pass, re-drawing the *same* slot-initialization
    /// noise as the saved forward call (see the module docs).
    ///
    /// # Errors
    ///
    /// Raises `ValueError` on a shape mismatch or missing gradient.
    fn backward(&self, py: Python<'_>, grad_output: &Bound<'_, PyAny>) -> PyResult<Py<PyAny>> {
        let grad_output = plain_tensor_from_dlpack::<3>(grad_output, self.out_shape)?;

        let inputs = leaf3(&self.inputs_shape, &self.inputs_data);
        let mut seed = self.seed_snapshot.clone();
        let output = self
            .module
            .forward(inputs.clone(), &mut seed)
            .expect("shape already validated by the saved forward call");

        let weighted = output * grad_output;
        let grads = weighted.sum().backward();

        let grad_inputs = inputs.grad(&grads).ok_or_else(|| {
            PyValueError::new_err("internal error: no gradient recorded for the bridge input")
        })?;
        export_tensor::<3>(py, grad_inputs)
    }
}

/// Slot Attention mechanism with iterative competitive binding, bridged to
/// `torch.autograd.Function` via DLPack.
///
/// Wraps [`prin_train::slot_attention::SlotAttentionModule`]; see the module
/// docs for the seed-snapshot recompute contract.
#[pyclass(
    name = "SlotAttentionModuleBridge",
    module = "prin._prin_core",
    unsendable
)]
pub struct PySlotAttentionModuleBridge {
    module: SlotAttentionModule<BridgeBackend>,
}

#[pymethods]
impl PySlotAttentionModuleBridge {
    /// Construct with seeded-random parameters (see
    /// [`SlotAttentionModuleConfig::init`]). `hidden_dim` defaults to
    /// `max(slot_dim, 128)`.
    ///
    /// # Errors
    ///
    /// Raises `ValueError` for invalid hyperparameters.
    #[new]
    #[pyo3(signature = (
        num_slots, slot_dim, input_dim, num_iterations=3, hidden_dim=None, eps=1e-8,
        seed_counter=0, seed_key=0,
    ))]
    #[allow(clippy::too_many_arguments)]
    fn new(
        num_slots: usize,
        slot_dim: usize,
        input_dim: usize,
        num_iterations: usize,
        hidden_dim: Option<usize>,
        eps: f64,
        seed_counter: u64,
        seed_key: u64,
    ) -> PyResult<Self> {
        let hidden_dim = hidden_dim.unwrap_or_else(|| slot_dim.max(128));
        let cfg = SlotAttentionModuleConfig::with_params(
            num_slots,
            slot_dim,
            input_dim,
            num_iterations,
            hidden_dim,
            eps,
        )
        .map_err(train_err_to_py)?;
        let mut seed = Seed::new(seed_counter as u128, seed_key as u128);
        let module = cfg.init::<BridgeBackend>(&device(), &mut seed);
        Ok(Self { module })
    }

    /// Number of slots.
    #[getter]
    fn num_slots(&self) -> usize {
        self.module.num_slots()
    }

    /// Slot dimensionality.
    #[getter]
    fn slot_dim(&self) -> usize {
        self.module.slot_dim()
    }

    /// Run Slot Attention. `inputs` is `[batch, n, input_dim]`; `seed` is
    /// consumed (advanced) for fresh slot-initialization noise. Returns
    /// `(output_capsule, ctx)`, `output` shaped `[batch, num_slots,
    /// slot_dim]`.
    ///
    /// # Errors
    ///
    /// Raises `ValueError` on a shape mismatch.
    fn forward(
        &self,
        py: Python<'_>,
        inputs: &Bound<'_, PyAny>,
        seed: &mut PySeed,
    ) -> PyResult<(Py<PyAny>, Py<PySlotAttentionModuleCtx>)> {
        let (inputs, inputs_shape, inputs_data) = tensor_from_dlpack_with_data::<3>(inputs)?;
        let seed_snapshot = seed.inner.clone();
        let mut consume_seed = seed.inner.clone();
        let output = self
            .module
            .forward(inputs, &mut consume_seed)
            .map_err(train_err_to_py)?;
        seed.inner = consume_seed;

        let out_shape = output.dims();
        let out_capsule = export_tensor::<3>(py, output.inner())?;
        let ctx = PySlotAttentionModuleCtx {
            module: self.module.clone(),
            out_shape,
            inputs_shape,
            inputs_data,
            seed_snapshot,
        };
        Ok((out_capsule, Py::new(py, ctx)?))
    }

    /// Serialize parameters to checkpoint bytes.
    fn state_dict<'py>(&self, py: Python<'py>) -> PyResult<Bound<'py, PyBytes>> {
        let bytes = record_to_bytes(&self.module)?;
        Ok(PyBytes::new(py, &bytes))
    }

    /// Restore parameters previously produced by [`Self::state_dict`],
    /// rejecting a shape mismatch and leaving `self` unchanged on failure.
    ///
    /// # Errors
    ///
    /// Raises `ValueError` if `bytes` does not decode to a record with this
    /// module's `num_slots`/`slot_dim`.
    fn load_state_dict(&mut self, bytes: &[u8]) -> PyResult<()> {
        let record = load_checkpoint_record::<SlotAttentionModule<BridgeBackend>>(bytes)?;
        let candidate = self.module.clone().load_record(record);
        candidate.validate_shapes().map_err(|e| {
            PyValueError::new_err(format!(
                "checkpoint shape mismatch: this module is configured for num_slots={}, \
                 slot_dim={} ({e})",
                self.module.num_slots(),
                self.module.slot_dim(),
            ))
        })?;
        self.module = candidate;
        Ok(())
    }
}

// --- TemporalSlotAttentionMOT bridge ---------------------------------------

/// Backward context for one
/// [`PyTemporalSlotAttentionMOTBridge::process_frame`] call.
#[pyclass(
    name = "TemporalSlotAttentionMOTProcessFrameCtx",
    module = "prin._prin_core",
    unsendable
)]
pub struct PyProcessFrameCtx {
    tracker: TemporalSlotAttentionMOT<BridgeBackend>,
    out_shape: [usize; 3],
    detections_shape: Vec<usize>,
    detections_data: Vec<f64>,
    prev_slots: Option<(Vec<usize>, Vec<f64>)>,
    seed_snapshot: Seed,
}

#[pymethods]
impl PyProcessFrameCtx {
    /// Run the Rust backward pass, re-drawing the same slot-initialization
    /// noise as the saved forward call. Returns `(grad_detections,
    /// grad_prev_slots)`; `grad_prev_slots` is `None` unless `prev_slots` was
    /// supplied to the saved call.
    ///
    /// # Errors
    ///
    /// Raises `ValueError` on a shape mismatch or missing gradient.
    fn backward(
        &self,
        py: Python<'_>,
        grad_output: &Bound<'_, PyAny>,
    ) -> PyResult<(Py<PyAny>, Option<Py<PyAny>>)> {
        let grad_output = plain_tensor_from_dlpack::<3>(grad_output, self.out_shape)?;

        let detections = Tensor::<BridgeBackend, 2>::from_data(
            burn::tensor::TensorData::new(
                self.detections_data.clone(),
                self.detections_shape.clone(),
            ),
            &device(),
        )
        .require_grad();
        let prev_leaf = self
            .prev_slots
            .as_ref()
            .map(|(shape, data)| leaf3(shape, data));

        let mut seed = self.seed_snapshot.clone();
        let output = self
            .tracker
            .process_frame(detections.clone(), prev_leaf.clone(), &mut seed)
            .expect("shape already validated by the saved forward call");

        let weighted = output * grad_output;
        let grads = weighted.sum().backward();

        let grad_detections = detections.grad(&grads).ok_or_else(|| {
            PyValueError::new_err("internal error: no gradient recorded for `detections`")
        })?;
        let grad_detections_capsule = export_tensor::<2>(py, grad_detections)?;

        let grad_prev_capsule = match prev_leaf {
            Some(p) => {
                let grad_prev = p.grad(&grads).ok_or_else(|| {
                    PyValueError::new_err("internal error: no gradient recorded for `prev_slots`")
                })?;
                Some(export_tensor::<3>(py, grad_prev)?)
            }
            None => None,
        };

        Ok((grad_detections_capsule, grad_prev_capsule))
    }
}

/// Backward context for one
/// [`PyTemporalSlotAttentionMOTBridge::slot_similarity`] call.
#[pyclass(
    name = "TemporalSlotAttentionMOTSimilarityCtx",
    module = "prin._prin_core",
    unsendable
)]
pub struct PySlotSimilarityCtx {
    tracker: TemporalSlotAttentionMOT<BridgeBackend>,
    out_shape: [usize; 2],
    a_shape: Vec<usize>,
    a_data: Vec<f64>,
    b_shape: Vec<usize>,
    b_data: Vec<f64>,
}

#[pymethods]
impl PySlotSimilarityCtx {
    /// Run the Rust backward pass. Returns `(d(loss)/d(slots_a),
    /// d(loss)/d(slots_b))`.
    ///
    /// # Errors
    ///
    /// Raises `ValueError` on a shape mismatch or missing gradient.
    fn backward(
        &self,
        py: Python<'_>,
        grad_output: &Bound<'_, PyAny>,
    ) -> PyResult<(Py<PyAny>, Py<PyAny>)> {
        let grad_output = plain_tensor_from_dlpack::<2>(grad_output, self.out_shape)?;

        let a = leaf3(&self.a_shape, &self.a_data);
        let b = leaf3(&self.b_shape, &self.b_data);
        let sim = self
            .tracker
            .slot_similarity(a.clone(), b.clone())
            .expect("shape already validated by the saved forward call");

        let grads = (sim * grad_output).sum().backward();

        let grad_a = a.grad(&grads).ok_or_else(|| {
            PyValueError::new_err("internal error: no gradient recorded for `slots_a`")
        })?;
        let grad_b = b.grad(&grads).ok_or_else(|| {
            PyValueError::new_err("internal error: no gradient recorded for `slots_b`")
        })?;
        Ok((
            export_tensor::<3>(py, grad_a)?,
            export_tensor::<3>(py, grad_b)?,
        ))
    }
}

/// Temporal Slot Attention for multi-frame object tracking — the direct
/// comparison baseline against `PhaseTracker`, bridged to Python.
#[pyclass(
    name = "TemporalSlotAttentionMOTBridge",
    module = "prin._prin_core",
    unsendable
)]
pub struct PyTemporalSlotAttentionMOTBridge {
    tracker: TemporalSlotAttentionMOT<BridgeBackend>,
}

impl PyTemporalSlotAttentionMOTBridge {
    /// Wrap an existing tracker without going through seeded construction.
    /// Used by `ablation.rs`'s `SlotAttentionFrozenBridge::inner` to expose a
    /// full bridge over a clone of its wrapped tracker.
    pub(crate) fn from_tracker(tracker: TemporalSlotAttentionMOT<BridgeBackend>) -> Self {
        Self { tracker }
    }

    pub(crate) fn tracker(&self) -> &TemporalSlotAttentionMOT<BridgeBackend> {
        &self.tracker
    }
}

#[pymethods]
impl PyTemporalSlotAttentionMOTBridge {
    /// Construct with seeded-random parameters (see
    /// [`TemporalSlotAttentionMOTConfig::init`]).
    ///
    /// # Errors
    ///
    /// Raises `ValueError` for invalid hyperparameters.
    #[new]
    #[pyo3(signature = (
        detection_dim, num_slots=8, slot_dim=64, num_iterations=3, match_threshold=0.3,
        seed_counter=0, seed_key=0,
    ))]
    #[allow(clippy::too_many_arguments)]
    fn new(
        detection_dim: usize,
        num_slots: usize,
        slot_dim: usize,
        num_iterations: usize,
        match_threshold: f64,
        seed_counter: u64,
        seed_key: u64,
    ) -> PyResult<Self> {
        let cfg = TemporalSlotAttentionMOTConfig::with_params(
            detection_dim,
            num_slots,
            slot_dim,
            num_iterations,
            match_threshold,
        )
        .map_err(train_err_to_py)?;
        let mut seed = Seed::new(seed_counter as u128, seed_key as u128);
        let tracker = cfg.init::<BridgeBackend>(&device(), &mut seed);
        Ok(Self { tracker })
    }

    /// Number of object slots.
    #[getter]
    fn num_slots(&self) -> usize {
        self.tracker.num_slots()
    }

    /// Slot dimensionality.
    #[getter]
    fn slot_dim(&self) -> usize {
        self.tracker.slot_dim()
    }

    /// Minimum similarity for a valid identity match.
    #[getter]
    fn match_threshold(&self) -> f64 {
        self.tracker.match_threshold()
    }

    /// Process one frame's detections, carrying `prev_slots` forward via GRU
    /// when supplied. `seed` is consumed (advanced) for fresh
    /// slot-initialization noise. Returns `(output_capsule, ctx)`, `output`
    /// shaped `[1, num_slots, slot_dim]`.
    ///
    /// # Errors
    ///
    /// Raises `ValueError` on a shape mismatch.
    #[pyo3(signature = (detections, seed, prev_slots=None))]
    fn process_frame(
        &self,
        py: Python<'_>,
        detections: &Bound<'_, PyAny>,
        seed: &mut PySeed,
        prev_slots: Option<&Bound<'_, PyAny>>,
    ) -> PyResult<(Py<PyAny>, Py<PyProcessFrameCtx>)> {
        let (detections, d_shape, d_data) = tensor_from_dlpack_with_data::<2>(detections)?;
        let prev_decoded = optional_tensor_from_dlpack_with_data::<3>(prev_slots)?;
        let (prev_tensor, prev_saved) = match prev_decoded {
            Some((t, shape, data)) => (Some(t), Some((shape, data))),
            None => (None, None),
        };

        let seed_snapshot = seed.inner.clone();
        let mut consume_seed = seed.inner.clone();
        let output = self
            .tracker
            .process_frame(detections, prev_tensor, &mut consume_seed)
            .map_err(train_err_to_py)?;
        seed.inner = consume_seed;

        let out_shape = output.dims();
        let out_capsule = export_tensor::<3>(py, output.inner())?;
        let ctx = PyProcessFrameCtx {
            tracker: self.tracker.clone(),
            out_shape,
            detections_shape: d_shape,
            detections_data: d_data,
            prev_slots: prev_saved,
            seed_snapshot,
        };
        Ok((out_capsule, Py::new(py, ctx)?))
    }

    /// Cosine similarity between two slot sets, each `[1, num_slots,
    /// slot_dim]`.
    ///
    /// # Errors
    ///
    /// Raises `ValueError` on a shape mismatch.
    fn slot_similarity(
        &self,
        py: Python<'_>,
        slots_a: &Bound<'_, PyAny>,
        slots_b: &Bound<'_, PyAny>,
    ) -> PyResult<(Py<PyAny>, Py<PySlotSimilarityCtx>)> {
        let (a, a_shape, a_data) = tensor_from_dlpack_with_data::<3>(slots_a)?;
        let (b, b_shape, b_data) = tensor_from_dlpack_with_data::<3>(slots_b)?;
        let sim = self
            .tracker
            .slot_similarity(a, b)
            .map_err(train_err_to_py)?;
        let out_shape = sim.dims();
        let capsule = export_tensor::<2>(py, sim.inner())?;
        let ctx = PySlotSimilarityCtx {
            tracker: self.tracker.clone(),
            out_shape,
            a_shape,
            a_data,
            b_shape,
            b_data,
        };
        Ok((capsule, Py::new(py, ctx)?))
    }

    /// Match detections across two consecutive frames. **Non-differentiable**
    /// (same contract as `PhaseTrackerBridge::match_frames`; see
    /// `phase_tracker.rs`'s module docs for the `forward` → `match_frames`
    /// rename rationale). `seed` is consumed (advanced).
    ///
    /// # Errors
    ///
    /// Raises `ValueError` on a shape mismatch.
    fn match_frames(
        &self,
        py: Python<'_>,
        detections_t: &Bound<'_, PyAny>,
        detections_t1: &Bound<'_, PyAny>,
        seed: &mut PySeed,
    ) -> PyResult<(Vec<i64>, Py<PyAny>)> {
        let detections_t = tensor_from_dlpack::<2>(detections_t)?;
        let detections_t1 = tensor_from_dlpack::<2>(detections_t1)?;
        let (matches, sim) = self
            .tracker
            .forward(detections_t, detections_t1, &mut seed.inner)
            .map_err(train_err_to_py)?;
        Ok((matches, export_tensor::<2>(py, sim.inner())?))
    }

    /// Track objects across a sequence of frames. **Non-differentiable**.
    /// `frame_detections` is a Python list of `[N_t, detection_dim]` DLPack
    /// tensors. `seed` is consumed (advanced). Returns `(slot_history:
    /// list[capsule], identity_matches, identity_preservation,
    /// per_frame_similarity)`.
    ///
    /// # Errors
    ///
    /// Raises `ValueError` on a shape mismatch in any frame.
    #[allow(clippy::type_complexity)]
    fn track_sequence(
        &self,
        py: Python<'_>,
        frame_detections: Vec<Py<PyAny>>,
        seed: &mut PySeed,
    ) -> PyResult<(Py<PyList>, Vec<Vec<i64>>, f64, Vec<f64>)> {
        let frames: Vec<Tensor<BridgeBackend, 2>> = frame_detections
            .into_iter()
            .map(|f| tensor_from_dlpack::<2>(f.bind(py)))
            .collect::<PyResult<Vec<_>>>()?;
        let (slot_history, identity_matches, identity_preservation, per_frame_similarity) = self
            .tracker
            .track_sequence(frames, &mut seed.inner)
            .map_err(train_err_to_py)?;
        let capsules: Vec<Py<PyAny>> = slot_history
            .into_iter()
            .map(|t| export_tensor::<3>(py, t.inner()))
            .collect::<PyResult<Vec<_>>>()?;
        let list = PyList::new(py, capsules)?.unbind();
        Ok((
            list,
            identity_matches,
            identity_preservation,
            per_frame_similarity,
        ))
    }

    /// Serialize parameters to checkpoint bytes.
    fn state_dict<'py>(&self, py: Python<'py>) -> PyResult<Bound<'py, PyBytes>> {
        let bytes = record_to_bytes(&self.tracker)?;
        Ok(PyBytes::new(py, &bytes))
    }

    /// Restore parameters previously produced by [`Self::state_dict`],
    /// rejecting a shape mismatch and leaving `self` unchanged on failure.
    ///
    /// # Errors
    ///
    /// Raises `ValueError` if `bytes` does not decode to a record with this
    /// tracker's `num_slots`/`slot_dim`.
    fn load_state_dict(&mut self, bytes: &[u8]) -> PyResult<()> {
        let record = load_checkpoint_record::<TemporalSlotAttentionMOT<BridgeBackend>>(bytes)?;
        let candidate = self.tracker.clone().load_record(record);
        candidate.validate_shapes().map_err(|e| {
            PyValueError::new_err(format!(
                "checkpoint shape mismatch: this tracker is configured for num_slots={}, \
                 slot_dim={} ({e})",
                self.tracker.num_slots(),
                self.tracker.slot_dim(),
            ))
        })?;
        self.tracker = candidate;
        Ok(())
    }
}

pub(crate) fn register(m: &Bound<'_, PyModule>) -> PyResult<()> {
    m.add_class::<PySlotAttentionModuleBridge>()?;
    m.add_class::<PySlotAttentionModuleCtx>()?;
    m.add_class::<PyTemporalSlotAttentionMOTBridge>()?;
    m.add_class::<PyProcessFrameCtx>()?;
    m.add_class::<PySlotSimilarityCtx>()?;
    Ok(())
}
