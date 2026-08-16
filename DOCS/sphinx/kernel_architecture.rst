Kernel Architecture
===================

PRIN replaces PRINet 3.0's three separate kernel implementations
(`utils/triton_kernels.py`, `utils/cuda_kernels.py`,
`utils/fused_kernels.py`) with a single-source CubeCL kernel set that
compiles to CUDA, Metal, Vulkan, and CPU SIMD at wheel-build time — no
runtime nvcc/MSVC JIT.

Design rule: **one algorithm, one implementation.** Backend dispatch
(CPU native / CubeCL CPU / wgpu / CUDA) lives inside `prin-kernels`; no
math is duplicated at call sites.

WP-017 — kernel architecture and CPU references
-----------------------------------------------

`prin-kernels` now contains the production kernel architecture and the
first fully validated kernel:

- **Backend abstraction** (`crates/prin-kernels/src/backend.rs`):
  `Device` enum (`Cuda`, `Wgpu`, `Cpu`), `BackendError`,
  `backend_priority`, and `auto_detect_order`. Callers try backends in
  priority order; the fastest available one wins.
- **Preallocated buffer pools** (`crates/prin-kernels/src/buffers.rs`):
  `MeanFieldRk4Buffers` for CPU and `CubeclBufferPool<R: Runtime>` for
  CubeCL GPU. Both expose `capacity()` and are validated against the
  call-site oscillator count, so a pool sized for one ``N`` cannot be
  silently reused at a different ``N``.
- **CPU reference** (`crates/prin-kernels/src/mean_field_rk4.rs`):
  `step_cpu` and `step_cpu_with_pool` are bit-identical; the pooled
  variant reuses 18 ``Vec<f32>`` buffers to avoid per-step allocations.
  `order_param` is the single authoritative mean-field order-parameter
  implementation used by both CPU and GPU paths.
- **CubeCL dispatch** (`crates/prin-kernels/src/mean_field_rk4/cubecl.rs`):
  single-source `#[cube(launch)]` kernels; runtime entry points
  `try_step_wgpu`, `try_step_cpu`, `try_step_cuda`; pooled
  `step_cubecl_with_pool`; and automatic `step_auto` dispatch with
  graceful fallback to the native CPU reference.
- **Equivalence harness** (`crates/prin-kernels/src/equivalence.rs`):
  `EquivalenceHarness` and `EquivalenceCase` generate deterministic
  cross-backend test cases and compare GPU results against the CPU
  reference at ``rtol=1e-5, atol=1e-6``.

Validation
----------

- ``cargo test -p prin-kernels --features cpu`` runs the CPU reference,
  buffer-pool, and CubeCL-CPU kernel-equivalence tests on every CI
  platform.
- ``cargo test -p prin-kernels --features wgpu,cpu -- --test-threads=1``
  runs the real wgpu kernel-equivalence tests at ``N=64`` and
  ``N=1,000,000`` against the CPU reference.
- ``cargo test -p prin-kernels --features cuda,cpu`` runs the CUDA path
  on a self-hosted CUDA runner.
- Property tests cover phase wrap, amplitude clamp, zero-coupling
  identity, RK4 local-error scaling, order-parameter bounds, and pool-size
  mismatch rejection.
- Coverage is measured with ``cargo llvm-cov -p prin-kernels --features
  cpu``. The ``#[cube(launch)]`` kernel bodies in `cubecl.rs` are
  non-instrumentable on stable Rust (plan amendment #10 / DV-004); the
  surrounding instrumentable code is at or above the 95% gate.

WP-018 — fused mean-field RK4 kernel
-------------------------------------

WP-018 productionized the mean-field RK4 kernel with a hierarchical
device-side reduction and real device-event timing:

- **Hierarchical device-side order-parameter reduction**
  (`crates/prin-kernels/src/mean_field_rk4/cubecl.rs`): a new
  `order_param_block_reduce` `#[cube(launch)]` kernel reduces each
  256-thread cube block's slice of ``amp[i]*e^{i*phase[i]}`` into one
  ``(real, imag)`` partial via shared memory; the host-side
  `order_param_device` helper finishes the reduction over
  ``ceil(N/256)`` partials with an ``f64`` accumulator. This replaces
  the prior ``O(N)`` full-state host read-back with an ``O(N/256)``
  partial read-back. `CubeclBufferPool` gained `block_real`/`block_imag`
  device handles sized to `num_blocks_for(n)` and a `num_blocks()`
  accessor.
- **`order_param` f64 accumulation**: the single authoritative
  CPU/GPU-shared reduction in `mean_field_rk4.rs` now accumulates in
  ``f64`` before the final normalization and ``f32`` downcast, matching
  the GPU path's host-side combine (Coding Standards §2.2).
- **Device-event timing**: `step_cubecl_with_pool` wraps its 8-launch
  sequence in `ComputeClient::profile`. The new `TimingMethod` enum
  (`Device`/`System`) and `StepReport::timing_method` field report
  whether the measurement is real hardware device timestamps (wgpu) or
  a host wall-clock fallback (CubeCL-CPU), replacing the WP-004/WP-017
  wall-clock-only prototype (partially closes DV-003).
- A CubeCL CPU-backend data race in an early `order_param_block_reduce`
  draft (missing second ``sync_cube()`` barrier) was found and fixed
  during S1, with a regression test.

Evidence: `DOCS/audits/018-wp018-audit.md` (verdict PASS, zero
findings); N=1,000,000 kernel-equivalence and benchmark evidence in
`DOCS/experiments/0069-wp018-s1-handoff.md`.

WP-019 — sparse k-NN and PAC kernels
--------------------------------------

WP-019 added the sparse phase-neighbor coupling and PAC modulation
kernels, continuing the WP-017/WP-018 single-source CubeCL architecture:

- **Sparse k-NN coupling**
  (`crates/prin-kernels/src/sparse_knn.rs`): ``SparseKnnGraph`` — a CSR
  (``indptr``/``indices``, both ``u32``) sparse phase-neighbor graph
  with ``from_csr`` (accepts an externally built CSR structure —
  CSR/index interoperability) and ``from_phase_knn`` (builds from a
  phase array and ``k``, reusing
  ``prin_dynamics::state::build_phase_knn_index``'s sort-based neighbor
  search). ``sparse_knn_derivatives_cpu`` — the CPU reference computing
  the Kuramoto-style sparse coupling derivative per row via the
  angle-difference trig identity, with per-row edge weight
  ``K/degree(i)`` and ``f64``-accumulated sums.
- **Sparse k-NN CubeCL kernel**
  (`crates/prin-kernels/src/sparse_knn/cubecl.rs`):
  ``sparse_knn_coupling`` — a single ``#[cube(launch)]`` gather kernel,
  one GPU thread per oscillator, walking its own CSR row directly
  rather than the two-SpMV decomposition ``prin_sim::csr_coupling``
  uses (a deliberate design choice for the ``N=16K, k=14`` target
  shape). Host dispatch mirrors ``mean_field_rk4::cubecl``'s pattern.
- **PAC modulation**
  (`crates/prin-kernels/src/pac.rs`): ``PacParams``, ``PacError``,
  ``pac_modulate_cpu`` — the ``f32`` CPU reference for PAC modulation
  (``A_out = clamp(A_fast · [1 + m·cos(mean(φ_slow) + offset)],
  amp_min, amp_max)``), matching ``prin_dynamics::pac`` with
  ``f64``-accumulated mean before downcasting.
- **PAC CubeCL kernel**
  (`crates/prin-kernels/src/pac/cubecl.rs`): two-stage kernel —
  ``pac_phase_sum_block_reduce`` (hierarchical device-side reduction of
  ``slow_phase``, structurally identical to
  ``order_param_block_reduce``'s proven two-barrier design) finished on
  the host in ``f64``, then ``pac_modulate`` (elementwise broadcast +
  clamp).
- **Benchmark**
  (`crates/prin-kernels/benches/sparse_knn_bench.rs`): criterion
  benchmark at the ``N=16,000, k=14`` acceptance-target shape.

Evidence: `DOCS/audits/019-wp019-audit.md` (verdict PASS-WITH-FINDINGS,
one D4 finding FIXED in S3); N=16K/k=14 equivalence and benchmark
evidence in `DOCS/experiments/0073-wp019-s1-handoff.md`.

Future work (WP-020..WP-021)
----------------------------

The Phase 3 work continues with:

- Fused discrete step (phase advance + PAC gating + Stuart–Landau in one
  launch).

Rust API reference for `prin-kernels` is published on `docs.rs
<https://docs.rs/prin-kernels/latest/prin_kernels/>`_.
