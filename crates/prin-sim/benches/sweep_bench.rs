//! Criterion benchmarks for OscilloSim sweep parallelism and SpMV scaling.

use criterion::{black_box, criterion_group, criterion_main, BenchmarkId, Criterion, Throughput};

use prin_dynamics::{RK4Integrator, Seed};
use prin_sim::csr_coupling::SparseCoupling;
use prin_sim::engine::{OscilloSim, SparseKuramoto};
use prin_sim::sweep::{run_sweep, SweepAxis, SweepConfig, SweepModel};

fn bench_sweep_scaling(c: &mut Criterion) {
    let mut group = c.benchmark_group("sweep_parallel");

    for &n_axis_vals in &[4, 8, 16, 32] {
        let values: Vec<f64> = (0..n_axis_vals).map(|i| 0.5 + 0.1 * i as f64).collect();
        let config = SweepConfig {
            n_oscillators: 256,
            half_k: 4,
            axes: vec![SweepAxis::CouplingStrength(values)],
            n_steps: 100,
            dt: 0.01,
            base_seed: 42,
            model: SweepModel::Kuramoto,
            record_trajectory: false,
        };

        group.throughput(Throughput::Elements(n_axis_vals as u64));
        group.bench_with_input(
            BenchmarkId::new("run_sweep", format!("{n_axis_vals}_configs")),
            &n_axis_vals,
            |b, _| {
                b.iter(|| {
                    let results = run_sweep(black_box(&config)).unwrap();
                    black_box(results)
                })
            },
        );
    }
    group.finish();
}

fn bench_spmv_scaling(c: &mut Criterion) {
    let mut group = c.benchmark_group("spmv_coupling");

    for &n in &[256, 1024, 4096, 16384] {
        let half_k = 4;
        let coupling = SparseCoupling::from_ring(n, half_k, 1.0).unwrap();
        let phases: Vec<f64> = (0..n)
            .map(|i| 2.0 * std::f64::consts::PI * i as f64 / n as f64)
            .collect();
        let amplitudes = vec![1.0_f64; n];

        group.throughput(Throughput::Elements(n as u64));
        group.bench_with_input(BenchmarkId::new("kuramoto_coupling", n), &n, |b, _| {
            b.iter(|| {
                let (sin_sum, cos_sum) = coupling
                    .kuramoto_coupling(black_box(&phases), black_box(&amplitudes))
                    .unwrap();
                black_box((sin_sum, cos_sum))
            })
        });
    }
    group.finish();
}

fn bench_engine_step_scaling(c: &mut Criterion) {
    let mut group = c.benchmark_group("engine_step");

    for &n in &[256, 1024, 4096, 16384] {
        let coupling = SparseCoupling::from_ring(n, 4, 1.0).unwrap();
        let model = SparseKuramoto::new(n, 0.1, 0.01, coupling.clone()).unwrap();
        let state = prin_dynamics::state::OscillatorState::create_random(
            n,
            (0.5, 5.0),
            &mut Seed::new(42, 0),
        )
        .unwrap();
        let integrator = Box::new(RK4Integrator::new());
        let mut engine = OscilloSim::new(state, coupling, integrator, 0.01).unwrap();

        group.throughput(Throughput::Elements(n as u64));
        group.bench_with_input(BenchmarkId::new("step", n), &n, |b, _| {
            b.iter(|| {
                engine.step(black_box(&model)).unwrap();
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
