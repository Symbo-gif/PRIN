# PRIN Executive Audit Report - Session 007

**Date:** 2026-10-11 UTC
**Auditor:** Devin (AI pair of record)
**Scope:** Campaign-readiness delta audit and full-project local re-verification;
EXP-002 E1 preparation only, outside sessions 0001-0198 and outside E-stages.
**Git branch/state:** `audit/ea007-exp002-readiness` from
`fdd28d88e4c57d544e5d30fa52cce85807ab15a9` plus this session's diff.
**Verdict:** PASS-WITH-REMEDIATION — four scoped findings (EA007-E-F1..F4)
FIXED with local evidence; zero unresolved D1/D2. Local session closure;
main delivery via PR pending — no claim of merged-to-main or current
hosted CI green.

## 1. Executive Summary Table

| Audit dimension | Status | Observation |
|---|---|---|
| E1: Mathematical and oscillator dynamics core | Delta reviewed | No new numerical implementation; PSR-039 S2-F3/S2-F4 remain governed deferrals. |
| E2: Codebase and architecture conformance | Delta reviewed | Runtime code unchanged; fix is feature-gated module documentation. |
| E3: Test suite and parity corpus | Verified | 19 gate-regression tests pass (18 quality-gate tests — 13 of the original 18 failed the pre-change config — plus 1 dependency-floor regression); full Windows suite passed: 5,667 / 184 skipped / 0 failed in 29:42. |
| E4: Security and supply chain | Checks complete; disposition recorded | EA007-E-F4 (D2) urllib3 floor FIXED and re-verified clean; the five main-manifest torch advisories are the pre-existing EA003-E-F7 governed dispositions; native audits, Snyk Code, and full-history secret scan all executed. |
| E5: Standards and documentation | Verified | DV-042 fixed and rustdoc verified in wgpu/cpu/cuda; closure artefacts issued. |
| E6: Evidence, baselines and analytics | Entry evidence verified | Historical r1 merge check exits 0; no campaign data or analysis re-derived. |
| E7: Session cycle and governance traceability | Completed | PSR-038/039 ledger exits 0; append-only status updates, PSR-040 and evidence bundle issued. |
| E8: Performance, benchmarking and reproducibility | Historically verified / suspended | Latest pre-pause nightly green; current-main nightly suspended, downstream reference-host gates remain open. |
| E9: CI/CD and build infrastructure | Local regime verified | Seven workflows disabled; PR-only ruleset active; one online GPU runner. |
| E10: Roadmap, risks and handoff | READY retained | 0159 stays READY; no experiment protocol, run or driver created. |

## 2. Detailed Findings across Audit Dimensions

### E1: Mathematical and Oscillator Dynamics Core Integrity

The accepted EXP-001-r1 E5 report (MichaelMaillet, 2026-09-29 UTC) records all
five hypotheses CONFIRMED and a non-reversal verdict. This audit reads that
governed report; it does not recompute its analyses or inspect EXP-002 results.
EXP-001's original REFUTED results remain immutable.

PSR-039 S2-F3 is still accurate: `GuardPolicy` in
`crates/prin-dynamics/src/integrate.rs` has no `#[non_exhaustive]`; its adoption
remains an API-freeze decision. S2-F4 also remains accurate: the module-level
documentation explicitly preserves the RK45/Exponential/Jacobian clamp
limitation; RK45 uses `GuardPolicy::Bounded`, and the existing regression
tests pin the documented behavior. Neither deferral is silently closed.
The new diff introduces no numerics, tolerance, guard-policy or seed change.

### E2: Codebase and Architecture Conformance

`gpu.rs`'s CUDA export paragraph now uses `cfg_attr(feature = "cuda", doc = ...)`
for links to CUDA-only items and a non-CUDA paragraph without unresolved links.
The original CUDA paragraph is retained, in the original documentation order.
All runtime imports, types, methods and dispatch code are unchanged.

### E3: Test Suite and Parity Corpus

DV-040's regression tests cover four campaign gates in both workflow and local
commands, source-only formatting, retention of existing package gates, and
Bandit's actual file discovery. Relative and absolute path tests distinguish
excluded top-level directories from experiment slugs containing `tests` or
`parity`. The 18 quality-gate tests failed against the old configuration
(13 failed, 5 passed) and pass against the new one; a nineteenth test
pins the `urllib3>=2.8.0` dependency floor (19 passed total).

The full local gate is recorded in section 5 at closure. Existing regression
tests may exercise fake/frozen fixtures as code checks; no campaign driver is
invoked as an experiment and no new `RUN-*` record is created.

### E4: Security and Supply Chain

Snyk MCP was discovered at entry. The repository-wide Snyk Code scan at
`severity_threshold=medium` returned `success=true`, `issueCount=0`; individual
scans of `gpu.rs` and the new test at threshold low also returned zero issues.
No runtime dependencies changed; `pyproject.toml` changes only Bandit's
path matching. A documentation dependency minimum (`urllib3`) was raised
during this audit — see EA007-E-F4 below.
Full-project dependency audits are nevertheless part of this executive gate.

Read-only GitHub queries show native secret scanning enabled with zero alerts,
but native push protection disabled, the pre-existing condition explicitly
flagged by amendment #48. No remote security setting was changed and no claim
that push protection passed is made. Local full-history secret scanning is a
separate required pre-push control, not a replacement claim for native
controls: gitleaks v8.30.1 (pinned, official-checksum-verified,
session-local) scanned all 704 commits / 72.4 MB with `--redact` and found
**no leaks** (exit 0, empty report). This scan ran before any new commit;
a post-commit scan remains required.

**EA007-E-F4 (D2).** The repository-wide Snyk SCA scan (`all_projects=true`,
severity low) flagged `urllib3` 2.7.0 in `DOCS/sphinx/requirements.txt`
under SNYK-PYTHON-URLLIB3-20302844/CVE-2026-97687 (HIGH),
20302845/CVE-2026-97688 (MEDIUM), and 20302846/CVE-2026-97689 (HIGH), all
`fixedIn` 2.8.0. The floor was raised to `urllib3>=2.8.0`, the gate venv
upgraded 2.7.0→2.8.0 with no unrelated packages touched, and a file-scoped
Snyk SCA rescan (`all_projects=false`) plus both `pip-audit` legs
re-verified clean. A regression test pins the floor. **FIXED.**

A separate resolved main-manifest scan flagged five advisories against `torch` 2.14.1 — the
resolved latest pin — via the main-manifest resolved input
(`uv pip compile` + governed audit environment + exact CI command
`snyk test --package-manager=pip --severity-threshold=low --fail-on=all
--policy-path=.snyk`): SNYK-PYTHON-TORCH-10332643, -10337825, -10337826,
-10337834 (MEDIUM) and -15746467 (HIGH). All five are the **pre-existing
approved `.snyk` dispositions of EA-003 finding E-F7** (expires
2026-11-14); with the policy applied the governed command reports *100
dependencies tested, no vulnerable paths found* (exit 0). A repository
search shows none of the affected torch APIs is used
(`torch.cuda.nccl.reduce`, `caching_allocator_delete`, `torch.jit.script`,
`torch.jit.jit_module_from_flatbuffer`, `torch.export.load`/`.pt2`,
`torch.nan_to_num` — zero call sites). No new ignore or disposition was
added.

The repo-wide scan still reports the same urllib3 advisories on copies of
the file inside foreign untracked agent worktrees (`.kilo/`, `.qwen/`) and
a `zod` advisory in `.kilo/package.json`; those are not repository
manifests, so no whole-repo SCA-clean claim is made — the claim is scoped
to the repository manifests and the resolved main-manifest input.

### E5: Standards and Documentation Adherence

DV-042 reproduced exactly: wgpu-only rustdoc with `-D warnings` failed at the
three CUDA-only links (exit 101). After the cfg-gated documentation fix,
exclusive wgpu, CPU and CUDA legs each exit 0; `cargo fmt` exits 0.
The optional hosted workflow doc leg is not added: the bounded fix's local
feature legs provide evidence while Actions remain paused.

The expanded Bandit gate originally exited 0 while scanning **zero lines**:
bare `parity` in `exclude_dirs` also matched both numerical-parity record slugs.
The paired directory-component globs now preserve the existing exclusions
without swallowing similarly named campaign directories. The expanded
package/campaign scan covers 24,864 lines with zero issues.

Ruff format's current default also formats Python fences in Markdown. The
campaign formatting leg positively selects `.py`, `.pyi`, and `.ipynb` source;
it checks both committed analysis modules without rewriting a frozen report's
one-off audit snippet. No finding suppression or new exclusion is introduced.

### E6: Evidence, Baselines and Analytics Integrity

PR #28 carried the EXP-001-r1 E1-E5 range to `main` at
`32cfed8a0b4d915a04e18efbfadd146a2ecb7e32`. The required historical check,
executed read-only on 2026-10-11, exits 0. Verbatim output:

```text
CI-green check — branch 'main', commit 32cfed8a0b4d915a04e18efbfadd146a2ecb7e32
  rust       green     — run 36641713788
  python     green     — run 36641713282
  parity     green     — run 36641713312
  repro      green     — run 36641713284
  snyk       green     — run 36641713362
  gpu        green     — run 36641713384
RESULT: all required workflows green
```

Command: `C:\dev\PRIN\.venv\Scripts\python tools/check_ci_green.py
32cfed8a0b4d915a04e18efbfadd146a2ecb7e32`.
This discharges campaign plan section 12 item 3's **historical entry evidence**,
not current-branch CI validation. The UTF-8 log is preserved under
`EVIDENCE/ea007/exp001-r1-merge-ci-green.log`.

**Packaging note (2026-10-11 UTC):** `.gitattributes` carries
`EVIDENCE/ea007/** -text whitespace=-trailing-space` so the committed blobs
are byte-exact copies of the raw captured logs — the bytes whose SHA-256 is
inventoried in `EVIDENCE/ea007/verification/SHA256SUMS.txt`. Without it, the
`* text=auto eol=lf` default would rewrite Windows CRLF tool output on a
clean checkout and the manifest would not verify. This is raw-output
byte-preservation under the existing `benchmarks/results/**` campaign
precedent, not a source-quality suppression. The `verification/` manifest
was generated before this attribute existed; the staged-log blobs will be
re-staged byte-exact under the new rule.

### E7: Session Cycle and Governance Traceability

Before closure edits, the PSR-038/039 consistency checker exits 0 (128 to 142
rows), the DV gate checker exits 0 (44 rows / 198 session entries), and the
existing global-registration checker exits 0 (17 executive reports).
PSR-040 inherits PSR-039's canonical delta rather than rewriting either
approved historical report. Register status corrections are dated additions.

Maintainer approval, **MichaelMaillet, 2026-10-11 UTC**, verbatim:

> I approve whatever you need to do, you have full access. keep in mind, we are no longer running github hosted checks, that is on pause until further notice. in the meantime we will run local equivequivalent checks. complete your tasks with that in mind.

DV-040 option **(a)** is selected under this approval: extend the record-root
quality gates and their local equivalents. No relocation, campaign section
14.2 amendment, new Plan amendment, or standards change is needed.

### E8: Performance, Benchmarking and Reproducibility

Latest existing nightly: run `36818721762`, attempt 1, started
`2026-10-01T05:13:10Z`, `main` at `bbf97dcef0beadc0bc62b21bb5e27808a92d0bd6`.
Both `full-suite` and `bench-regression` succeeded. The recorded gate states:

```text
Benchmark regression check passed: 69 benchmarks (63 gated, 6 advisory), none gated past +10%; 2 reference and 2 candidate runs.
```

The final log's `step_parallel/*` ratios span 1.018-1.063, and
`sweep_parallel/*` span 0.998-1.045, all below 1.10. These are transcriptions
of retained nightly output, not new measurements. DV-043's historical closure
remains supported. Current `main` is `fdd28d8`, not this nightly SHA: its hosted
nightly is **suspended, not satisfied**, under amendment #48.
DV-043's independent re-audit before 0166 remains scheduled.

DV036-F5 at 0166, DV-036 before 0168/0173, and EXP-004+ hardware gates are
recorded only; none is executed or closed here.

### E9: CI/CD and Build Infrastructure

Read-only API checks confirm `rust`, `python`, `parity`, `repro`, `snyk`, `gpu`,
and `nightly` are `disabled_manually`. `release` and manual `gpu-triton` are
left unchanged. No workflow is dispatched, enabled or re-run.
Ruleset 22150076 is active: PR required, deletion and non-fast-forward
protection retained, no required-status-check rule (amendment #48).

`PRIN-GPU-Runner` is online and idle, but is the **only** registered runner:
DV-034's single-machine SPOF remains open. DV-024's historical service-backed
closure remains supported; no service or power setting was changed.
DV-016 has no new hosted observation while checks are paused; its bounded
self-hosted Rust topology remains unchanged.

DV-033's Codecov upload step still exists on Python's Ubuntu 3.12 leg.
It is the retained hosted per-change path **when checks resume**, not current
authority while disabled. Python 3.14 host coverage availability is assessed
by the local gate; no tooling-version repair is silently assumed.

### E10: Roadmap, Risks and Future Session Handoff

0159 stays READY under the accepted r1 non-reversal result. E1 must carry:
DV-040 option (a) and local-first validation during #48; the historical merge
SHA and verbatim check above; report section 9 item 11's histogram units
(216 comparator records versus 72 per-case worst values); **14 figures, not
15** (two formats plus 11 tables = 39 generated files); `__all__` 175 PRIN
versus 172 reference symbols; `seed_key=2`; and caps **12 h CPU / 2 h GPU /
2 h CI / 10 MiB tracked**. The CI cap is retained, not permission to run
hosted checks during the pause.

## 3. Discovered Deviations and Findings Table

| ID | Severity | Category | Location | Finding | Governing clause | Status |
|---|---|---|---|---|---|---|
| EA007-E-F1 | D3 | Quality-gate coverage | `python.yml`, `AGENTS.md`, Bandit configuration | Campaign analysis roots omitted; bare directory exclusions would make their Bandit extension vacuous. | Coding Standards sections 5-6; campaign section 7.4; DV-040 | FIXED — implemented and locally validated under #48; main delivery pending PR. |
| EA007-E-F2 | D3 | Documentation build | `prin-sim/src/gpu.rs` | Non-CUDA rustdoc resolves links to absent CUDA-only items. | Documentation Standards; Coding Standards section 5; DV-042 | FIXED — exclusive wgpu/cpu/cuda documentation passes; main delivery pending PR. |
| EA007-E-F3 | D4 | Governance currency | Registers and PSR handoff | Historical status prose does not include post-PSR-039 closures and the #48 local regime. | Development Workflow sections 5/8; DV-044 append-only pattern | FIXED — dated deltas, PSR-040, closure indices and evidence bundle issued. |
| EA007-E-F4 | D2 | Dependency advisories | `DOCS/sphinx/requirements.txt` | `urllib3` 2.7.0 doc-build requirement carried three published advisories (CVE-2026-97687/-88/-89) | Coding Standards section 6 | FIXED: floor `>=2.8.0`, venv upgraded, scoped SCA + native rescans clean, regression pin. |

## 4. Remediation Plan

### 4.1 Immediate Remediation

DV-040 option (a), Bandit discovery regression, DV-042 documentation, and
the EA007-E-F4 dependency floor were implemented with checks in tandem. No
campaign analyses or frozen records were reformatted. PSR-040 issued,
register dispositions appended, indices and CHANGELOG updated, and the
verification evidence bundle preserved under
`EVIDENCE/ea007/verification/`. Commit on the named branch remains a
lead-authorized action.

### 4.2 Pass-Forward Items

DV-033/034 retain dated local-regime dispositions; downstream measurement
and hardware gates remain open. S2-F3/S2-F4 remain governed deferrals.
Native push protection remains a flagged external control under #48.
No production-platform, new nightly or EXP-002 evidence is claimed.

## 5. Verification Suite Results

All commands run on Windows (host `HP`), serially for cargo/pytest, with
the required in-repo pytest basetemp and process-local Git Bash PATH.
Raw commands/outputs live in `DOCS/test_and_benchmark_results/ea007/
full-gate/` (index `GATE-STATUS.md`); final evidence is retained
under `EVIDENCE/ea007/verification/`. Linux/macOS and hosted checks are
suspended, not passed.

| Gate | Command | Result |
|---|---|---|
| Lint (expanded roots) | `ruff check python/ tests/ benchmarks/ tools/ parity/ DOCS/experiments/` | exit 0 |
| Format (normal roots) | `ruff format --check python/ tests/ benchmarks/ tools/ parity/` | 322 files, exit 0 |
| Format (campaign source-only) | `ruff format --check DOCS/experiments/ --config 'include = ["*.py", "*.pyi", "*.ipynb"]'` | 2 files, exit 0 |
| Types (package) | `mypy python/prin --strict` | 62 files, exit 0 |
| Types (campaign) | `mypy DOCS/experiments/ --strict` | 2 files, exit 0 |
| Docstring coverage | `interrogate -c pyproject.toml python/prin` | 97.6% ≥ 95.0%, exit 0 |
| SAST | `bandit -r python/prin DOCS/experiments -c pyproject.toml` | 24,864 LOC non-vacuous, 0 issues, exit 0 |
| Rust fmt | `cargo fmt --all -- --check` | exit 0 |
| Clippy | `cargo clippy --workspace --all-targets -- -D warnings` and `--features strict-checks` | both exit 0 |
| Rust tests | `cargo test --workspace`; `--features strict-checks`; `--features cuda` / `--features wgpu` (`--test-threads=1`); `-p prin-kernels --features cpu`; `-p prin-sim --features cpu -- --test-threads=1` | all exit 0 |
| Rust coverage (raw totals) | `cargo llvm-cov -p prin-kernels --features wgpu,cpu` | TOTAL 87.30% regions / 87.18% lines |
| | `cargo llvm-cov -p prin-dynamics` | TOTAL 64.48% regions / 63.59% lines |
| | `cargo llvm-cov -p prin-dynamics --features strict-checks` | TOTAL 64.59% regions / 63.67% lines |
| Workspace docs | `RUSTDOCFLAGS="-D warnings" cargo doc --workspace --no-deps` | exit 0 |
| Docs build | `sphinx.cmd.build -W --keep-going -b html` (fresh output dir) | exit 0, 0 warnings |
| Python dependency audit | `pip_audit .` and `-r DOCS/sphinx/requirements.txt` (pre- and post-E-F4) | no known vulnerabilities, exit 0 |
| Rust dependency audit | `cargo audit` | 0 vulnerabilities; 3 allowed warnings (bincode/paste unmaintained, chacha20 yanked) |
| Snyk Code | repo `medium`; `gpu.rs`, `test_campaign_quality_gates.py` `low` | issueCount=0 each |
| Snyk SCA (doc manifest) | file-scoped `DOCS/sphinx/requirements.txt`, low | issueCount=0 post-E-F4 |
| Snyk SCA (main manifest, exact CI form) | `snyk test --file=<resolved> --package-manager=pip --severity-threshold=low --fail-on=all --policy-path=.snyk` | 100 dependencies, no vulnerable paths, exit 0 (EA003-E-F7 dispositions applied) |
| Secret scan | `gitleaks git --redact` v8.30.1 pinned, checksum-verified | 704 commits / 72.4 MB, no leaks, exit 0 |
| Governance | `wp001_baseline.py check`; `check_global_session_registration.py`; `check_dv_register_gates.py`; `check_deviation_ledger.py 039→040` | all exit 0 (18 EA reports; 44 rows; 142→146 ledger rows) |
| New gate tests | `pytest tests/test_campaign_quality_gates.py` | 19 passed, exit 0 |
| **Full Python suite** | `pytest tests/ parity/` (90-minute bound, faulthandler 300s) | **PASS — 5,667 passed / 184 skipped / 0 failed / 61 warnings in 1,782.21 s, exit 0.** Two prior 30-minute attempts exhausted their imposed bounds at different nodes with zero failures; isolated reproduction of the last nodes passes; one faulthandler dump showed genuine training compute in `hierarchical_layers.py:387` (test passed in 335.58 s) — the final pass, stack and isolated cases rule out a reproduced hang; the earlier mechanism beyond the exhausted bound is not established |
| Full `pytest --cov` | coverage-mode run (30-minute bound) | **BLOCKED — DV-033.** The bound was exhausted at ~60 % with zero failures; location recorded, mechanism not established |

The 61 pytest warnings are the existing classes — TorchScript/
`torch.jit.script_method` and legacy TorchScript ONNX export
deprecations, `torch.cuda.amp.GradScaler` deprecation, Dynamo tracing
limitations, stevedore `verify_requirements` deprecation, profiler
cycle/warmup notices, the Windows Proactor/ZMQ notebook notice, and
NumPy interoperability warnings. No warning was suppressed by this diff.

Raw coverage values are recorded as measured totals, **not** as ≥95%
claims: no new instrumented Rust production lines were added by this diff
(docs/config/dependency/test-only), so per-change coverage is N/A; the
Python per-change coverage path (DV-033) remains **open** — Rust coverage
is separate and does not close it.

## 6. Audit Verdict and Sign-off

**Final verdict:** `PASS-WITH-REMEDIATION` — local session closure. Findings
EA007-E-F1..F4 all FIXED with local evidence; zero unresolved D1/D2.
Standing items DV-033/DV-034, the downstream gates, and the #48
platform/push-protection flags are retained, not closed.
Main delivery via PR is pending — no merge-to-main or current hosted CI
green is claimed, and no new maintainer report acceptance is inferred.
**Auditor:** Devin (AI pair of record), 2026-10-11 UTC.
**0159:** READY; not started by EA-007.

## 7. Post-review errata (PR #32 review round, 2026-10-11 UTC)

Appended under the append-only rule for committed audits
(`DOCS/audits/README.md`); the report body above is unchanged. Each erratum
quotes the statement it supersedes and points at the finding in
`DOCS/audits/PR032-multi-review-audit.md`, which re-derived every PR #32 review
claim from the repository. **None changes this report's verdict, any EA007
finding, or its zero-unresolved-D1/D2 count.**

| ID | Supersedes | Correction |
|---|---|---|
| ER-1 (`PR32-F2`) | §2 E4: "scanned all 704 commits / 72.4 MB … This scan ran before any new commit; a post-commit scan remains required." and the §5 *Secret scan* row | The 704-commit result is the **historical** scan of base `fdd28d88` and stands. The required post-commit scans were run and are now committed verbatim in `EVIDENCE/ea007/verification/post-commit/`: **706 commits @ `0738714`** and **707 commits @ `add7386a`** (2026-10-11T06:47:37Z, 76.07 MB, no leaks, exit 0; 704 + the PR's 3 commits). Each result is about the commit it names; a later commit needs its own scan (`PR032-multi-review-audit.md` §6). |
| ER-2 (`PR32-F11`) | §2 E3: "The 18 quality-gate tests failed against the old configuration (13 failed, 5 passed)" | Thirteen of the 18 quality-gate tests failed and five passed against the old configuration (`dv040-newtests-oldconfig.log`: `13 failed, 5 passed`); the nineteenth test (the `urllib3` floor) has no old-configuration leg. |
| ER-3 (`PR32-F11`, `PR32-F7`) | §2 E6 packaging note: "the staged-log blobs will be re-staged byte-exact under the new rule" | Done in `add7386` (38 pure end-of-line rewrites, 13,420 insertions / 13,420 deletions); the head verifies 82/82 against `SHA256SUMS.txt`. History is not rewritten: at `0738714` 36 of the 82 entries did not match, because the `.gitattributes` rule landed in the same commit as the files it protects. |
| ER-4 (`PR32-F6`) | §5 intro: "Raw commands/outputs live in `DOCS/test_and_benchmark_results/ea007/full-gate/` (index `GATE-STATUS.md`)" | That tree is gitignored and local to the maintainer workstation. The **committed** record is `EVIDENCE/ea007/verification/` (index `full-gate/GATE-STATUS.md`, inventory `SHA256SUMS.txt`). |
| ER-5 (`PR32-F8`, `PR32-F9`) | §2 E5: "The optional hosted workflow doc leg is not added …" and the §5 *Workspace docs* row (`cargo doc --workspace --no-deps`, exit 0) | The workspace leg cannot document `prin_sim::gpu` (`#[cfg(any(cpu, cuda, wgpu))]`, `default = []`) and exited 0 at the defective base (`full-gate/24-rustdoc-workspace.log`), so it is not evidence for DV-042; the three feature legs are. Review of PR #32 reversed the "not added" decision as a root-cause fix: `rust.yml` and the `AGENTS.md` local gate gain `cargo doc -p prin-sim --no-deps --features cpu` (hosted run not performed — paused under #48). |
| ER-6 (`PR32-F3`) | `full-gate/GATE-STATUS.md` leg 19 ("142 → 146 rows after E-F4 append") and leg 22 ("274 pins") | The index cells were corrected in place against their logs (leg 19 log: 142 → 145; the final 146 is leg 26a; leg 22: 100 pinned packages in a 274-line resolved manifest) and `SHA256SUMS.txt` regenerated in the same commit. This report's own "142→146" and "100 dependencies" figures were already correct. |
