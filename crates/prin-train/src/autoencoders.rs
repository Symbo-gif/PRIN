//! Phase-to-rate conversion and autoencoder comparison models.
//!
//! This module ports PRINet 3.0's `nn.layers.PhaseToRateConverter`,
//! `PhaseToRateAutoencoder`, and `DenseAutoencoder` to Burn. All three are
//! trainable `Module`s with Rust-owned parameters; the encoder/decoder/
//! classifier stacks are plain [`burn::nn::Linear`] layers (Coding Standards
//! §1.2 — no Python numerics).
//!
//! # `phase_to_rate`
//!
//! [`phase_to_rate`] is a line-for-line port of PRINet 3.0's
//! `core.propagation.phase_to_rate` (the same formula the non-autodiff
//! `prin_sim::compat::phase_to_rate` binding implements):
//!
//! ```text
//! rate_i = amplitude_i * (1 + cos(phase_i)) / 2
//! soft:     softmax(rate / T, dim=-1)                       (fully autodiff)
//! hard:     scatter(zeros, topk_indices(rate, k), topk_values)   k = max(1, floor(N*sparsity))
//! annealed: (1 - b)*soft + b*hard,  b = sigmoid(1/max(T, 1e-6) - 1)
//! ```
//!
//! `soft` is fully differentiable and gradchecked. `hard` reproduces the
//! reference's non-differentiable top-`k` selection exactly in the forward
//! pass; Burn's autodiff routes a gradient to the selected entries through the
//! `topk`/`scatter` gather (a straight-through estimator — the discrete
//! selection itself carries no gradient). `annealed` interpolates, with the
//! blend coefficient treated as a constant of the temperature *value* (the
//! reference computes it from a detached `.item()`), so the soft-dominated
//! regime is what a finite-difference `gradcheck` can validate (WP-036A D-3).
//!
//! **Documented deviation — learnable temperature.** PRINet 3.0's
//! `PhaseToRateConverter.forward` reads its temperature with
//! `torch.clamp(self.temperature, min=1e-6).item()`, detaching it, so no
//! gradient reaches the temperature even when `learnable_temperature=True`.
//! [`PhaseToRateConverter`] keeps the temperature a live [`Param`] and lets
//! the `soft`/`annealed` softmax gradient flow to it — strictly a superset of
//! the reference behaviour, forward-identical, and the natural reading of a
//! "learnable temperature". The reference's `learnable_temperature=False`
//! buffer mode is not reproduced (hold the parameter out of the optimizer to
//! freeze it).
//!
//! # Autoencoder initial parameters
//!
//! [`PhaseToRateAutoencoderConfig::init`] / [`DenseAutoencoderConfig::init`]
//! draw the `Linear` weights from the project [`Seed`] (Xavier-uniform),
//! **not** PyTorch's default Kaiming-uniform `nn.Linear` init — only the
//! initial scale is load-bearing for training (the same precedent
//! [`crate::layers::ResonanceLayer`] documents). Forward-parity tests inject
//! the reference model's exact weights via
//! [`PhaseToRateAutoencoderConfig::init_from_params`].

use burn::module::{Ignored, Module, Param};
use burn::nn::Linear;
use burn::tensor::activation::{log_softmax, relu, softmax, softplus};
use burn::tensor::backend::Backend;
use burn::tensor::{ElementConversion, Tensor};
use prin_dynamics::Seed;

use crate::error::TrainError;
use crate::support::{check_dims, seeded_linear, validate_finite};

/// Winner-take-all mode for [`phase_to_rate`] / [`PhaseToRateConverter`].
#[derive(Clone, Copy, Debug, PartialEq, Eq)]
pub enum PhaseToRateMode {
    /// Temperature-scaled softmax of the instantaneous rates (fully autodiff).
    Soft,
    /// Preserve only the `max(1, floor(N * sparsity))` largest rates.
    Hard,
    /// Blend soft and hard outputs with `sigmoid(1/max(T, 1e-6) - 1)`.
    Annealed,
}

impl PhaseToRateMode {
    /// Parse the PRINet 3.0 mode string (`"soft"`, `"hard"`, `"annealed"`).
    ///
    /// # Errors
    ///
    /// An unrecognised string returns [`TrainError::NonFiniteParameter`] with
    /// `name = "mode"` and `value = f64::NAN` — reusing the existing
    /// "bad scalar hyperparameter" channel rather than growing the error enum
    /// for a string typo.
    pub fn parse(mode: &str) -> Result<Self, TrainError> {
        match mode {
            "soft" => Ok(Self::Soft),
            "hard" => Ok(Self::Hard),
            "annealed" => Ok(Self::Annealed),
            _ => Err(TrainError::NonFiniteParameter {
                name: "mode",
                value: f64::NAN,
            }),
        }
    }

    /// The PRINet 3.0 mode string.
    pub fn as_str(&self) -> &'static str {
        match self {
            Self::Soft => "soft",
            Self::Hard => "hard",
            Self::Annealed => "annealed",
        }
    }
}

/// Temperature floor, matching PRINet 3.0's `torch.clamp(..., min=1e-6)`.
const TEMP_EPS: f64 = 1e-6;

/// Convert phase/amplitude representations to sparse rate codes.
///
/// See the module docs for the exact formula. `temperature` is a shape-`[1]`
/// tensor so a composing module can learn it; it is floored at `1e-6`.
///
/// # Errors
///
/// Returns [`TrainError::ShapeMismatch`] when `phase` and `amplitude` differ
/// in shape or `temperature` is not shape `[1]`, and
/// [`TrainError::InvalidRatio`] when `sparsity` is outside `[0, 1]`.
pub fn phase_to_rate<B: Backend>(
    phase: Tensor<B, 2>,
    amplitude: Tensor<B, 2>,
    mode: PhaseToRateMode,
    sparsity: f64,
    temperature: Tensor<B, 1>,
) -> Result<Tensor<B, 2>, TrainError> {
    let dims = phase.dims();
    check_dims("amplitude", amplitude.dims(), dims)?;
    check_dims("temperature", temperature.dims(), [1])?;
    validate_finite("sparsity", sparsity)?;
    if !(0.0..=1.0).contains(&sparsity) {
        return Err(TrainError::InvalidRatio {
            name: "sparsity",
            value: sparsity,
        });
    }
    let [batch, n] = dims;
    let device = phase.device();

    let rate = amplitude * (phase.cos() + 1.0).div_scalar(2.0);
    let temperature = temperature.clamp_min(TEMP_EPS);

    let soft = |rate: &Tensor<B, 2>, temperature: &Tensor<B, 1>| -> Tensor<B, 2> {
        let temp = temperature
            .clone()
            .reshape([1, 1])
            .repeat_dim(0, batch)
            .repeat_dim(1, n);
        softmax(rate.clone() / temp, 1)
    };
    let hard = |rate: &Tensor<B, 2>| -> Tensor<B, 2> {
        // Build the top-`k` selection mask from `topk`'s (non-differentiable)
        // indices and a constant `ones`, then gate `rate` with it — the same
        // straight-through construction `crate::inhibition::FeedbackInhibition`
        // uses. `rate * mask` is forward-identical to PRINet 3.0's
        // `zeros.scatter_(topk_idx, topk_vals)`; the discrete selection carries
        // no gradient, so Burn autodiff never differentiates through `topk`.
        let k = ((n as f64 * sparsity) as usize).max(1).min(n);
        let (_vals, idx) = rate.clone().topk_with_indices(k, 1);
        let mask = Tensor::<B, 2>::zeros([batch, n], &device).scatter(
            1,
            idx,
            Tensor::<B, 2>::ones([batch, k], &device),
        );
        rate.clone() * mask
    };

    Ok(match mode {
        PhaseToRateMode::Soft => soft(&rate, &temperature),
        PhaseToRateMode::Hard => hard(&rate),
        PhaseToRateMode::Annealed => {
            // The blend coefficient is a constant of the temperature *value*
            // (PRINet 3.0 computes it from a detached `.item()`).
            let temp_scalar: f64 = temperature.clone().into_scalar().elem();
            let blend = 1.0 / (1.0 + (1.0 - 1.0 / temp_scalar).exp());
            soft(&rate, &temperature).mul_scalar(1.0 - blend) + hard(&rate).mul_scalar(blend)
        }
    })
}

/// Validated hyperparameters for [`PhaseToRateConverter`].
#[derive(Clone, Debug, PartialEq)]
pub struct PhaseToRateConverterConfig {
    /// Input oscillator dimension.
    pub n_oscillators: usize,
    /// Winner-take-all mode.
    pub mode: PhaseToRateMode,
    /// Target active fraction (used by `hard` / `annealed`).
    pub sparsity: f64,
    /// Initial softmax temperature.
    pub initial_temperature: f64,
}

impl PhaseToRateConverterConfig {
    /// Construct with PRINet 3.0 defaults (`mode="soft"`, `sparsity=0.1`,
    /// `initial_temperature=1.0`).
    ///
    /// # Errors
    ///
    /// Returns [`TrainError::EmptyBand`] when `n_oscillators` is zero.
    pub fn new(n_oscillators: usize) -> Result<Self, TrainError> {
        Self::with_params(n_oscillators, PhaseToRateMode::Soft, 0.1, 1.0)
    }

    /// Construct with explicit hyperparameters.
    ///
    /// # Errors
    ///
    /// Returns [`TrainError::EmptyBand`] when `n_oscillators` is zero,
    /// [`TrainError::InvalidRatio`] when `sparsity` is outside `[0, 1]`, and
    /// [`TrainError::InvalidPositiveParameter`] when `initial_temperature` is
    /// not finite and strictly positive.
    pub fn with_params(
        n_oscillators: usize,
        mode: PhaseToRateMode,
        sparsity: f64,
        initial_temperature: f64,
    ) -> Result<Self, TrainError> {
        if n_oscillators == 0 {
            return Err(TrainError::EmptyBand {
                name: "oscillators",
            });
        }
        validate_finite("sparsity", sparsity)?;
        validate_finite("initial_temperature", initial_temperature)?;
        if !(0.0..=1.0).contains(&sparsity) {
            return Err(TrainError::InvalidRatio {
                name: "sparsity",
                value: sparsity,
            });
        }
        if initial_temperature <= 0.0 {
            return Err(TrainError::InvalidPositiveParameter {
                name: "initial_temperature",
                value: initial_temperature,
            });
        }
        Ok(Self {
            n_oscillators,
            mode,
            sparsity,
            initial_temperature,
        })
    }

    /// Build a converter with the configured initial temperature.
    pub fn init<B: Backend>(&self, device: &B::Device) -> PhaseToRateConverter<B> {
        let temperature = Tensor::<B, 1>::from_data(
            burn::tensor::TensorData::new(vec![self.initial_temperature], vec![1]),
            device,
        )
        .require_grad();
        self.init_from_params(temperature)
            .expect("a shape-[1] temperature tensor constructed here is always valid")
    }

    /// Build a converter from an explicit shape-`[1]` temperature tensor.
    ///
    /// # Errors
    ///
    /// Returns [`TrainError::ShapeMismatch`] unless `temperature` is shape
    /// `[1]`.
    pub fn init_from_params<B: Backend>(
        &self,
        temperature: Tensor<B, 1>,
    ) -> Result<PhaseToRateConverter<B>, TrainError> {
        check_dims("temperature", temperature.dims(), [1])?;
        Ok(PhaseToRateConverter {
            temperature: Param::initialized(Default::default(), temperature.require_grad()),
            n_oscillators: self.n_oscillators,
            mode: Ignored(self.mode),
            sparsity: self.sparsity,
        })
    }
}

/// Trainable phase-to-rate converter with a Rust-owned learnable temperature.
///
/// See the module docs for the WTA formula and the learnable-temperature
/// deviation from PRINet 3.0.
#[derive(Module, Debug)]
pub struct PhaseToRateConverter<B: Backend> {
    temperature: Param<Tensor<B, 1>>,
    n_oscillators: usize,
    mode: Ignored<PhaseToRateMode>,
    sparsity: f64,
}

impl<B: Backend> PhaseToRateConverter<B> {
    /// Input oscillator dimension.
    pub fn n_oscillators(&self) -> usize {
        self.n_oscillators
    }

    /// Winner-take-all mode.
    pub fn mode(&self) -> PhaseToRateMode {
        self.mode.0
    }

    /// Target active fraction.
    pub fn sparsity(&self) -> f64 {
        self.sparsity
    }

    /// Validate the Rust-owned temperature shape after checkpoint restore.
    ///
    /// # Errors
    ///
    /// Returns [`TrainError::ShapeMismatch`] for a malformed parameter record.
    pub fn validate_shapes(&self) -> Result<(), TrainError> {
        check_dims("temperature", self.temperature.val().dims(), [1])
    }

    /// Convert matching `[batch, n_oscillators]` phase/amplitude tensors to
    /// rate codes.
    ///
    /// # Errors
    ///
    /// Returns [`TrainError::ShapeMismatch`] for a wrong-width or mismatched
    /// input.
    pub fn forward(
        &self,
        phase: Tensor<B, 2>,
        amplitude: Tensor<B, 2>,
    ) -> Result<Tensor<B, 2>, TrainError> {
        let dims = phase.dims();
        check_dims("phase", dims, [dims[0], self.n_oscillators])?;
        phase_to_rate(
            phase,
            amplitude,
            self.mode.0,
            self.sparsity,
            self.temperature.val(),
        )
    }
}

/// Explicit weight/bias pair for one [`burn::nn::Linear`], in PyTorch layout.
pub struct LinearWeights<B: Backend> {
    /// Weight in `torch.nn.Linear` layout, shape `[out_features, in_features]`.
    pub weight: Tensor<B, 2>,
    /// Bias, shape `[out_features]`.
    pub bias: Tensor<B, 1>,
}

impl<B: Backend> LinearWeights<B> {
    fn validate(
        &self,
        name: &'static str,
        out_features: usize,
        in_features: usize,
    ) -> Result<(), TrainError> {
        check_dims(name, self.weight.dims(), [out_features, in_features])?;
        check_dims(name, self.bias.dims(), [out_features])
    }

    fn into_linear(self) -> Linear<B> {
        // Rebuild fresh leaves from data: `Tensor::transpose` returns a
        // non-leaf op node, and `require_grad` on a non-leaf panics under the
        // autodiff backend. PyTorch's `nn.Linear` weight is `[out, in]`; Burn's
        // is `[in, out]`.
        let device = self.weight.device();
        let weight = Tensor::from_data(self.weight.transpose().into_data(), &device).require_grad();
        let bias = Tensor::from_data(self.bias.into_data(), &device).require_grad();
        Linear {
            weight: Param::initialized(Default::default(), weight),
            bias: Some(Param::initialized(Default::default(), bias)),
        }
    }
}

fn linear_dims<B: Backend>(linear: &Linear<B>) -> (usize, usize) {
    let [in_features, out_features] = linear.weight.val().dims();
    (out_features, in_features)
}

fn linear_forward<B: Backend>(stack: &[Linear<B>; 2], x: Tensor<B, 2>) -> Tensor<B, 2> {
    stack[1].forward(relu(stack[0].forward(x)))
}

/// Validated hyperparameters for [`PhaseToRateAutoencoder`].
#[derive(Clone, Debug, PartialEq)]
pub struct PhaseToRateAutoencoderConfig {
    /// Input feature dimension.
    pub n_input: usize,
    /// Bottleneck oscillator count.
    pub n_oscillators: usize,
    /// Hidden width of the encoder/decoder MLPs (PRINet 3.0 hardcodes `256`).
    pub hidden: usize,
    /// Number of classifier-head classes (PRINet 3.0 hardcodes `10`).
    pub n_classes: usize,
    /// Target sparsity for the phase-to-rate bottleneck.
    pub sparsity: f64,
    /// Winner-take-all mode for the bottleneck.
    pub mode: PhaseToRateMode,
}

impl PhaseToRateAutoencoderConfig {
    /// Construct with PRINet 3.0 defaults (`hidden=256`, `n_classes=10`,
    /// `sparsity=0.1`, `mode="soft"`).
    ///
    /// # Errors
    ///
    /// See [`Self::with_params`].
    pub fn new(n_input: usize, n_oscillators: usize) -> Result<Self, TrainError> {
        Self::with_params(n_input, n_oscillators, 256, 10, 0.1, PhaseToRateMode::Soft)
    }

    /// Construct with explicit hyperparameters.
    ///
    /// # Errors
    ///
    /// Returns [`TrainError::EmptyBand`] for a zero dimension and
    /// [`TrainError::InvalidRatio`] for a `sparsity` outside `[0, 1]`.
    pub fn with_params(
        n_input: usize,
        n_oscillators: usize,
        hidden: usize,
        n_classes: usize,
        sparsity: f64,
        mode: PhaseToRateMode,
    ) -> Result<Self, TrainError> {
        for (name, value) in [
            ("n_input", n_input),
            ("n_oscillators", n_oscillators),
            ("hidden", hidden),
            ("n_classes", n_classes),
        ] {
            if value == 0 {
                return Err(TrainError::EmptyBand { name });
            }
        }
        PhaseToRateConverterConfig::with_params(n_oscillators, mode, sparsity, 1.0)?;
        Ok(Self {
            n_input,
            n_oscillators,
            hidden,
            n_classes,
            sparsity,
            mode,
        })
    }

    /// Initialize with Xavier-uniform `Linear` weights drawn from `seed` and
    /// a unit initial bottleneck temperature.
    pub fn init<B: Backend>(
        &self,
        device: &B::Device,
        seed: &mut Seed,
    ) -> PhaseToRateAutoencoder<B> {
        let (ni, no, h) = (self.n_input, self.n_oscillators, self.hidden);
        PhaseToRateAutoencoder {
            encoder_phase: [
                seeded_linear::<B>(ni, h, true, device, seed),
                seeded_linear::<B>(h, no, true, device, seed),
            ],
            encoder_amp: [
                seeded_linear::<B>(ni, h, true, device, seed),
                seeded_linear::<B>(h, no, true, device, seed),
            ],
            decoder: [
                seeded_linear::<B>(no, h, true, device, seed),
                seeded_linear::<B>(h, ni, true, device, seed),
            ],
            classifier: seeded_linear::<B>(no, self.n_classes, true, device, seed),
            converter: PhaseToRateConverterConfig::with_params(no, self.mode, self.sparsity, 1.0)
                .expect("hyperparameters already validated by the config constructor")
                .init::<B>(device),
            n_input: ni,
            n_oscillators: no,
            hidden: h,
            n_classes: self.n_classes,
        }
    }

    /// Build from the reference model's exact parameters.
    ///
    /// # Errors
    ///
    /// Returns [`TrainError::ShapeMismatch`] if any tensor's shape disagrees
    /// with this config.
    pub fn init_from_params<B: Backend>(
        &self,
        params: PhaseToRateAutoencoderParams<B>,
    ) -> Result<PhaseToRateAutoencoder<B>, TrainError> {
        let (ni, no, h) = (self.n_input, self.n_oscillators, self.hidden);
        params.encoder_phase[0].validate("encoder_phase.0", h, ni)?;
        params.encoder_phase[1].validate("encoder_phase.1", no, h)?;
        params.encoder_amp[0].validate("encoder_amp.0", h, ni)?;
        params.encoder_amp[1].validate("encoder_amp.1", no, h)?;
        params.decoder[0].validate("decoder.0", h, no)?;
        params.decoder[1].validate("decoder.1", ni, h)?;
        params
            .classifier
            .validate("classifier", self.n_classes, no)?;
        check_dims("temperature", params.temperature.dims(), [1])?;

        let [pp0, pp1] = params.encoder_phase;
        let [pa0, pa1] = params.encoder_amp;
        let [pd0, pd1] = params.decoder;
        Ok(PhaseToRateAutoencoder {
            encoder_phase: [pp0.into_linear(), pp1.into_linear()],
            encoder_amp: [pa0.into_linear(), pa1.into_linear()],
            decoder: [pd0.into_linear(), pd1.into_linear()],
            classifier: params.classifier.into_linear(),
            converter: PhaseToRateConverterConfig::with_params(no, self.mode, self.sparsity, 1.0)
                .expect("hyperparameters already validated by the config constructor")
                .init_from_params(params.temperature)?,
            n_input: ni,
            n_oscillators: no,
            hidden: h,
            n_classes: self.n_classes,
        })
    }
}

/// Explicit parameters for [`PhaseToRateAutoencoderConfig::init_from_params`].
pub struct PhaseToRateAutoencoderParams<B: Backend> {
    /// `encoder_phase` `Linear` stack (`n_input -> hidden -> n_oscillators`).
    pub encoder_phase: [LinearWeights<B>; 2],
    /// `encoder_amp` `Linear` stack (`n_input -> hidden -> n_oscillators`).
    pub encoder_amp: [LinearWeights<B>; 2],
    /// `decoder` `Linear` stack (`n_oscillators -> hidden -> n_input`).
    pub decoder: [LinearWeights<B>; 2],
    /// `classifier` head (`n_oscillators -> n_classes`).
    pub classifier: LinearWeights<B>,
    /// Bottleneck converter temperature, shape `[1]`.
    pub temperature: Tensor<B, 1>,
}

/// Autoencoder with a trainable phase-to-rate bottleneck and a classifier head.
#[derive(Module, Debug)]
pub struct PhaseToRateAutoencoder<B: Backend> {
    encoder_phase: [Linear<B>; 2],
    encoder_amp: [Linear<B>; 2],
    decoder: [Linear<B>; 2],
    classifier: Linear<B>,
    converter: PhaseToRateConverter<B>,
    n_input: usize,
    n_oscillators: usize,
    hidden: usize,
    n_classes: usize,
}

impl<B: Backend> PhaseToRateAutoencoder<B> {
    /// Input feature dimension.
    pub fn n_input(&self) -> usize {
        self.n_input
    }

    /// Bottleneck oscillator count.
    pub fn n_oscillators(&self) -> usize {
        self.n_oscillators
    }

    /// Classifier-head class count.
    pub fn n_classes(&self) -> usize {
        self.n_classes
    }

    /// Validate every parameter tensor's shape after a checkpoint restore.
    ///
    /// # Errors
    ///
    /// Returns [`TrainError::ShapeMismatch`] naming the first bad tensor.
    pub fn validate_shapes(&self) -> Result<(), TrainError> {
        let (ni, no, h) = (self.n_input, self.n_oscillators, self.hidden);
        let expected = [
            (
                "encoder_phase.0",
                linear_dims(&self.encoder_phase[0]),
                (h, ni),
            ),
            (
                "encoder_phase.1",
                linear_dims(&self.encoder_phase[1]),
                (no, h),
            ),
            ("encoder_amp.0", linear_dims(&self.encoder_amp[0]), (h, ni)),
            ("encoder_amp.1", linear_dims(&self.encoder_amp[1]), (no, h)),
            ("decoder.0", linear_dims(&self.decoder[0]), (h, no)),
            ("decoder.1", linear_dims(&self.decoder[1]), (ni, h)),
            (
                "classifier",
                linear_dims(&self.classifier),
                (self.n_classes, no),
            ),
        ];
        for (name, got, want) in expected {
            if got != want {
                return Err(TrainError::ShapeMismatch {
                    name,
                    expected: vec![want.0, want.1],
                    got: vec![got.0, got.1],
                });
            }
        }
        self.converter.validate_shapes()
    }

    fn encode(&self, x: Tensor<B, 2>) -> Result<Tensor<B, 2>, TrainError> {
        let batch = x.dims()[0];
        check_dims("x", x.dims(), [batch, self.n_input])?;
        let phase = linear_forward(&self.encoder_phase, x.clone());
        let amplitude = softplus(linear_forward(&self.encoder_amp, x), 1.0);
        self.converter.forward(phase, amplitude)
    }

    /// Full forward pass: returns `(reconstruction, sparse_rates)`.
    ///
    /// # Errors
    ///
    /// Returns [`TrainError::ShapeMismatch`] if `x`'s width is not
    /// [`Self::n_input`].
    pub fn forward(&self, x: Tensor<B, 2>) -> Result<(Tensor<B, 2>, Tensor<B, 2>), TrainError> {
        let rates = self.encode(x)?;
        let reconstruction = linear_forward(&self.decoder, rates.clone());
        Ok((reconstruction, rates))
    }

    /// Classifier path: `log_softmax(classifier(sparse_rates))`.
    ///
    /// # Errors
    ///
    /// See [`Self::forward`].
    pub fn classify(&self, x: Tensor<B, 2>) -> Result<Tensor<B, 2>, TrainError> {
        let rates = self.encode(x)?;
        Ok(log_softmax(self.classifier.forward(rates), 1))
    }
}

/// Validated hyperparameters for [`DenseAutoencoder`].
#[derive(Clone, Debug, PartialEq)]
pub struct DenseAutoencoderConfig {
    /// Input feature dimension.
    pub n_input: usize,
    /// Bottleneck dimension.
    pub n_bottleneck: usize,
    /// Hidden width of the encoder/decoder MLPs (PRINet 3.0 hardcodes `256`).
    pub hidden: usize,
    /// Number of classifier-head classes (PRINet 3.0 hardcodes `10`).
    pub n_classes: usize,
}

impl DenseAutoencoderConfig {
    /// Construct with PRINet 3.0 defaults (`hidden=256`, `n_classes=10`).
    ///
    /// # Errors
    ///
    /// See [`Self::with_params`].
    pub fn new(n_input: usize, n_bottleneck: usize) -> Result<Self, TrainError> {
        Self::with_params(n_input, n_bottleneck, 256, 10)
    }

    /// Construct with explicit hyperparameters.
    ///
    /// # Errors
    ///
    /// Returns [`TrainError::EmptyBand`] for a zero dimension.
    pub fn with_params(
        n_input: usize,
        n_bottleneck: usize,
        hidden: usize,
        n_classes: usize,
    ) -> Result<Self, TrainError> {
        for (name, value) in [
            ("n_input", n_input),
            ("n_bottleneck", n_bottleneck),
            ("hidden", hidden),
            ("n_classes", n_classes),
        ] {
            if value == 0 {
                return Err(TrainError::EmptyBand { name });
            }
        }
        Ok(Self {
            n_input,
            n_bottleneck,
            hidden,
            n_classes,
        })
    }

    /// Initialize with Xavier-uniform `Linear` weights drawn from `seed`.
    pub fn init<B: Backend>(&self, device: &B::Device, seed: &mut Seed) -> DenseAutoencoder<B> {
        let (ni, nb, h) = (self.n_input, self.n_bottleneck, self.hidden);
        DenseAutoencoder {
            encoder: [
                seeded_linear::<B>(ni, h, true, device, seed),
                seeded_linear::<B>(h, nb, true, device, seed),
            ],
            decoder: [
                seeded_linear::<B>(nb, h, true, device, seed),
                seeded_linear::<B>(h, ni, true, device, seed),
            ],
            classifier: seeded_linear::<B>(nb, self.n_classes, true, device, seed),
            n_input: ni,
            n_bottleneck: nb,
            hidden: h,
            n_classes: self.n_classes,
        }
    }

    /// Build from the reference model's exact parameters.
    ///
    /// # Errors
    ///
    /// Returns [`TrainError::ShapeMismatch`] if any tensor's shape disagrees
    /// with this config.
    pub fn init_from_params<B: Backend>(
        &self,
        params: DenseAutoencoderParams<B>,
    ) -> Result<DenseAutoencoder<B>, TrainError> {
        let (ni, nb, h) = (self.n_input, self.n_bottleneck, self.hidden);
        params.encoder[0].validate("encoder.0", h, ni)?;
        params.encoder[1].validate("encoder.1", nb, h)?;
        params.decoder[0].validate("decoder.0", h, nb)?;
        params.decoder[1].validate("decoder.1", ni, h)?;
        params
            .classifier
            .validate("classifier", self.n_classes, nb)?;

        let [pe0, pe1] = params.encoder;
        let [pd0, pd1] = params.decoder;
        Ok(DenseAutoencoder {
            encoder: [pe0.into_linear(), pe1.into_linear()],
            decoder: [pd0.into_linear(), pd1.into_linear()],
            classifier: params.classifier.into_linear(),
            n_input: ni,
            n_bottleneck: nb,
            hidden: h,
            n_classes: self.n_classes,
        })
    }
}

/// Explicit parameters for [`DenseAutoencoderConfig::init_from_params`].
pub struct DenseAutoencoderParams<B: Backend> {
    /// `encoder` `Linear` stack (`n_input -> hidden -> n_bottleneck`).
    pub encoder: [LinearWeights<B>; 2],
    /// `decoder` `Linear` stack (`n_bottleneck -> hidden -> n_input`).
    pub decoder: [LinearWeights<B>; 2],
    /// `classifier` head (`n_bottleneck -> n_classes`).
    pub classifier: LinearWeights<B>,
}

/// Non-oscillatory dense-MLP autoencoder baseline with a classifier head.
#[derive(Module, Debug)]
pub struct DenseAutoencoder<B: Backend> {
    encoder: [Linear<B>; 2],
    decoder: [Linear<B>; 2],
    classifier: Linear<B>,
    n_input: usize,
    n_bottleneck: usize,
    hidden: usize,
    n_classes: usize,
}

impl<B: Backend> DenseAutoencoder<B> {
    /// Input feature dimension.
    pub fn n_input(&self) -> usize {
        self.n_input
    }

    /// Bottleneck dimension.
    pub fn n_bottleneck(&self) -> usize {
        self.n_bottleneck
    }

    /// Classifier-head class count.
    pub fn n_classes(&self) -> usize {
        self.n_classes
    }

    /// Validate every parameter tensor's shape after a checkpoint restore.
    ///
    /// # Errors
    ///
    /// Returns [`TrainError::ShapeMismatch`] naming the first bad tensor.
    pub fn validate_shapes(&self) -> Result<(), TrainError> {
        let (ni, nb, h) = (self.n_input, self.n_bottleneck, self.hidden);
        let expected = [
            ("encoder.0", linear_dims(&self.encoder[0]), (h, ni)),
            ("encoder.1", linear_dims(&self.encoder[1]), (nb, h)),
            ("decoder.0", linear_dims(&self.decoder[0]), (h, nb)),
            ("decoder.1", linear_dims(&self.decoder[1]), (ni, h)),
            (
                "classifier",
                linear_dims(&self.classifier),
                (self.n_classes, nb),
            ),
        ];
        for (name, got, want) in expected {
            if got != want {
                return Err(TrainError::ShapeMismatch {
                    name,
                    expected: vec![want.0, want.1],
                    got: vec![got.0, got.1],
                });
            }
        }
        Ok(())
    }

    fn encode(&self, x: Tensor<B, 2>) -> Result<Tensor<B, 2>, TrainError> {
        let batch = x.dims()[0];
        check_dims("x", x.dims(), [batch, self.n_input])?;
        Ok(relu(linear_forward(&self.encoder, x)))
    }

    /// Full forward pass: returns `(reconstruction, bottleneck_codes)`.
    ///
    /// # Errors
    ///
    /// Returns [`TrainError::ShapeMismatch`] if `x`'s width is not
    /// [`Self::n_input`].
    pub fn forward(&self, x: Tensor<B, 2>) -> Result<(Tensor<B, 2>, Tensor<B, 2>), TrainError> {
        let codes = self.encode(x)?;
        let reconstruction = linear_forward(&self.decoder, codes.clone());
        Ok((reconstruction, codes))
    }

    /// Classifier path: `log_softmax(classifier(bottleneck_codes))`.
    ///
    /// # Errors
    ///
    /// See [`Self::forward`].
    pub fn classify(&self, x: Tensor<B, 2>) -> Result<Tensor<B, 2>, TrainError> {
        let codes = self.encode(x)?;
        Ok(log_softmax(self.classifier.forward(codes), 1))
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

    fn t2(data: Vec<f64>, rows: usize, cols: usize) -> Tensor<TestBackend, 2> {
        Tensor::from_data(TensorData::new(data, vec![rows, cols]), &device())
    }

    fn t1(value: f64) -> Tensor<TestBackend, 1> {
        Tensor::from_data(TensorData::new(vec![value], vec![1]), &device())
    }

    // --- PhaseToRateMode ---

    #[test]
    fn mode_parse_and_display_round_trip() {
        for text in ["soft", "hard", "annealed"] {
            assert_eq!(PhaseToRateMode::parse(text).unwrap().as_str(), text);
        }
        assert!(matches!(
            PhaseToRateMode::parse("bogus").unwrap_err(),
            TrainError::NonFiniteParameter { name: "mode", .. }
        ));
    }

    // --- phase_to_rate ---

    #[test]
    fn phase_to_rate_soft_matches_reference_formula() {
        let phase = t2(vec![0.0, 1.0, 2.0, 0.5], 1, 4);
        let amplitude = t2(vec![1.0, 2.0, 0.5, 3.0], 1, 4);
        let got = phase_to_rate(phase, amplitude, PhaseToRateMode::Soft, 0.1, t1(0.7))
            .unwrap()
            .to_data()
            .to_vec::<f64>()
            .unwrap();

        let rates: Vec<f64> = [(0.0, 1.0), (1.0, 2.0), (2.0, 0.5), (0.5, 3.0)]
            .into_iter()
            .map(|(p, a): (f64, f64)| a * (1.0 + p.cos()) / 2.0)
            .collect();
        let scaled: Vec<f64> = rates.iter().map(|r| (r / 0.7).exp()).collect();
        let denom: f64 = scaled.iter().sum();
        for (g, s) in got.iter().zip(scaled) {
            assert!((g - s / denom).abs() < 1e-12, "{g} vs {}", s / denom);
        }
    }

    #[test]
    fn phase_to_rate_hard_selects_topk_values() {
        let phase = t2(vec![0.0, 0.0, 0.0, 0.0], 1, 4);
        let amplitude = t2(vec![1.0, 4.0, 2.0, 3.0], 1, 4);
        // rate = amplitude (phase 0 -> factor 1); sparsity 0.5 -> k = 2.
        let got = phase_to_rate(phase, amplitude, PhaseToRateMode::Hard, 0.5, t1(1.0))
            .unwrap()
            .to_data()
            .to_vec::<f64>()
            .unwrap();
        assert_eq!(got, vec![0.0, 4.0, 0.0, 3.0]);
    }

    #[test]
    fn phase_to_rate_annealed_interpolates_soft_and_hard() {
        let phase = t2(vec![0.0, 0.0, 0.0, 0.0], 1, 4);
        let amplitude = t2(vec![1.0, 4.0, 2.0, 3.0], 1, 4);
        let temp = 2.0;
        let soft = phase_to_rate(
            phase.clone(),
            amplitude.clone(),
            PhaseToRateMode::Soft,
            0.5,
            t1(temp),
        )
        .unwrap()
        .to_data()
        .to_vec::<f64>()
        .unwrap();
        let hard = phase_to_rate(
            phase.clone(),
            amplitude.clone(),
            PhaseToRateMode::Hard,
            0.5,
            t1(temp),
        )
        .unwrap()
        .to_data()
        .to_vec::<f64>()
        .unwrap();
        let annealed = phase_to_rate(phase, amplitude, PhaseToRateMode::Annealed, 0.5, t1(temp))
            .unwrap()
            .to_data()
            .to_vec::<f64>()
            .unwrap();
        let blend = 1.0 / (1.0 + (1.0 - 1.0 / temp).exp());
        for ((a, s), h) in annealed.iter().zip(soft).zip(hard) {
            let expected = (1.0 - blend) * s + blend * h;
            assert!((a - expected).abs() < 1e-12, "{a} vs {expected}");
        }
    }

    #[test]
    fn phase_to_rate_validates_shapes_and_sparsity() {
        assert!(matches!(
            phase_to_rate(
                t2(vec![0.0; 4], 1, 4),
                t2(vec![0.0; 3], 1, 3),
                PhaseToRateMode::Soft,
                0.1,
                t1(1.0),
            )
            .unwrap_err(),
            TrainError::ShapeMismatch {
                name: "amplitude",
                ..
            }
        ));
        assert!(matches!(
            phase_to_rate(
                t2(vec![0.0; 4], 1, 4),
                t2(vec![0.0; 4], 1, 4),
                PhaseToRateMode::Soft,
                1.5,
                t1(1.0),
            )
            .unwrap_err(),
            TrainError::InvalidRatio {
                name: "sparsity",
                ..
            }
        ));
        assert!(matches!(
            phase_to_rate(
                t2(vec![0.0; 4], 1, 4),
                t2(vec![0.0; 4], 1, 4),
                PhaseToRateMode::Soft,
                0.1,
                Tensor::<TestBackend, 1>::from_data(
                    TensorData::new(vec![1.0, 2.0], vec![2]),
                    &device()
                ),
            )
            .unwrap_err(),
            TrainError::ShapeMismatch {
                name: "temperature",
                ..
            }
        ));
    }

    #[test]
    fn phase_to_rate_soft_gradients_flow_to_inputs_and_temperature() {
        let _guard = crate::support::autodiff_test_guard();
        let dev: <TestAutodiffBackend as Backend>::Device = Default::default();
        let phase = Tensor::<TestAutodiffBackend, 2>::from_data(
            TensorData::new(vec![0.1, 0.9, 1.7, 2.4], vec![1, 4]),
            &dev,
        )
        .require_grad();
        let amplitude = Tensor::<TestAutodiffBackend, 2>::from_data(
            TensorData::new(vec![1.0, 2.0, 0.5, 3.0], vec![1, 4]),
            &dev,
        )
        .require_grad();
        let temperature =
            Tensor::<TestAutodiffBackend, 1>::from_data(TensorData::new(vec![0.8], vec![1]), &dev)
                .require_grad();
        let out = phase_to_rate(
            phase.clone(),
            amplitude.clone(),
            PhaseToRateMode::Soft,
            0.1,
            temperature.clone(),
        )
        .unwrap();
        let grads = (out.clone() * out).sum().backward();
        let finite2 = |t: Option<Tensor<TestBackend, 2>>| {
            t.expect("soft mode is differentiable")
                .to_data()
                .to_vec::<f64>()
                .unwrap()
                .iter()
                .all(|v| v.is_finite())
        };
        assert!(finite2(phase.grad(&grads)));
        assert!(finite2(amplitude.grad(&grads)));
        let temp_grad = temperature
            .grad(&grads)
            .expect("soft mode is differentiable in the temperature")
            .to_data()
            .to_vec::<f64>()
            .unwrap();
        assert!(temp_grad.iter().all(|v| v.is_finite()));
        assert!(temp_grad.iter().any(|v| v.abs() > 0.0));
    }

    #[test]
    fn phase_to_rate_hard_ste_gradient_has_input_shape() {
        let _guard = crate::support::autodiff_test_guard();
        let dev: <TestAutodiffBackend as Backend>::Device = Default::default();
        let phase = Tensor::<TestAutodiffBackend, 2>::from_data(
            TensorData::new(vec![0.1, 0.4, 0.2, 0.9], vec![1, 4]),
            &dev,
        )
        .require_grad();
        let amplitude = Tensor::<TestAutodiffBackend, 2>::from_data(
            TensorData::new(vec![1.0, 4.0, 2.0, 3.0], vec![1, 4]),
            &dev,
        )
        .require_grad();
        let temperature =
            Tensor::<TestAutodiffBackend, 1>::from_data(TensorData::new(vec![1.0], vec![1]), &dev);
        let out = phase_to_rate(
            phase.clone(),
            amplitude.clone(),
            PhaseToRateMode::Hard,
            0.5,
            temperature,
        )
        .unwrap();
        let grads = out.sum().backward();
        let g_amp = amplitude
            .grad(&grads)
            .expect("the STE routes a gradient to the selected amplitudes")
            .to_data()
            .to_vec::<f64>()
            .unwrap();
        assert_eq!(g_amp.len(), 4);
        assert!(g_amp.iter().all(|v| v.is_finite()));
        assert!(g_amp.iter().any(|v| v.abs() > 0.0));
    }

    // --- PhaseToRateConverter ---

    #[test]
    fn converter_config_validation() {
        assert!(matches!(
            PhaseToRateConverterConfig::new(0).unwrap_err(),
            TrainError::EmptyBand { .. }
        ));
        assert!(matches!(
            PhaseToRateConverterConfig::with_params(4, PhaseToRateMode::Soft, 2.0, 1.0)
                .unwrap_err(),
            TrainError::InvalidRatio {
                name: "sparsity",
                ..
            }
        ));
        assert!(matches!(
            PhaseToRateConverterConfig::with_params(4, PhaseToRateMode::Soft, 0.1, 0.0)
                .unwrap_err(),
            TrainError::InvalidPositiveParameter {
                name: "initial_temperature",
                ..
            }
        ));
    }

    #[test]
    fn converter_forward_matches_free_function_and_reports_config() {
        let converter =
            PhaseToRateConverterConfig::with_params(4, PhaseToRateMode::Soft, 0.25, 0.6)
                .unwrap()
                .init::<TestBackend>(&device());
        assert_eq!(converter.n_oscillators(), 4);
        assert_eq!(converter.mode(), PhaseToRateMode::Soft);
        assert!((converter.sparsity() - 0.25).abs() < 1e-15);
        converter.validate_shapes().unwrap();

        let phase = t2(vec![0.2, 1.1, 2.0, 0.7], 1, 4);
        let amplitude = t2(vec![1.0, 2.0, 0.5, 3.0], 1, 4);
        let got = converter
            .forward(phase.clone(), amplitude.clone())
            .unwrap()
            .to_data()
            .to_vec::<f64>()
            .unwrap();
        let want = phase_to_rate(phase, amplitude, PhaseToRateMode::Soft, 0.25, t1(0.6))
            .unwrap()
            .to_data()
            .to_vec::<f64>()
            .unwrap();
        assert_eq!(got, want);
    }

    #[test]
    fn converter_rejects_wrong_input_width() {
        let converter = PhaseToRateConverterConfig::new(4)
            .unwrap()
            .init::<TestBackend>(&device());
        assert!(matches!(
            converter
                .forward(t2(vec![0.0; 3], 1, 3), t2(vec![0.0; 3], 1, 3))
                .unwrap_err(),
            TrainError::ShapeMismatch { name: "phase", .. }
        ));
    }

    #[test]
    fn converter_init_from_params_validates_temperature_shape() {
        let bad = Tensor::<TestBackend, 1>::from_data(
            TensorData::new(vec![1.0, 2.0], vec![2]),
            &device(),
        );
        assert!(matches!(
            PhaseToRateConverterConfig::new(4)
                .unwrap()
                .init_from_params(bad)
                .unwrap_err(),
            TrainError::ShapeMismatch {
                name: "temperature",
                ..
            }
        ));
    }

    // --- PhaseToRateAutoencoder ---

    fn ptr_ae_config() -> PhaseToRateAutoencoderConfig {
        PhaseToRateAutoencoderConfig::with_params(6, 4, 5, 3, 0.1, PhaseToRateMode::Soft).unwrap()
    }

    #[test]
    fn phase_to_rate_autoencoder_forward_and_classify_shapes() {
        let mut seed = Seed::new(3, 0);
        let ae = ptr_ae_config().init::<TestBackend>(&device(), &mut seed);
        assert_eq!(ae.n_input(), 6);
        assert_eq!(ae.n_oscillators(), 4);
        assert_eq!(ae.n_classes(), 3);
        ae.validate_shapes().unwrap();

        let x = t2(vec![0.3; 12], 2, 6);
        let (recon, rates) = ae.forward(x.clone()).unwrap();
        assert_eq!(recon.dims(), [2, 6]);
        assert_eq!(rates.dims(), [2, 4]);
        assert!(rates
            .to_data()
            .to_vec::<f64>()
            .unwrap()
            .iter()
            .all(|v| *v >= 0.0));

        let logits = ae.classify(x).unwrap();
        assert_eq!(logits.dims(), [2, 3]);
        for row in logits.exp().sum_dim(1).to_data().to_vec::<f64>().unwrap() {
            assert!((row - 1.0).abs() < 1e-9, "log_softmax row sums to {row}");
        }
    }

    #[test]
    fn phase_to_rate_autoencoder_rejects_wrong_input_width() {
        let mut seed = Seed::new(3, 0);
        let ae = ptr_ae_config().init::<TestBackend>(&device(), &mut seed);
        assert!(matches!(
            ae.forward(t2(vec![0.0; 5], 1, 5)).unwrap_err(),
            TrainError::ShapeMismatch { name: "x", .. }
        ));
    }

    #[test]
    fn phase_to_rate_autoencoder_gradients_flow_to_every_parameter() {
        let _guard = crate::support::autodiff_test_guard();
        let dev: <TestAutodiffBackend as Backend>::Device = Default::default();
        let mut seed = Seed::new(9, 0);
        let ae = ptr_ae_config().init::<TestAutodiffBackend>(&dev, &mut seed);
        let x = Tensor::<TestAutodiffBackend, 2>::from_data(
            TensorData::new(vec![0.2; 12], vec![2, 6]),
            &dev,
        )
        .require_grad();
        let (recon, rates) = ae.forward(x.clone()).unwrap();
        let logits = ae.classify(x.clone()).unwrap();
        let loss = recon.sum() + rates.sum() + logits.sum();
        let grads = loss.backward();
        assert!(x.grad(&grads).is_some());
        assert!(ae.encoder_phase[0].weight.grad(&grads).is_some());
        assert!(ae.encoder_amp[1].weight.grad(&grads).is_some());
        assert!(ae.decoder[0].weight.grad(&grads).is_some());
        assert!(ae.classifier.weight.grad(&grads).is_some());
        assert!(ae.converter.temperature.grad(&grads).is_some());
    }

    #[test]
    fn phase_to_rate_autoencoder_init_from_params_validates_and_round_trips() {
        let cfg = ptr_ae_config();
        let (ni, no, h) = (cfg.n_input, cfg.n_oscillators, cfg.hidden);
        let lw = |out_f: usize, in_f: usize, fill: f64| LinearWeights {
            weight: t2(vec![fill; out_f * in_f], out_f, in_f),
            bias: Tensor::<TestBackend, 1>::from_data(
                TensorData::new(vec![0.0; out_f], vec![out_f]),
                &device(),
            ),
        };
        let params = || PhaseToRateAutoencoderParams {
            encoder_phase: [lw(h, ni, 0.01), lw(no, h, 0.02)],
            encoder_amp: [lw(h, ni, 0.03), lw(no, h, 0.04)],
            decoder: [lw(h, no, 0.05), lw(ni, h, 0.06)],
            classifier: lw(cfg.n_classes, no, 0.07),
            temperature: t1(1.0),
        };
        let ae = cfg.init_from_params(params()).unwrap();
        let x = t2(vec![0.5; ni], 1, ni);
        assert_eq!(ae.forward(x).unwrap().0.dims(), [1, ni]);

        let mut bad = params();
        bad.classifier = lw(cfg.n_classes + 1, no, 0.07);
        assert!(matches!(
            cfg.init_from_params(bad).unwrap_err(),
            TrainError::ShapeMismatch {
                name: "classifier",
                ..
            }
        ));
    }

    #[test]
    fn phase_to_rate_autoencoder_validate_shapes_detects_mismatched_record() {
        use burn::record::{BinBytesRecorder, DoublePrecisionSettings, Recorder};
        let dev = device();
        let mut seed = Seed::new(1, 0);
        let target = ptr_ae_config().init::<TestBackend>(&dev, &mut seed);
        let donor =
            PhaseToRateAutoencoderConfig::with_params(6, 4, 7, 3, 0.1, PhaseToRateMode::Soft)
                .unwrap()
                .init::<TestBackend>(&dev, &mut Seed::new(2, 0));
        let recorder = BinBytesRecorder::<DoublePrecisionSettings>::default();
        let bytes = Recorder::<TestBackend>::record(&recorder, donor.into_record(), ()).unwrap();
        let record = Recorder::<TestBackend>::load(&recorder, bytes, &dev).unwrap();
        let candidate = target.load_record(record);
        assert!(matches!(
            candidate.validate_shapes().unwrap_err(),
            TrainError::ShapeMismatch { .. }
        ));
    }

    #[test]
    fn phase_to_rate_autoencoder_config_rejects_zero_dims() {
        assert!(matches!(
            PhaseToRateAutoencoderConfig::with_params(0, 4, 5, 3, 0.1, PhaseToRateMode::Soft)
                .unwrap_err(),
            TrainError::EmptyBand { name: "n_input" }
        ));
        assert!(matches!(
            PhaseToRateAutoencoderConfig::with_params(6, 4, 5, 3, 2.0, PhaseToRateMode::Soft)
                .unwrap_err(),
            TrainError::InvalidRatio {
                name: "sparsity",
                ..
            }
        ));
    }

    // --- DenseAutoencoder ---

    fn dense_config() -> DenseAutoencoderConfig {
        DenseAutoencoderConfig::with_params(6, 4, 5, 3).unwrap()
    }

    #[test]
    fn dense_autoencoder_forward_and_classify_shapes() {
        let mut seed = Seed::new(5, 0);
        let ae = dense_config().init::<TestBackend>(&device(), &mut seed);
        assert_eq!(ae.n_input(), 6);
        assert_eq!(ae.n_bottleneck(), 4);
        assert_eq!(ae.n_classes(), 3);
        ae.validate_shapes().unwrap();

        let x = t2(vec![0.4; 12], 2, 6);
        let (recon, codes) = ae.forward(x.clone()).unwrap();
        assert_eq!(recon.dims(), [2, 6]);
        assert_eq!(codes.dims(), [2, 4]);
        assert!(codes
            .to_data()
            .to_vec::<f64>()
            .unwrap()
            .iter()
            .all(|v| *v >= 0.0));

        let logits = ae.classify(x).unwrap();
        assert_eq!(logits.dims(), [2, 3]);
        for row in logits.exp().sum_dim(1).to_data().to_vec::<f64>().unwrap() {
            assert!((row - 1.0).abs() < 1e-9);
        }
    }

    #[test]
    fn dense_autoencoder_gradients_flow_and_errors_are_typed() {
        let _guard = crate::support::autodiff_test_guard();
        let dev: <TestAutodiffBackend as Backend>::Device = Default::default();
        let mut seed = Seed::new(7, 0);
        let ae = dense_config().init::<TestAutodiffBackend>(&dev, &mut seed);
        let x = Tensor::<TestAutodiffBackend, 2>::from_data(
            TensorData::new(vec![0.3; 12], vec![2, 6]),
            &dev,
        )
        .require_grad();
        let (recon, codes) = ae.forward(x.clone()).unwrap();
        let logits = ae.classify(x.clone()).unwrap();
        let grads = (recon.sum() + codes.sum() + logits.sum()).backward();
        assert!(x.grad(&grads).is_some());
        assert!(ae.encoder[0].weight.grad(&grads).is_some());
        assert!(ae.decoder[1].weight.grad(&grads).is_some());
        assert!(ae.classifier.weight.grad(&grads).is_some());

        assert!(matches!(
            ae.forward(Tensor::<TestAutodiffBackend, 2>::zeros([1, 5], &dev))
                .unwrap_err(),
            TrainError::ShapeMismatch { name: "x", .. }
        ));
    }

    #[test]
    fn dense_autoencoder_init_from_params_and_validate_shapes() {
        let cfg = dense_config();
        let (ni, nb, h) = (cfg.n_input, cfg.n_bottleneck, cfg.hidden);
        let lw = |out_f: usize, in_f: usize| LinearWeights {
            weight: t2(vec![0.02; out_f * in_f], out_f, in_f),
            bias: Tensor::<TestBackend, 1>::from_data(
                TensorData::new(vec![0.0; out_f], vec![out_f]),
                &device(),
            ),
        };
        let params = DenseAutoencoderParams {
            encoder: [lw(h, ni), lw(nb, h)],
            decoder: [lw(h, nb), lw(ni, h)],
            classifier: lw(cfg.n_classes, nb),
        };
        let ae = cfg.init_from_params(params).unwrap();
        assert_eq!(
            ae.forward(t2(vec![0.5; ni], 1, ni)).unwrap().1.dims(),
            [1, nb]
        );

        let bad = DenseAutoencoderParams {
            encoder: [lw(h, ni), lw(nb, h)],
            decoder: [lw(h, nb), lw(ni + 1, h)],
            classifier: lw(cfg.n_classes, nb),
        };
        assert!(matches!(
            cfg.init_from_params(bad).unwrap_err(),
            TrainError::ShapeMismatch {
                name: "decoder.1",
                ..
            }
        ));

        assert!(matches!(
            DenseAutoencoderConfig::with_params(6, 0, 5, 3).unwrap_err(),
            TrainError::EmptyBand {
                name: "n_bottleneck"
            }
        ));
    }
}
