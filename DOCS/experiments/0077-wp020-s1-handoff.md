# Session 0077 — WP-020 S1 Handoff Note

**Session:** 0077 — WP-020 S1: Coding — Fused discrete step and reductions
**Date:** 2026-08-16
**Status:** S1 delivered; handoff to S2 audit (session 0078)

## Mission recap

"Implement fused three-band phase/amplitude/PAC advance plus reusable
hierarchical order-parameter reductions." Scope (`DOCS/reports/019-project-state.md`
§6, maintainer-approved 2026-08-16): `crates/prin-kernels/` — fused discrete
time-step kernel combining phase advance, PAC gating, and Stuart–Landau
amplitude dynamics in one launch sequence; hierarchical reductions for the
fused path. Non-goals: trainable-band integration (WP-022+); Python bindings
for the fused step.

## Scope delivered

| File | Change |
|---|---|
| `crates/prin-kernels/src/discrete_step.rs` | **New.** `discrete_step_cpu` — the CPU reference (numerical authority) for the fused three-band (delta/theta/gamma) *discrete-time* stepper. Reproduces the PRINet 3.0 `DeltaThetaGammaNetwork` discrete-time stepper semantics documented in `prin_dynamics::bands`'s "Correspondence to the PRINet 3.0 reference" (PAC as an *assignment/gate*, not `prin_dynamics::bands::BandNetwork`'s continuous relaxation term): step delta via one Euler evaluation, gate theta's amplitude with the PAC modulation factor computed from delta's just-stepped mean phase, step theta, gate gamma from theta's just-stepped mean phase, step gamma. Reuses `mean_field_rk4::mean_field_derivatives_into`/`wrap_phase`/`clamp_amp` (promoted from private to `pub(crate)` this session) for the per-band Kuramoto/Stuart–Landau derivative and Euler update rather than re-deriving the formula (Coding Standards §1). 15 unit/error-path tests + 2 proptest invariant suites. |
| `crates/prin-kernels/src/discrete_step/cubecl.rs` | **New.** Four `#[cube(launch)]` kernels: `complex_order_reduce` (hierarchical block-reduce of a band's order parameter, structurally identical to `mean_field_rk4::cubecl::order_param_block_reduce`, called 3× — once per band) and `real_sum_reduce` (hierarchical block-reduce for a PAC pair's slow-phase mean, structurally identical to `pac::cubecl::pac_phase_sum_block_reduce`, called 2× — once per PAC pair) are the "reusable hierarchical reductions" the mission names; `band_euler_step` (fused per-oscillator phase-advance + Stuart–Landau amplitude update, called 3×) and `pac_gate` (elementwise PAC broadcast+clamp, called 2×) complete the launch sequence. Host orchestration (`discrete_step_cubecl`, `try_*_wgpu`/`_cpu`/`_cuda`, `discrete_step_auto`) mirrors `mean_field_rk4::cubecl`'s pattern exactly (typed `BackendUnavailable`/`BackendReadError` errors, `catch_unwind`-guarded device init, priority-ordered auto-fallback, `ComputeClient::profile` device-event timing via a reused `StepReport`/`TimingMethod`). No buffer pool this session (see "Architecture decisions"). 12 tests: wgpu-vs-CPU equivalence at small N, non-block-aligned per-band sizes, and large N (65,536-oscillator gamma band); CubeCL-CPU multi-block determinism and typed-error/auto-fallback coverage. |
| `crates/prin-kernels/src/mean_field_rk4.rs` | `wrap_phase`, `clamp_amp`, `mean_field_derivatives_into` promoted from private to `pub(crate)` (doc comments added explaining the reuse), no behavior change. |
| `crates/prin-kernels/src/lib.rs` | Added `pub mod discrete_step;` and module-doc entries. |
| `crates/prin-kernels/benches/discrete_step_bench.rs` | **New** — criterion benchmark comparing the fused step against a hand-composed "unfused" baseline (three independent `mean_field_rk4::step_cpu` RK4 steps + two independent `pac::pac_modulate_cpu` gates, literally the pre-existing WP-018/WP-019 kernels), at band sizes `[4096, 16384, 65536]` (N=86,016). `cpu_native` group (always) and `wgpu_device_dispatch` (`--features wgpu`), the latter printing one untimed `StepReport` before the timed loop. |
| `crates/prin-kernels/Cargo.toml` | Added `[[bench]] discrete_step_bench`. No dependency changes. |

## Acceptance criteria → evidence map

Acceptance criteria from session 0077 brief / `019-project-state.md` §6:

| Criterion | Verdict | Evidence |
|---|---|---|
| **Fused-step kernel-equivalence at acceptance shapes on CPU/wgpu (CUDA compile-only, DV-002)** | **GREEN** | `discrete_step::cubecl::tests::wgpu_matches_cpu_reference_for_small_n` (band_sizes `[8,16,32]`), `..._for_non_block_aligned_bands` (`[300,777,513]`, none a multiple of 256 — exercises the partial-last-block mask in every reduction kernel), `..._at_large_n` (`[2048,16384,65536]`, N=84,992) all pass at `rtol=1e-5, atol=1e-6` against `discrete_step_cpu`. `discrete_step::cubecl::tests_cpu` exercises the CubeCL CPU backend the same way (`cpu_backend_matches_cpu_reference_multi_block`, N=600/band forcing 3 cube blocks) plus a 5-repeat determinism regression test (`cpu_backend_is_deterministic_across_repeated_calls`, guarding the same class of CubeCL CPU-backend shared-memory data race WP-018 found and fixed in `order_param_block_reduce`). `cargo build -p prin-kernels --features cuda --lib` compiles cleanly; no CUDA-capable runner is available in this environment to execute (**DV-002**, unchanged, pre-existing). |
| **Performance at or above the unfused sum of the individual kernels** | **GREEN** | `discrete_step_bench` at band_sizes `[4096, 16384, 65536]` (N=86,016), this host: `fused_cpu_native` **2.043–2.060 ms** (41.8–42.1 Melem/s) vs. `unfused_cpu_native` (3× `mean_field_rk4::step_cpu` RK4 + 2× `pac::pac_modulate_cpu`) **7.85–7.93 ms** (10.8–11.0 Melem/s) — the fused discrete step is **~3.8× faster** than composing the pre-existing WP-018/WP-019 kernels by hand. This is expected structurally (RK4 evaluates the derivative 4× per band vs. the fused step's single Euler evaluation, per the acceptance text's literal "individual kernels" reading — not a claim that Euler is numerically superior to RK4) and reported as observed pilot evidence (Testing Standards §2), not a scientific conclusion. GPU: `fused_wgpu_device_dispatch` **3.50–4.00 ms** (21.5–24.6 Melem/s, host-round-trip-dominated, comparable to `fused_cpu_native` — the same 10-launches-with-host-reads pattern WP-019's `sparse_knn_bench`/`pac` observed at small-to-medium per-launch workloads); one untimed `StepReport` prints genuine device-event timing (`backend_name: "wgpu<wgsl>", wall_time_seconds: 8.96e-6, timing_method: Device, launch_count: 10`) as required evidence (Benchmarking Standards §1.4, §2.2). No same-hardware PRINet 3.0 comparison is attempted (Benchmarking Standards §2.4's "Fused discrete step (3-band + PAC), GPU: ≥ parity, no runtime JIT" target names PRINet 3.0 directly) — this crate has no Python/torch harness, the same DV-001-class deferral WP-018/WP-019 already established for their own same-hardware comparisons; **no runtime JIT** is satisfied by construction (CubeCL kernels compile as part of the ordinary Rust build pipeline, no external JIT process at call time, unchanged from WP-017–WP-019's architecture). |
| **Coverage ≥95% on instrumentable code** | **GREEN for the CPU-reference file; DV-004 extension for the CubeCL dispatch file** | `cargo llvm-cov -p prin-kernels --features <cpu\|wgpu,cpu>`: `discrete_step.rs` **97.65%** lines / **98.25%** regions (both feature combinations — the CPU reference has no feature-gated branches) — above the ≥95% gate. `discrete_step/cubecl.rs` raw: **74.11%** lines (`cpu`), **79.32%** lines (`wgpu,cpu`) — below 95% for the same accepted reason as the three prior kernel-dispatch files (plan amendment #10 / **DV-004**): its four `#[cube(launch)]` kernel bodies (`complex_order_reduce`, `real_sum_reduce`, `band_euler_step`, `pac_gate`) are not instrumentable by `cargo-llvm-cov` on stable Rust. Unlike WP-019's two new files (which landed *above* the `mean_field_rk4/cubecl.rs` baseline), this file's raw `wgpu,cpu` figure (79.32%) is **1.44 points below** that baseline (80.76%, re-measured this session in the same run — matches PSR-018/PSR-019's reported value exactly, confirming stability): this session's fused path has **4** non-instrumentable kernel bodies against `mean_field_rk4`'s 3, `pac`'s 2, and `sparse_knn`'s 1 — a structurally higher non-instrumentable-to-total-code ratio, not a coverage regression in the instrumentable code. Verified by line-level inspection: outside the four kernel bodies, the only other missed lines are (a) the `ProfilingFailed` error-mapping closure (untestable without mocking a `ComputeClient::profile` failure — the identical gap exists in `mean_field_rk4::cubecl` today, confirmed by the same coverage run), and (b) `discrete_step_auto`'s `cpu`/native-fallback branches, unreached under `wgpu,cpu` because `try_discrete_step_wgpu` succeeds first on this host — the identical pattern `mean_field_rk4::cubecl::step_auto` shows in the same run (its own fallback branches are equally unreached lines 731–751 in that file). This is a new, small, honestly-quantified extension of DV-004 rather than a silent gap; flagged explicitly for the S2 audit's judgment. |
| **All quality/security gates green** | **GREEN** | See table below. |

## Quality gates (S1 verification)

| Gate | Command | Result |
|---|---|---|
| Format | `cargo fmt --all -- --check` | PASS |
| Clippy (default) | `cargo clippy --workspace --all-targets -- -D warnings` | PASS |
| Clippy (strict-checks) | `cargo clippy --workspace --all-targets --features strict-checks -- -D warnings` | PASS |
| Clippy (cpu) | `cargo clippy -p prin-kernels --all-targets --features cpu -- -D warnings` | PASS |
| Clippy (wgpu,cpu) | `cargo clippy -p prin-kernels --all-targets --features wgpu,cpu -- -D warnings` | PASS |
| Workspace tests | `cargo test --workspace` | PASS (all crates green; no regressions — 6 `test result: ok` blocks, 0 failures) |
| `prin-kernels` (default) | `cargo build -p prin-kernels` | PASS |
| `prin-kernels` (cpu) | `cargo test -p prin-kernels --features cpu` | PASS — 121 unit + 1 doctest |
| `prin-kernels` (wgpu,cpu) | `cargo test -p prin-kernels --features wgpu,cpu -- --test-threads=1` | PASS — 149 unit + 1 doctest (local DX12/wgpu) |
| `prin-kernels` (cuda, compile-only) | `cargo build -p prin-kernels --features cuda --lib` | PASS (no CUDA runner available to execute — DV-002, pre-existing) |
| Rustdoc (workspace, default) | `RUSTDOCFLAGS=-D warnings cargo doc --workspace --no-deps` (via per-feature `-p prin-kernels` checks below plus unaffected sibling crates) | PASS — 0 warnings |
| Rustdoc (prin-kernels, cpu/wgpu,cpu/cuda) | `RUSTDOCFLAGS=-D warnings cargo doc -p prin-kernels --no-deps --features <cpu\|wgpu,cpu\|cuda>` | PASS — 0 warnings, all three combinations |
| Audit | `cargo audit` | PASS — 1 allowed warning (pre-existing `paste` RUSTSEC-2024-0436, amendment #9); no new advisories |
| Snyk Code | `snyk code test crates/prin-kernels/src` | PASS — 0 issues |
| Snyk Open Source | Not run | No dependency/manifest changes this session (only a `[[bench]]` target added to `Cargo.toml`; `Cargo.lock` unchanged), matching the WP-018/WP-019 S1 precedent for the same non-gating case |
| Bench compile | `cargo bench -p prin-kernels --bench discrete_step_bench --no-run` (and `--features wgpu`) | PASS |

## Coverage (new/changed code)

`cargo llvm-cov -p prin-kernels --features <cpu|wgpu,cpu>` (each measured in its own clean, non-concurrent run):

| File | `cpu` lines | `wgpu,cpu` lines |
|---|---|---|
| `discrete_step.rs` | 97.65% | 97.65% |
| `discrete_step/cubecl.rs` (raw) | 74.11% | 79.32% |

For reference, the same clean `wgpu,cpu` run's sibling-file raw figures: `mean_field_rk4/cubecl.rs` 80.76%, `pac/cubecl.rs` 82.93%, `sparse_knn/cubecl.rs` 85.86% — see the acceptance-criteria table above for the DV-004 extension discussion of `discrete_step/cubecl.rs`'s 79.32%.

## Benchmark evidence (band_sizes = [4096, 16384, 65536], N=86,016)

`cargo bench -p prin-kernels --bench discrete_step_bench [--features wgpu]` on this host (wgpu/DX12 backend), 10 criterion samples:

| Path | Measurement | Value |
|---|---|---|
| `fused_cpu_native` | wall-clock | 2.043–2.060 ms (41.7–42.1 Melem/s) |
| `unfused_cpu_native` (3× `mean_field_rk4::step_cpu` + 2× `pac::pac_modulate_cpu`) | wall-clock | 7.851–7.928 ms (10.8–11.0 Melem/s) |
| `fused_wgpu_device_dispatch` | wall-clock (10 launches + host round-trips) | 3.498–4.003 ms (21.5–24.6 Melem/s) |
| wgpu `StepReport` (evidence, untimed, device-event timing) | device execution time | 8.96 µs (`timing_method: Device`, `launch_count: 10`) |

Reported as observed pilot evidence (Testing Standards §2, Benchmarking Standards §2.2), not a scientific conclusion; no regression gate is defined for this new benchmark (matching the non-gating status of `mean_field_rk4_bench`/`sparse_knn_bench`).

## Architecture decisions

1. **Discrete-time PAC gate (assignment), not `BandNetwork`'s continuous relaxation.** `prin_dynamics::bands::BandNetwork` (WP-013) implements PAC as a continuous relaxation term (`damplitude += decay * (target - current)`) so it composes with any `Integrator`. This session's fused kernel targets the *original* PRINet 3.0 discrete-time `DeltaThetaGammaNetwork` stepper semantics instead — an outright amplitude overwrite/gate — because the mission text ("PAC gating") and the session's non-goal boundary with WP-013's continuous form (documented in `bands.rs`'s own "Correspondence to the PRINet 3.0 reference" section, which explicitly reserves the discrete-time variant for a future trainable module) both point at the discrete stepper, not the ODE relaxation form. This is a new primitive, not a duplicate of `BandNetwork`.
2. **Sequential per-band cascade, parallel per-oscillator.** Delta steps first (no incoming PAC gate); its just-stepped mean phase gates theta's amplitude before theta itself steps; theta's just-stepped mean phase gates gamma the same way. This 3-stage cross-band dependency is inherent to the algorithm (a band's own order parameter depends on its — possibly gated — current-step amplitude, and the *next* band's gate depends on this band's *stepped* phase), so it cannot collapse into a single kernel launch; "fused" here means the same thing it did for WP-018's 8-launch RK4 step: far fewer launches and host round-trips than composing the already-shipped per-primitive kernels by hand (10 vs. the benchmark's naive unfused composition), not literally one launch.
3. **Own reduction kernels, not a refactor of `mean_field_rk4`/`pac`'s.** `complex_order_reduce`/`real_sum_reduce` are structurally identical to `order_param_block_reduce`/`pac_phase_sum_block_reduce` but are separate, `discrete_step`-local implementations (each called repeatedly across this WP's own 3-band/2-pair path — the "reusable" the mission names) rather than refactoring the private WP-018/WP-019 kernels into a shared module. Reusing those functions directly would require making them `pub(crate)` and pulling them out of already-closed, already-audited WP-018/WP-019 source — out of this WP's declared scope (`crates/prin-kernels/` fused-discrete-step scope, not a cross-cutting refactor) and matching WP-019's own precedent of re-implementing rather than reaching into WP-018's kernel internals.
4. **`.sin()`/`.cos()`, not `.sin_cos()`, in `band_euler_step`.** An initial version used `.sin_cos()` (matching `mean_field_rk4_stage`'s single-`if`-nesting-depth usage) but failed to compile (`no method named sin_cos found for type parameter F`, `cube` macro expansion error) even at the same nesting depth as the working precedent. Root cause not fully isolated (a `cubecl` `0.10.0` macro-expansion sensitivity finer-grained than nesting depth alone); worked around by following WP-019's already-established fallback (separate `.sin()`/`.cos()` calls), recorded here as a second concrete data point for future kernel authors in this crate.
5. **No buffer pool this session.** Each band's device handles are created fresh via `client.create_from_slice`/`client.empty`, matching the precedent WP-019 set for `sparse_knn`/`pac` (S1 handoff, "Out-of-scope discoveries") rather than `mean_field_rk4`'s pooled design — the fused step's per-call host-transfer volume (a handful of `N_b`-sized buffers per band) is smaller than `mean_field_rk4`'s 15-buffer RK4 pool, and the benchmark evidence above already shows the fused path beating the unfused composition without pooling.

## Out-of-scope discoveries

- **Buffer pooling for `discrete_step`.** Not attempted this session (Architecture decision 5); a future performance WP could add a `DiscreteStepBufferPool` if profiling on real (not synthetic) multi-step workloads shows per-call allocation overhead dominating, following `CubeclBufferPool`'s pattern.
- **CUDA execution evidence.** `try_discrete_step_cuda` compiles cleanly (`cargo build --features cuda`) but cannot be executed in this environment (no CUDA-capable runner) — **DV-002**, unchanged, not newly introduced.
- **`discrete_step/cubecl.rs` raw coverage extension of DV-004.** Documented in the acceptance-criteria table above; the S2 audit should confirm the 1.44-point (wgpu,cpu) / 2.62-point (cpu) shortfall against the `mean_field_rk4/cubecl.rs` baseline is fully explained by the higher kernel-body-to-total-code ratio (4 kernels vs. 3/2/1) and not a coverage gap in reachable, instrumentable code.
- **Same-hardware PRINet 3.0 comparison for the "≥ parity, no runtime JIT" target** (Benchmarking Standards §2.4). Not attempted — no Python/torch harness exists in this Rust crate, consistent with WP-018's DV-001 and WP-019's analogous deferral for their own targets.

## Parity-evidence disposition

No new cross-crate parity test is added this session. `discrete_step_cpu` composes two already-parity-verified primitives — the mean-field Kuramoto/Stuart–Landau derivative (`mean_field_derivatives_into`, exercised against `prin_dynamics::models::KuramotoOscillator` transitively via `mean_field_rk4`'s own existing parity coverage) and the PAC modulation formula (`1 + m·cos(mean(slow_phase) + offset)`, matching `prin_dynamics::pac::PhaseAmplitudeCoupling::modulate` and already parity-verified by `pac::tests::parity_against_prin_dynamics_phase_amplitude_coupling`) — in a new sequencing (per-band Euler + inter-band gating) that has no direct PRINet 3.0 Python/Rust counterpart to differential-test against (the closest analogue, `prin_dynamics::bands::BandNetwork`, deliberately implements the *continuous* relaxation form instead — see Architecture decision 1). The `zero_pac_depth_gates_to_identity` and `pac_gate_modulates_fast_band_amplitude` unit tests instead directly verify the fused stepper's own composition is internally consistent with the two primitives it reuses.
