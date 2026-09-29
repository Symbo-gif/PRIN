# EXP-001-r1 E1 — Entry evidence and handoff

**Session:** `EXP-001-r1-E1`, maintainer-declared; pre-registration only.<br>
**Date:** 2026-09-28 UTC. **AI pair:** Devin.<br>
**Deliverable:** a committed DRAFT for independent E2 review, not execution
approval or an experiment result.<br>
**Branch:** `campaign/exp001-r1-e1`.<br>
**Protocol:** [`preregistration.md`](preregistration.md).

## Entry and authority

The maintainer explicitly declared this E1 session against the re-run
[README](README.md). Its authority is campaign plan §10.4 item 4 and the
correction S4 authorization. The original numbered sessions and their
immutable experiment record are not reused.

The governing records read for this session were:

- `DOCS/PRIN_Project_Plan.md`, particularly F2, §4, §5, §6, §8 and
  amendment #47.
- Experimentation, Benchmarking and Reproducibility, Coding, Testing,
  Documentation, and Development Workflow and Audit Standards.
- The experiment-session workflow, active re-run README, campaign plan,
  pre-registration template and predecessor experiment record.
- PSR-039 and its deviation ledger, the Deferred Validation Register and
  the complete EXP-001 D1 correction audit.
- The correction's current evidence index, current corpus/driver/parity
  code, relevant CI and repository agent instructions.

The investigation used repository code to verify the corrected default,
the native and corrected reference paths, 504-case corpus, fixed fuzz stream,
22 sensitivity indices, CUDA residency proof and current publication APIs.
The retired `.vibecheck` material was not used. Archived documents were not
used as current governance. The importable, pinned PRINet 3.0 implementation
remains the experiment's explicit comparison baseline.

## Correction merge and CI

The session began at clean hotfix-branch HEAD
`3c0f584032b73ad7337d44d65ab1b93e203105e7`. GitHub reports PR #24 merged as
`149cf2d88ab6be401951b63d1d7e8fad209f52a5` at **2026-09-28T00:05:52Z**:

```text
gh pr view 24 --json state,mergedAt,mergeCommit,url,headRefOid
state: MERGED
mergedAt: 2026-09-28T00:05:52Z
mergeCommit: 149cf2d88ab6be401951b63d1d7e8fad209f52a5
headRefOid: 7235ae62aa700b2345b650ed6a8711429e56a4ed
url: https://github.com/Symbo-gif/PRIN/pull/24
```

The correction's S2–S4 documentation was present on the local hotfix branch
after the source head carried by PR #24. The new E1 branch retains those
commits and merges `origin/main` locally at
`a7ef308acffbf3ecd09aa1b4fbe55a9b09d09e74`. That merge changed no source
content. No older branch, published record or raw artefact was reset.

Campaign plan §12 item 3 / correction S4 item 7 evidence, checked during E1:

```text
.venv\Scripts\python.exe tools/check_ci_green.py 149cf2d88ab6be401951b63d1d7e8fad209f52a5
CI-green check — branch 'main', commit 149cf2d88ab6be401951b63d1d7e8fad209f52a5
  rust       green     — run 36360903237
  python     green     — run 36360903152
  parity     green     — run 36360903194
  repro      green     — run 36360903218
  snyk       green     — run 36360903391
  gpu        green     — run 36360903234
RESULT: all required workflows green
```

The checker exited 0. The terminal's display encoding rendered the dash
glyph inconsistently; the workflow names, statuses, SHA and run IDs above
are the command's output values.

The latest completed main nightly at this entry check was
[`36296497434`](https://github.com/Symbo-gif/PRIN/actions/runs/36296497434),
`success`, at `ce4049f36df629d074dadfee3381ccf7ca6b08f8`. It is prior nightly
evidence, not a nightly run of the correction merge or the new E1 commit.
E3 must recheck the then-current main/nightly entry conditions.

These results close the outstanding **merge-CI evidence** obligation. They
do not make the unpushed E1 driver CI-validated, approve the new protocol or
release 0159.

## Protocol decisions

The draft and driver adopt the following prospective choices:

1. Preserve every native comparison. A DV-007 explanation additionally
   requires PRIN to match the cast-only float64 reference at the original
   tolerance; no wider trajectory bound and no regenerated replacement
   corpus.
2. Keep exactly 22 named sensitivity cases outside the pointwise stratum,
   re-prove the reference-only one-ulp witness every time, validate PRIN's
   outputs, and retain their residuals and H2b contributions.
3. Retain the exact 1,000-input `Seed(0,1)` stream. Pin the complete input
   fingerprint before any integration and retain per-case parameters and
   input digests.
4. Define H3's 14 representatives from manifest metadata before execution,
   and require separately manifested repeat runs with array digests.
5. Use a three-way H2b interval decision. A CI overlapping an equivalence
   boundary is inconclusive; only a CI wholly outside it refutes. Derive
   the bootstrap seed through the registered `Seed`, and scope the claim
   to ensemble mean coherence rather than a full distribution or a
   phase-boundary conclusion.
6. Keep the required wgpu coverage and budget decisions explicit for E2.
   CUDA capsules cannot prove wgpu execution. The original raw files count
   toward the shared allocation, and its old fuzz waiver is not silently
   extended.

None of these choices edits or re-adjudicates the predecessor's frozen
hypotheses, thresholds, results or verdicts.

## Input-only checks

These checks read metadata/bytes or deterministic seed configuration;
they did not integrate any registered case or inspect new trajectory output:

| Check | Result |
|---|---|
| Corpus manifest | 504 unique case records; 14 valid model/coupling/integrator cells; Kuramoto 216, Hopf 216, Stuart–Landau 72 |
| CUDA selection | 72 manifest records with `model=kuramoto`, `coupling=sparse_knn` |
| H3 selection | Lexicographically first case ID in each of the 14 cells, enumerated in the draft and driver |
| Bootstrap seed | Fresh `_prin_core.Seed(0,1).next_u64()` = `12455822396014146421` |
| Corpus, reference, instrument and prior-evidence hashes | Exact values recorded in pre-registration §§5.1 and 5.3 |
| Live provenance-only preflight | `exp001_r1_driver.preflight("corpus", Path("parity/corpus"))` passed the real manifest, source/instrument hashes, cast-only AST and default-guard checks; it performs no integration |
| Existing EXP-001 raw-file size | `6,208,871` bytes, including each original result, sidecar and manifest |
| Existing campaign raw-file size | `6,208,871` bytes; no other experiment has a raw run directory |
| Remaining inherited shared allocation | `8,388,608 - 6,208,871 = 2,179,737` bytes |

Storage was counted from existing `EXP-*/RUN-*/*` regular-file sizes, not
from result values. The 16 MiB shared / 8 MiB new-r1 allocation and 6 MiB
new-fuzz allowance in the draft are requests awaiting a campaign §14.2
approval. No campaign budget or standard was amended in E1.

## Driver validation

Validation is of experiment **machinery**, using explicit synthetic arrays
and mocked numerical runners. It is not a pilot or a confirmatory run.

| Targeted validation | Result |
|---|---|
| Shared closure contract and explicit experiment identity | 67 passed, 147 deselected; only closure/envelope/identity tests selected |
| New r1 synthetic suite | 56 passed |
| New driver's executable-line coverage | 274/275 lines, 99.64%; the one uncovered line (261) is the defensive missing-one-ulp-reference exception |
| New driver's docstring coverage | 100%, 23/23 callables |
| Ruff on the two drivers and their tests | Clean |
| Strict mypy on the r1 driver | Clean |
| Bandit on the r1 driver | No issues |
| Deferred-validation register gate | Passed, 40 DV rows and 198 integer session entries |

Commands:

```powershell
.venv\Scripts\python.exe -m pytest tests/test_exp001_driver.py -k "RunClosure or Closure or explicit_experiment_identity" --basetemp=.pytest_basetemp -q
.venv\Scripts\python.exe -m pytest tests/test_exp001_r1_driver.py --basetemp=.pytest_basetemp -q --cov=benchmarks.campaign.exp001_r1_driver --cov-report=term-missing --cov-report=json:DOCS/test_and_benchmark_results/exp001-r1-e1-coverage.json
.venv\Scripts\ruff.exe check benchmarks/campaign/exp001_driver.py benchmarks/campaign/exp001_r1_driver.py tests/test_exp001_driver.py tests/test_exp001_r1_driver.py
.venv\Scripts\ruff.exe format --check benchmarks/campaign/exp001_driver.py benchmarks/campaign/exp001_r1_driver.py tests/test_exp001_driver.py tests/test_exp001_r1_driver.py
.venv\Scripts\mypy.exe benchmarks/campaign/exp001_r1_driver.py --strict
.venv\Scripts\python.exe -m interrogate -c pyproject.toml benchmarks/campaign/exp001_r1_driver.py
.venv\Scripts\python.exe -m bandit benchmarks/campaign/exp001_r1_driver.py -c pyproject.toml
.venv\Scripts\python.exe tools/check_dv_register_gates.py
```

Coverage output is a gitignored, reproducible local validation artefact,
not campaign evidence. The repository's 95% changed-code threshold is met;
no coverage or type-check suppression was added.

**Snyk Code:** the discovered, authenticated Snyk MCP `snyk_code_scan` was
run with `severity_threshold="low"` separately on the absolute paths to
both driver files and both test files. Each scan returned **0 issues**.
The new files were rescanned after their final source changes. This covers
the changed-source scope and is stronger than the governed zero-medium+
threshold; it is not a claim that the entire repository has no findings.
No dependency input changed, so this session did not trigger a new Snyk
Open Source or native dependency-resolution audit. Existing hosted secret
controls and CI remain independent merge gates; this local E1 commit has
not been pushed and cannot claim its own hosted checks passed.

## Final local gate

The full repository local gate ran once, sequentially, after the mechanical
E1 additions. pytest and cargo never overlapped; no experiment mode, parity
replay, correction-evidence generator or GPU workload ran, and no `RUN-`
directory or campaign output was created. Recorded results:

| Command | Result |
|---|---|
| `ruff check python/ tests/ benchmarks/ tools/ parity/` | All checks passed |
| `ruff format --check` (same scope) | 318 files already formatted |
| `mypy python/prin benchmarks/campaign --strict` | No issues in 65 source files |
| `interrogate -c pyproject.toml python/prin` | Passed (r1 driver file: 100%) |
| `bandit -r python/prin -c pyproject.toml` | No issues; 20,216 lines scanned |
| `pytest tests/ -m "not slow and not gpu" --basetemp=.pytest_basetemp -q` | 3332 passed, 181 skipped, 48 deselected, 56 warnings (711.70s) |
| `cargo fmt --all -- --check` | Clean |
| `cargo clippy --workspace --all-targets -j 1 -- -D warnings` | Clean, no warnings |
| `cargo test --workspace -j 1` | 48 test binaries; 1598 passed, 0 failed, 1 ignored |
| `tools/check_dv_register_gates.py` | Passed: 40 DV rows against 198 session entries |
| `tools/check_global_session_registration.py` | Passed: 17 Executive Audit reports |
| `git diff --cached --check` | Clean (all 16 staged files, including the new docs) |
| Local-link check on added/modified Markdown regions | 19/19 links resolve |

The Sphinx acceptance test's gitignored `DOCS/sphinx/_build_test` output
directory was removed immediately before pytest and the test passed inside
the suite; no separate Sphinx build ran. `cargo test --workspace -j 1`
initially hit Windows linker file-lock contention (`LNK1104: cannot open
file` on fresh test executables in `target\debug\deps\`, consistent with
antivirus/indexer contention — rustc also logged `os error 32` finalizing
incremental sessions). It was unblocked with no code change by repeating
`cargo test --workspace --no-run -j 1` in isolation; each attempt resumed
from the object cache and linked a few more binaries (~9 attempts), after
which the prescribed command ran unmodified and passed.

The merge CI above is evidence for the PR #24 correction merge only. This
E1 code is unpushed, so these local results are the only checks that have
seen the new driver and tests.

### Abort-evidence return and post-addition check

After that pass, `main()` gained a lead-authored abort guard: after durable
manifest closure it counts case records with `aborted is True` and returns
ABORT (exit 2), retaining the invalid run for audit rather than reporting
success. The synthetic regression
`test_cli_retains_aborted_case_evidence_and_returns_failure` verifies the
closed, manifested run is retained while exit 2 is returned; it stubs only
the test-local `tools.reproduce.ALLOWED_MANIFEST_ROOTS` for the pytest
`tmp_path` root — no production allowlist changed. The narrowed
changed-source gates were re-run on final source; the broad Python and
Rust results above are frozen and were not re-run:

| Command | Result |
|---|---|
| `pytest tests/test_exp001_r1_driver.py --basetemp=.pytest_basetemp -q --cov=benchmarks.campaign.exp001_r1_driver --cov-report=term-missing --cov-report=json:DOCS/test_and_benchmark_results/exp001-r1-e1-coverage.json` | 56 passed (5.06s); 274/275 lines, 99.64% |
| `ruff check` + `ruff format --check` (r1 driver and its test) | Clean; 2 files already formatted |
| `mypy benchmarks/campaign/exp001_r1_driver.py --strict` | No issues |
| `bandit benchmarks/campaign/exp001_r1_driver.py -c pyproject.toml` | No issues |
| Snyk Code, `severity_threshold="low"`, on both touched files | 0 issues each |

## Handoff boundary

The next stage is independent **EXP-001-r1 E2** review and maintainer
approval. Its concrete review checklist is pre-registration §10. It must
resolve the required wgpu capability/coverage disposition and approve a
feasible storage allocation before execution; this E1 declaration does
neither.

No E3 `log.md`, E4 output manifest, E5 `report.md`, raw r1 `RUN-` directory
or scientific verdict is created by this session. All original EXP-001
artefacts stay immutable. Session **0159**, all downstream experiments and
**0194** remain blocked under campaign plan §10.4 item 5.

The E1 changes are committed locally on the campaign branch under campaign
plan §12 item 3. No push, merge, E2 approval or experiment execution is
implied by this handoff.
