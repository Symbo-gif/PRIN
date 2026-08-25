//! Criterion evidence for the WP-030 acceptance criterion "hook
//! overhead/bounds are tested": per-call cost of
//! [`TrainingHooks::on_step_end_with_elapsed`] and
//! [`TrainingHooks::on_epoch_end`], the two calls a training loop makes on
//! every step/epoch. Reported as pilot evidence (Development Workflow
//! Standards §3: "no scientific conclusion claims from pilots"), not a
//! regression gate — `src/hooks.rs`'s
//! `step_accumulation_overhead_is_bounded` unit test is the actual pass/fail
//! bound.

use std::time::Duration;

use criterion::{criterion_group, criterion_main, BenchmarkId, Criterion};

use prin_daemon::hooks::TrainingHooks;
use prin_daemon::state::Regime;

fn bench_on_step_end(c: &mut Criterion) {
    let mut group = c.benchmark_group("training_hooks_on_step_end");
    for grad_dim in [0usize, 8, 64] {
        let grad_norms: Vec<f64> = (0..grad_dim).map(|i| i as f64 * 0.1 + 1.0).collect();
        group.bench_with_input(
            BenchmarkId::from_parameter(grad_dim),
            &grad_norms,
            |b, grad_norms| {
                let mut hooks = TrainingHooks::new(0.1, 100).unwrap();
                let norms = if grad_norms.is_empty() {
                    None
                } else {
                    Some(grad_norms.as_slice())
                };
                let mut loss = 0.5_f64;
                b.iter(|| {
                    hooks.on_step_end_with_elapsed(Duration::from_micros(10), loss, norms);
                    loss = (loss + 0.01) % 1.0;
                });
            },
        );
    }
    group.finish();
}

fn bench_on_epoch_end(c: &mut Criterion) {
    let mut hooks = TrainingHooks::new(0.1, 100).unwrap();
    for step in 0..100u64 {
        hooks.on_step_end_with_elapsed(
            Duration::from_micros(step % 50),
            1.0 / (step as f64 + 1.0),
            Some(&[1.0, 2.0, 3.0]),
        );
    }

    c.bench_function("training_hooks_on_epoch_end", |b| {
        b.iter(|| {
            hooks.on_epoch_end(
                1,
                None,
                vec![0.8, 0.6, 0.4],
                None,
                1e-3,
                1.0,
                Regime::MeanField,
                0.0,
            )
        });
    });
}

criterion_group!(benches, bench_on_step_end, bench_on_epoch_end);
criterion_main!(benches);
