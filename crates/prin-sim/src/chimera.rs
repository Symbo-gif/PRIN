//! Chimera-state detection for large oscillator systems.
//!
//! Integrates the chimera metrics from `prin-metrics` with the CSR sparse
//! coupling structure from [`SparseCoupling`]. The neighbor list for
//! local-order-parameter computation is extracted from the CSR sparsity
//! pattern, so no separate k-NN index is needed when the coupling matrix
//! already encodes the spatial adjacency.
//!
//! ## Metrics
//!
//! - **Local order parameter** `r_i`: per-oscillator coherence from
//!   `prin-metrics::local_order_parameter`.
//! - **Bimodality index**: Sarle's BC on the local-order-parameter distribution.
//! - **Strength of incoherence** (SI): Gopal et al. 2014, computed on the
//!   phase field.
//! - **Discontinuity measure** (chimera number η): coherent-to-incoherent
//!   transition count.
//! - **Chimera index** χ: fraction of oscillators with `r_i < threshold`.

use prin_dynamics::OscillatorState;
use prin_metrics::{
    bimodality_index, chimera_index, discontinuity_measure, local_order_parameter,
    strength_of_incoherence,
};
use serde::{Deserialize, Serialize};

use crate::csr_coupling::SparseCoupling;
use crate::error::SimError;

/// Snapshot of chimera-state metrics for a single time point.
///
/// All fields are in their natural ranges:
/// - `local_order`: `[0, 1]` per oscillator.
/// - `bimodality`: `[0, ∞)`; values above `5/9 ≈ 0.555` suggest bimodality.
/// - `strength_of_incoherence`: `[0, 1]`.
/// - `discontinuity`: non-negative integer (chimera number η).
/// - `chimera_index`: `[0, 1]`.
#[derive(Clone, Debug, PartialEq, Serialize, Deserialize)]
pub struct ChimeraMetrics {
    /// Per-oscillator local order parameter.
    pub local_order: Vec<f64>,

    /// Sarle's bimodality coefficient of the local-order-parameter distribution.
    pub bimodality: f64,

    /// Strength of incoherence (Gopal et al. 2014).
    pub strength_of_incoherence: f64,

    /// Chimera number η (coherent-to-incoherent transition count / 2).
    pub discontinuity: usize,

    /// Chimera index χ (fraction of incoherent oscillators).
    pub chimera_index: f64,
}

/// Compute all chimera metrics for the current state using the CSR coupling
/// pattern as the spatial neighbor structure.
///
/// The neighbor list is extracted from the CSR sparsity pattern of `coupling`.
/// Each oscillator's neighbors are the column indices of the non-zero entries
/// in its row.
///
/// # Arguments
///
/// - `state`: current oscillator state.
/// - `coupling`: CSR coupling matrix whose sparsity pattern defines spatial
///   adjacency.
/// - `chimera_threshold`: coherence threshold for the chimera index (typical
///   value: `0.5`).
/// - `si_window`: window size for the strength-of-incoherence computation
///   (typical value: `N / 10` or similar).
/// - `disc_threshold_ratio`: threshold ratio for the discontinuity measure
///   (typical value: `0.01`).
///
/// # Errors
///
/// Returns [`SimError`] if the coupling has isolated oscillators, the state
/// and coupling have different dimensions, or any metric computation fails.
pub fn compute_chimera_metrics(
    state: &OscillatorState,
    coupling: &SparseCoupling,
    chimera_threshold: f64,
    si_window: usize,
    disc_threshold_ratio: f64,
) -> Result<ChimeraMetrics, SimError> {
    let n = state.n_oscillators();
    if coupling.n_oscillators() != n {
        return Err(SimError::DimensionMismatch {
            name: "coupling vs state",
            expected: n,
            got: coupling.n_oscillators(),
        });
    }

    let neighbors = coupling.neighbor_list()?;

    let local_order = local_order_parameter(&state.phase, &neighbors).map_err(SimError::Metric)?;

    let bimodality = bimodality_index(&local_order).map_err(SimError::Metric)?;

    let si = if n >= 3 && si_window > 0 {
        strength_of_incoherence(&state.phase, si_window).map_err(SimError::Metric)?
    } else {
        0.0
    };

    let (_, disc) =
        discontinuity_measure(&state.phase, disc_threshold_ratio).map_err(SimError::Metric)?;

    let chi =
        chimera_index(&state.phase, &neighbors, chimera_threshold).map_err(SimError::Metric)?;

    Ok(ChimeraMetrics {
        local_order,
        bimodality,
        strength_of_incoherence: si,
        discontinuity: disc,
        chimera_index: chi,
    })
}

/// Compute chimera metrics over a trajectory, returning one [`ChimeraMetrics`]
/// per recorded step.
///
/// # Errors
///
/// Returns [`SimError`] if any step's metric computation fails.
pub fn trajectory_chimera_metrics(
    phases: &[Vec<f64>],
    coupling: &SparseCoupling,
    chimera_threshold: f64,
    si_window: usize,
    disc_threshold_ratio: f64,
) -> Result<Vec<ChimeraMetrics>, SimError> {
    let n = coupling.n_oscillators();
    let neighbors = coupling.neighbor_list()?;
    let mut results = Vec::with_capacity(phases.len());

    for step_phases in phases {
        if step_phases.len() != n {
            return Err(SimError::DimensionMismatch {
                name: "trajectory phase",
                expected: n,
                got: step_phases.len(),
            });
        }

        let local_order =
            local_order_parameter(step_phases, &neighbors).map_err(SimError::Metric)?;
        let bimodality = bimodality_index(&local_order).map_err(SimError::Metric)?;
        let si = if n >= 3 && si_window > 0 {
            strength_of_incoherence(step_phases, si_window).map_err(SimError::Metric)?
        } else {
            0.0
        };
        let (_, disc) =
            discontinuity_measure(step_phases, disc_threshold_ratio).map_err(SimError::Metric)?;
        let chi =
            chimera_index(step_phases, &neighbors, chimera_threshold).map_err(SimError::Metric)?;

        results.push(ChimeraMetrics {
            local_order,
            bimodality,
            strength_of_incoherence: si,
            discontinuity: disc,
            chimera_index: chi,
        });
    }

    Ok(results)
}

#[cfg(test)]
mod tests {
    use super::*;

    fn ring_coupling(n: usize, half_k: usize) -> SparseCoupling {
        SparseCoupling::from_ring(n, half_k, 1.0).unwrap()
    }

    fn sync_state(n: usize) -> OscillatorState {
        OscillatorState::new(vec![0.0; n], vec![1.0; n], vec![1.0; n], None).unwrap()
    }

    #[test]
    fn synchronized_has_no_chimera() {
        let n = 16;
        let coupling = ring_coupling(n, 2);
        let state = sync_state(n);
        let metrics = compute_chimera_metrics(&state, &coupling, 0.5, 4, 0.01).unwrap();
        assert_eq!(metrics.chimera_index, 0.0);
        assert_eq!(metrics.discontinuity, 0);
        for &r in &metrics.local_order {
            assert!((r - 1.0).abs() < 1e-12);
        }
    }

    #[test]
    fn dimension_mismatch_rejected() {
        let coupling = ring_coupling(8, 2);
        let state = sync_state(16);
        let err = compute_chimera_metrics(&state, &coupling, 0.5, 4, 0.01).unwrap_err();
        assert!(matches!(err, SimError::DimensionMismatch { .. }));
    }

    #[test]
    fn trajectory_metrics_length() {
        let n = 12;
        let coupling = ring_coupling(n, 2);
        let phases = vec![vec![0.0; n]; 5];
        let metrics = trajectory_chimera_metrics(&phases, &coupling, 0.5, 3, 0.01).unwrap();
        assert_eq!(metrics.len(), 5);
    }

    #[test]
    fn trajectory_dimension_mismatch() {
        let coupling = ring_coupling(8, 2);
        let phases = vec![vec![0.0; 16]];
        let err = trajectory_chimera_metrics(&phases, &coupling, 0.5, 3, 0.01).unwrap_err();
        assert!(matches!(err, SimError::DimensionMismatch { .. }));
    }

    #[test]
    fn small_system_si_zero() {
        let n = 4;
        let coupling = SparseCoupling::from_ring(n, 1, 1.0).unwrap();
        let state = sync_state(n);
        let metrics = compute_chimera_metrics(&state, &coupling, 0.5, 0, 0.01).unwrap();
        assert_eq!(metrics.strength_of_incoherence, 0.0);
    }

    #[test]
    fn n2_si_zero_even_with_window() {
        // n < 3 should give si = 0.0 even when si_window > 0
        let n = 2;
        // from_ring(2, 1, _) fails because degree=2 >= n=2, so build manually
        let indptr = vec![0, 1, 2];
        let indices = vec![1, 0];
        let data = vec![1.0, 1.0];
        let coupling = SparseCoupling::from_csr(&indptr, &indices, &data, n).unwrap();
        let state = sync_state(n);
        let metrics = compute_chimera_metrics(&state, &coupling, 0.5, 5, 0.01).unwrap();
        assert_eq!(metrics.strength_of_incoherence, 0.0);
    }

    #[test]
    fn chimera_metrics_with_desynchronized_phases() {
        use std::f64::consts::TAU;
        let n = 16;
        let coupling = ring_coupling(n, 2);
        // Spread phases uniformly around the circle
        let phases: Vec<f64> = (0..n).map(|i| TAU * (i as f64) / (n as f64)).collect();
        let state = OscillatorState::new(phases, vec![1.0; n], vec![1.0; n], None).unwrap();
        let metrics = compute_chimera_metrics(&state, &coupling, 0.5, 4, 0.01).unwrap();
        // Uniform phases should have low local order parameter for each oscillator
        assert!(metrics.bimodality >= 0.0);
        assert!((0.0..=1.0).contains(&metrics.chimera_index));
    }

    #[test]
    fn trajectory_metrics_empty_phases() {
        let n = 8;
        let coupling = ring_coupling(n, 2);
        let phases: Vec<Vec<f64>> = vec![];
        let metrics = trajectory_chimera_metrics(&phases, &coupling, 0.5, 3, 0.01).unwrap();
        assert!(metrics.is_empty());
    }

    #[test]
    fn chimera_metrics_serialization_round_trip() {
        let n = 12;
        let coupling = ring_coupling(n, 2);
        let state = sync_state(n);
        let metrics = compute_chimera_metrics(&state, &coupling, 0.5, 3, 0.01).unwrap();
        let json = serde_json::to_string(&metrics).unwrap();
        let deserialized: ChimeraMetrics = serde_json::from_str(&json).unwrap();
        assert_eq!(deserialized, metrics);
    }

    #[test]
    fn trajectory_si_zero_when_window_zero() {
        let n = 12;
        let coupling = ring_coupling(n, 2);
        let phases = vec![vec![0.0; n]; 3];
        let metrics = trajectory_chimera_metrics(&phases, &coupling, 0.5, 0, 0.01).unwrap();
        for m in &metrics {
            assert_eq!(m.strength_of_incoherence, 0.0);
        }
    }
}
