# PRIN Phase 7 — Experimentation and Benchmarking Campaign Plan

**Status:** APPROVED — FROZEN (2026-09-21; see §14)
**Campaign session:** 0153 — Campaign E0 (`DOCS/sessions/phase-7/0153-campaign-e0-planning.md`)
**Authors:** MichaelMaillet (maintainer); Claude Opus 5 (AI pair, drafting)
**Date:** 2026-09-21
**Maintainer approval:** MichaelMaillet, 2026-09-21 — recorded in §14 (decisions A1–A4); EXP-001 E1 (session 0154) is authorized
**Baseline code version:** `prin 1.0.0-rc1` @ `8ce115f` (`origin/main` HEAD; `tools/check_ci_green.py 8ce115f` → `RESULT: all required workflows green` for `rust`, `python`, `parity`, `repro`, `snyk`, `gpu`)
**Authority:** Project Plan §6 (Phase 7 row), §8.1, §9 DoD #12; Experimentation Standards §2–§4; Benchmarking and Reproducibility Standards §1–§3; Development Workflow and Audit Standards §3 ("Campaign trigger"), §5, §8. If this plan conflicts with a normative standard, the standard wins.

> This plan is the campaign-level artefact required by Experimentation
> Standards §3 ("The campaign plan … is itself an artefact … approved before
> the first campaign experiment starts"). It orders the experiments, fixes the
> shared rules every pre-registration inherits, and records the maintainer's
> approval. It contains **no hypotheses and no results**: hypotheses belong to
> each experiment's pre-registration (E1), results to its report (E5).

---

## 0. How to read this plan

| If you are… | Read |
|---|---|
| Pre-registering an experiment (E1) | §2 (your row), §5 (hardware you may claim), §6 (seed rule), §7 (artefact layout you must emit), §8 (your budget cap), §9 (statistics you must use), §10 (abort/D1 rules you must restate) |
| Reviewing a pre-registration (E2) | §2 (registered expectation and brief-vs-standard reconciliation), §8, §9, §10 |
| Executing (E3) | §5.3 (quiescence), §7 (run IDs, append-only, manifests), §10 |
| Analysing / reporting (E4/E5) | §7.4 (regeneration path), §9, §10.4 (reversal handling) |
| Synthesising the campaign (E6, session 0194) | §3 (dependency closure), §11 (registered gaps), §13 (deliverable checklist) |

---

## 1. Campaign entry verification (session 0153 entry conditions)

| Entry condition (brief 0153) | Verdict | Evidence |
|---|---|---|
| Phases 0–6 and WP-038 are closed | ✅ MET | `DOCS/reports/038-project-state.md` §4 "Phase 6 verdict: COMPLETE"; `SESSION_REGISTER.md` rows 0001–0152 `COMPLETE` |
| RC1 exists | ✅ MET | Tag `v1.0.0-rc1`; `release.yml` run `35245682857`; `prin-core` 1.0.0rc1 on PyPI; 7 crates on crates.io (PSR-038 §1) |
| All required tooling exists | ✅ MET | `benchmarks/benchrunner` (9 categories, `--list` verified), `tools/reproduce.py` (`append_manifest`/`verify_manifest`), `parity/` (504-case corpus + differential suite), `prin.reporting` (deterministic Markdown/leaderboard/figure/table generators), statistics (§9.2), `tools/check_dv_register_gates.py`, `tools/check_ci_green.py` |
| Deviation ledger has no unresolved D1/D2 | ✅ MET | PSR-038 §3 (WP038-F1–F6 all resolved); post-PSR-038 audits EDA-002 (`PASS` after remediation), ERA-001 (`PASS`, 12 findings all FIXED), PR017-devin-review (`PASS`, 2 D2 FIXED); EMA-007 `PASS` |
| Campaign trigger (Workflow Standards §3) — all phases complete **and audited** | ✅ MET | Phase-close executive audits EMA-007 / EDA-002 / ERA-001 on Phase 6 |
| `origin/main` green at the baseline SHA | ✅ MET | `check_ci_green.py 8ce115f`: all six required workflows green (run IDs `35392171819`, `35392171718`, `35392171759`, `35392171790`, `35392171956`, `35569217193`) |
| Latest `nightly.yml` conclusion dispositioned (amendment #45) | ⚠️ RED, dispositioned in §11 | Run `35563797483` (2026-09-21, HEAD `8ce115f`): `bench-regression` red (DV-036, re-audit gate = this session) and `full-suite` red (2 failures, environment provisioning — new DV-039). Neither is a code regression; both are routed with dated gates in §11. |

**Verdict:** the campaign may be planned and, on approval, EXP-001 E1 may begin. No entry condition is waived.

---

## 2. Experiment registry (Session Register order — authoritative)

The eight experiments below are registered in the exact `SESSION_REGISTER.md`
order (0154–0193). Each experiment occupies five consecutive sessions E1→E5.
The "Registered expectation" and "Failure/abort boundary" columns quote the
scientific contract in the E1 brief; the "Reconciliation" column records where
the brief's prose is superseded by a normative standard or an adopted plan
amendment (brief header: "If this brief conflicts with a normative standard,
the standard wins"). **E1 must pre-register against the reconciled target, and
must cite the reconciliation.**

### 2.1 Registry table

| ID / Track | Title | Sessions (E1–E5) | Record root / Raw root | Registered expectation (brief) | Failure / abort boundary (brief) | Reconciliation with normative standards (binding on E1) | Baselines for comparison |
|---|---|---|---|---|---|---|---|
| **EXP-001 / C1** | Golden-trajectory numerical parity | 0154–0158 | `DOCS/experiments/EXP-001-golden-trajectory-numerical-parity/` · `benchmarks/results/EXP-001/` | All non-chaotic cases satisfy registered tolerances; chaotic cases preserve registered distributional conclusions; bit-level seeded repeatability holds | Unexplained tolerance breach, invariant violation, or cross-run seed mismatch = D1; environment/schema/manifest failure aborts a run | Tolerances are Plan §5 numbered rule 2 ("Tolerances"): trajectories `rtol=1e-6, atol=1e-8` (corpus `manifest.json` `trajectory_rtol`/`trajectory_atol`); metrics/decompositions `rtol=2e-6` cross-platform (amendments #16/#17), `1e-10` single-runtime where achievable. `strength_of_incoherence*` is a **declared non-hazard exception** (amendment #25) and must be pre-registered as "expected divergence", not as parity. DV-007 f32-complex drift is a permanent disposition (`1e-6` derivative tolerance). | `parity/corpus/` — 504 cases (`n_cases: 504`, schema 1, generator `prinet 3.0.0`); `parity/test_parity_differential.py` (hypothesis fuzz); `crates/prin-dynamics/tests/parity_models.rs` |
| **EXP-002 / C1** | API, benchmark-result, and reproduction parity | 0159–0163 | `…/EXP-002-api-benchmark-result-and-reproduction-parity/` · `benchmarks/results/EXP-002/` | 175+ mapped symbols pass; all historical scientific conclusion orderings unchanged; 15 figures / 11 tables match the manifest | Missing symbols, changed scientific conclusions, or unexplained artefact mismatch = D1; corrupt source artefacts abort | **Figure count is 14, not 15** (WP034-F1, PSR-034 §4: figures 2–15 are the verifiable set; `tools/reproduce.py` docstring "fourteen verifiable historical figures"). Registered reproduction target = **14 figures × 2 formats + 11 tables = 39 generated files**, with the 172-record `paper/artefact_manifest.json`, byte-comparable (PSR-038 §4: "172 artefacts verified, 39 files generated"). **Symbol target:** `prin.__all__` = **175** symbols vs the frozen PRINet 3.0 canonical `__all__` of **172** (`DOCS/baselines/wp001_api_traceability.md`; 657 module-symbol rows); `verify_api_surface(__all__)` must return `(set(), set())`. "Conclusion orderings" = the ordering/direction claims in the Parity Report (`DOCS/sphinx/parity_report.rst`) re-derivable **without training or GPU**; training-/GPU-dependent conclusions are owned by EXP-004–EXP-007 and cross-referenced, never dropped. | `DOCS/archive and reference from PRINet 3.0/PRINet-3.0.0-main/benchmarks/results/` (172 JSON, manifested); `paper/artefact_manifest.json`; `DOCS/baselines/wp033_benchmark_traceability.md` (58 legacy scripts → 9 categories) |
| **EXP-003 / C2** | CPU scaling and sweep performance | 0164–0168 | `…/EXP-003-cpu-scaling-and-sweep-performance/` · `benchmarks/results/EXP-003/` | Eligible CPU kernels ≥2× and parameter sweeps ≥8× on controlled same-hardware comparisons without parity loss | Failure of a normative N1 target = D1 unless amended; thermal throttling, background load, or parity failure aborts timing | **Brief prose is superseded by amendment #21** (Benchmarking Standards §2.4 + footnote 1): CPU fallback paths **≥ 1.5×** and parameter sweeps **≥ 3.5×**, both *multi-core vs 1-thread* on the 8-physical-core / 16-SMT reference host, sweeps measured at config count ≈ physical core count (8). The "≥2× pure PyTorch" comparison is a **future obligation** pending a cross-language harness; E1 may pre-register it only as an *exploratory* hypothesis, and its miss is not a D1. Plan §6 Phase 2 exit row already carries the ≥3.5× re-scope. | WP-016 S3 evidence (`crates/prin-sim/benches/sweep_bench.rs`, 3.92× at 8 configs; SpMV plateau 1.51–1.60×); PRINet 3.0 torch-CPU stored artefacts for like-for-like scaling curves |
| **EXP-004 / C2** | GPU kernels and Torch bridge performance | 0169–0173 | `…/EXP-004-gpu-kernels-and-torch-bridge-performance/` · `benchmarks/results/EXP-004/` | GPU workloads meet or exceed registered 3.0 baselines; training parity ±10%; bridge overhead <5% with correctness intact | Normative target miss or correctness drift = D1; unavailable backend, asynchronous timing error, or throttling aborts affected runs | **Bridge overhead target is amendment #30**: `<5%` **at moderate/large batch and shape sizes**; the ~38–41 % small-shape dispatch floor (DV-021) is architecturally fixed and pre-registered as such. **Triton same-hardware comparison is hardware-gated (DV-001, no Linux GPU host)** → pre-register as a hypothesis whose verdict is `INCONCLUSIVE — hardware unavailable` unless a Linux GPU host is provisioned before 0171 (§5.4). GPU timing must use device-side events/synchronization (Benchmarking Standards §2.2); **DV-003**: `cubecl-cuda` 0.10 `TimingMethod::System` is bracketed by `sync()` (amendment #44) — E1 must state the timing method actually available and its bound. DV-005 (CUDA Burn training) is post-1.0 (amendment #38) — training-step parity is measured on the delivered torch-bridge path. | Benchmarking Standards §2.4 rows 1–3, 7; WP-018/019/020/021 kernel-equivalence and criterion baselines; PRINet 3.0 Triton/CUDA stored artefacts (numbers only — not same-hardware) |
| **EXP-005 / C3** | Dynamics, chimera, and capacity replication | 0174–0178 | `…/EXP-005-dynamics-chimera-and-capacity-replication/` · `benchmarks/results/EXP-005/` | Registered phase boundaries, effect directions, and capacity conclusions reproduce within predeclared statistical/numerical intervals | A published conclusion reversal = D1; insufficient coverage, failed controls, or invalid chaotic-window diagnostics aborts inference | Chimera **strength-of-incoherence** values are *expected* to differ from PRINet 3.0 fixtures (amendment #25, upstream defect EMA-001 M-F1); the replication target is the **phase-diagram boundary and ordering conclusions**, computed with PRIN's corrected implementation, versus the *published* boundaries. E1 must separate "boundary reproduces" (confirmatory) from "SI value matches 3.0" (declared non-target). | Published 3.0 figures/tables (`paper/figures`, `paper/tables`, `fig_chimera_heatmap`, `fig_gold_standard_chimera`, `fig_clevr_n_capacity`, `fig_oscillosim_scaling`); `benchmarks/chimera`, `benchmarks/scaling`, `benchmarks/integrators` |
| **EXP-006 / C3** | Temporal binding, PhaseTracker, and ablation replication | 0179–0183 | `…/EXP-006-temporal-binding-phasetracker-and-ablation-replication/` · `benchmarks/results/EXP-006/` | PhaseTracker reaches at least 3.0 IP scores and registered baseline/ablation ordering with predeclared effect-size intervals | Conclusion/order reversal = D1; budget mismatch, data leakage, failed seed count, or training instability beyond abort threshold invalidates runs | Fair-training framework (Benchmarking Standards §2.2: identical loss/optimizer/augmentation/parameter budgets) is **mandatory**; ≥10 seeds per arm (Experimentation Standards §2 E1 item 8). Phase 4 exit evidence (`DOCS/experiments/0105-wp027-temporal-clevr-n-validation.json`, 3 seeds, IP = 1.0) is a **pilot**, not a confirmatory result, and may be cited only as "basis for prediction". | Published 3.0 IP tables/ablation figures (`fig_ablation_results`, `fig_mot_identity_preservation`, `fig_parameter_efficiency`); `benchmarks/mot`, `benchmarks/ablations`, `benchmarks/training` |
| **EXP-007 / C3** | Daemon, MOT, and adversarial replication | 0184–0188 | `…/EXP-007-daemon-mot-and-adversarial-replication/` · `benchmarks/results/EXP-007/` | MOT matches motmetrics/3.0 references; daemon p95 improves; robustness direction/effect preserved under registered attacks | Published conclusion reversal or F5 failure = D1; provider fallback ambiguity, attack-bound violation, or invalid MOT fixture aborts | **F5 scope for this experiment is CPU + DirectML** (DV-006 DirectML half CLOSED by WP-036F; VitisAI/NPU half OPEN, hardware-gated → §5.4). The controller graph digest is `d7d7935b…` (WP-036F re-export); provider selection ladder VitisAI → DirectML → CPU must be logged per run so "provider fallback ambiguity" is mechanically detectable. MOT reference = `py-motmetrics` 1.4.0 on the 10 WP-030 fixture scenarios plus the 3.0 stored MOT artefacts. | `EVIDENCE/0125-wp032-s1-daemon-latency.json`, `EVIDENCE/0144U-wp036f-s1-controller-provider-report.json`, `tools/wp030_mot_fixture.py`, `benchmarks/daemon`, `benchmarks/mot`, `benchmarks/adversarial`; 3.0 stored robustness artefacts |
| **EXP-008 / C4** | Cross-platform and new-capability characterization | 0189–0193 | `…/EXP-008-cross-platform-and-new-capability-characterization/` · `benchmarks/results/EXP-008/` | Pre-registered capability-specific predictions hold with parity-safe behaviour; platform support satisfies N2/N4/F5 | Violation of N2/N4/F5 = D1; new-capability misses are reported negative unless they breach a normative requirement; unavailable hardware is inconclusive, not silently skipped | **N4 distribution name is `prin-core` (import `prin`), amendment #46.** **Metal (N2 "macOS (CPU + Metal)") has no validated host in the matrix** (§5) — E1 must pre-register the Metal leg with the §5.4 unavailability rule; if still unavailable at 0191, E6 escalates an N2 reconciliation to the maintainer (D3 → plan amendment or provisioning), never a silent skip. NPU leg: DoD #7 wording is "(where available) Ryzen AI NPU" → unavailability is `INCONCLUSIVE`, not D1. C4 has **no 3.0 baseline**; predictions must be quantitative and stated before execution. | Pre-registered predictions only (Experimentation Standards §3 table, C4 row); Phase 0 spike evidence (`EVIDENCE/0017-wp005-s1-*.json`); `release.yml` wheel matrix; DV-001/DV-006 rows |

### 2.2 Owners (Development Workflow §6 role split)

| Role | Person | Approves / performs |
|---|---|---|
| **Maintainer** | MichaelMaillet | Campaign plan approval and freeze (§14); every E2 approval (recorded in the pre-registration header, name + date); every E5 verdict acceptance; every D1 correction-cycle verdict; budget/hardware amendments to this plan (§14.2); campaign summary and Parity Report sign-off (0194) |
| **AI pair (executor)** | the AI pair of record for the session (identified in every artefact header, per Experimentation Standards §4 "Authorship and AI assistance") | Drafts pre-registrations (E1), runs committed drivers (E3), executes the pre-registered analysis (E4), drafts reports (E5); never approves |
| **Independent reviewer (E2)** | the maintainer, plus — where the E2 brief allows — a second AI reviewer that did **not** draft the E1 document | Falsifiability, statistical adequacy, fair baselines, resource sanity |

No experiment has a different owner; the campaign is single-maintainer and
runs one E-stage at a time (Workflow Standards §7 "one WP in flight", applied
to E-stages by the experiment-session workflow step 1: "Never collapse
multiple E stages into one session").

---

## 3. Dependency order

### 3.1 Dependency graph

```
                    Phase 0–6 closed (PSR-038) · origin/main 8ce115f green
                                        │
                                        ▼
                         EXP-001  Golden-trajectory parity (C1)
                          │          │           │           │
              ┌───────────┘          │           │           └────────────┐
              ▼                      ▼           │                        │
   EXP-002  API/benchmark/     EXP-003  CPU      │                        │
            reproduction (C1)  scaling (C2)      │                        │
              │      │               │           │                        │
              │      │               ▼           │                        │
              │      │      EXP-004  GPU kernels + torch bridge (C2) ◄────┘
              │      │               │        │
              │      └───────┐       │        │
              ▼              ▼       ▼        │
   EXP-005  Dynamics/    EXP-006  PhaseTracker/ablation (C3)
            chimera (C3)         │
                                 ▼
                        EXP-007  Daemon/MOT/adversarial (C3)
                                 │
      EXP-002 ─┐  EXP-003 ─┐     │
               ▼           ▼     ▼
                EXP-008  Cross-platform + new capability (C4)
                                 │
                                 ▼
                0194  Campaign E6 synthesis → WP-039 (0195–0198)
```

### 3.2 Dependency table (what must be closed before each E1 starts)

| Experiment | Hard prerequisites (E5 report approved **and** any triggered correction cycle closed) | Why |
|---|---|---|
| EXP-001 | Campaign plan approved (§14); baseline SHA green | Root of the campaign; every later claim assumes numerical parity |
| EXP-002 | EXP-001 | Benchmark-result and reproduction parity are meaningless if trajectories/metrics do not match |
| EXP-003 | EXP-001 | "Without parity loss" (brief) is checked against EXP-001's registered tolerances on every timed configuration |
| EXP-004 | EXP-001, EXP-003 | Kernel-equivalence + CPU reference numbers for like-for-like comparisons |
| EXP-005 | EXP-001, EXP-002 | Replication compares against the validated 3.0 artefact set |
| EXP-006 | EXP-002, EXP-004 | Training-step parity (±10 %) and bridge correctness must hold before IP/ablation replication is interpretable |
| EXP-007 | EXP-002, EXP-006 | MOT evaluation consumes PhaseTracker checkpoints and the validated MOT fixtures |
| EXP-008 | EXP-002, EXP-003, EXP-004 | Cross-platform characterization compares against the reference-host performance envelope and the validated wheel/API surface |
| 0194 (E6) | EXP-001…EXP-008 all E5-approved; no unresolved D1 | E6 entry condition (brief 0194) |

The Session Register order 0154→0193 is a valid topological order of this
graph. **No reordering is permitted without a Plan §8.3 amendment** (Workflow
Standards §8: "No planned session is skipped, merged, or reordered without an
approved amendment").

### 3.3 Blocking rule

A D1 raised at any E-stage of EXP-*n* **blocks** the listed successor session
and inserts the four conditional correction sessions from
`DOCS/sessions/contingencies/` (S1-correction → S2 → S3 → S4) before the
blocked numbered session resumes (Workflow Standards §8; `SESSION_REGISTER.md`
preamble). Planned numbers do not change. Every experiment downstream in §3.2
inherits the block.

---

## 4. Track coverage (Experimentation Standards §3 table)

| Track | Experiments | Baseline class |
|---|---|---|
| C1 Parity | EXP-001, EXP-002 | PRINet 3.0.0 artefacts (corpus, 172 stored JSON, paper manifest, frozen `__all__`) |
| C2 Performance | EXP-003, EXP-004 | Benchmarking Standards §2.4 targets (as amended #21, #30); 3.0 Triton/CUDA + torch CPU numbers |
| C3 Scientific replication | EXP-005, EXP-006, EXP-007 | Published 3.0 figures/tables |
| C4 New capability | EXP-008 | Pre-registered predictions |

Every §3 track item ("chimera phase diagrams, capacity analyses, MOT/IP
studies, ablation orderings, adversarial robustness", "all §2.4 targets, all
backends and platforms", "full golden-corpus + benchmark-result parity",
"anything PRIN enables beyond 3.0") maps to at least one row above.

---

## 5. Hardware and backend matrix

### 5.1 Hosts (verified from repository evidence — no host is assumed)

| Host | Identity | Verified facts | Backends | Campaign role |
|---|---|---|---|---|
| **H1** | Maintainer workstation = self-hosted `PRIN-GPU-Runner` (`gpu.yml`: "PRIN-GPU-Runner is the maintainer's 32 GB workstation") | Windows 11 `10.0.26200`; CPU `AMD64 Family 25 Model 117 Stepping 2, AuthenticAMD`, 16 logical CPUs / **8 physical cores** (amendment #21 reference hardware); 32 GB RAM; **NVIDIA GeForce RTX 4060** (driver 595.95, CUDA 13.2); DirectML-capable adapter (WP-036F); Python 3.14.0; rustc 1.92.0 (`EVIDENCE/0125-wp032-s1-daemon-latency.json`, `EVIDENCE/0144U-wp036f-s1-controller-provider-report.json`, DV-001, DV-024) | `cpu` (SIMD + rayon), `cuda`, `wgpu` (DX12), ONNX Runtime `CPUExecutionProvider` + `DmlExecutionProvider` | **Reference host for every timing claim (C2)** and for all GPU/DirectML execution; primary executor for C1/C3 |
| **H2** | GitHub-hosted `ubuntu-latest` | Linux x86_64; variable/throttled CPU (`nightly.yml` header caveat, PSR-016 §5); disk-constrained (DV-022); Python 3.11–3.13 legs | `cpu` | N2 Linux availability; cross-OS corpus regeneration at `rtol=2e-6` (`parity.yml`); **no timing claim may cite H2** |
| **H3** | GitHub-hosted `macos-latest` | macOS arm64 (`rust.yml` test leg, `release.yml` wheel leg) | `cpu`; **Metal not validated anywhere in the repository** | N2 macOS CPU availability + universal2 wheel smoke; Metal leg per §5.4 |
| **H4** | GitHub-hosted `windows-latest` | `python.yml` Windows legs | `cpu` | Windows wheel/platform availability only |
| — | Linux GPU host (Triton 3.0 same-hardware comparison) | **Not available** (DV-001; `gpu-triton.yml` staged, dormant) | — | See §5.4 |
| — | Ryzen AI NPU (`VitisAIExecutionProvider`) | **Not executing the controller graph** (DV-006 VitisAI half OPEN, hardware-gated) | — | See §5.4 |

### 5.2 Experiment → host/backend allocation

| Experiment | H1 cpu | H1 cuda | H1 wgpu | H1 DirectML | H2 | H3 | H4 | Unavailable legs (§5.4) |
|---|---|---|---|---|---|---|---|---|
| EXP-001 | ● primary | ● (kernel paths) | ● | — | ○ cross-OS regeneration | ○ | ○ | — |
| EXP-002 | ● | ○ (only where a stored 3.0 artefact is GPU-derived and re-derivable) | — | — | ○ reproduction re-run | — | — | — |
| EXP-003 | ● **timing** | — | — | — | — | — | — | pure-PyTorch cross-language comparison (no harness; exploratory only) |
| EXP-004 | ● reference | ● **timing** | ● **timing** | — | — | — | — | Triton same-hardware (DV-001) |
| EXP-005 | ● | ● (large grids) | ○ | — | — | — | — | — |
| EXP-006 | ○ | ● **training** | — | — | — | — | — | CUDA Burn training (DV-005, post-1.0) |
| EXP-007 | ● | ● | — | ● **F5 DirectML leg** | — | — | — | VitisAI/NPU (DV-006) |
| EXP-008 | ● (1M-oscillator CPU) | ● | ● | ● | ● wheels/platform | ● wheels/platform; Metal | ● wheels/platform | Metal execution (no validated host); NPU (DV-006) |

● = required leg; ○ = optional/confirmatory; — = not applicable.

### 5.3 Quiescence rule for timing claims (C2 and any latency claim)

1. Timing runs execute on **H1 only**, with the CI runner service stopped for
   the window (`Stop-Service 'actions.runner.*'` → run → `Start-Service`),
   and no other user workload. The E3 `log.md` records `Get-Service
   'actions.runner.*'` state before and after each timing window.
2. Warm-up iterations are excluded; ≥ 10 measured iterations; median **and**
   p95 reported (Benchmarking Standards §2.2; `benchrunner --iterations ≥ 10`
   is enforced by `BenchmarkConfig`).
3. Every timing run records the host's power/thermal state as pre-registered
   in E1 (at minimum: plugged-in, no throttling flag). A throttling or
   background-load detection is an **abort** (invalid run), never a data
   point.
4. Timing windows never overlap a push to `origin/main` (the required
   `gpu-cuda`/`gpu-wgpu` checks would queue on the stopped runner).

### 5.4 Unavailable-hardware rule (binding on EXP-004, EXP-007, EXP-008)

A hypothesis whose only execution path needs hardware absent from §5.1 is
still pre-registered in full. At E3 the run is logged as
`NOT EXECUTED — hardware unavailable (DV-NNN)`; at E5 the verdict is
`INCONCLUSIVE — hardware unavailable`, citing the DV row. It is never
skipped silently and never reported as a negative result. If the hardware
becomes available before that experiment's E3 session, the pre-registration
is amended **before E3** (normal edit under E2 rules) and the leg executes.
Whether an `INCONCLUSIVE` on a normative requirement (N2 Metal) becomes a D3
plan amendment or a provisioning action is a maintainer decision recorded at
E6 (0194).

---

## 6. Seed policy

1. **Single authority.** All randomness flows through the counter-based
   `Seed(counter, key)` type (Plan §4 rule 3; `crates/prin-dynamics/src/seed.rs`;
   `benchrunner --seed-counter / --seed-key`). No experiment may introduce a
   second RNG path; `torch.manual_seed` in torch-side code is set from the same
   registered integer.
2. **Key = experiment number.** `seed_key = n` for EXP-00*n* (1…8). This keeps
   campaign streams disjoint from every pre-campaign artefact (which used
   `seed_key = 0`) and from each other.
3. **Counter = replicate index.** Replicate *r* uses `seed_counter = r`,
   *r* ∈ {0, …, *n*−1}. **Confirmatory hypotheses use *n* ≥ 10** (Experimentation
   Standards §2 E1 item 8); a smaller *n* must be justified in E1 and approved
   at E2.
4. **Seeds are enumerated, not generated.** Every pre-registration lists the
   exact `(counter, key)` pairs per arm. Changing the list after E2 approval is
   a protocol deviation reported in E5.
5. **Repeatability gate.** Every E3 session re-runs replicate 0 of at least one
   registered configuration. Before comparison, validate each run's campaign
   metadata sidecar (§7.2) independently, require the same scientific config
   (including `seed_counter`, `seed_key`, backend, dtype, and code SHA), and
   compare a canonical result projection that excludes per-run provenance
   (`environment`, `config.out_dir`, and `run_id`) plus pre-registered timing
   measurements. All remaining scientific inputs and outputs must be identical.
   A mismatch is an abort for that configuration and, if unexplained, a D1
   (brief EXP-001: "cross-run seed mismatch is a D1").
6. **Cross-backend repeatability.** Where a configuration runs on more than one
   backend (cpu/cuda/wgpu), the E1 document states whether bit-identity or
   tolerance-identity is expected, with the tolerance — Plan §5 numbered rule 5
   ("Bit-level reproducibility") targets exact reproducibility across CPU/GPU;
   known f32 accumulation differences must be declared in advance.

---

## 7. Shared artefact schema, run IDs, and immutability

### 7.1 Directory layout (created as skeletons by this session)

```
DOCS/experiments/EXP-00n-<slug>/
├── README.md              # skeleton (this session): status, sessions, links
├── preregistration.md     # E1 creates from TEMPLATE_Preregistration.md; frozen at E3 start
├── log.md                 # E3 execution log
└── report.md              # E5 report

benchmarks/results/EXP-00n/
├── README.md              # skeleton (this session): the run-directory rule
└── RUN-<UTC yyyymmddThhmmssZ>-<short SHA>-<label>/
    ├── campaign-metadata.json     # campaign provenance sidecar
    ├── <category>_<name>.json     # benchrunner/driver artefacts (write_result envelope)
    ├── …
    └── manifest.json              # per-run SHA-256 manifest (tools/reproduce.py append_manifest)
```

`<label>` is a short pre-registered tag (e.g. `corpus-cpu`, `knn16k-cuda`,
`seedrep0`). A run directory is **never reused**: a re-run, a retry after an
abort, or a corrected run gets a new `RUN-…` directory (Experimentation
Standards §2 E3 "re-runs get new run IDs"; §4 "corrections happen by
re-running with a new run ID").

### 7.2 Result envelope and campaign metadata sidecar

Each category result is written by `benchmarks._common.result.write_result`
(or a committed driver that calls it) and therefore has exactly:

- `environment` — `benchmarks._common.environment.capture_environment` output:
  `prin_version`, `git_commit`, `rust_version`, `python_version`, `platform`,
  `processor`, `logical_cpus`, `gpu`, `gpu_vram_mb`, `backend`, `dtype`,
  `seed` (Benchmarking Standards §1.4);
- `config` — `iterations`, `warmup`, `seed_counter`, `seed_key`, `out_dir`;
- the category payload, whose field names stay those of the corresponding
  legacy 3.0 artefact (Benchmarking Standards §1.3 "Unchanged JSON schema";
  `benchmarks/README.md`).

Drivers that emit per-case records (EXP-001 corpus comparisons) use the same
result envelope with a payload of `{cases: [...]}`; the payload never contains
the reserved keys `environment`/`config` (enforced by `write_result`). Campaign
provenance does not alter that legacy-compatible payload schema.

Every run also contains a separate `campaign-metadata.json` sidecar with
`exp_id` (`"EXP-00n"`), `run_id` (the `RUN-…` directory name), `session`
(`"0156"` etc.), `operator`, and an `artefacts` mapping from each result filename
to the H-ids it bears on. GPU result entries additionally carry `timing_method`
(`"device-event"` | `"system-synced"` | `"not-timed"`, per DV-003/amendment #44
and §11.5's ratified extension for an untimed GPU correctness comparison). The
sidecar and all result files are covered by the run manifest.

Campaign runs must not invoke `benchrunner` directly. E1 must provide a
committed, tested campaign driver that accepts and validates the metadata above,
writes the sidecar, and invokes `benchrunner` or `write_result` without changing
the category payload schema. The pre-registration and E3 log record the exact
driver command and metadata inputs; missing metadata aborts before any result is
accepted.

### 7.3 Append-only enforcement and detection

| Property | Mechanism | Status |
|---|---|---|
| A run is never overwritten by a later run | Run-scoped `--out benchmarks/results/EXP-00n/RUN-<id>/`; directory name embeds UTC time + SHA; **rule: a `RUN-` directory that already exists is never passed to `--out`** | Enforced by convention (§7.1) + checked at E3 (`log.md` lists every `RUN-` directory created) |
| Mutation/removal of an accepted artefact is detected | `tools/reproduce.py verify_manifest(results_dir=<RUN dir>, manifest_path=<RUN dir>/manifest.json)` fails closed on missing, modified, resized, or unmanifested `*.json` (non-recursive glob, so one manifest per run directory) | **Enforced** by existing, tested code |
| The manifest itself is append-only | `append_manifest` refuses to rewrite or drop existing records | **Enforced** by existing, tested code |
| The writer refuses to overwrite an existing file | `write_result` stages and flushes complete JSON, then atomically publishes with exclusive-create semantics; concurrent writers cannot replace one another and failed staging writes leave no destination | **FIX COMMITTED — DV-038 (§11.1)**; closes when PR #19 merges green |

`git` history provides a further immutable record: raw artefacts and their
manifests are committed at E3 close; any later change is a visible diff.

### 7.4 Deterministic regeneration path (every report)

1. **Inputs:** the run directories named in the report's artefact index and
   their `manifest.json` files (verified with `verify_manifest` first).
2. **Analysis code:** committed under the experiment's record root or
   `python/prin/reporting/` **before** E4 starts (Experimentation Standards §2
   E4 "Analysis code is committed"); the report cites the path and the git SHA.
3. **Generators:** `prin.reporting.generate_benchmark_report` /
   `generate_leaderboard` for tables; the `fig_*` generators for figures; both
   are deterministic (explicit `generated_at` inputs, sorted keys).
4. **Outputs:** generated Markdown/figures under
   `DOCS/test_and_benchmark_results/EXP-00n/` (gitignored) with a SHA-256
   manifest committed to the record root as `report-manifest.json`; the E5
   report's artefact index lists every input run manifest and the output
   manifest digest.
5. **Check:** re-running step 3 on a clean checkout reproduces every output
   digest in `report-manifest.json` byte-for-byte; the E5 brief's exit gate and
   0194's expected work item 4 verify this.

### 7.5 Storage rules

- Raw JSON per run ≤ 2 MiB tracked; if a configuration needs more, store the
  large arrays (e.g. `.npz`) under `DOCS/test_and_benchmark_results/EXP-00n/`
  (gitignored) and record their SHA-256 in the run's `manifest.json` payload
  via a committed `*.json` sidecar. The tracked JSON must still allow every
  pre-registered decision rule to be re-evaluated.
- Model checkpoints are never tracked (Benchmarking Standards §3: only
  `models/subconscious_controller.onnx` is tracked); they are manifest-verified
  in the gitignored output root.
- Campaign-wide tracked-artefact cap: **64 MiB** across `benchmarks/results/EXP-*`
  (the whole repository pack is ~31 MiB today; the 172 legacy artefacts are
  16 MB). Exceeding the cap requires a §14.2 budget amendment.

---

## 8. Resource and storage budget (caps — exceeding a cap is an abort criterion)

Budgets are **upper bounds** each E1 must fit within (and may tighten). They
are stated per host from §5. "Wall" is the elapsed time of E3 execution on
H1; hosted-CI minutes are those consumed by campaign-specific workflow
dispatches (not the ordinary push-triggered CI).

| Experiment | H1 CPU wall | H1 GPU wall | Hosted CI (H2/H3/H4) | Tracked storage | Rationale |
|---|---|---|---|---|---|
| EXP-001 | ≤ 8 h | ≤ 2 h | ≤ 3 h (cross-OS regeneration) | ≤ 5 MiB | 504 corpus cases × PRIN + 3.0 regeneration; hypothesis fuzz (≥ 1,000 cases); seed-repeatability duplicates; cuda/wgpu kernel-path legs |
| EXP-002 | ≤ 12 h | ≤ 2 h | ≤ 2 h (reproduce.py on H2) | ≤ 10 MiB | API walk (minutes); reproduction (seconds); re-derivation of the non-training, non-GPU conclusion set from the 172 artefacts |
| EXP-003 | ≤ 16 h | — | — | ≤ 5 MiB | criterion + benchrunner scaling to N = 1M; sweep speedup at 4/8/16 configs; ≥ 10 iterations each; parity check per timed configuration |
| EXP-004 | ≤ 4 h | ≤ 12 h | — | ≤ 5 MiB | N = 1M fused RK4; N = 16K k-NN; fused discrete step; bridge overhead at small/moderate/large shapes; training-step parity |
| EXP-005 | ≤ 40 h | ≤ 10 h | — | ≤ 20 MiB | Chimera phase-diagram grids × ≥ 10 seeds; capacity curves; integrator accuracy/cost |
| EXP-006 | ≤ 8 h | ≤ 60 h | — | ≤ 10 MiB | PhaseTracker vs SlotAttention vs ablation variants, ≥ 10 seeds per arm, matched budgets on temporal CLEVR-N |
| EXP-007 | ≤ 8 h | ≤ 8 h | — | ≤ 5 MiB | Daemon p50/p95 (CPU + DirectML); MOT on fixtures + 3.0 artefacts; FGSM/PGD grids |
| EXP-008 | ≤ 8 h | ≤ 4 h | ≤ 10 h (wheel/platform legs) | ≤ 5 MiB | 1M-oscillator CPU characterization; platform/wheel matrix; Metal/NPU legs per §5.4 |
| **Campaign total** | **≤ 104 h** | **≤ 98 h** | **≤ 15 h** | **≤ 64 MiB** | — |

Capacity allocation: H1 is the single reference host and is also the CI
runner. Campaign timing windows (§5.3) are scheduled by the maintainer per E3
session; non-timing runs (C1/C3 correctness, training) may share the host with
CI. No campaign run executes on H2–H4 except the explicitly listed
cross-platform legs.

---

## 9. Statistics policy (every E1 inherits; deviations need E2 approval)

### 9.1 Rules

- **α = 0.05** unless justified in E1.
- **Two-arm comparisons:** Welch's *t*-test; **effect size** Cohen's *d* (or
  Cliff's δ for non-normal/ordinal outcomes); **95 % bootstrap CI** on the
  difference (≥ 10,000 resamples, seeded per §6).
- **> 2 comparisons in one hypothesis family:** Holm–Bonferroni step-down.
- **Parity/tolerance hypotheses (C1):** decision rule is a deterministic
  per-case pass/fail at the registered tolerance; the reported statistics are
  pass counts, maximum relative/absolute error, and their distribution — no
  significance test is needed, and none may be used to "rescue" a failed case.
- **Performance hypotheses (C2):** ratio of medians with bootstrap CI over the
  ≥ 10 measured iterations; a target is met only if the CI lower bound clears
  the target.
- **Chaotic regimes (EXP-001/EXP-005):** compared statistically beyond the
  shadowing horizon (Plan §5 numbered rule 2, "Tolerances"), with the horizon
  and the distributional statistic (e.g. order-parameter distribution, KS
  distance) pre-registered.
- Every verdict is `CONFIRMED | REFUTED | INCONCLUSIVE`. Statistical hypotheses
  report an effect size and CI (Experimentation Standards §2 E5). Deterministic
  C1 parity hypotheses instead report pass/fail counts, maximum relative and
  absolute error, the error distribution, and the registered tolerance; an
  effect size or CI is not applicable.

### 9.2 Implementations (the only permitted statistical code paths)

| Statistic | Implementation | Owner rule |
|---|---|---|
| Welch's *t* (with Cohen's *d*) | `prin.y4q1_tools.welch_t_test` → Rust `crates/prin-sim/src/y4q1_stats.rs::welch_t_test` | Plan §4 rule 2 (no numerics in Python) |
| Bootstrap CI | `prin.y4q1_tools.bootstrap_ci` → Rust `y4q1_stats::bootstrap_ci` (seeded) | idem |
| Cohen's *d* | `prin.y4q1_tools.cohens_d` → Rust | idem |
| Cliff's δ, Holm–Bonferroni | `benchmarks.phase1_statistical_hardening.cliffs_delta` / `holm_bonferroni` (ported experiment tooling, governed exception "post-hoc statistics are experiment tooling rather than oscillator numerics") | Existing governed exception; any new statistic must be added to Rust with a binding, never as new Python numerics |

---

## 10. Campaign-wide stop, abort, and escalation rules

### 10.1 Abort criteria every pre-registration must include (run-level, invalid — not negative)

1. NaN/Inf guard trip; order parameter outside [0, 1]; phase outside the
   wrapped range; amplitude/derivative clamp trips outside the documented
   hazard envelope (Plan §5 numbered rule 6, "Preserved numerical hazards").
2. Seed irreproducibility on the §6.5 repeatability gate.
3. Environment capture incomplete (any `environment` field `null` that the
   configuration requires — e.g. `gpu` null on a GPU leg).
4. Manifest failure (`verify_manifest` raises) for any input or the run's own
   directory.
5. Budget exceeded (§8 caps or the tighter E1 budget).
6. Timing invalidated (§5.3: throttling, background load, runner service
   running during a timing window, wall-clock GPU timing where device
   timing was registered).
7. Provider fallback ambiguity (EXP-007): the ONNX Runtime provider actually
   used is not the one registered for the leg.

Aborted runs stay in `log.md` and in their `RUN-` directory; they are never
deleted (Experimentation Standards §2 E3, §4).

### 10.2 Campaign-level stop conditions (halt the campaign, escalate to the maintainer)

| Condition | Action |
|---|---|
| Any **D1** at any E-stage | Block the successor session; insert the four contingency correction sessions (§3.3); no other campaign work until the correction S4 closes |
| Baseline code changes (any commit to `origin/main` that touches `crates/`, `python/prin/`, `benchmarks/`, `parity/`, `paper/`) between an experiment's E2 and E5 | The experiment's E3/E4 record the new SHA; the E5 report lists the diff as a protocol deviation; if numerics were touched, EXP-001's registered configurations most sensitive to the change are re-run as a **regression leg** before the campaign continues |
| `origin/main` not green (`check_ci_green.py`) at any E3 start | E3 does not start until green (amendment #45 applied to the campaign) |
| Red `nightly.yml` not dispositioned (fixed or dated DV row) at an E3 start | Disposition first (§11) |
| Campaign budget total (§8) exhausted | Maintainer budget amendment (§14.2) or campaign descoping via Plan §8.3 |
| Two consecutive experiments end with every confirmatory hypothesis `INCONCLUSIVE` | Maintainer review of statistical design before the next E1 |

### 10.3 What is *not* a stop condition

A **REFUTED** hypothesis in C4 (new capability) that breaches no normative
requirement is a reported negative result, not a D1 (brief EXP-008). A
**REFUTED** performance hypothesis whose target was already re-scoped by
amendment (#21, #30) is D1 only against the *amended* target.

### 10.4 C1–C3 conclusion reversals → D1 correction cycle (brief 0153 item 4)

Experimentation Standards §3: "C1–C3 failure conditions include 'scientific
conclusion differs from PRINet 3.0' — any such outcome is a D1 trajectory
breach feeding back into the Session Cycle (audit → remediation), not a
publishable novelty." This plan operationalizes it:

1. **Detection is at E4**, by the pre-registered decision rule, and is
   recorded in the E5 report as `REFUTED` with the D1 flag.
2. The E5 session **still completes** (the negative result is reported in full;
   Experimentation Standards §1.2) and then **blocks its successor** (the next
   experiment's E1 or 0194).
3. The four contingency sessions run: S1-correction implements the fix (or
   proves the 3.0 conclusion was itself defective, the amendment-#25 class —
   which requires an EMA-style mathematical audit claim, Z3/SymPy-verified
   where applicable, before the 3.0 conclusion may be declared the erroneous
   side); S2 audits; S3 remediates; S4 documents (PSR + register).
4. After S4, the affected experiment is **re-run as a new experiment record**
   (`EXP-00n-r1`, new pre-registration, new run directories); the original
   record stays as-is with an erratum pointer.
5. No later campaign session proceeds until step 4's E5 verdict is not a
   reversal (or the maintainer records a Plan §8.3 amendment accepting a
   changed conclusion with full justification — the only path by which a
   changed conclusion can become publishable, and it is a plan amendment, not
   an experiment outcome).

---

## 11. Gaps registered by this session (dispositions for maintainer approval)

Planning surfaced four conditions the campaign depends on. None is a code
defect in PRIN's numerics; each has a proposed disposition and a dated,
mechanically checkable gate (`tools/check_dv_register_gates.py` parses
"before session NNNN").

### 11.1 DV-038 — writer-level append-only enforcement (§7.3)

- **Original fact:** `benchmarks._common.result.write_result` used an
  unconditional `write_text`; re-running with the same `--out` overwrote the
  prior artefact.
- **Fix committed:** the writer stages and flushes complete JSON, then publishes
  it through an atomic exclusive-create operation. An existing destination
  raises `ArtefactExistsError`; concurrent writers cannot replace one another;
  failed staging writes leave no destination. Direct writer, concurrent-race,
  interrupted-write, and repeated-CLI tests cover the contract.
- **Closure gate:** PR #19 merges with required CI and Snyk Code green before
  session 0156 (EXP-001 E3). The §7.1 run-directory and per-run manifest rules
  remain independent defense in depth.

### 11.2 DV-039 — `nightly.yml` `full-suite` red: environment provisioning drift

- **Fact:** run `35563797483` (2026-09-21, `8ce115f`): 2 failed / 3,423 passed
  / 292 skipped. `tests/test_acceptance_y4q3.py::TestSphinxDocs::test_sphinx_build_succeeds`
  fails with `No module named sphinx`; `tests/test_notebooks.py::test_notebook_executes_end_to_end[02_clevr_n_binding.ipynb]`
  fails with `ImportError: motmetrics is required for MOT evaluation`. The
  `full-suite` job installs `.[dev,onnx]` and runs `tests/ parity/` in full,
  whereas `python.yml`'s docs job installs `.[dev,mot]` **and**
  `-r DOCS/sphinx/requirements.txt` before running these tests. Not a code
  regression.
- **Proposed disposition:** align `nightly.yml`'s `full-suite` install step with
  `python.yml`'s docs job (`.[dev,onnx,mot]` + `-r DOCS/sphinx/requirements.txt`,
  constrained by `ci/docs-constraints.txt`), **before session 0156**, as a
  governed CI hotfix; the nightly `full-suite` is the campaign's daily
  regression net and must be green before the first E3.

### 11.3 DV-036 — nightly `bench-regression` red (re-audit gate reached: this session)

- **Fact:** the same nightly run reports uniform +65 % … +134 % "regressions"
  across every criterion and pytest-benchmark group, including pure-Rust
  serial sweeps — the signature of hosted-runner speed variance against a
  rolling cache baseline, exactly the DV-036 diagnosis (host-instability /
  baseline-staleness). The DV row's re-audit gate was re-pointed by 0152 to
  "the Phase 7 benchmark campaign (session 0153 E0), where a quiescent-runner
  re-baseline belongs".
- **Disposition (this session):** the reference-host re-baseline is split into
  two independently blocking gates on quiescent H1 (§5.3): **(1) CPU
  criterion/pytest-benchmark groups are captured in EXP-003 E3 (0166) and must
  be committed before session 0168 (EXP-003 E5); (2) GPU/bridge groups are
  captured in EXP-004 E3 (0171) and must be committed before session 0173
  (EXP-004 E5).** Failure of the CPU gate blocks EXP-003 E5 and every dependent
  experiment; failure of the GPU/bridge gate blocks EXP-004 E5 and its
  dependants. Each gate produces committed baselines for
  `tools/check_bench_regression.py`; satisfying the CPU gate changes DV-036 to
  **PARTIALLY CLOSED**, and satisfying both closes it. The hosted `nightly.yml`
  gate remains a gross-regression detector only (its own header says so);
  making it baseline-stable on hosted runners (e.g. relative-to-same-run control
  benchmark, or a self-hosted nightly) is a CI-robustness item for WP-039 S1
  (0195), not a campaign experiment.

### 11.4 Brief-vs-standard target reconciliation (EXP-002, EXP-003, EXP-004, EXP-008)

Recorded in §2.1 "Reconciliation" and binding on E1: figure count 14 (not
15); CPU targets ≥ 1.5× / ≥ 3.5× (amendment #21, not ≥ 2× / ≥ 8×); bridge
overhead < 5 % at moderate/large shapes (amendment #30); distribution name
`prin-core` (amendment #46); Triton/NPU/Metal legs under §5.4. These are
**factual corrections to brief prose** (the PSR-034 §4 disposition class), not
plan amendments — the Plan already carries every amended target. Pre-registering
against the unamended brief prose would be a D3 (Workflow Standards §8 "stale
… session-plan metadata … D2 when it could authorize work incorrectly") — hence
this explicit record.

### 11.5 `timing_method` enum extension — EXP-001 H4 (§7.2), ratified 2026-09-22

- **Original fact:** §7.2 registers exactly two `timing_method` values for a
  GPU result entry, `"device-event"` and `"system-synced"` (DV-003/amendment
  #44), both premised on the entry being a *timed* GPU measurement. EXP-001's
  H4 (§2.1: "GPU kernel-path tolerance-identity") is a GPU result entry that
  performs no timing measurement at all — preregistration §5.1 states plainly
  "No H2/H3/H4 case is timed; this experiment measures correctness, not
  performance." Neither registered value describes that leg truthfully, and
  recording either would assert a timing method H4 never used.
- **Fix:** a third registered value, **`"not-timed"`**, for a GPU result entry
  that performs no timing measurement. Applied identically in the driver's
  writer (`exp001_driver.KERNEL_PATH_TIMING_METHOD`), the closure validator
  (`check_run_complete`'s `_TIMING_METHODS`), the tests, and the
  pre-registration (§5.1, §5.3, §5.12 item 6). No existing `"device-event"`/
  `"system-synced"` leg is touched.
- **Why a §11 disposition rather than a bare code fix:** §7.2 is a shared
  campaign-wide schema, and §14.2 restricts post-freeze amendments to
  hardware availability (§5), budget caps (§8), storage rules (§7.5), and gap
  dispositions (§11) — an untimed correctness leg discovered while
  implementing an already-authorized experiment (EXP-001 E1 was authorized at
  §14.1 A4) is exactly the class of registered-schema gap §11 exists to
  disposition, not a change to experiment order, seed policy, or statistics
  policy.
- **Disposition:** **ratified.** MichaelMaillet, 2026-09-22, in response to the
  ninth EXP-001 E2 remediation pass (preregistration §5.12 item 6). Any future
  experiment whose GPU leg is genuinely untimed may reuse `"not-timed"`
  without a further amendment; a *timed* GPU leg still requires
  `"device-event"` or `"system-synced"` per DV-003/amendment #44.

---

## 12. Campaign rules that E1–E5 briefs do not spell out (adopted here)

1. **Driver-commit slot.** Every driver a pre-registration names must be
   versioned code (Experimentation Standards §2 E3 "no unversioned scripts").
   New or modified drivers are authored in **E1** (with tests in tandem, the
   Coding Standards §5 local gate, and Snyk Code — Coding Standards §6),
   reviewed and approved in **E2**, and **frozen at E3 start** together with
   the pre-registration. E3 may not add or modify driver code; a needed driver
   fix at E3 is an abort → fix → new run ID, logged.
2. **One E-stage per session; no stage collapsing** (experiment-session
   workflow step 1).
3. **Commit cadence.** Each E-session commits locally at its exit gate on a
   `campaign/<session>-<exp>-<stage>` branch; `main` is PR-only (ruleset
   `22150076`, amendment #45). The E5 session's PR carries the E1–E5 range. Its
   report records the tested PR head SHA and required-check results available
   before approval; it must not claim the not-yet-created merge SHA. After
   merge, the next governed session (the dependent experiment's E1, or session
   0194 after EXP-008) records the final merge SHA and pastes
   `check_ci_green.py <merge-SHA>` output into its dependency/entry evidence. A
   red merge push is dispositioned before that session proceeds.
4. **Freeze semantics.** A pre-registration is frozen when its E3 session's
   first `RUN-` directory is created; the freeze is recorded by the git SHA of
   the last pre-registration edit, quoted in `log.md` line 1.
5. **Exploratory analyses** appear only under an "Exploratory" heading and
   never feed a verdict.
6. **Errata** follow Experimentation Standards §4: erratum in the experiment
   report **and** the Parity Report, plus a CHANGELOG line.
7. **AI assistance disclosure.** Every pre-registration and report header
   names the drafting AI pair and states that the maintainer verified the
   analyses (Experimentation Standards §4).

---

## 13. Session 0153 deliverable checklist

| Required output (brief 0153) | Artefact | State |
|---|---|---|
| Approved/frozen campaign plan | this file | **APPROVED — FROZEN** (§14.1 A4) |
| Experiment registry in Session Register order, dependencies, owners, hardware/backend matrix, seeds policy, resource/storage budgets, shared schemas, stop/escalation rules | §2, §3, §2.2, §5, §6, §8, §7, §10 | adopted (A1, A3, A4) |
| Raw artefacts append-only; deterministic regeneration path + SHA-256 manifest per report | §7.3 (DV-038 writer fix committed), §7.4 | adopted (A2) |
| C1–C3 reversals feed a D1 correction cycle before later sessions proceed | §10.4, §3.3 | adopted (A4) |
| Capacity allocation | §5.2, §5.3, §8 | adopted (A1, A3) |
| Experiment directory skeletons | `DOCS/experiments/EXP-001…008-*/README.md`; `benchmarks/results/EXP-001…008/README.md` | created |
| Register/README/DV/CHANGELOG updates | `SESSION_REGISTER.md`, `phase-7/README.md`, `DOCS/experiments/README.md`, `benchmarks/results/README.md`, `DEFERRED_VALIDATION_REGISTER.md` (DV-036 update, DV-038, DV-039), `CHANGELOG.md` | updated |
| Explicit authorization to begin EXP-001 E1 | §14.1 A4 | **granted** |

---

## 14. Approval record and freeze

### 14.1 Maintainer decisions (session 0153)

| # | Decision | Maintainer answer | Date |
|---|---|---|---|
| A1 | Hardware matrix §5 adopted as the campaign's authorized execution envelope; unavailable legs (Linux-GPU/Triton, VitisAI/NPU, Metal) handled by §5.4 | **Adopted as written.** No additional host is provisioned; the Metal N2 reconciliation is decided at E6 (0194) per §5.4. | 2026-09-21 |
| A2 | Gap dispositions §11.1–§11.3 adopted (DV-038 and DV-039 opened with "before session 0156" gates; DV-036 CPU re-baseline assigned to EXP-003 E3 before session 0168 and GPU/bridge re-baseline assigned to EXP-004 E3 before session 0173) | **Adopted.** Execution mode for DV-038/DV-039: **one governed CI/tooling hotfix PR** (Workflow Standards §7), opened after this session's commit — `write_result` refuse-to-overwrite guard with tests in tandem and Snyk Code; `nightly.yml` `full-suite` install aligned with `python.yml`'s docs job. Both rows close on green required CI plus one green `nightly.yml` dispatch; retro-audited at the next S2-class audit. | 2026-09-21 |
| A3 | Budget caps §8 and storage rules §7.5 adopted | **Adopted as written.** | 2026-09-21 |
| A4 | Campaign plan **APPROVED and FROZEN**; **EXP-001 E1 (session 0154) is authorized to begin** | **Approved and frozen; EXP-001 E1 authorized.** Recorded via the session's `AskUserQuestion` selections (the amendment-#38 planning-session precedent). | 2026-09-21 |

### 14.2 Post-freeze amendment rule

After A4, this plan may change only through a dated row in the table below,
approved by the maintainer, and limited to: hardware availability (§5),
budget caps (§8), storage rules (§7.5), and gap dispositions (§11).
Experiment order, dependency edges, owners, the seed policy, the statistics
policy, and the stop/escalation rules require a Project Plan §8.3 amendment.
Hypotheses are never in this document.

| # | Date | Section | Change | Approved by |
|---|---|---|---|---|
| 1 | 2026-09-21 | §11.1, §11.2 (gap dispositions; §7.3 enforcement row) | Executes decision A2: the DV-038 `write_result` guard stages and flushes JSON before atomic exclusive publication (`ArtefactExistsError`; direct, race, interrupted-write, and CLI tests; Snyk Code required) and DV-039 constrains every `nightly.yml` `full-suite` pip install while provisioning MOT/Sphinx. Both fixes are committed on governed hotfix branch `hotfix/dv038-dv039-artefact-guard-nightly-provisioning`; DV-038 closes on green merge and DV-039 on green merge plus one green nightly dispatch. No change to §2–§6, §8–§10. | MichaelMaillet (A2) |
| 2 | 2026-09-22 | §11.5 (gap disposition; §7.2 schema row) | Ratifies a third `timing_method` value, `"not-timed"`, for a GPU result entry that performs no timing measurement (EXP-001 H4, preregistration §5.12 item 6). Applied in the driver, the closure validator, and the pre-registration; no existing `"device-event"`/`"system-synced"` leg changes. No change to §2–§6, §8–§10, §11.1–§11.4. | MichaelMaillet |
