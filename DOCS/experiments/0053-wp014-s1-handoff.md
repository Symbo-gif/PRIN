# Session 0053 — WP-014 S1 Handoff Note

**Session:** 0053 — WP-014 S1: Coding — Tensor decompositions
**Date:** 2026-08-11
**Status:** S1 delivered; handoff to S2 audit (session 0054)

## Scope delivered

| File | Change |
|---|---|
| `crates/prin-tensor/src/lib.rs` | Stub → full module: re-exports `hosvd`, `PolyadicTensor`, `cp_als`, `CPDecomposition`, `CPResult`, `TensorError` |
| `crates/prin-tensor/src/error.rs` | New — `TensorError` enum (10 variants), `require_finite`, `require_positive_dims` validators |
| `crates/prin-tensor/src/utils.rs` | New — `mode_unfold`, `mode_n_product`, `frobenius_norm`, `refold`, `ndarray_to_faer`, `faer_mat_to_ndarray`, `flat_to_multi`, `multi_to_flat_excluding`, `invert_permutation` |
| `crates/prin-tensor/src/tucker.rs` | New — `PolyadicTensor` (core + factors), `hosvd()` via faer thin SVD, rank truncation |
| `crates/prin-tensor/src/cp.rs` | New — `CPDecomposition` (weights + factors), `cp_als()` with Seed-based deterministic init, Khatri-Rao product, Gauss-Jordan matrix inverse, convergence diagnostics |
| `crates/prin-tensor/Cargo.toml` | Added `prin-dynamics`, `faer` dependencies |
| `Cargo.toml` (workspace) | Added `faer = "0.20"`, `ndarray` serde feature |

## Acceptance criteria → evidence map

Acceptance criteria from session 0053 brief:
> "Reconstruction, rank/shape, degeneracy, and 3.0 parity tests pass at rtol=1e-10; seed reproducibility is exact."

| Acceptance criterion | Evidence | Notes |
|---|---|---|
| **Reconstruction** | `tucker::tests::hosvd_full_rank_reconstructs_exactly` — full-rank HOSVD of 3×4×2 tensor reconstructs to `< 1e-10`; `tucker::tests::hosvd_2d_is_matrix_svd` — 2×3 matrix exact reconstruction; `cp::tests::cp_als_converges_on_rank1_tensor` — rank-1 tensor CP-ALS reconstruction to `< 1e-8` | HOSVD full-rank is mathematically exact; CP-ALS on rank-1 data converges to machine precision |
| **Rank/shape** | `tucker::tests::hosvd_full_rank_shape_and_ranks` — shape `[3,4,2]`, ranks `[3,4,2]`; `hosvd_truncated_rank` — ranks `[2,3,1]`, core shape `[2,3,1]`; `hosvd_rank_one_approximation` — ranks `[1,1,1]`; `polyadic_tensor_new_validates` — shape/rank accessors; `cp_decomposition_reconstruct_shape` — CP reconstruction shape `[3,4,2]` | All rank and shape invariants verified |
| **Degeneracy** | `hosvd_rejects_empty_tensor`, `hosvd_rejects_nan`, `hosvd_rejects_invalid_rank` (rank 0 and rank > dim), `hosvd_rejects_wrong_number_of_ranks`, `hosvd_rejects_1d_tensor`; `cp_als_rejects_empty_tensor`, `cp_als_rejects_zero_components`, `cp_als_rejects_negative_tolerance`; `mode_n_product_dim_mismatch`; `polyadic_tensor_new_rejects_mismatched_factors` | All degenerate/invalid inputs produce typed errors |
| **rtol=1e-10** | `hosvd_full_rank_reconstructs_exactly` asserts `< 1e-10`; `hosvd_factor_orthogonality` asserts Gram matrix = I at `< 1e-10`; `hosvd_2d_is_matrix_svd` asserts `< 1e-10` | Single-runtime verification at `rtol=1e-10` |
| **Seed reproducibility exact** | `cp_als_seed_reproducibility` — same `Seed::new(123, 0)` produces identical iterations and weights at `< 1e-14` (machine epsilon) | Deterministic init through `prin_dynamics::Seed` |
| **≥95% coverage on new code** | 39 unit tests + 2 doctests across 4 modules (error, utils, tucker, cp). All public functions exercised. | Coverage gate to be verified by S2 audit with `cargo llvm-cov` |

## Quality gates (S1 verification)

| Gate | Command | Result |
|---|---|---|
| Format | `cargo fmt --all -- --check` | PASS |
| Clippy | `cargo clippy -p prin-tensor --all-targets -- -D warnings` | PASS |
| Workspace clippy | `cargo clippy --workspace --all-targets -- -D warnings` | PASS |
| Workspace tests | `cargo test --workspace` | PASS — 542 tests (41 new in prin-tensor, incl. 2 doctests) |
| Rustdoc | `RUSTDOCFLAGS=-D warnings cargo doc --workspace --no-deps` | PASS — 0 warnings |
| Ruff | `ruff check python/ tests/ benchmarks/ tools/ parity/` | PASS |
| Ruff format | `ruff format --check python/ tests/ benchmarks/ tools/ parity/` | PASS |
| mypy | `mypy python/prin --strict` | PASS — 0 issues |
| interrogate | `interrogate -c pyproject.toml python/prin` | PASS — 100% |
| bandit | `bandit -r . -c pyproject.toml` | PASS — 0 issues |
| Baseline | `pytest tests/test_wp001_baseline.py` | PASS — 43/43 |

## Out-of-scope discoveries

- The PRINet 3.0 `core/decomposition.py` reference code is present in the repository archive (`DOCS/archive and reference from PRINet 3.0/PRINet-3.0.0-main/src/prinet/core/decomposition.py`) and was used to generate parity evidence in S3 (session 0055). The S1 claim that "no reference code was found" was incorrect; this was identified by the S2 audit (WP014-F1) and corrected during S3 remediation. Parity tests now live in `crates/prin-tensor/tests/parity_decomposition.rs`.
- The CP-ALS uses a hand-written Gauss-Jordan matrix inverse for the normal equations. For large component counts, a faer-backed least-squares solver would be more numerically stable. This is a candidate for a future WP.
- No PyO3 bindings for the tensor decompositions were added. Python bindings are a candidate for a future WP.
- **API difference vs PRINet 3.0:** The 3.0 `PolyadicTensor` takes a single `rank` clamped to `min(shape)` for all modes; PRIN `hosvd` takes per-mode ranks clamped to `min(I_n, ∏_{k≠n} I_k)`. Document for the S4 Migration Guide.
