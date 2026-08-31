//! Feedforward inhibition and dentate-gyrus sparsification layers.
//!
//! This module ports PRINet 3.0's phase-to-rate gate and
//! FFI → EMA → FBI dentate-gyrus pipeline to Burn. The feedback stage composes
//! [`crate::inhibition::FeedbackInhibition`], retaining its hard-forward /
//! soft-backward straight-through estimator.

use burn::module::{Module, Param};
use burn::tensor::backend::Backend;
use burn::tensor::Tensor;

use crate::error::TrainError;
use crate::inhibition::{FeedbackInhibition, FeedbackInhibitionConfig};
use crate::support::{check_dims, validate_finite};

/// Validated hyperparameters for [`FeedforwardInhibition`].
#[derive(Clone, Debug, PartialEq)]
pub struct FeedforwardInhibitionConfig {
    /// Compatibility delay in integration steps.
    pub delay_steps: usize,
    /// Exponential-envelope time constant.
    pub tau: f64,
    /// Fraction of a cycle used for the phase-delay gate.
    pub delay_fraction: f64,
}

impl FeedforwardInhibitionConfig {
    /// Construct with PRINet 3.0 defaults.
    pub fn new() -> Self {
        Self {
            delay_steps: 1,
            tau: 0.05,
            delay_fraction: 0.1,
        }
    }

    /// Construct with explicit hyperparameters.
    ///
    /// # Errors
    ///
    /// Returns [`TrainError::NonFiniteParameter`] for a non-finite value and
    /// [`TrainError::InvalidPositiveParameter`] when `tau <= 0`.
    pub fn with_params(
        delay_steps: usize,
        tau: f64,
        delay_fraction: f64,
    ) -> Result<Self, TrainError> {
        validate_finite("tau", tau)?;
        validate_finite("delay_fraction", delay_fraction)?;
        if tau <= 0.0 {
            return Err(TrainError::InvalidPositiveParameter {
                name: "tau",
                value: tau,
            });
        }
        Ok(Self {
            delay_steps,
            tau,
            delay_fraction,
        })
    }

    /// Build the parameter-free gate.
    pub fn init(&self) -> FeedforwardInhibition {
        FeedforwardInhibition {
            delay_steps: self.delay_steps,
            tau: self.tau,
            delay_fraction: self.delay_fraction,
        }
    }
}

impl Default for FeedforwardInhibitionConfig {
    fn default() -> Self {
        Self::new()
    }
}

/// Parameter-free phase-delay / exponential-decay feedforward inhibition.
#[derive(Clone, Copy, Debug, PartialEq)]
pub struct FeedforwardInhibition {
    delay_steps: usize,
    tau: f64,
    delay_fraction: f64,
}

impl FeedforwardInhibition {
    /// Compatibility delay in integration steps.
    pub fn delay_steps(&self) -> usize {
        self.delay_steps
    }

    /// Exponential-envelope time constant.
    pub fn tau(&self) -> f64 {
        self.tau
    }

    /// Apply the phase-to-rate gate to matching `[batch, n]` tensors.
    ///
    /// The formula is the reference implementation's
    /// `amplitude * (1 + cos(phase)) / 2 *
    /// exp((cos(wrap(phase + 2πf) - phase) - 1) / tau_eff)`, where
    /// `tau_eff = max(tau, 1e-8)` is the reference's division guard.
    ///
    /// # Errors
    ///
    /// Returns [`TrainError::ShapeMismatch`] when the inputs differ in shape.
    pub fn gate<B: Backend>(
        &self,
        phase: Tensor<B, 2>,
        amplitude: Tensor<B, 2>,
    ) -> Result<Tensor<B, 2>, TrainError> {
        let dims = phase.dims();
        check_dims("amplitude", amplitude.dims(), dims)?;
        let rate = amplitude * (phase.clone().cos() + 1.0).div_scalar(2.0);
        let shift = std::f64::consts::TAU * self.delay_fraction;
        let delayed = (phase.clone() + shift).remainder_scalar(std::f64::consts::TAU);
        let strength = ((delayed - phase).cos() - 1.0)
            .div_scalar(self.tau.max(1e-8))
            .exp();
        Ok(rate * strength)
    }
}

/// Validated hyperparameters for [`DentateGyrusConverter`].
#[derive(Clone, Debug, PartialEq)]
pub struct DentateGyrusConverterConfig {
    /// Number of input oscillators.
    pub n_oscillators: usize,
    /// Explicit number of FBI winners.
    pub k: Option<usize>,
    /// Target active fraction when `k` is omitted.
    pub target_sparsity: f64,
    /// FFI compatibility delay.
    pub ffi_delay: usize,
    /// FFI decay time constant.
    pub ffi_tau: f64,
    /// FBI compatibility delay.
    pub fbi_delay: usize,
    /// FBI softmax temperature.
    pub fbi_temperature: f64,
    /// EMA retention coefficient.
    pub integration_alpha: f64,
}

impl DentateGyrusConverterConfig {
    /// Construct with PRINet 3.0 defaults.
    ///
    /// # Errors
    ///
    /// Returns a typed validation error when `n_oscillators` is zero.
    pub fn new(n_oscillators: usize) -> Result<Self, TrainError> {
        Self::with_params(n_oscillators, None, 0.1, 1, 0.05, 20, 1.0, 0.95)
    }

    /// Construct with explicit hyperparameters.
    ///
    /// # Errors
    ///
    /// Returns a typed validation error for invalid sizes, sparsity, FFI
    /// parameters, FBI temperature, or EMA coefficient.
    #[allow(clippy::too_many_arguments)]
    pub fn with_params(
        n_oscillators: usize,
        k: Option<usize>,
        target_sparsity: f64,
        ffi_delay: usize,
        ffi_tau: f64,
        fbi_delay: usize,
        fbi_temperature: f64,
        integration_alpha: f64,
    ) -> Result<Self, TrainError> {
        if n_oscillators == 0 {
            return Err(TrainError::EmptyBand {
                name: "oscillators",
            });
        }
        FeedforwardInhibitionConfig::with_params(ffi_delay, ffi_tau, 0.1)?;
        FeedbackInhibitionConfig::with_params(n_oscillators, k, target_sparsity, fbi_temperature)?;
        validate_finite("integration_alpha", integration_alpha)?;
        if !(0.0..=1.0).contains(&integration_alpha) {
            return Err(TrainError::InvalidRatio {
                name: "integration_alpha",
                value: integration_alpha,
            });
        }
        Ok(Self {
            n_oscillators,
            k,
            target_sparsity,
            ffi_delay,
            ffi_tau,
            fbi_delay,
            fbi_temperature,
            integration_alpha,
        })
    }

    /// Build the parameter-free conversion pipeline.
    pub fn init(&self) -> DentateGyrusConverter {
        DentateGyrusConverter {
            n_oscillators: self.n_oscillators,
            ffi: FeedforwardInhibitionConfig {
                delay_steps: self.ffi_delay,
                tau: self.ffi_tau,
                delay_fraction: 0.1,
            }
            .init(),
            fbi: FeedbackInhibitionConfig {
                n_oscillators: self.n_oscillators,
                k: self.k,
                sparsity: self.target_sparsity,
                temperature: self.fbi_temperature,
            }
            .init(),
            fbi_delay: self.fbi_delay,
            integration_alpha: self.integration_alpha,
        }
    }
}

/// Parameter-free FFI → EMA integration → FBI sparsification pipeline.
#[derive(Clone, Copy, Debug, PartialEq)]
pub struct DentateGyrusConverter {
    n_oscillators: usize,
    ffi: FeedforwardInhibition,
    fbi: FeedbackInhibition,
    fbi_delay: usize,
    integration_alpha: f64,
}

impl DentateGyrusConverter {
    /// Number of oscillators processed by the pipeline.
    pub fn n_oscillators(&self) -> usize {
        self.n_oscillators
    }

    /// Feedforward inhibition component.
    pub fn ffi(&self) -> &FeedforwardInhibition {
        &self.ffi
    }

    /// Feedback inhibition component.
    pub fn fbi(&self) -> &FeedbackInhibition {
        &self.fbi
    }

    /// Compatibility feedback delay in integration steps.
    pub fn fbi_delay(&self) -> usize {
        self.fbi_delay
    }

    /// Run the complete conversion pipeline.
    ///
    /// # Errors
    ///
    /// Returns [`TrainError::InvalidStepCount`] when no integration step is
    /// requested, or [`TrainError::ShapeMismatch`] for incompatible inputs.
    pub fn convert<B: Backend>(
        &self,
        phase: Tensor<B, 2>,
        amplitude: Tensor<B, 2>,
        n_integration_steps: usize,
    ) -> Result<Tensor<B, 2>, TrainError> {
        if n_integration_steps == 0 {
            return Err(TrainError::InvalidStepCount {
                name: "n_integration_steps",
                value: 0,
            });
        }
        let dims = phase.dims();
        check_dims("phase", dims, [dims[0], self.n_oscillators])?;
        check_dims("amplitude", amplitude.dims(), dims)?;
        let mut integrated = self.ffi.gate(phase.clone(), amplitude.clone())?;
        let mut phase_step = phase;
        for _ in 1..n_integration_steps {
            phase_step =
                (phase_step + 0.1 * std::f64::consts::TAU).remainder_scalar(std::f64::consts::TAU);
            let new_gated = self.ffi.gate(phase_step.clone(), amplitude.clone())?;
            integrated = integrated.mul_scalar(self.integration_alpha)
                + new_gated.mul_scalar(1.0 - self.integration_alpha);
        }
        self.fbi.compete(integrated)
    }
}

/// Explicit scalar parameters for [`DgLayer`].
pub struct DgLayerParams<B: Backend> {
    /// Multiplicative FFI amplitude scale, shape `[1]`.
    pub ffi_scale: Tensor<B, 1>,
    /// FBI softmax temperature, shape `[1]`.
    pub fbi_temperature: Tensor<B, 1>,
}

/// Validated hyperparameters for [`DgLayer`].
#[derive(Clone, Debug, PartialEq)]
pub struct DgLayerConfig {
    /// Input oscillator count.
    pub n_input: usize,
    /// Number of FBI winners.
    pub top_k: usize,
    /// FFI compatibility delay.
    pub ffi_delay: usize,
    /// FBI compatibility delay.
    pub fbi_delay: usize,
    /// EMA integration-step count.
    pub n_integration_steps: usize,
}

impl DgLayerConfig {
    /// Construct with PRINet 3.0 defaults.
    ///
    /// # Errors
    ///
    /// Returns a typed error for zero `n_input` or invalid `top_k`.
    pub fn new(n_input: usize) -> Result<Self, TrainError> {
        Self::with_params(n_input, 8, 2, 20, 5)
    }

    /// Construct with explicit hyperparameters.
    ///
    /// # Errors
    ///
    /// Returns a typed validation error for zero dimensions, winner count, or
    /// integration-step count.
    pub fn with_params(
        n_input: usize,
        top_k: usize,
        ffi_delay: usize,
        fbi_delay: usize,
        n_integration_steps: usize,
    ) -> Result<Self, TrainError> {
        if n_input == 0 {
            return Err(TrainError::EmptyBand { name: "input" });
        }
        if top_k == 0 {
            return Err(TrainError::InvalidTopK { k: top_k });
        }
        if n_integration_steps == 0 {
            return Err(TrainError::InvalidStepCount {
                name: "n_integration_steps",
                value: n_integration_steps,
            });
        }
        Ok(Self {
            n_input,
            top_k,
            ffi_delay,
            fbi_delay,
            n_integration_steps,
        })
    }

    /// Initialize reference-default scalar parameters.
    pub fn init<B: Backend>(&self, device: &B::Device) -> DgLayer<B> {
        DgLayer {
            ffi_scale: Param::initialized(
                Default::default(),
                Tensor::ones([1], device).require_grad(),
            ),
            fbi_temperature: Param::initialized(
                Default::default(),
                Tensor::ones([1], device).require_grad(),
            ),
            n_input: self.n_input,
            top_k: self.top_k.min(self.n_input),
            ffi_delay: self.ffi_delay,
            fbi_delay: self.fbi_delay,
            n_integration_steps: self.n_integration_steps,
            integration_alpha: 0.95,
        }
    }

    /// Initialize from explicit scalar parameter tensors.
    ///
    /// # Errors
    ///
    /// Returns [`TrainError::ShapeMismatch`] unless both tensors have shape
    /// `[1]`.
    pub fn init_from_params<B: Backend>(
        &self,
        params: DgLayerParams<B>,
    ) -> Result<DgLayer<B>, TrainError> {
        check_dims("ffi_scale", params.ffi_scale.dims(), [1])?;
        check_dims("fbi_temperature", params.fbi_temperature.dims(), [1])?;
        Ok(DgLayer {
            ffi_scale: Param::initialized(Default::default(), params.ffi_scale.require_grad()),
            fbi_temperature: Param::initialized(
                Default::default(),
                params.fbi_temperature.require_grad(),
            ),
            n_input: self.n_input,
            top_k: self.top_k.min(self.n_input),
            ffi_delay: self.ffi_delay,
            fbi_delay: self.fbi_delay,
            n_integration_steps: self.n_integration_steps,
            integration_alpha: 0.95,
        })
    }
}

/// Trainable dentate-gyrus layer with Rust-owned FFI scale and FBI temperature.
#[derive(Module, Debug)]
pub struct DgLayer<B: Backend> {
    ffi_scale: Param<Tensor<B, 1>>,
    fbi_temperature: Param<Tensor<B, 1>>,
    n_input: usize,
    top_k: usize,
    ffi_delay: usize,
    fbi_delay: usize,
    n_integration_steps: usize,
    integration_alpha: f64,
}

impl<B: Backend> DgLayer<B> {
    /// Input oscillator count.
    pub fn n_input(&self) -> usize {
        self.n_input
    }

    /// Number of winners retained by FBI.
    pub fn top_k(&self) -> usize {
        self.top_k
    }

    /// Compatibility feedback delay.
    pub fn fbi_delay(&self) -> usize {
        self.fbi_delay
    }

    /// EMA integration-step count.
    pub fn n_integration_steps(&self) -> usize {
        self.n_integration_steps
    }

    /// Validate Rust-owned parameter shapes after checkpoint restoration.
    ///
    /// # Errors
    ///
    /// Returns [`TrainError::ShapeMismatch`] for a malformed parameter record.
    pub fn validate_shapes(&self) -> Result<(), TrainError> {
        check_dims("ffi_scale", self.ffi_scale.val().dims(), [1])?;
        check_dims("fbi_temperature", self.fbi_temperature.val().dims(), [1])
    }

    /// Run the trainable FFI → EMA → FBI conversion.
    ///
    /// # Errors
    ///
    /// Returns [`TrainError::ShapeMismatch`] for incompatible inputs.
    pub fn forward(
        &self,
        phase: Tensor<B, 2>,
        amplitude: Tensor<B, 2>,
    ) -> Result<Tensor<B, 2>, TrainError> {
        let dims = phase.dims();
        check_dims("phase", dims, [dims[0], self.n_input])?;
        check_dims("amplitude", amplitude.dims(), dims)?;
        let ffi = FeedforwardInhibitionConfig {
            delay_steps: self.ffi_delay,
            tau: 0.05,
            delay_fraction: 0.1,
        }
        .init();
        let fbi = FeedbackInhibitionConfig {
            n_oscillators: self.n_input,
            k: Some(self.top_k),
            sparsity: 0.1,
            temperature: 1.0,
        }
        .init();
        let scale = self.ffi_scale.val().clamp_min(0.01).reshape([1, 1]);
        let scaled_amplitude = amplitude * scale;
        let mut integrated = ffi.gate(phase.clone(), scaled_amplitude.clone())?;
        let mut phase_step = phase;
        for _ in 1..self.n_integration_steps {
            phase_step =
                (phase_step + 0.1 * std::f64::consts::TAU).remainder_scalar(std::f64::consts::TAU);
            let new_gated = ffi.gate(phase_step.clone(), scaled_amplitude.clone())?;
            integrated = integrated.mul_scalar(self.integration_alpha)
                + new_gated.mul_scalar(1.0 - self.integration_alpha);
        }
        fbi.compete_with_temperature(integrated, self.fbi_temperature.val().clamp_min(1e-8))
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

    #[test]
    fn ffi_rejects_invalid_tau() {
        assert!(matches!(
            FeedforwardInhibitionConfig::with_params(1, 0.0, 0.1).unwrap_err(),
            TrainError::InvalidPositiveParameter { name: "tau", .. }
        ));
    }

    #[test]
    fn ffi_matches_reference_formula() {
        let ffi = FeedforwardInhibitionConfig::new().init();
        let phase = Tensor::<TestBackend, 2>::from_data(
            TensorData::new(vec![0.0, 1.0, 2.0], vec![1, 3]),
            &device(),
        );
        let amplitude = Tensor::<TestBackend, 2>::from_data(
            TensorData::new(vec![1.0, 2.0, 0.5], vec![1, 3]),
            &device(),
        );
        let got = ffi
            .gate(phase, amplitude)
            .unwrap()
            .to_data()
            .to_vec::<f64>()
            .unwrap();
        let strength = (((0.2 * std::f64::consts::PI).cos() - 1.0) / 0.05).exp();
        let expected = [
            (1.0_f64 + 0.0_f64.cos()) * 0.5 * strength,
            2.0 * (1.0_f64 + 1.0_f64.cos()) * 0.5 * strength,
            0.5 * (1.0_f64 + 2.0_f64.cos()) * 0.5 * strength,
        ];
        for (actual, reference) in got.iter().zip(expected) {
            assert!((actual - reference).abs() < 1e-8, "{actual} vs {reference}");
        }
    }

    #[test]
    fn converter_enforces_top_k_and_validates_shapes() {
        let converter =
            DentateGyrusConverterConfig::with_params(4, Some(2), 0.1, 1, 0.05, 20, 1.0, 0.95)
                .unwrap()
                .init();
        let phase = Tensor::<TestBackend, 2>::from_data(
            TensorData::new(vec![0.0, 0.5, 1.0, 1.5], vec![1, 4]),
            &device(),
        );
        let amplitude = Tensor::<TestBackend, 2>::ones([1, 4], &device());
        let out = converter.convert(phase, amplitude, 5).unwrap();
        let active = out
            .to_data()
            .to_vec::<f64>()
            .unwrap()
            .into_iter()
            .filter(|value| value.abs() > 1e-12)
            .count();
        assert_eq!(active, 2);
        let bad = Tensor::<TestBackend, 2>::ones([1, 3], &device());
        assert!(matches!(
            converter.convert(bad.clone(), bad, 5).unwrap_err(),
            TrainError::ShapeMismatch { .. }
        ));
    }

    #[test]
    fn converter_rejects_invalid_alpha_and_zero_steps() {
        assert!(matches!(
            DentateGyrusConverterConfig::with_params(4, Some(2), 0.1, 1, 0.05, 20, 1.0, 1.1,)
                .unwrap_err(),
            TrainError::InvalidRatio {
                name: "integration_alpha",
                ..
            }
        ));
        let converter = DentateGyrusConverterConfig::new(4).unwrap().init();
        let input = Tensor::<TestBackend, 2>::ones([1, 4], &device());
        assert!(matches!(
            converter.convert(input.clone(), input, 0).unwrap_err(),
            TrainError::InvalidStepCount { .. }
        ));
    }

    #[test]
    fn dg_layer_gradients_flow_to_inputs_and_parameters() {
        let _guard = crate::support::autodiff_test_guard();
        let dev: <TestAutodiffBackend as Backend>::Device = Default::default();
        let layer = DgLayerConfig::with_params(4, 2, 2, 20, 3)
            .unwrap()
            .init::<TestAutodiffBackend>(&dev);
        let phase = Tensor::<TestAutodiffBackend, 2>::from_data(
            TensorData::new(vec![0.1, 0.7, 1.4, 2.2], vec![1, 4]),
            &dev,
        )
        .require_grad();
        let amplitude = Tensor::<TestAutodiffBackend, 2>::ones([1, 4], &dev).require_grad();
        let loss = layer
            .forward(phase.clone(), amplitude.clone())
            .unwrap()
            .sum();
        let grads = loss.backward();
        assert!(phase.grad(&grads).is_some());
        assert!(amplitude.grad(&grads).is_some());
        assert!(layer.ffi_scale.grad(&grads).is_some());
        assert!(layer.fbi_temperature.grad(&grads).is_some());
    }

    #[test]
    fn dg_layer_configuration_and_parameter_shapes_are_validated() {
        assert!(matches!(
            DgLayerConfig::with_params(0, 1, 2, 20, 5).unwrap_err(),
            TrainError::EmptyBand { name: "input" }
        ));
        assert!(matches!(
            DgLayerConfig::with_params(4, 0, 2, 20, 5).unwrap_err(),
            TrainError::InvalidTopK { k: 0 }
        ));
        assert!(matches!(
            DgLayerConfig::with_params(4, 2, 2, 20, 0).unwrap_err(),
            TrainError::InvalidStepCount { .. }
        ));
        let cfg = DgLayerConfig::new(4).unwrap();
        let params = DgLayerParams {
            ffi_scale: Tensor::<TestBackend, 1>::ones([2], &device()),
            fbi_temperature: Tensor::<TestBackend, 1>::ones([1], &device()),
        };
        assert!(matches!(
            cfg.init_from_params(params).unwrap_err(),
            TrainError::ShapeMismatch {
                name: "ffi_scale",
                ..
            }
        ));
        let params = DgLayerParams {
            ffi_scale: Tensor::<TestBackend, 1>::ones([1], &device()),
            fbi_temperature: Tensor::<TestBackend, 1>::ones([2], &device()),
        };
        assert!(matches!(
            cfg.init_from_params(params).unwrap_err(),
            TrainError::ShapeMismatch {
                name: "fbi_temperature",
                ..
            }
        ));
    }

    #[test]
    fn ffi_defaults_accessors_and_shape_validation_are_covered() {
        let ffi = FeedforwardInhibitionConfig::default().init();
        assert_eq!(ffi.delay_steps(), 1);
        assert_eq!(ffi.tau(), 0.05);
        let phase = Tensor::<TestBackend, 2>::ones([1, 3], &device());
        let amplitude = Tensor::<TestBackend, 2>::ones([1, 2], &device());
        assert!(matches!(
            ffi.gate(phase, amplitude).unwrap_err(),
            TrainError::ShapeMismatch {
                name: "amplitude",
                ..
            }
        ));
        assert!(matches!(
            FeedforwardInhibitionConfig::with_params(1, f64::NAN, 0.1).unwrap_err(),
            TrainError::NonFiniteParameter { name: "tau", .. }
        ));
        assert!(matches!(
            FeedforwardInhibitionConfig::with_params(1, 0.1, f64::NAN).unwrap_err(),
            TrainError::NonFiniteParameter {
                name: "delay_fraction",
                ..
            }
        ));
    }

    #[test]
    fn converter_configuration_and_accessors_are_covered() {
        assert!(matches!(
            DentateGyrusConverterConfig::new(0).unwrap_err(),
            TrainError::EmptyBand {
                name: "oscillators"
            }
        ));
        assert!(
            DentateGyrusConverterConfig::with_params(4, Some(0), 0.1, 1, 0.05, 20, 1.0, 0.95,)
                .is_err()
        );
        assert!(
            DentateGyrusConverterConfig::with_params(4, Some(2), 0.1, 1, 0.0, 20, 1.0, 0.95,)
                .is_err()
        );
        assert!(DentateGyrusConverterConfig::with_params(
            4,
            Some(2),
            0.1,
            1,
            0.05,
            20,
            1.0,
            f64::NAN,
        )
        .is_err());
        let converter = DentateGyrusConverterConfig::new(4).unwrap().init();
        assert_eq!(converter.n_oscillators(), 4);
        assert_eq!(converter.ffi().delay_steps(), 1);
        assert_eq!(converter.fbi().n_oscillators(), 4);
        assert_eq!(converter.fbi_delay(), 20);
    }

    #[test]
    fn dg_layer_accessors_shape_validation_and_forward_errors_are_covered() {
        let layer = DgLayerConfig::with_params(4, 9, 2, 17, 3)
            .unwrap()
            .init::<TestBackend>(&device());
        assert_eq!(layer.n_input(), 4);
        assert_eq!(layer.top_k(), 4);
        assert_eq!(layer.fbi_delay(), 17);
        assert_eq!(layer.n_integration_steps(), 3);
        layer.validate_shapes().unwrap();
        let bad_phase = Tensor::<TestBackend, 2>::ones([1, 3], &device());
        let amplitude = Tensor::<TestBackend, 2>::ones([1, 3], &device());
        assert!(matches!(
            layer.forward(bad_phase, amplitude).unwrap_err(),
            TrainError::ShapeMismatch { name: "phase", .. }
        ));
        let phase = Tensor::<TestBackend, 2>::ones([1, 4], &device());
        let bad_amplitude = Tensor::<TestBackend, 2>::ones([1, 3], &device());
        assert!(matches!(
            layer.forward(phase, bad_amplitude).unwrap_err(),
            TrainError::ShapeMismatch {
                name: "amplitude",
                ..
            }
        ));
    }
}
