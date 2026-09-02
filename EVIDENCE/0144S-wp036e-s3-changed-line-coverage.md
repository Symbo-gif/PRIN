# 0144S / WP-036E S3 — changed-line coverage (finding WP036E-F3)

**Session:** `0144S` (WP-036E S3 remediation)
**Date:** 2026-09-02
**Host:** `PRIN-GPU-Runner` (Windows 11, RTX 4060, driver 595.95), Rust 1.92.0,
`cargo-llvm-cov`
**Finding:** WP036E-F3 (D2) — "No evidence proves ≥95% changed-code coverage."
**Result:** **98.71 %** changed-line coverage after the single documented
DV-004 `#[cube(launch)]` exclusion (97.22 % raw union). **PASS.**

## Method

`cargo llvm-cov ... --lcov` was run once per feature-matrix cell for the two
crates the audit named (`prin-kernels`, `prin-sim`):

| lcov file | invocation |
|---|---|
| `cov-nofeat.lcov` | `cargo llvm-cov -p prin-sim -p prin-kernels` |
| `cov-cpu.lcov` | `cargo llvm-cov --features cpu -p prin-kernels -p prin-sim` |
| `cov-wgpu.lcov` | `cargo llvm-cov --features wgpu -p prin-kernels -p prin-sim` |
| `cov-cuda.lcov` | `cargo llvm-cov --features cuda -p prin-kernels -p prin-sim` |
| `cov-cw.lcov` | `cargo llvm-cov --features cuda,wgpu -p prin-kernels -p prin-sim` |

The device dispatch layer is feature-gated: a given `#[cfg(feature = ...)]`
branch (the CUDA on-device `f64` finalize vs. the host `f64` combine; the whole
`prin-sim::gpu` module is `#[cfg(any(cpu, wgpu, cuda))]`; `order_param_device`'s
CUDA-vs-non-CUDA arms) is only reachable under the matching feature. Per-line
coverage is therefore the **union** of the five runs — a changed line is
"covered" if any matrix cell hits it. The changed-line set is
`git diff -U0 6343416 -- <file>` (working tree) restricted to the six changed
`*.rs` files (the WP-036E S1 range plus the S3 commits).

Tool: `tools/coverage_changed_lines.py`
(`python tools/coverage_changed_lines.py 6343416 cov-nofeat.lcov cov-cpu.lcov
cov-wgpu.lcov cov-cuda.lcov cov-cw.lcov -- <files>`).

## Raw union result

```
crates/prin-kernels/src/buffers.rs:               instrumentable=1   covered=1    uncovered=0   100.00%
crates/prin-kernels/src/discrete_step/cubecl.rs:  instrumentable=204 covered=203  uncovered=1   99.51%
crates/prin-kernels/src/mean_field_rk4/cubecl.rs: instrumentable=349 covered=327  uncovered=22  93.70%
crates/prin-kernels/src/sparse_knn.rs:            instrumentable=0   covered=0    uncovered=0   100.00%
crates/prin-kernels/src/sparse_knn/cubecl.rs:     instrumentable=270 covered=269  uncovered=1   99.63%
crates/prin-sim/src/gpu.rs:                       instrumentable=435 covered=424  uncovered=11  97.47%

UNION TOTAL: instrumentable=1259 covered=1224 uncovered=35  97.22%
```

## DV-004 exclusion (kernel body only)

One changed `#[cube(launch)]` body:

- `crates/prin-kernels/src/mean_field_rk4/cubecl.rs:267-285` —
  `order_param_finalize_f64` (CUDA-only on-device `f64` level-2 reduction,
  DV-003). `#[cube(launch)]` bodies are non-instrumentable by
  `cargo-llvm-cov`; **DV-004** (CLOSED, 2026-08-26) records kernel-equivalence
  tests as their permanent, accepted coverage mechanism. Equivalence for this
  kernel: `mean_field_rk4::cubecl::tests_cuda::*` (CUDA vs CPU, `rtol=1e-5,
  atol=1e-6`) and the new
  `tests_priority::wgpu_runtime_under_cuda_feature_uses_host_f64_combine`
  (host `f64` combine vs `order_param`).

**After excluding those 19 lines: instrumentable=1240, covered=1224,
uncovered=16 → 98.71 %.**

No other exclusion is taken — all host dispatch, validation, fallback and
export code is counted.

## Residual 16 uncovered lines (all non-product / host-unreachable)

| Line(s) | Kind | Why untestable on `PRIN-GPU-Runner` |
|---|---|---|
| `mean_field_rk4/cubecl.rs:693` | call-argument continuation inside the `client.profile(move \|\| { … })` closure in `step_cubecl_device` | `cargo-llvm-cov` attributes profiled-closure body lines inconsistently; the closure *is* executed by every `*_device_dispatch_matches_cpu_reference*` test (cpu/cuda/wgpu). |
| `mean_field_rk4/cubecl.rs:1203`, `:1723`; `discrete_step/cubecl.rs:872`; `sparse_knn/cubecl.rs:652` | `let Ok(client) = … else { return; };` guard in `#[cfg(feature = "wgpu")]` tests | the runner **has** a DX12 wgpu adapter, so the `else { return; }` is never taken. |
| `gpu.rs:511` | `_ => None` arm of the `compute_derivatives_cuda_export` handle-triple match | unreachable when the CUDA device path holds valid handles — each `export_cuda_handle` returns `Some`. |
| `gpu.rs:702-704`, `gpu.rs:991-993` | `Ok(Self::host(…))` tail of `GpuMeanFieldEngine::new` / `GpuBandStepper::new` | only reached when `try_create_client()` returns `None` (no GPU adapter with a compute feature compiled) — never on this host. The `host()` **body** is covered directly by `mean_field_engine_host_fallback_arms_round_trip` / `band_stepper_host_fallback_arms_round_trip`. |
| `gpu.rs:1414-1416`, `gpu.rs:1640-1642` | `assert!(…, "phase[{i}]: got={}, expected={}", got.phase[i], f64::from(pi))` panic-message arguments in two device multi-step tests | evaluated only when the assertion fails; the assertions pass. |

## Regression tests added this session

| Test | File / module | Covers |
|---|---|---|
| `device_state_from_parts_adopts_handles_without_transfer` | `mean_field_rk4/cubecl.rs` `tests_cpu` | `MeanFieldDeviceState::from_parts` |
| `device_dispatch_rejects_empty_population` | `mean_field_rk4/cubecl.rs` `tests_cpu` | `step_cubecl_device` `EmptyPopulation` guard |
| `wgpu_runtime_under_cuda_feature_uses_host_f64_combine` | `mean_field_rk4/cubecl.rs` `tests_priority` | `order_param_device_cuda_or_host` non-CUDA arm + `host_f64_combine` |
| `device_state_from_parts_adopts_per_band_handles` | `discrete_step/cubecl.rs` `tests_cpu` | `DiscreteStepDeviceState::from_parts` |
| `device_derivs_from_parts_adopts_handles` | `sparse_knn/cubecl.rs` `tests_cpu` | `SparseKnnDeviceDerivs::from_parts` |
| `mean_field_engine_host_fallback_arms_round_trip` | `prin-sim/gpu.rs` `tests` | `GpuMeanFieldEngine::host` + `MeanFieldInner::Host` arms of `n_oscillators`/`dt`/`state`/`step`/`Debug`/`state_cuda_export` |
| `band_stepper_host_fallback_arms_round_trip` | `prin-sim/gpu.rs` `tests` | `GpuBandStepper::host` + `BandStepperInner::Host` arms |
| `sparse_kuramoto_host_fallback_and_debug` | `prin-sim/gpu.rs` `tests` | `GpuSparseKuramoto` host-slice fallback + `SparseKnnDeviceResources` `Debug` |
| `cuda_export_helpers_and_guards` | `prin-sim/gpu.rs` `tests` (cuda) | `CudaBufferExport::into_raw_parts`; `compute_derivatives_cuda_export` length-mismatch / `n<=1` / `device=None` branches |

## Non-coverage cleanup folded in

`order_param_device`'s duplicated host `f64` combine (two byte-identical copies,
in `order_param_device` and `order_param_device_cuda_or_host`) extracted into
one `host_f64_combine<R>` helper — one algorithm, one implementation
(Coding Standards §1). No numeric change.
