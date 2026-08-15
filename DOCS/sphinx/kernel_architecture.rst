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

Future work (WP-018..WP-021)
----------------------------

The mean-field RK4 pattern is extended in the remaining Phase 3 work
packages:

- Hierarchical device-side order-parameter reductions (replacing the host
  reductions used in the current implementation).
- Sparse k-NN coupling.
- PAC modulation.
- Fused discrete step (phase advance + PAC gating + Stuart–Landau in one
  launch).

Rust API reference for `prin-kernels` is published on `docs.rs
<https://docs.rs/prin-kernels/latest/prin_kernels/>`_.
