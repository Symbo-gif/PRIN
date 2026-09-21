# benchmarks/_common/ (shared benchmark driver infrastructure)

Config, environment capture, timing harness, registry, and JSON result
writer shared by every category package and the `benchrunner` CLI (WP-033).

## Contents

- `config.py` — `BenchmarkConfig` (iterations/warmup/seed/output dir/params);
  enforces the ≥10-measured-iteration rule (Benchmarking and Reproducibility
  Standards §2.2) at construction.
- `environment.py` — `capture_environment()`: PRIN version, git SHA,
  Rust/Python versions, hardware, OS, backend, dtype, seed (Standards §1.4).
- `timing.py` — `timed_run()`: warmup-excluded median/p95 over ≥10 measured
  iterations.
- `registry.py` — `register`/`get`/`list_specs`: the `(category, name)` →
  benchmark-function registry `benchrunner` dispatches against.
- `result.py` — `write_result()`: merges environment/config/payload and
  writes JSON, confined to `benchmarks/results/`,
  `DOCS/test_and_benchmark_results/`, or a temp directory (Coding Standards
  §6.1). **Append-only:** an existing artefact path is never overwritten —
  `ArtefactExistsError` (a subclass of `OutputPathError`) is raised instead
  (DV-038; Experimentation Standards §4). Re-runs write to a new
  `RUN-<UTC>-<SHA>-<label>/` directory (`DOCS/experiments/campaign-plan.md` §7).

No numerical computation lives here or in any category module — every
measured quantity comes from the Rust-backed `prin` API or, for GPU kernel
performance, the existing `criterion` benches in `crates/prin-kernels`.
