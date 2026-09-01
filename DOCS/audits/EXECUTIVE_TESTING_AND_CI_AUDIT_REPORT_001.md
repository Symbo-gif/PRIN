# PRIN Executive Testing and CI Audit Report — Session 001 (ETCA-001)

**Date:** 2026-09-01
**Auditor:** AI pair (Claude Sonnet 5)
**Scope:** Executive Testing and CI Audit — Phase 6 mid-phase (WP-033 through
WP-036C S4, sessions 0129–0144P). First ETCA session; establishes the audit
type.
**Audit window:** Delta since EA-006 (`5d90427`, 2026-08-26) through `e4fb372`
— ~120 commits, sessions 0129–0144P plus global sessions EMA-006 and EDA-001.
Net Python test count ~1,770 → ~2,969 collected (`+1,199`); ported acceptance
suite 0 → 37 files / 1,670 `def test_` functions; new first-party Rust
~2,010 lines; CI/runner topology changed 3× (DV-016/DV-023/DV-024).
**Git Branch/State:** `main` @ `e4fb372` (local, EDA-001 closure; clean working
tree at session start); **`origin/main` @ `0313af5`** (WP-036D S4 closure) —
**local is 28 commits ahead of origin.**
**Live CI state at session start (`gh run list`, latest `origin/main` push
`0313af5`):** `rust` **failure** (self-hosted Windows leg: "exceeded maximum
execution time while awaiting a runner for 24h"; all hosted legs green),
`python` **failure** (lint + all 6 test-matrix legs), `repro` **failure**
(build step), `parity` **success**, `snyk` **success**, `gpu` skipped (no
`[gpu]` tag).
**Governing methodology:**
`DOCS/standards/Executive_Testing_and_CI_Audit_Governance_and_Methodology.md`
(established this session as Task 1; registered by Project Plan amendment #42).
**Prior session:** First ETCA session.
**Verdict:** **PASS-WITH-REMEDIATION**

---

## 0. What this session did

Phase 6 has produced the largest test-and-CI delta in the project's history:
the WP-036B + WP-036C strict acceptance-suite port added 37 files / 1,670
`def test_` functions (import-only adaptation of the PRINet 3.0 reference
suite), the WP-036A trainable-layer rebuild added ~600 first-party tests, and
the CI runner topology was rebuilt three times across Phase 5/6 (DV-016,
DV-023, DV-024). The EA session's E3/E9 dimensions sample this; they do not
exhaust it. A dedicated test-and-CI audit was warranted before Phase 6
continues to WP-036E/F/G and before the phase-close push.

This session had four objectives:

1. **Establish the ETCA methodology and governance** — define the audit type,
   its 8 dimensions (T1–T8), severity classification, workflow lifecycle, and
   reporting rules; register it as a global session type (plan amendment #42).
2. **Execute the audit** across all 8 dimensions against the Phase 6 test/CI
   delta, reproducing every mandated gate command's real exit code and
   pulling the live `origin/main` CI logs.
3. **Report findings and recommend remediation** for execution in a
   subsequent session.
4. **Document and commit locally.**

All four objectives were completed. **Ten findings** were discovered: zero D1,
three D2 (T-F1, T-F2, T-F3), five D3 (T-F4–T-F8), two D4 (T-F9, T-F10). The
headline is that **CI is red on `origin/main` and the entire WP-036C cycle
(28 commits) is unpushed and has never been through CI** — the mid-phase audit
did its job by surfacing this before the phase-close push.

This session is read-only with respect to first-party source and test code:
every finding is planned, not fixed. Consistent with the EDA-001 precedent, a
dedicated remediation session executes the source/test/workflow fixes.

---

## 1. Executive Summary Table

| Audit Dimension | Status | Summary & Key Observations |
|---|---|---|
| **T1: Test Suite Inventory & Health** | ⚠️ REMEDIATION | Local fast gate at `e4fb372`: **14 failed, 2729 passed, 201 skipped, 25 deselected** (410 s, `--basetemp=.pytest_basetemp` per AGENTS.md). No `xfail` anywhere (conforms). The 14 failures decompose into T-F2 (`prinet` missing — but not reproduced here because the maintainer host has it), T-F3 (`test_wp001_baseline.py` ×3, real), and T-F9 (`test_acceptance_y4q2` ×11, basetemp-sensitive). PSR-036C reported "2,743 passed, 201 skipped, **0 failed**" — measured with the default `%TEMP%` basetemp, which masks T-F9; and predating T-F3's brief edit. Rust workspace builds clean; `cargo fmt --check` clean. |
| **T2: Test-in-Tandem & Coverage Compliance** | ⚠️ REMEDIATION | Test-in-tandem holds for the audited scope (every WP-036* S1 range commits source + tests together — spot-verified across WP-036A/B/C). Coverage: `pytest --cov` reports **95% overall (7,683 stmts, 408 missing)** on the fast gate — at the ≥95% threshold but with no margin, and 8 first-party modules below 95% (`y4q1_tools.py` 83%, `simulation_experiments.py` 86%, `mot_evaluation.py` 87%). Per-change coverage (the actual gate — "≥95% for new/changed code") is **not locally measurable** on this host (`pytest-cov`/`coverage` instability, carried from Phase 6) and CI codecov has not run for the WP-036C range (T-F4). |
| **T3: Specialized Test Layers** | ✅ PASS | `proptest` property tests, `torch.autograd.gradcheck` (float64) bridges, and kernel-equivalence suites are present for the scope they cover (`test_gradcheck_*.py`, `crates/**/tests/parity_*.rs`, `prin-kernels` `--features cpu`). Stochastic tests seed through the `Seed` type. No missing required layer was found for Phase 6's touched primitives — WP-036C is import-only test porting (no new primitives), and its Rust additions (`polyfit`, `oscillo_compat`, STE term) carry unit tests (EMA-006 independently authored claims for the mathematical content). |
| **T4: Parity & Differential Testing** | ✅ PASS (CI-pending) | `parity/test_parity_differential.py` parametrised over all 504 corpus cases; `parity` workflow **`success`** on `origin/main` (`0313af5`). No tolerance annotation was added in Phase 6 beyond the one governed Parity Report entry for the GPU sparse-k-NN f32 dispatch (WP-036D) and the RNG-regime entry (WP-036C M5) — both carry `parity_report.rst` entries (Testing Standards §3 satisfied). The WP-036C range's own parity run is CI-pending (T-F4). |
| **T5: Governed Skips, Flaky Tests & Quarantine** | ⚠️ REMEDIATION | The `tests/conftest.py` central governed-skip layer is exemplary: one auditable hook, every entry names its governing item (DV-031, plan amendment #41, M5 RNG disposition), ported test text byte-unchanged. **But** `test_no_gpu_throughput_regression` is quarantined in the same hook as a "pre-existing host-sensitive perf-ratio flake … flagged in PSR-036C for a perf-test disposition" with **no DV-register row and no dated quarantine-specific maintainer approval** — Testing Standards §1.4 requires a linked issue and maintainer approval (T-F8). 201 skips total; the non-conftest skips are reference `skipif`/`pytest.skip` guards preserved verbatim (conforms). |
| **T6: CI/CD Workflow Coverage & Gate Effectiveness** | ❌ FAIL | All 7 workflows present and triggered as intended. **But on `origin/main`:** (a) the `python.yml` `lint` job **fails at the `bandit` step** (exits 1 on 3 Phase-6 Low findings suppressed only with ruff `# noqa`, not bandit `# nosec`), which makes the two later steps in the same job — the **R17 deviation-ledger gate** and the **R34 DV-register gate**, both built as *durable CI enforcement* by EA-004/EA-006 — **never execute** (T-F1); (b) all 6 `python.yml` test-matrix legs fail (T-F2 `prinet` missing on Windows; T-F5 disk exhaustion on ubuntu); (c) `repro.yml` fails at build (T-F5); (d) `rust.yml`'s self-hosted Windows leg hung 24 h awaiting an offline runner (T-F6). |
| **T7: Benchmark Regression Gates & Reproducibility Pipeline** | ⚠️ REMEDIATION | `tools/reproduce.py --verify-manifest` and `tests/test_reproduce.py` pass **locally** (exit 0); `repro.yml` does not run in CI (T-F5). **No enforcing benchmark-regression gate exists:** `rust.yml bench-smoke` runs one bench with `--test` (its own comment: "does not reproduce or gate on the documented speedup ratios"); `gpu.yml`'s "Kernel performance regression gates" runs `cargo bench … --save-baseline ci` which only *writes* a baseline, never compares; `pytest-benchmark` cases are `slow`-marked and excluded from `python.yml`; **no workflow has a `schedule:` trigger** despite Testing Standards §4 ("the full suite runs nightly"). A >10% regression cannot fail CI (T-F7). |
| **T8: Test Evidence, Traceability & Local/CI Gate Equivalence** | ⚠️ REMEDIATION | Multiple Phase-6 S4 PSR verification blocks record gate outcomes that do not match the commands as run: `bandit` "3 Low → passed" (command exits 1), `wp001_baseline.py check` "passed" (exits 1 at `fa427ad`), fast suite "0 failed" (14 fail at HEAD with the mandated basetemp). `python.yml` runs `bandit -r python/prin`; `AGENTS.md` runs `bandit -r .` (4 findings vs 3) — command drift, neither marked canonical (T-F10). The `origin/main` CI red state was not surfaced by any Phase-6 S4 PSR (T-F4). |

---

## 2. Detailed Findings across Audit Dimensions

### T1: Test Suite Inventory & Health

**Local default gate at `e4fb372`** (`pytest tests/ -m "not slow and not gpu"
--cov=prin --basetemp=.pytest_basetemp`, 2026-09-01, this host — Windows 11 /
Python 3.14.0 / torch 2.11.0+cu128):

```
14 failed, 2729 passed, 201 skipped, 25 deselected, 54 warnings in 410.43s
```

The 14 failures:

| Test(s) | Count | Root cause | Finding |
|---|---:|---|---|
| `test_acceptance_y4q2.py::TestGenerateAllFigures/TestGenerateAllTables/TestEdgeCases::*` | 11 | `prin.reporting.figure_generation.OutputPathError` — `--basetemp=.pytest_basetemp` (in-repo) is outside `ALLOWED_OUTPUT_ROOTS` (`benchmarks/results`, `DOCS/test_and_benchmark_results`, `tempfile.gettempdir()`) | **T-F9** (D4) |
| `test_wp001_baseline.py::{test_cli_check_reports_success, test_current_baseline_automation_is_green, test_session_plan_validator_accepts_additive_subsessions}` | 3 | `validate_session_plan` / `validate_baseline` → `"session 0144P: brief/register session type mismatch"` | **T-F3** (D2) |

`cargo build --workspace` exit 0; `cargo fmt --all -- --check` exit 0 at
`e4fb472`. Rust default/strict test runs are CI-pending for the WP-036C range
(T-F4); PSR-036C reports "~1,564 passed, 0 failed, 1 ignored" locally and
EMA-006 independently exercised the Rust math surface at `fa427ad`.

**No `xfail`** anywhere in `tests/` (grep-verified) — conforms to Testing
Standards and `tests/README.md`.

### T2: Test-in-Tandem & Coverage Compliance

- **Test-in-tandem:** spot-checked WP-036A (`d8b760e`, `756c4d2`, `e05e29d`
  each add source + tests in one commit), WP-036B (`0144E1`–`0144E6` strict
  port), WP-036C (`0144M1`–`0144M8` strict port + Rust owners with unit
  tests). No source-without-tests commit found in the audited range.
- **Coverage:** the fast-gate `--cov=prin` run reports **95% overall** (7,683
  statements, 408 missing) — exactly at the Testing Standards §4 ≥95% floor,
  no headroom. Modules below 95%: `y4q1_tools.py` 83%, `simulation_experiments.py`
  86%, `mot_evaluation.py` 87%, `subconscious_compat.py` 92%, `optimizers.py`
  93%, `training_hooks.py` 93%. The actual gate ("≥95% for **new/changed**
  code, non-decreasing overall") cannot be evaluated locally on this host
  (`pytest-cov`/`coverage` instability, a Phase-6 carried condition) and
  CI codecov (`python.yml`, ubuntu 3.12) has not run for the WP-036C range
  because that range is unpushed (T-F4) and, when last run at `0313af5`, the
  ubuntu leg died at build (T-F5). This coverage-measurement gap is **not
  recorded in the DV register** — see T-F4 remediation.

### T3: Specialized Test Layers

WP-036C is import-only acceptance-suite porting — it introduces no new
numerical primitive, kernel, or `autograd.Function` bridge, so it triggers no
new specialized-layer obligation. Its first-party Rust additions
(`prin_sim::y4q1_stats::polyfit`, `oscillo_compat`, the
`DiscreteDeltaThetaGamma` STE identity term) carry `#[cfg(test)]` unit tests
in the same commits, and EMA-006 independently authored and passed tool-executed
claims (`POLYFIT-01/02`, `SPATCORR-01`, …) for the mathematical content.
`proptest`, float64 `gradcheck`, and CPU/GPU kernel-equivalence suites are
present for the scope they cover. Stochastic tests seed through the `Seed`
type. **No finding.**

### T4: Parity & Differential Testing

- `parity/test_parity_differential.py` is parametrised over all 504 corpus
  cases (R8, closed); `parity/test_parity_subconscious.py` present.
- `parity` workflow conclusion on `origin/main` (`0313af5`): **`success`**
  (7m3s, `pytest parity/ -m parity -n auto`).
- Phase 6 added exactly two governed tolerance/parity dispositions, both with
  `DOCS/sphinx/parity_report.rst` entries: the WP-036D GPU sparse-k-NN f32
  dispatch (`rtol=1e-5, atol=1e-5`) and the WP-036C M5 RNG-regime divergence
  (deterministic `Seed` vs `torch.Generator`). No acceptance assertion was
  weakened (Testing Standards §1.1; confirmed by the WP-036C S2 A4 clean-diff
  finding). **No finding** — the WP-036C range's own parity CI run is pending
  (folded into T-F4).

### T5: Governed Skips, Flaky Tests & Quarantine

The `tests/conftest.py` `pytest_collection_modifyitems` governed-skip layer is
a model implementation: a single auditable hook; every skipped node maps to a
named governing item (`DV-031(A)` WP-037/038 deliverables, `DV-031(B)`
WP-036E CUDA path, plan amendment #41 versioning, the M5 RNG disposition);
ported test bodies are byte-unchanged (an adaptation hook, not a test edit).

**Finding T-F8 (D3):** the same hook also skips
`test_acceptance_subconscious.py::TestIntegration::test_no_gpu_throughput_regression`
with the reason *"Pre-existing host-sensitive perf-ratio flake from WP-036B S1
(not a WP-036C finding); … Flagged in PSR-036C for a perf-test disposition."*
This is a **quarantine**, and Testing Standards §1.4 requires "a linked issue
and maintainer approval". The skip cites **no DV-register row** (unlike the
DV-016 / DV-019 precedents for exactly this class of timing flake) and **no
dated quarantine-specific maintainer approval** — the conftest header's blanket
approval line is scoped to the DV-031 / amendment-#41 decisions. PSR-036C §5
lists it as a bare risk with no owner WP or DV number.

201 skips total on the fast gate; the non-conftest skips are reference
`skipif(not torch.cuda.is_available())` guards and reference-text
`pytest.skip(...)` calls preserved verbatim from PRINet 3.0 (`y4q1_8` ×65,
`triton_kernels` ×33, `y4q1_9` ×5) — these conform.

### T6: CI/CD Workflow Coverage & Gate Effectiveness

All 7 workflows (`rust`, `python`, `parity`, `repro`, `gpu`, `snyk`,
`release`) exist and are triggered as the `.github/workflows/README.md`
inventory describes. Gate-effectiveness verification (reproducing each command
locally):

| Gate | Command | Local exit | In CI? | Effective? |
|---|---|---:|---|---|
| Ruff / format / mypy / interrogate | (as `python.yml` lint) | 0 / 0 / 0 / 0 | yes | ✅ |
| **bandit** | `bandit -r python/prin -c pyproject.toml` | **1** | yes (lint) | ❌ **T-F1** — gate is red |
| Deviation-ledger | `check_deviation_ledger.py 036c 036d` | 0 (120 vs 120 rows) | yes (lint, **after** bandit) | ❌ **T-F1** — never runs (bandit fails first) |
| DV-register | `check_dv_register_gates.py` | 0 (31 rows × 198) | yes (lint, **after** bandit) | ❌ **T-F1** — never runs |
| No-Python-numerics | via `test_no_python_numerics.py` | 0 | yes (pytest) | ✅ (subject to T-F5/T-F6 test-job outage) |
| Baseline | via `test_wp001_baseline.py` | **fails ×3** | yes (pytest) | ⚠️ **T-F3** — gate red |
| `cargo audit` / `pip-audit` | | 0 / — | yes | ✅ |
| Sphinx `-W` | fresh-dir build | 0 (EDA-001 remediation) | — | ✅ |
| Snyk Code / Gitleaks | | — | yes | ✅ (`snyk` `success` on `origin/main`) |

Live `origin/main` (`0313af5`) per-workflow conclusion: `rust` **failure**,
`python` **failure**, `repro` **failure**, `parity` **success**, `snyk`
**success**. Detailed root causes in §3 (T-F1, T-F2, T-F5, T-F6). The
`0313af5` Windows `python` legs also failed two tests unrelated to `prinet`:
`test_acceptance_hybrid.py::TestStateCollector::test_latency_percentiles` (a
host-sensitive timing percentile assertion — same class as T-F8) and
`test_wp036d_gpu_dispatch.py::test_gpu_sparse_knn_dispatch_hook_agrees_with_cpu_reference`
(a WP-036D dispatch test — CPU-reference agreement on the hosted Windows
image). Both predate the WP-036C range's conftest/tolerance work and should be
re-checked when T-F4's push finally runs CI; if either persists it is a new
finding for the remediation session.

Branch-protection required-check membership was **not independently verified**
this session (requires repo-admin API access); recommended for the remediation
session or the next EA.

### T7: Benchmark Regression Gates & Reproducibility Pipeline

**Reproducibility pipeline:** `tools/reproduce.py --verify-manifest` → exit 0
("Generated 39 files", manifest verified); `pytest tests/test_reproduce.py` is
in the fast gate and passed in the local run. The `repro` **workflow** fails
in CI (T-F5) — so requirement F4's CI enforcement is currently inert.

**Benchmark-regression gates (T-F7, D3):** Testing Standards §2 requires
`criterion` + `pytest-benchmark` regression gates that "fail on >10%
slowdown". No such enforcing gate exists:

- `rust.yml` `bench-smoke`: `cargo bench -p prin-sim --bench sweep_bench --
  --test` — compile-and-run smoke only; its own comment states it "does not
  reproduce or gate on the documented speedup ratios".
- `gpu.yml` "Kernel performance regression gates": `cargo bench … --save-baseline
  ci` — **writes** a baseline named `ci` on every run; there is no
  `--baseline`/`--load-baseline` comparison step and no `critcmp` threshold,
  so it can never fail on a regression.
- `pytest-benchmark` cases (`test_dlpack_bridge.py`, `test_benchrunner.py`,
  `test_train_bridge*.py`) are `@pytest.mark.slow` and excluded by
  `python.yml`'s `-m "not slow and not gpu"`.
- **No workflow has a `schedule:` trigger** (`grep -rn "schedule\|cron"
  .github/workflows/` → empty), so Testing Standards §4's "the full suite runs
  nightly and on release tags" is unmet — there is no nightly full run, and
  the release path (`release.yml`) runs only wheel builds + smoke, not the
  suite.

### T8: Test Evidence, Traceability & Local/CI Gate Equivalence

- **PSR verification-claim accuracy (T-F10, D4):** PSR-036C §2 records
  `bandit … # 3 Low (pre-existing), 0 Med/High` and
  `wp001_baseline.py check # passed` — both commands exit **1** as committed
  at `fa427ad`. PSR-036D §2 records `bandit … # 1 Low (B110, governed)` — also
  exit 1. The fast-suite "0 failed" line was measured with the default
  `%TEMP%` basetemp (PSR-036C) which does not reproduce T-F9, or predates the
  WP-036C port (PSR-036D). These are genuinely-nearly-passing gates reported
  slightly too favourably, not fabrications — hence D4 — but they mean "the
  local gate passed" was not a reliable proxy for CI this phase.
- **Command drift (T-F10):** `python.yml` runs `bandit -r python/prin`;
  `AGENTS.md` runs `bandit -r .` (4 vs 3 findings). Neither is marked
  canonical. `check_deviation_ledger.py` in CI compares the two
  lexically-last PSRs (`036c` then `036d` — reverse chronological, but
  EDA-001's D-F4 delegation-pointer fix makes it compare 120 vs 120 rows
  correctly).
- **`origin/main` CI red not surfaced (folded into T-F4):** no Phase-6 S4 PSR
  (036, 036a–036d) reports the live `origin/main` CI conclusion; each reports
  only the local gate. The push/CI-cadence exit criterion (Development
  Workflow §3 S4: "CI is fully green on that push") was therefore not actually
  verified at any Phase-6 cycle close.

---

## 3. Discovered Deviations and Findings Table

| ID | Severity | Dimension | Location / Subsystem | Issue Description | Violated Clause | Status |
|---|---|---|---|---|---|---|
| **T-F1** | **D2** | T6 | `.github/workflows/python.yml` `lint` job; `python/prin/kernels.py` (B404/B603), `python/prin/nn/hybrid_compat.py:327` (B110); `AGENTS.md` one-liner | `bandit -r python/prin -c pyproject.toml` **exits 1** on 3 Phase-6-introduced Low findings suppressed only with ruff `# noqa: S6xx/S110` (not bandit `# nosec`). The `lint` job fails at this step, so the **R17 deviation-ledger gate** and **R34 DV-register gate** (both built as durable CI enforcement by EA-004/EA-006) — which run *later in the same job* — never execute on any push. At EA-006 (`5d90427`) bandit was genuinely clean; this is a Phase-6 regression that WP-036B/C/D S2 audits and every Phase-6 S4 PSR recorded as "3 Low (pre-existing) / passed". | Coding Standards §6 ("do not suppress findings without approved, evidence-backed governance"; secure-dev gate must pass); Development Workflow §3 ("deviations never accumulate"); R17 / R34 durable-enforcement intent | **OPEN** — recommend remediation in a dedicated session |
| **T-F2** | **D2** | T3 / T6 | `tests/test_autoencoders.py`, `tests/test_hierarchical_layers.py`, `tests/test_inhibition_layers.py`, `tests/test_model.py` (all WP-036A, 2026-08-30/31); `.github/workflows/python.yml` | ≥13 reference-parity tests do `from prinet… import … as Reference` **inside the test body** with no `importorskip`/`skipif` guard. `python.yml` does not install the archived PRINet 3.0 reference (only `parity.yml` does), so every such test **hard-fails `ModuleNotFoundError: No module named 'prinet'`** on every `python.yml` test-matrix leg. They pass on the maintainer host only via an editable install of the non-authoritative `DOCS/archive …/PRINet-3.0.0-main` tree. WP-036A S2 audit ("PASS, zero findings") missed this. | Testing Standards §2 (Python API layer), §4 (tests independent; no undeclared env dependency; cached fixtures); CLAUDE.md ("`DOCS/archive/` is historical and non-authoritative") | **OPEN** — recommend remediation in a dedicated session |
| **T-F3** | **D2** | T1 / T8 | `DOCS/sessions/phase-6/0144P-wp036c-s4-*.md`; `tools/wp001_baseline.py` (`lines[:12]` metadata parser); `tests/test_wp001_baseline.py` | Session brief `0144P` (WP-036C S4) opens with a multi-line `**Status:**` block that pushes `**Session type:**` to line 13; the parser reads only `lines[:12]`, so `Session type` is unparsed → `"session 0144P: brief/register session type mismatch"`. `wp001_baseline.py check` exits 1; `test_wp001_baseline.py` fails ×3 in the default gate. Present at `fa427ad`; WP-036C S4, EMA-006, and EDA-001 all closed/committed over the red. PSR-036C records the gate as "passed". | Testing Standards §1.4 ("never leave a failing test"); Development Workflow §3 S4 exit criteria (local gate green), §4 A10 (artefact-trail consistency) | **OPEN** — recommend remediation in a dedicated session |
| **T-F4** | **D3** | T6 / T8 | `origin/main` vs local `main`; Development Workflow §3 "Push and CI cadence" (amendment #28) | The WP-036C cycle (`0144M`–`0144P`) plus EMA-006 and EDA-001 — **28 commits, ~143k insertions, +1,172 acceptance tests, +~2,010 first-party Rust lines, 2 new EMA claim ledgers** — is **unpushed**; CI has never executed against any of it. Per Development Workflow §3 the WP-036C S4 commit (`fa427ad`) is "the cycle's sole push … CI fully green on that push"; that push has not happened, so WP-036C is not closed by the standard's own exit criterion, though PSR-036C declares it closed. WP-036E S1 is the registered successor and would build on the unverified range. Sub-item: the Phase-6 per-change-coverage measurement gap (T2) is not recorded in the DV register. | Development Workflow §3 S4 exit criteria + "Push and CI cadence" (amendment #28); Documentation Standards §7 item 5 | **OPEN** — recommend the maintainer push the WP-036C S4 range and drive CI green (after T-F1/T-F2/T-F3/T-F5/T-F6) **before** WP-036E S1 begins; record the coverage-measurement gap as a DV item |
| **T-F5** | **D3** | T6 / T7 | `.github/workflows/repro.yml`, `.github/workflows/python.yml` (ubuntu legs); DV-022 | On `origin/main`, `repro`'s "Build and install" and all 3 ubuntu `python` test legs fail `[Errno 28] No space left on device` during `maturin develop` / `pip install -e ".[dev,onnx]"` — the torch install pulls the full `nvidia-*-cu13` CUDA stack + `triton` (~5 GB) despite the `--index-url …/whl/cpu` intent, exhausting the 14 GB `ubuntu-latest` disk. Same root cause as DV-022, but DV-022's documented WSL2 self-hosted-Linux fallback is wired only into `parity.yml`. The reproducibility gate (requirement F4) does not run in CI. | Testing Standards §2 (Reproducibility layer); Benchmarking and Reproducibility Standards; DV-022 disposition | **OPEN** — extend DV-022 scope to `repro.yml` + `python.yml`; add a disk-reclaim step or route to a self-hosted Linux runner; pin a true CPU-only torch that does not drag the CUDA wheels |
| **T-F6** | **D3** | T6 | `.github/workflows/rust.yml` `test (windows-latest, self-hosted)`; `PRIN-GPU-Runner`; DV-024 | On `origin/main`, the self-hosted Windows `rust` test leg **hung 24 h "awaiting a runner"** then auto-failed — `PRIN-GPU-Runner` was offline. DV-024 (marked CLOSED 2026-08-25) is the same condition: migrating Windows CI entirely onto a single self-hosted runner removed the hosted-runner slowness (DV-016/DV-023) but also removed the fallback. All hosted `rust` legs (ubuntu, macOS, clippy, strict, docs, fmt, audit, bench-smoke) are green. | Development Workflow §3 S4 exit criteria (CI green); Versioning and Release Standards §3 | **OPEN** — add a hosted-runner fallback for the self-hosted Windows `rust` leg, or a fail-fast runner-online preflight instead of a 24 h queue hang; consider a queue-wait `timeout` |
| **T-F7** | **D3** | T7 | `.github/workflows/rust.yml` (`bench-smoke`), `.github/workflows/gpu.yml` ("Kernel performance regression gates"); no `schedule:`d workflow | No **enforcing** benchmark-regression gate exists. `bench-smoke` is `--test` compile-only; `gpu.yml` runs `cargo bench … --save-baseline ci` which only *writes* a baseline (no `--baseline` comparison, no `critcmp` threshold); `pytest-benchmark` cases are `slow`-excluded from `python.yml`; zero workflows have a `schedule:` trigger, so Testing Standards §4's "full suite runs nightly" is unmet. A >10% perf regression cannot fail CI. | Testing Standards §2 (Benchmarks — "fail on >10% slowdown"), §4 ("full suite runs nightly and on release tags"); Benchmarking and Reproducibility Standards | **OPEN** — add a `schedule:`d full-suite + `cargo bench --baseline` compare workflow on the self-hosted reference runner; wire `pytest-benchmark --benchmark-compare-fail`; or record a dated deferral |
| **T-F8** | **D3** | T5 | `tests/conftest.py` (`_FLAKE_NODES` / `_FLAKE_SKIP`); `test_acceptance_subconscious.py::TestIntegration::test_no_gpu_throughput_regression`; PSR-036C §5 | The perf-ratio flake is **quarantined** (skipped) in the conftest hook with no DV-register row and no dated quarantine-specific maintainer approval. Testing Standards §1.4: "Quarantine requires a linked issue and maintainer approval." Same class as DV-016 / DV-019 but never given a register row; PSR-036C §5 lists it as a bare risk with no owner. | Testing Standards §1.4 (quarantine governance) | **OPEN** — open a DV item (or fold into a perf-test-hardening DV) with a dated maintainer disposition and a concrete fix path; reference it from the conftest skip reason |
| **T-F9** | **D4** | T1 / T8 | `python/prin/reporting/figure_generation.py` (`ALLOWED_OUTPUT_ROOTS`); `tests/test_acceptance_y4q2.py` (`TestGenerateAllFigures` / `TestGenerateAllTables` / `TestEdgeCases`); `AGENTS.md` | 11 WP-036C figure/table-generation tests raise `OutputPathError` when run with `--basetemp=.pytest_basetemp` (the in-repo basetemp `AGENTS.md` mandates for Windows), because the reporting output allowlist is `{benchmarks/results, DOCS/test_and_benchmark_results, tempfile.gettempdir()}` and the in-repo path is outside it. PSR-036C ran the fast gate without `--basetemp` (default `%TEMP%` → pass); PSR-036D ran it with `--basetemp` but predates the port. CI (dynamic `gettempdir()`) is unaffected. The canonical local one-liner as written produces 11 spurious Windows failures and the two PSRs' runs are not comparable. | Testing Standards §4 (tests order/environment-insensitive); AGENTS.md local-gate consistency | **OPEN** — add the pytest basetemp (or `PYTEST_DEBUG_TEMPROOT`) to the reporting allowlist for test contexts, OR exclude figure/table tests from the `.pytest_basetemp` override in `AGENTS.md`, OR document the exclusion |
| **T-F10** | **D4** | T8 | Phase-6 S4 PSR verification blocks (036c §2, 036d §2); `AGENTS.md` vs `python.yml` bandit invocation | S4 verification blocks report `bandit` and `wp001_baseline.py check` as "passed"/"3 Low" when the commands as committed exit 1 (T-F1, T-F3), and "0 failed" fast suites measured under a basetemp that masks T-F9. `python.yml` runs `bandit -r python/prin`; `AGENTS.md` runs `bandit -r .` (4 vs 3 findings) — command drift, neither marked canonical. Genuinely-nearly-passing gates reported slightly too favourably (hence D4), but they broke "local gate green ⇒ CI green" this phase. | Development Workflow §1.4 ("audits are evidence-based … never by recollection"); Documentation Standards §7 | **OPEN** — single source of truth per gate command (a script both CI and `AGENTS.md` call); S4 verification blocks paste real exit codes |

---

## 4. Remediation Plan

### 4.1 Immediate Remediation (Not executed — this audit is read-only w.r.t. first-party source/test code)

No D1 findings exist. All three D2 findings (T-F1, T-F2, T-F3) require
source/test-code or workflow edits that are out of scope for an audit session
(EDA-001 §4.1 precedent). This session's own changes are limited to the new
governance document, the template, this report, the registration artefacts,
and the CHANGELOG entry.

### 4.2 Pass-Forward Items (Recommended for a dedicated ETCA-001 remediation session)

Ordered by dependency — the CI-green gate for Phase 6 close depends on 1–3 and 5–6:

1. **T-F1 (D2, bandit gate red):** add `# nosec B404` / `# nosec B603` /
   `# nosec B110` at the three sites in `python/prin/kernels.py` and
   `python/prin/nn/hybrid_compat.py` (carrying the vswhere-is-MS-signed /
   daemon-not-ready rationale already documented for the ruff `# noqa`), so
   `bandit` exits 0. **Additionally** restructure `python.yml`'s `lint` job so
   the deviation-ledger and DV-register steps run under `if: always()` or in a
   separate job — they must not be reachable only when every prior lint step
   passes. Verify: `bandit -r python/prin -c pyproject.toml` exit 0; a
   deliberately-corrupted PSR still fails the ledger step.

2. **T-F2 (D2, `prinet` missing in CI):** add
   `prinet = pytest.importorskip("prinet")` at the top of each of the ~13
   affected test bodies in `test_autoencoders.py`, `test_hierarchical_layers.py`,
   `test_inhibition_layers.py`, `test_model.py` (the `*_matches_installed_prinet`
   naming already implies optionality). Alternative: install the reference in
   `python.yml` as `parity.yml` does — heavier, and couples the fast gate to
   the archive. Recommend `importorskip`. Verify: `pip uninstall prinet` then
   `pytest tests/test_autoencoders.py …` → skipped, not failed.

3. **T-F3 (D2, `wp001_baseline` red):** (a) shorten/relocate the `0144P`
   brief's `**Status:**` block so `**Session type:**` is within the first 12
   lines; and (b) harden `tools/wp001_baseline.py` to scan all leading
   `**key:**` lines until the first blank line or `##` heading, not a hard
   `lines[:12]` cap. Verify: `wp001_baseline.py check` exit 0;
   `pytest tests/test_wp001_baseline.py` green.

4. **T-F8 (D3, untracked quarantine):** open a DV-register row (or fold into a
   new "perf-test hardening" DV) for `test_no_gpu_throughput_regression` with a
   dated maintainer disposition and a concrete fix (widen the ratio, mark
   `slow`, or convert to a `pytest-benchmark` gate); update the conftest skip
   reason to name it.

5. **T-F5 (D3, `repro`/`python` ubuntu disk):** extend the DV-022 disposition
   to `repro.yml` and `python.yml`; add a `rm -rf /opt/hostedtoolcache
   /usr/share/dotnet /usr/local/lib/android` reclaim step before the build, or
   route to the self-hosted Linux runner; investigate why torch pulls the
   `cu13` stack under `--index-url …/whl/cpu` and pin accordingly.

6. **T-F6 (D3, self-hosted runner hang):** add a hosted-runner fallback leg for
   `rust.yml`'s Windows tests (or a fail-fast preflight that checks
   `gh api …/actions/runners` and skips-with-notice instead of a 24 h hang).

7. **T-F7 (D3, no bench-regression gate):** add a `schedule:`d workflow (nightly)
   running `pytest tests/ parity/ -v` and `cargo bench --workspace` with
   `criterion --baseline`/`critcmp` and a 10% failure threshold on the
   self-hosted reference runner; or record an explicit dated deferral to a
   named WP.

8. **T-F9 (D4):** add the pytest basetemp to `figure_generation.ALLOWED_OUTPUT_ROOTS`
   for test contexts (or gate on an env var), or amend `AGENTS.md` to run the
   figure/table tests without the `.pytest_basetemp` override.

9. **T-F10 (D4):** create a single gate script (`tools/local_gate.*` or a
   `Makefile`) that both `python.yml`/`rust.yml` and `AGENTS.md` invoke, so the
   commands cannot drift; require S4 verification blocks to paste real exit
   codes.

10. **T-F4 (D3, unpushed range):** once 1–3 and 5–6 land, the maintainer pushes
    the WP-036C S4 range (`fa427ad` + the audit commits) and confirms `rust`,
    `python`, `parity`, `repro`, `snyk` all green on `origin/main` **before**
    WP-036E S1 begins. If the mid-phase-audit-before-push sequencing is
    deliberate for the Phase-6-close batch, record it as an explicit
    amendment-#28 exception in the PSR / a plan amendment.

### 4.3 Cross-audit observation (not an ETCA finding — out of dimension)

The two Phase-6 mid-phase global audit sessions committed just before this one
each closed without their required registration artefacts:

- **EMA-006** (`3ab206a`, 2026-09-01): no `SESSION_REGISTER.md` row — the
  "Global sessions — Executive Mathematical Audits" table still ends at
  EMA-005. `Executive_Mathematical_Audit_Governance_and_Methodology.md` §8.2
  requires the row.
- **EDA-001** (`cf81f05`/`e4fb372`, 2026-09-01): no Project Plan amendment and
  no `SESSION_REGISTER.md` "Global sessions — Executive Documentation Audits"
  section or EDA-001 row. `Executive_Documentation_Audit_Governance_and_Methodology.md`
  §5.2 requires the section; the EMA precedent (plan amendment #23) implies an
  amendment.

ETCA-001 follows the stronger EMA precedent in full: plan amendment #42 and a
dedicated `SESSION_REGISTER.md` section + ETCA-001 row, both added this
session, with a bracketed note in the register pointing at the EMA-006/EDA-001
gap. Flagged for the maintainer / the next EMA, EDA, or EA session to
reconcile. This is out of the T1–T8 dimension scope (it is a governance-
traceability matter, EDA/EA territory) and is recorded here only because
ETCA-001 touches the same registration machinery.

---

## 5. Verification Suite Results (Task 3 — evidence, not a session gate)

This audit session is read-only; the commands below are evidence for the
findings, not a claim that the session's own changes pass (the session
produces governance/report artefacts only).

| Verification Step | Command | Result (real exit code) | Notes / Evidence |
|---|---|---|---|
| Rust build | `cargo build --workspace -q` | **0** | clean at `e4fb372` |
| Rust format | `cargo fmt --all -- --check` | **0** | clean |
| Rust tests (`prin-sim`/`prin-train`/`prin-py`) | `cargo test -p prin-sim -p prin-train -p prin-py --quiet` | **0** | all green (WP-036C-touched crates); full `cargo test --workspace` is CI-pending for this range (T-F4) |
| Python fast gate | `pytest tests/ -m "not slow and not gpu" --cov=prin --basetemp=.pytest_basetemp` | **1** (14 failed) | T-F3 ×3 (real), T-F9 ×11 (basetemp), 2729 passed, 201 skipped |
| Coverage (overall) | (from the run above) | 95% (7683 stmts, 408 missing) | at floor, no margin; per-change gate not locally measurable (T-F4) |
| Ruff check | `ruff check python/ tests/ benchmarks/ tools/ parity/` | 0 | (PSR-036C evidence; unchanged in EDA-001 delta) |
| Ruff format | `ruff format --check …` | 0 | |
| mypy | `mypy python/prin --strict` | 0 | |
| interrogate | `interrogate -c pyproject.toml python/prin` | 0 | 97.6% (PSR-036C) |
| **bandit** | `bandit -r python/prin -c pyproject.toml` | **1** | 3 Low (B404/B603 `kernels.py`, B110 `hybrid_compat.py:327`) — **T-F1** |
| **bandit (AGENTS variant)** | `bandit -r . -c pyproject.toml` | **1** | 4 findings — **T-F1 / T-F10** |
| Deviation-ledger gate | `check_deviation_ledger.py DOCS/reports/036c-… 036d-…` | **0** | 120 vs 120 rows (EDA-001 D-F4 delegation fix working); **never runs in CI** — T-F1 |
| DV-register gate | `check_dv_register_gates.py` | **0** | 31 rows × 198 entries; **never runs in CI** — T-F1 |
| **Baseline gate** | `tools/wp001_baseline.py check` | **1** | `session 0144P: brief/register session type mismatch` — **T-F3** |
| No-Python-numerics | via `pytest tests/test_no_python_numerics.py` | 0 | 19 modules clean |
| Reproducibility | `tools/reproduce.py --verify-manifest` | **0** | 39 files, manifest verified; `repro.yml` fails in CI — T-F5 |
| Sphinx `-W` (fresh dir) | `sphinx-build -W --keep-going …` | 0 | EDA-001 remediation (D-F1) — 0 warnings |
| `cargo audit` | | 0 | 3 governed allowed warnings (`paste`/`bincode`/`chacha20`) — PSR-036C |
| Live CI (`origin/main` `0313af5`) | `gh run list` | — | `rust` ❌, `python` ❌, `repro` ❌, `parity` ✅, `snyk` ✅ — T-F1/T-F2/T-F5/T-F6 |

**§5 note (Rust scoped test run):** `cargo test -p prin-sim -p prin-train
-p prin-py --quiet` exited 0 (all test binaries `test result: ok`, 0 failed)
at `e4fb372` on this host. This covers the crates the WP-036C range added
first-party Rust to; the full `cargo test --workspace` (default + `strict-checks`)
for the whole unpushed range is CI-pending (T-F4) and last ran green on the
hosted `rust` legs at `0313af5`.

---

## 6. Audit Verdict and Sign-off

**Final Verdict:** **PASS-WITH-REMEDIATION**

**Rationale:** Zero D1 findings — no test asserts incorrect behavior, no
tolerance was weakened without governance, the parity corpus and reproducibility
guarantees hold, and the bandit findings are genuine `Low`s with pre-documented
rationale (they need bandit-native suppression, not a code change). Three D2
findings (T-F1 bandit gate red + two downstream CI enforcement steps inert;
T-F2 ~13 CI-failing `prinet`-dependent tests; T-F3 `wp001_baseline` gate red),
all mechanically remediable in a dedicated session. Five D3 findings, dominated
by **T-F4: the entire WP-036C cycle is unpushed and has never been through CI**
— which is exactly the condition a mid-phase testing/CI audit exists to catch
before the phase-close push. Two D4 findings (local/CI gate drift, PSR
verification-claim optimism).

The Phase 6 test suite itself is, on its merits, in strong shape: 2,729
passing tests on a clean run, an exemplary central governed-skip layer, zero
`xfail`, test-in-tandem compliance across the audited range, and independent
mathematical corroboration from EMA-006. The findings are concentrated in the
**CI gate machinery and the local↔CI equivalence contract**, not in test
correctness. `PASS-WITH-REMEDIATION` matches the sibling EMA-006 / EDA-001
mid-phase verdicts.

**Blocking recommendation:** the Phase 6 close push must not happen — and
WP-036E S1 must not begin — until T-F1, T-F2, T-F3, T-F5, and T-F6 are fixed
and `rust`/`python`/`parity`/`repro`/`snyk` are confirmed green on
`origin/main` (T-F4).

**Auditor Signature:** AI pair (Claude Sonnet 5)
**Date:** 2026-09-01

---

## 7. Remediation closure table (appended by the remediation session)

| ID | Resolution | Evidence |
|---|---|---|
| T-F1 | | |
| T-F2 | | |
| T-F3 | | |
| T-F4 | | |
| T-F5 | | |
| T-F6 | | |
| T-F7 | | |
| T-F8 | | |
| T-F9 | | |
| T-F10 | | |

---

## Appendix A: Phase 6 Test & CI Inventory (audit window)

| Category | Value | Notes |
|---|---|---|
| Python tests collected (fast gate) | ~2,969 | `+1,199` since EA-006 (~1,770) |
| Ported acceptance suite | 37 files / 1,670 `def test_` | WP-036B 13/498 + WP-036C 24/1,172 |
| Fast-gate result at `e4fb472` | 2,729 pass / 201 skip / 14 fail / 25 deselect | 410 s, `--basetemp=.pytest_basetemp` |
| `xfail` markers | 0 | conforms |
| Governed skips (`conftest.py`) | DV-031(A/B), amdt #41, M5 RNG, + 1 quarantine (T-F8) | one auditable hook |
| Rust tests (PSR-036C local) | ~1,564 pass / 0 fail / 1 ignored | CI-pending for WP-036C range (T-F4) |
| New first-party Rust (window) | ~2,010 lines | `oscillo_compat.rs`, `y4q1_stats.rs`, STE term, bands/attention |
| CI workflows | 7 (`rust`, `python`, `parity`, `repro`, `gpu`, `snyk`, `release`) | all present |
| `schedule:`d workflows | 0 | T-F7 (nightly full-suite obligation unmet) |
| Enforcing bench-regression gates | 0 | T-F7 |
| `origin/main` CI (latest push `0313af5`) | 2 green / 3 red | `parity`✅ `snyk`✅; `rust`❌ `python`❌ `repro`❌ |
| Unpushed commits (local `main` ahead) | 28 | WP-036C S1–S4 + EMA-006 + EDA-001 (T-F4) |
| New EMA claim ledgers in window | 2 (`prin-sim-phase6-stats`, `prin-train-phase6`) | EMA-006; CI-pending |
