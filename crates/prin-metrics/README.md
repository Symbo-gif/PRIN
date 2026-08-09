# prin-metrics

Synchronization and chimera metrics for PRIN — Rust rebuild of PRINet 3.0
`core/measurement.py` and the chimera utilities in `utils/oscillosim.py`.

**Phase:** 1 (Dynamics core) — **Status:** complete (WP-010, sessions 0037–0040)

## Modules

| Module | Public API | Description |
|---|---|---|
| `order` | `kuramoto_order_parameter`, `kuramoto_order_parameter_complex`, `inter_frame_phase_correlation`, `order_parameter_series` | Kuramoto order parameter (scalar and complex), inter-frame phase correlation |
| `coherence` | `mean_phase_coherence`, `phase_coherence_matrix`, `sparse_mean_phase_coherence` | Mean phase coherence (full and sparse k-NN), coherence matrix |
| `spectral` | `power_spectral_density`, `extract_concept_probabilities` | Power spectral density (rustfft-backed), concept-probability extraction |
| `energy` | `synchronization_energy`, `sparse_synchronization_energy` | Dense and sparse synchronization energy |
| `chimera` | `local_order_parameter`, `bimodality_index`, `strength_of_incoherence`, `discontinuity_measure`, `chimera_index`, `strength_of_incoherence_temporal`, `BIMODALITY_CHIMERA_THRESHOLD`, `DEFAULT_CHIMERA_THRESHOLD` | Full chimera metric set |
| `metastability` | `metastability` | Temporal standard deviation of the order parameter (PRIN extension) |
| `knn` | `build_phase_knn` | Measurement-facing k-NN wrapper delegating to `prin-dynamics` |
| `error` | `MetricError` | Typed error enum (9 variants) with boundary validation |

## Numerics

All metrics run in `f64`, matching PRINet 3.0's `torch.float64` reference
paths. Single-runtime verification targets `rtol = 1e-10`; cross-platform
corpus-regeneration comparisons use the registered METRIC tolerance
(`rtol = 1e-8`, amendment #16). PSD and chimera paths affected by PRINet's
`complex64`/`float32` internal arithmetic use the documented `1e-6` tolerance
(amendment #14).

## Invariants

- Order parameters `R ∈ [0, 1]`, coherence `C ∈ [−1, 1]` (clamped against
  ~1 ulp accumulation noise).
- `C = (N r² − 1)/(N − 1)` identity between mean phase coherence and
  Kuramoto order parameter cross-checked in tests.
- Sparse/full variants agree where equivalent (synchronized state, k=N−1
  energy ratio).

## Coverage

Lines 99.53%, regions 96.28%, functions 100% (145 tests: 104 unit/property +
22 parity/corpus + 19 doctests).

## Dependencies

- `prin-dynamics` — phase k-NN index delegation (one algorithm, one
  implementation), `safe_phase_diff`.
- `rustfft` — FFT for PSD (pure-Rust, workspace dependency).
