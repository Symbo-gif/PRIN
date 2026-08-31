# Session 0144I / WP-036D S1 running handoff

**Date:** 2026-08-31 (sub-pass 0144I1 complete)
**Status:** Sub-pass 0144I1 **COMPLETE** (committed locally at green gates;
not pushed). Sub-passes 0144I2–0144I3 remain. S1 does not self-certify —
`0144J` (S2 audit) is next after all three sub-passes.

## Session-start protocol (Development Workflow §6)

Read: latest Project State Report, the 0144I brief and its decomposition
(`WP-036D-S1-execution-plan-and-decomposition.md`), the 0144I1 sub-pass
brief, Project Plan §6/§8 (amendments #31/#33/#36), Development Workflow and
Audit Standards §3/§7, Testing Standards §1.1/§3, the audit
`036b-wp036b-audit.md` §8, and the WP-025 DLPack bridge precedent.

**Session ID/type:** 0144I — WP-036D S1 (Coding), sub-pass 0144I1.
**Planned output (0144I1):** PyO3 GPU binding layer over `prin-sim`'s GPU
engines, DLPack f32 helpers, `.pyi` updates, feature-gated tests, maturin
rebuild.

---

## Sub-pass 0144I1 — PyO3 GPU binding layer

### Deliverables

| # | Deliverable | Files | Status |
|---|---|---|---|
| 1 | Feature forwarding (`cuda`/`wgpu` → `prin-sim`) | `crates/prin-py/Cargo.toml` | ✅ |
| 2 | `read_dlpack_f32` / `export_dlpack_f32` helpers | `crates/prin-py/src/dlpack.rs` (new fns only) | ✅ |
| 3 | GPU binding module: `PyGpuSparseKuramoto`, `PyGpuMeanFieldEngine`, `PyGpuBandStepper` | `crates/prin-py/src/bindings/gpu.rs` (new file) | ✅ |
| 4 | Module wiring (feature-gated) | `crates/prin-py/src/bindings/mod.rs`, `crates/prin-py/src/lib.rs` | ✅ |
| 5 | `.pyi` stubs for all 3 GPU types | `python/prin/_prin_core.pyi` | ✅ |
| 6 | Feature-gated integration tests (4 tests) | `crates/prin-py/src/bindings/gpu.rs` `#[cfg(all(test, any(feature = "cuda", feature = "wgpu")))]` | ✅ |

### Design decisions

1. **DLPack f32 helpers are feature-gated** (`#[cfg(any(feature = "cuda", feature = "wgpu"))]`)
   to avoid dead-code warnings when building without GPU features. They are
   only consumed by the GPU binding module, which is itself feature-gated.

2. **`GpuSparseKuramoto` constructor takes CSR topology as flat lists**
   (`crow_indices`, `col_indices`, `values`) matching `SparseCoupling::from_csr`
   convention, plus scalar model parameters. This avoids exposing the
   `SparseCoupling` type to Python while preserving the exact topology the
   GPU kernel needs.

3. **`GpuMeanFieldEngine` and `GpuBandStepper` constructors take initial
   state as f32 DLPack tensors** plus scalar parameters. `step()` returns a
   dict with backend timing metadata. `state()` returns three f32 DLPack
   capsules `(phase, amplitude, frequency)`.

4. **`GpuBandStepper` constructor uses `#[allow(clippy::too_many_arguments)]`**
   since the 12 parameters (3 state tensors + band_sizes + 3×3 per-band
   params + 2×2 PAC params + amp_min/max + dt) are inherent to the fused
   three-band discrete-step API.

5. **No new `unsafe` blocks** in the binding module. The f32 DLPack helpers
   in `dlpack.rs` reuse the existing audited `unsafe` patterns (same SAFETY
   justifications as the `f64` counterparts).

6. **Numerical authority stays in Rust.** The binding is marshalling and
   dispatch only — no Python numerics. `check_no_python_numerics.py` stays
   clean.

### Quality gates

| Gate | Command | Result |
|---|---|---|
| `cargo fmt` | `cargo fmt --all -- --check` | ✅ clean |
| `clippy` (default) | `cargo clippy -p prin-py -- -D warnings` | ✅ clean |
| `clippy` (wgpu) | `cargo clippy -p prin-py --features wgpu -- -D warnings` | ✅ clean |
| GPU tests (wgpu) | `cargo test -p prin-py --features wgpu -- bindings::gpu::tests` | ✅ 4/4 pass |
| Workspace tests | `cargo test --workspace` | ✅ all pass |
| `ruff check` | `.venv\Scripts\ruff check python/prin/` | ✅ clean |
| `ruff format` | `.venv\Scripts\ruff format --check python/prin/_prin_core.pyi` | ✅ clean |
| `mypy --strict` | `.venv\Scripts\mypy python/prin/_prin_core.pyi --strict` | ✅ clean |
| CPU Python suite | `pytest tests/ -m "not slow and not gpu"` | ✅ 1724 pass / 9 skip |

### Pre-existing issue (not caused by this sub-pass)

`test_wp001_baseline::test_current_baseline_automation_is_green` fails with
"session 0144E: brief/register status mismatch" — a pre-existing register
status issue from the WP-036C renumber (amendment #36). Unrelated to 0144I1.

### Test evidence

```
running 4 tests
test bindings::gpu::tests::gpu_band_stepper_binding_step_and_state_f32 ... ok
test bindings::gpu::tests::gpu_mean_field_engine_binding_step_and_state_f32 ... ok
test bindings::gpu::tests::gpu_sparse_kuramoto_binding_agrees_with_cpu_reference ... ok
test bindings::gpu::tests::gpu_sparse_kuramoto_binding_compute_derivatives_f32_round_trip ... ok

test result: ok. 4 passed; 0 failed; 0 ignored; 0 measured; 10 filtered out
```

### Non-goals confirmed (not touched)

- No `_torch_compat.py` changes (→ 0144I2)
- No test marker/`gpu.yml` changes (→ 0144I3)
- No `prin-train` / autodiff changes
- No new `prin` public symbols
- No edits to existing `dlpack.rs` functions
- No Triton changes
- No scope creep

### Next step

Sub-pass `0144I2` — Python device dispatch + DLPack marshalling in
`_torch_compat.py`.
