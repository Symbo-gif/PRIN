# PRIN — Official Project Plan

**Project:** PRIN (Phase-Resonance Interference Network)
**Status:** Active — Phase 0 (Foundation and de-risking spikes)
**Reference implementation:** PRINet 3.0.0 (`Symbo-gif/PRINet-3.0.0`; ~25.5k lines of Python across 43 modules, 37 test files / ~1,670 tests, 62 benchmark scripts, Sphinx docs, NeurIPS paper artefacts)
**Planning source:** `DOCS/archive and reference from PRINet 3.0/PRINet-3.0.0-main/docs/Rebuild_Planning_Document.md` (archived; reference only)
**License:** MIT

---

## 1. Mission

Rebuild PRINet from scratch as **PRIN**, preserving all scientific functionality,
numerical results, and reproducibility guarantees while improving performance,
safety, and maintainability. PRIN is a two-layer system:

- **Rust core** (`crates/`) — oscillator dynamics, integrators, coupling
  topologies, sparse ops, phase metrics, tensor decomposition, simulation
  engine, trainable components, subconscious daemon, and single-source GPU
  kernels (CubeCL → CUDA/Metal/Vulkan; CPU SIMD + rayon fallback).
- **Thin Python package** (`python/prin/`) — the PRINet-3.0-compatible public
  API, `torch.autograd.Function` bridges with zero-copy DLPack tensor exchange,
  matplotlib figures, LaTeX tables, benchmark drivers, and the reproducibility
  pipeline. The Python layer contains **no numerics**.

The full functional inventory, language evaluation, and module-by-module
mapping are maintained in the archived Rebuild Planning Document (§2, §4, §6)
and are normative for this project except where superseded here.

## 2. Naming decisions (supersedes the archived plan)

| Archived plan | PRIN decision |
|---|---|
| Repository `prinet4/` | Repository **`PRIN/`** |
| Crates `prinet-*` | Crates **`prin-*`** |
| Python package `prinet` | Python package **`prin`** (PRINet-3.0-compatible symbol set; the Migration Guide documents the import rename) |
| Extension module `_prinet_core` | **`prin._prin_core`** |
| Version `4.0.0` | Semantic versioning from **`0.1.0`**; first feature-complete release is `1.0.0` (equivalent to the archived plan's "4.0.0" milestone) |
| Sphinx site at `docs/`, reports at `docs/test_and_benchmark_results/` | Single **`DOCS/`** tree (Windows filesystems are case-insensitive, so `docs/` and `DOCS/` cannot coexist): governance at the root, Sphinx site at **`DOCS/sphinx/`**, generated reports at **`DOCS/test_and_benchmark_results/`** (gitignored) |

## 3. Requirements

### 3.1 Functional

- **F1 — Feature parity:** every public class/function in PRINet 3.0's 175+-symbol API has an equivalent.
- **F2 — Numerical parity:** trajectories, metrics, and benchmark results match 3.0.0 within the documented tolerances (§5).
- **F3 — Differentiability:** all trainable components support reverse-mode autodiff and interop with PyTorch training loops.
- **F4 — Reproducibility:** `tools/reproduce.py` regenerates all 15 figures and 11 tables byte-comparably from the same JSON artefacts with a matching SHA-256 manifest.
- **F5 — ONNX controller:** the subconscious controller runs on CPU, DirectML, and Ryzen AI NPU.

### 3.2 Non-functional

- **N1 — Performance:** ≥ 3.0 Triton/CUDA fused-kernel throughput at N=1M oscillators; ≥2× the pure-PyTorch CPU fallback paths; ≥8× sweep speedup on 16 cores.
- **N2 — Platforms:** Linux, Windows (no runtime MSVC/nvcc JIT), macOS (CPU + Metal); CUDA GPUs; graceful CPU fallback everywhere.
- **N3 — Safety:** no `unsafe` outside audited kernel-FFI modules; no data races; NaN/Inf guards toggleable per build profile (`strict-checks` feature).
- **N4 — Distribution:** `pip install prin` yields prebuilt wheels (manylinux x86_64/aarch64, Windows x86_64, macOS universal2) with no compiler on the user machine.
- **N5 — Maintainability:** strict typing throughout; **one algorithm, one implementation** (backend dispatch inside `prin-kernels` only).
- **N6 — License:** MIT.

## 4. Architecture

See `crates/README.md` for the crate map and the archived plan §5 for the full
architecture diagram. Design rules (normative):

1. **One algorithm, one implementation.** Never duplicate math at call sites.
2. **The Python layer contains no numerics.**
3. **State is explicit.** Struct-of-arrays oscillator state; no hidden globals; deterministic seeding threaded through every stochastic entry point (single counter-based `Seed` type, Philox/PCG64).
4. **Feature flags:** `cuda`, `wgpu`, `npu`, `strict-checks`, mirrored as wheel variants where needed.
5. **Crate layering:** `dynamics → {metrics, tensor, kernels} → {sim, train, daemon} → py`. `prin-py` is the only crate that links Python.

## 5. Numerical parity program

Summarized from the archived plan §7 (normative):

1. **Golden-trajectory corpus** built from PRINet 3.0.0 *before* new numerics land (~500 cases; `parity/corpus/`).
2. **Tolerances:** trajectories `rtol=1e-6, atol=1e-8` (float64 reference); chaotic regimes compared statistically beyond the shadowing horizon; metrics/decompositions `rtol=1e-10`.
3. **Differential CI** (`.github/workflows/parity.yml`): old + new installed in one venv; golden corpus + hypothesis fuzzing.
4. **Benchmark-result parity:** full re-run of the benchmark suite; scientific conclusions unchanged; deviations documented in the Parity Report.
5. **Bit-level reproducibility:** all RNG behind the single `Seed` type; exact reproducibility across CPU/GPU and across runs.
6. **Preserved numerical hazards:** phase wrap `% 2π`; amplitude clamp `[1e-6, 10]`; derivative clamp `±1e4`; coupling normalization `1/N` vs `1/k`; φ₁(λ)→1 limit handling; STE forward-hard/backward-soft identity.

## 6. Phased roadmap

Dependency-ordered; each phase ends with green CI and a tagged pre-release.

| Phase | Scope | Exit criteria |
|---|---|---|
| **0 — Foundation** | Repo scaffold (this commit), maturin wheels on 3 OS targets in CI; spikes: (a) DLPack round-trip overhead, (b) CubeCL fused mean-field RK4 vs 3.0 Triton at N=1M, (c) `ort` DirectML/VitisAI check; golden corpus generation | Spikes meet §3.2 N1 targets (go/no-go gate — else revisit technology choices); corpus committed |
| **1 — Dynamics core** | `prin-dynamics` (state, models, Euler/RK4/RK45, PAC, coupling, k-NN index), `prin-metrics`; CPU only. Python-layer porting (datasets, reporting) starts in parallel | Parity suite green for all non-trainable dynamics; property tests green |
| **2 — Advanced numerics + sim** | Exponential/multi-rate integrators, continuous band networks, temporal propagator, sweeps, `prin-tensor`, `prin-sim` | OscilloSim parity at N≤1M on CPU; ≥8× sweep speedup |
| **3 — GPU kernels** (parallel with 2) | `prin-kernels`: fused mean-field RK4, sparse k-NN, PAC, fused discrete step, hierarchical reductions; CUDA + wgpu | §3.2 N1 GPU targets met on the self-hosted runner; kernel-equivalence tests green |
| **4 — Trainable stack + torch bridge** | `prin-train`, Python `prin.nn` autograd bridges, PhaseTracker, HybridPRINetV2, baselines, ablations | PhaseTracker ≥3.0 IP scores on temporal CLEVR-N; gradcheck green; bridge overhead <5% |
| **5 — Daemon + experiment tooling** | `prin-daemon`, training hooks, MOT evaluation, temporal metrics, adversarial/stats tools | Daemon latency target met; MOT metrics match motmetrics reference |
| **6 — Benchmarks, repro, docs, release** | `benchrunner` CLI, figure/table generators, `tools/reproduce.py`, full benchmark re-run, Parity Report, Migration Guide, notebooks, docs site | Reproducibility byte-identical; all CI green; `1.0.0-rc1` wheels published |
| **7 — Experimentation & Benchmarking Campaign** | Comprehensive pre-registered campaign (tracks C1 parity, C2 performance, C3 scientific replication, C4 new capability) per the Experimentation Standards; begins only when Phases 0–6 are complete and audited | Campaign plan executed; every experiment pre-registered (expected results + failure conditions **before** execution) and reported; Parity Report + campaign summary published; any conclusion-changing result resolved as a D1 deviation |

Every phase is decomposed into **work packages** executed through the Session
Cycle of §8.1 — there is no path to `main` outside that cycle. The complete
prospective decomposition is the 198-session execution ledger at
`DOCS/sessions/SESSION_REGISTER.md` (39 WPs × S1–S4, eight experiments ×
E1–E5, campaign planning/synthesis). Its traceability matrix maps every F/N
requirement, phase exit, risk, numerical hazard, and Definition-of-Done item.
Future session scope/order changes require the amendment protocol in §8.3.

### 6.1 First governed work package — WP-001

- **Title:** Foundation baseline and traceability.
- **Scope:** repository-state inventory; PRINet 3.0 public-API/module-to-WP
  traceability matrix; metadata consistency automation; baseline quality,
  security, CI, packaging, and governance measurements.
- **Acceptance:** automation is tested; every 3.0 module/public symbol has an
  assigned future WP; all baseline gaps are evidence-backed and recorded;
  no numerical implementation is introduced.
- **Non-goals:** numerical algorithms, performance conclusions, golden-data
  generation.
- **First session:** `DOCS/sessions/phase-0/0001-wp001-s1-foundation-baseline-and-traceability.md`.

## 7. Risk register

Maintained from the archived plan §13; top risks:

| # | Risk | Mitigation |
|---|---|---|
| 1 | CubeCL kernels can't match Triton at N=1M | Phase 0 spike gates; fallback `cudarc` hand-written CUDA or retain Triton behind the Python layer |
| 2 | Torch-bridge autograd overhead | Phase 0 DLPack spike; batch boundary crossings (one call per integration); Rust custom backward |
| 3 | Numerical drift breaks published results | Golden corpus + differential CI from day one; Parity Report before release |
| 4 | `ort` lacks VitisAI EP parity | Keep NPU path in Python `onnxruntime` (small, perf-uncritical) |
| 5 | Burn autodiff gaps (STE, complex tanh, HEP) | Closed-form adjoints as custom backward ops |
| 6 | Scope creep from 62 legacy benchmarks | Benchmarks are consumers: 9 category packages on shared drivers; old JSON artefacts stay valid |
| 7 | Rust ramp-up | Simplest, best-specified code first; the 1,670-test acceptance suite as guardrails |

## 8. Governance and standards

All contributions are governed by the standards in `DOCS/standards/`:

- [Development Workflow and Audit Standards](standards/Development_Workflow_and_Audit_Standards.md) — **the execution methodology (§8.1)**
- [Coding Standards](standards/Coding_Standards.md)
- [Testing Standards](standards/Testing_Standards.md)
- [Documentation Standards](standards/Documentation_Standards.md)
- [Benchmarking and Reproducibility Standards](standards/Benchmarking_and_Reproducibility_Standards.md)
- [Experimentation Standards](standards/Experimentation_Standards.md)
- [Versioning and Release Standards](standards/Versioning_and_Release_Standards.md)

Plus the repository-level `CONTRIBUTING.md`, `CODE_OF_CONDUCT.md`, and
`SECURITY.md`.

### 8.1 Execution methodology — the Session Cycle (normative)

All work advances through fixed, ordered sessions (full definition:
Development Workflow and Audit Standards):

1. **S1 Coding** — implementation with tests written **in tandem** (same
   session, same commits).
2. **S2 Audit** — read-only comparison of repository state against this plan
   and the standards, producing an evidence-backed Audit Report
   (`DOCS/audits/`) with severity-classified findings (D1–D4).
3. **S3 Remediation** — fixes audit findings only; every finding ends `FIXED`
   or `AMENDED` (approved plan amendment). Deviations from the planned
   trajectory cannot persist unresolved past this session.
4. **S4 Documentation** — READMEs of every touched directory, CHANGELOG,
   docstrings/Sphinx/Migration Guide, and the Project State Report
   (`DOCS/reports/`) declaring the next work package.

Self-correction guarantee: the audit checklist is derived from this plan, so
any drift between code and plan surfaces as a finding within one cycle and is
forced to resolution (fix or amendment) before new feature work proceeds.
Upon completion of all roadmap phases, the project enters the Phase 7 campaign
(§6), in which **experimentation follows pre-registration**: expected results
and failure conditions are committed before any experiment executes.

### 8.2 Session Execution Plan (normative sequencing)

`DOCS/sessions/` contains one prospective contract for every currently planned
session from WP-001 through stable `1.0.0`. `SESSION_REGISTER.md` defines the
exact default order; `TRACEABILITY.md` proves coverage of this plan. Each brief
states predecessor/successor, entry conditions, scoped expectations, required
evidence, prohibitions, and exit/handoff gate.

Briefs do not prove completion and cannot override this plan, standards, or the
latest approved Project State Report. Status advances only from committed
evidence. Future briefs may be amended when evidence justifies it, but changes
to trajectory/order/scope are recorded openly under §8.3; silent drift is D3.
Unexpected D1/D2 work uses the complete conditional correction cycle in
`DOCS/sessions/contingencies/` before the blocked numbered session resumes.

### 8.3 Plan amendment log

| # | Date | Section | Change | Approved by |
|---|---|---|---|---|
| 1 | 2026-07-10 | §6, §8, §9 | Added Session Cycle methodology, Phase 7 campaign, workflow/experimentation standards, DoD items 10–12 | maintainer |
| 2 | 2026-07-12 | §6.1, §8.2–§8.3 | Added the 198-session execution ledger, WP-001 declaration, complete requirement traceability, and conditional correction-session protocol | maintainer request |

## 9. Definition of Done

PRIN `1.0.0` ships when **all** of the following hold:

1. Every PRINet 3.0 public symbol (175+) has a working equivalent; renames documented in the Migration Guide.
2. The ported acceptance suite (~1,670 tests) passes on Linux + Windows, Python 3.11–3.13.
3. The parity suite passes at §5 tolerances; the Parity Report is published.
4. GPU and CPU performance targets (§3.2 N1) are met; benchmark regression gates active in CI.
5. `tools/reproduce.py` regenerates all figures/tables with a matching SHA-256 manifest.
6. Prebuilt wheels install cleanly on manylinux, Windows, and macOS without a compiler; wheel smoke test green.
7. Subconscious controller inference works on CPU, DirectML, and (where available) Ryzen AI NPU.
8. Docs site builds and deploys; crates documented on docs.rs; all four notebooks run end-to-end.
9. `cargo clippy -D warnings`, `cargo audit`, `ruff`, `mypy --strict`, `bandit`, and `pip-audit` are all clean.
10. Docstring coverage at threshold: 100% of public API (Rust `missing_docs` clean; Python public symbols), ≥95% overall (`interrogate`).
11. Every closed cycle has its Audit Report and Project State Report; the deviation ledger shows no open findings.
12. The Phase 7 campaign is complete: all experiments pre-registered and reported per the Experimentation Standards; campaign summary published.

---

*The directory `DOCS/archive and reference from PRINet 3.0/` is archived
reference material only: nothing in it is imported, executed, or built by PRIN.*
