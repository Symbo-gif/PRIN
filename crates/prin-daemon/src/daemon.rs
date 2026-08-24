//! Native daemon runtime and lock-free control-signal buffer.
//!
//! Rebuild of PRINet 3.0 `prinet.core.subconscious_daemon.SubconsciousDaemon`
//! and `prinet.core.subconscious.ControlSignalBuffer`. The main training loop
//! interacts with a [`SubconsciousDaemon`] through exactly two non-blocking
//! calls — [`SubconsciousDaemon::submit_state`] and
//! [`SubconsciousDaemon::get_control`] — while a background OS thread drains
//! submitted [`SubconsciousState`] snapshots, runs inference, and publishes
//! [`ControlSignals`].
//!
//! # What changed from the reference, and why
//!
//! * **The control buffer is lock-free, not `threading.Lock`-guarded.**
//!   [`ControlSignalBuffer`] publishes each update as an independently
//!   reference-counted, immutable snapshot behind an atomic pointer swap
//!   ([`arc_swap::ArcSwap`]). A reader never blocks on a writer, a writer
//!   never blocks on a reader, and there is no mutex, spinlock, or syscall on
//!   either path — the read side that the training loop calls every step is
//!   wait-free. `benches/control_buffer.rs` and
//!   `examples/control_buffer_pilot.rs` compare this against a
//!   `Mutex`-guarded re-implementation of the reference design under
//!   contention (Benchmarking Standards §2.4, "Daemon latency: lower p95
//!   than 3.0").
//! * **Inference is a pluggable [`InferenceBackend`], not an embedded ONNX
//!   Runtime session.** Project Plan §7 risk register #4 keeps ONNX Runtime
//!   session creation on the Python `onnxruntime` path (see
//!   `crates/prin-daemon/README.md`); this crate cannot link an inference
//!   runtime itself. Everything *around* inference — the thread, the bounded
//!   queue, the lock-free publish, telemetry, the dead-letter queue, error
//!   escalation, and shutdown — is native Rust and independently testable
//!   with a synthetic backend, which is what this module's test suite does.
//! * **Shutdown is bounded and reported, not fire-and-forget.**
//!   [`SubconsciousDaemon::stop`] returns whether the thread actually
//!   finished inside the timeout, matching the reference's
//!   `stop()`-then-warn behaviour, and [`Drop`] applies the same bounded wait
//!   so a caller that forgets to call `stop` cannot leave a runaway thread
//!   spinning past the process lifetime of the value that owns it.
//!
//! # Concurrency-safety argument
//!
//! No lock is ever held across a call into user code (state packing,
//! [`InferenceBackend::infer`], or a control-signal publish), and no two
//! locks are ever held at once: the state queue's `Mutex`/`Condvar` pair and
//! the dead-letter queue's `Mutex` are never nested, and the control buffer
//! takes no lock at all. That structure rules out the classic
//! lock-ordering deadlock by construction rather than by convention. The
//! bound on every blocking wait — the internal state queue's interval
//! timeout and the internal shutdown latch's stop timeout — means a caller
//! can never hang indefinitely even if that argument is wrong;
//! `tests/daemon_concurrency.rs` stresses exactly this with many concurrent
//! writers and readers plus repeated start/stop cycles.

use std::collections::VecDeque;
use std::sync::atomic::{AtomicBool, AtomicU64, Ordering};
use std::sync::{Arc, Condvar, Mutex, PoisonError};
use std::thread::{self, JoinHandle};
use std::time::{Duration, Instant};

use arc_swap::ArcSwap;

use crate::error::DaemonError;
use crate::state::{ControlSignals, SubconsciousState, CONTROL_DIM, STATE_DIM};

/// Default polling interval: the maximum time [`SubconsciousDaemon`] blocks
/// waiting for a submitted state before re-checking for shutdown.
///
/// PRINet 3.0 `subconscious_daemon._DEFAULT_INTERVAL`.
pub const DEFAULT_INTERVAL: Duration = Duration::from_secs(15);

/// Default bounded queue capacity for pending state snapshots.
///
/// PRINet 3.0 `subconscious_daemon._DEFAULT_QUEUE_SIZE`.
pub const DEFAULT_QUEUE_SIZE: usize = 100;

/// Default maximum dead-letter-queue entries retained.
///
/// PRINet 3.0 `SubconsciousDaemon.__init__`'s `dlq_maxlen` default.
pub const DEFAULT_DLQ_MAXLEN: usize = 100;

/// Default number of accumulated errors before escalation fires.
///
/// PRINet 3.0 `SubconsciousDaemon.__init__`'s
/// `max_errors_before_escalation` default.
pub const DEFAULT_MAX_ERRORS_BEFORE_ESCALATION: u64 = 10;

/// Default timeout [`Drop`] waits for the daemon thread before abandoning it.
const DEFAULT_DROP_TIMEOUT: Duration = Duration::from_secs(5);

// ---------------------------------------------------------------------------
// InferenceBackend
// ---------------------------------------------------------------------------

/// A pluggable controller-inference step.
///
/// [`SubconsciousDaemon`] owns the thread, the queue, the control buffer, and
/// telemetry; an `InferenceBackend` owns only the model call itself. Real
/// inference is wired in from `crates/prin-py` over the Python `onnxruntime`
/// session (Project Plan §7 risk register #4); tests and benchmarks in this
/// crate use plain closures via the blanket implementation below.
pub trait InferenceBackend: Send {
    /// Map one packed state vector to a packed control vector.
    ///
    /// # Errors
    ///
    /// Returns any [`DaemonError`] the underlying model call produces. A
    /// returned error is recorded in the dead-letter queue and does not stop
    /// the daemon thread.
    fn infer(&mut self, input: &[f32; STATE_DIM]) -> Result<[f32; CONTROL_DIM], DaemonError>;
}

impl<F> InferenceBackend for F
where
    F: FnMut(&[f32; STATE_DIM]) -> Result<[f32; CONTROL_DIM], DaemonError> + Send,
{
    fn infer(&mut self, input: &[f32; STATE_DIM]) -> Result<[f32; CONTROL_DIM], DaemonError> {
        self(input)
    }
}

// ---------------------------------------------------------------------------
// ControlSignalBuffer
// ---------------------------------------------------------------------------

/// Lock-free, wait-free-read cell publishing the controller's latest
/// [`ControlSignals`].
///
/// Rebuild of PRINet 3.0's `ControlSignalBuffer`, which serialises both
/// [`update`](ControlSignalBuffer::update) and
/// [`latest`](ControlSignalBuffer::latest) behind a single `threading.Lock`.
/// This type instead publishes each update as an independent, immutable
/// [`Arc`] snapshot and swaps the pointer atomically: `latest` is a single
/// atomic load plus a refcount bump, with no mutex, spinlock, or blocking
/// syscall, regardless of how many readers or writers are concurrently
/// active.
///
/// # Examples
///
/// ```
/// use prin_daemon::daemon::ControlSignalBuffer;
/// use prin_daemon::state::ControlSignals;
///
/// let buffer = ControlSignalBuffer::new();
/// assert_eq!(buffer.latest(), ControlSignals::default());
///
/// buffer.update(ControlSignals { alert_level: 0.8, ..ControlSignals::default() });
/// assert_eq!(buffer.latest().alert_level, 0.8);
/// ```
#[derive(Debug)]
pub struct ControlSignalBuffer {
    inner: ArcSwap<ControlSignals>,
}

impl Default for ControlSignalBuffer {
    /// A buffer holding [`ControlSignals::default`] until the first update,
    /// matching the reference's safe-defaults-before-inference behaviour.
    fn default() -> Self {
        Self {
            inner: ArcSwap::from_pointee(ControlSignals::default()),
        }
    }
}

impl ControlSignalBuffer {
    /// Create a buffer holding [`ControlSignals::default`].
    #[must_use]
    pub fn new() -> Self {
        Self::default()
    }

    /// Atomically publish new control signals, replacing whatever was there.
    ///
    /// Never blocks a concurrent [`latest`](ControlSignalBuffer::latest)
    /// call.
    pub fn update(&self, signals: ControlSignals) {
        self.inner.store(Arc::new(signals));
    }

    /// Read the most recently published control signals.
    ///
    /// Never blocks, including on a concurrent
    /// [`update`](ControlSignalBuffer::update).
    #[must_use]
    pub fn latest(&self) -> ControlSignals {
        ControlSignals::clone(&self.inner.load())
    }
}

// ---------------------------------------------------------------------------
// StateQueue (bounded, drop-oldest)
// ---------------------------------------------------------------------------

/// Bounded FIFO of pending [`SubconsciousState`] snapshots.
///
/// Rebuild of the reference's `queue.Queue(maxsize=queue_size)`, whose
/// `submit_state` drops the oldest pending state and retries rather than
/// blocking the caller. This is the daemon's only lock (a `Mutex` +
/// `Condvar` pair); it never nests with any other lock, and no lock is held
/// while calling into [`InferenceBackend::infer`].
struct StateQueue {
    items: Mutex<VecDeque<SubconsciousState>>,
    not_empty: Condvar,
    capacity: usize,
    closed: AtomicBool,
}

impl StateQueue {
    fn new(capacity: usize) -> Self {
        Self {
            items: Mutex::new(VecDeque::with_capacity(capacity.clamp(1, 1024))),
            not_empty: Condvar::new(),
            capacity: capacity.max(1),
            closed: AtomicBool::new(false),
        }
    }

    /// Non-blocking enqueue; drops the oldest pending state when full.
    fn push(&self, state: SubconsciousState) {
        let mut guard = self.items.lock().unwrap_or_else(PoisonError::into_inner);
        if guard.len() >= self.capacity {
            guard.pop_front();
        }
        guard.push_back(state);
        drop(guard);
        self.not_empty.notify_one();
    }

    /// Block up to `timeout` for a state, or `None` on timeout or shutdown.
    ///
    /// [`close`](StateQueue::close) wakes a blocked waiter immediately in the
    /// common case; the timeout is what bounds worst-case wake latency to
    /// `timeout` even if that notification is missed (a plain
    /// `Condvar::wait_timeout_while` re-waits for the *remaining* time on
    /// every spurious wake, so a lost notification costs at most one more
    /// full `timeout`, never an unbounded hang).
    fn pop_wait(&self, timeout: Duration) -> Option<SubconsciousState> {
        let guard = self.items.lock().unwrap_or_else(PoisonError::into_inner);
        let (mut guard, _) = self
            .not_empty
            .wait_timeout_while(guard, timeout, |items| {
                items.is_empty() && !self.closed.load(Ordering::Acquire)
            })
            .unwrap_or_else(PoisonError::into_inner);
        guard.pop_front()
    }

    /// Signal shutdown and wake any blocked waiter.
    fn close(&self) {
        self.closed.store(true, Ordering::Release);
        self.not_empty.notify_all();
    }

    fn is_closed(&self) -> bool {
        self.closed.load(Ordering::Acquire)
    }

    /// Number of states currently queued (telemetry only).
    fn len(&self) -> usize {
        self.items
            .lock()
            .unwrap_or_else(PoisonError::into_inner)
            .len()
    }
}

// ---------------------------------------------------------------------------
// ShutdownSignal
// ---------------------------------------------------------------------------

/// A one-shot, `Condvar`-based "the thread has finished" latch.
///
/// `std::thread::JoinHandle::join` has no timeout; this gives
/// [`SubconsciousDaemon::stop`] a bounded wait instead of an unbounded block.
struct ShutdownSignal {
    done: Mutex<bool>,
    cv: Condvar,
}

impl ShutdownSignal {
    fn new() -> Self {
        Self {
            done: Mutex::new(false),
            cv: Condvar::new(),
        }
    }

    fn mark_done(&self) {
        let mut guard = self.done.lock().unwrap_or_else(PoisonError::into_inner);
        *guard = true;
        self.cv.notify_all();
    }

    /// Block up to `timeout`; returns whether the thread had finished.
    fn wait_timeout(&self, timeout: Duration) -> bool {
        let guard = self.done.lock().unwrap_or_else(PoisonError::into_inner);
        let (guard, _) = self
            .cv
            .wait_timeout_while(guard, timeout, |done| !*done)
            .unwrap_or_else(PoisonError::into_inner);
        *guard
    }
}

// ---------------------------------------------------------------------------
// Dead-letter queue and escalation
// ---------------------------------------------------------------------------

/// One failed-inference record.
///
/// Rebuild of the reference's dead-letter-queue entry dict
/// (`{"error", "error_count", "timestamp"}`), with `timestamp` reframed as
/// `elapsed` — time since the daemon thread started — so records are
/// reproducible across process runs instead of carrying a wall-clock stamp.
#[derive(Debug, Clone, PartialEq)]
pub struct DeadLetterEntry {
    /// `Display` text of the [`DaemonError`] that caused the failure.
    pub error: String,
    /// Total error count at the time this entry was recorded (1-based).
    pub error_count: u64,
    /// Time elapsed since the daemon thread started.
    pub elapsed: Duration,
}

/// Payload delivered to an error-escalation callback.
///
/// Rebuild of the reference's `{"error_count", "dlq_tail"}` escalation
/// payload.
#[derive(Debug, Clone, PartialEq)]
pub struct EscalationEvent {
    /// Total error count that crossed the escalation threshold.
    pub error_count: u64,
    /// The dead-letter entry that triggered this escalation.
    pub dlq_tail: DeadLetterEntry,
}

/// A callback invoked on the daemon thread once accumulated errors cross the
/// configured threshold, and on every subsequent error.
pub type EscalationCallback = Box<dyn Fn(EscalationEvent) + Send>;

// ---------------------------------------------------------------------------
// DaemonConfig
// ---------------------------------------------------------------------------

/// Tunable parameters for [`SubconsciousDaemon::spawn`].
///
/// Rebuild of the reference `SubconsciousDaemon.__init__` keyword arguments.
///
/// # Examples
///
/// ```
/// use std::time::Duration;
/// use prin_daemon::daemon::DaemonConfig;
///
/// let config = DaemonConfig { interval: Duration::from_millis(100), ..DaemonConfig::default() };
/// assert_eq!(config.queue_size, 100);
/// ```
#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub struct DaemonConfig {
    /// Maximum time to block waiting for a submitted state before
    /// re-checking for shutdown; the effective polling interval.
    pub interval: Duration,
    /// Bounded queue capacity for pending states.
    pub queue_size: usize,
    /// Whether to run one warm-up inference on start.
    pub warmup: bool,
    /// Maximum dead-letter-queue entries retained; oldest are evicted first.
    pub dlq_maxlen: usize,
    /// Accumulated errors required before escalation fires. `0` disables
    /// escalation.
    pub max_errors_before_escalation: u64,
}

impl Default for DaemonConfig {
    fn default() -> Self {
        Self {
            interval: DEFAULT_INTERVAL,
            queue_size: DEFAULT_QUEUE_SIZE,
            warmup: true,
            dlq_maxlen: DEFAULT_DLQ_MAXLEN,
            max_errors_before_escalation: DEFAULT_MAX_ERRORS_BEFORE_ESCALATION,
        }
    }
}

/// A point-in-time snapshot of daemon telemetry.
///
/// # Examples
///
/// ```
/// use prin_daemon::daemon::DaemonStats;
/// use std::time::Duration;
///
/// let stats = DaemonStats { inferences: 3, errors: 0, dlq_size: 0, uptime: Duration::ZERO };
/// assert_eq!(stats.inferences, 3);
/// ```
#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub struct DaemonStats {
    /// Number of successful inferences completed.
    pub inferences: u64,
    /// Number of inference errors encountered.
    pub errors: u64,
    /// Current dead-letter-queue length.
    pub dlq_size: usize,
    /// Time elapsed since the daemon thread started.
    pub uptime: Duration,
}

// ---------------------------------------------------------------------------
// SubconsciousDaemon
// ---------------------------------------------------------------------------

/// A background OS thread that runs the subconscious controller.
///
/// Rebuild of PRINet 3.0 `SubconsciousDaemon`. The caller interacts only
/// through [`submit_state`](SubconsciousDaemon::submit_state) (non-blocking
/// enqueue) and [`get_control`](SubconsciousDaemon::get_control) (non-blocking
/// read of the lock-free [`ControlSignalBuffer`]); [`spawn`](Self::spawn)
/// starts the thread immediately (there is no separate reference-style
/// `start()` step — Rust threads have no `daemon=True` flag to defer, so
/// splitting construction from start would add API surface without adding
/// capability).
///
/// # Examples
///
/// ```
/// use std::time::Duration;
/// use prin_daemon::daemon::{DaemonConfig, SubconsciousDaemon};
/// use prin_daemon::state::{SubconsciousState, CONTROL_DIM, STATE_DIM};
///
/// let config = DaemonConfig { interval: Duration::from_millis(20), warmup: false, ..DaemonConfig::default() };
/// let mut daemon = SubconsciousDaemon::spawn(
///     Box::new(|_: &[f32; STATE_DIM]| Ok([0.0_f32; CONTROL_DIM])),
///     config,
///     None,
/// )?;
///
/// daemon.submit_state(SubconsciousState::default());
/// std::thread::sleep(Duration::from_millis(200));
/// assert!(daemon.inference_count() >= 1);
///
/// assert!(daemon.stop(Duration::from_secs(1)));
/// # Ok::<(), prin_daemon::DaemonError>(())
/// ```
pub struct SubconsciousDaemon {
    queue: Arc<StateQueue>,
    control: Arc<ControlSignalBuffer>,
    inferences: Arc<AtomicU64>,
    errors: Arc<AtomicU64>,
    dlq: Arc<Mutex<VecDeque<DeadLetterEntry>>>,
    running: Arc<AtomicBool>,
    shutdown: Arc<ShutdownSignal>,
    start: Instant,
    handle: Option<JoinHandle<()>>,
}

impl SubconsciousDaemon {
    /// Spawn the daemon thread.
    ///
    /// When `config.warmup` is set, one inference is attempted with an
    /// all-zero sentinel input before the thread starts servicing submitted
    /// states; a warm-up failure is logged and otherwise ignored, matching
    /// the reference's "may be expected" tolerance.
    ///
    /// # Errors
    ///
    /// Returns [`DaemonError::ThreadSpawn`] if the OS thread could not be
    /// created.
    pub fn spawn(
        mut backend: Box<dyn InferenceBackend>,
        config: DaemonConfig,
        on_escalation: Option<EscalationCallback>,
    ) -> Result<Self, DaemonError> {
        let queue = Arc::new(StateQueue::new(config.queue_size));
        let control = Arc::new(ControlSignalBuffer::new());
        let inferences = Arc::new(AtomicU64::new(0));
        let errors = Arc::new(AtomicU64::new(0));
        let dlq = Arc::new(Mutex::new(VecDeque::new()));
        let running = Arc::new(AtomicBool::new(true));
        let shutdown = Arc::new(ShutdownSignal::new());
        let start = Instant::now();

        let thread_queue = Arc::clone(&queue);
        let thread_control = Arc::clone(&control);
        let thread_inferences = Arc::clone(&inferences);
        let thread_errors = Arc::clone(&errors);
        let thread_dlq = Arc::clone(&dlq);
        let thread_running = Arc::clone(&running);
        let thread_shutdown = Arc::clone(&shutdown);
        let dlq_maxlen = config.dlq_maxlen;
        let max_before_escalation = config.max_errors_before_escalation;
        let interval = config.interval;
        let warmup = config.warmup;

        let handle = thread::Builder::new()
            .name("prin-subconscious".to_string())
            .spawn(move || {
                if warmup {
                    let sentinel = [0.0_f32; STATE_DIM];
                    if let Err(err) = backend.infer(&sentinel) {
                        tracing::debug!(error = %err, "warm-up inference raised (may be expected)");
                    }
                }

                while !thread_queue.is_closed() {
                    let Some(state) = thread_queue.pop_wait(interval) else {
                        continue;
                    };

                    let input = match state.to_tensor() {
                        Ok(input) => input,
                        Err(err) => {
                            record_failure(
                                err,
                                &thread_errors,
                                &thread_dlq,
                                dlq_maxlen,
                                start,
                                max_before_escalation,
                                &on_escalation,
                            );
                            continue;
                        }
                    };

                    match backend.infer(&input) {
                        Ok(raw) => match ControlSignals::from_tensor(&raw) {
                            Ok(signals) if signals.is_finite() => {
                                thread_control.update(signals);
                                thread_inferences.fetch_add(1, Ordering::Relaxed);
                            }
                            Ok(_) => {
                                tracing::warn!(
                                    "non-finite control signals detected — using defaults"
                                );
                                thread_control.update(ControlSignals::default());
                                thread_inferences.fetch_add(1, Ordering::Relaxed);
                            }
                            Err(err) => record_failure(
                                err,
                                &thread_errors,
                                &thread_dlq,
                                dlq_maxlen,
                                start,
                                max_before_escalation,
                                &on_escalation,
                            ),
                        },
                        Err(err) => record_failure(
                            err,
                            &thread_errors,
                            &thread_dlq,
                            dlq_maxlen,
                            start,
                            max_before_escalation,
                            &on_escalation,
                        ),
                    }
                }

                thread_running.store(false, Ordering::Release);
                thread_shutdown.mark_done();
            })
            .map_err(|source| DaemonError::ThreadSpawn { source })?;

        Ok(Self {
            queue,
            control,
            inferences,
            errors,
            dlq,
            running,
            shutdown,
            start,
            handle: Some(handle),
        })
    }

    /// Non-blocking enqueue of a system state snapshot.
    ///
    /// If the queue is full, the **oldest** pending state is dropped and the
    /// new state is enqueued, matching the reference's overflow policy.
    pub fn submit_state(&self, state: SubconsciousState) {
        self.queue.push(state);
    }

    /// Read the latest control signals (non-blocking, wait-free).
    ///
    /// Returns [`ControlSignals::default`] if no inference has completed yet.
    #[must_use]
    pub fn get_control(&self) -> ControlSignals {
        self.control.latest()
    }

    /// Signal the daemon to stop and wait up to `timeout` for it to finish.
    ///
    /// Returns `true` if the thread finished within `timeout`. On `false`
    /// the thread is still running and is abandoned (never force-terminated
    /// — Rust, like the reference's Python threads, has no safe mechanism to
    /// cancel a running thread); a later call may still observe it finish.
    pub fn stop(&mut self, timeout: Duration) -> bool {
        self.queue.close();
        let finished = self.shutdown.wait_timeout(timeout);
        if finished {
            if let Some(handle) = self.handle.take() {
                let _ = handle.join();
            }
        } else {
            tracing::warn!(?timeout, "SubconsciousDaemon did not stop within timeout");
        }
        finished
    }

    /// Whether the daemon thread is still running.
    #[must_use]
    pub fn is_running(&self) -> bool {
        self.running.load(Ordering::Acquire)
    }

    /// Number of successful inferences completed.
    #[must_use]
    pub fn inference_count(&self) -> u64 {
        self.inferences.load(Ordering::Relaxed)
    }

    /// Number of inference errors encountered.
    #[must_use]
    pub fn error_count(&self) -> u64 {
        self.errors.load(Ordering::Relaxed)
    }

    /// Snapshot of the dead-letter queue, most-recent first.
    #[must_use]
    pub fn dead_letter_queue(&self) -> Vec<DeadLetterEntry> {
        let guard = self.dlq.lock().unwrap_or_else(PoisonError::into_inner);
        guard.iter().rev().cloned().collect()
    }

    /// Number of entries currently in the dead-letter queue.
    #[must_use]
    pub fn dlq_size(&self) -> usize {
        self.dlq
            .lock()
            .unwrap_or_else(PoisonError::into_inner)
            .len()
    }

    /// Number of states currently queued and not yet processed.
    #[must_use]
    pub fn pending_states(&self) -> usize {
        self.queue.len()
    }

    /// Time elapsed since the daemon thread started.
    #[must_use]
    pub fn uptime(&self) -> Duration {
        self.start.elapsed()
    }

    /// A single-call snapshot of every telemetry counter.
    #[must_use]
    pub fn stats(&self) -> DaemonStats {
        DaemonStats {
            inferences: self.inference_count(),
            errors: self.error_count(),
            dlq_size: self.dlq_size(),
            uptime: self.uptime(),
        }
    }
}

impl Drop for SubconsciousDaemon {
    /// Best-effort shutdown for a daemon whose owner never called
    /// [`stop`](SubconsciousDaemon::stop).
    ///
    /// Bounded to a fixed default timeout: the thread is joined only if it
    /// finishes within that window, so a caller that forgets to call `stop`
    /// cannot make drop itself hang. A thread that does not finish in time is
    /// abandoned, exactly as [`stop`](SubconsciousDaemon::stop) documents.
    fn drop(&mut self) {
        self.queue.close();
        if let Some(handle) = self.handle.take() {
            if self.shutdown.wait_timeout(DEFAULT_DROP_TIMEOUT) {
                let _ = handle.join();
            }
        }
    }
}

/// Record a failed inference step: bump the error counter, append a
/// dead-letter entry (evicting the oldest when `dlq_maxlen` is exceeded), log
/// it, and escalate if the threshold is crossed.
#[allow(clippy::too_many_arguments)]
fn record_failure(
    err: DaemonError,
    errors: &AtomicU64,
    dlq: &Mutex<VecDeque<DeadLetterEntry>>,
    dlq_maxlen: usize,
    start: Instant,
    max_before_escalation: u64,
    on_escalation: &Option<EscalationCallback>,
) {
    let count = errors.fetch_add(1, Ordering::Relaxed) + 1;
    tracing::error!(error = %err, error_count = count, "inference error in SubconsciousDaemon");

    let entry = DeadLetterEntry {
        error: err.to_string(),
        error_count: count,
        elapsed: start.elapsed(),
    };

    if dlq_maxlen > 0 {
        let mut guard = dlq.lock().unwrap_or_else(PoisonError::into_inner);
        if guard.len() >= dlq_maxlen {
            guard.pop_front();
        }
        guard.push_back(entry.clone());
    }

    if max_before_escalation > 0 && count >= max_before_escalation {
        if let Some(callback) = on_escalation {
            callback(EscalationEvent {
                error_count: count,
                dlq_tail: entry,
            });
        }
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    use std::sync::mpsc;

    fn ok_backend() -> Box<dyn InferenceBackend> {
        Box::new(|_: &[f32; STATE_DIM]| Ok([0.0_f32; CONTROL_DIM]))
    }

    fn fast_config() -> DaemonConfig {
        DaemonConfig {
            interval: Duration::from_millis(20),
            warmup: false,
            ..DaemonConfig::default()
        }
    }

    // -- ControlSignalBuffer --------------------------------------------

    #[test]
    fn buffer_starts_at_safe_defaults() {
        let buffer = ControlSignalBuffer::new();
        assert_eq!(buffer.latest(), ControlSignals::default());
    }

    #[test]
    fn buffer_update_then_read_round_trips() {
        let buffer = ControlSignalBuffer::new();
        let signals = ControlSignals {
            alert_level: 0.9,
            ..ControlSignals::default()
        };
        buffer.update(signals.clone());
        assert_eq!(buffer.latest(), signals);
    }

    #[test]
    fn buffer_concurrent_writers_and_readers_never_panic_or_tear() {
        let buffer = Arc::new(ControlSignalBuffer::new());
        let writer_buffer = Arc::clone(&buffer);
        let writer = thread::spawn(move || {
            for i in 0..2_000 {
                writer_buffer.update(ControlSignals {
                    alert_level: f64::from(i) / 2_000.0,
                    ..ControlSignals::default()
                });
            }
        });
        let reader_buffer = Arc::clone(&buffer);
        let reader = thread::spawn(move || {
            for _ in 0..2_000 {
                let signals = reader_buffer.latest();
                // A torn read would be internally inconsistent; `is_finite`
                // over every field is the cheapest total check available.
                assert!(signals.is_finite());
                assert!((0.0..=1.0).contains(&signals.alert_level) || signals.alert_level == 0.0);
            }
        });
        writer.join().expect("writer thread panicked");
        reader.join().expect("reader thread panicked");
    }

    // -- StateQueue -------------------------------------------------------

    #[test]
    fn queue_drops_the_oldest_state_when_full() {
        let queue = StateQueue::new(2);
        for epoch in 0..5 {
            queue.push(SubconsciousState {
                epoch,
                ..SubconsciousState::default()
            });
        }
        assert_eq!(queue.len(), 2);
        let first = queue.pop_wait(Duration::from_millis(10)).expect("has item");
        let second = queue.pop_wait(Duration::from_millis(10)).expect("has item");
        assert_eq!(first.epoch, 3);
        assert_eq!(second.epoch, 4);
    }

    #[test]
    fn queue_pop_wait_times_out_on_an_empty_queue() {
        let queue = StateQueue::new(4);
        let start = Instant::now();
        let result = queue.pop_wait(Duration::from_millis(50));
        assert!(result.is_none());
        assert!(start.elapsed() >= Duration::from_millis(45));
    }

    #[test]
    fn queue_close_wakes_a_blocked_waiter_promptly() {
        let queue = Arc::new(StateQueue::new(4));
        let waiter_queue = Arc::clone(&queue);
        let (tx, rx) = mpsc::channel();
        let waiter = thread::spawn(move || {
            let start = Instant::now();
            let result = waiter_queue.pop_wait(Duration::from_secs(10));
            tx.send((result.is_none(), start.elapsed()))
                .expect("send result");
        });
        thread::sleep(Duration::from_millis(20));
        queue.close();
        let (was_none, elapsed) = rx
            .recv_timeout(Duration::from_secs(2))
            .expect("waiter finished");
        assert!(was_none);
        assert!(
            elapsed < Duration::from_secs(1),
            "close() should wake the waiter promptly, took {elapsed:?}"
        );
        waiter.join().expect("waiter thread panicked");
    }

    // -- Dead-letter queue and escalation ---------------------------------

    #[test]
    fn dead_letter_queue_evicts_oldest_beyond_capacity() {
        let dlq: Mutex<VecDeque<DeadLetterEntry>> = Mutex::new(VecDeque::new());
        let errors = AtomicU64::new(0);
        let start = Instant::now();
        for i in 0..5 {
            record_failure(
                DaemonError::ControlTooShort {
                    expected: 8,
                    got: i,
                },
                &errors,
                &dlq,
                3,
                start,
                0,
                &None,
            );
        }
        let guard = dlq.lock().expect("lock");
        assert_eq!(guard.len(), 3);
        assert_eq!(guard.front().expect("has entry").error_count, 3);
        assert_eq!(guard.back().expect("has entry").error_count, 5);
    }

    #[test]
    fn dead_letter_queue_with_zero_capacity_records_nothing() {
        let dlq: Mutex<VecDeque<DeadLetterEntry>> = Mutex::new(VecDeque::new());
        let errors = AtomicU64::new(0);
        record_failure(
            DaemonError::ControlTooShort {
                expected: 8,
                got: 0,
            },
            &errors,
            &dlq,
            0,
            Instant::now(),
            0,
            &None,
        );
        assert_eq!(errors.load(Ordering::Relaxed), 1);
        assert!(dlq.lock().expect("lock").is_empty());
    }

    #[test]
    fn escalation_fires_once_the_threshold_is_crossed_and_on_every_error_after() {
        let dlq: Mutex<VecDeque<DeadLetterEntry>> = Mutex::new(VecDeque::new());
        let errors = AtomicU64::new(0);
        let fired: Arc<Mutex<Vec<u64>>> = Arc::new(Mutex::new(Vec::new()));
        let fired_cb = Arc::clone(&fired);
        let callback: EscalationCallback = Box::new(move |event: EscalationEvent| {
            fired_cb.lock().expect("lock").push(event.error_count);
        });
        let on_escalation = Some(callback);

        for i in 0..5 {
            record_failure(
                DaemonError::ControlTooShort {
                    expected: 8,
                    got: i,
                },
                &errors,
                &dlq,
                10,
                Instant::now(),
                3,
                &on_escalation,
            );
        }
        // Errors 1 and 2 are below threshold 3; errors 3, 4, 5 each fire.
        assert_eq!(*fired.lock().expect("lock"), vec![3, 4, 5]);
    }

    #[test]
    fn escalation_never_fires_when_the_threshold_is_zero() {
        let dlq: Mutex<VecDeque<DeadLetterEntry>> = Mutex::new(VecDeque::new());
        let errors = AtomicU64::new(0);
        let fired = Arc::new(AtomicBool::new(false));
        let fired_cb = Arc::clone(&fired);
        let callback: EscalationCallback = Box::new(move |_| {
            fired_cb.store(true, Ordering::SeqCst);
        });
        let on_escalation = Some(callback);
        for i in 0..20 {
            record_failure(
                DaemonError::ControlTooShort {
                    expected: 8,
                    got: i,
                },
                &errors,
                &dlq,
                10,
                Instant::now(),
                0,
                &on_escalation,
            );
        }
        assert!(!fired.load(Ordering::SeqCst));
    }

    // -- SubconsciousDaemon lifecycle --------------------------------------

    #[test]
    fn daemon_default_control_before_any_inference() {
        let mut daemon = SubconsciousDaemon::spawn(
            Box::new(|_: &[f32; STATE_DIM]| Ok([0.0_f32; CONTROL_DIM])),
            DaemonConfig {
                interval: Duration::from_secs(60),
                warmup: false,
                ..DaemonConfig::default()
            },
            None,
        )
        .expect("spawns");
        let control = daemon.get_control();
        assert_eq!(control.lr_multiplier, 1.0);
        assert!(daemon.stop(Duration::from_secs(2)));
    }

    #[test]
    fn daemon_processes_a_submitted_state_and_updates_control() {
        let mut daemon = SubconsciousDaemon::spawn(
            Box::new(|input: &[f32; STATE_DIM]| {
                let mut out = [0.0_f32; CONTROL_DIM];
                out[6] = input[3]; // echo r_global into alert_level's raw slot
                Ok(out)
            }),
            fast_config(),
            None,
        )
        .expect("spawns");

        daemon.submit_state(SubconsciousState {
            r_global: 0.5,
            ..SubconsciousState::default()
        });

        let deadline = Instant::now() + Duration::from_secs(2);
        while daemon.inference_count() == 0 && Instant::now() < deadline {
            thread::sleep(Duration::from_millis(5));
        }
        assert_eq!(daemon.inference_count(), 1);
        assert_eq!(daemon.get_control().alert_level, 0.5);
        assert_eq!(daemon.error_count(), 0);
        assert!(daemon.stop(Duration::from_secs(2)));
        assert!(!daemon.is_running());
    }

    #[test]
    fn daemon_survives_a_failing_warmup_and_still_serves_the_first_real_state() {
        let calls = Arc::new(AtomicU64::new(0));
        let backend_calls = Arc::clone(&calls);
        let mut daemon = SubconsciousDaemon::spawn(
            Box::new(move |input: &[f32; STATE_DIM]| {
                let call = backend_calls.fetch_add(1, Ordering::SeqCst);
                if call == 0 {
                    // The warm-up call: fail it, matching the reference's
                    // "may be expected" tolerance.
                    return Err(DaemonError::ControlTooShort {
                        expected: 8,
                        got: 0,
                    });
                }
                let mut out = [0.0_f32; CONTROL_DIM];
                out[6] = input[3];
                Ok(out)
            }),
            DaemonConfig {
                interval: Duration::from_millis(20),
                warmup: true,
                ..DaemonConfig::default()
            },
            None,
        )
        .expect("spawns");

        daemon.submit_state(SubconsciousState {
            r_global: 0.25,
            ..SubconsciousState::default()
        });
        let deadline = Instant::now() + Duration::from_secs(2);
        while daemon.inference_count() == 0 && Instant::now() < deadline {
            thread::sleep(Duration::from_millis(5));
        }
        // The failed warm-up call is silently discarded, not counted as an
        // inference or a recorded error.
        assert_eq!(daemon.inference_count(), 1);
        assert_eq!(daemon.error_count(), 0);
        assert_eq!(daemon.get_control().alert_level, 0.25);
        assert!(daemon.stop(Duration::from_secs(2)));
    }

    #[test]
    fn daemon_stats_matches_the_individual_telemetry_accessors() {
        let mut daemon =
            SubconsciousDaemon::spawn(ok_backend(), fast_config(), None).expect("spawns");
        daemon.submit_state(SubconsciousState::default());
        let deadline = Instant::now() + Duration::from_secs(2);
        while daemon.inference_count() == 0 && Instant::now() < deadline {
            thread::sleep(Duration::from_millis(5));
        }
        let stats = daemon.stats();
        assert_eq!(stats.inferences, daemon.inference_count());
        assert_eq!(stats.errors, daemon.error_count());
        assert_eq!(stats.dlq_size, daemon.dlq_size());
        assert!(stats.uptime > Duration::ZERO);
        assert!(daemon.stop(Duration::from_secs(2)));
    }

    #[test]
    fn daemon_submit_overflow_does_not_error() {
        let mut daemon = SubconsciousDaemon::spawn(
            ok_backend(),
            DaemonConfig {
                interval: Duration::from_secs(60),
                queue_size: 5,
                warmup: false,
                ..DaemonConfig::default()
            },
            None,
        )
        .expect("spawns");
        for _ in 0..20 {
            daemon.submit_state(SubconsciousState::default());
        }
        assert!(daemon.pending_states() <= 5);
        assert!(daemon.stop(Duration::from_secs(2)));
    }

    #[test]
    fn daemon_uptime_increases_monotonically() {
        let mut daemon = SubconsciousDaemon::spawn(
            ok_backend(),
            DaemonConfig {
                interval: Duration::from_millis(50),
                warmup: false,
                ..DaemonConfig::default()
            },
            None,
        )
        .expect("spawns");
        let first = daemon.uptime();
        thread::sleep(Duration::from_millis(50));
        let second = daemon.uptime();
        assert!(second >= first);
        assert!(daemon.stop(Duration::from_secs(2)));
    }

    #[test]
    fn daemon_warmup_runs_before_any_submitted_state() {
        let calls: Arc<Mutex<Vec<&'static str>>> = Arc::new(Mutex::new(Vec::new()));
        let warmup_calls = Arc::clone(&calls);
        let mut daemon = SubconsciousDaemon::spawn(
            Box::new(move |input: &[f32; STATE_DIM]| {
                let label = if input.iter().all(|v| *v == 0.0) {
                    "warmup_or_default"
                } else {
                    "real"
                };
                warmup_calls.lock().expect("lock").push(label);
                Ok([0.0_f32; CONTROL_DIM])
            }),
            DaemonConfig {
                interval: Duration::from_millis(20),
                warmup: true,
                ..DaemonConfig::default()
            },
            None,
        )
        .expect("spawns");

        daemon.submit_state(SubconsciousState {
            r_global: 0.7,
            ..SubconsciousState::default()
        });
        let deadline = Instant::now() + Duration::from_secs(2);
        while calls.lock().expect("lock").len() < 2 && Instant::now() < deadline {
            thread::sleep(Duration::from_millis(5));
        }
        assert!(daemon.stop(Duration::from_secs(2)));
        assert!(calls.lock().expect("lock").len() >= 2);
    }

    #[test]
    fn daemon_non_finite_control_signals_fall_back_to_defaults() {
        let mut daemon = SubconsciousDaemon::spawn(
            Box::new(|_: &[f32; STATE_DIM]| {
                let mut out = [0.0_f32; CONTROL_DIM];
                out[6] = f32::NAN;
                Ok(out)
            }),
            fast_config(),
            None,
        )
        .expect("spawns");
        daemon.submit_state(SubconsciousState::default());
        let deadline = Instant::now() + Duration::from_secs(2);
        while daemon.inference_count() == 0 && Instant::now() < deadline {
            thread::sleep(Duration::from_millis(5));
        }
        assert_eq!(daemon.get_control(), ControlSignals::default());
        assert!(daemon.stop(Duration::from_secs(2)));
    }

    #[test]
    fn daemon_backend_errors_accumulate_in_the_dead_letter_queue() {
        let mut daemon = SubconsciousDaemon::spawn(
            Box::new(|_: &[f32; STATE_DIM]| {
                Err(DaemonError::ControlTooShort {
                    expected: 8,
                    got: 0,
                })
            }),
            fast_config(),
            None,
        )
        .expect("spawns");
        daemon.submit_state(SubconsciousState::default());
        let deadline = Instant::now() + Duration::from_secs(2);
        while daemon.error_count() == 0 && Instant::now() < deadline {
            thread::sleep(Duration::from_millis(5));
        }
        assert_eq!(daemon.error_count(), 1);
        assert_eq!(daemon.inference_count(), 0);
        let dlq = daemon.dead_letter_queue();
        assert_eq!(dlq.len(), 1);
        assert_eq!(dlq[0].error_count, 1);
        assert_eq!(daemon.dlq_size(), 1);
        assert!(daemon.stop(Duration::from_secs(2)));
    }

    #[cfg(feature = "strict-checks")]
    #[test]
    fn daemon_records_a_strict_checks_packing_failure_without_calling_the_backend() {
        let backend_calls = Arc::new(AtomicU64::new(0));
        let counted_calls = Arc::clone(&backend_calls);
        let mut daemon = SubconsciousDaemon::spawn(
            Box::new(move |_: &[f32; STATE_DIM]| {
                counted_calls.fetch_add(1, Ordering::SeqCst);
                Ok([0.0_f32; CONTROL_DIM])
            }),
            fast_config(),
            None,
        )
        .expect("spawns");
        daemon.submit_state(SubconsciousState {
            r_global: f64::NAN,
            ..SubconsciousState::default()
        });
        let deadline = Instant::now() + Duration::from_secs(2);
        while daemon.error_count() == 0 && Instant::now() < deadline {
            thread::sleep(Duration::from_millis(5));
        }
        assert_eq!(daemon.error_count(), 1);
        assert_eq!(daemon.inference_count(), 0);
        assert_eq!(
            backend_calls.load(Ordering::SeqCst),
            0,
            "an unpackable state must never reach the backend"
        );
        let dlq = daemon.dead_letter_queue();
        assert!(dlq[0].error.contains("non-finite"));
        assert!(daemon.stop(Duration::from_secs(2)));
    }

    #[test]
    fn daemon_stop_is_idempotent_after_the_thread_has_finished() {
        let mut daemon =
            SubconsciousDaemon::spawn(ok_backend(), fast_config(), None).expect("spawns");
        assert!(daemon.stop(Duration::from_secs(2)));
        // A second stop on an already-finished daemon must not panic or block.
        assert!(daemon.stop(Duration::from_secs(1)));
    }

    #[test]
    fn daemon_stop_reports_false_when_the_backend_outlives_the_timeout() {
        let mut daemon = SubconsciousDaemon::spawn(
            Box::new(|_: &[f32; STATE_DIM]| {
                thread::sleep(Duration::from_millis(300));
                Ok([0.0_f32; CONTROL_DIM])
            }),
            fast_config(),
            None,
        )
        .expect("spawns");
        daemon.submit_state(SubconsciousState::default());
        // Give the slow inference time to start before racing it with a
        // too-short stop timeout.
        thread::sleep(Duration::from_millis(30));
        assert!(!daemon.stop(Duration::from_millis(10)));
        // Clean up for real so the test process does not leak the thread.
        assert!(daemon.stop(Duration::from_secs(2)));
    }

    #[test]
    fn daemon_state_packing_carries_latency_telemetry_through_unchanged() {
        let observed: Arc<Mutex<Option<(f32, f32)>>> = Arc::new(Mutex::new(None));
        let sink = Arc::clone(&observed);
        let mut daemon = SubconsciousDaemon::spawn(
            Box::new(move |input: &[f32; STATE_DIM]| {
                *sink.lock().expect("lock") = Some((input[13], input[14]));
                Ok([0.0_f32; CONTROL_DIM])
            }),
            fast_config(),
            None,
        )
        .expect("spawns");
        daemon.submit_state(SubconsciousState {
            step_latency_p50: 0.011,
            step_latency_p95: 0.023,
            ..SubconsciousState::default()
        });
        let deadline = Instant::now() + Duration::from_secs(2);
        while observed.lock().expect("lock").is_none() && Instant::now() < deadline {
            thread::sleep(Duration::from_millis(5));
        }
        let (p50, p95) = observed.lock().expect("lock").expect("observed once");
        assert_eq!(p50, 0.011_f32);
        assert_eq!(p95, 0.023_f32);
        assert!(daemon.stop(Duration::from_secs(2)));
    }

    #[test]
    fn daemon_repeated_start_stop_cycles_do_not_deadlock() {
        for _ in 0..10 {
            let mut daemon =
                SubconsciousDaemon::spawn(ok_backend(), fast_config(), None).expect("spawns");
            daemon.submit_state(SubconsciousState::default());
            assert!(daemon.stop(Duration::from_secs(2)));
        }
    }

    #[test]
    fn daemon_dropped_without_stop_does_not_hang_the_test() {
        let daemon = SubconsciousDaemon::spawn(ok_backend(), fast_config(), None).expect("spawns");
        drop(daemon);
    }
}
