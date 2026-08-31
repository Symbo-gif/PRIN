//! Trainable hierarchical oscillator, PAC, and discrete-network layers.
//!
//! This module owns the Burn-autodiff implementations behind PRINet 3.0's
//! `HierarchicalResonanceLayer`, `PhaseAmplitudeCouplingLayer`, and
//! `DiscreteDeltaThetaGammaLayer`. The continuous layer keeps the reference
//! stepping order: one delta RK4 step, delta→theta PAC, three theta RK4
//! sub-steps, theta→gamma PAC, and twenty gamma RK4 sub-steps per outer step.
//! Every oscillator calculation is batched over `[batch, n]`; sparse phase-kNN
//! neighbour selection is tensorized and never loops over samples.

use burn::module::{Module, Param};
use burn::nn::Linear;
use burn::tensor::backend::Backend;
use burn::tensor::{Int, Tensor, TensorData};
use prin_dynamics::Seed;

use crate::bands::{
    DiscreteBandState, DiscreteDeltaThetaGamma, DiscreteDeltaThetaGammaConfig,
    DiscreteDeltaThetaGammaParams,
};
use crate::error::TrainError;
use crate::support::{
    check_dims, check_finite, seeded_uniform, validate_dt, validate_finite, wrap_floor,
    xavier_bound,
};

const AMPLITUDE_MIN: f64 = 1e-6;
const AMPLITUDE_MAX: f64 = 10.0;
const DECAY_RATE: f64 = 0.1;
const FREQ_ADAPTATION_RATE: f64 = 0.01;
const DELTA_FREQUENCY: f64 = 2.0;
const THETA_FREQUENCY: f64 = 6.0;
const GAMMA_FREQUENCY: f64 = 40.0;

/// Explicit PyTorch-layout projection weights for a bias-free linear layer.
pub struct ProjectionWeights<B: Backend> {
    /// Weight tensor with shape `[out_features, in_features]`.
    pub weight: Tensor<B, 2>,
}

impl<B: Backend> ProjectionWeights<B> {
    fn validate(
        &self,
        name: &'static str,
        out_features: usize,
        in_features: usize,
    ) -> Result<(), TrainError> {
        check_dims(name, self.weight.dims(), [out_features, in_features])
    }

    fn into_linear(self) -> Linear<B> {
        let device = self.weight.device();
        let weight = Tensor::from_data(self.weight.transpose().into_data(), &device).require_grad();
        Linear {
            weight: Param::initialized(Default::default(), weight),
            bias: None,
        }
    }
}

fn seeded_projection<B: Backend>(
    d_input: usize,
    d_output: usize,
    device: &B::Device,
    seed: &mut Seed,
) -> Linear<B> {
    let bound = xavier_bound(d_input, d_output, 0.5);
    let weight =
        seeded_uniform::<B, 2>([d_input, d_output], -bound, bound, device, seed).require_grad();
    Linear {
        weight: Param::initialized(Default::default(), weight),
        bias: None,
    }
}

/// Mean-slow-phase PAC modulation with a tensor-valued learnable depth.
///
/// `slow_phase` and `fast_amplitude` are batched tensors. The slow-band mean
/// is reduced independently for each batch row, then broadcast over the fast
/// width. The output clamp matches PRINet's `[1e-6, 10]` amplitude guard.
pub fn phase_amplitude_coupling<B: Backend>(
    slow_phase: Tensor<B, 2>,
    fast_amplitude: Tensor<B, 2>,
    depth: Tensor<B, 1>,
) -> Result<Tensor<B, 2>, TrainError> {
    let [batch, n_slow] = slow_phase.dims();
    let [amp_batch, n_fast] = fast_amplitude.dims();
    check_dims("fast_amplitude", [amp_batch, n_fast], [batch, n_fast])?;
    check_dims("modulation_depth", depth.dims(), [1])?;
    if n_slow == 0 {
        return Err(TrainError::EmptyBand { name: "slow" });
    }
    if n_fast == 0 {
        return Err(TrainError::EmptyBand { name: "fast" });
    }
    let mean = slow_phase.mean_dim(1);
    let factor = mean.cos() * depth.clamp(0.0, 1.0).reshape([1, 1]) + 1.0;
    Ok((fast_amplitude * factor).clamp(AMPLITUDE_MIN, AMPLITUDE_MAX))
}

/// Validated configuration for [`PhaseAmplitudeCouplingLayer`].
#[derive(Clone, Debug, PartialEq)]
pub struct PhaseAmplitudeCouplingLayerConfig {
    /// Initial modulation depth.
    pub initial_depth: f64,
}

impl PhaseAmplitudeCouplingLayerConfig {
    /// Construct with PRINet 3.0's default depth (`0.3`).
    pub fn new() -> Self {
        Self { initial_depth: 0.3 }
    }

    /// Construct with an explicit initial depth.
    ///
    /// # Errors
    ///
    /// Returns [`TrainError::InvalidRatio`] unless the depth is finite and in
    /// `[0, 1]`.
    pub fn with_depth(initial_depth: f64) -> Result<Self, TrainError> {
        validate_finite("initial_depth", initial_depth)?;
        if !(0.0..=1.0).contains(&initial_depth) {
            return Err(TrainError::InvalidRatio {
                name: "initial_depth",
                value: initial_depth,
            });
        }
        Ok(Self { initial_depth })
    }

    /// Initialize the trainable PAC layer.
    pub fn init<B: Backend>(&self, device: &B::Device) -> PhaseAmplitudeCouplingLayer<B> {
        let depth = Tensor::from_data(TensorData::new(vec![self.initial_depth], vec![1]), device)
            .require_grad();
        PhaseAmplitudeCouplingLayer {
            modulation_depth: Param::initialized(Default::default(), depth),
        }
    }

    /// Initialize from an explicit shape-`[1]` depth tensor.
    ///
    /// # Errors
    ///
    /// Returns [`TrainError::ShapeMismatch`] for any other shape.
    pub fn init_from_params<B: Backend>(
        &self,
        depth: Tensor<B, 1>,
    ) -> Result<PhaseAmplitudeCouplingLayer<B>, TrainError> {
        check_dims("modulation_depth", depth.dims(), [1])?;
        Ok(PhaseAmplitudeCouplingLayer {
            modulation_depth: Param::initialized(Default::default(), depth.require_grad()),
        })
    }
}

impl Default for PhaseAmplitudeCouplingLayerConfig {
    fn default() -> Self {
        Self::new()
    }
}

/// Trainable mean-slow-phase PAC layer.
#[derive(Module, Debug)]
pub struct PhaseAmplitudeCouplingLayer<B: Backend> {
    modulation_depth: Param<Tensor<B, 1>>,
}

impl<B: Backend> PhaseAmplitudeCouplingLayer<B> {
    /// Apply PAC to matching batch dimensions.
    ///
    /// # Errors
    ///
    /// Returns a typed shape or empty-band error for invalid inputs.
    pub fn forward(
        &self,
        slow_phase: Tensor<B, 2>,
        fast_amplitude: Tensor<B, 2>,
    ) -> Result<Tensor<B, 2>, TrainError> {
        phase_amplitude_coupling(slow_phase, fast_amplitude, self.modulation_depth.val())
    }

    /// Validate checkpoint parameter shape.
    ///
    /// # Errors
    ///
    /// Returns [`TrainError::ShapeMismatch`] for an incompatible record.
    pub fn validate_shapes(&self) -> Result<(), TrainError> {
        check_dims("modulation_depth", self.modulation_depth.val().dims(), [1])
    }
}

#[derive(Clone)]
struct ContinuousBandState<B: Backend> {
    phase: Tensor<B, 2>,
    amplitude: Tensor<B, 2>,
    frequency: Tensor<B, 2>,
}

fn automatic_sparse_k(n: usize) -> usize {
    if n <= 1 {
        0
    } else {
        (n.ilog2() as usize + usize::from(!n.is_power_of_two())).clamp(1, n - 1)
    }
}

fn sparse_neighbor_indices<B: Backend>(phase: Tensor<B, 2>, k: usize) -> Tensor<B, 3, Int> {
    let [batch, n] = phase.dims();
    let device = phase.device();
    let sort_idx = phase.argsort(1);
    let positions = Tensor::<B, 1, Int>::arange(0..n as i64, &device)
        .unsqueeze::<2>()
        .repeat_dim(0, batch);
    let inverse =
        Tensor::<B, 2, Int>::zeros([batch, n], &device).scatter(1, sort_idx.clone(), positions);
    let half = k / 2;
    let mut offsets = Vec::with_capacity(k);
    for offset in (1..=half).rev() {
        offsets.push(n as i64 - offset as i64);
    }
    for offset in 1..=(k - half) {
        offsets.push(offset as i64);
    }
    let offsets = Tensor::<B, 1, Int>::from_data(TensorData::new(offsets, vec![k]), &device)
        .reshape([1, 1, k])
        .repeat_dim(0, batch)
        .repeat_dim(1, n);
    let sorted_positions = (inverse.unsqueeze_dim::<3>(2) + offsets).remainder_scalar(n as i64);
    sort_idx
        .gather(1, sorted_positions.reshape([batch, n * k]))
        .reshape([batch, n, k])
}

fn sparse_derivatives<B: Backend>(
    state: &ContinuousBandState<B>,
    coupling_strength: f64,
    sparse_k: usize,
) -> (Tensor<B, 2>, Tensor<B, 2>, Tensor<B, 2>) {
    let [batch, n] = state.phase.dims();
    if n == 1 {
        return (
            state.frequency.clone(),
            state.amplitude.clone().mul_scalar(-DECAY_RATE),
            Tensor::zeros([batch, 1], &state.phase.device()),
        );
    }
    let k = sparse_k.min(n - 1).max(1);
    let neighbor_idx = sparse_neighbor_indices(state.phase.clone(), k);
    let flat_idx = neighbor_idx.reshape([batch, n * k]);
    let neighbor_phase = state
        .phase
        .clone()
        .gather(1, flat_idx.clone())
        .reshape([batch, n, k]);
    let neighbor_amplitude = state
        .amplitude
        .clone()
        .gather(1, flat_idx)
        .reshape([batch, n, k]);
    let phase_diff = neighbor_phase - state.phase.clone().unsqueeze_dim::<3>(2);
    let scale = coupling_strength / k as f64;
    let weighted_sin = phase_diff.clone().sin().mul_scalar(scale) * neighbor_amplitude.clone();
    let weighted_cos = phase_diff.cos().mul_scalar(scale) * neighbor_amplitude;
    let sin_sum = weighted_sin.sum_dim(2).squeeze::<2>(2);
    let cos_sum = weighted_cos.sum_dim(2).squeeze::<2>(2);
    let dphase = (state.frequency.clone() + sin_sum.clone()).clamp(-1e4, 1e4);
    let damplitude = (state.amplitude.clone().mul_scalar(-DECAY_RATE) + cos_sum).clamp(-1e4, 1e4);
    let dfrequency = sin_sum
        .mul_scalar(FREQ_ADAPTATION_RATE / k as f64)
        .clamp(-1e4, 1e4);
    (dphase, damplitude, dfrequency)
}

fn intermediate_state<B: Backend>(
    state: &ContinuousBandState<B>,
    derivative: (Tensor<B, 2>, Tensor<B, 2>, Tensor<B, 2>),
    scale: f64,
) -> ContinuousBandState<B> {
    ContinuousBandState {
        phase: state.phase.clone() + derivative.0.mul_scalar(scale),
        amplitude: (state.amplitude.clone() + derivative.1.mul_scalar(scale)).clamp_min(0.0),
        frequency: state.frequency.clone() + derivative.2.mul_scalar(scale),
    }
}

fn rk4_step<B: Backend>(
    state: ContinuousBandState<B>,
    dt: f64,
    coupling_strength: f64,
    sparse_k: usize,
) -> ContinuousBandState<B> {
    let k1 = sparse_derivatives(&state, coupling_strength, sparse_k);
    let s2 = intermediate_state(&state, k1.clone(), 0.5 * dt);
    let k2 = sparse_derivatives(&s2, coupling_strength, sparse_k);
    let s3 = intermediate_state(&state, k2.clone(), 0.5 * dt);
    let k3 = sparse_derivatives(&s3, coupling_strength, sparse_k);
    let s4 = intermediate_state(&state, k3.clone(), dt);
    let k4 = sparse_derivatives(&s4, coupling_strength, sparse_k);
    let combine = |a: Tensor<B, 2>, b: Tensor<B, 2>, c: Tensor<B, 2>, d: Tensor<B, 2>| {
        (a + b.mul_scalar(2.0) + c.mul_scalar(2.0) + d).mul_scalar(dt / 6.0)
    };
    ContinuousBandState {
        phase: wrap_floor(
            state.phase + combine(k1.0, k2.0, k3.0, k4.0),
            std::f64::consts::TAU,
        ),
        amplitude: (state.amplitude + combine(k1.1, k2.1, k3.1, k4.1)).clamp_min(0.0),
        frequency: state.frequency + combine(k1.2, k2.2, k3.2, k4.2),
    }
}

fn sub_steps<B: Backend>(
    mut state: ContinuousBandState<B>,
    count: usize,
    dt: f64,
    coupling_strength: f64,
    sparse_k: usize,
) -> ContinuousBandState<B> {
    let inner_dt = dt / count as f64;
    for _ in 0..count {
        state = rk4_step(state, inner_dt, coupling_strength, sparse_k);
    }
    state
}

/// Explicit parameters for [`HierarchicalResonanceLayer`].
pub struct HierarchicalResonanceLayerParams<B: Backend> {
    /// Delta projection in PyTorch layout `[n_delta, n_dims]`.
    pub proj_delta: ProjectionWeights<B>,
    /// Theta projection in PyTorch layout `[n_theta, n_dims]`.
    pub proj_theta: ProjectionWeights<B>,
    /// Gamma projection in PyTorch layout `[n_gamma, n_dims]`.
    pub proj_gamma: ProjectionWeights<B>,
    /// Delta→theta PAC depth, shape `[1]`.
    pub pac_depth_dt: Tensor<B, 1>,
    /// Theta→gamma PAC depth, shape `[1]`.
    pub pac_depth_tg: Tensor<B, 1>,
}

/// Validated configuration for [`HierarchicalResonanceLayer`].
#[derive(Clone, Debug, PartialEq)]
pub struct HierarchicalResonanceLayerConfig {
    /// Delta oscillator count.
    pub n_delta: usize,
    /// Theta oscillator count.
    pub n_theta: usize,
    /// Gamma oscillator count.
    pub n_gamma: usize,
    /// Input feature width.
    pub n_dims: usize,
    /// Outer integration step count.
    pub n_steps: usize,
    /// Outer integration timestep.
    pub dt: f64,
    /// Intra-band sparse Kuramoto coupling strength.
    pub coupling_strength: f64,
    /// Initial depth for both PAC links.
    pub pac_depth: f64,
    /// Optional common sparse neighbour count; `None` uses `ceil(log2(n))` per band.
    pub sparse_k: Option<usize>,
}

impl HierarchicalResonanceLayerConfig {
    /// Construct with PRINet 3.0 defaults.
    ///
    /// # Errors
    ///
    /// Returns a typed validation error for zero dimensions.
    pub fn new(
        n_delta: usize,
        n_theta: usize,
        n_gamma: usize,
        n_dims: usize,
    ) -> Result<Self, TrainError> {
        Self::with_params(n_delta, n_theta, n_gamma, n_dims, 10, 0.01, 2.0, 0.3, None)
    }

    /// Construct with explicit hyperparameters.
    ///
    /// # Errors
    ///
    /// Returns a typed validation error for empty bands, zero input/step count,
    /// invalid timestep, non-finite coupling, PAC depth outside `[0, 1]`, or a
    /// zero sparse neighbour count.
    #[allow(clippy::too_many_arguments)]
    pub fn with_params(
        n_delta: usize,
        n_theta: usize,
        n_gamma: usize,
        n_dims: usize,
        n_steps: usize,
        dt: f64,
        coupling_strength: f64,
        pac_depth: f64,
        sparse_k: Option<usize>,
    ) -> Result<Self, TrainError> {
        for (name, value) in [("delta", n_delta), ("theta", n_theta), ("gamma", n_gamma)] {
            if value == 0 {
                return Err(TrainError::EmptyBand { name });
            }
        }
        if n_dims == 0 {
            return Err(TrainError::EmptyBand { name: "input" });
        }
        if n_steps == 0 {
            return Err(TrainError::InvalidStepCount {
                name: "n_steps",
                value: n_steps,
            });
        }
        validate_dt(dt)?;
        validate_finite("coupling_strength", coupling_strength)?;
        validate_finite("pac_depth", pac_depth)?;
        if !(0.0..=1.0).contains(&pac_depth) {
            return Err(TrainError::InvalidRatio {
                name: "pac_depth",
                value: pac_depth,
            });
        }
        if sparse_k == Some(0) {
            return Err(TrainError::InvalidTopK { k: 0 });
        }
        Ok(Self {
            n_delta,
            n_theta,
            n_gamma,
            n_dims,
            n_steps,
            dt,
            coupling_strength,
            pac_depth,
            sparse_k,
        })
    }

    /// Total oscillator width.
    pub fn n_total(&self) -> usize {
        self.n_delta + self.n_theta + self.n_gamma
    }

    /// Initialize all Rust-owned parameters from the project seed.
    pub fn init<B: Backend>(
        &self,
        device: &B::Device,
        seed: &mut Seed,
    ) -> HierarchicalResonanceLayer<B> {
        let depth = || {
            Tensor::from_data(TensorData::new(vec![self.pac_depth], vec![1]), device).require_grad()
        };
        HierarchicalResonanceLayer {
            proj_delta: seeded_projection(self.n_dims, self.n_delta, device, seed),
            proj_theta: seeded_projection(self.n_dims, self.n_theta, device, seed),
            proj_gamma: seeded_projection(self.n_dims, self.n_gamma, device, seed),
            pac_depth_dt: Param::initialized(Default::default(), depth()),
            pac_depth_tg: Param::initialized(Default::default(), depth()),
            n_delta: self.n_delta,
            n_theta: self.n_theta,
            n_gamma: self.n_gamma,
            n_dims: self.n_dims,
            n_steps: self.n_steps,
            dt: self.dt,
            coupling_strength: self.coupling_strength,
            sparse_k: self.sparse_k,
        }
    }

    /// Initialize from explicit reference projection weights and PAC depths.
    ///
    /// # Errors
    ///
    /// Returns [`TrainError::ShapeMismatch`] for an incompatible tensor.
    pub fn init_from_params<B: Backend>(
        &self,
        params: HierarchicalResonanceLayerParams<B>,
    ) -> Result<HierarchicalResonanceLayer<B>, TrainError> {
        params
            .proj_delta
            .validate("proj_delta", self.n_delta, self.n_dims)?;
        params
            .proj_theta
            .validate("proj_theta", self.n_theta, self.n_dims)?;
        params
            .proj_gamma
            .validate("proj_gamma", self.n_gamma, self.n_dims)?;
        check_dims("pac_depth_dt", params.pac_depth_dt.dims(), [1])?;
        check_dims("pac_depth_tg", params.pac_depth_tg.dims(), [1])?;
        Ok(HierarchicalResonanceLayer {
            proj_delta: params.proj_delta.into_linear(),
            proj_theta: params.proj_theta.into_linear(),
            proj_gamma: params.proj_gamma.into_linear(),
            pac_depth_dt: Param::initialized(
                Default::default(),
                params.pac_depth_dt.require_grad(),
            ),
            pac_depth_tg: Param::initialized(
                Default::default(),
                params.pac_depth_tg.require_grad(),
            ),
            n_delta: self.n_delta,
            n_theta: self.n_theta,
            n_gamma: self.n_gamma,
            n_dims: self.n_dims,
            n_steps: self.n_steps,
            dt: self.dt,
            coupling_strength: self.coupling_strength,
            sparse_k: self.sparse_k,
        })
    }
}

/// Fully batched continuous delta/theta/gamma resonance layer.
#[derive(Module, Debug)]
pub struct HierarchicalResonanceLayer<B: Backend> {
    proj_delta: Linear<B>,
    proj_theta: Linear<B>,
    proj_gamma: Linear<B>,
    pac_depth_dt: Param<Tensor<B, 1>>,
    pac_depth_tg: Param<Tensor<B, 1>>,
    n_delta: usize,
    n_theta: usize,
    n_gamma: usize,
    n_dims: usize,
    n_steps: usize,
    dt: f64,
    coupling_strength: f64,
    sparse_k: Option<usize>,
}

impl<B: Backend> HierarchicalResonanceLayer<B> {
    /// Total oscillator width.
    pub fn n_total(&self) -> usize {
        self.n_delta + self.n_theta + self.n_gamma
    }

    /// Input feature width.
    pub fn n_dims(&self) -> usize {
        self.n_dims
    }

    /// Run all continuous hierarchical integration steps.
    ///
    /// Returns `(amplitude, wrapped_phase)` with both tensors shaped
    /// `[batch, n_total]`; wrappers may omit the phase result for the default
    /// PRINet-compatible path.
    ///
    /// # Errors
    ///
    /// Returns [`TrainError::ShapeMismatch`] unless `x` has width `n_dims`.
    pub fn forward(&self, x: Tensor<B, 2>) -> Result<(Tensor<B, 2>, Tensor<B, 2>), TrainError> {
        let batch = x.dims()[0];
        check_dims("x", x.dims(), [batch, self.n_dims])?;
        let initialize = |projection: &Linear<B>, n: usize, frequency: f64| {
            let projected = projection.forward(x.clone());
            ContinuousBandState {
                phase: wrap_floor(projected.clone(), std::f64::consts::TAU),
                amplitude: projected.abs().clamp_min(AMPLITUDE_MIN),
                frequency: Tensor::ones([batch, n], &x.device()).mul_scalar(frequency),
            }
        };
        let mut delta = initialize(&self.proj_delta, self.n_delta, DELTA_FREQUENCY);
        let mut theta = initialize(&self.proj_theta, self.n_theta, THETA_FREQUENCY);
        let mut gamma = initialize(&self.proj_gamma, self.n_gamma, GAMMA_FREQUENCY);
        let kd = self
            .sparse_k
            .unwrap_or_else(|| automatic_sparse_k(self.n_delta));
        let kt = self
            .sparse_k
            .unwrap_or_else(|| automatic_sparse_k(self.n_theta));
        let kg = self
            .sparse_k
            .unwrap_or_else(|| automatic_sparse_k(self.n_gamma));

        for _ in 0..self.n_steps {
            delta = rk4_step(delta, self.dt, self.coupling_strength, kd);
            theta.amplitude = phase_amplitude_coupling(
                delta.phase.clone(),
                theta.amplitude,
                self.pac_depth_dt.val(),
            )?;
            theta = sub_steps(theta, 3, self.dt, self.coupling_strength, kt);
            gamma.amplitude = phase_amplitude_coupling(
                theta.phase.clone(),
                gamma.amplitude,
                self.pac_depth_tg.val(),
            )?;
            gamma = sub_steps(gamma, 20, self.dt, self.coupling_strength, kg);
        }
        let amplitude = Tensor::cat(vec![delta.amplitude, theta.amplitude, gamma.amplitude], 1);
        let phase = wrap_floor(
            Tensor::cat(vec![delta.phase, theta.phase, gamma.phase], 1),
            std::f64::consts::TAU,
        );
        check_finite("amplitude", &amplitude)?;
        check_finite("phase", &phase)?;
        Ok((amplitude, phase))
    }

    /// Validate all parameter shapes after checkpoint loading.
    ///
    /// # Errors
    ///
    /// Returns [`TrainError::ShapeMismatch`] for an incompatible record.
    pub fn validate_shapes(&self) -> Result<(), TrainError> {
        check_dims(
            "proj_delta",
            self.proj_delta.weight.val().dims(),
            [self.n_dims, self.n_delta],
        )?;
        check_dims(
            "proj_theta",
            self.proj_theta.weight.val().dims(),
            [self.n_dims, self.n_theta],
        )?;
        check_dims(
            "proj_gamma",
            self.proj_gamma.weight.val().dims(),
            [self.n_dims, self.n_gamma],
        )?;
        check_dims("pac_depth_dt", self.pac_depth_dt.val().dims(), [1])?;
        check_dims("pac_depth_tg", self.pac_depth_tg.val().dims(), [1])
    }
}

/// Explicit parameters for [`DiscreteDeltaThetaGammaLayer`].
pub struct DiscreteDeltaThetaGammaLayerParams<B: Backend> {
    /// Input-to-phase projection in PyTorch layout `[n_total, n_dims]`.
    pub proj_phase: ProjectionWeights<B>,
    /// Input-to-amplitude projection in PyTorch layout `[n_total, n_dims]`.
    pub proj_amplitude: ProjectionWeights<B>,
    /// Existing discrete dynamics parameters.
    pub dynamics: DiscreteDeltaThetaGammaParams<B>,
}

/// Validated configuration for [`DiscreteDeltaThetaGammaLayer`].
#[derive(Clone, Debug, PartialEq)]
pub struct DiscreteDeltaThetaGammaLayerConfig {
    /// Discrete dynamics configuration.
    pub dynamics: DiscreteDeltaThetaGammaConfig,
    /// Input feature width.
    pub n_dims: usize,
    /// Discrete macro-step count.
    pub n_steps: usize,
    /// Macro timestep.
    pub dt: f64,
}

impl DiscreteDeltaThetaGammaLayerConfig {
    /// Construct with PRINet 3.0 defaults.
    ///
    /// # Errors
    ///
    /// Returns a typed validation error for zero dimensions.
    pub fn new(
        n_delta: usize,
        n_theta: usize,
        n_gamma: usize,
        n_dims: usize,
    ) -> Result<Self, TrainError> {
        Self::with_params(n_delta, n_theta, n_gamma, n_dims, 10, 0.01, 2.0, 0.3)
    }

    /// Construct with explicit dynamics and integration parameters.
    ///
    /// # Errors
    ///
    /// Returns a typed validation error for invalid dimensions or scalars.
    #[allow(clippy::too_many_arguments)]
    pub fn with_params(
        n_delta: usize,
        n_theta: usize,
        n_gamma: usize,
        n_dims: usize,
        n_steps: usize,
        dt: f64,
        coupling_strength: f64,
        pac_depth: f64,
    ) -> Result<Self, TrainError> {
        if n_dims == 0 {
            return Err(TrainError::EmptyBand { name: "input" });
        }
        if n_steps == 0 {
            return Err(TrainError::InvalidStepCount {
                name: "n_steps",
                value: n_steps,
            });
        }
        validate_dt(dt)?;
        let dynamics = DiscreteDeltaThetaGammaConfig::with_params(
            n_delta,
            n_theta,
            n_gamma,
            coupling_strength,
            pac_depth,
            DELTA_FREQUENCY,
            THETA_FREQUENCY,
            GAMMA_FREQUENCY,
        )?;
        Ok(Self {
            dynamics,
            n_dims,
            n_steps,
            dt,
        })
    }

    /// Total oscillator width.
    pub fn n_total(&self) -> usize {
        self.dynamics.n_total()
    }

    /// Initialize projections and dynamics from the project seed.
    pub fn init<B: Backend>(
        &self,
        device: &B::Device,
        seed: &mut Seed,
    ) -> DiscreteDeltaThetaGammaLayer<B> {
        DiscreteDeltaThetaGammaLayer {
            proj_phase: seeded_projection(self.n_dims, self.n_total(), device, seed),
            proj_amplitude: seeded_projection(self.n_dims, self.n_total(), device, seed),
            dynamics: self.dynamics.init(device, seed),
            n_dims: self.n_dims,
            n_steps: self.n_steps,
            dt: self.dt,
        }
    }

    /// Initialize from explicit reference tensors.
    ///
    /// # Errors
    ///
    /// Returns a typed shape error for any incompatible tensor.
    pub fn init_from_params<B: Backend>(
        &self,
        params: DiscreteDeltaThetaGammaLayerParams<B>,
    ) -> Result<DiscreteDeltaThetaGammaLayer<B>, TrainError> {
        params
            .proj_phase
            .validate("proj_phase", self.n_total(), self.n_dims)?;
        params
            .proj_amplitude
            .validate("proj_amplitude", self.n_total(), self.n_dims)?;
        Ok(DiscreteDeltaThetaGammaLayer {
            proj_phase: params.proj_phase.into_linear(),
            proj_amplitude: params.proj_amplitude.into_linear(),
            dynamics: self.dynamics.init_from_params(params.dynamics)?,
            n_dims: self.n_dims,
            n_steps: self.n_steps,
            dt: self.dt,
        })
    }
}

/// Bias-free projections composed with the existing discrete three-band core.
#[derive(Module, Debug)]
pub struct DiscreteDeltaThetaGammaLayer<B: Backend> {
    proj_phase: Linear<B>,
    proj_amplitude: Linear<B>,
    dynamics: DiscreteDeltaThetaGamma<B>,
    n_dims: usize,
    n_steps: usize,
    dt: f64,
}

impl<B: Backend> DiscreteDeltaThetaGammaLayer<B> {
    /// Input feature width.
    pub fn n_dims(&self) -> usize {
        self.n_dims
    }

    /// Total oscillator width.
    pub fn n_total(&self) -> usize {
        self.dynamics.n_total()
    }

    /// Project input, integrate the discrete core, and return final amplitudes.
    ///
    /// # Errors
    ///
    /// Returns a typed input or state shape error.
    pub fn forward(&self, x: Tensor<B, 2>) -> Result<Tensor<B, 2>, TrainError> {
        let batch = x.dims()[0];
        check_dims("x", x.dims(), [batch, self.n_dims])?;
        let phase = wrap_floor(self.proj_phase.forward(x.clone()), std::f64::consts::TAU);
        let amplitude = self
            .proj_amplitude
            .forward(x)
            .abs()
            .clamp_min(AMPLITUDE_MIN);
        let state = DiscreteBandState::new(phase, amplitude)?;
        Ok(self
            .dynamics
            .integrate(state, self.n_steps, self.dt)?
            .into_parts()
            .1)
    }

    /// Validate projection and nested dynamics dimensions after checkpoint load.
    ///
    /// # Errors
    ///
    /// Returns [`TrainError::ShapeMismatch`] for an incompatible record.
    pub fn validate_shapes(&self) -> Result<(), TrainError> {
        let total = self.n_total();
        check_dims(
            "proj_phase",
            self.proj_phase.weight.val().dims(),
            [self.n_dims, total],
        )?;
        check_dims(
            "proj_amplitude",
            self.proj_amplitude.weight.val().dims(),
            [self.n_dims, total],
        )?;
        self.dynamics.validate_shapes()
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    use burn::backend::{Autodiff, NdArray};
    use burn::tensor::ElementConversion;

    type TestBackend = NdArray<f64>;
    type TestAutodiffBackend = Autodiff<TestBackend>;

    fn device() -> <TestBackend as Backend>::Device {
        Default::default()
    }

    fn tensor2<B: Backend>(values: Vec<f64>, rows: usize, cols: usize) -> Tensor<B, 2> {
        Tensor::from_data(
            TensorData::new(values, vec![rows, cols]),
            &Default::default(),
        )
    }

    #[test]
    fn pac_matches_reference_and_clamps() {
        let layer = PhaseAmplitudeCouplingLayerConfig::with_depth(0.5)
            .unwrap()
            .init::<TestBackend>(&device());
        let phase = tensor2(vec![0.0, 1.0, 2.0], 1, 3);
        let amplitude = tensor2(vec![1.0, 100.0], 1, 2);
        let out = layer.forward(phase, amplitude).unwrap().to_data();
        let values = out.to_vec::<f64>().unwrap();
        let factor = 1.0 + 0.5 * 1.0_f64.cos();
        assert!((values[0] - factor).abs() < 1e-12);
        assert_eq!(values[1], 10.0);
    }

    #[test]
    fn configs_reject_invalid_values_and_parameter_shapes() {
        assert!(HierarchicalResonanceLayerConfig::new(0, 2, 2, 3).is_err());
        assert!(
            HierarchicalResonanceLayerConfig::with_params(2, 2, 2, 3, 0, 0.01, 2.0, 0.3, None)
                .is_err()
        );
        assert!(PhaseAmplitudeCouplingLayerConfig::with_depth(1.1).is_err());
        assert!(DiscreteDeltaThetaGammaLayerConfig::new(2, 2, 2, 0).is_err());
        let bad = tensor2::<TestBackend>(vec![0.3, 0.4], 1, 2).reshape([2]);
        assert!(PhaseAmplitudeCouplingLayerConfig::new()
            .init_from_params(bad)
            .is_err());
    }

    #[test]
    fn sparse_neighbors_follow_reference_sorted_ring() {
        let phase = tensor2::<TestBackend>(vec![4.0, 0.0, 2.0, 1.0], 1, 4);
        let idx = sparse_neighbor_indices(phase, 2)
            .to_data()
            .to_vec::<i64>()
            .unwrap();
        assert_eq!(idx, vec![2, 1, 0, 3, 3, 0, 1, 2]);
    }

    #[test]
    fn hierarchical_is_batched_and_phase_wrapped() {
        let cfg =
            HierarchicalResonanceLayerConfig::with_params(2, 2, 2, 3, 1, 0.001, 0.2, 0.3, Some(1))
                .unwrap();
        let mut seed = Seed::new(4, 0);
        let layer = cfg.init::<TestBackend>(&device(), &mut seed);
        let x = tensor2(vec![0.2, -0.3, 0.5, -0.4, 0.1, 0.7], 2, 3);
        let (amp, phase) = layer.forward(x).unwrap();
        assert_eq!(amp.dims(), [2, 6]);
        let values = phase.to_data().to_vec::<f64>().unwrap();
        assert!(values
            .iter()
            .all(|v| (0.0..std::f64::consts::TAU).contains(v)));
    }

    #[test]
    fn hierarchical_batch_matches_concatenated_single_rows() {
        let cfg =
            HierarchicalResonanceLayerConfig::with_params(2, 2, 2, 3, 1, 0.001, 0.2, 0.3, Some(1))
                .unwrap();
        let mut seed = Seed::new(5, 0);
        let layer = cfg.init::<TestBackend>(&device(), &mut seed);
        let x = tensor2(vec![0.2, -0.3, 0.5, -0.4, 0.1, 0.7], 2, 3);
        let batched = layer.forward(x.clone()).unwrap();
        let first = layer.forward(x.clone().narrow(0, 0, 1)).unwrap();
        let second = layer.forward(x.narrow(0, 1, 1)).unwrap();
        let amp = Tensor::cat(vec![first.0, second.0], 0);
        let phase = Tensor::cat(vec![first.1, second.1], 0);
        assert!(batched.0.equal(amp).all().into_scalar().elem::<bool>());
        assert!(batched.1.equal(phase).all().into_scalar().elem::<bool>());
    }

    #[test]
    fn hierarchical_autodiff_reaches_input_projections_and_depths() {
        let _guard = crate::support::autodiff_test_guard();
        let cfg =
            HierarchicalResonanceLayerConfig::with_params(2, 2, 2, 3, 1, 0.001, 0.2, 0.3, Some(1))
                .unwrap();
        let mut seed = Seed::new(6, 0);
        let layer = cfg.init::<TestAutodiffBackend>(&Default::default(), &mut seed);
        let x = tensor2::<TestAutodiffBackend>(vec![0.2, -0.3, 0.5], 1, 3).require_grad();
        let (amp, phase) = layer.forward(x.clone()).unwrap();
        let grads = (amp.sum() + phase.sum()).backward();
        assert!(x.grad(&grads).is_some());
        assert!(layer.proj_delta.weight.grad(&grads).is_some());
        assert!(layer.proj_theta.weight.grad(&grads).is_some());
        assert!(layer.proj_gamma.weight.grad(&grads).is_some());
        assert!(layer.pac_depth_dt.grad(&grads).is_some());
        assert!(layer.pac_depth_tg.grad(&grads).is_some());
    }

    #[test]
    fn pac_autodiff_reaches_both_inputs_and_depth() {
        let _guard = crate::support::autodiff_test_guard();
        let layer = PhaseAmplitudeCouplingLayerConfig::with_depth(0.4)
            .unwrap()
            .init::<TestAutodiffBackend>(&Default::default());
        let phase = tensor2::<TestAutodiffBackend>(vec![0.2, 0.4], 1, 2).require_grad();
        let amp = tensor2::<TestAutodiffBackend>(vec![0.8, 1.2], 1, 2).require_grad();
        let out = layer.forward(phase.clone(), amp.clone()).unwrap();
        let grads = out.sum().backward();
        assert!(phase.grad(&grads).is_some());
        assert!(amp.grad(&grads).is_some());
        assert!(layer.modulation_depth.grad(&grads).is_some());
    }

    #[test]
    fn discrete_layer_runs_and_autodiff_reaches_input_and_projections() {
        let _guard = crate::support::autodiff_test_guard();
        let cfg = DiscreteDeltaThetaGammaLayerConfig::with_params(2, 2, 2, 3, 1, 0.001, 0.2, 0.3)
            .unwrap();
        let mut seed = Seed::new(8, 0);
        let layer = cfg.init::<TestAutodiffBackend>(&Default::default(), &mut seed);
        let x = tensor2::<TestAutodiffBackend>(vec![0.2, -0.3, 0.5], 1, 3).require_grad();
        let out = layer.forward(x.clone()).unwrap();
        assert_eq!(out.dims(), [1, 6]);
        let grads = out.sum().backward();
        assert!(x.grad(&grads).is_some());
        assert!(layer.proj_phase.weight.grad(&grads).is_some());
        assert!(layer.proj_amplitude.weight.grad(&grads).is_some());
    }

    #[test]
    fn n_one_continuous_band_is_supported() {
        let cfg =
            HierarchicalResonanceLayerConfig::with_params(1, 1, 1, 2, 1, 0.001, 0.2, 0.3, None)
                .unwrap();
        let mut seed = Seed::new(9, 0);
        let layer = cfg.init::<TestBackend>(&device(), &mut seed);
        let output = layer.forward(tensor2(vec![0.2, -0.3], 1, 2)).unwrap();
        assert_eq!(output.0.dims(), [1, 3]);
    }

    fn tensor1(values: Vec<f64>) -> Tensor<TestBackend, 1> {
        let len = values.len();
        Tensor::from_data(TensorData::new(values, vec![len]), &device())
    }

    fn projection(rows: usize, cols: usize, value: f64) -> ProjectionWeights<TestBackend> {
        ProjectionWeights {
            weight: tensor2(vec![value; rows * cols], rows, cols),
        }
    }

    fn dynamics_params(
        n_delta: usize,
        n_theta: usize,
        n_gamma: usize,
    ) -> DiscreteDeltaThetaGammaParams<TestBackend> {
        DiscreteDeltaThetaGammaParams {
            delta_freq: tensor1(vec![2.0; n_delta]),
            theta_freq: tensor1(vec![6.0; n_theta]),
            gamma_freq: tensor1(vec![40.0; n_gamma]),
            w_delta: tensor2(vec![0.0; n_delta * n_delta], n_delta, n_delta),
            w_theta: tensor2(vec![0.0; n_theta * n_theta], n_theta, n_theta),
            w_gamma: tensor2(vec![0.0; n_gamma * n_gamma], n_gamma, n_gamma),
            w_pac_dt: tensor2(vec![0.0; 2 * n_delta * n_theta], 2 * n_delta, n_theta),
            b_pac_dt: tensor1(vec![0.3; n_theta]),
            w_pac_tg: tensor2(vec![0.0; 2 * n_theta * n_gamma], 2 * n_theta, n_gamma),
            b_pac_tg: tensor1(vec![0.3; n_gamma]),
            mu_delta: tensor2(vec![1.0], 1, 1),
            mu_theta: tensor2(vec![1.0], 1, 1),
            mu_gamma: tensor2(vec![1.0], 1, 1),
        }
    }

    fn hierarchical_params(
        cfg: &HierarchicalResonanceLayerConfig,
    ) -> HierarchicalResonanceLayerParams<TestBackend> {
        HierarchicalResonanceLayerParams {
            proj_delta: projection(cfg.n_delta, cfg.n_dims, 0.1),
            proj_theta: projection(cfg.n_theta, cfg.n_dims, -0.2),
            proj_gamma: projection(cfg.n_gamma, cfg.n_dims, 0.3),
            pac_depth_dt: tensor1(vec![0.25]),
            pac_depth_tg: tensor1(vec![0.5]),
        }
    }

    #[test]
    fn pac_validation_empty_bands_and_explicit_parameters_are_typed() {
        assert_eq!(
            PhaseAmplitudeCouplingLayerConfig::default().initial_depth,
            0.3
        );
        for value in [f64::NAN, f64::INFINITY] {
            assert!(matches!(
                PhaseAmplitudeCouplingLayerConfig::with_depth(value).unwrap_err(),
                TrainError::NonFiniteParameter {
                    name: "initial_depth",
                    ..
                }
            ));
        }
        for value in [-0.1, 1.1] {
            assert!(matches!(
                PhaseAmplitudeCouplingLayerConfig::with_depth(value).unwrap_err(),
                TrainError::InvalidRatio {
                    name: "initial_depth",
                    ..
                }
            ));
        }

        let layer = PhaseAmplitudeCouplingLayerConfig::new()
            .init_from_params(tensor1(vec![0.6]))
            .unwrap();
        assert!(layer.validate_shapes().is_ok());
        let output = layer
            .forward(tensor2(vec![0.0, 0.0], 1, 2), tensor2(vec![2.0], 1, 1))
            .unwrap()
            .to_data()
            .to_vec::<f64>()
            .unwrap();
        assert_eq!(output, vec![3.2]);

        let batch_error = phase_amplitude_coupling(
            tensor2(vec![0.0, 0.0], 1, 2),
            tensor2(vec![1.0, 1.0], 2, 1),
            tensor1(vec![0.3]),
        )
        .unwrap_err();
        assert!(matches!(
            batch_error,
            TrainError::ShapeMismatch {
                name: "fast_amplitude",
                ..
            }
        ));
        assert!(matches!(
            phase_amplitude_coupling(
                Tensor::zeros([1, 0], &device()),
                Tensor::ones([1, 1], &device()),
                tensor1(vec![0.3])
            )
            .unwrap_err(),
            TrainError::EmptyBand { name: "slow" }
        ));
        assert!(matches!(
            phase_amplitude_coupling(
                Tensor::ones([1, 1], &device()),
                Tensor::zeros([1, 0], &device()),
                tensor1(vec![0.3])
            )
            .unwrap_err(),
            TrainError::EmptyBand { name: "fast" }
        ));

        let mut malformed = layer;
        malformed.modulation_depth =
            Param::initialized(Default::default(), tensor1(vec![0.2, 0.3]).require_grad());
        assert!(matches!(
            malformed.validate_shapes().unwrap_err(),
            TrainError::ShapeMismatch {
                name: "modulation_depth",
                ..
            }
        ));
    }

    #[test]
    fn automatic_sparse_k_and_odd_even_rings_cover_boundary_rules() {
        assert_eq!(automatic_sparse_k(0), 0);
        assert_eq!(automatic_sparse_k(1), 0);
        assert_eq!(automatic_sparse_k(2), 1);
        assert_eq!(automatic_sparse_k(5), 3);
        assert_eq!(automatic_sparse_k(8), 3);

        let phase = tensor2::<TestBackend>(vec![0.0, 1.0, 2.0, 3.0, 4.0], 1, 5);
        let odd = sparse_neighbor_indices(phase.clone(), 3)
            .to_data()
            .to_vec::<i64>()
            .unwrap();
        let even = sparse_neighbor_indices(phase, 4)
            .to_data()
            .to_vec::<i64>()
            .unwrap();
        assert_eq!(&odd[0..3], &[4, 1, 2]);
        assert_eq!(&even[0..4], &[3, 4, 1, 2]);
    }

    #[test]
    fn hierarchical_config_rejects_every_invalid_boundary() {
        for (sizes, expected) in [
            ((0, 1, 1), "delta"),
            ((1, 0, 1), "theta"),
            ((1, 1, 0), "gamma"),
        ] {
            assert!(matches!(
                HierarchicalResonanceLayerConfig::new(sizes.0, sizes.1, sizes.2, 2)
                    .unwrap_err(),
                TrainError::EmptyBand { name } if name == expected
            ));
        }
        assert!(matches!(
            HierarchicalResonanceLayerConfig::new(1, 1, 1, 0).unwrap_err(),
            TrainError::EmptyBand { name: "input" }
        ));
        assert!(matches!(
            HierarchicalResonanceLayerConfig::with_params(1, 1, 1, 2, 0, 0.01, 0.2, 0.3, None)
                .unwrap_err(),
            TrainError::InvalidStepCount {
                name: "n_steps",
                value: 0
            }
        ));
        for dt in [0.0, -0.1, f64::NAN] {
            assert!(matches!(
                HierarchicalResonanceLayerConfig::with_params(1, 1, 1, 2, 1, dt, 0.2, 0.3, None)
                    .unwrap_err(),
                TrainError::InvalidTimestep { .. }
            ));
        }
        assert!(matches!(
            HierarchicalResonanceLayerConfig::with_params(
                1,
                1,
                1,
                2,
                1,
                0.01,
                f64::INFINITY,
                0.3,
                None
            )
            .unwrap_err(),
            TrainError::NonFiniteParameter {
                name: "coupling_strength",
                ..
            }
        ));
        assert!(matches!(
            HierarchicalResonanceLayerConfig::with_params(1, 1, 1, 2, 1, 0.01, 0.2, f64::NAN, None)
                .unwrap_err(),
            TrainError::NonFiniteParameter {
                name: "pac_depth",
                ..
            }
        ));
        for depth in [-0.01, 1.01] {
            assert!(matches!(
                HierarchicalResonanceLayerConfig::with_params(
                    1, 1, 1, 2, 1, 0.01, 0.2, depth, None
                )
                .unwrap_err(),
                TrainError::InvalidRatio {
                    name: "pac_depth",
                    ..
                }
            ));
        }
        assert!(matches!(
            HierarchicalResonanceLayerConfig::with_params(1, 1, 1, 2, 1, 0.01, 0.2, 0.3, Some(0))
                .unwrap_err(),
            TrainError::InvalidTopK { k: 0 }
        ));
    }

    #[test]
    fn hierarchical_explicit_params_multistep_and_accessors_work() {
        let cfg =
            HierarchicalResonanceLayerConfig::with_params(2, 3, 4, 2, 2, 0.001, 0.2, 0.3, None)
                .unwrap();
        assert_eq!(cfg.n_total(), 9);
        let layer = cfg.init_from_params(hierarchical_params(&cfg)).unwrap();
        assert_eq!(layer.n_total(), 9);
        assert_eq!(layer.n_dims(), 2);
        assert!(layer.validate_shapes().is_ok());
        let (amplitude, phase) = layer
            .forward(tensor2(vec![0.2, -0.1, -0.3, 0.4], 2, 2))
            .unwrap();
        assert_eq!(amplitude.dims(), [2, 9]);
        assert_eq!(phase.dims(), [2, 9]);
        assert!(amplitude
            .to_data()
            .to_vec::<f64>()
            .unwrap()
            .iter()
            .all(|value| value.is_finite() && *value >= 0.0));
    }

    #[test]
    fn hierarchical_explicit_params_report_each_shape_error() {
        let cfg =
            HierarchicalResonanceLayerConfig::with_params(2, 3, 4, 2, 1, 0.001, 0.2, 0.3, Some(2))
                .unwrap();
        for expected_name in [
            "proj_delta",
            "proj_theta",
            "proj_gamma",
            "pac_depth_dt",
            "pac_depth_tg",
        ] {
            let mut params = hierarchical_params(&cfg);
            match expected_name {
                "proj_delta" => params.proj_delta = projection(1, 2, 0.0),
                "proj_theta" => params.proj_theta = projection(1, 2, 0.0),
                "proj_gamma" => params.proj_gamma = projection(1, 2, 0.0),
                "pac_depth_dt" => params.pac_depth_dt = tensor1(vec![0.2, 0.3]),
                "pac_depth_tg" => params.pac_depth_tg = tensor1(vec![0.2, 0.3]),
                _ => unreachable!(),
            }
            assert!(matches!(
                cfg.init_from_params(params).unwrap_err(),
                TrainError::ShapeMismatch { name, .. } if name == expected_name
            ));
        }
    }

    #[test]
    fn hierarchical_forward_and_validate_shapes_reject_malformed_tensors() {
        let cfg =
            HierarchicalResonanceLayerConfig::with_params(2, 2, 2, 3, 1, 0.001, 0.2, 0.3, Some(8))
                .unwrap();
        let fresh = || cfg.init::<TestBackend>(&device(), &mut Seed::new(14, 0));
        assert!(matches!(
            fresh()
                .forward(Tensor::zeros([2, 2], &device()))
                .unwrap_err(),
            TrainError::ShapeMismatch { name: "x", .. }
        ));

        let mut layer = fresh();
        layer.proj_delta.weight = Param::initialized(
            Default::default(),
            Tensor::zeros([1, 1], &device()).require_grad(),
        );
        assert!(matches!(
            layer.validate_shapes().unwrap_err(),
            TrainError::ShapeMismatch {
                name: "proj_delta",
                ..
            }
        ));
        let mut layer = fresh();
        layer.proj_theta.weight = Param::initialized(
            Default::default(),
            Tensor::zeros([1, 1], &device()).require_grad(),
        );
        assert!(matches!(
            layer.validate_shapes().unwrap_err(),
            TrainError::ShapeMismatch {
                name: "proj_theta",
                ..
            }
        ));
        let mut layer = fresh();
        layer.proj_gamma.weight = Param::initialized(
            Default::default(),
            Tensor::zeros([1, 1], &device()).require_grad(),
        );
        assert!(matches!(
            layer.validate_shapes().unwrap_err(),
            TrainError::ShapeMismatch {
                name: "proj_gamma",
                ..
            }
        ));
        let mut layer = fresh();
        layer.pac_depth_dt =
            Param::initialized(Default::default(), tensor1(vec![0.2, 0.3]).require_grad());
        assert!(matches!(
            layer.validate_shapes().unwrap_err(),
            TrainError::ShapeMismatch {
                name: "pac_depth_dt",
                ..
            }
        ));
        assert!(matches!(
            layer.forward(Tensor::zeros([1, 3], &device())).unwrap_err(),
            TrainError::ShapeMismatch {
                name: "modulation_depth",
                ..
            }
        ));
        let mut layer = fresh();
        layer.pac_depth_tg =
            Param::initialized(Default::default(), tensor1(vec![0.2, 0.3]).require_grad());
        assert!(matches!(
            layer.validate_shapes().unwrap_err(),
            TrainError::ShapeMismatch {
                name: "pac_depth_tg",
                ..
            }
        ));
        assert!(matches!(
            layer.forward(Tensor::zeros([1, 3], &device())).unwrap_err(),
            TrainError::ShapeMismatch {
                name: "modulation_depth",
                ..
            }
        ));
    }

    #[test]
    fn discrete_config_validation_explicit_params_and_multistep_work() {
        assert!(matches!(
            DiscreteDeltaThetaGammaLayerConfig::new(1, 1, 1, 0).unwrap_err(),
            TrainError::EmptyBand { name: "input" }
        ));
        assert!(matches!(
            DiscreteDeltaThetaGammaLayerConfig::with_params(1, 1, 1, 2, 0, 0.01, 0.2, 0.3)
                .unwrap_err(),
            TrainError::InvalidStepCount {
                name: "n_steps",
                value: 0
            }
        ));
        assert!(matches!(
            DiscreteDeltaThetaGammaLayerConfig::with_params(1, 1, 1, 2, 1, 0.0, 0.2, 0.3)
                .unwrap_err(),
            TrainError::InvalidTimestep { .. }
        ));
        assert!(DiscreteDeltaThetaGammaLayerConfig::new(0, 1, 1, 2).is_err());

        let cfg = DiscreteDeltaThetaGammaLayerConfig::with_params(1, 2, 3, 2, 3, 0.001, 0.2, 0.3)
            .unwrap();
        assert_eq!(cfg.n_total(), 6);
        let layer = cfg
            .init_from_params(DiscreteDeltaThetaGammaLayerParams {
                proj_phase: projection(6, 2, 0.1),
                proj_amplitude: projection(6, 2, -0.2),
                dynamics: dynamics_params(1, 2, 3),
            })
            .unwrap();
        assert_eq!(layer.n_dims(), 2);
        assert_eq!(layer.n_total(), 6);
        assert!(layer.validate_shapes().is_ok());
        let output = layer
            .forward(tensor2(vec![0.2, -0.1, -0.4, 0.3], 2, 2))
            .unwrap();
        assert_eq!(output.dims(), [2, 6]);
        assert!(output
            .to_data()
            .to_vec::<f64>()
            .unwrap()
            .iter()
            .all(|value| value.is_finite() && *value >= 0.0));
    }

    #[test]
    fn discrete_explicit_params_and_forward_report_shape_errors() {
        let cfg = DiscreteDeltaThetaGammaLayerConfig::with_params(1, 2, 3, 2, 1, 0.001, 0.2, 0.3)
            .unwrap();
        let make_params = || DiscreteDeltaThetaGammaLayerParams {
            proj_phase: projection(6, 2, 0.1),
            proj_amplitude: projection(6, 2, 0.2),
            dynamics: dynamics_params(1, 2, 3),
        };
        let mut params = make_params();
        params.proj_phase = projection(5, 2, 0.0);
        assert!(matches!(
            cfg.init_from_params(params).unwrap_err(),
            TrainError::ShapeMismatch {
                name: "proj_phase",
                ..
            }
        ));
        let mut params = make_params();
        params.proj_amplitude = projection(5, 2, 0.0);
        assert!(matches!(
            cfg.init_from_params(params).unwrap_err(),
            TrainError::ShapeMismatch {
                name: "proj_amplitude",
                ..
            }
        ));
        let mut params = make_params();
        params.dynamics.delta_freq = tensor1(vec![2.0, 2.0]);
        assert!(matches!(
            cfg.init_from_params(params).unwrap_err(),
            TrainError::ShapeMismatch {
                name: "delta_freq",
                ..
            }
        ));

        let layer = cfg.init_from_params(make_params()).unwrap();
        assert!(matches!(
            layer.forward(Tensor::zeros([1, 3], &device())).unwrap_err(),
            TrainError::ShapeMismatch { name: "x", .. }
        ));
        let mut malformed = layer;
        malformed.proj_amplitude.weight = Param::initialized(
            Default::default(),
            Tensor::zeros([1, 1], &device()).require_grad(),
        );
        assert!(matches!(
            malformed.validate_shapes().unwrap_err(),
            TrainError::ShapeMismatch {
                name: "proj_amplitude",
                ..
            }
        ));
    }
}
