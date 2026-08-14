//! Parity tests: sparse CSR coupling vs dense dynamics from `prin-dynamics`.
//!
//! These tests verify that the sparse coupling computations in `prin-sim`
//! produce numerically equivalent results to the dense implementations in
//! `prin-dynamics` when given the same coupling weights.

use approx::assert_relative_eq;
use prin_dynamics::models::{Dynamics, KuramotoOscillator, StuartLandauOscillator};
use prin_dynamics::state::OscillatorState;
use prin_dynamics::{CouplingMode, RK4Integrator, Seed};
use prin_sim::{OscilloSim, SparseCoupling, SparseKuramoto, SparseStuartLandau};

/// Build a dense coupling matrix for a ring topology with `half_k` neighbours
/// on each side and weight `strength / (2 * half_k)`.
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

// ────────────────────────────────────────────────────────────────────────────
// Kuramoto parity
// ────────────────────────────────────────────────────────────────────────────

#[test]
fn kuramoto_parity_n8_ring() {
    let n = 8;
    let half_k = 2;
    let strength = 1.5;
    let decay = 0.1;
    let freq_adapt = 0.01;

    let mut seed = Seed::new(42, 0);
    let state = OscillatorState::create_random(n, (0.5, 5.0), &mut seed).unwrap();

    // Dense reference
    let dense_mat = ring_dense(n, half_k, strength);
    let dense_model = KuramotoOscillator::new(
        n,
        strength,
        decay,
        freq_adapt,
        CouplingMode::Full {
            matrix: Some(dense_mat),
        },
    )
    .unwrap();
    let dense_derivs = dense_model.compute_derivatives(&state).unwrap();

    // Sparse
    let sparse_coupling = SparseCoupling::from_ring(n, half_k, strength).unwrap();
    let sparse_model = SparseKuramoto::new(n, decay, freq_adapt, sparse_coupling).unwrap();
    let sparse_derivs = sparse_model.compute_derivatives(&state).unwrap();

    for i in 0..n {
        assert_relative_eq!(
            sparse_derivs.dphase[i],
            dense_derivs.dphase[i],
            epsilon = 1e-12
        );
        assert_relative_eq!(
            sparse_derivs.damplitude[i],
            dense_derivs.damplitude[i],
            epsilon = 1e-12
        );
        assert_relative_eq!(
            sparse_derivs.dfrequency[i],
            dense_derivs.dfrequency[i],
            epsilon = 1e-12
        );
    }
}

#[test]
fn kuramoto_parity_n64_ring() {
    let n = 64;
    let half_k = 4;
    let strength = 2.0;
    let decay = 0.05;
    let freq_adapt = 0.005;

    let mut seed = Seed::new(123, 7);
    let state = OscillatorState::create_random(n, (1.0, 10.0), &mut seed).unwrap();

    let dense_mat = ring_dense(n, half_k, strength);
    let dense_model = KuramotoOscillator::new(
        n,
        strength,
        decay,
        freq_adapt,
        CouplingMode::Full {
            matrix: Some(dense_mat),
        },
    )
    .unwrap();
    let dense_derivs = dense_model.compute_derivatives(&state).unwrap();

    let sparse_coupling = SparseCoupling::from_ring(n, half_k, strength).unwrap();
    let sparse_model = SparseKuramoto::new(n, decay, freq_adapt, sparse_coupling).unwrap();
    let sparse_derivs = sparse_model.compute_derivatives(&state).unwrap();

    for i in 0..n {
        assert_relative_eq!(
            sparse_derivs.dphase[i],
            dense_derivs.dphase[i],
            epsilon = 1e-12
        );
        assert_relative_eq!(
            sparse_derivs.damplitude[i],
            dense_derivs.damplitude[i],
            epsilon = 1e-12
        );
        assert_relative_eq!(
            sparse_derivs.dfrequency[i],
            dense_derivs.dfrequency[i],
            epsilon = 1e-12
        );
    }
}

#[test]
fn kuramoto_parity_n256_ring() {
    let n = 256;
    let half_k = 8;
    let strength = 1.0;
    let decay = 0.1;
    let freq_adapt = 0.01;

    let mut seed = Seed::new(999, 1);
    let state = OscillatorState::create_random(n, (0.1, 8.0), &mut seed).unwrap();

    let dense_mat = ring_dense(n, half_k, strength);
    let dense_model = KuramotoOscillator::new(
        n,
        strength,
        decay,
        freq_adapt,
        CouplingMode::Full {
            matrix: Some(dense_mat),
        },
    )
    .unwrap();
    let dense_derivs = dense_model.compute_derivatives(&state).unwrap();

    let sparse_coupling = SparseCoupling::from_ring(n, half_k, strength).unwrap();
    let sparse_model = SparseKuramoto::new(n, decay, freq_adapt, sparse_coupling).unwrap();
    let sparse_derivs = sparse_model.compute_derivatives(&state).unwrap();

    for i in 0..n {
        assert_relative_eq!(
            sparse_derivs.dphase[i],
            dense_derivs.dphase[i],
            epsilon = 1e-10
        );
        assert_relative_eq!(
            sparse_derivs.damplitude[i],
            dense_derivs.damplitude[i],
            epsilon = 1e-10
        );
        assert_relative_eq!(
            sparse_derivs.dfrequency[i],
            dense_derivs.dfrequency[i],
            epsilon = 1e-10
        );
    }
}

// ────────────────────────────────────────────────────────────────────────────
// Stuart–Landau parity
// ────────────────────────────────────────────────────────────────────────────

#[test]
fn stuart_landau_parity_n8_ring() {
    let n = 8;
    let half_k = 2;
    let strength = 0.5;
    let mu = 1.0;

    let mut seed = Seed::new(42, 0);
    let state = OscillatorState::create_random(n, (0.5, 5.0), &mut seed).unwrap();

    let dense_mat = ring_dense(n, half_k, strength);
    let dense_model = StuartLandauOscillator::new(
        n,
        strength,
        mu,
        CouplingMode::Full {
            matrix: Some(dense_mat),
        },
    )
    .unwrap();
    let dense_derivs = dense_model.compute_derivatives(&state).unwrap();

    let sparse_coupling = SparseCoupling::from_ring(n, half_k, strength).unwrap();
    let sparse_model = SparseStuartLandau::new(n, mu, sparse_coupling).unwrap();
    let sparse_derivs = sparse_model.compute_derivatives(&state).unwrap();

    for i in 0..n {
        assert_relative_eq!(
            sparse_derivs.dphase[i],
            dense_derivs.dphase[i],
            epsilon = 1e-10
        );
        assert_relative_eq!(
            sparse_derivs.damplitude[i],
            dense_derivs.damplitude[i],
            epsilon = 1e-10
        );
    }
}

// ────────────────────────────────────────────────────────────────────────────
// Engine trajectory parity
// ────────────────────────────────────────────────────────────────────────────

#[test]
fn engine_trajectory_parity_n16() {
    let n = 16;
    let half_k = 2;
    let strength = 1.0;
    let decay = 0.1;
    let freq_adapt = 0.01;
    let dt = 0.01;
    let n_steps = 100;

    let mut seed = Seed::new(42, 0);
    let state = OscillatorState::create_random(n, (0.5, 5.0), &mut seed).unwrap();

    // Sparse engine trajectory
    let sparse_coupling = SparseCoupling::from_ring(n, half_k, strength).unwrap();
    let sparse_model = SparseKuramoto::new(n, decay, freq_adapt, sparse_coupling.clone()).unwrap();
    let mut engine = OscilloSim::new(
        state.clone(),
        sparse_coupling,
        Box::new(RK4Integrator::new()),
        dt,
    )
    .unwrap();
    let (_, sparse_traj) = engine.run(&sparse_model, n_steps, true).unwrap();
    let sparse_traj = sparse_traj.unwrap();

    // Dense reference trajectory via integrate_fixed
    let dense_mat = ring_dense(n, half_k, strength);
    let dense_model = KuramotoOscillator::new(
        n,
        strength,
        decay,
        freq_adapt,
        CouplingMode::Full {
            matrix: Some(dense_mat),
        },
    )
    .unwrap();
    let mut integrator = RK4Integrator::new();
    let (_, dense_traj) =
        prin_dynamics::integrate_fixed(&mut integrator, &dense_model, &state, n_steps, dt, true)
            .unwrap();
    let dense_traj = dense_traj.unwrap();

    assert_eq!(sparse_traj.phases.len(), dense_traj.len() + 1);
    for (sp, dp) in sparse_traj
        .phases
        .iter()
        .zip(std::iter::once(&state.phase).chain(dense_traj.iter().map(|s| &s.phase)))
    {
        for i in 0..n {
            assert_relative_eq!(sp[i], dp[i], epsilon = 1e-10);
        }
    }
}

// ────────────────────────────────────────────────────────────────────────────
// Large-N memory measurement
// ────────────────────────────────────────────────────────────────────────────

#[test]
fn large_n_memory_bounded() {
    let n = 10_000;
    let half_k = 10;
    let coupling = SparseCoupling::from_ring(n, half_k, 1.0).unwrap();

    let expected_nnz = n * 2 * half_k;
    assert_eq!(coupling.nnz(), expected_nnz);

    let mem = coupling.memory_bytes();
    let expected_mem = (n + 1) * 8 + expected_nnz * 8 + expected_nnz * 8;
    assert_eq!(mem, expected_mem);

    // For N=10k with k=10, memory should be well under 5 MB
    assert!(mem < 5_000_000, "memory {mem} bytes exceeds 5 MB for N={n}");

    let sparsity = coupling.sparsity();
    assert!(
        sparsity > 0.99,
        "sparsity {sparsity} should be > 0.99 for N={n}"
    );
}

// ────────────────────────────────────────────────────────────────────────────
// Deterministic seed flow
// ────────────────────────────────────────────────────────────────────────────

#[test]
fn engine_deterministic_across_runs() {
    let n = 32;
    let dt = 0.01;
    let n_steps = 50;

    let run = || {
        let coupling = SparseCoupling::from_ring(n, 4, 1.0).unwrap();
        let model = SparseKuramoto::new(n, 0.1, 0.01, coupling.clone()).unwrap();
        let state = OscillatorState::create_random(n, (0.5, 5.0), &mut Seed::new(42, 0)).unwrap();
        let mut engine =
            OscilloSim::new(state, coupling, Box::new(RK4Integrator::new()), dt).unwrap();
        let (_, traj) = engine.run(&model, n_steps, true).unwrap();
        traj.unwrap().phases
    };

    let t1 = run();
    let t2 = run();
    assert_eq!(t1, t2);
}

// ────────────────────────────────────────────────────────────────────────────
// Chimera metrics integration
// ────────────────────────────────────────────────────────────────────────────

#[test]
fn chimera_metrics_on_engine_trajectory() {
    let n = 32;
    let coupling = SparseCoupling::from_ring(n, 4, 1.0).unwrap();
    let model = SparseKuramoto::new(n, 0.1, 0.01, coupling.clone()).unwrap();
    let state = OscillatorState::create_random(n, (0.5, 5.0), &mut Seed::new(42, 0)).unwrap();
    let mut engine = OscilloSim::new(
        state,
        coupling.clone(),
        Box::new(RK4Integrator::new()),
        0.01,
    )
    .unwrap();
    let (_, traj) = engine.run(&model, 20, true).unwrap();
    let traj = traj.unwrap();

    let metrics =
        prin_sim::trajectory_chimera_metrics(&traj.phases, &coupling, 0.5, 4, 0.01).unwrap();
    assert_eq!(metrics.len(), traj.n_steps());

    for m in &metrics {
        assert!((0.0..=1.0).contains(&m.chimera_index));
        assert!(m.bimodality >= 0.0);
        assert!((0.0..=1.0).contains(&m.strength_of_incoherence));
    }
}

// ────────────────────────────────────────────────────────────────────────────
// SparseCoupling construction error paths
// ────────────────────────────────────────────────────────────────────────────

#[test]
fn from_knn_empty_rejected() {
    let err = SparseCoupling::from_knn(&[], 2, 1.0).unwrap_err();
    assert!(format!("{err}").contains("n >= 1"));
}

#[test]
fn from_knn_k_too_large_rejected() {
    let phases = vec![0.0, 1.0, 2.0];
    let err = SparseCoupling::from_knn(&phases, 5, 1.0).unwrap_err();
    assert!(format!("{err}").contains("dimension mismatch"));
}

#[test]
fn from_csr_n_zero_rejected() {
    let err = SparseCoupling::from_csr(&[0], &[], &[], 0).unwrap_err();
    assert!(format!("{err}").contains("n >= 1"));
}

#[test]
fn from_dense_wrong_length_rejected() {
    let err = SparseCoupling::from_dense(&[1.0, 2.0], 2, 0.0).unwrap_err();
    assert!(format!("{err}").contains("dimension mismatch"));
}

#[test]
fn from_ring_infinite_strength_rejected() {
    let err = SparseCoupling::from_ring(8, 2, f64::INFINITY).unwrap_err();
    assert!(format!("{err}").contains("non-finite"));
}

// ────────────────────────────────────────────────────────────────────────────
// SparseCoupling::submatrix
// ────────────────────────────────────────────────────────────────────────────

#[test]
fn submatrix_preserves_weights() {
    let n = 8;
    let coupling = SparseCoupling::from_ring(n, 2, 1.0).unwrap();
    let kept = vec![0, 2, 4, 6];
    let sub = coupling.submatrix(&kept).unwrap();
    assert_eq!(sub.n_oscillators(), 4);
    // Each kept oscillator had 2 neighbors in the ring; the submatrix should
    // only keep entries where both row and column are in `kept`.
    assert!(sub.nnz() > 0);
    assert!(sub.nnz() <= coupling.nnz());
}

#[test]
fn submatrix_out_of_range_rejected() {
    let coupling = SparseCoupling::from_ring(4, 1, 1.0).unwrap();
    let err = coupling.submatrix(&[0, 100]).unwrap_err();
    assert!(format!("{err}").contains("dimension mismatch"));
}

// ────────────────────────────────────────────────────────────────────────────
// SparseKuramoto / SparseStuartLandau parity for small N
// ────────────────────────────────────────────────────────────────────────────

#[test]
fn stuart_landau_parity_n16_ring() {
    let n = 16;
    let half_k = 2;
    let strength = 0.8;
    let mu = 0.5;

    let mut seed = Seed::new(77, 3);
    let state = OscillatorState::create_random(n, (0.5, 5.0), &mut seed).unwrap();

    let dense_mat = ring_dense(n, half_k, strength);
    let dense_model = StuartLandauOscillator::new(
        n,
        strength,
        mu,
        CouplingMode::Full {
            matrix: Some(dense_mat),
        },
    )
    .unwrap();
    let dense_derivs = dense_model.compute_derivatives(&state).unwrap();

    let sparse_coupling = SparseCoupling::from_ring(n, half_k, strength).unwrap();
    let sparse_model = SparseStuartLandau::new(n, mu, sparse_coupling).unwrap();
    let sparse_derivs = sparse_model.compute_derivatives(&state).unwrap();

    for i in 0..n {
        assert_relative_eq!(
            sparse_derivs.dphase[i],
            dense_derivs.dphase[i],
            epsilon = 1e-10
        );
        assert_relative_eq!(
            sparse_derivs.damplitude[i],
            dense_derivs.damplitude[i],
            epsilon = 1e-10
        );
    }
}

// ────────────────────────────────────────────────────────────────────────────
// Engine error paths
// ────────────────────────────────────────────────────────────────────────────

#[test]
fn engine_rejects_negative_dt() {
    let n = 8;
    let coupling = SparseCoupling::from_ring(n, 2, 1.0).unwrap();
    let state = OscillatorState::create_random(n, (0.5, 5.0), &mut Seed::new(0, 0)).unwrap();
    let result = OscilloSim::new(state, coupling, Box::new(RK4Integrator::new()), -0.01);
    assert!(result.is_err());
}

#[test]
fn engine_rejects_coupling_state_size_mismatch() {
    let coupling = SparseCoupling::from_ring(4, 1, 1.0).unwrap();
    let state = OscillatorState::create_random(8, (0.5, 5.0), &mut Seed::new(0, 0)).unwrap();
    let result = OscilloSim::new(state, coupling, Box::new(RK4Integrator::new()), 0.01);
    assert!(result.is_err());
}

// ────────────────────────────────────────────────────────────────────────────
// Pruning integration
// ────────────────────────────────────────────────────────────────────────────

#[test]
fn pruning_strategy_validates_range() {
    use prin_sim::PruningStrategy;
    let bad = PruningStrategy::AmplitudeThreshold(-0.1);
    assert!(bad.validate().is_err());

    let good = PruningStrategy::AmplitudeThreshold(1.0);
    assert!(good.validate().is_ok());
}

// ────────────────────────────────────────────────────────────────────────────
// SparseCoupling::prune
// ────────────────────────────────────────────────────────────────────────────

#[test]
fn prune_reduces_nnz() {
    let coupling = SparseCoupling::from_ring(8, 2, 0.5).unwrap();
    let pruned = coupling.prune(0.3).unwrap();
    // weight = 0.5 / 4 = 0.125, which is <= 0.3, so all entries pruned
    assert_eq!(pruned.nnz(), 0);
}

#[test]
fn prune_zero_threshold_keeps_all() {
    let coupling = SparseCoupling::from_ring(8, 2, 1.0).unwrap();
    let pruned = coupling.prune(0.0).unwrap();
    assert_eq!(pruned.nnz(), coupling.nnz());
}
