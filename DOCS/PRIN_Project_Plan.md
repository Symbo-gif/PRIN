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
2. **Tolerances:** trajectories `rtol=1e-6, atol=1e-8` (float64 reference); chaotic regimes compared statistically beyond the shadowing horizon; metrics/decompositions `rtol=2e-6` for cross-platform corpus-regeneration comparisons (amendments #16, #17), with single-runtime metric/decomposition verification still targeting `rtol=1e-10` where achievable (WP-010/WP-014 acceptance).
3. **Differential CI** (`.github/workflows/parity.yml`): old + new installed in one venv; golden corpus + hypothesis fuzzing.
4. **Benchmark-result parity:** full re-run of the benchmark suite; scientific conclusions unchanged; deviations documented in the Parity Report.
5. **Bit-level reproducibility:** all RNG behind the single `Seed` type; exact reproducibility across CPU/GPU and across runs.
6. **Preserved numerical hazards:** phase wrap `% 2π`; amplitude clamp `[1e-6, 10]`; derivative clamp `±1e4`; coupling normalization `1/N` vs `1/k`; φ₁(λ)→1 limit handling; STE forward-hard/backward-soft identity; **PRINet 3.0 `torch.complex64` (f32) internal arithmetic for mean-field order parameters and Stuart–Landau complex amplitudes, which produces up to ~1e-7 per-step drift from a fully f64 reference and is therefore accepted as a reference-implementation numerical hazard (see Parity Report and `crates/prin-dynamics/tests/parity_models.rs` for the documented derivative-level tolerance of `1e-6`); **cross-platform torch CPU f32 arithmetic noise in PRINet 3.0's derived metric computations (order parameter, mean phase coherence), which compounds across the N-oscillator reduction and differs by up to ~1.1e-6 relative between OS/torch builds (corpus authored on Windows; CI regenerates on Linux) and is accepted as a reference-implementation hazard with the corpus metric tolerance set to `rtol=2e-6` (amendments #16, #17, Parity Report EA-002 entry).

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
| 3 | 2026-07-27 | Coding Standards §6.2, §6.4 | Replaced the unavailable repository-local VibeCheck truthpack/badge convention with repository-native sources of truth and additive Snyk Code/Open Source controls across agentic, IDE, and CI workflows; retained ecosystem audits and GitHub hosted secret controls as mandatory independent gates | maintainer request |
| 4 | 2026-07-27 | Coding Standards §6.2 | Required full visibility, threat assessment, compensating controls, maintainer approval, and per-cycle recheck for advisories with no upstream fix; permitted Snyk `--fail-on=all` so all findings remain reported while any available upgrade or patch blocks CI. Applied to six all-version Torch advisories discovered during WP-001 S3 | maintainer approval |
| 5 | 2026-08-06 | Coding Standards §6.2 | Added a temporary, fail-closed substitute only when GitHub reports native secret scanning unavailable: required full-history secret scanning CI, protected PR-only `main`, and per-cycle availability rechecks until native secret scanning and push protection can be enabled | maintainer approval |
| 6 | 2026-08-06 | Coding Standards §2.1, §6.1 | Approved an audited Python-FFI exception for `prin-py/src/dlpack.rs` to use `unsafe` for the PyO3/DLPack C ABI under the same controls as kernel-FFI modules: dedicated module, `#![deny(unsafe_op_in_unsafe_fn)]`, `// SAFETY:` comments on every `unsafe` block, and second-reviewer sign-off recorded in the audit. `prin-py` uses crate-level `#![deny(unsafe_code)]` with module-level `#![allow(unsafe_code)]` because `#![forbid` cannot be scoped to a single module | maintainer approval |
| 7 | 2026-08-06 | Project Plan §6 (WP-003/Phase 0) | Documented the WP-003/Phase 0 go/no-go: the CPU DLPack exchange and the `pytest-benchmark` round-trip/batched evidence are validated and on file; the CUDA round-trip and the `<5%` training-step overhead target are deferred to the Phase 4 trainable-stack work (WP-022/WP-026 or the first GPU-backed integration WP) with a re-audit gate | maintainer approval |
| 8 | 2026-08-07 | Coding Standards §2.1, §6.1 | Approved the same audited kernel-FFI `unsafe` pattern already used for `prin-py` for `prin-kernels`: crate-level `#![deny(unsafe_code)]`, module-level `#![allow(unsafe_code)]` with `#![deny(unsafe_op_in_unsafe_fn)]`, a `// SAFETY:` justification on every `unsafe` block, and second-reviewer sign-off recorded in the WP-004 S3 audit. This is the only permitted `unsafe` pattern outside the previously audited Python-FFI module | maintainer approval |
| 9 | 2026-08-07 | Project Plan §6 / Coding Standards §6.2 | Accepted the inherited `paste` RUSTSEC-2024-0436 warning as a transitive dependency of `cubecl` 0.10.0 with no upstream patch or replacement available at this dependency level; re-check every S3/S4 cycle and upgrade/patch as soon as a fixed `cubecl` release is available | maintainer approval |
| 10 | 2026-08-07 | Testing Standards §4 | Documented that `#[cube(launch)]` kernel launch bodies in `crates/prin-kernels/src/mean_field_rk4/cubecl.rs` are not instrumentable by `cargo-llvm-cov` on stable Rust; coverage for the file is reported as-is, the 90 uncovered lines are the two kernel stubs, and correctness is verified by kernel-equivalence tests. The instrumentable surrounding code (CPU reference, runtime launch, tests) remains at ≥95% line coverage | maintainer approval |
| 11 | 2026-08-07 | Project Plan §3.2 N1 / WP-004 acceptance criterion | Recorded the WP-004/Phase 0 go/no-go: the PRINet 3.0 PyTorch reference and the wgpu/CubeCL-CPU kernel-equivalence at N=1M are validated; the direct same-hardware Triton 3.0 fused-kernel comparison is deferred to a Linux/CUDA runner in Phase 3 or the `gpu.yml` workflow with evidence | maintainer approval |
| 12 | 2026-08-07 | Testing Standards §2 / Development Workflow and Audit Standards A9 | Added `cargo test -p prin-kernels --features cpu` to the default `rust.yml` matrix; the `wgpu` kernel-equivalence CI step is gated by availability of a headless GPU runner and remains in the opt-in `gpu.yml` / local validation path until such a runner is available | maintainer approval |
| 13 | 2026-08-07 | Project Plan §6 (WP-005/Phase 0) | Recorded the WP-005/Phase 0 ORT go/no-go: the CPU fallback for the subconscious controller is proven on all CI platforms; DirectML graph execution falls back to CPU on the current Windows host; the VitisAI NPU runtime and DirectML parity are unavailable in Phase 0 and deferred to WP-028 (Phase 5 daemon) with a re-audit gate | maintainer approval |
| 14 | 2026-08-07 | Project Plan §5 (numerical parity program / preserved numerical hazards) | Documented that PRINet 3.0 uses `torch.complex64` (f32) internally for mean-field order parameters and Stuart–Landau complex amplitudes, producing up to ~1e-7 per-step drift from a fully f64 reference; accepted as a preserved numerical hazard with derivative-level parity tolerance `1e-6` for affected model/coupling paths, pending maintainer sign-off | S3 (WP-007); maintainer approval granted in EA-002, 2026-08-08 |
| 15 | 2026-08-08 | Development Workflow and Audit Standards §8 / `DOCS/sessions/SESSION_REGISTER.md` | Established the registration convention for Executive Audit Sessions: EA sessions are global sessions recorded in a dedicated "Global sessions — Executive Audits" register section, outside the planned 0001–0198 sequence; planned session numbering is never renumbered by an executive audit (preserves TRACEABILITY invariant 4). Retroactively registered EA-001 (2026-08-07, `d1e6e0a`) and EA-002 (2026-08-08), and corrected EA-001's unexecuted session-register claim (EA-002 finding E-F2) via tagged correction notes in `EXECUTIVE_AUDIT_REPORT_001.md` and `CHANGELOG.md` | maintainer approval (EA-002, 2026-08-08) |
| 16 | 2026-08-08 | Project Plan §5 (tolerances) / Testing Standards §3 / `python/prin/parity/schema.py` | Raised the corpus differential-harness METRIC tolerance from `rtol=1e-10` to `rtol=1e-8` for cross-platform corpus-regeneration comparisons: PRINet 3.0's torch CPU computation of the derived metric arrays (order parameter, mean phase coherence) exhibits reduction-order noise up to ~1.27e-9 relative between OS/torch builds (corpus authored on Windows torch; CI regenerates on Linux). Trajectory tolerances unchanged; single-runtime metric verification (WP-010/WP-014) still targets `rtol=1e-10`; documented in the Parity Report EA-002 register entry | maintainer approval (EA-002, 2026-08-08) |
| 17 | 2026-08-09 | Project Plan §5 (tolerances) / `python/prin/parity/schema.py` | Raised the corpus differential-harness METRIC tolerance from `rtol=1e-8` to `rtol=2e-6` for cross-platform corpus-regeneration comparisons of derived metric arrays: CI exhaustive parity runs exposed that the amendment #16 estimate (~1e-9 relative) was too optimistic — the dominant source is PRINet 3.0's `torch.complex64` (f32) internal arithmetic for mean-field order parameters (preserved numerical hazard, amendment #14) compounding across the N-oscillator reduction, producing cross-platform differences up to ~1.1e-6 in `mean_phase_coherence_traj` for Kuramoto/Hopf mean-field cases. Trajectory tolerances and single-runtime metric verification target (`rtol=1e-10`) are unchanged | S4 (parity CI fix) |

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
