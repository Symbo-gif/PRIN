# Session 0081 — WP-021 S1 Handoff Note

**Session:** 0081 — WP-021 S1: Coding — GPU integration and Phase 3 gate
**Date:** 2026-08-16
**Status:** S1 delivered; handoff to S2 audit (session 0082)

## Mission recap

"Integrate all kernel dispatch into simulation, exercise self-hosted CUDA and
wgpu/Metal-capable paths, and lock regression baselines." Contract
(`DOCS/sessions/phase-3/0081-wp021-s1-gpu-integration-and-phase-3-gate.md`):
every kernel-equivalence test green; all §N1 GPU targets met or approved
amendments; Phase 3 pre-release gate passes. Non-goals: trainable
architecture implementation.

## Environment discovery (changes the starting conditions for this session)

This host has a working NVIDIA GeForce RTX 4060 (driver 595.95, CUDA 13.2)
and `nvcc` 12.5 installed. Every prior Phase-3 session recorded CUDA hardware
as unavailable (DV-001 "blocked on Windows Python 3.14" for Triton; DV-005
"blocked on CUDA hardware"). This is the **first session in the project's
history that can actually execute the `cuda` feature**, not just
compile it — every "CUDA: compile-only" evidence line in PSR-004 through
PSR-020 is superseded by real execution evidence below. `git`/DV-register
disposition of this fact is an S4 (PSR) responsibility, not S1's; this note
records the raw evidence for that later session to act on.

## Scope delivered

| File | Change |
|---|---|
| `crates/prin-kernels/src/mean_field_rk4/cubecl.rs` | **Bug fix + tests.** `step_auto` tried `wgpu` before `cuda`, contradicting its own rustdoc ("Tries each backend ... in priority order (CUDA → wgpu → CPU)") and `backend::auto_detect_order()`'s documented/tested CUDA-first priority. Reordered to try `cuda` first. Added `tests_cuda` (CUDA-vs-CPU-reference kernel equivalence at N=64 and N=1,000,000, typed-error coverage) and `tests_priority` (`step_auto_prefers_cuda_over_wgpu_when_both_available`, asserting `StepReport.backend_name == "cuda"` when both backends are compiled in and available). |
| `crates/prin-kernels/src/discrete_step/cubecl.rs` | Same bug fix and the same two new test modules (`tests_cuda`, `tests_priority`) for `discrete_step_auto`. |
| `crates/prin-kernels/src/pac/cubecl.rs` | Same bug fix for `pac_modulate_auto`. `pac_modulate_auto`/`sparse_knn_coupling_auto` return no backend-identifying report (unlike the two step functions above), so no priority-order regression test is possible from the public return value alone; added `tests_cuda` (direct `try_pac_modulate_cuda` kernel-equivalence and error-path coverage) as the best available regression signal. |
| `crates/prin-kernels/src/sparse_knn/cubecl.rs` | Same bug fix for `sparse_knn_coupling_auto`, plus `tests_cuda` (direct `try_sparse_knn_coupling_cuda` kernel-equivalence and error-path coverage), same rationale as `pac`. |
| `crates/prin-sim/Cargo.toml` | Added `prin-kernels` as a runtime dependency (was previously undeclared — `prin-sim` had zero calls into `prin-kernels`, see `lib.rs`'s pre-existing "Non-goals: GPU dispatch (Phase 3)... remain out of scope" line, now removed). Added `cpu`/`cuda`/`wgpu` features forwarding to the identically-named `prin-kernels` features. Added `[[bench]] gpu_bench`. |
| `crates/prin-sim/src/error.rs` | Added three `SimError` variants wrapping `prin-kernels` error types (`MeanFieldKernel`, `DiscreteStepKernel`, `SparseKnnKernel`, all `#[from]`), matching the existing `Dynamics`/`Integration`/`Metric` wrapping convention. |
| `crates/prin-sim/src/lib.rs` | Added `pub mod gpu;` gated on `any(feature = "cpu", feature = "cuda", feature = "wgpu")`; updated the module doc's GPU-dispatch section (was "Non-goals... GPU dispatch remains out of scope"). |
| `crates/prin-sim/src/gpu.rs` | **New** (968 lines). See "GPU integration into simulation" below. |
| `crates/prin-sim/benches/gpu_bench.rs` | **New** (155 lines). Criterion benchmark comparing the CPU and GPU-dispatched paths at the exact §N1-named problem sizes. See "Benchmark evidence" below. |
| `.github/workflows/rust.yml` | Added `cargo test -p prin-sim --features cpu -- --test-threads=1` to the `test` job, mirroring the existing `cargo test -p prin-kernels --features cpu` step — the new `prin-sim::gpu` module now has its own CI-exercised kernel-equivalence suite on every push/PR, not just the local dev/`gpu.yml` self-hosted-runner path. |

## GPU integration into simulation

`prin-sim` previously had **zero** calls into `prin-kernels` (confirmed by
`grep -rn "prin_kernels" crates/prin-sim/src/` before this session: no
matches). `gpu.rs` adds three types, one per existing `prin-kernels` kernel
family that has a natural simulation-layer consumer:

1. **`GpuSparseKuramoto`** — a `prin_dynamics::models::Dynamics`
   implementation that dispatches the sparse Kuramoto coupling term through
   `prin_kernels::sparse_knn::cubecl::sparse_knn_coupling_auto` instead of
   `SparseCoupling::kuramoto_coupling`'s CSR SpMV. Because it implements the
   same `Dynamics` trait as the existing `SparseKuramoto`, it drops directly
   into `OscilloSim::step`/`run` via the existing `Integrator` machinery —
   **no changes to `engine.rs`'s core loop were needed or made**. It reuses
   an existing `SparseCoupling`'s CSR topology (`indptr`/`indices` via
   `CsMat::indptr().raw_storage()`/`indices()`) rather than rebuilding a
   neighbor graph, and validates at construction time that the coupling's
   per-row weights match the uniform `K/degree(i)` convention
   `prin-kernels`' kernel assumes (returns `SimError::InvalidCoupling`
   otherwise — a `SparseCoupling::from_dense`/custom-weighted `from_csr`
   coupling will generally fail this check by design, since silently
   ignoring real per-edge weights would compute wrong physics).
2. **`GpuMeanFieldEngine`** — a small stepper wrapping the fully fused dense
   all-to-all RK4 kernel (`mean_field_rk4::cubecl::step_auto`). Because the
   kernel fuses all four RK4 sub-stages into one launch sequence, it cannot
   be expressed as a `Dynamics` + generic `Integrator` composition (that
   would re-decompose the fusion the kernel exists to provide); this type
   owns its own minimal `step`/`run` loop instead, reusing `engine::Trajectory`
   for trajectory recording so callers get the same recorded-artifact shape
   `OscilloSim::run` produces.
3. **`GpuBandStepper`** — the same pattern for the three-band fused discrete
   step (`discrete_step::cubecl::discrete_step_auto`, the WP-020 kernel).
   This is the first point in the project either fused kernel (mean-field
   RK4 or discrete-step) is driven by anything beyond a unit test or
   microbenchmark.

All three convert `f64` (the `prin_dynamics`/`prin-sim` numerical authority)
to `f32` (the kernel's native dtype) at the boundary and back, matching the
precision convention every existing kernel-equivalence test already
establishes.

## Acceptance criteria → evidence map

| Criterion | Verdict | Evidence |
|---|---|---|
| **Integrate all kernel dispatch into simulation** | **GREEN** | `GpuSparseKuramoto`/`GpuMeanFieldEngine`/`GpuBandStepper` cover the three kernel families with a natural simulation-layer shape (sparse coupling, dense mean-field, three-band discrete step). `pac`'s kernel is not separately integrated at the simulation layer — it is already consumed internally by `discrete_step_auto`'s fused launch sequence (WP-020); a standalone "PAC modulation in the simulation loop, outside the three-band stepper" integration point does not exist in the current architecture and is not invented here, matching the "only the declared WP scope" rule. |
| **Every kernel-equivalence test is green** | **GREEN** | `cargo test -p prin-kernels --features cuda` (real CUDA hardware): 113 passed, 1 doctest. `cargo test -p prin-kernels --features cuda,wgpu -- --test-threads=1`: 143 passed, 1 doctest (includes the two new `tests_priority` cases, both confirming CUDA is selected over wgpu). `cargo test -p prin-kernels --features cpu`: 121 passed, 1 doctest (unchanged from PSR-020 baseline — no new tests compile under `cpu` alone). `cargo test -p prin-kernels --features wgpu,cpu -- --test-threads=1`: 149 passed, 1 doctest (unchanged from PSR-020 baseline). `cargo test -p prin-sim --features cuda`: 153 passed (128 pre-existing + 25 new `gpu::tests`), fast (~1s). `cargo test -p prin-sim --features cpu -- --test-threads=1`: 153 passed (same 25 new tests, ~110s — CubeCL-CPU per-call JIT overhead, matching `prin-kernels`' own known cost profile for this backend). `cargo test --workspace --features cuda -- --test-threads=1`: confirms `--workspace --features cuda` forwards correctly to `prin-sim` (153 passed there too) — the existing `gpu.yml` `cargo test --workspace --features cuda` step now exercises the new integration without any workflow change. `cargo test --workspace` (default, no GPU features): unaffected, all green. |
| **All §N1 GPU targets meet or have approved amendments** | **PARTIAL — see below** | "Mean-field RK4, N=1M, GPU ≥ Triton-fused parity": no Triton comparison is possible from this Rust crate (DV-001, unchanged — Triton is Linux/WSL-only regardless of local CUDA hardware); this session's benchmark instead reports genuine CUDA-vs-CPU speedup at N=1M through the new simulation-integrated path (5.9×, see below) as partial evidence toward the target's intent. "Sparse k-NN coupling, N=16K, k=14, GPU ≥ parity (3× torch)": no torch comparison exists in this crate either; benchmark evidence below shows the naive (unpooled) `GpuSparseKuramoto` dispatch is currently *slower* than the CPU SpMV path at this N — an honest negative result, not a target met, recorded as an out-of-scope discovery below (buffer pooling is the known fix, already used by `mean_field_rk4`'s CPU/GPU dispatch, not attempted here). "Fused discrete step (3-band + PAC), GPU ≥ parity, no runtime JIT": not separately re-benchmarked this session (WP-020 already established this kernel's own performance evidence via `discrete_step_bench.rs`; this WP's job was integration, which `GpuBandStepper`'s equivalence tests confirm preserves the kernel's numerics through the new wrapper). No new plan amendment is proposed in S1 (amendments require maintainer approval per the Session Cycle's S3 mechanism); this table is the evidence base for S2/S3 to determine whether an amendment is warranted for the sparse k-NN target. |
| **Phase 3 pre-release gate passes** | **DEFERRED TO S4/PSR, BY DESIGN** | Investigated whether to build a `tools/wp021_phase3_gate.py` mirroring `tools/wp005_phase0_gate.py` (the Phase 0 go/no-go tool). Found that Phase 1 and Phase 2 exit gates were **not** determined by a dedicated script — PSR-011 and PSR-016 recorded their phase-exit verdicts directly in each PSR's "Trajectory verdict" section, evidence-backed but not tool-automated; `wp005_phase0_gate.py` was Phase-0-specific tooling for that phase's three foundational technology-choice spikes (CubeCL vs. Triton, DLPack round-trip, ORT/DirectML), not a repeated per-phase pattern. Building new gate-checking tooling this session would be scope invention beyond the mission's literal text and the established two-phase precedent; the Phase 3 gate is instead expected to follow the Phase 1/2 precedent — an evidence-backed verdict in the WP-021 S4 Project State Report (session 0084), informed by this note's evidence table. Flagged for maintainer visibility, not decided unilaterally. |
| **All quality/security gates green** | **GREEN** | See table below. |

## Quality gates (S1 verification)

| Gate | Command | Result |
|---|---|---|
| Format | `cargo fmt --all -- --check` | PASS |
| Clippy (default) | `cargo clippy --workspace --all-targets -- -D warnings` | PASS |
| Clippy (strict-checks) | `cargo clippy --workspace --all-targets --features strict-checks -- -D warnings` | PASS |
| Clippy (`prin-sim`, cpu/cuda/wgpu, individually and combined) | `cargo clippy -p prin-sim --all-targets --features <cpu\|cuda\|wgpu\|cpu,cuda,wgpu> -- -D warnings` | PASS, all four combinations |
| Clippy (`prin-kernels`, cuda/cuda+wgpu) | `cargo clippy -p prin-kernels --all-targets --features <cuda\|cuda,wgpu> -- -D warnings` | PASS |
| Workspace tests (default) | `cargo test --workspace` | PASS, no regressions |
| Workspace tests (cuda) | `cargo test --workspace --features cuda -- --test-threads=1` | PASS |
| `prin-kernels` (cuda) | `cargo test -p prin-kernels --features cuda` | PASS — 113 unit + 1 doctest (first real CUDA execution in project history) |
| `prin-kernels` (cuda,wgpu) | `cargo test -p prin-kernels --features cuda,wgpu -- --test-threads=1` | PASS — 143 unit + 1 doctest, including the new priority-fix regression tests |
| `prin-kernels` (cpu) | `cargo test -p prin-kernels --features cpu` | PASS — 121 unit + 1 doctest (unchanged from PSR-020) |
| `prin-kernels` (wgpu,cpu) | `cargo test -p prin-kernels --features wgpu,cpu -- --test-threads=1` | PASS — 149 unit + 1 doctest (unchanged from PSR-020) |
| `prin-sim` (cuda) | `cargo test -p prin-sim --features cuda -- --test-threads=1` | PASS — 153 unit (128 pre-existing + 25 new), 3 doctests |
| `prin-sim` (cpu) | `cargo test -p prin-sim --features cpu -- --test-threads=1` | PASS — 153 unit, 3 doctests |
| `prin-sim` (wgpu,cpu) | `cargo test -p prin-sim --features wgpu,cpu -- --test-threads=1` | PASS — 153 unit |
| Rustdoc (workspace, default) | `RUSTDOCFLAGS=-D warnings cargo doc --workspace --no-deps` | PASS — 0 warnings (the module doc's `gpu` reference is deliberately non-intra-doc-linked text, since the module doesn't exist in a default-feature build) |
| Rustdoc (`prin-sim`+`prin-kernels`, cuda+wgpu+cpu) | `RUSTDOCFLAGS=-D warnings cargo doc -p prin-sim -p prin-kernels --no-deps --features cuda,wgpu,cpu` | PASS — 0 warnings |
| `cargo audit` | `cargo audit` | PASS — 1 allowed warning (pre-existing `paste` RUSTSEC-2024-0436, amendment #9), unchanged, no new advisories |
| Snyk Code | `snyk code test crates/prin-sim/src` and `crates/prin-kernels/src` | PASS — 0 issues, both paths |
| Snyk Open Source | Not run | No external dependency added — `Cargo.lock`'s only change is the internal `prin-sim → prin-kernels` workspace edge (both already in the workspace); matches the established non-gating precedent for manifest changes with no new external crate |
| Bench compile/smoke | `cargo bench -p prin-sim --bench gpu_bench --features cuda -- --test` | PASS (see "Benchmark evidence" for the caveat on `--features cpu` alone) |

## Coverage (new/changed code)

`cargo llvm-cov -p prin-sim --features cuda` on `crates/prin-sim/src/gpu.rs`:
**99.67% lines** (604/606), **98.41% functions** (62/63), **98.17% regions**
(1124/1145) — well above the ≥95% gate. The single missed line (525) is the
closing `)?;` of a multi-line kernel-dispatch call inside `GpuBandStepper::step`
— an `llvm-cov` multi-line-expression attribution artifact (the surrounding
lines of the same call and every branch of `step` are covered); the one
missed function is a derived `Clone` impl never explicitly invoked via
`.clone()` in a test. Neither represents an untested code path.

## Benchmark evidence

`cargo bench -p prin-sim --bench gpu_bench --features cuda` (10 criterion
samples each), this host (RTX 4060):

| Benchmark | Path | Time | Notes |
|---|---|---|---|
| `sparse_kuramoto_cpu_vs_gpu` (N=16,000, k=14 — the exact §N1 sparse target size) | `cpu_spmv` (existing `SparseKuramoto`) | 3.57–3.63 ms | |
| | `gpu_kernel_dispatch` (new `GpuSparseKuramoto`, CUDA) | 5.60–6.95 ms | **Slower than CPU at this N.** `GpuSparseKuramoto::compute_derivatives` allocates fresh device buffers every call (`client.create_from_slice`, no pool) and is invoked 4× per RK4 step; host↔device transfer + launch overhead dominates at N=16K. See "Out-of-scope discoveries." |
| `mean_field_cpu_vs_gpu` (N=1,000,000 — the exact §N1 mean-field target size) | `cpu_dynamics` (`prin_dynamics::KuramotoOscillator` + `RK4Integrator`) | 191.3–192.7 ms | |
| | `gpu_kernel_dispatch` (new `GpuMeanFieldEngine`, CUDA, fused single-launch-sequence RK4) | 31.8–32.9 ms | **≈5.9× faster than CPU.** The fused kernel's single launch sequence per step (vs. 4 separate host-orchestrated derivative evaluations for the CPU path) is exactly where GPU dispatch is expected to win. |

Reported as observed pilot evidence (Testing Standards §2, Benchmarking
Standards §2.2), not a scientific conclusion; no regression gate is defined
for this new benchmark, matching the established non-gating status of
`mean_field_rk4_bench`/`sparse_knn_bench`/`discrete_step_bench`. **Not**
added to the `bench-smoke` CI job — see "Out-of-scope discoveries" for the
`--features cpu`-only crash this decision is based on.

## Out-of-scope discoveries

- **`prin-kernels::mean_field_rk4::cubecl::try_step_cpu` (CubeCL-CPU backend)
  hangs/crashes at N=1,000,000 with only the `cpu` feature enabled (no
  `cuda`/`wgpu`).** Discovered while smoke-testing `gpu_bench.rs` for
  `bench-smoke` CI inclusion: the process grew to significant memory over
  several minutes, then exited with `0xffffffff`. Confirmed as a
  **pre-existing `prin-kernels`-level gap, not a defect introduced by this
  WP**: `prin-kernels`' own `mean_field_rk4_bench.rs` has never benchmarked
  `try_step_cpu` at N=1M in its history (only the native `step_cpu`
  reference, which is fast and unaffected), and no existing `prin-kernels`
  test exercises this combination either — `tests_cpu`'s N=1M-scale tests
  don't exist, only small-N cases (64, 300). `cuda` and `wgpu` both complete
  the identical N=1M call in tens of milliseconds. Documented prominently in
  `gpu_bench.rs`'s module doc; `bench-smoke` CI was **not** extended to run
  this new benchmark (a CPU-only GitHub-hosted runner would hit exactly this
  path). Recommend a future `prin-kernels` WP investigate root cause
  (unbounded per-element interpretation cost in the CubeCL-CPU runtime at
  this N, most likely) before enabling `cpu`-only large-N testing anywhere.
- **`GpuSparseKuramoto`'s unpooled per-call dispatch is slower than CPU SpMV
  at the sparse k-NN §N1 target size (N=16K, k=14).** See "Benchmark
  evidence." The established fix pattern already exists in this codebase
  (`mean_field_rk4::cubecl::CubeclBufferPool`/`step_cubecl_with_pool`,
  landed in WP-018) but adding an analogous pool for `sparse_knn` — and
  redesigning `GpuSparseKuramoto` to reuse it across the 4 RK4 sub-stage
  calls in one step, and ideally across multiple steps — is a nontrivial
  design task (`Dynamics::compute_derivatives(&self, ...)` takes `&self`,
  so a pool would need interior mutability or a different trait shape) left
  to a future performance WP rather than attempted under this session's
  time budget.
- **`prin-py` sweep/engine PyO3 bindings (DV-012/R19) remain open.** This
  session's scope is `crates/prin-sim` GPU-dispatch integration (a
  Rust-internal change), not new Python bindings; R19 explicitly defers the
  final WP assignment for the carried `prin-py` scope to "the Phase 3
  exit-gate PSR (WP-021 S4, session 0084) at latest" — an S4 decision, not
  S1's to make.
- **Pre-existing deviation-ledger inconsistency, found but not investigated
  or fixed (unrelated to this WP's scope).** WP016-F7 (`020-project-state.md`
  §3) claims a `phase2-gate` CI job was "added to `rust.yml`" in commit
  `57c5f4a`; neither the job nor that commit hash exist in the current
  repository (`git cat-file -t 57c5f4a` → "Not a valid object name";
  `.github/workflows/rust.yml` has no `phase2-gate` job). This resembles the
  "fabricated commit hash" defect class EA-003 already found and corrected
  elsewhere in the ledger (`EXECUTIVE_AUDIT_REPORT_003.md`). Flagged here
  for a future audit's attention; not investigated further or corrected in
  this session (git-history/ledger archaeology is not this WP's declared
  scope, and S1 may not perform audit-style corrections outside its own
  work).

## Parity-evidence disposition

No new numerical primitive is introduced this session — `GpuSparseKuramoto`,
`GpuMeanFieldEngine`, and `GpuBandStepper` are thin dispatch/state-management
wrappers around `prin-kernels` kernels whose PRINet 3.0 parity was already
established at WP-018/WP-019/WP-020 (grep-verified: no new trig/ODE/reduction
formula appears in `gpu.rs` — every numerical operation is delegated to an
existing `prin_kernels::*::cubecl::*_auto` call). This session's own tests
instead verify the *wrapper* is correct: `gpu_sparse_kuramoto_matches_cpu_
dynamics_reference` checks `GpuSparseKuramoto` against `prin_dynamics::
KuramotoOscillator`'s already-parity-verified `SparseKnn` mode (reusing the
`sparse_knn::tests::parity_against_prin_dynamics_kuramoto_sparse_knn`
precedent's `1e-4` absolute f32-vs-f64 tolerance), and the `*_step_matches_
kernel_cpu_reference_loop` tests confirm `GpuMeanFieldEngine`/`GpuBandStepper`
thread state across multiple steps identically to calling the underlying
`step_cpu`/`discrete_step_cpu` kernel functions directly in a loop.
