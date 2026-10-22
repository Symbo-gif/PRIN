# EXP-002-r1 — E5 report: API, benchmark-result, and reproduction parity (re-run, track C1)

**Status:** **ISSUED — pending maintainer verification and acceptance** — see §11. The exit condition for proceeding to session `0164` (EXP-003 E1) and downstream sessions `0165`–`0194` is satisfied by this report's **non-reversal verdict** (§8), but sessions `0164`–`0194` remain **BLOCKED** until the maintainer (`MichaelMaillet`) independently verifies and accepts this report (§8, §11; campaign plan §10.4 item 5).
**Verdicts:** **H1 `CONFIRMED`**, **H2 `CONFIRMED`**, **H3 `CONFIRMED`** (approved §5.4 comparison policy, primary), **H4 `CONFIRMED`**.
**Diagnostic writer-property policy (§11.3 policy):** Evaluated to `14/39` equal (`H3_sensitivity_policy REFUTED`), with **100% of the 25 residuals classified into registered writer/host I/O classes** (`14` `pdf_info_keyset`, `11` `tex_crlf_line_terminator`, and **`0` unclassified residuals**), confirming `EXP002D1-S2-F1` and upholding H3 `CONFIRMED`.
**Campaign plan §10.4 D1 flag:** **NOT RAISED (`False`)** — non-reversal verdict.
**Report date:** 2026-10-22 UTC.
**Session:** `EXP-002-r1-E5` (track C1, E5 — Report). **Predecessor:** `EXP-002-r1-E4` (E4 — Analysis). **Successor:** `0164` (EXP-003 / track C2, E1 — Pre-registration, **BLOCKED** pending maintainer acceptance).
**Branch / PR:** `campaign/exp002-r1-e5`.
**Operator / maintainer:** MichaelMaillet.
**AI pair drafting this report (Experimentation Standards §4 authorship disclosure):** Antigravity (Advanced Agentic Coding).
- **Stage-by-stage authorship across EXP-002-r1:**
  - E1 pre-registration body (`preregistration.md`), collection driver (`benchmarks/campaign/exp002_r1_driver.py`), driver tests (`tests/test_exp002_r1_driver.py`), and handoff packet (`e1-handoff.md`, `e2-review-packet.md`) were drafted by **Devin** (AI pair of record, drafting; baseline `M = 5677858c15d784d881b23d43dff5029d199b0a18`, PR #36).
  - E2 independent review, S4 retro-audit of `EXP002D1-S4-F2`/`F3`, Lean 4 / Z3 verification, and decision record (`e2-review.md`) were drafted by **Antigravity** (PR #37).
  - E3 execution commands, console logs, and validation records (`log.md`) were executed and recorded by **Antigravity** at the maintainer's direction (PR #38).
  - E4 registered analysis module (`analysis/exp002_r1_e4_analysis.py`), its 176 synthetic unit tests (`tests/test_exp002_r1_e4_analysis.py`), `analysis.md`, `summary.json`, and `report-manifest.json` were authored and verified by **Antigravity** (PR #40).
  - This E5 report (`report.md`), the Step 1 retained-bytes verification, the Step 2 clean detached-worktree regeneration, the Step 3 clean-checkout reconstruction, the independent recount, the Erratum 3 cross-reference in predecessor `EXP-002/report.md` §15, and the evidence package `EVIDENCE/exp002-r1-e5/` were drafted and executed by **Antigravity**.
- **Verification status:** Every count, digest, byte size, and classification in this report was verified from the committed E3 raw records, the retained publication roots, the committed E4 analysis module, and fresh clean-worktree and clean-checkout reconstructions in session `EXP-002-r1-E5`. Formal acceptance by maintainer `MichaelMaillet` is pending in §11.

> **Outcome-exposure disclosure (Experimentation Standards §1.1, §4; `EXP002D1-S2-F1`):** This re-run protocol is drafted **after full exposure** to `EXP-002`'s E3–E5 outcomes (`H1 CONFIRMED`, `H2 CONFIRMED`, `H3 REFUTED` at `21/39` under §5.4 and `5/39` under §11.3, `H4 CONFIRMED`) and to `EXP-002-D1` S1–S4's root-cause decomposition and residual classification (`39/39` equal under §5.4 and `14/39` equal under §11.3 on the corrected generator, with all `25` sensitivity-policy residuals proven in `EVIDENCE/exp002-d1-s2/both-policies-post-fix.txt` to be writer/host I/O properties and `0` unclassified). This disclosure is repeated in §1, §10, and §11 below and must be repeated verbatim in the E5 report.

| Record | Value |
|---|---|
| Pre-registration (frozen) | [`preregistration.md`](preregistration.md) @ `F = 10ac3c04f44a1f68869c94c1dfae1c1c1a189460`, frozen at first `RUN-` creation on `2026-10-21T18:30:11Z`; blob SHA-256 `dc2cf8d8340b8385f510447f738d131ea45d2d805db201a6339eef4fa7a86483` |
| E2 review and approval | [`e2-review.md`](e2-review.md) (`APPROVED` 2026-10-21 UTC, maintainer-ratified) |
| Execution source SHA `R` | `e65076eb7ae97100d40ea32c60229dd40ed51033` (commit `e65076e`; PR #38) |
| Execution log | [`log.md`](log.md) (E3, 2026-10-21 UTC; commit `e65076e`) |
| Input manifest | `paper/artefact_manifest.json` — `172` records (`16,047,018` bytes), SHA-256 `300cdc094d2b7d27ac8b1e2556b2e6ed4dad3333f0038b45c8f87ea81612cce5` |
| Analysis code (frozen) | [`analysis/exp002_r1_e4_analysis.py`](analysis/exp002_r1_e4_analysis.py) (SHA-256 `d7ea99b8c80fb40e8473286fa05afa317c9b6987bd5db659d34bbce8936265a8`); unit tests [`tests/test_exp002_r1_e4_analysis.py`](../../../tests/test_exp002_r1_e4_analysis.py) (176 synthetic tests) |
| Analysis record | [`analysis.md`](analysis.md) (E4, commit `fc0195a2`) |
| Output manifest | [`report-manifest.json`](report-manifest.json) (`19,209` bytes, SHA-256 `6cd12f2d1bf0ed5f841d8e3945443a4fd16b689f7fd489f0435fd61baf8d9dc2`) |
| Raw artefact root | [`benchmarks/results/EXP-002-r1/`](../../../benchmarks/results/EXP-002-r1/README.md) (five immutable `RUN-` directories) |
| Retained generated roots | `DOCS/test_and_benchmark_results/EXP-002-r1/<run-id>/{inputs,publication}` (gitignored; retained unmodified per protocol §8.2) |
| Campaign plan row | [`campaign-plan.md`](../campaign-plan.md) §2.1 `EXP-002 / C1` |
| Related Plan items | Project Plan §3.1 `F1`, `F2`, `F4` (amendment #51), §5 items 4–5, §6 Phase 7 `C1`, §9 DoD `1`, `3`, `5`, `12` |
| Errata against this report | [§12](#12-errata) — (none upon issue) |

---

## 1. Summary verdicts (pre-registration §4.1, §5.4, §7, §11.1–§11.3; campaign plan §9.1)

The pre-registered decision rules (`preregistration.md` §§4.1, 5.2, 5.4, 5.5, 11.1–11.3) were frozen at `F = 10ac3c04f44a1f68869c94c1dfae1c1c1a189460` before the first E3 run and applied without modification. All five E3 run records are `COMPLETED` and admissible; zero runs and zero observations aborted (`aborted_runs = []`, `inadmissible_runs = []`).

| Hypothesis | Verdict | Registered denominator (unit) | Pass / Equal | Fail / Differ | Missing / Extra / Unverifiable | Effect size & 95% CI | Primary evidence |
|---|---|---:|---:|---:|---|---|---|
| **H1** — API mapping census | **CONFIRMED** | `175` (`api_symbol`); `172` (`legacy_api_name`) | `175/175` `api_symbols` resolved (`172` callable, `3` constants); `172/172` `legacy_api_names` owned; `175` observed exports | `0` failing `api_symbols`; `0` unowned `legacy_api_names`; `0` duplicate/removed/unexpected; frozen sets `0/0` | `0` unverifiable `api_symbols` | not applicable (deterministic census; §7) | `RUN-20261021T183011Z-e65076e-r1-api-cpu/api.json`, §3.1 |
| **H2** — Historical conclusion preservation | **CONFIRMED** | `62` (`claim_comparator_record`) across 5 families | `62/62` `claim_comparator_records` agree (`C01` `5/5`, `C02` `42/42`, `C03` `4/4`, `C04` `5/5`, `C05` `6/6`) | `0` disagree | `0` missing | not applicable (deterministic census; §7) | `RUN-20261021T183952Z-e65076e-r1-conclusions-cpu/conclusions.json`, §3.2 |
| **H3** — Publication fidelity (approved §5.4 policy, **primary**) | **CONFIRMED** | `39` (`generated_file`: `14` PDF, `14` PNG, `11` `.tex` tables); `11` tables vs archived | `39/39` `generated_files` equal (`14/14` PDF, `14/14` PNG, `11/11` `.tex`); `11/11` PRIN tables & `11/11` reference tables equal archived | `0` differ | `0` missing, `0` extra in either arm | not applicable (deterministic census; §7) | `RUN-…-reproduction-reference-cpu` vs `RUN-…-reproduction-prin-cpu`, §3.3 |
| **H3 diagnostic** — Writer-property diagnostic (§11.3 policy) | **REFUTED (reported diagnostic)** | `39` (`generated_file`); `11` tables vs archived (raw bytes) | `14/39` `generated_files` equal (`0/14` PDF, `14/14` PNG, `0/11` `.tex`); `11/11` PRIN tables equal archived | **`25/39` `generated_files` differ** (`14/14` PDF, `11/11` `.tex`); all 25 classified (`14` `pdf_info_keyset`, `11` `tex_crlf_line_terminator`, `0` unclassified) | `0` missing, `0` extra in either arm | not applicable (deterministic census; §7) | `sensitivity-residuals.json`, `summary.json`, §3.4 |
| **H4** — Repeatability parity | **CONFIRMED** | `39` (`generated_file`) | `39/39` `generated_files` raw-identical (`14/14` PDF, `14/14` PNG, `11/11` `.tex`); §5.5 canonical projection equal (`true`) | `0` raw differences; `0` projection differences | `0` only in `prin`, `0` only in `repeatability` | not applicable (deterministic census; §7) | `RUN-…-reproduction-prin-cpu` vs `RUN-…-seedrep0-prin-cpu`, §3.5 |

**Deterministic censuses (pre-registration §7; campaign plan §9.1):** H1, H2, H3, and H4 are deterministic censuses of fixed, finite populations (`175` `api_symbols`, `172` `legacy_api_names`, `62` `claim_comparator_records`, and `39` `generated_files`) with `replicates = 1`, `measurement_kind = "deterministic_census"`, and `seed_used = false`. Confidence intervals, Cohen's *d*, Cliff's δ, α, power calculations, bootstrap resampling, and significance tests are not applicable to these deterministic censuses. Repeating identical deterministic runs does not generate independent sampling variance. The 39 publication `generated_files` and the 7 E4 analysis output files (`analysis_output_file_count = 7`) are disjoint populations and are never summed.

**Campaign plan §10.4 D1 flag: NOT RAISED (`False`).** Under pre-registration §4.3 and campaign plan §10.4, all four primary hypotheses (H1, H2, H3 under the approved §5.4 policy, H4) are `CONFIRMED`. The diagnostic §11.3 residuals are 100% classified into the two registered writer/host I/O classes with `0` unclassified residuals, satisfying `EXP002D1-S2-F1`. This constitutes a **non-reversal verdict**.

---

## 2. Results versus the pre-registered expectations (pre-registration §3)

Side-by-side comparison of pre-registration §3's predictions against the observed outcomes (matching `DOCS/test_and_benchmark_results/EXP-002-r1/analysis/expected-vs-observed.md`, SHA-256 `1a27f264f02cd7e2bea0f1d6649ded3f797982d288b4ac870d358accd26bd4d7`):

| Hypothesis | Predicted direction (protocol §3) | Predicted magnitude (protocol §3) | Independent basis (protocol §3) | Observed (exact counts and units) | Verdict & expectation match |
|---|---|---|---|---|---|
| **H1** | Complete namespace and ownership preservation | `175/175` resolved; `172/172` owned; zero duplicate/missing/extra names | Frozen reference literal API, WP-001 ownership matrix, PRIN canonical tuple, Migration Guide; inspected statically at E1 | `175/175 api_symbols` resolved (`172` callable, `3` scalar constants); `172/172 legacy_api_names` owned; `175` observed export-list entries; duplicates `0`, removed `0`, unexpected `0`; frozen-contract missing/extra `0/0`; unverifiable rows `0` | **CONFIRMED** — matches prediction in full |
| **H2** | No reversal of registered historical predicates | `62/62` agreements; zero disagreements | Published chimera/topology/Goldilocks claims and previously stored threshold flags, specified per family in §5.2; no new PRIN outcomes used | `62/62 claim_comparator_records` agree (`C01` `5/5`, `C02` `42/42`, `C03` `4/4`, `C04` `5/5`, `C05` `6/6`); `0` disagree | **CONFIRMED** — matches prediction in full |
| **H3 (approved policy, primary)** | Reference-faithful publication representation | `39/39` equal under the registered format-specific comparison | Corrected generator port (EXP-002-D1 S1–S4); 11-table reference-byte acceptance contract; matched rendering environment; declared metadata normalizations | `39/39 generated_files` equal (`14/14` PDF, `14/14` PNG, `11/11` `.tex`); `0` differ; missing reference/PRIN `0/0`; extra reference/PRIN `0/0`; PRIN tables equal to archived `11/11`; reference tables inconsistent with archived `0/11` | **CONFIRMED** — matches prediction in full |
| **H3 (§11.3 sensitivity policy)** | Registered sensitivity analysis (§11.3 item 2), reported beside primary | Reported beside primary H3 verdict; `14/39` expected | Pre-exposure (`6314532`) comparison policy: raw table bytes, in-place PDF Info value masking, PNG normalization | `14/39 generated_files` equal (`0/14` PDF, `14/14` PNG, `0/11` `.tex`); `25/39` differ (`14/14` PDF, `11/11` `.tex`); all 25 classified (`14` `pdf_info_keyset`, `11` `tex_crlf_line_terminator`, `0` unclassified); PRIN tables equal archived `11/11`; reference tables inconsistent with archived `11/11` | **REFUTED (diagnostic)** — matches prediction in full; 0 unclassified residuals |
| **H4** | Exact same-implementation repeatability | `39/39` raw byte identities; zero projection differences | `tools/reproduce.py` deterministic pipeline, fixed figure dates, explicit output roots, sorted manifests, deterministic table formatting | `39/39 generated_files` raw-identical (`14/14` PDF, `14/14` PNG, `11/11` `.tex`); `0` differ; only in PRIN/repeat `0/0`; canonical projection equal: `true` | **CONFIRMED** — matches prediction in full |

**Note on table comparisons:** In `expected-vs-observed.md` and `summary.json`, `tables_equal_to_archived` counts the PRIN arm's 11 tables against the 11 archived reference tables (`REFERENCE/paper/tables/tab_*.tex`), which equals `11/11` under both policies. The reference arm's comparison against archived tables is tracked in `reference_tables_inconsistent_with_archived`: `0/11` inconsistent under the approved CRLF→LF policy, and `11/11` inconsistent under the raw sensitivity policy due to Windows text-mode CRLF translation by the unpinned reference writer.

---

## 3. Per-hypothesis results and E5 independent recount

In session `EXP-002-r1-E5`, an independent recount parsed the five raw JSON records directly and recomputed every count, classification, predicate comparison, format digest comparison, and projection comparison. All numbers matched the committed E4 deliverables with **zero discrepancies**.

### 3.1 H1 — API mapping census: `CONFIRMED`

- **Source record:** `benchmarks/results/EXP-002-r1/RUN-20261021T183011Z-e65076e-r1-api-cpu/api.json` (`97,334` B, SHA-256 `1dcd87ff4c258cb6a2e30dd8b96e0ce180729460702630107aea96c13912d7d3`).
- **Expected population (`175` `api_symbols`):** the `172` unique names in `REFERENCE/src/prinet/__init__.py` literal `__all__` (SHA-256 `ede92afc6771f2e29206534905e2820598ba841662a93d59f669f803a382f182`) union the `3` disjoint PRIN additions (`BackendUnavailableError`, `__version__`, `core_version`).
- **Resolution census:** `175/175` `api_symbols` resolved (`resolved = true`, `error = null`):
  - `172` classified as `callable` (`callable = true`, non-`None` class or function export);
  - `3` classified as scalar `constant` (`callable = false`, `type` in `{"int", "str"}`: `CONTROL_DIM` (`int`), `STATE_DIM` (`int`), and `__version__` (`str`)).
  - `0` `none`, `0` `unsupported`, `0` `unresolved`, `0` `unverifiable`.
- **Legacy ownership census (`172` `legacy_api_names`):** `172/172` have both a Migration Guide row (`DOCS/sphinx/migration_guide.rst` `.. wp036-consolidated-table-begin`..`end`) and a WP-001 ownership row (`DOCS/baselines/wp001_api_traceability.md`); `0` unowned.
- **Observed `prin.__all__` list:** `175` entries, `175` unique (`0` duplicates, `0` removed exports, `0` unexpected exports).
- **Frozen contract check (`verify_api_surface(prin.__all__)`):** `frozen_missing = []` (`0`), `frozen_extra = []` (`0`).
- **Counterexamples:** `0`. Verdict under §4.1: **`CONFIRMED`**.

### 3.2 H2 — Historical conclusion preservation: `CONFIRMED`

- **Source record:** `benchmarks/results/EXP-002-r1/RUN-20261021T183952Z-e65076e-r1-conclusions-cpu/conclusions.json` (`59,346` B, SHA-256 `f61f5575fb8d28646c583e15923236e2b22c32bcfc00a9acd25b4f73eacb2a87`).
- **Population (`62` `claim_comparator_records` across 5 registered families):** every input JSON file was verified against `paper/artefact_manifest.json` (`300cdc094d2b7d27ac8b1e2556b2e6ed4dad3333f0038b45c8f87ea81612cce5`), and every operand, JSON pointer path, operator, unit, and expected Boolean was verified:

| Family | Frozen input JSON | Registered predicate population | Operand unit | Denominator | Agree | Disagree | Missing |
|---|---|---|---|---:|---:|---:|---:|
| `C01` | `phase1_chimera_seeds.json` | `bimodality_coefficient.raw_values[i] > 0.555` for `i = 0..4` (expected `true`; `paper/main.tex` §`sec:chimera`) | `BC` (dimensionless) | `5` | `5` | `0` | `0` |
| `C02` | `benchmark_y4q1_3_k_alpha_sensitivity.json` | All `42` distinct `(K, alpha)` grid rows: `bc_mean > 0.555` compared with row's stored `chimera_detected` Boolean (`26` `true`, `16` `false`; Fig. 4) | `BC` (dimensionless) | `42` | `42` | `0` | `0` |
| `C03` | `phase2_chimera_nsweep.json` | Four `sweep` rows at `n_oscillators` ∈ `{128, 256, 512, 1024}`: `bc_stats.mean > 0.5` (expected `true`; `paper/main.tex`) | `BC` (dimensionless) | `4` | `4` | `0` | `0` |
| `C04` | `y4q1_8_topology_comparison.json` | Ring `bc_mean` > `2community` & `4community` means (2); ring `bc_ci.ci_width` > `2community` & `4community` widths (2); `2community` width > `4community` width (1) (`paper/supplementary.tex` Table `tab:topology`) | `BC` (2); `historical_BC_CI_width` (3) | `5` | `5` | `0` | `0` |
| `C05` | `y3q49_goldilocks_zones.json` | Regimes `csr_cpu`, `full_cpu`, `mean_field_cpu`, `sparse_knn_cpu`: `csr_cpu` `zone_width` > each other width (3); `full_cpu` `K_c` < each other onset (3) (`paper/supplementary.tex` Table `tab:goldilocks`) | `stored_coupling_K` | `6` | `6` | `0` | `0` |
| **Total** | — | — | — | **`62`** | **`62`** | **`0`** | **`0`** |

- **Counterexamples:** `0`. Verdict under §4.1: **`CONFIRMED`**.

### 3.3 H3 — Publication fidelity under the approved §5.4 policy (primary): `CONFIRMED`

- **Source records:**
  - Reference arm (`prinet` 3.0.0 frozen generators): `benchmarks/results/EXP-002-r1/RUN-20261021T184447Z-e65076e-r1-reproduction-reference-cpu/reproduction.json` (`59,724` B, SHA-256 `eaeddfb0ad06b49f0a1390207540f6303ed23e1a432807f95ae34aa6513f4493`).
  - PRIN arm (`tools.reproduce.run_reproduction`): `benchmarks/results/EXP-002-r1/RUN-20261021T184600Z-e65076e-r1-reproduction-prin-cpu/reproduction.json` (`59,711` B, SHA-256 `09df73ad43144c870ad95b7fcb2a8bd02cd394549335d3a89b848b4631536771`).
- **Matched renderer environment:** Python `3.14.0`, Matplotlib `3.11.1`, NumPy `2.5.1`, Pillow `12.3.0`, FreeType `2.14.3`, backend `Agg`, font cache `fontlist-v3.11.0.json` (`146,692` B, SHA-256 `9c00441405ce72925562e017858a729b402612a203b0682b2e7fd79329c8f6bb`), 40 bundled `.ttf` fonts (`font_sha256` `168e1aee710ca4496f65d7dc0689ed93257ed3e1ab3711dad4494940b51c8189`).
- **Inventory:** Both arms produced all `39` registered publication files (`14` PDF figures, `14` PNG figures, `11` `.tex` tables; `0` missing in either arm, `0` extra).
- **Approved comparison policy (§5.4):**
  - `.tex` tables: CRLF (`\r\n`) canonicalized to LF (`\n`) symmetrically in both arms and the archived baseline.
  - `.pdf` figures: validated Matplotlib single-revision classic-xref container; four registered metadata keys (`CreationDate`, `ModDate`, `Creator`, `Producer`) and values stripped from `/Info`; trailer `/ID` masked; `xref` offsets and `startxref` pointer canonicalized to 0; all drawing, font, and stream bytes preserved.
  - `.png` figures: validated PNG container and decoded pixels (`_validate_png`); critical chunks `IHDR`/`PLTE`/`tRNS`/`IDAT`/`IEND` retained via `normalize_matplotlib_output`.
- **Outcome by format:**
  - **PDF Figures:** **14/14 equal** (`0` differ).
  - **PNG Figures:** **14/14 equal** (`0` differ).
  - **LaTeX Tables:** **11/11 equal** (`0` differ), and `11/11` equal to the archived tables in `REFERENCE/paper/tables/`.
- **Total:** **39/39 equal** (`0` differing, `counterexample_count = 0`). Verdict under §4.1 and §5.4: **`CONFIRMED`**.

### 3.4 H3 Writer-Property Diagnostic (§11.3 policy; `EXP002D1-S2-F1` resolution): `DISCLOSED DIAGNOSTIC`

- **Purpose:** Non-gating sensitivity diagnostic capturing `sensitivity_bytes` and `sensitivity_sha256` under the pre-exposure (`6314532`) policy (raw table bytes without CRLF normalization, and in-place PDF `/Info` value masking preserving key sets).
- **Outcome:** `14/39` files equal (all 14 PNG figures), `25/39` files differ (14 PDF figures, 11 LaTeX tables).
- **Residual Classification:** Per `preregistration.md` §11.1 item 2, all 25 differing files were inspected structurally:
  1. **14 PDF Figures (`pdf_info_keyset`):** In all 14 figures (`fig2`..`fig15`), the divergence is strictly the `/Info` dictionary key set. Reference passes no metadata, so Matplotlib writes 3 keys (`Creator`, `Producer`, `CreationDate`), while PRIN passes fixed metadata required for H4 determinism, writing 4 keys (`Creator`, `Producer`, `CreationDate`, `ModDate`). All 14 files are byte-identical across all drawing streams, fonts, and contents under §5.4.
  2. **11 LaTeX Tables (`tex_crlf_line_terminator`):** In all 11 tables (`tab_ablation`..`tab_supercritical`), the divergence is host text-mode newline translation. The reference writer on Windows wrote `CRLF` (count = 13 to 22), while PRIN wrote explicit `\n` (`LF`, CRLF count = 0). All 11 files are 100% byte-identical after CRLF→LF normalization.
  3. **Unclassified Residuals:** Exactly **`0` unclassified residuals** (100% of residuals accounted for by registered writer/host I/O classes).
- Because §5.4 is `39/39` equal and unclassified residuals are `0`, H3's single verdict is **`CONFIRMED`**, and the sensitivity policy is reported alongside as an explained writer-property diagnostic.

### 3.5 H4 — Repeatability parity: `CONFIRMED`

- **Source records:**
  - PRIN reproduction arm (`prin`): `benchmarks/results/EXP-002-r1/RUN-20261021T184600Z-e65076e-r1-reproduction-prin-cpu/reproduction.json` (`59,711` B, SHA-256 `09df73ad43144c870ad95b7fcb2a8bd02cd394549335d3a89b848b4631536771`).
  - PRIN repeatability arm (`repeatability`): `benchmarks/results/EXP-002-r1/RUN-20261021T184707Z-e65076e-r1-seedrep0-prin-cpu/reproduction.json` (`59,708` B, SHA-256 `f1f5e5bcdd12714e112e22dfa058a6a37274ee8208c2dee7bb4a6cf3a4a01176`).
- **Outcome:** `39/39` `generated_files` (`14` PDFs, `14` PNGs, `11` tables) have identical filenames, identical `raw_bytes`, and identical `raw_sha256` digests across both independent interpreter processes (`raw_differing_generated_files = []`, `only_in_prin = []`, `only_in_repeat = []`). No normalization is used.
- **Canonical projection (§5.5):** Stripping only run metadata (`started_at_utc`, `recorded_at_utc`, `elapsed_seconds`, `config.out_dir`, `environment`) yields byte-identical canonical JSON projections (`projection_equal = true`).
- **Counterexamples:** `0`. Verdict under §4.1: **`CONFIRMED`**.

---

## 4. Bearing on Project Plan requirements and Definition of Done

In accordance with Experimentation Standards §1.5 ("Claims match evidence"), the table below evaluates what the registered EXP-002-r1 verdicts support regarding cited Project Plan clauses:

| Plan clause | Verbatim wording in `DOCS/PRIN_Project_Plan.md` | Hypothesis | What the registered EXP-002-r1 verdict supports |
|---|---|---|---|
| **§3.1 F1 — Feature parity** | *"every public class/function in PRINet 3.0's 175+-symbol API has an equivalent."* | **H1 (`CONFIRMED`)** | Supports that all `175` expected `prin` exports resolve to non-`None` callables (`172`) or scalar constants (`3`), that `verify_api_surface(prin.__all__)` returns empty missing/extra sets against `FROZEN_PUBLIC_API`, and that all `172` legacy names have Migration Guide and WP-001 ownership rows. Does **not** by itself prove runtime behavioural or numerical equivalence of every callable. |
| **§9 DoD #1** | *"Every PRINet 3.0 public symbol (175+) has a working equivalent; renames documented in the Migration Guide."* | **H1 (`CONFIRMED`)** | Supports the export-resolution and Migration Guide mapping census (`175/175` resolved, `172/172` documented). Implementation equivalence belongs to the test suite, EXP-001-r1, and C2–C4 experiments. |
| **§3.1 F2 — Numerical parity** | *"trajectories, metrics, and benchmark results match 3.0.0 within the documented tolerances (§5)."* | **H2 (`CONFIRMED`)** | Supports that all `62/62` registered elementary direction/threshold predicates across families `C01`–`C05` in the frozen 172-artefact JSON set hold as predicted (`0` reversals). Trajectory and metric numerical parity on the golden corpus was adjudicated in `EXP-001-r1`. Fresh benchmark measurements remain owned by EXP-003–EXP-008 (§7). |
| **§5 item 4 — Benchmark-result parity** | *"full re-run of the benchmark suite; scientific conclusions unchanged; deviations documented in the Parity Report."* | **H2 (`CONFIRMED`), H3 (`CONFIRMED`)** | H2 confirms preservation of the 62 registered CPU-readable archival conclusion predicates from stored JSON artefacts; H3 confirms that all 39 publication files equal the reference generator under the approved §5.4 policy. Updated in the Parity Report (§8.4). |
| **§9 DoD #3** | *"The parity suite passes at §5 tolerances; the Parity Report is published."* | **H2 (`CONFIRMED`), H3 (`CONFIRMED`)** | The Parity Report (`DOCS/sphinx/parity_report.rst`) is updated with EXP-002-r1's confirmation of H1–H4. DoD #3 remains open until campaign completion. |
| **§3.1 F4 — Reproducibility (amendment #51)** | *"`tools/reproduce.py` regenerates all 14 verifiable figures (figures 2–15; there was never a figure 1) and 11 tables byte-comparably from the same JSON artefacts with a matching SHA-256 manifest (amendment #51)."* | **H3 (`CONFIRMED`), H4 (`CONFIRMED`)** | **H4 (`CONFIRMED`)** proves **PRIN-versus-PRIN** repeatability: two separate invocations of `tools/reproduce.py` regenerate all `39/39` files raw-byte-identically. **H3 (`CONFIRMED`)** proves **cross-generator publication fidelity**: all `39/39` files match the frozen reference generator under the approved §5.4 comparison policy (with all 25 sensitivity residuals classified into writer/host I/O properties and 0 unclassified). |
| **§5 item 5 — Bit-level reproducibility** | *"all RNG behind the single `Seed` type; exact reproducibility across CPU/GPU and across runs."* | **H4 (`CONFIRMED`)** | Supports exact cross-run raw-byte repeatability (`39/39` files) and canonical-projection identity for PRIN's deterministic publication pipeline on the Windows reference host (`seed_used = false`). |
| **§9 DoD #5** | *"`tools/reproduce.py` regenerates all figures/tables with a matching SHA-256 manifest."* | **H3 (`CONFIRMED`), H4 (`CONFIRMED`)** | Satisfied for publication outputs: PRIN-versus-PRIN regeneration is `39/39` raw-byte-identical, and PRIN-versus-reference regeneration is `39/39` equal under the approved §5.4 policy. |
| **§9 DoD #12** | *"The Phase 7 campaign is complete: all experiments pre-registered and reported per the Experimentation Standards; campaign summary published."* | **All (`CONFIRMED`)** | EXP-002-r1 returns a non-reversal verdict, satisfying the campaign plan §10.4 item 5 gate required to proceed with campaign sessions upon maintainer acceptance. |

---

## 5. Runs, aborts, exclusions, and resource budget

No run aborted. No observation aborted. No symbol, claim predicate, or publication file was excluded from any denominator. Each registered leg ran once, in its own Python interpreter process, at clean source `R = e65076eb7ae97100d40ea32c60229dd40ed51033`, in the exact order registered in pre-registration §5.5 (`log.md` §§4–5).

| # | Mode | Label | Run ID | Hypotheses | UTC start → end (`2026-10-21`) | Exit | Driver `elapsed_seconds` (s) | `status` | Admissible |
|---:|---|---|---|---|---|---:|---:|---|---|
| 1 | `api` | `r1-api-cpu` | `RUN-20261021T183011Z-e65076e-r1-api-cpu` | H1 | `18:30:47.097Z` → `18:30:47.863Z` | `0` | `0.7669` | `COMPLETED` | yes |
| 2 | `conclusions` | `r1-conclusions-cpu` | `RUN-20261021T183952Z-e65076e-r1-conclusions-cpu` | H2 | `18:40:08.220Z` → `18:40:08.695Z` | `0` | `0.4742` | `COMPLETED` | yes |
| 3 | `reference` | `r1-reproduction-reference-cpu` | `RUN-20261021T184447Z-e65076e-r1-reproduction-reference-cpu` | H3 | `18:45:04.231Z` → `18:45:11.244Z` | `0` | `7.0124` | `COMPLETED` | yes |
| 4 | `prin` | `r1-reproduction-prin-cpu` | `RUN-20261021T184600Z-e65076e-r1-reproduction-prin-cpu` | H3, H4 | `18:46:13.441Z` → `18:46:19.055Z` | `0` | `5.6138` | `COMPLETED` | yes |
| 5 | `repeatability` | `r1-seedrep0-prin-cpu` | `RUN-20261021T184707Z-e65076e-r1-seedrep0-prin-cpu` | H4 | `18:47:23.205Z` → `18:47:29.290Z` | `0` | `6.0846` | `COMPLETED` | yes |
| **Total** | — | — | **5 runs (`0` aborted, `0` reruns)** | — | — | — | **`19.9519`** | — | **5 / 5** |

### Budget accounting against pre-registration §9 and campaign plan §§7.5, 8

| Resource | Measured | Registered cap | Status |
|---|---|---|---|
| H1 Windows CPU wall (all E3 legs) | Sum of driver `elapsed_seconds` = `19.9519 s` (`< 0.01 h`) | `≤ 12 h` (`43,200 s`) | Within cap (`< 0.05%` used) |
| H1 GPU wall | `0 s` (no GPU leg registered or executed) | `≤ 2 h` | Within cap (`0%` used) |
| Hosted CI wall (experiment legs) | `0 s` (Plan amendment #52 hosted check runs validate source and are not charged to legs) | `≤ 2 h` | Within cap (`0%` used) |
| Single-run tracked JSON size (largest run: `r1-api-cpu`) | `98,118 B` (`~0.0935 MiB`; other runs ~`60.5 KiB` each) | `≤ 2 MiB` (`2,097,152 B`) | Within cap (`4.68%` used) |
| EXP-002-r1 raw root tracked artefacts (`benchmarks/results/EXP-002-r1/`) | `343,259 B` (`~0.327 MiB`) | `≤ 10 MiB` (`10,485,760 B`) | Within cap (`3.27%` used) |
| Combined EXP-002 + EXP-002-r1 raw roots (`341,879 B` + `343,259 B`) | `685,138 B` (`~0.653 MiB`) | `≤ 10 MiB` (`10,485,760 B`) | Within cap (`6.53%` used) |
| Combined EXP-002 + EXP-002-r1 raw + record roots | `1,875,567 B` (`~1.789 MiB`) | `≤ 10 MiB` (`10,485,760 B`) | Within cap (`17.89%` used) |
| Campaign-wide `benchmarks/results/EXP-*` tracked storage | `14,103,546 B` (`~13.450 MiB`: EXP-001 + EXP-002 + EXP-002-r1) | `≤ 64 MiB` (`67,108,864 B`) | Within cap (`21.02%` used) |

---

## 6. Retained-bytes verification, clean-checkout regeneration, and Protocol §8.2 reconstruction

Pre-registration §8.2 and §11.3 item 1 require E5 to execute three sequential verification steps:
1. **First verify the retained publication and input bytes** against manifested digests and E3 listing hashes.
2. **Regenerate the seven E4 analysis outputs and `report-manifest.json`** in a clean detached worktree outside the repository and match byte-for-byte (`8/8`).
3. **Reconstruct both publication arms** from clean checkout into a fresh gitignored directory under the matched renderer environment.

### 6.1 Step 1 — Verification of retained publication and input bytes (executed first)

1. **Retained Input Snapshots (`inputs/`):**
   - Verified all 172 JSON files across all 5 runs in `DOCS/test_and_benchmark_results/EXP-002-r1/<run-id>/inputs/` against `paper/artefact_manifest.json` (`300cdc094d2b7d27ac8b1e2556b2e6ed4dad3333f0038b45c8f87ea81612cce5`): exactly **172/172 files present and byte-identical across all 5 runs** (`16,047,018 B` per run, 0 mismatches, 0 extra).
   - Deterministic input listing hash (sorted `path size sha256`): `f4c239d06461ef3933930eefb9a91c3e1e04083e2e078418ef61852277242fb9` (identical across all 5 runs).
2. **Retained Publication Outputs (`publication/`):**
   - Verified all 39 publication files across all three reproduction legs in `DOCS/test_and_benchmark_results/EXP-002-r1/<run-id>/publication/` against the manifested raw digests in each run's `reproduction.json`:
     - `r1-reproduction-reference-cpu`: **39/39 matched**, 0 mismatches (`1,501,980 B`). Listing hash: `e38a1078d9ea2e17ddfd0d27af150581512aa402e125ee57e0c5bd0990e7bc5b`.
     - `r1-reproduction-prin-cpu`: **39/39 matched**, 0 mismatches (`1,500,705 B`). Listing hash: `0f99f95524fff7e4e0e885e18c19d57e3360801921ea78f244aa7d8ab65f60fe`.
     - `r1-seedrep0-prin-cpu`: **39/39 matched**, 0 mismatches (`1,500,705 B`). Listing hash: `0f99f95524fff7e4e0e885e18c19d57e3360801921ea78f244aa7d8ab65f60fe`.
   - The PRIN reproduction and repeatability listing hashes are byte-identical (`0f99f955…`), directly confirming H4 raw determinism on disk.

### 6.2 Step 2 — Clean detached-worktree regeneration of E4 deliverables

To verify reproducibility without workspace pollution, a detached git worktree was created outside the repository at `C:\dev\PRIN-worktree-e5-clean` at commit `c7c54d18` (the commit where E4 executed before committing the analysis module, preserving `commit: null` provenance in `summary.json`). The retained run directories and extension `_prin_core.pyd` (`9,290,240 B`, SHA-256 `37392d06…ee99e`) were supplied, and the E4 analysis module was executed:
- All generated files matched the committed files **byte-for-byte identical (`8/8` files)**:
  - `summary.json`: `fcdb56250165f18d65c22d07f9caae1a9e0ff632f3dbcab0047046dabc9e01ad`
  - `api-mapping.csv` / `api-census.csv`: `5656cb9b570889a911b35283b8a5cfdc55c5ec8e0f28ba35d34d8fec526e10c3`
  - `conclusion-comparisons.csv` / `conclusions-census.csv`: `0c01c59c8e1f32ea3ad173dddde117ad9a94b187289328da760e1c906e0bba85`
  - `reproduction-comparisons.csv`: `925b40b4b13f6e76ec62eed08f65b400d13da66c446f54766963804781f5e532`
  - `error-distributions.json`: `afd3d1454dabdd12e12b504300b07996a12553cc262a16f6748c38d7a3fffb1e`
  - `expected-vs-observed.md`: `1a27f264f02cd7e2bea0f1d6649ded3f797982d288b4ac870d358accd26bd4d7`
  - `coverage-and-deferrals.md`: `4e82524ff0fa8b20cc2dbc2a13b5202730b4d5d6c01a0e107ec100574fb74dad`
  - `report-manifest.json`: `6cd12f2d1bf0ed5f841d8e3945443a4fd16b689f7fd489f0435fd61baf8d9dc2`
  - (Also `repeatability-comparisons.csv` `18f91d6b…` and `sensitivity-residuals.json` `884c0c6c…`).
- Detached worktree was cleanly removed with `git worktree remove --force`.

### 6.3 Step 3 — Clean-checkout reconstruction of publication arms

Reconstruction was performed in `C:\dev\PRIN` writing exclusively to a fresh gitignored directory `DOCS/test_and_benchmark_results/EXP-002-r1/e5-reconstruction/` using `collect_reproduction` under the matched renderer environment:
- **PRIN Reconstruction vs E3 PRIN:**
  - Raw digests: **39/39 equal** (`14/14` PDF, `14/14` PNG, `11/11` `.tex`).
  - Normalized digests: **39/39 equal**.
  - Sensitivity digests: **39/39 equal**.
  - Listing hash: `0f99f95524fff7e4e0e885e18c19d57e3360801921ea78f244aa7d8ab65f60fe` (**identical** to E3 PRIN and repeatability).
- **Reference Reconstruction vs E3 Reference:**
  - Raw digests: **25/39 equal** (`0/14` PDF, `14/14` PNG, `11/11` `.tex`).
  - Normalized digests: **39/39 equal**.
  - Sensitivity digests: **39/39 equal**.
  - Listing hash: `9ee51086fa27083a2162da15e98587376c669e46a3c6d66e51bfd785e05d0e2e` (differs from E3 reference listing hash `e38a1078…` solely due to the unpinned reference generator writing wall-clock `CreationDate` and trailer `/ID` into raw PDFs).
- **Reconstruction Limitation Disclosed (preregistration §8.2, §11.3 item 1):** The reference-arm raw PDF timestamp difference is an understood property of the frozen `prinet==3.0.0` reference writer. Under both normalized (§5.4) and sensitivity (§11.3) policies, 39/39 digests match. Because Step 1 verified all 39/39 retained raw files, this is recorded as a reconstruction limitation, never as a new H3/H4 observation.

---

## 7. Coverage and deferrals (owner matrix; pre-registration §5.3)

Pre-registration §5.3 requires E4 and E5 to carry the seven-row scientific-owner table verbatim so that no downstream obligation is silently treated as discharged by EXP-002-r1's archival rendering:

| Historical conclusion class / source | Scientific owner | Status after EXP-002-r1 E5 |
|---|---|---|
| CPU throughput, coupling complexity, sweep speedups and CPU scaling | EXP-003, including DV036-F5 at 0166 and the DV-036 CPU gate before 0168 | **OPEN — not discharged by EXP-002-r1** |
| GPU throughput (including OscilloSim's 1.95B claim), Triton/CUDA comparisons, training-step and bridge overhead | EXP-004; GPU/bridge DV-036 gate before 0173; DV-001/DV-003 limitations retained | **OPEN — not discharged by EXP-002-r1** |
| Fresh chimera boundaries, topology/size effects and capacity relation/replication | EXP-005; corrected-SI exception retained | **OPEN — not discharged by EXP-002-r1** |
| CUDA-tagged `y3q49_finite_size_scaling.json` fit ranking and `y3q49_phase_coherence.json` lifetime ranking | EXP-004 backend qualification and EXP-005 scientific replication; their CUDA-derived directions are not substituted with CPU measurements here | **OPEN — not discharged by EXP-002-r1** |
| CLEVR-N/IP accuracy, PT-versus-SA statistical equivalence, ablations, freezing, parameter/FLOP efficiency, trained supercritical regimes, gradient/representation geometry and training curves | EXP-006, with EXP-004 performance dependencies; historical intervals/p-values remain reference-only | **OPEN — not discharged by EXP-002-r1** |
| Daemon p95, MOT/IP evaluation, noise/velocity/occlusion and adversarial robustness | EXP-007, with EXP-006 training dependencies; CPU/DirectML/NPU dispositions retained | **OPEN — not discharged by EXP-002-r1** |
| Linux/macOS/Metal, compiler-free wheel matrix and NPU/new capabilities | EXP-008; amendment #48 suspension and campaign section 5.4 unavailable-hardware rule | **OPEN — not discharged by EXP-002-r1** |

Within EXP-002-r1's own registered scope, coverage is complete across all five runs (`0` missing or unverifiable items in H1, H2, H3, or H4).

---

## 8. Non-reversal verdict and release condition (campaign plan §10.4 item 5)

### 8.1 Declaration of Non-Reversal Verdict

All four primary hypotheses are `CONFIRMED`:
- **H1 CONFIRMED** (`175/175` symbols, `172/172` legacy names owned).
- **H2 CONFIRMED** (`62/62` archival predicates preserved).
- **H3 CONFIRMED** under the maintainer-approved primary §5.4 policy (`39/39` publication files equal; `0` differ).
- **H4 CONFIRMED** (`39/39` raw-byte identical repeatability).
- The §11.3 diagnostic residual breakdown accounts for all 25 differing files with **`0` unclassified residuals** (`14` `pdf_info_keyset`, `11` `tex_crlf_line_terminator`), resolving `EXP002D1-S2-F1`.
- Campaign plan §10.4 D1 flag is **NOT RAISED (`False`)**.

Therefore, EXP-002-r1 returns a **non-reversal verdict**.

### 8.2 Release Condition and Status of Blocked Sessions

Under campaign plan §10.4 item 5:
> *"No later campaign session proceeds until step 4's E5 verdict is not a reversal and is verified and accepted by the maintainer, or the maintainer records a Project Plan §8.3 amendment accepting a changed conclusion with full justification."*

1. **Satisfaction of non-reversal condition:** This E5 report establishes that EXP-002-r1's verdict is a non-reversal verdict (`d1_flag = False`).
2. **Maintenance of block pending formal maintainer acceptance:** The AI pair does **not** unblock session `0164` (EXP-003 E1) or downstream sessions `0165`–`0194`. Sessions `0164`–`0194` remain **`BLOCKED`** in all project registers and session briefs until maintainer `MichaelMaillet` independently reviews, verifies, and accepts this report in §11.

---

## 9. Threats to validity and procedural disclosures

1. **Outcome Exposure:** This re-run was drafted and executed after full exposure to EXP-002 outcomes and the EXP-002-D1 correction findings, as disclosed in the header and preregistration §1/§10/§11.
2. **Re-run Namespace Isolation:** All raw records reside strictly under `benchmarks/results/EXP-002-r1/`, generated outputs under `DOCS/test_and_benchmark_results/EXP-002-r1/`, and evidence under `EVIDENCE/exp002-r1-e1/`..`e5/`. Predecessor `EXP-002` roots remained completely unedited (except Erratum 3 appended to `EXP-002/report.md` §15).
3. **Reference PDF Timestamp Limitation:** The reference generator in `prinet==3.0.0` does not pin `/CreationDate`, producing differing raw PDF hashes upon reconstruction. Normalized and sensitivity hashes match 39/39, and retained E3 bytes match 39/39.
4. **Platform Scope:** All execution took place on the designated Windows 11 reference workstation (`H1`). Linux, macOS, and Metal remain suspended under Plan amendment #48 and are not claimed.
5. **Procedural Disclosures:**
   - **Git Bash PATH Precedence:** On Windows, WSL's `bash.exe` can mask Git Bash if prepended. Local gates enforce Git Bash precedence process-locally without mutating global system PATH.
   - **Gitleaks Secret Scan Rule Sensitivity:** Gitleaks flags 64-hex digests under keys containing the string `api` (rule `generic-api-key`). In E4, commit-bound fingerprints for `summary.json:270-271` were approved and pinned in `.gitleaksignore` and `tests/test_wp001_baseline.py`. In E5, all evidence keys and documentation avoided keys triggering false positives.
   - **Clean-Worktree Regeneration Commit Selection:** The E4 analysis script inspects `git log -1` on its own path; regenerating at `c7c54d18` preserved `commit: null`, matching the committed E4 deliverables byte-for-byte.

---

## 10. Complete artefact index

### 10.1 Tracked Raw Records (`benchmarks/results/EXP-002-r1/`)

| Run ID | Mode | File | Bytes | SHA-256 |
|---|---|---|---:|---|
| `RUN-20261021T183011Z-e65076e-r1-api-cpu` | `api` (H1) | `api.json` | `97,334` | `1dcd87ff4c258cb6a2e30dd8b96e0ce180729460702630107aea96c13912d7d3` |
| `RUN-20261021T183011Z-e65076e-r1-api-cpu` | `api` (H1) | `campaign-metadata.json` | `230` | `7137d320fab9955bdcbdd66477f7dadee6c8d484c04de1c4862f5a0390e46fa2` |
| `RUN-20261021T183011Z-e65076e-r1-api-cpu` | `api` (H1) | `manifest.json` | `554` | `b859dba6739cfc420f1d89ecb322d9b8e01f918151eaea827cfca00b6f6a723c` |
| `RUN-20261021T183952Z-e65076e-r1-conclusions-cpu` | `conclusions` (H2) | `conclusions.json` | `59,346` | `f61f5575fb8d28646c583e15923236e2b22c32bcfc00a9acd25b4f73eacb2a87` |
| `RUN-20261021T183952Z-e65076e-r1-conclusions-cpu` | `conclusions` (H2) | `campaign-metadata.json` | `254` | `c2cd7800763a36bf01d0e29ea01f1d26d6451680d61c25a81f7019428303bb4f` |
| `RUN-20261021T183952Z-e65076e-r1-conclusions-cpu` | `conclusions` (H2) | `manifest.json` | `562` | `af3164f093eb4030ff98d9a905da452d6bf7193983d61d76fe65561ea6a6ec82` |
| `RUN-20261021T184447Z-e65076e-r1-reproduction-reference-cpu` | `reference` (H3) | `reproduction.json` | `59,724` | `eaeddfb0ad06b49f0a1390207540f6303ed23e1a432807f95ae34aa6513f4493` |
| `RUN-20261021T184447Z-e65076e-r1-reproduction-reference-cpu` | `reference` (H3) | `campaign-metadata.json` | `264` | `1cdd61267c68542a7b2ff0d3f2a08e8ee112a050256d03e547d077e9f867295e` |
| `RUN-20261021T184447Z-e65076e-r1-reproduction-reference-cpu` | `reference` (H3) | `manifest.json` | `563` | `a8b88998535be9ab23dbcbf538de41e1f1704908ca9426f5704f66da3fafe8e7` |
| `RUN-20261021T184600Z-e65076e-r1-reproduction-prin-cpu` | `prin` (H3, H4) | `reproduction.json` | `59,711` | `09df73ad43144c870ad95b7fcb2a8bd02cd394549335d3a89b848b4631536771` |
| `RUN-20261021T184600Z-e65076e-r1-reproduction-prin-cpu` | `prin` (H3, H4) | `campaign-metadata.json` | `267` | `26bd9b4cd1ce91ee8ed17fb798ef2aa207ccbd04364fbf4f5f9583ca835eea7c` |
| `RUN-20261021T184600Z-e65076e-r1-reproduction-prin-cpu` | `prin` (H3, H4) | `manifest.json` | `563` | `ce7497c4b2cb5eaeb5c769da5c518d4600f5fcb2183f41f5f09de628874cd207` |
| `RUN-20261021T184707Z-e65076e-r1-seedrep0-prin-cpu` | `repeatability` (H4) | `reproduction.json` | `59,708` | `f1f5e5bcdd12714e112e22dfa058a6a37274ee8208c2dee7bb4a6cf3a4a01176` |
| `RUN-20261021T184707Z-e65076e-r1-seedrep0-prin-cpu` | `repeatability` (H4) | `campaign-metadata.json` | `259` | `cefdaf73760c1af0adcf7bc9f51845f0a974312483a00083578b0c4bdaf06504` |
| `RUN-20261021T184707Z-e65076e-r1-seedrep0-prin-cpu` | `repeatability` (H4) | `manifest.json` | `563` | `416737200c0224a2d0cf92a80a75d28737e1c94556e47b61ffe1c3a77a061729` |

### 10.2 Analysis Deliverables (`analysis/` and `report-manifest.json`)

| Path | Bytes | SHA-256 |
|---|---:|---|
| [`analysis/api-census.csv`](analysis/api-census.csv) | `18,378` | `5656cb9b570889a911b35283b8a5cfdc55c5ec8e0f28ba35d34d8fec526e10c3` |
| [`analysis/conclusions-census.csv`](analysis/conclusions-census.csv) | `10,872` | `0c01c59c8e1f32ea3ad173dddde117ad9a94b187289328da760e1c906e0bba85` |
| [`analysis/reproduction-comparisons.csv`](analysis/reproduction-comparisons.csv) | `31,250` | `925b40b4b13f6e76ec62eed08f65b400d13da66c446f54766963804781f5e532` |
| [`analysis/repeatability-comparisons.csv`](analysis/repeatability-comparisons.csv) | `7,445` | `18f91d6bf46bc0006225ab2d78ceaa058362466faaea63de753ff50035653027` |
| [`analysis/summary.json`](analysis/summary.json) | `12,308` | `fcdb56250165f18d65c22d07f9caae1a9e0ff632f3dbcab0047046dabc9e01ad` |
| [`analysis/sensitivity-residuals.json`](analysis/sensitivity-residuals.json) | `18,525` | `884c0c6ce0344e8e4757c99e5555e24ddb314be62a89f8619ed9108644a4de06` |
| [`report-manifest.json`](report-manifest.json) | `19,209` | `6cd12f2d1bf0ed5f841d8e3945443a4fd16b689f7fd489f0435fd61baf8d9dc2` |

---

## 11. Approvals and maintainer verification

| Obligation | Owner | Status |
|---|---|---|
| Step 1: Retained publication and input bytes verified against manifested digests | AI pair (`Antigravity`) | **DONE** — §6.1 (`39/39` publication files, `172/172` inputs per run) |
| Step 2: Seven E4 analysis outputs and `report-manifest.json` regenerated in clean detached worktree | AI pair (`Antigravity`) | **DONE** — §6.2 (`8/8` files byte-identical) |
| Step 3: Protocol §8.2 reconstruction of the 39 publication files for reference and PRIN arms | AI pair (`Antigravity`) | **DONE** — §6.3 (`39/39` PRIN raw-identical; `39/39` normalized/sensitivity identical) |
| Step 4: Independent recount from the five raw records | AI pair (`Antigravity`) | **DONE** — §3 (`0` discrepancies vs E4) |
| Step 5: E5 report (`report.md`) drafted and issued | AI pair (`Antigravity`) | **DONE** — this document |
| Step 6: Non-reversal verdict declared; session `0164` held `BLOCKED` pending maintainer acceptance | AI pair (`Antigravity`) | **DONE** — §8 |
| Step 7: Erratum 3 cross-referencing EXP-002-r1 added to predecessor `EXP-002/report.md` §15 | AI pair (`Antigravity`) | **DONE** |
| Step 8: Parity Report updated with EXP-002-r1 non-reversal verdict | AI pair (`Antigravity`) | **DONE** |
| **Maintainer verification of the EXP-002-r1 report and acceptance of verdicts** | **MichaelMaillet** | **PENDING** — see verification block below |

**Maintainer verification block (to be completed by MichaelMaillet at acceptance):**

```text
Verified by: MichaelMaillet                Date (UTC): YYYY-MM-DD
Verdicts accepted as reported (H1 CONFIRMED, H2 CONFIRMED, H3 CONFIRMED [primary §5.4], H4 CONFIRMED): [ ]
Non-reversal verdict accepted (d1_flag = False):                                                        [ ]
Release of session 0164 (EXP-003 E1) and downstream sessions 0165-0194 approved:                         [ ]
```

---

## 12. Errata

Corrections to this report after issue are appended as dated errata, never silent edits (Experimentation Standards §1.3, §4; campaign plan §12 item 6).

| # | Date (UTC) | Corrects | Substance | Raised by |
|---|---|---|---|---|
| — | — | — | (no errata upon initial issue) | — |
