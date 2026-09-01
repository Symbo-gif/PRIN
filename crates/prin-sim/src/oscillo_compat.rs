//! Reference-faithful `OscilloSim` rebuild (PRINet 3.0 `utils/oscillosim.py`).
//!
//! This module is the owned Rust numerical core for the
//! [`prin.simulation`](../../../python/prin/simulation.py) compatibility surface
//! that WP-036C S1 (`0144M5`) needs: ring / small-world / CSR coupling modes,
//! phase-lag (`α`) Kuramoto coupling, per-edge coupling weights, and the Euler /
//! RK4 integrators the `test_y4q1*` acceptance suite exercises.
//!
//! The step equations are a line-for-line port of the archived reference
//! (`_step_mean_field`, `_step_sparse_knn`, `_step_sparse_knn_rk4`, `_step_csr`,
//! `run`). The only intentional divergence is the RNG: PRINet 3.0 seeded
//! `torch.Generator` streams, which this crate cannot reproduce bit-for-bit, so
//! frequencies, initial phases, and topology rewiring are drawn from a
//! deterministic [`prin_dynamics::Seed`] instead. Same-seed reproducibility is
//! preserved (`test_ring_deterministic`); cross-implementation phase-value
//! parity is not claimed and no acceptance test requires it.
//!
//! Chimera-detection metrics (`local_order_parameter`, `bimodality_index`,
//! `strength_of_incoherence`, `discontinuity_measure`, `chimera_index`,
//! `strength_of_incoherence_temporal`) are already owned by
//! [`prin_metrics`](../../prin_metrics/index.html) and are not duplicated here.

use std::f64::consts::PI;
use std::time::Instant;

use prin_dynamics::Seed;
use serde::{Deserialize, Serialize};

use crate::error::SimError;

const TAU: f64 = 2.0 * PI;

/// Coupling topology for [`OscilloCompat`].
#[derive(Clone, Copy, PartialEq, Eq, Debug, Serialize, Deserialize)]
pub enum CompatCoupling {
    /// `O(N)` global coupling via the complex order parameter.
    MeanField,
    /// `O(N·k)` random k-nearest-neighbour coupling.
    SparseKnn,
    /// `O(nnz)` arbitrary sparse coupling via a CSR matrix.
    Csr,
    /// `O(N·k)` 1-D ring lattice spatial neighbours (chimera-capable).
    Ring,
    /// `O(N·k)` Watts–Strogatz small-world topology.
    SmallWorld,
}

impl CompatCoupling {
    /// Parse the PRINet 3.0 coupling-mode string (`"auto"` must be resolved by
    /// the caller before this point).
    pub fn parse(s: &str) -> Result<Self, SimError> {
        match s {
            "mean_field" => Ok(Self::MeanField),
            "sparse_knn" => Ok(Self::SparseKnn),
            "csr" => Ok(Self::Csr),
            "ring" => Ok(Self::Ring),
            "small_world" => Ok(Self::SmallWorld),
            other => Err(SimError::InvalidCoupling {
                reason: format!("unknown coupling mode {other:?}"),
            }),
        }
    }
}

/// Integration method for [`OscilloCompat`].
#[derive(Clone, Copy, PartialEq, Eq, Debug, Serialize, Deserialize)]
pub enum CompatIntegrator {
    /// 1st-order forward Euler.
    Euler,
    /// 4th-order Runge–Kutta (recommended for chimera studies).
    Rk4,
}

impl CompatIntegrator {
    /// Parse the PRINet 3.0 integrator string.
    pub fn parse(s: &str) -> Result<Self, SimError> {
        match s {
            "euler" => Ok(Self::Euler),
            "rk4" => Ok(Self::Rk4),
            other => Err(SimError::InvalidCoupling {
                reason: format!("unknown integrator {other:?}"),
            }),
        }
    }
}

/// Construction parameters for [`OscilloCompat`] (mirrors the reference
/// `OscilloSim.__init__` signature).
#[derive(Clone, Debug)]
pub struct OscilloCompatConfig {
    /// Number of oscillators.
    pub n: usize,
    /// Global coupling constant `K`.
    pub coupling_strength: f64,
    /// Resolved coupling mode (`"auto"` already mapped by the caller).
    pub mode: CompatCoupling,
    /// Neighbours per oscillator for `sparse_knn` / `ring` / `small_world`.
    pub k_neighbors: usize,
    /// Sparsity level for CSR mode (`0.0` dense … `0.99` very sparse).
    pub sparsity: f64,
    /// Stuart–Landau growth parameter `μ`.
    pub mu: f64,
    /// Mean natural frequency.
    pub freq_mean: f64,
    /// Standard deviation of natural frequencies.
    pub freq_std: f64,
    /// Phase lag `α` in the coupling function `sin(φ_j − φ_i − α)`.
    pub phase_lag: f64,
    /// Rewiring probability for `small_world` mode.
    pub p_rewire: f64,
    /// Integration method.
    pub integrator: CompatIntegrator,
    /// Optional per-edge coupling weights, row-major `(N, k)`.
    pub coupling_weights: Option<Vec<f64>>,
    /// Random seed.
    pub seed: u64,
}

/// One recorded simulation output (mirrors `SimulationResult`).
#[derive(Clone, Debug, Serialize, Deserialize)]
pub struct OscilloCompatOutput {
    /// Final oscillator phases `(N,)`.
    pub final_phase: Vec<f64>,
    /// Final oscillator amplitudes `(N,)`.
    pub final_amplitude: Vec<f64>,
    /// Kuramoto order parameter `r` at each recorded step.
    pub order_parameter: Vec<f64>,
    /// Total wall-clock simulation time in seconds.
    pub wall_time_s: f64,
    /// Oscillator-steps per second.
    pub throughput: f64,
    /// Phase trajectory `(n_record, N)` if `record_trajectory` was set.
    pub trajectory_phase: Option<Vec<Vec<f64>>>,
}

/// Reference-faithful `OscilloSim` engine.
pub struct OscilloCompat {
    cfg: OscilloCompatConfig,
    frequencies: Vec<f64>,
    /// Row-major `(N, k)` neighbour indices for sparse / ring / small-world.
    neighbors: Vec<usize>,
    /// Neighbour count `k` (0 for mean-field / CSR).
    k: usize,
    /// Row-major `(N, k)` per-edge weights (uniform `1/k` fallback applied at
    /// step time when [`OscilloCompatConfig::coupling_weights`] is `None`).
    weights: Option<Vec<f64>>,
    /// CSR coupling `(indptr, indices, data)` for CSR mode.
    csr: Option<(Vec<usize>, Vec<usize>, Vec<f64>)>,
}

/// Box–Muller standard-normal draw from a deterministic seed stream.
fn next_gaussian(seed: &mut Seed) -> f64 {
    let u1 = 1.0 - seed.next_f64();
    let u2 = 1.0 - seed.next_f64();
    (-2.0 * u1.ln()).sqrt() * (TAU * u2).cos()
}

/// Deterministic Fisher–Yates partial shuffle: first `k` of a `0..m` range.
fn partial_perm(m: usize, k: usize, seed: &mut Seed) -> Vec<usize> {
    let mut idx: Vec<usize> = (0..m).collect();
    let take = k.min(m);
    for i in 0..take {
        let j = i + (seed.next_f64() * ((m - i) as f64)) as usize;
        idx.swap(i, j.min(m - 1));
    }
    idx.truncate(take);
    idx
}

impl OscilloCompat {
    /// Build the engine: draw natural frequencies and the coupling structure.
    ///
    /// # Errors
    ///
    /// Returns [`SimError`] for an empty population, a non-positive neighbour
    /// count where one is required, or a malformed weight buffer.
    pub fn new(cfg: OscilloCompatConfig) -> Result<Self, SimError> {
        if cfg.n == 0 {
            return Err(SimError::EmptyPopulation { n: 0 });
        }
        let n = cfg.n;

        // Natural frequencies: randn(N) * freq_std + freq_mean.
        let mut fseed = Seed::new(cfg.seed as u128, 0);
        let frequencies: Vec<f64> = (0..n)
            .map(|_| next_gaussian(&mut fseed) * cfg.freq_std + cfg.freq_mean)
            .collect();

        let mut k = 0usize;
        let mut neighbors: Vec<usize> = Vec::new();
        let mut csr: Option<(Vec<usize>, Vec<usize>, Vec<f64>)> = None;

        match cfg.mode {
            CompatCoupling::MeanField => {}
            CompatCoupling::SparseKnn => {
                k = cfg.k_neighbors.min(n.saturating_sub(1)).max(1);
                let mut kseed = Seed::new(cfg.seed as u128, 0x6b6e_6e00);
                neighbors = Vec::with_capacity(n * k);
                for i in 0..n {
                    // Candidates = 0..n excluding i.
                    let cand: Vec<usize> = (0..n).filter(|&j| j != i).collect();
                    let picks = partial_perm(cand.len(), k, &mut kseed);
                    for p in picks {
                        neighbors.push(cand[p]);
                    }
                }
            }
            CompatCoupling::Ring | CompatCoupling::SmallWorld => {
                let mut kk = cfg.k_neighbors.min(n.saturating_sub(1)).max(2);
                if kk % 2 != 0 {
                    kk = kk.saturating_sub(1).max(2);
                }
                k = kk;
                neighbors = ring_indices(n, k)?;
                if cfg.mode == CompatCoupling::SmallWorld {
                    let mut rseed = Seed::new(cfg.seed as u128, 0x7377_0000);
                    rewire_in_place(&mut neighbors, n, k, cfg.p_rewire, &mut rseed);
                }
            }
            CompatCoupling::Csr => {
                let nnz_per_row = (((1.0 - cfg.sparsity) * n as f64) as usize).max(1);
                let mut cseed = Seed::new(cfg.seed as u128, 0x6373_7200);
                let mut indptr = Vec::with_capacity(n + 1);
                let mut indices: Vec<usize> = Vec::new();
                let mut data: Vec<f64> = Vec::new();
                indptr.push(0usize);
                let base = cfg.coupling_strength / (nnz_per_row.max(1) as f64);
                for i in 0..n {
                    let cand: Vec<usize> = (0..n).filter(|&j| j != i).collect();
                    let mut picks: Vec<usize> = partial_perm(cand.len(), nnz_per_row, &mut cseed)
                        .into_iter()
                        .map(|p| cand[p])
                        .collect();
                    picks.sort_unstable();
                    for c in &picks {
                        indices.push(*c);
                        data.push(next_gaussian(&mut cseed) * 0.1 + base);
                    }
                    indptr.push(indices.len());
                }
                csr = Some((indptr, indices, data));
            }
        }

        let weights = match &cfg.coupling_weights {
            Some(w) => {
                if k == 0 || w.len() != n * k {
                    return Err(SimError::DimensionMismatch {
                        name: "coupling_weights",
                        expected: n * k,
                        got: w.len(),
                    });
                }
                Some(w.clone())
            }
            None => None,
        };

        Ok(Self {
            cfg,
            frequencies,
            neighbors,
            k,
            weights,
            csr,
        })
    }

    /// Number of oscillators.
    pub fn n(&self) -> usize {
        self.cfg.n
    }

    /// Natural frequencies `(N,)`.
    pub fn frequencies(&self) -> &[f64] {
        &self.frequencies
    }

    /// Sparse coupling contribution `(N,)` for ring / knn / small-world modes.
    fn sparse_coupling(&self, phase: &[f64]) -> Vec<f64> {
        let n = self.cfg.n;
        let k = self.k;
        let alpha = self.cfg.phase_lag;
        let kstr = self.cfg.coupling_strength;
        (0..n)
            .map(|i| {
                let mut acc = 0.0;
                for slot in 0..k {
                    let j = self.neighbors[i * k + slot];
                    let s = (phase[j] - phase[i] - alpha).sin();
                    match &self.weights {
                        Some(w) => acc += w[i * k + slot] * s,
                        None => acc += s,
                    }
                }
                match &self.weights {
                    Some(_) => kstr * acc,
                    None => kstr / (k as f64) * acc,
                }
            })
            .collect()
    }

    /// `dφ/dt` for sparse modes: `2π·ω + coupling`.
    fn sparse_derivative(&self, phase: &[f64]) -> Vec<f64> {
        let coupling = self.sparse_coupling(phase);
        self.frequencies
            .iter()
            .zip(coupling)
            .map(|(&f, c)| TAU * f + c)
            .collect()
    }

    /// Stuart–Landau amplitude Euler update, clamped to `[1e-6, 10]`.
    fn amplitude_step(&self, amplitude: &[f64], dt: f64) -> Vec<f64> {
        let mu = self.cfg.mu;
        amplitude
            .iter()
            .map(|&a| (a + dt * a * (mu - a * a)).clamp(1e-6, 10.0))
            .collect()
    }

    fn step_mean_field(&self, phase: &[f64], amplitude: &[f64], dt: f64) -> (Vec<f64>, Vec<f64>) {
        let n = self.cfg.n as f64;
        let (mut re, mut im) = (0.0, 0.0);
        for &p in phase {
            re += p.cos();
            im += p.sin();
        }
        re /= n;
        im /= n;
        let r = (re * re + im * im).sqrt();
        let psi = im.atan2(re);
        let alpha = self.cfg.phase_lag;
        let kstr = self.cfg.coupling_strength;
        let new_phase = phase
            .iter()
            .zip(&self.frequencies)
            .map(|(&p, &f)| {
                let dphi = f * dt + kstr * r * (psi - p - alpha).sin() * dt;
                (p + TAU * f * dt + dphi).rem_euclid(TAU)
            })
            .collect();
        (new_phase, self.amplitude_step(amplitude, dt))
    }

    fn step_sparse_euler(&self, phase: &[f64], amplitude: &[f64], dt: f64) -> (Vec<f64>, Vec<f64>) {
        let d = self.sparse_derivative(phase);
        let new_phase = phase
            .iter()
            .zip(d)
            .map(|(&p, dp)| (p + dp * dt).rem_euclid(TAU))
            .collect();
        (new_phase, self.amplitude_step(amplitude, dt))
    }

    fn step_sparse_rk4(&self, phase: &[f64], amplitude: &[f64], dt: f64) -> (Vec<f64>, Vec<f64>) {
        let add = |a: &[f64], b: &[f64], s: f64| -> Vec<f64> {
            a.iter().zip(b).map(|(&x, &y)| x + s * y).collect()
        };
        let k1 = self.sparse_derivative(phase);
        let k2 = self.sparse_derivative(&add(phase, &k1, 0.5 * dt));
        let k3 = self.sparse_derivative(&add(phase, &k2, 0.5 * dt));
        let k4 = self.sparse_derivative(&add(phase, &k3, dt));
        let new_phase = (0..phase.len())
            .map(|i| {
                (phase[i] + (dt / 6.0) * (k1[i] + 2.0 * k2[i] + 2.0 * k3[i] + k4[i]))
                    .rem_euclid(TAU)
            })
            .collect();
        (new_phase, self.amplitude_step(amplitude, dt))
    }

    fn step_csr(&self, phase: &[f64], amplitude: &[f64], dt: f64) -> (Vec<f64>, Vec<f64>) {
        let (indptr, indices, data) = self.csr.as_ref().expect("csr mode has csr storage");
        let n = self.cfg.n;
        let sin_p: Vec<f64> = phase.iter().map(|p| p.sin()).collect();
        let cos_p: Vec<f64> = phase.iter().map(|p| p.cos()).collect();
        // coupling = (A @ sin)·cos − (A @ cos)·sin
        let new_phase = (0..n)
            .map(|i| {
                let (mut a_sin, mut a_cos) = (0.0, 0.0);
                for idx in indptr[i]..indptr[i + 1] {
                    let j = indices[idx];
                    a_sin += data[idx] * sin_p[j];
                    a_cos += data[idx] * cos_p[j];
                }
                let coupling = a_sin * cos_p[i] - a_cos * sin_p[i];
                (phase[i] + TAU * self.frequencies[i] * dt + coupling * dt).rem_euclid(TAU)
            })
            .collect();
        (new_phase, self.amplitude_step(amplitude, dt))
    }

    fn step(&self, phase: &[f64], amplitude: &[f64], dt: f64) -> (Vec<f64>, Vec<f64>) {
        match self.cfg.mode {
            CompatCoupling::MeanField => self.step_mean_field(phase, amplitude, dt),
            CompatCoupling::Csr => self.step_csr(phase, amplitude, dt),
            CompatCoupling::SparseKnn | CompatCoupling::Ring | CompatCoupling::SmallWorld => {
                match self.cfg.integrator {
                    CompatIntegrator::Rk4 => self.step_sparse_rk4(phase, amplitude, dt),
                    CompatIntegrator::Euler => self.step_sparse_euler(phase, amplitude, dt),
                }
            }
        }
    }

    /// Run the simulation for `n_steps` steps of size `dt`.
    ///
    /// Mirrors the reference `OscilloSim.run`: the order parameter (and, when
    /// requested, the phase trajectory) is recorded at step 0 modulo
    /// `record_interval` and always at the final step.
    ///
    /// # Errors
    ///
    /// Returns [`SimError`] for a non-positive `dt`, a zero `record_interval`,
    /// or an initial buffer whose length is not `N`.
    pub fn run(
        &self,
        n_steps: usize,
        dt: f64,
        record_trajectory: bool,
        record_interval: usize,
        initial_phase: Option<Vec<f64>>,
        initial_amplitude: Option<Vec<f64>>,
    ) -> Result<OscilloCompatOutput, SimError> {
        if !dt.is_finite() || dt <= 0.0 {
            return Err(SimError::NonFiniteValue {
                name: "dt",
                index: 0,
                value: dt,
            });
        }
        if record_interval == 0 {
            return Err(SimError::DimensionMismatch {
                name: "record_interval",
                expected: 1,
                got: 0,
            });
        }
        let n = self.cfg.n;

        let mut phase = match initial_phase {
            Some(p) => {
                if p.len() != n {
                    return Err(SimError::DimensionMismatch {
                        name: "initial_phase",
                        expected: n,
                        got: p.len(),
                    });
                }
                p
            }
            None => {
                let mut pseed = Seed::new(self.cfg.seed as u128 + 1, 0);
                (0..n).map(|_| pseed.next_f64() * TAU).collect()
            }
        };
        let mut amplitude = match initial_amplitude {
            Some(a) => {
                if a.len() != n {
                    return Err(SimError::DimensionMismatch {
                        name: "initial_amplitude",
                        expected: n,
                        got: a.len(),
                    });
                }
                a
            }
            None => vec![1.0; n],
        };

        let mut order_parameter: Vec<f64> = Vec::new();
        let mut trajectory: Vec<Vec<f64>> = Vec::new();

        let t0 = Instant::now();
        for step in 0..n_steps {
            let (np, na) = self.step(&phase, &amplitude, dt);
            phase = np;
            amplitude = na;
            if step % record_interval == 0 || step + 1 == n_steps {
                order_parameter.push(order_parameter_magnitude(&phase));
                if record_trajectory {
                    trajectory.push(phase.clone());
                }
            }
        }
        let wall_time_s = t0.elapsed().as_secs_f64();
        let throughput = (n as f64 * n_steps as f64) / wall_time_s.max(1e-12);

        Ok(OscilloCompatOutput {
            final_phase: phase,
            final_amplitude: amplitude,
            order_parameter,
            wall_time_s,
            throughput,
            trajectory_phase: if record_trajectory {
                Some(trajectory)
            } else {
                None
            },
        })
    }
}

/// Kuramoto order-parameter magnitude `r = |mean(exp(iφ))|`.
pub fn order_parameter_magnitude(phase: &[f64]) -> f64 {
    if phase.is_empty() {
        return 0.0;
    }
    let n = phase.len() as f64;
    let (mut re, mut im) = (0.0, 0.0);
    for &p in phase {
        re += p.cos();
        im += p.sin();
    }
    ((re / n).powi(2) + (im / n).powi(2)).sqrt()
}

/// Validate the ring-lattice constraints shared by `ring` / `small_world`.
fn validate_ring(n: usize, k: usize) -> Result<(), SimError> {
    if k < 2 {
        return Err(SimError::InvalidCoupling {
            reason: format!("k must be >= 2, got {k}"),
        });
    }
    if k % 2 != 0 {
        return Err(SimError::InvalidCoupling {
            reason: format!("k must be even for ring lattice, got {k}"),
        });
    }
    if k >= n {
        return Err(SimError::InvalidCoupling {
            reason: format!("k must be < N, got k={k}, N={n}"),
        });
    }
    Ok(())
}

/// Build a row-major `(N, k)` ring-lattice neighbour-index table.
///
/// Each oscillator `i` connects to its `k/2` nearest neighbours on each side of
/// a ring (`(i ± d) mod N`). Ordering matches the reference: the `k/2` left
/// offsets `[-half, −1]` followed by the `k/2` right offsets `[1, half]`.
///
/// # Errors
///
/// Returns [`SimError::InvalidCoupling`] when `k` is odd, `k < 2`, or `k >= N`.
pub fn ring_indices(n: usize, k: usize) -> Result<Vec<usize>, SimError> {
    validate_ring(n, k)?;
    let half = (k / 2) as isize;
    let mut out = Vec::with_capacity(n * k);
    let ni = n as isize;
    for i in 0..ni {
        for off in (-half..0).chain(1..=half) {
            out.push(((i + off).rem_euclid(ni)) as usize);
        }
    }
    Ok(out)
}

/// Rewire a ring-lattice neighbour table in place (Watts–Strogatz).
///
/// Mirrors the reference vectorised path: draw an `(N, k)` Bernoulli(`p`) mask
/// and `(N, k)` uniform random targets, replace masked entries, then repair any
/// self-loop by pointing it at `(i + 1) mod N`.
fn rewire_in_place(nbr: &mut [usize], n: usize, k: usize, p_rewire: f64, seed: &mut Seed) {
    for i in 0..n {
        for slot in 0..k {
            let rewire = seed.next_f64() < p_rewire;
            let target = (seed.next_f64() * n as f64) as usize % n.max(1);
            if rewire {
                nbr[i * k + slot] = target;
            }
        }
    }
    for i in 0..n {
        for slot in 0..k {
            if nbr[i * k + slot] == i {
                nbr[i * k + slot] = (i + 1) % n;
            }
        }
    }
}

/// Build a row-major `(N, k)` Watts–Strogatz small-world neighbour-index table.
///
/// # Errors
///
/// Returns [`SimError::InvalidCoupling`] when `k` is odd, `k < 2`, or `k >= N`.
pub fn small_world_indices(
    n: usize,
    k: usize,
    p_rewire: f64,
    seed: u64,
) -> Result<Vec<usize>, SimError> {
    let mut nbr = ring_indices(n, k)?;
    let mut s = Seed::new(seed as u128, 0x7377_0000);
    rewire_in_place(&mut nbr, n, k, p_rewire, &mut s);
    Ok(nbr)
}

/// Per-edge cosine coupling weights for a ring topology (Abrams & Strogatz).
///
/// Returns a length-`k` weight row `G(d) = (1 + A·cos(2π d / n)) / 2π`,
/// normalised to sum to `1`. The caller broadcasts it to `(N, k)`.
///
/// # Errors
///
/// Returns [`SimError::InvalidCoupling`] when `k == 0`.
pub fn cosine_coupling_kernel(n: usize, k: usize, a: f64) -> Result<Vec<f64>, SimError> {
    if k == 0 {
        return Err(SimError::InvalidCoupling {
            reason: "k must be >= 1 for a cosine kernel".to_string(),
        });
    }
    let half_k = (k / 2) as isize;
    let mut offsets: Vec<f64> = (-half_k..0).chain(1..=half_k).map(|o| o as f64).collect();
    if offsets.len() < k {
        offsets.push((half_k + 1) as f64);
    }
    offsets.truncate(k);
    let raw: Vec<f64> = offsets
        .iter()
        .map(|&o| (1.0 + a * (TAU * o / n as f64).cos()) / TAU)
        .collect();
    let sum: f64 = raw.iter().sum();
    Ok(raw.iter().map(|&r| r / sum).collect())
}

/// Single-humped chimera initial condition `φ_i = 6·exp(−30(x_i−0.5)²)·r_i`.
pub fn chimera_initial_condition(n: usize, seed: u64) -> Vec<f64> {
    let mut s = Seed::new(seed as u128, 0x6963_0000);
    (0..n)
        .map(|i| {
            let x = if n <= 1 {
                0.0
            } else {
                i as f64 / (n - 1) as f64
            };
            let bump = 6.0 * (-30.0 * (x - 0.5).powi(2)).exp();
            let noise = s.next_f64() - 0.5;
            bump * noise
        })
        .collect()
}

/// Smooth Gaussian-bump initial condition, wrapped to `[0, 2π)`.
pub fn gaussian_bump_ic(
    n: usize,
    a0: f64,
    sigma_ratio: f64,
    phi0: f64,
    noise_amp: f64,
    seed: u64,
) -> Vec<f64> {
    let mut s = Seed::new(seed as u128, 0x6762_0000);
    let i0 = n as f64 / 2.0;
    let sigma = sigma_ratio * n as f64;
    (0..n)
        .map(|i| {
            let bump = a0 * (-((i as f64 - i0).powi(2)) / (2.0 * sigma * sigma)).exp();
            let noise = (s.next_f64() - 0.5) * 2.0 * noise_amp;
            (phi0 + bump + noise).rem_euclid(TAU)
        })
        .collect()
}

/// Half-synchronised, half-random initial condition, wrapped to `[0, 2π)`.
pub fn half_sync_half_random_ic(n: usize, sync_phase: f64, noise_amp: f64, seed: u64) -> Vec<f64> {
    let mut s = Seed::new(seed as u128, 0x6873_0000);
    let half = n / 2;
    let mut out = Vec::with_capacity(n);
    for _ in 0..half {
        out.push((sync_phase + (s.next_f64() - 0.5) * 2.0 * noise_amp).rem_euclid(TAU));
    }
    for _ in half..n {
        out.push((s.next_f64() * TAU).rem_euclid(TAU));
    }
    out
}

#[cfg(test)]
mod tests {
    use super::*;

    fn cfg(mode: CompatCoupling, k: usize) -> OscilloCompatConfig {
        OscilloCompatConfig {
            n: 32,
            coupling_strength: 2.0,
            mode,
            k_neighbors: k,
            sparsity: 0.9,
            mu: 1.0,
            freq_mean: 5.0,
            freq_std: 0.5,
            phase_lag: 0.0,
            p_rewire: 0.1,
            integrator: CompatIntegrator::Euler,
            coupling_weights: None,
            seed: 42,
        }
    }

    #[test]
    fn ring_shape_and_bounds() {
        let idx = ring_indices(16, 4).unwrap();
        assert_eq!(idx.len(), 64);
        assert!(idx.iter().all(|&v| v < 16));
    }

    #[test]
    fn ring_rejects_odd() {
        assert!(ring_indices(16, 3).is_err());
        assert!(ring_indices(8, 8).is_err());
        assert!(ring_indices(16, 1).is_err());
    }

    #[test]
    fn zero_rewire_equals_ring() {
        let ring = ring_indices(16, 4).unwrap();
        let sw = small_world_indices(16, 4, 0.0, 0).unwrap();
        assert_eq!(ring, sw);
    }

    #[test]
    fn small_world_reproducible() {
        let a = small_world_indices(16, 4, 0.5, 99).unwrap();
        let b = small_world_indices(16, 4, 0.5, 99).unwrap();
        assert_eq!(a, b);
    }

    #[test]
    fn ring_run_is_finite_and_deterministic() {
        let sim1 = OscilloCompat::new(cfg(CompatCoupling::Ring, 4)).unwrap();
        let sim2 = OscilloCompat::new(cfg(CompatCoupling::Ring, 4)).unwrap();
        let r1 = sim1.run(50, 0.01, false, 1, None, None).unwrap();
        let r2 = sim2.run(50, 0.01, false, 1, None, None).unwrap();
        assert_eq!(r1.final_phase, r2.final_phase);
        assert!(r1.final_phase.iter().all(|v| v.is_finite()));
        assert!(r1.throughput > 0.0);
    }

    #[test]
    fn rk4_ring_bounded() {
        let mut c = cfg(CompatCoupling::Ring, 8);
        c.integrator = CompatIntegrator::Rk4;
        c.coupling_strength = 5.0;
        let sim = OscilloCompat::new(c).unwrap();
        let out = sim.run(200, 0.05, false, 10, None, None).unwrap();
        assert!(out
            .final_phase
            .iter()
            .all(|&p| (0.0..TAU + 1e-9).contains(&p)));
    }

    #[test]
    fn mean_field_runs() {
        let sim = OscilloCompat::new(cfg(CompatCoupling::MeanField, 0)).unwrap();
        let out = sim.run(20, 0.01, true, 5, None, None).unwrap();
        assert!(out.trajectory_phase.is_some());
    }

    #[test]
    fn csr_runs() {
        let sim = OscilloCompat::new(cfg(CompatCoupling::Csr, 0)).unwrap();
        let out = sim.run(20, 0.01, false, 5, None, None).unwrap();
        assert_eq!(out.final_phase.len(), 32);
    }

    #[test]
    fn cosine_kernel_normalised_and_symmetric() {
        let w = cosine_coupling_kernel(64, 8, 0.9).unwrap();
        assert!((w.iter().sum::<f64>() - 1.0).abs() < 1e-9);
        for d in 0..4 {
            assert!((w[d] - w[7 - d]).abs() < 1e-9);
        }
        let uniform = cosine_coupling_kernel(64, 8, 0.0).unwrap();
        assert!(uniform.iter().all(|&v| (v - 1.0 / 8.0).abs() < 1e-9));
    }

    #[test]
    fn ics_are_finite_and_bounded() {
        let a = chimera_initial_condition(256, 42);
        let b = chimera_initial_condition(256, 42);
        assert_eq!(a, b);
        assert!(a.iter().all(|v| v.is_finite()));
        let g = gaussian_bump_ic(256, PI, 1.0 / 6.0, 0.0, 0.01, 0);
        assert!(g.iter().all(|&v| (0.0..TAU + 1e-9).contains(&v)));
        let h = half_sync_half_random_ic(200, 0.0, 0.01, 42);
        assert!(h.iter().all(|&v| (0.0..TAU + 1e-9).contains(&v)));
    }

    #[test]
    fn weighted_coupling_dimension_check() {
        let mut c = cfg(CompatCoupling::Ring, 8);
        c.coupling_weights = Some(vec![0.1; 3]);
        assert!(OscilloCompat::new(c).is_err());
    }
}
