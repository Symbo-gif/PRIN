//! Criterion benchmarks for the sparse k-NN coupling derivative kernel at
//! the WP-019 acceptance target shape: N=16,000, k=14 (Project Plan §6 WP-019
//! declaration).
//!
//! `bench_cpu` always runs (the native `sparse_knn_derivatives_cpu`
//! reference has no feature dependency). `bench_wgpu` additionally runs
//! under `--features wgpu`, printing one untimed call's evidence before the
//! timed loop (Benchmarking and Reproducibility Standards §1.4, §2.2). No
//! same-hardware PRINet 3.0 torch comparison is attempted here (this crate
//! has no Python/torch harness); this benchmark reports this host's wgpu
//! (DX12) and CPU-native timings as observed evidence, not a scientific
//! conclusion (Testing Standards §2).

use criterion::{black_box, criterion_group, criterion_main, Criterion, Throughput};

use prin_kernels::sparse_knn::{sparse_knn_derivatives_cpu, SparseKnnGraph, SparseKnnParams};

const N: usize = 16_000;
const HALF_K: usize = 7; // degree = 2 * HALF_K = 14.

fn make_state(n: usize) -> (Vec<f32>, Vec<f32>, Vec<f32>) {
    let tau = core::f32::consts::TAU;
    let phase: Vec<_> = (0..n).map(|i| (0.01 * i as f32).rem_euclid(tau)).collect();
    let amplitude: Vec<_> = (0..n).map(|_| 1.0_f32).collect();
    let frequency: Vec<_> = (0..n).map(|i| 0.02 * ((i % 100) as f32 - 50.0)).collect();
    (phase, amplitude, frequency)
}

fn make_graph(n: usize, half_k: usize) -> SparseKnnGraph {
    let mut indptr = Vec::with_capacity(n + 1);
    let mut indices = Vec::new();
    indptr.push(0u32);
    for i in 0..n {
        for d in 1..=half_k {
            indices.push(((i + n - d) % n) as u32);
            indices.push(((i + d) % n) as u32);
        }
        indptr.push(indices.len() as u32);
    }
    SparseKnnGraph::from_csr(n, indptr, indices).unwrap()
}

fn default_params() -> SparseKnnParams {
    SparseKnnParams {
        k: 2.0,
        decay: 0.1,
        gamma: 0.01,
    }
}

fn bench_cpu(c: &mut Criterion) {
    let (phase, amplitude, frequency) = make_state(N);
    let graph = make_graph(N, HALF_K);
    let params = default_params();

    let mut group = c.benchmark_group("sparse_knn_n16k_k14");
    group.sample_size(20);
    group.throughput(Throughput::Elements(N as u64));
    group.bench_function("cpu_native", |b| {
        b.iter(|| {
            sparse_knn_derivatives_cpu(
                black_box(&phase),
                black_box(&amplitude),
                black_box(&frequency),
                black_box(&graph),
                black_box(&params),
            )
            .unwrap()
        });
    });
    group.finish();
}

#[cfg(feature = "wgpu")]
fn bench_wgpu(c: &mut Criterion) {
    use cubecl::wgpu::{WgpuDevice, WgpuRuntime};
    use cubecl::Runtime;
    use prin_kernels::sparse_knn::cubecl::sparse_knn_coupling_cubecl;

    let (phase, amplitude, frequency) = make_state(N);
    let graph = make_graph(N, HALF_K);
    let params = default_params();

    let device = WgpuDevice::DefaultDevice;
    let client = WgpuRuntime::client(&device);

    // Evidence: one untimed call, confirming the backend initializes and
    // matches the expected output shape (Benchmarking Standards §1.4).
    let (dphase, _, _) =
        sparse_knn_coupling_cubecl(&client, &phase, &amplitude, &frequency, &graph, &params)
            .unwrap();
    eprintln!(
        "N={N} k=14 wgpu sparse_knn_coupling evidence: dphase.len()={}",
        dphase.len()
    );

    let mut group = c.benchmark_group("sparse_knn_n16k_k14");
    group.sample_size(20);
    group.throughput(Throughput::Elements(N as u64));
    group.bench_function("wgpu_device_dispatch", |b| {
        b.iter(|| {
            sparse_knn_coupling_cubecl(
                black_box(&client),
                black_box(&phase),
                black_box(&amplitude),
                black_box(&frequency),
                black_box(&graph),
                black_box(&params),
            )
            .unwrap()
        });
    });
    group.finish();
}

criterion_group!(cpu_benches, bench_cpu);

#[cfg(feature = "wgpu")]
criterion_group!(wgpu_benches, bench_wgpu);

#[cfg(feature = "wgpu")]
criterion_main!(cpu_benches, wgpu_benches);
#[cfg(not(feature = "wgpu"))]
criterion_main!(cpu_benches);
