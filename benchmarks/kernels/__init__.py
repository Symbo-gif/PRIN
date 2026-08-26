"""``kernels``: fused-kernel performance (mean-field RK4, sparse k-NN, PAC,
discrete step).

`prin-kernels` has no Python (PyO3) binding surface (verified: no
`step_auto`/kernel class appears in `python/prin/_prin_core.pyi`) -- GPU
kernel performance is measured exclusively by the existing Rust `criterion`
benches (`crates/prin-kernels/benches/*.rs`), per Benchmarking and
Reproducibility Standards §2.1 ("Rust microbenchmarks use `criterion`").
Reimplementing kernel timing in Python would duplicate Rust numerics
(Coding Standards §1). This category therefore *orchestrates* `cargo bench`
as a subprocess and republishes its `estimates.json` output under the
unified `benchrunner` JSON envelope -- it measures nothing itself.

Consolidates PRINet 3.0's `triton_fused_kernel_benchmark.py`,
`multirate_triton_benchmark.py`, `activation_profile.py`,
`concurrent_{2,3}regime_benchmark.py`, `heterogeneous_gpu_cpu_benchmark.py`,
`holomorphic_profile.py`, `y2q3_benchmarks.py`, `y3q3_benchmarks.py`,
`y3q49_scientific_regime_benchmark.py`, and `y4q3_benchmarks.py`. See
`DOCS/baselines/wp033_benchmark_traceability.md`.
"""

from __future__ import annotations

from benchmarks.kernels import criterion_bridge

__all__ = ["criterion_bridge"]
