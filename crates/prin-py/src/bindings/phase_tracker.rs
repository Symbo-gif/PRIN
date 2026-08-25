//! PyO3 bridge for [`prin_train::phase_tracker::PhaseTracker`]
//! (Exec-WP-026 S1).
//!
//! `encode`/`evolve`/`phase_similarity` are genuinely differentiable
//! "trainable ops" (Coding Standards §3.2) and get full
//! `torch.autograd.Function` bridges (multi-output vector-Jacobian-product,
//! generalizing `train.rs`'s single-output recompute-on-backward pattern —
//! for `N` outputs `y_1..y_N` paired with cotangents `g_1..g_N`, the
//! backward pass seeds `sum_i (y_i * g_i).sum()).backward()`, which is the
//! standard multi-output VJP). `match_frames` (`PhaseTracker::forward`,
//! renamed — see below) and `track_sequence` are bridged as plain,
//! non-differentiable methods: their `matches: Vec<i64>` output is host-side
//! greedy-assignment bookkeeping with no gradient, exactly as documented in
//! `prin_train::phase_tracker`'s own module docs ("non-differentiable
//! host-side bookkeeping, identical in kind to PRINet 3.0's
//! `.item()`-per-element Python loop").
//!
//! **`forward` → `match_frames` rename.** The Rust method is named `forward`
//! by PRINet 3.0 convention, but a non-differentiable method named `forward`
//! on a Python `torch.nn.Module` would collide with `nn.Module.__call__`'s
//! autograd-tracking expectations and mislead callers. Bridged here as
//! `match_frames`, a deliberate, documented Python-API adaptation (not a
//! dropped symbol) — `python/prin/nn`'s `PhaseTracker` wrapper is a plain
//! `torch.nn.Module` whose own `.forward` is not defined; callers use
//! `.encode`/`.evolve`/`.phase_similarity` (differentiable) and
//! `.match_frames`/`.track_sequence` (evaluation utilities) directly.

use burn::module::Module;
use burn::tensor::Tensor;
use pyo3::exceptions::PyValueError;
use pyo3::prelude::*;
use pyo3::types::PyBytes;

use prin_dynamics::Seed;
use prin_train::phase_tracker::{PhaseTracker, PhaseTrackerConfig};

use super::train_support::{
    device, export_tensor, load_checkpoint_record, plain_tensor_from_dlpack, record_to_bytes,
    tensor_from_dlpack, tensor_from_dlpack_with_data, train_err_to_py, BridgeBackend,
};

fn leaf2(shape: &[usize], data: &[f64]) -> Tensor<BridgeBackend, 2> {
    Tensor::from_data(
        burn::tensor::TensorData::new(data.to_vec(), shape.to_vec()),
        &device(),
    )
    .require_grad()
}

// --- encode ------------------------------------------------------------

/// Backward context for [`PyPhaseTrackerBridge::encode`].
#[pyclass(name = "PhaseTrackerEncodeCtx", module = "prin._prin_core", unsendable)]
pub struct PyPhaseTrackerEncodeCtx {
    tracker: PhaseTracker<BridgeBackend>,
    phase_shape: [usize; 2],
    amp_shape: [usize; 2],
    detections_shape: Vec<usize>,
    detections_data: Vec<f64>,
}

#[pymethods]
impl PyPhaseTrackerEncodeCtx {
    /// Run the Rust backward pass. Returns `d(loss)/d(detections)`.
    ///
    /// # Errors
    ///
    /// Raises `ValueError` on a shape mismatch or missing gradient (see
    /// `train.rs`'s `ResonanceLayerCtx::backward`).
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

        let weighted = (phase * grad_phase).sum() + (amp * grad_amp).sum();
        let grads = weighted.backward();

        let grad_detections = detections.grad(&grads).ok_or_else(|| {
            PyValueError::new_err("internal error: no gradient recorded for the bridge input")
        })?;
        export_tensor::<2>(py, grad_detections)
    }
}

// --- evolve --------------------------------------------------------------

/// Backward context for [`PyPhaseTrackerBridge::evolve`].
#[pyclass(name = "PhaseTrackerEvolveCtx", module = "prin._prin_core", unsendable)]
pub struct PyPhaseTrackerEvolveCtx {
    tracker: PhaseTracker<BridgeBackend>,
    out_phase_shape: [usize; 2],
    out_amp_shape: [usize; 2],
    phase_shape: Vec<usize>,
    phase_data: Vec<f64>,
    amp_shape: Vec<usize>,
    amp_data: Vec<f64>,
}

#[pymethods]
impl PyPhaseTrackerEvolveCtx {
    /// Run the Rust backward pass. Returns `(d(loss)/d(phase),
    /// d(loss)/d(amplitude))`.
    ///
    /// # Errors
    ///
    /// See [`PyPhaseTrackerEncodeCtx::backward`].
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
        let (phase_out, amp_out) = self
            .tracker
            .evolve(phase.clone(), amp.clone())
            .expect("shape already validated by the saved forward call");

        let weighted = (phase_out * grad_phase_out).sum() + (amp_out * grad_amp_out).sum();
        let grads = weighted.backward();

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

// --- phase_similarity ------------------------------------------------------

/// Backward context for [`PyPhaseTrackerBridge::phase_similarity`].
#[pyclass(
    name = "PhaseTrackerSimilarityCtx",
    module = "prin._prin_core",
    unsendable
)]
pub struct PyPhaseTrackerSimilarityCtx {
    tracker: PhaseTracker<BridgeBackend>,
    out_shape: [usize; 2],
    a_shape: Vec<usize>,
    a_data: Vec<f64>,
    b_shape: Vec<usize>,
    b_data: Vec<f64>,
}

#[pymethods]
impl PyPhaseTrackerSimilarityCtx {
    /// Run the Rust backward pass. Returns `(d(loss)/d(phase_a),
    /// d(loss)/d(phase_b))`.
    ///
    /// # Errors
    ///
    /// See [`PyPhaseTrackerEncodeCtx::backward`].
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

// --- TrackingResult ----------------------------------------------------

/// Python-facing mirror of [`prin_train::phase_tracker::TrackingResult`].
///
/// A plain, non-differentiable data holder — `phase_history` capsules are
/// detached (no gradient graph); see the module docs for why `track_sequence`
/// is not a `torch.autograd.Function`.
#[pyclass(name = "TrackingResult", module = "prin._prin_core", get_all)]
pub struct PyTrackingResult {
    /// Per-frame phase tensors (DLPack capsules), one per input frame.
    phase_history: Vec<Py<PyAny>>,
    /// Per-transition match indices (frame `t` → frame `t+1`), `-1` if
    /// unmatched.
    identity_matches: Vec<Vec<i64>>,
    /// Fraction of matchable detections successfully matched, in `[0, 1]`.
    identity_preservation: f64,
    /// Per-transition mean best-match similarity.
    per_frame_similarity: Vec<f64>,
    /// Per-transition mean circular phase correlation.
    per_frame_phase_correlation: Vec<f64>,
}

/// Convert a Rust [`prin_train::phase_tracker::TrackingResult`] into its
/// Python mirror, exporting each phase-history tensor as a fresh DLPack
/// capsule.
pub(crate) fn tracking_result_to_py(
    py: Python<'_>,
    result: prin_train::phase_tracker::TrackingResult<BridgeBackend>,
) -> PyResult<PyTrackingResult> {
    let phase_history = result
        .phase_history
        .into_iter()
        .map(|t| export_tensor::<2>(py, t.inner()))
        .collect::<PyResult<Vec<_>>>()?;
    Ok(PyTrackingResult {
        phase_history,
        identity_matches: result.identity_matches,
        identity_preservation: result.identity_preservation,
        per_frame_similarity: result.per_frame_similarity,
        per_frame_phase_correlation: result.per_frame_phase_correlation,
    })
}

/// Decode a Python list of DLPack tensors into `Vec<Tensor<BridgeBackend, 2>>`
/// (non-differentiable input — used only by `track_sequence`).
pub(crate) fn decode_frame_sequence(
    py: Python<'_>,
    frames: Vec<Py<PyAny>>,
) -> PyResult<Vec<Tensor<BridgeBackend, 2>>> {
    frames
        .into_iter()
        .map(|f| tensor_from_dlpack::<2>(f.bind(py)))
        .collect()
}

// --- PhaseTracker bridge -------------------------------------------------

/// Phase-based multi-object tracker, bridged to Python (PRIN's primary
/// contribution). See the module docs for the differentiable/non-
/// differentiable method split.
#[pyclass(name = "PhaseTrackerBridge", module = "prin._prin_core", unsendable)]
pub struct PyPhaseTrackerBridge {
    tracker: PhaseTracker<BridgeBackend>,
}

impl PyPhaseTrackerBridge {
    /// Wrap an existing tracker without going through seeded construction.
    /// Used by `ablation.rs`'s `PhaseTrackerFrozenBridge::inner` to expose a
    /// full differentiable bridge over a clone of its wrapped tracker.
    pub(crate) fn from_tracker(tracker: PhaseTracker<BridgeBackend>) -> Self {
        Self { tracker }
    }

    pub(crate) fn tracker(&self) -> &PhaseTracker<BridgeBackend> {
        &self.tracker
    }
}

#[pymethods]
impl PyPhaseTrackerBridge {
    /// Construct with seeded-random parameters (see
    /// [`PhaseTrackerConfig::init`]).
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
        let tracker = cfg.init::<BridgeBackend>(&device(), &mut seed);
        Ok(Self { tracker })
    }

    /// Total oscillator count across all three bands.
    #[getter]
    fn n_osc(&self) -> usize {
        self.tracker.n_osc()
    }

    /// Minimum phase similarity for a valid match.
    #[getter]
    fn match_threshold(&self) -> f64 {
        self.tracker.match_threshold()
    }

    /// Encode detections into `(phase, amplitude)` oscillator embeddings.
    /// `detections` is `[N, detection_dim]`; each output is `[N, n_osc]`.
    ///
    /// # Errors
    ///
    /// Raises `ValueError` on a shape mismatch.
    fn encode(
        &self,
        py: Python<'_>,
        detections: &Bound<'_, PyAny>,
    ) -> PyResult<(Py<PyAny>, Py<PyAny>, Py<PyPhaseTrackerEncodeCtx>)> {
        let (detections, d_shape, d_data) = tensor_from_dlpack_with_data::<2>(detections)?;
        let (phase, amp) = self.tracker.encode(detections).map_err(train_err_to_py)?;
        let phase_shape = phase.dims();
        let amp_shape = amp.dims();
        let phase_capsule = export_tensor::<2>(py, phase.inner())?;
        let amp_capsule = export_tensor::<2>(py, amp.inner())?;
        let ctx = PyPhaseTrackerEncodeCtx {
            tracker: self.tracker.clone(),
            phase_shape,
            amp_shape,
            detections_shape: d_shape,
            detections_data: d_data,
        };
        Ok((phase_capsule, amp_capsule, Py::new(py, ctx)?))
    }

    /// Evolve a `(phase, amplitude)` state through `n_discrete_steps` of
    /// dynamics.
    ///
    /// # Errors
    ///
    /// Raises `ValueError` on a shape mismatch.
    fn evolve(
        &self,
        py: Python<'_>,
        phase: &Bound<'_, PyAny>,
        amplitude: &Bound<'_, PyAny>,
    ) -> PyResult<(Py<PyAny>, Py<PyAny>, Py<PyPhaseTrackerEvolveCtx>)> {
        let (phase, phase_shape, phase_data) = tensor_from_dlpack_with_data::<2>(phase)?;
        let (amp, amp_shape, amp_data) = tensor_from_dlpack_with_data::<2>(amplitude)?;
        let (phase_out, amp_out) = self.tracker.evolve(phase, amp).map_err(train_err_to_py)?;
        let out_phase_shape = phase_out.dims();
        let out_amp_shape = amp_out.dims();
        let phase_capsule = export_tensor::<2>(py, phase_out.inner())?;
        let amp_capsule = export_tensor::<2>(py, amp_out.inner())?;
        let ctx = PyPhaseTrackerEvolveCtx {
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

    /// Phase-coherence similarity matrix between two `(N, n_osc)` phase
    /// tensors.
    ///
    /// # Errors
    ///
    /// Raises `ValueError` on a shape mismatch.
    fn phase_similarity(
        &self,
        py: Python<'_>,
        phase_a: &Bound<'_, PyAny>,
        phase_b: &Bound<'_, PyAny>,
    ) -> PyResult<(Py<PyAny>, Py<PyPhaseTrackerSimilarityCtx>)> {
        let (phase_a, a_shape, a_data) = tensor_from_dlpack_with_data::<2>(phase_a)?;
        let (phase_b, b_shape, b_data) = tensor_from_dlpack_with_data::<2>(phase_b)?;
        let sim = self
            .tracker
            .phase_similarity(phase_a, phase_b)
            .map_err(train_err_to_py)?;
        let out_shape = sim.dims();
        let capsule = export_tensor::<2>(py, sim.inner())?;
        let ctx = PyPhaseTrackerSimilarityCtx {
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
    /// (see the module docs) — `matches[i]` is the index in `detections_t1`
    /// matched to detection `i` in `detections_t`, or `-1` if unmatched;
    /// `similarity` is the full `[N_t, N_t1]` matrix (detached — no gradient
    /// graph).
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

    /// Track objects across a sequence of frames. **Non-differentiable** (see
    /// the module docs). `frame_detections` is a Python list of `[N_t,
    /// detection_dim]` DLPack tensors.
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
    /// rejecting a shape mismatch and leaving `self` unchanged on failure
    /// (WP025-F1 contract).
    ///
    /// # Errors
    ///
    /// Raises `ValueError` if `bytes` does not decode to a record with this
    /// tracker's `n_osc`.
    fn load_state_dict(&mut self, bytes: &[u8]) -> PyResult<()> {
        let record = load_checkpoint_record::<PhaseTracker<BridgeBackend>>(bytes)?;
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

pub(crate) fn register(m: &Bound<'_, PyModule>) -> PyResult<()> {
    m.add_class::<PyPhaseTrackerBridge>()?;
    m.add_class::<PyPhaseTrackerEncodeCtx>()?;
    m.add_class::<PyPhaseTrackerEvolveCtx>()?;
    m.add_class::<PyPhaseTrackerSimilarityCtx>()?;
    m.add_class::<PyTrackingResult>()?;
    Ok(())
}
