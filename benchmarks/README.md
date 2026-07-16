# benchmarks/ — categorized benchmark suite + benchrunner CLI

Reorganization of PRINet 3.0's 62 benchmark scripts (quarterly y2q/y3q/y4q
naming) into topic-named category packages sharing common drivers, executed
through a single `benchrunner` CLI. The JSON output schema is **identical** to
3.0 so historical artefacts remain valid.

## Planned category packages

| Package | Topic |
|---|---|
| `scaling/` | Oscillator-count scaling (up to N=1M), sweep throughput |
| `chimera/` | Chimera phase diagrams and metrics |
| `mot/` | Multi-object tracking (PhaseTracker vs SlotAttention) |
| `ablations/` | Ablation variants (frozen/static/no-GRU, adaptive allocation) |
| `kernels/` | Fused-kernel performance (mean-field RK4, k-NN, PAC, discrete step) |
| `integrators/` | Integrator accuracy/cost (RK45, exponential, multi-rate) |
| `training/` | Training throughput, HEP vs BPTT, optimizer comparisons |
| `daemon/` | Subconscious controller latency (p50/p95) across backends |
| `adversarial/` | FGSM/PGD robustness evaluation |

## Usage (Phase 6)

```bash
python -m benchmarks.benchrunner --category scaling --out benchmarks/results/
```

Results are written to `benchmarks/results/` (canonical, tracked) and mirrored
to `DOCS/test_and_benchmark_results/` (gitignored) by reporting
tools. Regression gates: `criterion` (Rust) and `pytest-benchmark` (Python)
fail CI on >10% regressions.
