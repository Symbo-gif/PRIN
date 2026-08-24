//! Criterion comparison: WP-029's lock-free `ControlSignalBuffer` vs. a
//! same-language `Mutex`-guarded re-implementation of PRINet 3.0's
//! `ControlSignalBuffer` (Benchmarking Standards §2.4, "Daemon latency: lower
//! p95 than 3.0"; `crates/prin-daemon/examples/control_buffer_pilot.rs` reports
//! the manual p50/p95 percentiles this same comparison produces, and
//! `EVIDENCE/0113-wp029-s1-control-buffer-pilot.json` adds a genuine
//! cross-language data point measured against the archived PRINet 3.0 Python
//! implementation directly).
//!
//! `MutexControlSignalBuffer` below is not a strawman: it implements exactly
//! the reference's design (one `Mutex`/`Lock` guarding a single stored value,
//! locked on both the read and the write path) in Rust, so the comparison
//! isolates "lock-free publish vs. mutex-guarded publish" from any
//! Rust-vs-Python interpreter effect.

use std::sync::Mutex;
use std::thread;
use std::time::Duration;

use criterion::{criterion_group, criterion_main, BenchmarkId, Criterion};

use prin_daemon::daemon::ControlSignalBuffer;
use prin_daemon::state::ControlSignals;

/// Rust re-implementation of PRINet 3.0's `ControlSignalBuffer`: a single
/// `Mutex<ControlSignals>`, locked by both `update` and `latest`.
struct MutexControlSignalBuffer {
    inner: Mutex<ControlSignals>,
}

impl MutexControlSignalBuffer {
    fn new() -> Self {
        Self {
            inner: Mutex::new(ControlSignals::default()),
        }
    }

    fn update(&self, signals: ControlSignals) {
        let mut guard = self.inner.lock().expect("lock");
        *guard = signals;
    }

    fn latest(&self) -> ControlSignals {
        self.inner.lock().expect("lock").clone()
    }
}

/// Spawn `n` background writers continuously publishing updates, returning a
/// handle that stops them when dropped.
struct ContentionGuard {
    stop: std::sync::Arc<std::sync::atomic::AtomicBool>,
    handles: Vec<thread::JoinHandle<()>>,
}

impl Drop for ContentionGuard {
    fn drop(&mut self) {
        self.stop.store(true, std::sync::atomic::Ordering::Relaxed);
        for handle in self.handles.drain(..) {
            let _ = handle.join();
        }
    }
}

fn lock_free_contention(writers: usize) -> (std::sync::Arc<ControlSignalBuffer>, ContentionGuard) {
    let buffer = std::sync::Arc::new(ControlSignalBuffer::new());
    let stop = std::sync::Arc::new(std::sync::atomic::AtomicBool::new(false));
    let handles = (0..writers)
        .map(|i| {
            let buffer = std::sync::Arc::clone(&buffer);
            let stop = std::sync::Arc::clone(&stop);
            thread::spawn(move || {
                let mut counter = 0.0_f64;
                while !stop.load(std::sync::atomic::Ordering::Relaxed) {
                    counter = (counter + 1.0) % 1.0;
                    buffer.update(ControlSignals {
                        alert_level: counter,
                        coupling_mode_suggestion: i as f64,
                        ..ControlSignals::default()
                    });
                }
            })
        })
        .collect();
    (buffer, ContentionGuard { stop, handles })
}

fn mutex_contention(writers: usize) -> (std::sync::Arc<MutexControlSignalBuffer>, ContentionGuard) {
    let buffer = std::sync::Arc::new(MutexControlSignalBuffer::new());
    let stop = std::sync::Arc::new(std::sync::atomic::AtomicBool::new(false));
    let handles = (0..writers)
        .map(|i| {
            let buffer = std::sync::Arc::clone(&buffer);
            let stop = std::sync::Arc::clone(&stop);
            thread::spawn(move || {
                let mut counter = 0.0_f64;
                while !stop.load(std::sync::atomic::Ordering::Relaxed) {
                    counter = (counter + 1.0) % 1.0;
                    buffer.update(ControlSignals {
                        alert_level: counter,
                        coupling_mode_suggestion: i as f64,
                        ..ControlSignals::default()
                    });
                }
            })
        })
        .collect();
    (buffer, ContentionGuard { stop, handles })
}

fn bench_control_buffer_reads(c: &mut Criterion) {
    let mut group = c.benchmark_group("control_buffer_read_under_contention");
    group.measurement_time(Duration::from_secs(5));

    for writers in [0_usize, 1, 4] {
        let (lock_free, _guard) = lock_free_contention(writers);
        group.bench_with_input(BenchmarkId::new("lock_free", writers), &writers, |b, _| {
            b.iter(|| criterion::black_box(lock_free.latest()));
        });

        let (mutex, _guard) = mutex_contention(writers);
        group.bench_with_input(BenchmarkId::new("mutex", writers), &writers, |b, _| {
            b.iter(|| criterion::black_box(mutex.latest()));
        });
    }

    group.finish();
}

criterion_group!(benches, bench_control_buffer_reads);
criterion_main!(benches);
