//! Discrete-time trainable multi-rate hierarchical oscillator network.
//!
//! [`DiscreteDeltaThetaGamma`] is the Burn `Module` rebuild of PRINet 3.0's
//! `core.propagation.networks.DiscreteDeltaThetaGamma`: a fixed number of
//! discrete macro steps (learned coupling + phase-amplitude-coupling gating)
//! rather than an inner ODE loop. It is the trainable counterpart to
//! [`prin_dynamics::bands::BandNetwork`], which documents on itself why the
//! discrete-time variant lives here instead.
//!
//! # Correspondence to the PRINet 3.0 reference
//!
//! Per macro step (`step`), for each band `b` with phase `φ_b`, amplitude
//! `a_b`, learned intra-band coupling `W_b`, and center frequency `f_b`:
//!
//! 1. **Phase advance:** `φ_b' = wrap(φ_b + 2π·f_b·dt + dt·Σⱼ W_b[i,j]·sin(φ_b[j] − φ_b[i]))`.
//! 2. **PAC gating (multiplicative):** theta amplitude is gated by
//!    `σ(W_pac_dt · [cos(φ_δ'), sin(φ_δ')] + b_pac_dt)`; gamma amplitude by
//!    the analogous delta→theta→gamma gate from `φ_θ'`.
//! 3. **Amplitude update:** Stuart–Landau `a' = clamp(a + dt·a·(μ − a²), 1e-6, 10.0)`
//!    with a learned per-band growth rate `μ`.
//!
//! This is a line-for-line port of `DiscreteDeltaThetaGamma.step` (PRINet 3.0
//! `nn`-tracked `torch.nn.Module`); every operation above has a matching
//! Burn tensor op in [`step`](DiscreteDeltaThetaGamma::step). Golden-value
//! parity tests live in `tests/parity_bands.rs`.
//!
//! All operations are batched: `(batch, n_total)` tensors throughout, no
//! per-sample loop, matching the reference.
//!
//! # Example
//!
//! ```
//! use burn::backend::NdArray;
//! use burn::tensor::Tensor;
//! use prin_dynamics::Seed;
//! use prin_train::bands::{DiscreteBandState, DiscreteDeltaThetaGammaConfig};
//!
//! type Backend = NdArray<f32>;
//!
//! let cfg = DiscreteDeltaThetaGammaConfig::new(2, 4, 8).unwrap();
//! let device = Default::default();
//! let mut seed = Seed::new(0, 0);
//! let net = cfg.init::<Backend>(&device, &mut seed);
//!
//! let phase = Tensor::<Backend, 2>::zeros([1, net.n_total()], &device);
//! let amplitude = Tensor::<Backend, 2>::ones([1, net.n_total()], &device);
//! let state = DiscreteBandState::new(phase, amplitude).unwrap();
//!
//! let next = net.step(state, 0.01).unwrap();
//! assert_eq!(next.phase().dims(), [1, net.n_total()]);
//! ```

use burn::module::{Module, Param};
use burn::tensor::activation::sigmoid;
use burn::tensor::backend::Backend;
use burn::tensor::Tensor;
use prin_dynamics::Seed;

use crate::error::TrainError;
use crate::support::{check_dims, seeded_uniform, validate_dt, validate_finite, xavier_bound};

/// Validated discrete-time band state: concatenated per-oscillator phase and
/// amplitude, both shape `[batch, n_total]`.
///
/// This is the state contract [`DiscreteDeltaThetaGamma::step`] and
/// [`DiscreteDeltaThetaGamma::integrate`] operate on — constructing one
/// validates that `phase` and `amplitude` share a shape.
#[derive(Debug, Clone)]
pub struct DiscreteBandState<B: Backend> {
    phase: Tensor<B, 2>,
    amplitude: Tensor<B, 2>,
}

impl<B: Backend> DiscreteBandState<B> {
    /// Validate and wrap a `(phase, amplitude)` pair.
    ///
    /// # Errors
    ///
    /// Returns [`TrainError::ShapeMismatch`] if `phase` and `amplitude` do
    /// not share the same shape.
    pub fn new(phase: Tensor<B, 2>, amplitude: Tensor<B, 2>) -> Result<Self, TrainError> {
        let p_dims = phase.dims();
        let a_dims = amplitude.dims();
        check_dims("amplitude", a_dims, p_dims)?;
        Ok(Self { phase, amplitude })
    }

    /// The phase tensor, shape `[batch, n_total]`.
    pub fn phase(&self) -> &Tensor<B, 2> {
        &self.phase
    }

    /// The amplitude tensor, shape `[batch, n_total]`.
    pub fn amplitude(&self) -> &Tensor<B, 2> {
        &self.amplitude
    }

    /// Consume the state, returning `(phase, amplitude)`.
    pub fn into_parts(self) -> (Tensor<B, 2>, Tensor<B, 2>) {
        (self.phase, self.amplitude)
    }
}

/// Explicit parameter tensors for [`DiscreteDeltaThetaGamma`] construction.
///
/// Used by golden-reference tests (fixed weights compared against a
/// PRINet-3.0-derived Python computation) and by any checkpoint path outside
/// [`burn::record`]. Shapes are validated against the owning
/// [`DiscreteDeltaThetaGammaConfig`] by
/// [`DiscreteDeltaThetaGammaConfig::init_from_params`].
pub struct DiscreteDeltaThetaGammaParams<B: Backend> {
    /// Delta-band center frequencies, shape `[n_delta]`.
    pub delta_freq: Tensor<B, 1>,
    /// Theta-band center frequencies, shape `[n_theta]`.
    pub theta_freq: Tensor<B, 1>,
    /// Gamma-band center frequencies, shape `[n_gamma]`.
    pub gamma_freq: Tensor<B, 1>,
    /// Delta intra-band coupling, shape `[n_delta, n_delta]`.
    pub w_delta: Tensor<B, 2>,
    /// Theta intra-band coupling, shape `[n_theta, n_theta]`.
    pub w_theta: Tensor<B, 2>,
    /// Gamma intra-band coupling, shape `[n_gamma, n_gamma]`.
    pub w_gamma: Tensor<B, 2>,
    /// Delta→theta PAC gate weight, shape `[2 * n_delta, n_theta]`.
    pub w_pac_dt: Tensor<B, 2>,
    /// Delta→theta PAC gate bias, shape `[n_theta]`.
    pub b_pac_dt: Tensor<B, 1>,
    /// Theta→gamma PAC gate weight, shape `[2 * n_theta, n_gamma]`.
    pub w_pac_tg: Tensor<B, 2>,
    /// Theta→gamma PAC gate bias, shape `[n_gamma]`.
    pub b_pac_tg: Tensor<B, 1>,
    /// Delta Stuart–Landau growth rate, shape `[1, 1]`.
    pub mu_delta: Tensor<B, 2>,
    /// Theta Stuart–Landau growth rate, shape `[1, 1]`.
    pub mu_theta: Tensor<B, 2>,
    /// Gamma Stuart–Landau growth rate, shape `[1, 1]`.
    pub mu_gamma: Tensor<B, 2>,
}

/// Validated hyperparameters for [`DiscreteDeltaThetaGamma`].
///
/// Defaults (`new`) match the PRINet 3.0 reference:
/// `coupling_strength=2.0, pac_depth=0.3, delta_freq=2.0, theta_freq=6.0,
/// gamma_freq=40.0`.
#[derive(Clone, Debug, PartialEq)]
pub struct DiscreteDeltaThetaGammaConfig {
    /// Number of delta-band oscillators.
    pub n_delta: usize,
    /// Number of theta-band oscillators.
    pub n_theta: usize,
    /// Number of gamma-band oscillators.
    pub n_gamma: usize,
    /// Initial intra-band coupling magnitude.
    pub coupling_strength: f64,
    /// Initial PAC gate bias.
    pub pac_depth: f64,
    /// Delta-band center frequency (Hz).
    pub delta_freq: f64,
    /// Theta-band center frequency (Hz).
    pub theta_freq: f64,
    /// Gamma-band center frequency (Hz).
    pub gamma_freq: f64,
}

impl DiscreteDeltaThetaGammaConfig {
    /// Validated configuration with PRINet 3.0's default hyperparameters.
    ///
    /// # Errors
    ///
    /// Returns [`TrainError::EmptyBand`] if any band size is zero.
    pub fn new(n_delta: usize, n_theta: usize, n_gamma: usize) -> Result<Self, TrainError> {
        Self::with_params(n_delta, n_theta, n_gamma, 2.0, 0.3, 2.0, 6.0, 40.0)
    }

    /// Validated configuration with explicit hyperparameters.
    ///
    /// # Errors
    ///
    /// Returns [`TrainError::EmptyBand`] if any band size is zero, or
    /// [`TrainError::NonFiniteParameter`] if any hyperparameter is
    /// non-finite.
    #[allow(clippy::too_many_arguments)]
    pub fn with_params(
        n_delta: usize,
        n_theta: usize,
        n_gamma: usize,
        coupling_strength: f64,
        pac_depth: f64,
        delta_freq: f64,
        theta_freq: f64,
        gamma_freq: f64,
    ) -> Result<Self, TrainError> {
        if n_delta == 0 {
            return Err(TrainError::EmptyBand { name: "delta" });
        }
        if n_theta == 0 {
            return Err(TrainError::EmptyBand { name: "theta" });
        }
        if n_gamma == 0 {
            return Err(TrainError::EmptyBand { name: "gamma" });
        }
        validate_finite("coupling_strength", coupling_strength)?;
        validate_finite("pac_depth", pac_depth)?;
        validate_finite("delta_freq", delta_freq)?;
        validate_finite("theta_freq", theta_freq)?;
        validate_finite("gamma_freq", gamma_freq)?;
        Ok(Self {
            n_delta,
            n_theta,
            n_gamma,
            coupling_strength,
            pac_depth,
            delta_freq,
            theta_freq,
            gamma_freq,
        })
    }

    /// Total oscillator count across all three bands.
    pub fn n_total(&self) -> usize {
        self.n_delta + self.n_theta + self.n_gamma
    }

    /// Initialize a [`DiscreteDeltaThetaGamma`] with parameters drawn from
    /// the project's deterministic [`Seed`] (Coding Standards §1.3).
    ///
    /// Center frequencies are set to the configured constant per band
    /// (matching PRINet 3.0's `torch.full`, not random). Intra-band coupling
    /// is uniform on `[-coupling_strength/n, coupling_strength/n]`, PAC gate
    /// weights use a Xavier-uniform bound (gain `0.5`, matching PRINet 3.0's
    /// `nn.init.xavier_uniform_(gain=0.5)`) with bias initialized to
    /// `pac_depth`, and every `μ` starts at `1.0` — all matching the
    /// reference exactly except the coupling-matrix distribution (uniform
    /// here vs. PRINet 3.0's `torch.randn`; only the initial scale is
    /// load-bearing for training, not the exact distribution shape).
    pub fn init<B: Backend>(
        &self,
        device: &B::Device,
        seed: &mut Seed,
    ) -> DiscreteDeltaThetaGamma<B> {
        let (nd, nt, ng) = (self.n_delta, self.n_theta, self.n_gamma);
        let cs = self.coupling_strength;

        let delta_freq =
            seeded_uniform::<B, 1>([nd], self.delta_freq, self.delta_freq, device, seed);
        let theta_freq =
            seeded_uniform::<B, 1>([nt], self.theta_freq, self.theta_freq, device, seed);
        let gamma_freq =
            seeded_uniform::<B, 1>([ng], self.gamma_freq, self.gamma_freq, device, seed);

        let w_delta =
            seeded_uniform::<B, 2>([nd, nd], -cs / nd as f64, cs / nd as f64, device, seed);
        let w_theta =
            seeded_uniform::<B, 2>([nt, nt], -cs / nt as f64, cs / nt as f64, device, seed);
        let w_gamma =
            seeded_uniform::<B, 2>([ng, ng], -cs / ng as f64, cs / ng as f64, device, seed);

        let dt_bound = xavier_bound(2 * nd, nt, 0.5);
        let w_pac_dt = seeded_uniform::<B, 2>([2 * nd, nt], -dt_bound, dt_bound, device, seed);
        let b_pac_dt = seeded_uniform::<B, 1>([nt], self.pac_depth, self.pac_depth, device, seed);

        let tg_bound = xavier_bound(2 * nt, ng, 0.5);
        let w_pac_tg = seeded_uniform::<B, 2>([2 * nt, ng], -tg_bound, tg_bound, device, seed);
        let b_pac_tg = seeded_uniform::<B, 1>([ng], self.pac_depth, self.pac_depth, device, seed);

        let mu_delta = seeded_uniform::<B, 2>([1, 1], 1.0, 1.0, device, seed);
        let mu_theta = seeded_uniform::<B, 2>([1, 1], 1.0, 1.0, device, seed);
        let mu_gamma = seeded_uniform::<B, 2>([1, 1], 1.0, 1.0, device, seed);

        self.init_from_params(DiscreteDeltaThetaGammaParams {
            delta_freq,
            theta_freq,
            gamma_freq,
            w_delta,
            w_theta,
            w_gamma,
            w_pac_dt,
            b_pac_dt,
            w_pac_tg,
            b_pac_tg,
            mu_delta,
            mu_theta,
            mu_gamma,
        })
        .expect("seeded-init parameter shapes are constructed from `self` and always valid")
    }

    /// Build a [`DiscreteDeltaThetaGamma`] from explicit parameter tensors.
    ///
    /// # Errors
    ///
    /// Returns [`TrainError::ShapeMismatch`] if any tensor's shape does not
    /// match the band sizes declared by this config.
    pub fn init_from_params<B: Backend>(
        &self,
        params: DiscreteDeltaThetaGammaParams<B>,
    ) -> Result<DiscreteDeltaThetaGamma<B>, TrainError> {
        let (nd, nt, ng) = (self.n_delta, self.n_theta, self.n_gamma);
        check_dims("delta_freq", params.delta_freq.dims(), [nd])?;
        check_dims("theta_freq", params.theta_freq.dims(), [nt])?;
        check_dims("gamma_freq", params.gamma_freq.dims(), [ng])?;
        check_dims("w_delta", params.w_delta.dims(), [nd, nd])?;
        check_dims("w_theta", params.w_theta.dims(), [nt, nt])?;
        check_dims("w_gamma", params.w_gamma.dims(), [ng, ng])?;
        check_dims("w_pac_dt", params.w_pac_dt.dims(), [2 * nd, nt])?;
        check_dims("b_pac_dt", params.b_pac_dt.dims(), [nt])?;
        check_dims("w_pac_tg", params.w_pac_tg.dims(), [2 * nt, ng])?;
        check_dims("b_pac_tg", params.b_pac_tg.dims(), [ng])?;
        check_dims("mu_delta", params.mu_delta.dims(), [1, 1])?;
        check_dims("mu_theta", params.mu_theta.dims(), [1, 1])?;
        check_dims("mu_gamma", params.mu_gamma.dims(), [1, 1])?;

        Ok(DiscreteDeltaThetaGamma {
            delta_freq: Param::initialized(Default::default(), params.delta_freq.require_grad()),
            theta_freq: Param::initialized(Default::default(), params.theta_freq.require_grad()),
            gamma_freq: Param::initialized(Default::default(), params.gamma_freq.require_grad()),
            w_delta: Param::initialized(Default::default(), params.w_delta.require_grad()),
            w_theta: Param::initialized(Default::default(), params.w_theta.require_grad()),
            w_gamma: Param::initialized(Default::default(), params.w_gamma.require_grad()),
            w_pac_dt: Param::initialized(Default::default(), params.w_pac_dt.require_grad()),
            b_pac_dt: Param::initialized(Default::default(), params.b_pac_dt.require_grad()),
            w_pac_tg: Param::initialized(Default::default(), params.w_pac_tg.require_grad()),
            b_pac_tg: Param::initialized(Default::default(), params.b_pac_tg.require_grad()),
            mu_delta: Param::initialized(Default::default(), params.mu_delta.require_grad()),
            mu_theta: Param::initialized(Default::default(), params.mu_theta.require_grad()),
            mu_gamma: Param::initialized(Default::default(), params.mu_gamma.require_grad()),
            n_delta: nd,
            n_theta: nt,
            n_gamma: ng,
        })
    }
}

/// Discrete-time trainable multi-rate hierarchical oscillator network.
///
/// See the module docs for the exact per-step formula. Construct via
/// [`DiscreteDeltaThetaGammaConfig::init`] (seeded random parameters) or
/// [`DiscreteDeltaThetaGammaConfig::init_from_params`] (explicit tensors).
#[derive(Module, Debug)]
pub struct DiscreteDeltaThetaGamma<B: Backend> {
    delta_freq: Param<Tensor<B, 1>>,
    theta_freq: Param<Tensor<B, 1>>,
    gamma_freq: Param<Tensor<B, 1>>,
    w_delta: Param<Tensor<B, 2>>,
    w_theta: Param<Tensor<B, 2>>,
    w_gamma: Param<Tensor<B, 2>>,
    w_pac_dt: Param<Tensor<B, 2>>,
    b_pac_dt: Param<Tensor<B, 1>>,
    w_pac_tg: Param<Tensor<B, 2>>,
    b_pac_tg: Param<Tensor<B, 1>>,
    mu_delta: Param<Tensor<B, 2>>,
    mu_theta: Param<Tensor<B, 2>>,
    mu_gamma: Param<Tensor<B, 2>>,
    n_delta: usize,
    n_theta: usize,
    n_gamma: usize,
}

impl<B: Backend> DiscreteDeltaThetaGamma<B> {
    /// Number of delta-band oscillators.
    pub fn n_delta(&self) -> usize {
        self.n_delta
    }

    /// Number of theta-band oscillators.
    pub fn n_theta(&self) -> usize {
        self.n_theta
    }

    /// Number of gamma-band oscillators.
    pub fn n_gamma(&self) -> usize {
        self.n_gamma
    }

    /// Total oscillator count across all three bands.
    pub fn n_total(&self) -> usize {
        self.n_delta + self.n_theta + self.n_gamma
    }

    /// Whether `w_delta` currently requires grad — crate-internal
    /// introspection for [`crate::ablation::PhaseTrackerFrozen`]'s
    /// regression test (confirms [`burn::module::Module::no_grad`]
    /// actually froze the coupling weights it wraps).
    #[cfg(test)]
    pub(crate) fn w_delta_requires_grad(&self) -> bool {
        self.w_delta.val().is_require_grad()
    }

    /// Advance all three bands by one discrete macro step.
    ///
    /// # Errors
    ///
    /// Returns [`TrainError::ShapeMismatch`] if `state`'s width is not
    /// [`Self::n_total`], [`TrainError::InvalidTimestep`] if `dt` is
    /// non-finite or non-positive, and (under `strict-checks`)
    /// [`TrainError::NonFiniteState`] if the result contains a non-finite
    /// value.
    pub fn step(
        &self,
        state: DiscreteBandState<B>,
        dt: f64,
    ) -> Result<DiscreteBandState<B>, TrainError> {
        validate_dt(dt)?;
        let (nd, nt, ng) = (self.n_delta, self.n_theta, self.n_gamma);
        let (phase, amplitude) = state.into_parts();
        let batch = phase.dims()[0];
        check_dims("phase", phase.dims(), [batch, nd + nt + ng])?;

        let p_d = phase.clone().narrow(1, 0, nd);
        let p_t = phase.clone().narrow(1, nd, nt);
        let p_g = phase.narrow(1, nd + nt, ng);
        let a_d = amplitude.clone().narrow(1, 0, nd);
        let a_t = amplitude.clone().narrow(1, nd, nt);
        let a_g = amplitude.narrow(1, nd + nt, ng);

        let two_pi_dt = std::f64::consts::TAU * dt;

        let new_p_d = wrap_phase(
            p_d.clone()
                + self.delta_freq.val().unsqueeze::<2>().mul_scalar(two_pi_dt)
                + phase_coupling(p_d, self.w_delta.val()).mul_scalar(dt),
        );
        let new_p_t = wrap_phase(
            p_t.clone()
                + self.theta_freq.val().unsqueeze::<2>().mul_scalar(two_pi_dt)
                + phase_coupling(p_t, self.w_theta.val()).mul_scalar(dt),
        );
        let new_p_g = wrap_phase(
            p_g.clone()
                + self.gamma_freq.val().unsqueeze::<2>().mul_scalar(two_pi_dt)
                + phase_coupling(p_g, self.w_gamma.val()).mul_scalar(dt),
        );

        let delta_repr = Tensor::cat(vec![new_p_d.clone().cos(), new_p_d.clone().sin()], 1);
        let gate_dt =
            sigmoid(delta_repr.matmul(self.w_pac_dt.val()) + self.b_pac_dt.val().unsqueeze::<2>());
        let a_t = a_t * gate_dt;

        let theta_repr = Tensor::cat(vec![new_p_t.clone().cos(), new_p_t.clone().sin()], 1);
        let gate_tg =
            sigmoid(theta_repr.matmul(self.w_pac_tg.val()) + self.b_pac_tg.val().unsqueeze::<2>());
        let a_g = a_g * gate_tg;

        let new_a_d = amplitude_update(a_d, self.mu_delta.val(), dt);
        let new_a_t = amplitude_update(a_t, self.mu_theta.val(), dt);
        let new_a_g = amplitude_update(a_g, self.mu_gamma.val(), dt);

        let new_phase = Tensor::cat(vec![new_p_d, new_p_t, new_p_g], 1);
        let new_amp = Tensor::cat(vec![new_a_d, new_a_t, new_a_g], 1);

        crate::support::check_finite("phase", &new_phase)?;
        crate::support::check_finite("amplitude", &new_amp)?;

        DiscreteBandState::new(new_phase, new_amp)
    }

    /// Integrate for `n_steps` discrete macro steps.
    ///
    /// # Errors
    ///
    /// See [`Self::step`].
    pub fn integrate(
        &self,
        mut state: DiscreteBandState<B>,
        n_steps: usize,
        dt: f64,
    ) -> Result<DiscreteBandState<B>, TrainError> {
        for _ in 0..n_steps {
            state = self.step(state, dt)?;
        }
        Ok(state)
    }
}

/// Wrap a phase tensor to `[0, 2π)`.
fn wrap_phase<B: Backend, const D: usize>(phase: Tensor<B, D>) -> Tensor<B, D> {
    phase.remainder_scalar(std::f64::consts::TAU)
}

/// `Σⱼ W[i,j]·sin(φ[j] − φ[i])`, batched: `phase` shape `[batch, n]`, `w`
/// shape `[n, n]`, result shape `[batch, n]`.
fn phase_coupling<B: Backend>(phase: Tensor<B, 2>, w: Tensor<B, 2>) -> Tensor<B, 2> {
    let p_j = phase.clone().unsqueeze_dim::<3>(1); // [batch, 1, n]
    let p_i = phase.unsqueeze_dim::<3>(2); // [batch, n, 1]
    let sin_diff = (p_j - p_i).sin(); // [batch, n, n], [b,i,j] = sin(phase[j] - phase[i])
    let w_b = w.unsqueeze::<3>(); // [1, n, n]
    (w_b * sin_diff).sum_dim(2).squeeze::<2>(2)
}

/// Stuart–Landau amplitude update: `clamp(a + dt·a·(μ − a²), 1e-6, 10.0)`.
fn amplitude_update<B: Backend>(amp: Tensor<B, 2>, mu: Tensor<B, 2>, dt: f64) -> Tensor<B, 2> {
    let da = (amp.clone() * (mu - amp.clone().powf_scalar(2.0))).mul_scalar(dt);
    (amp + da).clamp(1e-6, 10.0)
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

    fn small_config() -> DiscreteDeltaThetaGammaConfig {
        DiscreteDeltaThetaGammaConfig::new(2, 3, 4).unwrap()
    }

    fn seeded_net<B: Backend>(device: &B::Device) -> DiscreteDeltaThetaGamma<B> {
        let mut seed = Seed::new(7, 0);
        small_config().init(device, &mut seed)
    }

    // --- Config validation ---

    #[test]
    fn zero_band_sizes_rejected() {
        assert!(matches!(
            DiscreteDeltaThetaGammaConfig::new(0, 3, 4).unwrap_err(),
            TrainError::EmptyBand { name: "delta" }
        ));
        assert!(matches!(
            DiscreteDeltaThetaGammaConfig::new(2, 0, 4).unwrap_err(),
            TrainError::EmptyBand { name: "theta" }
        ));
        assert!(matches!(
            DiscreteDeltaThetaGammaConfig::new(2, 3, 0).unwrap_err(),
            TrainError::EmptyBand { name: "gamma" }
        ));
    }

    #[test]
    fn non_finite_hyperparameter_rejected() {
        let err =
            DiscreteDeltaThetaGammaConfig::with_params(2, 3, 4, f64::NAN, 0.3, 2.0, 6.0, 40.0)
                .unwrap_err();
        assert!(matches!(
            err,
            TrainError::NonFiniteParameter {
                name: "coupling_strength",
                ..
            }
        ));
    }

    #[test]
    fn n_total_sums_band_sizes() {
        assert_eq!(small_config().n_total(), 9);
    }

    // --- Construction ---

    #[test]
    fn seeded_init_produces_expected_shapes() {
        let net = seeded_net::<TestBackend>(&device());
        assert_eq!(net.n_delta(), 2);
        assert_eq!(net.n_theta(), 3);
        assert_eq!(net.n_gamma(), 4);
        assert_eq!(net.n_total(), 9);
    }

    #[test]
    fn same_seed_gives_identical_parameters() {
        let mut s1 = Seed::new(123, 0);
        let mut s2 = Seed::new(123, 0);
        let net1 = small_config().init::<TestBackend>(&device(), &mut s1);
        let net2 = small_config().init::<TestBackend>(&device(), &mut s2);
        let d1 = net1.w_delta.val().to_data().to_vec::<f64>().unwrap();
        let d2 = net2.w_delta.val().to_data().to_vec::<f64>().unwrap();
        assert_eq!(d1, d2);
    }

    #[test]
    fn different_seeds_give_different_coupling() {
        let mut s1 = Seed::new(1, 0);
        let mut s2 = Seed::new(2, 0);
        let net1 = small_config().init::<TestBackend>(&device(), &mut s1);
        let net2 = small_config().init::<TestBackend>(&device(), &mut s2);
        let d1 = net1.w_delta.val().to_data().to_vec::<f64>().unwrap();
        let d2 = net2.w_delta.val().to_data().to_vec::<f64>().unwrap();
        assert_ne!(d1, d2);
    }

    #[test]
    fn init_from_params_rejects_wrong_shape() {
        let cfg = small_config();
        let dev = device();
        let mut seed = Seed::new(0, 0);
        let ok = cfg.init::<TestBackend>(&dev, &mut seed);
        // Reuse valid params but corrupt one shape.
        let bad_w_delta = Tensor::<TestBackend, 2>::zeros([2, 3], &dev);
        let params = DiscreteDeltaThetaGammaParams {
            delta_freq: ok.delta_freq.val(),
            theta_freq: ok.theta_freq.val(),
            gamma_freq: ok.gamma_freq.val(),
            w_delta: bad_w_delta,
            w_theta: ok.w_theta.val(),
            w_gamma: ok.w_gamma.val(),
            w_pac_dt: ok.w_pac_dt.val(),
            b_pac_dt: ok.b_pac_dt.val(),
            w_pac_tg: ok.w_pac_tg.val(),
            b_pac_tg: ok.b_pac_tg.val(),
            mu_delta: ok.mu_delta.val(),
            mu_theta: ok.mu_theta.val(),
            mu_gamma: ok.mu_gamma.val(),
        };
        let err = cfg.init_from_params(params).unwrap_err();
        assert!(matches!(
            err,
            TrainError::ShapeMismatch {
                name: "w_delta",
                ..
            }
        ));
    }

    // --- Forward / shape / dtype ---

    #[test]
    fn step_preserves_shape_and_is_finite() {
        let net = seeded_net::<TestBackend>(&device());
        let dev = device();
        let phase = Tensor::<TestBackend, 2>::zeros([3, 9], &dev);
        let amp = Tensor::<TestBackend, 2>::ones([3, 9], &dev);
        let state = DiscreteBandState::new(phase, amp).unwrap();
        let next = net.step(state, 0.01).unwrap();
        assert_eq!(next.phase().dims(), [3, 9]);
        assert_eq!(next.amplitude().dims(), [3, 9]);
        let p = next.phase().clone().to_data().to_vec::<f64>().unwrap();
        let a = next.amplitude().clone().to_data().to_vec::<f64>().unwrap();
        assert!(p.iter().all(|v| v.is_finite()));
        assert!(a.iter().all(|v| v.is_finite()));
    }

    #[test]
    fn phase_output_wrapped_to_0_2pi() {
        let net = seeded_net::<TestBackend>(&device());
        let dev = device();
        // Start near the wrap boundary so at least one oscillator wraps.
        let phase = Tensor::<TestBackend, 2>::full([1, 9], std::f64::consts::TAU - 0.001, &dev);
        let amp = Tensor::<TestBackend, 2>::ones([1, 9], &dev);
        let state = DiscreteBandState::new(phase, amp).unwrap();
        let next = net.step(state, 0.5).unwrap();
        let p = next.phase().clone().to_data().to_vec::<f64>().unwrap();
        for v in p {
            assert!(
                (0.0..std::f64::consts::TAU).contains(&v),
                "phase {v} not wrapped"
            );
        }
    }

    #[test]
    fn amplitude_output_clamped_to_valid_range() {
        let net = seeded_net::<TestBackend>(&device());
        let dev = device();
        let phase = Tensor::<TestBackend, 2>::zeros([1, 9], &dev);
        // Extreme amplitude to stress the clamp.
        let amp = Tensor::<TestBackend, 2>::full([1, 9], 1e6, &dev);
        let state = DiscreteBandState::new(phase, amp).unwrap();
        let next = net.step(state, 0.01).unwrap();
        let a = next.amplitude().clone().to_data().to_vec::<f64>().unwrap();
        for v in a {
            assert!(
                (1e-6..=10.0).contains(&v),
                "amplitude {v} out of clamp range"
            );
        }
    }

    #[test]
    fn integrate_matches_repeated_step() {
        let net = seeded_net::<TestBackend>(&device());
        let dev = device();
        let mut seed = Seed::new(1, 0);
        let phase = seeded_uniform::<TestBackend, 2>([2, 9], 0.0, 6.0, &dev, &mut seed);
        let amp = Tensor::<TestBackend, 2>::ones([2, 9], &dev);
        let state = DiscreteBandState::new(phase.clone(), amp.clone()).unwrap();

        let via_integrate = net
            .integrate(
                DiscreteBandState::new(phase.clone(), amp.clone()).unwrap(),
                3,
                0.01,
            )
            .unwrap();

        let mut manual = state;
        for _ in 0..3 {
            manual = net.step(manual, 0.01).unwrap();
        }

        let a = via_integrate
            .phase()
            .clone()
            .to_data()
            .to_vec::<f64>()
            .unwrap();
        let b = manual.phase().clone().to_data().to_vec::<f64>().unwrap();
        assert_eq!(a, b);
    }

    // --- Numerical / shape guards ---

    #[cfg(feature = "strict-checks")]
    #[test]
    fn step_rejects_non_finite_input_under_strict_checks() {
        let net = seeded_net::<TestBackend>(&device());
        let dev = device();
        let phase = Tensor::<TestBackend, 2>::full([1, 9], f64::NAN, &dev);
        let amp = Tensor::<TestBackend, 2>::ones([1, 9], &dev);
        let state = DiscreteBandState::new(phase, amp).unwrap();
        let err = net.step(state, 0.01).unwrap_err();
        assert!(matches!(err, TrainError::NonFiniteState { name: "phase" }));
    }

    #[test]
    fn step_rejects_wrong_width() {
        let net = seeded_net::<TestBackend>(&device());
        let dev = device();
        let phase = Tensor::<TestBackend, 2>::zeros([1, 5], &dev);
        let amp = Tensor::<TestBackend, 2>::ones([1, 5], &dev);
        let state = DiscreteBandState::new(phase, amp).unwrap();
        let err = net.step(state, 0.01).unwrap_err();
        assert!(matches!(
            err,
            TrainError::ShapeMismatch { name: "phase", .. }
        ));
    }

    #[test]
    fn state_rejects_mismatched_phase_amplitude_shape() {
        let dev = device();
        let phase = Tensor::<TestBackend, 2>::zeros([1, 9], &dev);
        let amp = Tensor::<TestBackend, 2>::ones([1, 5], &dev);
        let err = DiscreteBandState::new(phase, amp).unwrap_err();
        assert!(matches!(
            err,
            TrainError::ShapeMismatch {
                name: "amplitude",
                ..
            }
        ));
    }

    #[test]
    fn step_rejects_invalid_dt() {
        let net = seeded_net::<TestBackend>(&device());
        let dev = device();
        let phase = Tensor::<TestBackend, 2>::zeros([1, 9], &dev);
        let amp = Tensor::<TestBackend, 2>::ones([1, 9], &dev);
        for bad in [0.0, -0.01, f64::NAN, f64::INFINITY] {
            let state = DiscreteBandState::new(phase.clone(), amp.clone()).unwrap();
            let err = net.step(state, bad).unwrap_err();
            assert!(matches!(err, TrainError::InvalidTimestep { .. }));
        }
    }

    // --- Gradient reference tests ---

    #[test]
    fn gradients_flow_to_every_parameter() {
        let dev: <TestAutodiffBackend as Backend>::Device = Default::default();
        let mut seed = Seed::new(42, 0);
        let net = small_config().init::<TestAutodiffBackend>(&dev, &mut seed);

        // Distinct per-oscillator phase/amplitude: with every oscillator in a
        // band starting identical (same phase, same amplitude, same
        // per-band frequency), intra-band synchrony is preserved exactly at
        // every step (sin(0) = 0 throughout), making the coupling-matrix
        // Jacobian structurally zero — not a bug, but the wrong fixture for
        // "every parameter gets a gradient".
        let mut init_seed = Seed::new(1, 0);
        let phase = seeded_uniform::<TestAutodiffBackend, 2>(
            [2, 9],
            0.0,
            std::f64::consts::TAU,
            &dev,
            &mut init_seed,
        )
        .require_grad();
        let amp = seeded_uniform::<TestAutodiffBackend, 2>([2, 9], 0.5, 1.5, &dev, &mut init_seed)
            .require_grad();
        let state = DiscreteBandState::new(phase, amp).unwrap();

        let out = net.integrate(state, 3, 0.01).unwrap();
        // `w_gamma` only shapes gamma's own phase trajectory: gamma is the
        // fastest band, so nothing downstream reads its phase back into an
        // amplitude, and an amplitude-only loss would give it a structurally
        // (correctly) zero gradient. Sum both outputs of the state contract
        // so every parameter this module exposes is exercised.
        let loss = out.amplitude().clone().sum_dim(1).sum_dim(0)
            + out.phase().clone().sum_dim(1).sum_dim(0);
        let grads = loss.backward();

        let grad_w_delta = net.w_delta.val().grad(&grads);
        let grad_w_gamma = net.w_gamma.val().grad(&grads);
        let grad_mu_theta = net.mu_theta.val().grad(&grads);
        let grad_b_pac_tg = net.b_pac_tg.val().grad(&grads);

        for grad in [
            grad_w_delta.map(|g| g.to_data().to_vec::<f64>().unwrap()),
            grad_w_gamma.map(|g| g.to_data().to_vec::<f64>().unwrap()),
            grad_mu_theta.map(|g| g.to_data().to_vec::<f64>().unwrap()),
            grad_b_pac_tg.map(|g| g.to_data().to_vec::<f64>().unwrap()),
        ] {
            let values = grad.expect("gradient must be present for every trainable parameter");
            assert!(!values.is_empty());
            assert!(
                values.iter().any(|v| v.abs() > 0.0),
                "gradient is identically zero"
            );
            assert!(values.iter().all(|v| v.is_finite()));
        }
    }

    #[test]
    fn gradient_matches_central_finite_difference() {
        // Gradcheck-style reference test (Testing Standards §2): compare the
        // autodiff gradient of a scalar loss w.r.t. a single coupling entry
        // against a central finite difference at float64 precision.
        let dev: <TestAutodiffBackend as Backend>::Device = Default::default();
        let cfg = DiscreteDeltaThetaGammaConfig::new(2, 2, 2).unwrap();

        let loss_for = |w_delta_00: f64| -> f64 {
            let mut s = Seed::new(99, 0);
            let net = cfg.init::<TestBackend>(&Default::default(), &mut s);
            let mut w = net.w_delta.val().to_data().to_vec::<f64>().unwrap();
            w[0] = w_delta_00;
            let w_delta = Tensor::<TestBackend, 2>::from_data(
                burn::tensor::TensorData::new(w, vec![2, 2]),
                &Default::default(),
            );
            let params = DiscreteDeltaThetaGammaParams {
                delta_freq: net.delta_freq.val(),
                theta_freq: net.theta_freq.val(),
                gamma_freq: net.gamma_freq.val(),
                w_delta,
                w_theta: net.w_theta.val(),
                w_gamma: net.w_gamma.val(),
                w_pac_dt: net.w_pac_dt.val(),
                b_pac_dt: net.b_pac_dt.val(),
                w_pac_tg: net.w_pac_tg.val(),
                b_pac_tg: net.b_pac_tg.val(),
                mu_delta: net.mu_delta.val(),
                mu_theta: net.mu_theta.val(),
                mu_gamma: net.mu_gamma.val(),
            };
            let net = cfg.init_from_params(params).unwrap();
            let dev: <TestBackend as Backend>::Device = Default::default();
            let phase = Tensor::<TestBackend, 2>::zeros([1, 6], &dev) + 0.3;
            let amp = Tensor::<TestBackend, 2>::ones([1, 6], &dev);
            let state = DiscreteBandState::new(phase, amp).unwrap();
            let out = net.step(state, 0.01).unwrap();
            out.amplitude()
                .clone()
                .to_data()
                .to_vec::<f64>()
                .unwrap()
                .iter()
                .sum()
        };

        let mut s = Seed::new(99, 0);
        let net0 = cfg.init::<TestAutodiffBackend>(&dev, &mut s);
        let w_delta0 = net0.w_delta.val().to_data().to_vec::<f64>().unwrap()[0];

        let eps = 1e-6;
        let numerical = (loss_for(w_delta0 + eps) - loss_for(w_delta0 - eps)) / (2.0 * eps);

        // Analytic gradient via autodiff on the same computation.
        let w_delta_grad_tensor = net0.w_delta.val().require_grad();
        let params = DiscreteDeltaThetaGammaParams {
            delta_freq: net0.delta_freq.val(),
            theta_freq: net0.theta_freq.val(),
            gamma_freq: net0.gamma_freq.val(),
            w_delta: w_delta_grad_tensor.clone(),
            w_theta: net0.w_theta.val(),
            w_gamma: net0.w_gamma.val(),
            w_pac_dt: net0.w_pac_dt.val(),
            b_pac_dt: net0.b_pac_dt.val(),
            w_pac_tg: net0.w_pac_tg.val(),
            b_pac_tg: net0.b_pac_tg.val(),
            mu_delta: net0.mu_delta.val(),
            mu_theta: net0.mu_theta.val(),
            mu_gamma: net0.mu_gamma.val(),
        };
        let net_ad = cfg.init_from_params(params).unwrap();
        let phase = Tensor::<TestAutodiffBackend, 2>::zeros([1, 6], &dev) + 0.3;
        let amp = Tensor::<TestAutodiffBackend, 2>::ones([1, 6], &dev);
        let state = DiscreteBandState::new(phase, amp).unwrap();
        let out = net_ad.step(state, 0.01).unwrap();
        let loss = out.amplitude().clone().sum_dim(1).sum_dim(0);
        let grads = loss.backward();
        let analytic = w_delta_grad_tensor
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

    // --- Serialization ---

    #[test]
    fn record_roundtrip_preserves_parameters() {
        use burn::record::{BinBytesRecorder, DoublePrecisionSettings, Recorder};

        let dev = device();
        let net = seeded_net::<TestBackend>(&dev);
        let before = net.w_pac_dt.val().to_data().to_vec::<f64>().unwrap();

        let recorder = BinBytesRecorder::<DoublePrecisionSettings>::default();
        let bytes =
            Recorder::<TestBackend>::record(&recorder, net.clone().into_record(), ()).unwrap();
        let record = Recorder::<TestBackend>::load(&recorder, bytes, &dev).unwrap();
        let restored = net.load_record(record);

        let after = restored.w_pac_dt.val().to_data().to_vec::<f64>().unwrap();
        assert_eq!(before, after);
        assert_eq!(restored.n_delta(), 2);
        assert_eq!(restored.n_theta(), 3);
        assert_eq!(restored.n_gamma(), 4);
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
        fn step_output_always_finite_and_in_range(
            nd in 1usize..=3,
            nt in 1usize..=3,
            ng in 1usize..=3,
            seed_val in 0u64..1000,
            phase_seed in 0u64..1000,
        ) {
            let cfg = DiscreteDeltaThetaGammaConfig::new(nd, nt, ng).unwrap();
            let dev = Default::default();
            let mut seed = Seed::new(seed_val as u128, 0);
            let net = cfg.init::<TestBackend>(&dev, &mut seed);

            let mut pseed = Seed::new(phase_seed as u128, 1);
            let n_total = cfg.n_total();
            let phase = seeded_uniform::<TestBackend, 2>([2, n_total], 0.0, std::f64::consts::TAU, &dev, &mut pseed);
            let amp = seeded_uniform::<TestBackend, 2>([2, n_total], 0.5, 2.0, &dev, &mut pseed);
            let state = DiscreteBandState::new(phase, amp).unwrap();

            let next = net.step(state, 0.01).unwrap();
            let p = next.phase().clone().to_data().to_vec::<f64>().unwrap();
            let a = next.amplitude().clone().to_data().to_vec::<f64>().unwrap();

            for v in &p {
                prop_assert!(v.is_finite());
                prop_assert!((0.0..std::f64::consts::TAU).contains(v));
            }
            for v in &a {
                prop_assert!(v.is_finite());
                prop_assert!((1e-6..=10.0).contains(v));
            }
        }
    }
}
