//! Criterion benchmarks for the mean-field RK4 step at N=1,000,000
//! oscillators (Project Plan §3.2 N1 / Benchmarking and Reproducibility
//! Standards §2.4: "Mean-field RK4, N=1M, GPU | >= Triton-fused parity").
//!
//! `bench_cpu_step` always runs (the native `step_cpu` reference has no
//! feature dependency). `bench_wgpu_step` additionally runs under
//! `--features wgpu`, using the hierarchical device-side order-parameter
//! reduction and `ComputeClient::profile` device-event timing landed in
//! WP-018; its `StepReport` (genuine device timestamps where the backend
//! supports them, not a wall-clock guess) is printed once before the timed
//! loop as environment-captured evidence (Benchmarking and Reproducibility
//! Standards §1.4, §2.2).
//!
//! The direct same-hardware PRINet 3.0 Triton-fused-kernel comparison
//! remains blocked on a Linux/CUDA runner (DV-001); this benchmark reports
//! this host's wgpu (DX12) and CPU-native timings, not a Triton-relative
//! figure.

use criterion::{black_box, criterion_group, criterion_main, Criterion, Throughput};

use prin_kernels::mean_field_rk4::{step_cpu, MeanFieldRk4Params};

const N: usize = 1_000_000;

fn make_state(n: usize) -> (Vec<f32>, Vec<f32>, Vec<f32>) {
    let phase: Vec<_> = (0..n).map(|i| 0.1 * (i % 64) as f32).collect();
    let amplitude: Vec<_> = (0..n).map(|_| 1.0_f32).collect();
    let frequency: Vec<_> = (0..n).map(|i| 0.05 * ((i % 64) as f32 - 32.0)).collect();
    (phase, amplitude, frequency)
}

fn default_params() -> MeanFieldRk4Params {
    MeanFieldRk4Params {
        k: 2.0,
        decay: 0.1,
        gamma: 0.01,
        dt: 0.01,
    }
}

fn bench_cpu_step(c: &mut Criterion) {
    let (phase, amplitude, frequency) = make_state(N);
    let params = default_params();

    let mut group = c.benchmark_group("mean_field_rk4_n1m");
    group.sample_size(10);
    group.throughput(Throughput::Elements(N as u64));
    group.bench_function("cpu_native", |b| {
        b.iter(|| {
            step_cpu(
                black_box(&phase),
                black_box(&amplitude),
                black_box(&frequency),
                black_box(&params),
            )
            .unwrap()
        });
    });
    group.finish();
}

#[cfg(feature = "wgpu")]
fn bench_wgpu_step(c: &mut Criterion) {
    use cubecl::wgpu::{WgpuDevice, WgpuRuntime};
    use cubecl::Runtime;
    use prin_kernels::buffers::CubeclBufferPool;
    use prin_kernels::mean_field_rk4::cubecl::step_cubecl_with_pool;

    let (phase, amplitude, frequency) = make_state(N);
    let params = default_params();

    let device = WgpuDevice::DefaultDevice;
    let client = WgpuRuntime::client(&device);
    let pool = CubeclBufferPool::<WgpuRuntime>::new(&client, N);

    // Evidence: one untimed step's StepReport, capturing the backend name and
    // device-event wall time for this host (Benchmarking Standards §1.4).
    let (_, report) =
        step_cubecl_with_pool(&client, &phase, &amplitude, &frequency, &params, &pool).unwrap();
    eprintln!("N={N} wgpu StepReport (evidence, untimed): {report:?}");

    let mut group = c.benchmark_group("mean_field_rk4_n1m");
    group.sample_size(10);
    group.throughput(Throughput::Elements(N as u64));
    group.bench_function("wgpu_device_dispatch", |b| {
        b.iter(|| {
            step_cubecl_with_pool(
                black_box(&client),
                black_box(&phase),
                black_box(&amplitude),
                black_box(&frequency),
                black_box(&params),
                black_box(&pool),
            )
            .unwrap()
        });
    });
    group.finish();
}

criterion_group!(cpu_benches, bench_cpu_step);

#[cfg(feature = "wgpu")]
criterion_group!(wgpu_benches, bench_wgpu_step);

#[cfg(feature = "wgpu")]
criterion_main!(cpu_benches, wgpu_benches);
#[cfg(not(feature = "wgpu"))]
criterion_main!(cpu_benches);
