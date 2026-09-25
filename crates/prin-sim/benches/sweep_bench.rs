//! Criterion benchmarks for OscilloSim sweep parallelism and SpMV scaling.
//!
//! Every group benchmarks a `serial` variant (a dedicated 1-thread rayon
//! pool, via `ThreadPoolBuilder`) alongside the default `parallel` variant
//! (the process-global rayon pool, sized to the available cores) so that
//! every reported number is a direct, in-process speedup ratio rather than
//! a throughput figure that needs an external `RAYON_NUM_THREADS=1` run to
//! interpret (WP016-F5). Workloads are sized so the parallel variant has
//! enough work per task to amortize thread-pool dispatch overhead
//! (WP016-F1): the sweep uses a larger per-config workload than the S1
//! benchmark, and `spmv_coupling`/`engine_step` scale up to N = 1,000,000 to
//! give direct N = 1M CPU timing evidence for the WP-016 acceptance
//! criterion "parity reaches N = 1M CPU where feasible".

use std::time::Duration;

use criterion::{black_box, criterion_group, criterion_main, BenchmarkId, Criterion, Throughput};
use rayon::ThreadPoolBuilder;

use prin_dynamics::models::Dynamics;
use prin_dynamics::{GuardPolicy, RK4Integrator, Seed};
use prin_sim::csr_coupling::SparseCoupling;
use prin_sim::engine::{OscilloSim, SparseKuramoto};
use prin_sim::sweep::{run_sweep, SweepAxis, SweepConfig, SweepModel};

/// A dedicated single-thread rayon pool for the `serial` baseline variant.
/// Running `run_sweep`/`kuramoto_coupling`/`engine.step()` inside
/// `pool.install(...)` forces every nested `rayon` call in `prin-sim` onto
/// this one worker thread, giving an in-process serial baseline without
/// relaunching the process under `RAYON_NUM_THREADS=1`.
fn serial_pool() -> rayon::ThreadPool {
    ThreadPoolBuilder::new()
        .num_threads(1)
        .build()
        .expect("failed to build single-threaded rayon pool for serial baseline")
}

fn bench_sweep_scaling(c: &mut Criterion) {
    let mut group = c.benchmark_group("sweep_parallel");
    group.measurement_time(Duration::from_secs(5));
    group.sample_size(10);
    let serial = serial_pool();

    for &n_axis_vals in &[4, 8, 16, 32, 64] {
        let values: Vec<f64> = (0..n_axis_vals).map(|i| 0.5 + 0.1 * i as f64).collect();
        let config = SweepConfig {
            n_oscillators: 4096,
            half_k: 4,
            axes: vec![SweepAxis::CouplingStrength(values)],
            n_steps: 300,
            dt: 0.01,
            base_seed: 42,
            model: SweepModel::Kuramoto,
            record_trajectory: false,
        };

        group.throughput(Throughput::Elements(n_axis_vals as u64));
        group.bench_with_input(
            BenchmarkId::new("run_sweep_parallel", format!("{n_axis_vals}_configs")),
            &n_axis_vals,
            |b, _| {
                b.iter(|| {
                    let results = run_sweep(black_box(&config)).unwrap();
                    black_box(results)
                })
            },
        );
        group.bench_with_input(
            BenchmarkId::new("run_sweep_serial", format!("{n_axis_vals}_configs")),
            &n_axis_vals,
            |b, _| {
                b.iter(|| {
                    serial.install(|| {
                        let results = run_sweep(black_box(&config)).unwrap();
                        black_box(results)
                    })
                })
            },
        );
    }
    group.finish();
}

fn bench_spmv_scaling(c: &mut Criterion) {
    let mut group = c.benchmark_group("spmv_coupling");
    group.measurement_time(Duration::from_secs(3));
    group.sample_size(10);
    let serial = serial_pool();

    for &n in &[256, 1024, 4096, 16384, 65536, 262144, 1_000_000] {
        let half_k = 4;
        let coupling = SparseCoupling::from_ring(n, half_k, 1.0).unwrap();
        let phases: Vec<f64> = (0..n)
            .map(|i| 2.0 * std::f64::consts::PI * i as f64 / n as f64)
            .collect();
        let amplitudes = vec![1.0_f64; n];

        group.throughput(Throughput::Elements(n as u64));
        group.bench_with_input(
            BenchmarkId::new("kuramoto_coupling_parallel", n),
            &n,
            |b, _| {
                b.iter(|| {
                    let (sin_sum, cos_sum) = coupling
                        .kuramoto_coupling(black_box(&phases), black_box(&amplitudes))
                        .unwrap();
                    black_box((sin_sum, cos_sum))
                })
            },
        );
        group.bench_with_input(
            BenchmarkId::new("kuramoto_coupling_serial", n),
            &n,
            |b, _| {
                b.iter(|| {
                    serial.install(|| {
                        let (sin_sum, cos_sum) = coupling
                            .kuramoto_coupling(black_box(&phases), black_box(&amplitudes))
                            .unwrap();
                        black_box((sin_sum, cos_sum))
                    })
                })
            },
        );
    }
    group.finish();
}

fn bench_engine_step_scaling(c: &mut Criterion) {
    let mut group = c.benchmark_group("engine_step");
    group.measurement_time(Duration::from_secs(3));
    group.sample_size(10);
    let serial = serial_pool();

    for &n in &[256, 1024, 4096, 16384, 65536, 262144, 1_000_000] {
        let coupling = SparseCoupling::from_ring(n, 4, 1.0).unwrap();
        let model = SparseKuramoto::new(n, 0.1, 0.01, coupling.clone()).unwrap();
        let state = prin_dynamics::state::OscillatorState::create_random(
            n,
            (0.5, 5.0),
            &mut Seed::new(42, 0),
        )
        .unwrap();
        let integrator = Box::new(RK4Integrator::new().with_guard(GuardPolicy::Bounded));
        let mut engine =
            OscilloSim::new(state.clone(), coupling.clone(), integrator, 0.01).unwrap();

        group.throughput(Throughput::Elements(n as u64));

        // Full RK4 engine step (integrator + dispatch-gated derivatives),
        // default global rayon pool.
        group.bench_with_input(BenchmarkId::new("step_parallel", n), &n, |b, _| {
            b.iter(|| {
                engine.step(black_box(&model)).unwrap();
            })
        });

        // `Dynamics::compute_derivatives` alone — the exact WP016-F1 hot
        // path — forced onto the serial baseline pool. `OscilloSim` bundles
        // a `Box<dyn Integrator>`, which is not `Send`, so it cannot cross
        // `ThreadPool::install`'s `Send` bound; `compute_derivatives` takes
        // `&self`/`&OscillatorState` only, both `Sync`, so it can.
        group.bench_with_input(BenchmarkId::new("derivatives_parallel", n), &n, |b, _| {
            b.iter(|| black_box(model.compute_derivatives(black_box(&state)).unwrap()))
        });
        group.bench_with_input(BenchmarkId::new("derivatives_serial", n), &n, |b, _| {
            b.iter(|| {
                serial.install(|| black_box(model.compute_derivatives(black_box(&state)).unwrap()))
            })
        });
    }
    group.finish();
}

criterion_group!(
    benches,
    bench_sweep_scaling,
    bench_spmv_scaling,
    bench_engine_step_scaling,
);
criterion_main!(benches);
