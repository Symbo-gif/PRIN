//! Oscillator-compatible activation functions.
//!
//! Burn `Module` rebuild of PRINet 3.0's `nn/activations.py`: [`d_silu`] (the
//! exact derivative of SiLU/Swish), [`HolomorphicActivation`] for
//! complex-valued oscillator states, and [`phase_activation`] /
//! [`GatedPhaseActivation`] for phase-valued outputs wrapped to `[0, 2π)`.
//!
//! # Complex representation — documented deviation
//!
//! Burn's autodiff backend has no complex tensor kind (the same constraint
//! [`crate::layers`] documents for `ResonanceLayer::init_state`). PRINet
//! 3.0's `HolomorphicActivation` therefore has two branches: a genuinely
//! holomorphic complex `tanh(z)` (`holomorphic=True`), and a "split-complex"
//! fallback that activates the real and imaginary parts independently
//! (`holomorphic=False`). Only the second is representable here: complex
//! oscillator states are carried as a [`ComplexTensor`] pair of real
//! tensors, and [`HolomorphicActivation::forward`] always takes the
//! split-complex path. This is a deliberate, permanent deviation (same
//! class and rationale as `ResonanceLayer`'s FFT-init substitution), not a
//! numerical-precision hazard: the two branches compute genuinely different
//! functions (`tanh(a+bi)` is not `tanh(a) + i·tanh(b)`), so no parity
//! tolerance closes this gap. Any Rust caller that needs the true-complex
//! branch's behavior is out of WP-023 scope pending Burn complex-tensor
//! support.
//!
//! # Example
//!
//! ```
//! use burn::backend::NdArray;
//! use burn::tensor::Tensor;
//! use prin_train::activations::{d_silu, phase_activation};
//!
//! type Backend = NdArray<f64>;
//! let device = Default::default();
//!
//! let z = Tensor::<Backend, 2>::zeros([2, 3], &device);
//! let activated = d_silu(z.clone());
//! assert_eq!(activated.dims(), [2, 3]);
//!
//! let wrapped = phase_activation(z);
//! let data = wrapped.to_data().to_vec::<f64>().unwrap();
//! assert!(data.iter().all(|v| (0.0..std::f64::consts::TAU).contains(v)));
//! ```

use burn::module::{Module, Param};
use burn::tensor::activation::{sigmoid, tanh};
use burn::tensor::backend::Backend;
use burn::tensor::Tensor;

use crate::error::TrainError;
use crate::support::{check_dims, wrap_floor};

/// Upper bound used to clamp a wrapped phase away from exactly `2π`
/// (floating-point edge case where the remainder rounds up to the
/// modulus), matching PRINet 3.0's `PhaseActivation`.
const PHASE_CLAMP_EPS: f64 = 1e-7;

/// Derivative of SiLU (Swish): `σ(z)·(1 + z·(1 − σ(z)))`, the exact
/// analytical derivative of `SiLU(z) = z·σ(z)`.
///
/// Non-monotonic and naturally bounded (`dSiLU(0) = 0.5`), which PRINet 3.0
/// notes makes it well-suited to phase-coupled oscillatory layers where
/// unbounded activations risk NaN divergence.
///
/// # Confirmed upstream precision floor (not a `prin-train` defect)
///
/// `burn-tensor` 0.16.1's default `sigmoid` op (`tensor/ops/activation.rs`,
/// used by every backend — including `NdArray<f64>` — that does not
/// override it, which `burn-ndarray` does not) explicitly downcasts its
/// input to `f32` before computing `exp`/`log` and casts the result back:
/// `B::float_cast(tensor, FloatDType::F32)` followed by the sigmoid formula
/// and `B::float_cast(_, dtype)`. This gives `sigmoid`, and therefore
/// [`d_silu`], [`phase_activation`], and [`GatedPhaseActivation`], an
/// effective precision floor around f32 epsilon (~1e-7 relative) *even when
/// every tensor involved is declared `f64`*. Confirmed empirically during
/// WP-023 S1: `sigmoid(1e-6)` measured `0.50000023841857910` against a true
/// `0.50000025000000003` (an ~5% relative error at that `eps` scale — see
/// the `eps` comment on `gate_bias_gradient_matches_central_finite_difference`).
/// This is a third-party numerical-precision constraint, not a correctness
/// defect: gradchecks and reference-formula comparisons in this module are
/// scaled/toleranced accordingly (documented at each call site) rather than
/// silently loosened without explanation.
pub fn d_silu<B: Backend, const D: usize>(z: Tensor<B, D>) -> Tensor<B, D> {
    let sig = sigmoid(z.clone());
    let one_minus_sig = sig.ones_like() - sig.clone();
    sig.clone() + z * sig * one_minus_sig
}

/// Apply [`d_silu`], then wrap the result to `[0, 2π)` using floored modulo
/// (see `crate::support::wrap_floor`'s doc comment for why this differs from
/// Burn's `remainder_scalar`).
///
/// Matches PRINet 3.0's `PhaseActivation` with its default inner activation.
pub fn phase_activation<B: Backend>(z: Tensor<B, 2>) -> Tensor<B, 2> {
    let wrapped = wrap_floor(d_silu(z), std::f64::consts::TAU);
    wrapped.clamp(0.0, std::f64::consts::TAU - PHASE_CLAMP_EPS)
}

/// A complex tensor carried as an explicit `(re, im)` pair of real tensors
/// (see the module docs' "Complex representation" section for why).
///
/// Both parts share shape `[batch, n]`; constructing a `ComplexTensor`
/// validates that they match.
#[derive(Debug, Clone)]
pub struct ComplexTensor<B: Backend> {
    re: Tensor<B, 2>,
    im: Tensor<B, 2>,
}

impl<B: Backend> ComplexTensor<B> {
    /// Validate and wrap a `(re, im)` pair.
    ///
    /// # Errors
    ///
    /// Returns [`TrainError::ShapeMismatch`] if `re` and `im` do not share a
    /// shape.
    pub fn new(re: Tensor<B, 2>, im: Tensor<B, 2>) -> Result<Self, TrainError> {
        check_dims("im", im.dims(), re.dims())?;
        Ok(Self { re, im })
    }

    /// Build a purely real complex tensor (`im = 0`).
    pub fn from_real(re: Tensor<B, 2>) -> Self {
        let im = Tensor::zeros(re.dims(), &re.device());
        Self { re, im }
    }

    /// The real part.
    pub fn re(&self) -> &Tensor<B, 2> {
        &self.re
    }

    /// The imaginary part.
    pub fn im(&self) -> &Tensor<B, 2> {
        &self.im
    }

    /// Consume `self`, returning the `(re, im)` pair.
    pub fn into_parts(self) -> (Tensor<B, 2>, Tensor<B, 2>) {
        (self.re, self.im)
    }

    /// Squared modulus `|z|² = re² + im²`, elementwise.
    pub fn abs_sq(&self) -> Tensor<B, 2> {
        self.re.clone().powf_scalar(2.0) + self.im.clone().powf_scalar(2.0)
    }
}

/// Validated hyperparameters for [`HolomorphicActivation`].
#[derive(Clone, Debug, PartialEq)]
pub struct HolomorphicActivationConfig {
    /// Output scaling factor.
    pub scale: f64,
}

impl HolomorphicActivationConfig {
    /// A validated configuration.
    ///
    /// # Errors
    ///
    /// Returns [`TrainError::NonFiniteParameter`] if `scale` is not finite.
    pub fn new(scale: f64) -> Result<Self, TrainError> {
        if !scale.is_finite() {
            return Err(TrainError::NonFiniteParameter {
                name: "scale",
                value: scale,
            });
        }
        Ok(Self { scale })
    }

    /// Build a [`HolomorphicActivation`] from this configuration.
    pub fn init(&self) -> HolomorphicActivation {
        HolomorphicActivation { scale: self.scale }
    }
}

/// Holomorphic-compatible (split-complex) activation for complex oscillator
/// states.
///
/// See the module docs for why this always takes PRINet 3.0's
/// `holomorphic=False` split-complex path: `tanh` applied independently to
/// the real and imaginary parts, each scaled.
#[derive(Debug, Clone, Copy, PartialEq)]
pub struct HolomorphicActivation {
    scale: f64,
}

impl HolomorphicActivation {
    /// The output scaling factor.
    pub fn scale(&self) -> f64 {
        self.scale
    }

    /// Apply the activation to a complex oscillator state.
    pub fn forward<B: Backend>(&self, z: ComplexTensor<B>) -> ComplexTensor<B> {
        let (re, im) = z.into_parts();
        ComplexTensor {
            re: tanh(re).mul_scalar(self.scale),
            im: tanh(im).mul_scalar(self.scale),
        }
    }
}

/// Explicit parameter tensors for [`GatedPhaseActivation`] construction.
pub struct GatedPhaseActivationParams<B: Backend> {
    /// Per-feature gate weight, shape `[n_dims]`.
    pub gate_weight: Tensor<B, 1>,
    /// Per-feature gate bias, shape `[n_dims]`.
    pub gate_bias: Tensor<B, 1>,
}

/// Validated hyperparameters for [`GatedPhaseActivation`].
#[derive(Clone, Debug, PartialEq)]
pub struct GatedPhaseActivationConfig {
    /// Input/output feature dimension.
    pub n_dims: usize,
}

impl GatedPhaseActivationConfig {
    /// A validated configuration.
    ///
    /// # Errors
    ///
    /// Returns [`TrainError::EmptyBand`] if `n_dims` is zero.
    pub fn new(n_dims: usize) -> Result<Self, TrainError> {
        if n_dims == 0 {
            return Err(TrainError::EmptyBand { name: "dims" });
        }
        Ok(Self { n_dims })
    }

    /// Initialize with zero gate weight/bias, matching PRINet 3.0's
    /// `nn.Parameter(torch.zeros(n_dims))` (deterministic; no [`Seed`] draw
    /// needed).
    ///
    /// [`Seed`]: prin_dynamics::Seed
    pub fn init<B: Backend>(&self, device: &B::Device) -> GatedPhaseActivation<B> {
        let n = self.n_dims;
        self.init_from_params(GatedPhaseActivationParams {
            gate_weight: Tensor::zeros([n], device),
            gate_bias: Tensor::zeros([n], device),
        })
        .expect("zero-initialized parameter shapes are constructed from `self` and always valid")
    }

    /// Build a [`GatedPhaseActivation`] from explicit parameter tensors.
    ///
    /// # Errors
    ///
    /// Returns [`TrainError::ShapeMismatch`] if either tensor's shape does
    /// not match this config's `n_dims`.
    pub fn init_from_params<B: Backend>(
        &self,
        params: GatedPhaseActivationParams<B>,
    ) -> Result<GatedPhaseActivation<B>, TrainError> {
        let n = self.n_dims;
        check_dims("gate_weight", params.gate_weight.dims(), [n])?;
        check_dims("gate_bias", params.gate_bias.dims(), [n])?;
        Ok(GatedPhaseActivation {
            gate_weight: Param::initialized(Default::default(), params.gate_weight.require_grad()),
            gate_bias: Param::initialized(Default::default(), params.gate_bias.require_grad()),
            n_dims: n,
        })
    }
}

/// Phase activation with a learnable per-feature gate:
/// `y = σ(w_g·z + b_g) · phase_activation(z)`.
///
/// Burn `Module` rebuild of PRINet 3.0's `GatedPhaseActivation`.
#[derive(Module, Debug)]
pub struct GatedPhaseActivation<B: Backend> {
    gate_weight: Param<Tensor<B, 1>>,
    gate_bias: Param<Tensor<B, 1>>,
    n_dims: usize,
}

impl<B: Backend> GatedPhaseActivation<B> {
    /// Input/output feature dimension.
    pub fn n_dims(&self) -> usize {
        self.n_dims
    }

    /// Apply the gated phase activation.
    ///
    /// # Errors
    ///
    /// Returns [`TrainError::ShapeMismatch`] if `z`'s width is not
    /// [`Self::n_dims`].
    pub fn forward(&self, z: Tensor<B, 2>) -> Result<Tensor<B, 2>, TrainError> {
        let batch = z.dims()[0];
        check_dims("z", z.dims(), [batch, self.n_dims])?;

        let gate = sigmoid(
            self.gate_weight.val().unsqueeze::<2>() * z.clone()
                + self.gate_bias.val().unsqueeze::<2>(),
        );
        let phase_out = phase_activation(z);
        Ok(gate * phase_out)
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    use burn::backend::{Autodiff, NdArray};
    use burn::tensor::TensorData;
    use prin_dynamics::Seed;

    type TestBackend = NdArray<f64>;
    type TestAutodiffBackend = Autodiff<TestBackend>;

    fn device() -> <TestBackend as Backend>::Device {
        Default::default()
    }

    // --- d_silu ---

    #[test]
    fn d_silu_at_zero_is_one_half() {
        let dev = device();
        let z = Tensor::<TestBackend, 1>::zeros([4], &dev);
        let y = d_silu(z).to_data().to_vec::<f64>().unwrap();
        for v in y {
            assert!((v - 0.5).abs() < 1e-12);
        }
    }

    #[test]
    fn d_silu_is_bounded() {
        let dev = device();
        let data: Vec<f64> = (-50..=50).map(|i| i as f64 / 5.0).collect();
        let n = data.len();
        let z = Tensor::<TestBackend, 1>::from_data(TensorData::new(data, vec![n]), &dev);
        let y = d_silu(z).to_data().to_vec::<f64>().unwrap();
        for v in y {
            assert!(v.is_finite());
            assert!(v > -0.3 && v < 1.2, "dSiLU({v}) escaped documented bounds");
        }
    }

    #[test]
    fn d_silu_matches_reference_formula() {
        // Independent reimplementation from PRINet 3.0's docstring formula:
        // sigma(z) + z*sigma(z)*(1-sigma(z)). Tolerance is 1e-6, not exact
        // double precision: `burn-ndarray`'s `sigmoid` measurably departs
        // from a `1/(1+exp(-x))` reference (observed up to ~1.8e-8 absolute
        // here) even on an `NdArray<f64>` backend (see the `eps` comment on
        // `gate_bias_gradient_matches_central_finite_difference` for the
        // larger-impact version of the same backend precision floor).
        let dev = device();
        let xs = [-3.0_f64, -1.0, 0.0, 0.5, 2.0, 4.0];
        let z = Tensor::<TestBackend, 1>::from_data(TensorData::new(xs.to_vec(), vec![6]), &dev);
        let y = d_silu(z).to_data().to_vec::<f64>().unwrap();
        for (x, v) in xs.iter().zip(y.iter()) {
            let sig = 1.0 / (1.0 + (-x).exp());
            let expected = sig + x * sig * (1.0 - sig);
            assert!((v - expected).abs() < 1e-6, "{v} vs {expected}");
        }
    }

    // --- phase_activation ---

    #[test]
    fn phase_activation_wraps_into_two_pi() {
        let dev = device();
        let xs: Vec<f64> = (-200..=200).map(|i| i as f64 / 3.0).collect();
        let n = xs.len();
        let z = Tensor::<TestBackend, 2>::from_data(TensorData::new(xs, vec![1, n]), &dev);
        let y = phase_activation(z).to_data().to_vec::<f64>().unwrap();
        for v in y {
            assert!(
                (0.0..std::f64::consts::TAU).contains(&v),
                "phase_activation output {v} not in [0, 2*pi)"
            );
        }
    }

    #[test]
    fn phase_activation_folds_negative_dsilu_output_correctly() {
        // dSiLU(-3.0) is negative (below the [0, 2*pi) wrap range), so this
        // exercises the floored-modulo distinction documented on
        // `wrap_floor`: Python's `%` (and this activation) must return a
        // small *positive* value near TAU, not the small negative raw value
        // a signed (Rust/C) remainder would leave unchanged.
        let dev = device();
        let z = Tensor::<TestBackend, 2>::full([1, 1], -3.0, &dev);
        let raw = d_silu(z.clone()).to_data().to_vec::<f64>().unwrap()[0];
        assert!(raw < 0.0, "test precondition: dSiLU(-3) must be negative");

        let wrapped = phase_activation(z).to_data().to_vec::<f64>().unwrap()[0];
        let expected = raw.rem_euclid(std::f64::consts::TAU);
        assert!((wrapped - expected).abs() < 1e-9);
        assert!(wrapped >= 0.0);
    }

    // --- ComplexTensor ---

    #[test]
    fn complex_tensor_rejects_mismatched_shapes() {
        let dev = device();
        let re = Tensor::<TestBackend, 2>::zeros([2, 3], &dev);
        let im = Tensor::<TestBackend, 2>::zeros([2, 4], &dev);
        let err = ComplexTensor::new(re, im).unwrap_err();
        assert!(matches!(err, TrainError::ShapeMismatch { name: "im", .. }));
    }

    #[test]
    fn complex_tensor_re_im_accessors_return_the_constructed_parts() {
        let dev = device();
        let re = Tensor::<TestBackend, 2>::full([1, 1], 3.0, &dev);
        let im = Tensor::<TestBackend, 2>::full([1, 1], 4.0, &dev);
        let z = ComplexTensor::new(re, im).unwrap();
        assert!((z.re().clone().to_data().to_vec::<f64>().unwrap()[0] - 3.0).abs() < 1e-15);
        assert!((z.im().clone().to_data().to_vec::<f64>().unwrap()[0] - 4.0).abs() < 1e-15);
    }

    #[test]
    fn complex_tensor_abs_sq_matches_pythagoras() {
        let dev = device();
        let re = Tensor::<TestBackend, 2>::full([1, 1], 3.0, &dev);
        let im = Tensor::<TestBackend, 2>::full([1, 1], 4.0, &dev);
        let z = ComplexTensor::new(re, im).unwrap();
        let abs_sq = z.abs_sq().to_data().to_vec::<f64>().unwrap()[0];
        assert!((abs_sq - 25.0).abs() < 1e-12);
    }

    // --- HolomorphicActivation ---

    #[test]
    fn holomorphic_activation_rejects_non_finite_scale() {
        assert!(matches!(
            HolomorphicActivationConfig::new(f64::NAN).unwrap_err(),
            TrainError::NonFiniteParameter { name: "scale", .. }
        ));
    }

    #[test]
    fn holomorphic_activation_scale_accessor_reports_config_value() {
        let act = HolomorphicActivationConfig::new(3.5).unwrap().init();
        assert!((act.scale() - 3.5).abs() < 1e-15);
    }

    #[test]
    fn holomorphic_activation_applies_split_complex_tanh() {
        let dev = device();
        let act = HolomorphicActivationConfig::new(2.0).unwrap().init();
        let re = Tensor::<TestBackend, 2>::full([1, 1], 0.5, &dev);
        let im = Tensor::<TestBackend, 2>::full([1, 1], -0.5, &dev);
        let z = ComplexTensor::new(re, im).unwrap();
        let out = act.forward(z);
        let (re_out, im_out) = out.into_parts();
        let re_v = re_out.to_data().to_vec::<f64>().unwrap()[0];
        let im_v = im_out.to_data().to_vec::<f64>().unwrap()[0];
        assert!((re_v - 2.0 * 0.5_f64.tanh()).abs() < 1e-10);
        assert!((im_v - 2.0 * (-0.5_f64).tanh()).abs() < 1e-10);
    }

    #[test]
    fn holomorphic_activation_real_input_reduces_to_scaled_tanh() {
        // im = 0 exercises the "reduces to scaled tanh" claim in the
        // PRINet 3.0 docstring for real-valued input.
        let dev = device();
        let act = HolomorphicActivationConfig::new(1.0).unwrap().init();
        let z = ComplexTensor::from_real(Tensor::<TestBackend, 2>::full([1, 2], 0.75, &dev));
        let out = act.forward(z);
        let (re_out, im_out) = out.into_parts();
        let re_v = re_out.to_data().to_vec::<f64>().unwrap();
        let im_v = im_out.to_data().to_vec::<f64>().unwrap();
        for v in re_v {
            assert!((v - 0.75_f64.tanh()).abs() < 1e-10);
        }
        for v in im_v {
            assert!(v.abs() < 1e-10);
        }
    }

    // --- GatedPhaseActivation ---

    #[test]
    fn zero_dims_rejected() {
        assert!(matches!(
            GatedPhaseActivationConfig::new(0).unwrap_err(),
            TrainError::EmptyBand { name: "dims" }
        ));
    }

    #[test]
    fn n_dims_accessor_reports_config_value() {
        let dev = device();
        let act = GatedPhaseActivationConfig::new(7)
            .unwrap()
            .init::<TestBackend>(&dev);
        assert_eq!(act.n_dims(), 7);
    }

    #[test]
    fn zero_init_gate_is_one_half_everywhere() {
        // sigmoid(0*z + 0) = 0.5 regardless of z, matching PRINet 3.0's
        // zero-initialized gate parameters.
        let dev = device();
        let act = GatedPhaseActivationConfig::new(3)
            .unwrap()
            .init::<TestBackend>(&dev);
        let z = Tensor::<TestBackend, 2>::from_data(
            TensorData::new(vec![1.0, -2.0, 3.5], vec![1, 3]),
            &dev,
        );
        let out = act.forward(z.clone()).unwrap();
        let expected = phase_activation(z).mul_scalar(0.5);
        let got = out.to_data().to_vec::<f64>().unwrap();
        let exp = expected.to_data().to_vec::<f64>().unwrap();
        for (g, e) in got.iter().zip(exp.iter()) {
            assert!((g - e).abs() < 1e-10);
        }
    }

    #[test]
    fn gated_phase_activation_rejects_wrong_width() {
        let dev = device();
        let act = GatedPhaseActivationConfig::new(3)
            .unwrap()
            .init::<TestBackend>(&dev);
        let z = Tensor::<TestBackend, 2>::zeros([2, 4], &dev);
        let err = act.forward(z).unwrap_err();
        assert!(matches!(err, TrainError::ShapeMismatch { name: "z", .. }));
    }

    #[test]
    fn gated_phase_activation_output_bounded_and_finite() {
        let dev = device();
        let mut seed = Seed::new(9, 0);
        let bound =
            crate::support::seeded_uniform::<TestBackend, 2>([4, 5], -6.0, 6.0, &dev, &mut seed);
        let act = GatedPhaseActivationConfig::new(5)
            .unwrap()
            .init::<TestBackend>(&dev);
        let out = act.forward(bound).unwrap();
        let data = out.to_data().to_vec::<f64>().unwrap();
        for v in data {
            assert!(v.is_finite());
            // gate in [0,1] times phase output in [0, 2*pi).
            assert!((0.0..std::f64::consts::TAU).contains(&v));
        }
    }

    // --- Gradient reference tests ---

    #[test]
    fn gated_phase_activation_gradients_flow_to_every_parameter() {
        let dev: <TestAutodiffBackend as Backend>::Device = Default::default();
        let act = GatedPhaseActivationConfig::new(3)
            .unwrap()
            .init::<TestAutodiffBackend>(&dev);
        let z = Tensor::<TestAutodiffBackend, 2>::from_data(
            TensorData::new(vec![0.4, -1.1, 2.3], vec![1, 3]),
            &dev,
        )
        .require_grad();

        let out = act.forward(z).unwrap();
        let loss = out.sum();
        let grads = loss.backward();

        let w_grad = act
            .gate_weight
            .val()
            .grad(&grads)
            .expect("gate_weight gradient must be present")
            .to_data()
            .to_vec::<f64>()
            .unwrap();
        let b_grad = act
            .gate_bias
            .val()
            .grad(&grads)
            .expect("gate_bias gradient must be present")
            .to_data()
            .to_vec::<f64>()
            .unwrap();
        assert!(w_grad.iter().all(|v| v.is_finite()));
        assert!(b_grad.iter().all(|v| v.is_finite()));
    }

    #[test]
    fn gate_bias_gradient_matches_central_finite_difference() {
        let dev: <TestBackend as Backend>::Device = Default::default();
        let z_data = vec![0.6_f64, -0.9, 1.7];
        let z = || {
            Tensor::<TestBackend, 2>::from_data(TensorData::new(z_data.clone(), vec![1, 3]), &dev)
        };

        let loss_for = |bias0: f64| -> f64 {
            let params = GatedPhaseActivationParams {
                gate_weight: Tensor::<TestBackend, 1>::zeros([3], &dev),
                gate_bias: Tensor::<TestBackend, 1>::from_data(
                    TensorData::new(vec![bias0, 0.0, 0.0], vec![3]),
                    &dev,
                ),
            };
            let act = GatedPhaseActivationConfig::new(3)
                .unwrap()
                .init_from_params(params)
                .unwrap();
            act.forward(z()).unwrap().sum().into_scalar()
        };

        // `burn-ndarray`'s `sigmoid` has an effective absolute precision
        // floor around 1e-7 near 0.5 even on an `NdArray<f64>` backend
        // (confirmed empirically: `sigmoid(1e-6)` measured
        // `0.5000002384...` vs. the true `0.5000002500...`, an ~5%
        // relative error at that eps — large enough to fail a naive
        // gradcheck). `eps=1e-6` (used elsewhere in this crate for
        // gradchecks over `matmul`/`sin`/`cos` chains, which do not hit this
        // floor) is too small to resolve a clean signal through `sigmoid`
        // here; `eps=1e-4` keeps the finite-difference signal (~5e-5) two
        // orders of magnitude above the noise floor.
        let eps = 1e-4;
        let numerical = (loss_for(eps) - loss_for(-eps)) / (2.0 * eps);

        let dev_ad: <TestAutodiffBackend as Backend>::Device = Default::default();
        let params = GatedPhaseActivationParams {
            gate_weight: Tensor::<TestAutodiffBackend, 1>::zeros([3], &dev_ad),
            gate_bias: Tensor::<TestAutodiffBackend, 1>::zeros([3], &dev_ad).require_grad(),
        };
        let bias_tensor = params.gate_bias.clone();
        let act = GatedPhaseActivationConfig::new(3)
            .unwrap()
            .init_from_params(params)
            .unwrap();
        let z_ad = Tensor::<TestAutodiffBackend, 2>::from_data(
            TensorData::new(z_data, vec![1, 3]),
            &dev_ad,
        );
        let loss = act.forward(z_ad).unwrap().sum();
        let grads = loss.backward();
        let analytic = bias_tensor
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

#[cfg(test)]
mod proptests {
    use super::*;
    use burn::backend::NdArray;
    use prin_dynamics::Seed;
    use proptest::prelude::*;

    type TestBackend = NdArray<f64>;

    proptest! {
        #[test]
        fn phase_activation_always_wraps_in_range(
            n in 1usize..=8,
            batch in 1usize..=4,
            seed_val in 0u64..1000,
        ) {
            let dev = Default::default();
            let mut seed = Seed::new(seed_val as u128, 0);
            let z = crate::support::seeded_uniform::<TestBackend, 2>(
                [batch, n], -50.0, 50.0, &dev, &mut seed,
            );
            let out = phase_activation(z);
            let data = out.to_data().to_vec::<f64>().unwrap();
            prop_assert_eq!(data.len(), batch * n);
            for v in &data {
                prop_assert!(v.is_finite());
                prop_assert!((0.0..std::f64::consts::TAU).contains(v));
            }
        }

        #[test]
        fn d_silu_always_finite_and_bounded(
            n in 1usize..=8,
            seed_val in 0u64..1000,
        ) {
            let dev = Default::default();
            let mut seed = Seed::new(seed_val as u128, 0);
            let z = crate::support::seeded_uniform::<TestBackend, 1>(
                [n], -20.0, 20.0, &dev, &mut seed,
            );
            let out = d_silu(z);
            let data = out.to_data().to_vec::<f64>().unwrap();
            for v in &data {
                prop_assert!(v.is_finite());
                prop_assert!(*v > -0.5 && *v < 1.5);
            }
        }
    }
}
