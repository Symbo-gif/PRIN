# Independent E2 Review and S4 Retro-Audit — EXP-002-r1

**Experiment:** `EXP-002-r1` — API, benchmark-result, and reproduction parity (track C1, bounded re-run of `EXP-002`)
**Session:** `EXP-002-r1 E2` (Independent Review, Approval Decision, and S4 Retro-Audit)
**Reviewer:** Antigravity (independent E2 AI pair, non-author of E1 deliverables)
**Review date:** 2026-10-21 UTC
**Review branch:** `campaign/exp002-r1-e2`
**Reviewed E1 head:** `bdaae83f2f384fba3c8d33013c40c6a2f4f011b5` (`campaign/exp002-r1-e1`, PR #36, initial E1 commit `62680946134847a8963c9caaa5179ec4868c8c02` + remediation commit `bdaae83f2f384fba3c8d33013c40c6a2f4f011b5`)
**Repository `origin/main` baseline (`M`):** `5677858c15d784d881b23d43dff5029d199b0a18` (PR #35 merge)
**Pre-registration status after E2 review:** `DRAFT` (`**Maintainer approval:** NOT GRANTED` — preserved unchanged pending the maintainer's dated scientific approval)
**Evidence bundle:** [`EVIDENCE/exp002-r1-e2/`](../../../EVIDENCE/exp002-r1-e2/README.md) ([`SHA256SUMS.txt`](../../../EVIDENCE/exp002-r1-e2/SHA256SUMS.txt))
**Overall E2 review verdict:** **RECOMMENDED FOR MAINTAINER APPROVAL** (**0 blocking findings**, **3 non-blocking observations** `E2-OBS-1`..`E2-OBS-3`; S2-class retro-audit of `EXP002D1-S4-F2`, `EXP002D1-S4-F3`, and PR #35 follow-up **PASS / RATIFIED**)

---

## 0. Role, Authority, and Scope Discipline

This document records the independent E2 review of the `EXP-002-r1` E1 deliverables ([`preregistration.md`](preregistration.md), [`benchmarks/campaign/exp002_r1_driver.py`](../../../benchmarks/campaign/exp002_r1_driver.py), [`tests/test_exp002_r1_driver.py`](../../../tests/test_exp002_r1_driver.py), [`e1-handoff.md`](e1-handoff.md), [`e2-review-packet.md`](e2-review-packet.md), and [`EVIDENCE/exp002-r1-e1/`](../../../EVIDENCE/exp002-r1-e1/README.md)) together with the S2-class retro-audit mandated by `DOCS/audits/2026-10-15-exp002-d1-correction-audit.md` §S4.13–§S4.16 and `DOCS/reports/041-project-state.md`.

Per campaign plan §6.1, Experimentation Standards §2, and the E2 session brief:

1. **No fabricated approval:** The E2 AI reviewer is not permitted to record maintainer scientific approval, flip [`preregistration.md`](preregistration.md) to `APPROVED`, or authorize E3 on its own initiative. [`preregistration.md`](preregistration.md) remains at `**Status:** DRAFT` and `**Maintainer approval:** NOT GRANTED` (`50,885` bytes, SHA-256 `c0e5a77b4b7a9815dd452114329b899b337543a100735495b596a0bd3e82a523`, untouched by this session).
2. **No E3 execution:** No `RUN-` directory was created, no experiment leg was executed, and `benchmarks/results/EXP-002-r1/` and `DOCS/test_and_benchmark_results/EXP-002-r1/` remain non-existent.
3. **Predecessor immutability preserved:** Zero bytes were modified under `DOCS/experiments/EXP-002-api-benchmark-result-and-reproduction-parity/`, `benchmarks/results/EXP-002/`, `DOCS/test_and_benchmark_results/EXP-002/`, `EVIDENCE/0159/`–`0163/`, or `EVIDENCE/exp002-d1-s1/`–`s4/` ([`predecessor-immutability.txt`](../../../EVIDENCE/exp002-r1-e2/predecessor-immutability.txt)).

---

## 1. Entry Verification and Verbatim Hosted-Check Record (Task 1)

### 1.1 Baseline and PR #36 State at Entry

At E2 entry (`2026-10-21T00:08:23Z`), `git fetch origin --prune` and `gh pr view 36` confirmed ([`entry-origin-main.txt`](../../../EVIDENCE/exp002-r1-e2/entry-origin-main.txt)):

- `origin/main` is at `5677858c15d784d881b23d43dff5029d199b0a18` (`Merge pull request #35 from MichaelMaillet/fix/dv032-deterministic-seed-and-audit`).
- PR #36 (`EXP-002-r1 E1: pre-registration, isolated driver, and DV-047 closure`, branch `campaign/exp002-r1-e1`, base `main`) is `OPEN` (unmerged) at head `bdaae83f2f384fba3c8d33013c40c6a2f4f011b5` (`remediate PR #36 EXP-002-r1 E1 review findings`, child of initial E1 commit `62680946134847a8963c9caaa5179ec4868c8c02`).
- Per the session brief (*"If not yet merged, the review subject is head `bdaae83f`; do NOT merge the PR yourself — merging is the maintainer's act"*), `campaign/exp002-r1-e2` was branched directly from `bdaae83f2f384fba3c8d33013c40c6a2f4f011b5`.
- `tools/check_ci_green.py` exited `0` on both `origin/main` (`5677858c15d784d881b23d43dff5029d199b0a18`, [`check-ci-green-5677858c.txt`](../../../EVIDENCE/exp002-r1-e2/check-ci-green-5677858c.txt)) and the E1 review subject (`bdaae83f2f384fba3c8d33013c40c6a2f4f011b5 --branch campaign/exp002-r1-e1`, [`check-ci-green-bdaae83f.txt`](../../../EVIDENCE/exp002-r1-e2/check-ci-green-bdaae83f.txt)).

| Target | Command | `rust` | `python` | `parity` | `repro` | `snyk` | `gpu` | Exit code | Evidence |
|---|---|---|---|---|---|---|---|---|---|
| `main` (`5677858c15d784d881b23d43dff5029d199b0a18`) | `.venv/Scripts/python.exe tools/check_ci_green.py 5677858c15d784d881b23d43dff5029d199b0a18` | `39405463375` (green) | `39405463348` (green) | `39405463347` (green) | `39405463356` (green) | `39405463333` (green) | `39405463413` (green) | `0` | [`check-ci-green-5677858c.txt`](../../../EVIDENCE/exp002-r1-e2/check-ci-green-5677858c.txt) |
| `campaign/exp002-r1-e1` (`bdaae83f2f384fba3c8d33013c40c6a2f4f011b5`) | `.venv/Scripts/python.exe tools/check_ci_green.py bdaae83f2f384fba3c8d33013c40c6a2f4f011b5 --branch campaign/exp002-r1-e1 --limit 100` | `39496143045` (green) | `39496143063` (green) | `39496143042` (green) | `39496143041` (green) | `39496143043` (green) | `39496143047` (green) | `0` | [`check-ci-green-bdaae83f.txt`](../../../EVIDENCE/exp002-r1-e2/check-ci-green-bdaae83f.txt) |

### 1.2 Verbatim Hosted-Check Record on `bdaae83f2f384fba3c8d33013c40c6a2f4f011b5`

On the initial E1 commit `62680946134847a8963c9caaa5179ec4868c8c02`, the six `python`-workflow matrix jobs failed because `test_live_prin_core_pyd_pin_matches_registered_build` ran unconditionally against the CI-built platform extension binary (`_prin_core.cpython-312-x86_64-linux-gnu.so` / `.pyd`) instead of being gated to the registered Windows E3 host, and `rust` `audit` failed on newly published `RUSTSEC-2026-0381` / `RUSTSEC-2026-0382`. Remediation commit `bdaae83f2f384fba3c8d33013c40c6a2f4f011b5` resolved both issues plus seven review findings. All **7 workflows** and all **32 check runs** on `bdaae83f2f384fba3c8d33013c40c6a2f4f011b5` succeeded ([`hosted-pr36-statuscheckrollup.txt`](../../../EVIDENCE/exp002-r1-e2/hosted-pr36-statuscheckrollup.txt), [`hosted-runs-verbatim.txt`](../../../EVIDENCE/exp002-r1-e2/hosted-runs-verbatim.txt)):

| Workflow | Run ID | Event | Head SHA | Status / Conclusion | Run URL | Jobs (all `COMPLETED` / `SUCCESS`) |
|---|---|---|---|---|---|---|
| `python` | `39496143063` | `pull_request` | `bdaae83f2f384fba3c8d33013c40c6a2f4f011b5` | `completed` / `success` | https://github.com/MichaelMaillet/PRIN/actions/runs/39496143063 | `lint` (`106173930553`), `security` (`106173930536`), `governance` (`106173930656`), `docs` (`106173930690`), `test (ubuntu-latest, 3.12)` (`106173930562`), `test (ubuntu-latest, 3.13)` (`106173930576`), `test (macos-latest, 3.12)` (`106173930589`), `test (macos-latest, 3.13)` (`106173930574`), `test (windows-latest, 3.12)` (`106173930594`), `test (windows-latest, 3.13)` (`106173930597`) |
| `rust` | `39496143045` | `pull_request` | `bdaae83f2f384fba3c8d33013c40c6a2f4f011b5` | `completed` / `success` | https://github.com/MichaelMaillet/PRIN/actions/runs/39496143045 | `fmt` (`106173930082`), `clippy` (`106173930173`), `audit` (`106173930086`), `test-strict` (`106173930262`), `test (ubuntu-latest)` (`106173930198`), `test (macos-latest)` (`106173930255`), `test (windows-latest)` (`106173930239`) |
| `parity` | `39496143042` | `pull_request` | `bdaae83f2f384fba3c8d33013c40c6a2f4f011b5` | `completed` / `success` | https://github.com/MichaelMaillet/PRIN/actions/runs/39496143042 | `parity` (`106173929785`), `detect_corpus` (`106173929760`) |
| `repro` | `39496143041` | `pull_request` | `bdaae83f2f384fba3c8d33013c40c6a2f4f011b5` | `completed` / `success` | https://github.com/MichaelMaillet/PRIN/actions/runs/39496143041 | `reproduce (ubuntu-latest)` (`106173929995`), `reproduce (macos-latest)` (`106173930037`), `reproduce (windows-latest)` (`106173930016`) |
| `gpu` | `39496143047` | `pull_request` | `bdaae83f2f384fba3c8d33013c40c6a2f4f011b5` | `completed` / `success` | https://github.com/MichaelMaillet/PRIN/actions/runs/39496143047 | `gpu-cuda` (`106173930075`), `gpu-wgpu` (`106173930093`) |
| `Secret Scan` | `39496132811` | `pull_request` | `bdaae83f2f384fba3c8d33013c40c6a2f4f011b5` | `completed` / `success` | https://github.com/MichaelMaillet/PRIN/actions/runs/39496132811 | `gitleaks` (`106173895350`), `commit-hygiene` (`106173895358`), `dependency-audit` (`106173895363`), `supply-chain` (`106173895343`) |
| `snyk` | `39496143043` | `pull_request` | `bdaae83f2f384fba3c8d33013c40c6a2f4f011b5` | `completed` / `success` | https://github.com/MichaelMaillet/PRIN/actions/runs/39496143043 | `snyk-rust` (`106173930060`), `snyk-python (3.12)` (`106173930012`), `snyk-python (3.13)` (`106173930015`), `snyk-code` (`106173929972`) |

### 1.3 Change Scope and Predecessor Immutability Verification

- `git diff --name-status 5677858c15d784d881b23d43dff5029d199b0a18..bdaae83f2f384fba3c8d33013c40c6a2f4f011b5` touches exactly **16 files** ([`e1-range-scope.txt`](../../../EVIDENCE/exp002-r1-e2/e1-range-scope.txt)): `.gitattributes`, `Cargo.lock`, `DOCS/experiments/EXP-002-r1-api-benchmark-result-and-reproduction-parity/{README.md,e1-handoff.md,e2-review-packet.md,preregistration.md}`, `DOCS/experiments/campaign-plan.md`, `DOCS/reports/DEFERRED_VALIDATION_REGISTER.md`, `EVIDENCE/exp002-r1-e1/{README.md,SHA256SUMS.txt,check-ci-green-5677858c.txt,dv047-closure.txt,pr36-remediation.txt,provenance-hashes.txt,verification-gate.txt}`, `benchmarks/campaign/exp002_r1_driver.py`, and `tests/test_exp002_r1_driver.py`.
- `git diff 5677858c15d784d881b23d43dff5029d199b0a18 HEAD` across all frozen predecessor roots (`DOCS/experiments/EXP-002-api-benchmark-result-and-reproduction-parity`, `benchmarks/results/EXP-002`, `DOCS/test_and_benchmark_results/EXP-002`, `EVIDENCE/0159`–`0163`, `EVIDENCE/exp002-d1-s1`–`s4`) is **empty** (`0` lines; [`predecessor-immutability.txt`](../../../EVIDENCE/exp002-r1-e2/predecessor-immutability.txt)).

---

## 2. Independent Protocol Review (`preregistration.md`, Task 2)

The E1 pre-registration [`preregistration.md`](preregistration.md) (`50,885` bytes, SHA-256 `c0e5a77b4b7a9815dd452114329b899b337543a100735495b596a0bd3e82a523`) was independently audited against [`e2-review-packet.md`](e2-review-packet.md) §2, `preregistration.md` §10 items 1–5, campaign plan §§6–12, and the frozen predecessor [`DOCS/experiments/EXP-002-api-benchmark-result-and-reproduction-parity/preregistration.md`](../EXP-002-api-benchmark-result-and-reproduction-parity/preregistration.md).

### 2.1 Summary Verdicts on `preregistration.md` §10 Items 1–5

| §10 Item | Scope | E2 Review Verdict | Summary of Independent Verification |
|---|---|---|---|
| **Item 1** | H1 export/mapping census (`175` / `172` + `3` additions) & H2 5-family / `62`-predicate closed archival scope + §5.3 downstream owner matrix | **PASS** | Exact parity with frozen `EXP-002` H1/H2 definitions, populations (`175`, `172`, `62`), thresholds (`0.555`, `0.5`), strict operators (`>`, `<`), CPU Goldilocks selection (`csr_cpu`, `full_cpu`, `mean_field_cpu`, `sparse_knn_cpu`), and §5.3 downstream scientific owner table (EXP-003 through EXP-008). |
| **Item 2** | H3 39-file census, §5.4 sole primary comparison policy, and §11.3 non-gating sensitivity diagnostic (`0` `unclassified` residuals, amended `pdf_info_keyset` verification rule) | **PASS** | `39`-file inventory (`14` figures × `{.pdf, .png}` + `11` `.tex` tables) unchanged; §5.4 approved comparison is the **sole primary H3 decision rule**; §11.3 sensitivity digest (`6314532` rule) is retained as a **non-gating diagnostic** requiring `0` `unclassified` residuals across `{crlf_table, pdf_info_keyset, unclassified}`, with PR #36's (`bdaae83f`) explicit `/Info`-dictionary verification duty for `pdf_info_keyset`. |
| **Item 3** | H4 separate-process raw-byte identity, `(counter,key) = (0,2)` deterministic `n=1` sample plan, and §11.2 confirmatory framing disclosure | **PASS** | H4 requires `39/39` raw byte size + raw SHA-256 identity + identical canonical scientific projections across two separate PRIN processes (`prin` vs `repeatability`), with zero normalization rescue. `(0,2)` `n=1` deterministic census (`seed_used=False`, `measurement_kind="deterministic_census"`, `replicates=1`, `iterations=10`, `warmup=0`) and §11.2 prior-exposure disclosure are complete and accurate. |
| **Item 4** | Versioned driver `exp002_r1_driver.py`, 344-test suite, all-pin admission/finalization guards, environment-shadowing check, and isolated `EXP-002-r1` / `exp002-r1-e1`..`e5` roots | **PASS** (with non-blocking `E2-OBS-1`) | All roots, `r1-` run labels, DV-047 `_prin_core.pyd` pin (`5,127,680 B`, `5b8ab839...`), corrected generator pins (`d721f021...`, `8e54bbcb...`), reference pins, and shadowing guards are verified against live bytes. See `E2-OBS-1` on §1.1 vs §5.5/`_verify_all_pins()` wording for `paper/artefact_manifest.json`. |
| **Item 5** | S2-class retro-audit of S4 code changes (`EXP002D1-S4-F2`, `EXP002D1-S4-F3`, and PR #35 follow-up `33520b62`/`a570aa7f`) | **PASS (RATIFIED)** | Executed in full in Section 4 below; all code changes, negative controls, and focused pytest runs pass with zero defects. |

### 2.2 Detailed Protocol Verification

1. **H1 (`175`-symbol / `172`-legacy census, §§2, 3, 4.1, 5.1):**
   - Independently verified that `REFERENCE/src/prinet/__init__.py` (`ede92afc6771f2e29206534905e2820598ba841662a93d59f669f803a382f182`) defines a literal `__all__` of `172` unique names, and unioning `PRIN_ADDITIONS = {"BackendUnavailableError", "__version__", "core_version"}` yields `175` unique expected names ([`live-environment-and-pins.txt`](../../../EVIDENCE/exp002-r1-e2/live-environment-and-pins.txt)).
   - H1 requires: (a) all `175` expected names resolve on `prin` to non-`None` callable/class exports or scalar `str`/`int`/`float`/`tuple` constants (without invoking callables); (b) all `172` legacy names appear in the committed Migration Guide consolidated ownership table (`DOCS/sphinx/migration_guide.rst` between `.. wp036-consolidated-table-begin` and `.. wp036-consolidated-table-end`) and `DOCS/baselines/wp001_api_traceability.md`; (c) `prin.__all__` has length `175` with zero duplicates, removals, or additions; and (d) `verify_api_surface(prin.__all__)` returns `(set(), set())`.
2. **H2 (`62`-predicate closed archival census + §5.3 downstream owner matrix, §§2, 3, 4.1, 5.2, 5.3):**
   - Verified the five closed archival families and exact counts:
     - `C01` (`phase1_chimera_seeds.json`): `5` predicates (`bimodality_coefficient.raw_values[i] > 0.555`, `i=0..4`, expected `True`).
     - `C02` (`benchmark_y4q1_3_k_alpha_sensitivity.json`): `42` predicates (`bc_mean > 0.555` vs stored `chimera_detected` boolean for each distinct `(K, alpha)` row, preserving `(K, alpha_radians)` labels).
     - `C03` (`phase2_chimera_nsweep.json`): `4` predicates (`bc_stats.mean > 0.5` for `n_oscillators` in `{128, 256, 512, 1024}`, expected `True`).
     - `C04` (`y4q1_8_topology_comparison.json`): `5` predicates (`ring.bc_mean > {2community, 4community}.bc_mean` [2], `ring.bc_ci.ci_width > {2community, 4community}.bc_ci.ci_width` [2], `2community.bc_ci.ci_width > 4community.bc_ci.ci_width` [1], expected `True`).
     - `C05` (`y3q49_goldilocks_zones.json`): `6` predicates over CPU-tagged entries `csr_cpu`, `full_cpu`, `mean_field_cpu`, `sparse_knn_cpu` (`csr_cpu.zone_width > other.zone_width` [3], `full_cpu.K_c < other.K_c` [3], expected `True`).
   - Verified §5.3 explicitly preserves downstream scientific ownership across `EXP-003` (CPU throughput/scaling), `EXP-004` (GPU throughput/Triton/CUDA), `EXP-005` (fresh chimera replication/corrected SI), `EXP-006` (CLEVR-N/PT-vs-SA/ablations/training), `EXP-007` (daemon p95/MOT/robustness), and `EXP-008` (cross-OS/wheel/NPU).
3. **H3 (`39`-file publication census, §5.4 sole primary policy, and §11.3 diagnostic, §§2, 3, 4.1, 5.4, 8.1, 11.1, 11.3):**
   - Confirmed the exact `39`-file publication inventory: `14` figure stems (`fig2_clevr_n_capacity` through `fig15_noise_velocity`) in `.pdf` and `.png` (`28` files) plus `11` table stems (`tab_ablation` through `tab_geometry`) in `.tex` (`11` files).
   - Confirmed that §5.4's comparison policy (CRLF→LF on `.tex`; critical chunks `IHDR`/`PLTE`/`tRNS`/`IDAT`/`IEND` on `.png` after CRC/zlib/colour-rule validation; single-revision classic-xref `.pdf` container validation with removal of `/Creator`, `/Producer`, `/CreationDate`, `/ModDate` from the flat `/Info` dictionary, single-space re-serialization, trailer `/ID` zeroing, and in-use xref offset / `startxref` zeroing) is the **sole primary H3 decision rule**.
   - Confirmed that §11.3's pre-`6314532` sensitivity digest (`sensitivity_bytes`, `sensitivity_sha256`: raw `.tex` bytes, in-place PDF `/Info` value masking keeping key set and line wrapping, identical `.png` normalization) is retained as a **non-gating diagnostic** reported alongside the primary verdict in `summary.json`, `reproduction-comparisons.csv`, and the E5 report.
   - Confirmed the PR #36 (`bdaae83f`) amendment to §11.1 / §11.3: every primary-pass / sensitivity-mismatch residual must be classified by E4 into `{crlf_table, pdf_info_keyset, unclassified}`, where assigning `pdf_info_keyset` requires verifying from the retained publication files that the two raw PDFs' `/Info` dictionaries differ in key set/order or serialized byte length after in-place value masking (not merely checking `.pdf` suffix + `normalized_sha256` equality), and **any non-zero `unclassified` count (`unclassified > 0`) triggers a mandatory E4 stop-and-escalate**.
4. **H4 (`39`-file two-process raw-byte repeatability, §§2, 3, 4.1, 5.5):**
   - Confirmed H4 compares two separate PRIN render processes (`prin` and `repeatability`) on **raw byte size** (`raw_bytes`), **raw SHA-256** (`raw_sha256`), and canonical scientific result projections. Normalization never applies to H4.
5. **DV-047 closure and governed source pins (§1.1, [`dv047-closure.txt`](../../../EVIDENCE/exp002-r1-e1/dv047-closure.txt), [`live-environment-and-pins.txt`](../../../EVIDENCE/exp002-r1-e2/live-environment-and-pins.txt)):**
   - Verified on this governed Windows host that `python/prin/_prin_core.pyd` (`5,127,680` bytes, SHA-256 `5b8ab8398fc341b66c4bd004628d542d414d0e6bb371072a5e32ab2f8e05bc05`) exports `prin._prin_core.core_version() == "1.0.0rc1"` matching `prin.__version__ == "1.0.0rc1"`, closing `DV-047`.
   - Verified all 10 baseline input/source digests in `preregistration.md` §1.1 match the live repository files byte-for-byte.
6. **Zero silent tolerance loosening vs frozen `EXP-002`:**
   - A line-by-line comparison between `EXP-002/preregistration.md` and `EXP-002-r1/preregistration.md` confirms that no hypothesis denominator (`175`, `172`, `62`, `39`), numerical threshold (`0.555`, `0.5`), strict relational operator (`>`, `<`), normalization rule, seed pair (`(0,2)`), or resource cap (`<=12 h` CPU wall, `<=2 MiB` per run, `<=10 MiB` raw and combined `EXP-002 + EXP-002-r1`, `<=64 MiB` campaign) was loosened.

---

## 3. Independent Driver and Test Suite Review (Task 3)

The versioned driver [`benchmarks/campaign/exp002_r1_driver.py`](../../../benchmarks/campaign/exp002_r1_driver.py) (`1,887` lines, `72,355` bytes, SHA-256 `f122be9833ed49e70a2333c6c4e1a482fb2e5efaf06914d456b296e7bd218185`) and its test suite [`tests/test_exp002_r1_driver.py`](../../../tests/test_exp002_r1_driver.py) (`3,726` lines, `144,745` bytes, SHA-256 `69afc0b3169add884b531a6d7b5752e623db7084986d62ac15057cf66174792c`) were read in full and verified against [`preregistration.md`](preregistration.md) and [`e2-review-packet.md`](e2-review-packet.md) §§3 and 5.

### 3.1 Verification of Core Driver Contracts (`e2-review-packet.md` §3)

| Contract Area | Driver Implementation Reference | Test Coverage Reference | Verdict |
|---|---|---|---|
| **Isolated roots & predecessor rejection** | `EXP_ID = "EXP-002-r1"`, `SESSION_ID = "EXP-002-r1-E3"`, `RAW_ROOT = ROOT / "benchmarks/results/EXP-002-r1"`, `OUTPUT_ROOT = ROOT / "DOCS/test_and_benchmark_results/EXP-002-r1"`, `_reject_predecessor_path` (lines 48–92, 241–273) | `TestNamespaceIsolationAndRealPins`, `TestTraversalConfinement` | **PASS** |
| **Mode labels (`r1-` prefixed)** | `MODE_LABELS = {"api": "r1-api-cpu", "conclusions": "r1-conclusions-cpu", "reference": "r1-reproduction-reference-cpu", "prin": "r1-reproduction-prin-cpu", "repeatability": "r1-seedrep0-prin-cpu"}` (lines 93–99) | `TestReserve`, `TestRunRegistered` | **PASS** |
| **H1 `collect_api` census** | Reads `REFERENCE/src/prinet/__init__.py` via `read_no_follow`, verifies digest against `REFERENCE_PINS`, AST-parses 172 literal `__all__` strings, checks `175` expected names on `prin` without calling callables (`isinstance(value, (str, int, float, tuple))` vs `callable(value)`), checks Migration Guide consolidated table + `wp001_api_traceability.md`, records `verify_api_surface` sets (lines 384–486) | `TestCollectApi`, `TestLegacyNames` | **PASS** |
| **H2 `collect_conclusions` census** | Evaluates 62 elementary predicates across `CONCLUSION_FILES` (`C01`: 5, `C02`: 42 with `(K, alpha_radians)` uniqueness and boolean check, `C03`: 4 for `{128,256,512,1024}`, `C04`: 5, `C05`: 6 CPU-tagged regimes), rejects `bool`/`NaN`/`Inf` operands via `_number`, emits no verdict field (lines 489–676) | `TestCollectConclusions`, `TestConclusionValidation` (22 mutation cases) | **PASS** |
| **H3/H4 `normalized_bytes` & `sensitivity_bytes`** | `.tex` CRLF→LF (`normalized_bytes`) vs raw (`sensitivity_bytes`); `.png` full chunk/CRC/IHDR/PLTE/tRNS/IDAT/zlib decompression/scanline filter validation (`_validate_png`); `.pdf` classic-xref/trailer/object validation, flat `/Info` removal & single-space re-serialization + zeroed xref/startxref (`normalized_bytes`) vs in-place `/Info` value masking (`sensitivity_bytes`) (lines 679–1036) | `TestNormalizedBytes`, `TestPdfInfoCanonicalization`, `TestPdfDecimalBounds`, `TestPngColourRules` | **PASS** |
| **Admission, reservation, abort, and closure** | `_admission` checks `Status: APPROVED` + dated `MichaelMaillet, YYYY-MM-DD UTC` header, `HEAD == source_sha`, clean tracked/untracked/shadowing tree, `_environment_shadowing()`, and `_verify_all_pins()`; `_reserve` enforces `RUN-<UTC>-<R7>-r1-<label>` naming and no directory reuse; `_abort` writes `ABORTED` result + `abort.json` + `manifest.json`; `check_run_complete` re-verifies git provenance, schema, population counts (`175`, `62`), pins, and storage caps (lines 1471–1856) | `TestAdmission`, `TestEnvironmentShadowing`, `TestRealGitShadowScan`, `TestReserve`, `TestRunRegistered`, `TestCheckRunComplete` (38 result + 8 metadata mutations) | **PASS** |

### 3.2 Verification of PR #36 Remediation Items (`e2-review-packet.md` §5 (a)–(e))

1. **§5(a) Opt-in `PRIN_EXP002_R1_HOST_PIN=1` binary-pin test gating:**
   - **Verified:** In [`tests/test_exp002_r1_driver.py`](../../../tests/test_exp002_r1_driver.py#L653-L665), `test_live_prin_core_pyd_pin_matches_registered_build` is decorated with `@pytest.mark.skipif(os.environ.get("PRIN_EXP002_R1_HOST_PIN") != "1", ...)` and is the **only** host-specific skip in the 344-test file.
   - In [`benchmarks/campaign/exp002_r1_driver.py`](../../../benchmarks/campaign/exp002_r1_driver.py#L1039-L1068), `_verify_prin_core_extension()` has **zero** environment-variable bypasses: it unconditionally verifies `Path(_prin_core.__file__).resolve() == PRIN_CORE_PYD.resolve()`, `len(raw) == PRIN_CORE_PYD_BYTES` (`5,127,680`), `_digest(raw) == PRIN_CORE_PYD_SHA256` (`5b8ab839...`), and `core_version() == prin.__version__`.
   - Portable source-pin test `test_real_generator_source_pins_match_repository` (lines 646–651) runs unconditionally on all CI platforms.
2. **§5(b) Resolved-path confinement (`..` traversal rejection + pre-resolution symlink detection):**
   - **Verified:** `_reject_parent_traversal(path, role)` (lines 207–211) inspects `path.parts` on the raw `Path` before `resolve()` and raises `DriverError` if `".."` is present.
   - `_no_symlink(path, role)` (lines 214–219) walks `(path, *path.parents)` on the raw un-resolved `Path` and raises `DriverError` on any symlink component before `resolve()` collapses it.
   - `_reject_predecessor_path`, `_snapshot`, `collect_reproduction`, `_reserve`, and `check_run_complete` all apply `_reject_parent_traversal` + `_no_symlink` and then compare `.resolve()` against `OUTPUT_ROOT.resolve()`, `RAW_ROOT.resolve()`, and the three `PREDECESSOR_*` roots. `TestTraversalConfinement` (lines 2448–2484) and the `@_needs_symlink_support` tests directly exercise both traversal aliases (`OUTPUT_ROOT / ".." / "EXP-002" / ...`, `RAW_ROOT / ".." / "EXP-002" / ...`) and symlink ancestors.
3. **§5(c) Prospective storage check and durable `abort.json` inadmissibility:**
   - **Verified:** In `run_registered` (lines 1692–1727), after `observations` are collected and `_verify_all_pins()` passes at finalization, the driver serializes `payload_bytes = (json.dumps(payload, indent=2) + "\n").encode("utf-8")` in memory and calls `_storage_check(run_dir, prospective={result_path: len(payload_bytes)})` **before** calling `write_result(payload, result_path)`.
   - If any cap (`RUN_CAP = 2 MiB`, `RAW_CAP = 10 MiB`, `COMBINED_EXP002_CAP = 10 MiB` across `EXP-002 + EXP-002-r1`, or `CAMPAIGN_CAP = 64 MiB`) would be exceeded, `_storage_check` raises `DriverError` inside the `try` block, entering `_abort` (lines 1545–1597).
   - `_abort` writes `status: "ABORTED"` to `result_path`, writes `abort.json` (`exp_id`, `session`, `run_id`, `mode`, `abort_reason`, `aborted_at_utc`), and manifests `abort.json` into `manifest.json`.
   - In `check_run_complete` (lines 1762–1766), `if (run_dir / "abort.json").exists(): raise DriverError(...)` plus strict 3-file inventory enforcement (`{metadata_name, result_name, "manifest.json"}`) ensures an aborted run is permanently inadmissible as a completed observation, while remaining retained on disk as an invalid/aborted attempt in compliance with `preregistration.md` §4.2–§4.3.
4. **§5(d) Fail-closed reference `prinet` bootstrap:**
   - **Verified:** In `collect_reproduction` (lines 1207–1250), the `reference` arm:
     1. Rejects any preloaded `prinet` or `prinet.*` module in `sys.modules` (`DriverError("preloaded prinet module(s) in sys.modules ...")`).
     2. Prepends `str(REFERENCE / "src")` to `sys.path` if not already present and calls `importlib.invalidate_caches()`.
     3. Calls `spec = importlib.util.find_spec("prinet")` and requires `spec is not None`, `spec.origin is not None`, and `Path(spec.origin).resolve() == (REFERENCE / "src/prinet/__init__.py").resolve()`.
     4. Imports `prinet.utils.figure_generation` and `prinet.utils.table_generation`, checks each module's `Path(module.__file__).resolve() == expected.resolve()`, and verifies `_digest(read_no_follow(expected, ...)) == REFERENCE_PINS[relative]`.
   - Tested by `test_reference_leg_rejects_preloaded_prinet`, `test_reference_leg_rejects_foreign_resolution`, `test_reference_leg_rejects_unresolvable_prinet`, and `test_reference_origin_and_digest_guards` (lines 1677–1767).
5. **§5(e) All-pin enforcement at admission and finalization + recursive shadow scan:**
   - **Verified:** `_verify_all_pins()` (lines 1095–1109) calls `_verify_prin_core_extension()`, `_verify_prin_generators()`, and `_verify_reference_sources()`. It is invoked at `_admission()` (line 1644, before `_reserve` or `_snapshot`) and again at finalization in `run_registered()` (line 1692, after collection and before `_storage_check` / `write_result`).
   - `_SHADOW_PATHSPECS` (lines 150–167) scans `:(glob)*.py`, `:(glob)*.pth`, `:(glob)*.pyd`, `:(glob)*.so`, `:(glob)*.dll` at repo root and recursively (`**`) across `python/`, `benchmarks/`, `tools/`, and `parity/` (excluding only the non-importable parser corpus `tools/code-intelligence`).
   - `_environment_shadowing()` (lines 1112–1182) inspects `sys.modules["prin"]`, `importlib.util.find_spec("prinet")`, `sys.path`, `site.getsitepackages()`, `site.getusersitepackages()`, and every `*.pth` file in site-packages to reject any foreign `prin`/`prinet` checkout or `.pth` redirection.
   - **Non-blocking Observation `E2-OBS-1` (`INPUT_MANIFEST` pin timing vs §1.1 prose):**
     - `preregistration.md` §1.1 (lines 124–131) lists `paper/artefact_manifest.json` alongside `_prin_core.pyd`, the two PRIN generators, and the three `REFERENCE` files, and states: *"Enforcement is live at both ends of a run: the admission gate verifies all governed-source pins before any collection, and the finalization step re-verifies all of them before a completed record is published, so a governed source mutated mid-collection aborts the run."*
     - Meanwhile, `preregistration.md` §5.5 (lines 410–413) and §10 item 4 (lines 674–676) explicitly enumerate the six governed-source pins verified by admission and finalization as `(_prin_core.pyd, both PRIN publication generators, and all three REFERENCE sources)`.
     - In `exp002_r1_driver.py`, `_verify_all_pins()` implements the §5.5 / §10 item 4 set (`_prin_core.pyd` + 2 PRIN generators + 3 `REFERENCE` sources). `INPUT_MANIFEST` (`paper/artefact_manifest.json` against `INPUT_MANIFEST_SHA`) is verified at the start of `_snapshot()` (line 1353, before any collector runs) and recorded in `identity["input_manifest_sha256"]` (verified by `check_run_complete` at line 1824), while `collect_reproduction` re-runs `verify_manifest(snapshot, INPUT_MANIFEST)` after rendering (line 1297). As shown by the synthetic probe in [`input-manifest-finalization-probe.txt`](../../../EVIDENCE/exp002-r1-e2/input-manifest-finalization-probe.txt), if `_snapshot` is stubbed and `INPUT_MANIFEST` is mutated mid-collection during `api` mode, `_verify_all_pins()` at finalization does not re-hash `INPUT_MANIFEST`.
     - **Why `E2-OBS-1` is non-blocking (D4):** On any real repository run, `paper/artefact_manifest.json` is a tracked file checked clean by `git diff --name-only HEAD` in `_admission()` before `_reserve()`, hash-verified against `INPUT_MANIFEST_SHA` in `_snapshot()` before any collector runs, and all 172 JSON inputs are copied via `read_verified_no_follow` into the per-run isolated `inputs/` snapshot before collection. No collector writes to `paper/artefact_manifest.json`. Thus no scientific measurement, provenance guarantee, or abort criterion is weakened. Adding `_digest(read_no_follow(INPUT_MANIFEST, "input manifest")) == INPUT_MANIFEST_SHA` to `_verify_all_pins()` (or aligning §1.1's wording with §5.5) is recorded as a non-blocking observation for the maintainer.

---

## 4. S2-Class Retro-Audit of S4 Code Changes (Task 4)

Per Development Workflow §7, `DOCS/audits/2026-10-15-exp002-d1-correction-audit.md` §S4.13–§S4.16, `DOCS/reports/041-project-state.md`, and [`e2-review-packet.md`](e2-review-packet.md) §4, E2 performed the independent S2-class retro-audit of the two code changes landed during the S4 documentation session of `EXP-002-D1` (`EXP002D1-S4-F2` at `814b670c22dcbfee9de5a1d9d7fc602203f14a56` and `EXP002D1-S4-F3` at `67100a69bfdd353d3be06e35c04956795f56e805`) and the PR #35 follow-up commits (`33520b6216bdbeae6345beed2c2ce1b96ebdc390` and `a570aa7f5132b4f8c09699395d8cc9c47f45cf56`).

### 4.1 Retro-Audit of `EXP002D1-S4-F2` (`814b670c`, `parity/test_parity_publication.py`)

- **Inspected artefacts:** `git show 814b670c22dcbfee9de5a1d9d7fc602203f14a56 -- parity/test_parity_publication.py` ([`retro-s4f2-814b670c.txt`](../../../EVIDENCE/exp002-r1-e2/retro-s4f2-814b670c.txt)), [`EVIDENCE/exp002-d1-s4/pr34-review/adjudication.md`](../../../EVIDENCE/exp002-d1-s4/pr34-review/adjudication.md), [`EVIDENCE/exp002-d1-s4/pr34-review/negative-controls.txt`](../../../EVIDENCE/exp002-d1-s4/pr34-review/negative-controls.txt), and fresh local pytest execution ([`retro-s4f2-pytest.txt`](../../../EVIDENCE/exp002-r1-e2/retro-s4f2-pytest.txt)).
- **Checklist verification (`e2-review-packet.md` §4.1):**
  1. **Root cause & platform-scoping mechanism:** `test_reference_arm_reproduces_e3_reference_arm` previously asserted that an in-process render by `prinet==3.0.0` reproduces the Windows-authored `normalized_sha256` in `RUN-20261012T170147Z-da53ea1-reproduction-reference-cpu/reproduction.json` on *every* OS. Because Matplotlib rasterizes and subsets fonts through the host OS FreeType build and font stack, figures (`28` PDF/PNG files) differ across OSes while `.tex` tables (`11` files) do not. `814b670c` reads `E3_REFERENCE_PLATFORM = E3_REFERENCE_RECORD["environment"]["platform"]` (`"Windows-11-10.0.26300-SP0"`) from the frozen record itself and sets `_ON_RECORD_PLATFORM = platform.platform() == E3_REFERENCE_PLATFORM` — never hard-coding an OS name.
  2. **Authoring-platform invariance:** When `_ON_RECORD_PLATFORM` is `True` (on the authoritative Windows host), all `39` files (both `.tex` tables and `.pdf`/`.png` figures) still undergo the exact `digest == E3_REFERENCE_NORMALIZED[rel_path]` assertion.
  3. **Off-platform table & structural guarantees:** When `_ON_RECORD_PLATFORM` is `False` (e.g. Linux/macOS hosted runners), all `11` `.tex` tables (`rel_path.endswith(".tex")`) **still** require byte-exact `digest == E3_REFERENCE_NORMALIZED[rel_path]`, while the `28` figures must still render, be non-empty (`len(raw) > 0`), and pass `driver.normalized_bytes(raw, suffix)` container/chunk validation (`len(normalized) > 0`).
  4. **Primary H3 comparison untouched:** `test_prin_matches_reference_under_registered_comparison` (lines 204–219 of `parity/test_parity_publication.py`) was not modified and compares same-process PRIN vs reference renders across all `39` files on every platform.
  5. **Mechanism pin & four negative controls:** `test_digest_tie_is_scoped_by_the_records_own_platform` pins the record schema and branch selection. The four negative controls in [`EVIDENCE/exp002-d1-s4/pr34-review/negative-controls.txt`](../../../EVIDENCE/exp002-d1-s4/pr34-review/negative-controls.txt) prove non-vacuity:
     - `NEGCTL=corrupt-figure` (authoring platform): **FAILED** (`1 failed, 38 passed`, exit `1`) — proves figure byte-exact comparison is live on Windows.
     - `NEGCTL=corrupt-tex` (authoring platform): **FAILED** (`1 failed, 38 passed`, exit `1`) — proves table byte-exact comparison is live on Windows.
     - `NEGCTL=bogus+corrupt-figure` (off-platform): **PASSED** (`39 passed`, exit `0`) — proves only the figure digest tie takes the structural branch off-platform.
     - `NEGCTL=bogus+corrupt-tex` (off-platform): **FAILED** (`1 failed, 38 passed`, exit `1`) — proves tables remain byte-exact off-platform.
  6. **Independent local execution:** `.venv\Scripts\python.exe -m pytest parity/test_parity_publication.py --basetemp=.pytest_basetemp -o faulthandler_timeout=300` passed **`94 passed in 12.60s`** (exit `0`, [`retro-s4f2-pytest.txt`](../../../EVIDENCE/exp002-r1-e2/retro-s4f2-pytest.txt)).
- **Retro-Audit Verdict (`EXP002D1-S4-F2`):** **PASS (RATIFIED, 0 findings).** The change corrects a false cross-OS byte-identity assumption on a single-OS record without weakening H3 or the authoritative Windows gate.

### 4.2 Retro-Audit of `EXP002D1-S4-F3` (`67100a69`) and PR #35 Follow-Up (`33520b62` / `a570aa7f`)

- **Inspected artefacts:** `git show 67100a69bfdd353d3be06e35c04956795f56e805 -- tests/test_acceptance_subconscious.py` and `git diff 157ce5bc..5677858c -- tests/test_acceptance_subconscious.py benchmarks/y4q1_5_benchmarks.py tests/test_acceptance_y4q1_5.py tests/conftest.py` ([`retro-s4f3-diffs.txt`](../../../EVIDENCE/exp002-r1-e2/retro-s4f3-diffs.txt)), [`EVIDENCE/exp002-d1-s4/gate/dv032-fix/FIX.md`](../../../EVIDENCE/exp002-d1-s4/gate/dv032-fix/FIX.md), [`EVIDENCE/exp002-d1-s4/gate/dv032-fix/verify/summary.txt`](../../../EVIDENCE/exp002-d1-s4/gate/dv032-fix/verify/summary.txt), [`EVIDENCE/exp002-d1-s4/gate/dv032-fix/sensitivity/run2-corrected.txt`](../../../EVIDENCE/exp002-d1-s4/gate/dv032-fix/sensitivity/run2-corrected.txt), and fresh local pytest execution ([`retro-s4f3-pytest.txt`](../../../EVIDENCE/exp002-r1-e2/retro-s4f3-pytest.txt)).
- **Checklist verification (`e2-review-packet.md` §4.2):**
  1. **`67100a69` (`tests/test_acceptance_subconscious.py::TestIntegration::test_no_gpu_throughput_regression`, DV-032 item 1):**
     - Replaced the OS-scheduler-contaminated wall-clock ratio (`t_with_daemon / t_baseline < 1.30` over `_dummy_work(n=1_000_000)`, where 3 daemon inferences cost `~4.5 ms` against a `~420 ms` window — a `~1.1%` signal buried `~27x` below its `30%` tolerance that failed at `22.07x` under Windows host contention) with:
       - A paired process-CPU measurement (`time.process_time()`) over `_DUMMY_WORK_ITERATIONS = 8_000_000` (`~480 ms`, lengthening the sample per Testing Standards §7 item 6 so the `15.625 ms` Windows process-time tick moves the ratio by `~3%` rather than `~25%`), bounded by `_DAEMON_CPU_RATIO_LIMIT = 1.60` (sized from the 8-repetition distribution in `tolerance-probe.txt`: quiet mean `1.03`, saturated mean `1.02`, worst observed `1.1429`).
       - A handled-state drain (`_drain_submitted_inferences`, awaiting `inference_count + error_count >= submitted` rather than queue emptiness so in-flight inferences are included in the CPU window).
       - Load-invariant deterministic assertions (`error_count == 0`, `dlq_size == 0`, `inference_count >= _MIN_DAEMON_INFERENCES` (`3`)).
     - Verified positive and negative controls in [`EVIDENCE/exp002-d1-s4/gate/dv032-fix/verify/summary.txt`](../../../EVIDENCE/exp002-d1-s4/gate/dv032-fix/verify/summary.txt) and [`sensitivity/run2-corrected.txt`](../../../EVIDENCE/exp002-d1-s4/gate/dv032-fix/sensitivity/run2-corrected.txt):
       - Quiet host (`3/3` passed, ratio `1.03`); saturated 100%-CPU host (`3/3` passed, ratio `1.02`).
       - CPU-hog negative control on quiet host: **FAILED as required** (`Daemon process-CPU overhead ratio 2.03 > 1.6`).
       - Erroring-daemon negative control: **FAILED as required** (`daemon reported 3 inference errors`).
       - Residual limitation under 100% host saturation (`loaded-negctl-cpu` ratio `1.02 <= 1.60` because the single in-process hog thread is itself CPU-starved by the 16 host load processes) is honestly measured and documented in `FIX.md` and `DOCS/reports/DEFERRED_VALIDATION_REGISTER.md` (DV-032).
     - *Non-blocking citation note (`E2-OBS-2`):* [`e2-review-packet.md`](e2-review-packet.md) §4.2 cites the pre-collection scratch filenames `EVIDENCE/exp002-d1-s4/gate/dv032-fix/dv032-verify2.txt` and `dv032-sensitivity2.txt`; in the committed `EVIDENCE/exp002-d1-s4/` bundle (indexed by [`EVIDENCE/exp002-d1-s4/gate/dv032-fix/README.md`](../../../EVIDENCE/exp002-d1-s4/gate/dv032-fix/README.md)), those exact files live at `EVIDENCE/exp002-d1-s4/gate/dv032-fix/verify/summary.txt` and `EVIDENCE/exp002-d1-s4/gate/dv032-fix/sensitivity/run2-corrected.txt`.
  2. **`33520b62` + `a570aa7f` (`benchmarks/y4q1_5_benchmarks.py`, `tests/test_acceptance_y4q1_5.py`, `tests/conftest.py`, DV-032 item 2):**
     - `33520b62` added optional `max_frames: int | None = None` and `warmup_frames: int | None = None` to `run_timed_session` (preserving default wall-clock behavior when `None`), converted `TestSessionRunnerSmoke::test_deterministic_seed` to a deterministic fixed-frame check (`max_frames=100, warmup_frames=20`) asserting exact frame/interval counts, `pytest.approx(..., rel=1e-6, abs=1e-6)` metric equality for `seed=42` vs `seed=42`, and metric inequality for `seed=42` vs `seed=99` (in-test negative control), and removed `test_deterministic_seed` from `_TIMING_NODES` in `tests/conftest.py`.
     - `a570aa7f` hardened `run_timed_session` in response to PR #35 review: strict input validation rejecting `bool`, negative, or non-finite frame/duration arguments; per-batch clamping `min(FRAMES_PER_BATCH, ...)` so non-multiple `max_frames`/`warmup_frames` stop at the exact cap; tail-frame flushing via `_flush_interval()` with `partial_interval` tagging; `len(pt_phases_interval) >= 1` support; and frame-weighted aggregation (`_weighted_mean_and_std`) avoiding synthetic `0.0` dilution on 1-frame remainder batches, accompanied by 3 new unit tests (`test_zero_duration_fixed_frame_session_succeeds`, `test_non_multiple_and_short_frame_caps_preserve_tail_frames`, `test_invalid_frame_caps_and_durations_raise_value_error`).
  3. **Independent local execution:** `.venv\Scripts\python.exe -m pytest tests/test_acceptance_subconscious.py tests/test_acceptance_y4q1_5.py -k "test_no_gpu_throughput_regression or TestSessionRunnerSmoke" --basetemp=.pytest_basetemp -o faulthandler_timeout=300` passed **`8 passed, 0 skipped, 75 deselected in 25.00s`** (exit `0`, [`retro-s4f3-pytest.txt`](../../../EVIDENCE/exp002-r1-e2/retro-s4f3-pytest.txt)).
- **Retro-Audit Verdict (`EXP002D1-S4-F3` + PR #35 follow-up):** **PASS (RATIFIED, 0 blocking findings; 1 non-blocking doc path note `E2-OBS-2`).**

---

## 5. Independent Reproduction of E1 Local Evidence (Task 5)

All E1 local evidence claims were independently reproduced from current working-tree bytes on `campaign/exp002-r1-e2` (`bdaae83f2f384fba3c8d33013c40c6a2f4f011b5`):

1. **Recomputation of all 19 provenance digests (`EVIDENCE/exp002-r1-e1/provenance-hashes.txt`):**
   - Every row in [`EVIDENCE/exp002-r1-e1/provenance-hashes.txt`](../../../EVIDENCE/exp002-r1-e1/provenance-hashes.txt) (`19` files: `paper/artefact_manifest.json`, `python/prin/{__init__.py,_public_api.py,_deprecation.py,_prin_core.pyd}`, `python/prin/reporting/{_artifacts.py,figure_generation.py,table_generation.py}`, `tools/reproduce.py`, 3 `REFERENCE` sources, 4 `EXP-002-r1` docs, `exp002_r1_driver.py`, `test_exp002_r1_driver.py`, and `EVIDENCE/exp002-r1-e1/dv047-closure.txt`) was recomputed from live disk bytes ([`e1-digests-recomputed.txt`](../../../EVIDENCE/exp002-r1-e2/e1-digests-recomputed.txt)): **`ROWS=19 MISMATCHES=0`** (exit `0`).
   - Key deliverable digests verified:
     - `DOCS/experiments/EXP-002-r1-api-benchmark-result-and-reproduction-parity/preregistration.md`: `50,885` B, `c0e5a77b4b7a9815dd452114329b899b337543a100735495b596a0bd3e82a523`
     - `benchmarks/campaign/exp002_r1_driver.py`: `72,355` B, `f122be9833ed49e70a2333c6c4e1a482fb2e5efaf06914d456b296e7bd218185`
     - `tests/test_exp002_r1_driver.py`: `144,745` B, `69afc0b3169add884b531a6d7b5752e623db7084986d62ac15057cf66174792c`
     - `python/prin/_prin_core.pyd`: `5,127,680` B, `5b8ab8398fc341b66c4bd004628d542d414d0e6bb371072a5e32ab2f8e05bc05`
2. **Focused driver test suite and coverage (`focused-suite-coverage.txt`):**
   - Command: `.venv\Scripts\python.exe -m pytest tests/test_exp002_r1_driver.py --cov=benchmarks.campaign.exp002_r1_driver --cov-report=term-missing --basetemp=.pytest_basetemp -o faulthandler_timeout=300`
   - Result: **`343 passed, 1 skipped in 10.29s`**, line coverage **`98%`** (`865` statements, `17` missed defensive branches), exit `0` ([`focused-suite-coverage.txt`](../../../EVIDENCE/exp002-r1-e2/focused-suite-coverage.txt)).
3. **Opt-in governed-host `_prin_core.pyd` binary-pin test (`host-pin-test.txt`):**
   - Command: `$env:PRIN_EXP002_R1_HOST_PIN='1'; .venv\Scripts\python.exe -m pytest tests/test_exp002_r1_driver.py -k "live_prin_core_pyd_pin or real_generator_source_pins or real_driver_constants or allowed_output_roots" --basetemp=.pytest_basetemp -o faulthandler_timeout=300`
   - Result: **`4 passed, 340 deselected in 0.90s`**, exit `0` ([`host-pin-test.txt`](../../../EVIDENCE/exp002-r1-e2/host-pin-test.txt)).
4. **Rust advisory gate after PR #36 `Cargo.lock` bump (`cargo-audit.txt`):**
   - Command: `cargo audit`
   - Result: **`0` vulnerabilities found** (`3` allowed warnings: `bincode` `RUSTSEC-2025-0141`, `paste` `RUSTSEC-2024-0436`, `rustls-pemfile` `RUSTSEC-2025-0134`), confirming that PR #36's minimal `Cargo.lock` bump (`rustls-webpki 0.103.16`, `webpki-roots 1.0.10`) keeps `RUSTSEC-2026-0381` and `RUSTSEC-2026-0382` closed, exit `0` ([`cargo-audit.txt`](../../../EVIDENCE/exp002-r1-e2/cargo-audit.txt)).
5. **`.gitattributes` and `.gitignore` stage-isolation rules (`gitattributes-and-ignore.txt`):**
   - Confirmed `EVIDENCE/exp002-r1-e*/** -text whitespace=-trailing-space` and `benchmarks/results/** -text whitespace=-trailing-space` preserve exact CRLF/LF bytes across `exp002-r1-e1`..`e5` and `benchmarks/results/EXP-002-r1/**`, while `.gitignore` rule `DOCS/test_and_benchmark_results/` gitignores `DOCS/test_and_benchmark_results/EXP-002-r1/**` ([`gitattributes-and-ignore.txt`](../../../EVIDENCE/exp002-r1-e2/gitattributes-and-ignore.txt)).

---

## 6. Classified Findings and Observations

### 6.1 Blocking Findings

- **None (`0` blocking findings).**

### 6.2 Non-Blocking Observations

| ID | Severity / Class | Target | Description and Disposition |
|---|---|---|---|
| `E2-OBS-1` | Non-blocking (`D4` protocol-prose vs helper-scope alignment) | `preregistration.md` §1.1 vs §5.5 & `exp002_r1_driver.py::_verify_all_pins` | `preregistration.md` §1.1 (lines 124–131) lists `paper/artefact_manifest.json` alongside `_prin_core.pyd`, the two PRIN generators, and the three `REFERENCE` files, and states that admission and finalization verify "all governed-source pins". In §5.5 (lines 410–413), §10 item 4 (lines 674–676), and `exp002_r1_driver.py::_verify_all_pins()` (lines 1095–1109), the six pins re-verified at admission and finalization are explicitly `(_prin_core.pyd, both PRIN publication generators, and all three REFERENCE sources)`, whereas `INPUT_MANIFEST_SHA` (`paper/artefact_manifest.json`) is verified at the start of `_snapshot()` (before any collector runs) and in `check_run_complete()` (and `verify_manifest(snapshot, INPUT_MANIFEST)` is re-run at the end of `collect_reproduction()`). Because `paper/artefact_manifest.json` is tracked (`git diff --name-only HEAD` checked at `_admission()`), hash-verified in `_snapshot()` before collection, and never written by any collector, no E3 provenance or abort guarantee is weakened ([`input-manifest-finalization-probe.txt`](../../../EVIDENCE/exp002-r1-e2/input-manifest-finalization-probe.txt)). **Disposition:** Non-blocking; recorded for visibility. No silent driver or protocol edit made during E2. |
| `E2-OBS-2` | Non-blocking (`D4` handoff-packet path citation) | `e2-review-packet.md` §4.2 | `e2-review-packet.md` §4.2 cites pre-collection scratch names `EVIDENCE/exp002-d1-s4/gate/dv032-fix/dv032-verify2.txt` and `dv032-sensitivity2.txt`. In the committed and indexed `EVIDENCE/exp002-d1-s4/gate/dv032-fix/` directory ([`README.md`](../../../EVIDENCE/exp002-d1-s4/gate/dv032-fix/README.md)), those two records are stored at [`EVIDENCE/exp002-d1-s4/gate/dv032-fix/verify/summary.txt`](../../../EVIDENCE/exp002-d1-s4/gate/dv032-fix/verify/summary.txt) and [`EVIDENCE/exp002-d1-s4/gate/dv032-fix/sensitivity/run2-corrected.txt`](../../../EVIDENCE/exp002-d1-s4/gate/dv032-fix/sensitivity/run2-corrected.txt). **Disposition:** Resolved by inspecting and cross-referencing the exact committed paths in Section 4.2 above. |
| `E2-OBS-3` | Non-blocking (workstation environment note) | Local Snyk SCA `all_projects=true` vs `.kilo/package-lock.json` | As documented in [`EVIDENCE/exp002-r1-e1/verification-gate.txt`](../../../EVIDENCE/exp002-r1-e1/verification-gate.txt) and [`kilo-sca-finding-context.txt`](../../../EVIDENCE/exp002-r1-e2/kilo-sca-finding-context.txt), an untracked, gitignored local agent-tooling lockfile (`.kilo/package-lock.json`, outside PRIN's tracked tree where `git ls-files .kilo` contains only `.kilo/agents/data.md`) causes `snyk_sca_scan` with `all_projects=true` on this workstation to report transitive npm advisories (`axios`, `follow-redirects`) in `.kilo/package-lock.json` while reporting `0` issues on `pyproject.toml` and `DOCS/sphinx/requirements.txt`. Hosted `snyk` workflow run `39496143043` (`snyk-rust`, `snyk-python (3.12)`, `snyk-python (3.13)`, `snyk-code`) and local `cargo audit` / `pip_audit` all pass with `0` vulnerabilities. **Disposition:** Non-blocking workstation-only untracked file outside repository scope. |

---

## 7. Approval Recommendation and Maintainer Sign-Off Procedure

### 7.1 E2 Recommendation

All five §10 review items in [`preregistration.md`](preregistration.md), all five PR #36 remediation checks in [`e2-review-packet.md`](e2-review-packet.md) §5 (a)–(e), the S2-class retro-audit of `EXP002D1-S4-F2`, `EXP002D1-S4-F3`, and PR #35 follow-up commits (`33520b62`/`a570aa7f`), and the full local/hosted E1 evidence bundle have been independently verified with **0 blocking findings**.

**E2 recommends that the maintainer grant scientific approval to `EXP-002-r1` (`preregistration.md`) and authorize session `EXP-002-r1 E3`.**

### 7.2 Required Sequence for Maintainer Approval and E3 Release

Before `EXP-002-r1 E3` (`benchmarks.campaign.exp002_r1_driver`) can execute:

1. **Merge PR #36 (`campaign/exp002-r1-e1`) and this E2 PR (`campaign/exp002-r1-e2`)** as governed by the maintainer.
2. **Record dated maintainer approval in [`preregistration.md`](preregistration.md):**
   - Update line 3 from `**Status:** DRAFT` to `**Status:** APPROVED`.
   - Update line 7 from `**Maintainer approval:** NOT GRANTED (E1 draft; requires E2 independent review and dated maintainer signature before E3)` to `**Maintainer approval:** MichaelMaillet, YYYY-MM-DD UTC` (with the actual UTC date of sign-off).
   - Commit the approved `preregistration.md` on a clean tree so the E3 driver's `_admission()` gate (`_parse_approval_header`, `git show <F>:...`, and `git merge-base --is-ancestor <F> <R>`) can verify the committed approval commit `F` as an ancestor of the clean execution commit `R`.
