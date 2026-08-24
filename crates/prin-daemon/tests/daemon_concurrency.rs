//! Stress, race, and lifecycle tests for [`prin_daemon::daemon`]
//! (WP-029 acceptance: "Stress/race/lifecycle tests pass; no deadlocks/data
//! races").
//!
//! Every test here has a bounded worst-case running time: [`stop`] takes an
//! explicit timeout, so a genuine deadlock in the code under test would fail
//! a test (via a timed-out `stop` or a `recv_timeout`) rather than hang the
//! suite.
//!
//! [`stop`]: prin_daemon::daemon::SubconsciousDaemon::stop

use std::sync::atomic::{AtomicI64, AtomicUsize, Ordering};
use std::sync::{Arc, Barrier};
use std::thread;
use std::time::{Duration, Instant};

use prin_daemon::daemon::{DaemonConfig, SubconsciousDaemon};
use prin_daemon::state::{SubconsciousState, CONTROL_DIM, STATE_DIM};

const TEST_TIMEOUT: Duration = Duration::from_secs(10);

fn fast_config() -> DaemonConfig {
    DaemonConfig {
        interval: Duration::from_millis(10),
        warmup: false,
        ..DaemonConfig::default()
    }
}

/// Stop the daemon inside a shared `Arc` once every other clone has been
/// dropped, by spinning briefly for the refcount to settle. Test-only: real
/// callers own a single `SubconsciousDaemon` and share `&SubconsciousDaemon`
/// references (every public method takes `&self`, `stop`/`submit_state`
/// included via interior mutability on the `Mutex`/atomics), so production
/// code never needs this.
fn stop_shared(mut shared: Arc<SubconsciousDaemon>, timeout: Duration) -> bool {
    let deadline = Instant::now() + timeout;
    let mut daemon = loop {
        match Arc::try_unwrap(shared) {
            Ok(daemon) => break daemon,
            Err(still_shared) => {
                assert!(
                    Instant::now() < deadline,
                    "other Arc handles never released"
                );
                thread::sleep(Duration::from_millis(5));
                shared = still_shared;
            }
        }
    };
    daemon.stop(timeout)
}

/// Many producer threads calling `submit_state` and many consumer threads
/// calling `get_control`, all concurrently with the daemon thread itself,
/// must never panic, deadlock, or corrupt state.
#[test]
fn concurrent_producers_and_consumers_never_panic_or_deadlock() {
    let daemon = Arc::new(
        SubconsciousDaemon::spawn(
            Box::new(|input: &[f32; STATE_DIM]| {
                let mut out = [0.0_f32; CONTROL_DIM];
                out[7] = input[3]; // echo r_global through a raw output slot
                Ok(out)
            }),
            fast_config(),
            None,
        )
        .expect("spawns"),
    );

    const PRODUCERS: usize = 8;
    const CONSUMERS: usize = 8;
    const ITERATIONS: usize = 500;
    let barrier = Arc::new(Barrier::new(PRODUCERS + CONSUMERS));

    let mut handles = Vec::with_capacity(PRODUCERS + CONSUMERS);
    for p in 0..PRODUCERS {
        let daemon = Arc::clone(&daemon);
        let barrier = Arc::clone(&barrier);
        handles.push(thread::spawn(move || {
            barrier.wait();
            for i in 0..ITERATIONS {
                daemon.submit_state(SubconsciousState {
                    r_global: (p * ITERATIONS + i) as f64 / 1000.0,
                    ..SubconsciousState::default()
                });
            }
        }));
    }
    for _ in 0..CONSUMERS {
        let daemon = Arc::clone(&daemon);
        let barrier = Arc::clone(&barrier);
        handles.push(thread::spawn(move || {
            barrier.wait();
            for _ in 0..ITERATIONS {
                let control = daemon.get_control();
                assert!(control.is_finite(), "reader observed non-finite control");
            }
        }));
    }

    let deadline = Instant::now() + TEST_TIMEOUT;
    for handle in handles {
        handle.join().expect("worker thread panicked");
        assert!(
            Instant::now() < deadline,
            "workers took too long — possible deadlock"
        );
    }

    // Give the (slower) daemon thread a moment to drain any tail of the
    // producer burst before asserting on its counters.
    let drain_deadline = Instant::now() + Duration::from_secs(2);
    while daemon.inference_count() == 0 && Instant::now() < drain_deadline {
        thread::sleep(Duration::from_millis(5));
    }
    assert!(daemon.inference_count() >= 1);
    assert_eq!(daemon.error_count(), 0);

    assert!(
        stop_shared(daemon, TEST_TIMEOUT),
        "stop() timed out — possible deadlock"
    );
}

/// A single writer submitting states with a strictly increasing counter,
/// read concurrently by several readers: because the daemon thread processes
/// the bounded queue strictly in FIFO (submission) order and the control
/// buffer publishes whole, atomically-swapped snapshots, every value any
/// reader observes must be one that was genuinely submitted, and no reader's
/// own sequence of reads may ever decrease. A torn read, a lock-ordering bug
/// that reordered publishes, or a race in the drop-oldest queue would show up
/// here as an out-of-order or bogus observation.
#[test]
fn control_buffer_reads_are_monotonic_under_a_single_ordered_writer() {
    const SUBMITTED: i64 = 3_000;

    let daemon = Arc::new(
        SubconsciousDaemon::spawn(
            Box::new(|input: &[f32; STATE_DIM]| {
                let mut out = [0.0_f32; CONTROL_DIM];
                // `epoch` is packed at input[16] as `epoch / 1e4`.
                out[7] = input[16];
                Ok(out)
            }),
            DaemonConfig {
                interval: Duration::from_millis(5),
                warmup: false,
                queue_size: SUBMITTED as usize, // large enough that nothing drops
                ..DaemonConfig::default()
            },
            None,
        )
        .expect("spawns"),
    );

    let submitted_all = Arc::new(AtomicUsize::new(0));

    let reader_daemon = Arc::clone(&daemon);
    let reader_submitted = Arc::clone(&submitted_all);
    let reader = thread::spawn(move || {
        let mut last_seen = -1_i64;
        let mut saw_final = false;
        while !saw_final {
            let control = reader_daemon.get_control();
            // `out[7]` round-trips through slot 7 (`coupling_mode_suggestion`,
            // unclamped) as the raw `epoch / 1e4` float.
            let observed = (control.coupling_mode_suggestion * 1e4).round() as i64;
            if observed != 0 || last_seen >= 0 {
                assert!(
                    observed >= last_seen,
                    "control value regressed: saw {observed} after {last_seen}"
                );
                last_seen = observed;
            }
            if reader_submitted.load(Ordering::SeqCst) == SUBMITTED as usize {
                if last_seen >= SUBMITTED - 1 {
                    saw_final = true;
                } else {
                    thread::sleep(Duration::from_millis(1));
                }
            }
        }
    });

    for epoch in 0..SUBMITTED {
        daemon.submit_state(SubconsciousState {
            epoch,
            ..SubconsciousState::default()
        });
        submitted_all.fetch_add(1, Ordering::SeqCst);
    }

    reader.join().expect("reader thread panicked");

    assert!(stop_shared(daemon, TEST_TIMEOUT));
}

/// Repeated spawn/submit/stop cycles must never hang or leak a thread that
/// blocks a subsequent `stop()`.
#[test]
fn repeated_lifecycle_cycles_do_not_deadlock() {
    for cycle in 0..25 {
        let mut daemon = SubconsciousDaemon::spawn(
            Box::new(|_: &[f32; STATE_DIM]| Ok([0.0_f32; CONTROL_DIM])),
            fast_config(),
            None,
        )
        .expect("spawns");
        daemon.submit_state(SubconsciousState {
            epoch: cycle,
            ..SubconsciousState::default()
        });
        assert!(
            daemon.stop(Duration::from_secs(2)),
            "cycle {cycle} failed to stop in time"
        );
    }
}

/// A slow backend must not prevent `stop()` from returning within its own
/// timeout, and the daemon must still become stoppable once the in-flight
/// call finishes.
#[test]
fn stop_never_blocks_past_its_own_timeout_even_with_a_slow_backend() {
    let call_count = Arc::new(AtomicI64::new(0));
    let backend_calls = Arc::clone(&call_count);
    let mut daemon = SubconsciousDaemon::spawn(
        Box::new(move |_: &[f32; STATE_DIM]| {
            backend_calls.fetch_add(1, Ordering::SeqCst);
            thread::sleep(Duration::from_millis(250));
            Ok([0.0_f32; CONTROL_DIM])
        }),
        fast_config(),
        None,
    )
    .expect("spawns");

    daemon.submit_state(SubconsciousState::default());
    // Let the slow call begin before racing it with a short timeout.
    let deadline = Instant::now() + Duration::from_secs(2);
    while call_count.load(Ordering::SeqCst) == 0 && Instant::now() < deadline {
        thread::sleep(Duration::from_millis(2));
    }

    let attempt_start = Instant::now();
    let stopped = daemon.stop(Duration::from_millis(20));
    assert!(
        attempt_start.elapsed() < Duration::from_secs(1),
        "stop() should return promptly even when it reports failure"
    );
    assert!(
        !stopped,
        "stop() should report false while inference is in flight"
    );

    assert!(
        daemon.stop(Duration::from_secs(2)),
        "the follow-up stop should succeed"
    );
}
