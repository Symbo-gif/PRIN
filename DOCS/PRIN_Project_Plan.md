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
6. **Preserved numerical hazards:** phase wrap `% 2π`; amplitude clamp `[1e-6, 10]`; derivative clamp `±1e4`; coupling normalization `1/N` vs `1/k`; φ₁(λ)→1 limit handling; STE forward-hard/backward-soft identity; **PRINet 3.0 `torch.complex64` (f32) internal arithmetic for mean-field order parameters and Stuart–Landau complex amplitudes, which produces up to ~1e-7 per-step drift from a fully f64 reference and is therefore accepted as a reference-implementation numerical hazard (see Parity Report and `crates/prin-dynamics/tests/parity_models.rs` for the documented derivative-level tolerance of `1e-6`); **cross-platform torch CPU f32 arithmetic noise in PRINet 3.0's derived metric computations (order parameter, mean phase coherence), which compounds across the N-oscillator reduction and differs by up to ~1.1e-6 relative between OS/torch builds (corpus authored on Windows; CI regenerates on Linux) and is accepted as a reference-implementation hazard with the corpus metric tolerance set to `rtol=2e-6` (amendments #16, #17, Parity Report EA-002 entry). **Explicit non-hazard exception (amendment #25):** `prin-metrics::chimera::strength_of_incoherence`/`strength_of_incoherence_temporal` are deliberately, permanently *not* parity-matched to the PRINet 3.0 fixture — PRINet 3.0's wrap-centring formula is an upstream defect (EMA-001 M-F1, Z3-confirmed), not a legitimate convention difference, so PRIN's corrected implementation is authoritative and the resulting fixture divergence is not a "preserved numerical hazard" in the sense of the other items in this list.

## 6. Phased roadmap

Dependency-ordered; each phase ends with green CI and a tagged pre-release.

| Phase | Scope | Exit criteria |
|---|---|---|
| **0 — Foundation** ✅ COMPLETE | Repo scaffold (this commit), maturin wheels on 3 OS targets in CI; spikes: (a) DLPack round-trip overhead, (b) CubeCL fused mean-field RK4 vs 3.0 Triton at N=1M, (c) `ort` DirectML/VitisAI check; golden corpus generation | Spikes meet §3.2 N1 targets (go/no-go gate — else revisit technology choices); corpus committed |
| **1 — Dynamics core** ✅ COMPLETE | `prin-dynamics` (state, models, Euler/RK4/RK45, PAC, coupling, k-NN index), `prin-metrics`; CPU only. Python-layer porting (datasets, reporting) starts in parallel | Parity suite green for all non-trainable dynamics; property tests green |
| **2 — Advanced numerics + sim** ✅ COMPLETE | Exponential/multi-rate integrators, continuous band networks, temporal propagator, sweeps, `prin-tensor`, `prin-sim` | OscilloSim parity at N≤1M on CPU; ≥3.5× sweep speedup on 8 physical cores (amendment #21, re-scoped from the original ≥8×/16-core target after S1 benchmark evidence showed a memory-bandwidth/SMT ceiling) |
| **3 — GPU kernels** (parallel with 2) ✅ COMPLETE | `prin-kernels`: fused mean-field RK4, sparse k-NN, PAC, fused discrete step, hierarchical reductions; CUDA + wgpu | §3.2 N1 GPU targets met on the self-hosted runner; kernel-equivalence tests green |
| **4 — Trainable stack + torch bridge** ✅ COMPLETE | `prin-train`, Python `prin.nn` autograd bridges, PhaseTracker, HybridPRINetV2, baselines, ablations | PhaseTracker ≥3.0 IP scores on temporal CLEVR-N; gradcheck green; bridge overhead <5% at moderate/large batch and shape sizes (amendment #30, re-scoped from an unqualified <5% target after three independent measurement rounds showed a ~38–41% architecturally fixed dispatch-cost floor at small shapes) |
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
| 18 | 2026-08-10 | Project Plan §6 (WP-012) | Clarified WP-012 "multi-rate" scope: the `MultiRateIntegrator` implements uniform sub-stepping (dividing the outer timestep into `sub_steps` equal inner RK4/Euler steps applied to all oscillators), matching the PRINet 3.0 reference implementation. Band-aware per-`freq_band` scheduling (different step sizes per frequency band) is a deferred capability, not part of WP-012. The WP-012 declaration text "multi-rate sub-stepped RK4 for stiff/slow oscillator partitions" is read as "uniform sub-stepping sufficient to resolve the fastest partition" | S3 (WP-012); WP012-F4 (D3) |
| 19 | 2026-08-10 | Project Plan §4/§5 / WP-013 declaration (`DOCS/reports/012-project-state.md` §6) | Recorded the WP-013 band-network composition decision. PRINet 3.0's `ThetaGammaNetwork`/`DeltaThetaGammaNetwork` are *steppers*: a per-band `KuramotoOscillator`, PAC applied as an instantaneous amplitude assignment between band steps, and a per-band `MultiRateIntegrator` with `sub_steps = floor(f_fast / f_slow)` embedded in the network. PRIN's `BandNetwork` is instead a single continuous ODE right-hand side over the concatenated state implementing `Dynamics`, so it composes with every PRIN `Integrator` rather than embedding one. Three consequences are accepted as the intended trajectory: (a) intra-band terms are the identical Kuramoto equations for the configured `CouplingMode`, including the reference's `sparse_knn`, and are parity-verified per mode against `prinet==3.0.0` (`crates/prin-dynamics/tests/parity_bands.rs`); (b) PAC enters `dA_fast/dt` as the relaxation term `λ_fast·(A_target − A_fast)` toward the reference's modulation target `A_fast·[1 + m·cos(mean(φ_slow) + offset)]`, which is the continuous-time analogue of the reference's discrete assignment and is parity-verified against the reference's `PhaseAmplitudeCoupling.modulate` target; (c) per-band sub-stepping is supplied by driving the network with `MultiRateIntegrator`, with the reference's sub-step count exposed as `BandNetwork::theoretical_capacity`. Whole-network step-for-step trajectory parity with the reference stepper is therefore not claimed and is not a WP-013 acceptance criterion; band/temporal golden-trajectory acceptance is evidenced by `parity_bands.rs` and `parity_temporal.rs` | S3 (WP-013); WP013-F2 (D2) |
| 20 | 2026-08-14 | Project Plan §6 / WP-016 declaration (`DOCS/reports/015-project-state.md` §6) | Narrowed the WP-016 ("Parallel sweeps, CPU optimization, and Phase 2 gate") scope to `crates/prin-sim/` only. The original declaration also listed `crates/prin-py/` (sweep/engine PyO3 bindings) and `crates/prin-kernels/` (CPU reference work), neither of which S1 touched (WP016-F6, S2 audit `DOCS/audits/016-wp016-audit.md`). S1 delivered the rayon sweeps, CSR SpMV, and benchmark-gate work entirely inside `prin-sim`; extending Python bindings and a `prin-kernels` CPU reference implementation is new feature work outside S3's remediation-only mandate (session brief `DOCS/sessions/phase-2/0063-wp016-s3-...md`, "no feature work"). `prin-py` sweep/engine bindings and any `prin-kernels` CPU-reference work move to a future WP, to be declared in the WP-016 S4 Project State Report. The Phase 2 gate validation report and the acceptance criteria (sweep speedup, CPU path speedup, N=1M-where-feasible parity) are unaffected and remain WP-016 obligations | maintainer approval (MichaelMaillet, 2026-08-14); WP016-F6 (D3) |
| 21 | 2026-08-14 | Benchmarking and Reproducibility Standards §2.4 (performance targets) | Amended the "CPU fallback paths" and "Parameter sweeps" performance targets from "≥ 2× pure PyTorch" / "≥ 8× on 16-core CPU" to hardware-scoped, evidence-based targets: "≥ 1.5× on 8-physical-core/16-SMT-thread reference hardware" (CPU/SpMV paths) and "≥ 3.5× on 8-physical-core/16-SMT-thread reference hardware, measured at config count ≈ physical core count" (sweeps). WP016-F1 (D1) remediation replaced the S1 `par_bridge()`/unconditional `par_iter()` implementation (which was up to 6× *slower* than serial, per the S2 audit) with a size-gated sequential/rayon dispatcher (`crates/prin-sim/src/dispatch.rs`) and eliminated the regression, but S3 benchmark evidence (`crates/prin-sim/benches/sweep_bench.rs`, serial baseline via a dedicated 1-thread `rayon` pool) on the 8-physical-core/16-SMT reference machine shows a genuine hardware ceiling, not a code defect: sweep speedup peaks at 3.92× at 8 configs and degrades to 1.8–2.1× at 16–64 configs (SMT sibling contention on compute-bound work), and SpMV/`compute_derivatives` plateaus at 1.51–1.60× up to N=1M (memory-bandwidth-bound sparse kernel; thread count cannot close a memory-bus ceiling). The original "16-core"/"pure PyTorch" targets assumed independent (non-SMT) cores and a cross-language harness that does not exist for `prin-sim`; both figures were always measured, per the established WP-016 S1/S2 methodology, as internal Rust multi-core-vs-1-thread speedup. Closes WP016-F1 as AMENDED | maintainer approval (MichaelMaillet, 2026-08-14); WP016-F1 (D1) |
| 22 | 2026-08-14 | Versioning and Release Standards §1 (phase-exit tagging) | Recorded that the Phase 1 exit pre-release tag was skipped as a process gap and formally closes it. PSR-011 (2026-08-09) declared Phase 1 complete and stated `v0.2.0-alpha.1` was "ready pending maintainer approval," but no `chore: release v0.2.0-alpha.1` commit or tag was ever created; `Cargo.toml`/`pyproject.toml` stayed at `0.1.0-alpha.1` through five subsequent cycles (WP-012..WP-016) and the pending action was never re-raised as an open risk in any of PSR-012 through PSR-015 (untracked drift, EA-003 finding E-F6, D2). The version then jumped directly to `0.3.0-alpha.1` in the Phase 2 exit release commit (`fbe1c92`), and — independently — neither `v0.1.0-alpha.1` nor any later tag was ever pushed to `origin` (`git ls-remote --tags origin` returns none), so `release.yml` (tag-triggered wheel/PyPI/crates.io publish) has never executed for this project. A retroactive `v0.2.0-alpha.1` tag on the Phase 1 exit commit (`a354a2d`) would misrepresent the historical record, since `Cargo.toml` at that commit reads `0.1.0-alpha.1`, not `0.2.0-alpha.1`. `v0.3.0-alpha.1` therefore retroactively and jointly covers the Phase 1 and Phase 2 exit-tagging obligations; the underlying Phase 1/2 engineering work was independently and substantively verified (PSR-011, PSR-016 exit-gate verdicts) regardless of the missing tag artifact. Actually creating and pushing the `v0.1.0-alpha.1`/`v0.3.0-alpha.1` tags — which triggers a real PyPI/crates.io publish via `release.yml` — is deliberately left to an explicit, separate maintainer-confirmed action rather than being executed inside this audit; the maintainer confirmed during EA-003 that tag creation/push should **not** happen in this session | maintainer approval (EA-003, MichaelMaillet, 2026-08-14); WP-011/WP-016 (D2) |
| 23 | 2026-08-14 | Development Workflow and Audit Standards §8 / `DOCS/sessions/SESSION_REGISTER.md` / new standard `Executive_Mathematical_Audit_Governance_and_Methodology.md` | Introduced Executive Mathematical Audit (EMA) Sessions: a new, dedicated global-session audit type that independently re-verifies PRIN's mathematical claims (dimension E1 and adjacent numerical claims) using `math-audit-mcp`, an external tool that recomputes/proves/falsifies each claim with SymPy, SciPy, Z3, mpmath, and NetworkX rather than reading the target code's own reasoning — a structurally stronger evidentiary channel than an Executive Audit's direct source review, which EA-003 finding E-F5 showed can itself be satisfied by a test suite that only verifies internal invariants. EMA is additive: it does not replace EA sessions, the parity corpus, or the Rust/Python test suites. Registered using the identical "global session outside the planned 0001–0198 sequence" precedent amendment #15 established for EA sessions (`EMA-NNN` identifiers, `M-FN` finding prefix, own report template `DOCS/audits/TEMPLATE_Executive_Math_Audit_Report.md`). The tool itself is not vendored into this repository (same external-tool posture as Snyk/`cargo-audit`/`pip-audit`); PRIN owns only `tools/math_audit_policy.yaml`, `tools/math_audit_claims/`, `tools/math_audit_run.py`, and the resulting `EVIDENCE/math-audit/` evidence chain | maintainer request (EMA-001 session initiation, 2026-08-14) |
| 24 | 2026-08-14 | `Executive_Mathematical_Audit_Governance_and_Methodology.md` §3 / `tools/math_audit_policy.yaml` | EMA-001 remediation session: enabled the optional Lean 4 adapter (`adapters.enable_lean: true`) that §3 had left disabled pending "a separate plan amendment." Scope is narrow: bare `lean` (no mathlib dependency) is used for `decide`-based kernel-checked formal proofs of two new claims, `GRA-01-LEAN` and `TEN-01-LEAN` (`tools/math_audit_claims/prin-dynamics-graph-topology.json`, `prin-dynamics-tensor-contracts.json`), which formally corroborate GRA-01/TEN-01's concrete, finite, decidable graph/matrix properties and resolve to genuine `PASS` under the strict policy's `high_severity_requires_symbolic_or_formal` gate (`EVIDENCE/math-audit/audits/bundle-861cee2f1497/report.md`, `bundle-492de710aafb/report.md`). `adapters.enable_wolfram` stays `false`: Wolfram Engine was used only as informal, out-of-band secondary corroboration for the `ode_property` claims (`EVIDENCE/math-audit/manual/`), never as a policy-gating required check, so it never crossed the threshold requiring an amendment | maintainer request (EMA-001 remediation session, MichaelMaillet, 2026-08-14); M-F3 |
| 25 | 2026-08-14 | Project Plan §5 (preserved numerical hazards) / `crates/prin-metrics/src/chimera.rs` / `crates/prin-metrics/tests/parity_chimera.rs` | EMA-001 remediation session, M-F1 (D1): fixed `strength_of_incoherence`'s per-pair phase-difference wrap, which computed `diff.rem_euclid(2*pi) - pi` (mapping an in-phase pair, raw difference 0, to `-pi` instead of `0`) instead of the documented "centred to `[-pi, pi)`" contract (Z3-confirmed counterexample, `EXECUTIVE_MATH_AUDIT_REPORT_001.md` M-F1). Investigating the fix's parity-test breakage discovered that PRINet 3.0's own reference (`oscillosim.py:876-878`) has the identical defect under the identical "Centre to `[-pi, pi]`" comment — this is an upstream implementation bug, not a legitimate PRINet-vs-PRIN convention difference, so it is **not** treated as a preserved numerical hazard in the amendment #14/#16/#17 sense (those document equally-valid f32-vs-f64/convention choices). PRIN's corrected implementation is therefore deliberately, permanently non-parity with the PRINet 3.0 fixture for `strength_of_incoherence`/`strength_of_incoherence_temporal` specifically; `parity_chimera.rs` now positively demonstrates (via a test-local reimplementation of PRINet's actual buggy formula) that the fixture is explained by exactly this defect and nothing else, rather than silently weakening or deleting the parity assertion | maintainer approval (MichaelMaillet, 2026-08-14); M-F1 (D1) |
| 26 | 2026-08-18 | `.github/workflows/gpu.yml` / `DOCS/reports/DEFERRED_VALIDATION_REGISTER.md` (DV-001, DV-002, DV-005) | R24's consolidated GPU CI runner strategy decision, made at its assigned checkpoint (WP-022 S1, session 0085): PRIN adopts a **self-hosted GPU runner** strategy — confirming and extending the design `gpu.yml` already anticipated (`runs-on: [self-hosted, gpu]`, added under amendment #12's precedent) rather than a cloud GPU CI provider or a time-bounded local-only acceptance. `gpu.yml` is extended in this session to also run the `wgpu` kernel-equivalence suite (`cargo test --workspace --features wgpu`) alongside the existing CUDA job, so once a runner is registered both DV-001's local-CUDA/wgpu evidence and DV-002's wgpu CI gap close in the same job. Registering the physical/virtual machine as a GitHub Actions self-hosted runner labeled `[self-hosted, gpu]` is an out-of-band operational action (GitHub Settings → Actions → Runners, on the target machine) outside repository source changes, so it is **not** claimed as complete here; DV-001/DV-002 remain OPEN pending that registration, and DV-001's Triton comparison specifically needs a **Linux** GPU machine registered under the same labels (Triton does not support Windows), which this decision does not by itself provide — the current on-hand hardware (RTX 4060, Windows) can close the wgpu/CUDA halves of DV-001/DV-002 once registered, but not the Triton comparison. DV-005 (CUDA DLPack full validation) remains deferred to Phase 4's actual torch-bridge integration (WP-025) per amendment #7 and is unaffected by this CI-runner decision — WP-022 S1's Burn primitives are CPU-only (`NdArray`) and do not touch DLPack | maintainer approval (MichaelMaillet, 2026-08-18); R24 |
| 27 | 2026-08-18 | Project Plan §6 / Coding Standards §6.2 (DV-017) | **Threat assessment (Coding Standards §6.2):** advisory `RUSTSEC-2025-0141` — `bincode` 2.0.1 is flagged `informational = "unmaintained"` (no `patched` versions listed; not a CVE/vulnerability class advisory). Origin: the bincode maintainers ceased development permanently following a doxxing/harassment incident; upstream states 1.3.3 is considered "complete," not that 2.0.1 is insecure. Affected API/exploit prerequisites: none — the advisory carries no vulnerability, exploit, or affected-function disclosure of any kind, only a maintenance-status flag. Dependency path: transitive via `burn-core` 0.16.1's `BinBytesRecorder`/`BinFileRecorder` (`cargo tree -p prin-train -i bincode`), exercised by `prin-train`'s `Module::into_record`/`load_record` roundtrip tests (`bands.rs`/`layers.rs`); no PRIN code calls `bincode` directly. No newer `bincode` 2.x release exists (`cargo update -p bincode --dry-run`: already latest) and `burn` 0.16 ships no alternative recorder that avoids it. Compensating controls: `cargo audit` reports the advisory as a non-blocking warning (exit code 0); record round-trips are covered by dedicated regression tests (`record_roundtrip_preserves_parameters`, both modules) so any future functional regression in the serialization path — maintained or not — is caught independent of upstream status. **Accepted** the inherited `bincode` RUSTSEC-2025-0141 warning under the same disposition and cadence as amendment #9/DV-008 (`paste`): re-check every S3/S4 cycle with `cargo audit`, and upgrade or switch recorder as soon as Burn moves off `bincode` or a maintained fork appears. Closes WP022-F1 as AMENDED | maintainer approval (MichaelMaillet, 2026-08-18); WP022-F1 (D4) |
| 28 | 2026-08-18 | Development Workflow and Audit Standards §3, §4, §7 / Coding Standards §4 | **Push/CI cadence change:** every session (S1–S4) continues to commit locally at its own exit gate, but only the **S4** commit that closes a cycle is now **pushed** to `origin/main`, carrying the full S1–S4 commit range for that WP in one push — the sole point at which CI runs for the cycle. Previously each session pushed individually (observed practice: e.g. WP-022 S1 commit `8bce1a2`, S3 commits `c3ae5c8`/`a5458ef`, S4 commit `f3aaba4` each triggered their own CI run). Rationale: CI minutes/wall-clock were being spent on S1–S3 intermediate states that are, by design, revised or fixed before the cycle closes (S2 is read-only/audit-only and S3 exists specifically to fix what S2 finds), so per-session CI on those states verifies states the cycle does not ship; batching to one CI run per closed cycle is the meaningful gate. Consequences recorded in the same edit: S2's audit checklist item A9 cannot check live CI during S1–S3 under this cadence (nothing has been pushed yet) and instead relies on local gate reproduction (Coding Standards §5) plus ecosystem-native security/quality tool output reproduced locally; S4's exit criteria now explicitly require the push itself and a fully green CI run over the whole batched range before the cycle is declared closed. The existing hotfix exception (§7: broken `main` or a live security finding may bypass session ordering) is unchanged and is the only case that may push outside this cadence, retro-audited at the next S2 | maintainer approval (MichaelMaillet, 2026-08-18) |
| 29 | 2026-08-19 | Development Workflow and Audit Standards §5 (D3) / `DOCS/reports/023-project-state.md` §7 (WP-024 declaration) | **WP-024 declaration naming correction.** PSR-023 §7's WP-024 acceptance criteria name `PhaseAdam` (a Riemannian phase-angle Adam variant) and `KuramotoOptimizer`, with file paths `phase_adam.rs`/`kuramoto_optimizer.rs`; `grep -rl "PhaseAdam\|KuramotoOptimizer"` against the full archived PRINet 3.0 reference tree and `DOCS/` returns only `023-project-state.md` itself — neither class ever existed in the reference implementation. The session brief (`DOCS/sessions/phase-4/0093-wp024-s1-oscillator-aware-optimizers.md`) mission text and the Rebuild Planning Document's normative `nn/optimizers.py` mapping (Project Plan §1) both independently name `SCALR`/`RIP`/`SyncGD`, matching PRINet 3.0's actual `SCALROptimizer`/`RIPOptimizer`/`SynchronizedGradientDescent` classes. WP-024 S1 delivered `Scalr`/`Rip`/`SyncGd` (`crates/prin-train/src/scalr.rs`/`rip.rs`/`sync_gd.rs`) against this evidence-backed reference, per CLAUDE.md ("verify implementation facts from the repository; do not invent... evidence") and F1 feature-parity (a non-reference symbol cannot serve F1). PSR-023 §7's acceptance-criteria bullet naming `PhaseAdam`/`KuramotoOptimizer` and `phase_adam.rs`/`kuramoto_optimizer.rs` is read, retroactively and for all downstream purposes (PSR-024, the traceability matrix, `SESSION_REGISTER.md`), as naming `SCALR`/`RIP`/`SyncGD` and `scalr.rs`/`rip.rs`/`sync_gd.rs` respectively — the delivered, PRINet-3.0-verified scope. Same disposition class as amendments #18–#20 (declaration-text drift corrected by amendment, no direct PSR edit). Closes WP024-F1 as AMENDED; closes DV-020 | S3 (WP-024, session 0095); WP024-F1 (D3); maintainer approval (MichaelMaillet, 2026-08-19) |
| 30 | 2026-08-21 | Project Plan §6 (Phase 4 exit criterion) / `DOCS/reports/DEFERRED_VALIDATION_REGISTER.md` (DV-021) | **Bridge-overhead exit criterion re-scoped to evidence (Phase 4 analytics R29).** Plan §6's original Phase 4 exit criterion, "bridge overhead <5%," carried no qualifying language. Three independent, increasingly rigorous measurement rounds — WP-025 S3's 5-run process-level median-of-medians benchmark, the WP-025 S3-exec performance-engineering follow-up (`e720a24`), and WP-027 S1's re-corroboration — consistently show the target is met at moderate/large shapes but not at small ones: `small_32osc_16dims_8batch` measured **+39.8%**, **+40.6%**, and **+37.8%** overhead across the three rounds; `moderate_128osc_64dims_32batch` measured **+5.3%**, **+4.5%**, and **+6.5%**, close to the original target. Root cause, confirmed by direct profiling and source reading of `crates/prin-py/src/bindings/train.rs::forward()` (WP-025 S3-exec): a largely fixed per-call `torch.autograd.Function.apply()` node-construction/bookkeeping and `torch.utils.dlpack.from_dlpack()` dispatch cost (~3 ms) dominates at small absolute compute time; this cost is inherent to the mandated `torch.autograd.Function`/DLPack bridge architecture and is not reachable from the Rust side without abandoning that architecture (out of scope) or batching multiple bridge calls at a higher application level (a caller-side decision, not something the bridge itself can force). A genuine, verified Rust-side inefficiency (a redundant Tensor→data round-trip) was found and fixed during the WP-025 S3-exec investigation but did not measurably close the gap, positively ruling out "an unfixed Rust-side oversight" as the explanation. **Revised Phase 4 exit criterion (Plan §6):** "bridge overhead <5% at moderate/large batch and shape sizes (≥128 oscillators/64 dims/32 batch); small-shape calls (as small as 32 oscillators/16 dims/8 batch) carry a measured, architecturally fixed dispatch overhead of ~38–41%, dominated by per-call `torch.autograd.Function`/DLPack dispatch cost rather than Rust-side computation, and are not held to the <5% target." Same disposition class and precedent as amendment #21 (Phase 2 sweep-speedup re-scoping): a materially large but honestly measured, architecture-attributed gap between an early aspirational target and reality, resolved by revising the target's own text to the evidence rather than leaving an indefinitely open deviation. Closes DV-021 as AMENDED | maintainer approval (MichaelMaillet, 2026-08-21); R29 (Phase 4 analytics) |

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
