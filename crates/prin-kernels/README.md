# prin-kernels

Single-source fused kernels for PRIN (CubeCL: CUDA / Metal / Vulkan / CPU SIMD),
replacing PRINet 3.0's triple implementation
(`utils/triton_kernels.py`, `utils/cuda_kernels.py`, `utils/fused_kernels.py`).

Kernels: fused mean-field RK4, sparse k-NN coupling, PAC, fused discrete step,
hierarchical reductions. All precompiled at wheel-build time — no runtime
nvcc/MSVC JIT.

Feature flags: `cpu` (CubeCL CPU runtime, headless/CI-friendly), `cuda`, `wgpu`.
Kernel-equivalence tests compare every GPU/CPU kernel against the CPU reference
across shapes and dtypes.

## Phase 3 — WP-017: Kernel architecture and CPU references

`prin-kernels` now has the production kernel architecture in place:

- [`src/backend.rs`](src/backend.rs) — `Device` enum (`Cuda`, `Wgpu`, `Cpu`),
  `BackendError`, `backend_priority`, and `auto_detect_order`.
  Preference is decoupled from availability: callers try backends in priority
  order and fall through to the next available one.
- [`src/buffers.rs`](src/buffers.rs) — preallocated buffer pools.
  - `MeanFieldRk4Buffers` — 18 reusable CPU `Vec<f32>` buffers for the RK4
    intermediates, stage state, and output.
  - `CubeclBufferPool<R: Runtime>` — 18 reusable CubeCL device `Handle`s for
    the GPU path.
  - Both pools expose `capacity()` and are validated against the call-site
    oscillator count so a pool sized for one `N` cannot be silently reused at
    a different `N`.
- [`src/mean_field_rk4.rs`](src/mean_field_rk4.rs) — CPU reference and the
  single authoritative `order_param` implementation.
  - `MeanFieldRk4Params` / `MeanFieldRk4Error` / `MeanFieldRk4Output`.
  - `step_cpu` — one-shot CPU RK4 step.
  - `step_cpu_with_pool` — pooled CPU step; bit-identical to `step_cpu`.
  - The CPU reference is the numerical authority for all GPU paths.
- [`src/mean_field_rk4/cubecl.rs`](src/mean_field_rk4/cubecl.rs) — single-source
  CubeCL GPU kernels.
  - `step_cubecl` / `step_cubecl_with_pool` — one-shot or pooled CubeCL step.
  - `try_step_wgpu` / `try_step_cpu` / `try_step_cuda` — runtime-specific
    entry points.
  - `step_auto` — automatic backend selection in `auto_detect_order` priority
    (wgpu → cuda → CubeCL CPU), falling back to native `step_cpu` if no
    CubeCL backend is available.
  - `StepReport` — backend name, host wall-clock time, and launch count
    (device-event timing is still a Phase 3 optimization, DV-003).
- [`src/equivalence.rs`](src/equivalence.rs) — `EquivalenceHarness`,
  `EquivalenceCase`, and `assert_allclose` for cross-backend testing.
  The CPU reference is the authority; GPU outputs are compared at
  `rtol=1e-5, atol=1e-6`.
- [`src/ops.rs`](src/ops.rs) — element-wise utility kernels from the Phase 0
  DLPack bridge spike.

Design rule: **one algorithm, one implementation.** Backend dispatch
(CPU native / CubeCL CPU / wgpu / CUDA) happens inside this crate, never by
duplicating math at call sites.

## Phase 3 — WP-018: Fused mean-field RK4 kernel

WP-018 productionized the mean-field RK4 kernel with hierarchical device-side
reductions and real device-event timing:

- **Hierarchical device-side order-parameter reduction** — a new
  `order_param_block_reduce` `#[cube(launch)]` kernel reduces each 256-thread
  cube block's slice of `amp[i]*e^{i*phase[i]}` into one `(real, imag)`
  partial via shared memory; `order_param_device` finishes the reduction over
  `ceil(N/256)` partials on the host with an `f64` accumulator. This replaces
  the prior `O(N)` full-state host read-back with an `O(N/256)` partial
  read-back. `CubeclBufferPool` gained `block_real`/`block_imag` handles sized
  to `num_blocks_for(n)` and a `num_blocks()` accessor.
- **`order_param` f64 accumulation** — the single authoritative CPU/GPU-shared
  reduction now accumulates in `f64` before normalization (Coding Standards
  §2.2), matching the GPU path's host-side combine.
- **Device-event timing** — `step_cubecl_with_pool` wraps its 8-launch
  sequence in `ComputeClient::profile`. The new `TimingMethod` enum
  (`Device`/`System`) and `StepReport::timing_method` field report whether the
  measurement is real hardware device timestamps (wgpu) or a host wall-clock
  fallback (CubeCL-CPU), replacing the WP-004/WP-017 wall-clock-only
  prototype.
- A CubeCL CPU-backend data race (missing second `sync_cube()` barrier,
  letting idle worker threads race into the next cube block's shared memory)
  was found and fixed during S1, with a regression test.

Evidence: `DOCS/audits/018-wp018-audit.md` (verdict `PASS`, zero findings);
`DOCS/experiments/0069-wp018-s1-handoff.md`.

## Validation

- `cargo test -p prin-kernels --features cpu` runs CPU reference, buffer-pool,
  and CubeCL-CPU kernel-equivalence tests on every CI platform.
- `cargo test -p prin-kernels --features wgpu,cpu -- --test-threads=1` runs the
  real wgpu kernel-equivalence tests at N=64 and N=1M against the CPU reference
  (`rtol=1e-5, atol=1e-6`).
- `cargo test -p prin-kernels --features cuda,cpu` runs the CUDA path where a
  self-hosted CUDA runner is available.
- Property tests (`proptest`) cover phase wrap, amplitude clamp,
  zero-coupling identity, RK4 local-error scaling, order-parameter bounds, and
  pool-size-mismatch rejection.
- Coverage is measured with `cargo llvm-cov -p prin-kernels --features cpu`.
  The `#[cube(launch)]` kernel bodies in `cubecl.rs` are non-instrumentable on
  stable Rust (plan amendment #10 / DV-004); the surrounding instrumentable
  code is ≥95% covered.

## Future work

The full production suite continues in WP-019..WP-021:

- Sparse k-NN coupling kernel.
- PAC modulation kernel.
- Fused discrete step (phase advance + PAC gating + Stuart–Landau in one
  launch).

Rust API reference for `prin-kernels` is published on
[docs.rs](https://docs.rs/prin-kernels/latest/prin_kernels/).
