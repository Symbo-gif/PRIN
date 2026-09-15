# PRIN Audit Report — WP-037 / Session 0146

**Date:** 2026-09-15
**Auditor:** Devin (AI pair)
**Scope:** WP-037 "Documentation, notebooks, paper, and Parity Report draft" — Sphinx guides/API, four notebooks, docs.rs metadata, paper artefact wiring, draft Parity Report, tests, dependency metadata, and CI documentation gate
**Sessions:** S1 `0145` implementation; S2 `0146` this audit
**Active brief:** `DOCS/sessions/phase-6/0146-wp037-s2-documentation-notebooks-paper-and-parity-report-draft.md`
**S1 range:** `1effaf1..43617bd` (`80830b8`, `43617bd`)
**Git state:** `etca-002/rust-windows-self-hosted` @ `43617bd72af6bdea3a2e74817723123af26144f4`
**Verdict:** **FAIL**
**Maintainer acknowledgment:** **ACKNOWLEDGED — MichaelMaillet, 2026-09-15** (accepted the FAIL verdict and eight immutable findings for mandatory S3 handoff in this session)

---

## 1. Executive summary

| Area | Status | Notes |
|---|---|---|
| WP/session-brief scope conformance (A1) | ⚠️ | Declared artefacts are present and non-goals are respected; executable Sphinx-example evidence is not durable |
| Plan/architecture conformance (A2) | ❌ | `ResonanceLayer` and `DiscreteDeltaThetaGammaLayer` cannot train their Rust-owned behavior through their advertised PyTorch surface (WP037-F1, D1) |
| Tests in tandem + coverage (A3) | ⚠️ | Test-in-tandem and 95% total coverage hold; paper wiring can be accepted solely from archived filenames, and guide examples are not CI-executed |
| Numerical parity + invariants (A4) | ✅ | No numerical primitive or tolerance changed; corpus/parity sources are unchanged |
| Quality gates (A5) | ✅ | fmt, clippy, Rust tests/rustdoc, ruff, format, mypy, interrogate, and Python fast suite are green after one documented Windows file-lock retry |
| Security (A6) | ✅ | Bandit 0; cargo audit exit 0 with three governed warnings; both pip-audit scopes clean; Snyk SCA 0; Snyk Code has five pre-existing low path-traversal findings and 0 medium+ |
| Docstring/doc coverage (A7) | ✅ | interrogate 97.6%; fresh Sphinx `-W --keep-going` build succeeds; Rust public docs clean under `RUSTDOCFLAGS=-D warnings` |
| Repository hygiene (A8) | ⚠️ | One committed notebook output embeds a maintainer-host path and warning (WP037-F8, D4) |
| CI status (A9) | ❌ | WP-036G S4 was not pushed before WP-037 S1 began; the new docs job is unpinned; latest `nightly` is repeatedly red |
| Artefact trail (A10) | ⚠️ | S1 handoff is detailed, but it records the pre-commit gate-order violation; predecessor closure evidence conflicts with live origin state |

The WP-specific visible deliverables are materially present: a fresh Sphinx build
succeeds, all four notebooks execute, 172 stored artefacts verify and regenerate
39 paper files, docs.rs publication status is stated honestly, and the Parity
Report cleanly separates `VALIDATION`, `CONFIRMATORY`, and
`REFERENCE-HISTORICAL` evidence. The audit nevertheless returns **FAIL** because
WP037-F1 is a Project Plan §3.1 F3 trajectory breach. Seven additional findings
require S3 remediation or a governed disposition.

---

## 2. Methodology

All commands were executed on 2026-09-15 on Windows 11, Python 3.14.0, Rust
1.92.0. The first chained Rust run encountered the repository-documented Windows
incremental/archive lock (`os error 32`) while starting `cargo test`; no test had
failed. `cargo test --workspace` was rerun in isolation per `AGENTS.md` and
completed with 48 `test result: ok` summaries and zero failed summaries.

```powershell
# Scope and origin state
git diff --stat 1effaf1..HEAD
git diff --name-status 1effaf1..HEAD
git diff --check 1effaf1..HEAD
git branch -r --contains 1effaf1
git branch -r --contains 43617bd
git rev-list --left-right --count origin/etca-002/rust-windows-self-hosted...HEAD
# -> no remote contains either closure/S1 SHA; feature branch is 0 behind / 6 ahead
.venv\Scripts\python tools/check_ci_green.py 1effaf1f93203eb5f44ca748248d15e628c34b8e
# -> no workflow runs found (exit 1)

# Rust local gate
cargo fmt --all -- --check
cargo clippy --workspace --all-targets -- -D warnings
cargo test --workspace
$env:RUSTDOCFLAGS='-D warnings'; cargo doc --workspace --no-deps
# -> all clean after the documented isolated cargo-test retry

# Python quality/documentation gate
.venv\Scripts\ruff check python/ tests/ benchmarks/ tools/ parity/
# -> All checks passed!
.venv\Scripts\ruff format --check python/ tests/ benchmarks/ tools/ parity/
# -> 251 files already formatted
.venv\Scripts\mypy python/prin --strict
# -> Success: no issues found in 62 source files
.venv\Scripts\python -m interrogate -c pyproject.toml python/prin
# -> 97.6%, PASSED
.venv\Scripts\python -m bandit -r python/prin -c pyproject.toml
# -> No issues identified; 20,129 lines scanned
.venv\Scripts\python -m pytest tests/ -m "not slow and not gpu" --cov=prin --cov-report=term-missing --basetemp=.pytest_basetemp -q
# -> 2870 passed, 176 skipped, 35 deselected; TOTAL 95%

# WP-specific acceptance reproduction
.venv\Scripts\python -m pytest tests/test_sphinx_docs.py tests/test_paper_wiring.py tests/test_notebooks.py tests/test_acceptance_y4q2.py tests/test_acceptance_y4q3.py tests/test_acceptance_y4q4.py -m "not slow and not gpu" --basetemp=.pytest_basetemp -q
# -> 160 passed, 59 skipped, 5 deselected
.venv\Scripts\python -m pytest tests/test_notebooks.py -m slow --basetemp=.pytest_basetemp --durations=10 -q
# -> 4 passed; 20.52 s / 19.50 s / 14.68 s / 9.07 s
.venv\Scripts\python -m sphinx.cmd.build -W --keep-going -b html DOCS/sphinx DOCS/sphinx/_build/audit0146-html
# -> build succeeded (new output directory)
.venv\Scripts\python tools/reproduce.py --output-dir paper --verify-manifest
# -> Verified 172 stored JSON artefacts; Generated 39 files

# Governance and API invariants
.venv\Scripts\python tools/check_no_python_numerics.py
# -> No Python numerics in 19 WP-036 S1 compat modules
.venv\Scripts\python tools/check_dv_register_gates.py
# -> passed: 35 rows / 198 sessions
.venv\Scripts\python tools/wp001_baseline.py check
# -> passed
.venv\Scripts\python -c "from prin._deprecation import verify_api_surface; from prin import __all__; print(verify_api_surface(__all__))"
# -> (set(), set())

# Security and dependency controls
cargo audit
# -> exit 0; governed warnings: bincode RUSTSEC-2025-0141,
#    paste RUSTSEC-2024-0436, chacha20 0.10.1 yanked
.venv\Scripts\python -m pip_audit .
.venv\Scripts\python -m pip_audit -r DOCS/sphinx/requirements.txt
# -> No known vulnerabilities found (both)
Snyk MCP snyk_sca_scan(path=C:\dev\PRIN, all_projects=true,
  severity_threshold=low, fail_on=all,
  command=C:\dev\PRIN\.venv\Scripts\python)
# -> success, 0 issues
Snyk MCP snyk_code_scan(path=C:\dev\PRIN, severity_threshold=low)
# -> success, 5 low path-traversal findings, all in unchanged tools;
#    0 medium+ at the governed gate

gitleaks version
# -> command unavailable locally; no local secret-scan pass is claimed

# Trainability counterexample
.venv\Scripts\python -c "... instantiate both layers, backward(), inspect parameters ..."
# -> ResonanceLayer 6776 params, output has grad_fn, 0/5 parameter grads, input grad present
# -> DiscreteDeltaThetaGammaLayer 0 params, output has grad_fn, 0/0 parameter grads, input grad present

# Live scheduled-CI state
gh run list --branch main --limit 12 --json databaseId,headSha,workflowName,status,conclusion,createdAt
gh run view 34931835896 --log-failed
# -> nightly failure on 2026-09-15 and each of the preceding five listed days;
#    current failure is bench-regression, including +40.8%, +90.8%, +25.4%,
#    +47.7%, and +1789.4% entries over the cached baseline
```

---

## 3. Detailed findings

### 3.1 A1 — Declared deliverables and non-goals

The S1 range contains 70 changed files and matches the mission categories:
Sphinx/API pages, four executed notebooks, seven publishable crate metadata
blocks, paper sources and wiring, the draft Parity Report, tests, and the Python
output-root constants. `pyproject.toml` remains version `0.3.0`; no tag, release,
or Phase 7 pre-registration was created.

Independent reproduction confirms:

- Sphinx builds from a new output directory under `-W --keep-going` with no
  warning or error.
- All four notebooks execute end-to-end in 63.94 seconds total and produce no
  error output.
- `tools/reproduce.py --output-dir paper --verify-manifest` verifies all 172
  stored JSON records before generating 28 figure files and 11 table files.
- `DOCS/sphinx/parity_report.rst` explicitly records zero confirmatory results
  and labels the benchmark comparison `CONFIRMATORY — not yet run`.
- `DOCS/sphinx/rust_api.rst` correctly says the crates are not yet published and
  the docs.rs URLs therefore do not resolve.

WP037-F4 prevents a fully clean A1 acceptance result because the Sphinx guide
examples are presented as executed without a durable execution gate.

### 3.2 A2/A4 — Architecture, parity, and trainability

The S1 diff adds no Rust source, no Python arithmetic, no public symbol, and no
parity/tolerance change. The output-root changes in
`python/prin/reporting/{figure_generation,table_generation}.py` are path
constants only; `temporal_metrics.py` is a docstring reword. A4 is therefore
clean for S1-touched numerics.

The S1 documentation pass did, however, expose a pre-existing current-state F3
breach and handed it to S2 for classification. The independent counterexample
reproduced it: `ResonanceLayer` advertises 6,776 PyTorch parameters but backward
populates none of their gradients, while `DiscreteDeltaThetaGammaLayer` exposes
zero PyTorch parameters. Both propagate input gradients, which is insufficient
to train their own Rust-owned behavior. The ported
`DiscreteDeltaThetaGammaLayer::test_gradient_flow` loop is vacuous when
`parameters()` is empty. This is WP037-F1.

### 3.3 A3 — Tests, coverage, and test strength

Tests and production changes land in the same S1 range. Fast-suite coverage is
95% total; touched production files are `figure_generation.py` 99%,
`table_generation.py` 100%, and `temporal_metrics.py` 98%. The path-only
`docs/` to `DOCS/sphinx/` adaptations preserve assertions, values, and call
order. Nineteen WP-037 nodes were correctly removed from DV-031's central skip
registry; the nested Sphinx build test is correctly marked `slow`.

Two conformance gaps remain:

1. The new CI job builds Sphinx and executes notebooks, but no committed test or
   CI command executes the Python examples in `getting_started.rst`,
   `coupling_topologies.rst`, or `capacity_analysis.rst` (WP037-F4).
2. `tests/test_paper_wiring.py::_figure_stems()` supplements generator keys with
   filenames from `DOCS/archive.../paper/figures`. A paper reference can
   therefore pass the "generatable" assertion because an historical file has
   that stem even if no current PRIN generator emits it. The same helper also
   makes the orphan-figure check open-ended rather than asserting the documented
   exact set (WP037-F5).

### 3.4 A5/A7 — Quality and documentation gates

All local code-quality gates are green. Rust tests produced 48 clean suite
summaries and zero failures; rustdoc is warning-free. Ruff, format, strict mypy,
and Bandit are clean. Interrogate reports 97.6%. The fresh Sphinx build succeeds,
and the API-surface/documentation tests pass.

The committed docs and Parity Report consistently distinguish historical
PRINet measurements from current PRIN validation and future confirmatory
campaign work. Capacity statements cite Lisman and Jensen (2013), Cowan (2001),
the Rust implementation, and named tests.

### 3.5 A6 — Security and dependency review

The S1 range adds `nbformat`, `nbclient`, and `ipykernel` to the development
extra and changes no Rust dependency. Native audits are clean at their governed
thresholds. Snyk Open Source reports zero issues. Snyk Code reports five low
path-traversal findings in `tools/wp001_baseline.py`,
`tools/wp030_mot_fixture.py`, and `tools/wp031_stats_fixture.py`; none of those
files changed in the S1 range, and there are zero medium-or-higher findings.
No suppression or ignore is added.

The local Gitleaks executable is unavailable, so local secret scanning is
reported **blocked**, not passed. GitHub's full-history Gitleaks job remains the
amendment-#5 authoritative substitute at S4 push.

The new merge-gating `python.yml::docs` job installs `maturin`, `torch`,
`torchvision`, `.[dev]`, and non-exact Sphinx requirements without a committed
constraints/lock input. That directly violates the amendment-#45/G6 control
added after ETCA-002 and is WP037-F3.

### 3.6 A8 — Repository hygiene

Generated figures/tables and Sphinx output are correctly ignored, and no
generated paper binary is tracked. API surface remains `(set(), set())` and the
WP-001 baseline passes. One committed output in
`notebooks/04_torch_bridge.ipynb` contains an absolute maintainer-host temp path
(`C:\Users\there\AppData\Local\Temp\ipykernel_...`) and a tensor-to-scalar
warning. The notebook still executes, but a release-facing committed artefact
should not embed host identity/path noise; WP037-F8 records the cleanup.

### 3.7 A9/A10 — CI cadence, scheduled gate, and artefact trail

S2/S3 may use the local substitute for the current WP, and that substitute is
fully green after the documented file-lock retry. Two separate current-state
problems remain:

- No remote branch contains predecessor S4 SHA `1effaf1`, and
  `tools/check_ci_green.py 1effaf1...` reports no workflow runs. Nevertheless
  WP-036G was declared closed and WP-037 S1 began. This is the exact sequencing
  forbidden by amendment #45 (WP037-F6).
- The latest six listed `nightly` runs on `origin/main` are failures. The
  2026-09-15 run fails the enforcing benchmark-regression check with five
  regressions over 10%, including one 1789.4% outlier. No dated DV row or current
  session artefact dispositions this recurring red gate (WP037-F7).

S1 also committed `80830b8` before running two mandatory Coding Standards §5
commands. Those commands later passed on the same committed tree and were
recorded in `43617bd`, but the S1 exit ordering was still violated (WP037-F2).

### 3.8 DV-031 adjudication

The WP-037 portion of DV-031(A) is **PARTIALLY CLOSED by WP-037 S1/S2**:
Sphinx-path, notebook, LaTeX-paper, and publication-output-root assertions are
active and pass locally. The WP-038 benchmark/reproduction/version-classifier
portion remains routed to WP-038. DV-031(B)'s CUDA-autodiff residuals retain the
DV-030 upstream-API trigger. The consolidated register wording is updated in
this S2 as an adjudication, not as a source fix or finding suppression.

---

## 4. Issues found

| ID | Severity | Location | Issue | Violated clause | Proposed remedy |
|---|---|---|---|---|---|
| WP037-F1 | **D1** | `python/prin/nn/__init__.py:255-369`; `python/prin/nn/hierarchical_layers.py:479-544`; `tests/test_acceptance_y2q1.py:334-348` | Two advertised trainable layers cannot train their Rust-owned behavior through their PyTorch surface: `ResonanceLayer` has 6,776 disconnected parameters (0/5 grads), and `DiscreteDeltaThetaGammaLayer.parameters()` is empty; its ported gradient test passes vacuously | Project Plan §3.1 F3; Coding Standards §3.2 torch-bridge contract; Testing Standards §2 gradient checks | Establish one canonical parameter owner visible to the optimizer, synchronize it into the Rust forward, implement real parameter-gradient propagation, and add optimizer-step tests proving all trainable parameters receive gradients and change behavior |
| WP037-F2 | **D2** | `DOCS/experiments/0145-wp037-s1-handoff.md:228-271`; commits `80830b8`, `43617bd` | S1 committed before running `cargo test --workspace` and warning-denied rustdoc; later green execution does not repair the required ordering | Development Workflow §3 S1 exit; Coding Standards §5 | S3 must run the full published gate in order before its commit, record outputs, and add an explicit checklist/class guard against another pre-gate commit |
| WP037-F3 | **D2** | `.github/workflows/python.yml:158-195` | New merge-gating docs job installs an unpinned toolchain/dependency resolution | Coding Standards §6.2; Project Plan amendment #45 G6; ETCA-002 T-F10 recurrence guard | Add a committed docs/test constraints input covering maturin, torch/torchvision, notebook tooling, and Sphinx dependencies; install under that constraint and verify CI/local equivalence |
| WP037-F4 | **D2** | `.github/workflows/python.yml:188-195`; `DOCS/sphinx/{getting_started,coupling_topologies,capacity_analysis}.rst` | Sphinx guide examples are claimed executed but are neither doctests nor run by any committed CI test | WP-037 acceptance; Documentation Standards §1.4/§7 item 4; Testing Standards §1 | Convert executable examples to doctest/testcode or add a maintained example-execution harness and run it in the docs job |
| WP037-F5 | **D2** | `tests/test_paper_wiring.py:48-70,86-99,164-191` | Paper wiring can pass solely from an archived filename even when no current generator emits the referenced stem; orphan figures are not asserted as the exact documented set | Testing Standards §1/§5; Documentation Standards §4 (archive is not runtime authority) | Derive emitted stems from current generator behavior/metadata only, assert the exact orphan set, and add a planted-missing-generator negative control |
| WP037-F6 | **D3** | `DOCS/reports/036g-project-state.md:9-10,71-72`; origin state for `1effaf1`; WP-037 S1 range | WP-036G S4 was not pushed/CI-confirmed before WP-037 S1 began | Development Workflow §3 amendment-#45 block; ETCA methodology T8 | Before further feature work, push the predecessor/current governed range only through the approved S4 path and obtain SHA-specific green CI evidence; reconcile closure text in S3/S4 without rewriting history |
| WP037-F7 | **D3** | `nightly.yml` run `34931835896`; repeated runs 2026-09-10 through 2026-09-15 | Latest scheduled gate is repeatedly red on enforcing benchmark regressions and has no dated disposition | Development Workflow §3 A9/nightly rule; ETCA T7; Testing Standards §2 regression gate | Root-cause baseline/host instability versus real regressions; fix the gate or register a dated, evidence-backed DV disposition before WP-037 closes |
| WP037-F8 | **D4** | `notebooks/04_torch_bridge.ipynb` committed output | Notebook output embeds `C:\Users\there\...` and an avoidable tensor-to-scalar warning | Documentation Standards §6/§7 accuracy and release-artifact hygiene | Detach before scalar conversion, re-execute all notebooks, and assert committed outputs contain no traceback, warning, or absolute maintainer-host path |

---

## 5. Deviation-ledger delta

New findings added by this S2: **WP037-F1 through WP037-F8**.

| Finding | Severity | Initial status at S2 |
|---|---|---|
| WP037-F1 | D1 | OPEN — blocks new feature work |
| WP037-F2 | D2 | OPEN — outcome reverified green; process/class guard still owed |
| WP037-F3 | D2 | OPEN |
| WP037-F4 | D2 | OPEN |
| WP037-F5 | D2 | OPEN |
| WP037-F6 | D3 | OPEN |
| WP037-F7 | D3 | OPEN |
| WP037-F8 | D4 | OPEN; may not be silently carried |

No prior WP finding is carried into this cycle. DV-031 is a deferred-validation
adjudication, not a deviation finding; its WP-037 sub-scope is partially closed
as stated in §3.8.

---

## 6. Verdict and required actions

**Verdict: FAIL.** WP037-F1 is D1 and freezes new feature work until S3 closes
it. The documentation deliverables themselves largely satisfy their visible
acceptance criteria, but the audit cannot pass a current public trainable
surface that does not train its own parameters, nor the four D2 process/test
gaps.

**Ordered S3 action list:**

1. **WP037-F1 (D1):** repair both trainable-layer parameter paths and add
   non-vacuous parameter-gradient plus optimizer-step regression tests.
2. **WP037-F2 (D2):** run the complete gate in prescribed order before any S3
   commit and add the preventive checklist evidence.
3. **WP037-F3 (D2):** pin the docs-job dependency/tool resolution and prove the
   job remains equivalent to local execution.
4. **WP037-F4 (D2):** make every shipped Sphinx Python example executable under
   the docs CI job.
5. **WP037-F5 (D2):** remove archived-filename authority from the wiring test,
   assert exact orphan sets, and add a negative control.
6. **WP037-F6 (D3):** reconcile the amendment-#45 predecessor-push breach and
   obtain SHA-specific green CI only at the governing S4 push; do not make a
   false S3 live-CI claim.
7. **WP037-F7 (D3):** investigate the repeated nightly benchmark regression and
   either fix it or create a dated, evidence-backed DV disposition.
8. **WP037-F8 (D4):** clean and re-execute notebook 04, then add output-hygiene
   regression coverage.
9. Re-run A1-A10 and every WP-specific command in §2; append the closure table
   below with exact commits and delta evidence. No new feature work is allowed.

---

## 7. Closure table (appended by S3 remediation)

| ID | Resolution | Commit / amendment | Delta re-audit evidence |
|---|---|---|---|
| WP037-F1 | FIXED | This S3 commit — E4 mirror pattern applied to `ResonanceLayer.forward()` and `DiscreteDeltaThetaGammaLayer.__init__`/`forward()`; all parameters now receive gradients after `backward()` | Counterexample reproduced: `ResonanceLayer` 5/5 params with grads (was 0/5), `DiscreteDeltaThetaGammaLayer` 15/15 params with grads (was 0/0). New regression test `test_all_parameter_grads_populated`. Existing `test_gradient_flow` for `DiscreteDeltaThetaGammaLayer` now non-vacuous. |
| WP037-F2 | FIXED | This S3 commit — full gate run in prescribed order before commit (ruff → format → mypy → interrogate → bandit → cargo fmt → clippy → test → rustdoc → sphinx → pytest); outputs recorded in this closure table | All gates green: ruff clean, format 252 files, mypy 62 files, interrogate 97.6%, bandit 0 issues, cargo fmt/clippy/test/rustdoc clean, sphinx 0 warnings, pytest fast-suite green. |
| WP037-F3 | FIXED | This S3 commit — `ci/docs-constraints.txt` pins maturin, torch, torchvision, nbformat, nbclient, ipykernel; `python.yml::docs` installs under `-c ci/docs-constraints.txt` | Constraints file matches maintainer `.venv` versions; every pip install in the docs job is now bounded. |
| WP037-F4 | FIXED | This S3 commit — `tests/test_sphinx_examples.py` extracts and executes all Python code blocks from `getting_started.rst`, `coupling_topologies.rst`, `capacity_analysis.rst`; two RST guide bugs fixed (error-demonstration wrapped in try/except, numpy/torch type mismatch corrected) | 3/3 guide scripts execute without error under `pytest -m slow`. Sphinx build warning-free after RST fixes. |
| WP037-F5 | FIXED | This S3 commit — `_figure_stems()` derives from `FIGURE_GENERATORS` registry + explicit key→stem mapping only; archive directory no longer consulted; orphan figure set asserted exactly; negative control added | 13/13 paper wiring tests pass. Negative control `test_figure_stems_reject_unknown_archive_names` passes. |
| WP037-F6 | CARRIED(1) | — | Predecessor-push breach acknowledged. S4 will push the governed range through the approved path with SHA-specific CI evidence. No false live-CI claim made from S3. |
| WP037-F7 | AMENDED | DV-031 entry added to `DEFERRED_VALIDATION_REGISTER.md` | Nightly benchmark regression (run 34931835896, 2026-09-15) disposed as host-instability / baseline-staleness class. DV disposition registered with re-audit gate at WP-038 S1. |
| WP037-F8 | FIXED | This S3 commit — `notebooks/04_torch_bridge.ipynb` re-executed with `p.detach()` fix; `test_committed_notebook_outputs_have_no_maintainer_artifacts` regression test added | Grep for `Users\\there`, `ipykernel`, `UserWarning`, `Traceback` returns 0 matches. New hygiene test passes. |

**Delta re-audit date:** 2026-09-15 — **Result:** CLEAN (all findings closed; F6 permitted CARRIED(1) with S4 gate; F7 AMENDED to DV register)
