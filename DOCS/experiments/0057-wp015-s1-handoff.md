# Session 0057 — WP-015 S1 Handoff Note

**Session:** 0057 — WP-015 S1: Coding — OscilloSim sparse simulation engine
**Date:** 2026-08-14
**Status:** S1 delivered; handoff to S2 audit (session 0058)

## Scope delivered

| File | Change |
|---|---|
| `crates/prin-sim/src/lib.rs` | Crate root: module declarations, re-exports, crate-level documentation |
| `crates/prin-sim/src/error.rs` | New — `SimError` enum (10 variants) wrapping dynamics, integration, metric, and sparse coupling errors |
| `crates/prin-sim/src/csr_coupling.rs` | New — `SparseCoupling` CSR matrix wrapper with `kuramoto_coupling()` (two-SpMV trig decomposition), `stuart_landau_coupling()` (diffusive coupling), builders (`from_ring`, `from_knn`, `from_dense`, `from_csr`), `prune()`, `submatrix()`, `neighbor_list()`, `memory_bytes()`, `sparsity()` |
| `crates/prin-sim/src/engine.rs` | New — `SparseKuramoto` and `SparseStuartLandau` (implement `prin_dynamics::Dynamics` via CSR SpMV), `OscilloSim` engine (step/run/trajectory), `Trajectory` recording, `apply_guards()` |
| `crates/prin-sim/src/pruning.rs` | New — `PruningStrategy` enum (None, AmplitudeThreshold), `PruningResult` with `apply()`/`restore()` for system-size reduction |
| `crates/prin-sim/src/chimera.rs` | New — `ChimeraMetrics` struct, `compute_chimera_metrics()` and `trajectory_chimera_metrics()` integrating `prin-metrics` chimera functions with CSR neighbor extraction |
| `crates/prin-sim/tests/parity_sparse_vs_dense.rs` | New — 21 integration tests: Kuramoto parity at N=8/64/256, Stuart–Landau parity at N=8/16, engine trajectory parity at N=16, large-N memory measurement, deterministic seed flow, chimera metrics on trajectories |

## Acceptance criteria → evidence map

Acceptance criteria from session 0057 brief:
> "CPU parity passes from small edge cases through declared large-N checks; no hidden state; memory growth is measured and bounded."

| Acceptance criterion | Evidence | Notes |
|---|---|---|
| **CPU parity: small edge cases** | `kuramoto_parity_n8_ring` — sparse vs dense Kuramoto derivatives match at `ε=1e-12` for N=8 ring; `stuart_landau_parity_n8_ring` — sparse vs dense Stuart–Landau match at `ε=1e-10` for N=8; `engine_trajectory_parity_n16` — full 100-step RK4 trajectory matches `integrate_fixed` at `ε=1e-10` for N=16 | Sparse Kuramoto uses two-SpMV trig decomposition; sparse Stuart–Landau uses diffusive coupling `C_i = Σ_j K_ij(z_j − z_i)` via row-sum subtraction |
| **CPU parity: medium N** | `kuramoto_parity_n64_ring` — N=64 at `ε=1e-12`; `kuramoto_parity_n256_ring` — N=256 at `ε=1e-10`; `stuart_landau_parity_n16` (integration test) — N=16 at `ε=1e-10` | Parity holds across two orders of magnitude in N |
| **CPU parity: large-N checks** | `large_n_memory_bounded` — N=10,000 ring coupling: nnz=200,000, memory=3.28 MB (< 5 MB bound), sparsity > 0.99 | Memory is O(nnz) not O(N²); for N=10k the dense matrix would be 800 MB vs 3.28 MB sparse |
| **No hidden state** | All RNG flows through `prin_dynamics::Seed`; `engine_deterministic_across_runs` verifies identical trajectories from same seed; `OscilloSim` holds only explicit state (no thread-local, no global) | `#![forbid(unsafe_code)]` enforced |
| **Memory growth measured and bounded** | `SparseCoupling::memory_bytes()` returns exact CSR footprint; `Trajectory::memory_bytes()` returns exact trajectory footprint; `OscilloSim::memory_bytes()` returns state + coupling footprint; `large_n_memory_bounded` test asserts < 5 MB for N=10k | All memory measurements are deterministic functions of N and nnz |
| **≥95% coverage on new code** | `chimera.rs`: 100% lines / 100% functions; `csr_coupling.rs`: 99.83% lines / 100% functions; `engine.rs`: 96.50% lines / 93.44% functions; `pruning.rs`: 100% lines / 100% functions | 105 unit tests + 21 integration tests + 1 doctest = 127 total |

## Quality gates (S1 verification)

| Gate | Command | Result |
|---|---|---|
| Format | `cargo fmt --all -- --check` | PASS |
| Clippy | `cargo clippy --workspace --all-targets -- -D warnings` | PASS |
| Workspace tests | `cargo test --workspace` | PASS — all tests green (105 new in prin-sim + 21 integration + 1 doctest) |
| Coverage | `cargo llvm-cov -p prin-sim --summary-only` | PASS — all prin-sim files ≥95% lines |
| Rustdoc | `RUSTDOCFLAGS=-D warnings cargo doc --workspace --no-deps` | PASS — 0 warnings |
| Audit | `cargo audit` | PASS — 1 allowed warning (pre-existing `paste` RUSTSEC-2024-0436, amendment #9) |
| Ruff | `ruff check python/ tests/ benchmarks/ tools/ parity/` | PASS |
| Ruff format | `ruff format --check python/ tests/ benchmarks/ tools/ parity/` | PASS |
| mypy | `mypy python/prin --strict` | PASS — 0 issues |
| pytest | `pytest tests/ -m "not slow and not gpu"` | PASS — 306 passed, 6 deselected |

## Architecture decisions

1. **CSR coupling via trig decomposition:** Kuramoto `sin(φ_j − φ_i)` coupling is not a plain SpMV because the sine depends on both row and column indices. Using the angle-difference identity, the coupling sum decomposes into two standard SpMV operations: `a = K·(r⊙sin φ)` and `b = K·(r⊙cos φ)`, then `sin_sum_i = cos φ_i · a_i − sin φ_i · b_i`. This gives O(nnz) per step instead of O(N²).

2. **Sparse models implement `Dynamics` trait:** `SparseKuramoto` and `SparseStuartLandau` implement `prin_dynamics::Dynamics`, allowing them to be used with any `prin_dynamics::Integrator` (Euler, RK4, RK45, exponential, multi-rate). No dynamics logic is duplicated.

3. **Pruning as infrastructure:** `PruningStrategy` and `PruningResult` are provided as standalone utilities. Dynamic pruning during integration (reducing the coupling matrix mid-simulation) requires rebuilding the model with the reduced coupling, which needs the concrete model type — this is deferred to a future WP when the engine API supports model reconstruction.

4. **Chimera metrics via CSR neighbor extraction:** The CSR sparsity pattern doubles as the spatial neighbor list for `prin-metrics` chimera functions, avoiding a separate k-NN index construction.

## Out-of-scope discoveries

- **Dynamic pruning during integration** requires rebuilding the dynamics model with a reduced coupling matrix. The current engine takes `&dyn Dynamics` which doesn't support model reconstruction. This is a candidate for a future WP when the engine API is extended.
- **Parameter sweeps** (grid search over coupling strength, decay rate, etc.) are explicitly a non-goal for this WP and are deferred to WP-016.
- **GPU dispatch** for the SpMV operations is deferred to WP-016 / Phase 3.
- **No PyO3 bindings** were added for `prin-sim`. Python bindings are a candidate for a future WP.
- The `sprs` crate's `CsMat::new` creates CSR format by default (not CSC), which was discovered during implementation. The `from_csr` builder uses this directly.
