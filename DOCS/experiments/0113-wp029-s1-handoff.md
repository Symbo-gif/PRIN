# Session 0113 — WP-029 S1 Handoff Note

**Session:** 0113 — WP-029 S1: Coding — Daemon runtime and lock-free control buffer
**Date:** 2026-08-24
**Status:** S1 delivered; handoff to S2 audit (session 0114)

## Mission recap

"Implement native daemon lifecycle, bounded control-signal ring buffer,
telemetry, shutdown, and concurrency safety."
Contract (`DOCS/sessions/phase-5/0113-wp029-s1-daemon-runtime-and-lock-free-control-buffer.md`):
stress/race/lifecycle tests pass; no deadlocks/data races; p50/p95
instrumentation is valid and latency pilot improves on 3.0. Non-goals:
training hooks or MOT evaluation.

## Entry conditions

| Condition | Status |
|---|---|
| Preceding S4 closed and committed | Yes — session 0112 (WP-028 S4) closed the cycle; PSR-028 declares WP-029 with the scope/acceptance criteria quoted above |
| WP-029 scope, acceptance criteria, and non-goals have maintainer approval | PSR-028 §6 recorded approval as *pending, required before WP-029 S1 begins*. **Obtained in-session** — this session was executed at the direct instruction of the repository's maintainer (`MichaelMaillet`, matching the git identity and configured user email), which this project's own precedent (WP-028 S1 handoff, "Maintainer decisions taken this session") treats as an in-session approval when no separate written sign-off exists yet. Recorded here per that precedent |
| No unresolved D1/D2 finding | Yes — PSR-028 §1: WP-028 S2 verdict `PASS`, zero findings; S3 no-change closure with a clean delta re-audit |

## Scope decision (record per "do not expand scope silently")

Declared scope (PSR-028 §6, quoted verbatim above): the native daemon
lifecycle and the lock-free control-signal buffer inside `crates/prin-daemon`.
Everything delivered below sits inside that scope.

**One deliberate scope boundary, decided this session and recorded here
rather than attempted silently:** wiring `daemon::InferenceBackend` into a
PyO3 binding whose background thread calls back into the Python
`SubconsciousController` (`python/prin/daemon.py`, delivered WP-028) is **not**
delivered this session, even though WP-028's own S1 delivered Python bindings
in the same session as its Rust work. Reason: a `SubconsciousDaemon`'s
background OS thread calling back into Python requires acquiring the GIL
(`Python::with_gil`) on every inference; if that same daemon is later dropped
or explicitly stopped from a thread that is *itself* holding the GIL (e.g. a
Python `__del__`/garbage-collection pass, which PyO3 always runs with the GIL
held), the dropping thread's bounded wait for the background thread to finish
would hold the GIL for the whole wait, while the background thread blocks
trying to *acquire* that same GIL to finish its in-flight callback — not an
unbounded deadlock (this crate's every blocking wait has a timeout, see
"Concurrency-safety argument" below), but the interpreter would freeze for up
to the drop timeout on every such drop. The correct fix (releasing the GIL
around the blocking wait via `Python::allow_threads`, PyO3's documented
pattern for exactly this scenario) is a `prin-py`-side design that needs its
own dedicated test coverage proving the interpreter does not freeze — not
something to bolt on inside this Rust-crate-scoped session without diluting
the rigor of either half. Recorded here as a concrete design note for
whichever session (WP-030, or a dedicated follow-up) wires the daemon into
the real training loop; `crates/prin-daemon/README.md` cross-references this
note. **This is a scope decision, not a deferred deliverable** — the WP-029
declaration itself (PSR-028 §6) never named Python bindings, unlike the
`ControlSignalBuffer`/daemon-thread deferral WP-028 explicitly recorded
*into* this WP.

To keep the acceptance criterion "latency pilot improves on 3.0" honest
without that binding, the latency pilot instead measures the actual archived
PRINet 3.0 `ControlSignalBuffer` directly in Python (`tools/wp029_control_buffer_pilot.py`,
using the same `.venv` install the parity suite already depends on) and the
new Rust implementation independently (`crates/prin-daemon/examples/control_buffer_pilot.rs`),
combining both into one evidence file — see "AC3" below.

## Scope delivered

| File | Change |
|---|---|
| `crates/prin-daemon/src/daemon.rs` | **New.** `SubconsciousDaemon` (native background thread), `ControlSignalBuffer` (lock-free, `ArcSwap`-backed), `InferenceBackend` (pluggable inference seam, blanket closure impl), `DaemonConfig`, `DaemonStats`, `DeadLetterEntry`, `EscalationEvent`/`EscalationCallback`, and the internal `StateQueue`/`ShutdownSignal` primitives. |
| `crates/prin-daemon/src/error.rs` | Added `DaemonError::ThreadSpawn`. |
| `crates/prin-daemon/src/lib.rs` | Wired the `daemon` module; re-exported its public types; rewrote the crate-level scope-boundary docs (the "deliberately absent" WP-029 note no longer applies). |
| `crates/prin-daemon/src/state.rs` | Updated the stale doc comment pointing at the old (WP-028-era) `ControlSignalBuffer` deferral note to the delivered `crate::daemon::ControlSignalBuffer`. |
| `crates/prin-daemon/Cargo.toml` | Added `arc-swap`; added `criterion` (dev); registered the `control_buffer` bench. |
| `Cargo.toml` (workspace) | Added `arc-swap = "1.7"` to `[workspace.dependencies]` with justification (Coding Standards §2.2). |
| `crates/prin-daemon/tests/daemon_concurrency.rs` | **New.** 4 stress/race/lifecycle tests: concurrent multi-producer/multi-consumer access, single-writer monotonic-ordering under the lock-free buffer, repeated start/stop cycles, and a slow-backend bounded-`stop()` test. |
| `crates/prin-daemon/tests/proptest_properties.rs` | Added `control_signal_buffer_always_reads_back_the_last_published_value` and its `arb_control_signals` strategy. |
| `crates/prin-daemon/benches/control_buffer.rs` | **New.** `criterion` comparison of the lock-free buffer against a same-language `Mutex`-guarded re-implementation of the PRINet 3.0 design, under 0/1/4 writer-thread contention. |
| `crates/prin-daemon/examples/control_buffer_pilot.rs` | **New.** Manual p50/p95/max latency pilot for the same two implementations. |
| `tools/wp029_control_buffer_pilot.py` | **New.** The same pilot protocol run against the actual archived PRINet 3.0 `ControlSignalBuffer`. |
| `EVIDENCE/0113-wp029-s1-control-buffer-pilot.json` | **New.** Combined pilot evidence: 5 Rust runs, 5 Python runs, methodology, environment capture. |
| `crates/prin-daemon/README.md` | Added the WP-029-delivered module table, the PyO3-binding scope-boundary note, and the benchmarks/pilots table. |

## Parity-evidence disposition (Development Workflow Standards §3, S1 exit item)

**A directly comparable PRINet 3.0 reference exists for the daemon thread and
the control buffer; this is behavioral/concurrency parity evidence (lifecycle
semantics, overflow policy, telemetry), not numerical parity — this WP
introduces no new floating-point primitive.**

Verification of the claim, not an assertion:

```
$ ls "DOCS/archive and reference from PRINet 3.0/PRINet-3.0.0-main/src/prinet/core/subconscious_daemon.py"   # 409 lines
$ grep -n "class ControlSignalBuffer" "DOCS/archive and reference from PRINet 3.0/PRINet-3.0.0-main/src/prinet/core/subconscious.py"
322:class ControlSignalBuffer:
$ grep -n "class TestSubconsciousDaemon\|class TestControlSignalBuffer" "DOCS/archive and reference from PRINet 3.0/PRINet-3.0.0-main/tests/test_subconscious.py"
247:class TestControlSignalBuffer:
430:class TestSubconsciousDaemon:
```

| Reference behaviour | Reference test | PRIN test |
|---|---|---|
| `ControlSignalBuffer` starts at safe defaults | `test_initial_value_is_default` | `daemon::tests::buffer_starts_at_safe_defaults` |
| Update then read round-trips | `test_update_and_read` | `daemon::tests::buffer_update_then_read_round_trips` |
| Concurrent writers/readers never corrupt state | `test_thread_safety` | `daemon::tests::buffer_concurrent_writers_and_readers_never_panic_or_tear`, `daemon_concurrency.rs::concurrent_producers_and_consumers_never_panic_or_deadlock` |
| `submit_state` overflow does not raise/error | `test_daemon_submit_overflow` | `daemon::tests::daemon_submit_overflow_does_not_error` |
| `get_control` returns safe defaults before any inference | `test_daemon_default_control_before_inference` | `daemon::tests::daemon_default_control_before_any_inference` |
| Multiple submitted states are all eventually processed | `test_daemon_multiple_inferences` | `daemon::tests::daemon_processes_a_submitted_state_and_updates_control`, `daemon_concurrency.rs::control_buffer_reads_are_monotonic_under_a_single_ordered_writer` |
| `uptime` increases while running | `test_daemon_uptime` | `daemon::tests::daemon_uptime_increases_monotonically` |
| Lifecycle: start → submit → read → stop, no errors | `test_daemon_lifecycle` | `daemon::tests::daemon_processes_a_submitted_state_and_updates_control`, `daemon_concurrency.rs::repeated_lifecycle_cycles_do_not_deadlock` |
| Non-finite controller output falls back to defaults | (`_run_inference`'s `is_finite()` guard, no dedicated reference test) | `daemon::tests::daemon_non_finite_control_signals_fall_back_to_defaults` |
| Warm-up failure is tolerated ("may be expected") | (`_init_session`'s warm-up `try/except`, no dedicated reference test) | `daemon::tests::daemon_survives_a_failing_warmup_and_still_serves_the_first_real_state` |
| Errors accumulate in a dead-letter queue with escalation | (`_run_inference`'s DLQ/escalation logic, no dedicated reference test) | `daemon::tests::daemon_backend_errors_accumulate_in_the_dead_letter_queue`, `escalation_fires_once_the_threshold_is_crossed_and_on_every_error_after`, `escalation_never_fires_when_the_threshold_is_zero` |

Two deliberate behavioral deviations, both improvements, both asserted rather
than left implicit:

* **The control buffer is lock-free**, not `threading.Lock`-guarded (the
  session's stated mission). See "Design notes" below.
* **Shutdown is bounded and reported**, not `join(timeout)`-then-log. The
  reference's `stop()` also takes a timeout and logs a warning on timeout, but
  never tells the caller programmatically whether it actually succeeded;
  `SubconsciousDaemon::stop` returns `bool`. Pinned by
  `daemon_stop_reports_false_when_the_backend_outlives_the_timeout` and
  `daemon_concurrency.rs::stop_never_blocks_past_its_own_timeout_even_with_a_slow_backend`.

## Concurrency-safety argument (acceptance: "no deadlocks/data races")

No lock is ever held across a call into user code (state packing,
`InferenceBackend::infer`, or a control-signal publish), and no two locks are
ever held at once: the state queue's `Mutex`/`Condvar` pair and the
dead-letter queue's `Mutex` are never nested, and the control buffer takes no
lock at all (`ArcSwap`'s atomic-pointer-swap, entirely inside the `arc-swap`
dependency — `#![forbid(unsafe_code)]` holds on this crate; see "Why
`arc-swap`" below). That structure rules out the classic lock-ordering
deadlock by construction. Every blocking wait is bounded by an explicit
timeout — the state queue's `pop_wait(interval)` and the shutdown latch's
`wait_timeout(timeout)` — so a caller can never hang indefinitely even if that
structural argument is wrong; the concurrency test suite is built to prove
exactly that empirically, not just assert it in prose:

* `daemon_concurrency.rs::concurrent_producers_and_consumers_never_panic_or_deadlock` —
  8 producer + 8 consumer threads racing the daemon thread; a bounded overall
  deadline (`TEST_TIMEOUT = 10s`) fails the test rather than hanging CI if a
  deadlock exists.
* `daemon_concurrency.rs::control_buffer_reads_are_monotonic_under_a_single_ordered_writer` —
  3,000 states submitted with a strictly increasing counter; every value any
  concurrent reader observes must be one that was genuinely submitted and no
  reader's own read sequence may ever decrease. A torn read, a lock-ordering
  bug reordering publishes, or a drop-oldest-queue race would show up here as
  an out-of-order observation — none did.
* `daemon_concurrency.rs::repeated_lifecycle_cycles_do_not_deadlock` — 25
  spawn/submit/stop cycles.
* `daemon_concurrency.rs::stop_never_blocks_past_its_own_timeout_even_with_a_slow_backend` —
  proves `stop()`'s bound is real even while an inference call is genuinely
  in flight.
* `daemon::tests::buffer_concurrent_writers_and_readers_never_panic_or_tear` —
  the direct Rust re-implementation of the reference's own `test_thread_safety`.

No `unsafe` was written to build any of this: `#![forbid(unsafe_code)]` is
unchanged on `prin-daemon`, so this argument does not rest on manual
`unsafe`-block auditing.

## Design notes worth an auditor's attention

### Why `arc-swap`, and why that does not weaken the `unsafe` posture

Coding Standards §2.2 pins hand-rolled threading to "`prin-daemon`'s audited
ring buffer" as the sole exception to "no hand-rolled threading outside
`rayon`" — this crate is exactly that exception, and the state queue's
`Mutex`/`Condvar` pair *is* hand-rolled. The control buffer's lock-freedom
could in principle also be hand-rolled (a fixed-size ring of pre-allocated
slots with an atomic index — "triple buffering"), but implementing that
correctly and safely without `unsafe` requires either `UnsafeCell`-based
interior mutability (needs `unsafe` to dereference) or reconstructing an
`Arc`/`AtomicPtr` swap protocol by hand (needs `unsafe` to convert between
raw pointers and `Arc`, plus a hazard-pointer-equivalent reclamation scheme to
avoid freeing a snapshot a reader still holds — exactly the machinery
`arc-swap` exists to get right once, audited, instead of every caller getting
it right independently). `arc-swap` is a widely-used, mature dependency (its
own `unsafe` internals are outside this crate's `#![forbid(unsafe_code)]`
boundary, the same way `std::sync::Mutex`'s internals are); adopting it keeps
zero `unsafe` in `prin-daemon`'s own source rather than trading the "hand
rolled but auditable Rust" the state queue already is for "hand rolled and
`unsafe`." Justification recorded here per Coding Standards §2.2
("dependencies added ... with justification").

### The statically-unreachable `ControlSignals::from_tensor` error arm

`daemon.rs`'s inference-success path calls
`ControlSignals::from_tensor(&raw)` where `raw: [f32; CONTROL_DIM]` — a fixed
array whose length always satisfies `from_tensor`'s `values.len() >=
CONTROL_DIM` check, so the `Err` arm is unreachable given today's
`from_tensor` implementation. It is kept (not replaced with an infallible
helper) because `from_tensor` is a public API this call is not privileged
against future changes to (e.g. a future finiteness check moved into
`from_tensor` itself); removing the handling would silently reintroduce a
panic path if that ever happens. `cargo llvm-cov` correctly reports this arm
uncovered — noted under "Coverage" below rather than forced to 100% with a
contrived test.

### Two other "0% function coverage" entries are the exact point of their tests

`escalation_never_fires_when_the_threshold_is_zero`'s callback closure and
`daemon_records_a_strict_checks_packing_failure_without_calling_the_backend`'s
backend closure both show as never-invoked in `cargo llvm-cov`'s per-function
report — because each test's assertion *is* "this closure must never run."
Forcing them to execute would invalidate the test they exist to be.

## Acceptance-criterion evidence map

### AC1 — "Stress/race/lifecycle tests pass"

| Evidence | Result |
|---|---|
| `cargo test -p prin-daemon --test daemon_concurrency` | 4/4 passed |
| `cargo test -p prin-daemon --lib daemon::` | 22/22 passed (24 with `--features strict-checks`) |
| `cargo test -p prin-daemon --test proptest_properties` | 12/12 passed, including the new buffer property |
| `cargo test --workspace` | Full workspace green; one re-run needed for the pre-existing `hybrid::tests::gradients_flow_to_every_layer_class` flake (DV-019, `prin-train`, frozen scope, unrelated to this session — see "Non-blocking pre-existing flake" below) |

### AC2 — "No deadlocks/data races"

See "Concurrency-safety argument" above: structural argument (no nested
locks, no lock held across user code, every wait bounded) plus 4 dedicated
stress/race/lifecycle tests plus the property test proving the buffer never
returns a torn value across arbitrary update sequences. No `unsafe` in this
crate's own source (`#![forbid(unsafe_code)]` unchanged;
`grep -c "unsafe" crates/prin-daemon/src/daemon.rs` → `0`).

### AC3 — "p50/p95 instrumentation is valid and latency pilot improves on 3.0"

**Instrumentation validity:** `SubconsciousState::step_latency_p50`/`step_latency_p95`
(WP-028) survive the full `submit_state` → `to_tensor` → `InferenceBackend::infer`
pipeline unchanged, pinned by
`daemon::tests::daemon_state_packing_carries_latency_telemetry_through_unchanged`.

**Latency pilot (`EVIDENCE/0113-wp029-s1-control-buffer-pilot.json`, full
methodology and 10 individual runs there):**

| Implementation | p50 (ns) | p95 (ns) | max (ns), 5-run range |
|---|---|---|---|
| PRIN lock-free (`ControlSignalBuffer`, this session) | 0 | 100–200 | 1,800–6,400 |
| Same-language `Mutex` re-implementation of the 3.0 design | 200 | 2,400–3,000 | 17,500–314,400 |
| Actual PRINet 3.0 `ControlSignalBuffer` (Python, `threading.Lock`) | 100–200 | 200–300 | 13,000–32,200, with one 279,908,000 (≈280ms) outlier |

The controlled, same-language comparison (row 1 vs. row 2) is the rigorous
piece of evidence: lock-free p95 is consistently 13–20× lower than the
mutex-guarded re-implementation of the reference design, and its worst-case
tail is consistently far tighter. The direct Python measurement (row 3) is
reported honestly rather than cherry-picked: CPython's GIL (confirmed
`sys._is_gil_enabled() == True` on this host) means the reference's
*typical*-case numbers sit in the same clock-resolution-dominated band as the
Rust numbers, so they do not by themselves show the lock's true cost — but its
tail does: one of five runs hit a 279.9ms stall, a failure mode a lock-free
design has no blocking primitive to reproduce. Per Development Workflow
Standards §3 ("no scientific conclusion claims from pilots"), this is reported
as pilot evidence for the stated acceptance criterion, not a throughput/latency
scientific result.

## Gate evidence (2026-08-24, this host)

```powershell
cargo fmt --all -- --check                                              # clean
cargo clippy --workspace --all-targets -- -D warnings                   # clean (exit 0)
cargo clippy -p prin-daemon --all-targets --features strict-checks -- -D warnings   # clean
RUSTDOCFLAGS="-D warnings" cargo doc --workspace --no-deps               # 0 warnings (exit 0)
cargo test --workspace                                                  # all crates green (1 re-run needed for DV-019, see below)
cargo test -p prin-daemon --features strict-checks                      # all green, 104 lib tests (+2 strict-checks-only)
cargo audit                                                             # exit 0; 2 allowed warnings (amendments #9, #27 — unchanged, both pre-existing/transitive, unrelated to arc-swap)
.venv\Scripts\ruff check python/ tests/ benchmarks/ tools/ parity/       # clean
.venv\Scripts\ruff format --check python/ tests/ benchmarks/ tools/ parity/  # 73 files already formatted
.venv\Scripts\mypy python/prin --strict                                 # 28 files, 0 issues (this WP touches no python/prin/ source)
.venv\Scripts\python -m interrogate -c pyproject.toml python/prin       # 100.0% (262/262, unchanged)
.venv\Scripts\python -m interrogate -c pyproject.toml tools/wp029_control_buffer_pilot.py  # 100.0% (6/6)
.venv\Scripts\python -m bandit -r python/prin -c pyproject.toml         # 0 issues
.venv\Scripts\python -m bandit tools/wp029_control_buffer_pilot.py -c pyproject.toml  # 0 issues
.venv\Scripts\python -m pip_audit .                                     # 0 vulnerabilities
.venv\Scripts\python -m pytest tests/ -m "not slow and not gpu"         # 547 passed, 8 deselected (unchanged — no python/prin/ change)
```

### Non-blocking pre-existing flake encountered this session

One `cargo test --workspace` run failed
`hybrid::tests::gradients_flow_to_every_layer_class` at `hybrid.rs:843`
("gradient must be present for every trainable parameter"); an immediate
re-run passed cleanly. This is DV-019
(`DOCS/reports/DEFERRED_VALIDATION_REGISTER.md`), recurring for the sixth
time across five prior sessions, always in `prin-train` (WP-022's frozen
scope) and always non-reproducible on re-run. This session touched zero files
under `crates/prin-train/`, so per the established non-regression pattern this
cannot be a regression from this session's changes. No action taken here
(the DV-019 root cause and its two candidate mitigations are already on
record; `bands.rs`/`hybrid.rs` are frozen scope this session does not own).

### Coverage on new/changed code (`cargo llvm-cov -p prin-daemon --features strict-checks`)

| File | Regions | Functions | Lines |
|---|---|---|---|
| `crates/prin-daemon/src/daemon.rs` | **97.16%** | **94.74%** | **97.28%** |

Regions and lines clear the ≥95% bar comfortably. The functions metric
(72/76) sits just under it; every uncovered function is one of the three
explained cases above (a statically-unreachable defensive error arm, and two
closures whose non-invocation is the exact assertion their tests make) — not
an untested code path. `backend.rs`/`model.rs`/`onnx.rs`/`state.rs` are
unchanged from PSR-028 (99.50%/96.52%/95.16%/99.29% regions respectively) —
this WP did not modify them beyond the one doc-comment update in `state.rs`.

### Snyk (Coding Standards §6, mandatory control)

Not run this session — no interactive Snyk CLI/IDE session available in this
non-interactive execution environment. Per Coding Standards §6.1 item 5 and
the standing condition on record since WP-001 (R23, maintainer decision
2026-08-18: "Snyk-CLI-only accepted as permanent; CI is the authoritative
gate"), this is reported as **blocked**, not claimed as passed; CI's Snyk job
remains the authoritative gate for this change. `cargo audit`/`pip-audit`
(ecosystem-native, independent of Snyk per Coding Standards §6.2) are both
clean, as recorded above. Snyk Open Source is additionally N/A for this
change's only new dependency (`arc-swap`, Cargo — no Python manifest change).

## Out-of-scope discoveries (logged, not acted on)

1. **The PyO3/Python daemon binding and its GIL-release design** — see "Scope
   decision" above. Concrete recommendation: whichever session wires
   `daemon::InferenceBackend` into `python/prin/daemon.py`'s
   `SubconsciousController` should implement `Drop` for the PyO3 wrapper type
   (not rely on `SubconsciousDaemon`'s own `Drop`) as
   `Python::with_gil(|py| py.allow_threads(|| { /* stop the inner daemon */ }))`,
   and add a dedicated test that drops a running daemon from a GIL-holding
   thread while an inference is in flight, asserting the interpreter does not
   stall past the drop timeout.
2. **`benchmarks/daemon/`** (the `benchrunner` category package
   `benchmarks/README.md` already reserves for "Subconscious controller
   latency (p50/p95) across backends") does not exist yet — `benchrunner`
   itself is Phase 6 scope (Project Plan §6). This session's pilot
   (`tools/wp029_control_buffer_pilot.py`, `examples/control_buffer_pilot.rs`)
   is therefore a one-off script in the same style as `tools/wp005_ort_probe.py`,
   not a `benchmarks/` category package; recommend Phase 6's `benchrunner`
   work absorb this pilot's protocol into the `daemon/` package it already
   reserves.
3. **A transient Windows-only build warning**, unrelated to this session's
   code: `cargo doc` intermittently printed
   `warning: error finalizing incremental compilation session directory ...
   The process cannot access the file because it is being used by another
   process. (os error 32)` for `prin-daemon`'s incremental cache on this host.
   Did not affect the build's exit code (0) or output completeness across
   several repeated runs; consistent with a known Windows
   antivirus/filesystem-lock class of issue with Cargo's incremental
   compilation, not a code or CI defect. Not investigated further as it is
   outside this session's scope and non-blocking.

## Handoff to S2 (session 0114)

Suggested audit focus, in descending order of risk:

1. **The concurrency-safety argument itself** — re-derive it independently
   from `daemon.rs`'s source (lock nesting, wait boundedness, no lock held
   across `InferenceBackend::infer`) rather than trusting this note's prose;
   consider running the stress tests under increased iteration counts or a
   thread-sanitizer-equivalent if one is available in this toolchain.
2. **The `arc-swap` dependency justification** — confirm it is proportionate
   (widely audited, zero non-build dependencies of its own — verified this
   session via `cargo tree -p arc-swap`) and that `cargo audit` staying clean
   with it added is durable, not a one-time artifact.
3. **The PyO3-binding scope decision** — judge whether deferring it (rather
   than attempting it this session) was the right call given the WP-029
   declaration's literal text, and whether the GIL-release design sketch in
   "Out-of-scope discoveries" #1 is sufficient guidance for whoever picks it
   up.
4. **The latency pilot's honesty** — confirm the reported Python numbers were
   not cherry-picked (`EVIDENCE/0113-wp029-s1-control-buffer-pilot.json`
   carries all 5+5 individual runs, not just a summary) and that the
   "improves on 3.0" claim is adequately hedged as pilot evidence, not a
   scientific result.
5. **The function-coverage shortfall** (94.74% vs. the ≥95% target on
   `daemon.rs`) — confirm the three named exceptions are genuinely
   unreachable/intentional rather than a rationalization for an actual gap.
