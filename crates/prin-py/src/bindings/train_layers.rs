//! PyO3 `torch.autograd.Function` bridges for the `prin-train` WP-023
//! trainable primitives — Bucket E of the WP-036 S1 compatibility surface
//! (sub-pass 0141B).
//!
//! Six PRINet-3.0-compatible symbols land here, all thin marshalling over
//! audited `prin-train` owners (Coding Standards §2.1 — no numerics in
//! `prin-py`):
//!
//! - [`PyDSiluBridge`] — `prin_train::activations::d_silu`
//! - [`PyPhaseActivationBridge`] — `prin_train::activations::phase_activation`
//! - [`PyHolomorphicActivationBridge`] —
//!   `prin_train::activations::HolomorphicActivation` (split-complex path;
//!   see that type's docs for the permanent `holomorphic=False` deviation)
//! - [`PyFeedbackInhibitionBridge`] —
//!   `prin_train::inhibition::FeedbackInhibition` (hard-forward / soft-backward
//!   STE)
//! - [`PyHolomorphicEnergyBridge`] — `prin_train::energy::HolomorphicEnergy`
//! - [`PyHolomorphicEpTrainer`] — `prin_train::hep::HolomorphicEp` (a ±β
//!   equilibrium-propagation *gradient estimator*, not itself a
//!   `torch.autograd.Function`)
//!
//! Every differentiable bridge follows the recompute-on-backward contract
//! [`super::train`]'s module docs establish: `forward` runs the whole Rust
//! pass in one boundary crossing and returns `(*output_capsules, ctx)`;
//! `ctx.backward(*grad_output_capsules)` rebuilds a fresh `require_grad` leaf
//! from the saved plain input values, re-runs the forward pass, and seeds the
//! reverse pass with `(output · grad_output).sum().backward()` — the standard
//! VJP trick `torch.autograd.gradcheck` needs (it calls `backward` once per
//! output element against the same saved forward pass). No new `unsafe`; all
//! DLPack FFI is delegated to the audited `dlpack` module (Project Plan
//! amendment #6).
//!
//! `d_silu` / `phase_activation` inherit `burn-tensor` 0.16.1's `f32`-internal
//! `sigmoid` precision floor (`DOCS/reports/DEFERRED_VALIDATION_REGISTER.md`
//! DV-018); the Python-side gradcheck tests for these two use the DV-018
//! epsilon/tolerance (`eps=1e-4`), documented at each call site.

use burn::tensor::Tensor;
use pyo3::exceptions::PyValueError;
use pyo3::prelude::*;

use prin_train::activations::{
    d_silu, phase_activation, ComplexTensor, HolomorphicActivationConfig,
};
use prin_train::energy::{HolomorphicEnergy, HolomorphicEnergyConfig};
use prin_train::hep::{HolomorphicEp, HolomorphicEpConfig};
use prin_train::inhibition::{FeedbackInhibition, FeedbackInhibitionConfig};

use super::train::PyResonanceLayerBridge;
use super::train_support::{
    device, export_tensor, plain_tensor_from_dlpack, tensor_from_dlpack_with_data, train_err_to_py,
};

/// Rebuild a `[batch, n]` gradient-tracked leaf from saved plain values.
fn leaf_2d(shape: &[usize], data: &[f64]) -> Tensor<super::train_support::BridgeBackend, 2> {
    Tensor::from_data(
        burn::tensor::TensorData::new(data.to_vec(), shape.to_vec()),
        &device(),
    )
    .require_grad()
}

// --- dSiLU ---------------------------------------------------------------

/// Backward context for one [`PyDSiluBridge::forward`] call. Re-callable —
/// see [`super::train`]'s module docs for the recompute-on-backward contract.
#[pyclass(name = "DSiLUCtx", module = "prin._prin_core", unsendable)]
pub struct PyDSiluCtx {
    out_shape: [usize; 2],
    z_shape: Vec<usize>,
    z_data: Vec<f64>,
}

#[pymethods]
impl PyDSiluCtx {
    /// Run the Rust backward pass for the saved forward call.
    ///
    /// # Errors
    ///
    /// Raises `ValueError` if `grad_output` has the wrong dtype/device/shape.
    fn backward(&self, py: Python<'_>, grad_output: &Bound<'_, PyAny>) -> PyResult<Py<PyAny>> {
        let grad_output = plain_tensor_from_dlpack::<2>(grad_output, self.out_shape)?;
        let z = leaf_2d(&self.z_shape, &self.z_data);
        let output = d_silu(z.clone());
        let grads = (output * grad_output).sum().backward();
        let grad_z = z.grad(&grads).ok_or_else(|| {
            PyValueError::new_err("internal error: no gradient recorded for the bridge input")
        })?;
        export_tensor::<2>(py, grad_z)
    }
}

/// `dSiLU(z) = σ(z)·(1 + z·(1 − σ(z)))`, the exact SiLU derivative, bridged
/// to `torch.autograd.Function` via DLPack. Wraps
/// [`prin_train::activations::d_silu`] (stateless — no parameters).
#[pyclass(name = "DSiLUBridge", module = "prin._prin_core", unsendable)]
pub struct PyDSiluBridge;

#[pymethods]
impl PyDSiluBridge {
    /// Construct the (stateless) bridge.
    #[new]
    fn new() -> Self {
        Self
    }

    /// Run `dSiLU` elementwise over a `[batch, n]` `float64` CPU DLPack
    /// tensor. Returns `(output_capsule, ctx)` with the same shape.
    ///
    /// # Errors
    ///
    /// Raises `ValueError` on a non-`float64`/non-CPU/non-contiguous input or
    /// a non-2-D shape.
    fn forward(
        &self,
        py: Python<'_>,
        z: &Bound<'_, PyAny>,
    ) -> PyResult<(Py<PyAny>, Py<PyDSiluCtx>)> {
        let (z, z_shape, z_data) = tensor_from_dlpack_with_data::<2>(z)?;
        let output = d_silu(z);
        let out_shape = output.dims();
        let out_capsule = export_tensor::<2>(py, output.inner())?;
        let ctx = PyDSiluCtx {
            out_shape,
            z_shape,
            z_data,
        };
        Ok((out_capsule, Py::new(py, ctx)?))
    }
}

// --- PhaseActivation ----------------------------------------------------

/// Backward context for one [`PyPhaseActivationBridge::forward`] call.
#[pyclass(name = "PhaseActivationCtx", module = "prin._prin_core", unsendable)]
pub struct PyPhaseActivationCtx {
    out_shape: [usize; 2],
    z_shape: Vec<usize>,
    z_data: Vec<f64>,
}

#[pymethods]
impl PyPhaseActivationCtx {
    /// Run the Rust backward pass for the saved forward call.
    ///
    /// # Errors
    ///
    /// Raises `ValueError` if `grad_output` has the wrong dtype/device/shape.
    fn backward(&self, py: Python<'_>, grad_output: &Bound<'_, PyAny>) -> PyResult<Py<PyAny>> {
        let grad_output = plain_tensor_from_dlpack::<2>(grad_output, self.out_shape)?;
        let z = leaf_2d(&self.z_shape, &self.z_data);
        let output = phase_activation(z.clone());
        let grads = (output * grad_output).sum().backward();
        let grad_z = z.grad(&grads).ok_or_else(|| {
            PyValueError::new_err("internal error: no gradient recorded for the bridge input")
        })?;
        export_tensor::<2>(py, grad_z)
    }
}

/// `PhaseActivation(z) = clamp(dSiLU(z) mod 2π, 0, 2π − 1e-7)`, bridged to
/// `torch.autograd.Function` via DLPack. Wraps
/// [`prin_train::activations::phase_activation`] (stateless — the default
/// `dSiLU` inner activation; a caller-supplied inner activation is a WP-036B/C
/// parity concern, not this pass).
#[pyclass(name = "PhaseActivationBridge", module = "prin._prin_core", unsendable)]
pub struct PyPhaseActivationBridge;

#[pymethods]
impl PyPhaseActivationBridge {
    /// Construct the (stateless) bridge.
    #[new]
    fn new() -> Self {
        Self
    }

    /// Run `PhaseActivation` over a `[batch, n]` `float64` CPU DLPack tensor.
    /// Returns `(output_capsule, ctx)`; output values lie in `[0, 2π)`.
    ///
    /// # Errors
    ///
    /// Raises `ValueError` on a non-`float64`/non-CPU/non-contiguous input or
    /// a non-2-D shape.
    fn forward(
        &self,
        py: Python<'_>,
        z: &Bound<'_, PyAny>,
    ) -> PyResult<(Py<PyAny>, Py<PyPhaseActivationCtx>)> {
        let (z, z_shape, z_data) = tensor_from_dlpack_with_data::<2>(z)?;
        let output = phase_activation(z);
        let out_shape = output.dims();
        let out_capsule = export_tensor::<2>(py, output.inner())?;
        let ctx = PyPhaseActivationCtx {
            out_shape,
            z_shape,
            z_data,
        };
        Ok((out_capsule, Py::new(py, ctx)?))
    }
}

// --- HolomorphicActivation (split-complex) -----------------------------

/// Backward context for one [`PyHolomorphicActivationBridge::forward`] call.
#[pyclass(
    name = "HolomorphicActivationCtx",
    module = "prin._prin_core",
    unsendable
)]
pub struct PyHolomorphicActivationCtx {
    scale: f64,
    out_shape: [usize; 2],
    re_shape: Vec<usize>,
    re_data: Vec<f64>,
    im_shape: Vec<usize>,
    im_data: Vec<f64>,
}

#[pymethods]
impl PyHolomorphicActivationCtx {
    /// Run the Rust backward pass, returning `(grad_re, grad_im)`.
    ///
    /// # Errors
    ///
    /// Raises `ValueError` if either cotangent has the wrong
    /// dtype/device/shape, or if the split-complex activation unexpectedly
    /// records no gradient for an input part.
    fn backward(
        &self,
        py: Python<'_>,
        grad_re: &Bound<'_, PyAny>,
        grad_im: &Bound<'_, PyAny>,
    ) -> PyResult<(Py<PyAny>, Py<PyAny>)> {
        let grad_re = plain_tensor_from_dlpack::<2>(grad_re, self.out_shape)?;
        let grad_im = plain_tensor_from_dlpack::<2>(grad_im, self.out_shape)?;
        let re = leaf_2d(&self.re_shape, &self.re_data);
        let im = leaf_2d(&self.im_shape, &self.im_data);
        let act = HolomorphicActivationConfig::new(self.scale)
            .map_err(train_err_to_py)?
            .init();
        let z = ComplexTensor::new(re.clone(), im.clone()).map_err(train_err_to_py)?;
        let (out_re, out_im) = act.forward(z).into_parts();
        let grads = (out_re * grad_re + out_im * grad_im).sum().backward();
        let g_re = re.grad(&grads).ok_or_else(|| {
            PyValueError::new_err("internal error: no gradient recorded for the real part")
        })?;
        let g_im = im.grad(&grads).ok_or_else(|| {
            PyValueError::new_err("internal error: no gradient recorded for the imaginary part")
        })?;
        Ok((export_tensor::<2>(py, g_re)?, export_tensor::<2>(py, g_im)?))
    }
}

/// Split-complex holomorphic-compatible activation
/// `(re, im) ↦ (scale·tanh(re), scale·tanh(im))`, bridged to
/// `torch.autograd.Function` via DLPack. Wraps
/// [`prin_train::activations::HolomorphicActivation`] — always the
/// `holomorphic=False` path (that type's permanent documented deviation:
/// Burn has no complex-tensor autodiff).
#[pyclass(
    name = "HolomorphicActivationBridge",
    module = "prin._prin_core",
    unsendable
)]
pub struct PyHolomorphicActivationBridge {
    scale: f64,
}

#[pymethods]
impl PyHolomorphicActivationBridge {
    /// Construct with output scale `scale` (PRINet 3.0 default `1.0`).
    ///
    /// # Errors
    ///
    /// Raises `ValueError` if `scale` is not finite.
    #[new]
    #[pyo3(signature = (scale=1.0))]
    fn new(scale: f64) -> PyResult<Self> {
        HolomorphicActivationConfig::new(scale).map_err(train_err_to_py)?;
        Ok(Self { scale })
    }

    /// Output scale factor.
    #[getter]
    fn scale(&self) -> f64 {
        self.scale
    }

    /// Activate a complex state carried as a `(re, im)` pair of `[batch, n]`
    /// `float64` CPU DLPack tensors. Returns `(re_capsule, im_capsule, ctx)`.
    ///
    /// # Errors
    ///
    /// Raises `ValueError` on a non-`float64`/non-CPU/non-contiguous input,
    /// a non-2-D shape, or mismatched `re`/`im` shapes.
    fn forward(
        &self,
        py: Python<'_>,
        re: &Bound<'_, PyAny>,
        im: &Bound<'_, PyAny>,
    ) -> PyResult<(Py<PyAny>, Py<PyAny>, Py<PyHolomorphicActivationCtx>)> {
        let (re_t, re_shape, re_data) = tensor_from_dlpack_with_data::<2>(re)?;
        let (im_t, im_shape, im_data) = tensor_from_dlpack_with_data::<2>(im)?;
        let act = HolomorphicActivationConfig::new(self.scale)
            .map_err(train_err_to_py)?
            .init();
        let z = ComplexTensor::new(re_t, im_t).map_err(train_err_to_py)?;
        let (out_re, out_im) = act.forward(z).into_parts();
        let out_shape = out_re.dims();
        let re_capsule = export_tensor::<2>(py, out_re.inner())?;
        let im_capsule = export_tensor::<2>(py, out_im.inner())?;
        let ctx = PyHolomorphicActivationCtx {
            scale: self.scale,
            out_shape,
            re_shape,
            re_data,
            im_shape,
            im_data,
        };
        Ok((re_capsule, im_capsule, Py::new(py, ctx)?))
    }
}

// --- FeedbackInhibition (top-k WTA STE) --------------------------------

/// Backward context for one [`PyFeedbackInhibitionBridge::forward`] call.
#[pyclass(name = "FeedbackInhibitionCtx", module = "prin._prin_core", unsendable)]
pub struct PyFeedbackInhibitionCtx {
    fbi: FeedbackInhibition,
    out_shape: [usize; 2],
    rates_shape: Vec<usize>,
    rates_data: Vec<f64>,
}

#[pymethods]
impl PyFeedbackInhibitionCtx {
    /// Run the Rust backward pass for the saved forward call.
    ///
    /// The STE means gradients flow through the soft-softmax term while the
    /// forward pass returns the hard top-`k` selection — see
    /// [`prin_train::inhibition`]'s module docs.
    ///
    /// # Errors
    ///
    /// Raises `ValueError` if `grad_output` has the wrong dtype/device/shape.
    fn backward(&self, py: Python<'_>, grad_output: &Bound<'_, PyAny>) -> PyResult<Py<PyAny>> {
        let grad_output = plain_tensor_from_dlpack::<2>(grad_output, self.out_shape)?;
        let rates = leaf_2d(&self.rates_shape, &self.rates_data);
        let output = self
            .fbi
            .compete(rates.clone())
            .expect("shape already validated by the saved forward call");
        let grads = (output * grad_output).sum().backward();
        let grad_rates = rates.grad(&grads).ok_or_else(|| {
            PyValueError::new_err("internal error: no gradient recorded for the bridge input")
        })?;
        export_tensor::<2>(py, grad_rates)
    }
}

/// Top-`k` winner-take-all feedback inhibition with a hard-forward /
/// soft-backward straight-through estimator, bridged to
/// `torch.autograd.Function` via DLPack. Wraps
/// [`prin_train::inhibition::FeedbackInhibition`] (no learnable parameters —
/// `k`/`sparsity`/`temperature` are fixed hyperparameters).
#[pyclass(
    name = "FeedbackInhibitionBridge",
    module = "prin._prin_core",
    unsendable
)]
pub struct PyFeedbackInhibitionBridge {
    fbi: FeedbackInhibition,
}

#[pymethods]
impl PyFeedbackInhibitionBridge {
    /// Construct with `n_oscillators` units. `k` (when `None`) is derived
    /// from `sparsity` at construction: `k = min(n, max(1, floor(n·sparsity)))`.
    ///
    /// # Errors
    ///
    /// Raises `ValueError` if `n_oscillators` is zero, `k` is `Some(0)`,
    /// `sparsity ∉ (0, 1]`, or `temperature` is not finite.
    #[new]
    #[pyo3(signature = (n_oscillators, k=None, sparsity=0.1, temperature=1.0))]
    fn new(
        n_oscillators: usize,
        k: Option<usize>,
        sparsity: f64,
        temperature: f64,
    ) -> PyResult<Self> {
        let fbi = FeedbackInhibitionConfig::with_params(n_oscillators, k, sparsity, temperature)
            .map_err(train_err_to_py)?
            .init();
        Ok(Self { fbi })
    }

    /// Number of units the competition operates over.
    #[getter]
    fn n_oscillators(&self) -> usize {
        self.fbi.n_oscillators()
    }

    /// Resolved top-`k` winner count.
    #[getter]
    fn k(&self) -> usize {
        self.fbi.k()
    }

    /// Softmax temperature for the soft (backward-pass) scores.
    #[getter]
    fn temperature(&self) -> f64 {
        self.fbi.temperature()
    }

    /// Apply the competition to a `[batch, n_oscillators]` `float64` CPU
    /// DLPack tensor. Returns `(output_capsule, ctx)` with the same shape.
    ///
    /// # Errors
    ///
    /// Raises `ValueError` on a non-`float64`/non-CPU/non-contiguous input, a
    /// non-2-D shape, or a width other than `n_oscillators`.
    fn forward(
        &self,
        py: Python<'_>,
        rates: &Bound<'_, PyAny>,
    ) -> PyResult<(Py<PyAny>, Py<PyFeedbackInhibitionCtx>)> {
        let (rates_t, rates_shape, rates_data) = tensor_from_dlpack_with_data::<2>(rates)?;
        let output = self.fbi.compete(rates_t).map_err(train_err_to_py)?;
        let out_shape = output.dims();
        let out_capsule = export_tensor::<2>(py, output.inner())?;
        let ctx = PyFeedbackInhibitionCtx {
            fbi: self.fbi,
            out_shape,
            rates_shape,
            rates_data,
        };
        Ok((out_capsule, Py::new(py, ctx)?))
    }
}

// --- HolomorphicEnergy -------------------------------------------------

/// Backward context for one [`PyHolomorphicEnergyBridge::forward`] call.
#[pyclass(name = "HolomorphicEnergyCtx", module = "prin._prin_core", unsendable)]
pub struct PyHolomorphicEnergyCtx {
    energy: HolomorphicEnergy,
    beta: f64,
    re_shape: Vec<usize>,
    re_data: Vec<f64>,
    im_shape: Vec<usize>,
    im_data: Vec<f64>,
    coupling_shape: Vec<usize>,
    coupling_data: Vec<f64>,
    task_loss: Option<(Vec<usize>, Vec<f64>)>,
}

#[pymethods]
impl PyHolomorphicEnergyCtx {
    /// Run the Rust backward pass, returning `(grad_re, grad_im,
    /// grad_coupling)`. `task_loss` (when supplied) is treated as a
    /// non-differentiable constant.
    ///
    /// # Errors
    ///
    /// Raises `ValueError` if `grad_output` is not a scalar `[1]` cotangent,
    /// or if the energy unexpectedly records no gradient for an input.
    fn backward(
        &self,
        py: Python<'_>,
        grad_output: &Bound<'_, PyAny>,
    ) -> PyResult<(Py<PyAny>, Py<PyAny>, Py<PyAny>)> {
        let grad_output = plain_tensor_from_dlpack::<1>(grad_output, [1])?;
        let re = leaf_2d(&self.re_shape, &self.re_data);
        let im = leaf_2d(&self.im_shape, &self.im_data);
        let coupling = leaf_2d(&self.coupling_shape, &self.coupling_data);
        let task = self.task_loss.as_ref().map(|(shape, data)| {
            Tensor::<super::train_support::BridgeBackend, 2>::from_data(
                burn::tensor::TensorData::new(data.clone(), shape.clone()),
                &device(),
            )
        });
        let z = ComplexTensor::new(re.clone(), im.clone()).map_err(train_err_to_py)?;
        let out = self
            .energy
            .forward(z, coupling.clone(), task, self.beta)
            .map_err(train_err_to_py)?;
        let grads = (out * grad_output).sum().backward();
        let g_re = re.grad(&grads).ok_or_else(no_energy_grad)?;
        let g_im = im.grad(&grads).ok_or_else(no_energy_grad)?;
        let g_coupling = coupling.grad(&grads).ok_or_else(no_energy_grad)?;
        Ok((
            export_tensor::<2>(py, g_re)?,
            export_tensor::<2>(py, g_im)?,
            export_tensor::<2>(py, g_coupling)?,
        ))
    }
}

fn no_energy_grad() -> PyErr {
    PyValueError::new_err("internal error: no gradient recorded for a HolomorphicEnergy input")
}

/// Holomorphic energy of a complex oscillator state under a real coupling
/// matrix, bridged to `torch.autograd.Function` via DLPack. Wraps
/// [`prin_train::energy::HolomorphicEnergy`] (no learnable parameters).
///
/// `E = mean_batch(−Σᵢⱼ K[i,j]·Re(z_i* z_j) + Σᵢ (|z_i|² − 1)² + β·task_loss)`.
#[pyclass(
    name = "HolomorphicEnergyBridge",
    module = "prin._prin_core",
    unsendable
)]
pub struct PyHolomorphicEnergyBridge {
    energy: HolomorphicEnergy,
}

#[pymethods]
impl PyHolomorphicEnergyBridge {
    /// Construct for `n_oscillators` complex oscillators.
    ///
    /// # Errors
    ///
    /// Raises `ValueError` if `n_oscillators` is zero.
    #[new]
    fn new(n_oscillators: usize) -> PyResult<Self> {
        let energy = HolomorphicEnergyConfig::new(n_oscillators)
            .map_err(train_err_to_py)?
            .init();
        Ok(Self { energy })
    }

    /// Number of complex oscillators.
    #[getter]
    fn n_oscillators(&self) -> usize {
        self.energy.n_oscillators()
    }

    /// Compute the scalar batch-averaged energy. `re`/`im` are
    /// `[batch, n_oscillators]`, `coupling` is `[n_oscillators,
    /// n_oscillators]`, `task_loss` (optional) is `[batch, 1]`, and `beta`
    /// scales `task_loss` only when non-zero. Returns `(output_capsule,
    /// ctx)`; `output` is shape `[1]`.
    ///
    /// # Errors
    ///
    /// Raises `ValueError` on a non-`float64`/non-CPU/non-contiguous input or
    /// any [`prin_train::error::TrainError`] shape guard.
    #[pyo3(signature = (re, im, coupling, task_loss=None, beta=0.0))]
    fn forward(
        &self,
        py: Python<'_>,
        re: &Bound<'_, PyAny>,
        im: &Bound<'_, PyAny>,
        coupling: &Bound<'_, PyAny>,
        task_loss: Option<&Bound<'_, PyAny>>,
        beta: f64,
    ) -> PyResult<(Py<PyAny>, Py<PyHolomorphicEnergyCtx>)> {
        let (re_t, re_shape, re_data) = tensor_from_dlpack_with_data::<2>(re)?;
        let (im_t, im_shape, im_data) = tensor_from_dlpack_with_data::<2>(im)?;
        let (coupling_t, coupling_shape, coupling_data) =
            tensor_from_dlpack_with_data::<2>(coupling)?;
        let task = match task_loss {
            Some(obj) => {
                let (t, shape, data) = tensor_from_dlpack_with_data::<2>(obj)?;
                Some((t, shape, data))
            }
            None => None,
        };
        let z = ComplexTensor::new(re_t, im_t).map_err(train_err_to_py)?;
        let task_tensor = task.as_ref().map(|(t, _, _)| t.clone());
        let out = self
            .energy
            .forward(z, coupling_t, task_tensor, beta)
            .map_err(train_err_to_py)?;
        let out_capsule = export_tensor::<1>(py, out.inner())?;
        let ctx = PyHolomorphicEnergyCtx {
            energy: self.energy,
            beta,
            re_shape,
            re_data,
            im_shape,
            im_data,
            coupling_shape,
            coupling_data,
            task_loss: task.map(|(_, shape, data)| (shape, data)),
        };
        Ok((out_capsule, Py::new(py, ctx)?))
    }
}

// --- HolomorphicEPTrainer (±β equilibrium-propagation estimator) -------

/// ±β Holomorphic Equilibrium Propagation gradient estimator over a
/// [`PyResonanceLayerBridge`]. Wraps [`prin_train::hep::HolomorphicEp`].
///
/// This is a *gradient estimator*, not a differentiable op: it runs the
/// resonance layer's dynamics to the free and ±β-nudged equilibria and
/// returns a closed-form coupling-gradient estimate. No `torch.autograd`
/// graph is involved (and none is needed — the estimate replaces
/// backpropagation).
#[pyclass(name = "HolomorphicEpTrainer", module = "prin._prin_core", unsendable)]
pub struct PyHolomorphicEpTrainer {
    hep: HolomorphicEp,
    energy: HolomorphicEnergy,
    free_steps: usize,
    nudge_steps: usize,
}

#[pymethods]
impl PyHolomorphicEpTrainer {
    /// Construct for `n_oscillators` oscillators with nudge strength `beta`
    /// and the PRINet 3.0 default equilibrium step counts.
    ///
    /// # Errors
    ///
    /// Raises `ValueError` if `beta` is not strictly positive/finite, either
    /// step count is zero, or `n_oscillators` is zero.
    #[new]
    #[pyo3(signature = (n_oscillators, beta=0.1, free_steps=50, nudge_steps=20))]
    fn new(
        n_oscillators: usize,
        beta: f64,
        free_steps: usize,
        nudge_steps: usize,
    ) -> PyResult<Self> {
        let hep = HolomorphicEpConfig::with_params(beta, free_steps, nudge_steps)
            .map_err(train_err_to_py)?
            .init();
        let energy = HolomorphicEnergyConfig::new(n_oscillators)
            .map_err(train_err_to_py)?
            .init();
        Ok(Self {
            hep,
            energy,
            free_steps,
            nudge_steps,
        })
    }

    /// Nudge strength β.
    #[getter]
    fn beta(&self) -> f64 {
        self.hep.beta()
    }

    /// Set the nudge strength β (PRINet 3.0's `beta` setter).
    ///
    /// # Errors
    ///
    /// Raises `ValueError` if `value` is not strictly positive/finite.
    #[setter]
    fn set_beta(&mut self, value: f64) -> PyResult<()> {
        self.hep = HolomorphicEpConfig::with_params(value, self.free_steps, self.nudge_steps)
            .map_err(train_err_to_py)?
            .init();
        Ok(())
    }

    /// Closed-form ±β coupling-gradient estimate for `layer`.
    ///
    /// `x` is `[batch, n_dims]`, `target_direction` is
    /// `[batch, n_oscillators]`; both `float64` CPU DLPack tensors. Returns a
    /// `[n_oscillators, n_oscillators]` gradient capsule.
    ///
    /// # Errors
    ///
    /// Raises `ValueError` on a bad tensor or a `prin-train` shape guard.
    fn coupling_gradient(
        &self,
        py: Python<'_>,
        layer: PyRef<'_, PyResonanceLayerBridge>,
        x: &Bound<'_, PyAny>,
        target_direction: &Bound<'_, PyAny>,
    ) -> PyResult<Py<PyAny>> {
        let (x_t, _, _) = tensor_from_dlpack_with_data::<2>(x)?;
        let (dir_t, _, _) = tensor_from_dlpack_with_data::<2>(target_direction)?;
        let grad = self
            .hep
            .coupling_gradient(layer.layer(), x_t, dir_t)
            .map_err(train_err_to_py)?;
        export_tensor::<2>(py, grad.inner())
    }

    /// Physics energy (β=0, no task term) of `layer`'s free-phase
    /// equilibrium, under `coupling` (`[n_oscillators, n_oscillators]`).
    /// Returns a scalar `[1]` capsule.
    ///
    /// # Errors
    ///
    /// Raises `ValueError` on a bad tensor or a `prin-train` shape guard.
    fn free_energy(
        &self,
        py: Python<'_>,
        layer: PyRef<'_, PyResonanceLayerBridge>,
        x: &Bound<'_, PyAny>,
        coupling: &Bound<'_, PyAny>,
    ) -> PyResult<Py<PyAny>> {
        let (x_t, _, _) = tensor_from_dlpack_with_data::<2>(x)?;
        let (coupling_t, _, _) = tensor_from_dlpack_with_data::<2>(coupling)?;
        let e = self
            .hep
            .free_energy(layer.layer(), x_t, &self.energy, coupling_t)
            .map_err(train_err_to_py)?;
        export_tensor::<1>(py, e.inner())
    }
}

pub(crate) fn register(m: &Bound<'_, PyModule>) -> PyResult<()> {
    m.add_class::<PyDSiluBridge>()?;
    m.add_class::<PyDSiluCtx>()?;
    m.add_class::<PyPhaseActivationBridge>()?;
    m.add_class::<PyPhaseActivationCtx>()?;
    m.add_class::<PyHolomorphicActivationBridge>()?;
    m.add_class::<PyHolomorphicActivationCtx>()?;
    m.add_class::<PyFeedbackInhibitionBridge>()?;
    m.add_class::<PyFeedbackInhibitionCtx>()?;
    m.add_class::<PyHolomorphicEnergyBridge>()?;
    m.add_class::<PyHolomorphicEnergyCtx>()?;
    m.add_class::<PyHolomorphicEpTrainer>()?;
    Ok(())
}
