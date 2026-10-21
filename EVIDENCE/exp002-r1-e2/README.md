# EVIDENCE/exp002-r1-e2/ — Verification evidence for `EXP-002-r1` E2

**Stage:** `EXP-002-r1-E2` (Independent Review, Approval Decision, and S4 Retro-Audit, track C1).<br>
**Date:** 2026-10-21 UTC.<br>
**Branch:** `campaign/exp002-r1-e2` (branched from PR #36 head `bdaae83f2f384fba3c8d33013c40c6a2f4f011b5`, entry `origin/main` baseline `M = 5677858c15d784d881b23d43dff5029d199b0a18`, post-merge `origin/main` baseline `M' = 313a76f649d8e00f82959521eb7d5eaee2e409bd`).<br>
**Experiment record:** [`DOCS/experiments/EXP-002-r1-api-benchmark-result-and-reproduction-parity/`](../../DOCS/experiments/EXP-002-r1-api-benchmark-result-and-reproduction-parity/README.md).<br>
**Independent E2 review & S4 retro-audit:** [`DOCS/experiments/EXP-002-r1-api-benchmark-result-and-reproduction-parity/e2-review.md`](../../DOCS/experiments/EXP-002-r1-api-benchmark-result-and-reproduction-parity/e2-review.md).

Under the **Re-run (`-r1`/`-rN`) Namespace & Evidence Isolation Rule** (campaign
plan §7.1, §7.5, §8, amendment #10), all stage verification evidence for
`EXP-002-r1` E2 lives in this dedicated `EVIDENCE/exp002-r1-e2/` directory and
never modifies `EVIDENCE/0159/`..`0163/`, `EVIDENCE/exp002-d1-s1/`..`s4/`, or
`EVIDENCE/exp002-r1-e1/`.

Verify this bundle with:

```powershell
.venv\Scripts\python.exe -I EVIDENCE/exp002-d1-s3/index_selfcheck.py exp002-r1-e2
```

## Indexed files

| File | Description |
|---|---|
| [`README.md`](README.md) | This evidence index |
| [`entry-origin-main.txt`](entry-origin-main.txt) | Entry verification of `origin/main` (`5677858c15d784d881b23d43dff5029d199b0a18`) and PR #36 (`campaign/exp002-r1-e1`, head `bdaae83f2f384fba3c8d33013c40c6a2f4f011b5`, `OPEN` / unmerged at entry) |
| [`check-ci-green-5677858c.txt`](check-ci-green-5677858c.txt) | Verbatim output of `.venv\Scripts\python.exe tools/check_ci_green.py 5677858c15d784d881b23d43dff5029d199b0a18` on `main` (`RESULT: all required workflows green`, exit `0`) |
| [`check-ci-green-bdaae83f.txt`](check-ci-green-bdaae83f.txt) | Verbatim output of `.venv\Scripts\python.exe tools/check_ci_green.py bdaae83f2f384fba3c8d33013c40c6a2f4f011b5 --branch campaign/exp002-r1-e1 --limit 100` (`RESULT: all required workflows green`, exit `0`) |
| [`check-ci-green-313a76f6.txt`](check-ci-green-313a76f6.txt) | Verbatim output of `.venv\Scripts\python.exe tools/check_ci_green.py 313a76f649d8e00f82959521eb7d5eaee2e409bd` on `main` (`M'` after PR #36 merge; `RESULT: all required workflows green`, exit `0`) |
| [`hosted-pr36-statuscheckrollup.txt`](hosted-pr36-statuscheckrollup.txt) | Verbatim `gh pr view 36 --json number,state,headRefName,headRefOid,baseRefName,mergeable,statusCheckRollup` output confirming `32` status entries (`29` `SUCCESS` CheckRuns, `1` `SKIPPED` CheckRun `Sourcery review`, and `2` `SUCCESS` StatusContexts `CodeRabbit` and `Devin Review`) on `bdaae83f2f384fba3c8d33013c40c6a2f4f011b5` |
| [`hosted-runs-verbatim.txt`](hosted-runs-verbatim.txt) | Verbatim `gh run view --json` records for all 7 workflow runs on `bdaae83f2f384fba3c8d33013c40c6a2f4f011b5`: `39496143063` (`python`), `39496143045` (`rust`), `39496143042` (`parity`), `39496143041` (`repro`), `39496143047` (`gpu`), `39496132811` (`snyk`, `push`), and `39496143043` (`snyk`, `pull_request`) |
| [`e1-range-scope.txt`](e1-range-scope.txt) | `git log --oneline` and `git diff --name-status` over `5677858c15d784d881b23d43dff5029d199b0a18..bdaae83f2f384fba3c8d33013c40c6a2f4f011b5` (`23 files changed, 7386 insertions(+), 125 deletions(-)`) |
| [`predecessor-immutability.txt`](predecessor-immutability.txt) | Proof that `git diff 5677858c15d784d881b23d43dff5029d199b0a18 HEAD` across all frozen `EXP-002`, `0159`–`0163`, and `exp002-d1-s1`–`s4` roots is empty |
| [`e1-digests-recomputed.txt`](e1-digests-recomputed.txt) | Independent recomputation of all 19 byte sizes and SHA-256 digests in `EVIDENCE/exp002-r1-e1/provenance-hashes.txt` from E1 review-subject disk bytes (`ROWS=19 MISMATCHES=0`) |
| [`live-environment-and-pins.txt`](live-environment-and-pins.txt) | Independent verification of live `prin`/`_prin_core` version and origin, `_verify_all_pins()`, `_environment_shadowing()`, 172 legacy / 175 expected API symbols, and non-existence of `EXP-002-r1` run/output directories |
| [`focused-suite-coverage.txt`](focused-suite-coverage.txt) | Verbatim output of `.venv\Scripts\python.exe -m pytest tests/test_exp002_r1_driver.py --cov=benchmarks.campaign.exp002_r1_driver --cov-report=term-missing --basetemp=.pytest_basetemp -o faulthandler_timeout=300 -q` at E2 entry (`343 passed, 1 skipped in 10.29s`, `98%` line coverage, exit `0`) |
| [`host-pin-test.txt`](host-pin-test.txt) | Verbatim output of the opt-in registered-host binary-pin test run with `PRIN_EXP002_R1_HOST_PIN=1` at E2 entry on this governed Windows host (`4 passed, 340 deselected in 2.28s`, exit `0`) |
| [`cargo-audit.txt`](cargo-audit.txt) | Verbatim `cargo audit` output confirming `0` vulnerabilities (`3` allowed warnings: `bincode`, `paste`, `chacha20`, exit `0`) after PR #36's minimal `Cargo.lock` bump |
| [`gitattributes-and-ignore.txt`](gitattributes-and-ignore.txt) | Inspection of `.gitattributes`, `git check-attr -a`, and `git check-ignore -v` confirming `-text whitespace=-trailing-space` on `EVIDENCE/exp002-r1-e*/**` and `benchmarks/results/**` and `.gitignore` coverage of `DOCS/test_and_benchmark_results/EXP-002-r1/**` |
| [`input-manifest-finalization-probe.txt`](input-manifest-finalization-probe.txt) | Synthetic read-only probe at E2 entry (`bdaae83f2f384fba3c8d33013c40c6a2f4f011b5`) backing observation `E2-OBS-1`, resolved in code by `PR37-F1` (`pr37-remediation.txt`) |
| [`kilo-sca-finding-context.txt`](kilo-sca-finding-context.txt) | Verification that `.kilo/package-lock.json` is an untracked, gitignored local agent-tooling file outside PRIN's tracked repository (`E2-OBS-3`) |
| [`retro-s4f2-814b670c.txt`](retro-s4f2-814b670c.txt) | Verbatim `git show 814b670c2aafa4b1e6b58e3f847613928c813e95 -- parity/test_parity_publication.py` diff for the `EXP002D1-S4-F2` retro-audit |
| [`retro-s4f2-pytest.txt`](retro-s4f2-pytest.txt) | Verbatim output of `.venv\Scripts\python.exe -m pytest parity/test_parity_publication.py --basetemp=.pytest_basetemp -o faulthandler_timeout=300 -q -rs` (`94 passed in 12.60s`, exit `0`) |
| [`retro-s4f3-diffs.txt`](retro-s4f3-diffs.txt) | Verbatim `git show 67100a698469307da52956698f504df5251e5b0b` and `git diff 305416fb0f85e690b12640b3f32fad48b55d9077..5677858c15d784d881b23d43dff5029d199b0a18` across `tests/test_acceptance_subconscious.py`, `benchmarks/y4q1_5_benchmarks.py`, `tests/test_acceptance_y4q1_5.py`, and `tests/conftest.py` for the `EXP002D1-S4-F3` / PR #35 retro-audit |
| [`retro-s4f3-pytest.txt`](retro-s4f3-pytest.txt) | Verbatim output of `.venv\Scripts\python.exe -m pytest tests/test_acceptance_subconscious.py tests/test_acceptance_y4q1_5.py -k "test_no_gpu_throughput_regression or TestSessionRunnerSmoke" --basetemp=.pytest_basetemp -o faulthandler_timeout=300 -v -rs` (`8 passed, 104 deselected, 2 warnings in 28.91s`, exit `0`) |
| [`pr37-remediation.txt`](pr37-remediation.txt) | Post-remediation verification for PR #37 findings (`PR37-F1`..`PR37-F6`): updated file digests, `100.00%` (`47/47`) docstring coverage on `exp002_r1_driver.py`, `346 passed, 1 skipped` (`98%` coverage), and `7 passed` under `PRIN_EXP002_R1_HOST_PIN=1` including `INPUT_MANIFEST` admission and mid-collection mutation tests |
| [`verification-gate.txt`](verification-gate.txt) | Authoritative local verification and security gate record for E2 (`ruff`, `mypy --strict`, `interrogate`, `bandit`, governance checkers, clean Sphinx `-W` HTML build, `gitleaks`, and `index_selfcheck.py`) |
| [`SHA256SUMS.txt`](SHA256SUMS.txt) | SHA-256 digests of the evidence files in this directory |
