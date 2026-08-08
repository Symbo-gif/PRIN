# Session 0033 — WP-009 S1 Handoff Note

**Session:** 0033 — WP-009 S1: Coding — PAC, coupling topologies, and phase k-NN
**Author:** S1 coding session
**Date:** 2025
**Status:** S1 complete; handing off to mandatory S2 audit (session 0034)

## Scope delivered

This S1 session implemented the WP-009 S1 scope in the `prin-dynamics` crate:

1. **Phase–amplitude coupling (PAC)** — `crates/prin-dynamics/src/pac.rs`
2. **Coupling topology enums/builders** — `crates/prin-dynamics/src/coupling.rs`
3. **Sparse/full equivalence, k-NN edge property, and 1/N vs 1/k normalization tests** — `crates/prin-dynamics/src/models.rs` (test module)
4. **PAC parity tests against PRINet 3.0** — `crates/prin-dynamics/tests/parity_pac.rs`
5. **Public API re-exports** — `crates/prin-dynamics/src/lib.rs`

## Acceptance criteria → evidence mapping

| Acceptance criterion (session brief §Contract) | Evidence |
|---|---|
| Golden parity covers all modes | `cargo test -p prin-dynamics` — 162 unit + 16 integrator parity + 9 model parity + 9 PAC parity = **196 tests, all green**. Model parity (`tests/parity_models.rs`) covers Kuramoto, Stuart-Landau, Hopf across mean-field, full, and sparse k-NN modes. PAC parity (`tests/parity_pac.rs`) covers 9 cases vs PRINet 3.0 reference values. |
| 1/N versus 1/k is explicit | `models::tests::normalization_one_over_n_explicit_in_mean_field` and `models::tests::normalization_one_over_k_explicit_in_sparse` verify the distinct normalization rules. `models::tests::sparse_knn_k_equals_n_minus_1_equals_full_default` verifies the K/N vs K/k ratio is exactly `(N-1)/N` when k=N-1. |
| Sparse/full equivalence and k-NN edge properties pass | `models::tests::sparse_knn_k_equals_n_minus_1_equals_full_default` (sparse vs full with k=N-1); `models::tests::knn_index_has_exact_k_neighbors_no_self_loops`, `knn_index_neighbors_are_phase_nearest`, `knn_index_wraps_around_circle`, `knn_index_symmetric_neighbor_property` (edge properties); `state::proptests::knn_index_has_k_entries_and_no_self` (property test). |
| Topology enums/builders | `coupling::Topology` enum with `AllToAll`, `Ring { k_ring }`, `SmallWorld { k_ring, rewire_prob, seed }` variants; `Topology::build_matrix` produces N×N row-major matrices; `validate_coupling_matrix` validates length and finiteness. 16 unit tests + 3 property tests in `coupling.rs`. |
| Normalization rules preserved | All topology builders use `K / degree` per edge (analogous to `K/N` all-to-all and `K/k` sparse k-NN), keeping total coupling energy per oscillator constant. Documented in `coupling.rs` module docs. |

## Quality gates

| Gate | Command | Result |
|---|---|---|
| Format | `cargo fmt --all -- --check` | **PASS** (exit 0) |
| Clippy | `cargo clippy --workspace --all-targets -- -D warnings` | **PASS** (exit 0; only a transient Windows incremental-compilation file-lock warning, not a code issue) |
| Rust tests | `cargo test -p prin-dynamics` | **PASS** (196 tests: 162 unit + 16 integrator parity + 9 model parity + 9 PAC parity + 2 doctests) |
| Workspace tests | `cargo test --workspace` | **PASS** (all crates green) |
| Rustdoc | `RUSTDOCFLAGS='-D warnings' cargo doc --workspace --no-deps` | **PASS** (exit 0, clean) |
| Cargo audit | `cargo audit` | **PASS** (only the inherited, documented `paste` RUSTSEC-2024-0436 advisory — amendment #9) |
| Snyk Code | `snyk_code_scan` on `crates/prin-dynamics/src` | **PASS** (0 issues) |

## Numerical invariants preserved

- **1/N mean-field normalization**: `Z = (1/N) Σⱼ rⱼ e^{iφⱼ}` — verified by `normalization_one_over_n_explicit_in_mean_field`.
- **1/k sparse normalization**: `K_eff = K/k` per edge — verified by `normalization_one_over_k_explicit_in_sparse` and the K/k vs K/N ratio test.
- **Phase wrapping**: `safe_phase_diff` uses `atan2(sin, cos)` for `(-π, π]` differences (carried over from existing `state.rs`).
- **Amplitude clamping**: PAC output clamped to `[AMPLITUDE_MIN, AMPLITUDE_MAX]` = `[1e-6, 10.0]`, matching PRINet 3.0.
- **f64 throughout**: Rust PAC uses f64; PRINet 3.0 uses torch.float32, so parity tests use `epsilon = 1e-6` to absorb the documented f32 truncation drift (amendment #14).

## Public API added

- `prin_dynamics::pac::PhaseAmplitudeCoupling` — PAC modulator struct.
- `prin_dynamics::pac::PacError` — typed error enum.
- `prin_dynamics::coupling::Topology` — coupling topology enum (`AllToAll`, `Ring`, `SmallWorld`).
- `prin_dynamics::coupling::CouplingError` — typed error enum.
- `prin_dynamics::coupling::validate_coupling_matrix` — matrix validation helper.
- Re-exported from `prin_dynamics` crate root: `PacError`, `PhaseAmplitudeCoupling`, `CouplingError`, `Topology`.

## Files changed

| File | Change |
|---|---|
| `crates/prin-dynamics/src/pac.rs` | **New** — full PAC implementation (543 lines: impl + 22 unit tests + 2 property tests) |
| `crates/prin-dynamics/src/coupling.rs` | **Modified** — added `Topology` enum, `CouplingError`, `validate_coupling_matrix`, 3 builder functions, 16 unit tests, 3 property tests |
| `crates/prin-dynamics/src/models.rs` | **Modified** — added 9 tests for k-NN edge properties, sparse/full equivalence, 1/N vs 1/k normalization, topology integration |
| `crates/prin-dynamics/src/lib.rs` | **Modified** — re-exports for new public API |
| `crates/prin-dynamics/tests/parity_pac.rs` | **New** — 9 PAC parity tests vs PRINet 3.0 reference values |

## Non-goals respected

- **No GPU kernels** — all CPU-only, as specified.
- **No trainable discrete bands** — PAC modulation depth is a runtime parameter, not a trainable parameter.
- **No scope creep** — only PAC, topologies, and the k-NN index tests were touched; no other modules modified.

## Known limitations / notes for S2

1. **Rayon parallelism**: The session brief mentions "rayon phase-sort k-NN index". The existing `build_phase_knn_index` in `state.rs` uses sequential sort. Rayon parallelism was not added in this S1 because the existing implementation is already O(N log N) and the brief's acceptance criteria focus on correctness (edge properties, equivalence), not parallelism. If the S2 audit determines rayon parallelism is in-scope, it should be filed as a remediation item.
2. **Small-world rewiring**: Uses `Seed::next_f64` for deterministic rewiring. The algorithm avoids self-loops and duplicate edges but does not guarantee exact degree preservation if all rewire targets are exhausted (falls back to keeping the original edge). This matches the Watts–Strogatz variant where rewiring is best-effort.
3. **Coverage**: Not measured with `cargo llvm-cov` in this session (not wired for `prin-dynamics` yet). The S2 audit should verify ≥95% on new/changed code if llvm-cov is available.

## Handoff

S1 is complete. All acceptance criteria are evidence-mapped above. Handing off to the mandatory S2 audit (session 0034) per the Development Workflow Standards §3. S1 may not self-certify completion.
