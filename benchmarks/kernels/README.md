# benchmarks/kernels/ (fused-kernel performance)

Mean-field RK4, sparse k-NN, and fused discrete-step CPU kernel performance
(WP-033). Consolidates 11 PRINet 3.0 legacy scripts — see
`DOCS/baselines/wp033_benchmark_traceability.md`.

## Contents

- `criterion_bridge.py` — `kernel_criterion_suite`: runs
  `cargo bench -p prin-kernels --features cpu` for every CPU `criterion`
  target in `crates/prin-kernels/benches/{mean_field_rk4,discrete_step,
  sparse_knn}_bench.rs` and republishes each bench's `estimates.json` under
  the unified `benchrunner` envelope.

`prin-kernels` has no Python (PyO3) binding surface — verified: no kernel
class or `step_auto`-style function appears in `python/prin/_prin_core.pyi`.
GPU kernel performance is therefore measured exclusively by the existing
Rust `criterion` benches (Benchmarking and Reproducibility Standards §2.1:
"Rust microbenchmarks use `criterion`"); this package *orchestrates*
`cargo bench` as a subprocess and republishes its output — it performs no
numerical computation and duplicates no Rust kernel logic in Python. Only
the CPU-feature targets run by default, matching the established
`rust.yml --features cpu` CI convention; `wgpu`/`cuda` targets exist in the
same bench files but need GPU hardware not assumed here.
