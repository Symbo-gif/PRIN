# PRIN Benchmarking and Reproducibility Standards

**Status:** Normative. These standards guarantee that PRIN's published
scientific results remain exactly reproducible and that performance claims are
evidence-based.

---

## 1. Reproducibility requirements

1. **Byte-comparable artefact regeneration (F4).** `tools/reproduce.py` must
   regenerate all 15 paper figures and 11 LaTeX tables from the stored JSON
   artefacts (~172 files) with a matching SHA-256 manifest, in seconds, with no
   GPU or training. Checked in CI (`repro.yml`) on every relevant change.
2. **Single seed authority.** All randomness flows through one counter-based
   `Seed` type (Philox/PCG64). Multi-seed experiments (bootstrap CIs, Welch
   t-tests) must be exactly reproducible across CPU/GPU and across runs.
3. **Unchanged JSON schema.** Benchmark artefacts keep the exact PRINet 3.0
   JSON schema so historical artefacts stay valid and nothing needs
   re-measuring for reproduction.
4. **Environment capture.** Every benchmark artefact records: PRIN version +
   git SHA, Rust/Python versions, hardware (CPU model, core count, GPU, VRAM),
   OS, backend (CPU SIMD/CUDA/wgpu), dtype, and seed.

## 2. Benchmarking requirements

### 2.1 Structure

- Benchmarks live in `benchmarks/` as 9 topic-named category packages sharing
  common drivers, executed via the single `benchrunner` CLI. No one-off
  scripts.
- Rust microbenchmarks use `criterion`; Python-level benchmarks use
  `pytest-benchmark`.

### 2.2 Methodology (minimum bar for any reported number)

- Warmup iterations excluded; report median and p95 over ≥10 measured
  iterations (criterion defaults satisfy this).
- GPU timing uses device-side events/synchronization, never wall-clock around
  async launches.
- Compare like-for-like: identical dtype, batch shape, and hardware; fair
  PT-vs-SA comparisons use identical loss/optimizer/augmentation/parameter
  budgets (ported fair-training framework).
- Statistical claims require multi-seed runs with bootstrap CIs; significance
  via Welch t-tests.

### 2.3 Regression gates

- CI fails on **>10% regression** against the stored baseline for gated
  benchmarks (criterion baselines + pytest-benchmark autosave).
- Performance-motivated PRs must include before/after numbers and the exact
  `benchrunner`/criterion command used.

### 2.4 Performance targets (tracked against PRINet 3.0 on the same hardware)

| Workload | Target |
|---|---|
| Mean-field RK4, N=1M, GPU | ≥ Triton-fused parity |
| Sparse k-NN coupling, N=16K, k=14, GPU | ≥ parity (3× torch) |
| Fused discrete step (3-band + PAC), GPU | ≥ parity, no runtime JIT |
| CPU fallback paths | ≥ 2× pure PyTorch |
| Parameter sweeps | ≥ 8× on 16-core CPU |
| Daemon latency | lower p95 than 3.0 |
| Torch-bridge training step | parity ±10%; bridge overhead <5% |

## 3. Artefact and results hygiene

- Canonical benchmark results: `benchmarks/results/` (tracked).
- Generated reports/figures for docs: `DOCS/test_and_benchmark_results/`
  (gitignored).
- Model weights: only `models/subconscious_controller.onnx` is tracked;
  everything else is manifest-verified or regenerated.
- The Parity Report (docs) publishes the full old-vs-new benchmark comparison
  before any release candidate; scientific conclusions (chimera phase-diagram
  boundaries, IP scores, ablation orderings, statistical outcomes) must be
  unchanged.
