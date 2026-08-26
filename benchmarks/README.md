# benchmarks/ — categorized benchmark suite + benchrunner CLI

Reorganization of PRINet 3.0's legacy benchmark scripts (quarterly
y2q/y3q/y4q naming; 58 verified present in the archived source, see
`DOCS/baselines/wp033_benchmark_traceability.md`) into topic-named category
packages sharing common drivers, executed through a single `benchrunner`
CLI (WP-033). Every category's JSON output keeps the field names of its
corresponding legacy artefact so historical results remain parseable.

## Category packages

| Package | Topic | Registered benchmark(s) |
|---|---|---|
| `scaling/` | Oscillator-count scaling, sweep throughput | `oscillator_count`, `coupling_complexity` |
| `chimera/` | Chimera phase diagrams and metrics | `phase_diagram` |
| `mot/` | Multi-object tracking (PhaseTracker vs SlotAttention) | `tracker_comparison` |
| `ablations/` | Ablation variants (frozen/static/no-GRU, adaptive allocation) | `variant_comparison` |
| `kernels/` | Fused-kernel performance (mean-field RK4, k-NN, discrete step) | `criterion_suite` |
| `integrators/` | Integrator accuracy/cost (RK45, exponential, multi-rate) | `accuracy_cost` |
| `training/` | Training throughput | `throughput` |
| `daemon/` | Subconscious controller latency (p50/p95) | `control_latency` |
| `adversarial/` | FGSM/PGD robustness evaluation | `robustness` |

`_common/` holds the shared config/environment-capture/timing/registry/
result-writer infrastructure; `benchrunner/` is the CLI itself. See each
package's own README for what it measures and which Rust-backed `prin` API
(or, for `kernels/`, which `crates/prin-kernels` `criterion` bench) backs it.
No numerical computation lives in this suite — every measured quantity comes
from Rust.

## Usage

```bash
python -m benchmarks.benchrunner --list
python -m benchmarks.benchrunner --category scaling --out benchmarks/results/
python -m benchmarks.benchrunner --category scaling --name oscillator_count --iterations 20
```

Results are written to `benchmarks/results/` (canonical, tracked) and mirrored
to `DOCS/test_and_benchmark_results/` (gitignored) by reporting
tools. Regression gates: `criterion` (Rust) and `pytest-benchmark` (Python)
fail CI on >10% regressions.

## Status (WP-033 S1)

The CLI, shared infrastructure, and all nine category modules are
implemented and tested (`tests/test_benchrunner.py`) at small, fast,
characterization-scale parameters — this validates the *machinery* (schema
compatibility, the ≥10-iteration timing rule, CLI dispatch), not final
scientific conclusions (a WP-033 non-goal). Production-scale campaign runs
and the Parity Report comparing legacy vs. new numbers are future work.
