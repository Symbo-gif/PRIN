# PRIN Audit Report — Cycle 017 / WP-017

**Date:** 2026-08-15
**Auditor:** Claude (AI pair)
**Scope:** WP-017 "Kernel architecture and CPU references" — `crates/prin-kernels/` (`backend.rs`, `buffers.rs`, `equivalence.rs`, `mean_field_rk4.rs`, `mean_field_rk4/cubecl.rs`, `lib.rs`)
**Sessions:** 0065 (S1 implementation); 0066 (S2 this audit)
**Active brief:** `DOCS/sessions/phase-3/0066-wp017-s2-kernel-architecture-and-cpu-references.md`
**Git state:** `main` @ `4e507bc` (single S1 commit; predecessor `5b3648d`)
**Verdict:** **FAIL**

---

## 1. Executive summary

| Area | Status | Notes |
|---|---|---|
| WP/session-brief scope conformance (A1) | ⚠️ | All touched files are inside the declared `crates/prin-kernels/` scope. However the declared deliverable "device/dtype dispatch" (PSR-016 §7; session 0065/0066 mission) is only partially delivered — see WP017-F3. |
| Plan/architecture conformance (A2) | ⚠️ | `order_param` consolidated to one `pub(crate)` implementation (one-algorithm-one-implementation holds). `#![deny(unsafe_code)]` / module-level `#![allow(unsafe_code)]` structure preserved per Coding Standards §2.1. But the audited-unsafe `array_arg` path has a live safety-invariant gap — WP017-F1. |
| Tests in tandem + coverage (A3) | ❌ | 46 new/changed tests added in the S1 commit range. `cargo llvm-cov -p prin-kernels --features cpu`: `buffers.rs` 91.43% lines / 71.43% functions, `equivalence.rs` 94.61% lines / 84.38% functions — both below the mandatory ≥95% gate (WP017-F2). `backend.rs` 100%, `mean_field_rk4.rs` 99.55% meet the gate. `cubecl.rs` 76.09% is consistent with the pre-existing amendment #10 kernel-body carve-out (verified below). |
| Numerical parity + invariants (A4) | ✅ | `order_param` refactor is bit-identical to the pre-refactor implementation (proptest `pool_matches_fresh_allocation_across_random_inputs`, 32 cases); `step_cpu_with_pool` is bit-identical to `step_cpu` (dedicated test + proptest). wgpu-vs-CPU equivalence passes at N=64 and N=1M (reproduced locally, DX12 backend available on this host). No new numerical primitive introduced (S1 handoff parity-evidence disposition is accurate). |
| Quality gates (A5) | ✅ | `cargo fmt`, `cargo clippy` (default, `--features cpu`, `--features wgpu`), `cargo test --workspace`, `cargo test -p prin-kernels --features cpu`/`--features wgpu`, `RUSTDOCFLAGS=-D warnings cargo doc --workspace --no-deps` all clean. Python gates (ruff, mypy, interrogate, bandit) unaffected and green (no Python touched). |
| Security (A6) | ⚠️ | `cargo audit` clean except the pre-existing allowed `paste` RUSTSEC-2024-0436 (amendment #9). Snyk Code on `crates/prin-kernels/src`: 0 issues. Snyk Open Source (npm/pip manifests, no native Cargo support in this plan): 0 issues. However, WP017-F1 is itself a memory-safety-relevant defect in audited `unsafe` code — see A6 discussion. |
| Docstring/doc coverage (A7) | ✅ | `cargo doc --no-deps` clean under `RUSTDOCFLAGS=-D warnings` (100% public rustdoc, enforced by `#![warn(missing_docs)]` + `-D warnings`). Crate-level `lib.rs` architecture section is accurate and current. |
| Repository hygiene (A8) | ⚠️ | No TODO/FIXME/stub markers. `CubeclBufferPool`'s four public accessor methods (`k1_phase`, `out_phase`, `out_amp`, `out_freq`) are dead code — never called anywhere in the crate (folded into WP017-F2). `crates/prin-kernels/README.md` still describes the WP-004 "Phase 0 status" and does not mention `backend`/`buffers`/`equivalence`; this is normally an S4 duty and is noted, not raised as a finding. |
| CI status (A9) | ✅ | No `.github/workflows/*` files touched. `cargo test -p prin-kernels --features cpu` (amendment #12) remains wired in `rust.yml`; reproduced locally, green. |
| Artefact trail (A10) | ⚠️ | S1 handoff note `DOCS/experiments/0065-wp017-s1-handoff.md` present and substantively accurate. `SESSION_REGISTER.md` row for session 0065 still reads `PLANNED` despite the session brief's own `Status: S1 DELIVERED` and the committed work (WP017-F5). The S1 commit `4e507bc` is labeled `docs(WP-017)` despite shipping new first-party source (WP017-F4). |

**Verdict rationale (summary):** WP017-F1 is a reproduced, evidence-backed D1 (a public API in the audited-`unsafe` module silently returns truncated output instead of a typed error when a preallocated GPU buffer pool is reused at a different oscillator count than it was sized for). Per Development Workflow and Audit Standards §3, any D1 finding requires a `FAIL` verdict.

---

## 2. Methodology

Commands executed and environments used (every claim above and below is backed by the command output shown here):

```powershell
# Git inspection
git log --oneline -15
git status --porcelain
git show 4e507bc --stat
git log --oneline 5b3648d..4e507bc

# Quality gates (all green)
cargo fmt --all -- --check
cargo clippy --workspace --all-targets -- -D warnings
cargo clippy -p prin-kernels --all-targets --features cpu -- -D warnings
cargo clippy -p prin-kernels --all-targets --features wgpu -- -D warnings
cargo test --workspace
cargo test -p prin-kernels --features cpu
cargo test -p prin-kernels --features wgpu -- --test-threads=1
$env:RUSTDOCFLAGS='-D warnings'; cargo doc --workspace --no-deps

# Coverage (new/changed code in prin-kernels)
cargo llvm-cov -p prin-kernels --features cpu --show-missing-lines --summary-only

# Security
cargo audit
snyk code test crates/prin-kernels/src --severity-threshold=low
snyk test --severity-threshold=low --all-projects

# Python gates (unaffected — confirms no regression from this WP)
.venv\Scripts\python -m ruff check python/ tests/ benchmarks/ tools/ parity/
.venv\Scripts\python -m mypy python/prin --strict
.venv\Scripts\python -m interrogate -c pyproject.toml python/prin
.venv\Scripts\python -m bandit -r . -c pyproject.toml
.venv\Scripts\python -m pip_audit .

# Hygiene
grep -rniE "TODO|FIXME|XXX|unimplemented!|todo!|stub" crates/prin-kernels/src
```

**Reproduction of WP017-F1** (temporary, non-committed integration test — created, run, and deleted per the S2 read-only-with-respect-to-source rule; not part of any commit):

```rust
// crates/prin-kernels/tests/audit_scratch_pool_mismatch.rs (deleted after use)
let pool = CubeclBufferPool::<CpuRuntime>::new(&client, 4);   // sized for n=4
let n = 4096usize;
let (phase, amp, freq) = (vec![0.1f32; n], vec![1.0f32; n], vec![0.0f32; n]);
let result = step_cubecl_with_pool(&client, &phase, &amp, &freq, &params, &pool);
```

```text
cargo test -p prin-kernels --features cpu --test audit_scratch_pool_mismatch -- --nocapture
NO ERROR RETURNED: pool sized for n=4 accepted a step with n=4096. out lens: p=4, a=4, f=4
thread '...' panicked at ...: step_cubecl_with_pool did not reject a pool/n size mismatch
test result: FAILED. 0 passed; 1 failed
```

Hardware/environment: Windows host, `wgpu` backend available (DX12) — `cargo test -p prin-kernels --features wgpu` ran the real `wgpu_matches_cpu_reference_at_one_million` kernel-equivalence test locally (not just the CI-default `cpu` feature), giving direct evidence the equivalence harness is operational against an actual GPU backend, not only the CubeCL CPU runtime.

---

## 3. Detailed findings

### 3.1 A1 — WP scope conformance

The S1 commit (`4e507bc`, `5b3648d..4e507bc`) touches only:

```text
DOCS/experiments/0065-wp017-s1-handoff.md
DOCS/sessions/phase-3/0065-wp017-s1-kernel-architecture-and-cpu-references.md  (status line only)
crates/prin-kernels/src/backend.rs        (new)
crates/prin-kernels/src/buffers.rs        (new)
crates/prin-kernels/src/equivalence.rs    (new)
crates/prin-kernels/src/lib.rs
crates/prin-kernels/src/mean_field_rk4.rs
crates/prin-kernels/src/mean_field_rk4/cubecl.rs
```

No file outside the declared `crates/prin-kernels/` scope was touched — no scope creep by file location. However, PSR-016 §7 and both session briefs (0065/0066) declare the WP-017 deliverable as "backend abstraction, CubeCL build path, **device/dtype dispatch**, preallocated buffers, and authoritative CPU references." The delivered code provides a static backend *priority ordering* (`backend_priority`, `auto_detect_order`) and preallocated buffers, but no operational *dispatch* mechanism and no dtype dispatch at all. This is WP017-F3 (A1 scope-declaration gap, not a scope-creep issue).

### 3.2 A2 — Plan/architecture conformance

`order_param` is now a single `pub(crate)` implementation in `mean_field_rk4.rs` (line 138), used by both the CPU reference (`mean_field_derivatives_into`) and the CubeCL host-side stage driver (`cubecl.rs:296,330,364,398` via `super::order_param`):

```
grep -rn "fn order_param" crates/prin-kernels/src   →   mean_field_rk4.rs:138 only
grep -rn "order_param_host" crates/prin-kernels/src  →   no matches (removed, as claimed)
```

This satisfies "one algorithm, one implementation" for the order parameter.

`#![deny(unsafe_code)]` at the crate level with module-scoped `#![allow(unsafe_code)]` + `#![deny(unsafe_op_in_unsafe_fn)]` in `cubecl.rs` is unchanged and matches Coding Standards §2.1 exception 1. The `array_arg` helper's `// SAFETY:` comment states: *"handle must refer to a device allocation of at least `n * size_of::<f32>()` bytes. All handles in this module come from `client.create_from_slice` or `client.empty(byte_len)`, so the invariant holds."* This reasoning is incomplete: it establishes that handles originate from a sized allocation, but never that the allocation's size is `>= n` for the `n` passed at each *call site*. `CubeclBufferPool` handles are sized once, at pool construction (`buffers.rs:172`, `byte_len = n * size_of::<f32>()`), while `step_cubecl_with_pool` (`cubecl.rs:267`) computes its own, independent `n` from the input slices and never compares it against the pool's size (which `CubeclBufferPool` does not even expose — contrast `MeanFieldRk4Buffers::capacity()`, which does). See WP017-F1.

### 3.3 A3 — Tests in tandem + coverage

Tests were added in the same commit as the code (`4e507bc`): 46 tests total under `--features wgpu` (up from 21 pre-WP-017, per amendment #10's baseline), all passing.

```text
cargo llvm-cov -p prin-kernels --features cpu --show-missing-lines --summary-only

Filename                                    Lines   Missed   Cover    Functions  Missed  Cover
backend.rs                                    57       0    100.00%      12        0    100.00%
buffers.rs                                   140      12     91.43%      14        4     71.43%
equivalence.rs                               241      13     94.61%      32        5     84.38%
mean_field_rk4.rs                            441       2     99.55%      33        0    100.00%
mean_field_rk4/cubecl.rs                     389      93     76.09%      15        3     80.00%
```

- `buffers.rs` missing lines 199–216 are exactly the bodies of `CubeclBufferPool::{k1_phase, out_phase, out_amp, out_freq}` — four `pub` accessor methods with zero call sites anywhere in the crate (`grep -rn "\.k1_phase()\|\.out_phase()\|\.out_amp()\|\.out_freq()" crates/prin-kernels` → no matches). Dead, untested public API.
- `equivalence.rs` missing lines 224–226 are `impl Default for EquivalenceHarness` (never called — only `::new()` is used by any test); lines 134/141/148 are the amplitude/frequency-mismatch `?`-propagation arms of `verify_against_reference_with_tolerance` — meaning the harness's own core behavior (detecting and reporting a genuine backend divergence) is never exercised end-to-end; existing tests only ever feed it matching backends, and `assert_allclose`'s error branch is tested in isolation, not through the harness. Lines 282/288/294 are `assert_eq!` message-format arguments, an inherent line-coverage artifact of passing assertions, not a real gap.
- `mean_field_rk4.rs` (441 lines, 2 missed) and `backend.rs` (100%) both clear the ≥95% gate.
- `cubecl.rs`: the 93 missed lines are lines 56–106 and 110–146 — exactly the bodies of the two `#[cube(launch)]` kernels (`mean_field_rk4_stage`, `mean_field_rk4_finalize`), which amendment #10 (Project Plan) already documents as non-instrumentable by `cargo-llvm-cov` on stable Rust, plus 4 additional lines (329, 363, 397 — the `?`-propagated `read_state` error arms for RK4 stages 2–4, never hit because no test drives a mid-sequence backend-read failure; 668 — an assertion message argument in the test module). Excluding the two kernel bodies (the amendment's documented carve-out), the remaining instrumentable surface is 299 lines with 3 missed ≈ 99%, still clearing the "instrumentable surrounding code ≥95%" condition amendment #10 sets. This is **not** a new deviation; it is confirmed consistent with the existing, maintainer-approved carve-out. The 4 extra uncovered lines are noted for completeness but are not large enough to warrant their own finding.

`buffers.rs` and `equivalence.rs` have no applicable amendment and both sit below the ≥95% gate — this is WP017-F2, evidence-backed and reproducible (`cargo llvm-cov -p prin-kernels --features cpu`).

### 3.4 A4 — Numerical parity + invariants

- `order_param` consolidation: `pool_matches_fresh_allocation_across_random_inputs` (proptest, 32 cases) and `step_cpu_with_pool_matches_step_cpu` confirm `step_cpu_with_pool` is bit-identical (`==`, not tolerance-based) to `step_cpu`, so the refactor preserves the pre-existing CPU reference exactly — no parity regression.
- Cross-backend equivalence: reproduced locally with `cargo test -p prin-kernels --features wgpu -- --test-threads=1` — `wgpu_matches_cpu_reference_for_small_n` (N=64) and `wgpu_matches_cpu_reference_at_one_million` (N=1,000,000) both pass at `rtol=1e-5, atol=1e-6`, using a real DX12 `wgpu` backend on this host (not only the CubeCL CPU runtime). This is stronger evidence for "equivalence harness is operational" than the S1 handoff note claims (which only cites the CI-default `--features cpu` run).
- No new numerical primitive was introduced in S1; the handoff note's parity-evidence disposition ("refactor, same algorithm/inputs/outputs, no parity evidence needed") is accurate for `order_param` and `step_cpu_with_pool`.

### 3.5 A5 — Quality gates

All clean:

```text
cargo fmt --all -- --check                                              exit 0
cargo clippy --workspace --all-targets -- -D warnings                   exit 0
cargo clippy -p prin-kernels --all-targets --features cpu -- -D warnings   exit 0
cargo clippy -p prin-kernels --all-targets --features wgpu -- -D warnings  exit 0
cargo test --workspace                                                  all crates pass (prin_kernels: 39 unit + 1 doctest, default features)
cargo test -p prin-kernels --features cpu                                40 unit + 1 doctest
cargo test -p prin-kernels --features wgpu -- --test-threads=1           46 unit + 1 doctest
RUSTDOCFLAGS='-D warnings'; cargo doc --workspace --no-deps              exit 0, 0 warnings
```

Python gates (`ruff check`, `mypy --strict`, `interrogate`, `bandit`, `pip_audit`) all pass unchanged — no Python file is in this WP's diff, confirming no regression.

`prin-kernels` has no `strict-checks` feature (unaffected by this WP; consistent with it never having had one — not a new gap).

### 3.6 A6 — Security

- `cargo audit`: 1 pre-existing allowed advisory (`paste` RUSTSEC-2024-0436, amendment #9), unchanged.
- Snyk Code, `crates/prin-kernels/src`, severity ≥ low: **0 issues**.
- Snyk Open Source, whole repo (`--all-projects`): the npm (`.kilo/package-lock.json`) and pip (`DOCS/sphinx/requirements.txt`) manifests both scan clean (0 vulnerable paths); Snyk has no native Cargo/Rust support in this plan (consistent with prior audits), so `cargo audit` remains the authoritative gate for the Rust dependency graph per Coding Standards §6.2 — and no dependency was added or changed in this WP.
- No new `#[deny(unsafe_code)]` exception was introduced; the existing `cubecl.rs` module-level `#![allow(unsafe_code)]` scope is unchanged.
- WP017-F1 is a defect *within* that already-audited unsafe scope: it does not add new unsafe code, but it invalidates part of the existing `// SAFETY:` reasoning for a call path this WP newly exposes as a documented, intended-for-reuse public API (`step_cubecl_with_pool`). Automated scanners (Snyk Code, clippy) did not and structurally cannot catch this — it requires reasoning about a cross-function invariant (pool construction size vs. call-site size) that Rust's type system does not encode. This is why the manual reproduction in §2 was necessary.

### 3.7 A7 — Docstring/doc coverage

`cargo doc --no-deps` is clean under `RUSTDOCFLAGS=-D warnings`, and `#![warn(missing_docs)]` is present at the crate level, making this a 100%-public-rustdoc build gate — satisfied. The `lib.rs` crate-level "Architecture" section accurately lists `backend`, `buffers`, `mean_field_rk4`, `equivalence`, `ops` and is consistent with the delivered modules (the stale WP-004-era "Implementation lands in Phase 3" sentence was correctly removed in this diff).

`crates/prin-kernels/README.md`, by contrast, still describes only the WP-004 "Phase 0" spike and does not mention `backend`/`buffers`/`equivalence` at all. Per Development Workflow and Audit Standards §3, README updates are an **S4** duty ("Update the README of every directory touched in S1–S3"), not an S1/S2 one, so this is not raised as a finding here — it is noted so S4 does not omit it.

### 3.8 A8 — Repository hygiene

No `TODO`/`FIXME`/`XXX`/`unimplemented!`/`todo!`/stub markers in `crates/prin-kernels/src` (`grep -rniE` clean). The dead-code accessor methods on `CubeclBufferPool` (§3.3) are a hygiene issue as much as a coverage one; they are counted once, under WP017-F2, rather than as a separate finding.

### 3.9 A9 — CI / local regressions

No `.github/workflows/*.yml` file is touched by this WP. `cargo test -p prin-kernels --features cpu` (the amendment-#12 CI step) was reproduced locally and is green. The `wgpu` step remains local-only / `gpu.yml`-gated per amendment #12 (DV-002); this WP does not change that disposition. DV-003 (device-event timing, `StepReport.wall_time_seconds` still uses host wall-clock) and DV-004 (kernel-body coverage carve-out) were both flagged in the Deferred Validation Register with "re-audit gate: Phase 3 (WP-017)" — both were explicitly re-examined in this audit (§3.3 for DV-004; DV-003's wall-clock caveat is unchanged and still correctly documented as a prototype limitation in `StepReport`'s rustdoc, and WP-017's own non-goals state "Production GPU kernels" is out of scope, so DV-003 remains legitimately open, appropriately deferred to a later Phase-3 WP such as WP-018).

### 3.10 A10 — Artefact trail

- S1 handoff note: `DOCS/experiments/0065-wp017-s1-handoff.md` — present, and its factual claims (test counts, quality-gate results, architecture decisions) were independently reproduced and found accurate in §3.3–§3.5, with one omission: it does not disclose the `buffers.rs`/`equivalence.rs` coverage shortfall (WP017-F2) or the pool/size-validation gap (WP017-F1) — both are the kind of thing S1's own exit-gate check should have caught (Development Workflow and Audit Standards §3 S1 exit criteria: "New/changed code at ≥95% coverage").
- `DOCS/sessions/phase-3/0065-...md`: self-reports `Status: S1 DELIVERED` — consistent with the committed work.
- `DOCS/sessions/SESSION_REGISTER.md`: row 110 (session 0065) still reads `PLANNED`. Compare precedent: the WP-016 audit (`DOCS/audits/016-wp016-audit.md` §3.10) found session 0061's register row already `COMPLETE` at the equivalent point in that cycle. This inconsistency is WP017-F5.
- Prior cycle audit/report: `DOCS/audits/016-wp016-audit.md` (CLEAN delta re-audit) and `DOCS/reports/016-project-state.md` are both present and consistent; no unresolved D1/D2 finding was carried into WP-017 from WP-016.
- `DOCS/reports/DEFERRED_VALIDATION_REGISTER.md` DV-012/R19 (carried `prin-kernels` CPU-reference scope from WP-016, amendment #20) is substantively addressed by this WP's "authoritative CPU references" deliverable (`step_cpu`/`step_cpu_with_pool`), but neither the S1 handoff note nor this WP's commit message cross-references DV-012/R19 explicitly. Recommend S3/S4 close the `prin-kernels` half of DV-012 with an explicit pointer to this audit; the `prin-py` half remains open (different crate, not in this WP's scope).
- Commit-message convention: `4e507bc` is typed `docs(WP-017)` — see WP017-F4.

---

## 4. Issues found

| ID | Severity | Location | Issue | Violated clause | Proposed remedy |
|---|---|---|---|---|---|
| WP017-F1 | D1 | `crates/prin-kernels/src/mean_field_rk4/cubecl.rs:155-158` (`array_arg`), `:267-461` (`step_cubecl_with_pool`); `crates/prin-kernels/src/buffers.rs:137-217` (`CubeclBufferPool`) | `step_cubecl_with_pool` never validates that the oscillator count `n` derived from its input slices matches the size the caller's `CubeclBufferPool` was constructed for. Reproduced: a pool built with `CubeclBufferPool::new(&client, 4)` accepted a step call with `n=4096` inputs and returned `Ok` with silently truncated 4-element output instead of an error — i.e. 4092 of 4096 requested results are silently dropped, with no diagnostic. On the CubeCL CPU runtime this manifests as data truncation; the same code path on `wgpu`/`cuda` backends would construct an `ArrayArg` claiming more elements than the underlying device `Handle` was allocated for, which is out-of-bounds device-buffer access reachable through a documented, `pub` reuse API — a violation of the `array_arg` `// SAFETY:` invariant it depends on. `CubeclBufferPool` also exposes no way for a caller to check its allocated size (unlike `MeanFieldRk4Buffers::capacity()`), so this cannot even be defensively guarded by the caller today. | Coding Standards §1.4 ("fail loudly, early, and typed"); §6.1 (audited-`unsafe` invariant correctness); WP-017 acceptance criterion "unsupported devices fall back safely" (a size-mismatch should never be allowed to silently corrupt output) | Add an explicit size check at the top of `step_cubecl_with_pool` (and expose a `CubeclBufferPool::capacity()`/`len()` accessor analogous to `MeanFieldRk4Buffers::capacity()`) that returns a new typed error (e.g. `MeanFieldRk4Error::PoolSizeMismatch { expected, actual }`) when `n` does not match the pool's allocated size, instead of proceeding. Add a regression test asserting this exact scenario returns `Err`, not `Ok` with truncated data. Consider the same defensive check for `MeanFieldRk4Buffers` for API symmetry, even though its `Vec`-based reuse is memory-safe (it silently reallocates rather than corrupting data, which is a lesser but related documentation-accuracy issue). |
| WP017-F2 | D2 | `crates/prin-kernels/src/buffers.rs:196-217`; `crates/prin-kernels/src/equivalence.rs:223-227, 89-151` | New/changed-code coverage gate breach: `buffers.rs` 91.43% lines / 71.43% functions; `equivalence.rs` 94.61% lines / 84.38% functions (gate: ≥95%). Root causes: (a) `CubeclBufferPool::{k1_phase, out_phase, out_amp, out_freq}` are `pub` accessor methods with zero call sites anywhere in the crate — dead, untested API; (b) `EquivalenceHarness`'s `Default` impl is never invoked by any test; (c) `verify_against_reference_with_tolerance`'s mismatch-detection `Err` arms (amplitude/frequency) are never exercised — the harness's central purpose (detecting a genuine cross-backend divergence) has no direct test, only the standalone `assert_allclose` helper does. | Testing Standards §4 ("≥95% line coverage for new/changed code"); WP-017 acceptance criterion "≥95% coverage on new/changed code" | Either remove the four unused `CubeclBufferPool` accessors (the crate already accesses the `pub(crate)` fields directly wherever needed) or add tests that call them. Add a test that calls `EquivalenceHarness::default()`. Add a test that feeds `verify_against_reference`/`_with_tolerance` a deliberately wrong `backend_fn` (e.g. one that returns a constant-offset result) and asserts the returned `Err` message names the correct backend/case/quantity. |
| WP017-F3 | D2 | `crates/prin-kernels/src/backend.rs` (whole file); `crates/prin-kernels/src/mean_field_rk4/cubecl.rs:463-515` (`try_step_wgpu`/`try_step_cpu`/`try_step_cuda`) | The WP-017 declaration (PSR-016 §7; session briefs 0065/0066 mission: "backend abstraction, CubeCL build path, **device/dtype dispatch**, preallocated buffers, and authoritative CPU references") is only partially delivered. `backend_priority`/`auto_detect_order` are pure functions returning a static `Vec<Device>`; nothing in the crate calls them (`grep -rn "backend_priority\|auto_detect_order" crates/prin-kernels/src` → matches only inside `backend.rs` itself and its own tests). There is no dispatcher that takes a `Device` (or the priority list) and actually invokes the matching `try_step_*`, catching `BackendUnavailable` and falling through to the next entry — so "unsupported devices fall back safely" is asserted by the S1 handoff note but not demonstrated end-to-end by any test; only that each individual backend probe fails safely (without panicking) in isolation. Dtype dispatch does not exist at all: `MeanFieldRk4Params`, `step_cpu`, and both CubeCL kernels are hardcoded to `f32` (`mean_field_rk4_stage::launch::<f32, R>` — the `F` type parameter is never instantiated with anything else); there is no dtype enum, no f64 path, and no selection mechanism. | Development Workflow and Audit Standards §4 A1/A2 (declared deliverables present; architecture rules); WP-017 declaration (PSR-016 §7) | Either (a) implement a `step_auto`/`dispatch_step`-style function in `backend.rs` or `mean_field_rk4.rs` that consumes `backend_priority`/`auto_detect_order` and actually tries each `try_step_*` in order with a regression test proving automatic fallback (e.g. force CUDA unavailable, verify wgpu or CPU is silently used), or narrow the WP-017 scope declaration via a plan amendment to explicitly defer end-to-end device dispatch and dtype dispatch to a named future WP (as was done for WP-016's carried scope via amendment #20 / DV-012), so the declared-vs-delivered gap is tracked rather than silently unaddressed. |
| WP017-F4 | D2 | Commit `4e507bc` | The entire S1 change set is committed as a single commit typed `docs(WP-017): S1 delivery — kernel architecture, CPU buffer pooling, and parity foundation`, but it adds three new Rust modules and substantially refactors two more (1,349 insertions / 218 deletions across `crates/prin-kernels/src/**`) — this is new first-party executable behavior, not documentation. | Coding Standards §4 (Conventional Commits: `feat:`/`fix:`/`docs:`/... must match the change) | Direct precedent WP015-F2 (D2, AMENDED): the closure disposition there recorded the mislabeling in the audit report rather than rewriting committed history. Recommend the same here — record the correct type (`feat(WP-017): ...`) in this audit's closure table; do not rewrite the already-pushed commit unless the maintainer explicitly wants history amended. |
| WP017-F5 | D4 | `DOCS/sessions/SESSION_REGISTER.md:110` | Session 0065's register row still reads status `PLANNED`, despite the session brief `DOCS/sessions/phase-3/0065-wp017-s1-kernel-architecture-and-cpu-references.md` itself stating `Status: S1 DELIVERED` and the work being committed (`4e507bc`). Precedent (`DOCS/audits/016-wp016-audit.md` §3.10): the equivalent WP-016 S1 row (session 0061) was already `COMPLETE` by the time of that cycle's S2 audit. | Development Workflow and Audit Standards §8 ("Stale or broken session-plan metadata is a governance finding") | Update `SESSION_REGISTER.md` row 110 to `COMPLETE` (S1 only; rows 111-113 for S2-S4 remain `PLANNED`/in-progress as appropriate through the remainder of this cycle). |

---

## 5. Deviation-ledger delta

New findings added to the ledger: WP017-F1 (D1), WP017-F2 (D2), WP017-F3 (D2), WP017-F4 (D2), WP017-F5 (D4).

Carried findings re-inspected: all WP-016 findings (WP016-F1 through WP016-F7) remain FIXED/AMENDED per `DOCS/audits/016-wp016-audit.md` §8-9 (CLEAN delta re-audit). WP-017's `prin-kernels` code does not reopen any WP-016 finding — `prin-sim` (where WP-016's findings live) is untouched by this WP. The two EMA-001 findings (M-F1, M-F3, both resolved per `DOCS/reports/016-project-state.md` §6) are outside `prin-kernels` and unaffected.

DV-004 (Deferred Validation Register) — re-examined per its "re-audit gate: Phase 3 (WP-017)" instruction: confirmed still valid and unchanged in substance (§3.3). DV-003 — re-examined per the same instruction: confirmed still open and appropriately deferred, no action required in this WP given its stated non-goal ("Production GPU kernels"). DV-012/R19 — the `prin-kernels` half is substantively addressed by this WP's CPU-reference deliverable; recommend S3/S4 add an explicit cross-reference closing that half of DV-012 (§3.10).

---

## 6. Verdict and required actions

**Verdict: FAIL**

WP017-F1 is a D1 finding: a reproduced, evidence-backed defect in the crate's audited-`unsafe` module where a documented, public buffer-pool-reuse API silently returns truncated results instead of a typed error when the pool's allocated size does not match the call's oscillator count. Per Development Workflow and Audit Standards §3, any D1 finding mandates a `FAIL` verdict and freezes new feature work in this WP's scope until S3 clears it.

The remainder of the delivered code is materially sound: `order_param` consolidation is correct and bit-identical to the pre-refactor path, `step_cpu`/`step_cpu_with_pool` are verified bit-identical to each other, cross-backend equivalence is genuinely operational (verified locally against a real `wgpu` DX12 backend at N=1M, not just the CubeCL CPU runtime), all quality/format/lint/doc/security gates are green, and no scope creep occurred outside the declared crate.

**Ordered S3 action list (severity order):**

1. **WP017-F1 (D1) — Buffer-pool size-validation gap:** Add a size check (and a `CubeclBufferPool` size accessor) so `step_cubecl_with_pool` returns a typed error instead of silently truncating output when the pool and the call's `n` disagree. Add a regression test reproducing the exact scenario in §2 and asserting `Err`. Re-run `cargo test -p prin-kernels --features cpu,wgpu` and reconfirm via `cargo llvm-cov` that the new error path is covered.
2. **WP017-F2 (D2) — Coverage gate:** Remove or test the four dead `CubeclBufferPool` accessors; add a `EquivalenceHarness::default()` test; add a genuine-mismatch test through `verify_against_reference`/`_with_tolerance`. Re-run `cargo llvm-cov -p prin-kernels --features cpu` and confirm `buffers.rs`/`equivalence.rs` both reach ≥95% lines.
3. **WP017-F3 (D2) — Device/dtype dispatch scope gap:** Either implement and test an actual fallback dispatcher wired to `backend_priority`, or record a plan amendment narrowing WP-017's declared scope and assigning the remainder to a named future WP (mirroring amendment #20's precedent for WP-016's carried scope).
4. **WP017-F4 (D2) — Commit-type mislabeling:** Record the correct Conventional Commits type in this audit's closure table (no history rewrite required unless the maintainer wants one).
5. **WP017-F5 (D4) — Session register staleness:** Update `SESSION_REGISTER.md` row 110 to `COMPLETE`.

A delta re-audit of the touched areas (particularly WP017-F1's fix and its regression test) is required before this cycle can proceed to S4, per Development Workflow and Audit Standards §3.

**Maintainer acknowledgment:** MichaelMaillet, 2026-08-15 — verdict `FAIL` and all five findings (WP017-F1–F5) acknowledged as reported; proceed to session 0067 (S3 remediation).

---

## 7. Closure table (appended by S3 remediation)

| ID | Resolution | Commit / amendment | Delta re-audit evidence |
|---|---|---|---|
| WP017-F1 | | | |
| WP017-F2 | | | |
| WP017-F3 | | | |
| WP017-F4 | | | |
| WP017-F5 | | | |

**Delta re-audit date:** — **Result:** —
