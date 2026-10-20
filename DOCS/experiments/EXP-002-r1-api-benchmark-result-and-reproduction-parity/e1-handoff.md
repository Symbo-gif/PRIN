# EXP-002-r1 E1 — Entry evidence and handoff

**Session:** `EXP-002-r1-E1` (EXP-002-r1 / C1, E1 — Pre-registration and Driver Preparation).<br>
**Date:** 2026-10-20 UTC. **AI pair:** Devin.<br>
**Deliverable:** codified Re-run (`-r1`/`-rN`) Namespace & Evidence Isolation governance, DV-047 closure, a DRAFT [`preregistration.md`](preregistration.md), and the isolated collection driver [`benchmarks/campaign/exp002_r1_driver.py`](../../../benchmarks/campaign/exp002_r1_driver.py) with synthetic-fixture regression tests [`tests/test_exp002_r1_driver.py`](../../../tests/test_exp002_r1_driver.py) for independent E2 review — **not** execution approval and not an experiment result.<br>
**Branch:** `campaign/exp002-r1-e1`.<br>
**Baseline (`M`):** `5677858c15d784d881b23d43dff5029d199b0a18` (`origin/main` after PR #35 merged 2026-10-20T10:05:42Z from `a570aa7f1f3cc30163d3a48e962fc1f058e55cdb`).<br>
**Protocol:** [`preregistration.md`](preregistration.md) (`Status: DRAFT`).

## 1. Entry verification and authority

The maintainer declared `EXP-002-r1` E1 on 2026-10-20 UTC and ratified three
governing pre-E1 decisions:

1. **Strict Re-run (`-r1`/`-rN`) Namespace & Evidence Isolation Rule**
   (codified in [`campaign-plan.md`](../campaign-plan.md) §7.1, §10.4 item 4,
   §14.2 amendment #10; [`DOCS/experiments/README.md`](../README.md);
   [`Experimentation_Standards.md`](../../standards/Experimentation_Standards.md)
   §4; and [`benchmarks/results/EXP-002-r1/README.md`](../../../benchmarks/results/EXP-002-r1/README.md)):
   `EXP-002-r1` uses completely disjoint roots (`benchmarks/results/EXP-002-r1/`,
   `DOCS/test_and_benchmark_results/EXP-002-r1/`, `EVIDENCE/exp002-r1-e1/`..`e5/`)
   and `exp002_r1_` driver/test/analysis module basenames. Predecessor
   `benchmarks/results/EXP-002/` and `DOCS/test_and_benchmark_results/EXP-002/`
   are never opened for writing. Combined `EXP-002` + `EXP-002-r1` tracked
   storage remains bounded by the existing 10 MiB allocation.
2. **Deciding H3 comparison policy (`EXP002D1-S2-F1`):** Registered the
   approved **§5.4 policy** (`CRLF`→`LF` table canonicalization + 4-key PDF
   `/Info` removal and `xref`/`startxref` pointer canonicalization + PNG
   critical-chunk normalization; `39/39` equal on the corrected generator) as
   the **sole primary decision rule for H3**, and retained the **§11.3
   pre-exposure policy** (`14/39` equal; `25` classified writer/host I/O
   residuals, `0` unclassified) as a **reported, non-gating writer-property
   diagnostic**, replacing `EXP-002`'s §11.3 item 1 clause and disclosing
   outcome exposure in `preregistration.md` (header, §1, §11.2).
3. **DV-047 closure:** Executed in E1 before authoring the driver (see §2
   below).

### 1.1 Verbatim `check_ci_green.py` and hosted-CI entry record (campaign plan §12 item 3)

Executed at E1 entry against `origin/main` baseline
`M = 5677858c15d784d881b23d43dff5029d199b0a18`:

```text
$ .venv/Scripts/python.exe tools/check_ci_green.py 5677858c15d784d881b23d43dff5029d199b0a18
CI-green check — branch 'main', commit 5677858c15d784d881b23d43dff5029d199b0a18
  rust       green     — run 39405463375
  python     green     — run 39405463348
  parity     green     — run 39405463347
  repro      green     — run 39405463356
  snyk       green     — run 39405463333
  gpu        green     — run 39405463413
RESULT: all required workflows green

EXIT_CODE=0
```

Additional hosted corroboration recorded at entry:

- **PR #34 merge commit (`305416fb0f85e690b12640b3f32fad48b55d9077`, merged 2026-10-18T05:00Z):**
  push-triggered `python` (`39099067876`), `parity` (`39099067955`), `repro`
  (`39099067747`), `snyk` (`39099067759`), and `gpu` (`39099067681`) all
  `success`; `rust` (`39099067757`) failed only on `audit` (DV-045 + 3
  unreachable `zip 1.1.4` advisories, subsequently closed in PR #35).
- **Scheduled `nightly.yml` runs on `main`:** two consecutive scheduled runs
  succeeded in full (`full-suite` + `bench-regression`): run `39203786555`
  (2026-10-19 on `305416fb`) and run `39373976832` (2026-10-20 on `305416fb`),
  corroborating O-1 on Linux and confirming zero benchmark regressions.
- **PR #35 head (`a570aa7f1f3cc30163d3a48e962fc1f058e55cdb`) and merge (`5677858c15d784d881b23d43dff5029d199b0a18`):**
  all 6 required workflows passed 31/31 check runs with 0 Node-20 deprecation
  annotations; `gpu` run `39405463413` passed both `gpu-cuda` and `gpu-wgpu`
  (0 occurrences of DV-046's `flops` test failure).

## 2. DV-047 discharge record

1. **Removed stale `.pth`:** Deleted `.venv/Lib/site-packages/prin_core.pth`
   (which pointed at `C:\dev\PRIN-r1-amendment\python`) and verified
   `.venv/Lib/site-packages/prin.pth` points to `C:\dev\PRIN\python`.
2. **Rebuilt `python/prin/_prin_core.pyd` from clean `main` (`5677858c15d784d881b23d43dff5029d199b0a18`):**
   ran `.venv\Scripts\python.exe -m maturin develop --release -m crates/prin-py/Cargo.toml`
   strictly sequentially (exit 0 in 6m 21s, installing `prin-core-1.0.0rc1`),
   then removed the transient `prin_core.pth` written by `maturin develop` so
   only `prin.pth` (`C:\dev\PRIN\python`) and `__editable__.prinet-3.0.0.pth`
   remain in `.venv/Lib/site-packages/`.
3. **Verified rebuilt binary provenance:**
   - Path: `C:\dev\PRIN\python\prin\_prin_core.pyd`
   - Byte size: `9,290,240` bytes (`PRIN_CORE_PYD_BYTES = 9290240`)
   - SHA-256: `37392d067efa3983e384c94f4ac2268c4fad2f5ea929c529b3db50bff4fee99e`
     (replacing the stale 2026-09-28 binary `64ea1a2cf38cdbe43fc029c55e791e244b771b2909360c3890ae6f9224b47349`)
   - `prin.__file__ == "C:\\dev\\PRIN\\python\\prin\\__init__.py"`,
     `prin._prin_core.__file__ == "C:\\dev\\PRIN\\python\\prin\\_prin_core.pyd"`,
     `prin.core_version() == "1.0.0-rc1"`.
4. **Pinned and closed:** Pinned in `benchmarks/campaign/exp002_r1_driver.py`
   (`PRIN_CORE_PYD_SHA256`, `PRIN_CORE_PYD_BYTES`) and `preregistration.md`
   §1.1, and recorded **DV-047 CLOSED** (append-only, 0 deleted lines) in
   [`DOCS/reports/DEFERRED_VALIDATION_REGISTER.md`](../../reports/DEFERRED_VALIDATION_REGISTER.md).

## 3. Deliverables under review

| Artefact | State |
|---|---|
| [`preregistration.md`](preregistration.md) | `DRAFT` (`Status: DRAFT`); outcome exposure disclosed in header, §1, and §11.2; §5.4 registered as primary H3 rule and §11.3 as non-gating writer-property diagnostic; isolated `EXP-002-r1` roots and DV-047 `.pyd` pin registered |
| [`benchmarks/campaign/exp002_r1_driver.py`](../../../benchmarks/campaign/exp002_r1_driver.py) | Isolated E1 collection driver bound to `RAW_ROOT = benchmarks/results/EXP-002-r1`, `OUTPUT_ROOT = DOCS/test_and_benchmark_results/EXP-002-r1`, `EXP_ID = "EXP-002-r1"`, `SESSION_ID = "EXP-002-r1-E3"`, `r1-` mode labels, `_prin_core.pyd` and generator SHA-256 verification, predecessor `EXP-002` path rejection, and combined `EXP-002` + `EXP-002-r1` 10 MiB storage cap enforcement |
| [`tests/test_exp002_r1_driver.py`](../../../tests/test_exp002_r1_driver.py) | 320 synthetic-fixture regression tests (`320 passed`, `99.60%` statement coverage on `exp002_r1_driver.py`, `751/754` statements), including `allowed_output_roots` admission tests, negative predecessor-path rejection tests, `_prin_core.pyd` and generator digest mismatch tests, and combined storage-cap tests |
| [`benchmarks/results/EXP-002-r1/README.md`](../../../benchmarks/results/EXP-002-r1/README.md) | Skeleton README for the isolated raw-artefact root (no `RUN-` directory exists) |
| [`e2-review-packet.md`](e2-review-packet.md) | Decision and S4 retro-audit packet for `EXP-002-r1-E2` (`PREPARED FOR REVIEW — NOT APPROVED`) |
| [`EVIDENCE/exp002-r1-e1/`](../../../EVIDENCE/exp002-r1-e1/README.md) | Isolated E1 verification evidence bundle with `SHA256SUMS.txt` |

## 4. Open for `EXP-002-r1-E2` (Review and approval + S4 retro-audit)

1. Independent review of [`preregistration.md`](preregistration.md) (§10 items
   1–5) and [`benchmarks/campaign/exp002_r1_driver.py`](../../../benchmarks/campaign/exp002_r1_driver.py),
   followed by recording dated maintainer scientific approval (`**Status:** APPROVED`
   and `**Maintainer approval:** MichaelMaillet, YYYY-MM-DD UTC`) in
   `preregistration.md` and `e2-review.md`.
2. **Independent S2-class retro-audit of `EXP002D1-S4-F2` (`814b670c`) and
   `EXP002D1-S4-F3` (`67100a69`)** per Development Workflow §7 and
   `DOCS/audits/2026-10-15-exp002-d1-correction-audit.md` §S4.16 item 4, using
   the checklist in [`e2-review-packet.md`](e2-review-packet.md) §4.
3. Freeze occurs only at the first `RUN-` creation in `EXP-002-r1-E3`. Session
   `0164` and `0165`–`0194` remain `BLOCKED` until `EXP-002-r1-E5` returns a
   non-reversal verdict verified and accepted by the maintainer.

## 5. Verification summary (E1 local & security gate)

Full command logs and digests are archived in
[`EVIDENCE/exp002-r1-e1/`](../../../EVIDENCE/exp002-r1-e1/README.md):

- **Focused driver suite:** `.venv\Scripts\python.exe -m pytest tests/test_exp002_r1_driver.py --cov=benchmarks.campaign.exp002_r1_driver --cov-report=term-missing --basetemp=.pytest_basetemp -o faulthandler_timeout=300 --durations=20` → **`320 passed`**, **`99.60%` coverage** (`751/754` statements; ≥95% gate met), exit `0`.
- **Static & type gates:** `ruff check python/ tests/ benchmarks/ tools/ parity/ DOCS/experiments/` → exit `0`; `ruff format --check` (both scopes) → exit `0`; `mypy python/prin --strict` and `mypy DOCS/experiments/ --strict` (plus `benchmarks/campaign/exp002_r1_driver.py` and `tests/test_exp002_r1_driver.py`) → exit `0`; `interrogate -c pyproject.toml python/prin` → `97.6%`, exit `0`.
- **Security gates (Coding Standards §6):** `bandit -r python/prin DOCS/experiments -c pyproject.toml` → `0` issues, exit `0`; Snyk Code MCP (`snyk_code_scan`) on `benchmarks/campaign/exp002_r1_driver.py` and `tests/test_exp002_r1_driver.py` at threshold `low` → `0` issues (`issueCount: 0`); `cargo audit` → exit `0`; `pip-audit .` and `pip-audit -r DOCS/sphinx/requirements.txt` → `0` vulnerabilities, exit `0`; `gitleaks git . --no-banner` and `gitleaks git . --staged --no-banner` → `0` leaks, exit `0`.
- **Governance & docs:** `check_dv_register_gates.py`, `check_global_session_registration.py`, `check_skipif_probes.py`, `wp001_baseline.py check`, and `pytest tests/test_campaign_quality_gates.py tests/test_wp001_baseline.py` → all exit `0`; clean Sphinx build (`-W --keep-going -b html` after removing `DOCS/sphinx/_build`) → `build succeeded`, `0` warnings, exit `0`.
- **Predecessor immutability check:** `git diff 5677858c15d784d881b23d43dff5029d199b0a18 -- DOCS/experiments/EXP-002-api-benchmark-result-and-reproduction-parity/ benchmarks/results/EXP-002/` is **empty** (`0` changed files), and `verify_manifest` passes on all 5 frozen `benchmarks/results/EXP-002/RUN-*` directories and the 172-record `paper/artefact_manifest.json`.
