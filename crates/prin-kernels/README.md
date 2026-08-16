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

## Phase 3 — WP-019: Sparse k-NN and PAC kernels

WP-019 added the sparse phase-neighbor coupling and PAC modulation kernels:

- **Sparse k-NN coupling** ([`src/sparse_knn.rs`](src/sparse_knn.rs)):
  `SparseKnnGraph` — a CSR (`indptr`/`indices`, both `u32`) sparse
  phase-neighbor graph with two constructors: `from_csr` (accepts an
  externally built CSR structure — CSR/index interoperability) and
  `from_phase_knn` (builds from a phase array and `k`, reusing
  `prin_dynamics::state::build_phase_knn_index`'s sort-based neighbor
  search). `sparse_knn_derivatives_cpu` — the CPU reference computing
  the Kuramoto-style sparse coupling derivative per row via the
  angle-difference trig identity, with per-row edge weight `K/degree(i)`
  and `f64`-accumulated sums.
- **Sparse k-NN CubeCL kernel** ([`src/sparse_knn/cubecl.rs`](src/sparse_knn/cubecl.rs)):
  `sparse_knn_coupling` — a single `#[cube(launch)]` gather kernel, one
  GPU thread per oscillator, walking its own CSR row directly. Host
  dispatch (`sparse_knn_coupling_cubecl`, `try_*_wgpu`/`_cpu`/`_cuda`,
  `sparse_knn_coupling_auto`) mirrors `mean_field_rk4::cubecl`'s pattern.
- **PAC modulation** ([`src/pac.rs`](src/pac.rs)):
  `PacParams`, `PacError`, `pac_modulate_cpu` — the `f32` CPU reference
  for PAC modulation (`A_out = clamp(A_fast · [1 + m·cos(mean(φ_slow) +
  offset)], amp_min, amp_max)`), matching `prin_dynamics::pac` with
  `f64`-accumulated mean before downcasting.
- **PAC CubeCL kernel** ([`src/pac/cubecl.rs`](src/pac/cubecl.rs)):
  Two-stage kernel: `pac_phase_sum_block_reduce` (hierarchical
  device-side reduction of `slow_phase`, structurally identical to
  `order_param_block_reduce`'s proven two-barrier design) finished on
  the host in `f64`, then `pac_modulate` (elementwise broadcast + clamp).
- **Benchmark** ([`benches/sparse_knn_bench.rs`](benches/sparse_knn_bench.rs)):
  criterion benchmark at the `N=16,000, k=14` acceptance-target shape.

Evidence: `DOCS/audits/019-wp019-audit.md` (verdict `PASS-WITH-FINDINGS`,
one D4 finding, FIXED in S3); `DOCS/experiments/0073-wp019-s1-handoff.md`.

## Phase 3 — WP-020: Fused discrete step and reductions

WP-020 added the fused three-band (delta/theta/gamma) discrete-time step
kernel and reusable hierarchical order-parameter reductions:

- **Fused discrete step CPU reference**
  ([`src/discrete_step.rs`](src/discrete_step.rs)):
  `discrete_step_cpu` — the CPU reference (numerical authority) for the
  fused three-band discrete-time stepper. Reproduces the PRINet 3.0
  `DeltaThetaGammaNetwork` discrete-time stepper semantics: step delta
  via one Euler evaluation, gate theta's amplitude with the PAC modulation
  factor computed from delta's just-stepped mean phase, step theta, gate
  gamma from theta's just-stepped mean phase, step gamma. Reuses
  `mean_field_rk4::mean_field_derivatives_into`/`wrap_phase`/`clamp_amp`
  (promoted from private to `pub(crate)`) for the per-band
  Kuramoto/Stuart–Landau derivative and Euler update (Coding Standards §1,
  "one algorithm, one implementation").
- **Fused discrete step CubeCL kernel**
  ([`src/discrete_step/cubecl.rs`](src/discrete_step/cubecl.rs)):
  Four `#[cube(launch)]` kernels — `complex_order_reduce` (hierarchical
  block-reduce of a band's order parameter, called 3× — once per band),
  `real_sum_reduce` (hierarchical block-reduce for a PAC pair's slow-phase
  mean, called 2× — once per PAC pair), `band_euler_step` (fused
  per-oscillator phase-advance + Stuart–Landau amplitude update, called
  3×), and `pac_gate` (elementwise PAC broadcast+clamp, called 2×) —
  complete the 10-launch fused path. Host dispatch
  (`discrete_step_cubecl`, `try_*_wgpu`/`_cpu`/`_cuda`,
  `discrete_step_auto`) mirrors `mean_field_rk4::cubecl`'s pattern with
  `StepReport` device-event timing.
- **Benchmark**
  ([`benches/discrete_step_bench.rs`](benches/discrete_step_bench.rs)):
  criterion benchmark comparing the fused step against a hand-composed
  unfused baseline at band sizes `[4096, 16384, 65536]` (N=86,016).
  Observed ~3.7–3.8× speedup (fused ~2.1 ms vs. unfused ~7.9 ms on CPU
  native).
- 29 new tests (15 CPU unit/error-path + 2 proptests + 12 CubeCL) in S1.
  Kernel-equivalence at small N, non-block-aligned bands, and large N
  (65,536-oscillator gamma band, N=84,992 total) pass at `rtol=1e-5,
  atol=1e-6`.

Evidence: `DOCS/audits/020-wp020-audit.md` (verdict `PASS`, zero S2
findings; one self-discovered D4 WP020-F1 FIXED in S3);
`DOCS/experiments/0077-wp020-s1-handoff.md`.

## Phase 3 — WP-021: GPU integration and Phase 3 gate

WP-021 completed the GPU kernel suite, integrated kernel dispatch into `prin-sim`,
and locked regression baselines:

- **Dispatch-priority bug fix** — Corrected `*_auto` functions (`mean_field_rk4`,
  `discrete_step`, `pac`, `sparse_knn`) to try CUDA before wgpu, aligning runtime
  priority with `backend::auto_detect_order()` and documented priority order (CUDA → wgpu → CPU).
  Added priority regression tests.
- **Hardware CUDA execution and kernel equivalence** — Exercised real CUDA hardware
  (NVIDIA GeForce RTX 4060, CUDA 13.2) across all four kernel families. 113 `prin-kernels`
  CUDA tests pass at `rtol=1e-5, atol=1e-6` against CPU references:
  - Mean-field RK4 at $N=64$ and $N=1{,}000{,}000$.
  - Discrete step at multi-block $[600, 600, 600]$.
  - PAC modulation at $N=600$.
  - Sparse k-NN coupling at $N=300, k=6$.
- **Simulation layer integration** — Integrated with `prin-sim::gpu` (`GpuSparseKuramoto`,
  `GpuMeanFieldEngine`, `GpuBandStepper`).
- **Phase 3 Exit Gate** — All 5 Phase 3 work packages (WP-017 through WP-021) are
  complete with clean audits.

Evidence: `DOCS/audits/021-wp021-audit.md` (verdict `PASS-WITH-FINDINGS`, one D4 finding
WP021-F1 FIXED in S3); `DOCS/experiments/0081-wp021-s1-handoff.md`.

## Roadmap Progression

Phase 3 (GPU kernels) is complete. Phase 4 begins with WP-022:
- Trainable bands and resonance primitives (`prin-train`, Burn-based differentiable layers).

Rust API reference for `prin-kernels` is published on
[docs.rs](https://docs.rs/prin-kernels/latest/prin_kernels/).
