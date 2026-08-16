//! Criterion benchmarks for the fused three-band discrete step, comparing the
//! new fused primitive against the "unfused sum of the individual kernels" —
//! literally composing the pre-existing WP-018 `mean_field_rk4::step_cpu`
//! (RK4) and WP-019 `pac::pac_modulate_cpu` kernels by hand, three
//! independent band steps plus two independent PAC-gate calls — matching the
//! acceptance text's "performance at or above the unfused sum of the
//! individual kernels" (session brief 0077 / `DOCS/reports/019-project-state.md`
//! §6).
//!
//! `bench_cpu_step` always runs (native reference paths have no feature
//! dependency). `bench_wgpu_step` additionally runs under `--features wgpu`.
//! This is reported as observed pilot evidence (Benchmarking and
//! Reproducibility Standards §2.2), not a scientific conclusion: the unfused
//! baseline uses RK4 (four derivative evaluations per band) while the fused
//! step uses one Euler evaluation per band — a fair comparison of "kernels
//! actually shipped" per the acceptance text, not a same-algorithm
//! micro-comparison.

use criterion::{black_box, criterion_group, criterion_main, Criterion, Throughput};

use prin_kernels::discrete_step::{
    discrete_step_cpu, BandStepParams, DiscreteStepParams, PacGateParams,
};
use prin_kernels::mean_field_rk4::{step_cpu, MeanFieldRk4Params};
use prin_kernels::pac::{pac_modulate_cpu, PacParams};

const BAND_SIZES: [usize; 3] = [4_096, 16_384, 65_536];

fn make_state(band_sizes: [usize; 3]) -> (Vec<f32>, Vec<f32>, Vec<f32>) {
    let n: usize = band_sizes.iter().sum();
    let phase: Vec<_> = (0..n)
        .map(|i| (0.01 * i as f32).rem_euclid(core::f32::consts::TAU))
        .collect();
    let amplitude: Vec<_> = (0..n).map(|i| 0.5 + 0.5 * (i as f32 / n as f32)).collect();
    let frequency: Vec<_> = (0..n).map(|i| 0.02 * (i as f32 - n as f32 / 2.0)).collect();
    (phase, amplitude, frequency)
}

fn fused_params() -> DiscreteStepParams {
    DiscreteStepParams {
        bands: [
            BandStepParams {
                k: 1.0,
                decay: 0.1,
                gamma: 0.01,
            },
            BandStepParams {
                k: 1.5,
                decay: 0.15,
                gamma: 0.005,
            },
            BandStepParams {
                k: 0.5,
                decay: 0.2,
                gamma: 0.0,
            },
        ],
        pac: [
            PacGateParams {
                modulation_depth: 0.3,
                phase_offset: 0.0,
            },
            PacGateParams {
                modulation_depth: 0.4,
                phase_offset: 0.2,
            },
        ],
        amp_min: 1e-6,
        amp_max: 10.0,
        dt: 0.01,
    }
}

/// Naive composition of the pre-existing (unfused) kernels: one RK4 step per
/// band via `mean_field_rk4::step_cpu`, PAC-gated between adjacent bands via
/// `pac::pac_modulate_cpu`.
fn unfused_step_cpu(
    phase: &[f32],
    amplitude: &[f32],
    frequency: &[f32],
    band_sizes: [usize; 3],
    params: &DiscreteStepParams,
) -> (Vec<f32>, Vec<f32>, Vec<f32>) {
    let offsets = [0, band_sizes[0], band_sizes[0] + band_sizes[1]];
    let band_range = |b: usize| offsets[b]..offsets[b] + band_sizes[b];

    let rk4_params = |b: usize| MeanFieldRk4Params {
        k: params.bands[b].k,
        decay: params.bands[b].decay,
        gamma: params.bands[b].gamma,
        dt: params.dt,
    };

    let r0 = band_range(0);
    let (mut out_p0, mut out_a0, mut out_f0) = step_cpu(
        &phase[r0.clone()],
        &amplitude[r0.clone()],
        &frequency[r0.clone()],
        &rk4_params(0),
    )
    .unwrap();

    let mut out_phase = Vec::new();
    let mut out_amp = Vec::new();
    let mut out_freq = Vec::new();
    out_phase.append(&mut out_p0);
    out_amp.append(&mut out_a0);
    out_freq.append(&mut out_f0);

    for pair in 0..2 {
        let slow_new_phase_slice = match pair {
            0 => &out_phase[0..band_sizes[0]],
            _ => &out_phase[band_sizes[0]..band_sizes[0] + band_sizes[1]],
        };

        let fast = pair + 1;
        let fr = band_range(fast);
        let pac_params = PacParams {
            modulation_depth: params.pac[pair].modulation_depth,
            phase_offset: params.pac[pair].phase_offset,
            amp_min: params.amp_min,
            amp_max: params.amp_max,
        };
        let gated_amp =
            pac_modulate_cpu(slow_new_phase_slice, &amplitude[fr.clone()], &pac_params).unwrap();

        let (mut op, mut oa, mut of) = step_cpu(
            &phase[fr.clone()],
            &gated_amp,
            &frequency[fr.clone()],
            &rk4_params(fast),
        )
        .unwrap();
        out_phase.append(&mut op);
        out_amp.append(&mut oa);
        out_freq.append(&mut of);
    }

    (out_phase, out_amp, out_freq)
}

fn bench_cpu_step(c: &mut Criterion) {
    let (phase, amplitude, frequency) = make_state(BAND_SIZES);
    let params = fused_params();
    let n: usize = BAND_SIZES.iter().sum();

    let mut group = c.benchmark_group("discrete_step_3band");
    group.sample_size(10);
    group.throughput(Throughput::Elements(n as u64));
    group.bench_function("fused_cpu_native", |b| {
        b.iter(|| {
            discrete_step_cpu(
                black_box(&phase),
                black_box(&amplitude),
                black_box(&frequency),
                black_box(BAND_SIZES),
                black_box(&params),
            )
            .unwrap()
        });
    });
    group.bench_function("unfused_cpu_native", |b| {
        b.iter(|| {
            unfused_step_cpu(
                black_box(&phase),
                black_box(&amplitude),
                black_box(&frequency),
                black_box(BAND_SIZES),
                black_box(&params),
            )
        });
    });
    group.finish();
}

#[cfg(feature = "wgpu")]
fn bench_wgpu_step(c: &mut Criterion) {
    use prin_kernels::discrete_step::cubecl::try_discrete_step_wgpu;

    let (phase, amplitude, frequency) = make_state(BAND_SIZES);
    let params = fused_params();
    let n: usize = BAND_SIZES.iter().sum();

    // Evidence: one untimed step's StepReport (Benchmarking Standards §1.4).
    let (_, report) =
        try_discrete_step_wgpu(&phase, &amplitude, &frequency, BAND_SIZES, &params).unwrap();
    eprintln!(
        "band_sizes={BAND_SIZES:?} wgpu discrete-step StepReport (evidence, untimed): {report:?}"
    );

    let mut group = c.benchmark_group("discrete_step_3band");
    group.sample_size(10);
    group.throughput(Throughput::Elements(n as u64));
    group.bench_function("fused_wgpu_device_dispatch", |b| {
        b.iter(|| {
            try_discrete_step_wgpu(
                black_box(&phase),
                black_box(&amplitude),
                black_box(&frequency),
                black_box(BAND_SIZES),
                black_box(&params),
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
