//! WP-027 S1 controlled temporal CLEVR-N integration: trains
//! [`prin_train::phase_tracker::PhaseTracker`] end-to-end via
//! [`prin_train::trainer::train_phase_tracker`] on
//! [`prin_train::dataset::generate_dataset`]-produced sequences and asserts
//! the validation `identity_preservation` (IP) score meets the registered
//! PRINet 3.0 threshold.
//!
//! # Registered threshold
//!
//! `benchmarks/results/y4q1_7_statistical_summary.json`
//! (`DOCS/archive and reference from PRINet 3.0/PRINet-3.0.0-main/`) is the
//! only PRINet 3.0 artifact that (a) uses the real
//! `generate_dataset`/`generate_temporal_clevr_n` sequences, (b) uses
//! actually-trained (not random-weight) models via `TemporalTrainer`, and
//! (c) is tied to a preregistration hash (`y4q1_7_preregistration_hash.json`)
//! — i.e. the canonical "registered" comparison the session brief refers to.
//! Protocol: `train_seqs=50, val_seqs=10, n_objects=4, n_frames=20,
//! max_epochs=20, patience=5, match_threshold=0.1`, seeds `(42, 123, 456)`.
//! PhaseTracker's per-seed IP: `[1.0, 1.0, 0.99605]`, mean `0.99868`.
//!
//! This is a **validation run for the Phase 4 gate**, not Phase 7 campaign
//! evidence — the session brief's own non-goal ("Final scientific
//! publication claims") and WP-027's acceptance text ("without treating
//! pilot data as campaign evidence") both apply: this test asserts a single
//! reproducibility-checked threshold, not a pre-registered scientific
//! comparison with effect sizes/confidence intervals (that is Phase 7's
//! EXP-006, `DOCS/sessions/phase-7/0179-...md`).
//!
//! # Why `#[ignore]`
//!
//! The full canonical protocol (3 seeds x 20 epochs x 60 sequences) takes
//! ~150s in `--release` (correspondingly much longer under the default
//! debug profile `cargo test --workspace` uses) — the same tension the
//! PRINet 3.0 reference itself resolved by keeping its heavy multi-seed
//! trained-to-convergence sweeps as standalone, explicitly-not-pytest-run
//! scripts (`benchmarks/y4q1_7_benchmarks.py`) while a tiny toy-scale
//! smoke test (few epochs, few sequences) stayed in the always-run test
//! suite (`tests/test_y4q1_7.py::test_pt_train_and_evaluate`). This module
//! is the heavy validation-run counterpart to that tiny smoke test —
//! `prin_train::trainer::tests::training_runs_and_produces_valid_metrics`
//! (2 sequences, 3 epochs) exercises the identical training code path on
//! every default `cargo test --workspace` run. Run this test explicitly to
//! reproduce the acceptance-criterion evidence:
//!
//! ```text
//! cargo test --release -p prin-train --test integration_temporal_clevr_n -- --ignored --nocapture
//! ```

use burn::backend::{Autodiff, NdArray};
use burn::tensor::backend::Backend;
use prin_dynamics::Seed;
use prin_train::dataset::{generate_dataset, TemporalClevrNConfig};
use prin_train::phase_tracker::PhaseTrackerConfig;
use prin_train::trainer::{train_phase_tracker, TemporalTrainerConfig};

type TestBackend = NdArray<f64>;
type TestAutodiffBackend = Autodiff<TestBackend>;

/// The registered PhaseTracker mean IP score from
/// `y4q1_7_statistical_summary.json` (see module docs).
const REGISTERED_MEAN_IP: f64 = 0.99868;

const SEEDS: [u128; 3] = [42, 123, 456];

fn run_one_seed(seed_val: u128) -> f64 {
    let device: <TestAutodiffBackend as Backend>::Device = Default::default();

    let dataset_config = TemporalClevrNConfig::new(4, 20).unwrap();
    let train_data = generate_dataset(50, &dataset_config, seed_val);
    let val_data = generate_dataset(10, &dataset_config, seed_val + 9000);

    let mut init_seed = Seed::new(seed_val, 1);
    let model = PhaseTrackerConfig::with_params(4, 4, 8, 16, 5, 0.1)
        .unwrap()
        .init::<TestAutodiffBackend>(&device, &mut init_seed);

    let trainer_config = TemporalTrainerConfig {
        max_epochs: 20,
        patience: 5,
        ..TemporalTrainerConfig::default()
    };

    let (_trained, result) =
        train_phase_tracker(model, &trainer_config, &train_data, &val_data, &device).unwrap();

    println!(
        "seed {seed_val}: final_val_ip={:.5} total_epochs={} final_val_loss={:.5}",
        result.final_val_ip, result.total_epochs, result.final_val_loss
    );

    result.final_val_ip
}

#[test]
#[ignore = "expensive (~150s in --release): the full canonical multi-seed \
            validation run; see module docs for how to run it explicitly"]
fn phase_tracker_reaches_registered_temporal_clevr_n_ip_threshold() {
    let ips: Vec<f64> = SEEDS.iter().map(|&s| run_one_seed(s)).collect();
    let mean_ip = ips.iter().sum::<f64>() / ips.len() as f64;

    for (seed, ip) in SEEDS.iter().zip(&ips) {
        assert!(
            (0.0..=1.0).contains(ip),
            "seed {seed}: IP {ip} out of [0, 1]"
        );
    }

    assert!(
        mean_ip >= REGISTERED_MEAN_IP,
        "mean validation IP {mean_ip:.5} across seeds {SEEDS:?} (per-seed: {ips:?}) \
         did not reach the registered PRINet 3.0 threshold {REGISTERED_MEAN_IP:.5} \
         (y4q1_7_statistical_summary.json)"
    );
}
