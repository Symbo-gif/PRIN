//! PyO3 `torch.autograd.Function` bridge for
//! [`prin_train::attention::OscillatoryAttention`] (Exec-WP-026 S1).
//!
//! Follows the `train.rs` WP-025 bridge pattern (see that module's docs for
//! the recompute-on-backward contract), generalized to rank-3 tensors and an
//! optional second differentiable input (`phase`) via
//! [`super::train_support`].
//!
//! **Dropout is restricted to `0.0`.** `burn::nn::Dropout::forward` applies a
//! stochastic Bernoulli mask whenever `B::ad_enabled()` is true and `prob !=
//! 0.0` (confirmed by reading `burn-core`'s `Dropout` source), drawn from the
//! backend's own unseeded RNG. That breaks two things this bridge requires:
//! `torch.autograd.gradcheck` needs a deterministic forward (a fresh random
//! mask each call fails the finite-difference check outright), and the
//! recompute-on-backward design needs `backward()`'s internal re-run of
//! `forward()` to reproduce the *exact* computation that produced the saved
//! output (a different random mask on recompute would silently compute the
//! gradient of the wrong function). Rather than plumb the project's seeded
//! [`Seed`] through Burn's `Dropout` (no exercising caller in this WP's
//! scope, and Burn's `Dropout` has no seed-injection hook to do so safely),
//! the bridge constructor rejects any non-zero `dropout`, documented here as
//! a deliberate bridge-level restriction — training-time dropout
//! regularization through this bridge is an explicit out-of-scope discovery
//! for a future WP, not a silently dropped feature.

use burn::module::Module;
use burn::tensor::Tensor;
use pyo3::exceptions::PyValueError;
use pyo3::prelude::*;
use pyo3::types::PyBytes;

use prin_dynamics::Seed;
use prin_train::attention::{OscillatoryAttention, OscillatoryAttentionConfig};

use super::train_support::{
    device, export_tensor, load_checkpoint_record, optional_tensor_from_dlpack_with_data,
    plain_tensor_from_dlpack, record_to_bytes, tensor_from_dlpack_with_data, train_err_to_py,
    BridgeBackend,
};

/// Backward context for one [`PyOscillatoryAttentionBridge::forward`] call.
/// See `train.rs`'s module docs for the recompute-on-backward contract.
#[pyclass(
    name = "OscillatoryAttentionCtx",
    module = "prin._prin_core",
    unsendable
)]
pub struct PyOscillatoryAttentionCtx {
    layer: OscillatoryAttention<BridgeBackend>,
    out_shape: [usize; 3],
    x_shape: Vec<usize>,
    x_data: Vec<f64>,
    /// `Some((shape, data))` only when `phase` was explicitly supplied to
    /// `forward` (otherwise phase is derived internally from `x` and has no
    /// independent gradient to report).
    phase: Option<(Vec<usize>, Vec<f64>)>,
    /// `Some((shape, data))` when an attention `mask` was supplied; replayed
    /// as a constant (non-grad) `[seq, seq]` tensor on the backward recompute.
    mask: Option<(Vec<usize>, Vec<f64>)>,
}

#[pymethods]
impl PyOscillatoryAttentionCtx {
    /// Run the Rust backward pass for the saved forward call.
    ///
    /// Returns `(grad_x, grad_phase)`: `grad_phase` is `None` unless an
    /// explicit `phase` tensor was passed to the saved `forward` call.
    ///
    /// # Errors
    ///
    /// Raises `ValueError` if `grad_output` has the wrong shape, or if the
    /// gradient graph unexpectedly has no entry for `x` (internal bridge
    /// defect, not a user error).
    #[allow(clippy::type_complexity)]
    fn backward(
        &self,
        py: Python<'_>,
        grad_output: &Bound<'_, PyAny>,
    ) -> PyResult<(Py<PyAny>, Option<Py<PyAny>>, Option<Py<PyAny>>)> {
        let grad_output = plain_tensor_from_dlpack::<3>(grad_output, self.out_shape)?;

        let x = Tensor::from_data(
            burn::tensor::TensorData::new(self.x_data.clone(), self.x_shape.clone()),
            &device(),
        )
        .require_grad();
        let phase_leaf = self.phase.as_ref().map(|(shape, data)| {
            Tensor::<BridgeBackend, 3>::from_data(
                burn::tensor::TensorData::new(data.clone(), shape.clone()),
                &device(),
            )
            .require_grad()
        });

        let mask_leaf = self.mask.as_ref().map(|(shape, data)| {
            Tensor::<BridgeBackend, 2>::from_data(
                burn::tensor::TensorData::new(data.clone(), shape.clone()),
                &device(),
            )
        });

        let output = self
            .layer
            .forward_masked(x.clone(), phase_leaf.clone(), mask_leaf)
            .expect("shape already validated by the saved forward call");

        let weighted = output * grad_output;
        let grads = weighted.sum().backward();

        let grad_x = x.grad(&grads).ok_or_else(|| {
            PyValueError::new_err("internal error: no gradient recorded for the bridge input")
        })?;
        let grad_x_capsule = export_tensor::<3>(py, grad_x)?;

        let grad_phase_capsule = match phase_leaf {
            Some(p) => {
                let grad_phase = p.grad(&grads).ok_or_else(|| {
                    PyValueError::new_err(
                        "internal error: no gradient recorded for the bridge phase input",
                    )
                })?;
                Some(export_tensor::<3>(py, grad_phase)?)
            }
            None => None,
        };

        // The attention `mask` is a constant with no gradient.
        Ok((grad_x_capsule, grad_phase_capsule, None))
    }
}

/// Multi-head attention with an additive oscillatory coherence bias, bridged
/// to `torch.autograd.Function` via DLPack.
///
/// Wraps [`prin_train::attention::OscillatoryAttention`]; see that module's
/// docs for the exact formula. Weight/bias/`alpha` parameters live in Rust —
/// see `train.rs`'s docs for the training-ownership split. See the module
/// docs above for why `dropout` is restricted to `0.0`.
#[pyclass(
    name = "OscillatoryAttentionBridge",
    module = "prin._prin_core",
    unsendable
)]
pub struct PyOscillatoryAttentionBridge {
    layer: OscillatoryAttention<BridgeBackend>,
}

#[pymethods]
impl PyOscillatoryAttentionBridge {
    /// Construct with seeded-random parameters. `alpha` (the coherence-bias
    /// strength) is zero-initialized, matching PRINet 3.0.
    ///
    /// # Errors
    ///
    /// Raises `ValueError` for an invalid `d_model`/`n_heads` (see
    /// [`OscillatoryAttentionConfig::with_params`]) or a non-zero `dropout`
    /// (see the module docs).
    #[new]
    #[pyo3(signature = (d_model, n_heads, dropout=0.0, seed_counter=0, seed_key=0))]
    fn new(
        d_model: usize,
        n_heads: usize,
        dropout: f64,
        seed_counter: u64,
        seed_key: u64,
    ) -> PyResult<Self> {
        if dropout != 0.0 {
            return Err(PyValueError::new_err(
                "OscillatoryAttentionBridge requires dropout=0.0: burn::nn::Dropout draws from \
                 an unseeded backend RNG under autodiff, which breaks both torch.autograd.\
                 gradcheck determinism and this bridge's recompute-on-backward contract",
            ));
        }
        let cfg = OscillatoryAttentionConfig::with_params(d_model, n_heads, dropout)
            .map_err(train_err_to_py)?;
        let mut seed = Seed::new(seed_counter as u128, seed_key as u128);
        let layer = cfg.init::<BridgeBackend>(&device(), &mut seed);
        Ok(Self { layer })
    }

    /// Model (embedding) dimension.
    #[getter]
    fn d_model(&self) -> usize {
        self.layer.d_model()
    }

    /// Number of attention heads.
    #[getter]
    fn n_heads(&self) -> usize {
        self.layer.n_heads()
    }

    /// Forward pass. `x` is `[batch, seq, d_model]`; `phase`, if supplied, is
    /// `[batch, seq, n_heads]` (otherwise derived from `x` internally).
    /// Returns `(output_capsule, ctx)`, `output` shaped `[batch, seq,
    /// d_model]`.
    ///
    /// # Errors
    ///
    /// Raises `ValueError` on a non-`float64`/non-CPU/non-contiguous input or
    /// a shape mismatch (see
    /// [`prin_train::attention::OscillatoryAttention::forward`]).
    #[pyo3(signature = (x, phase=None, mask=None))]
    fn forward(
        &self,
        py: Python<'_>,
        x: &Bound<'_, PyAny>,
        phase: Option<&Bound<'_, PyAny>>,
        mask: Option<&Bound<'_, PyAny>>,
    ) -> PyResult<(Py<PyAny>, Py<PyOscillatoryAttentionCtx>)> {
        let (x, x_shape, x_data) = tensor_from_dlpack_with_data::<3>(x)?;
        let phase_decoded = optional_tensor_from_dlpack_with_data::<3>(phase)?;
        let (phase_tensor, phase_saved) = match phase_decoded {
            Some((t, shape, data)) => (Some(t), Some((shape, data))),
            None => (None, None),
        };
        let mask_decoded = optional_tensor_from_dlpack_with_data::<2>(mask)?;
        let (mask_tensor, mask_saved) = match mask_decoded {
            Some((t, shape, data)) => (Some(t), Some((shape, data))),
            None => (None, None),
        };

        let output = self
            .layer
            .forward_masked(x, phase_tensor, mask_tensor)
            .map_err(train_err_to_py)?;
        let out_shape = output.dims();
        let out_capsule = export_tensor::<3>(py, output.inner())?;
        let ctx = PyOscillatoryAttentionCtx {
            layer: self.layer.clone(),
            out_shape,
            x_shape,
            x_data,
            phase: phase_saved,
            mask: mask_saved,
        };
        Ok((out_capsule, Py::new(py, ctx)?))
    }

    /// Replace the per-head coherence-bias strength `alpha` (length
    /// `n_heads`). The Python wrapper owns the canonical `alpha`
    /// `nn.Parameter` and pushes it here before every forward.
    fn set_alpha(&mut self, alpha: Vec<f64>) -> PyResult<()> {
        if alpha.len() != self.layer.n_heads() {
            return Err(PyValueError::new_err(format!(
                "alpha length {} does not match n_heads {}",
                alpha.len(),
                self.layer.n_heads()
            )));
        }
        let tensor = Tensor::<BridgeBackend, 1>::from_data(
            burn::tensor::TensorData::new(alpha, [self.layer.n_heads()]),
            &device(),
        );
        self.layer.set_alpha(tensor);
        Ok(())
    }

    /// Serialize parameters to checkpoint bytes. See `train.rs`'s
    /// `ResonanceLayerBridge::state_dict`.
    fn state_dict<'py>(&self, py: Python<'py>) -> PyResult<Bound<'py, PyBytes>> {
        let bytes = record_to_bytes(&self.layer)?;
        Ok(PyBytes::new(py, &bytes))
    }

    /// Restore parameters previously produced by [`Self::state_dict`],
    /// rejecting a shape mismatch and leaving `self` unchanged on failure
    /// (WP025-F1 contract).
    ///
    /// # Errors
    ///
    /// Raises `ValueError` if `bytes` does not decode to a record with this
    /// layer's `d_model`/`n_heads`.
    fn load_state_dict(&mut self, bytes: &[u8]) -> PyResult<()> {
        let record = load_checkpoint_record::<OscillatoryAttention<BridgeBackend>>(bytes)?;
        let candidate = self.layer.clone().load_record(record);
        candidate.validate_shapes().map_err(|e| {
            PyValueError::new_err(format!(
                "checkpoint shape mismatch: this layer is configured for d_model={}, \
                 n_heads={} ({e})",
                self.layer.d_model(),
                self.layer.n_heads(),
            ))
        })?;
        self.layer = candidate;
        Ok(())
    }
}

pub(crate) fn register(m: &Bound<'_, PyModule>) -> PyResult<()> {
    m.add_class::<PyOscillatoryAttentionBridge>()?;
    m.add_class::<PyOscillatoryAttentionCtx>()?;
    Ok(())
}
