# PRIN Executive Testing and CI Audit Report — Session 002 (ETCA-002)

**Date:** 2026-09-02
**Auditor:** AI pair (Claude Sonnet 5)
**Scope:** Executive Testing and CI Audit — post-push CI-failure audit of the
batched WP-036E + WP-036F range (Deferred-Validation closure work, Phase 6),
sessions `0144Q`–`0144X`. Triggered by the methodology's §1.1 condition 3
(**CI-health trigger**: `origin/main` CI is red on the most recent push and the
prior remediation's green state did not survive one work-package cycle) and
condition 4 (maintainer request for a dedicated testing/CI audit of the recent
failed GitHub Actions runs).
**Audit window:** `6343416..adbb1e3` — 17 commits, 2026-09-01 20:59 →
2026-09-02 13:17, sessions `0144Q`–`0144X` (WP-036E S1–S4 + WP-036F S1–S4).
`6343416` is the ETCA-001-remediation HEAD at which `origin/main` CI was last
fully green (2026-09-01 23:59, all of `rust`/`python`/`parity`/`repro`/`snyk`
`success`).
**Git Branch/State:** `main` @ `adbb1e3` (local == `origin/main`; clean working
tree at session start).
**Live CI state at session start (`gh run list`, latest `origin/main` push
`adbb1e3`):** `python` **failure** (the `lint` job's `mypy python/prin
--strict` step + all three `windows-latest` test-matrix legs), `rust`
**in progress** (>1 h — every hosted leg `success`; the Windows leg still
queued/running, DV-016 class), `parity` **success**, `repro` **success**,
`snyk` **success**, `gpu` **skipped** (no `[gpu]` tag on the commit).
`nightly` (schedule, 2026-09-02 05:12): **failure** (`full-suite` job;
`bench-regression` job `success`).
**Governing methodology:**
`DOCS/standards/Executive_Testing_and_CI_Audit_Governance_and_Methodology.md`
(established at ETCA-001 as Task 1; Project Plan amendment #42). Task 1 for this
session is *confirmation of the existing methodology* — no methodology change is
made here; governance **recommendations** for the maintainer/remediation
session are in §4.3.
**Prior session:** ETCA-001 + its remediation (2026-09-01, verdict `PASS`).
**Verdict:** **FAIL** (audit) → **PASS** (ETCA-002 remediation session,
2026-09-02, commits `bef851c`→`47d7ef3`→`9d4fd86`; `origin/main` HEAD
`9d4fd86` green on all six workflows incl. `gpu` — §7).

---

## 0. What this session did

ETCA-001 (2026-09-01) found that the entire WP-036C cycle had been declared
closed while unpushed and never through CI (finding T-F4), remediated it, drove
`origin/main` CI green at `6343416`, and added `nightly.yml` (T-F7) and a
`python.yml` `governance` job (T-F1). **That green state did not survive the
next work-package cycle.** Between `6343416` and the current HEAD there has been
exactly one push — `adbb1e3`, the WP-036F S4 commit — and it carries the whole
17-commit WP-036E + WP-036F range in one batch. That push is red: the `python`
workflow fails on `mypy --strict` and on 15 test instances (5 tests × 3 Windows
legs); the `gpu` workflow was skipped; `nightly` is red. WP-036E and WP-036F
were nonetheless both declared **closed**, PSR-036F was issued, the DirectML
half of **DV-006** was marked **CLOSED**, and Project Plan **amendment #13**
(the WP-005 DirectML deferral) was marked **discharged** — all with the closing
push red and its S4 documentation asserting "CI is green."

This session executed the ETCA audit across all eight dimensions (T1–T8),
reproducing every relevant gate command's real exit code, pulling the failed
`origin/main` and `nightly` run logs, and tracing each failure to root cause.
It:

1. Confirmed the methodology (no change; ETCA-002 is the second session of an
   established type).
2. Executed the T1–T8 audit against the audit window and the live CI state.
3. **Reports ten findings** — **one D1** (T-F1), **three D2** (T-F2, T-F3,
   T-F4), **four D3** (T-F5–T-F8), **two D4** (T-F9, T-F10) — and a remediation
   plan plus governance/methodology recommendations for a dedicated remediation
   session, as the task requires.
4. Documented and committed locally.

Consistent with methodology §5.3 and the ETCA-001 / EDA-001 precedent, this
session is **read-only with respect to first-party source and test code**:
every finding is planned, not fixed. This session's own writes are the new
report, the `SESSION_REGISTER.md` row, and the `CHANGELOG.md` entry.

---

## 1. Executive Summary Table

| Audit Dimension | Status | Summary & Key Observations |
|---|---|---|
| **T1: Test Suite Inventory & Health** | ⚠️ REMEDIATION | Local fast gate (`pytest -m "not slow and not gpu" --basetemp=.pytest_basetemp`, this host) is green **because the maintainer host has a real DirectML GPU and ORT 1.24.4**; the same suite on CI's hosted `windows-latest` fails 5 tests on every leg (T-F3). `cargo build --workspace` exit 0; `ruff check` / `ruff format --check` clean; **`mypy python/prin --strict` exit 0 locally, exit 1 in CI** (T-F2). No `xfail` (conforms). `nightly` full-suite red on a perf-ratio assertion not tracked by DV-032 (T-F5). |
| **T2: Test-in-Tandem & Coverage Compliance** | ✅ PASS (CI-pending) | Test-in-tandem holds across the window: WP-036E `0144Q1`–`0144Q3` and WP-036F `0144U` each commit source + tests together; WP036E-F3 raised changed-line coverage to 98.71 %, WP036F-F1 raised the two new tools to 100 %. Per-change coverage remains CI-authoritative via `codecov` (DV-033); that leg last uploaded at `6343416` (green) and has **not** run for this window because the `python` workflow's ubuntu legs pass but the codecov upload is gated on the full `test` job matrix — the Windows legs' failure does not block the ubuntu 3.12 upload, so codecov *did* receive this range. No finding. |
| **T3: Specialized Test Layers** | ✅ PASS | WP-036E adds `proptest` / kernel-equivalence coverage for the new `prin-kernels` device-`Handle` dispatch entry points and the on-device `f64` combine; `cargo test --features cuda` / `--features wgpu` carry them but run **only** in `gpu.yml` (T-F6). WP-036F introduces no numerical primitive (a graph-transform pass + two tools). float64 `gradcheck` bridges unchanged. Stochastic tests seed through `Seed`. No missing required layer for the touched scope. |
| **T4: Parity & Differential Testing** | ✅ PASS | `parity` workflow **`success`** on `adbb1e3` (6 m 18 s). No acceptance assertion weakened. WP-036F adds one governed deviation-register entry (`parity_report.rst` "WP-036F — DirectML controller-graph execution", CPU bit-identity + DirectML agreement `max_abs_diff 7.15e-7`) — but see T-F3: the "CPU bit-identity" claim is **host/ORT-build-specific** and does not reproduce on the hosted-runner ORT, which is itself a finding against the DV-006 evidence base. |
| **T5: Governed Skips, Flaky Tests & Quarantine** | ⚠️ REMEDIATION | The `tests/conftest.py` central skip layer remains exemplary (DV-031/DV-032, amendment #41, M5 RNG — every entry names its governing item). **But** three test classes rely on `@pytest.mark.skipif("DmlExecutionProvider" not in ort.get_available_providers())` which **does not fire** on a host where `onnxruntime-directml` is installed but no DirectML device exists — the guard tests build capability, not executability (T-F3). And `test_acceptance_y2q1.py::…::test_speed_vs_transformer` is a fourth host-timing flake of the DV-032 class with no register row (T-F5). |
| **T6: CI/CD Workflow Coverage & Gate Effectiveness** | ❌ FAIL | 8 workflows present. **`python` is red** on `origin/main`: `lint` fails at `mypy --strict` (3 unused `type: ignore`, T-F2), and all three `windows-latest` `test` legs fail 5 tests each (T-F3). The `governance` job (ETCA-001 T-F1 fix) **held** — it runs independently and is green. **`gpu` is opt-in** (`[gpu]` commit-message tag) and was skipped for the one push that closed a *GPU device-resident execution* work package (T-F6). **No branch protection on `main`** — CI is not an enforced merge gate; the red `adbb1e3` push landed unimpeded (T-F7). The self-hosted Windows `rust` leg is unbounded wall-clock (T-F8). |
| **T7: Benchmark Regression Gates & Reproducibility Pipeline** | ⚠️ REMEDIATION | `repro` workflow **`success`** on `adbb1e3`. `nightly.yml` `bench-regression` (ETCA-001 T-F7 remediation) **`success`** — the enforcing >10 % gate is live and passing. **But** `nightly.yml` `full-suite` is **red** (T-F5) and has been since it began running; a permanently-red nightly gate that no session dispositions is the same failure mode ETCA-001 T-F7 set out to fix, one layer up. |
| **T8: Test Evidence, Traceability & Local/CI Gate Equivalence** | ❌ FAIL | The WP-036F S2 audit's checklist item A9 records **"✅ (local substitute)"**; the `0144X` S4 session document asserts **"the S4 push carries the full WP-036F S1–S4 range and CI is green. WP-036F is closed"** — CI was never consulted and is in fact red (T-F4). Session memory and multiple `0144Q`–`0144X` session docs say commits are "not pushed" when they were pushed at `adbb1e3` (T-F9). `python.yml`'s `lint` job installs an unpinned, bespoke toolchain disjoint from `.[dev]`, so `mypy --strict` is a moving target run-to-run (T-F10). The amendment-#28 S4 exit criterion ("a fully green CI run over the whole batched range before the cycle is declared closed") was not met for **either** WP-036E or WP-036F. |

---

## 2. Detailed Findings across Audit Dimensions

### T1: Test Suite Inventory & Health

**Local default gate at `adbb1e3`** (`pytest tests/ -m "not slow and not gpu"
--basetemp=.pytest_basetemp`, 2026-09-02, this host — Windows 11 / Python 3.14 /
torch 2.11.0+cu128 / onnxruntime 1.24.4 with `DmlExecutionProvider`
registered **and a real DirectML adapter present**):

- Targeted re-run of the CI-failing set —
  `pytest tests/test_wp036f_reexport.py tests/test_daemon_controller.py::TestCrossProviderAgreement`
  → **34 passed in 4.21 s**.
- `cargo build --workspace -q` → exit 0.
- `ruff check python/ tests/ benchmarks/ tools/` → `All checks passed!`;
  `ruff format --check …` → `241 files already formatted`.
- **`mypy python/prin --strict`** → `Success: no issues found in 62 source
  files` (**exit 0**) — CI reports **exit 1** (§T2/T-F2).
- No `xfail` anywhere in `tests/` (grep-verified) — conforms.

**The local gate is green only because of the maintainer host's hardware and
pinned ORT.** On CI's hosted `windows-latest` the same suite fails 5 tests on
every Python leg (3.11 / 3.12 / 3.13):

| Test | CI failure | Root cause |
|---|---|---|
| `test_wp036f_reexport.py::TestDirectMLExecution::test_pre_transform_graph_is_rejected_by_directml` | `Failed: DID NOT RAISE Exception` | `@pytest.mark.skipif("DmlExecutionProvider" not in ort.get_available_providers())` does not fire — `onnxruntime-directml` registers the provider even with no device; `ort.InferenceSession(pristine, providers=["DmlExecutionProvider"])` silently falls back to CPU instead of raising `InvalidGraph`. **T-F3** |
| `test_wp036f_reexport.py::TestDirectMLExecution::test_directml_executes_the_reexported_graph` | `assert 'CPUExecutionProvider' == 'DmlExecutionProvider'` | same faulty guard; session's active provider is CPU. **T-F3** |
| `test_wp036f_reexport.py::TestProviderLatencyTool::test_build_report_records_the_acceptance_evidence` | `assert False is True` on `report["pre_transform_differential"]["bit_identical"]` | **no guard**; the pre/post-transform CPU inference is *not* byte-identical on the hosted-runner ORT build (the zero-bias `Gemm` `+ C` term is folded by `ORT_ENABLE_ALL` on some builds, executed on others). **T-F3** |
| `test_wp036f_reexport.py::TestProviderLatencyTool::test_main_writes_the_evidence_json` | `assert 1 == 0` | **no guard**; `wp036f_provider_latency.main()` returns 1 because DirectML is "registered" but does not execute. **T-F3** |
| `test_daemon_controller.py::TestCrossProviderAgreement::test_directml_executes_the_reexported_graph` | `assert 'DmlExecutionProvider' in ['CPUExecutionProvider']` | same faulty `skipif` on `ort.get_available_providers()`. **T-F3** |

`nightly.yml` `full-suite` (schedule, 2026-09-02 05:12) — **red**:
`test_acceptance_y2q1.py::TestDiscreteDeltaThetaGamma::test_speed_vs_transformer`
→ `AssertionError: DiscreteDTG is 5.66× slower than Transformer (limit: 5×)`
(`@pytest.mark.slow`, hard `assert ratio <= 5.0` on a wall-clock forward-pass
ratio on the shared ubuntu runner). **T-F5.**

### T2: Test-in-Tandem & Coverage Compliance

Test-in-tandem holds across the window (`0144Q1`/`0144Q2`/`0144Q3` and `0144U`
each add source + tests in one commit; WP036E-F3 and WP036F-F1 raised changed
coverage above the floor at S3). No source-without-tests commit in
`6343416..adbb1e3`.

Per-change coverage stays CI-authoritative (DV-033). The `python.yml` `test`
matrix has `fail-fast: false`, so the ubuntu 3.12 leg (which does the
`codecov/codecov-action` upload) completed and uploaded despite the Windows
legs failing — this window *was* measured by codecov. **No finding** at T2;
the coverage gap is the pre-existing DV-033, unchanged.

### T3: Specialized Test Layers

WP-036E's new `prin-kernels` device-`Handle` dispatch entry points and its
CUDA-only `order_param_finalize_f64` `#[cube(launch)]` kernel carry
kernel-equivalence and `proptest` coverage in-tree, and the WP-036E S2 audit
(`b66533c`, verdict **FAIL** — then remediated at S3, delta re-audit CLEAN)
independently exercised them. **But those tests execute only under
`cargo test --workspace --features cuda` / `--features wgpu`, which run
exclusively in `gpu.yml`** — skipped for this push (T-F6). So WP-036E's
signature deliverable (device-resident GPU execution) closed with **no CI
exercise of its GPU path at all** for the closing range.

WP-036F introduces no numerical primitive — a graph-transform pass
(`tools/wp036f_reexport_controller.py`), an evidence tool
(`tools/wp036f_provider_latency.py`), tests, and docs. float64 `gradcheck`
bridges and the `Seed`-seeded stochastic tests are unchanged. **No missing
required layer** for the touched scope.

### T4: Parity & Differential Testing

`parity` workflow **`success`** on `adbb1e3` (6 m 18 s). The golden corpus is
current; hypothesis fuzzing intact; no acceptance assertion weakened (the
WP-036F change is confined to graph transform + tools + tests + docs, confirmed
by the WP-036F S2 audit's clean-diff finding).

WP-036F adds one `parity_report.rst` deviation-register entry. Its stated basis
— *"bit-identical to the pristine PRINet 3.0 graph on `CPUExecutionProvider`
over the 48-case differential set"* — is asserted by
`test_wp036f_reexport.py::TestProviderLatencyTool` via
`_pre_transform_check(...)["bit_identical"]`, and **that assertion fails on the
hosted-runner ORT build** (§T1). The parity-corpus differential suite itself is
unaffected (it does not touch the controller graph), so this is not a
parity-suite regression — but it is a defect in the DV-006 evidence base:
"bit-identical on CPU" is portable only under a specific ORT build/optimisation
level. Folded into **T-F3**.

### T5: Governed Skips, Flaky Tests & Quarantine

The `tests/conftest.py` `pytest_collection_modifyitems` layer remains a model
implementation — one auditable hook, every skipped node mapped to a named
governing item (DV-031(A/B), DV-032, amendment #41, the M5 RNG disposition),
ported test bodies byte-unchanged.

**Finding T-F3 (D2), skip-guard dimension:** three test classes —
`test_wp036f_reexport.py::TestDirectMLExecution`,
`test_daemon_controller.py::TestCrossProviderAgreement::test_directml_executes_the_reexported_graph`,
and (implicitly, by *lacking* a guard) `TestProviderLatencyTool` — depend on
`"DmlExecutionProvider" not in ort.get_available_providers()` as a skip
predicate. `ort.get_available_providers()` returns every provider **compiled
into the wheel**, not every provider that can **execute on this host**. On
GitHub-hosted `windows-latest` (`onnxruntime-directml` installed, no
DirectML-capable adapter) the predicate is `False`, the guard does not skip,
and the tests run and hard-fail. Testing Standards §4 (tests must be
environment-insensitive or explicitly guarded) is violated. This is the
**recurrence of ETCA-001 finding T-F2** (environment-dependent tests reaching
the default CI gate unguarded) — one work package after that finding's
remediation, in a directly analogous form.

**Finding T-F5 (D3):**
`test_acceptance_y2q1.py::TestDiscreteDeltaThetaGamma::test_speed_vs_transformer`
is a wall-clock perf-ratio assertion (`assert ratio <= 5.0`) of exactly the
DV-032 class. DV-032 enumerates two such tests; this is an untracked third
(`test_speed_vs_transformer`) — plus DV-032's own note lists a second
(`test_deterministic_seed`), so the register is already known to under-count
this class. It is `@pytest.mark.slow`, so it does not touch the fast gate, but
it turns `nightly.yml` `full-suite` permanently red.

### T6: CI/CD Workflow Coverage & Gate Effectiveness

All 8 workflows (`rust`, `python`, `parity`, `repro`, `gpu`, `snyk`,
`release`, `nightly`) exist and are triggered as the
`.github/workflows/README.md` inventory describes.

**`python` workflow — RED on `origin/main` (`adbb1e3`):**

| Job | Step | CI result | Finding |
|---|---|---:|---|
| `lint` | `mypy python/prin --strict` | **exit 1** — 3 unused `type: ignore[no-untyped-call]` (`nn/_bridge.py:146`, `_torch_compat.py:430`, `_torch_compat.py:1088`) | **T-F2** (D2) |
| `lint` | `ruff` / `ruff format` / `interrogate` / `bandit` | pass | — (bandit `# nosec` from ETCA-001 T-F1 held) |
| `governance` | deviation-ledger + DV-register gates | **pass** | ✅ ETCA-001 T-F1 fix **held** — the job is independent of `lint` and ran green |
| `test` (ubuntu ×3) | `pytest -m "not slow and not gpu"` | pass | — (ETCA-001 T-F5 disk-reclaim + CPU-torch held) |
| `test` (windows ×3) | `pytest -m "not slow and not gpu"` | **exit 1** — 5 failures/leg | **T-F3** (D2) |
| `codecov` | upload (ubuntu 3.12) | pass | — |

**`gpu` workflow — SKIPPED.** `gpu.yml` triggers only on
`contains(github.event.head_commit.message, '[gpu]')`. `adbb1e3`'s message is
`docs(WP-036F S4 0144X): close DirectML half of DV-006; issue PSR-036F` — no
tag — so the workflow was skipped (1 s). Consequence: the push that closed
**WP-036E (GPU device-resident execution)** and **WP-036F (DirectML
controller-graph execution)** ran **zero** GPU CI — no `cargo test --features
cuda/wgpu`, no 12 `@pytest.mark.gpu` acceptance tests, no kernel-perf-regression
bench, and — critically — **no run of the DirectML/provider tests on
`PRIN-GPU-Runner`, which has a real GPU + DirectML and on which they would pass
and emit the provider/latency data DV-006's re-audit gate names**. **T-F6**
(D3). This is the structural cause of "GPU tests are skipped and we have no
data": the opt-in tag is forgotten on exactly the pushes that most need it.

**No branch protection on `main`.** `gh api
repos/Symbo-gif/PRIN/branches/main/protection` → `404 "Branch protection has
been disabled on this repository."` CLAUDE.md and Coding Standards §6 assert
"CI is the authoritative merge gate"; methodology T6 requires "branch-protection
required-check sets match the workflow set." There is **no required-check set at
all**, and no PR flow — commits are pushed directly to `main`. The red
`adbb1e3` push landed with nothing to stop it. **T-F7** (D3). This is the
single highest-leverage structural enabler of the recurring red-push pattern.

**`rust` self-hosted Windows leg** — `test (windows-latest, windows-latest)`
still `in_progress` >1 h after every hosted `rust` leg (clippy, strict, fmt,
docs, bench-smoke, audit, ubuntu, macOS) went green; historical `rust` runs on
the WP-036* pushes show repeated `cancelled` (superseded). DV-016 class;
ETCA-001 T-F6 moved the *python* Windows leg to hosted but the *rust* Windows
leg was left on the self-hosted runner. Not a failure this push, but it makes
"is CI green?" slow to answer — which is part of why sessions close before
confirming (T-F4). **T-F8** (D3).

### T7: Benchmark Regression Gates & Reproducibility Pipeline

- `repro` workflow **`success`** on `adbb1e3` (5 m 45 s) — `tools/reproduce.py
  --verify-manifest` + `tests/test_reproduce.py` (ETCA-001 T-F5 remediation
  held).
- `nightly.yml` `bench-regression` **`success`** (39 m 26 s) — the enforcing
  criterion + `pytest-benchmark` >10 % gate ETCA-001 T-F7 added is live and
  passing against its rolling `actions/cache` baseline.
- `nightly.yml` `full-suite` **`failure`** (T-F5). The `full-suite` job has no
  `|| true`, no quarantine hook of its own, and its failure is not surfaced in
  any PSR or S4 verification block. A scheduled full-suite gate that is red on
  every run and that no cadence step dispositions is inert in the same way
  ETCA-001 T-F7 found the *absent* nightly gate inert.

### T8: Test Evidence, Traceability & Local/CI Gate Equivalence

**False CI-verification claims (T-F4, D2):**

- `DOCS/audits/036f-wp036f-audit.md` §"CI status (A9)": `✅ (local substitute)`
  — "Local gate fully reproduced this session." §3.7: "green apart from the
  changed-code coverage." Amendment #28 permits a local substitute **at S2/S3**
  (nothing is pushed yet), so the S2 audit's phrasing is within the letter of
  the rule; the failure is that the substitute was never upgraded to a real CI
  check at S4.
- `DOCS/sessions/phase-6/0144X-wp036f-s4-directml-controller-graph-execution.md`
  lines 88–89: *"the S4 push carries the full WP-036F S1–S4 range and CI is
  green. WP-036F is closed."* The push happened (`adbb1e3` triggered CI); CI is
  **red**; the session closed anyway. PSR-036F was issued, DV-006's DirectML
  half was marked **CLOSED**, and amendment #13 was marked **discharged**, all
  over the red.
- Amendment #28: *"S4's exit criteria now explicitly require the push itself
  and a fully green CI run over the whole batched range before the cycle is
  declared closed."* Not met for WP-036E (never pushed as its own cycle) or
  WP-036F (pushed red).

**Local ≡ CI drift (T-F2 / T-F10):** `python.yml`'s `lint` job runs
`pip install ruff mypy "interrogate>=1.7" "bandit[toml]>=1.7" hypothesis torch`
— **unpinned** `mypy`, **unpinned** `torch` from the default (CUDA) PyPI index,
and it does **not** install `.[dev]`. The maintainer host has `mypy 2.3.0` /
`torch 2.11.0+cu128`, under which the three `# type: ignore[no-untyped-call]`
comments on `torch.autograd.Function.apply()` call sites are **required**; the
CI environment resolves a torch whose stubs type `Function.apply`, making the
same comments **unused**, which `--strict` (`warn_unused_ignores`) rejects.
Neither environment is wrong; the gate is simply non-deterministic because its
toolchain floats. `pyproject.toml` pins only floors (`torch>=2.0`,
`mypy>=1.11`). **T-F10** (D4) is the hygiene half; **T-F2** (D2) is the current
red.

**Documentation/state drift (T-F9, D4):** session memory and the `0144Q`–
`0144X` session docs describe commits as "not pushed" / "batched push is a
maintainer action" when the range is in fact on `origin/main` at `adbb1e3`;
CHANGELOG `[Unreleased]` and PSR-036F narrate WP-036E/WP-036F as closed without
recording the actual `origin/main` CI conclusion.

---

## 3. Discovered Deviations and Findings Table

| ID | Severity | Dim. | Location / Subsystem | Issue | Violated Clause | Status |
|---|---|---|---|---|---|---|
| **T-F1** | **D1** | T8 / T6 | `origin/main` @ `adbb1e3`; `DOCS/sessions/phase-6/0144T-*`, `0144X-*`; `DOCS/reports/036f-project-state.md`; `DEFERRED_VALIDATION_REGISTER.md` DV-006; Project Plan amendment #13 | WP-036E S4 (`b7d3ee7`) was never pushed as its own cycle-closing push; WP-036F S4 (`adbb1e3`) pushed the batched 17-commit WP-036E+WP-036F range and CI is **red** (`python` `lint` + all Windows `test` legs; `gpu` skipped; `nightly` red). Both WPs were nonetheless declared **closed**, **PSR-036F** issued, the **DV-006 DirectML half** marked **CLOSED**, and **amendment #13** marked **discharged** — with the closing push red and its S4 doc asserting "CI is green." The Phase 6 → Phase 7 Deferred-Validation-closure ledger, on which Phase 7 pre-registration depends (amendment #38), now records a closure whose own mandated exit gate is unmet and misreported. | Development Workflow §3 + amendment #28 ("a fully green CI run over the whole batched range before the cycle is declared closed"; per-WP S4 push); Development Workflow §1.4 (evidence-based, never by recollection); methodology §2 principle 1/3, §4 principle 5 | **OPEN** — recommend a dedicated remediation session; WP-036F is **not** closed and WP-036G S1 (`0144Y`) **must not begin** until T-F1–T-F4 are resolved and `origin/main` CI (incl. a `[gpu]` run) is confirmed green |
| **T-F2** | **D2** | T6 / T8 | `.github/workflows/python.yml` `lint`; `python/prin/nn/_bridge.py:146`; `python/prin/_torch_compat.py:430`, `:1088` | `mypy python/prin --strict` **exits 1** in CI on 3 unused `type: ignore[no-untyped-call]` at `torch.autograd.Function.apply()` sites; **exit 0** locally (`mypy 2.3.0` / `torch 2.11.0+cu128`). The `lint` job installs unpinned `mypy` + unpinned CUDA `torch` (not `.[dev]`), so the strict-mode `warn_unused_ignores` verdict flips with the resolved torch stubs. The 3 sites are WP-036E-era code, so WP-036F S3's "mypy 3→0 on both tools" fix (correctly scoped to the changed tools) never touched them, and every local session's `mypy python/prin --strict` was green. | Coding Standards §5/§6 (lint gate must pass); methodology §2 principle 3 ("local gate ≡ CI gate"); recurrence of ETCA-001 T-F10 / EA-005 E-F1 | **OPEN** — recommend remediation |
| **T-F3** | **D2** | T1 / T3 / T5 | `tests/test_wp036f_reexport.py` (`TestDirectMLExecution`, `TestProviderLatencyTool`); `tests/test_daemon_controller.py::TestCrossProviderAgreement`; `tools/wp036f_provider_latency.py` (`_pre_transform_check` `bit_identical`) | 5 tests hard-fail every `python.yml` `windows-latest` leg (15 instances/push). `@pytest.mark.skipif("DmlExecutionProvider" not in ort.get_available_providers())` tests *build capability*, not *executability* — it does not fire on a host with `onnxruntime-directml` installed and no DirectML adapter (hosted `windows-latest`). `TestProviderLatencyTool` has **no** guard and asserts host/ORT-build-specific behaviour (`bit_identical is True`, `main() == 0`). All pass on the maintainer host (real DirectML GPU). Recurrence of ETCA-001 T-F2. Sub-point: the "CPU bit-identical" basis of the DV-006 `parity_report.rst` entry is not portable across ORT builds. | Testing Standards §4 (environment-insensitive or explicitly guarded); §3 (a tolerance annotation must be reproducible); recurrence of ETCA-001 T-F2 | **OPEN** — recommend remediation |
| **T-F4** | **D2** | T8 | `DOCS/audits/036f-wp036f-audit.md` §A9/§3.7; `DOCS/sessions/phase-6/0144X-*` §Exit; PSR-036F §CI | The WP-036F audit records CI status as "✅ (local substitute)" and the S4 session doc asserts "CI is green. WP-036F is closed" — CI was never checked and is red. No `0144Q`–`0144X` artefact records the live `origin/main` CI conclusion. The push/CI-cadence S4 exit criterion was declared satisfied without evidence. | Development Workflow §1.4; §3 S4 exit criteria + amendment #28; Documentation Standards §7; methodology §2 principle 1 | **OPEN** — recommend remediation (and a machine-checked S4 CI-green gate, §4.3 G2) |
| **T-F5** | **D3** | T5 / T7 | `.github/workflows/nightly.yml` `full-suite`; `tests/test_acceptance_y2q1.py::TestDiscreteDeltaThetaGamma::test_speed_vs_transformer`; `DEFERRED_VALIDATION_REGISTER.md` DV-032 | `nightly` `full-suite` is red (since it began running) on a `@pytest.mark.slow` wall-clock perf-ratio assertion (`assert ratio <= 5.0`, measured 5.66×) — a fourth test of the DV-032 host-timing-flake class with no register row. A permanently-red scheduled gate that no cadence step dispositions. | Testing Standards §1.4 (quarantine requires a linked item + approval); §4; methodology T7 (a nightly obligation met by a permanently-red job is not met) | **OPEN** — fold into DV-032 with a dated disposition; convert to a seeded / `pytest-benchmark` bound |
| **T-F6** | **D3** | T3 / T6 | `.github/workflows/gpu.yml` (`if: contains(…, '[gpu]')`); S4 checklist (Development Workflow §3) | `gpu.yml` is opt-in via a `[gpu]` commit-message tag. `adbb1e3` — the push closing a *GPU device-resident execution* WP and a *DirectML* WP — carried no tag, so **all** GPU CI was skipped: `cargo test --features cuda/wgpu`, 12 `@pytest.mark.gpu` tests, the kernel-perf bench, and the DirectML tests on the real-GPU `PRIN-GPU-Runner`. WP-036E closed with no CI exercise of its deliverable; DV-006's provider/latency data was not regenerated in CI. | Testing Standards §2 (GPU integration layer must run for touched GPU scope); Plan §6 Phase 6 exit ("all CI green"); the maintainer's explicit requirement that GPU tests never be skipped | **OPEN** — make `gpu.yml` run on every `main` push (or mandate the `[gpu]` tag on any GPU-touching S4 push) + route DirectML tests to a GPU-runner marker; §4.3 G4 |
| **T-F7** | **D3** | T6 | Repository settings — `main` branch protection | Branch protection is **disabled** on the repo; there is no required-status-check set and no PR flow. Red pushes to `main` (e.g. `adbb1e3`) are unimpeded. "CI is the authoritative merge gate" (CLAUDE.md) is unenforced. | Methodology T6 ("branch-protection required-check sets match the workflow set"); CLAUDE.md / Coding Standards §6 | **OPEN** — enable branch protection with the full workflow set as required checks + `enforce_admins`, or a mandatory pre-push local-gate hook; §4.3 G3. Record as a DV item if the maintainer elects to keep direct-push for velocity |
| **T-F8** | **D3** | T6 | `.github/workflows/rust.yml` Windows `test` leg; `PRIN-GPU-Runner`; DV-016 | The self-hosted Windows `rust` leg runs unbounded wall-clock (>1 h on `adbb1e3`; repeated `cancelled` on superseded pushes) after every hosted `rust` leg is green. Makes the "is CI green?" answer slow, feeding T-F4. ETCA-001 T-F6 hosted the *python* Windows leg but not the *rust* one. | Development Workflow §3 S4 exit (CI green, in bounded time); DV-016 | **OPEN** — host the `rust` Windows leg (accept DV-016 slowness on a bounded `timeout-minutes`) or add a queue-wait timeout + fail-fast |
| **T-F9** | **D4** | T8 | Session memory; `DOCS/sessions/phase-6/0144Q`–`0144X`; `CHANGELOG.md`; `DOCS/reports/036f-project-state.md` | Artefacts describe the WP-036E/WP-036F commits as "not pushed" / "batched push is a maintainer action" when the range is on `origin/main` at `adbb1e3`; no artefact records the actual CI conclusion. | Documentation Standards §7 (artefact-trail accuracy) | **OPEN** — correct in the remediation session's doc-alignment step |
| **T-F10** | **D4** | T8 / T6 | `.github/workflows/python.yml` `lint` (`pip install … mypy … torch`); `pyproject.toml` (floors only) | The `lint` job's toolchain is unpinned and disjoint from `.[dev]`, so `mypy --strict` / `ruff` / `bandit` results drift run-to-run with upstream releases. Root cause shared with T-F2; recorded separately as the durable hygiene fix. | Methodology §2 principle 3; Benchmarking & Reproducibility Standards (pinned toolchains) | **OPEN** — install `.[dev]` or a `constraints.txt` in `lint`; add `# type: ignore[no-untyped-call, unused-ignore]` at the torch `.apply()` sites |

---

## 4. Remediation Plan

### 4.1 Immediate Remediation (not executed — methodology §5.3: ETCA is read-only w.r.t. first-party source/test code)

The single D1 (T-F1) and all three D2 (T-F2, T-F3, T-F4) require
source/test-code, workflow, and repository-settings changes plus a CI push
cycle — out of scope for an audit session. They are passed forward to a
dedicated **ETCA-002 remediation session** (EDA-001 / ETCA-001 precedent). This
session's own writes are limited to this report, the `SESSION_REGISTER.md` row,
and the `CHANGELOG.md` entry.

### 4.2 Pass-Forward Items (dedicated ETCA-002 remediation session — ordered by dependency)

1. **T-F2 (D2, mypy red).** Add `# type: ignore[no-untyped-call, unused-ignore]`
   at `python/prin/nn/_bridge.py:146`, `python/prin/_torch_compat.py:430`,
   `python/prin/_torch_compat.py:1088` (mypy accepts a redundant
   `unused-ignore` code, so the comment is correct under *both* torch stub
   versions). **And** pin the `python.yml` `lint` toolchain — install
   `pip install -e ".[dev]"` (or a committed `constraints.txt`) so the gate is
   deterministic (T-F10). Verify: `mypy python/prin --strict` exit 0 both
   locally and on a CI re-run.

2. **T-F3 (D2, DirectML tests red in CI).** Replace the
   `"DmlExecutionProvider" not in ort.get_available_providers()` guards with an
   *executability* probe — a shared `tests/_env.py::directml_executes()` that
   builds a 1-node session on `["DmlExecutionProvider"]` and checks
   `session.get_providers()[0] == "DmlExecutionProvider"` — and add the same
   guard (or `@pytest.mark.gpu` / a new `@pytest.mark.directml`) to
   `TestProviderLatencyTool`. Make `wp036f_provider_latency._pre_transform_check`
   compare with a tolerance (`np.allclose(..., rtol=1e-5, atol=1e-6)`), not a
   `uint32` byte view, and record the tolerance in the `parity_report.rst`
   entry — "bit-identical on CPU" is not portable across ORT builds. Route the
   DirectML acceptance tests to run on `PRIN-GPU-Runner` (T-F6 / G4) so they
   are **verified on a real device**, not skipped. Verify: on a host without a
   DirectML adapter the tests **skip** (not fail); on `PRIN-GPU-Runner` they
   **pass** and emit the provider/latency JSON.

3. **T-F5 (D3, nightly red).** Sweep `tests/` for `assert <ratio> <= <k>` /
   wall-clock timing assertions; fold `test_speed_vs_transformer` (and any
   siblings found) into **DV-032** with a dated maintainer disposition; convert
   to a seeded frame-count / `pytest-benchmark` bound or widen to a defensible
   ratio. Verify: `nightly.yml` `full-suite` green on a `workflow_dispatch` run.

4. **T-F6 + governance G4 (D3, GPU tests skipped).** Change `gpu.yml` to run
   unconditionally on `push: branches: [main]` (the self-hosted runner is idle
   otherwise) — **or**, if opt-in is retained for cost, add an S4-checklist
   gate: any S4 push whose WP touched `crates/prin-kernels/**`,
   `crates/prin-sim/**` GPU engines, `crates/prin-py/src/bindings/gpu.rs`,
   `python/prin/daemon/**`, or `models/**` **must** carry `[gpu]`, verified by a
   pre-push hook. Add a `workflow_dispatch` + nightly `schedule` GPU leg so the
   data is collected on quiet days. Verify: a GPU run appears green on the next
   Phase-6 push.

5. **T-F7 (D3, no branch protection).** Enable branch protection on `main` with
   required checks `{python, rust, parity, repro, snyk}` (+ `gpu` once it runs
   on every push) and `enforce_admins: true`. If the maintainer keeps
   direct-push for a single-maintainer repo, install a mandatory pre-push hook
   running the `AGENTS.md` canonical local gate and record the decision as a
   dated DV item. Verify: a deliberately-red push is rejected (or the hook
   blocks it).

6. **T-F1 (D1) — closure.** Once 1–5 land: push the fixes, confirm
   `origin/main` CI green across `python`/`rust`/`parity`/`repro`/`snyk` **and
   a `[gpu]` run**, then update PSR-036F, the DV-006 row, and the amendment-#13
   discharge note to cite the **real** green CI run (or, if the maintainer
   accepts that the DirectML capability is already proven on `PRIN-GPU-Runner`,
   re-affirm the closures explicitly with that evidence and a dated note that
   the hosted-runner failures are guard defects, not capability defects).
   Append the §7 closure table. Only then may WP-036G S1 (`0144Y`) begin.

7. **T-F8 (D3), T-F9 (D4), T-F10 (D4)** — as described in §3; T-F8 may be
   carried with a dated disposition if hosting the `rust` Windows leg is
   deferred to a CI-topology WP.

### 4.3 Governance & Methodology Recommendations (for the maintainer / a plan amendment)

The task asks specifically for changes that "mitigate and prevent the
repetitive push CI failures." ETCA-001 found the *first* instance (T-F4);
ETCA-002 finds it recurred one cycle later, worse, despite that remediation —
because the remediation fixed the *symptoms* (the specific red gates) but added
no mechanism that forces a session to **confirm green after it pushes**. The
recommendations below are ordered by leverage.

- **G1 — Per-WP S4 push is mandatory and blocking; no multi-WP batching without
  an amendment.** Amend Development Workflow §3 / restate amendment #28: a WP's
  S4 session **must** push its own cycle range, and the **next** WP's S1
  **must not begin** until `gh run list --branch main` shows every
  non-opt-in workflow green for that push. Batching two or more WPs into one
  "phase-close" push (as WP-036E + WP-036F were) is prohibited absent an
  explicit dated plan amendment that names the batch and assigns the
  green-CI-confirmation step to a specific session. The "local substitute"
  (amendment #28) is an S2/S3 device only and **expires at S4**.

- **G2 — Machine-checked S4 CI-green gate.** Add `tools/check_ci_green.py`
  (wrapping `gh run list --branch main --json headSha,workflowName,conclusion`)
  that the S4 session **must** run against its own push SHA and paste verbatim
  into the PSR verification block. A WP **cannot** be declared CLOSED, a PSR
  issued, or a DV item / plan amendment discharged while it returns non-green
  or "no run found." This converts T-F4's "recollected green" from a
  process norm into an impossible state. Add the same check to the ETCA and EA
  S-checklists.

- **G3 — Branch protection = the merge gate.** Enable it (G-item under §4.2.5).
  Even for a single maintainer this makes "red push, close anyway" impossible
  rather than merely discouraged. This is the one change that would have
  stopped both T-F4 and T-F1 at the door.

- **G4 — GPU tests run on every `main` push, not opt-in.** The `[gpu]`-tag
  convention structurally guarantees the tests are skipped on the pushes that
  forget the tag — which, empirically, includes the push that closed two GPU
  work packages. Make `gpu.yml` unconditional on `push: main` (idle
  self-hosted runner, no cost argument) and add a `schedule:` leg. Route
  hardware/runtime-dependent tests (DirectML, CUDA-device, VitisAI-when-present)
  to markers that **skip cleanly on incapable hosts and run on the capable
  runner** — never a guard that silently no-ops into a false pass/fail on a
  hosted runner. Add to Testing Standards §1.4 / §2: "a `skipif` guarding a
  hardware/runtime feature must probe *executability* (attempt the operation),
  not *registration* (`… in get_available_providers()` / `is_available()` at
  import), and must be verified to actually fire on a host lacking the feature."

- **G5 — Nightly red is dispositioned like a push red.** Add to the S4 and
  ETCA cadence: check the latest `nightly.yml` conclusion; any failure is
  fixed, or given a dated DV row, before the next WP closes. A scheduled gate
  that is always red is worth less than no gate (it trains reviewers to ignore
  it).

- **G6 — Pin every CI gate's toolchain.** No CI job may `pip install` an
  unpinned tool that gates a merge. `lint` installs `.[dev]` or a
  `constraints.txt`; `mypy`, `ruff`, `bandit`, `torch` versions are pinned and
  bumped deliberately. Add to Coding Standards §5.

- **G7 — ETCA auto-triggers on the CI-health condition.** Methodology §1.1
  condition 3 ("`origin/main` red for >1 push, or a hotfix workflow change owes
  a retro-audit") should be an *automatic* trigger, not a maintainer-discretion
  one, and — given the density of CI-topology change in the WP-036 family — one
  ETCA per WP-family close (036E/F/G), not only per phase. Record in
  methodology §5.5.

- **G8 — "Recurrence" is a first-class audit check.** When an audit finding is
  a recurrence of a prior finding whose remediation was signed off (T-F3 ⟵
  ETCA-001 T-F2; T-F2 ⟵ ETCA-001 T-F10 ⟵ EA-005 E-F1), the remediation session
  must add a *regression guard* for the class, not just fix the instance — e.g.
  a CI job that greps for `get_available_providers()` / `is_available()` in a
  `skipif` predicate, or a scheduled "local-vs-CI mypy" diff. Add to
  methodology §4.

---

## 5. Verification Suite Results (Task 3 — evidence, not a session gate)

This audit session is read-only; the commands below are evidence for the
findings.

| Verification Step | Command | Result (real exit code) | Notes / Evidence |
|---|---|---|---|
| Rust build | `cargo build --workspace -q` | **0** | clean at `adbb1e3` |
| Rust format | `ruff`/`cargo fmt` n/a here | — | `rust` workflow hosted legs all `success` on `adbb1e3` |
| Ruff check | `ruff check python/ tests/ benchmarks/ tools/` | **0** | `All checks passed!` |
| Ruff format | `ruff format --check …` | **0** | 241 files formatted |
| **mypy (local)** | `mypy python/prin --strict` | **0** | `Success: no issues found in 62 source files` |
| **mypy (CI, `adbb1e3`)** | `mypy python/prin --strict` (lint job) | **1** | 3 unused `type: ignore[no-untyped-call]` — **T-F2** |
| Python fast gate (local, minus `test_wp036f_reexport.py`) | `pytest tests/ -m "not slow and not gpu" --basetemp=.pytest_basetemp --ignore=tests/test_wp036f_reexport.py` | **0** | 2744 passed, 202 skipped, 30 deselected, **0 failed** (311 s) — the maintainer host masks all 5 CI failures |
| DirectML/provider tests (local) | `pytest tests/test_wp036f_reexport.py tests/test_daemon_controller.py::TestCrossProviderAgreement --basetemp=.pytest_basetemp` | **0** | 34 passed (maintainer host has a DirectML adapter) |
| **DirectML/provider tests (CI, `adbb1e3`)** | same, `windows-latest` ×3 | **1** | 5 failed/leg — **T-F3** |
| Live CI — `python` | `gh run view 33654648030` | **failure** | `lint` (mypy) + windows `test` ×3 — T-F2, T-F3 |
| Live CI — `rust` | `gh run view 33654648160` | **in progress** | every hosted leg `success`; Windows leg >1 h — T-F8 |
| Live CI — `parity` | `gh run list` | **success** | 6 m 18 s |
| Live CI — `repro` | `gh run list` | **success** | 5 m 45 s |
| Live CI — `snyk` | `gh run list` | **success** | 41 s |
| Live CI — `gpu` | `gh run list` | **skipped** | no `[gpu]` tag — **T-F6** |
| Live CI — `nightly` (2026-09-02) | `gh run view 33593747871` | **failure** | `full-suite` red (`test_speed_vs_transformer` 5.66×); `bench-regression` `success` — **T-F5** |
| Branch protection | `gh api repos/Symbo-gif/PRIN/branches/main/protection` | **404** | "Branch protection has been disabled" — **T-F7** |
| Push cadence | `gh run list` since `6343416` | 1 push (`adbb1e3`) for 2 WPs / 17 commits | amendment #28 per-WP S4 push not honoured — **T-F1** |
| Governance job (ETCA-001 T-F1 fix) | `python.yml` `governance` job @ `adbb1e3` | **success** | deviation-ledger + DV-register gates ran independently — fix **held** |

---

## 6. Audit Verdict and Sign-off

**Final Verdict (audit session):** **FAIL** →
**PASS after remediation** (ETCA-002 remediation session, 2026-09-02) — all
ten findings `FIXED`, `DISPOSITIONED`, or superseded; see the §7 closure table
and `tools/check_ci_green.py` output for the green `origin/main` SHA. The
blocking recommendation below is discharged: T-F1–T-F4 are fixed, `origin/main`
CI (including a `gpu` run on `PRIN-GPU-Runner`) is green, and Plan amendment #45
adopts G1–G3/G6 (per-WP blocking push, machine-checked S4 CI-green gate, `main`
branch ruleset, pinned toolchains) plus G4/G5/G7/G8.

**Rationale (as found at audit):** One **D1** finding is open. WP-036E and WP-036F were both
declared closed — with PSR-036F issued, the DV-006 DirectML half marked CLOSED,
and Project Plan amendment #13 marked discharged — while the single push that
closed them is **red** on `origin/main` and its S4 documentation asserts the
opposite. The amendment-#28 S4 exit criterion (a fully green CI run over the
batched range before the cycle is declared closed) was met for neither WP. This
is the **recurrence of ETCA-001 T-F4**, one work-package cycle after that
finding's remediation drove CI green — the remediation fixed the red gates but
added no mechanism forcing a session to confirm green *after* it pushes, so the
same failure mode re-formed immediately and at larger scale (two batched WPs).

Three **D2** findings compound it: `mypy --strict` is red in CI and green
locally because the `lint` toolchain floats (T-F2, itself a recurrence of
ETCA-001 T-F10 / EA-005 E-F1); 5 DirectML/provider tests hard-fail every CI
Windows leg because their `skipif` guards test build capability rather than
device executability (T-F3, a recurrence of ETCA-001 T-F2); and the WP-036F
audit and S4 documentation record CI as verified and green when it was never
checked (T-F4). Four **D3** findings — a permanently-red nightly gate (T-F5),
GPU CI skipped on the push that closed two GPU work packages (T-F6), no branch
protection so nothing stops a red push (T-F7), an unbounded self-hosted `rust`
leg (T-F8). Two **D4** — documentation/state drift (T-F9), the unpinned lint
toolchain as a hygiene item (T-F10).

The **test suite and the delivered capabilities are, on their merits, sound**:
the DirectML re-export is mathematically correct and executes on a real device;
WP-036E's device-resident path was independently audited (WP-036E S2 `FAIL` →
S3 remediated → delta re-audit CLEAN); the parity corpus, reproducibility
pipeline, `governance` job, disk-reclaim fix, and enforcing bench-regression
gate from ETCA-001 all held. **Every ETCA-002 finding is in the CI-gate
machinery, the local↔CI equivalence contract, and the push/close cadence — not
in test correctness or in the mathematics.** But a `FAIL` verdict is required
by methodology §3 (an open D1) and §4 principle 5 (an ETCA session cannot close
clean until every D1/D2 is `FIXED` or `AMENDED`; this read-only session passes
them forward).

**Blocking recommendation:** WP-036F is **not closed**. **WP-036G S1
(`0144Y`) must not begin** until T-F1, T-F2, T-F3, and T-F4 are resolved and
`origin/main` CI — including a `[gpu]` run on `PRIN-GPU-Runner` — is confirmed
green over the WP-036E + WP-036F range. The governance recommendations G1–G3
(per-WP blocking push, machine-checked S4 CI-green gate, branch protection)
should be adopted as a plan amendment in the same remediation cycle, because
without them the recurrence will re-form a third time.

**Auditor Signature:** AI pair (Claude Sonnet 5)
**Date:** 2026-09-02

---

## 7. Remediation closure table (appended by the remediation session)

**ETCA-002 remediation session — 2026-09-02.** Maintainer decisions taken via
`AskUserQuestion`: enable GitHub branch protection (a `main` branch **ruleset**,
classic branch-protection being unavailable on this private/Free repo — DV-009
precedent); run `gpu.yml` on every `main` push; adopt G1–G8 as Plan
**amendment #45**; quarantine `test_speed_vs_transformer` into DV-032.

Remediation commits (pushed to `origin/main` 2026-09-02, over `adbb1e3`):
`bef851c` (fixes) → `47d7ef3` (finalize this closure table) → `9d4fd86`
(promote `gpu` to a required check; root-cause + fix the runner-offline
condition).
**Green-CI confirmation — `9d4fd86` (HEAD): all six workflows
`success`** (`rust` / `python` / `parity` / `repro` / `snyk` / `gpu`);
`tools/check_ci_green.py 9d4fd86` → exit 0 (output below). `bef851c` is also
green on all six (its `gpu` run dequeued once the runner came online).
**T-F3 verified on real hardware:** on `PRIN-GPU-Runner`'s DirectML adapter
the `gpu-cuda` job's DirectML tests **run and pass** —
`TestDirectMLExecution::{test_pre_transform_graph_is_rejected_by_directml,
test_directml_executes_the_reexported_graph,
test_directml_agrees_with_cpu_within_tolerance}` all `PASSED`
(`4 passed, 15 skipped`); on every hosted `windows-latest` `test` leg of
`bef851c` the same tests **skip cleanly** (`python` workflow `success`).
**T-F5 verified:** `nightly` `workflow_dispatch` run `33678873449` — both
`full-suite` and `bench-regression` `success` (was permanently red).
The GPU runner is online because this session started a stopgap
`Runner.Listener.exe run`; the durable fix
(`ci/install-gpu-runner-service.ps1`, run once elevated) makes it an
auto-start service so DV-024's chronic-offline condition does not recur.

| ID | Severity | Resolution | Evidence |
|---|---|---|---|
| **T-F1** | D1 | **FIXED.** WP-036F is re-closed over a real green `origin/main` CI run — `9d4fd86` (HEAD), all six workflows `success` including `gpu` (`tools/check_ci_green.py 9d4fd86` exit 0); `bef851c` green on all six too — not a recollected one. `tools/check_ci_green.py` (G2) is the machine-checked S4 gate that makes "recollected green" an impossible state going forward; Development Workflow §3 + Plan amendment #45 G1 make per-WP S4 push blocking and prohibit un-amended multi-WP batching. WP-036E's own closure (`0144T`) is retro-covered by the same green run over the `6343416..bef851c` range. | `check_ci_green.py bef851c` output (below); Plan amendment #45; Development Workflow §3 "Per-WP push is mandatory and blocking"; `tools/check_ci_green.py` |
| **T-F2** | D2 | **FIXED.** `# type: ignore[no-untyped-call]` → `# type: ignore[no-untyped-call, unused-ignore]` at all 6 torch-stub-dependent sites (`nn/_bridge.py:146`, `_torch_compat.py:430`/`:1088`, `adversarial_tools.py:69`/`:132`, `temporal_training.py:573`) — `mypy` accepts a redundant `unused-ignore` code, so the comment is correct under both torch stub versions. `python.yml` `lint` toolchain pinned via `ci/lint-constraints.txt` (T-F10 / G6). `mypy python/prin --strict` exit 0 locally and in the `bef851c` CI run. | `git show` the 4 files; `ci/lint-constraints.txt`; `python.yml` `lint` job; CI `bef851c` `lint` green |
| **T-F3** | D2 | **FIXED.** New `tests/_env.py::directml_executes()` builds a one-node `DmlExecutionProvider` session and runs it — an *executability* probe. `TestDirectMLExecution`, `TestProviderLatencyTool`'s DirectML branch, and `test_daemon_controller.py::…::test_directml_executes_the_reexported_graph` now guard on it + carry `@pytest.mark.directml`; `_executable_backends()` checks active providers, not just the constructed session. `wp036f_provider_latency._pre_transform_check` records a portable `close` (`np.allclose rtol=1e-5 atol=1e-6`) alongside `bit_identical`; `main()` returns 0 when DirectML is registered-but-not-executable. `parity_report.rst` updated: tolerance, not bit-identity, is the acceptance criterion. Guard-class regression guard `tools/check_skipif_probes.py` in `python.yml` `governance`. **Verified end-to-end in CI:** on every hosted `windows-latest` `test` leg (`bef851c`/`9d4fd86` `python` `success`) the five previously-failing tests **skip cleanly** and `TestProviderLatencyTool`'s two tests **run and pass** under the tolerance assertions; on `PRIN-GPU-Runner`'s real DirectML adapter (`gpu-cuda` job, `-m "gpu or directml"`) `TestDirectMLExecution`'s three tests + the `test_daemon_controller` cross-provider test **run and pass** (`4 passed, 15 skipped`). | `tests/_env.py`; `git show` the 3 test files + the tool; `check_skipif_probes.py` exit 0; CI `9d4fd86` `python` (6 legs) + `gpu-cuda` "Python GPU + DirectML tests" step green |
| **T-F4** | D2 | **FIXED.** Root cause was procedural — S4 closed on a recollected "CI is green". `tools/check_ci_green.py` (G2) + Development Workflow §3 A9 update + amendment #45 G1 require the S4 session to run it against its own SHA and paste the output into the PSR before any closure. PSR-036F §9 addendum records the correction; the `0144X` "CI is green" claim is superseded. | Plan amendment #45 G1/G2; Development Workflow §4 checklist item A9; `DOCS/reports/036f-project-state.md` §9 |
| **T-F5** | D3 | **FIXED.** `test_acceptance_y2q1.py::…::test_speed_vs_transformer` folded into **DV-032** with a dated maintainer disposition (AskUserQuestion, 2026-09-02) — central `pytest.mark.skip` in `tests/conftest.py`, assertion byte-unchanged. `tests/` swept for wall-clock ratio siblings: this is the only one (the `test_acceptance_y2q2.py` ±5% asserts are on computed values). `nightly.yml` re-triggered via `workflow_dispatch` (run `33678873449`): `full-suite` **and** `bench-regression` both `success` (was permanently red). | `tests/conftest.py` `_RATIO_NODES`; `DEFERRED_VALIDATION_REGISTER.md` DV-032 test (3); `nightly` run `33678873449` (both jobs green) |
| **T-F6** | D3 | **FIXED.** `.github/workflows/gpu.yml` loses the `if: contains(…, '[gpu]')` gate on both jobs and runs on `push: [main]` + `schedule` (nightly) + `workflow_dispatch`; installs `.[dev,onnx]`; runs `-m "gpu or directml"` so the DirectML acceptance tests execute on the real adapter. `@pytest.mark.directml` registered in `pyproject.toml`. (Amendment #45 G4.) Verified: `gpu.yml` ran and passed on `bef851c`, `47d7ef3`, **and** `9d4fd86` (`gpu-cuda` + `gpu-wgpu` both `success` each time) — no `[gpu]` tag on any of them. | `git show .github/workflows/gpu.yml`; `gh run list --workflow gpu.yml` (3 consecutive `success` runs, no tag); DV-034 |
| **T-F7** | D3 | **FIXED (as a ruleset).** Classic branch protection is unavailable on this private/Free repo (`404 "Branch protection has been disabled"` — DV-009 precedent), so a `main` branch **ruleset** (`ci/main-branch-ruleset.json`) is created instead: required status checks — **every** `python` / `rust` / `parity` / `repro` / `snyk` / `gpu` job context, `gpu-cuda` / `gpu-wgpu` included (maintainer decision 2026-09-02, promoted per DV-034) — pull-request-required (0 approvals), block force-push/deletion, **no bypass actors**, enforcement `active`. Direct pushes to `main` are replaced by a PR flow whose merge is blocked on a red or pending check. The residual is the accepted single-runner SPOF: while `PRIN-GPU-Runner` is offline, no PR merges until it returns (DV-034 — mitigation: a second GPU runner). | `ci/main-branch-ruleset.json`; `ci/README.md`; `gh api repos/Symbo-gif/PRIN/rulesets` (post-remediation); Plan amendment #45 G3; DV-034 |
| **T-F8** | D3 | **DISPOSITIONED.** The finding described the `rust.yml` Windows `test` leg as an unbounded self-hosted job; verified against the repo it is already on GitHub-hosted `windows-latest` with `timeout-minutes: 120` (ETCA-001 DV-024 remediation, in place at the audit baseline `6343416`). The >1 h runtime observed at audit is DV-016 hosted-Windows CubeCL slowness **within** that bound, not an unbounded hang. Residual = DV-016 (standing disposition, not re-fixable without faster Windows CI hardware). No code change. | `.github/workflows/rust.yml` `test` job (`runs-on: windows-latest`, `timeout-minutes: 120`); DV-016; DV-024 |
| **T-F9** | D4 | **FIXED.** PSR-036F §9 addendum, DV-006 / DV-024 / DV-032 annotations, `036f-project-state.md` §7 CI bullet marked superseded, `CHANGELOG.md` `[Unreleased]`, and the session memory index all corrected to record that `adbb1e3` **was** pushed and **was** red, and to cite the real green run. | `git show` the doc set; `DOCS/reports/036f-project-state.md` §7/§9; memory index |
| **T-F10** | D4 | **FIXED.** `python.yml` `lint` installs `ruff`/`mypy`/`interrogate`/`bandit`/`hypothesis`/`torch` from the committed, pinned `ci/lint-constraints.txt` (torch from the CPU index), kept in step with the maintainer `.venv`. Coding Standards §6.2 gains the "no merge-gating job may `pip install` an unpinned tool" rule (amendment #45 G6). | `ci/lint-constraints.txt`; `.github/workflows/python.yml` `lint` job; Coding Standards §6.2 |

### `tools/check_ci_green.py` output for the green SHA

```
$ python tools/check_ci_green.py 9d4fd86
CI-green check — branch 'main', commit 9d4fd86
  rust       green     — run 33681657283
  python     green     — run 33681657366
  parity     green     — run 33681657160
  repro      green     — run 33681657256
  snyk       green     — run 33681657350
  gpu        green     — run 33681657236
RESULT: all required workflows green
$ echo $?
0

# `gpu` run 33681657236 job breakdown:
#   gpu-wgpu: success        gpu-cuda: success
#   "Python GPU + DirectML tests": 4 passed, 15 skipped
#     TestDirectMLExecution::test_pre_transform_graph_is_rejected_by_directml PASSED
#     TestDirectMLExecution::test_directml_executes_the_reexported_graph        PASSED
#     TestDirectMLExecution::test_directml_agrees_with_cpu_within_tolerance     PASSED

$ python tools/check_ci_green.py bef851c
  rust green · python green · parity green · repro green · snyk green · gpu green
RESULT: all required workflows green     # gpu dequeued once the runner came online

Audit-window range 6343416..9d4fd86 is covered by these green runs: they carry
the whole WP-036E (0144Q–0144T) + WP-036F (0144U–0144X) range plus the
remediation commits, so WP-036E's own never-independently-pushed closure
(0144T) is retro-covered here.
```

---

## Appendix A: ETCA-002 Audit Window Inventory

| Category | Value | Notes |
|---|---|---|
| Audit window | `6343416..adbb1e3` | 17 commits, 2026-09-01 20:59 → 2026-09-02 13:17 |
| Work packages | WP-036E (`0144Q`–`0144T`), WP-036F (`0144U`–`0144X`) | Deferred-Validation closure work (amendment #38) |
| Pushes to `origin/main` in window | **1** (`adbb1e3`) | amendment #28 requires one per WP S4 → expected 2 — **T-F1** |
| `origin/main` CI @ `adbb1e3` | `parity` ✅ `repro` ✅ `snyk` ✅ · `python` ❌ · `rust` ⏳ · `gpu` ⏭️ | last green was `6343416` (ETCA-001 remediation) |
| `nightly` @ 2026-09-02 | `bench-regression` ✅ · `full-suite` ❌ | **T-F5** |
| CI-failing tests | 5 (`test_wp036f_reexport.py` ×4, `test_daemon_controller.py` ×1) × 3 Windows legs | all pass on the maintainer host — **T-F3** |
| CI-failing lint steps | `mypy python/prin --strict` (3 unused ignores) | passes locally — **T-F2** |
| `xfail` markers | 0 | conforms |
| Workflows | 8 | `governance` job (ETCA-001 T-F1) present and green |
| Branch protection | **disabled** | **T-F7** |
| Findings | 10 — 1×D1, 3×D2, 4×D3, 2×D4 | 3 are recurrences of ETCA-001 findings (T-F2⟵T-F10, T-F3⟵T-F2, and T-F1⟵T-F4) |
