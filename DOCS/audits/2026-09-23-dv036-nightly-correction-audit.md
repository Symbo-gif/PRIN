# DV-036 nightly comparison correction audit

**Date:** 2026-09-23 UTC
**Auditor:** Devin (AI pair); maintainer acceptance remains a separate action.
**Scope:** Conditional DV-036 S2; implementation commit `8bcea55`.
**Blocked session:** 0156 (EXP-001 E3).
**Verdict:** PASS for the local correction audit; hosted correction validation
and S4 closure remain pending. This is not a green-nightly certificate.

## A1–A10 review

| Check | Result | Evidence |
|---|---|---|
| A1 Scope | PASS | Workflow/checker/tests plus governance only; no numerical core or EXP-001 driver change. |
| A2 Architecture/method | PASS | Campaign §11.6 / amendment 3 approved fixed reference `4590d611f34eae5dfcdadb99b562aacf998d6e94`, measured before candidate on one host; same frozen dependencies; unchanged eight Rust targets, Python benchmark selection, and 10% threshold. No cached timing promotion. |
| A3 Tests | PASS | Original checker: 37 failed / 8 passed. Corrected tests: 49 passed; checker 100% line coverage (96/96 statements). Full local fast suite: 3166 passed / 176 skipped / 48 deselected after documented invocation correction. |
| A4 Numerical parity | UNAFFECTED | No oscillator, metric, kernel, tolerance or EXP-001 hypothesis/sample change; workspace tests including existing parity tests passed. No campaign parity claim is made. |
| A5 Quality | PASS | fmt, workspace Clippy, tests, warnings-denied rustdoc; repository Ruff (310 files), package strict mypy (62 files), checker strict mypy; Bash syntax and actionlint v1.7.7 clean. |
| A6 Security | PASS locally | Snyk Code at low threshold: checker and tests zero issues; Bandit zero issues; project/docs pip-audit no known vulnerabilities; cargo audit only the existing bincode/paste/chacha20 governed warnings. No manifest or suppression change. Hosted secret control remains independent. |
| A7 Documentation | PASS locally | Checker helpers and error have docstrings; package interrogate 97.6%. No public package API or Sphinx source changed. Final directory/report updates belong to S4. |
| A8 Hygiene | PASS | Diff limited to declared correction, no unintended tracked output; git diff --check clean; DV-register and wp001 baseline checks passed. |
| A9 CI | PENDING | Original nightly `35804529743` failed at main `e9974318b2d1ced3beb7506ca217dbb92864158e`; corrected branch nightly and required workflows have not yet run. Local evidence cannot close this gate. |
| A10 Trail | PASS | E3 log preserves original failure and maintainer approvals; campaign amendment and four conditional briefs are versioned. No RUN directory created. |

## Findings and disposition

| ID | Severity | Finding | Disposition |
|---|---|---|---|
| DV036-F1 | D2 | Cross-host cached timings remained from 2026-09-16 despite later refresh steps; not a controlled same-host comparison. | Implementation addressed by `8bcea55`; live validation pending. |
| DV036-F2 | D2 | Missing/malformed/non-finite, duplicate or unmatched measurement data could pass the old checker. | FIXED by `8bcea55`; fail-closed regression tests and 100% line coverage. |

No additional source finding arose in S2. GitHub expression scope was corrected
before the S1 commit, then checked by both a regression assertion and real
actionlint. The audit does not claim that all old slowdowns were caused by
hardware variance: logs establish stale cross-run evidence reuse, not the
physical cause of each measured difference.

## Verification record

Focused checks:

```powershell
.venv\Scripts\ruff check tools/check_bench_regression.py tests/test_check_bench_regression.py
.venv\Scripts\mypy tools/check_bench_regression.py --strict
.venv\Scripts\python -m pytest tests/test_check_bench_regression.py --cov=tools.check_bench_regression --cov-report=term-missing --cov-fail-under=95 --basetemp=.pytest_basetemp_dv036_green
.venv\Scripts\python -m bandit tools/check_bench_regression.py
go run github.com/rhysd/actionlint/cmd/actionlint@v1.7.7 -shellcheck= -pyflakes= .github/workflows/nightly.yml
```

The initial full pytest command used `.pytest_basetemp_dv036_localgate` and
resolved a nonworking WSL bash relay, causing 15 failures. Its result is
retained in the E3 log. The corrected full command passed:

```powershell
$env:PATH = 'C:\Program Files\Git\bin;' + $env:PATH
.venv\Scripts\python -m pytest tests/ -m "not slow and not gpu" --basetemp=.pytest_basetemp
```

Full local checks executed once apart from that corrected pytest invocation:

```powershell
cargo fmt --all -- --check
cargo clippy --workspace --all-targets -- -D warnings
cargo test --workspace
$env:RUSTDOCFLAGS='-D warnings'; cargo doc --workspace --no-deps
.venv\Scripts\ruff check python/ tests/ benchmarks/ tools/ parity/
.venv\Scripts\ruff format --check python/ tests/ benchmarks/ tools/ parity/
.venv\Scripts\mypy python/prin --strict
.venv\Scripts\python -m interrogate -c pyproject.toml python/prin
.venv\Scripts\python -m bandit -r python/prin -c pyproject.toml
cargo audit
.venv\Scripts\python -m pip_audit .
.venv\Scripts\python -m pip_audit -r DOCS/sphinx/requirements.txt
.venv\Scripts\python tools/check_dv_register_gates.py
.venv\Scripts\python tools/wp001_baseline.py check
```

## Required next stages

S3 must record the mandatory no-change delta verification even though S2 found
no additional source defect. S4 must update directory indexes, status and
ledger records, push the authorized hotfix branch, and collect the corrected
nightly and required-check evidence. No merge is authorized by this audit.
Session 0156 stays blocked until the correction closes and all entry conditions
are met. DV-036's separate reference-host EXP-003/004 re-baseline obligations
remain open regardless of this CI repair.

## S3 — no-change delta verification

**Date:** 2026-09-23 UTC. S2 commit: `e09b7f5`.

S2 raised no additional source finding; S3 is nevertheless executed, not
skipped. `git diff 8bcea55 HEAD -- .github/workflows/nightly.yml
tools/check_bench_regression.py tests/test_check_bench_regression.py` returned
no changes. The audited implementation is identical to the locally validated
S1 source; no repeated test pass is represented as new independent evidence.

| Finding | Local disposition | Remaining obligation |
|---|---|---|
| DV036-F1 | AMENDED / implemented under campaign §11.6, amendment 3, commit `8bcea55` | Corrected hosted comparison and required CI; S4 stays open until evidence permits closure. |
| DV036-F2 | FIXED, commit `8bcea55` | Covered by the accepted fail-closed tests and Snyk Code scan. |

**Delta re-audit:** CLEAN at local scope. No new code change required.
This is not closure of DV-036's campaign re-baseline obligations, not a claim
of hosted success, and not authorization to start session 0156.
