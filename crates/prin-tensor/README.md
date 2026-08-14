# prin-tensor

Tensor decomposition for PRIN: Tucker/HOSVD (`PolyadicTensor`) and CP/PARAFAC
(`CPDecomposition`, ALS).

Rebuild target for PRINet 3.0 `core/decomposition.py`. Phase 2, WP-014.

## Modules

- **`tucker`** — Tucker/HOSVD decomposition via `faer` SVD. `hosvd()` computes
  factor matrices as left singular vectors of mode-n unfoldings, with optional
  per-mode rank truncation. Full-rank HOSVD is an exact reconstruction.
- **`cp`** — CP/PARAFAC decomposition via alternating least squares. `cp_als()`
  uses deterministic initialization through `prin_dynamics::Seed` for
  reproducible factor matrices, with convergence diagnostics.
- **`utils`** — Mode-n unfolding, mode-n product, Frobenius norm, and
  tensor/ndarray/faer conversion utilities.
- **`error`** — Typed `TensorError` enum for input validation and convergence
  failures.

## Numerics

All decomposition paths run in f64. SVD is computed via `faer` (pure Rust,
no system dependencies). Parity with the PRINet 3.0 reference is verified by
integration tests (`tests/parity_decomposition.rs`) at `rtol = 1e-10` (float64,
single-runtime).

## PRINet 3.0 migration notes

- `prinet.core.decomposition.PolyadicTensor` → `prin_tensor::hosvd` +
  `prin_tensor::PolyadicTensor`. The reference takes a single rank clamped to
  `min(shape)` for all modes; PRIN takes per-mode ranks clamped to
  `min(I_n, prod_{k != n} I_k)`.
- `prinet.core.decomposition.CPDecomposition` → `prin_tensor::cp_als` +
  `prin_tensor::CPDecomposition`. CP-ALS uses all-factor normalization (column
  norms clamped at `1e-12`) and convergence is monitored via the relative change
  in reconstruction error `‖X − X̂‖_F`. Factor initialization is uniform `[0, 1)`
  from the deterministic `Seed` authority.
- No PyO3 bindings are exposed in this WP; Python bindings are a future WP.

## Dependencies

- `ndarray` — N-dimensional tensor storage
- `faer` — Pure Rust SVD and linear algebra
- `prin-dynamics` — Deterministic `Seed` for CP-ALS initialization
- `serde` — `Serialize`/`Deserialize` for `PolyadicTensor` and `CPDecomposition`
- `rayon` — Data-parallel helpers (future WP)
