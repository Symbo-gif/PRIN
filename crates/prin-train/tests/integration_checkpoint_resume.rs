//! WP-027 S1 serialization acceptance: checkpoints a
//! [`PhaseTracker`](prin_train::phase_tracker::PhaseTracker) mid-training
//! (not just a freshly-initialized one — extending the existing per-module
//! `record_roundtrip_preserves_parameters` unit tests, which only exercise
//! freshly-seeded parameters, to a genuinely trained-state checkpoint) and
//! confirms a reload reproduces identical validation behavior.

use burn::backend::{Autodiff, NdArray};
use burn::module::{AutodiffModule, Module};
use burn::record::{BinBytesRecorder, DoublePrecisionSettings, Recorder};
use burn::tensor::backend::Backend;
use prin_dynamics::Seed;
use prin_train::dataset::{generate_dataset, TemporalClevrNConfig};
use prin_train::phase_tracker::PhaseTrackerConfig;
use prin_train::trainer::{evaluate_phase_tracker, train_phase_tracker, TemporalTrainerConfig};

type TestBackend = NdArray<f64>;
type TestAutodiffBackend = Autodiff<TestBackend>;

#[test]
fn checkpoint_after_training_round_trips_and_reproduces_validation_behavior() {
    let device: <TestAutodiffBackend as Backend>::Device = Default::default();

    let dataset_config = TemporalClevrNConfig::new(3, 8).unwrap();
    let train_data = generate_dataset(6, &dataset_config, 500);
    let val_data = generate_dataset(3, &dataset_config, 9500);

    let mut init_seed = Seed::new(42, 0);
    let model = PhaseTrackerConfig::with_params(4, 2, 3, 4, 3, 0.1)
        .unwrap()
        .init::<TestAutodiffBackend>(&device, &mut init_seed);

    let trainer_config = TemporalTrainerConfig {
        max_epochs: 4,
        patience: 4,
        warmup_epochs: 1,
        smoothing_window: 2,
        ..TemporalTrainerConfig::default()
    };

    let (trained, _result) =
        train_phase_tracker(model, &trainer_config, &train_data, &val_data, &device).unwrap();
    let trained_inner = trained.valid();

    // Checkpoint the trained (not freshly-initialized) model.
    let recorder = BinBytesRecorder::<DoublePrecisionSettings>::default();
    let bytes = Recorder::<TestBackend>::record(&recorder, trained_inner.clone().into_record(), ())
        .unwrap();

    // Reload into a fresh instance built from a *different* seed, so any
    // parameter agreement after loading is attributable to the checkpoint,
    // not to coincidentally-identical initialization.
    let mut other_seed = Seed::new(999, 0);
    let fresh = PhaseTrackerConfig::with_params(4, 2, 3, 4, 3, 0.1)
        .unwrap()
        .init::<TestBackend>(&device, &mut other_seed);
    let record = Recorder::<TestBackend>::load(&recorder, bytes, &device).unwrap();
    let restored = fresh.load_record(record);
    restored.validate_shapes().unwrap();

    // Both models must now produce bit-identical validation results.
    let before = evaluate_phase_tracker(&trained_inner, &val_data, &device);
    let after = evaluate_phase_tracker(&restored, &val_data, &device);
    assert_eq!(
        before, after,
        "checkpoint round trip changed validation metrics"
    );

    // And bit-identical track_sequence output on a fresh sequence.
    let probe = &val_data[0];
    let frames_before = probe.frame_tensors::<TestBackend>(&device);
    let frames_after = probe.frame_tensors::<TestBackend>(&device);
    let result_before = trained_inner.track_sequence(frames_before).unwrap();
    let result_after = restored.track_sequence(frames_after).unwrap();
    assert_eq!(
        result_before.identity_preservation, result_after.identity_preservation,
        "checkpoint round trip changed track_sequence output"
    );
    assert_eq!(
        result_before.identity_matches,
        result_after.identity_matches
    );
}
