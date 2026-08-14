//! Property-based tests for the sparse simulation engine.
//!
//! Uses `proptest` to verify invariants over arbitrary inputs:
//! - Sparse-vs-dense Kuramoto parity at arbitrary N and ring degree.
//! - `memory_bytes()` correctness for arbitrary N and nnz.
//! - Determinism for arbitrary seeds.

use approx::assert_relative_eq;
use proptest::prelude::*;

use prin_dynamics::models::{Dynamics, KuramotoOscillator};
use prin_dynamics::state::OscillatorState;
use prin_dynamics::{CouplingMode, Seed};
use prin_sim::{OscilloSim, SparseCoupling, SparseKuramoto};

/// Build a dense coupling matrix for a ring topology.
fn ring_dense(n: usize, half_k: usize, strength: f64) -> Vec<f64> {
    let degree = 2 * half_k;
    let w = strength / (degree as f64);
    let mut mat = vec![0.0; n * n];
    for i in 0..n {
        for d in 1..=half_k {
            let left = (i + n - d) % n;
            let right = (i + d) % n;
            mat[i * n + left] = w;
            mat[i * n + right] = w;
        }
    }
    mat
}

/// Strategy for valid (n, half_k) pairs: n >= 3, 1 <= half_k < n/2.
fn valid_n_half_k() -> impl Strategy<Value = (usize, usize)> {
    (3..64usize).prop_flat_map(|n| {
        let max_half_k = (n - 1) / 2;
        (Just(n), 1..=max_half_k)
    })
}

proptest! {
    /// Sparse-vs-dense Kuramoto derivatives match at arbitrary N and ring degree.
    #[test]
    fn kuramoto_parity_arbitrary_n(
        (n, half_k) in valid_n_half_k(),
        seed_val in 0..1000u128,
    ) {
        let strength = 1.5;
        let decay = 0.1;
        let freq_adapt = 0.01;

        let mut seed = Seed::new(seed_val, 0);
        let state = OscillatorState::create_random(n, (0.5, 5.0), &mut seed).unwrap();

        let dense_mat = ring_dense(n, half_k, strength);
        let dense_model = KuramotoOscillator::new(
            n, strength, decay, freq_adapt,
            CouplingMode::Full { matrix: Some(dense_mat) },
        ).unwrap();
        let dense_derivs = dense_model.compute_derivatives(&state).unwrap();

        let sparse_coupling = SparseCoupling::from_ring(n, half_k, strength).unwrap();
        let sparse_model = SparseKuramoto::new(n, decay, freq_adapt, sparse_coupling).unwrap();
        let sparse_derivs = sparse_model.compute_derivatives(&state).unwrap();

        for i in 0..n {
            assert_relative_eq!(
                sparse_derivs.dphase[i], dense_derivs.dphase[i],
                epsilon = 1e-10,
            );
            assert_relative_eq!(
                sparse_derivs.damplitude[i], dense_derivs.damplitude[i],
                epsilon = 1e-10,
            );
            assert_relative_eq!(
                sparse_derivs.dfrequency[i], dense_derivs.dfrequency[i],
                epsilon = 1e-10,
            );
        }
    }

    /// `memory_bytes()` returns the correct footprint for arbitrary N and ring degree.
    #[test]
    fn memory_bytes_correct_for_ring(
        (n, half_k) in valid_n_half_k(),
    ) {
        let coupling = SparseCoupling::from_ring(n, half_k, 1.0).unwrap();

        // Ring CSR: each row has exactly 2*half_k entries → nnz = n * 2*half_k.
        let expected_nnz = n * 2 * half_k;
        assert_eq!(coupling.nnz(), expected_nnz);

        // memory_bytes for CSR = nnz * (sizeof(f64) + sizeof(usize)) + (n+1) * sizeof(usize)
        let expected_bytes = expected_nnz * (std::mem::size_of::<f64>() + std::mem::size_of::<usize>())
            + (n + 1) * std::mem::size_of::<usize>();
        assert_eq!(coupling.memory_bytes(), expected_bytes);
    }

    /// Engine produces identical trajectories for the same seed, at arbitrary N.
    #[test]
    fn determinism_arbitrary_n_and_seed(
        (n, half_k) in valid_n_half_k(),
        seed_a in 0..10_000u128,
        seed_b in 0..10_000u128,
    ) {
        // Only compare when seeds match (determinism: same seed → same result).
        let seed_val = seed_a.min(seed_b);
        let coupling = SparseCoupling::from_ring(n, half_k, 1.0).unwrap();
        let model = SparseKuramoto::new(n, 0.1, 0.01, coupling.clone()).unwrap();

        let state_a = OscillatorState::create_random(n, (0.5, 5.0), &mut Seed::new(seed_val, 0)).unwrap();
        let state_b = OscillatorState::create_random(n, (0.5, 5.0), &mut Seed::new(seed_val, 0)).unwrap();

        let integrator_a = Box::new(prin_dynamics::RK4Integrator::new());
        let integrator_b = Box::new(prin_dynamics::RK4Integrator::new());
        let mut engine_a = OscilloSim::new(state_a, coupling.clone(), integrator_a, 0.01).unwrap();
        let mut engine_b = OscilloSim::new(state_b, coupling, integrator_b, 0.01).unwrap();

        let (_, traj_a) = engine_a.run(&model, 10, true).unwrap();
        let (_, traj_b) = engine_b.run(&model, 10, true).unwrap();

        let ta = traj_a.unwrap();
        let tb = traj_b.unwrap();
        prop_assert_eq!(ta.phases, tb.phases);
        prop_assert_eq!(ta.amplitudes, tb.amplitudes);
    }

    /// Engine memory_bytes is positive and consistent with state + coupling sizes.
    #[test]
    fn engine_memory_bytes_consistent(
        (n, half_k) in valid_n_half_k(),
    ) {
        let coupling = SparseCoupling::from_ring(n, half_k, 1.0).unwrap();
        let model = SparseKuramoto::new(n, 0.1, 0.01, coupling.clone()).unwrap();
        let state = OscillatorState::create_random(n, (0.5, 5.0), &mut Seed::new(42, 0)).unwrap();
        let integrator = Box::new(prin_dynamics::RK4Integrator::new());
        let engine = OscilloSim::new(state, coupling.clone(), integrator, 0.01).unwrap();

        let expected = n * 3 * std::mem::size_of::<f64>() + coupling.memory_bytes();
        prop_assert_eq!(engine.memory_bytes(), expected);
        prop_assert!(engine.memory_bytes() > 0);

        let _ = model;
    }
}
