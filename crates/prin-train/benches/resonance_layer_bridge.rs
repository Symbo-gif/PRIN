//! Criterion baseline for the WP-025 Torch-bridge boundary-overhead
//! evidence (Benchmarking Standards §2.4, "Torch-bridge training step...
//! bridge overhead <5%").
//!
//! Measures the pure-Rust cost of exactly the computation
//! `prin-py::bindings::train::PyResonanceLayerBridge` performs per training
//! step: one `forward()` call to produce the output, then — matching the
//! bridge's recompute-on-backward design (see that module's doc comment for
//! why Burn's autodiff graph cannot be reused across multiple `backward()`
//! calls) — a second `forward()` call under a `require_grad()` leaf followed
//! by `backward()`. Comparing this number against
//! `tests/test_train_bridge.py::TestTrainBridgeBenchmarks` (the same shape,
//! measured through the full `torch.autograd.Function`/DLPack round trip)
//! isolates the PyO3/DLPack boundary-crossing cost from the underlying
//! numerics — see the WP-025 S1 handoff for the combined evidence.

use std::time::Duration;

use burn::backend::{Autodiff, NdArray};
use burn::tensor::{Tensor, TensorData};
use criterion::{black_box, criterion_group, criterion_main, Criterion};

use prin_dynamics::Seed;
use prin_train::layers::ResonanceLayerConfig;

type Backend = Autodiff<NdArray<f64>>;

/// One `(n_oscillators, n_dims, n_steps, batch)` shape, named to match the
/// corresponding case in `tests/test_train_bridge.py::TestTrainBridgeBenchmarks`
/// — keep both files' shapes in sync.
struct Shape {
    name: &'static str,
    n_oscillators: usize,
    n_dims: usize,
    n_steps: usize,
    batch: usize,
}

const SHAPES: &[Shape] = &[
    Shape {
        name: "small_32osc_16dims_8batch",
        n_oscillators: 32,
        n_dims: 16,
        n_steps: 10,
        batch: 8,
    },
    Shape {
        name: "moderate_128osc_64dims_32batch",
        n_oscillators: 128,
        n_dims: 64,
        n_steps: 10,
        batch: 32,
    },
];

fn bench_resonance_layer_forward_backward(c: &mut Criterion) {
    let device = Default::default();

    let mut group = c.benchmark_group("resonance_layer_bridge_baseline");
    group.measurement_time(Duration::from_secs(5));

    for shape in SHAPES {
        let mut seed = Seed::new(1, 0);
        let layer = ResonanceLayerConfig::with_params(
            shape.n_oscillators,
            shape.n_dims,
            shape.n_steps,
            0.01,
            0.1,
            0.01,
        )
        .expect("valid config")
        .init::<Backend>(&device, &mut seed);

        let x_data: Vec<f64> = (0..shape.batch * shape.n_dims)
            .map(|i| ((i as f64) * 0.017).sin())
            .collect();

        group.bench_function(shape.name, |b| {
            b.iter(|| {
                // Mirrors PyResonanceLayerBridge::forward: one forward call
                // to produce the returned output.
                let x = Tensor::<Backend, 2>::from_data(
                    TensorData::new(x_data.clone(), vec![shape.batch, shape.n_dims]),
                    &device,
                );
                let output = layer.forward(x).expect("valid forward pass");
                black_box(output.into_data());

                // Mirrors PyResonanceLayerCtx::backward: recompute forward
                // under a fresh require_grad() leaf, then seed the reverse
                // pass with a unit cotangent (equivalent to
                // `grad_output = ones_like`).
                let x_grad = Tensor::<Backend, 2>::from_data(
                    TensorData::new(x_data.clone(), vec![shape.batch, shape.n_dims]),
                    &device,
                )
                .require_grad();
                let output_grad = layer.forward(x_grad.clone()).expect("valid forward pass");
                let grads = output_grad.sum().backward();
                let grad_x = x_grad.grad(&grads).expect("gradient recorded for input");
                black_box(grad_x.into_data());
            });
        });
    }

    group.finish();
}

criterion_group!(benches, bench_resonance_layer_forward_backward);
criterion_main!(benches);
