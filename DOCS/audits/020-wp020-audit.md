
# PRIN Audit Report — Cycle 020 / WP-020

**Date:** 2026-08-16
**Auditor:** Qwen Code (AI pair)
**Scope:** WP-020 "Fused discrete step and reductions" — `crates/prin-kernels/` (`discrete_step.rs`, `discrete_step/cubecl.rs`, `mean_field_rk4.rs` (visibility promotions only), `lib.rs`, `benches/discrete_step_bench.rs`, `Cargo.toml`)
**Sessions:** 0077 (S1 implementation); 0078 (S2 this audit)
**Active brief:** `DOCS/sessions/phase-3/0078-wp020-s2-fused-discrete-step-and-reductions.md`
**Git state:** `main` @ `9af9ce0`
**Verdict:** **PASS**

---

## 1. Executive summary

| Area | Status | Notes |
|---|---|---|
| WP/session-brief scope conformance (A1) | ✅ | All declared scope present (`git diff 71654e4..9af9ce0 --stat`: 12 files); nothing undeclared shipped. Non-goal (autograd bridges / trainable model stack) untouched. |
| Plan/architecture conformance (A2) | ✅ | `prin-kernels` layering preserved; `mean_field_rk4` helpers promoted to `pub(crate)` and reused rather than re-derived (Coding Standards §1, "one algorithm, one implementation"); no Python numerics; f64-accumulated CPU reference and f64-finished device reductions. |
| Tests in tandem + coverage (A3) | ✅ | 29 new tests (15 CPU unit/error-path + 2 proptests + 12 CubeCL) in the single S1 commit. `discrete_step.rs` **97.65%** lines (≥95% gate met). `discrete_step/cubecl.rs` raw **79.32%** (`wgpu,cpu`) — below 95% for the same accepted DV-004 reason as all prior kernel-dispatch files; shortfall against the `mean_field_rk4/cubecl.rs` baseline (80.76%) is fully explained by the higher kernel-body-to-total-code ratio (4 vs. 3), not a coverage regression in reachable code. |
| Numerical parity + invariants (A4) | ✅ | wgpu-vs-CPU equivalence at small N (`[8,16,32]`), non-block-aligned per-band sizes (`[300,777,513]`), and large N (`[2048,16384,65536]`, N=84,992) all pass at `rtol=1e-5, atol=1e-6`. CubeCL-CPU multi-block equivalence (`[600,600,600]`, 3 blocks) and 5-repeat determinism regression test pass. Proptest invariant suites (output invariants, zero-coupling free-run) green. CUDA: compiles cleanly; no runner available (DV-002, pre-existing). |
| Quality gates (A5) | ✅ | `cargo fmt`, clippy (default, cpu, wgpu+cpu — all `-D warnings`), rustdoc (workspace + feature combinations), ruff check/format, mypy --strict, bandit — all independently re-run clean. |
| Security (A6) | ✅ | No new unapproved `unsafe`; `discrete_step/cubecl.rs` confines `unsafe` to `ArrayArg::from_raw_parts` with `// SAFETY:` justifications, matching the audited pattern. `cargo audit`: 1 pre-existing allowed `paste` advisory (DV-008), no new. `bandit`: 0 issues. No dependency/manifest changes (only a `[[bench]]` target added). |
| Docstring/doc coverage (A7) | ✅ | `interrogate` 100.0% (106/106, no Python files touched). Rustdoc: 0 warnings under `-D warnings` for workspace and all feature combinations. All new public items documented; module-level docs explain algorithm, state layout, launch sequence, and reduction design. |
| Repository hygiene (A8) | ✅ | No TODO/FIXME/stub markers in new code. Git tree clean. Session register and brief status correctly updated. S1 handoff note is accurate and evidence-backed. |
| CI status (A9) | ✅ | No `.github/workflows/*` files touched. Local reproduction of every test/coverage/quality command matches S1 handoff figures. |
| Artefact trail (A10) | ✅ | Prior audit (`019-wp019-audit.md`, PASS-WITH-FINDINGS → FIXED) and PSR-019 consistent with this WP's declared scope. S1 handoff note (`DOCS/experiments/0077-wp020-s1-handoff.md`) present with full acceptance-criterion evidence map, architecture-decision rationale, out-of-scope discoveries, and parity-evidence disposition. |

## 2. Methodology

All commands executed on Windows (local dev machine, wgpu/DX12 backend), independently, without reference to the S1 handoff note's own command transcripts except to compare final figures. Git diff range: `71654e4` (WP-019 S4, predecessor baseline) → `9af9ce0` (WP-020 S1).

```powershell
# A1 — scope
git diff 71654e4..9af9ce0 --stat                                          # 12 files, matches declared scope

# A5 — Quality gates
cargo fmt --all -- --check                                                # exit 0, clean
cargo clippy --workspace --all-targets -- -D warnings                     # exit 0, clean
cargo build -p prin-kernels --features cuda --lib                         # exit 0, clean (compile-only, DV-002)
set RUSTDOCFLAGS=-D warnings && cargo doc --workspace --no-deps           # exit 0, 0 warnings
.venv\Scripts\python -m ruff check python/ tests/ benchmarks/ tools/ parity/     # All checks passed!
.venv\Scripts\python -m ruff format --check python/ tests/ benchmarks/ tools/ parity/  # 50 files already formatted
.venv\Scripts\python -m mypy python/prin --strict                         # Success: no issues found in 18 source files

# A3 — Tests
cargo test --workspace                                                    # all crates green, 0 failed
cargo test -p prin-kernels --features cpu                                 # 121 unit + 1 doctest passed
cargo test -p prin-kernels --features wgpu,cpu                            # 149 unit + 1 doctest passed

# A3 — Coverage
cargo llvm-cov -p prin-kernels --features wgpu,cpu                        # per-file figures captured

# A6 — Security
cargo audit                                                                # 1 allowed warning (paste RUSTSEC-2024-0436)
.venv\Scripts\python -m bandit -r . -c pyproject.toml                     # No issues identified

# A7 — Documentation
.venv\Scripts\python -m interrogate -c pyproject.toml python/prin         # 100.0% (106/106) PASSED

# A4 — Python tests (unaffected; re-run for non-regression)
.venv\Scripts\python -m pytest tests/ -m "not slow and not gpu" --basetemp=.pytest_basetemp  # 306 passed, 6 deselected

# A8 — Hygiene
grep -rn "TODO|FIXME|HACK|XXX|STUB" crates/prin-kernels/src/discrete_step.rs crates/prin-kernels/src/discrete_step/   # 0 matches
```

## 3. Detailed findings

### 3.1 A1 — WP scope conformance

**Declared scope** (session 0077/0078 brief, PSR-019 §6): `crates/prin-kernels/` — fused three-band discrete-time step kernel combining phase advance, PAC gating, and Stuart–Landau amplitude dynamics; reusable hierarchical order-parameter reductions. Non-goals: autograd bridges, trainable model stack, Python bindings.

**Delivered** (`git diff 71654e4..9af9ce0 --stat`):

| File | Change | In scope? |
|---|---|---|
| `crates/prin-kernels/src/discrete_step.rs` | **New.** `discrete_step_cpu` — CPU reference (numerical authority) for the fused three-band (delta/theta/gamma) discrete-time stepper. 15 unit/error-path tests + 2 proptest suites. | ✅ |
| `crates/prin-kernels/src/discrete_step/cubecl.rs` | **New.** Four `#[cube(launch)]` kernels (`complex_order_reduce`, `real_sum_reduce`, `band_euler_step`, `pac_gate`) + host dispatch (`discrete_step_cubecl`, `try_*_wgpu`/`_cpu`/`_cuda`, `discrete_step_auto`). 12 tests (7 wgpu + 5 CubeCL-CPU). | ✅ |
| `crates/prin-kernels/src/mean_field_rk4.rs` | `wrap_phase`, `clamp_amp`, `mean_field_derivatives_into` promoted from private to `pub(crate)` with doc comments explaining the reuse. No behavior change. | ✅ |
| `crates/prin-kernels/src/lib.rs` | `pub mod discrete_step;` + module-doc entries. | ✅ |
| `crates/prin-kernels/benches/discrete_step_bench.rs` | **New** — criterion benchmark comparing fused vs. unfused composition. | ✅ |
| `crates/prin-kernels/Cargo.toml` | `[[bench]]` target only; no dependency changes. | ✅ |
| `DOCS/experiments/0077-wp020-s1-handoff.md` | S1 handoff note with acceptance-criterion evidence map. | ✅ |
| `DOCS/reports/019-project-state.md` | Minor update (session register reference). | ✅ |
| `DOCS/sessions/SESSION_REGISTER.md` | Session 0077 → COMPLETE. | ✅ |
| `DOCS/sessions/phase-3/0077-...md` | Status field update. | ✅ |
| `DOCS/sessions/phase-3/README.md` | Session brief listing update. | ✅ |
| `DOCS/experiments/README.md` | Handoff note listing update. | ✅ |

No undeclared work shipped. The non-goal areas (autograd bridges, trainable model stack, Python bindings) are untouched — confirmed by `grep` for `autograd`, `trainable`, `PyDiscreteStep` in the diff (0 matches).

### 3.2 A2 — Plan/architecture conformance

- **Crate layering:** All new code lives in `prin-kernels` (Plan §6). No new crate dependencies. `prin-dynamics` referenced only in doc comments (design-rationale citations), not as a new `use` dependency.
- **One algorithm, one implementation (Coding Standards §1):** `discrete_step_cpu` reuses `mean_field_rk4::mean_field_derivatives_into` for the per-band Kuramoto/Stuart–Landau derivative evaluation rather than re-deriving the formula. `wrap_phase` and `clamp_amp` are similarly reused. The three functions were promoted from private to `pub(crate)` with doc comments explaining the reuse — a clean, minimal visibility change with no behavior modification.
- **Reusable hierarchical reductions:** `complex_order_reduce` and `real_sum_reduce` are separate, `discrete_step`-local implementations (each called multiple times across the fused path) rather than refactoring the WP-018/WP-019 kernels into a shared module. This matches WP-019's own precedent of re-implementing rather than reaching into prior WP kernel internals, and is explicitly within the declared scope ("reusable hierarchical order-parameter reductions").
- **No Python numerics:** No Python files touched.
- **f64 accumulation:** `discrete_step_cpu::mean_f64` accumulates in `f64` before downcasting (Coding Standards §2.2). The CubeCL device reductions (`complex_order_reduce_device`, `real_mean_reduce_device`) finish with `f64` host accumulators, matching exactly.
- **Explicit state/seeding:** No RNG introduced; deterministic data flow preserved.

### 3.3 A3 — Tests in tandem + coverage

**New tests in the S1 commit** (`9af9ce0`, single commit — trivially in-tandem): 29 tests total:
- 15 CPU unit/error-path tests in `discrete_step::tests` (shape preservation, PAC identity, free-run, 8 error-path rejections, PAC modulation)
- 2 proptest suites in `discrete_step::proptests` (output invariants, zero-coupling free-run)
- 7 wgpu tests in `discrete_step::cubecl::tests` (equivalence at 3 shapes, 3 error paths, backend-unavailable)
- 5 CubeCL-CPU tests in `discrete_step::cubecl::tests_cpu` (multi-block equivalence, determinism, auto-fallback, population check)

**Coverage** (`cargo llvm-cov -p prin-kernels --features wgpu,cpu`, independently re-run):

| File | Lines | Missed | Cover% | Gate |
|---|---|---|---|---|
| `discrete_step.rs` | 468 | 11 | **97.65%** | ≥95% ✅ |
| `discrete_step/cubecl.rs` (raw) | 590 | 122 | **79.32%** | See below |

`discrete_step.rs`'s 97.65% exceeds the ≥95% gate. The 11 missed lines are `thiserror`-generated `Display` code for error variants whose `format_args` paths are not fully exercised by `matches!` assertions — a standard Rust pattern, not a logic gap.

`discrete_step/cubecl.rs`'s raw 79.32% is below 95% for the same accepted reason established at WP-017/WP-018/WP-019 (DV-004, plan amendment #10): the four `#[cube(launch)]` kernel bodies (`complex_order_reduce`, `real_sum_reduce`, `band_euler_step`, `pac_gate`) are non-instrumentable by `cargo-llvm-cov` on stable Rust; correctness is verified by the kernel-equivalence tests (§3.4). The 1.44-point shortfall against the `mean_field_rk4/cubecl.rs` baseline (80.76%, re-measured this session, exact match to PSR-018/PSR-019) is fully explained by the higher kernel-body-to-total-code ratio (4 kernel bodies in 590 lines vs. 3 in 764 lines) — not a coverage regression in reachable, instrumentable code. Outside the four kernel bodies, the only other missed lines are:
- The `ProfilingFailed` error-mapping closure (untestable without mocking `ComputeClient::profile` — the identical gap exists in `mean_field_rk4::cubecl`)
- `discrete_step_auto`'s `cpu`/native-fallback branches (unreached under `wgpu,cpu` because `try_discrete_step_wgpu` succeeds first — the identical pattern `mean_field_rk4::cubecl::step_auto` shows in the same run)

Both are structurally identical to pre-existing accepted gaps. No weakened tests or tolerance drift detected. All kernel-equivalence tests use `rtol=1e-5, atol=1e-6` (Testing Standards §3).

### 3.4 A4 — Numerical parity + invariants

**Kernel equivalence (GPU/CubeCL-CPU vs. CPU reference), independently re-run:**

| Test | Shape | Backend | Tolerance | Result |
|---|---|---|---|---|
| `wgpu_matches_cpu_reference_for_small_n` | `[8, 16, 32]` | wgpu (DX12) | `rtol=1e-5, atol=1e-6` | PASS |
| `wgpu_matches_cpu_reference_for_non_block_aligned_bands` | `[300, 777, 513]` | wgpu (DX12) | `rtol=1e-5, atol=1e-6` | PASS |
| `wgpu_matches_cpu_reference_at_large_n` | `[2048, 16384, 65536]` (N=84,992) | wgpu (DX12) | `rtol=1e-5, atol=1e-6` | PASS |
| `cpu_backend_matches_cpu_reference_multi_block` | `[600, 600, 600]` (3 blocks) | CubeCL-CPU | `rtol=1e-5, atol=1e-6` | PASS |
| `cpu_backend_is_deterministic_across_repeated_calls` | `[300, 400, 500]` × 5 repeats | CubeCL-CPU | exact (bit-identical) | PASS |
| `discrete_step_auto_falls_back_to_available_backend` | `[4, 4, 4]` | auto (wgpu) | `rtol=1e-5, atol=1e-6` | PASS |

**Proptest invariant suites, independently re-run:**

| Test | Property | Result |
|---|---|---|
| `output_invariants_always_hold` | Phase ∈ [0, 2π), amplitude ∈ [amp_min, amp_max], all finite | PASS |
| `zero_coupling_all_bands_is_free_run` | With K=0, decay=0, γ=0, m=0: phase = wrap(φ + dt·ω), amp unchanged, freq unchanged | PASS |

**CPU/wgpu covered; CUDA compiles, not executed:** `cargo build -p prin-kernels --features cuda --lib` succeeds (re-verified this session). No CUDA-capable runner available (**DV-002**, pre-existing, unchanged).

**Parity-evidence disposition (S1 exit gate, R15):** The S1 handoff note correctly states that no new cross-crate parity test is added, because `discrete_step_cpu` composes two already-parity-verified primitives (`mean_field_derivatives_into` transitively via `mean_field_rk4`'s coverage, PAC modulation formula via `pac::tests::parity_against_prin_dynamics_phase_amplitude_coupling`) in a new sequential composition that has no direct PRINet 3.0 counterpart (the closest analogue, `BandNetwork`, deliberately implements the *continuous* relaxation form). The `zero_pac_depth_gates_to_identity` and `pac_gate_modulates_fast_band_amplitude` tests verify internal consistency with the two primitives. This is a valid disposition, not an unverified assertion — the grep/import check against the archived reference is documented in the handoff note's "Parity-evidence disposition" section.

**Launch-count and report evidence:** All CubeCL tests verify `report.launch_count == 10` (matching the module documentation's launch sequence) and `report.backend_name` correctness. The `StepReport::wall_time_seconds` is non-negative and `timing_method` is correctly reported.

### 3.5 A5 — Quality gates

All gates independently re-executed (commands in §2); all clean/PASS, matching S1's own claims exactly.

### 3.6 A6 — Security

- **`unsafe` audit:** `discrete_step/cubecl.rs` carries `#![allow(unsafe_code)]` + `#![deny(unsafe_op_in_unsafe_fn)]` at module scope (the established `prin-kernels` kernel-FFI exception, Coding Standards §2.1/§6.1). Every `unsafe` block (`array_arg` function) is confined to `ArrayArg::from_raw_parts` with a `// SAFETY:` comment matching the established handle-length-contract pattern from `mean_field_rk4/cubecl.rs` and `pac/cubecl.rs`. No other `unsafe` code introduced.
- **`cargo audit`:** 1 allowed warning — pre-existing `paste` RUSTSEC-2024-0436 (DV-008). No new advisories.
- **`bandit -r .`:** 0 issues (3168 lines scanned, unchanged — no Python touched).
- **No dependency/manifest changes:** `git diff 71654e4..9af9ce0 -- crates/prin-kernels/Cargo.toml` shows only a `[[bench]]` target added; `Cargo.lock` unchanged. Snyk Open Source correctly not re-run.
- No secrets, no runtime codegen, no new dependencies.

### 3.7 A7 — Docstring/doc coverage

- **Python:** `interrogate` 100.0% (106/106) — unchanged, no Python files touched.
- **Rust:** `cargo doc --workspace --no-deps` under `RUSTDOCFLAGS=-D warnings` — 0 warnings, independently re-run. All new public items carry doc comments: `BandStepParams` (all fields), `PacGateParams` (all fields), `DiscreteStepParams` (all fields), `DiscreteStepOutput`, `DiscreteStepError` (all variants), `discrete_step_cpu`, `discrete_step_cubecl`/`try_*`/`_auto`, `StepReport` (all fields), `StepCubeclOutput`. Module-level docs on both `discrete_step.rs` and `discrete_step/cubecl.rs` explain the algorithm, state layout, launch sequence (10 launches enumerated), reduction design rationale, and correspondence to the PRINet 3.0 reference.

### 3.8 A8 — Repository hygiene

- **TODO/FIXME scan:** `grep` for `TODO|FIXME|HACK|XXX|STUB` in `discrete_step.rs` and `discrete_step/cubecl.rs` — 0 matches.
- **Session register:** Row 0077 = `COMPLETE`; row 0078 = `PLANNED` (correct — S2 exit updates it).
- **Git state:** Clean working tree at the audited commit, 1 commit ahead of `origin/main`.
- **No orphan files.** All new files accounted for in the S1 commit.
- **S1 handoff note accuracy:** All coverage figures, test counts, benchmark timings, and architecture-decision descriptions verified against independent re-measurement. No factual inaccuracies found (contrast with WP-019's WP019-F1).

### 3.9 A9 — CI status

- **No `.github/workflows/*` files touched** in the S1 commit range.
- **Local reproduction:** every test/coverage/quality/security command independently re-run this session (§2); all results match the S1 handoff note's figures exactly.
- **wgpu/CUDA CI:** remain deferred to a headless GPU / CUDA-capable runner (DV-001, DV-002, unchanged, pre-existing).
- **Benchmark regression gates:** none defined for `prin-kernels` (unchanged); the new `discrete_step_bench` is a pilot, not a regression gate (Benchmarking Standards §2.2).

### 3.10 A10 — Artefact trail

- **Prior audit:** `DOCS/audits/019-wp019-audit.md` exists, verdict `PASS-WITH-FINDINGS` → FIXED (commit `cdc01e6`), S3 no-change closure CLEAN.
- **Prior PSR:** `DOCS/reports/019-project-state.md` exists and is consistent with this WP's declared scope, acceptance criteria, and non-goals.
- **S1 handoff note:** `DOCS/experiments/0077-wp020-s1-handoff.md` — comprehensive, with an acceptance-criterion evidence map, architecture-decision rationale (5 decisions documented), out-of-scope discoveries log, and parity-evidence disposition. All claims verified.
- **Deferred Validation Register:** DV-002/DV-004 correctly referenced by the S1 handoff note. DV-004's "re-audit gate" field says "Phase 3 (WP-020) — remains open while more `#[cube(launch)]` kernels are added" — this WP adds 4 more kernel bodies (total now 10), exactly the scenario the register anticipated. S4 should update the register text.
- **CHANGELOG:** WP-020 changes not yet in `CHANGELOG.md` — expected (S4 duty, not an S1/S2 gap).

## 4. Issues found

**No issues found.** All ten audit dimensions pass without qualification.

| ID | Severity | Location | Issue | Violated clause | Proposed remedy |
|---|---|---|---|---|---|
| *(none)* | — | — | — | — | — |

## 5. Deviation-ledger delta

**New findings added to the ledger:** *(none)*

**Carried findings re-inspected:**

| ID | Status | Notes |
|---|---|---|
| DV-001 | Unchanged | Same-hardware Triton comparison still blocked on Linux/CUDA runner; not this WP's scope. |
| DV-002 | Re-inspected, unchanged | `try_discrete_step_cuda` compiles cleanly (`cargo build --features cuda --lib`, re-verified this session); no CUDA-capable runner available to execute. Pre-existing, not newly introduced. |
| DV-004 | Re-inspected | Four more `#[cube(launch)]` kernel bodies now carry the non-instrumentable-coverage carve-out (`complex_order_reduce`, `real_sum_reduce`, `band_euler_step`, `pac_gate`), bringing the cumulative total from 6 to **10**. `discrete_step/cubecl.rs` raw `wgpu,cpu` figure (79.32%) is 1.44 points below the `mean_field_rk4/cubecl.rs` baseline (80.76%), fully explained by the higher kernel-body-to-total-code ratio. Register text anticipated exactly this; S4 should record the four additional kernel bodies and re-measure all files' baselines. |
| DV-008 | Re-inspected | `cargo audit` clean except the pre-existing `paste` advisory. No new advisory. Unchanged. |

## 6. Verdict and required actions

**Verdict: PASS**

All ten audit dimensions pass without qualification. The WP-020 delivery is evidence-backed, well-tested (29 new tests including 2 proptest suites and 12 CubeCL backend-equivalence tests), architecturally sound (reuses `mean_field_rk4` primitives via minimal `pub(crate)` visibility promotions, f64-accumulated reductions matching the CPU reference exactly, 10-launch fused path structurally analogous to WP-018/WP-019's patterns), and cleanly documented.

The `discrete_step/cubecl.rs` raw coverage (79.32%) is below the 95% gate for the same accepted DV-004 reason as all prior kernel-dispatch files; the shortfall against the `mean_field_rk4/cubecl.rs` baseline is fully explained by the higher kernel-body count, not a coverage regression. No new deviation is raised.

**S3 work list (mandatory even with zero findings — Development Workflow Standards §3):**

1. Record a no-change closure in the audit report's closure table (§7).
2. Independent delta verification: re-confirm all gates remain green against the unchanged source tree.
3. Hand off to S4 (session 0080) for documentation closure: README updates, CHANGELOG entry, DV-004 register update (four additional non-instrumentable kernel bodies, total now 10), and PSR-020.

**Maintainer acknowledgment:** _(pending)_

---

## 7. Closure table (appended by S3 remediation)

**S2 verdict (§6) recorded zero findings** — the issues table in §4 is empty
and no D1–D4 items exist to process. Per `Development_Workflow_and_Audit_Standards.md`
§3 ("S3 remains mandatory when S2 finds zero deviations: it records a
no-change closure and independent delta verification") and session brief
0079 item 6, this closure records a no-change delta verification.

Independent reproduction of §2's methodology commands surfaced one
evidentiary inaccuracy in the audit report itself (not a source defect):
the `cargo test -p prin-kernels --features cpu` cell in §2 read "102 unit +
1 doctest passed", but the S1 handoff note (`DOCS/experiments/0077-wp020-s1-handoff.md`,
line 50) recorded "121 unit + 1 doctest" for the identical command, and two
independent re-runs this session reproduce 121 exactly (§3.5's claim that
S2 "match[ed] S1's own claims exactly" was therefore false for this one
cell). This is assigned **WP020-F1** (D4 — cosmetic/evidentiary, no
verdict impact: both figures are "all green", the crate's actual test
count is unaffected) and corrected in §2 of this report as part of this
closure, per the WP019-F1 precedent (`DOCS/audits/019-wp019-audit.md` §7).

| ID | Resolution | Commit / amendment | Delta re-audit evidence |
|---|---|---|---|
| WP020-F1 | FIXED | S3 commit (session 0079) — corrects §2's `cargo test -p prin-kernels --features cpu` comment from "102 unit + 1 doctest" to "121 unit + 1 doctest", matching the S1 handoff note and two independent re-runs this session | See "`prin-kernels` (`cpu`)" row below |
| *(no other findings — S2 recorded none)* | NO-CHANGE | S3 commit (session 0079) — no source, test, or dependency edits; `git diff 9af9ce0..HEAD -- crates/ python/ tests/ tools/ parity/ benchmarks/` is empty | See independent re-execution table below |

### Independent delta re-execution (session 0079, git state unchanged at `9af9ce0`; audit-report-only edit on top of `4fefc6e`)

All commands re-run from a clean working tree (`git status` clean, 2 commits
ahead of `origin/main` at the start of this session; `git diff 9af9ce0..HEAD`
restricted to `crates/ python/ tests/ tools/ parity/ benchmarks/` is empty —
confirms the source tree audited at S2 is byte-for-byte unchanged):

| Gate | Command | Result | vs. S2 audit (§2–§3) |
|---|---|---|---|
| Rust format | `cargo fmt --all -- --check` | PASS (exit 0) | Unchanged |
| Clippy (default) | `cargo clippy --workspace --all-targets -- -D warnings` | PASS (exit 0) | Unchanged |
| Clippy (strict-checks) | `cargo clippy --workspace --all-targets --features strict-checks -- -D warnings` | PASS (exit 0) | Unchanged (not in S2's own command list; included here for parity with the WP-018/WP-019 S3 pattern) |
| Clippy (`cpu`) | `cargo clippy -p prin-kernels --all-targets --features cpu -- -D warnings` | PASS (exit 0) | Unchanged |
| Clippy (`wgpu,cpu`) | `cargo clippy -p prin-kernels --all-targets --features wgpu,cpu -- -D warnings` | PASS (exit 0) | Unchanged |
| CUDA (compile-only) | `cargo build -p prin-kernels --features cuda --lib` | PASS (exit 0) | Unchanged (DV-002 still open, pre-existing) |
| Rustdoc (workspace) | `RUSTDOCFLAGS='-D warnings' cargo doc --workspace --no-deps` | PASS, 0 warnings | Unchanged |
| Rustdoc (`prin-kernels`, cpu / wgpu,cpu / cuda) | `cargo doc -p prin-kernels --no-deps --features <cpu\|wgpu,cpu\|cuda>` | PASS, 0 warnings, all three combinations | Unchanged |
| Workspace tests | `cargo test --workspace` | PASS, exit 0, all suites `ok` (0 failed) | Unchanged |
| `prin-kernels` (`cpu`) | `cargo test -p prin-kernels --features cpu` | PASS — **121** unit + 1 doctest | Corrects WP020-F1 (S2's §2 cell read 102); exact match to the S1 handoff note and two independent re-runs this session |
| `prin-kernels` (`wgpu,cpu`) | `cargo test -p prin-kernels --features wgpu,cpu -- --test-threads=1` | PASS — 149 unit + 1 doctest | Exact match |
| Coverage (`wgpu,cpu`) | `cargo llvm-cov -p prin-kernels --features wgpu,cpu` | `discrete_step.rs` 97.65% lines (468/11 missed); `discrete_step/cubecl.rs` raw 79.32% lines (590/122 missed); `mean_field_rk4/cubecl.rs` 80.76%, `pac/cubecl.rs` raw 82.93%, `sparse_knn/cubecl.rs` raw 85.86% | Exact match to §3.3/§3.4's figures and the DV-004 baseline table |
| `cargo audit` | `cargo audit` | 1 allowed warning — `paste` RUSTSEC-2024-0436 (DV-008), no new advisory | Unchanged |
| Snyk Code | `snyk code test crates/prin-kernels/src` | PASS — 0 issues (org `symbo-gif`) | Supplements S2, which (unlike WP-018/WP-019's S2/S3) did not independently re-run Snyk Code — this closure adds that evidence |
| Snyk Open Source | Not re-run — no dependency/manifest changes since `9af9ce0` (Coding Standards §6.2 gates dependency changes; none occurred, `Cargo.lock` unchanged) | N/A | Unchanged (no trigger), matching S2's §3.6 disposition |
| `ruff check` | `ruff check python/ tests/ benchmarks/ tools/ parity/` | PASS — all checks passed | Unchanged |
| `ruff format --check` | `ruff format --check python/ tests/ benchmarks/ tools/ parity/` | PASS — 50 files already formatted | Unchanged |
| `mypy --strict` | `mypy python/prin --strict` | PASS — 0 issues, 18 files | Unchanged |
| `bandit` | `bandit -r . -c pyproject.toml` | PASS — 0 issues | Unchanged |
| `interrogate` | `interrogate -c pyproject.toml python/prin` | PASS — 100.0% (106/106) | Unchanged |
| `pytest` | `pytest tests/ -m "not slow and not gpu" --basetemp=.pytest_basetemp` | PASS — 306 passed, 6 deselected | Exact match |
| WP acceptance (`discrete_step_bench`, `--features wgpu`) | `cargo bench -p prin-kernels --bench discrete_step_bench --features wgpu` | `fused_cpu_native` 2.256–2.332 ms (36.9–38.1 Melem/s) vs. `unfused_cpu_native` 8.56–8.78 ms (9.79–10.05 Melem/s) — fused ~3.7× faster; wgpu `StepReport` (untimed evidence): `backend_name: "wgpu<wgsl>"`, `wall_time_seconds: 9.216e-6`, `timing_method: Device`, `launch_count: 10` | Consistent with the S1 handoff's reported range (2.043–2.060 ms / 7.85–7.93 ms / ~3.8×) and launch-count target; the absolute-time increase is normal run-to-run machine-load variance for a non-gating pilot benchmark (Benchmarking Standards §2.2), not a code change — confirmed by the empty `git diff` above. `launch_count: 10` and `timing_method: Device` reproduce exactly. |

No newly introduced deviation. No regression below any coverage, quality,
security, or parity gate. The only change in the tree across this S3 cycle
is the one-cell documentation correction (WP020-F1) in this audit report's
own §2, plus the closure content appended here.

**Delta re-audit date:** 2026-08-16

**Result:** CLEAN — the sole finding (WP020-F1, self-discovered during this
session's independent reproduction) is FIXED in this closure commit;
independent re-execution of every A1–A10 gate and the WP-020 acceptance
evidence (forward equivalence, no runtime JIT, 10-launch reduction/launch-count
target) reproduces the S2 audit's PASS verdict exactly, with no newly
introduced deviation. Hand off to S4 (session 0080).
