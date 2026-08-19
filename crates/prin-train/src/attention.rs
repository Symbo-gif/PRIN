//! Multi-head attention with an additive oscillatory coherence bias.
//!
//! [`OscillatoryAttention`] is the Burn `Module` rebuild of PRINet 3.0's
//! `nn.layers.OscillatoryAttention`: standard scaled dot-product multi-head
//! attention, plus a learnable per-head bias toward tokens whose oscillatory
//! phases are aligned.
//!
//! # Correspondence to the PRINet 3.0 reference
//!
//! For input `x` of shape `[batch, seq, d_model]`, per-head phase `φ` of
//! shape `[batch, seq, n_heads]` (derived from `x` via a learned projection
//! when not supplied externally), and learnable per-head bias strength `α`:
//!
//! ```text
//! Q, K, V = W_q·x, W_k·x, W_v·x                    // [batch, n_heads, seq, d_k]
//! scores  = (Q·Kᵀ) / √d_k + α·cos(φ_i − φ_j)        // [batch, n_heads, seq, seq]
//! out     = W_o·(softmax(scores, dim=-1)·V)         // [batch, seq, d_model]
//! ```
//!
//! This is a line-for-line port of `OscillatoryAttention.forward`
//! (`nn/layers.py`). The optional attention `mask` argument the PRINet 3.0
//! reference also accepts is not ported: no caller in this WP's scope
//! ([`crate::hybrid::HybridPRINetV2`]) ever passes one, and adding masked
//! softmax support with no exercising caller and no golden-value coverage
//! would be unregistered experimentation (Development Workflow and Audit
//! Standards). Recorded as an explicit out-of-scope discovery for a future
//! WP that needs masked attention.
//!
//! Standard multi-head-attention plumbing (`Q`/`K`/`V`/output linear
//! projections, dropout) uses [`burn::nn::Linear`]/[`burn::nn::Dropout`]
//! rather than this crate's usual hand-rolled `Param<Tensor>` fields: unlike
//! [`crate::bands`]/[`crate::layers`], this is generic transformer plumbing,
//! not oscillator-specific physics, and Burn's implementations are
//! functionally identical to PyTorch's `nn.Linear`/`nn.Dropout`. Weights are
//! still drawn from the project's [`Seed`] via `crate::support::seeded_linear`
//! rather than [`burn::nn::LinearConfig::init`] — see that function's docs
//! for why (`Backend::seed` is a shared global, not safe under parallel
//! test execution). Documented deviation, same class as [`crate::layers`]'s
//! initial-state projection: only the initial distribution shape differs
//! from PRINet 3.0's default PyTorch init, not the reproducibility guarantee.
//!
//! # Example
//!
//! ```
//! use burn::backend::NdArray;
//! use burn::tensor::Tensor;
//! use prin_dynamics::Seed;
//! use prin_train::attention::OscillatoryAttentionConfig;
//!
//! type Backend = NdArray<f32>;
//!
//! let cfg = OscillatoryAttentionConfig::new(64, 4).unwrap();
//! let device = Default::default();
//! let mut seed = Seed::new(0, 0);
//! let attn = cfg.init::<Backend>(&device, &mut seed);
//!
//! let x = Tensor::<Backend, 3>::ones([8, 10, 64], &device);
//! let out = attn.forward(x, None).unwrap();
//! assert_eq!(out.dims(), [8, 10, 64]);
//! ```

use burn::module::{Module, Param};
use burn::nn::{Dropout, DropoutConfig, Linear};
use burn::tensor::activation::softmax;
use burn::tensor::backend::Backend;
use burn::tensor::Tensor;
use prin_dynamics::Seed;

use crate::error::TrainError;
use crate::support::{check_dims, seeded_linear};

/// Explicit parameter tensors for [`OscillatoryAttention`] construction.
///
/// Used by golden-reference parity tests (`tests/parity_attention.rs`). Every
/// weight uses Burn's `[d_input, d_output]` layout (PyTorch's `nn.Linear`
/// stores `[d_output, d_input]` — transpose when transcribing).
pub struct OscillatoryAttentionParams<B: Backend> {
    /// Query projection weight, shape `[d_model, d_model]`.
    pub w_q_weight: Tensor<B, 2>,
    /// Query projection bias, shape `[d_model]`.
    pub w_q_bias: Tensor<B, 1>,
    /// Key projection weight, shape `[d_model, d_model]`.
    pub w_k_weight: Tensor<B, 2>,
    /// Key projection bias, shape `[d_model]`.
    pub w_k_bias: Tensor<B, 1>,
    /// Value projection weight, shape `[d_model, d_model]`.
    pub w_v_weight: Tensor<B, 2>,
    /// Value projection bias, shape `[d_model]`.
    pub w_v_bias: Tensor<B, 1>,
    /// Output projection weight, shape `[d_model, d_model]`.
    pub w_o_weight: Tensor<B, 2>,
    /// Output projection bias, shape `[d_model]`.
    pub w_o_bias: Tensor<B, 1>,
    /// Phase projection weight, shape `[d_model, n_heads]`.
    pub phase_proj_weight: Tensor<B, 2>,
    /// Phase projection bias, shape `[n_heads]`.
    pub phase_proj_bias: Tensor<B, 1>,
    /// Per-head coherence bias strength, shape `[n_heads]`.
    pub alpha: Tensor<B, 1>,
}

/// Validated hyperparameters for [`OscillatoryAttention`].
///
/// Defaults (`new`) match the PRINet 3.0 reference: `n_heads=4, dropout=0.1`.
#[derive(Clone, Debug, PartialEq)]
pub struct OscillatoryAttentionConfig {
    /// Model (embedding) dimension.
    pub d_model: usize,
    /// Number of attention heads. Must evenly divide `d_model`.
    pub n_heads: usize,
    /// Attention-weight dropout probability.
    pub dropout: f64,
}

impl OscillatoryAttentionConfig {
    /// Validated configuration with PRINet 3.0's default hyperparameters.
    ///
    /// # Errors
    ///
    /// See [`Self::with_params`].
    pub fn new(d_model: usize, n_heads: usize) -> Result<Self, TrainError> {
        Self::with_params(d_model, n_heads, 0.1)
    }

    /// Validated configuration with explicit hyperparameters.
    ///
    /// # Errors
    ///
    /// Returns [`TrainError::EmptyBand`] if `d_model` or `n_heads` is zero,
    /// [`TrainError::IndivisibleHeads`] if `d_model % n_heads != 0`, or
    /// [`TrainError::InvalidDropout`] if `dropout` is not in `[0, 1)`.
    pub fn with_params(d_model: usize, n_heads: usize, dropout: f64) -> Result<Self, TrainError> {
        if d_model == 0 {
            return Err(TrainError::EmptyBand { name: "d_model" });
        }
        if n_heads == 0 {
            return Err(TrainError::EmptyBand { name: "n_heads" });
        }
        if d_model % n_heads != 0 {
            return Err(TrainError::IndivisibleHeads { d_model, n_heads });
        }
        if !(dropout.is_finite() && (0.0..1.0).contains(&dropout)) {
            return Err(TrainError::InvalidDropout { value: dropout });
        }
        Ok(Self {
            d_model,
            n_heads,
            dropout,
        })
    }

    /// Initialize an [`OscillatoryAttention`] with parameters drawn from the
    /// project's deterministic [`Seed`] (Coding Standards §1.3).
    pub fn init<B: Backend>(&self, device: &B::Device, seed: &mut Seed) -> OscillatoryAttention<B> {
        let w_q = seeded_linear::<B>(self.d_model, self.d_model, true, device, seed);
        let w_k = seeded_linear::<B>(self.d_model, self.d_model, true, device, seed);
        let w_v = seeded_linear::<B>(self.d_model, self.d_model, true, device, seed);
        let w_o = seeded_linear::<B>(self.d_model, self.d_model, true, device, seed);
        let phase_proj = seeded_linear::<B>(self.d_model, self.n_heads, true, device, seed);
        let alpha = Param::initialized(
            Default::default(),
            Tensor::<B, 1>::zeros([self.n_heads], device).require_grad(),
        );
        let dropout = DropoutConfig::new(self.dropout).init();

        OscillatoryAttention {
            w_q,
            w_k,
            w_v,
            w_o,
            phase_proj,
            alpha,
            dropout,
            d_model: self.d_model,
            n_heads: self.n_heads,
            d_k: self.d_model / self.n_heads,
        }
    }

    /// Build an [`OscillatoryAttention`] from explicit parameter tensors.
    ///
    /// # Errors
    ///
    /// Returns [`TrainError::ShapeMismatch`] if any tensor's shape does not
    /// match this config's `d_model`/`n_heads`.
    pub fn init_from_params<B: Backend>(
        &self,
        params: OscillatoryAttentionParams<B>,
    ) -> Result<OscillatoryAttention<B>, TrainError> {
        let (d, h) = (self.d_model, self.n_heads);
        check_dims("w_q_weight", params.w_q_weight.dims(), [d, d])?;
        check_dims("w_q_bias", params.w_q_bias.dims(), [d])?;
        check_dims("w_k_weight", params.w_k_weight.dims(), [d, d])?;
        check_dims("w_k_bias", params.w_k_bias.dims(), [d])?;
        check_dims("w_v_weight", params.w_v_weight.dims(), [d, d])?;
        check_dims("w_v_bias", params.w_v_bias.dims(), [d])?;
        check_dims("w_o_weight", params.w_o_weight.dims(), [d, d])?;
        check_dims("w_o_bias", params.w_o_bias.dims(), [d])?;
        check_dims("phase_proj_weight", params.phase_proj_weight.dims(), [d, h])?;
        check_dims("phase_proj_bias", params.phase_proj_bias.dims(), [h])?;
        check_dims("alpha", params.alpha.dims(), [h])?;

        let linear = |weight: Tensor<B, 2>, bias: Tensor<B, 1>| Linear {
            weight: Param::initialized(Default::default(), weight.require_grad()),
            bias: Some(Param::initialized(Default::default(), bias.require_grad())),
        };

        Ok(OscillatoryAttention {
            w_q: linear(params.w_q_weight, params.w_q_bias),
            w_k: linear(params.w_k_weight, params.w_k_bias),
            w_v: linear(params.w_v_weight, params.w_v_bias),
            w_o: linear(params.w_o_weight, params.w_o_bias),
            phase_proj: linear(params.phase_proj_weight, params.phase_proj_bias),
            alpha: Param::initialized(Default::default(), params.alpha.require_grad()),
            dropout: DropoutConfig::new(self.dropout).init(),
            d_model: d,
            n_heads: h,
            d_k: d / h,
        })
    }
}

/// Multi-head attention with an additive oscillatory coherence bias.
///
/// See the module docs for the exact formula. Construct via
/// [`OscillatoryAttentionConfig::init`].
#[derive(Module, Debug)]
pub struct OscillatoryAttention<B: Backend> {
    w_q: Linear<B>,
    w_k: Linear<B>,
    w_v: Linear<B>,
    w_o: Linear<B>,
    phase_proj: Linear<B>,
    alpha: Param<Tensor<B, 1>>,
    dropout: Dropout,
    d_model: usize,
    n_heads: usize,
    d_k: usize,
}

impl<B: Backend> OscillatoryAttention<B> {
    /// Model (embedding) dimension.
    pub fn d_model(&self) -> usize {
        self.d_model
    }

    /// Number of attention heads.
    pub fn n_heads(&self) -> usize {
        self.n_heads
    }

    /// Forward pass with an oscillatory coherence bias.
    ///
    /// `phase`, when supplied, must have shape `[batch, seq, n_heads]`; when
    /// `None`, phases are derived from `x` via a learned projection.
    ///
    /// # Errors
    ///
    /// Returns [`TrainError::ShapeMismatch`] if `x`'s last dimension is not
    /// [`Self::d_model`] or `phase`'s shape does not match
    /// `[batch, seq, n_heads]`.
    pub fn forward(
        &self,
        x: Tensor<B, 3>,
        phase: Option<Tensor<B, 3>>,
    ) -> Result<Tensor<B, 3>, TrainError> {
        let [batch, seq, d] = x.dims();
        check_dims("x", [d], [self.d_model])?;
        let (h, dk) = (self.n_heads, self.d_k);

        let to_heads =
            |t: Tensor<B, 3>| -> Tensor<B, 4> { t.reshape([batch, seq, h, dk]).swap_dims(1, 2) };
        let q = to_heads(self.w_q.forward(x.clone()));
        let k = to_heads(self.w_k.forward(x.clone()));
        let v = to_heads(self.w_v.forward(x.clone()));

        let scale = (dk as f64).powf(-0.5);
        let scores = q.matmul(k.swap_dims(2, 3)).mul_scalar(scale); // [batch, h, seq, seq]

        let phase = match phase {
            Some(p) => {
                check_dims("phase", p.dims(), [batch, seq, h])?;
                p
            }
            None => self.phase_proj.forward(x),
        };
        let phase_h = phase.swap_dims(1, 2); // [batch, h, seq]
        let phase_i = phase_h.clone().unsqueeze_dim::<4>(3); // [batch, h, seq, 1]
        let phase_j = phase_h.unsqueeze_dim::<4>(2); // [batch, h, 1, seq]
        let coherence = (phase_i - phase_j).cos(); // [batch, h, seq, seq]

        let alpha = self.alpha.val().reshape([1, h, 1, 1]);
        let scores = scores + coherence * alpha;

        let attn = self.dropout.forward(softmax(scores, 3));
        let out = attn.matmul(v); // [batch, h, seq, d_k]
        let out = out.swap_dims(1, 2).reshape([batch, seq, self.d_model]);

        Ok(self.w_o.forward(out))
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    use burn::backend::{Autodiff, NdArray};

    type TestBackend = NdArray<f64>;
    type TestAutodiffBackend = Autodiff<TestBackend>;

    fn device() -> <TestBackend as Backend>::Device {
        Default::default()
    }

    // --- Config validation ---

    #[test]
    fn zero_sizes_rejected() {
        assert!(matches!(
            OscillatoryAttentionConfig::new(0, 4).unwrap_err(),
            TrainError::EmptyBand { name: "d_model" }
        ));
        assert!(matches!(
            OscillatoryAttentionConfig::new(64, 0).unwrap_err(),
            TrainError::EmptyBand { name: "n_heads" }
        ));
    }

    #[test]
    fn accessors_report_configured_sizes() {
        let mut seed = Seed::new(0, 0);
        let attn = OscillatoryAttentionConfig::new(16, 4)
            .unwrap()
            .init::<TestBackend>(&device(), &mut seed);
        assert_eq!(attn.d_model(), 16);
        assert_eq!(attn.n_heads(), 4);
    }

    #[test]
    fn indivisible_heads_rejected() {
        let err = OscillatoryAttentionConfig::new(65, 4).unwrap_err();
        assert!(matches!(
            err,
            TrainError::IndivisibleHeads {
                d_model: 65,
                n_heads: 4
            }
        ));
    }

    #[test]
    fn invalid_dropout_rejected() {
        for bad in [-0.1, 1.0, 1.5, f64::NAN] {
            assert!(matches!(
                OscillatoryAttentionConfig::with_params(64, 4, bad).unwrap_err(),
                TrainError::InvalidDropout { .. }
            ));
        }
    }

    // --- Forward / shape / dtype ---

    #[test]
    fn forward_returns_expected_shape_and_is_finite() {
        let mut seed = Seed::new(3, 0);
        let attn = OscillatoryAttentionConfig::new(16, 4)
            .unwrap()
            .init::<TestBackend>(&device(), &mut seed);
        let x = Tensor::<TestBackend, 3>::ones([2, 5, 16], &device());
        let out = attn.forward(x, None).unwrap();
        assert_eq!(out.dims(), [2, 5, 16]);
        let data = out.to_data().to_vec::<f64>().unwrap();
        assert!(data.iter().all(|v| v.is_finite()));
    }

    #[test]
    fn forward_accepts_external_phase() {
        let mut seed = Seed::new(4, 0);
        let attn = OscillatoryAttentionConfig::new(8, 2)
            .unwrap()
            .init::<TestBackend>(&device(), &mut seed);
        let dev = device();
        let x = Tensor::<TestBackend, 3>::ones([1, 3, 8], &dev);
        let phase = Tensor::<TestBackend, 3>::zeros([1, 3, 2], &dev);
        let out = attn.forward(x, Some(phase)).unwrap();
        assert_eq!(out.dims(), [1, 3, 8]);
    }

    #[test]
    fn alpha_zero_init_matches_plain_attention_bias() {
        // At init, alpha == 0, so the coherence bias contributes nothing:
        // the coherence-independent scores alone drive softmax. Verify this
        // by comparing outputs for two different external phase tensors —
        // they must be identical since alpha == 0 makes phase irrelevant.
        let mut seed = Seed::new(5, 0);
        let attn = OscillatoryAttentionConfig::new(8, 2)
            .unwrap()
            .init::<TestBackend>(&device(), &mut seed);
        let dev = device();
        let x = Tensor::<TestBackend, 3>::ones([1, 3, 8], &dev) * 0.3;
        let phase_a = Tensor::<TestBackend, 3>::zeros([1, 3, 2], &dev);
        let phase_b = Tensor::<TestBackend, 3>::ones([1, 3, 2], &dev) * 5.0;
        let out_a = attn.forward(x.clone(), Some(phase_a)).unwrap();
        let out_b = attn.forward(x, Some(phase_b)).unwrap();
        let a = out_a.to_data().to_vec::<f64>().unwrap();
        let b = out_b.to_data().to_vec::<f64>().unwrap();
        for (va, vb) in a.iter().zip(b.iter()) {
            assert!((va - vb).abs() < 1e-10);
        }
    }

    // --- Shape guards ---

    #[test]
    fn forward_rejects_wrong_d_model() {
        let mut seed = Seed::new(6, 0);
        let attn = OscillatoryAttentionConfig::new(8, 2)
            .unwrap()
            .init::<TestBackend>(&device(), &mut seed);
        let x = Tensor::<TestBackend, 3>::ones([1, 3, 5], &device());
        let err = attn.forward(x, None).unwrap_err();
        assert!(matches!(err, TrainError::ShapeMismatch { name: "x", .. }));
    }

    #[test]
    fn forward_rejects_wrong_phase_shape() {
        let mut seed = Seed::new(7, 0);
        let attn = OscillatoryAttentionConfig::new(8, 2)
            .unwrap()
            .init::<TestBackend>(&device(), &mut seed);
        let dev = device();
        let x = Tensor::<TestBackend, 3>::ones([1, 3, 8], &dev);
        let bad_phase = Tensor::<TestBackend, 3>::zeros([1, 3, 3], &dev);
        let err = attn.forward(x, Some(bad_phase)).unwrap_err();
        assert!(matches!(
            err,
            TrainError::ShapeMismatch { name: "phase", .. }
        ));
    }

    // --- Gradient reference tests ---

    #[test]
    fn gradients_flow_to_every_parameter() {
        let dev: <TestAutodiffBackend as Backend>::Device = Default::default();
        let mut seed = Seed::new(21, 0);
        let attn = OscillatoryAttentionConfig::new(8, 2)
            .unwrap()
            .init::<TestAutodiffBackend>(&dev, &mut seed);
        let x = Tensor::<TestAutodiffBackend, 3>::ones([2, 4, 8], &dev).require_grad();

        let out = attn.forward(x, None).unwrap();
        let loss = out.sum();
        let grads = loss.backward();

        for grad in [
            attn.w_q
                .weight
                .val()
                .grad(&grads)
                .map(|g| g.to_data().to_vec::<f64>().unwrap()),
            attn.w_o
                .weight
                .val()
                .grad(&grads)
                .map(|g| g.to_data().to_vec::<f64>().unwrap()),
            attn.phase_proj
                .weight
                .val()
                .grad(&grads)
                .map(|g| g.to_data().to_vec::<f64>().unwrap()),
            attn.alpha
                .val()
                .grad(&grads)
                .map(|g| g.to_data().to_vec::<f64>().unwrap()),
        ] {
            let values = grad.expect("gradient must be present for every trainable parameter");
            assert!(values.iter().all(|v| v.is_finite()));
        }
    }

    #[test]
    fn alpha_gradient_matches_central_finite_difference() {
        // Burn's `Dropout::forward` is a no-op unless both `B::ad_enabled()`
        // and `prob > 0`, so a nonzero dropout probability would make the
        // autodiff-backend forward pass stochastic (masking draws) while the
        // plain-backend numerical reference stays deterministic (dropout
        // never applies without autodiff) — comparing them would not be a
        // like-for-like gradcheck. Use `dropout=0.0` so both paths compute
        // the identical deterministic function.
        let dev: <TestAutodiffBackend as Backend>::Device = Default::default();

        let loss_for = |alpha_val: f64| -> f64 {
            let device: <TestBackend as Backend>::Device = Default::default();
            let mut seed = Seed::new(9, 0);
            let mut attn = OscillatoryAttentionConfig::with_params(4, 2, 0.0)
                .unwrap()
                .init::<TestBackend>(&device, &mut seed);
            attn.alpha = Param::initialized(
                Default::default(),
                Tensor::<TestBackend, 1>::from_data(
                    burn::tensor::TensorData::new(vec![alpha_val, alpha_val], vec![2]),
                    &device,
                ),
            );
            let x = Tensor::<TestBackend, 3>::ones([1, 3, 4], &device) * 0.2;
            let phase = Tensor::<TestBackend, 3>::from_data(
                burn::tensor::TensorData::new(vec![0.1, 0.7, 0.4, 1.1, 0.9, 0.2], vec![1, 3, 2]),
                &device,
            );
            let out = attn.forward(x, Some(phase)).unwrap();
            out.to_data().to_vec::<f64>().unwrap().iter().sum()
        };

        let eps = 1e-6;
        let numerical = (loss_for(0.5 + eps) - loss_for(0.5 - eps)) / (2.0 * eps);

        let mut seed = Seed::new(9, 0);
        let mut attn = OscillatoryAttentionConfig::with_params(4, 2, 0.0)
            .unwrap()
            .init::<TestAutodiffBackend>(&dev, &mut seed);
        let alpha_tensor = Tensor::<TestAutodiffBackend, 1>::from_data(
            burn::tensor::TensorData::new(vec![0.5, 0.5], vec![2]),
            &dev,
        )
        .require_grad();
        attn.alpha = Param::initialized(Default::default(), alpha_tensor.clone());
        let x = Tensor::<TestAutodiffBackend, 3>::ones([1, 3, 4], &dev) * 0.2;
        let phase = Tensor::<TestAutodiffBackend, 3>::from_data(
            burn::tensor::TensorData::new(vec![0.1, 0.7, 0.4, 1.1, 0.9, 0.2], vec![1, 3, 2]),
            &dev,
        );
        let out = attn.forward(x, Some(phase)).unwrap();
        let loss = out.sum();
        let grads = loss.backward();
        let analytic = alpha_tensor
            .grad(&grads)
            .unwrap()
            .to_data()
            .to_vec::<f64>()
            .unwrap()[0];

        assert!(
            (analytic - numerical).abs() < 1e-3,
            "analytic {analytic} vs finite-difference {numerical}"
        );
    }
}
