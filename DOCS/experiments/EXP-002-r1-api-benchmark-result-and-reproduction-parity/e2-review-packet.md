# EXP-002-r1 — Maintainer review and S4 retro-audit packet for `EXP-002-r1-E2`

**Status:** PREPARED FOR REVIEW — NOT APPROVED
**Prepared by:** Devin, `EXP-002-r1-E1` drafting AI pair
**Date:** 2026-10-20 UTC
**Independent reviewer:** MichaelMaillet (maintainer), plus optional non-author E2 AI reviewer (campaign plan §2.2) — review/decision pending
**Active stage:** `EXP-002-r1-E1` complete on branch `campaign/exp002-r1-e1`; `EXP-002-r1-E2` next
**Protocol:** [`preregistration.md`](preregistration.md) (`Status: DRAFT`)

This is an author-prepared decision and retro-audit packet, not an independent
non-author review, signed E2 approval, or E3 authorization. No `EXP-002-r1`
experiment leg has executed and no `RUN-` directory exists under
`benchmarks/results/EXP-002-r1/`.

## 1. Reviewed source, baseline, and provenance hashes

- **`origin/main` baseline (`M`):** `5677858c15d784d881b23d43dff5029d199b0a18`
  (PR #35 merged 2026-10-20T10:05:42Z from `a570aa7f1f3cc30163d3a48e962fc1f058e55cdb`;
  `tools/check_ci_green.py 5677858c15d784d881b23d43dff5029d199b0a18` exit `0`,
  all 6 required workflows green; two consecutive scheduled `nightly.yml` runs
  `39203786555` and `39373976832` succeeded in full).
- **DV-047 discharged at E1:** stale `.venv/Lib/site-packages/prin_core.pth`
  removed; `python/prin/_prin_core.pyd` rebuilt from clean `main` (`5677858c`)
  via `.venv\Scripts\python.exe -m maturin develop --release -m crates/prin-py/Cargo.toml`
  (`9,290,240` bytes, SHA-256
  `37392d067efa3983e384c94f4ac2268c4fad2f5ea929c529b3db50bff4fee99e`).

| Artefact / pinned input | Byte size | SHA-256 of reviewed bytes (post-remediation head) |
|---|---:|---|
| `DOCS/experiments/EXP-002-r1-api-benchmark-result-and-reproduction-parity/preregistration.md` | 50,885 | `c0e5a77b4b7a9815dd452114329b899b337543a100735495b596a0bd3e82a523` |
| `benchmarks/campaign/exp002_r1_driver.py` | 72,355 | `f122be9833ed49e70a2333c6c4e1a482fb2e5efaf06914d456b296e7bd218185` |
| `tests/test_exp002_r1_driver.py` | 144,745 | `69afc0b3169add884b531a6d7b5752e623db7084986d62ac15057cf66174792c` |
| `python/prin/_prin_core.pyd` (DV-047 rebuilt binary) | 9,290,240 | `37392d067efa3983e384c94f4ac2268c4fad2f5ea929c529b3db50bff4fee99e` |
| `python/prin/reporting/figure_generation.py` (EXP-002-D1 corrected port) | 41,869 | `e216fec4f45ab71cfc5ef1286701c920731df278120e0afa0d216515b4bb19a7` |
| `python/prin/reporting/table_generation.py` | 29,173 | `1593f52d9a652842ee7d62163d9e6b397989e9c6489aa5cc43a8416b1083c8af` |
| `paper/artefact_manifest.json` (172 historical JSON records) | 28,645 | `300cdc094d2b7d27ac8b1e2556b2e6ed4dad3333f0038b45c8f87ea81612cce5` |

## 2. Scientific and governance decisions for E2 review (`preregistration.md` §10)

| # | Decision item | Registered contract in `preregistration.md` | E2 review action |
|---|---|---|---|
| 1 | **H1–H4 scope and decision rules (§2–§4)** | H1: 175 PRIN exports / 172 legacy names owned / `verify_api_surface(__all__) == (set(), set())`. H2: 62 elementary archival predicates across C01–C05 + §5.3 downstream owner matrix. H3: 39 publication files (14 figures × 2 formats + 11 `.tex` tables) compared under the primary §5.4 policy. H4: two separate PRIN processes raw-byte identical (`39/39`) with identical canonical projections | Verify falsifiability, denominators, and absence of silent tolerance loosening |
| 2 | **Resolution of `EXP002D1-S2-F1` (§4.1, §5.4, §11.1)** | Ratified by maintainer pre-E1: **§5.4 is the sole primary deciding rule for H3** (`39/39` expected). **§11.3 pre-exposure policy** (`14/39` expected) is retained as a **reported, non-gating writer-property diagnostic** requiring all 25 residuals between §5.4 and §11.3 to be classified into the two known writer/host I/O classes (`pdf_info_keyset` = 14, `tex_crlf_line_terminator` = 11) with **0 unclassified residuals**; any unclassified residual refutes H3. Replaces `EXP-002` §11.3 item 1. Outcome exposure is disclosed in header, §1, and §11.2; neither writer is altered | Independently verify that `exp002_r1_driver.py` records `raw_*`, `normalized_*` (§5.4), and `sensitivity_*` (§11.3) sizes/digests for every generated file and that the residual-classification contract is unambiguous before E3 freeze |
| 3 | **Re-run Namespace & Evidence Isolation (§5.5, §9; campaign plan amendment #10)** | Disjoint roots: `RAW_ROOT = benchmarks/results/EXP-002-r1`, `OUTPUT_ROOT = DOCS/test_and_benchmark_results/EXP-002-r1`, `EVIDENCE/exp002-r1-e1/`..`e5/`, `EXP_ID = "EXP-002-r1"`, `SESSION_ID = "EXP-002-r1-E3"`, `r1-` run labels (`r1-api-cpu`, `r1-conclusions-cpu`, `r1-reproduction-reference-cpu`, `r1-reproduction-prin-cpu`, `r1-seedrep0-prin-cpu`). `_reject_predecessor_path` refuses any `EXP-002` raw/output/record path. `_storage_check` enforces 2 MiB per-run, 10 MiB `EXP-002-r1`, **10 MiB combined `EXP-002` + `EXP-002-r1`**, and 64 MiB campaign-wide caps | Verify isolation guards and negative tests in `tests/test_exp002_r1_driver.py` |
| 4 | **DV-047 closure and provenance pins (§1.1)** | Stale `prin_core.pth` removed; `python/prin/_prin_core.pyd` rebuilt at `5677858c` (`9,290,240 B`, SHA-256 `37392d06…ee99e`); `_verify_prin_core_extension` and `_verify_prin_generators` enforced at runtime and checked at run closure | Independently re-compute `python/prin/_prin_core.pyd` and `figure_generation.py`/`table_generation.py` digests against `preregistration.md` §1.1 and `exp002_r1_driver.py` |
| 5 | **Sample/seed plan and E5 retained-bytes order (§7, §8.2, §11.3)** | `n=1` deterministic census per leg, `(counter,key) = (0,2)`, `seed_used = False`, unused `BenchmarkConfig(iterations=10, warmup=0)` tagged `measurement_kind="deterministic_census"`. Retained `DOCS/test_and_benchmark_results/EXP-002-r1/<run-id>/` verified first at E5 before §8.2 clean-checkout reconstruction | Approve deterministic `n=1` exception and retained-bytes verification order |

## 3. E1 verification summary

- `tests/test_exp002_r1_driver.py`: **343 passed, 1 skipped** (the skip is the
  opt-in registered-host `_prin_core.pyd` binary test, which passes `3/3` when
  explicitly selected on the governed E3 host; see §5 item 1), **98 %**
  coverage on `benchmarks/campaign/exp002_r1_driver.py` (`865` statements,
  `17` missing). The pre-remediation baseline on `62680946` was `320 passed`,
  `99.60 %` (`751/754` statements).
- `ruff check`, `ruff format --check` (both scopes), `mypy --strict` (both scopes + new driver/tests), `interrogate` (`97.6 %`), `bandit` (`0` issues), Snyk Code MCP (`0` issues at `low` threshold on both new Python files), `cargo audit` (exit `0`), `pip-audit` (both manifests, `0` vulnerabilities), all four governance scripts, clean Sphinx `-W --keep-going` build (`0` warnings), and `gitleaks` (full history + `--staged`, `0` leaks) all exit `0`.
- Full evidence bundle: [`EVIDENCE/exp002-r1-e1/`](../../../EVIDENCE/exp002-r1-e1/README.md).

## 4. Queued S2-class retro-audit checklist for `EXP002D1-S4-F2` and `EXP002D1-S4-F3`

Per Development Workflow and Audit Standards §7 and
[`DOCS/audits/2026-10-15-exp002-d1-correction-audit.md`](../../audits/2026-10-15-exp002-d1-correction-audit.md)
§S4.16 item 4, two maintainer-authorized code changes were made inside the
`EXP-002-D1` S4 documentation session (`PR #34`) and are queued for independent
retro-audit at the next S2-class audit (`EXP-002-r1-E2`). In addition, `PR #35`
(`5677858c`) landed the maintainer-ratified follow-up for DV-032 test (2) and
DV-045. `EXP-002-r1-E2` should execute and record the following independent
verification checklist in `e2-review.md`:

### 4.1 `EXP002D1-S4-F2` — Platform-scoped E3 reference-digest tie (`commit 814b670c`, `parity/test_parity_publication.py`)

- **What changed:** `parity/test_parity_publication.py::test_reference_arm_reproduces_e3_reference_arm`
  previously asserted that an in-process render by `prinet==3.0.0` matches the
  `normalized_sha256` recorded in the frozen Windows E3 reference run on *every*
  OS. Because Matplotlib's FreeType/font rasterization is OS-specific, the 28
  figure files differed on Ubuntu CI while the 11 `.tex` tables and the 39/39
  in-process PRIN-vs-reference comparison (`test_prin_matches_reference_under_registered_comparison`)
  passed. Commit `814b670c` scoped the figure-digest tie to the authoring
  platform declared in the E3 record itself (`environment.platform`), kept the
  11 `.tex` tables byte-exact on all platforms, required off-platform figures to
  render non-empty and pass `driver.normalized_bytes` container validation, and
  added `test_digest_tie_is_scoped_by_the_records_own_platform`.
- **E2 retro-audit verification items:**
  1. Inspect `git show 814b670c -- parity/test_parity_publication.py` and confirm
     no test was skipped, deselected, or xfailed, and `test_prin_matches_reference_under_registered_comparison`
     (the 39/39 H3 parity gate) is untouched.
  2. Run `.venv\Scripts\python.exe -m pytest parity/test_parity_publication.py --basetemp=.pytest_basetemp`
     on the Windows reference host and confirm all 94 tests pass (`94 passed`)
     with the byte-exact figure tie active (`platform.platform() == _E3_REFERENCE_PLATFORM`).
  3. Review the four negative controls in
     `EVIDENCE/exp002-d1-s4/pr34-review/negative-controls.txt` (`corrupt-figure`
     on matching platform fails; `corrupt-tex` on matching platform fails;
     `bogus+corrupt-figure` on differing platform passes; `bogus+corrupt-tex`
     on differing platform fails).
  4. Record retro-audit verdict (`PASS` or findings) for `EXP002D1-S4-F2` in
     `e2-review.md`.

### 4.2 `EXP002D1-S4-F3` — Process-CPU-time conversion of `test_no_gpu_throughput_regression` (`commit 67100a69`, `tests/test_acceptance_subconscious.py`) and PR #35 DV-032 test (2) conversion (`commits 33520b62`, `a570aa7f`)

- **What changed:**
  - In `67100a69` (`EXP002D1-S4-F3`, DV-032 test 1):
    `tests/test_acceptance_subconscious.py::TestIntegration::test_no_gpu_throughput_regression`
    was converted from a wall-clock ratio (`< 1.30`, which measured host noise
    and failed at `22.07` under load while its true daemon signal was `~1.1%`)
    to `time.process_time()`, with workload raised `n=1_000_000` → `n=8_000_000`
    (`~480 ms` vs the `15.6 ms` Windows process-time tick), bound
    `_DAEMON_CPU_RATIO_LIMIT = 1.60`, and three deterministic load-invariant
    assertions (`error_count == 0`, `dlq_size == 0`,
    `inference_count >= submitted`).
  - In `33520b62` / `a570aa7f` (PR #35, DV-032 test 2):
    `benchmarks/y4q1_5_benchmarks.py::run_timed_session` gained optional
    `max_frames` and `warmup_frames` parameters (with exact batch-cap bounding
    and partial tail-interval flushing), and
    `tests/test_acceptance_y4q1_5.py::TestSessionRunnerSmoke::test_deterministic_seed`
    was un-quarantined and converted to a seeded fixed-frame determinism check
    (`seed=42` twice agreeing within `1e-6`, plus a `seed=99` distinct-seed
    control).
- **E2 retro-audit verification items:**
  1. Inspect `git show 67100a69 -- tests/test_acceptance_subconscious.py` and
     `git diff 305416fb..5677858c -- benchmarks/y4q1_5_benchmarks.py tests/test_acceptance_y4q1_5.py tests/conftest.py`.
  2. Run `.venv\Scripts\python.exe -m pytest tests/test_acceptance_subconscious.py tests/test_acceptance_y4q1_5.py -k "test_no_gpu_throughput_regression or TestSessionRunnerSmoke" --basetemp=.pytest_basetemp`
     and confirm all targeted tests pass with zero skips.
  3. Review the negative controls in `EVIDENCE/exp002-d1-s4/gate/dv032-fix/dv032-verify2.txt`
     (CPU-hogging daemon fails on `ratio 2.03 > 1.6`; erroring daemon fails on
     `daemon reported 3 inference errors`) and the documented saturation
     limitation in `dv032-sensitivity2.txt`.
  4. Record retro-audit verdict (`PASS` or findings) for `EXP002D1-S4-F3` (and
     the PR #35 follow-up) in `e2-review.md`.

## 5. PR #36 multi-agent review remediation (post-`62680946`)

Hosted CI and multi-agent review on PR #36 — including the independent
Perplexity Deep Research report, which corroborated the other reviewers'
findings — surfaced eight findings against the E1 head `62680946`. All were
remediated on `campaign/exp002-r1-e1`; E2 should review the **remediation
commit** as the protocol/driver under review. The registered contract in
`preregistration.md` §5.5, §9, §10 items 3–4, and §11.1 was amended in lock-step
with the driver changes; the table below is the review-oriented summary (full
narrative in [`e1-handoff.md`](e1-handoff.md) §6).

| # | Finding | Remediation in `exp002_r1_driver.py` / protocol | Regression coverage |
|---|---|---|---|
| 1 | Portable hosted CI cannot satisfy the registered Windows `_prin_core.pyd` pin; the live test failed on hosted Ubuntu and hosted Windows matrix jobs | Generator-pin checks run portably; the exact-binary assertion is now opt-in and skipped unless explicitly selected on the governed E3 host. `_verify_prin_core_extension()` itself stays strict — no pin was weakened | `3 passed` on governed host when selected; `1 skipped` in the portable suite |
| 2 | `Path.absolute()` preserves `..`, allowing traversal aliases into immutable predecessor raw/output/record roots | Resolved-path confinement added: `_reject_predecessor_path` resolves candidates and rejects `..` components; generated/snapshot destinations are confined to `OUTPUT_ROOT`. Unresolved `.absolute()` paths are still used for symlink-ancestor detection in `_reserve`/`check_run_complete` so symlinks remain detectable before resolution | Traversal-alias negative tests for outputs, snapshots, and run paths |
| 3 | A storage-cap breach was only detected at closure, after `COMPLETED` had been published and manifested | `_storage_check` now runs prospectively before result publication (pending result + manifest bytes) **and** retrospectively at `check_run_complete`; failed runs write a durable `abort.json` that `check_run_complete` rejects from the manifest inventory, so an aborted run can never become an admissible completed observation | Storage-cap and `abort.json`/`check_run_complete` tests |
| 4 | Reference arm could import an installed/shadowing `prinet` or fail with `ModuleNotFoundError`; import happened before pin verification | Fail-closed bootstrap: reject a preloaded `prinet` in `sys.modules`, verify **all** `REFERENCE_PINS` digests pre-import, prepend `REFERENCE/src` to `sys.path`, and require `importlib.util.find_spec("prinet")` to resolve to the frozen `src/prinet/__init__.py` before importing generators | Reference-bootstrap tests incl. preloaded-module and wrong-origin negatives |
| 5 | Source pins were registered but not uniformly enforced at admission/finalization | `_verify_all_pins` runs at admission and again immediately before result publication, covering `_prin_core.pyd`, both PRIN generators, and all three `REFERENCE` sources | Admission/finalization pin-mutation negative tests |
| 6 | Shallow git pathspecs (`*.py`/`*.pth`) missed nested rogue files; no environment shadowing check existed | Recursive pathspecs scoped to the governed import surface (including ignored files) plus `_environment_shadowing` inspecting site `.pth` files and `sys.path` entries that could shadow `prin`/`prinet` | Nested-shadow and environment-shadow tests (incl. a real-git pathspec test) |
| 7 | `pdf_info_keyset` residuals could be misclassified from digest differences alone (identical `/Info` key sets can serialize differently) | `preregistration.md` §11.1 amended: classification requires inspecting actual `/Info` key sets and residual byte structure at E4; digest disagreement alone is insufficient. `normalized_bytes` docstring notes canonical projections are digest inputs, not regenerable documents | Protocol clarification; E4 classification duty registered |
| 8 | `EVIDENCE/exp002-r1-e1/verification-gate.txt` lacked a head-specific full local gate record; `.gitattributes` covered only `exp002-r1-e1` | Verification gate regenerated for the remediation head distinguishing authoritative local checks from hosted checks; `.gitattributes` now covers `EVIDENCE/exp002-r1-e*/**` for all stage roots | Evidence bundle re-hashed in `SHA256SUMS.txt` / `provenance-hashes.txt` |

**E2 review additions:** in addition to §2 items 1–5, confirm (a) the
opt-in live-pin test is the only host-specific gate and the production
verifier is unchanged in strictness; (b) resolved-path confinement rejects
traversal aliases while symlink detection still operates pre-resolution;
(c) the prospective storage check plus durable `abort.json` means an invalid
run can never be represented as a completed observation (aborted records are
invalid observations, not refutations); (d) the reference bootstrap cannot
resolve `prinet` to anything but the frozen `REFERENCE/src` tree; and (e)
all-pin enforcement covers every registered source pin at admission and
finalization.
