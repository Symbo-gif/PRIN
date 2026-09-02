# Session 0144Q1 — WP-036E S1 (sub-pass 1/3): `prin-kernels` device-`Handle` dispatch layer

**Status:** COMPLETE
**Roadmap phase:** 6 — Benchmarks, reproduction, docs, and RC1
**Execution unit:** WP-036E
**Session type:** S1 — Coding
**Predecessor:** [0144Q — Coding (decomposed)](0144Q-wp036e-s1-gpu-device-resident-execution-path.md)
**Successor:** [0144Q2 — Coding (sub-pass 2/3)](0144Q2-wp036e-s1-prin-sim-persistent-device-buffers-dv003.md)
**Authority:** Project Plan §6/§8, amendments #38/#43, and
[`WP-036E-S1-execution-plan-and-decomposition.md`](WP-036E-S1-execution-plan-and-decomposition.md).
The normative standard wins on conflict.

> Prospective execution contract, not completion evidence.

## Mission

Add device-`Handle`-in/out dispatch entry points to the three `prin-kernels`
CubeCL kernel modules, alongside the existing host-slice functions, so a caller
holding CubeCL device buffers can run each kernel with **no host transfer**. The
host-slice path (`*_cubecl` / `*_auto`) becomes a thin
`upload → device path → download` wrapper — one algorithm, one implementation
(Coding Standards §1).

## Scope

- `sparse_knn::cubecl` — `sparse_knn_coupling_device<R>(client, &SparseKnnDeviceState<R>, params, &mut SparseKnnDeviceDerivs<R>)` operating purely on `Handle`s; CSR `indptr`/`indices` handles owned by the caller. `sparse_knn_coupling_cubecl` re-expressed as upload→device→download.
- `mean_field_rk4::cubecl` — `step_cubecl_device<R>(client, &mut MeanFieldDeviceState<R>, params, &CubeclBufferPool<R>) -> StepReport`; all four RK4 stages take their order parameter from the device reduction (`order_param_device`), removing the host-slice dependency of stage 1. `step_cubecl_with_pool` re-expressed as upload→`step_cubecl_device`→download. `launch_count` semantics documented if the stage-1 device reduction changes the count.
- `discrete_step::cubecl` — analogous `discrete_step_device<R>` + host wrapper re-expression.
- Feature-gated `cuda`/`wgpu`/`cpu`, mirroring the existing `cubecl` submodule gating.

## Contract

- Kernel-equivalence tests for every new device entry point against the CPU
  reference: `rtol=1e-5, atol=1e-6` (Testing Standards §3); wider only via a
  per-test annotation + Parity Report entry (amendments #14/#16/#17/#25).
- No numerical change to any `#[cube]` kernel body; the device entry points
  re-use the exact same kernels the host path launches.
- `unsafe` only in the existing `#![allow(unsafe_code)]` kernel modules under
  the amendment-#8 `// SAFETY:` pattern; no new `unsafe` surface.
- No new `prin` public symbol; `check_no_python_numerics.py` unaffected
  (`prin-kernels` is Rust).
- `≥95%` coverage on changed first-party lines (non-`#[cube]` bodies; DV-004).

## Gates

`cargo fmt --all -- --check`; `cargo clippy --workspace --all-targets -- -D warnings`
(+ `-p prin-kernels --features cuda --all-targets`, `--features wgpu`,
`--features cpu`); `cargo test --workspace`;
`cargo test -p prin-kernels --features cuda` (CUDA kernels on the RTX 4060);
`cargo test -p prin-kernels --features cpu`; `cargo test -p prin-kernels --features wgpu`;
`RUSTDOCFLAGS='-D warnings' cargo doc -p prin-kernels --no-deps`;
`cargo audit` (no `Cargo.toml` change expected → no new advisory);
Snyk Code on modified `.rs`.

## Non-goals

`prin-sim` engine changes (→ `0144Q2`); the on-device `f64` combine / DV-003
(→ `0144Q2`); any `prin-py` / Python / DLPack change (→ `0144Q3`);
`test_sparse_vram_subquadratic` (→ `0144Q3`); the S2 audit `0144R`.

## Exit

All gates green; every new device entry point has kernel-equivalence coverage;
host-slice wrappers are byte-equivalent in behaviour to their pre-change form
(existing `*_cubecl` tests unchanged and green). Commit at the green local gate;
hand to `0144Q2`.
