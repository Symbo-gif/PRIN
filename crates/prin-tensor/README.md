# prin-tensor

Tensor decomposition for PRIN: Tucker/HOSVD (`PolyadicTensor`) and CP/PARAFAC
(`CPDecomposition`, ALS).

Rebuild target for PRINet 3.0 `core/decomposition.py`.

## Modules

- **`tucker`** — Tucker/HOSVD decomposition via faer SVD. `hosvd()` computes
  factor matrices as left singular vectors of mode-n unfoldings, with optional
  rank truncation. Full-rank HOSVD is an exact reconstruction.
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

## Dependencies

- `ndarray` — N-dimensional tensor storage
- `faer` — Pure Rust SVD and linear algebra
- `prin-dynamics` — Deterministic `Seed` for CP-ALS initialization
