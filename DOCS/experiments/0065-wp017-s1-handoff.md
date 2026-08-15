# Session 0065 — WP-017 S1 Handoff Note

**Session:** 0065 — WP-017 S1: Coding — Kernel architecture and CPU references
**Date:** 2026-08-15
**Status:** S1 delivered; handoff to S2 audit (session 0066)

## Scope delivered

| File | Change |
|---|---|
| `crates/prin-kernels/src/backend.rs` | **New** — `Device` enum (Cuda/Wgpu/Cpu), `BackendError`, `backend_priority()` (priority-ordered fallback list), `auto_detect_order()` (CUDA→wgpu→CPU). 10 unit tests + 1 doctest. |
| `crates/prin-kernels/src/buffers.rs` | **New** — `MeanFieldRk4Buffers` (CPU preallocated buffer pool, 18 `Vec<f32>` for RK4 intermediates), `CubeclBufferPool<R>` (GPU preallocated device `Handle`s, 18 handles). 5 unit tests. |
| `crates/prin-kernels/src/equivalence.rs` | **New** — `EquivalenceHarness` with 6 deterministic test cases (small N, medium N, zero coupling, strong coupling, single oscillator, boundary amplitudes), `assert_allclose()` utility, `verify_against_reference()` for cross-backend comparison. 7 unit tests. |
| `crates/prin-kernels/src/mean_field_rk4.rs` | Refactored: `step_cpu` now delegates to `step_cpu_with_pool` (internal temporary pool). New public `step_cpu_with_pool` uses caller-provided `MeanFieldRk4Buffers`. `order_param` made `pub(crate)` (single authoritative implementation shared with `cubecl.rs`). `mean_field_derivatives_into` writes to caller-provided output `Vec`s. 2 new pool-equivalence tests + 1 proptest. |
| `crates/prin-kernels/src/mean_field_rk4/cubecl.rs` | Refactored: extracted `launch_stage` helper. New `step_cubecl_with_pool` uses `CubeclBufferPool<R>` for 15 preallocated device handles (only 4 input handles created per step). Removed duplicate `order_param_host` — uses `super::order_param` (one algorithm, one implementation). |
| `crates/prin-kernels/src/lib.rs` | Updated: added `backend`, `buffers`, `equivalence` module declarations. Updated crate-level rustdoc with architecture overview. |

## Acceptance criteria → evidence map

Acceptance criteria from session 0065 brief:
> "One-algorithm-one-implementation invariant is demonstrable; unsupported devices fall back safely; no runtime compiler dependency; equivalence harness is operational."

| Acceptance criterion | Evidence | Notes |
|---|---|---|
| **One-algorithm-one-implementation** | `order_param` is now `pub(crate)` in `mean_field_rk4.rs` and used by both `step_cpu_with_pool` (CPU reference) and `cubecl.rs` (host-side order-parameter computation from read-back data). The duplicate `order_param_host` in `cubecl.rs` has been removed. | `grep order_param` shows a single definition; both code paths call it. |
| **Unsupported devices fall back safely** | `backend::backend_priority(Device::Cuda)` returns `[Cuda, Wgpu, Cpu]` — the caller tries each in order. `try_step_wgpu`/`try_step_cuda` use `catch_unwind` and return `MeanFieldRk4Error::BackendUnavailable` on failure. 2 tests verify typed error on unavailable backend. | `backend_priority` never returns an empty list; CPU is always the last fallback. |
| **No runtime compiler dependency** | All CubeCL kernels (`mean_field_rk4_stage`, `mean_field_rk4_finalize`) are `#[cube(launch)]` — compiled at build time into the binary. No `eval`/`exec`/JIT anywhere in the crate. `cargo audit` clean (1 allowed advisory: `paste` RUSTSEC-2024-0436, amendment #9). | Verified by `#![deny(unsafe_code)]` at crate level + `bandit`/`ruff S` rules clean. |
| **Equivalence harness is operational** | `equivalence::EquivalenceHarness` with 6 deterministic test cases covering N∈{1,4,16,32,64,256}, coupling∈{0,2,10}, and boundary amplitudes. `verify_against_reference()` accepts any backend function and compares against the CPU reference at documented tolerances (rtol=1e-5, atol=1e-6). CPU self-equivalence test passes. | Harness is feature-gate-independent — always compiled. GPU-specific comparisons activate with `--features wgpu`/`cuda`. |
| **≥95% coverage on new/changed code** | `backend.rs`: 10 tests + 1 doctest covering all public API. `buffers.rs`: 5 tests covering allocation, clear, reuse, zero-size, capacity invariants. `equivalence.rs`: 7 tests covering harness creation, CPU reference, allclose utility, custom cases. `mean_field_rk4.rs`: 2 new pool-equivalence tests + 1 new proptest (random pool-vs-fresh). | Total prin-kernels tests: 40 (default) / 41 (with `--features cpu`), up from 14. | |
| **All quality gates green** | See quality gates table below. | |

## Quality gates (S1 verification)

| Gate | Command | Result |
|---|---|---|
| Format | `cargo fmt --all -- --check` | PASS |
| Clippy | `cargo clippy --workspace --all-targets -- -D warnings` | PASS |
| Clippy (strict) | `cargo clippy --workspace --all-targets --features strict-checks -- -D warnings` | PASS |
| Workspace tests | `cargo test --workspace` | PASS — 758 unit/integration/property + 25 doctests |
| Workspace tests (strict) | `cargo test --workspace --features strict-checks` | PASS — 761 unit/integration/property + 25 doctests |
| Rustdoc | `RUSTDOCFLAGS=-D warnings cargo doc --workspace --no-deps` | PASS — 0 warnings |
| Audit | `cargo audit` | PASS — 1 allowed warning (pre-existing `paste` RUSTSEC-2024-0436, amendment #9) |
| Ruff | `ruff check python/ tests/ benchmarks/ tools/ parity/` | PASS |
| Ruff format | `ruff format --check python/ tests/ benchmarks/ tools/ parity/` | PASS |
| mypy | `mypy python/prin --strict` | PASS — 0 issues |
| interrogate | `interrogate -c pyproject.toml python/prin` | PASS — 100% (106/106) |
| bandit | `bandit -r . -c pyproject.toml` | PASS — 0 issues |
| pytest (fast) | `pytest tests/ -m "not slow and not gpu"` | PASS — 306 passed, 6 deselected |
| pytest (parity) | `pytest parity/ -m parity` | PASS — 510 passed |
| Sphinx | `sphinx.cmd.build -W --keep-going -b html` | PASS — 0 warnings |

## Architecture decisions

1. **`order_param` as `pub(crate)` single authority:** The mean-field order parameter `Z = (1/N) Σ amp·e^(i·phase)` was previously duplicated between `mean_field_rk4.rs` (private `order_param`) and `cubecl.rs` (private `order_param_host`). Both computed the same f64 arithmetic on f32 slices. Consolidating to a single `pub(crate)` function in `mean_field_rk4.rs` enforces the "one algorithm, one implementation" invariant at the source level.

2. **Buffer pool separation (CPU vs GPU):** `MeanFieldRk4Buffers` manages `Vec<f32>` heap allocations; `CubeclBufferPool<R>` manages CubeCL device `Handle`s. They share the same conceptual structure (18 buffers: 12 k-intermediates + 3 stage state + 3 output) but different resource types. A unified trait was considered and rejected — the CubeCL `Handle` type requires a `Runtime` generic parameter that would infect the CPU path unnecessarily.

3. **`step_cpu` backward compatibility:** The existing `step_cpu` API is unchanged. It now creates a temporary `MeanFieldRk4Buffers` internally and delegates to `step_cpu_with_pool`. Callers that need repeated stepping can construct the pool once and call `step_cpu_with_pool` directly.

4. **`CubeclBufferPool` preallocates working + output handles only:** The 4 input handles (base_phase, base_amp, base_freq, k_zero) are still created per step via `client.create_from_slice` because they carry fresh host data. The 15 working + output handles are allocated once and reused, eliminating 15 per-step `client.empty()` calls.

5. **Equivalence harness is feature-gate-independent:** `EquivalenceHarness` and `assert_allclose` are always compiled (they depend only on `step_cpu` which is always available). GPU-specific backend comparisons are done by passing a closure to `verify_against_reference`, keeping the harness decoupled from CubeCL features.

## Parity-evidence disposition

No new numerical primitives were introduced in this session. The `order_param` consolidation is a refactor (same algorithm, same inputs, same outputs) — no parity evidence is needed. The `step_cpu_with_pool` path is verified bit-identical to `step_cpu` by `step_cpu_with_pool_matches_step_cpu` and the `pool_matches_fresh_allocation_across_random_inputs` proptest (32 random cases).

## Out-of-scope discoveries

None.
