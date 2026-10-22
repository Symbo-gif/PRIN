# EXP-002-r1 E5 — Operator Execution Log

**Stage:** `EXP-002-r1-E5` (Report Stage, track C1).
**Date:** 2026-10-22 UTC.
**Branch:** `campaign/exp002-r1-e5` (created from `main` @ `fc0195a2`).
**Operator / maintainer:** MichaelMaillet.
**AI pair of record:** Antigravity (Advanced Agentic Coding).

---

## 1. Pre-Flight and Baseline Verification

- **PR #40 Status:** Merged into `main` by maintainer MichaelMaillet at commit `fc0195a2`.
- **Working Tree:**
  ```powershell
  git checkout main
  git pull origin main # fast-forward to fc0195a2
  git checkout -b campaign/exp002-r1-e5
  git status # clean working tree
  ```
- **Frozen Predecessors:** Verified immutable with `git diff fc0195a2 -- benchmarks/results/EXP-002/ EVIDENCE/0159/ ...` returning 0 bytes diff.

---

## 2. Step 1: Retained-Bytes Verification (Executed First)

- **Input Snapshots (172/172):**
  Verified against `paper/artefact_manifest.json` (`300cdc094d2b7d27ac8b1e2556b2e6ed4dad3333f0038b45c8f87ea81612cce5`):
  All 5 runs in `DOCS/test_and_benchmark_results/EXP-002-r1/<run-id>/inputs/` matched 172/172 files. Listing hash:
  `f4c239d06461ef3933930eefb9a91c3e1e04083e2e078418ef61852277242fb9` (identical across all 5 runs).
- **Publication Files (39/39):**
  Verified against manifested raw digests in each run's `reproduction.json`:
  - `r1-reproduction-reference-cpu`: 39/39 matched, listing hash `e38a1078d9ea2e17ddfd0d27af150581512aa402e125ee57e0c5bd0990e7bc5b`.
  - `r1-reproduction-prin-cpu`: 39/39 matched, listing hash `0f99f95524fff7e4e0e885e18c19d57e3360801921ea78f244aa7d8ab65f60fe`.
  - `r1-seedrep0-prin-cpu`: 39/39 matched, listing hash `0f99f95524fff7e4e0e885e18c19d57e3360801921ea78f244aa7d8ab65f60fe`.
- **Listing Identity:** PRIN reproduction and repeatability listings are identical, confirming H4 raw determinism on disk.
- Result: **PASS** (recorded in `retained-bytes-verification.txt`).

---

## 3. Step 2: Clean Detached-Worktree Regeneration

- Created detached worktree at `C:/dev/PRIN-worktree-e5-clean` at commit `c7c54d18`.
- Retained run directories and compiled extension `_prin_core.pyd` (`9,290,240 B`, SHA-256 `37392d06…ee99e`) were supplied.
- Executed:
  ```powershell
  .venv\Scripts\python -I analysis/exp002_r1_e4_analysis.py
  ```
- Output matched committed deliverables **8/8 byte-for-byte identical**:
  - `summary.json`: `fcdb56250165f18d65c22d07f9caae1a9e0ff632f3dbcab0047046dabc9e01ad`
  - `api-mapping.csv` / `api-census.csv`: `5656cb9b570889a911b35283b8a5cfdc55c5ec8e0f28ba35d34d8fec526e10c3`
  - `conclusion-comparisons.csv` / `conclusions-census.csv`: `0c01c59c8e1f32ea3ad173dddde117ad9a94b187289328da760e1c906e0bba85`
  - `reproduction-comparisons.csv`: `925b40b4b13f6e76ec62eed08f65b400d13da66c446f54766963804781f5e532`
  - `error-distributions.json`: `afd3d1454dabdd12e12b504300b07996a12553cc262a16f6748c38d7a3fffb1e`
  - `expected-vs-observed.md`: `1a27f264f02cd7e2bea0f1d6649ded3f797982d288b4ac870d358accd26bd4d7`
  - `coverage-and-deferrals.md`: `4e82524ff0fa8b20cc2dbc2a13b5202730b4d5d6c01a0e107ec100574fb74dad`
  - `report-manifest.json`: `6cd12f2d1bf0ed5f841d8e3945443a4fd16b689f7fd489f0435fd61baf8d9dc2`
  - Also `repeatability-comparisons.csv` (`18f91d6b…`) and `sensitivity-residuals.json` (`884c0c6c…`).
- Detached worktree cleanly removed with `git worktree remove --force`.
- Result: **PASS** (recorded in `regeneration-verification.txt`).

---

## 4. Step 3: Clean-Checkout Reconstruction

- Reconstructed both publication arms in gitignored directory `DOCS/test_and_benchmark_results/EXP-002-r1/e5-reconstruction/` using `collect_reproduction` under matched renderer environment (Python 3.14.0, Matplotlib 3.11.1, NumPy 2.5.1, Pillow 12.3.0, FreeType 2.14.3, backend Agg, font cache 146,692 B).
- **PRIN Arm vs E3 PRIN:** raw 39/39 equal, normalized 39/39 equal, sensitivity 39/39 equal. Listing hash: `0f99f95524fff7e4e0e885e18c19d57e3360801921ea78f244aa7d8ab65f60fe` (identical).
- **Reference Arm vs E3 Reference:** raw 25/39 equal (14 PDF figures differ due to reference unpinned wall-clock `CreationDate`), normalized 39/39 equal, sensitivity 39/39 equal. Listing hash: `9ee51086fa27083a2162da15e98587376c669e46a3c6d66e51bfd785e05d0e2e`.
- **Cross-Arm Reconstruction (Reference vs PRIN):**
  - Approved §5.4 policy: 39/39 equal.
  - Diagnostic §11.3 policy: 14/39 equal (14 PNG equal, 14 PDF and 11 TeX differ, matching the 25 residuals).
- Result: **PASS** (recorded in `reconstruction-verification.txt`).

---

## 5. Deliverables Authoring

1. `DOCS/experiments/EXP-002-r1-api-benchmark-result-and-reproduction-parity/report.md`:
   - Comprehensive E5 report authored, issuing all verdicts: H1 CONFIRMED, H2 CONFIRMED, H3 CONFIRMED (primary §5.4), H4 CONFIRMED.
   - Diagnostic §11.3 sensitivity policy: REFUTED (14/39 equal, 25 residuals 100% classified into 14 `pdf_info_keyset` and 11 `tex_crlf_line_terminator`, 0 unclassified).
   - Campaign plan §10.4 D1 flag: False (non-reversal verdict).
   - Slot for maintainer verification and acceptance.
2. `DOCS/experiments/EXP-002-api-benchmark-result-and-reproduction-parity/report.md` §15:
   - Appended Erratum 3 cross-referencing EXP-002-r1 E5 completion and non-reversal verdict. Predecessor record otherwise untouched.
3. `DOCS/sphinx/parity_report.rst`:
   - Added dated Update admonition (2026-10-22) recording EXP-002-r1 E5 completion and non-reversal verdict.
   - Updated `REFERENCE-HISTORICAL`, `paper/artefact_manifest.json`, and `tools/reproduce.py, repro.yml` table descriptions.
4. `DOCS/experiments/EXP-002-r1-api-benchmark-result-and-reproduction-parity/README.md`:
   - Status updated to E5 REPORTED. Current artefacts table updated.
5. `DOCS/experiments/README.md`:
   - Appended E2, E3, E4, and E5 stage progression narratives and updated table row.
6. `DOCS/sessions/SESSION_REGISTER.md`:
   - Updated line 5 entry point and narrative history. Session 0164 and downstream sessions held BLOCKED awaiting maintainer acceptance.

---

## 6. Evidence Assembly and Self-Check

- Assembled `EVIDENCE/exp002-r1-e5/` with `README.md`, `log.md`, `retained-bytes-verification.txt`, `regeneration-verification.txt`, `reconstruction-verification.txt`, `predecessor-immutability.txt`, and `SHA256SUMS.txt`.
- Executed:
  ```powershell
  .venv\Scripts\python -I EVIDENCE/exp002-d1-s3/index_selfcheck.py exp002-r1-e5
  ```
  Exit code: 0.

---

## 7. Quality Gate Verification

- **Governance Checks:**
  - `tools/wp001_baseline.py check`: Exit code 0.
  - `tools/check_global_session_registration.py`: Exit code 0 (checked 18 reports).
  - `tools/check_dv_register_gates.py`: Exit code 0 (checked 47 rows against 198 sessions).
  - `tools/check_skipif_probes.py`: Exit code 0.
- **Analysis Suite:**
  - `.venv\Scripts\python -m pytest tests/test_exp002_r1_e4_analysis.py --basetemp=.pytest_basetemp -o faulthandler_timeout=300`: 176 passed in 2942.11 s (Exit code 0).
- **Static Analysis & Security:**
  - `ruff check python/ tests/ benchmarks/ tools/ parity/ DOCS/experiments/`: Exit code 0.
  - `ruff format --check`: Exit code 0.
  - `mypy python/prin --strict`: Exit code 0 (62 files).
  - `mypy DOCS/experiments/ --strict`: Exit code 0 (4 files).
  - `interrogate -c pyproject.toml python/prin`: Exit code 0 (97.6% coverage).
  - `bandit -r python/prin DOCS/experiments -c pyproject.toml`: Exit code 0 (0 issues).
  - Clean Sphinx build (`Remove-Item -Recurse -Force DOCS/sphinx/_build; python -m sphinx.cmd.build -W --keep-going -b html DOCS/sphinx DOCS/sphinx/_build/html`): Exit code 0 (0 warnings).
  - `tests/test_wp001_baseline.py::test_secret_scan_is_blocking_and_covers_full_history`: Exit code 0.

