//! Property tests for the parallel parameter sweep module.
//!
//! Verifies sweep determinism, order-parameter bounds, and oscillation
//! detection invariants under arbitrary configurations.

use proptest::prelude::*;

use prin_sim::sweep::{detect_oscillation, run_sweep, SweepAxis, SweepConfig, SweepModel};

fn any_sweep_config() -> impl Strategy<Value = SweepConfig> {
    (
        10usize..=32, // n_oscillators (must be > 2*half_k max=8)
        1usize..=4,   // half_k
        10usize..=50, // n_steps
        0.001..=0.05, // dt
    )
        .prop_map(|(n, half_k, n_steps, dt)| {
            let k_values = vec![0.5, 1.0, 2.0];
            SweepConfig {
                n_oscillators: n,
                half_k: half_k.min((n - 1) / 2),
                axes: vec![SweepAxis::CouplingStrength(k_values)],
                n_steps,
                dt,
                base_seed: 42,
                model: SweepModel::Kuramoto,
                record_trajectory: true,
            }
        })
}

proptest! {
    #![proptest_config(ProptestConfig::with_cases(16))]

    #[test]
    fn sweep_results_have_valid_order_parameters(config in any_sweep_config()) {
        let results = run_sweep(&config).unwrap();
        for r in &results {
            prop_assert!(r.final_order_parameter >= 0.0);
            prop_assert!(r.final_order_parameter <= 1.0);
            if let Some(mean_r) = r.mean_order_parameter {
                prop_assert!(mean_r >= 0.0);
                prop_assert!(mean_r <= 1.0);
            }
        }
    }

    #[test]
    fn sweep_result_count_matches_config(config in any_sweep_config()) {
        let results = run_sweep(&config).unwrap();
        prop_assert_eq!(results.len(), config.n_configs());
    }

    #[test]
    fn sweep_is_deterministic(config in any_sweep_config()) {
        let r1 = run_sweep(&config).unwrap();
        let r2 = run_sweep(&config).unwrap();
        prop_assert_eq!(r1.len(), r2.len());
        for (a, b) in r1.iter().zip(r2.iter()) {
            prop_assert!((a.final_order_parameter - b.final_order_parameter).abs() < 1e-14);
            prop_assert_eq!(a.seed, b.seed);
        }
    }
}

proptest! {
    #![proptest_config(ProptestConfig::with_cases(64))]

    #[test]
    fn detect_oscillation_constant_history_is_stable(
        window in 1usize..=50,
        value in -10.0_f64..=10.0,
        n in 10usize..=100,
    ) {
        let history = vec![value; n];
        prop_assert!(!detect_oscillation(&history, window, 0.01));
    }

    #[test]
    fn detect_oscillation_high_variance_is_flagged(
        window in 5usize..=30,
        n in 30usize..=100,
    ) {
        let history: Vec<f64> = (0..n)
            .map(|i| if i % 2 == 0 { 1.0 } else { -1.0 })
            .collect();
        prop_assert!(detect_oscillation(&history, window, 0.01));
    }
}
