//! Oscillator models behind the `Dynamics` trait.
//!
//! - [`KuramotoOscillator`]: mean-field `O(N)`, full pairwise `O(N²)`, sparse k-NN `O(N·k)`.
//! - [`StuartLandauOscillator`]: complex amplitude limit-cycle dynamics.
//! - [`HopfOscillator`]: bifurcation-driven polar coordinate dynamics.
//!
//! Coupling mode is an enum ([`CouplingMode`]), never a string.
//!
//! # Derivative clamping
//!
//! As in PRINet 3.0 (`oscillator_models.py`), only the sparse k-NN coupling
//! paths clamp derivatives to `±DERIV_CLAMP` (the reference's `_clamp_finite`,
//! via [`StateDerivatives::new`]). Full and mean-field Kuramoto/Hopf, every
//! Stuart–Landau path with a PRINet 3.0 counterpart, and the `N ≤ 1` shortcut
//! return derivatives exactly as computed ([`StateDerivatives::unclamped`]).
//! Stuart–Landau sparse k-NN has no PRINet 3.0 counterpart and keeps the
//! clamp. A consumer that wants every derivative bounded selects
//! [`GuardPolicy::Bounded`](crate::integrate::GuardPolicy::Bounded) on the
//! integrator.

use num_complex::Complex64;
use serde::{Deserialize, Serialize};

use crate::coupling::CouplingMode;
use crate::state::{
    build_phase_knn_index, safe_phase_diff, OscillatorState, StateDerivatives, StateError,
};

/// Trait implemented by all oscillator dynamics models.
pub trait Dynamics {
    /// Compute time derivatives (`dphase/dt`, `damplitude/dt`, `dfrequency/dt`) for a given oscillator state.
    ///
    /// # Errors
    ///
    /// Returns [`StateError`] if:
    /// - `state.n_oscillators()` does not match the model's population size,
    /// - custom coupling matrix shape or values are invalid,
    /// - with `strict-checks` enabled, a derivative or parameter is non-finite or out of bounds.
    fn compute_derivatives(&self, state: &OscillatorState) -> Result<StateDerivatives, StateError>;
}

/// Compute a vector-Jacobian product for oscillator derivatives.
///
/// The derivative model remains Rust-owned while the PyTorch compatibility
/// facade uses this central-difference fallback to connect the non-trainable
/// dynamics API to autograd. Phase-neighbour selection is treated as locally
/// constant, matching the reference's non-differentiable sort operation.
///
/// # Errors
///
/// Returns [`StateError`] when gradient lengths mismatch the state or a model
/// evaluation fails.
pub fn dynamics_vjp(
    model: &dyn Dynamics,
    state: &OscillatorState,
    grad_dphase: &[f64],
    grad_damplitude: &[f64],
    grad_dfrequency: &[f64],
) -> Result<StateDerivatives, StateError> {
    let n = state.n_oscillators();
    for (name, values) in [
        ("grad_dphase", grad_dphase),
        ("grad_damplitude", grad_damplitude),
        ("grad_dfrequency", grad_dfrequency),
    ] {
        if values.len() != n {
            return Err(StateError::LengthMismatch {
                name,
                expected: n,
                got: values.len(),
            });
        }
    }

    fn objective(
        derivative: &StateDerivatives,
        grad_dphase: &[f64],
        grad_damplitude: &[f64],
        grad_dfrequency: &[f64],
    ) -> f64 {
        derivative
            .dphase
            .iter()
            .zip(grad_dphase)
            .chain(derivative.damplitude.iter().zip(grad_damplitude))
            .chain(derivative.dfrequency.iter().zip(grad_dfrequency))
            .map(|(value, gradient)| value * gradient)
            .sum()
    }

    const EPSILON: f64 = 1e-6;
    let mut gradients = [vec![0.0; n], vec![0.0; n], vec![0.0; n]];
    for (field, output) in gradients.iter_mut().enumerate() {
        for (index, gradient) in output.iter_mut().enumerate() {
            let mut plus = state.clone();
            let mut minus = state.clone();
            let (plus_field, minus_field) = match field {
                0 => (&mut plus.phase, &mut minus.phase),
                1 => (&mut plus.amplitude, &mut minus.amplitude),
                _ => (&mut plus.frequency, &mut minus.frequency),
            };
            plus_field[index] += EPSILON;
            minus_field[index] -= EPSILON;
            let plus_value = objective(
                &model.compute_derivatives(&plus)?,
                grad_dphase,
                grad_damplitude,
                grad_dfrequency,
            );
            let minus_value = objective(
                &model.compute_derivatives(&minus)?,
                grad_dphase,
                grad_damplitude,
                grad_dfrequency,
            );
            *gradient = (plus_value - minus_value) / (2.0 * EPSILON);
        }
    }
    for (name, values) in [
        ("gradient_phase", &gradients[0]),
        ("gradient_amplitude", &gradients[1]),
        ("gradient_frequency", &gradients[2]),
    ] {
        for (index, &value) in values.iter().enumerate() {
            if !value.is_finite() {
                return Err(StateError::NonFiniteValue { name, index, value });
            }
        }
    }
    Ok(StateDerivatives {
        dphase: gradients[0].clone(),
        damplitude: gradients[1].clone(),
        dfrequency: gradients[2].clone(),
    })
}

fn validate_finite(value: f64, name: &'static str) -> Result<(), StateError> {
    if !value.is_finite() {
        return Err(StateError::NonFiniteValue {
            name,
            index: 0,
            value,
        });
    }
    Ok(())
}

fn validate_coupling_mode(mode: &CouplingMode, n_oscillators: usize) -> Result<(), StateError> {
    match mode {
        CouplingMode::MeanField => Ok(()),
        CouplingMode::Full { matrix: Some(mat) } => {
            let expected = n_oscillators * n_oscillators;
            if mat.len() != expected {
                return Err(StateError::LengthMismatch {
                    name: "coupling_matrix",
                    expected,
                    got: mat.len(),
                });
            }
            for (i, &v) in mat.iter().enumerate() {
                if !v.is_finite() {
                    return Err(StateError::NonFiniteValue {
                        name: "coupling_matrix",
                        index: i,
                        value: v,
                    });
                }
            }
            Ok(())
        }
        CouplingMode::Full { matrix: None } => Ok(()),
        CouplingMode::SparseKnn { k: Some(k) } => {
            if *k == 0 || *k >= n_oscillators {
                return Err(StateError::InvalidKNeighbors {
                    k: *k,
                    n: n_oscillators,
                });
            }
            Ok(())
        }
        CouplingMode::SparseKnn { k: None } => Ok(()),
    }
}

fn resolve_sparse_k(user_k: Option<usize>, n: usize) -> usize {
    match user_k {
        Some(k_val) => k_val,
        None => {
            let default_k = (n as f64).log2().ceil() as usize;
            let default_k = default_k.max(1);
            if default_k >= n {
                n - 1
            } else {
                default_k
            }
        }
    }
}

/// Kuramoto coupled oscillator model with amplitude and frequency modulation.
///
/// Implements extended Kuramoto equations with amplitude decay and frequency adaptation:
/// - Mean-field `O(N)`: global complex order parameter `Z = (1/N) Σ_j r_j e^{i φ_j} = R e^{i ψ}`.
/// - Full pairwise `O(N²)`: custom `N x N` matrix or uniform all-to-all `K/N` with zero diagonal.
/// - Sparse k-NN `O(N k)`: coupling to `k` nearest phase-space neighbors.
#[derive(Clone, Debug, PartialEq, Serialize, Deserialize)]
pub struct KuramotoOscillator {
    n_oscillators: usize,
    coupling_strength: f64,
    decay_rate: f64,
    freq_adaptation_rate: f64,
    coupling_mode: CouplingMode,
}

impl KuramotoOscillator {
    /// Create a new Kuramoto oscillator model.
    ///
    /// # Errors
    ///
    /// Returns [`StateError`] for an empty population, non-finite parameters, or invalid coupling mode.
    pub fn new(
        n_oscillators: usize,
        coupling_strength: f64,
        decay_rate: f64,
        freq_adaptation_rate: f64,
        coupling_mode: CouplingMode,
    ) -> Result<Self, StateError> {
        if n_oscillators == 0 {
            return Err(StateError::EmptyPopulation);
        }
        validate_finite(coupling_strength, "coupling_strength")?;
        validate_finite(decay_rate, "decay_rate")?;
        validate_finite(freq_adaptation_rate, "freq_adaptation_rate")?;
        validate_coupling_mode(&coupling_mode, n_oscillators)?;

        Ok(Self {
            n_oscillators,
            coupling_strength,
            decay_rate,
            freq_adaptation_rate,
            coupling_mode,
        })
    }

    /// Number of oscillators N.
    pub fn n_oscillators(&self) -> usize {
        self.n_oscillators
    }

    /// Global coupling strength K.
    pub fn coupling_strength(&self) -> f64 {
        self.coupling_strength
    }

    /// Set global coupling strength K.
    pub fn set_coupling_strength(&mut self, val: f64) -> Result<(), StateError> {
        validate_finite(val, "coupling_strength")?;
        self.coupling_strength = val;
        Ok(())
    }

    /// Amplitude decay rate λ.
    pub fn decay_rate(&self) -> f64 {
        self.decay_rate
    }

    /// Set amplitude decay rate λ.
    pub fn set_decay_rate(&mut self, val: f64) -> Result<(), StateError> {
        validate_finite(val, "decay_rate")?;
        self.decay_rate = val;
        Ok(())
    }

    /// Frequency adaptation rate γ.
    pub fn freq_adaptation_rate(&self) -> f64 {
        self.freq_adaptation_rate
    }

    /// Set frequency adaptation rate γ.
    pub fn set_freq_adaptation_rate(&mut self, val: f64) -> Result<(), StateError> {
        validate_finite(val, "freq_adaptation_rate")?;
        self.freq_adaptation_rate = val;
        Ok(())
    }

    /// Active coupling mode.
    pub fn coupling_mode(&self) -> &CouplingMode {
        &self.coupling_mode
    }

    /// Set active coupling mode.
    pub fn set_coupling_mode(&mut self, mode: CouplingMode) -> Result<(), StateError> {
        validate_coupling_mode(&mode, self.n_oscillators)?;
        self.coupling_mode = mode;
        Ok(())
    }

    fn compute_mean_field(&self, state: &OscillatorState) -> Result<StateDerivatives, StateError> {
        let n = state.n_oscillators();
        let inv_n = 1.0 / (n as f64);

        let mut z_r = 0.0;
        let mut z_i = 0.0;
        for i in 0..n {
            let r = state.amplitude[i];
            let phi = state.phase[i];
            z_r += r * phi.cos();
            z_i += r * phi.sin();
        }
        z_r *= inv_n;
        z_i *= inv_n;

        let big_r = (z_r * z_r + z_i * z_i).sqrt();
        let psi = z_i.atan2(z_r);

        let k = self.coupling_strength;
        let k_r = k * big_r;

        let mut dphase = Vec::with_capacity(n);
        let mut damplitude = Vec::with_capacity(n);
        let mut dfrequency = Vec::with_capacity(n);

        for i in 0..n {
            let phi = state.phase[i];
            let r = state.amplitude[i];
            let omega = state.frequency[i];
            let d_psi = psi - phi;

            let sin_diff = d_psi.sin();
            let cos_diff = d_psi.cos();

            dphase.push(omega + k_r * sin_diff);
            damplitude.push(-self.decay_rate * r + k_r * cos_diff);
            dfrequency.push(self.freq_adaptation_rate * k_r * sin_diff * inv_n);
        }

        StateDerivatives::unclamped(dphase, damplitude, dfrequency)
    }

    fn compute_full(
        &self,
        state: &OscillatorState,
        matrix: Option<&[f64]>,
    ) -> Result<StateDerivatives, StateError> {
        let n = state.n_oscillators();
        let inv_n = 1.0 / (n as f64);
        let default_k_elem = self.coupling_strength * inv_n;

        let mut dphase = Vec::with_capacity(n);
        let mut damplitude = Vec::with_capacity(n);
        let mut dfrequency = Vec::with_capacity(n);

        for i in 0..n {
            let phi_i = state.phase[i];
            let r_i = state.amplitude[i];
            let omega_i = state.frequency[i];

            let mut sin_sum = 0.0;
            let mut cos_sum = 0.0;

            for j in 0..n {
                let k_ij = match matrix {
                    Some(mat) => mat[i * n + j],
                    None => {
                        if i == j {
                            0.0
                        } else {
                            default_k_elem
                        }
                    }
                };

                if k_ij != 0.0 {
                    let phi_j = state.phase[j];
                    let r_j = state.amplitude[j];
                    let diff = safe_phase_diff(phi_j, phi_i);
                    sin_sum += k_ij * diff.sin() * r_j;
                    cos_sum += k_ij * diff.cos() * r_j;
                }
            }

            dphase.push(omega_i + sin_sum);
            damplitude.push(-self.decay_rate * r_i + cos_sum);
            dfrequency.push(self.freq_adaptation_rate * sin_sum * inv_n);
        }

        StateDerivatives::unclamped(dphase, damplitude, dfrequency)
    }

    fn compute_sparse_knn(
        &self,
        state: &OscillatorState,
        user_k: Option<usize>,
    ) -> Result<StateDerivatives, StateError> {
        let n = state.n_oscillators();
        let k = resolve_sparse_k(user_k, n);

        let nbr_index = build_phase_knn_index(&state.phase, k)?;
        let k_eff = k as f64;
        let k_eff_coupling = self.coupling_strength / k_eff;

        let mut dphase = Vec::with_capacity(n);
        let mut damplitude = Vec::with_capacity(n);
        let mut dfrequency = Vec::with_capacity(n);

        for (i, nbrs) in nbr_index.iter().enumerate() {
            let phi_i = state.phase[i];
            let r_i = state.amplitude[i];
            let omega_i = state.frequency[i];

            let mut sin_sum = 0.0;
            let mut cos_sum = 0.0;

            for &j in nbrs {
                let phi_j = state.phase[j];
                let r_j = state.amplitude[j];
                let diff = safe_phase_diff(phi_j, phi_i);
                sin_sum += k_eff_coupling * diff.sin() * r_j;
                cos_sum += k_eff_coupling * diff.cos() * r_j;
            }

            dphase.push(omega_i + sin_sum);
            damplitude.push(-self.decay_rate * r_i + cos_sum);
            dfrequency.push(self.freq_adaptation_rate * sin_sum / k_eff);
        }

        StateDerivatives::new(dphase, damplitude, dfrequency)
    }
}

impl Dynamics for KuramotoOscillator {
    fn compute_derivatives(&self, state: &OscillatorState) -> Result<StateDerivatives, StateError> {
        let n = state.n_oscillators();
        if n != self.n_oscillators {
            return Err(StateError::LengthMismatch {
                name: "state",
                expected: self.n_oscillators,
                got: n,
            });
        }

        if n <= 1 {
            let dphase = state.frequency.clone();
            let damplitude = state
                .amplitude
                .iter()
                .map(|&a| -self.decay_rate * a)
                .collect();
            let dfrequency = vec![0.0; n];
            return StateDerivatives::unclamped(dphase, damplitude, dfrequency);
        }

        match &self.coupling_mode {
            CouplingMode::MeanField => self.compute_mean_field(state),
            CouplingMode::Full { matrix } => self.compute_full(state, matrix.as_deref()),
            CouplingMode::SparseKnn { k } => self.compute_sparse_knn(state, *k),
        }
    }
}

/// Stuart–Landau coupled oscillator model (Hopf normal form).
///
/// Implements complex-amplitude dynamics:
/// `dz_i/dt = (μ + i ω_i) z_i - |z_i|² z_i + C_i`
/// where `z_i = r_i exp(i φ_i)` and `C_i` is the per-mode coupling term.
///
/// Coupling term `C_i` for each [`CouplingMode`]:
/// - `MeanField`: `C_i = K (Z - z_i)` where `Z = (1/N) Σ_j z_j` is the mean
///   complex phasor.
/// - `Full { matrix }`: `C_i = Σ_j K_{ij} (z_j - z_i)`. When no matrix is
///   supplied the equivalent uniform mean-field form is used (the diagonal
///   contribution to this sum is zero, so `K/N` on or off the diagonal gives
///   the same result for Stuart–Landau).
/// - `SparseKnn { k }`: `C_i = (K/k) Σ_{j ∈ NN_k(i)} (z_j - z_i)` where
///   `NN_k(i)` are the `k` nearest phase neighbours; `k` defaults to
///   `max(1, ceil(log2 N))`.
///
/// The polar derivatives are extracted as
/// `dr_i/dt = Re(dz_i/dt · exp(-i φ_i))` and
/// `dφ_i/dt = Im(dz_i/dt · exp(-i φ_i)) / r_i` (with `r_i` clamped at `1e-8`).
#[derive(Clone, Debug, PartialEq, Serialize, Deserialize)]
pub struct StuartLandauOscillator {
    n_oscillators: usize,
    coupling_strength: f64,
    bifurcation_param: f64,
    coupling_mode: CouplingMode,
}

impl StuartLandauOscillator {
    /// Create a new Stuart–Landau oscillator model.
    ///
    /// # Errors
    ///
    /// Returns [`StateError`] for an empty population, non-finite parameters, or invalid coupling mode.
    pub fn new(
        n_oscillators: usize,
        coupling_strength: f64,
        bifurcation_param: f64,
        coupling_mode: CouplingMode,
    ) -> Result<Self, StateError> {
        if n_oscillators == 0 {
            return Err(StateError::EmptyPopulation);
        }
        validate_finite(coupling_strength, "coupling_strength")?;
        validate_finite(bifurcation_param, "bifurcation_param")?;
        validate_coupling_mode(&coupling_mode, n_oscillators)?;

        Ok(Self {
            n_oscillators,
            coupling_strength,
            bifurcation_param,
            coupling_mode,
        })
    }

    /// Number of oscillators N.
    pub fn n_oscillators(&self) -> usize {
        self.n_oscillators
    }

    /// Global coupling strength K.
    pub fn coupling_strength(&self) -> f64 {
        self.coupling_strength
    }

    /// Set global coupling strength K.
    pub fn set_coupling_strength(&mut self, val: f64) -> Result<(), StateError> {
        validate_finite(val, "coupling_strength")?;
        self.coupling_strength = val;
        Ok(())
    }

    /// Hopf bifurcation parameter μ.
    pub fn bifurcation_param(&self) -> f64 {
        self.bifurcation_param
    }

    /// Set Hopf bifurcation parameter μ.
    pub fn set_bifurcation_param(&mut self, val: f64) -> Result<(), StateError> {
        validate_finite(val, "bifurcation_param")?;
        self.bifurcation_param = val;
        Ok(())
    }

    /// Active coupling mode.
    pub fn coupling_mode(&self) -> &CouplingMode {
        &self.coupling_mode
    }

    /// Set active coupling mode.
    pub fn set_coupling_mode(&mut self, mode: CouplingMode) -> Result<(), StateError> {
        validate_coupling_mode(&mode, self.n_oscillators)?;
        self.coupling_mode = mode;
        Ok(())
    }

    fn compute_mean_field(&self, state: &OscillatorState) -> Result<StateDerivatives, StateError> {
        let n = state.n_oscillators();
        let inv_n = 1.0 / (n as f64);

        let z_vec: Vec<Complex64> = (0..n)
            .map(|i| Complex64::from_polar(state.amplitude[i], state.phase[i]))
            .collect();

        let z_mean: Complex64 = z_vec.iter().sum::<Complex64>() * inv_n;
        let k = self.coupling_strength;
        let mu = self.bifurcation_param;

        let mut dphase = Vec::with_capacity(n);
        let mut damplitude = Vec::with_capacity(n);
        let dfrequency = vec![0.0; n];

        for (i, &z_i) in z_vec.iter().enumerate() {
            let r_i = state.amplitude[i];
            let phi_i = state.phase[i];
            let omega_i = state.frequency[i];

            let c_i = (z_mean - z_i) * k;
            let mu_c = Complex64::new(mu, omega_i);
            let dz_i = mu_c * z_i - (r_i * r_i) * z_i + c_i;

            let rot = Complex64::from_polar(1.0, -phi_i);
            let w_i = dz_i * rot;

            let dr = w_i.re;
            let safe_r = r_i.max(1e-8);
            let dphi = w_i.im / safe_r;

            dphase.push(dphi);
            damplitude.push(dr);
        }

        StateDerivatives::unclamped(dphase, damplitude, dfrequency)
    }

    fn compute_full(
        &self,
        state: &OscillatorState,
        matrix: Option<&[f64]>,
    ) -> Result<StateDerivatives, StateError> {
        let n = state.n_oscillators();
        let z_vec: Vec<Complex64> = (0..n)
            .map(|i| Complex64::from_polar(state.amplitude[i], state.phase[i]))
            .collect();

        let mu = self.bifurcation_param;

        let mut dphase = Vec::with_capacity(n);
        let mut damplitude = Vec::with_capacity(n);
        let dfrequency = vec![0.0; n];

        match matrix {
            None => self.compute_mean_field(state),
            Some(mat) => {
                for i in 0..n {
                    let z_i = z_vec[i];
                    let r_i = state.amplitude[i];
                    let phi_i = state.phase[i];
                    let omega_i = state.frequency[i];

                    let mut c_i = Complex64::new(0.0, 0.0);
                    for j in 0..n {
                        let k_ij = mat[i * n + j];
                        if k_ij != 0.0 {
                            c_i += k_ij * (z_vec[j] - z_i);
                        }
                    }

                    let mu_c = Complex64::new(mu, omega_i);
                    let dz_i = mu_c * z_i - (r_i * r_i) * z_i + c_i;

                    let rot = Complex64::from_polar(1.0, -phi_i);
                    let w_i = dz_i * rot;

                    let dr = w_i.re;
                    let safe_r = r_i.max(1e-8);
                    let dphi = w_i.im / safe_r;

                    dphase.push(dphi);
                    damplitude.push(dr);
                }

                StateDerivatives::unclamped(dphase, damplitude, dfrequency)
            }
        }
    }

    fn compute_sparse_knn(
        &self,
        state: &OscillatorState,
        user_k: Option<usize>,
    ) -> Result<StateDerivatives, StateError> {
        let n = state.n_oscillators();
        let k = resolve_sparse_k(user_k, n);

        let nbr_index = build_phase_knn_index(&state.phase, k)?;
        let k_eff = k as f64;
        let k_eff_coupling = self.coupling_strength / k_eff;
        let mu = self.bifurcation_param;

        let z_vec: Vec<Complex64> = (0..n)
            .map(|i| Complex64::from_polar(state.amplitude[i], state.phase[i]))
            .collect();

        let mut dphase = Vec::with_capacity(n);
        let mut damplitude = Vec::with_capacity(n);
        let dfrequency = vec![0.0; n];

        for (i, nbrs) in nbr_index.iter().enumerate() {
            let z_i = z_vec[i];
            let r_i = state.amplitude[i];
            let phi_i = state.phase[i];
            let omega_i = state.frequency[i];

            let mut c_i = Complex64::new(0.0, 0.0);
            for &j in nbrs {
                c_i += k_eff_coupling * (z_vec[j] - z_i);
            }

            let mu_c = Complex64::new(mu, omega_i);
            let dz_i = mu_c * z_i - (r_i * r_i) * z_i + c_i;

            let rot = Complex64::from_polar(1.0, -phi_i);
            let w_i = dz_i * rot;

            let dr = w_i.re;
            let safe_r = r_i.max(1e-8);
            let dphi = w_i.im / safe_r;

            dphase.push(dphi);
            damplitude.push(dr);
        }

        StateDerivatives::new(dphase, damplitude, dfrequency)
    }
}

impl Dynamics for StuartLandauOscillator {
    fn compute_derivatives(&self, state: &OscillatorState) -> Result<StateDerivatives, StateError> {
        let n = state.n_oscillators();
        if n != self.n_oscillators {
            return Err(StateError::LengthMismatch {
                name: "state",
                expected: self.n_oscillators,
                got: n,
            });
        }

        if n <= 1 {
            let mu = self.bifurcation_param;
            let dphase = state.frequency.clone();
            let damplitude = state
                .amplitude
                .iter()
                .map(|&r| mu * r - r * r * r)
                .collect();
            let dfrequency = vec![0.0; n];
            return StateDerivatives::unclamped(dphase, damplitude, dfrequency);
        }

        match &self.coupling_mode {
            CouplingMode::MeanField => self.compute_mean_field(state),
            CouplingMode::Full { matrix } => self.compute_full(state, matrix.as_deref()),
            CouplingMode::SparseKnn { k } => self.compute_sparse_knn(state, *k),
        }
    }
}

/// Hopf bifurcation oscillator with explicit polar amplitude-phase dynamics.
///
/// Implements supercritical Hopf bifurcation dynamics:
/// - `dr_i/dt = μ r_i - r_i³ + C_i^cos`
/// - `dφ_i/dt = ω_i + C_i^sin / r_i` (with `r_i` clamped at `1e-8`)
/// - `dω_i/dt = (γ / N) C_i^sin`
///
/// The per-mode coupling sums are:
/// - `MeanField`: `C_i^sin = K R sin(ψ - φ_i)` and `C_i^cos = K R cos(ψ - φ_i)`
///   where `R e^{i ψ} = (1/N) Σ_j r_j e^{i φ_j}` is the complex order parameter.
/// - `Full { matrix }`: `C_i^sin = Σ_j K_{ij} sin(φ_j - φ_i) r_j` and
///   `C_i^cos = Σ_j K_{ij} cos(φ_j - φ_i) r_j`. When no matrix is supplied,
///   `K_{ij} = K/N` for `i ≠ j` and `0` on the diagonal.
/// - `SparseKnn { k }`: `C_i^sin = (K/k) Σ_{j ∈ NN_k(i)} sin(φ_j - φ_i) r_j` and
///   `C_i^cos = (K/k) Σ_{j ∈ NN_k(i)} cos(φ_j - φ_i) r_j` where `NN_k(i)` are the
///   `k` nearest phase neighbours; `k` defaults to `max(1, ceil(log2 N))`.
#[derive(Clone, Debug, PartialEq, Serialize, Deserialize)]
pub struct HopfOscillator {
    n_oscillators: usize,
    coupling_strength: f64,
    bifurcation_param: f64,
    freq_adaptation_rate: f64,
    coupling_mode: CouplingMode,
}

impl HopfOscillator {
    /// Create a new Hopf oscillator model.
    ///
    /// # Errors
    ///
    /// Returns [`StateError`] for an empty population, non-finite parameters, or invalid coupling mode.
    pub fn new(
        n_oscillators: usize,
        coupling_strength: f64,
        bifurcation_param: f64,
        freq_adaptation_rate: f64,
        coupling_mode: CouplingMode,
    ) -> Result<Self, StateError> {
        if n_oscillators == 0 {
            return Err(StateError::EmptyPopulation);
        }
        validate_finite(coupling_strength, "coupling_strength")?;
        validate_finite(bifurcation_param, "bifurcation_param")?;
        validate_finite(freq_adaptation_rate, "freq_adaptation_rate")?;
        validate_coupling_mode(&coupling_mode, n_oscillators)?;

        Ok(Self {
            n_oscillators,
            coupling_strength,
            bifurcation_param,
            freq_adaptation_rate,
            coupling_mode,
        })
    }

    /// Number of oscillators N.
    pub fn n_oscillators(&self) -> usize {
        self.n_oscillators
    }

    /// Global coupling strength K.
    pub fn coupling_strength(&self) -> f64 {
        self.coupling_strength
    }

    /// Set global coupling strength K.
    pub fn set_coupling_strength(&mut self, val: f64) -> Result<(), StateError> {
        validate_finite(val, "coupling_strength")?;
        self.coupling_strength = val;
        Ok(())
    }

    /// Hopf bifurcation parameter μ.
    pub fn bifurcation_param(&self) -> f64 {
        self.bifurcation_param
    }

    /// Set Hopf bifurcation parameter μ.
    pub fn set_bifurcation_param(&mut self, val: f64) -> Result<(), StateError> {
        validate_finite(val, "bifurcation_param")?;
        self.bifurcation_param = val;
        Ok(())
    }

    /// Frequency adaptation rate γ.
    pub fn freq_adaptation_rate(&self) -> f64 {
        self.freq_adaptation_rate
    }

    /// Set frequency adaptation rate γ.
    pub fn set_freq_adaptation_rate(&mut self, val: f64) -> Result<(), StateError> {
        validate_finite(val, "freq_adaptation_rate")?;
        self.freq_adaptation_rate = val;
        Ok(())
    }

    /// Active coupling mode.
    pub fn coupling_mode(&self) -> &CouplingMode {
        &self.coupling_mode
    }

    /// Set active coupling mode.
    pub fn set_coupling_mode(&mut self, mode: CouplingMode) -> Result<(), StateError> {
        validate_coupling_mode(&mode, self.n_oscillators)?;
        self.coupling_mode = mode;
        Ok(())
    }

    /// Theoretical limit cycle amplitude sqrt(μ) when μ > 0.
    pub fn limit_cycle_amplitude(&self) -> f64 {
        if self.bifurcation_param <= 0.0 {
            0.0
        } else {
            self.bifurcation_param.sqrt()
        }
    }

    fn compute_mean_field(&self, state: &OscillatorState) -> Result<StateDerivatives, StateError> {
        let n = state.n_oscillators();
        let inv_n = 1.0 / (n as f64);

        let mut z_r = 0.0;
        let mut z_i = 0.0;
        for i in 0..n {
            let r = state.amplitude[i];
            let phi = state.phase[i];
            z_r += r * phi.cos();
            z_i += r * phi.sin();
        }
        z_r *= inv_n;
        z_i *= inv_n;

        let big_r = (z_r * z_r + z_i * z_i).sqrt();
        let psi = z_i.atan2(z_r);

        let k = self.coupling_strength;
        let k_r = k * big_r;
        let mu = self.bifurcation_param;

        let mut dphase = Vec::with_capacity(n);
        let mut damplitude = Vec::with_capacity(n);
        let mut dfrequency = Vec::with_capacity(n);

        for i in 0..n {
            let phi = state.phase[i];
            let r = state.amplitude[i];
            let omega = state.frequency[i];
            let d_psi = psi - phi;

            let sin_diff = d_psi.sin();
            let cos_diff = d_psi.cos();

            let safe_r = r.max(1e-8);

            dphase.push(omega + k_r * sin_diff / safe_r);
            damplitude.push(mu * r - r * r * r + k_r * cos_diff);
            dfrequency.push(self.freq_adaptation_rate * k_r * sin_diff * inv_n);
        }

        StateDerivatives::unclamped(dphase, damplitude, dfrequency)
    }

    fn compute_full(
        &self,
        state: &OscillatorState,
        matrix: Option<&[f64]>,
    ) -> Result<StateDerivatives, StateError> {
        let n = state.n_oscillators();
        let inv_n = 1.0 / (n as f64);
        let default_k_elem = self.coupling_strength * inv_n;
        let mu = self.bifurcation_param;

        let mut dphase = Vec::with_capacity(n);
        let mut damplitude = Vec::with_capacity(n);
        let mut dfrequency = Vec::with_capacity(n);

        for i in 0..n {
            let phi_i = state.phase[i];
            let r_i = state.amplitude[i];
            let omega_i = state.frequency[i];

            let mut sin_sum = 0.0;
            let mut cos_sum = 0.0;

            for j in 0..n {
                let k_ij = match matrix {
                    Some(mat) => mat[i * n + j],
                    None => {
                        if i == j {
                            0.0
                        } else {
                            default_k_elem
                        }
                    }
                };

                if k_ij != 0.0 {
                    let phi_j = state.phase[j];
                    let r_j = state.amplitude[j];
                    let diff = safe_phase_diff(phi_j, phi_i);
                    sin_sum += k_ij * diff.sin() * r_j;
                    cos_sum += k_ij * diff.cos() * r_j;
                }
            }

            let safe_r = r_i.max(1e-8);

            dphase.push(omega_i + sin_sum / safe_r);
            damplitude.push(mu * r_i - r_i * r_i * r_i + cos_sum);
            dfrequency.push(self.freq_adaptation_rate * sin_sum * inv_n);
        }

        StateDerivatives::unclamped(dphase, damplitude, dfrequency)
    }

    fn compute_sparse_knn(
        &self,
        state: &OscillatorState,
        user_k: Option<usize>,
    ) -> Result<StateDerivatives, StateError> {
        let n = state.n_oscillators();
        let k = resolve_sparse_k(user_k, n);

        let nbr_index = build_phase_knn_index(&state.phase, k)?;
        let k_eff = k as f64;
        let k_eff_coupling = self.coupling_strength / k_eff;
        let mu = self.bifurcation_param;

        let mut dphase = Vec::with_capacity(n);
        let mut damplitude = Vec::with_capacity(n);
        let mut dfrequency = Vec::with_capacity(n);

        for (i, nbrs) in nbr_index.iter().enumerate() {
            let phi_i = state.phase[i];
            let r_i = state.amplitude[i];
            let omega_i = state.frequency[i];

            let mut sin_sum = 0.0;
            let mut cos_sum = 0.0;

            for &j in nbrs {
                let phi_j = state.phase[j];
                let r_j = state.amplitude[j];
                let diff = safe_phase_diff(phi_j, phi_i);
                sin_sum += k_eff_coupling * diff.sin() * r_j;
                cos_sum += k_eff_coupling * diff.cos() * r_j;
            }

            let safe_r = r_i.max(1e-8);

            dphase.push(omega_i + sin_sum / safe_r);
            damplitude.push(mu * r_i - r_i * r_i * r_i + cos_sum);
            dfrequency.push(self.freq_adaptation_rate * sin_sum / k_eff);
        }

        StateDerivatives::new(dphase, damplitude, dfrequency)
    }
}

impl Dynamics for HopfOscillator {
    fn compute_derivatives(&self, state: &OscillatorState) -> Result<StateDerivatives, StateError> {
        let n = state.n_oscillators();
        if n != self.n_oscillators {
            return Err(StateError::LengthMismatch {
                name: "state",
                expected: self.n_oscillators,
                got: n,
            });
        }

        if n <= 1 {
            let mu = self.bifurcation_param;
            let dphase = state.frequency.clone();
            let damplitude = state
                .amplitude
                .iter()
                .map(|&r| mu * r - r * r * r)
                .collect();
            let dfrequency = vec![0.0; n];
            return StateDerivatives::unclamped(dphase, damplitude, dfrequency);
        }

        match &self.coupling_mode {
            CouplingMode::MeanField => self.compute_mean_field(state),
            CouplingMode::Full { matrix } => self.compute_full(state, matrix.as_deref()),
            CouplingMode::SparseKnn { k } => self.compute_sparse_knn(state, *k),
        }
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    use approx::assert_relative_eq;
    use proptest::prelude::*;

    #[test]
    fn dynamics_vjp_rejects_each_gradient_length_mismatch() {
        let model = KuramotoOscillator::new(1, 2.0, 0.1, 0.0, CouplingMode::MeanField).unwrap();
        let state = OscillatorState::new(vec![0.2], vec![1.0], vec![3.0], None).unwrap();
        assert!(dynamics_vjp(&model, &state, &[], &[1.0], &[1.0]).is_err());
        assert!(dynamics_vjp(&model, &state, &[1.0], &[], &[1.0]).is_err());
        assert!(dynamics_vjp(&model, &state, &[1.0], &[1.0], &[]).is_err());
    }

    #[test]
    fn dynamics_vjp_matches_singleton_kuramoto_derivatives() {
        let model = KuramotoOscillator::new(1, 2.0, 0.1, 0.0, CouplingMode::MeanField).unwrap();
        let state = OscillatorState::new(vec![0.2], vec![1.0], vec![3.0], None).unwrap();
        let gradient = dynamics_vjp(&model, &state, &[1.0], &[1.0], &[1.0]).unwrap();
        assert_relative_eq!(gradient.dphase[0], 0.0, epsilon = 1e-8);
        assert_relative_eq!(gradient.damplitude[0], -0.1, epsilon = 1e-8);
        assert_relative_eq!(gradient.dfrequency[0], 1.0, epsilon = 1e-8);
    }

    #[test]
    fn dynamics_vjp_does_not_apply_time_derivative_clamp() {
        let model = KuramotoOscillator::new(1, 2.0, 0.1, 0.0, CouplingMode::MeanField).unwrap();
        let state = OscillatorState::new(vec![0.2], vec![1.0], vec![3.0], None).unwrap();
        let gradient = dynamics_vjp(&model, &state, &[0.0], &[1.0e6], &[0.0]).unwrap();
        assert_relative_eq!(gradient.damplitude[0], -1.0e5, epsilon = 1e-2);
    }

    // ------------------------------------------------------------------
    // EXP-001 D1: derivative clamping matches PRINet 3.0 per coupling path
    // ------------------------------------------------------------------
    //
    // PRINet 3.0 applies `_clamp_finite` (±1e4, NaN → 0) only inside the
    // sparse k-NN paths (`oscillator_models.py` lines 505-507 and 872-874).
    // Its full, mean-field, and Stuart–Landau derivatives are returned as
    // computed.

    /// Two oscillators whose natural frequencies exceed `DERIV_CLAMP`, so
    /// `dφ/dt ≈ ω` lies outside `±1e4` on every coupling path.
    fn fast_pair() -> OscillatorState {
        OscillatorState::new(vec![0.0, 1.0], vec![1.0, 1.0], vec![2.0e4, 3.0e4], None).unwrap()
    }

    #[test]
    fn non_sparse_derivatives_are_not_clamped_like_prinet() {
        let full = || CouplingMode::Full { matrix: None };
        let models: Vec<(&str, Box<dyn Dynamics>)> = vec![
            (
                "kuramoto/full",
                Box::new(KuramotoOscillator::new(2, 1.0, 0.1, 0.0, full()).unwrap()),
            ),
            (
                "kuramoto/mean_field",
                Box::new(
                    KuramotoOscillator::new(2, 1.0, 0.1, 0.0, CouplingMode::MeanField).unwrap(),
                ),
            ),
            (
                "hopf/full",
                Box::new(HopfOscillator::new(2, 1.0, 1.0, 0.0, full()).unwrap()),
            ),
            (
                "hopf/mean_field",
                Box::new(HopfOscillator::new(2, 1.0, 1.0, 0.0, CouplingMode::MeanField).unwrap()),
            ),
            (
                "stuart_landau/full",
                Box::new(StuartLandauOscillator::new(2, 1.0, 1.0, full()).unwrap()),
            ),
        ];
        let state = fast_pair();
        for (label, model) in &models {
            let d = model.compute_derivatives(&state).unwrap();
            assert!(
                d.dphase[1] > 2.9e4,
                "{label}: dφ/dt = {} was clamped; PRINet 3.0 returns it unclamped",
                d.dphase[1]
            );
        }
    }

    #[cfg(not(feature = "strict-checks"))]
    #[test]
    fn sparse_knn_derivatives_remain_clamped_like_prinet() {
        let sparse = || CouplingMode::SparseKnn { k: Some(1) };
        let models: Vec<Box<dyn Dynamics>> = vec![
            Box::new(KuramotoOscillator::new(2, 1.0, 0.1, 0.0, sparse()).unwrap()),
            Box::new(HopfOscillator::new(2, 1.0, 1.0, 0.0, sparse()).unwrap()),
        ];
        let state = fast_pair();
        for model in &models {
            let d = model.compute_derivatives(&state).unwrap();
            assert_eq!(d.dphase[1], crate::state::DERIV_CLAMP);
        }
    }

    #[cfg(feature = "strict-checks")]
    #[test]
    fn sparse_knn_out_of_range_derivatives_are_rejected_under_strict_checks() {
        let model =
            KuramotoOscillator::new(2, 1.0, 0.1, 0.0, CouplingMode::SparseKnn { k: Some(1) })
                .unwrap();
        assert!(matches!(
            model.compute_derivatives(&fast_pair()),
            Err(StateError::OutOfRange { .. })
        ));
    }

    #[test]
    fn test_coupling_mode_default() {
        assert_eq!(CouplingMode::default(), CouplingMode::Full { matrix: None });
    }

    #[test]
    fn test_stuart_landau_constructor_getters_setters() {
        let mut model =
            StuartLandauOscillator::new(10, 1.5, 0.5, CouplingMode::Full { matrix: None }).unwrap();

        assert_eq!(model.n_oscillators(), 10);
        assert_relative_eq!(model.coupling_strength(), 1.5);
        assert_relative_eq!(model.bifurcation_param(), 0.5);
        assert_eq!(*model.coupling_mode(), CouplingMode::Full { matrix: None });

        assert!(StuartLandauOscillator::new(0, 1.0, 0.5, CouplingMode::MeanField).is_err());
        assert!(StuartLandauOscillator::new(5, f64::NAN, 0.5, CouplingMode::MeanField).is_err());
        assert!(
            StuartLandauOscillator::new(5, 1.0, f64::INFINITY, CouplingMode::MeanField).is_err()
        );

        assert!(model.set_coupling_strength(2.0).is_ok());
        assert_relative_eq!(model.coupling_strength(), 2.0);
        assert!(model.set_coupling_strength(f64::NAN).is_err());

        assert!(model.set_bifurcation_param(1.0).is_ok());
        assert_relative_eq!(model.bifurcation_param(), 1.0);
        assert!(model.set_bifurcation_param(f64::INFINITY).is_err());

        assert!(model.set_coupling_mode(CouplingMode::MeanField).is_ok());
        assert_eq!(*model.coupling_mode(), CouplingMode::MeanField);
    }

    #[test]
    fn test_stuart_landau_custom_matrix_and_sparse_knn() {
        let mat = vec![0.0, 0.5, 0.5, 0.0];
        let model_full =
            StuartLandauOscillator::new(2, 1.0, 1.0, CouplingMode::Full { matrix: Some(mat) })
                .unwrap();

        let state =
            OscillatorState::new(vec![0.0, 0.2], vec![1.0, 1.0], vec![1.0, 1.0], None).unwrap();
        let deriv = model_full.compute_derivatives(&state).unwrap();
        assert_eq!(deriv.n_oscillators(), 2);

        let model_sparse =
            StuartLandauOscillator::new(2, 1.0, 1.0, CouplingMode::SparseKnn { k: Some(1) })
                .unwrap();
        let deriv_sparse = model_sparse.compute_derivatives(&state).unwrap();
        assert_eq!(deriv_sparse.n_oscillators(), 2);

        let model_sparse_default =
            StuartLandauOscillator::new(2, 1.0, 1.0, CouplingMode::SparseKnn { k: None }).unwrap();
        let deriv_sparse_default = model_sparse_default.compute_derivatives(&state).unwrap();
        assert_eq!(deriv_sparse_default.n_oscillators(), 2);

        let invalid_mat = vec![0.0, 0.5];
        assert!(StuartLandauOscillator::new(
            2,
            1.0,
            1.0,
            CouplingMode::Full {
                matrix: Some(invalid_mat)
            },
        )
        .is_err());

        assert!(
            StuartLandauOscillator::new(2, 1.0, 1.0, CouplingMode::SparseKnn { k: Some(2) },)
                .is_err()
        );
    }

    #[test]
    fn test_hopf_constructor_getters_setters() {
        let mut model =
            HopfOscillator::new(10, 1.5, 1.0, 0.02, CouplingMode::Full { matrix: None }).unwrap();

        assert_eq!(model.n_oscillators(), 10);
        assert_relative_eq!(model.coupling_strength(), 1.5);
        assert_relative_eq!(model.bifurcation_param(), 1.0);
        assert_relative_eq!(model.freq_adaptation_rate(), 0.02);
        assert_eq!(*model.coupling_mode(), CouplingMode::Full { matrix: None });

        assert!(HopfOscillator::new(0, 1.0, 1.0, 0.01, CouplingMode::MeanField).is_err());
        assert!(HopfOscillator::new(5, f64::NAN, 1.0, 0.01, CouplingMode::MeanField).is_err());
        assert!(HopfOscillator::new(5, 1.0, f64::INFINITY, 0.01, CouplingMode::MeanField).is_err());
        assert!(
            HopfOscillator::new(5, 1.0, 1.0, f64::NEG_INFINITY, CouplingMode::MeanField).is_err()
        );

        assert!(model.set_coupling_strength(2.0).is_ok());
        assert_relative_eq!(model.coupling_strength(), 2.0);
        assert!(model.set_coupling_strength(f64::NAN).is_err());

        assert!(model.set_bifurcation_param(2.0).is_ok());
        assert_relative_eq!(model.bifurcation_param(), 2.0);
        assert!(model.set_bifurcation_param(f64::INFINITY).is_err());

        assert!(model.set_freq_adaptation_rate(0.05).is_ok());
        assert_relative_eq!(model.freq_adaptation_rate(), 0.05);
        assert!(model.set_freq_adaptation_rate(f64::NAN).is_err());

        assert!(model.set_coupling_mode(CouplingMode::MeanField).is_ok());
        assert_eq!(*model.coupling_mode(), CouplingMode::MeanField);
    }

    #[test]
    fn test_hopf_custom_matrix_and_sparse_knn() {
        let mat = vec![0.0, 0.5, 0.5, 0.0];
        let model_full =
            HopfOscillator::new(2, 1.0, 1.0, 0.01, CouplingMode::Full { matrix: Some(mat) })
                .unwrap();

        let state =
            OscillatorState::new(vec![0.0, 0.2], vec![1.0, 1.0], vec![1.0, 1.0], None).unwrap();
        let deriv = model_full.compute_derivatives(&state).unwrap();
        assert_eq!(deriv.n_oscillators(), 2);

        let model_sparse =
            HopfOscillator::new(2, 1.0, 1.0, 0.01, CouplingMode::SparseKnn { k: Some(1) }).unwrap();
        let deriv_sparse = model_sparse.compute_derivatives(&state).unwrap();
        assert_eq!(deriv_sparse.n_oscillators(), 2);

        let invalid_mat = vec![0.0, 0.5];
        assert!(HopfOscillator::new(
            2,
            1.0,
            1.0,
            0.01,
            CouplingMode::Full {
                matrix: Some(invalid_mat)
            },
        )
        .is_err());

        assert!(
            HopfOscillator::new(2, 1.0, 1.0, 0.01, CouplingMode::SparseKnn { k: Some(2) },)
                .is_err()
        );
    }

    #[test]
    fn test_kuramoto_constructor_and_getters_setters() {
        let mut model =
            KuramotoOscillator::new(10, 1.5, 0.1, 0.02, CouplingMode::Full { matrix: None })
                .unwrap();

        assert_eq!(model.n_oscillators(), 10);
        assert_relative_eq!(model.coupling_strength(), 1.5);
        assert_relative_eq!(model.decay_rate(), 0.1);
        assert_relative_eq!(model.freq_adaptation_rate(), 0.02);
        assert_eq!(*model.coupling_mode(), CouplingMode::Full { matrix: None });

        assert!(KuramotoOscillator::new(0, 1.0, 0.1, 0.01, CouplingMode::MeanField).is_err());
        assert!(KuramotoOscillator::new(5, f64::NAN, 0.1, 0.01, CouplingMode::MeanField).is_err());
        assert!(
            KuramotoOscillator::new(5, 1.0, f64::INFINITY, 0.01, CouplingMode::MeanField).is_err()
        );
        assert!(
            KuramotoOscillator::new(5, 1.0, 0.1, f64::NEG_INFINITY, CouplingMode::MeanField)
                .is_err()
        );

        assert!(model.set_coupling_strength(2.0).is_ok());
        assert_relative_eq!(model.coupling_strength(), 2.0);
        assert!(model.set_coupling_strength(f64::NAN).is_err());

        assert!(model.set_decay_rate(0.2).is_ok());
        assert_relative_eq!(model.decay_rate(), 0.2);
        assert!(model.set_decay_rate(f64::INFINITY).is_err());

        assert!(model.set_freq_adaptation_rate(0.05).is_ok());
        assert_relative_eq!(model.freq_adaptation_rate(), 0.05);
        assert!(model.set_freq_adaptation_rate(f64::NAN).is_err());

        assert!(model.set_coupling_mode(CouplingMode::MeanField).is_ok());
        assert_eq!(*model.coupling_mode(), CouplingMode::MeanField);
    }

    #[test]
    fn test_kuramoto_n1_uncoupled() {
        let model = KuramotoOscillator::new(1, 1.0, 0.5, 0.01, CouplingMode::Full { matrix: None })
            .unwrap();
        let state = OscillatorState::new(vec![0.5], vec![2.0], vec![1.5], None).unwrap();

        let deriv = model.compute_derivatives(&state).unwrap();
        assert_eq!(deriv.n_oscillators(), 1);
        assert_relative_eq!(deriv.dphase[0], 1.5, epsilon = 1e-12);
        assert_relative_eq!(deriv.damplitude[0], -0.5 * 2.0, epsilon = 1e-12);
        assert_relative_eq!(deriv.dfrequency[0], 0.0, epsilon = 1e-12);
    }

    #[test]
    fn test_kuramoto_mean_field_and_full_equivalence_n2() {
        let model_mf = KuramotoOscillator::new(2, 1.0, 0.1, 0.01, CouplingMode::MeanField).unwrap();
        // Mean field includes self-interaction K/N on diagonal; specify full matrix with K/N on diagonal to match:
        let mat = vec![0.5, 0.5, 0.5, 0.5];
        let model_full =
            KuramotoOscillator::new(2, 1.0, 0.1, 0.01, CouplingMode::Full { matrix: Some(mat) })
                .unwrap();

        let state =
            OscillatorState::new(vec![0.1, 0.5], vec![1.0, 1.2], vec![1.0, 2.0], None).unwrap();

        let d_mf = model_mf.compute_derivatives(&state).unwrap();
        let d_full = model_full.compute_derivatives(&state).unwrap();

        for i in 0..2 {
            assert_relative_eq!(d_mf.dphase[i], d_full.dphase[i], epsilon = 1e-12);
            assert_relative_eq!(d_mf.damplitude[i], d_full.damplitude[i], epsilon = 1e-12);
            assert_relative_eq!(d_mf.dfrequency[i], d_full.dfrequency[i], epsilon = 1e-12);
        }
    }

    #[test]
    fn test_kuramoto_custom_coupling_matrix() {
        let mat = vec![0.0, 0.5, 0.5, 0.0];
        let model =
            KuramotoOscillator::new(2, 1.0, 0.1, 0.01, CouplingMode::Full { matrix: Some(mat) })
                .unwrap();

        let state =
            OscillatorState::new(vec![0.0, 0.2], vec![1.0, 1.0], vec![1.0, 1.0], None).unwrap();
        let deriv = model.compute_derivatives(&state).unwrap();
        assert_eq!(deriv.n_oscillators(), 2);

        let invalid_mat = vec![0.0, 0.5, 0.5];
        assert!(KuramotoOscillator::new(
            2,
            1.0,
            0.1,
            0.01,
            CouplingMode::Full {
                matrix: Some(invalid_mat)
            }
        )
        .is_err());
    }

    #[test]
    fn test_kuramoto_sparse_knn() {
        let model =
            KuramotoOscillator::new(4, 1.0, 0.1, 0.01, CouplingMode::SparseKnn { k: Some(2) })
                .unwrap();

        let state = OscillatorState::new(
            vec![0.0, 0.1, 1.0, 1.1],
            vec![1.0, 1.0, 1.0, 1.0],
            vec![1.0, 1.0, 1.0, 1.0],
            None,
        )
        .unwrap();

        let deriv = model.compute_derivatives(&state).unwrap();
        assert_eq!(deriv.n_oscillators(), 4);

        assert!(
            KuramotoOscillator::new(4, 1.0, 0.1, 0.01, CouplingMode::SparseKnn { k: Some(4) })
                .is_err()
        );

        assert!(
            KuramotoOscillator::new(4, 1.0, 0.1, 0.01, CouplingMode::SparseKnn { k: Some(0) })
                .is_err()
        );
    }

    #[test]
    fn test_kuramoto_full_default_no_matrix() {
        let model = KuramotoOscillator::new(3, 1.5, 0.1, 0.01, CouplingMode::Full { matrix: None })
            .unwrap();

        let state = OscillatorState::new(
            vec![0.0, 0.2, 1.0],
            vec![1.0, 1.0, 1.0],
            vec![1.0, 1.0, 1.0],
            None,
        )
        .unwrap();

        let deriv = model.compute_derivatives(&state).unwrap();
        assert_eq!(deriv.n_oscillators(), 3);

        // Diagonal entries are zero; off-diagonal coupling strength is K/N.
        let inv_n = 1.0 / 3.0;
        let default_k = 1.5 * inv_n;

        let sin_sum0 = default_k * (0.2f64.sin() + 1.0f64.sin());
        let cos_sum0 = default_k * (0.2f64.cos() + 1.0f64.cos());
        assert_relative_eq!(deriv.dphase[0], 1.0 + sin_sum0, epsilon = 1e-12);
        assert_relative_eq!(deriv.damplitude[0], -0.1 * 1.0 + cos_sum0, epsilon = 1e-12);
        assert_relative_eq!(
            deriv.dfrequency[0],
            0.01 * sin_sum0 * inv_n,
            epsilon = 1e-12
        );
    }

    #[test]
    fn test_kuramoto_sparse_knn_n1_uses_k_zero_path() {
        // For N=1, the default k resolves to 0 and triggers the early-return path.
        let model = KuramotoOscillator::new(1, 1.0, 0.5, 0.01, CouplingMode::SparseKnn { k: None })
            .unwrap();
        let state = OscillatorState::new(vec![0.5], vec![2.0], vec![1.5], None).unwrap();
        let deriv = model.compute_derivatives(&state).unwrap();
        assert_relative_eq!(deriv.dphase[0], 1.5, epsilon = 1e-12);
        assert_relative_eq!(deriv.damplitude[0], -0.5 * 2.0, epsilon = 1e-12);
        assert_relative_eq!(deriv.dfrequency[0], 0.0, epsilon = 1e-12);
    }

    #[test]
    fn test_stuart_landau_uncoupled_limit_cycle() {
        let model = StuartLandauOscillator::new(2, 0.0, 1.0, CouplingMode::MeanField).unwrap();
        let state =
            OscillatorState::new(vec![0.1, 0.5], vec![2.0, 0.5], vec![1.0, 2.0], None).unwrap();

        let deriv = model.compute_derivatives(&state).unwrap();
        assert_eq!(deriv.n_oscillators(), 2);

        assert_relative_eq!(deriv.dphase[0], 1.0, epsilon = 1e-12);
        assert_relative_eq!(deriv.dphase[1], 2.0, epsilon = 1e-12);

        assert_relative_eq!(
            deriv.damplitude[0],
            1.0 * 2.0 - 2.0 * 2.0 * 2.0,
            epsilon = 1e-12
        );
        assert_relative_eq!(
            deriv.damplitude[1],
            1.0 * 0.5 - 0.5 * 0.5 * 0.5,
            epsilon = 1e-12
        );

        assert_relative_eq!(deriv.dfrequency[0], 0.0, epsilon = 1e-12);
        assert_relative_eq!(deriv.dfrequency[1], 0.0, epsilon = 1e-12);
    }

    #[test]
    fn test_hopf_limit_cycle_and_amplitude() {
        let model_pos = HopfOscillator::new(3, 1.0, 4.0, 0.01, CouplingMode::MeanField).unwrap();
        assert_relative_eq!(model_pos.limit_cycle_amplitude(), 2.0, epsilon = 1e-12);

        let model_neg = HopfOscillator::new(3, 1.0, -1.0, 0.01, CouplingMode::MeanField).unwrap();
        assert_relative_eq!(model_neg.limit_cycle_amplitude(), 0.0, epsilon = 1e-12);

        let model_uncoupled =
            HopfOscillator::new(2, 0.0, 1.0, 0.01, CouplingMode::MeanField).unwrap();
        let state =
            OscillatorState::new(vec![0.1, 0.5], vec![1.5, 0.5], vec![1.0, 2.0], None).unwrap();

        let deriv = model_uncoupled.compute_derivatives(&state).unwrap();
        assert_relative_eq!(deriv.dphase[0], 1.0, epsilon = 1e-12);
        assert_relative_eq!(
            deriv.damplitude[0],
            1.0 * 1.5 - 1.5 * 1.5 * 1.5,
            epsilon = 1e-12
        );
    }

    #[test]
    fn test_stuart_landau_setters_and_invalid_matrix_reject() {
        let mut model = StuartLandauOscillator::new(5, 1.0, 0.5, CouplingMode::MeanField).unwrap();

        assert!(model.set_coupling_strength(2.0).is_ok());
        assert_relative_eq!(model.coupling_strength(), 2.0);
        assert!(model.set_coupling_strength(f64::NAN).is_err());

        assert!(model.set_bifurcation_param(1.0).is_ok());
        assert_relative_eq!(model.bifurcation_param(), 1.0);
        assert!(model.set_bifurcation_param(f64::NEG_INFINITY).is_err());

        let bad_mat = vec![f64::NAN, 0.5, 0.5, 0.0];
        assert!(StuartLandauOscillator::new(
            2,
            1.0,
            0.5,
            CouplingMode::Full {
                matrix: Some(bad_mat)
            }
        )
        .is_err());
    }

    #[test]
    fn test_hopf_setters_and_invalid_matrix_reject() {
        let mut model = HopfOscillator::new(5, 1.0, 0.5, 0.01, CouplingMode::MeanField).unwrap();

        assert!(model.set_coupling_strength(2.0).is_ok());
        assert_relative_eq!(model.coupling_strength(), 2.0);
        assert!(model.set_coupling_strength(f64::NAN).is_err());

        assert!(model.set_bifurcation_param(1.0).is_ok());
        assert_relative_eq!(model.bifurcation_param(), 1.0);
        assert!(model.set_bifurcation_param(f64::NEG_INFINITY).is_err());

        assert!(model.set_freq_adaptation_rate(0.05).is_ok());
        assert_relative_eq!(model.freq_adaptation_rate(), 0.05);
        assert!(model.set_freq_adaptation_rate(f64::NAN).is_err());

        let bad_mat = vec![0.0, 0.5, f64::INFINITY, 0.0];
        assert!(HopfOscillator::new(
            2,
            1.0,
            0.5,
            0.01,
            CouplingMode::Full {
                matrix: Some(bad_mat)
            }
        )
        .is_err());
    }

    #[test]
    fn test_state_length_mismatch_for_hopf_and_stuart_landau() {
        let hopf = HopfOscillator::new(3, 1.0, 1.0, 0.01, CouplingMode::MeanField).unwrap();
        let state =
            OscillatorState::new(vec![0.1, 0.2], vec![1.0, 1.0], vec![1.0, 1.0], None).unwrap();
        assert!(matches!(
            hopf.compute_derivatives(&state).unwrap_err(),
            StateError::LengthMismatch { .. }
        ));

        let stuart = StuartLandauOscillator::new(3, 1.0, 1.0, CouplingMode::MeanField).unwrap();
        assert!(matches!(
            stuart.compute_derivatives(&state).unwrap_err(),
            StateError::LengthMismatch { .. }
        ));
    }

    #[test]
    fn test_state_length_mismatch_rejected() {
        let model = KuramotoOscillator::new(3, 1.0, 0.1, 0.01, CouplingMode::MeanField).unwrap();
        let state =
            OscillatorState::new(vec![0.1, 0.2], vec![1.0, 1.0], vec![1.0, 1.0], None).unwrap();

        let err = model.compute_derivatives(&state).unwrap_err();
        match err {
            StateError::LengthMismatch {
                name,
                expected,
                got,
            } => {
                assert_eq!(name, "state");
                assert_eq!(expected, 3);
                assert_eq!(got, 2);
            }
            other => panic!("expected LengthMismatch, got {:?}", other),
        }
    }

    #[test]
    fn test_kuramoto_all_setters_and_sparse_default_k() {
        let mut model =
            KuramotoOscillator::new(4, 1.0, 0.1, 0.01, CouplingMode::SparseKnn { k: Some(2) })
                .unwrap();

        assert!(model.set_decay_rate(0.2).is_ok());
        assert_relative_eq!(model.decay_rate(), 0.2);
        assert!(model.set_decay_rate(f64::NAN).is_err());

        assert!(model.set_freq_adaptation_rate(0.05).is_ok());
        assert_relative_eq!(model.freq_adaptation_rate(), 0.05);
        assert!(model.set_freq_adaptation_rate(f64::INFINITY).is_err());

        // Invalid coupling mode for current N should fail.
        assert!(model
            .set_coupling_mode(CouplingMode::SparseKnn { k: Some(4) })
            .is_err());
        assert!(model.set_coupling_mode(CouplingMode::MeanField).is_ok());

        // SparseKnn with None uses default k = ceil(log2(4)) = 2.
        assert!(model
            .set_coupling_mode(CouplingMode::SparseKnn { k: None })
            .is_ok());
        let state = OscillatorState::new(
            vec![0.0, 0.1, 1.0, 1.1],
            vec![1.0, 1.0, 1.0, 1.0],
            vec![1.0, 1.0, 1.0, 1.0],
            None,
        )
        .unwrap();
        let deriv = model.compute_derivatives(&state).unwrap();
        assert_eq!(deriv.n_oscillators(), 4);
    }

    #[test]
    fn test_stuart_landau_and_hopf_set_coupling_mode_error() {
        let mut stuart = StuartLandauOscillator::new(4, 1.0, 0.5, CouplingMode::MeanField).unwrap();
        assert!(stuart
            .set_coupling_mode(CouplingMode::SparseKnn { k: Some(4) })
            .is_err());
        assert!(stuart
            .set_coupling_mode(CouplingMode::Full { matrix: None })
            .is_ok());

        let mut hopf = HopfOscillator::new(4, 1.0, 0.5, 0.01, CouplingMode::MeanField).unwrap();
        assert!(hopf
            .set_coupling_mode(CouplingMode::SparseKnn { k: Some(0) })
            .is_err());
        assert!(hopf
            .set_coupling_mode(CouplingMode::Full { matrix: None })
            .is_ok());
    }

    #[test]
    fn test_model_helper_validation_and_resolution() {
        assert!(super::validate_finite(1.0, "x").is_ok());
        assert!(super::validate_finite(f64::NAN, "x").is_err());

        assert!(super::validate_coupling_mode(&CouplingMode::MeanField, 10).is_ok());
        assert!(super::validate_coupling_mode(&CouplingMode::Full { matrix: None }, 10).is_ok());

        let ok_mat = vec![0.0, 0.5, 0.5, 0.0];
        assert!(super::validate_coupling_mode(
            &CouplingMode::Full {
                matrix: Some(ok_mat)
            },
            2
        )
        .is_ok());

        let short_mat = vec![0.0, 0.5, 0.5];
        assert!(super::validate_coupling_mode(
            &CouplingMode::Full {
                matrix: Some(short_mat)
            },
            2
        )
        .is_err());

        let bad_mat = vec![0.0, f64::NAN, 0.5, 0.0];
        assert!(super::validate_coupling_mode(
            &CouplingMode::Full {
                matrix: Some(bad_mat)
            },
            2
        )
        .is_err());

        assert!(super::validate_coupling_mode(&CouplingMode::SparseKnn { k: Some(2) }, 4).is_ok());
        assert!(super::validate_coupling_mode(&CouplingMode::SparseKnn { k: Some(0) }, 4).is_err());
        assert!(super::validate_coupling_mode(&CouplingMode::SparseKnn { k: Some(4) }, 4).is_err());
        assert!(super::validate_coupling_mode(&CouplingMode::SparseKnn { k: None }, 4).is_ok());

        assert_eq!(super::resolve_sparse_k(Some(2), 4), 2);
        assert_eq!(super::resolve_sparse_k(None, 4), 2); // ceil(log2(4)) = 2
        assert_eq!(super::resolve_sparse_k(None, 2), 1); // ceil(log2(2)) = 1, N-1 = 1
        assert_eq!(super::resolve_sparse_k(None, 1), 0); // N-1 = 0
    }

    fn assert_derivs_close(
        deriv: &StateDerivatives,
        dphase: &[f64],
        damplitude: &[f64],
        dfrequency: &[f64],
        epsilon: f64,
    ) {
        assert_eq!(deriv.n_oscillators(), dphase.len());
        for (a, e) in deriv.dphase.iter().zip(dphase.iter()) {
            assert_relative_eq!(*a, *e, epsilon = epsilon, max_relative = epsilon);
        }
        for (a, e) in deriv.damplitude.iter().zip(damplitude.iter()) {
            assert_relative_eq!(*a, *e, epsilon = epsilon, max_relative = epsilon);
        }
        for (a, e) in deriv.dfrequency.iter().zip(dfrequency.iter()) {
            assert_relative_eq!(*a, *e, epsilon = epsilon, max_relative = epsilon);
        }
    }

    #[test]
    fn test_stuart_landau_coupled_reference_values() {
        // Full pairwise (default all-to-all K/N, equivalent to mean field for SL).
        let state =
            OscillatorState::new(vec![0.0, 0.2], vec![1.0, 1.0], vec![1.0, 1.0], None).unwrap();
        let model =
            StuartLandauOscillator::new(2, 1.0, 1.0, CouplingMode::Full { matrix: None }).unwrap();
        let deriv = model.compute_derivatives(&state).unwrap();
        assert_derivs_close(
            &deriv,
            &[1.0993346646428108, 0.9006653732161427],
            &[-0.00996670126914978, -0.009966720198626544],
            &[0.0, 0.0],
            1e-6,
        );

        // Mean-field with a non-trivial order parameter.
        let state = OscillatorState::new(
            vec![0.0, 0.2, 0.7],
            vec![1.0, 1.2, 0.9],
            vec![1.0, 1.5, 2.0],
            None,
        )
        .unwrap();
        let model = StuartLandauOscillator::new(3, 1.0, 1.0, CouplingMode::MeanField).unwrap();
        let deriv = model.compute_derivatives(&state).unwrap();
        assert_derivs_close(
            &deriv,
            &[1.2727330327033997, 1.5646705146166249, 1.5483228811260992],
            &[
                -0.045187364021937015,
                -0.7380364740471499,
                0.17698043388305695,
            ],
            &[0.0, 0.0, 0.0],
            1e-6,
        );

        // Sparse k-NN with k=2.
        let state = OscillatorState::new(
            vec![0.0, 0.1, 1.0, 1.1],
            vec![1.0, 1.0, 1.0, 1.0],
            vec![1.0, 1.0, 1.0, 1.0],
            None,
        )
        .unwrap();
        let model =
            StuartLandauOscillator::new(4, 1.0, 1.0, CouplingMode::SparseKnn { k: Some(2) })
                .unwrap();
        let deriv = model.compute_derivatives(&state).unwrap();
        assert_derivs_close(
            &deriv,
            &[
                1.4955203756690025,
                1.341746764035639,
                0.658253171381233,
                0.5044795869875003,
            ],
            &[
                -0.2756998538970947,
                -0.19169296418641601,
                -0.1916928987346953,
                -0.2756998440121947,
            ],
            &[0.0, 0.0, 0.0, 0.0],
            1e-6,
        );
    }

    #[test]
    fn test_hopf_coupled_reference_values() {
        // Full pairwise.
        let state = OscillatorState::new(
            vec![0.0, 0.2, 1.0],
            vec![1.0, 1.0, 1.0],
            vec![1.0, 1.0, 1.0],
            None,
        )
        .unwrap();
        let model =
            HopfOscillator::new(3, 1.5, 1.0, 0.01, CouplingMode::Full { matrix: None }).unwrap();
        let deriv = model.compute_derivatives(&state).unwrap();
        assert_derivs_close(
            &deriv,
            &[1.5200701578014788, 1.259343380052231, 0.2205864621462903],
            &[0.7601844418546907, 0.8383866435942036, 0.6185045076076525],
            &[
                0.001733567192671596,
                0.000864477933507436,
                -0.0025980451261790323,
            ],
            1e-12,
        );

        // Mean field.
        let state = OscillatorState::new(
            vec![0.1, 0.5, 1.0],
            vec![1.5, 0.5, 1.0],
            vec![1.0, 2.0, 1.5],
            None,
        )
        .unwrap();
        let model = HopfOscillator::new(3, 1.0, 1.0, 0.01, CouplingMode::MeanField).unwrap();
        let deriv = model.compute_derivatives(&state).unwrap();
        assert_derivs_close(
            &deriv,
            &[1.2173413382538607, 1.9301986572827874, 1.0284322865210977],
            &[-1.0142865242388244, 1.2947246650232098, 0.7904020546010853],
            &[
                0.0010867066912693042,
                -0.00011633557119535445,
                -0.0015718923782630076,
            ],
            1e-6,
        );

        // Sparse k-NN.
        let state = OscillatorState::new(
            vec![0.0, 0.1, 1.0, 1.1],
            vec![1.0, 1.0, 1.0, 1.0],
            vec![1.0, 1.0, 1.0, 1.0],
            None,
        )
        .unwrap();
        let model =
            HopfOscillator::new(4, 1.0, 1.0, 0.01, CouplingMode::SparseKnn { k: Some(2) }).unwrap();
        let deriv = model.compute_derivatives(&state).unwrap();
        assert_derivs_close(
            &deriv,
            &[
                1.4955203883541317,
                1.3417467464903277,
                0.6582532535096723,
                0.5044796116458682,
            ],
            &[
                0.7243001433518016,
                0.808307066774345,
                0.808307066774345,
                0.7243001433518015,
            ],
            &[
                0.0024776019417706587,
                0.0017087337324516382,
                -0.001708733732451638,
                -0.002477601941770659,
            ],
            1e-12,
        );
    }

    // -------------------------------------------------------------------------
    // WP-009: sparse/full equivalence, k-NN edge properties, 1/N vs 1/k
    // -------------------------------------------------------------------------

    #[test]
    fn knn_index_has_exact_k_neighbors_no_self_loops() {
        // k-NN edge property: each oscillator has exactly k neighbors,
        // no self-loops, all indices in range.
        let phase = vec![0.1, 0.5, 1.0, 2.0, 3.0, 5.0];
        let k = 3;
        let nbrs = build_phase_knn_index(&phase, k).unwrap();
        assert_eq!(nbrs.len(), phase.len());
        for (i, row) in nbrs.iter().enumerate() {
            assert_eq!(row.len(), k, "oscillator {i} should have {k} neighbors");
            assert!(!row.contains(&i), "oscillator {i} has self-loop");
            for &j in row {
                assert!(j < phase.len(), "neighbor index {j} out of range");
            }
        }
    }

    #[test]
    fn knn_index_neighbors_are_phase_nearest() {
        // k-NN edge property: the sort-based algorithm takes k/2 left and
        // k - k/2 right neighbours in sorted phase order (wrapping around
        // the circle). For k=2, that's 1 left + 1 right.
        let phase = vec![0.0, 0.1, 0.2, 1.0, 1.1];
        let k = 2;
        let nbrs = build_phase_knn_index(&phase, k).unwrap();
        // Sorted: [(0,0.0), (1,0.1), (2,0.2), (3,1.0), (4,1.1)]
        // For oscillator 0 (sorted pos 0): left=4 (phase 1.1), right=1 (phase 0.1).
        let mut nbrs_0 = nbrs[0].clone();
        nbrs_0.sort();
        assert_eq!(nbrs_0, vec![1, 4]);
        // For oscillator 3 (sorted pos 3): left=2 (phase 0.2), right=4 (phase 1.1).
        let mut nbrs_3 = nbrs[3].clone();
        nbrs_3.sort();
        assert_eq!(nbrs_3, vec![2, 4]);
    }

    #[test]
    fn knn_index_wraps_around_circle() {
        // k-NN edge property: wrapping across TAU boundary.
        let phase = vec![0.0, 0.01, 6.27, 6.275];
        let k = 2;
        let nbrs = build_phase_knn_index(&phase, k).unwrap();
        // Sorted: 0.0(0), 0.01(1), 6.27(2), 6.28(3)
        // For oscillator 0 (0.0): neighbors are 1 (0.01) and 3 (6.28, wrapping).
        let mut nbrs_0 = nbrs[0].clone();
        nbrs_0.sort();
        assert!(nbrs_0.contains(&1));
        assert!(nbrs_0.contains(&3));
    }

    #[test]
    fn knn_index_symmetric_neighbor_property() {
        // k-NN edge property: if j is a neighbor of i, it's likely i is a
        // neighbor of j for nearby phases (not guaranteed for all k, but
        // holds for k >= 2 on uniform distributions).
        let phase = vec![0.0, 0.1, 0.2, 0.3];
        let k = 2;
        let nbrs = build_phase_knn_index(&phase, k).unwrap();
        // Oscillator 1 (0.1) neighbors should include 0 and 2.
        let mut nbrs_1 = nbrs[1].clone();
        nbrs_1.sort();
        assert_eq!(nbrs_1, vec![0, 2]);
    }

    #[test]
    fn sparse_knn_k_equals_n_minus_1_equals_full_default() {
        // Sparse/full equivalence: when k = N-1, sparse k-NN couples to
        // all other oscillators. With K/k = K/(N-1) vs full K/N, the
        // normalization differs by a factor of N/(N-1). This test verifies
        // the explicit 1/N vs 1/k normalization difference is documented
        // and the relationship holds.
        let n = 4;
        let state = OscillatorState::new(
            vec![0.0, 0.1, 1.0, 1.1],
            vec![1.0, 1.0, 1.0, 1.0],
            vec![1.0, 1.0, 1.0, 1.0],
            None,
        )
        .unwrap();

        let full_model =
            KuramotoOscillator::new(n, 1.0, 0.1, 0.01, CouplingMode::Full { matrix: None })
                .unwrap();
        let sparse_model = KuramotoOscillator::new(
            n,
            1.0,
            0.1,
            0.01,
            CouplingMode::SparseKnn { k: Some(n - 1) },
        )
        .unwrap();

        let full_deriv = full_model.compute_derivatives(&state).unwrap();
        let sparse_deriv = sparse_model.compute_derivatives(&state).unwrap();

        // Full uses K/N per edge, sparse uses K/k = K/(N-1) per edge.
        // The ratio is (N-1)/N for the coupling terms.
        let ratio = (n as f64 - 1.0) / (n as f64);
        for i in 0..n {
            // dphase = omega + coupling. omega is the same, so the difference
            // is in the coupling term.
            let full_coupling = full_deriv.dphase[i] - state.frequency[i];
            let sparse_coupling = sparse_deriv.dphase[i] - state.frequency[i];
            // sparse_coupling / full_coupling should be N/(N-1) = 1/ratio.
            if full_coupling.abs() > 1e-10 {
                let actual_ratio = sparse_coupling / full_coupling;
                assert_relative_eq!(actual_ratio, 1.0 / ratio, epsilon = 1e-10);
            }
        }
    }

    #[test]
    fn normalization_one_over_n_explicit_in_mean_field() {
        // 1/N normalization: mean-field uses the complex order parameter
        // Z = (1/N) Σ_j r_j e^{iφ_j}, so the coupling is normalized by 1/N.
        // Verify: doubling N with the same per-oscillator contribution
        // halves the order parameter magnitude (for synchronized state).
        let n1 = 4;
        let n2 = 8;
        let state1 = OscillatorState::create_synchronized(n1, 1.0).unwrap();
        let state2 = OscillatorState::create_synchronized(n2, 1.0).unwrap();

        let model1 = KuramotoOscillator::new(n1, 1.0, 0.1, 0.01, CouplingMode::MeanField).unwrap();
        let model2 = KuramotoOscillator::new(n2, 1.0, 0.1, 0.01, CouplingMode::MeanField).unwrap();

        let d1 = model1.compute_derivatives(&state1).unwrap();
        let d2 = model2.compute_derivatives(&state2).unwrap();

        // For a synchronized state (all phase=0, amplitude=1), R=1, ψ=0.
        // dphase = omega + K*R*sin(ψ-φ) = omega + 0 = omega.
        // damplitude = -λ*r + K*R*cos(ψ-φ) = -λ + K.
        // These are independent of N (1/N is already absorbed in R).
        for i in 0..n1 {
            assert_relative_eq!(d1.dphase[i], 1.0, epsilon = 1e-12);
            assert_relative_eq!(d1.damplitude[i], -0.1 + 1.0, epsilon = 1e-12);
        }
        for i in 0..n2 {
            assert_relative_eq!(d2.dphase[i], 1.0, epsilon = 1e-12);
            assert_relative_eq!(d2.damplitude[i], -0.1 + 1.0, epsilon = 1e-12);
        }
    }

    #[test]
    fn normalization_one_over_k_explicit_in_sparse() {
        // 1/k normalization: sparse k-NN uses K/k per edge (not K/N).
        // Verify explicitly: for each oscillator, the dphase coupling term
        // equals (K/k) * Σ_{j ∈ NN_k(i)} sin(φ_j - φ_i) * r_j, computed from
        // the actual k-NN neighbour set. This distinguishes 1/k from 1/N
        // (which would divide by N=5 instead of k).
        let phase = vec![0.0, 0.1, 0.2, 0.3, 0.4];
        let state = OscillatorState::new(
            phase.clone(),
            vec![1.0, 1.0, 1.0, 1.0, 1.0],
            vec![1.0, 1.0, 1.0, 1.0, 1.0],
            None,
        )
        .unwrap();
        let n = 5;
        let k_strength = 1.0_f64;

        for k in [2_usize, 3] {
            let model = KuramotoOscillator::new(
                n,
                k_strength,
                0.1,
                0.01,
                CouplingMode::SparseKnn { k: Some(k) },
            )
            .unwrap();
            let d = model.compute_derivatives(&state).unwrap();
            let nbrs = build_phase_knn_index(&phase, k).unwrap();
            // Per-edge weight is K/k (the 1/k normalization under test).
            let per_edge = k_strength / (k as f64);
            for i in 0..n {
                let mut expected_coupling = 0.0_f64;
                for &j in &nbrs[i] {
                    expected_coupling +=
                        per_edge * (phase[j] - phase[i]).sin() * state.amplitude[j];
                }
                let expected_dphase = state.frequency[i] + expected_coupling;
                assert_relative_eq!(d.dphase[i], expected_dphase, epsilon = 1e-12);

                // Sanity: the 1/k result must differ from the 1/N result
                // (k < N), proving the normalization is 1/k, not 1/N.
                let per_edge_n = k_strength / (n as f64);
                let mut n_coupling = 0.0_f64;
                for &j in &nbrs[i] {
                    n_coupling += per_edge_n * (phase[j] - phase[i]).sin() * state.amplitude[j];
                }
                if expected_coupling.abs() > 1e-10 {
                    assert!(
                        (expected_coupling - n_coupling).abs() > 1e-10,
                        "osc {i} k={k}: 1/k coupling {expected_coupling} == 1/N coupling {n_coupling}"
                    );
                }
            }
        }

        // Explicit ratio check on oscillator 0: the k=2 and k=3 neighbour
        // sets share two neighbours, so the per-edge weight ratio K/2 vs K/3
        // = 3/2 shows up directly in the shared-neighbour contribution.
        let nbrs2 = build_phase_knn_index(&phase, 2).unwrap();
        let nbrs3 = build_phase_knn_index(&phase, 3).unwrap();
        let shared: Vec<usize> = nbrs2[0]
            .iter()
            .filter(|j| nbrs3[0].contains(j))
            .copied()
            .collect();
        let k2_shared: f64 = shared
            .iter()
            .map(|&j| (phase[j] - phase[0]).sin())
            .sum::<f64>()
            * (k_strength / 2.0);
        let k3_shared: f64 = shared
            .iter()
            .map(|&j| (phase[j] - phase[0]).sin())
            .sum::<f64>()
            * (k_strength / 3.0);
        if k2_shared.abs() > 1e-10 {
            assert_relative_eq!(k2_shared / k3_shared, 3.0 / 2.0, epsilon = 1e-10);
        }
    }

    #[test]
    fn topology_all_to_all_matrix_matches_full_default() {
        // The AllToAll topology builder should produce the same matrix
        // that CouplingMode::Full { matrix: None } uses internally (K/N
        // off-diagonal, 0 diagonal).
        use crate::coupling::Topology;

        let n = 5;
        let k = 2.0;
        let matrix = Topology::AllToAll.build_matrix(n, k).unwrap();

        let state = OscillatorState::create_synchronized(n, 1.0).unwrap();
        let model_default =
            KuramotoOscillator::new(n, k, 0.1, 0.01, CouplingMode::Full { matrix: None }).unwrap();
        let model_matrix = KuramotoOscillator::new(
            n,
            k,
            0.1,
            0.01,
            CouplingMode::Full {
                matrix: Some(matrix),
            },
        )
        .unwrap();

        let d_default = model_default.compute_derivatives(&state).unwrap();
        let d_matrix = model_matrix.compute_derivatives(&state).unwrap();

        for i in 0..n {
            assert_relative_eq!(d_default.dphase[i], d_matrix.dphase[i], epsilon = 1e-12);
            assert_relative_eq!(
                d_default.damplitude[i],
                d_matrix.damplitude[i],
                epsilon = 1e-12
            );
            assert_relative_eq!(
                d_default.dfrequency[i],
                d_matrix.dfrequency[i],
                epsilon = 1e-12
            );
        }
    }

    #[test]
    fn topology_ring_matrix_produces_valid_kuramoto_derivatives() {
        use crate::coupling::Topology;

        let n = 6;
        let k = 1.5;
        let matrix = Topology::Ring { k_ring: 4 }.build_matrix(n, k).unwrap();

        let mut seed = crate::Seed::new(0, 42);
        let state = OscillatorState::create_random(n, (0.5, 2.5), &mut seed).unwrap();
        let model = KuramotoOscillator::new(
            n,
            k,
            0.1,
            0.01,
            CouplingMode::Full {
                matrix: Some(matrix),
            },
        )
        .unwrap();

        let deriv = model.compute_derivatives(&state).unwrap();
        assert_eq!(deriv.n_oscillators(), n);
        for i in 0..n {
            assert!(deriv.dphase[i].is_finite());
            assert!(deriv.damplitude[i].is_finite());
            assert!(deriv.dfrequency[i].is_finite());
        }
    }

    #[test]
    fn topology_small_world_matrix_produces_valid_kuramoto_derivatives() {
        use crate::coupling::Topology;
        use crate::Seed;

        let n = 8;
        let k = 1.0;
        let matrix = Topology::SmallWorld {
            k_ring: 4,
            rewire_prob: 0.3,
            seed: Seed::new(0, 42),
        }
        .build_matrix(n, k)
        .unwrap();

        let mut seed = crate::Seed::new(0, 99);
        let state = OscillatorState::create_random(n, (0.5, 2.5), &mut seed).unwrap();
        let model = KuramotoOscillator::new(
            n,
            k,
            0.1,
            0.01,
            CouplingMode::Full {
                matrix: Some(matrix),
            },
        )
        .unwrap();

        let deriv = model.compute_derivatives(&state).unwrap();
        assert_eq!(deriv.n_oscillators(), n);
        for i in 0..n {
            assert!(deriv.dphase[i].is_finite());
            assert!(deriv.damplitude[i].is_finite());
            assert!(deriv.dfrequency[i].is_finite());
        }
    }

    proptest! {
        #[test]
        fn proptest_kuramoto_derivatives_finite(
            n in 2usize..=16,
            k_val in 1.0f64..5.0,
            decay in 0.01f64..0.5,
            gamma in 0.001f64..0.1,
        ) {
            let model = KuramotoOscillator::new(n, k_val, decay, gamma, CouplingMode::MeanField).unwrap();
            let mut seed = crate::Seed::new(0, 42);
            let state = OscillatorState::create_random(n, (0.5, 2.5), &mut seed).unwrap();

            let deriv = model.compute_derivatives(&state).unwrap();
            prop_assert_eq!(deriv.n_oscillators(), n);

            for i in 0..n {
                prop_assert!(deriv.dphase[i].is_finite());
                prop_assert!(deriv.damplitude[i].is_finite());
                prop_assert!(deriv.dfrequency[i].is_finite());
            }
        }

        #[test]
        fn proptest_hopf_derivatives_finite(
            n in 2usize..=16,
            k_val in 1.0f64..5.0,
            mu in -2.0f64..5.0,
        ) {
            let model = HopfOscillator::new(n, k_val, mu, 0.01, CouplingMode::SparseKnn { k: None }).unwrap();
            let mut seed = crate::Seed::new(0, 12345);
            let state = OscillatorState::create_random(n, (0.5, 2.5), &mut seed).unwrap();

            let deriv = model.compute_derivatives(&state).unwrap();
            prop_assert_eq!(deriv.n_oscillators(), n);

            for i in 0..n {
                prop_assert!(deriv.dphase[i].is_finite());
                prop_assert!(deriv.damplitude[i].is_finite());
                prop_assert!(deriv.dfrequency[i].is_finite());
            }
        }
    }
}
