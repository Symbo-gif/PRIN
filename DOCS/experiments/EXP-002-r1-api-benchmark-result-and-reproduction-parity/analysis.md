# EXP-002-r1 — E4 Analysis Record

**Status:** ANALYSED — the frozen decision rules (pre-registration §4.1, §5.2, §5.4, §5.5, §11.1–§11.3) were
applied to the five immutable E3 records under `benchmarks/results/EXP-002-r1/`.
**H1 `CONFIRMED`, H2 `CONFIRMED`, H3 `CONFIRMED` (primary approved §5.4 comparison policy), H4 `CONFIRMED`.**
The pre-exposure §11.3 sensitivity diagnostic policy evaluated to `14/39` equal, with **100% of the 25 residuals
classified into registered writer/host I/O classes** (`14` `pdf_info_keyset`, `11` `tex_crlf_line_terminator`,
and **`0` unclassified residuals**).
**The campaign plan §10.4 D1 flag is NOT RAISED (`False`).**

**Record date:** 2026-10-21 / 2026-10-22 UTC.
**Session:** EXP-002-r1-E4 — track C1, E4 (Analysis and Hypothesis Adjudication). Predecessor EXP-002-r1-E3, successor EXP-002-r1-E5.
**Branch / PR:** `campaign/exp002-r1-e4`.
**AI pair drafting this analysis:** Antigravity (Advanced Agentic Coding, Experimentation Standards §4 authorship disclosure).
Maintainer: MichaelMaillet.
**Pre-registration freeze SHA `F`:** `10ac3c04f44a1f68869c94c1dfae1c1c1a189460` (preregistration commit; campaign plan §12.4).
Protocol SHA-256: `903d65bcae7287042a3ebf6498ffaa9f45d13a697666249bdf5fe5bbaaa84e72`.
**Execution source `R`:** `e65076eb7ae97100d40ea32c60229dd40ed51033` (the clean E3 execution HEAD commit).
**Analysis code (campaign plan §7.4 item 2):** [`analysis/exp002_r1_e4_analysis.py`](analysis/exp002_r1_e4_analysis.py)
(module SHA-256 `d7ea99b8c80fb40e8473286fa05afa317c9b6987bd5db659d34bbce8936265a8`).

> **Outcome-exposure disclosure:** This re-run protocol and analysis were executed after full exposure to `EXP-002`'s
> E3–E5 outcomes (`H1 CONFIRMED`, `H2 CONFIRMED`, `H3 REFUTED` at 21/39 under §5.4, `H4 CONFIRMED`) and to `EXP-002-D1`
> S1–S4's root-cause decomposition and residual classification. Every `EXP-002-r1` verdict was computed solely from
> fresh, unmanipulated `RUN-*-r1-*` directories created at E3 under `benchmarks/results/EXP-002-r1/`.

---

## 1. Pre-Flight Verification of E3 Records and Baseline

Before executing the analysis module on the live E3 data, all five registered run directories were verified
against the repository index, manifest verifications, and immutability invariants:

| Run Mode | Run Directory | Manifest Files | Status | `abort.json` |
|---|---|---:|---|---|
| `api` | `RUN-20261021T183011Z-e65076e-r1-api-cpu` | 2 | `COMPLETED` | ABSENT |
| `conclusions` | `RUN-20261021T183952Z-e65076e-r1-conclusions-cpu` | 2 | `COMPLETED` | ABSENT |
| `reference` | `RUN-20261021T184447Z-e65076e-r1-reproduction-reference-cpu` | 2 | `COMPLETED` | ABSENT |
| `prin` | `RUN-20261021T184600Z-e65076e-r1-reproduction-prin-cpu` | 2 | `COMPLETED` | ABSENT |
| `repeatability` | `RUN-20261021T184707Z-e65076e-r1-seedrep0-prin-cpu` | 2 | `COMPLETED` | ABSENT |

### Strict Predecessor Immutability
Predecessor roots (`DOCS/experiments/EXP-002-api-benchmark-result-and-reproduction-parity/`, `benchmarks/results/EXP-002/`,
`DOCS/test_and_benchmark_results/EXP-002/`, `EVIDENCE/0159/`..`0163/`, `EVIDENCE/exp002-d1-s1/`..`s4/`) were verified:
`git diff HEAD -- <predecessor roots>` returned **0 bytes** (completely untouched and immutable).

### Retained Publication Files
The uncommitted publication directories under `DOCS/test_and_benchmark_results/EXP-002-r1/` were verified intact:
each of the three reproduction arms (`r1-reproduction-reference-cpu`, `r1-reproduction-prin-cpu`, `r1-seedrep0-prin-cpu`)
contains exactly 39 publication files (14 PDF, 14 PNG, 11 TeX) and the verified `inputs/` directory.

---

## 2. Analysis Implementation and Quality Verification

The E4 analysis engine was authored in [`DOCS/experiments/EXP-002-r1-api-benchmark-result-and-reproduction-parity/analysis/exp002_r1_e4_analysis.py`](analysis/exp002_r1_e4_analysis.py).
It enforces standard-library-only execution (never importing `prin`, `prinet`, or Matplotlib), strict JSON parsing
(refusing BOM, duplicate keys, and non-finite floats), reparse-point junction defense on Windows, exact-key envelope checks,
and atomic file replacement with prefix `.exp002-r1-e4-`.

The companion unit test suite [`tests/test_exp002_r1_e4_analysis.py`](../../../tests/test_exp002_r1_e4_analysis.py)
contains 176 synthetic test cases covering all valid-counterexample and coverage branches, both H3 policies,
H4 canonical projection, D1 flag gating, link refusal, and output confinement.

### Quality Gate Results (Authoritative Regime)
- **Pytest:** 176 passed in 3,441.14 s (exit 0):
  `.venv\Scripts\python -m pytest tests/test_exp002_r1_e4_analysis.py --basetemp=.pytest_basetemp -o faulthandler_timeout=300`
- **Ruff Check:** Passed 0 errors across workspace:
  `.venv\Scripts\ruff check python/ tests/ benchmarks/ tools/ parity/ DOCS/experiments/`
- **Ruff Format:** Passed clean (336 files formatted):
  `.venv\Scripts\ruff format --check python/ tests/ benchmarks/ tools/ parity/`
  `.venv\Scripts\ruff format --check DOCS/experiments/ --config "include = ['*.py', '*.pyi', '*.ipynb']"`
- **Strict MyPy:** Passed 0 issues:
  `.venv\Scripts\mypy DOCS/experiments/ --strict`
- **Bandit Security Scan:** Passed 0 issues (30,859 LOC scanned):
  `.venv\Scripts\python -m bandit -r python/prin DOCS/experiments -c pyproject.toml`

---

## 3. Hypothesis Adjudication and Findings

The analysis script was executed against the real E3 raw records, producing the following frozen verdicts:

```text
H1: CONFIRMED
H2: CONFIRMED
H3: CONFIRMED
H4: CONFIRMED
H3_sensitivity_policy: REFUTED
D1 flag: False
```

### H1 — API Parity: **CONFIRMED**
- **Public API Resolution:** All 175 expected names (`172` legacy reference names + `3` PRIN additions: `BackendUnavailableError`, `__version__`, `core_version`) resolved successfully.
- **Classification:** 172 callable/class exports, 3 scalar constants (`int`, `str`). 0 `None`, 0 unsupported, 0 unresolved, 0 unverifiable.
- **Ownership Traceability:** 172/172 legacy names are accounted for in both the Migration Guide and `DOCS/baselines/wp001_api_traceability.md`.
- **Export Inventory:** Observed export list has exactly 175 entries with 0 duplicates, 0 unexpected exports, and 0 removals.
- **Frozen Contract Check:** `frozen_missing == []`, `frozen_extra == []`.

### H2 — Archival Historical Conclusions Parity: **CONFIRMED**
- **Predicate Evaluation:** All 62 claim-comparator records evaluated to their independently pre-registered values (`observed == expected` for 62/62).
- **Family Breakdown:**
  - `C01` (Bimodality coefficient threshold `> 0.555` on 5 chimera seeds): **5/5** agree.
  - `C02` (42 `(K, alpha)` parameter grid rows matching historical `chimera_detected` flag): **42/42** agree.
  - `C03` (Oscillator scaling `N in {128, 256, 512, 1024}`, mean `> 0.5`): **4/4** agree.
  - `C04` (Ring vs community topology comparison): **5/5** agree.
  - `C05` (Goldilocks zone CSR width and full coupling onset): **6/6** agree.
- Every operand, path, operator, and unit was re-derived from the 172 frozen JSON inputs in `paper/artefact_manifest.json` and verified identical.

### H3 — Publication Fidelity: **CONFIRMED** (Approved §5.4 Policy, Primary)
Under the governing, approved §5.4 comparison policy (canonicalized CRLF->LF tables, normalized PNGs, 4-key PDF Info removal and xref pointer canonicalization):
- **Generated Files:** Both arms produced exactly the 39 registered publication files.
- **Comparison Outcome:** **39/39 generated files are EQUAL** between reference and PRIN reproduction arms:
  - **PDF Figures:** 14/14 equal.
  - **PNG Figures:** 14/14 equal.
  - **LaTeX Tables:** 11/11 equal (and 11/11 equal to the archived historical tables in `REFERENCE/paper/tables/`).
- **Veracity:** The 34 drawing divergences identified in `EXP-002-D1` are completely resolved.

### H3 Diagnostic Residual Classification (§11.3 Policy): **DISCLOSED WRITER-PROPERTY DIAGNOSTIC**
Under the pre-exposure §11.3 sensitivity policy (raw table bytes without CRLF normalization, and PDF Info value masking retaining key sets):
- **Equal Files:** 14/39 equal (all 14 PNG figures are equal).
- **Differing Files:** 25/39 differ (14 PDF figures, 11 LaTeX tables).
- **Diagnostic Residual Decomposition:**
  In accordance with `preregistration.md` §11.1 item 2, all 25 differing files were subjected to structural byte and keyset inspection:
  1. **14 PDF Figures (`pdf_info_keyset`):** In all 14 cases, the difference is strictly the `/Info` dictionary key set. Reference passes no metadata, so Matplotlib writes 3 keys (`Creator`, `Producer`, `CreationDate`), while PRIN passes fixed metadata required for H4 determinism, writing 4 keys (`Creator`, `Producer`, `CreationDate`, `ModDate`). All 14 files are byte-identical across all drawing streams, fonts, and contents under §5.4.
  2. **11 LaTeX Tables (`tex_crlf_line_terminator`):** In all 11 cases, the difference is strictly host text-mode newline translation. The reference writer on Windows wrote `CRLF` (e.g., CRLF count = 13 to 22), while PRIN wrote explicit `\n` (`LF`, CRLF count = 0). All 11 files are 100% byte-identical after CRLF->LF normalization.
  3. **Unclassified Residuals:** Exactly **`0` unclassified residuals** (100% of residuals accounted for by registered writer/host I/O classes).
- Because §5.4 is 39/39 equal and unclassified residuals are 0, H3's single final verdict is **`CONFIRMED`**.

### H4 — Repeatability Parity: **CONFIRMED**
- **Raw Byte Identity:** All 39 publication files have identical raw byte lengths and identical raw SHA-256 digests between the PRIN reproduction run (`r1-reproduction-prin-cpu`) and the independent PRIN repeatability run (`r1-seedrep0-prin-cpu`):
  - **PDF Figures:** 14/14 raw equal.
  - **PNG Figures:** 14/14 raw equal.
  - **LaTeX Tables:** 11/11 raw equal.
- Normalization or masking was not used; 39/39 files are byte-for-byte identical across separate process invocations.

---

## 4. Campaign D1 Escalation Status

**D1 Flag: NOT RAISED (`False`).**

Under campaign plan §10.4 and pre-registration §4.3:
- H1 is `CONFIRMED`.
- H2 is `CONFIRMED`.
- H3 is `CONFIRMED` under the governing §5.4 primary policy, with 0 unclassified residuals under the §11.3 diagnostic.
- H4 is `CONFIRMED`.
- No primary hypothesis is `REFUTED`.
- Parity criteria C1, F1, F2, and F4 are fully maintained.

---

## 5. Summary of Analysis Deliverables

All seven pre-registered analysis deliverables were generated and verified. Their SHA-256 digests are pinned below:

| Deliverable | Path | Bytes | SHA-256 Digest |
|---|---|---:|---|
| Deliverable 1 | [`analysis/api-census.csv`](analysis/api-census.csv) | 18,378 | `5656cb9b570889a911b35283b8a5cfdc55c5ec8e0f28ba35d34d8fec526e10c3` |
| Deliverable 2 | [`analysis/conclusions-census.csv`](analysis/conclusions-census.csv) | 10,872 | `0c01c59c8e1f32ea3ad173dddde117ad9a94b187289328da760e1c906e0bba85` |
| Deliverable 3 | [`analysis/reproduction-comparisons.csv`](analysis/reproduction-comparisons.csv) | 31,250 | `925b40b4b13f6e76ec62eed08f65b400d13da66c446f54766963804781f5e532` |
| Deliverable 4 | [`analysis/repeatability-comparisons.csv`](analysis/repeatability-comparisons.csv) | 7,445 | `18f91d6bf46bc0006225ab2d78ceaa058362466faaea63de753ff50035653027` |
| Deliverable 5 | [`analysis/summary.json`](analysis/summary.json) | 12,308 | `fcdb56250165f18d65c22d07f9caae1a9e0ff632f3dbcab0047046dabc9e01ad` |
| Deliverable 6 | [`analysis/sensitivity-residuals.json`](analysis/sensitivity-residuals.json) | 18,525 | `884c0c6ce0344e8e4757c99e5555e24ddb314be62a89f8619ed9108644a4de06` |
| Deliverable 7 | [`analysis/report-manifest.json`](analysis/report-manifest.json) | 19,209 | `6cd12f2d1bf0ed5f841d8e3945443a4fd16b689f7fd489f0435fd61baf8d9dc2` |

Additionally, the analysis engine populated the complete uncommitted set in `DOCS/test_and_benchmark_results/EXP-002-r1/analysis/`:
- `summary.json`: `fcdb56250165f18d65c22d07f9caae1a9e0ff632f3dbcab0047046dabc9e01ad`
- `api-mapping.csv`: `5656cb9b570889a911b35283b8a5cfdc55c5ec8e0f28ba35d34d8fec526e10c3`
- `conclusion-comparisons.csv`: `0c01c59c8e1f32ea3ad173dddde117ad9a94b187289328da760e1c906e0bba85`
- `reproduction-comparisons.csv`: `925b40b4b13f6e76ec62eed08f65b400d13da66c446f54766963804781f5e532`
- `error-distributions.json`: `afd3d1454dabdd12e12b504300b07996a12553cc262a16f6748c38d7a3fffb1e`
- `expected-vs-observed.md`: `1a27f264f02cd7e2bea0f1d6649ded3f797982d288b4ac870d358accd26bd4d7`
- `coverage-and-deferrals.md`: `4e82524ff0fa8b20cc2dbc2a13b5202730b4d5d6c01a0e107ec100574fb74dad`
- Root `report-manifest.json`: `6cd12f2d1bf0ed5f841d8e3945443a4fd16b689f7fd489f0435fd61baf8d9dc2`

---

## 6. Coverage and Deferrals (Owner Matrix)

In accordance with pre-registration §5.3, none of the historical claims owned elsewhere are discharged by this archival analysis:

| Historical Conclusion Class / Source | Scientific Owner | Status After EXP-002-r1 E4 |
|---|---|---|
| CPU throughput, coupling complexity, sweep speedups and CPU scaling | EXP-003, including DV036-F5 at 0166 and the DV-036 CPU gate before 0168 | OPEN — not discharged by EXP-002-r1 |
| GPU throughput (including OscilloSim's 1.95B claim), Triton/CUDA comparisons, training-step and bridge overhead | EXP-004; GPU/bridge DV-036 gate before 0173; DV-001/DV-003 limitations retained | OPEN — not discharged by EXP-002-r1 |
| Fresh chimera boundaries, topology/size effects and capacity relation/replication | EXP-005; corrected-SI exception retained | OPEN — not discharged by EXP-002-r1 |
| CUDA-tagged `y3q49_finite_size_scaling.json` fit ranking and `y3q49_phase_coherence.json` lifetime ranking | EXP-004 backend qualification and EXP-005 scientific replication; their CUDA-derived directions are not substituted with CPU measurements here | OPEN — not discharged by EXP-002-r1 |
| CLEVR-N/IP accuracy, PT-versus-SA statistical equivalence, ablations, freezing, parameter/FLOP efficiency, trained supercritical regimes, gradient/representation geometry and training curves | EXP-006, with EXP-004 performance dependencies; historical intervals/p-values remain reference-only | OPEN — not discharged by EXP-002-r1 |
| Daemon p95, MOT/IP evaluation, noise/velocity/occlusion and adversarial robustness | EXP-007, with EXP-006 training dependencies; CPU/DirectML/NPU dispositions retained | OPEN — not discharged by EXP-002-r1 |
| Linux/macOS/Metal, compiler-free wheel matrix and NPU/new capabilities | EXP-008; amendment #48 suspension and campaign section 5.4 unavailable-hardware rule | OPEN — not discharged by EXP-002-r1 |

---

## 7. Threats to Validity and Protocol Compliance

1. **Outcome Exposure:** Full disclosure is maintained that this re-run was conducted after outcome exposure to EXP-002 and EXP-002-D1.
2. **Re-run Namespace Isolation:** Raw artefacts reside strictly under `benchmarks/results/EXP-002-r1/` and publication outputs under `DOCS/test_and_benchmark_results/EXP-002-r1/`. Predecessor roots remain completely unedited.
3. **Determinism:** All analysis deliverables are deterministic censuses of finite, fixed populations without confidence interval estimation, sampling noise, or multiplicity adjustments.
4. **Environment Consistency:** Extension `python/prin/_prin_core.pyd` (9,290,240 bytes, SHA-256 `37392d067efa3983e384c94f4ac2268c4fad2f5ea929c529b3db50bff4fee99e`) was verified across all admission and retrospective gates.

---

## 8. Handoff to E5

EXP-002-r1 E4 analysis is **COMPLETE** and ready for E5 reporting:
1. All four primary hypotheses are **`CONFIRMED`**.
2. D1 flag is **`False`** (not raised).
3. The 25 diagnostic sensitivity residuals are 100% classified into registered writer/host I/O classes (`14` `pdf_info_keyset`, `11` `tex_crlf_line_terminator`, `0` unclassified).
4. All seven analysis deliverables are committed and manifested.
5. Stage E5 is authorized to draft `report.md`, execute clean-checkout reconstruction, and assemble the final report package.
