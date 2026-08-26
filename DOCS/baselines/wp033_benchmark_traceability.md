# WP-033 legacy benchmark traceability

Maps every PRINet 3.0 benchmark script under `DOCS/archive and reference
from PRINet 3.0/PRINet-3.0.0-main/benchmarks/` to the topic category and
`benchrunner`-registered module that replaces it (Mission: "migrate all
legacy scripts into nine topic categories without schema changes";
Acceptance: "Every legacy benchmark has a traceability row and executable
replacement").

## Verified script count: 58, not 62

The session brief's Mission and Contract text (and the Project Plan / Rebuild
Planning Document text it quotes) say **62** benchmark scripts. A directory
listing of the archived source — the authoritative repository state, not the
planning-document figure (CLAUDE.md: "Verify implementation facts from the
repository; do not invent") — gives **58** `.py` scripts, excluding
`README.md` and the `results/` data directory:

```powershell
(Get-ChildItem "DOCS\archive and reference from PRINet 3.0\PRINet-3.0.0-main\benchmarks" -Filter *.py).Count
# 58
```

The archived tree is a single-commit "scaffold" import (`git log` on it shows
one commit, `655521d`) with no history explaining the discrepancy; nothing in
this repository names which four scripts would be missing. This is recorded
here as a verified factual correction for the S2 audit and maintainer to
formally disposition (a plan-text correction is not this S1 session's call to
make unilaterally) — every one of the 58 scripts actually present has a row
below; none were dropped to hit a target count.

## Category mapping methodology

Each script's primary category was assigned by:

1. Its module docstring's stated topic (all 58 have one).
2. A keyword-frequency ranking across the 9 category descriptions'
   vocabulary (`scaling`/`chimera`/`mot`/`ablations`/`kernels`/
   `integrators`/`training`/`daemon`/`adversarial`), cross-checked against
   `grep -n "^def \|^class "` output for ambiguous/large "grab-bag" scripts.
3. Manual override when the docstring's literal topic word (e.g. "scaling",
   "complexity") disagreed with the raw keyword ranking (common for GPU
   benchmarks, whose CUDA/device boilerplate outranks their actual subject).

Many legacy scripts are quarterly "grab bags" that internally span several
categories (e.g. `q4_benchmarks.py` has ablation, throughput, and capacity
sub-experiments). This table assigns one **primary** category per script —
the consolidation this WP performs is exactly collapsing many overlapping
legacy scripts onto one shared per-topic driver, so many-to-one rows are
expected, not a gap.

**`integrators/` has no legacy-script predecessor.** No PRINet 3.0 benchmark
script has integrator accuracy/cost (RK45/exponential/multi-rate) as its
primary topic — these are PRIN-native constructs built in Phase 2, absent
from the 3.0 suite in this form. `multirate_triton_benchmark.py` is the
closest secondary reference, but its primary topic (Triton kernel timing) is
tracked under `kernels/` instead. `benchmarks/integrators/accuracy_cost.py`
is still implemented (required: nine topic categories, not eight) with no
legacy row pointing to it.

**Two scripts are non-benchmark tooling, not migrated.** `y4q2_benchmarks.py`
(figure/table/reproduce-pipeline generation) and `y4q4_benchmarks.py`
(archival/release-readiness reporting) contain no timed measurement — see
their `def`/`class` listing in the Notes column. They belong to the
figure/table-generator and release-readiness work Project Plan §6 Phase 6
lists as separate deliverables from `benchrunner`, not this WP. Recorded here
per Expected Work item 5 ("record out-of-scope discoveries for a later WP")
rather than silently dropped or force-migrated.

## Traceability table

| # | Legacy script | Category | New module | Notes |
|---|---|---|---|---|
| 1 | `activation_profile.py` | kernels | `benchmarks/kernels/criterion_bridge.py` | GPU activation-function profiling; kernel-topic keyword rank #1. |
| 2 | `clevr_n.py` | mot | `benchmarks/mot/tracker_comparison.py` | CLEVR-N binding capacity; `mot` rank #1 (55 hits). |
| 3 | `concurrent_2regime_benchmark.py` | kernels | `benchmarks/kernels/criterion_bridge.py` | CUDA-streams concurrency benchmark. |
| 4 | `concurrent_3regime_benchmark.py` | kernels | `benchmarks/kernels/criterion_bridge.py` | CUDA-streams concurrency benchmark. |
| 5 | `coupling_complexity_benchmark.py` | scaling | `benchmarks/scaling/coupling_complexity.py` | Docstring: "O(N²) vs O(N log N) vs O(N)" — overridden from raw kernels rank to match its literal complexity-scaling topic. |
| 6 | `desync_catastrophe.py` | chimera | `benchmarks/chimera/phase_diagram.py` | Desynchronization catastrophe replication; `chimera` rank #1. |
| 7 | `goldilocks_sustained_benchmark.py` | scaling | `benchmarks/scaling/oscillator_count.py` | Docstring: "GPU O(N) vs O(N log N) vs O(N²)"; `scaling` rank #1. |
| 8 | `goldilocks_sustained_cpu_benchmark.py` | scaling | `benchmarks/scaling/oscillator_count.py` | CPU/RAM variant of #7; `scaling` rank #1. |
| 9 | `gpu_benchmarks.py` | scaling | `benchmarks/scaling/oscillator_count.py` | `def benchmark_oscillator_scaling_gpu` is its first/primary function; overridden from raw `chimera` rank (desync/sync helpers) to match. |
| 10 | `heterogeneous_gpu_cpu_benchmark.py` | kernels | `benchmarks/kernels/criterion_bridge.py` | Heterogeneous GPU+CPU concurrent benchmark; `kernels` rank #1. |
| 11 | `holomorphic_profile.py` | kernels | `benchmarks/kernels/criterion_bridge.py` | Holomorphic energy GPU profiling; `kernels` rank #1. |
| 12 | `mnist_subset.py` | training | `benchmarks/training/throughput.py` | MNIST-subset baseline training with order-parameter monitoring. |
| 13 | `multirate_triton_benchmark.py` | kernels | `benchmarks/kernels/criterion_bridge.py` | Triton kernel timing is the primary topic (`kernels` rank #1, 42 hits); multi-rate *stepping* is a secondary reference for `integrators/`. |
| 14 | `on_stress_benchmark.py` | scaling | `benchmarks/scaling/coupling_complexity.py` | Docstring: "O(N) Mean-Field — Hardware Limits"; overridden from raw `kernels` rank to match its scaling/complexity topic. |
| 15 | `on_vs_onlogn_benchmark.py` | scaling | `benchmarks/scaling/coupling_complexity.py` | Docstring: "O(N) Mean-Field vs O(N log N) Sparse k-NN"; overridden from raw `kernels` rank. |
| 16 | `oscillator_scaling.py` | scaling | `benchmarks/scaling/oscillator_count.py` | Task 1.7, 10k-oscillator scalability; `scaling` rank #1. |
| 17 | `oscillobench.py` | training | `benchmarks/training/throughput.py` | `def benchmark_{xor_n,random_dichotomies,mnist_convergence,...}` vs. LSTM/Hopfield/Transformer baselines — a training/baseline-comparison suite; overridden from raw `kernels` rank. |
| 18 | `pairwise_coupling_scaling.py` | scaling | `benchmarks/scaling/coupling_complexity.py` | Docstring: "O(N²) Full Pairwise Coupling Scaling"; overridden from raw `kernels` rank. |
| 19 | `phase1_bf_extension.py` | training | `benchmarks/training/throughput.py` | Multi-seed training comparison (Bayes-factor extension); `training` rank #1. |
| 20 | `phase1_bf_tost_resolution.py` | training | `benchmarks/training/throughput.py` | TOST equivalence resolution for #19's seed comparisons; grouped with its sibling (raw keyword signal too weak to rank alone). |
| 21 | `phase1_statistical_hardening.py` | chimera | `benchmarks/chimera/phase_diagram.py` | Experiments 1.3–1.5; `chimera` rank #1 (33 hits). |
| 22 | `phase2_scaling_analysis.py` | scaling | `benchmarks/scaling/oscillator_count.py` | Docstring: "Scaling Analysis"; overridden from raw `chimera` rank to match its literal topic. |
| 23 | `phase3_scientific_experiments.py` | training | `benchmarks/training/throughput.py` | `experiment_3_{1,3,4}` build/train PhaseTracker/SlotAttention then profile gradient flow/representation geometry; overridden from raw `mot` rank (tracker construction helpers). |
| 24 | `phase4_theoretical_verification.py` | training | `benchmarks/training/throughput.py` | `experiment_4_{1,2}`: convergence verification and parameter-scaling by component during training; overridden from raw `mot` rank. |
| 25 | `phase_diagram.py` | chimera | `benchmarks/chimera/phase_diagram.py` | Kuramoto bifurcation analysis; `chimera` rank #1. |
| 26 | `phase_to_rate_benchmark.py` | training | `benchmarks/training/throughput.py` | Phase-to-rate autoencoder training/information-preservation benchmark. |
| 27 | `q2_benchmarks.py` | training | `benchmarks/training/throughput.py` | NaN-fix verification, mixed-precision VRAM, SCALR training; `training` rank #1. |
| 28 | `q4_benchmarks.py` | ablations | `benchmarks/ablations/variant_comparison.py` | `AblatedHybridCLEVRN`/`run_ablation`/`run_adaptive_control` ("adaptive allocation" — the category's own description text) are its central content; overridden from a spurious raw `daemon` rank (substring false-positives, not a real daemon topic). |
| 29 | `run_clevr_n_sweep.py` | mot | `benchmarks/mot/tracker_comparison.py` | Sweep runner for CLEVR-N tracking baselines; `mot` rank #1. |
| 30 | `run_q17_individual.py` | ablations | `benchmarks/ablations/variant_comparison.py` | Individual-benchmark runner for Y4 Q1.7; `ablations` rank #1. |
| 31 | `run_q18_individual.py` | adversarial | `benchmarks/adversarial/robustness.py` | Dispatcher (`run_single`/`show_status`) over `y4q1_8_benchmarks.py`'s benchmarks; category mirrors its target (#53). |
| 32 | `run_q19_individual.py` | mot | `benchmarks/mot/tracker_comparison.py` | Dispatcher over `y4q1_9_benchmarks.py`'s benchmarks; category mirrors its target (#54). |
| 33 | `scalr_vs_adam_benchmark.py` | training | `benchmarks/training/throughput.py` | SCALR vs. Adam optimizer benchmark; `training` rank #1. |
| 34 | `scientific_coupling_benchmark.py` | scaling | `benchmarks/scaling/coupling_complexity.py` | Docstring: "Sequential Per-Regime Coupling Complexity Analysis"; overridden from raw `kernels` rank; sibling of #5. |
| 35 | `subconscious_benchmark.py` | daemon | `benchmarks/daemon/control_latency.py` | ONNX inference latency / daemon thread overhead; `daemon` rank #1 (58 hits). |
| 36 | `triton_fused_kernel_benchmark.py` | kernels | `benchmarks/kernels/criterion_bridge.py` | Triton vs. PyTorch Kuramoto-step latency; `kernels` rank #1 (76 hits). |
| 37 | `y2q1_benchmarks.py` | mot | `benchmarks/mot/tracker_comparison.py` | Integration-bottleneck benchmarks; `mot` rank #1. |
| 38 | `y2q2_benchmarks.py` | mot | `benchmarks/mot/tracker_comparison.py` | Oscillatory advantage / temporal binding; `mot` rank #1. |
| 39 | `y2q3_benchmarks.py` | kernels | `benchmarks/kernels/criterion_bridge.py` | "Scale and Harden"; `kernels` rank #1 (65 hits). |
| 40 | `y2q4_benchmarks.py` | mot | `benchmarks/mot/tracker_comparison.py` | Consolidation quarter; `mot` rank #1. |
| 41 | `y3q1_benchmarks.py` | mot | `benchmarks/mot/tracker_comparison.py` | `mot` rank #1. |
| 42 | `y3q2_benchmarks.py` | mot | `benchmarks/mot/tracker_comparison.py` | `mot` rank #1 (88 hits). |
| 43 | `y3q3_benchmarks.py` | kernels | `benchmarks/kernels/criterion_bridge.py` | "Efficiency & Scaling (Windows-Native)"; `kernels` rank #1 (87 hits). |
| 44 | `y3q45_comprehensive_benchmarks.py` | daemon | `benchmarks/daemon/control_latency.py` | "Final Validation"; `daemon` rank #1 (74 hits). |
| 45 | `y3q49_scientific_regime_benchmark.py` | kernels | `benchmarks/kernels/criterion_bridge.py` | Coupling-regime × device benchmark; `kernels` rank #1 (77 hits). |
| 46 | `y3q4_benchmarks.py` | mot | `benchmarks/mot/tracker_comparison.py` | "Publication & OscilloSim v2.0"; `mot` rank #1. |
| 47 | `y4q1_2_benchmarks.py` | chimera | `benchmarks/chimera/phase_diagram.py` | "Rigorous Scientific Analysis"; `chimera` rank #1 (41 hits). |
| 48 | `y4q1_3_benchmarks.py` | chimera | `benchmarks/chimera/phase_diagram.py` | "Chimera State Deepening"; `chimera` rank #1 (71 hits). |
| 49 | `y4q1_4_benchmarks.py` | mot | `benchmarks/mot/tracker_comparison.py` | "Temporal Advantage Deepening"; `mot` rank #1 (88 hits). |
| 50 | `y4q1_5_benchmarks.py` | mot | `benchmarks/mot/tracker_comparison.py` | "Session-Length Dynamics"; `mot` rank #1. |
| 51 | `y4q1_5_cross_comparison.py` | mot | `benchmarks/mot/tracker_comparison.py` | Standalone companion to #50; same category. |
| 52 | `y4q1_7_benchmarks.py` | mot | `benchmarks/mot/tracker_comparison.py` | "Definitive Temporal Advantage Protocol"; `mot` rank #1. |
| 53 | `y4q1_8_benchmarks.py` | adversarial | `benchmarks/adversarial/robustness.py` | "Extended Scientific Rigor"; `adversarial` rank #1 (53 hits). |
| 54 | `y4q1_9_benchmarks.py` | mot | `benchmarks/mot/tracker_comparison.py` | "Reviewer Gap Analysis"; `mot` rank #1 (41 hits). |
| 55 | `y4q1_benchmarks.py` | chimera | `benchmarks/chimera/phase_diagram.py` | "Paper-Critical Experiments"; `chimera` rank #1. |
| 56 | `y4q2_benchmarks.py` | *(deferred — non-benchmark)* | *(none)* | `def benchmark_{figure_generation,table_generation,reproduce_pipeline,artefact_completeness,style_consistency}` — release/reporting tooling, not a timed measurement. Belongs to the Project Plan §6 figure/table-generator deliverable, a separate WP. |
| 57 | `y4q3_benchmarks.py` | kernels | `benchmarks/kernels/criterion_bridge.py` | "v3.0.0 Release Readiness"; `kernels` rank #1 (45 hits). |
| 58 | `y4q4_benchmarks.py` | *(deferred — non-benchmark)* | *(none)* | `def benchmark_{year4_report,retrospective,archive_files,sha256_manifest,final_regression,doc_completeness,project_metrics}` — archival/release-readiness reporting, not a timed measurement. Same deferral basis as #56. |

## Category → new module summary

| Category | Legacy rows | New module | Registered benchmark name |
|---|---|---|---|
| `scaling` | 10 (#5, 7, 8, 9, 14, 15, 16, 18, 22, 34) | `benchmarks/scaling/oscillator_count.py`, `benchmarks/scaling/coupling_complexity.py` | `scaling/oscillator_count`, `scaling/coupling_complexity` |
| `chimera` | 6 (#6, 21, 25, 47, 48, 55) | `benchmarks/chimera/phase_diagram.py` | `chimera/phase_diagram` |
| `mot` | 14 (#2, 29, 32, 37, 38, 40, 41, 42, 46, 49, 50, 51, 52, 54) | `benchmarks/mot/tracker_comparison.py` | `mot/tracker_comparison` |
| `ablations` | 2 (#28, 30) | `benchmarks/ablations/variant_comparison.py` | `ablations/variant_comparison` |
| `kernels` | 11 (#1, 3, 4, 10, 11, 13, 36, 39, 43, 45, 57) | `benchmarks/kernels/criterion_bridge.py` (orchestrates existing `crates/prin-kernels/benches/*.rs`) | `kernels/criterion_suite` |
| `integrators` | 0 (no legacy predecessor — see above) | `benchmarks/integrators/accuracy_cost.py` | `integrators/accuracy_cost` |
| `training` | 9 (#12, 17, 19, 20, 23, 24, 26, 27, 33) | `benchmarks/training/throughput.py` | `training/throughput` |
| `daemon` | 2 (#35, 44) | `benchmarks/daemon/control_latency.py` | `daemon/control_latency` |
| `adversarial` | 2 (#31, 53) | `benchmarks/adversarial/robustness.py` | `adversarial/robustness` |
| *(deferred, non-benchmark)* | 2 (#56, 58) | — | — |

**58 legacy rows total: 56 migrated (10+6+14+2+11+0+9+2+2) + 2 deferred = 58.**
