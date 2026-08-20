//! Criterion baseline for WP-027's bridge-profiling acceptance criterion,
//! extending DV-021's `ResonanceLayer` evidence
//! (`resonance_layer_bridge.rs`) to [`PhaseTracker`]'s composed
//! `encode -> evolve -> phase_similarity` `forward` path — exactly the
//! computation `PhaseTrackerBridge::match_frames`
//! (`crates/prin-py/src/bindings/phase_tracker.rs`) performs per call, so
//! this is directly comparable to
//! `tests/test_train_bridge_phase_tracker.py::TestPhaseTrackerBenchmarks`'s
//! `match_frames` measurement (same two named shapes — keep both files'
//! shapes in sync).
//!
//! **Scope note**: unlike `ResonanceLayer` (whose Python API is one
//! composed differentiable `forward`+`backward` call, matching
//! `resonance_layer_bridge.rs`'s methodology exactly), `PhaseTracker` has no
//! single composed *differentiable* Python entry point —
//! `encode`/`evolve`/`phase_similarity` are three separate bridge calls,
//! and `match_frames` (measured here) is the non-differentiable evaluation
//! path with no `backward()`. This bench therefore measures the
//! forward-only round trip, the one PhaseTracker operation with a direct
//! single-call Python equivalent; it does not (and should not) also fold in
//! a mismatched backward pass with no comparable Python-side call.

use std::time::Duration;

use burn::backend::{Autodiff, NdArray};
use burn::tensor::{Tensor, TensorData};
use criterion::{black_box, criterion_group, criterion_main, Criterion};

use prin_dynamics::Seed;
use prin_train::phase_tracker::PhaseTrackerConfig;

type Backend = Autodiff<NdArray<f64>>;

/// One `(n_objects, detection_dim)` shape at the canonical PhaseTracker
/// band sizes (`n_delta=4, n_theta=8, n_gamma=16` -> `n_osc=28`,
/// `n_discrete_steps=5, match_threshold=0.1`, matching the registered
/// temporal CLEVR-N validation protocol).
struct Shape {
    name: &'static str,
    n_objects: usize,
    detection_dim: usize,
}

const SHAPES: &[Shape] = &[
    Shape {
        name: "small_4obj_28osc",
        n_objects: 4,
        detection_dim: 4,
    },
    Shape {
        name: "moderate_32obj_28osc",
        n_objects: 32,
        detection_dim: 4,
    },
];

fn bench_phase_tracker_match_frames(c: &mut Criterion) {
    let device = Default::default();

    let mut group = c.benchmark_group("phase_tracker_bridge_baseline");
    group.measurement_time(Duration::from_secs(5));

    for shape in SHAPES {
        let mut seed = Seed::new(1, 0);
        let tracker = PhaseTrackerConfig::with_params(shape.detection_dim, 4, 8, 16, 5, 0.1)
            .expect("valid config")
            .init::<Backend>(&device, &mut seed);

        let n = shape.n_objects;
        let d = shape.detection_dim;
        let dets_t_data: Vec<f64> = (0..n * d).map(|i| ((i as f64) * 0.013).sin()).collect();
        let dets_t1_data: Vec<f64> = (0..n * d).map(|i| ((i as f64) * 0.019).cos()).collect();

        group.bench_function(shape.name, |b| {
            b.iter(|| {
                // Mirrors `PhaseTrackerBridge::match_frames` exactly: one
                // forward call producing matches + similarity, no grad.
                let dets_t = Tensor::<Backend, 2>::from_data(
                    TensorData::new(dets_t_data.clone(), vec![n, d]),
                    &device,
                );
                let dets_t1 = Tensor::<Backend, 2>::from_data(
                    TensorData::new(dets_t1_data.clone(), vec![n, d]),
                    &device,
                );
                let (matches, sim) = tracker
                    .forward(dets_t, dets_t1)
                    .expect("valid forward pass");
                black_box(sim.into_data());
                black_box(matches);
            });
        });
    }

    group.finish();
}

criterion_group!(benches, bench_phase_tracker_match_frames);
criterion_main!(benches);
