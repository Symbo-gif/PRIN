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
| DV036-F3 | D2 | First hosted run of the corrected job (dispatch `35810787820`) failed in "Build matched candidate and reference environments": `--no-build-isolation` editable installs spawn the `maturin` CLI from the PEP 517 hook, but neither venv's `bin/` was on PATH (`FileNotFoundError: 'maturin'`). | FIXED post-S4-documentation by venv activation before each editable install, plus ordering assertions in `test_nightly_uses_fresh_same_job_reference_and_preserves_gate`; re-dispatch pending. |
| DV036-F4 | D2 | The approved single reference-first pass with a nested `.nightly-reference` checkout is not a like-for-like comparison: identical binaries read a reproducible +14.5%, and hosted-runner contention/µs noise exceeds 10% for identical code (runs `35811372090`, `35826531821`). | AMENDED by campaign amendment 4 (maintainer-selected): equal-length sibling arms, counterbalanced ABBA order with per-arm mean, contention group advisory on hosted runners. Hosted confirmation pending. |
| DV036-F5 | D3 | `crates/prin-daemon/benches/control_buffer.rs` shadows the lock-free `_guard` with the mutex one, so the lock-free writers keep spinning while `mutex/N` is measured (2N writers, not N). | DEFERRED to EXP-003 E3 (0166): fixing it now would make the fixed-reference comparison compare different harnesses; fix lands with the reference-host CPU re-baseline, where this group gates. |

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

## Hosted validation round 1 — DV036-F3

Branch nightly dispatch `35810787820` (workflow on
`hotfix/dv036-nightly-comparable-baseline`) exercised the corrected job
end-to-end for the first time. `bench-regression` failed in the environment
build step before any measurement: the `--no-build-isolation` editable
install ran `maturin`'s PEP 517 hook, which spawns the `maturin` binary, but
the step invoked `.venv/bin/python` without putting `.venv/bin` on PATH.
The uploaded evidence artefact preserved the failure exactly as designed.

Fix: `source` each venv before its own editable install (candidate `.venv`,
then reference `.nightly-reference/.venv`), matching the `full-suite` job's
activation pattern; measurement arms were already activating correctly.
Ordering assertions added to the workflow-contract test. Focused suite
49/49, Ruff/format/strict mypy/YAML parse/actionlint v1.7.7 clean. The 10%
threshold, benchmark selection, reference SHA, and fail-closed checker are
unchanged. A further hosted run is required; this entry is not a green
certificate.

## Hosted validation round 2 — DV036-F4 / DV036-F5

Branch dispatch `35811372090` (`e5866f7`) and main nightly `35826531821`
(`de411d0`, after PR #21) both reached the comparison; `full-suite` passed
in each. Breaches: run `35826531821` — `control_buffer_read_under_contention/mutex/4`
+25.2%, `resonance_layer_bridge_baseline/moderate_128osc_64dims_32batch`
+14.7%, DLPack `test_negate_round_trip_latency[float64]` +18.4%; run
`35811372090` — `lock_free/4` +12.2%, the same resonance case +14.4%.
Both evidence artefacts were downloaded and analysed; no run was retried.

| Evidence | Result |
|---|---|
| Whole-population ratio (69 ids) | median 0.998 / 1.001; no global order bias |
| Identical-code A/A across the two runs (reference vs reference; candidate `e5866f7` vs `de411d0`, which differ only in `nightly.yml`) | contention group 0.39×–1.46×; DLPack float64 0.79×; resonance moderate 1.008× / 1.005× |
| Resonance source and build inputs | `git diff 4590d61 de411d0 -- crates Cargo.lock` touches READMEs only; identical Criterion binary hashes (`resonance_layer_bridge-c0d1e0d33f085338`) in both arms |
| Same computation through `prin-py` in the same jobs | 0.923× and 0.985× (not slower) |
| Local interleaved A/B, both SHAs as equal-length sibling worktrees (Windows, `cargo +1.98.1 bench -p prin-train --bench resonance_layer_bridge`, 20 samples) | ref 385.2 ms, cand 386.0 ms, ref 414.3 ms, cand 411.1 ms — ratios 1.002× / 0.992×; ~7.5% drift for both arms between rounds; executables equal size, 19 differing bytes (PDB path/stamp) |
| DLPack float64 candidate, run `35826531821` | median moved with the mean (9.67 µs vs 8.07 µs) while the minimum stayed within 2% — transient host phase |

Conclusion: none of the breaches is attributable to candidate code. The
design itself was not like-for-like (DV036-F4); DV036-F5 is a harness defect
in the contention benchmark. MichaelMaillet selected the correction recorded
as campaign amendment 4. It keeps the fixed reference, matched dependencies,
all eight Rust targets, the Python selection, the 10% threshold, and
fail-closed inputs.

Implementation: `nightly.yml` checks out `arms/candidate` and
`arms/reference`, then measures `reference-1`, `candidate-1`, `candidate-2`,
`reference-2`, preserving every pass. `tools/check_bench_regression.py` now
takes `--reference RUN...` / `--candidate RUN...`, averages each arm over
its runs (identities must match across every run), prints every
benchmark's ratio, and treats `--advisory` prefixes as reported but not
gating. A blank prefix, or one that matches no benchmark, is an input error
(exit 2).

Local verification: `pytest tests/test_check_bench_regression.py` 58 passed;
checker 100% line coverage (121/121). Mutation check against the pre-change
checker and workflow: 57 failed / 1 passed; the pass is the unchanged pytest
`name` fallback test. Ruff check/format, `mypy --strict`, Bandit, YAML
parse, and actionlint v1.7.7 are clean. Snyk Code (`--severity-threshold=low`)
reports 0 issues in the changed files; the 8 LOW repository findings are all
in untouched files. No dependency manifest changed. Smoke test on the real
`35826531821` evidence parses all 69 ids and marks the six contention ids
advisory. A hosted ABBA run is required, and this entry is not a green
certificate.
