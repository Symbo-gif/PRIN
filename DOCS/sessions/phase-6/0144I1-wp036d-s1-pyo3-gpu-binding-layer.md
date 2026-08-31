# Session 0144I1 — WP-036D S1 (sub-pass 1/3): PyO3 GPU binding layer

**Status:** PLANNED
**Roadmap phase:** 6 — Benchmarks, reproduction, docs, and RC1
**Execution unit:** WP-036D
**Session type:** S1 — Coding
**Predecessor:** [0144I — Coding (decomposed)](0144I-wp036d-s1-gpu-execution-path-ported-acceptance-suite.md)
**Successor:** [0144I2 — device dispatch and DLPack marshalling](0144I2-wp036d-s1-device-dispatch-and-dlpack-marshalling.md)
**Authority:** Project Plan §6/§8, amendments #31/#33/#36, and [`WP-036D-S1-execution-plan-and-decomposition.md`](WP-036D-S1-execution-plan-and-decomposition.md). The normative standard wins on conflict.

> Prospective execution contract, not completion evidence.

## Mission

Expose `prin-sim`'s already-audited GPU engine types through a new thin PyO3
`gpu` binding module (Phase A of audit `036b` §8.4): `crates/prin-py/src/
bindings/gpu.rs` (or a `gpu/` submodule) behind `#[cfg(feature = "cuda")]`
and `#[cfg(feature = "wgpu")]`, wrapping `GpuSparseKuramoto`,
`GpuMeanFieldEngine`, `GpuBandStepper`, and the GPU exponential-integrator
step.

## Contract

- Device-aware constructors that allocate GPU buffers via CubeCL; GPU
  step/forward methods that **accept and return DLPack GPU tensors**
  (zero-copy GPU↔GPU, no CPU round-trip) — mirror the WP-025
  `read_dlpack_f64` / `export_dlpack_f64` pattern with an f32 GPU variant in
  `dlpack.rs` (new helpers only; touch no existing function; no new `unsafe`
  block without approval).
- Numerical authority stays in the existing CubeCL kernels; the binding is
  marshalling and dispatch only. No Python numerics.
- `_prin_core.pyi` updated for every new callable/type.
- `#[cfg(all(test, feature = "cuda"))]` and `#[cfg(all(test, feature =
  "wgpu"))]` PyO3 integration tests assert GPU-tensor round-trip and
  GPU-vs-CPU kernel agreement within Testing Standards §3 tolerances.
- maturin rebuild so the new symbols import.
- **Non-goals:** any `_torch_compat.py` change (`0144I2`); test activation or
  `gpu.yml` (`0144I3`); `prin-train` / autodiff; new `prin` public symbols;
  Triton.

## Required reading

- The 0144I parent brief, amendment #36, and the decomposition plan
- `DOCS/audits/036b-wp036b-audit.md` §8.2–§8.4
- `crates/prin-sim/src/` `gpu` module; `crates/prin-kernels/` kernel APIs
- `crates/prin-py/src/bindings/dlpack.rs` and the WP-025 bridge precedent
- Testing Standards §3 (GPU tolerances); Coding Standards §2.1, §6

## Entry conditions

Amendment #36 adopted; WP-036B closed; no unresolved D1/D2; `PRIN-GPU-Runner`
state recorded.

## Expected work

1. Add the `gpu` binding module and DLPack f32 GPU helpers.
2. Wire device-aware constructors and step/forward methods over the
   `prin-sim` GPU engines.
3. Update `_prin_core.pyi`; rebuild with maturin.
4. Add `cuda`/`wgpu`-gated PyO3 integration tests; run
   `cargo test --features cuda` / `--features wgpu` and the CPU workspace
   suite; ≥95% coverage on changed Rust.
5. Run `cargo fmt` / clippy, `ruff`/`mypy` on any touched Python stub glue,
   Snyk Code on modified Rust; append evidence to
   `DOCS/experiments/0144I-wp036d-s1-handoff.md`.

## Prohibited

Python numerics, new public `prin` symbols, edits to existing `dlpack.rs`
functions, unapproved `unsafe`, `_torch_compat.py` changes, `prin-train`
changes, scope creep, or push.

## Exit gate

The GPU binding module imports after a maturin rebuild, its `cuda`/`wgpu`
PyO3 tests pass on a GPU-capable host, the CPU workspace suite is green, and
the sub-pass local gate is green. Commit locally only; proceed to `0144I2`.
