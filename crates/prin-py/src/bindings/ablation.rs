//! PyO3 bridges for [`prin_train::ablation`] (Exec-WP-026 S1): structural
//! ablation variants isolating which components drive temporal binding.
//!
//! [`PyPhaseTrackerFrozenBridge`] and [`PySlotAttentionFrozenBridge`] wrap an
//! inner tracker (`PhaseTrackerFrozen`/`SlotAttentionFrozen` both compose
//! rather than reimplement — see `prin_train::ablation`'s module docs) and
//! expose an `.inner` accessor returning a fresh
//! [`super::phase_tracker::PyPhaseTrackerBridge`] /
//! [`super::slot_attention::PyTemporalSlotAttentionMOTBridge`] over a *clone*
//! of the wrapped module — cheap (Burn `Module` parameters are `Rc`-shared)
//! and reuses every differentiable bridge method (`encode`/`evolve`/
//! `phase_similarity` / `process_frame`/`slot_similarity`) those types
//! already implement, rather than re-deriving them. [`PhaseTrackerStatic`]
//! and [`SlotAttentionNoGRU`] fully reimplement (do not wrap) their base
//! type in Rust, so their bridges implement their own differentiable methods
//! following the same pattern as `phase_tracker.rs`/`slot_attention.rs`.

use burn::module::Module;
use burn::tensor::Tensor;
use pyo3::exceptions::PyValueError;
use pyo3::prelude::*;
use pyo3::types::{PyBytes, PyList};

use prin_dynamics::Seed;
use prin_train::ablation::{
    PhaseTrackerFrozen, PhaseTrackerStatic, SlotAttentionFrozen, SlotAttentionNoGRU,
};
use prin_train::phase_tracker::PhaseTrackerConfig;
use prin_train::slot_attention::TemporalSlotAttentionMOTConfig;

use super::phase_tracker::{
    decode_frame_sequence, tracking_result_to_py, PyPhaseTrackerBridge, PyTrackingResult,
};
use super::slot_attention::PyTemporalSlotAttentionMOTBridge;
use super::state::PySeed;
use super::train_support::{
    device, export_tensor, load_checkpoint_record, plain_tensor_from_dlpack, record_to_bytes,
    tensor_from_dlpack, tensor_from_dlpack_with_data, train_err_to_py, BridgeBackend,
};

// =========================================================================
// PhaseTrackerFrozen
// =========================================================================

/// [`PhaseTrackerFrozen`], bridged to Python. Only `match_frames`/
/// `track_sequence` are exposed directly (mirroring the Rust type); use
/// [`Self::inner`] for the differentiable `encode`/`evolve`/
/// `phase_similarity` bridge (the detection encoder remains trainable — only
/// the dynamics submodule is frozen).
#[pyclass(
    name = "PhaseTrackerFrozenBridge",
    module = "prin._prin_core",
    unsendable
)]
pub struct PyPhaseTrackerFrozenBridge {
    tracker: PhaseTrackerFrozen<BridgeBackend>,
}

#[pymethods]
impl PyPhaseTrackerFrozenBridge {
    #[new]
    #[pyo3(signature = (detection_dim, n_delta=4, n_theta=8, n_gamma=16, n_discrete_steps=5, match_threshold=0.3, seed_counter=0, seed_key=0))]
    #[allow(clippy::too_many_arguments)]
    fn new(
        detection_dim: usize,
        n_delta: usize,
        n_theta: usize,
        n_gamma: usize,
        n_discrete_steps: usize,
        match_threshold: f64,
        seed_counter: u64,
        seed_key: u64,
    ) -> PyResult<Self> {
        let cfg = PhaseTrackerConfig::with_params(
            detection_dim,
            n_delta,
            n_theta,
            n_gamma,
            n_discrete_steps,
            match_threshold,
        )
        .map_err(train_err_to_py)?;
        let mut seed = Seed::new(seed_counter as u128, seed_key as u128);
        let tracker = PhaseTrackerFrozen::new(&cfg, &device(), &mut seed);
        Ok(Self { tracker })
    }

    /// A fresh [`PyPhaseTrackerBridge`] over a clone of the wrapped tracker
    /// (encoder trainable, dynamics frozen) — use for `encode`/`evolve`/
    /// `phase_similarity`.
    #[getter]
    fn inner(&self) -> PyPhaseTrackerBridge {
        PyPhaseTrackerBridge::from_tracker(self.tracker.inner().clone())
    }

    /// Match detections across two consecutive frames. **Non-differentiable**
    /// — see `phase_tracker.rs`'s module docs.
    ///
    /// # Errors
    ///
    /// Raises `ValueError` on a shape mismatch.
    fn match_frames(
        &self,
        py: Python<'_>,
        detections_t: &Bound<'_, PyAny>,
        detections_t1: &Bound<'_, PyAny>,
    ) -> PyResult<(Vec<i64>, Py<PyAny>)> {
        let detections_t = tensor_from_dlpack::<2>(detections_t)?;
        let detections_t1 = tensor_from_dlpack::<2>(detections_t1)?;
        let (matches, sim) = self
            .tracker
            .forward(detections_t, detections_t1)
            .map_err(train_err_to_py)?;
        Ok((matches, export_tensor::<2>(py, sim.inner())?))
    }

    /// Track objects across a sequence of frames. **Non-differentiable**.
    ///
    /// # Errors
    ///
    /// Raises `ValueError` on a shape mismatch in any frame.
    fn track_sequence(
        &self,
        py: Python<'_>,
        frame_detections: Vec<Py<PyAny>>,
    ) -> PyResult<PyTrackingResult> {
        let frames = decode_frame_sequence(py, frame_detections)?;
        let result = self
            .tracker
            .track_sequence(frames)
            .map_err(train_err_to_py)?;
        tracking_result_to_py(py, result)
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
    /// tracker's `n_osc`.
    fn load_state_dict(&mut self, bytes: &[u8]) -> PyResult<()> {
        let record = load_checkpoint_record::<PhaseTrackerFrozen<BridgeBackend>>(bytes)?;
        let candidate = self.tracker.clone().load_record(record);
        candidate.inner().validate_shapes().map_err(|e| {
            PyValueError::new_err(format!(
                "checkpoint shape mismatch: this tracker is configured for n_osc={} ({e})",
                self.tracker.inner().n_osc(),
            ))
        })?;
        self.tracker = candidate;
        Ok(())
    }
}

// =========================================================================
// PhaseTrackerStatic
// =========================================================================

fn leaf2(shape: &[usize], data: &[f64]) -> Tensor<BridgeBackend, 2> {
    Tensor::from_data(
        burn::tensor::TensorData::new(data.to_vec(), shape.to_vec()),
        &device(),
    )
    .require_grad()
}

/// Backward context for [`PyPhaseTrackerStaticBridge::encode`].
#[pyclass(
    name = "PhaseTrackerStaticEncodeCtx",
    module = "prin._prin_core",
    unsendable
)]
pub struct PyPhaseTrackerStaticEncodeCtx {
    tracker: PhaseTrackerStatic<BridgeBackend>,
    phase_shape: [usize; 2],
    amp_shape: [usize; 2],
    detections_shape: Vec<usize>,
    detections_data: Vec<f64>,
}

#[pymethods]
impl PyPhaseTrackerStaticEncodeCtx {
    fn backward(
        &self,
        py: Python<'_>,
        grad_phase: &Bound<'_, PyAny>,
        grad_amp: &Bound<'_, PyAny>,
    ) -> PyResult<Py<PyAny>> {
        let grad_phase = plain_tensor_from_dlpack::<2>(grad_phase, self.phase_shape)?;
        let grad_amp = plain_tensor_from_dlpack::<2>(grad_amp, self.amp_shape)?;
        let detections = leaf2(&self.detections_shape, &self.detections_data);
        let (phase, amp) = self
            .tracker
            .encode(detections.clone())
            .expect("shape already validated by the saved forward call");
        let grads = ((phase * grad_phase).sum() + (amp * grad_amp).sum()).backward();
        let grad_detections = detections.grad(&grads).ok_or_else(|| {
            PyValueError::new_err("internal error: no gradient recorded for the bridge input")
        })?;
        export_tensor::<2>(py, grad_detections)
    }
}

/// Backward context for [`PyPhaseTrackerStaticBridge::evolve`].
#[pyclass(
    name = "PhaseTrackerStaticEvolveCtx",
    module = "prin._prin_core",
    unsendable
)]
pub struct PyPhaseTrackerStaticEvolveCtx {
    tracker: PhaseTrackerStatic<BridgeBackend>,
    out_phase_shape: [usize; 2],
    out_amp_shape: [usize; 2],
    phase_shape: Vec<usize>,
    phase_data: Vec<f64>,
    amp_shape: Vec<usize>,
    amp_data: Vec<f64>,
}

#[pymethods]
impl PyPhaseTrackerStaticEvolveCtx {
    fn backward(
        &self,
        py: Python<'_>,
        grad_phase_out: &Bound<'_, PyAny>,
        grad_amp_out: &Bound<'_, PyAny>,
    ) -> PyResult<(Py<PyAny>, Py<PyAny>)> {
        let grad_phase_out = plain_tensor_from_dlpack::<2>(grad_phase_out, self.out_phase_shape)?;
        let grad_amp_out = plain_tensor_from_dlpack::<2>(grad_amp_out, self.out_amp_shape)?;
        let phase = leaf2(&self.phase_shape, &self.phase_data);
        let amp = leaf2(&self.amp_shape, &self.amp_data);
        // `PhaseTrackerStatic::evolve` is infallible (no dynamics module to
        // shape-check against — see `prin_train::ablation`'s module docs).
        let (phase_out, amp_out) = self.tracker.evolve(phase.clone(), amp.clone());
        let grads =
            ((phase_out * grad_phase_out).sum() + (amp_out * grad_amp_out).sum()).backward();
        let grad_phase = phase.grad(&grads).ok_or_else(|| {
            PyValueError::new_err("internal error: no gradient recorded for `phase`")
        })?;
        let grad_amp = amp.grad(&grads).ok_or_else(|| {
            PyValueError::new_err("internal error: no gradient recorded for `amplitude`")
        })?;
        Ok((
            export_tensor::<2>(py, grad_phase)?,
            export_tensor::<2>(py, grad_amp)?,
        ))
    }
}

/// Backward context for [`PyPhaseTrackerStaticBridge::phase_similarity`].
#[pyclass(
    name = "PhaseTrackerStaticSimilarityCtx",
    module = "prin._prin_core",
    unsendable
)]
pub struct PyPhaseTrackerStaticSimilarityCtx {
    tracker: PhaseTrackerStatic<BridgeBackend>,
    out_shape: [usize; 2],
    a_shape: Vec<usize>,
    a_data: Vec<f64>,
    b_shape: Vec<usize>,
    b_data: Vec<f64>,
}

#[pymethods]
impl PyPhaseTrackerStaticSimilarityCtx {
    fn backward(
        &self,
        py: Python<'_>,
        grad_output: &Bound<'_, PyAny>,
    ) -> PyResult<(Py<PyAny>, Py<PyAny>)> {
        let grad_output = plain_tensor_from_dlpack::<2>(grad_output, self.out_shape)?;
        let phase_a = leaf2(&self.a_shape, &self.a_data);
        let phase_b = leaf2(&self.b_shape, &self.b_data);
        let sim = self
            .tracker
            .phase_similarity(phase_a.clone(), phase_b.clone())
            .expect("shape already validated by the saved forward call");
        let grads = (sim * grad_output).sum().backward();
        let grad_a = phase_a.grad(&grads).ok_or_else(|| {
            PyValueError::new_err("internal error: no gradient recorded for `phase_a`")
        })?;
        let grad_b = phase_b.grad(&grads).ok_or_else(|| {
            PyValueError::new_err("internal error: no gradient recorded for `phase_b`")
        })?;
        Ok((
            export_tensor::<2>(py, grad_a)?,
            export_tensor::<2>(py, grad_b)?,
        ))
    }
}

/// [`PhaseTrackerStatic`] (PT-static): no coupling, independent
/// fixed-frequency phase advance. Fully reimplements (does not wrap)
/// `PhaseTracker` — see `prin_train::ablation`'s module docs.
#[pyclass(
    name = "PhaseTrackerStaticBridge",
    module = "prin._prin_core",
    unsendable
)]
pub struct PyPhaseTrackerStaticBridge {
    tracker: PhaseTrackerStatic<BridgeBackend>,
}

#[pymethods]
impl PyPhaseTrackerStaticBridge {
    #[new]
    #[pyo3(signature = (detection_dim, n_delta=4, n_theta=8, n_gamma=16, n_discrete_steps=5, match_threshold=0.3, seed_counter=0, seed_key=0))]
    #[allow(clippy::too_many_arguments)]
    fn new(
        detection_dim: usize,
        n_delta: usize,
        n_theta: usize,
        n_gamma: usize,
        n_discrete_steps: usize,
        match_threshold: f64,
        seed_counter: u64,
        seed_key: u64,
    ) -> PyResult<Self> {
        let cfg = PhaseTrackerConfig::with_params(
            detection_dim,
            n_delta,
            n_theta,
            n_gamma,
            n_discrete_steps,
            match_threshold,
        )
        .map_err(train_err_to_py)?;
        let mut seed = Seed::new(seed_counter as u128, seed_key as u128);
        let tracker = PhaseTrackerStatic::new(&cfg, &device(), &mut seed);
        Ok(Self { tracker })
    }

    /// Total oscillator count.
    #[getter]
    fn n_osc(&self) -> usize {
        self.tracker.n_osc()
    }

    /// Encode detections into `(phase, amplitude)`.
    ///
    /// # Errors
    ///
    /// Raises `ValueError` on a shape mismatch.
    fn encode(
        &self,
        py: Python<'_>,
        detections: &Bound<'_, PyAny>,
    ) -> PyResult<(Py<PyAny>, Py<PyAny>, Py<PyPhaseTrackerStaticEncodeCtx>)> {
        let (detections, d_shape, d_data) = tensor_from_dlpack_with_data::<2>(detections)?;
        let (phase, amp) = self.tracker.encode(detections).map_err(train_err_to_py)?;
        let phase_shape = phase.dims();
        let amp_shape = amp.dims();
        let phase_capsule = export_tensor::<2>(py, phase.inner())?;
        let amp_capsule = export_tensor::<2>(py, amp.inner())?;
        let ctx = PyPhaseTrackerStaticEncodeCtx {
            tracker: self.tracker.clone(),
            phase_shape,
            amp_shape,
            detections_shape: d_shape,
            detections_data: d_data,
        };
        Ok((phase_capsule, amp_capsule, Py::new(py, ctx)?))
    }

    /// Advance `phase` by fixed per-band frequencies (no coupling);
    /// `amplitude` passes through unchanged.
    fn evolve(
        &self,
        py: Python<'_>,
        phase: &Bound<'_, PyAny>,
        amplitude: &Bound<'_, PyAny>,
    ) -> PyResult<(Py<PyAny>, Py<PyAny>, Py<PyPhaseTrackerStaticEvolveCtx>)> {
        let (phase, phase_shape, phase_data) = tensor_from_dlpack_with_data::<2>(phase)?;
        let (amp, amp_shape, amp_data) = tensor_from_dlpack_with_data::<2>(amplitude)?;
        let (phase_out, amp_out) = self.tracker.evolve(phase, amp);
        let out_phase_shape = phase_out.dims();
        let out_amp_shape = amp_out.dims();
        let phase_capsule = export_tensor::<2>(py, phase_out.inner())?;
        let amp_capsule = export_tensor::<2>(py, amp_out.inner())?;
        let ctx = PyPhaseTrackerStaticEvolveCtx {
            tracker: self.tracker.clone(),
            out_phase_shape,
            out_amp_shape,
            phase_shape,
            phase_data,
            amp_shape,
            amp_data,
        };
        Ok((phase_capsule, amp_capsule, Py::new(py, ctx)?))
    }

    /// Phase-coherence similarity, identical formula to `PhaseTracker`.
    ///
    /// # Errors
    ///
    /// Raises `ValueError` on a shape mismatch.
    fn phase_similarity(
        &self,
        py: Python<'_>,
        phase_a: &Bound<'_, PyAny>,
        phase_b: &Bound<'_, PyAny>,
    ) -> PyResult<(Py<PyAny>, Py<PyPhaseTrackerStaticSimilarityCtx>)> {
        let (phase_a, a_shape, a_data) = tensor_from_dlpack_with_data::<2>(phase_a)?;
        let (phase_b, b_shape, b_data) = tensor_from_dlpack_with_data::<2>(phase_b)?;
        let sim = self
            .tracker
            .phase_similarity(phase_a, phase_b)
            .map_err(train_err_to_py)?;
        let out_shape = sim.dims();
        let capsule = export_tensor::<2>(py, sim.inner())?;
        let ctx = PyPhaseTrackerStaticSimilarityCtx {
            tracker: self.tracker.clone(),
            out_shape,
            a_shape,
            a_data,
            b_shape,
            b_data,
        };
        Ok((capsule, Py::new(py, ctx)?))
    }

    /// Match detections across two consecutive frames. **Non-differentiable**.
    ///
    /// # Errors
    ///
    /// Raises `ValueError` on a shape mismatch.
    fn match_frames(
        &self,
        py: Python<'_>,
        detections_t: &Bound<'_, PyAny>,
        detections_t1: &Bound<'_, PyAny>,
    ) -> PyResult<(Vec<i64>, Py<PyAny>)> {
        let detections_t = tensor_from_dlpack::<2>(detections_t)?;
        let detections_t1 = tensor_from_dlpack::<2>(detections_t1)?;
        let (matches, sim) = self
            .tracker
            .forward(detections_t, detections_t1)
            .map_err(train_err_to_py)?;
        Ok((matches, export_tensor::<2>(py, sim.inner())?))
    }

    /// Track objects across a sequence of frames. **Non-differentiable**.
    /// `per_frame_phase_correlation` is always empty, matching the reference
    /// (see `prin_train::ablation`'s module docs).
    ///
    /// # Errors
    ///
    /// Raises `ValueError` on a shape mismatch in any frame.
    fn track_sequence(
        &self,
        py: Python<'_>,
        frame_detections: Vec<Py<PyAny>>,
    ) -> PyResult<PyTrackingResult> {
        let frames = decode_frame_sequence(py, frame_detections)?;
        let result = self
            .tracker
            .track_sequence(frames)
            .map_err(train_err_to_py)?;
        tracking_result_to_py(py, result)
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
    /// tracker's `n_osc`.
    fn load_state_dict(&mut self, bytes: &[u8]) -> PyResult<()> {
        let record = load_checkpoint_record::<PhaseTrackerStatic<BridgeBackend>>(bytes)?;
        let candidate = self.tracker.clone().load_record(record);
        candidate.validate_shapes().map_err(|e| {
            PyValueError::new_err(format!(
                "checkpoint shape mismatch: this tracker is configured for n_osc={} ({e})",
                self.tracker.n_osc(),
            ))
        })?;
        self.tracker = candidate;
        Ok(())
    }
}

// =========================================================================
// SlotAttentionNoGRU
// =========================================================================

fn leaf3(shape: &[usize], data: &[f64]) -> Tensor<BridgeBackend, 3> {
    Tensor::from_data(
        burn::tensor::TensorData::new(data.to_vec(), shape.to_vec()),
        &device(),
    )
    .require_grad()
}

/// Backward context for [`PySlotAttentionNoGRUBridge::process_frame`].
#[pyclass(
    name = "SlotAttentionNoGRUProcessFrameCtx",
    module = "prin._prin_core",
    unsendable
)]
pub struct PySlotAttentionNoGRUProcessFrameCtx {
    tracker: SlotAttentionNoGRU<BridgeBackend>,
    out_shape: [usize; 3],
    detections_shape: Vec<usize>,
    detections_data: Vec<f64>,
    seed_snapshot: Seed,
}

#[pymethods]
impl PySlotAttentionNoGRUProcessFrameCtx {
    fn backward(&self, py: Python<'_>, grad_output: &Bound<'_, PyAny>) -> PyResult<Py<PyAny>> {
        let grad_output = plain_tensor_from_dlpack::<3>(grad_output, self.out_shape)?;
        let detections = leaf2(&self.detections_shape, &self.detections_data);
        let mut seed = self.seed_snapshot.clone();
        let output = self
            .tracker
            .process_frame(detections.clone(), &mut seed)
            .expect("shape already validated by the saved forward call");
        let grads = (output * grad_output).sum().backward();
        let grad_detections = detections.grad(&grads).ok_or_else(|| {
            PyValueError::new_err("internal error: no gradient recorded for the bridge input")
        })?;
        export_tensor::<2>(py, grad_detections)
    }
}

/// Backward context for [`PySlotAttentionNoGRUBridge::slot_similarity`].
#[pyclass(
    name = "SlotAttentionNoGRUSimilarityCtx",
    module = "prin._prin_core",
    unsendable
)]
pub struct PySlotAttentionNoGRUSimilarityCtx {
    tracker: SlotAttentionNoGRU<BridgeBackend>,
    out_shape: [usize; 2],
    a_shape: Vec<usize>,
    a_data: Vec<f64>,
    b_shape: Vec<usize>,
    b_data: Vec<f64>,
}

#[pymethods]
impl PySlotAttentionNoGRUSimilarityCtx {
    fn backward(
        &self,
        py: Python<'_>,
        grad_output: &Bound<'_, PyAny>,
    ) -> PyResult<(Py<PyAny>, Py<PyAny>)> {
        let grad_output = plain_tensor_from_dlpack::<2>(grad_output, self.out_shape)?;
        let a = leaf3(&self.a_shape, &self.a_data);
        let b = leaf3(&self.b_shape, &self.b_data);
        let sim = self.tracker.slot_similarity(a.clone(), b.clone());
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

/// [`SlotAttentionNoGRU`] (SA-no-GRU): slots re-initialize from scratch every
/// frame, no temporal carry-over.
#[pyclass(
    name = "SlotAttentionNoGRUBridge",
    module = "prin._prin_core",
    unsendable
)]
pub struct PySlotAttentionNoGRUBridge {
    tracker: SlotAttentionNoGRU<BridgeBackend>,
}

#[pymethods]
impl PySlotAttentionNoGRUBridge {
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
        let tracker = SlotAttentionNoGRU::new(&cfg, &device(), &mut seed);
        Ok(Self { tracker })
    }

    /// Process a frame, always ignoring any prior state (fresh slots every
    /// call — the ablated behavior). `seed` is consumed (advanced). See
    /// `slot_attention.rs`'s module docs for the seed-snapshot recompute
    /// contract.
    ///
    /// # Errors
    ///
    /// Raises `ValueError` on a shape mismatch.
    fn process_frame(
        &self,
        py: Python<'_>,
        detections: &Bound<'_, PyAny>,
        seed: &mut PySeed,
    ) -> PyResult<(Py<PyAny>, Py<PySlotAttentionNoGRUProcessFrameCtx>)> {
        let (detections, d_shape, d_data) = tensor_from_dlpack_with_data::<2>(detections)?;
        let seed_snapshot = seed.inner.clone();
        let mut consume_seed = seed.inner.clone();
        let output = self
            .tracker
            .process_frame(detections, &mut consume_seed)
            .map_err(train_err_to_py)?;
        seed.inner = consume_seed;

        let out_shape = output.dims();
        let out_capsule = export_tensor::<3>(py, output.inner())?;
        let ctx = PySlotAttentionNoGRUProcessFrameCtx {
            tracker: self.tracker.clone(),
            out_shape,
            detections_shape: d_shape,
            detections_data: d_data,
            seed_snapshot,
        };
        Ok((out_capsule, Py::new(py, ctx)?))
    }

    /// Cosine similarity between two `[1, k, d]` slot sets.
    ///
    /// # Errors
    ///
    /// Raises `ValueError` on a shape mismatch.
    fn slot_similarity(
        &self,
        py: Python<'_>,
        slots_a: &Bound<'_, PyAny>,
        slots_b: &Bound<'_, PyAny>,
    ) -> PyResult<(Py<PyAny>, Py<PySlotAttentionNoGRUSimilarityCtx>)> {
        let (a, a_shape, a_data) = tensor_from_dlpack_with_data::<3>(slots_a)?;
        let (b, b_shape, b_data) = tensor_from_dlpack_with_data::<3>(slots_b)?;
        let sim = self.tracker.slot_similarity(a, b);
        let out_shape = sim.dims();
        let capsule = export_tensor::<2>(py, sim.inner())?;
        let ctx = PySlotAttentionNoGRUSimilarityCtx {
            tracker: self.tracker.clone(),
            out_shape,
            a_shape,
            a_data,
            b_shape,
            b_data,
        };
        Ok((capsule, Py::new(py, ctx)?))
    }

    /// Match detections across two consecutive frames. **Non-differentiable**.
    /// `seed` is consumed (advanced).
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

    /// Track a sequence of frames with independent (no-carry-over) slots per
    /// frame. **Non-differentiable**. `seed` is consumed (advanced). Returns
    /// `(slot_history: list[capsule], identity_matches,
    /// identity_preservation, per_frame_similarity)`.
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
    /// tracker's parameter shapes.
    fn load_state_dict(&mut self, bytes: &[u8]) -> PyResult<()> {
        let record = load_checkpoint_record::<SlotAttentionNoGRU<BridgeBackend>>(bytes)?;
        let candidate = self.tracker.clone().load_record(record);
        candidate
            .validate_shapes()
            .map_err(|e| PyValueError::new_err(format!("checkpoint shape mismatch: {e}")))?;
        self.tracker = candidate;
        Ok(())
    }
}

// =========================================================================
// SlotAttentionFrozen
// =========================================================================

/// [`SlotAttentionFrozen`], bridged to Python: every parameter frozen (the
/// untrained SA baseline paired with [`PyPhaseTrackerFrozenBridge`]). Only
/// `match_frames`/`track_sequence` are exposed directly (mirroring the Rust
/// type); use [`Self::inner`] for the (parameter-free-gradient, but still
/// numerically well-defined) `process_frame`/`slot_similarity` bridge.
#[pyclass(
    name = "SlotAttentionFrozenBridge",
    module = "prin._prin_core",
    unsendable
)]
pub struct PySlotAttentionFrozenBridge {
    tracker: SlotAttentionFrozen<BridgeBackend>,
}

#[pymethods]
impl PySlotAttentionFrozenBridge {
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
        let tracker = SlotAttentionFrozen::new(&cfg, &device(), &mut seed);
        Ok(Self { tracker })
    }

    /// A fresh [`PyTemporalSlotAttentionMOTBridge`] over a clone of the
    /// wrapped, fully-frozen tracker — use for `process_frame`/
    /// `slot_similarity`.
    #[getter]
    fn inner(&self) -> PyTemporalSlotAttentionMOTBridge {
        PyTemporalSlotAttentionMOTBridge::from_tracker(self.tracker.inner().clone())
    }

    /// Match detections across two consecutive frames. **Non-differentiable**.
    /// `seed` is consumed (advanced).
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
    /// `seed` is consumed (advanced).
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
    /// tracker's parameter shapes.
    fn load_state_dict(&mut self, bytes: &[u8]) -> PyResult<()> {
        let record = load_checkpoint_record::<SlotAttentionFrozen<BridgeBackend>>(bytes)?;
        let candidate = self.tracker.clone().load_record(record);
        candidate
            .inner()
            .validate_shapes()
            .map_err(|e| PyValueError::new_err(format!("checkpoint shape mismatch: {e}")))?;
        self.tracker = candidate;
        Ok(())
    }
}

pub(crate) fn register(m: &Bound<'_, PyModule>) -> PyResult<()> {
    m.add_class::<PyPhaseTrackerFrozenBridge>()?;
    m.add_class::<PyPhaseTrackerStaticBridge>()?;
    m.add_class::<PyPhaseTrackerStaticEncodeCtx>()?;
    m.add_class::<PyPhaseTrackerStaticEvolveCtx>()?;
    m.add_class::<PyPhaseTrackerStaticSimilarityCtx>()?;
    m.add_class::<PySlotAttentionNoGRUBridge>()?;
    m.add_class::<PySlotAttentionNoGRUProcessFrameCtx>()?;
    m.add_class::<PySlotAttentionNoGRUSimilarityCtx>()?;
    m.add_class::<PySlotAttentionFrozenBridge>()?;
    Ok(())
}
