# Hotfix-DV019 Handoff Note

**Session:** `Hotfix-DV019` — dedicated, governed hotfix/correction session,
run outside the numbered WP-033 S1–S4 cycle (sessions 0129+), per
Development Workflow and Audit Standards §3 ("a code defect discovered here
becomes a governed hotfix/correction cycle; it is not silently repaired")
and the ad hoc-session-naming precedent (`WP-025 S3-exec`, `Exec-WP-026 S1`
— see `DOCS/sessions/SESSION_REGISTER.md` for the corresponding registration
row added by this session).
**Date:** 2026-08-26
**Git state:** `main` @ `5fdfeb0` (post-EA-006/EMA-005 remediation, pre-Phase-6)
**Mandate:** Phase 5 analytics recommendation **R33** (P0 — Critical,
`DOCS/ANALYTICS/phase-5/phase-5-recommendations.md`), itself the execution of
Phase 4's R28 and the hard, mechanically-enforced entry-condition gate EA-006
(finding E-F2) added to `DOCS/sessions/phase-6/0129-wp033-s1-unified-benchmark-runner-and-category-migration.md`
("Entry conditions"). Closes **DV-019**
(`DOCS/reports/DEFERRED_VALIDATION_REGISTER.md`).
**Status:** Delivered; DV-019 closed; WP-033 S1's entry-condition gate is now
satisfied. Does not itself constitute WP-033 S1 — that session still opens
fresh, following its own brief.

---

## 1. Mission recap

DV-019's `gradients_flow_to_every_parameter`-class test had recurred at least
six times across three modules (`bands.rs`, `hybrid.rs`, `phase_tracker.rs`)
and once more on the Python side, spanning three consecutive phases, with two
candidate mitigations recorded but never implemented:

- **(a)** pin the flaky test(s) to single-threaded execution — DV-019
  characterized this as "requires reconfiguring rayon's process-wide global
  thread pool — a broad architectural change," because `rayon::ThreadPoolBuilder::build_global()`
  can only be called once per process and would affect every concurrently
  running test in the same test binary, not just the flaky one.
- **(b)** strengthen the fixture (different seed/init range) so the
  affected gradient is robustly bounded away from zero.

R33 directed opening the dedicated hotfix/correction session, evaluating
both options against the evidence in DV-019, and implementing the
lower-risk one. This session did that — and, in the process of building the
confirmation evidence R33's own text calls for ("10+ consecutive
`cargo test -p prin-train` runs... with zero recurrence"), obtained a
**local, reliable reproduction of the flake for the first time** (prior
sessions only ever observed it in already-completed CI/local runs, never
reproduced it on demand), which substantially corrected the root-cause
diagnosis both options were based on. §2 covers that finding; §3 covers the
fix actually implemented, which is a precise, bounded refinement of the
diagnosis behind option (a) rather than either option as originally stated.

## 2. Root-cause correction (new evidence this session)

### 2.1 Reproduction

Filtering to just the affected gradient tests (`cargo test -p prin-train
--lib gradients_flow`) never failed across 20+ runs — matching every prior
session's experience that the tests are "fine in isolation." Running the
**full** `prin-train` lib suite (375 tests) at default (multi-threaded) test
concurrency, however, reliably reproduced the flake: **9 of 12 consecutive
runs failed** before any fix, with `-- --test-threads=1` clean across every
run of the same command. This is the first session to obtain on-demand
reproduction of DV-019, and it immediately falsifies the "isolated re-run
always passes, so it must be rare" framing every prior session's evidence
was limited to — it is not rare, it is concurrency-dependent, and the prior
sessions' own re-run-until-clean verification protocol was (unknowingly)
selecting for the single-threaded case every time.

### 2.2 The failures were not confined to the three named tests

Across repeated reproduction runs, the panicking test rotated across
locations DV-019 had never recorded:
`bands::tests::gradient_matches_central_finite_difference` (a numerical
finite-difference comparison, not a gradient-presence assertion) and
`trainer::tests::phase_tracker_training_runs_and_produces_valid_metrics`
(production training-loop code, called transitively, with no gradient
assertion of its own) both failed in the same reproduction batch that also
hit `bands::tests::gradients_flow_to_every_parameter` and
`phase_tracker::tests::gradients_flow_to_encoder_and_dynamics_parameters`.
One occurrence panicked **inside `burn-autodiff` itself**
(`runtime/server.rs:30`, `"Node should have a step registered, did you
forget to call Tensor::register_grad..."`) rather than in any PRIN
assertion. A defect whose symptom rotates across unrelated test names,
including one panic inside the third-party library's own internals, is not
consistent with "a specific test's fixture produces a knife-edge gradient
value" — it is consistent with shared, cross-test state corruption.

### 2.3 Confirmed mechanism

Reading `burn-autodiff` 0.16.1's own source
(`~/.cargo/registry/.../burn-autodiff-0.16.1/src/runtime/{server,mutex}.rs`):
the default (non-`async`) runtime backs **every** `Autodiff<B>` graph in the
process with **one shared global instance**,
`static SERVER: spin::Mutex<Option<AutodiffServer>>`
(`runtime/mutex.rs`), keyed by `NodeID` across a single
`steps: HashMap<NodeID, StepBoxed>`. Individual `register`/`backward` calls
are mutex-serialized (no data race on the map itself), but the server has no
concept of which nodes belong to which independent computation graph — its
`backward()` method runs a reference-counted memory-management sweep
(`free_unavailable_nodes`) after every call, over the **entire shared map**.
Rust's default test harness runs each `#[test]` on its own OS thread
(`--test-threads` defaults to the core count — 16 on this host); when two
unrelated tests build independent `Autodiff` graphs concurrently, one test's
`backward()` call can trigger a sweep that frees nodes still in-flight in
the other test's not-yet-backpropagated graph, producing exactly the
observed symptom (`.grad()` returns `None` instead of `Some(≈0.0)`, or the
library's own bookkeeping panics outright).

This is a genuine, independently-confirmable thread-safety limitation of
`burn-autodiff`'s default runtime under Rust's default parallel test
harness — not a "rayon summation-order artifact in a specific test's
fixture," the leading hypothesis DV-019 carried into this session. That
hypothesis was itself a reasonable, evidence-consistent step from every
prior session's information (none of which had a reliable local
reproduction to test it against), and this correction does not fault those
sessions' diagnosis discipline — it reflects genuinely new evidence this
session was able to gather because it had, for the first time, a fast
(~4s), reliable (~75%) local repro loop to iterate against.

Independent corroboration already existed in this crate before this
session, in a different context:
`crates/prin-train/src/support.rs`'s `seeded_linear`/`seeded_gru` doc
comments already document that `burn::nn::LinearConfig::init`/
`GruConfig::init` draw from **another** Burn-owned global (`Backend::seed`,
a `static Mutex` inside `burn-ndarray`), and that two `Config::init` calls
racing across parallel test threads can observe each other's draws — the
reason this crate's `Config::init` paths were already written to bypass
Burn's built-in initializers entirely in favor of this project's own
`Seed`. DV-019 is the same general class of defect (Burn ecosystem global
mutable state, unscoped per test-thread) in a different subsystem
(`burn-autodiff`'s graph server, which has no project-level bypass — every
`Autodiff<B>` tensor operation goes through it).

### 2.4 Why "reconfigure `burn-autodiff`'s runtime" is out of scope

`burn-autodiff` ships an alternate `async` feature (`runtime/mspc.rs`) that
routes every `register`/`backward` call through one dedicated background
thread via an `mpsc` channel instead of a `spin::Mutex`. This was
considered and rejected for this session: (1) it is a Cargo *feature* on a
shared workspace dependency, so enabling it would affect every crate that
depends on `burn-autodiff`, a project-wide dependency-configuration change
far outside a bounded hotfix session's scope — the same "broad architectural
change" concern DV-019 already raised against option (a); (2) its
`ChannelClient` still owns exactly **one** global `AutodiffServer` instance
(`static INSTANCE: spin::Lazy<ChannelClient>`) with the identical
whole-map `free_unavailable_nodes` sweep — serializing *access* to the
server does not by itself prove the memory-management sweep is safe when
multiple independent graphs are interleaved within it, only that two
threads cannot corrupt the `HashMap` via a data race. It was not evaluated
further because a project-wide dependency-feature change is disproportionate
to what a bounded, `prin-train`-local hotfix requires when a
test-binary-local fix (§3) fully resolves the confirmed symptom.

## 3. Fix implemented

### 3.1 Concurrency fix (the decisive fix)

Added a shared, test-only serialization guard,
`crate::support::autodiff_test_guard()` (`crates/prin-train/src/support.rs`,
`#[cfg(test)]`-gated — it does not exist in the compiled library, so it
cannot affect `crates/prin-py`'s Python bindings or any release artifact):
a `static std::sync::Mutex<()>`, poison-tolerant (`unwrap_or_else(
PoisonError::into_inner)`, since a prior test's panic while holding a
plain synchronization mutex must not permanently deadlock every later
test).

Every `prin-train` unit test that builds a `TestAutodiffBackend`
(`Autodiff<NdArray<f64>>`) graph — directly, or indirectly through a helper
function or a production function like `trainer.rs`'s training loop —
acquires this guard as the first statement in its body, for the duration of
its forward/backward/gradient-inspection sequence. This was enumerated
programmatically (not by memory or a partial grep): every `#[test]` function
in `prin-train` whose body, or whose call graph one level through same-file
helper functions, mentions `Autodiff`/`AutodiffBackend`. **42 test
functions across 14 files** were identified and guarded:
`ablation.rs` (3), `activations.rs` (2), `adversarial.rs` (14),
`allocation.rs` (1), `attention.rs` (2), `bands.rs` (2), `energy.rs` (1),
`hybrid.rs` (1), `inhibition.rs` (2), `layers.rs` (2), `losses.rs` (1),
`phase_tracker.rs` (1), `slot_attention.rs` (1), `trainer.rs` (9).

This deliberately guards more than the three modules DV-019/R28/R33's own
text named (`bands.rs`, `hybrid.rs`, `phase_tracker.rs`) — §2.2's
reproduction evidence showed the underlying defect is not confined to
those three; a fix scoped only to the three originally-suspected files
would have left the crate's other 39 autodiff-graph tests still exposed to
the identical cross-test corruption, unable to satisfy the "zero
recurrence" confirmation bar R33 itself sets. It is, conversely,
deliberately *not* every test in the crate: the ~330 non-autodiff tests
(config validation, shape checks, `TestBackend`-only numerics, etc.) never
touch the shared `AutodiffServer` and are unaffected by this defect, so
guarding them would add lock contention for zero benefit.

This is best understood as a bounded, precisely-targeted refinement of
option (a)'s underlying intent ("pin the flaky test(s) to single-threaded
execution") rather than either option as originally stated: it serializes
exactly the operation now confirmed to race (concurrent `burn-autodiff`
graph construction/backward across OS threads within this one test
binary), without reconfiguring rayon's process-wide thread pool (which
governs `NdArray`'s internal compute parallelism, a different mechanism
than `burn-autodiff`'s graph-server sharing) and without affecting any
other crate's tests (the guard is a `prin-train`-private static; each
crate's test binary is a separate OS process with its own copy).

### 3.2 Fixture hardening (defense in depth, not the decisive fix)

Before finding the true root cause (§2.3), this session first attempted
option (b) directly, following DV-019's own framing:

- `bands.rs::gradients_flow_to_every_parameter` — widened the batch from 2
  to 4 independent seeded draws and extended integration from 3 to 6 steps,
  reducing the risk that `w_gamma`'s off-diagonal gradient entries (the
  only nonzero path for that parameter, per the test's own existing
  comment) sum to a value close to cancellation. Confirmed by direct
  instrumentation: off-diagonal magnitudes moved from
  ~0.002–0.06 to ~0.009–0.19.
- `hybrid.rs::gradients_flow_to_every_layer_class` and
  `phase_tracker.rs::gradients_flow_to_encoder_and_dynamics_parameters` —
  replaced a fully-symmetric input fixture (`Tensor::ones([2, N]) * c`,
  every batch row and every feature identical) with a seeded-distinct
  draw (`crate::support::seeded_uniform`, matching the same fixture-design
  principle `bands.rs`'s own phase/amplitude fixture already used), which
  removes several structurally-degenerate Jacobian paths (symmetric
  batch rows, identical `sin(phase_i − phase_i)` cross-terms) that a fully
  symmetric input creates by construction.

**Direct evidence that this alone does not fix DV-019:** with only this
fixture hardening applied (§3.1's mutex not yet added), the full-suite
reproduction in §2.1 still failed in most runs — the panicking parameter
and location continued to rotate, including tests §3.2 never touched. This
fixture hardening is kept because it is independently good test design
(removing a real structural-degeneracy risk that would matter even in a
single-threaded world, and one `bands.rs` itself already avoids for its own
phase/amplitude fixture), but it is not what closes DV-019 — §3.1 is.

### 3.3 Python-side item (DV-019's separately-tracked, unconfirmed instance)

DV-019 also records one Python-side recurrence
(`tests/test_train_bridge_slot_attention.py::TestTemporalSlotAttentionMOT::test_process_frame_gradcheck_with_prev_slots`,
WP-030 S4), explicitly flagged in the register as "a new, unconfirmed
possible instance of the same general class... a future investigating
session should confirm or rule out the shared-cause hypothesis before
treating it as the same defect" — and the WP-033 S1 entry-condition gate
this session closes names only the three Rust modules. This session did not
modify that test or any Python/PyTorch code (the mechanism in §2.3 is
specific to `burn-autodiff`'s Rust-side graph server and has no PyTorch
analogue — `torch.autograd`'s own graph is per-call, not a shared
process-global singleton). Per R33's own confirmation-evidence text ("plus
the Python-side test also clean"), it was re-run **15 consecutive times in
isolation** (all clean) and as part of the full fast Python suite (**555
passed, 8 deselected** — matching the established baseline) once. This
confirms the test is currently clean; it does not confirm or rule out the
shared-cause hypothesis DV-019 itself says still needs investigation. That
open sub-question is unaffected by this session's closure of DV-019's
Rust-side pattern and remains available for a future session if the
Python-side test recurs.

## 4. Verification evidence

```powershell
cargo fmt --all -- --check                                              # clean
cargo clippy -p prin-train --all-targets -- -D warnings                 # clean
cargo clippy --workspace --all-targets -- -D warnings                   # clean
RUSTDOCFLAGS="-D warnings" cargo doc -p prin-train --no-deps             # 0 warnings
cargo audit                                                              # exit 0; 2 pre-accepted warnings (DV-008, DV-017), unchanged — no dependency change
snyk code test crates/prin-train                                        # 0 issues
```

Reproduction / regression confirmation (all post-fix):

| Command | Runs | Result |
|---|---|---|
| `cargo test -p prin-train --lib` (default concurrency) | 35 (20 + 15, across two batches spanning a doc-comment fix in between) | **35/35 clean**, 375 passed each run |
| `cargo test -p prin-train --lib` × 10, launched concurrently as separate OS processes (the exact configuration that reproduced the pre-fix flake in §2.1) | 10 | **10/10 clean** |
| `cargo test --workspace` | 16 (6 + 10, across two batches) | **16/16 clean** |
| `.venv\Scripts\python.exe -m pytest tests/test_train_bridge_slot_attention.py::TestTemporalSlotAttentionMOT::test_process_frame_gradcheck_with_prev_slots` | 15 | **15/15 clean** |
| `.venv\Scripts\python.exe -m pytest tests/ -m "not slow and not gpu"` | 1 | 555 passed, 8 deselected (baseline-consistent) |

This is a **51-run** clean streak for the `prin-train` lib suite alone
(35 sequential + 16 workspace) at default concurrency, plus the 10-process
contention scenario that reliably reproduced the defect before the fix —
substantially exceeding R33's own confirmation bar ("10+ consecutive
`cargo test -p prin-train` runs at default thread count with zero
recurrence").

One additional, unexplained `cargo test --workspace` failure was observed
during an earlier stress-testing batch (before the final `cargo fmt`
pass), with no captured panic/failure detail (the capture script did not
save output on that run). It was not reproduced across the subsequent 16
consecutive `cargo test --workspace` runs recorded above. Given the
`prin-train` lib suite's own 51-run clean streak isolates this crate's
component of DV-019 conclusively, and the one anomaly did not recur, it is
recorded here for transparency rather than treated as a residual defect;
if a similar anomaly recurs in a future session, it should be treated as a
**new**, separately-diagnosed item rather than folded back into DV-019.

## 5. Acceptance criteria → evidence map

| Criterion (R33) | Verdict | Evidence |
|---|---|---|
| Dedicated, governed hotfix/correction session opened per Development Workflow and Audit Standards §7 | **GREEN** | This session, `Hotfix-DV019`, registered in `DOCS/sessions/SESSION_REGISTER.md` |
| Both mitigation options evaluated against the evidence in DV-019 | **GREEN** | §2–§3: option (b) attempted first and shown insufficient by direct reproduction; option (a) re-evaluated in light of the corrected root cause and implemented as a bounded, test-scoped refinement (§3.1) rather than the rejected broad rayon-global-pool form |
| Lower-risk mitigation implemented | **GREEN** | §3.1 — `prin-train`-private, `#[cfg(test)]`-gated static mutex; zero effect on the compiled library, zero effect on other crates, ~0.2s added to a ~4.2s suite |
| DV-019 closed with mitigation implemented and verified | **GREEN** | §4; `DEFERRED_VALIDATION_REGISTER.md` DV-019 updated to `CLOSED` this session |
| 10+ consecutive `cargo test -p prin-train` runs at default thread count, zero recurrence | **GREEN** | 51 total (§4), including the exact 10-concurrent-process scenario that reproduced the pre-fix defect |
| Python-side test also clean | **GREEN** | 15/15 isolated + full fast suite (§3.3) |
| WP-033 S1's entry-condition gate satisfied | **GREEN** | `DOCS/sessions/phase-6/0129-wp033-s1-unified-benchmark-runner-and-category-migration.md` updated this session |

## 6. Out-of-scope items (recorded, not silently dropped)

- **R34** (mechanical enforcement for DV-register preconditions),
  **R35** (DV-004 Phase 6 scoping decision), **R36** (vendoring
  `math-audit-mcp`) — not in this session's mandate (R33/DV-019 only, per
  the session's own instructions); untouched.
- **Python-side shared-cause hypothesis** (§3.3) — confirmed clean this
  session, root-cause confirmation/ruling-out still open for a future
  session if it recurs.
- **`burn-autodiff` `async`-feature evaluation** (§2.4) — considered and
  explicitly declined as disproportionate to a bounded hotfix session;
  available for a future dedicated dependency-configuration session if the
  project ever needs its other properties (e.g. off-thread autodiff
  scheduling) for a different reason.
- **The one unexplained `cargo test --workspace` anomaly** (§4, final
  paragraph) — not reproduced; flagged for separate diagnosis only if it
  recurs.
