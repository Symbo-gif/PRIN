//! Hybrid oscillator + attention architecture — the canonical Phase-4
//! classification model.
//!
//! [`HybridPRINetV2`] is the Burn `Module` rebuild of PRINet 3.0's
//! `nn.hybrid.HybridPRINetV2`: input features are projected to a token
//! sequence, an adaptive oscillator phase is derived from the same input and
//! evolved through [`crate::bands::DiscreteDeltaThetaGamma`] dynamics each
//! layer, and [`crate::attention::OscillatoryAttention`] biases every
//! attention layer toward phase-aligned tokens.
//!
//! # Correspondence to the PRINet 3.0 reference
//!
//! ```text
//! h          = input_proj(x).view(B, n_tokens, d_model)
//! φ₀         = wrap(phase_init(x).view(B, n_tokens, n_heads))
//! (dyn_φ, a) = (mean_h(φ₀), ones(B, n_osc))
//! for layer in 0..n_layers:
//!     (dyn_φ, a) = DiscreteDeltaThetaGamma.integrate(dyn_φ, a, n_discrete_steps, dt=0.01)
//!     token_φ    = dyn_φ.unsqueeze(-1).expand(B, n_tokens, n_heads)
//!     h          = h + OscillatoryAttention(norm1(h), phase=token_φ)
//!     h          = h + FFN(norm2(h))
//! logits     = classifier(pool_norm(mean_tokens(h))).clamp(±50)
//! out        = log_softmax(logits)
//! ```
//!
//! This is a line-for-line port of `HybridPRINetV2.forward` (`nn/hybrid.py`).
//! `n_tokens == n_osc_total` always in v2 (the reference's own "adaptive
//! token count" design point), so no fixed-padding interpolation is needed.
//!
//! **Not ported — `use_conv_stem`.** The reference's optional CNN stem
//! (`Conv2d`→`BatchNorm2d`→`ReLU` ×2 →`AdaptiveAvgPool2d`→`Flatten`) targets
//! 2D image inputs (CIFAR-10/Fashion-MNIST benchmarks) — a separate input
//! modality from this WP's oscillatory-binding scope (temporal CLEVR-N,
//! MOT). No caller in this WP exercises it and porting it would add an
//! entire, separately-testable image-preprocessing surface with zero
//! coverage. Recorded as an explicit out-of-scope discovery for a future WP
//! that needs the image-classification benchmarks; this port always takes
//! the flat-vector `x: [batch, n_input]` path (the reference's own primary
//! documented usage). `torch.compile`/`oscillatory_parameters`/
//! `rate_coded_parameters` introspection helpers are Python/`torch`-runtime
//! concerns with no Burn equivalent and are likewise not ported.
//!
//! Standard transformer plumbing (`Linear`/`LayerNorm`/`Dropout`/`Gelu`) uses
//! [`burn::nn`], weights seeded via `crate::support::seeded_linear` — see
//! [`crate::attention`]'s module docs for why.
//!
//! # Example
//!
//! ```
//! use burn::backend::NdArray;
//! use burn::tensor::Tensor;
//! use prin_dynamics::Seed;
//! use prin_train::hybrid::HybridPRINetV2Config;
//!
//! type Backend = NdArray<f32>;
//!
//! let cfg = HybridPRINetV2Config::new(128, 10).unwrap();
//! let device = Default::default();
//! let mut seed = Seed::new(0, 0);
//! let model = cfg.init::<Backend>(&device, &mut seed);
//!
//! let x = Tensor::<Backend, 2>::ones([8, 128], &device);
//! let log_probs = model.forward(x).unwrap();
//! assert_eq!(log_probs.dims(), [8, 10]);
//! ```

use burn::module::Module;
use burn::nn::{Dropout, DropoutConfig, LayerNorm, LayerNormConfig, Linear};
use burn::tensor::activation::{gelu, log_softmax};
use burn::tensor::backend::Backend;
use burn::tensor::Tensor;
use prin_dynamics::Seed;

use crate::attention::{OscillatoryAttention, OscillatoryAttentionConfig};
use crate::bands::{DiscreteBandState, DiscreteDeltaThetaGamma, DiscreteDeltaThetaGammaConfig};
use crate::error::TrainError;
use crate::support::{check_dims, seeded_linear};

/// Logit clamp before `log_softmax`, matching PRINet 3.0's `_LOGIT_CLAMP`.
const LOGIT_CLAMP: f64 = 50.0;
const FIXED_DT: f64 = 0.01;

/// Validated hyperparameters for [`HybridPRINetV2`].
///
/// Defaults (`new`) match the PRINet 3.0 reference: `d_model=64, n_heads=4,
/// n_layers=2, dropout=0.1, n_delta=4, n_theta=8, n_gamma=32,
/// n_discrete_steps=5, coupling_strength=2.0, pac_depth=0.3`.
#[derive(Clone, Debug, PartialEq)]
pub struct HybridPRINetV2Config {
    /// Input feature dimension.
    pub n_input: usize,
    /// Number of output classes.
    pub n_classes: usize,
    /// Model dimension for attention/FFN layers.
    pub d_model: usize,
    /// Number of attention heads.
    pub n_heads: usize,
    /// Number of interleaved attention+FFN blocks.
    pub n_layers: usize,
    /// Dropout rate.
    pub dropout: f64,
    /// Delta-band oscillators.
    pub n_delta: usize,
    /// Theta-band oscillators.
    pub n_theta: usize,
    /// Gamma-band oscillators.
    pub n_gamma: usize,
    /// Discrete dynamics steps per layer.
    pub n_discrete_steps: usize,
    /// Initial intra-band coupling strength.
    pub coupling_strength: f64,
    /// Initial PAC modulation depth.
    pub pac_depth: f64,
}

impl HybridPRINetV2Config {
    /// Validated configuration with PRINet 3.0's default hyperparameters.
    ///
    /// # Errors
    ///
    /// See [`Self::with_params`].
    pub fn new(n_input: usize, n_classes: usize) -> Result<Self, TrainError> {
        Self::with_params(n_input, n_classes, 64, 4, 2, 0.1, 4, 8, 32, 5, 2.0, 0.3)
    }

    /// Validated configuration with explicit hyperparameters.
    ///
    /// # Errors
    ///
    /// Returns [`TrainError::EmptyBand`] if `n_input`, `n_classes`,
    /// `n_layers`, or any band size is zero, [`TrainError::IndivisibleHeads`]
    /// if `d_model % n_heads != 0`, [`TrainError::InvalidDropout`] if
    /// `dropout` is not in `[0, 1)`, or [`TrainError::InvalidStepCount`] if
    /// `n_discrete_steps` is zero.
    #[allow(clippy::too_many_arguments)]
    pub fn with_params(
        n_input: usize,
        n_classes: usize,
        d_model: usize,
        n_heads: usize,
        n_layers: usize,
        dropout: f64,
        n_delta: usize,
        n_theta: usize,
        n_gamma: usize,
        n_discrete_steps: usize,
        coupling_strength: f64,
        pac_depth: f64,
    ) -> Result<Self, TrainError> {
        if n_input == 0 {
            return Err(TrainError::EmptyBand { name: "n_input" });
        }
        if n_classes == 0 {
            return Err(TrainError::EmptyBand { name: "n_classes" });
        }
        if n_layers == 0 {
            return Err(TrainError::EmptyBand { name: "n_layers" });
        }
        // Validates d_model/n_heads/dropout together with EmptyBand/IndivisibleHeads.
        let _ = OscillatoryAttentionConfig::with_params(d_model, n_heads, dropout)?;
        let _ = DiscreteDeltaThetaGammaConfig::with_params(
            n_delta,
            n_theta,
            n_gamma,
            coupling_strength,
            pac_depth,
            2.0,
            6.0,
            40.0,
        )?;
        if n_discrete_steps == 0 {
            return Err(TrainError::InvalidStepCount {
                name: "n_discrete_steps",
                value: n_discrete_steps,
            });
        }
        Ok(Self {
            n_input,
            n_classes,
            d_model,
            n_heads,
            n_layers,
            dropout,
            n_delta,
            n_theta,
            n_gamma,
            n_discrete_steps,
            coupling_strength,
            pac_depth,
        })
    }

    /// Total oscillator count (`== n_tokens` in v2's adaptive-token design).
    pub fn n_tokens(&self) -> usize {
        self.n_delta + self.n_theta + self.n_gamma
    }

    /// Initialize a [`HybridPRINetV2`] with parameters drawn from the
    /// project's deterministic [`Seed`] (Coding Standards §1.3).
    pub fn init<B: Backend>(&self, device: &B::Device, seed: &mut Seed) -> HybridPRINetV2<B> {
        let n_tokens = self.n_tokens();
        let d = self.d_model;

        let input_proj = seeded_linear::<B>(self.n_input, n_tokens * d, true, device, seed);
        let phase_init =
            seeded_linear::<B>(self.n_input, n_tokens * self.n_heads, true, device, seed);
        let dynamics = DiscreteDeltaThetaGammaConfig::with_params(
            self.n_delta,
            self.n_theta,
            self.n_gamma,
            self.coupling_strength,
            self.pac_depth,
            2.0,
            6.0,
            40.0,
        )
        .expect("hyperparameters already validated by HybridPRINetV2Config::with_params")
        .init::<B>(device, seed);

        let attn_cfg = OscillatoryAttentionConfig::with_params(d, self.n_heads, self.dropout)
            .expect("hyperparameters already validated by HybridPRINetV2Config::with_params");
        let mut attn_layers = Vec::with_capacity(self.n_layers);
        let mut ffn_layers = Vec::with_capacity(self.n_layers);
        let mut norm1_layers = Vec::with_capacity(self.n_layers);
        let mut norm2_layers = Vec::with_capacity(self.n_layers);
        for _ in 0..self.n_layers {
            attn_layers.push(attn_cfg.init::<B>(device, seed));
            ffn_layers.push([
                seeded_linear::<B>(d, d * 4, true, device, seed),
                seeded_linear::<B>(d * 4, d, true, device, seed),
            ]);
            norm1_layers.push(LayerNormConfig::new(d).init::<B>(device));
            norm2_layers.push(LayerNormConfig::new(d).init::<B>(device));
        }

        let pool_norm = LayerNormConfig::new(d).init::<B>(device);
        let classifier = [
            seeded_linear::<B>(d, d, true, device, seed),
            seeded_linear::<B>(d, self.n_classes, true, device, seed),
        ];
        let dropout = DropoutConfig::new(self.dropout).init();

        HybridPRINetV2 {
            input_proj,
            phase_init,
            dynamics,
            attn_layers,
            ffn_layers,
            norm1_layers,
            norm2_layers,
            pool_norm,
            classifier,
            dropout,
            n_input: self.n_input,
            n_classes: self.n_classes,
            d_model: d,
            n_heads: self.n_heads,
            n_layers: self.n_layers,
            n_tokens,
            n_discrete_steps: self.n_discrete_steps,
        }
    }
}

/// Hybrid oscillator + attention architecture (PRIN's canonical
/// classification model).
///
/// See the module docs for the exact formula. Construct via
/// [`HybridPRINetV2Config::init`].
#[derive(Module, Debug)]
pub struct HybridPRINetV2<B: Backend> {
    input_proj: Linear<B>,
    phase_init: Linear<B>,
    dynamics: DiscreteDeltaThetaGamma<B>,
    attn_layers: Vec<OscillatoryAttention<B>>,
    ffn_layers: Vec<[Linear<B>; 2]>,
    norm1_layers: Vec<LayerNorm<B>>,
    norm2_layers: Vec<LayerNorm<B>>,
    pool_norm: LayerNorm<B>,
    classifier: [Linear<B>; 2],
    dropout: Dropout,
    n_input: usize,
    n_classes: usize,
    d_model: usize,
    n_heads: usize,
    n_layers: usize,
    n_tokens: usize,
    n_discrete_steps: usize,
}

impl<B: Backend> HybridPRINetV2<B> {
    /// Input feature dimension.
    pub fn n_input(&self) -> usize {
        self.n_input
    }

    /// Number of output classes.
    pub fn n_classes(&self) -> usize {
        self.n_classes
    }

    /// Total oscillator/token count.
    pub fn n_tokens(&self) -> usize {
        self.n_tokens
    }

    fn ffn_forward(&self, layer: usize, x: Tensor<B, 3>) -> Tensor<B, 3> {
        let [w1, w2] = &self.ffn_layers[layer];
        let h = self.dropout.forward(gelu(w1.forward(x)));
        self.dropout.forward(w2.forward(h))
    }

    /// Forward pass: project `x` to a token sequence, evolve adaptive
    /// oscillator phase through `n_layers` interleaved
    /// attention+FFN blocks, pool, and classify.
    ///
    /// # Errors
    ///
    /// Returns [`TrainError::ShapeMismatch`] if `x`'s width is not
    /// [`Self::n_input`]. See [`crate::bands::DiscreteDeltaThetaGamma::integrate`]
    /// and [`crate::attention::OscillatoryAttention::forward`] for further
    /// error conditions.
    pub fn forward(&self, x: Tensor<B, 2>) -> Result<Tensor<B, 2>, TrainError> {
        let batch = x.dims()[0];
        check_dims("x", [x.dims()[1]], [self.n_input])?;
        let (n_tokens, d, h_count) = (self.n_tokens, self.d_model, self.n_heads);
        let device = x.device();

        let mut h = self
            .input_proj
            .forward(x.clone())
            .reshape([batch, n_tokens, d]);
        let phase_init_raw = self
            .phase_init
            .forward(x)
            .reshape([batch, n_tokens, h_count]);
        let phase_state = phase_init_raw.remainder_scalar(std::f64::consts::TAU);

        let mut amp_state = Tensor::<B, 2>::ones([batch, n_tokens], &device);
        let mut dyn_phase = phase_state.mean_dim(2).squeeze::<2>(2);

        for i in 0..self.n_layers {
            let state = DiscreteBandState::new(dyn_phase, amp_state)?;
            let evolved = self
                .dynamics
                .integrate(state, self.n_discrete_steps, FIXED_DT)?;
            let (new_phase, new_amp) = evolved.into_parts();
            dyn_phase = new_phase;
            amp_state = new_amp;

            let token_phase = dyn_phase
                .clone()
                .unsqueeze_dim::<3>(2)
                .repeat_dim(2, h_count);

            let h_norm = self.norm1_layers[i].forward(h.clone());
            let attn_out = self.attn_layers[i].forward(h_norm, Some(token_phase))?;
            h = h + attn_out;

            let h_norm2 = self.norm2_layers[i].forward(h.clone());
            let ffn_out = self.ffn_forward(i, h_norm2);
            h = h + ffn_out;
        }

        let pooled = self.pool_norm.forward(h.mean_dim(1).squeeze::<2>(1));
        let logits = self.classifier[1].forward(self.classifier[0].forward(pooled));
        let logits = logits.clamp(-LOGIT_CLAMP, LOGIT_CLAMP);
        Ok(log_softmax(logits, 1))
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

    fn small_config() -> HybridPRINetV2Config {
        HybridPRINetV2Config::with_params(8, 3, 8, 2, 2, 0.0, 1, 1, 2, 2, 2.0, 0.3).unwrap()
    }

    fn seeded_model<B: Backend>(device: &B::Device) -> HybridPRINetV2<B> {
        let mut seed = Seed::new(11, 0);
        small_config().init(device, &mut seed)
    }

    // --- Config validation ---

    #[test]
    fn zero_sizes_rejected() {
        assert!(matches!(
            HybridPRINetV2Config::new(0, 3).unwrap_err(),
            TrainError::EmptyBand { name: "n_input" }
        ));
        assert!(matches!(
            HybridPRINetV2Config::new(8, 0).unwrap_err(),
            TrainError::EmptyBand { name: "n_classes" }
        ));
    }

    #[test]
    fn zero_layers_rejected() {
        let err = HybridPRINetV2Config::with_params(8, 3, 8, 2, 0, 0.1, 1, 1, 2, 2, 2.0, 0.3)
            .unwrap_err();
        assert!(matches!(err, TrainError::EmptyBand { name: "n_layers" }));
    }

    #[test]
    fn indivisible_heads_rejected() {
        let err = HybridPRINetV2Config::with_params(8, 3, 9, 2, 1, 0.1, 1, 1, 2, 2, 2.0, 0.3)
            .unwrap_err();
        assert!(matches!(err, TrainError::IndivisibleHeads { .. }));
    }

    // --- Construction ---

    #[test]
    fn seeded_init_produces_expected_sizes() {
        let model = seeded_model::<TestBackend>(&device());
        assert_eq!(model.n_input(), 8);
        assert_eq!(model.n_classes(), 3);
        assert_eq!(model.n_tokens(), 4);
    }

    #[test]
    fn same_seed_gives_identical_parameters() {
        let mut s1 = Seed::new(5, 0);
        let mut s2 = Seed::new(5, 0);
        let m1 = small_config().init::<TestBackend>(&device(), &mut s1);
        let m2 = small_config().init::<TestBackend>(&device(), &mut s2);
        let w1 = m1
            .input_proj
            .weight
            .val()
            .to_data()
            .to_vec::<f64>()
            .unwrap();
        let w2 = m2
            .input_proj
            .weight
            .val()
            .to_data()
            .to_vec::<f64>()
            .unwrap();
        assert_eq!(w1, w2);
    }

    // --- Forward / shape / dtype ---

    #[test]
    fn forward_returns_log_probabilities() {
        let model = seeded_model::<TestBackend>(&device());
        let dev = device();
        let x = Tensor::<TestBackend, 2>::ones([2, 8], &dev) * 0.3;
        let log_probs = model.forward(x).unwrap();
        assert_eq!(log_probs.dims(), [2, 3]);
        let data = log_probs.to_data().to_vec::<f64>().unwrap();
        assert!(data.iter().all(|v| v.is_finite() && *v <= 0.0));
        // log_softmax rows sum (in probability space) to 1.
        for row in data.chunks(3) {
            let sum: f64 = row.iter().map(|v| v.exp()).sum();
            assert!((sum - 1.0).abs() < 1e-8, "row sum {sum} not ~1.0");
        }
    }

    #[test]
    fn forward_rejects_wrong_input_dim() {
        let model = seeded_model::<TestBackend>(&device());
        let x = Tensor::<TestBackend, 2>::ones([2, 5], &device());
        let err = model.forward(x).unwrap_err();
        assert!(matches!(err, TrainError::ShapeMismatch { name: "x", .. }));
    }

    // --- Gradient reference tests ---

    #[test]
    fn gradients_flow_to_every_layer_class() {
        let dev: <TestAutodiffBackend as Backend>::Device = Default::default();
        let mut seed = Seed::new(21, 0);
        let model = small_config().init::<TestAutodiffBackend>(&dev, &mut seed);
        let x = Tensor::<TestAutodiffBackend, 2>::ones([2, 8], &dev).require_grad() * 0.3;

        let out = model.forward(x).unwrap();
        let loss = out.sum();
        let grads = loss.backward();

        for grad in [
            model
                .input_proj
                .weight
                .val()
                .grad(&grads)
                .map(|g| g.to_data().to_vec::<f64>().unwrap()),
            model
                .phase_init
                .weight
                .val()
                .grad(&grads)
                .map(|g| g.to_data().to_vec::<f64>().unwrap()),
            model.classifier[0]
                .weight
                .val()
                .grad(&grads)
                .map(|g| g.to_data().to_vec::<f64>().unwrap()),
            model.ffn_layers[0][0]
                .weight
                .val()
                .grad(&grads)
                .map(|g| g.to_data().to_vec::<f64>().unwrap()),
        ] {
            let values = grad.expect("gradient must be present for every trainable parameter");
            assert!(values.iter().all(|v| v.is_finite()));
        }
    }

    // --- Serialization ---

    #[test]
    fn record_roundtrip_preserves_parameters() {
        use burn::record::{BinBytesRecorder, DoublePrecisionSettings, Recorder};

        let dev = device();
        let model = seeded_model::<TestBackend>(&dev);
        let before = model
            .input_proj
            .weight
            .val()
            .to_data()
            .to_vec::<f64>()
            .unwrap();

        let recorder = BinBytesRecorder::<DoublePrecisionSettings>::default();
        let bytes =
            Recorder::<TestBackend>::record(&recorder, model.clone().into_record(), ()).unwrap();
        let record = Recorder::<TestBackend>::load(&recorder, bytes, &dev).unwrap();
        let restored = model.load_record(record);

        let after = restored
            .input_proj
            .weight
            .val()
            .to_data()
            .to_vec::<f64>()
            .unwrap();
        assert_eq!(before, after);
        assert_eq!(restored.n_tokens(), 4);
    }
}
