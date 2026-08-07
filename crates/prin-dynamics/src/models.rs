//! Oscillator models behind the `Dynamics` trait.
//!
//! - [`KuramotoOscillator`]: mean-field `O(N)`, full pairwise `O(N²)`, sparse k-NN `O(N·k)`.
//! - [`StuartLandauOscillator`]: complex amplitude limit-cycle dynamics.
//! - [`HopfOscillator`]: bifurcation-driven polar coordinate dynamics.
//!
//! Coupling mode is an enum ([`CouplingMode`]), never a string.

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

        StateDerivatives::new(dphase, damplitude, dfrequency)
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

        StateDerivatives::new(dphase, damplitude, dfrequency)
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
            return StateDerivatives::new(dphase, damplitude, dfrequency);
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
/// Implements complex amplitude dynamics:
/// `dz_i/dt = (μ + i ω_i) z_i - |z_i|² z_i + C_i`
/// where `z_i = r_i exp(i φ_i)`.
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

        StateDerivatives::new(dphase, damplitude, dfrequency)
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

                StateDerivatives::new(dphase, damplitude, dfrequency)
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
            return StateDerivatives::new(dphase, damplitude, dfrequency);
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
/// - `dr_i/dt = μ r_i - r_i³ + Σ_j K_ij cos(φ_j - φ_i) r_j`
/// - `dφ_i/dt = ω_i + Σ_j K_ij sin(φ_j - φ_i) r_j / r_i`
/// - `dω_i/dt = (γ / N) Σ_j K_ij sin(φ_j - φ_i) r_j`
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

        StateDerivatives::new(dphase, damplitude, dfrequency)
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

        StateDerivatives::new(dphase, damplitude, dfrequency)
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
            return StateDerivatives::new(dphase, damplitude, dfrequency);
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
