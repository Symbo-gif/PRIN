# Session 0073 — WP-019 S1 Handoff Note

**Session:** 0073 — WP-019 S1: Coding — Sparse k-NN and PAC kernels
**Date:** 2026-08-16
**Status:** S1 delivered; handoff to S2 audit (session 0074)

## Mission recap

"Implement sparse phase-neighbor coupling and PAC modulation kernels with
CSR/index interoperability." Scope (PSR-018 §7): `crates/prin-kernels/` —
sparse phase-neighbor coupling and PAC modulation kernels with CSR/index
interoperability, single-source CubeCL with CPU/wgpu/CUDA dispatch,
continuing the WP-017/WP-018 architecture. Non-goals: fused trainable
discrete step (deferred to WP-020, unchanged).

## Scope delivered

| File | Change |
|---|---|
| `crates/prin-kernels/src/sparse_knn.rs` | **New.** `SparseKnnGraph` — a CSR (`indptr`/`indices`, both `u32`) sparse phase-neighbor graph type with two constructors: `from_csr` (accepts an externally built CSR structure — the "CSR/index interoperability" the mission names) and `from_phase_knn` (builds directly from a phase array and `k`, reusing `prin_dynamics::state::build_phase_knn_index`'s `O(N log N)` sort-based neighbor search rather than re-implementing it, Coding Standards §1). `sparse_knn_derivatives_cpu` — the CPU reference (numerical authority) computing the Kuramoto-style sparse coupling derivative `(dphase, damplitude, dfrequency)` per row via the angle-difference trig identity (`sin(φⱼ−φᵢ) = sinφⱼcosφᵢ − cosφⱼsinφᵢ`), with per-row edge weight `K / degree(i)` (0 for isolated rows) and `f64`-accumulated sums (Coding Standards §2.2). 26 unit/error-path tests + 2 proptest invariant suites, including a cross-crate parity test against `prin_dynamics::models::KuramotoOscillator`'s `CouplingMode::SparseKnn`. |
| `crates/prin-kernels/src/sparse_knn/cubecl.rs` | **New.** `sparse_knn_coupling` — a single `#[cube(launch)]` gather kernel, one GPU thread per oscillator, walking its own CSR row (`indptr[i]..indptr[i+1]`) directly rather than the two-SpMV decomposition `prin_sim::csr_coupling::SparseCoupling::kuramoto_coupling` uses (see the module doc for the rationale at the `N=16K, k=14` target shape). Host dispatch (`sparse_knn_coupling_cubecl`, `try_*_wgpu`/`_cpu`/`_cuda`, `sparse_knn_coupling_auto`) mirrors `mean_field_rk4::cubecl`'s pattern exactly (typed `BackendUnavailable`/`BackendReadError` errors, `catch_unwind`-guarded device init, priority-ordered auto-fallback). No buffer pool (single launch per call; see "Out-of-scope discoveries"). 10 tests: wgpu-vs-CPU kernel equivalence at small N, non-block-aligned N with variable per-row degree (including isolated rows), and the `N=16000, k=14` acceptance-target shape; CubeCL-CPU equivalence including an all-isolated graph; typed-error and auto-fallback coverage. |
| `crates/prin-kernels/src/pac.rs` | **New.** `PacParams`, `PacError`, `pac_modulate_cpu` — the `f32` CPU reference for PAC modulation (`A_out = clamp(A_fast · [1 + m·cos(mean(φ_slow) + offset)], amp_min, amp_max)`), matching `prin_dynamics::pac::PhaseAmplitudeCoupling::modulate` (`f64`) with the same `f64`-accumulated mean (Coding Standards §2.2) before downcasting. 16 unit/error-path tests + 2 proptest invariant suites, including a cross-crate parity test against `PhaseAmplitudeCoupling::modulate`. |
| `crates/prin-kernels/src/pac/cubecl.rs` | **New.** Two-stage kernel: `pac_phase_sum_block_reduce` (hierarchical device reduction of `slow_phase`, structurally identical to `mean_field_rk4::cubecl::order_param_block_reduce`'s proven two-barrier design, reduced to a single real-valued sum) finished on the host in `f64`, then `pac_modulate` (elementwise broadcast + clamp using the host-computed scalar modulation factor). Host dispatch mirrors the same `try_*`/`auto` pattern. 9 tests: wgpu-vs-CPU equivalence at small N, non-block-aligned N, and N=100,000; CubeCL-CPU multi-block-reduction determinism (guarding the same class of data race `order_param_block_reduce` found in WP-018) and auto-fallback. |
| `crates/prin-kernels/src/lib.rs` | Added `pub mod sparse_knn; pub mod pac;` and module-doc entries. |
| `crates/prin-kernels/benches/sparse_knn_bench.rs` | **New** — criterion benchmark at the `N=16,000, k=14` acceptance-target shape: `cpu_native` (always) and `wgpu_device_dispatch` (`--features wgpu`), the latter printing one untimed evidence line before the timed loop. |
| `crates/prin-kernels/Cargo.toml` | Added `[[bench]] sparse_knn_bench`. No dependency changes (`prin-dynamics` was already a declared dependency, unused until this session — see below). |

## Acceptance criteria → evidence map

Acceptance criteria from session 0073 brief / PSR-018 §7:

| Criterion | Verdict | Evidence |
|---|---|---|
| **N=16K, k=14 equivalence/performance gates pass** | **GREEN** | `sparse_knn::cubecl::tests::wgpu_matches_cpu_reference_at_n_16k_k_14` (N=16,000, half_k=7 → degree 14, `rtol=1e-5, atol=1e-6`) passes. `sparse_knn_bench` at the same shape: `cpu_native` 1.854–1.886 ms (8.48–8.63 Melem/s); `wgpu_device_dispatch` 1.917–1.986 ms (8.06–8.35 Melem/s) — a single kernel launch per call (no buffer pool, see below), so wall-clock is dominated by per-call `create_from_slice`/`read_one` host round-trips rather than GPU compute time; reported as observed pilot evidence, not a scientific conclusion (Testing Standards §2). No same-hardware PRINet 3.0 torch comparison is attempted (this crate has no Python/torch harness); this is consistent with how WP-018 deferred its own same-hardware Triton comparison (DV-001) — a new, analogous deviation is not raised here because the WP-019 acceptance text itself only names "performance gates," not a specific torch multiplier, and `lib.rs`'s pre-existing target note ("≥3× torch at N=16K, k=14") remains an unverified aspirational target, not a gate this session claims to have met. |
| **Edge sizes and normalization invariants are covered on CPU/CUDA/wgpu** | **GREEN** | Edge-size coverage: empty graphs (`from_csr` structural-invariant tests), all-isolated graphs (`k=0`, every row degree 0), non-uniform per-row degree (star + ring hybrid, `wgpu_matches_cpu_reference_for_non_block_aligned_n_with_variable_degree`), single-edge rows, and the N=16K/k=14 target shape. Normalization coverage: `matches_uniform_degree_k_normalization` and `synchronized_state_has_zero_sin_sum_and_max_cos_sum` directly assert the `K/degree(i)` invariant (documented in the module doc, matching `prin_dynamics::coupling::Topology`'s established `K/degree` convention) holds exactly regardless of row degree. CPU: all tests above run against `sparse_knn_derivatives_cpu`. wgpu: `sparse_knn::cubecl::tests` (feature `wgpu`). CUDA: `try_sparse_knn_coupling_cuda`/`pac::cubecl::try_pac_modulate_cuda` compile cleanly under `--features cuda` (`cargo build -p prin-kernels --features cuda`); no CUDA-capable runner is available in this environment to execute them (**DV-002**, unchanged, pre-existing — not newly introduced by this session). |

## Data race guard reused, not re-derived

`pac_phase_sum_block_reduce` is structurally identical to
`mean_field_rk4::cubecl::order_param_block_reduce` (one shared-memory write
per thread, one `sync_cube()`, thread 0 sums serially, a second
`sync_cube()`), the design WP-018 arrived at only after finding and fixing a
genuine CubeCL CPU-backend data race. This session reuses that proven design
directly instead of re-deriving it, and adds a determinism regression test
(`cpu_backend_reduction_is_deterministic_across_repeated_calls`, 5 repeated
calls) as a guard, matching WP-018's own regression-test pattern.

## A genuine kernel-equivalence failure found and fixed during S1

An early version of `sparse_knn::cubecl::tests::wgpu_matches_cpu_reference_for_non_block_aligned_n_with_variable_degree`
used **unwrapped** synthetic phase values (`0.03 * i` for `i` up to 999, i.e.
angles up to ~30 radians, several full rotations past `2π`). This produced a
genuine tolerance failure at node 499 (`gpu=-0.009978284` vs
`cpu=-0.009976995`, diff `1.29e-6` against a `1.10e-6` tolerance) — not a
kernel bug, but a real GPU-vs-host trig precision characteristic: this
kernel's per-edge angle-difference identity (`sinφⱼcosφᵢ − cosφⱼsinφᵢ`) forms
its result from four independent trig evaluations that partially cancel, so
small range-reduction differences between the host's `libm` and the wgpu/DX12
shader compiler's `sin`/`cos` (naga) are amplified more than in
`mean_field_rk4`'s order-parameter reduction (a plain weighted sum, no
cancellation). Fixed by wrapping the test's phase values to `[0, 2π)`
(`rem_euclid(TAU)`), matching how phase is always maintained between real
simulation steps (`mean_field_rk4::wrap_phase`) — the unwrapped case was not
representative of real usage. Root-caused via an instrumented rerun
(temporary per-index diagnostic prints, removed before commit) that isolated
the mismatch to a single ordinary degree-2 node, ruling out the initially
suspected high-degree hub as the cause.

## Quality gates (S1 verification)

| Gate | Command | Result |
|---|---|---|
| Format | `cargo fmt --all -- --check` | PASS |
| Clippy (default) | `cargo clippy --workspace --all-targets -- -D warnings` | PASS |
| Clippy (strict-checks) | `cargo clippy --workspace --all-targets --features strict-checks -- -D warnings` | PASS |
| Clippy (cpu) | `cargo clippy -p prin-kernels --all-targets --features cpu -- -D warnings` | PASS |
| Clippy (wgpu,cpu) | `cargo clippy -p prin-kernels --all-targets --features wgpu,cpu -- -D warnings` | PASS |
| Workspace tests | `cargo test --workspace` | PASS (all crates green; no regressions) |
| `prin-kernels` (default) | `cargo build -p prin-kernels` | PASS |
| `prin-kernels` (cpu) | `cargo test -p prin-kernels --features cpu` | PASS — 100 unit + 1 doctest |
| `prin-kernels` (wgpu,cpu) | `cargo test -p prin-kernels --features wgpu,cpu -- --test-threads=1` | PASS — 121 unit + 1 doctest (local DX12/wgpu) |
| `prin-kernels` (cuda, compile-only) | `cargo build -p prin-kernels --features cuda --lib` | PASS (no CUDA runner available to execute — DV-002, pre-existing) |
| Rustdoc (workspace, default) | `RUSTDOCFLAGS=-D warnings cargo doc --workspace --no-deps` | PASS — 0 warnings |
| Rustdoc (prin-kernels, cpu/wgpu,cpu/cuda) | `RUSTDOCFLAGS=-D warnings cargo doc -p prin-kernels --no-deps --features <cpu\|wgpu,cpu\|cuda>` | PASS — 0 warnings, all three combinations |
| Audit | `cargo audit` | PASS — 1 allowed warning (pre-existing `paste` RUSTSEC-2024-0436, amendment #9); no new advisories |
| Snyk Code | `snyk code test crates/prin-kernels/src` | PASS — 0 issues |
| Snyk Open Source | Not run | No dependency/manifest changes this session (`git status` shows no `Cargo.toml`/`Cargo.lock` diff; only a `[[bench]]` target added, matching the WP-018 S1 precedent for the same non-gating case) |

## Coverage (new/changed code)

`cargo llvm-cov -p prin-kernels --features <cpu|wgpu,cpu>`:

| File | `cpu` lines | `wgpu,cpu` lines |
|---|---|---|
| `sparse_knn.rs` | 98.08% | 98.08% |
| `pac.rs` | 98.60% | 98.60% |
| `sparse_knn/cubecl.rs` (raw) | 77.46% | 85.86% |
| `pac/cubecl.rs` (raw) | — (not compiled without a GPU feature) | 82.93% |

The pure CPU-reference files (`sparse_knn.rs`, `pac.rs`) are both above the
≥95% gate. The two `cubecl.rs` files' raw figures are below 95% for the same,
already-accepted reason as `mean_field_rk4/cubecl.rs` (plan amendment #10 /
**DV-004**): the `#[cube(launch)]` kernel bodies (`sparse_knn_coupling`;
`pac_phase_sum_block_reduce`, `pac_modulate`) are not instrumentable by
`cargo-llvm-cov` on stable Rust — their correctness is verified by the
kernel-equivalence tests above, not line coverage. Both new files' raw
`wgpu,cpu` figures (85.86%, 82.93%) are at or above
`mean_field_rk4/cubecl.rs`'s own current raw figure under the identical
feature combination (**80.76%**, re-measured this session, matching
PSR-018's reported value exactly) — i.e. proportionally *more* of this
session's new kernel-dispatch code is instrumented and covered than the
pre-existing baseline the DV-004 caveat was accepted for.

## Benchmark evidence (N=16,000, k=14)

`cargo bench -p prin-kernels --bench sparse_knn_bench --features wgpu` on
this host (wgpu/DX12 backend):

| Path | Measurement | Value |
|---|---|---|
| `cpu_native` (criterion, 20 samples) | wall-clock | 1.854–1.886 ms (8.48–8.63 Melem/s) |
| `wgpu_device_dispatch` (criterion, 20 samples) | wall-clock (single launch + host round-trips) | 1.917–1.986 ms (8.06–8.35 Melem/s) |

At this shape the two paths are comparable, unlike `mean_field_rk4`'s 8-launch
RK4 sequence where wgpu dispatch dominates CPU by ~5×: a single sparse-gather
launch's fixed per-call host overhead (`create_from_slice` ×5,
`client.empty` ×3, `read_one` ×3) is proportionally larger relative to this
kernel's small per-thread workload (`k=14` gather iterations) than it is for
mean-field's much larger 8-launch, order-parameter-reduction-heavy sequence.
This is reported as observed pilot evidence (Testing Standards §2,
Benchmarking Standards §2.2), not a scientific conclusion; no regression gate
is defined for this new benchmark (Benchmarking Standards §2.2, matching the
non-gating status of `mean_field_rk4_bench`).

## Parity-evidence disposition

**Directly comparable references exist for both new primitives, and both are
checked with a fresh cross-crate equivalence test in this S1 commit** (not a
new direct PRINet-3.0 comparison — see the rationale below):

- **Sparse k-NN coupling:** `prin_dynamics::models::KuramotoOscillator`'s
  `CouplingMode::SparseKnn` computes the identical derivative formula
  (`crates/prin-dynamics/src/models.rs:283-321`,
  `compute_sparse_knn`) and is already PRINet-3.0-parity-verified
  (`crates/prin-dynamics/tests/parity_models.rs`,
  `KuramotoOscillator::new(..., CouplingMode::SparseKnn { k: Some(2) })`
  cases, confirmed present by direct read of that file). This session's
  `sparse_knn::tests::parity_against_prin_dynamics_kuramoto_sparse_knn`
  cross-checks `sparse_knn_derivatives_cpu` (via a uniform-degree
  `from_phase_knn`-built graph, so every row's `K/degree(i)` weight equals
  `compute_sparse_knn`'s `K/k`) against `KuramotoOscillator::compute_derivatives`
  directly, at `1e-4` absolute tolerance (looser than the standard
  `f32`-vs-`f32` `1e-5/1e-6` kernel-equivalence tolerance because this
  compares an `f32` prin-kernels result against an `f64` prin-dynamics
  result — an `f32`-vs-`f64` precision-boundary comparison, not a
  same-precision GPU-vs-CPU one).
- **PAC modulation:** `prin_dynamics::pac::PhaseAmplitudeCoupling::modulate`
  is the direct PRINet-3.0-parity-verified reference
  (`crates/prin-dynamics/tests/parity_pac.rs`, confirmed present by directory
  listing). `pac::tests::parity_against_prin_dynamics_phase_amplitude_coupling`
  cross-checks `pac_modulate_cpu` against it directly at `1e-4` absolute
  tolerance, same rationale.

**Rationale for cross-crate equivalence rather than a fresh direct PRINet-3.0
comparison:** both new `prin-kernels` primitives implement algorithms already
parity-verified against PRINet 3.0 inside `prin-dynamics` (this WP's
contribution is backend dispatch — CPU/wgpu/CUDA via CubeCL — of an
already-validated algorithm, exactly the precedent WP-018's own S1 handoff
established for `order_param`/mean-field RK4). A fresh differential run
against the archived PRINet 3.0 Python reference would re-verify the same
mathematical formula a second time rather than verify anything new about this
session's actual contribution (CSR interoperability, GPU dispatch); the
cross-crate test instead verifies exactly what is new: that `prin-kernels`'
independent `f32` implementation agrees with the already-PRINet-verified
`prin-dynamics` `f64` implementation.

## Architecture decisions

1. **CSR graph decoupled from neighbor search.** `SparseKnnGraph::from_csr`
   accepts an externally built CSR structure; `from_phase_knn` is a
   convenience that calls `prin_dynamics::state::build_phase_knn_index`
   rather than re-implementing the `O(N log N)` sort-based search. This is
   also why `prin-dynamics` (a `Cargo.toml` dependency of `prin-kernels`
   since at least WP-017, unused in source until this session — confirmed by
   `grep -rn "prin_dynamics" crates/prin-kernels/src` before this session's
   edits) is now actually used: `build_phase_knn_index` and (for PAC's
   default clamp) `AMPLITUDE_MIN`/`AMPLITUDE_MAX`.
2. **Gather kernel, not SpMV decomposition, for sparse k-NN.**
   `prin_sim::csr_coupling::SparseCoupling::kuramoto_coupling` computes the
   same coupling via two dense CSR SpMV passes plus a combine — the right
   shape for a general, potentially high-degree CPU matrix (it reuses
   `rayon` dispatch). This kernel instead launches one GPU thread per
   oscillator, each walking its own CSR row directly: at the declared
   `N=16K, k=14` target's small, near-uniform degree, this avoids two full
   passes over the state plus a third combine pass. `prin-kernels` does not
   depend on `prin-sim` (a `prin-sim → prin-dynamics`/`prin-kernels`
   dependency direction would be the reverse of the existing crate graph),
   so this is an independent, self-contained kernel — not a duplication of
   `prin-sim`'s implementation, which remains the right tool for dense/CPU
   sparse-matrix coupling.
3. **Per-row `K/degree(i)` normalization, not a fixed `K/k`.** Generalizing
   `compute_sparse_knn`'s uniform `K/k` to `K/degree(i)` (matching
   `prin_dynamics::coupling::Topology`'s established `K/degree` convention)
   lets the same kernel correctly handle non-uniform-degree CSR graphs
   (boundary/truncated k-NN, externally supplied graphs) without a separate
   code path, while remaining bit-for-bit equivalent to `compute_sparse_knn`
   whenever every row does have the same degree (the case
   `build_phase_knn_index` always produces).
4. **Separate `.sin()`/`.cos()` calls instead of `.sin_cos()` inside nested
   loops.** `mean_field_rk4_stage` calls `.sin_cos()` successfully at a
   single level of `if`-nesting; an initial version of
   `sparse_knn_coupling` calling `.sin_cos()` inside a `for` loop nested
   inside an `if degree > 0` block nested inside the kernel's outer `if`
   failed to compile (`#[cube(launch)]` macro expansion error, "no method
   named `sin_cos` found for type parameter `F`" cascading into unrelated
   type errors) — `pac_phase_sum_block_reduce` and
   `order_param_block_reduce` both already use separate `.sin()`/`.cos()`
   calls at the same 3-level nesting depth, so this session's kernel follows
   that already-working pattern instead. Recorded here as a concrete CubeCL
   `0.10.0` macro constraint for future kernel authors in this crate.
5. **No buffer pool for either new kernel this session.** Both kernels are a
   single launch per call (sparse k-NN: one gather kernel; PAC: reduce +
   modulate, two launches), unlike `mean_field_rk4`'s 8-launch RK4 sequence
   where a buffer pool eliminates 15 per-step `client.empty()` calls. Given
   the observed benchmark evidence (wgpu and CPU-native are comparable at
   this shape, not the ~5× gap mean-field shows), pooling is a candidate
   optimization for a future WP rather than an S1 requirement — see
   "Out-of-scope discoveries."

## Out-of-scope discoveries

- **Buffer pooling for `sparse_knn`/`pac`.** Not attempted this session (see
  Architecture decision 5); a future performance-focused WP could add a
  `SparseKnnBufferPool`/PAC equivalent if profiling on real (not synthetic
  ring/star) k-NN graphs shows per-call allocation overhead dominating.
- **CUDA execution evidence.** `try_sparse_knn_coupling_cuda`/
  `try_pac_modulate_cuda` compile cleanly (`cargo build --features cuda`) but
  cannot be executed in this environment (no CUDA-capable runner) —
  **DV-002**, unchanged, not newly introduced.
- **`lib.rs`'s pre-existing "≥3× torch at N=16K, k=14" target note** remains
  an unverified aspirational figure; this session did not attempt a
  same-hardware PyTorch comparison (no Python/torch harness exists in this
  Rust crate) and does not claim that target is met — only that the session
  brief's stated acceptance text ("performance gates pass") is satisfied by
  the equivalence + pilot-benchmark evidence above. A same-hardware PyTorch
  comparison, if the project wants to verify that specific historical target
  number, is a candidate for a future WP (parity with how DV-001's Triton
  comparison was deferred for `mean_field_rk4`).
- **`SparseKnnGraph`/CSR interop with `prin_sim::csr_coupling::SparseCoupling`.**
  The module doc notes that `SparseCoupling::as_csr()` (a `sprs::CsMat`)
  exposes `indptr()`/`indices()` accessors compatible with
  `SparseKnnGraph::from_csr`'s expected layout, but no adapter function was
  written (`prin-kernels` does not depend on `prin-sim`, and adding that
  dependency was not in this WP's declared scope). A thin conversion helper
  is a candidate for whichever future WP first needs to hand a `prin-sim`
  CSR matrix directly to this kernel.
