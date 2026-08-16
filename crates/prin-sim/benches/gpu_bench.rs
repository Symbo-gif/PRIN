//! Criterion benchmarks for the WP-021 GPU-dispatched simulation components
//! (`prin_sim::gpu`), at the exact problem sizes the §N1 GPU performance
//! targets name (Benchmarking and Reproducibility Standards §2.4):
//!
//! - `sparse_kuramoto_cpu_vs_gpu`: sparse k-NN coupling at `N = 16,000, k =
//!   14` ("Sparse k-NN coupling, N=16K, k=14, GPU | >= parity (3x torch)"),
//!   comparing `prin-sim`'s existing rayon/CSR `SparseKuramoto` against the
//!   `prin-kernels`-dispatched `GpuSparseKuramoto` — both driven through the
//!   identical `OscilloSim`/`RK4Integrator` loop, so this is a true
//!   apples-to-apples before/after comparison of only the coupling
//!   evaluation.
//! - `mean_field_cpu_vs_gpu`: dense all-to-all mean-field RK4 at `N =
//!   1,000,000` ("Mean-field RK4, N=1M, GPU | >= Triton-fused parity"),
//!   comparing `prin-dynamics`' O(N) `KuramotoOscillator` (`MeanField` mode)
//!   + `RK4Integrator` against `GpuMeanFieldEngine`'s fused kernel step.
//!
//! This crate has no GPU-vs-Triton same-hardware comparison (DV-001, blocked
//! on a Linux/CUDA runner); these benchmarks report this host's CPU-vs-GPU
//! timings for the *simulation-integrated* path (not the raw kernel
//! micro-benchmarks already covered by `prin-kernels`' own
//! `mean_field_rk4_bench`/`sparse_knn_bench`), establishing the regression
//! baseline this WP's mission names ("lock regression baselines").
//!
//! Requires the `cpu`, `cuda`, or `wgpu` feature (whichever backend
//! `prin_sim::gpu` was compiled with `step_auto`/`sparse_knn_coupling_auto`
//! will select automatically per `prin_kernels::backend::auto_detect_order`).
//!
//! **`cpu`-only caveat (WP-021 discovery, out of this WP's scope to fix):**
//! with *only* the `cpu` feature enabled (no `cuda`/`wgpu`), `mean_field_
//! cpu_vs_gpu`'s `gpu_kernel_dispatch` case routes through `prin-kernels`'
//! CubeCL-CPU backend (`try_step_cpu`) at `N = 1,000,000` — a combination no
//! existing `prin-kernels` test or benchmark had previously exercised (its
//! own `mean_field_rk4_bench` only benchmarks the native `step_cpu`
//! reference at that size, never `try_step_cpu`). On this host that call
//! hung for several minutes under heavy memory growth and then aborted
//! (`0xffffffff`). Verified as a `prin-kernels`-level pre-existing gap, not a
//! defect in this WP's `prin_sim::gpu` wrapper: `cuda` and `wgpu` both
//! complete this exact benchmark in milliseconds. Run this benchmark with
//! `--features cuda` or `--features wgpu`; avoid `--features cpu` alone at
//! this problem size until a future `prin-kernels` WP investigates.

#[cfg(any(feature = "cpu", feature = "cuda", feature = "wgpu"))]
mod imp {
    use std::time::Duration;

    use criterion::{black_box, criterion_group, Criterion, Throughput};

    use prin_dynamics::coupling::CouplingMode;
    use prin_dynamics::models::KuramotoOscillator;
    use prin_dynamics::{Integrator, OscillatorState, RK4Integrator, Seed};
    use prin_kernels::mean_field_rk4::MeanFieldRk4Params;
    use prin_sim::csr_coupling::SparseCoupling;
    use prin_sim::engine::{OscilloSim, SparseKuramoto};
    use prin_sim::gpu::{GpuMeanFieldEngine, GpuSparseKuramoto};

    const SPARSE_N: usize = 16_000;
    const SPARSE_K: usize = 14;
    const MEAN_FIELD_N: usize = 1_000_000;

    pub(super) fn bench_sparse_kuramoto_cpu_vs_gpu(c: &mut Criterion) {
        let mut group = c.benchmark_group("sparse_kuramoto_cpu_vs_gpu");
        group.measurement_time(Duration::from_secs(5));
        group.sample_size(10);
        group.throughput(Throughput::Elements(SPARSE_N as u64));

        let coupling = SparseCoupling::from_ring(SPARSE_N, SPARSE_K / 2, 2.0).unwrap();
        let state =
            OscillatorState::create_random(SPARSE_N, (0.5, 5.0), &mut Seed::new(0, 0)).unwrap();

        group.bench_function("cpu_spmv", |b| {
            let cpu_model = SparseKuramoto::new(SPARSE_N, 0.1, 0.01, coupling.clone()).unwrap();
            let integrator = Box::new(RK4Integrator::new());
            let mut engine =
                OscilloSim::new(state.clone(), coupling.clone(), integrator, 0.01).unwrap();
            b.iter(|| {
                engine.step(&cpu_model).unwrap();
                black_box(engine.state());
            });
        });

        group.bench_function("gpu_kernel_dispatch", |b| {
            let gpu_model =
                GpuSparseKuramoto::new(SPARSE_N, 0.1, 0.01, 2.0, coupling.clone()).unwrap();
            let integrator = Box::new(RK4Integrator::new());
            let mut engine =
                OscilloSim::new(state.clone(), coupling.clone(), integrator, 0.01).unwrap();
            b.iter(|| {
                engine.step(&gpu_model).unwrap();
                black_box(engine.state());
            });
        });

        group.finish();
    }

    pub(super) fn bench_mean_field_cpu_vs_gpu(c: &mut Criterion) {
        let mut group = c.benchmark_group("mean_field_cpu_vs_gpu");
        group.measurement_time(Duration::from_secs(5));
        group.sample_size(10);
        group.throughput(Throughput::Elements(MEAN_FIELD_N as u64));

        let state =
            OscillatorState::create_random(MEAN_FIELD_N, (0.5, 5.0), &mut Seed::new(0, 0)).unwrap();

        group.bench_function("cpu_dynamics", |b| {
            let model =
                KuramotoOscillator::new(MEAN_FIELD_N, 2.0, 0.1, 0.01, CouplingMode::MeanField)
                    .unwrap();
            let mut integrator = RK4Integrator::new();
            let mut current = state.clone();
            b.iter(|| {
                current = integrator.step(&model, &current, 0.01).unwrap();
                black_box(&current);
            });
        });

        group.bench_function("gpu_kernel_dispatch", |b| {
            let params = MeanFieldRk4Params {
                k: 2.0,
                decay: 0.1,
                gamma: 0.01,
                dt: 0.01,
            };
            let mut engine = GpuMeanFieldEngine::new(&state, params).unwrap();
            b.iter(|| {
                engine.step().unwrap();
                black_box(engine.state().unwrap());
            });
        });

        group.finish();
    }

    criterion_group!(
        gpu_benches,
        bench_sparse_kuramoto_cpu_vs_gpu,
        bench_mean_field_cpu_vs_gpu
    );
}

#[cfg(any(feature = "cpu", feature = "cuda", feature = "wgpu"))]
fn main() {
    imp::gpu_benches();
    criterion::Criterion::default()
        .configure_from_args()
        .final_summary();
}

#[cfg(not(any(feature = "cpu", feature = "cuda", feature = "wgpu")))]
fn main() {
    eprintln!(
        "gpu_bench requires the `cpu`, `cuda`, or `wgpu` feature (prin_sim::gpu is not compiled \
         in without one) — skipping."
    );
}
