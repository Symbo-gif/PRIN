//! Parallel parameter sweeps for OscilloSim.
//!
//! Rebuild of PRINet 3.0 `sweep_coupling_params` and `detect_oscillation` from
//! `core/propagation/sweep_utils.py`. The sweep runs a grid of parameter
//! configurations in parallel via rayon, each an independent OscilloSim
//! simulation with deterministic seeding.
//!
//! ## Design
//!
//! - [`SweepConfig`] defines the parameter grid (coupling strength, decay rate,
//!   frequency adaptation rate, bifurcation parameter).
//! - [`run_sweep`] executes all configurations in parallel using rayon's
//!   thread pool, returning one [`SweepResult`] per configuration.
//! - [`detect_oscillation`] flags destabilizing oscillations in order-parameter
//!   histories via windowed variance.
//!
//! Each configuration receives a unique [`Seed`] derived from the base seed
//! and the configuration index, ensuring deterministic, reproducible results
//! regardless of thread scheduling.

use rayon::prelude::*;
use serde::{Deserialize, Serialize};

use prin_dynamics::state::OscillatorState;
use prin_dynamics::{Integrator, RK4Integrator, Seed};

use crate::csr_coupling::SparseCoupling;
use crate::engine::{OscilloSim, SparseKuramoto, SparseStuartLandau};
use crate::error::SimError;

/// A single parameter axis to sweep.
///
/// Each variant names the parameter and provides a vector of values to try.
/// The sweep forms the Cartesian product of all specified axes.
#[derive(Clone, Debug, Serialize, Deserialize)]
pub enum SweepAxis {
    /// Coupling strength for ring-lattice topology (passed to `from_ring`).
    CouplingStrength(Vec<f64>),
    /// Amplitude decay rate λ for Kuramoto models.
    DecayRate(Vec<f64>),
    /// Frequency adaptation rate γ for Kuramoto models.
    FreqAdaptationRate(Vec<f64>),
    /// Bifurcation parameter μ for Stuart–Landau models.
    BifurcationParam(Vec<f64>),
}

impl SweepAxis {
    /// Name of the parameter (for result reporting).
    pub fn name(&self) -> &'static str {
        match self {
            Self::CouplingStrength(_) => "coupling_strength",
            Self::DecayRate(_) => "decay_rate",
            Self::FreqAdaptationRate(_) => "freq_adaptation_rate",
            Self::BifurcationParam(_) => "bifurcation_param",
        }
    }

    /// The values to sweep over.
    pub fn values(&self) -> &[f64] {
        match self {
            Self::CouplingStrength(v) => v,
            Self::DecayRate(v) => v,
            Self::FreqAdaptationRate(v) => v,
            Self::BifurcationParam(v) => v,
        }
    }
}

/// The dynamical model type for the sweep.
#[derive(Clone, Copy, Debug, Serialize, Deserialize, PartialEq, Eq)]
pub enum SweepModel {
    /// Sparse Kuramoto model.
    Kuramoto,
    /// Sparse Stuart–Landau model.
    StuartLandau,
}

/// Configuration for a parameter sweep.
///
/// Defines the grid of parameter combinations to explore. The sweep forms the
/// Cartesian product of all axes. Each configuration runs an independent
/// OscilloSim simulation.
#[derive(Clone, Debug, Serialize, Deserialize)]
pub struct SweepConfig {
    /// Number of oscillators.
    pub n_oscillators: usize,
    /// Half-degree for ring-lattice coupling (each oscillator couples to
    /// `half_k` neighbours on each side).
    pub half_k: usize,
    /// Parameter axes to sweep (Cartesian product).
    pub axes: Vec<SweepAxis>,
    /// Number of integration steps per configuration.
    pub n_steps: usize,
    /// Timestep.
    pub dt: f64,
    /// Base seed for deterministic RNG. Each configuration derives its own
    /// seed from this base and its configuration index.
    pub base_seed: u64,
    /// Which model to use.
    pub model: SweepModel,
    /// Whether to record trajectories.
    pub record_trajectory: bool,
}

impl SweepConfig {
    /// Total number of configurations in the grid.
    pub fn n_configs(&self) -> usize {
        self.axes.iter().map(|a| a.values().len()).product()
    }

    /// Validate the configuration.
    ///
    /// # Errors
    ///
    /// Returns [`SimError`] for empty axes, empty axis values, or invalid
    /// simulation parameters.
    pub fn validate(&self) -> Result<(), SimError> {
        if self.n_oscillators == 0 {
            return Err(SimError::EmptyPopulation { n: 0 });
        }
        if self.axes.is_empty() {
            return Err(SimError::DimensionMismatch {
                name: "axes",
                expected: 1,
                got: 0,
            });
        }
        for axis in &self.axes {
            if axis.values().is_empty() {
                return Err(SimError::DimensionMismatch {
                    name: axis.name(),
                    expected: 1,
                    got: 0,
                });
            }
            for (i, &v) in axis.values().iter().enumerate() {
                if !v.is_finite() {
                    return Err(SimError::NonFiniteValue {
                        name: axis.name(),
                        index: i,
                        value: v,
                    });
                }
            }
        }
        if self.n_steps == 0 {
            return Err(SimError::DimensionMismatch {
                name: "n_steps",
                expected: 1,
                got: 0,
            });
        }
        if !self.dt.is_finite() || self.dt <= 0.0 {
            return Err(SimError::NonFiniteValue {
                name: "dt",
                index: 0,
                value: self.dt,
            });
        }
        Ok(())
    }
}

/// Result of a single sweep configuration.
#[derive(Clone, Debug, Serialize, Deserialize)]
pub struct SweepResult {
    /// Configuration index (row-major order in the Cartesian product).
    pub config_index: usize,
    /// Parameter values for this configuration: `(axis_name, value)` pairs.
    pub params: Vec<(String, f64)>,
    /// Final-order parameter magnitude `r = |1/N Σ exp(iφ)|`.
    pub final_order_parameter: f64,
    /// Mean order parameter over the trajectory (if recorded).
    pub mean_order_parameter: Option<f64>,
    /// Whether destabilizing oscillations were detected.
    pub oscillation_detected: bool,
    /// Number of integration steps completed.
    pub n_steps: usize,
    /// Seed used for this configuration.
    pub seed: u64,
}

/// Detect destabilizing oscillations in an order-parameter history.
///
/// Computes the windowed variance of the last `window` values. If the variance
/// exceeds `threshold`, oscillation is flagged. Matches PRINet 3.0
/// `detect_oscillation`.
///
/// # Arguments
///
/// * `r_history` - Order-parameter values over time.
/// * `window` - Number of recent values to inspect.
/// * `threshold` - Variance threshold above which oscillation is detected.
///
/// # Example
///
/// ```
/// use prin_sim::sweep::detect_oscillation;
///
/// let stable = vec![0.8_f64; 30];
/// assert!(!detect_oscillation(&stable, 20, 0.01));
///
/// let oscillating: Vec<f64> = (0..30).map(|i| (i as f64 * 0.5).sin()).collect();
/// assert!(detect_oscillation(&oscillating, 20, 0.01));
/// ```
pub fn detect_oscillation(r_history: &[f64], window: usize, threshold: f64) -> bool {
    if r_history.len() < window || window == 0 {
        return false;
    }
    let recent = &r_history[r_history.len() - window..];
    let mean = recent.iter().sum::<f64>() / recent.len() as f64;
    let var = recent.iter().map(|v| (v - mean).powi(2)).sum::<f64>() / recent.len() as f64;
    var > threshold
}

/// Compute the Kuramoto order parameter for a phase slice.
fn order_parameter(phase: &[f64]) -> f64 {
    let n_inv = 1.0 / phase.len() as f64;
    let (sum_sin, sum_cos) = phase.iter().fold((0.0_f64, 0.0_f64), |(ss, sc), &p| {
        let (s, c) = p.sin_cos();
        (ss + s, sc + c)
    });
    let z_re = sum_cos * n_inv;
    let z_im = sum_sin * n_inv;
    (z_re * z_re + z_im * z_im).sqrt().min(1.0)
}

/// Expand the Cartesian product of axis values at a given flat index.
fn expand_config(axes: &[SweepAxis], flat_index: usize) -> Vec<f64> {
    let mut idx = flat_index;
    let n_axes = axes.len();
    let mut values = vec![0.0; n_axes];
    for axis_idx in (0..n_axes).rev() {
        let n_values = axes[axis_idx].values().len();
        values[axis_idx] = axes[axis_idx].values()[idx % n_values];
        idx /= n_values;
    }
    values
}

/// Run a parallel parameter sweep.
///
/// Executes all configurations in the Cartesian product of the sweep axes
/// in parallel using rayon. Each configuration runs an independent OscilloSim
/// simulation with a deterministic seed derived from the base seed and the
/// configuration index.
///
/// # Errors
///
/// Returns [`SimError`] for invalid configurations or simulation failures.
///
/// # Example
///
/// ```rust,no_run
/// use prin_sim::sweep::{SweepConfig, SweepAxis, SweepModel, run_sweep};
///
/// let config = SweepConfig {
///     n_oscillators: 64,
///     half_k: 4,
///     axes: vec![SweepAxis::CouplingStrength(vec![0.5, 1.0, 2.0])],
///     n_steps: 100,
///     dt: 0.01,
///     base_seed: 42,
///     model: SweepModel::Kuramoto,
///     record_trajectory: true,
/// };
/// let results = run_sweep(&config).unwrap();
/// assert_eq!(results.len(), 3);
/// ```
pub fn run_sweep(config: &SweepConfig) -> Result<Vec<SweepResult>, SimError> {
    config.validate()?;

    let n_configs = config.n_configs();
    let indices: Vec<usize> = (0..n_configs).collect();

    let results: Vec<Result<SweepResult, SimError>> = indices
        .into_par_iter()
        .map(|config_idx| run_single_config(config, config_idx))
        .collect();

    let mut ok_results = Vec::with_capacity(n_configs);
    for r in results {
        ok_results.push(r?);
    }
    Ok(ok_results)
}

/// Run a single sweep configuration (called in parallel by `run_sweep`).
fn run_single_config(config: &SweepConfig, config_idx: usize) -> Result<SweepResult, SimError> {
    let param_values = expand_config(&config.axes, config_idx);

    let params: Vec<(String, f64)> = config
        .axes
        .iter()
        .zip(param_values.iter())
        .map(|(axis, &val)| (axis.name().to_string(), val))
        .collect();

    let seed_val = config.base_seed.wrapping_add(config_idx as u64);
    let mut seed = Seed::new(seed_val as u128, 0);

    let coupling = SparseCoupling::from_ring(
        config.n_oscillators,
        config.half_k,
        get_coupling_strength(&params, 1.0)?,
    )?;

    let state = OscillatorState::create_random(config.n_oscillators, (0.5, 5.0), &mut seed)
        .map_err(SimError::Dynamics)?;

    let integrator: Box<dyn Integrator> = Box::new(RK4Integrator::new());

    let mut engine = OscilloSim::new(state, coupling, integrator, config.dt)?;

    let model_result = match config.model {
        SweepModel::Kuramoto => {
            let decay = get_param(&params, "decay_rate", 0.1);
            let gamma = get_param(&params, "freq_adaptation_rate", 0.01);
            let model = SparseKuramoto::new(
                config.n_oscillators,
                decay,
                gamma,
                engine.coupling().clone(),
            )?;
            engine.run(&model, config.n_steps, config.record_trajectory)
        }
        SweepModel::StuartLandau => {
            let mu = get_param(&params, "bifurcation_param", 1.0);
            let model =
                SparseStuartLandau::new(config.n_oscillators, mu, engine.coupling().clone())?;
            engine.run(&model, config.n_steps, config.record_trajectory)
        }
    };

    let (final_state, trajectory) = model_result?;

    let final_r = order_parameter(&final_state.phase);

    let (mean_r, osc_detected) = if let Some(ref traj) = trajectory {
        let r_series: Vec<f64> = traj.phases.iter().map(|p| order_parameter(p)).collect();
        let mean = r_series.iter().sum::<f64>() / r_series.len() as f64;
        let osc = detect_oscillation(&r_series, 20, 0.01);
        (Some(mean), osc)
    } else {
        (None, false)
    };

    let _ = params; // suppress warning; params already moved into result
    let param_report: Vec<(String, f64)> = config
        .axes
        .iter()
        .zip(param_values.iter())
        .map(|(axis, &val)| (axis.name().to_string(), val))
        .collect();

    Ok(SweepResult {
        config_index: config_idx,
        params: param_report,
        final_order_parameter: final_r,
        mean_order_parameter: mean_r,
        oscillation_detected: osc_detected,
        n_steps: config.n_steps,
        seed: seed_val,
    })
}

/// Extract coupling strength from params, defaulting to `default`.
fn get_coupling_strength(params: &[(String, f64)], default: f64) -> Result<f64, SimError> {
    Ok(get_param(params, "coupling_strength", default))
}

/// Extract a named parameter from the params list, defaulting if absent.
fn get_param(params: &[(String, f64)], name: &str, default: f64) -> f64 {
    params
        .iter()
        .find(|(n, _)| n == name)
        .map(|(_, v)| *v)
        .unwrap_or(default)
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn detect_oscillation_stable() {
        let stable = vec![0.8_f64; 30];
        assert!(!detect_oscillation(&stable, 20, 0.01));
    }

    #[test]
    fn detect_oscillation_oscillating() {
        let oscillating: Vec<f64> = (0..30).map(|i| (i as f64 * 0.5).sin()).collect();
        assert!(detect_oscillation(&oscillating, 20, 0.01));
    }

    #[test]
    fn detect_oscillation_short_history() {
        let short = vec![0.5, 0.6, 0.7];
        assert!(!detect_oscillation(&short, 20, 0.01));
    }

    #[test]
    fn detect_oscillation_zero_window() {
        let data = vec![0.5; 10];
        assert!(!detect_oscillation(&data, 0, 0.01));
    }

    #[test]
    fn sweep_config_n_configs_single_axis() {
        let config = SweepConfig {
            n_oscillators: 8,
            half_k: 2,
            axes: vec![SweepAxis::CouplingStrength(vec![0.5, 1.0, 2.0])],
            n_steps: 10,
            dt: 0.01,
            base_seed: 0,
            model: SweepModel::Kuramoto,
            record_trajectory: false,
        };
        assert_eq!(config.n_configs(), 3);
    }

    #[test]
    fn sweep_config_n_configs_multi_axis() {
        let config = SweepConfig {
            n_oscillators: 8,
            half_k: 2,
            axes: vec![
                SweepAxis::CouplingStrength(vec![0.5, 1.0]),
                SweepAxis::DecayRate(vec![0.1, 0.2, 0.3]),
            ],
            n_steps: 10,
            dt: 0.01,
            base_seed: 0,
            model: SweepModel::Kuramoto,
            record_trajectory: false,
        };
        assert_eq!(config.n_configs(), 6);
    }

    #[test]
    fn sweep_config_validate_empty_axes() {
        let config = SweepConfig {
            n_oscillators: 8,
            half_k: 2,
            axes: vec![],
            n_steps: 10,
            dt: 0.01,
            base_seed: 0,
            model: SweepModel::Kuramoto,
            record_trajectory: false,
        };
        assert!(config.validate().is_err());
    }

    #[test]
    fn sweep_config_validate_non_finite_value() {
        let config = SweepConfig {
            n_oscillators: 8,
            half_k: 2,
            axes: vec![SweepAxis::CouplingStrength(vec![1.0, f64::NAN])],
            n_steps: 10,
            dt: 0.01,
            base_seed: 0,
            model: SweepModel::Kuramoto,
            record_trajectory: false,
        };
        assert!(config.validate().is_err());
    }

    #[test]
    fn sweep_kuramoto_basic() {
        let config = SweepConfig {
            n_oscillators: 16,
            half_k: 2,
            axes: vec![SweepAxis::CouplingStrength(vec![0.5, 1.0, 2.0])],
            n_steps: 50,
            dt: 0.01,
            base_seed: 42,
            model: SweepModel::Kuramoto,
            record_trajectory: true,
        };
        let results = run_sweep(&config).unwrap();
        assert_eq!(results.len(), 3);
        for r in &results {
            assert!(r.final_order_parameter >= 0.0);
            assert!(r.final_order_parameter <= 1.0);
            assert!(r.mean_order_parameter.is_some());
            assert_eq!(r.n_steps, 50);
        }
    }

    #[test]
    fn sweep_stuart_landau_basic() {
        let config = SweepConfig {
            n_oscillators: 16,
            half_k: 2,
            axes: vec![SweepAxis::BifurcationParam(vec![0.5, 1.0, 1.5])],
            n_steps: 50,
            dt: 0.01,
            base_seed: 42,
            model: SweepModel::StuartLandau,
            record_trajectory: true,
        };
        let results = run_sweep(&config).unwrap();
        assert_eq!(results.len(), 3);
        for r in &results {
            assert!(r.final_order_parameter >= 0.0);
            assert!(r.final_order_parameter <= 1.0);
        }
    }

    #[test]
    fn sweep_deterministic() {
        let config = SweepConfig {
            n_oscillators: 16,
            half_k: 2,
            axes: vec![SweepAxis::CouplingStrength(vec![1.0, 2.0])],
            n_steps: 20,
            dt: 0.01,
            base_seed: 99,
            model: SweepModel::Kuramoto,
            record_trajectory: true,
        };
        let r1 = run_sweep(&config).unwrap();
        let r2 = run_sweep(&config).unwrap();
        assert_eq!(r1.len(), r2.len());
        for (a, b) in r1.iter().zip(r2.iter()) {
            assert_eq!(a.config_index, b.config_index);
            assert!((a.final_order_parameter - b.final_order_parameter).abs() < 1e-14);
            assert_eq!(a.seed, b.seed);
        }
    }

    #[test]
    fn sweep_multi_axis_cartesian_product() {
        let config = SweepConfig {
            n_oscillators: 8,
            half_k: 2,
            axes: vec![
                SweepAxis::CouplingStrength(vec![0.5, 1.0]),
                SweepAxis::DecayRate(vec![0.1, 0.2]),
            ],
            n_steps: 10,
            dt: 0.01,
            base_seed: 0,
            model: SweepModel::Kuramoto,
            record_trajectory: false,
        };
        let results = run_sweep(&config).unwrap();
        assert_eq!(results.len(), 4);
        // Check that all 4 combinations are present
        let param_sets: Vec<Vec<(String, f64)>> =
            results.iter().map(|r| r.params.clone()).collect();
        assert!(param_sets.iter().any(|p| {
            p.iter()
                .any(|(n, v)| n == "coupling_strength" && (*v - 0.5).abs() < 1e-12)
                && p.iter()
                    .any(|(n, v)| n == "decay_rate" && (*v - 0.1).abs() < 1e-12)
        }));
        assert!(param_sets.iter().any(|p| {
            p.iter()
                .any(|(n, v)| n == "coupling_strength" && (*v - 1.0).abs() < 1e-12)
                && p.iter()
                    .any(|(n, v)| n == "decay_rate" && (*v - 0.2).abs() < 1e-12)
        }));
    }

    #[test]
    fn expand_config_single_axis() {
        let axes = vec![SweepAxis::CouplingStrength(vec![0.5, 1.0, 2.0])];
        assert!((expand_config(&axes, 0)[0] - 0.5).abs() < 1e-12);
        assert!((expand_config(&axes, 1)[0] - 1.0).abs() < 1e-12);
        assert!((expand_config(&axes, 2)[0] - 2.0).abs() < 1e-12);
    }

    #[test]
    fn expand_config_multi_axis() {
        let axes = vec![
            SweepAxis::CouplingStrength(vec![0.5, 1.0]),
            SweepAxis::DecayRate(vec![0.1, 0.2, 0.3]),
        ];
        // 2 × 3 = 6 configs; row-major: (0.5, 0.1), (0.5, 0.2), (0.5, 0.3), (1.0, 0.1), ...
        let v0 = expand_config(&axes, 0);
        assert!((v0[0] - 0.5).abs() < 1e-12);
        assert!((v0[1] - 0.1).abs() < 1e-12);
        let v3 = expand_config(&axes, 3);
        assert!((v3[0] - 1.0).abs() < 1e-12);
        assert!((v3[1] - 0.1).abs() < 1e-12);
    }

    #[test]
    fn order_parameter_synchronized() {
        let phase = vec![0.5_f64; 100];
        let r = order_parameter(&phase);
        assert!((r - 1.0).abs() < 1e-12);
    }

    #[test]
    fn order_parameter_uniform_spread() {
        let n = 1000;
        let phase: Vec<f64> = (0..n)
            .map(|i| 2.0 * std::f64::consts::PI * i as f64 / n as f64)
            .collect();
        let r = order_parameter(&phase);
        assert!(r < 0.01, "uniform spread should have r ≈ 0, got {r}");
    }

    #[test]
    fn sweep_no_trajectory() {
        let config = SweepConfig {
            n_oscillators: 8,
            half_k: 2,
            axes: vec![SweepAxis::CouplingStrength(vec![1.0])],
            n_steps: 10,
            dt: 0.01,
            base_seed: 0,
            model: SweepModel::Kuramoto,
            record_trajectory: false,
        };
        let results = run_sweep(&config).unwrap();
        assert_eq!(results.len(), 1);
        assert!(results[0].mean_order_parameter.is_none());
        assert!(!results[0].oscillation_detected);
    }

    #[test]
    fn sweep_axis_name() {
        assert_eq!(
            SweepAxis::CouplingStrength(vec![]).name(),
            "coupling_strength"
        );
        assert_eq!(SweepAxis::DecayRate(vec![]).name(), "decay_rate");
        assert_eq!(
            SweepAxis::FreqAdaptationRate(vec![]).name(),
            "freq_adaptation_rate"
        );
        assert_eq!(
            SweepAxis::BifurcationParam(vec![]).name(),
            "bifurcation_param"
        );
    }
}
