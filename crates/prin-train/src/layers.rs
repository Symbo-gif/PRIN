//! Trainable single-layer Kuramoto resonance primitive.
//!
//! [`ResonanceLayer`] is the Burn `Module` rebuild of PRINet 3.0's
//! `nn.layers.ResonanceLayer`: an input feature vector is projected to an
//! initial oscillator state, propagated for a fixed number of extended-
//! Kuramoto steps with learned coupling/decay/frequency-modulation, and the
//! final amplitudes are returned.
//!
//! # Correspondence to the PRINet 3.0 reference
//!
//! [`ResonanceLayer::step`] is a direct, line-for-line port of the loop body
//! in `ResonanceLayer.forward` (`nn/layers.py`): for phase `φ`, amplitude
//! `a`, frequency `ω`, zero-diagonal coupling `C = coupling·(1 −
//! I)/√n_oscillators`, and modulation `M`, one step computes (all terms
//! evaluated from the *pre-step* `φ`/`a`, matching the reference's ordering):
//!
//! ```text
//! sin_diff[i,j] = sin(φ[j] − φ[i]),  cos_diff[i,j] = cos(φ[j] − φ[i])
//! φ' = wrap(φ + dt·(ω + Σⱼ C[i,j]·sin_diff[i,j]·a[j]))
//! a' = clamp(a + dt·(−decay·a + Σⱼ C[i,j]·cos_diff[i,j]·a[j]), 1e-6, 10.0)
//! ω' = ω + dt·γ·Σⱼ M[i,j]·sin_diff[i,j]·a[j]
//! ```
//!
//! Golden-value parity tests for this step formula live in
//! `tests/parity_layers.rs`.
//!
//! **Documented deviation — initial-state projection.** PRINet 3.0's
//! `_compute_initial_state` derives the initial phase/amplitude from an FFT
//! of the input projection (a complex-valued, not straightforwardly
//! differentiable-in-Burn operation). [`ResonanceLayer::init_state`]
//! substitutes a simpler, fully real-valued and differentiable mapping:
//! `phase0 = wrap(x · input_proj)`, `amp0 = max(|x · input_proj|, 1e-6)`. The
//! *dynamics* this module exists to provide — the extended-Kuramoto step
//! above — are unaffected and remain bit-faithful to the reference; only the
//! feature-to-oscillator encoding differs. This mirrors the precedent set by
//! `prin_dynamics::bands` documenting its own composition difference from
//! the PRINet 3.0 stepper (Project Plan amendment #19).
//!
//! # Example
//!
//! ```
//! use burn::backend::NdArray;
//! use burn::tensor::Tensor;
//! use prin_dynamics::Seed;
//! use prin_train::layers::ResonanceLayerConfig;
//!
//! type Backend = NdArray<f32>;
//!
//! let cfg = ResonanceLayerConfig::new(8, 16).unwrap();
//! let device = Default::default();
//! let mut seed = Seed::new(0, 0);
//! let layer = cfg.init::<Backend>(&device, &mut seed);
//!
//! let x = Tensor::<Backend, 2>::ones([4, 16], &device);
//! let amplitudes = layer.forward(x).unwrap();
//! assert_eq!(amplitudes.dims(), [4, 8]);
//! ```

use burn::module::{Module, Param};
use burn::tensor::backend::Backend;
use burn::tensor::Tensor;
use prin_dynamics::Seed;

use crate::error::TrainError;
use crate::support::{check_dims, seeded_uniform, validate_dt, validate_finite, xavier_bound};

/// Amplitude floor, matching PRINet 3.0's `_EPS`.
const AMP_EPS: f64 = 1e-6;
/// Amplitude ceiling, matching PRINet 3.0's `_AMP_MAX`.
const AMP_MAX: f64 = 10.0;

/// Validated resonance state: phase, amplitude, and frequency, each shape
/// `[batch, n_oscillators]`.
///
/// This is the state contract [`ResonanceLayer::step`] and
/// [`ResonanceLayer::integrate`] operate on — constructing one validates that
/// all three tensors share a shape.
#[derive(Debug, Clone)]
pub struct ResonanceState<B: Backend> {
    phase: Tensor<B, 2>,
    amplitude: Tensor<B, 2>,
    frequency: Tensor<B, 2>,
}

impl<B: Backend> ResonanceState<B> {
    /// Validate and wrap a `(phase, amplitude, frequency)` triple.
    ///
    /// # Errors
    ///
    /// Returns [`TrainError::ShapeMismatch`] if the three tensors do not
    /// share the same shape.
    pub fn new(
        phase: Tensor<B, 2>,
        amplitude: Tensor<B, 2>,
        frequency: Tensor<B, 2>,
    ) -> Result<Self, TrainError> {
        let p_dims = phase.dims();
        check_dims("amplitude", amplitude.dims(), p_dims)?;
        check_dims("frequency", frequency.dims(), p_dims)?;
        Ok(Self {
            phase,
            amplitude,
            frequency,
        })
    }

    /// The phase tensor, shape `[batch, n_oscillators]`.
    pub fn phase(&self) -> &Tensor<B, 2> {
        &self.phase
    }

    /// The amplitude tensor, shape `[batch, n_oscillators]`.
    pub fn amplitude(&self) -> &Tensor<B, 2> {
        &self.amplitude
    }

    /// The frequency tensor, shape `[batch, n_oscillators]`.
    pub fn frequency(&self) -> &Tensor<B, 2> {
        &self.frequency
    }

    /// Consume the state, returning `(phase, amplitude, frequency)`.
    pub fn into_parts(self) -> (Tensor<B, 2>, Tensor<B, 2>, Tensor<B, 2>) {
        (self.phase, self.amplitude, self.frequency)
    }
}

/// Explicit parameter tensors for [`ResonanceLayer`] construction.
///
/// Used by golden-reference tests and by any checkpoint path outside
/// [`burn::record`]. Shapes are validated against the owning
/// [`ResonanceLayerConfig`] by [`ResonanceLayerConfig::init_from_params`].
pub struct ResonanceLayerParams<B: Backend> {
    /// Coupling matrix, shape `[n_oscillators, n_oscillators]`.
    pub coupling: Tensor<B, 2>,
    /// Per-oscillator decay rate, shape `[n_oscillators]`.
    pub decay: Tensor<B, 1>,
    /// Input-to-oscillator projection, shape `[n_dims, n_oscillators]`.
    pub input_proj: Tensor<B, 2>,
    /// Frequency-modulation matrix, shape `[n_oscillators, n_oscillators]`.
    pub modulation: Tensor<B, 2>,
    /// Base per-oscillator frequency, shape `[n_oscillators]`.
    pub base_frequency: Tensor<B, 1>,
}

/// Validated hyperparameters for [`ResonanceLayer`].
///
/// Defaults (`new`) match the PRINet 3.0 reference: `n_steps=10, dt=0.01,
/// decay_rate=0.1, freq_adaptation_rate=0.01`.
#[derive(Clone, Debug, PartialEq)]
pub struct ResonanceLayerConfig {
    /// Number of coupled oscillators.
    pub n_oscillators: usize,
    /// Input feature dimension.
    pub n_dims: usize,
    /// Number of Kuramoto steps per forward pass.
    pub n_steps: usize,
    /// Timestep per step.
    pub dt: f64,
    /// Initial per-oscillator amplitude decay rate.
    pub decay_rate: f64,
    /// Frequency-modulation rate `γ`.
    pub freq_adaptation_rate: f64,
}

impl ResonanceLayerConfig {
    /// Validated configuration with PRINet 3.0's default hyperparameters.
    ///
    /// # Errors
    ///
    /// Returns [`TrainError::EmptyBand`] if `n_oscillators` or `n_dims` is
    /// zero.
    pub fn new(n_oscillators: usize, n_dims: usize) -> Result<Self, TrainError> {
        Self::with_params(n_oscillators, n_dims, 10, 0.01, 0.1, 0.01)
    }

    /// Validated configuration with explicit hyperparameters.
    ///
    /// # Errors
    ///
    /// Returns [`TrainError::EmptyBand`] if `n_oscillators` or `n_dims` is
    /// zero, or [`TrainError::NonFiniteParameter`] /
    /// [`TrainError::InvalidTimestep`] if a hyperparameter is invalid.
    pub fn with_params(
        n_oscillators: usize,
        n_dims: usize,
        n_steps: usize,
        dt: f64,
        decay_rate: f64,
        freq_adaptation_rate: f64,
    ) -> Result<Self, TrainError> {
        if n_oscillators == 0 {
            return Err(TrainError::EmptyBand {
                name: "oscillators",
            });
        }
        if n_dims == 0 {
            return Err(TrainError::EmptyBand { name: "dims" });
        }
        validate_dt(dt)?;
        validate_finite("decay_rate", decay_rate)?;
        validate_finite("freq_adaptation_rate", freq_adaptation_rate)?;
        Ok(Self {
            n_oscillators,
            n_dims,
            n_steps,
            dt,
            decay_rate,
            freq_adaptation_rate,
        })
    }

    /// Initialize a [`ResonanceLayer`] with parameters drawn from the
    /// project's deterministic [`Seed`] (Coding Standards §1.3).
    ///
    /// `decay` starts at the configured constant `decay_rate` (matching
    /// PRINet 3.0's `torch.full`); `base_frequency` is linearly spaced on
    /// `[0.1, 10.0]` (matching PRINet 3.0's `torch.linspace`, deterministic
    /// in both). `coupling`/`modulation`/`input_proj` are Xavier-uniform
    /// (gain `0.5`, matching PRINet 3.0's projection init) drawn from `seed`;
    /// the coupling diagonal is zeroed to match the public parameter contract.
    /// PRINet 3.0 uses `torch.randn` for `coupling`/`modulation`; only the
    /// initial scale is load-bearing for training, not the exact
    /// distribution shape.
    pub fn init<B: Backend>(&self, device: &B::Device, seed: &mut Seed) -> ResonanceLayer<B> {
        let n = self.n_oscillators;
        let d = self.n_dims;

        let coupling_bound = xavier_bound(n, n, 0.5);
        let coupling_mask = Tensor::<B, 2>::ones([n, n], device) - Tensor::<B, 2>::eye(n, device);
        let coupling =
            seeded_uniform::<B, 2>([n, n], -coupling_bound, coupling_bound, device, seed)
                * coupling_mask;
        let modulation_bound = xavier_bound(n, n, 0.05);
        let modulation =
            seeded_uniform::<B, 2>([n, n], -modulation_bound, modulation_bound, device, seed);
        let proj_bound = xavier_bound(d, n, 0.5);
        let input_proj = seeded_uniform::<B, 2>([d, n], -proj_bound, proj_bound, device, seed);
        let decay = seeded_uniform::<B, 1>([n], self.decay_rate, self.decay_rate, device, seed);

        let base_frequency = if n == 1 {
            seeded_uniform::<B, 1>([1], 0.1, 0.1, device, seed)
        } else {
            let step = (10.0 - 0.1) / (n - 1) as f64;
            let data: Vec<f64> = (0..n).map(|i| 0.1 + step * i as f64).collect();
            Tensor::from_data(burn::tensor::TensorData::new(data, vec![n]), device)
        };

        self.init_from_params(ResonanceLayerParams {
            coupling,
            decay,
            input_proj,
            modulation,
            base_frequency,
        })
        .expect("seeded-init parameter shapes are constructed from `self` and always valid")
    }

    /// Build a [`ResonanceLayer`] from explicit parameter tensors.
    ///
    /// # Errors
    ///
    /// Returns [`TrainError::ShapeMismatch`] if any tensor's shape does not
    /// match this config's `n_oscillators`/`n_dims`.
    pub fn init_from_params<B: Backend>(
        &self,
        params: ResonanceLayerParams<B>,
    ) -> Result<ResonanceLayer<B>, TrainError> {
        let n = self.n_oscillators;
        let d = self.n_dims;
        check_dims("coupling", params.coupling.dims(), [n, n])?;
        check_dims("decay", params.decay.dims(), [n])?;
        check_dims("input_proj", params.input_proj.dims(), [d, n])?;
        check_dims("modulation", params.modulation.dims(), [n, n])?;
        check_dims("base_frequency", params.base_frequency.dims(), [n])?;

        Ok(ResonanceLayer {
            coupling: Param::initialized(Default::default(), params.coupling.require_grad()),
            decay: Param::initialized(Default::default(), params.decay.require_grad()),
            input_proj: Param::initialized(Default::default(), params.input_proj.require_grad()),
            modulation: Param::initialized(Default::default(), params.modulation.require_grad()),
            base_frequency: Param::initialized(
                Default::default(),
                params.base_frequency.require_grad(),
            ),
            n_oscillators: n,
            n_dims: d,
            n_steps: self.n_steps,
            dt: self.dt,
            coupling_scale: 1.0 / (n as f64).sqrt(),
            freq_adaptation_rate: self.freq_adaptation_rate,
        })
    }
}

/// Trainable single-layer Kuramoto resonance primitive.
///
/// See the module docs for the exact per-step formula and the documented
/// initial-state deviation from PRINet 3.0. Construct via
/// [`ResonanceLayerConfig::init`] (seeded random parameters) or
/// [`ResonanceLayerConfig::init_from_params`] (explicit tensors).
#[derive(Module, Debug)]
pub struct ResonanceLayer<B: Backend> {
    coupling: Param<Tensor<B, 2>>,
    decay: Param<Tensor<B, 1>>,
    input_proj: Param<Tensor<B, 2>>,
    modulation: Param<Tensor<B, 2>>,
    base_frequency: Param<Tensor<B, 1>>,
    n_oscillators: usize,
    n_dims: usize,
    n_steps: usize,
    dt: f64,
    coupling_scale: f64,
    freq_adaptation_rate: f64,
}

impl<B: Backend> ResonanceLayer<B> {
    /// Number of coupled oscillators.
    pub fn n_oscillators(&self) -> usize {
        self.n_oscillators
    }

    /// Input feature dimension.
    pub fn n_dims(&self) -> usize {
        self.n_dims
    }

    /// Validate that every parameter tensor's current shape still matches
    /// this layer's declared `n_oscillators`/`n_dims` configuration.
    ///
    /// `n_oscillators`/`n_dims` are plain `usize` fields, not `Param`
    /// tensors, so `Module::load_record` (checkpoint restore) does not
    /// touch them — it overwrites each `Param` tensor with whatever shape
    /// the record contains, without validating it against these fields.
    /// A well-formed record produced by a differently-configured layer
    /// therefore loads without error, leaving the tensors and the declared
    /// configuration silently inconsistent unless a caller checks
    /// explicitly. Checkpoint-loading callers (e.g. `prin-py`'s
    /// `train.rs`) must call this after `load_record` and before
    /// committing the result.
    ///
    /// # Errors
    ///
    /// Returns [`TrainError::ShapeMismatch`] naming the first tensor whose
    /// shape does not match.
    pub fn validate_shapes(&self) -> Result<(), TrainError> {
        let n = self.n_oscillators;
        let d = self.n_dims;
        check_dims("coupling", self.coupling.val().dims(), [n, n])?;
        check_dims("decay", self.decay.val().dims(), [n])?;
        check_dims("input_proj", self.input_proj.val().dims(), [d, n])?;
        check_dims("modulation", self.modulation.val().dims(), [n, n])?;
        check_dims("base_frequency", self.base_frequency.val().dims(), [n])?;
        Ok(())
    }

    /// Return cloned parameter tensor handles in the explicit bridge layout.
    ///
    /// Clones preserve Burn autodiff identities, allowing a foreign-autograd
    /// bridge to extract parameter VJPs from the graph built by [`Self::forward`].
    pub fn parameter_tensors(&self) -> ResonanceLayerParams<B> {
        ResonanceLayerParams {
            coupling: self.coupling.val(),
            decay: self.decay.val(),
            input_proj: self.input_proj.val(),
            modulation: self.modulation.val(),
            base_frequency: self.base_frequency.val(),
        }
    }

    /// Number of Kuramoto steps per forward pass.
    pub fn n_steps(&self) -> usize {
        self.n_steps
    }

    /// Timestep per step.
    pub fn dt(&self) -> f64 {
        self.dt
    }

    /// Zero-diagonal, `1/√n_oscillators`-scaled coupling matrix (P0 NaN-fix
    /// scaling from PRINet 3.0).
    fn scaled_coupling(&self) -> Tensor<B, 2> {
        let n = self.n_oscillators;
        let device = self.coupling.val().device();
        let mask = Tensor::<B, 2>::ones([n, n], &device) - Tensor::<B, 2>::eye(n, &device);
        (self.coupling.val() * mask).mul_scalar(self.coupling_scale)
    }

    /// Project input features to an initial [`ResonanceState`].
    ///
    /// See the module docs' "Documented deviation" section: this substitutes
    /// a real-valued, differentiable mapping for PRINet 3.0's FFT-based
    /// initializer.
    ///
    /// # Errors
    ///
    /// Returns [`TrainError::ShapeMismatch`] if `x`'s width is not
    /// [`Self::n_dims`].
    pub fn init_state(&self, x: Tensor<B, 2>) -> Result<ResonanceState<B>, TrainError> {
        let batch = x.dims()[0];
        check_dims("x", x.dims(), [batch, self.n_dims])?;

        let projection = x.matmul(self.input_proj.val()); // [batch, n_oscillators]
        let phase0 = projection.clone().remainder_scalar(std::f64::consts::TAU);
        let amp0 = projection.abs().clamp_min(AMP_EPS);
        let freq0 = self
            .base_frequency
            .val()
            .unsqueeze::<2>()
            .repeat_dim(0, batch);

        ResonanceState::new(phase0, amp0, freq0)
    }

    /// Advance the state by one Kuramoto step.
    ///
    /// # Errors
    ///
    /// Returns [`TrainError::ShapeMismatch`] if `state`'s width is not
    /// [`Self::n_oscillators`], and (under `strict-checks`)
    /// [`TrainError::NonFiniteState`] if the result contains a non-finite
    /// value.
    pub fn step(&self, state: ResonanceState<B>) -> Result<ResonanceState<B>, TrainError> {
        let n = self.n_oscillators;
        let (phase, amplitude, frequency) = state.into_parts();
        let batch = phase.dims()[0];
        check_dims("phase", phase.dims(), [batch, n])?;

        let coupling = self.scaled_coupling();
        let dt = self.dt;

        let p_j = phase.clone().unsqueeze_dim::<3>(1); // [batch, 1, n]
        let p_i = phase.clone().unsqueeze_dim::<3>(2); // [batch, n, 1]
        let diff = p_j - p_i; // [batch, n, n], [b,i,j] = phase[j] - phase[i]
        let sin_diff = diff.clone().sin();
        let cos_diff = diff.cos();
        let amp_weight = amplitude.clone().unsqueeze_dim::<3>(1); // [batch, 1, n], aligned to j

        let coupling_b = coupling.unsqueeze::<3>(); // [1, n, n]
        let phase_update = (coupling_b.clone() * sin_diff.clone() * amp_weight.clone())
            .sum_dim(2)
            .squeeze::<2>(2);
        let new_phase = (phase + (frequency.clone() + phase_update).mul_scalar(dt))
            .remainder_scalar(std::f64::consts::TAU);

        let amp_coupling = (coupling_b * cos_diff * amp_weight.clone())
            .sum_dim(2)
            .squeeze::<2>(2);
        let new_amplitude = (amplitude.clone()
            + ((self.decay.val().unsqueeze::<2>() * -1.0) * amplitude + amp_coupling)
                .mul_scalar(dt))
        .clamp(AMP_EPS, AMP_MAX);

        let modulation_b = self.modulation.val().unsqueeze::<3>();
        let freq_update = (modulation_b * sin_diff * amp_weight)
            .sum_dim(2)
            .squeeze::<2>(2);
        let new_frequency = frequency + freq_update.mul_scalar(dt * self.freq_adaptation_rate);

        crate::support::check_finite("phase", &new_phase)?;
        crate::support::check_finite("amplitude", &new_amplitude)?;

        ResonanceState::new(new_phase, new_amplitude, new_frequency)
    }

    /// Integrate for `n_steps` Kuramoto steps.
    ///
    /// # Errors
    ///
    /// See [`Self::step`].
    pub fn integrate(
        &self,
        mut state: ResonanceState<B>,
        n_steps: usize,
    ) -> Result<ResonanceState<B>, TrainError> {
        for _ in 0..n_steps {
            state = self.step(state)?;
        }
        Ok(state)
    }

    /// Full forward pass: project `x` to an initial state, integrate for
    /// [`Self::n_steps`], and return the final amplitudes — matching PRINet
    /// 3.0's `ResonanceLayer.forward` return contract.
    ///
    /// # Errors
    ///
    /// See [`Self::init_state`] and [`Self::step`].
    pub fn forward(&self, x: Tensor<B, 2>) -> Result<Tensor<B, 2>, TrainError> {
        let state = self.init_state(x)?;
        let n_steps = self.n_steps;
        let out = self.integrate(state, n_steps)?;
        Ok(out.into_parts().1)
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

    fn small_config() -> ResonanceLayerConfig {
        ResonanceLayerConfig::new(4, 6).unwrap()
    }

    fn seeded_layer<B: Backend>(device: &B::Device) -> ResonanceLayer<B> {
        let mut seed = Seed::new(11, 0);
        small_config().init(device, &mut seed)
    }

    // --- Config validation ---

    #[test]
    fn zero_sizes_rejected() {
        assert!(matches!(
            ResonanceLayerConfig::new(0, 6).unwrap_err(),
            TrainError::EmptyBand {
                name: "oscillators"
            }
        ));
        assert!(matches!(
            ResonanceLayerConfig::new(4, 0).unwrap_err(),
            TrainError::EmptyBand { name: "dims" }
        ));
    }

    #[test]
    fn invalid_dt_rejected() {
        assert!(matches!(
            ResonanceLayerConfig::with_params(4, 6, 10, 0.0, 0.1, 0.01).unwrap_err(),
            TrainError::InvalidTimestep { .. }
        ));
        assert!(matches!(
            ResonanceLayerConfig::with_params(4, 6, 10, f64::NAN, 0.1, 0.01).unwrap_err(),
            TrainError::InvalidTimestep { .. }
        ));
    }

    // --- Construction ---

    #[test]
    fn seeded_init_produces_expected_shapes_and_linspace_frequency() {
        let layer = seeded_layer::<TestBackend>(&device());
        assert_eq!(layer.n_oscillators(), 4);
        assert_eq!(layer.n_dims(), 6);
        assert_eq!(layer.n_steps(), 10);
        assert!((layer.dt() - 0.01).abs() < 1e-15);
        let freq = layer
            .base_frequency
            .val()
            .to_data()
            .to_vec::<f64>()
            .unwrap();
        assert_eq!(freq.len(), 4);
        assert!((freq[0] - 0.1).abs() < 1e-12);
        assert!((freq[3] - 10.0).abs() < 1e-12);
        // Strictly increasing (linspace).
        for w in freq.windows(2) {
            assert!(w[1] > w[0]);
        }
    }

    #[test]
    fn same_seed_gives_identical_parameters() {
        let mut s1 = Seed::new(5, 0);
        let mut s2 = Seed::new(5, 0);
        let l1 = small_config().init::<TestBackend>(&device(), &mut s1);
        let l2 = small_config().init::<TestBackend>(&device(), &mut s2);
        assert_eq!(
            l1.coupling.val().to_data().to_vec::<f64>().unwrap(),
            l2.coupling.val().to_data().to_vec::<f64>().unwrap()
        );
    }

    // --- Forward / shape / dtype ---

    #[test]
    fn forward_returns_expected_shape_and_is_finite() {
        let layer = seeded_layer::<TestBackend>(&device());
        let dev = device();
        let x = Tensor::<TestBackend, 2>::ones([3, 6], &dev);
        let out = layer.forward(x).unwrap();
        assert_eq!(out.dims(), [3, 4]);
        let data = out.to_data().to_vec::<f64>().unwrap();
        assert!(data.iter().all(|v| v.is_finite()));
    }

    #[test]
    fn step_output_amplitude_within_clamp_range() {
        let layer = seeded_layer::<TestBackend>(&device());
        let dev = device();
        let phase = Tensor::<TestBackend, 2>::zeros([1, 4], &dev);
        let amp = Tensor::<TestBackend, 2>::full([1, 4], 1e6, &dev);
        let freq = Tensor::<TestBackend, 2>::ones([1, 4], &dev);
        let state = ResonanceState::new(phase, amp, freq).unwrap();
        let next = layer.step(state).unwrap();
        let a = next.amplitude().clone().to_data().to_vec::<f64>().unwrap();
        for v in a {
            assert!(
                (AMP_EPS..=AMP_MAX).contains(&v),
                "amplitude {v} out of clamp range"
            );
        }
    }

    #[test]
    fn step_output_phase_wrapped() {
        let layer = seeded_layer::<TestBackend>(&device());
        let dev = device();
        let phase = Tensor::<TestBackend, 2>::full([1, 4], std::f64::consts::TAU - 1e-4, &dev);
        let amp = Tensor::<TestBackend, 2>::ones([1, 4], &dev);
        let freq = Tensor::<TestBackend, 2>::full([1, 4], 100.0, &dev);
        let state = ResonanceState::new(phase, amp, freq).unwrap();
        let next = layer.step(state).unwrap();
        let p = next.phase().clone().to_data().to_vec::<f64>().unwrap();
        for v in p {
            assert!(
                (0.0..std::f64::consts::TAU).contains(&v),
                "phase {v} not wrapped"
            );
        }
    }

    #[test]
    fn coupling_diagonal_does_not_self_couple() {
        // A single oscillator has no off-diagonal coupling partner, so phase
        // evolves at exactly its own frequency and amplitude only decays.
        let cfg = ResonanceLayerConfig::new(1, 2).unwrap();
        let dev = device();
        let mut seed = Seed::new(3, 0);
        let layer = cfg.init::<TestBackend>(&dev, &mut seed);
        let phase = Tensor::<TestBackend, 2>::zeros([1, 1], &dev);
        let amp = Tensor::<TestBackend, 2>::full([1, 1], 2.0, &dev);
        let freq = Tensor::<TestBackend, 2>::full([1, 1], 5.0, &dev);
        let state = ResonanceState::new(phase, amp, freq).unwrap();
        let next = layer.step(state).unwrap();
        let p = next.phase().clone().to_data().to_vec::<f64>().unwrap()[0];
        assert!((p - 5.0 * layer.dt()).abs() < 1e-10);
    }

    // --- Numerical / shape guards ---

    #[cfg(feature = "strict-checks")]
    #[test]
    fn step_rejects_non_finite_input_under_strict_checks() {
        let layer = seeded_layer::<TestBackend>(&device());
        let dev = device();
        let phase = Tensor::<TestBackend, 2>::full([1, 4], f64::NAN, &dev);
        let amp = Tensor::<TestBackend, 2>::ones([1, 4], &dev);
        let freq = Tensor::<TestBackend, 2>::ones([1, 4], &dev);
        let state = ResonanceState::new(phase, amp, freq).unwrap();
        let err = layer.step(state).unwrap_err();
        assert!(matches!(err, TrainError::NonFiniteState { name: "phase" }));
    }

    #[test]
    fn init_state_rejects_wrong_width() {
        let layer = seeded_layer::<TestBackend>(&device());
        let dev = device();
        let x = Tensor::<TestBackend, 2>::ones([2, 3], &dev);
        let err = layer.init_state(x).unwrap_err();
        assert!(matches!(err, TrainError::ShapeMismatch { name: "x", .. }));
    }

    #[test]
    fn state_rejects_mismatched_shapes() {
        let dev = device();
        let phase = Tensor::<TestBackend, 2>::zeros([1, 4], &dev);
        let amp = Tensor::<TestBackend, 2>::ones([1, 3], &dev);
        let freq = Tensor::<TestBackend, 2>::ones([1, 4], &dev);
        let err = ResonanceState::new(phase, amp, freq).unwrap_err();
        assert!(matches!(
            err,
            TrainError::ShapeMismatch {
                name: "amplitude",
                ..
            }
        ));
    }

    #[test]
    fn step_rejects_wrong_width() {
        let layer = seeded_layer::<TestBackend>(&device());
        let dev = device();
        let phase = Tensor::<TestBackend, 2>::zeros([1, 2], &dev);
        let amp = Tensor::<TestBackend, 2>::ones([1, 2], &dev);
        let freq = Tensor::<TestBackend, 2>::ones([1, 2], &dev);
        let state = ResonanceState::new(phase, amp, freq).unwrap();
        let err = layer.step(state).unwrap_err();
        assert!(matches!(
            err,
            TrainError::ShapeMismatch { name: "phase", .. }
        ));
    }

    // --- Gradient reference tests ---

    #[test]
    fn gradients_flow_to_every_parameter() {
        let _guard = crate::support::autodiff_test_guard();
        let dev: <TestAutodiffBackend as Backend>::Device = Default::default();
        let mut seed = Seed::new(21, 0);
        let layer = small_config().init::<TestAutodiffBackend>(&dev, &mut seed);
        let x = Tensor::<TestAutodiffBackend, 2>::ones([2, 6], &dev).require_grad();

        let out = layer.forward(x).unwrap();
        let loss = out.sum_dim(1).sum_dim(0);
        let grads = loss.backward();

        for grad in [
            layer
                .coupling
                .val()
                .grad(&grads)
                .map(|g| g.to_data().to_vec::<f64>().unwrap()),
            layer
                .decay
                .val()
                .grad(&grads)
                .map(|g| g.to_data().to_vec::<f64>().unwrap()),
            layer
                .input_proj
                .val()
                .grad(&grads)
                .map(|g| g.to_data().to_vec::<f64>().unwrap()),
            layer
                .base_frequency
                .val()
                .grad(&grads)
                .map(|g| g.to_data().to_vec::<f64>().unwrap()),
        ] {
            let values = grad.expect("gradient must be present for every trainable parameter");
            assert!(values.iter().all(|v| v.is_finite()));
        }
    }

    /// Build explicit params from a fixed seed, overriding one off-diagonal
    /// coupling entry so both the analytic and finite-difference paths probe
    /// the exact same parameter.
    fn params_with_coupling_entry<B: Backend>(
        cfg: &ResonanceLayerConfig,
        device: &B::Device,
        coupling_01: f64,
    ) -> ResonanceLayerParams<B> {
        let mut seed = Seed::new(77, 0);
        let base = cfg.init::<B>(device, &mut seed);
        let mut c = base.coupling.val().to_data().to_vec::<f64>().unwrap();
        c[1] = coupling_01;
        let coupling = Tensor::from_data(burn::tensor::TensorData::new(c, vec![3, 3]), device);
        ResonanceLayerParams {
            coupling,
            decay: base.decay.val(),
            input_proj: base.input_proj.val(),
            modulation: base.modulation.val(),
            base_frequency: base.base_frequency.val(),
        }
    }

    #[test]
    fn gradient_matches_central_finite_difference() {
        let _guard = crate::support::autodiff_test_guard();
        let dev: <TestAutodiffBackend as Backend>::Device = Default::default();
        let cfg = ResonanceLayerConfig::new(3, 2).unwrap();

        let base_c01 = {
            let mut seed = Seed::new(77, 0);
            let base = cfg.init::<TestBackend>(&Default::default(), &mut seed);
            base.coupling.val().to_data().to_vec::<f64>().unwrap()[1]
        };

        let loss_for = |coupling_01: f64| -> f64 {
            let device: <TestBackend as Backend>::Device = Default::default();
            let params = params_with_coupling_entry::<TestBackend>(&cfg, &device, coupling_01);
            let layer = cfg.init_from_params(params).unwrap();
            let x = Tensor::<TestBackend, 2>::ones([1, 2], &device) * 0.5;
            let out = layer.forward(x).unwrap();
            out.to_data().to_vec::<f64>().unwrap().iter().sum()
        };

        let eps = 1e-6;
        let numerical = (loss_for(base_c01 + eps) - loss_for(base_c01 - eps)) / (2.0 * eps);

        // Analytic gradient via autodiff on the same computation.
        let mut params = params_with_coupling_entry::<TestAutodiffBackend>(&cfg, &dev, base_c01);
        let coupling_grad_tensor = params.coupling.require_grad();
        params.coupling = coupling_grad_tensor.clone();
        let layer = cfg.init_from_params(params).unwrap();
        let x = Tensor::<TestAutodiffBackend, 2>::ones([1, 2], &dev) * 0.5;
        let out = layer.forward(x).unwrap();
        let loss = out.sum_dim(1).sum_dim(0);
        let grads = loss.backward();
        let grad_data = coupling_grad_tensor
            .grad(&grads)
            .unwrap()
            .to_data()
            .to_vec::<f64>()
            .unwrap();
        let analytic = grad_data[1];

        assert!(
            (analytic - numerical).abs() < 1e-3,
            "analytic {analytic} vs finite-difference {numerical}"
        );
    }

    // --- Serialization ---

    #[test]
    fn record_roundtrip_preserves_parameters() {
        use burn::record::{BinBytesRecorder, DoublePrecisionSettings, Recorder};

        let dev = device();
        let layer = seeded_layer::<TestBackend>(&dev);
        let before = layer.coupling.val().to_data().to_vec::<f64>().unwrap();

        let recorder = BinBytesRecorder::<DoublePrecisionSettings>::default();
        let bytes =
            Recorder::<TestBackend>::record(&recorder, layer.clone().into_record(), ()).unwrap();
        let record = Recorder::<TestBackend>::load(&recorder, bytes, &dev).unwrap();
        let restored = layer.load_record(record);

        let after = restored.coupling.val().to_data().to_vec::<f64>().unwrap();
        assert_eq!(before, after);
        assert_eq!(restored.n_oscillators(), 4);
        assert_eq!(restored.n_dims(), 6);
    }

    #[test]
    fn validate_shapes_passes_for_freshly_initialized_layer() {
        let dev = device();
        let layer = seeded_layer::<TestBackend>(&dev);
        assert!(layer.validate_shapes().is_ok());
    }

    /// WP025-F1 regression (prin-train level): loading a well-formed record
    /// from a differently-configured layer must be caught by
    /// `validate_shapes`, mirroring exactly the checkpoint-load path
    /// `crates/prin-py/src/bindings/train.rs`'s `load_state_dict` guards.
    #[test]
    fn validate_shapes_detects_mismatch_after_loading_a_differently_configured_record() {
        use burn::record::{BinBytesRecorder, DoublePrecisionSettings, Recorder};

        let dev = device();
        let target = seeded_layer::<TestBackend>(&dev); // small_config: 4 oscillators, 6 dims
        let mut seed = Seed::new(77, 0);
        let donor = ResonanceLayerConfig::new(9, 6)
            .unwrap()
            .init::<TestBackend>(&dev, &mut seed);

        let recorder = BinBytesRecorder::<DoublePrecisionSettings>::default();
        let bytes = Recorder::<TestBackend>::record(&recorder, donor.into_record(), ()).unwrap();
        let record = Recorder::<TestBackend>::load(&recorder, bytes, &dev).unwrap();
        let candidate = target.load_record(record);

        let err = candidate.validate_shapes().unwrap_err();
        assert!(matches!(
            err,
            TrainError::ShapeMismatch {
                name: "coupling",
                ..
            }
        ));
    }
}

#[cfg(test)]
mod proptests {
    use super::*;
    use burn::backend::NdArray;
    use proptest::prelude::*;

    type TestBackend = NdArray<f64>;

    proptest! {
        #[test]
        fn forward_output_always_finite_and_in_range(
            n_osc in 1usize..=6,
            n_dims in 1usize..=6,
            batch in 1usize..=4,
            seed_val in 0u64..1000,
        ) {
            let cfg = ResonanceLayerConfig::new(n_osc, n_dims).unwrap();
            let dev = Default::default();
            let mut seed = Seed::new(seed_val as u128, 0);
            let layer = cfg.init::<TestBackend>(&dev, &mut seed);

            let mut xseed = Seed::new(seed_val as u128, 1);
            let x = seeded_uniform::<TestBackend, 2>([batch, n_dims], -2.0, 2.0, &dev, &mut xseed);

            let out = layer.forward(x).unwrap();
            let data = out.to_data().to_vec::<f64>().unwrap();
            prop_assert_eq!(data.len(), batch * n_osc);
            for v in &data {
                prop_assert!(v.is_finite());
                prop_assert!((1e-6..=10.0).contains(v));
            }
        }
    }
}
