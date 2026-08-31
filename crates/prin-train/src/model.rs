//! Full trainable PRINet model container.
//!
//! [`PRINetModel`] is the Burn `Module` rebuild of PRINet 3.0's
//! `nn.layers.PRINetModel`: an input [`crate::layers::ResonanceLayer`], a stack
//! of `n_layers - 1` further `ResonanceLayer`s, a `LayerNorm` after every
//! resonance layer, a learned concept-readout [`burn::nn::Linear`], a logit
//! clamp to `[-50, 50]`, and a final `log_softmax` over the concept axis.
//!
//! # Correspondence to the PRINet 3.0 reference
//!
//! [`PRINetModel::forward`] is a line-for-line port of `PRINetModel.forward`
//! (`nn/layers.py`) for a single dtype:
//!
//! ```text
//! h = input_layer(x)                     # [batch, n_resonances]
//! h = layer_norms[0](h)
//! for i, layer in enumerate(layers):     # n_layers - 1 stacked layers
//!     h = layer(h)
//!     h = layer_norms[i + 1](h)
//! logits = concept_proj(h)               # [batch, n_concepts]
//! logits = clamp(logits, -50.0, 50.0)
//! log_probs = log_softmax(logits, dim=-1)
//! ```
//!
//! **Documented deviation — mixed precision.** PRINet 3.0's `forward` casts the
//! post-resonance hidden state to `float32` (`h = h.float()`) before the
//! readout, unconditionally, "for stability". That cast makes the reference's
//! own `forward` raise `RuntimeError: mat1 and mat2 must have the same dtype`
//! for a `.double()` model (the `concept_proj` weights stay `float64`), so a
//! float64 end-to-end reference output does not exist. [`PRINetModel`] runs the
//! whole forward in the backend dtype with no internal cast; the readout head
//! (`LayerNorm` + `concept_proj` + clamp + `log_softmax`) is otherwise a
//! bit-faithful port and is parity-checked against the reference's own
//! submodules in float64 (`tests/test_model.py`).
//!
//! **Inherited deviation — resonance initial state.** [`PRINetModel`] composes
//! [`crate::layers::ResonanceLayer`] unchanged, so it inherits that layer's
//! documented FFT-vs-matmul feature-to-oscillator encoding deviation (plan
//! amendment #19). End-to-end parity with the reference is exact only where the
//! `ResonanceLayer` encoding coincides (a zero input); for arbitrary inputs the
//! end-to-end delta is bounded by — not newly introduced by — that inherited
//! deviation.
//!
//! `enable_mixed_precision` / `torch.compile` fusion from the reference are not
//! reproduced (CPU-only Burn core; `compile_model` is a pure-Python
//! `torch.compile` passthrough, WP-036A D-2).

use burn::module::{Module, Param};
use burn::nn::{LayerNorm, LayerNormConfig, Linear};
use burn::tensor::activation::log_softmax;
use burn::tensor::backend::Backend;
use burn::tensor::Tensor;
use prin_dynamics::Seed;

use crate::error::TrainError;
use crate::layers::{ResonanceLayer, ResonanceLayerConfig, ResonanceLayerParams};
use crate::support::{check_dims, seeded_linear, validate_dt};
use crate::LinearWeights;

/// Logit clamp bound, matching PRINet 3.0's `torch.clamp(logits, -50.0, 50.0)`.
const LOGIT_CLAMP: f64 = 50.0;

/// Rebuild a fresh gradient-tracked [`burn::nn::Linear`] from PyTorch-layout
/// weights (`[out_features, in_features]`).
///
/// `Tensor::transpose` returns a non-leaf op node and `require_grad` on a
/// non-leaf panics under the autodiff backend, so the leaf is rebuilt from
/// data — the same construction [`crate::autoencoders`] uses.
fn linear_from_weights<B: Backend>(weights: LinearWeights<B>) -> Linear<B> {
    let device = weights.weight.device();
    let weight = Tensor::from_data(weights.weight.transpose().into_data(), &device).require_grad();
    let bias = Tensor::from_data(weights.bias.into_data(), &device).require_grad();
    Linear {
        weight: Param::initialized(Default::default(), weight),
        bias: Some(Param::initialized(Default::default(), bias)),
    }
}

/// `(out_features, in_features)` of a [`burn::nn::Linear`] (Burn stores the
/// weight `[in, out]`).
fn linear_dims<B: Backend>(linear: &Linear<B>) -> (usize, usize) {
    let [in_features, out_features] = linear.weight.val().dims();
    (out_features, in_features)
}

/// Explicit affine parameters for one [`burn::nn::LayerNorm`].
pub struct LayerNormWeights<B: Backend> {
    /// Elementwise scale `γ`, shape `[n_features]`.
    pub gamma: Tensor<B, 1>,
    /// Elementwise shift `β`, shape `[n_features]`.
    pub beta: Tensor<B, 1>,
}

impl<B: Backend> LayerNormWeights<B> {
    fn into_layer_norm(self, n_features: usize) -> Result<LayerNorm<B>, TrainError> {
        check_dims("layer_norm.gamma", self.gamma.dims(), [n_features])?;
        check_dims("layer_norm.beta", self.beta.dims(), [n_features])?;
        let device = self.gamma.device();
        let mut norm = LayerNormConfig::new(n_features).init::<B>(&device);
        norm.gamma = Param::initialized(Default::default(), self.gamma.require_grad());
        norm.beta = Param::initialized(Default::default(), self.beta.require_grad());
        Ok(norm)
    }
}

/// Explicit parameters for [`PRINetModelConfig::init_from_params`].
///
/// Used by the forward-parity tests to inject a PRINet 3.0 model's exact
/// weights (PRIN's seeded init deliberately differs — only the initial scale is
/// load-bearing, the [`crate::layers::ResonanceLayer`] precedent).
pub struct PRINetModelParams<B: Backend> {
    /// Input `ResonanceLayer` parameters (`n_dims -> n_resonances`).
    pub input_layer: ResonanceLayerParams<B>,
    /// `n_layers - 1` stacked `ResonanceLayer` parameters
    /// (`n_resonances -> n_resonances`).
    pub stacked: Vec<ResonanceLayerParams<B>>,
    /// One `LayerNorm` affine pair per resonance layer (`n_layers` total).
    pub layer_norms: Vec<LayerNormWeights<B>>,
    /// Concept-readout `Linear` (`n_resonances -> n_concepts`, PyTorch layout).
    pub concept_proj: LinearWeights<B>,
}

/// Validated hyperparameters for [`PRINetModel`].
///
/// Defaults (`new`) match the PRINet 3.0 reference: `n_layers=4, n_steps=10,
/// dt=0.01`.
#[derive(Clone, Debug, PartialEq)]
pub struct PRINetModelConfig {
    /// Oscillators per resonance layer (the hidden width).
    pub n_resonances: usize,
    /// Input feature dimension.
    pub n_dims: usize,
    /// Number of output concepts/classes.
    pub n_concepts: usize,
    /// Number of resonance layers (input layer + `n_layers - 1` stacked).
    pub n_layers: usize,
    /// Kuramoto steps per resonance layer.
    pub n_steps: usize,
    /// Integration timestep.
    pub dt: f64,
}

impl PRINetModelConfig {
    /// Validated configuration with PRINet 3.0's default hyperparameters.
    ///
    /// # Errors
    ///
    /// Returns [`TrainError::EmptyBand`] if any dimension is zero and
    /// [`TrainError::InvalidStepCount`] if `n_layers` or `n_steps` is zero.
    pub fn new(n_resonances: usize, n_dims: usize, n_concepts: usize) -> Result<Self, TrainError> {
        Self::with_params(n_resonances, n_dims, n_concepts, 4, 10, 0.01)
    }

    /// Validated configuration with explicit hyperparameters.
    ///
    /// # Errors
    ///
    /// Returns [`TrainError::EmptyBand`] if `n_resonances`, `n_dims`, or
    /// `n_concepts` is zero, [`TrainError::InvalidStepCount`] if `n_layers` or
    /// `n_steps` is zero, and [`TrainError::InvalidTimestep`] for a
    /// non-finite/non-positive `dt`.
    pub fn with_params(
        n_resonances: usize,
        n_dims: usize,
        n_concepts: usize,
        n_layers: usize,
        n_steps: usize,
        dt: f64,
    ) -> Result<Self, TrainError> {
        for (name, value) in [
            ("resonances", n_resonances),
            ("dims", n_dims),
            ("concepts", n_concepts),
        ] {
            if value == 0 {
                return Err(TrainError::EmptyBand { name });
            }
        }
        if n_layers == 0 {
            return Err(TrainError::InvalidStepCount {
                name: "n_layers",
                value: n_layers,
            });
        }
        if n_steps == 0 {
            return Err(TrainError::InvalidStepCount {
                name: "n_steps",
                value: n_steps,
            });
        }
        validate_dt(dt)?;
        Ok(Self {
            n_resonances,
            n_dims,
            n_concepts,
            n_layers,
            n_steps,
            dt,
        })
    }

    fn resonance_config(&self, n_dims: usize) -> ResonanceLayerConfig {
        ResonanceLayerConfig::with_params(
            self.n_resonances,
            n_dims,
            self.n_steps,
            self.dt,
            0.1,
            0.01,
        )
        .expect("resonance hyperparameters are validated by the model config constructor")
    }

    /// Initialize a [`PRINetModel`] with parameters drawn from the project's
    /// deterministic [`Seed`] (Coding Standards §1.3).
    ///
    /// The concept-readout `Linear` is Xavier-uniform (gain `1.0`) drawn from
    /// `seed`; PRINet 3.0 uses PyTorch's default Kaiming-uniform `nn.Linear`
    /// init — only the initial scale is load-bearing (the `ResonanceLayer`
    /// precedent). `LayerNorm` starts at `γ = 1`, `β = 0` (identical in both).
    pub fn init<B: Backend>(&self, device: &B::Device, seed: &mut Seed) -> PRINetModel<B> {
        let input_layer = self.resonance_config(self.n_dims).init::<B>(device, seed);
        let layers: Vec<ResonanceLayer<B>> = (0..self.n_layers - 1)
            .map(|_| {
                self.resonance_config(self.n_resonances)
                    .init::<B>(device, seed)
            })
            .collect();
        let layer_norms: Vec<LayerNorm<B>> = (0..self.n_layers)
            .map(|_| LayerNormConfig::new(self.n_resonances).init::<B>(device))
            .collect();
        let concept_proj =
            seeded_linear::<B>(self.n_resonances, self.n_concepts, true, device, seed);
        PRINetModel {
            input_layer,
            layers,
            layer_norms,
            concept_proj,
            n_resonances: self.n_resonances,
            n_dims: self.n_dims,
            n_concepts: self.n_concepts,
            n_layers: self.n_layers,
        }
    }

    /// Build a [`PRINetModel`] from explicit parameter tensors.
    ///
    /// # Errors
    ///
    /// Returns [`TrainError::ShapeMismatch`] if any tensor's shape does not
    /// match this config, including a wrong number of stacked layers or
    /// `LayerNorm`s.
    pub fn init_from_params<B: Backend>(
        &self,
        params: PRINetModelParams<B>,
    ) -> Result<PRINetModel<B>, TrainError> {
        if params.stacked.len() != self.n_layers - 1 {
            return Err(TrainError::ShapeMismatch {
                name: "stacked_layers",
                expected: vec![self.n_layers - 1],
                got: vec![params.stacked.len()],
            });
        }
        if params.layer_norms.len() != self.n_layers {
            return Err(TrainError::ShapeMismatch {
                name: "layer_norms",
                expected: vec![self.n_layers],
                got: vec![params.layer_norms.len()],
            });
        }

        let input_layer = self
            .resonance_config(self.n_dims)
            .init_from_params(params.input_layer)?;
        let layers = params
            .stacked
            .into_iter()
            .map(|p| self.resonance_config(self.n_resonances).init_from_params(p))
            .collect::<Result<Vec<_>, _>>()?;
        let layer_norms = params
            .layer_norms
            .into_iter()
            .map(|w| w.into_layer_norm(self.n_resonances))
            .collect::<Result<Vec<_>, _>>()?;

        let (out_features, in_features) = (self.n_concepts, self.n_resonances);
        check_dims(
            "concept_proj",
            params.concept_proj.weight.dims(),
            [out_features, in_features],
        )?;
        check_dims(
            "concept_proj",
            params.concept_proj.bias.dims(),
            [out_features],
        )?;
        let concept_proj = linear_from_weights(params.concept_proj);

        Ok(PRINetModel {
            input_layer,
            layers,
            layer_norms,
            concept_proj,
            n_resonances: self.n_resonances,
            n_dims: self.n_dims,
            n_concepts: self.n_concepts,
            n_layers: self.n_layers,
        })
    }
}

/// Full trainable PRINet model: stacked resonance layers with inter-layer
/// `LayerNorm`, a concept readout, and a clamped `log_softmax`.
///
/// See the module docs for the exact forward formula and the documented
/// deviations from PRINet 3.0.
#[derive(Module, Debug)]
pub struct PRINetModel<B: Backend> {
    input_layer: ResonanceLayer<B>,
    layers: Vec<ResonanceLayer<B>>,
    layer_norms: Vec<LayerNorm<B>>,
    concept_proj: Linear<B>,
    n_resonances: usize,
    n_dims: usize,
    n_concepts: usize,
    n_layers: usize,
}

impl<B: Backend> PRINetModel<B> {
    /// Oscillators per resonance layer.
    pub fn n_resonances(&self) -> usize {
        self.n_resonances
    }

    /// Input feature dimension.
    pub fn n_dims(&self) -> usize {
        self.n_dims
    }

    /// Number of output concepts.
    pub fn n_concepts(&self) -> usize {
        self.n_concepts
    }

    /// Number of resonance layers.
    pub fn n_layers(&self) -> usize {
        self.n_layers
    }

    /// Full forward pass: returns concept log-probabilities, shape
    /// `[batch, n_concepts]` (PRINet 3.0's `PRINetModel.forward` return
    /// contract).
    ///
    /// # Errors
    ///
    /// Returns [`TrainError::ShapeMismatch`] if `x`'s width is not
    /// [`Self::n_dims`], propagating any [`crate::layers::ResonanceLayer`]
    /// error.
    pub fn forward(&self, x: Tensor<B, 2>) -> Result<Tensor<B, 2>, TrainError> {
        let batch = x.dims()[0];
        check_dims("x", x.dims(), [batch, self.n_dims])?;

        let mut h = self.input_layer.forward(x)?;
        h = self.layer_norms[0].forward(h);
        for (i, layer) in self.layers.iter().enumerate() {
            h = layer.forward(h)?;
            h = self.layer_norms[i + 1].forward(h);
        }

        let logits = self
            .concept_proj
            .forward(h)
            .clamp(-LOGIT_CLAMP, LOGIT_CLAMP);
        Ok(log_softmax(logits, 1))
    }

    /// Validate every parameter tensor's shape after a checkpoint restore.
    ///
    /// # Errors
    ///
    /// Returns [`TrainError::ShapeMismatch`] naming the first bad tensor.
    pub fn validate_shapes(&self) -> Result<(), TrainError> {
        self.input_layer.validate_shapes()?;
        if self.layers.len() != self.n_layers - 1 {
            return Err(TrainError::ShapeMismatch {
                name: "stacked_layers",
                expected: vec![self.n_layers - 1],
                got: vec![self.layers.len()],
            });
        }
        for layer in &self.layers {
            layer.validate_shapes()?;
        }
        if self.layer_norms.len() != self.n_layers {
            return Err(TrainError::ShapeMismatch {
                name: "layer_norms",
                expected: vec![self.n_layers],
                got: vec![self.layer_norms.len()],
            });
        }
        for norm in &self.layer_norms {
            check_dims(
                "layer_norm.gamma",
                norm.gamma.val().dims(),
                [self.n_resonances],
            )?;
            check_dims(
                "layer_norm.beta",
                norm.beta.val().dims(),
                [self.n_resonances],
            )?;
        }
        let (out_features, in_features) = linear_dims(&self.concept_proj);
        if (out_features, in_features) != (self.n_concepts, self.n_resonances) {
            return Err(TrainError::ShapeMismatch {
                name: "concept_proj",
                expected: vec![self.n_concepts, self.n_resonances],
                got: vec![out_features, in_features],
            });
        }
        Ok(())
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    use burn::backend::{Autodiff, NdArray};
    use burn::tensor::TensorData;

    type TestBackend = NdArray<f64>;
    type TestAutodiffBackend = Autodiff<TestBackend>;

    fn device() -> <TestBackend as Backend>::Device {
        Default::default()
    }

    fn small_config() -> PRINetModelConfig {
        PRINetModelConfig::with_params(4, 6, 3, 2, 2, 0.01).unwrap()
    }

    fn seeded_model<B: Backend>(device: &B::Device) -> PRINetModel<B> {
        let mut seed = Seed::new(7, 0);
        small_config().init::<B>(device, &mut seed)
    }

    // --- Config validation ---

    #[test]
    fn zero_dims_and_zero_counts_rejected() {
        assert!(matches!(
            PRINetModelConfig::new(0, 6, 3).unwrap_err(),
            TrainError::EmptyBand { name: "resonances" }
        ));
        assert!(matches!(
            PRINetModelConfig::new(4, 0, 3).unwrap_err(),
            TrainError::EmptyBand { name: "dims" }
        ));
        assert!(matches!(
            PRINetModelConfig::new(4, 6, 0).unwrap_err(),
            TrainError::EmptyBand { name: "concepts" }
        ));
        assert!(matches!(
            PRINetModelConfig::with_params(4, 6, 3, 0, 2, 0.01).unwrap_err(),
            TrainError::InvalidStepCount {
                name: "n_layers",
                ..
            }
        ));
        assert!(matches!(
            PRINetModelConfig::with_params(4, 6, 3, 2, 0, 0.01).unwrap_err(),
            TrainError::InvalidStepCount {
                name: "n_steps",
                ..
            }
        ));
        assert!(matches!(
            PRINetModelConfig::with_params(4, 6, 3, 2, 2, 0.0).unwrap_err(),
            TrainError::InvalidTimestep { .. }
        ));
    }

    // --- Construction / forward ---

    #[test]
    fn seeded_init_reports_configuration() {
        let model = seeded_model::<TestBackend>(&device());
        assert_eq!(model.n_resonances(), 4);
        assert_eq!(model.n_dims(), 6);
        assert_eq!(model.n_concepts(), 3);
        assert_eq!(model.n_layers(), 2);
        assert_eq!(model.layers.len(), 1);
        assert_eq!(model.layer_norms.len(), 2);
        assert!(model.validate_shapes().is_ok());
    }

    #[test]
    fn single_layer_model_has_no_stacked_layers() {
        let cfg = PRINetModelConfig::with_params(4, 6, 3, 1, 2, 0.01).unwrap();
        let model = cfg.init::<TestBackend>(&device(), &mut Seed::new(1, 0));
        assert!(model.layers.is_empty());
        assert_eq!(model.layer_norms.len(), 1);
        let out = model
            .forward(Tensor::<TestBackend, 2>::zeros([2, 6], &device()))
            .unwrap();
        assert_eq!(out.dims(), [2, 3]);
    }

    #[test]
    fn forward_returns_log_probabilities() {
        let model = seeded_model::<TestBackend>(&device());
        let x = Tensor::<TestBackend, 2>::ones([3, 6], &device()) * 0.25;
        let out = model.forward(x).unwrap();
        assert_eq!(out.dims(), [3, 3]);
        let data = out.clone().to_data().to_vec::<f64>().unwrap();
        assert!(data.iter().all(|v| v.is_finite() && *v <= 0.0));
        for row in out.exp().sum_dim(1).to_data().to_vec::<f64>().unwrap() {
            assert!((row - 1.0).abs() < 1e-9, "log_softmax row sums to {row}");
        }
    }

    #[test]
    fn forward_rejects_wrong_input_width() {
        let model = seeded_model::<TestBackend>(&device());
        assert!(matches!(
            model
                .forward(Tensor::<TestBackend, 2>::ones([2, 5], &device()))
                .unwrap_err(),
            TrainError::ShapeMismatch { name: "x", .. }
        ));
    }

    #[test]
    fn logits_are_clamped_before_log_softmax() {
        // A degenerate single-concept readout: log_softmax of any finite logit
        // is exactly 0, but the clamp still has to keep the pre-softmax value
        // finite. Use a wide readout weight and large input to force
        // saturation, then check the output is a valid (finite) log-prob.
        let cfg = PRINetModelConfig::with_params(3, 2, 2, 1, 1, 0.01).unwrap();
        let big = 1e3;
        let params = PRINetModelParams {
            input_layer: reference_resonance_params(3, 2, 1.0),
            stacked: vec![],
            layer_norms: vec![layer_norm_weights(3, 1.0, 0.0)],
            concept_proj: LinearWeights {
                weight: t2(vec![big, big, big, -big, -big, -big], 2, 3),
                bias: t1(vec![0.0, 0.0]),
            },
        };
        let model = cfg.init_from_params(params).unwrap();
        let out = model
            .forward(Tensor::<TestBackend, 2>::ones([1, 2], &device()) * 5.0)
            .unwrap();
        let data = out.to_data().to_vec::<f64>().unwrap();
        assert!(data.iter().all(|v| v.is_finite()));
        // With logits clamped to +-50, the softmax gap is bounded and the
        // dominant class log-prob is > -1e-40 but the other is ~ -100, never
        // -inf (which an unclamped 1e3 logit gap would risk under f32).
        assert!(data.iter().all(|v| *v > -1e4));
    }

    // --- Explicit params / parity plumbing ---

    fn t2(data: Vec<f64>, rows: usize, cols: usize) -> Tensor<TestBackend, 2> {
        Tensor::from_data(TensorData::new(data, vec![rows, cols]), &device())
    }

    fn t1(data: Vec<f64>) -> Tensor<TestBackend, 1> {
        let len = data.len();
        Tensor::from_data(TensorData::new(data, vec![len]), &device())
    }

    fn layer_norm_weights(n: usize, gamma: f64, beta: f64) -> LayerNormWeights<TestBackend> {
        LayerNormWeights {
            gamma: t1(vec![gamma; n]),
            beta: t1(vec![beta; n]),
        }
    }

    fn reference_resonance_params(
        n_oscillators: usize,
        n_dims: usize,
        fill: f64,
    ) -> ResonanceLayerParams<TestBackend> {
        let n = n_oscillators;
        ResonanceLayerParams {
            coupling: t2(vec![0.0; n * n], n, n),
            decay: t1(vec![0.1; n]),
            input_proj: t2(vec![fill; n_dims * n], n_dims, n),
            modulation: t2(vec![0.0; n * n], n, n),
            base_frequency: {
                let step = if n == 1 {
                    0.0
                } else {
                    (10.0 - 0.1) / (n - 1) as f64
                };
                t1((0..n).map(|i| 0.1 + step * i as f64).collect())
            },
        }
    }

    #[test]
    fn init_from_params_validates_layer_and_norm_counts() {
        let cfg = small_config(); // n_layers = 2
        let ok = PRINetModelParams {
            input_layer: reference_resonance_params(4, 6, 0.05),
            stacked: vec![reference_resonance_params(4, 4, 0.05)],
            layer_norms: (0..2).map(|_| layer_norm_weights(4, 1.0, 0.0)).collect(),
            concept_proj: LinearWeights {
                weight: t2(vec![0.02; 3 * 4], 3, 4),
                bias: t1(vec![0.0; 3]),
            },
        };
        assert!(cfg.init_from_params(ok).is_ok());

        let wrong_stack = PRINetModelParams {
            input_layer: reference_resonance_params(4, 6, 0.05),
            stacked: vec![],
            layer_norms: (0..2).map(|_| layer_norm_weights(4, 1.0, 0.0)).collect(),
            concept_proj: LinearWeights {
                weight: t2(vec![0.02; 3 * 4], 3, 4),
                bias: t1(vec![0.0; 3]),
            },
        };
        assert!(matches!(
            cfg.init_from_params(wrong_stack).unwrap_err(),
            TrainError::ShapeMismatch {
                name: "stacked_layers",
                ..
            }
        ));

        let wrong_norms = PRINetModelParams {
            input_layer: reference_resonance_params(4, 6, 0.05),
            stacked: vec![reference_resonance_params(4, 4, 0.05)],
            layer_norms: vec![layer_norm_weights(4, 1.0, 0.0)],
            concept_proj: LinearWeights {
                weight: t2(vec![0.02; 3 * 4], 3, 4),
                bias: t1(vec![0.0; 3]),
            },
        };
        assert!(matches!(
            cfg.init_from_params(wrong_norms).unwrap_err(),
            TrainError::ShapeMismatch {
                name: "layer_norms",
                ..
            }
        ));
    }

    #[test]
    fn init_from_params_reports_concept_proj_shape_error() {
        let cfg = PRINetModelConfig::with_params(4, 6, 3, 1, 2, 0.01).unwrap();
        let params = PRINetModelParams {
            input_layer: reference_resonance_params(4, 6, 0.05),
            stacked: vec![],
            layer_norms: vec![layer_norm_weights(4, 1.0, 0.0)],
            concept_proj: LinearWeights {
                weight: t2(vec![0.02; 4 * 4], 4, 4),
                bias: t1(vec![0.0; 4]),
            },
        };
        assert!(matches!(
            cfg.init_from_params(params).unwrap_err(),
            TrainError::ShapeMismatch {
                name: "concept_proj",
                ..
            }
        ));
    }

    #[test]
    fn init_from_params_reports_layer_norm_shape_error() {
        let cfg = PRINetModelConfig::with_params(4, 6, 3, 1, 2, 0.01).unwrap();
        let params = PRINetModelParams {
            input_layer: reference_resonance_params(4, 6, 0.05),
            stacked: vec![],
            layer_norms: vec![layer_norm_weights(3, 1.0, 0.0)],
            concept_proj: LinearWeights {
                weight: t2(vec![0.02; 3 * 4], 3, 4),
                bias: t1(vec![0.0; 3]),
            },
        };
        assert!(matches!(
            cfg.init_from_params(params).unwrap_err(),
            TrainError::ShapeMismatch {
                name: "layer_norm.gamma",
                ..
            }
        ));
    }

    // --- D-5: batched equals stacked singles ---

    #[test]
    fn batched_forward_matches_stacked_single_rows() {
        let model = seeded_model::<TestBackend>(&device());
        let x = t2(
            vec![
                0.2, -0.3, 0.5, -0.4, 0.1, 0.7, 0.3, -0.1, 0.6, -0.2, 0.0, 0.4,
            ],
            2,
            6,
        );
        let batched = model.forward(x.clone()).unwrap();
        let first = model.forward(x.clone().narrow(0, 0, 1)).unwrap();
        let second = model.forward(x.narrow(0, 1, 1)).unwrap();
        let stacked = Tensor::cat(vec![first, second], 0);
        let delta = (batched - stacked).abs().max().into_scalar();
        assert!(delta < 1e-12, "batched vs stacked delta {delta}");
    }

    // --- Gradient reference tests ---

    #[test]
    fn gradients_flow_to_the_readout_and_through_the_resonance_stack() {
        let _guard = crate::support::autodiff_test_guard();
        let dev: <TestAutodiffBackend as Backend>::Device = Default::default();
        let mut seed = Seed::new(21, 0);
        let model = small_config().init::<TestAutodiffBackend>(&dev, &mut seed);
        let x = Tensor::<TestAutodiffBackend, 2>::ones([2, 6], &dev).require_grad();

        let out = model.forward(x.clone()).unwrap();
        let grads = out.sum().backward();

        // The input gradient is only non-`None` if the whole graph — every
        // stacked `ResonanceLayer`, every `LayerNorm`, and the readout —
        // backpropagated (`crate::layers` proves the resonance parameters
        // themselves receive gradients).
        let input_grad = x
            .grad(&grads)
            .expect("gradient must reach the model input")
            .to_data()
            .to_vec::<f64>()
            .unwrap();
        assert!(input_grad.iter().all(|v| v.is_finite()));
        assert!(input_grad.iter().any(|v| v.abs() > 0.0));

        assert!(model.concept_proj.weight.grad(&grads).is_some());
        assert!(model
            .concept_proj
            .bias
            .as_ref()
            .unwrap()
            .grad(&grads)
            .is_some());
        assert!(model.layer_norms[0].gamma.grad(&grads).is_some());
        assert!(model.layer_norms[1].beta.grad(&grads).is_some());
    }

    #[test]
    fn concept_readout_matches_hand_computed_clamped_log_softmax() {
        // Parity of the head PRINetModel adds: given a fixed hidden state `h`
        // (forced by a zero coupling + identity-ish projection so the
        // resonance stack is deterministic), the output equals
        // `log_softmax(clamp(h @ Wᵀ + b, -50, 50))` computed independently.
        let cfg = PRINetModelConfig::with_params(3, 3, 2, 1, 1, 0.01).unwrap();
        let weight = vec![0.4, -0.1, 0.2, 0.05, 0.3, -0.25];
        let bias = vec![0.1, -0.2];
        let params = PRINetModelParams {
            input_layer: reference_resonance_params(3, 3, 0.0),
            stacked: vec![],
            layer_norms: vec![layer_norm_weights(3, 1.0, 0.0)],
            concept_proj: LinearWeights {
                weight: t2(weight.clone(), 2, 3),
                bias: t1(bias.clone()),
            },
        };
        let model = cfg.init_from_params(params).unwrap();
        // Zero input -> zero projection -> phase=0, amp=1e-6 initial state;
        // with zero coupling the amplitude only decays, so `h` is a known
        // constant vector after one step.
        let x = Tensor::<TestBackend, 2>::zeros([1, 3], &device());
        let out = model.forward(x).unwrap().to_data().to_vec::<f64>().unwrap();

        // Reproduce: h is `1e-6 * (1 - dt*decay)` per oscillator (decay 0.1,
        // dt 0.01), then LayerNorm(gamma=1, beta=0) of a constant vector is
        // exactly 0, so logits = bias, clamped (no-op), then log_softmax.
        let logits = bias;
        let max = logits.iter().cloned().fold(f64::MIN, f64::max);
        let denom: f64 = logits.iter().map(|l| (l - max).exp()).sum();
        let expected: Vec<f64> = logits.iter().map(|l| (l - max) - denom.ln()).collect();
        for (got, want) in out.iter().zip(expected) {
            assert!((got - want).abs() < 1e-12, "{got} vs {want}");
        }
    }

    // --- Serialization ---

    #[test]
    fn record_roundtrip_preserves_forward_output() {
        use burn::record::{BinBytesRecorder, DoublePrecisionSettings, Recorder};

        let dev = device();
        let model = seeded_model::<TestBackend>(&dev);
        let x = t2(vec![0.1; 12], 2, 6);
        let before = model
            .forward(x.clone())
            .unwrap()
            .to_data()
            .to_vec::<f64>()
            .unwrap();

        let recorder = BinBytesRecorder::<DoublePrecisionSettings>::default();
        let bytes =
            Recorder::<TestBackend>::record(&recorder, model.clone().into_record(), ()).unwrap();
        let record = Recorder::<TestBackend>::load(&recorder, bytes, &dev).unwrap();
        let restored = model.load_record(record);

        let after = restored
            .forward(x)
            .unwrap()
            .to_data()
            .to_vec::<f64>()
            .unwrap();
        assert_eq!(before, after);
        assert!(restored.validate_shapes().is_ok());
    }

    #[test]
    fn validate_shapes_detects_mismatched_record() {
        use burn::record::{BinBytesRecorder, DoublePrecisionSettings, Recorder};

        let dev = device();
        let target = seeded_model::<TestBackend>(&dev); // 4 resonances, 6 dims, 3 concepts
        let donor = PRINetModelConfig::with_params(4, 6, 5, 2, 2, 0.01)
            .unwrap()
            .init::<TestBackend>(&dev, &mut Seed::new(99, 0));
        let recorder = BinBytesRecorder::<DoublePrecisionSettings>::default();
        let bytes = Recorder::<TestBackend>::record(&recorder, donor.into_record(), ()).unwrap();
        let record = Recorder::<TestBackend>::load(&recorder, bytes, &dev).unwrap();
        let candidate = target.load_record(record);
        assert!(matches!(
            candidate.validate_shapes().unwrap_err(),
            TrainError::ShapeMismatch {
                name: "concept_proj",
                ..
            }
        ));
    }
}
