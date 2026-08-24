//! Manual p50/p95 latency pilot: WP-029's lock-free `ControlSignalBuffer` vs.
//! a same-language `Mutex`-guarded re-implementation of PRINet 3.0's design,
//! under concurrent writer contention.
//!
//! This is deliberately a *pilot*, not a scientific benchmark (Development
//! Workflow Standards §3, S1 exit criteria: "no scientific conclusion claims
//! from pilots"): one process, one host, wall-clock timing. It exists to
//! produce the raw p50/p95 numbers behind the WP-029 acceptance criterion
//! ("p50/p95 instrumentation is valid and latency pilot improves on 3.0") and
//! `EVIDENCE/0113-wp029-s1-control-buffer-pilot.json` in a form a human can
//! read directly, in addition to `benches/control_buffer.rs`'s criterion
//! statistics. Run with:
//!
//! ```text
//! cargo run --release --example control_buffer_pilot -p prin-daemon
//! ```
//!
//! `tools/wp029_control_buffer_pilot.py` runs the equivalent measurement
//! against the archived PRINet 3.0 `ControlSignalBuffer` directly, for a
//! genuine cross-language comparison point.

use std::sync::atomic::{AtomicBool, AtomicUsize, Ordering};
use std::sync::{Arc, Mutex};
use std::thread;
use std::time::{Duration, Instant};

use prin_daemon::daemon::ControlSignalBuffer;
use prin_daemon::state::ControlSignals;

const READS_PER_TRIAL: usize = 20_000;
const WRITER_THREADS: usize = 4;

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

fn percentile(sorted_nanos: &[u64], pct: f64) -> u64 {
    if sorted_nanos.is_empty() {
        return 0;
    }
    let rank = ((sorted_nanos.len() - 1) as f64 * pct).round() as usize;
    sorted_nanos[rank.min(sorted_nanos.len() - 1)]
}

struct Trial {
    p50_ns: u64,
    p95_ns: u64,
    max_ns: u64,
}

fn measure_lock_free() -> Trial {
    let buffer = Arc::new(ControlSignalBuffer::new());
    let stop = Arc::new(AtomicBool::new(false));
    let writer_counter = Arc::new(AtomicUsize::new(0));

    let writers: Vec<_> = (0..WRITER_THREADS)
        .map(|i| {
            let buffer = Arc::clone(&buffer);
            let stop = Arc::clone(&stop);
            let writer_counter = Arc::clone(&writer_counter);
            thread::spawn(move || {
                let mut n = 0.0_f64;
                while !stop.load(Ordering::Relaxed) {
                    n = (n + 1.0) % 1000.0;
                    buffer.update(ControlSignals {
                        alert_level: n,
                        coupling_mode_suggestion: i as f64,
                        ..ControlSignals::default()
                    });
                    writer_counter.fetch_add(1, Ordering::Relaxed);
                }
            })
        })
        .collect();

    // Let writers reach steady state before measuring.
    thread::sleep(Duration::from_millis(50));

    let mut samples = Vec::with_capacity(READS_PER_TRIAL);
    for _ in 0..READS_PER_TRIAL {
        let start = Instant::now();
        let signals = buffer.latest();
        let elapsed = start.elapsed();
        std::hint::black_box(&signals);
        samples.push(elapsed.as_nanos() as u64);
    }

    stop.store(true, Ordering::Relaxed);
    for w in writers {
        let _ = w.join();
    }

    samples.sort_unstable();
    Trial {
        p50_ns: percentile(&samples, 0.50),
        p95_ns: percentile(&samples, 0.95),
        max_ns: *samples.last().expect("non-empty"),
    }
}

fn measure_mutex() -> Trial {
    let buffer = Arc::new(MutexControlSignalBuffer::new());
    let stop = Arc::new(AtomicBool::new(false));

    let writers: Vec<_> = (0..WRITER_THREADS)
        .map(|i| {
            let buffer = Arc::clone(&buffer);
            let stop = Arc::clone(&stop);
            thread::spawn(move || {
                let mut n = 0.0_f64;
                while !stop.load(Ordering::Relaxed) {
                    n = (n + 1.0) % 1000.0;
                    buffer.update(ControlSignals {
                        alert_level: n,
                        coupling_mode_suggestion: i as f64,
                        ..ControlSignals::default()
                    });
                }
            })
        })
        .collect();

    thread::sleep(Duration::from_millis(50));

    let mut samples = Vec::with_capacity(READS_PER_TRIAL);
    for _ in 0..READS_PER_TRIAL {
        let start = Instant::now();
        let signals = buffer.latest();
        let elapsed = start.elapsed();
        std::hint::black_box(&signals);
        samples.push(elapsed.as_nanos() as u64);
    }

    stop.store(true, Ordering::Relaxed);
    for w in writers {
        let _ = w.join();
    }

    samples.sort_unstable();
    Trial {
        p50_ns: percentile(&samples, 0.50),
        p95_ns: percentile(&samples, 0.95),
        max_ns: *samples.last().expect("non-empty"),
    }
}

fn main() {
    let lock_free = measure_lock_free();
    let mutex = measure_mutex();

    println!(
        "{{\"writer_threads\": {WRITER_THREADS}, \"reads_per_trial\": {READS_PER_TRIAL}, \
         \"lock_free\": {{\"p50_ns\": {}, \"p95_ns\": {}, \"max_ns\": {}}}, \
         \"mutex_baseline\": {{\"p50_ns\": {}, \"p95_ns\": {}, \"max_ns\": {}}}}}",
        lock_free.p50_ns,
        lock_free.p95_ns,
        lock_free.max_ns,
        mutex.p50_ns,
        mutex.p95_ns,
        mutex.max_ns,
    );
}
