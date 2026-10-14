# EXP-002 — E5 report: API, benchmark-result, and reproduction parity (track C1)

**Status:** **ISSUED - awaiting maintainer verification** — see §14. Maintainer verification is **not** claimed in this document. The exit gate for proceeding to session `0164` (EXP-003 E1) is open on the triggered campaign plan §10.4 D1 correction cycle (§8).
**Verdicts:** **H1 `CONFIRMED`**, **H2 `CONFIRMED`**, **H3 `REFUTED`** (approved §5.4 policy, primary), **H3 `REFUTED`** (§11.3 sensitivity policy), **H4 `CONFIRMED`**.
**Campaign plan §10.4 D1 flag: RAISED** (on H3, publication-fidelity mismatch; pre-registration §4.3). This report completes (§10.4 item 2) and then **blocks session `0164`** and every later campaign session (§8.3).
**Report date:** 2026-10-14 UTC.
**Session:** `0163` (EXP-002 / C1, E5 — Report). **Predecessor:** `0162` (E4 — Analysis). **Successor:** `0164` (EXP-003 / C2 E1 — Pre-registration, **BLOCKED**).
**Branch / PR:** `campaign/0159-exp002-e1` / PR #33 (open; not merged).
**Operator / maintainer:** MichaelMaillet.
**AI pair drafting this report (Experimentation Standards §4 authorship disclosure):** Devin (`Gemini 4 Argon High`).
- **Stage-by-stage authorship across EXP-002:** The E1 pre-registration body (`preregistration.md` §§1–10) and collection driver (`benchmarks/campaign/exp002_driver.py`) were drafted by **Devin** (session `0159`). The PR #33 pre-E2 review remediation (`preregistration.md` §§11.1–11.2, `DOCS/audits/PR033-multi-review-audit.md`) and the E2 review and approval record (`e2-review.md`, `preregistration.md` §11.3) were drafted by **Claude Opus 5.5** (sessions `0159`–`0160`). The E3 execution commands and `log.md` were issued and recorded by **Claude Sonnet 5.5** at the maintainer's direction (session `0161`). The E4 registered analysis module (`analysis/exp002_e4_analysis.py`), its 176 synthetic tests (`tests/test_exp002_e4_analysis.py`), `analysis.md`, and `report-manifest.json` were drafted by **Claude Opus 5.5** (session `0162`). This E5 report (`report.md`), the E5 retained-bytes verification, the clean-worktree regeneration check, the §8.2 reconstruction, the independent recount, and the D1 contingency briefs were drafted and executed by **Devin (`Gemini 4 Argon High`)** (session `0163`).
- **Cold-review independence disclosure:** Because this E5 report was drafted by a Gemini-family model (`Gemini 4 Argon High`), the Antigravity (`gemini-3.8-flash-high`) read-only cold reviewer is in the same model family and is **not** model-family independent of the E5 author. Two rounds of `agy --model gemini-3.8-flash-high --mode plan --output-format text` ran to completion (`exit 0`), surfacing four documentation/formatting items (`AUDIT-EXP002-F1`..`F3` in Round 1 and `FINDING-EXP002-E5-01`..`02` in Round 2; all EXP-002 items verified and fixed before commit). Invoking `devin --model swe-2-high --respect-workspace-trust false -p …` exited `1` with `Error: Not logged in. Run devin.exe auth login to authenticate.`, and two attempts with `agy --model gpt-oss-120b-medium` did not produce a completed review (attempt 1 stopped at a plan-confirmation prompt under `--mode plan`; attempt 2 exited `3` with HTTP `503 UNAVAILABLE: No capacity available for model gpt-oss-120b-medium on the server`). All transcripts are preserved verbatim in `EVIDENCE/0163/verification/delegation/`, supplemented by a deterministic programmatic self-audit (`programmatic-self-audit.txt`), and the maintainer is asked at E5 close whether to run an additional non-Gemini cold reviewer.
- **Verification status:** Every count, digest, and byte size in this report was re-derived in session `0163` from the committed E3 raw records, the retained publication roots, and the frozen E4 analysis module. **The maintainer's verification and acceptance of the E4/E5 verdicts has not yet occurred and is not claimed** (§14).

| Record | Value |
|---|---|
| Pre-registration (frozen) | [`preregistration.md`](preregistration.md) @ `F` = `9a9889d08dcaf2ad0ce31659ed67721b54b114d0`, frozen at first `RUN-` creation on `2026-10-12T21:27:05Z`; blob SHA-256 `0f3073dd2ed73b64071bcf3ae182510a69a26bd575b81b5a97cc5a1f9bbc8c8b` |
| E2 review and approval | [`e2-review.md`](e2-review.md) (`APPROVED` `2026-10-12 UTC`, MichaelMaillet delegated authority) |
| Execution source SHA `R` | `fae24c4393c7a0232e6c8f0a6388b1775aa5fc05` (`R7` = `fae24c4`; session `0161`) |
| Execution log | [`log.md`](log.md) (E3, session `0161`; line 1 freeze-SHA erratum added in `7d850ba`) |
| Input manifest | `paper/artefact_manifest.json` — `172` records (`16,047,018` bytes), SHA-256 `300cdc094d2b7d27ac8b1e2556b2e6ed4dad3333f0038b45c8f87ea81612cce5` |
| Analysis code (frozen) | [`analysis/exp002_e4_analysis.py`](analysis/exp002_e4_analysis.py) @ `3731fc2590cf86bdb657fce25e4917d26567b23a` (pushed `2026-10-13T16:10:53Z`, before the first real run at `16:11:43Z`), SHA-256 `7a400aa66d1edd9a8aa41967f22ed77b720f0534bba6f9fe99f3af703d6ee4e4`; tests `tests/test_exp002_e4_analysis.py` (176 synthetic tests, 99 % branch coverage) |
| Analysis record | [`analysis.md`](analysis.md) (E4, session `0162`; commit `cad9a8c502bfd38800594336663f621990bb8b22`) |
| Output manifest | [`report-manifest.json`](report-manifest.json) (`18,848` bytes, SHA-256 `6b15dcc112513cdce9cb2d923208f93d3616898225efed545706c56526e68781`) |
| Raw artefact root | [`benchmarks/results/EXP-002/`](../../../benchmarks/results/EXP-002/README.md) (five immutable `RUN-` directories) |
| Retained generated roots | `DOCS/test_and_benchmark_results/EXP-002/<run-id>/{inputs,publication}` (gitignored; retained unmodified per E2 decision 8) |
| Campaign plan row | [`DOCS/experiments/campaign-plan.md`](../campaign-plan.md) §2.1 `EXP-002 / C1` |
| Related Plan items | Project Plan §3.1 `F1`, `F2`, `F4` (amendment #51), §5 items 4–5, §6 Phase 7 `C1`, §9 DoD `1`, `3`, `5`, `12` |
| Errata against this report | [§15](#15-errata) — none at initial issue |

---

## 1. Summary verdicts (pre-registration §4.1, §7, §11.3; campaign plan §9.1)

The pre-registered decision rules (`preregistration.md` §§4.1, 5.2, 5.4, 5.5, 11.3) were frozen at `F = 9a9889d08dcaf2ad0ce31659ed67721b54b114d0` before the first E3 run and applied without modification. All five E3 run records are `COMPLETED` and admissible; zero runs and zero observations aborted (`aborted_runs = []`, `inadmissible_runs = []`).

| Hypothesis | Verdict | Registered denominator (unit) | Pass / Equal | Fail / Differ | Missing / Extra / Unverifiable | Effect size & 95 % CI | Primary evidence |
|---|---|---:|---:|---:|---|---|---|
| **H1** — API mapping census | **CONFIRMED** | `175` (`api_symbol`); `172` (`legacy_api_name`) | `175/175` `api_symbols` resolved (`172` callable, `3` constants); `172/172` `legacy_api_names` owned; `175` observed exports | `0` failing `api_symbols`; `0` unowned `legacy_api_names`; `0` duplicate/removed/unexpected; frozen sets `0/0` | `0` unverifiable `api_symbols` | not applicable (deterministic census; §7) | `RUN-20261012T212705Z-fae24c4-api-cpu/api.json`, §3.1 |
| **H2** — Historical conclusion preservation | **CONFIRMED** | `62` (`claim_comparator_record`) across 5 families | `62/62` `claim_comparator_records` agree (`C01` `5/5`, `C02` `42/42`, `C03` `4/4`, `C04` `5/5`, `C05` `6/6`) | `0` disagree | `0` missing | not applicable (deterministic census; §7) | `RUN-20261012T213054Z-fae24c4-conclusions-cpu/conclusions.json`, §3.2 |
| **H3** — Publication fidelity (approved §5.4 policy, **primary**) | **REFUTED (D1)** | `39` (`generated_file`: `14` PDF, `14` PNG, `11` `.tex` tables); `11` tables vs archived | `21/39` `generated_files` equal (`5/14` PDF, `5/14` PNG, `11/11` `.tex`); `11/11` PRIN tables & `11/11` reference tables equal archived | **`18/39` `generated_files` differ** (`9/14` PDF, `9/14` PNG: figures 5, 7, 8, 9, 10, 11, 12, 14, 15); `0/11` tables differ from archived | `0` missing, `0` extra in either arm | not applicable (deterministic census; §7) | `RUN-…-reproduction-reference-cpu` vs `RUN-…-reproduction-prin-cpu`, §3.3 |
| **H3** — Publication fidelity (§11.3 **sensitivity** policy, pre-exposure `6314532`) | **REFUTED** | `39` (`generated_file`); `11` tables vs archived (raw bytes) | `5/39` `generated_files` equal (`0/14` PDF, `5/14` PNG, `0/11` `.tex`); `11/11` PRIN tables equal archived | **`34/39` `generated_files` differ** (`14/14` PDF, `9/14` PNG, `11/11` `.tex`); `11/11` reference tables inconsistent with archived (CRLF vs LF) | `0` missing, `0` extra in either arm | not applicable (deterministic census; §7) | `RUN-…-reproduction-reference-cpu` vs `RUN-…-reproduction-prin-cpu`, §3.4 |
| **H4** — Deterministic reproduction | **CONFIRMED** | `39` (`generated_file`) | `39/39` `generated_files` raw-identical (`14/14` PDF, `14/14` PNG, `11/11` `.tex`); §5.5 canonical projection equal (`true`) | `0` raw differences; `0` projection differences | `0` only in `prin`, `0` only in `repeatability` | not applicable (deterministic census; §7) | `RUN-…-reproduction-prin-cpu` vs `RUN-…-seedrep0-prin-cpu`, §3.5 |

**Why effect sizes, confidence intervals, and significance tests are "not applicable" (pre-registration §7; campaign plan §9.1; `e2-review.md` §3 and decision 5).** Although the generic template text in the session `0162` and `0163` briefs mentions effect sizes and 95 % confidence intervals, protocol §7 and campaign plan §9.1 govern: H1, H2, H3, and H4 are deterministic censuses of fixed, finite populations (`175` `api_symbols`, `172` `legacy_api_names`, `62` `claim_comparator_records`, and `39` `generated_files`) with `replicates = 1`, `measurement_kind = "deterministic_census"`, and `seed_used = false` (`iterations = 10` and `warmup = 0` in the `BenchmarkConfig` envelope are unused schema-compatibility fields and must never be read as sample size `n`). Repeating identical deterministic inputs would not create independent samples or statistical power, and campaign plan §9.1 forbids using any significance test, pooled pass rate, or interval to rescue a falsifier. Note also that the `39` publication `generated_files` and the `7` E4 analysis output files (`analysis_output_file_count = 7`) are separate populations and are never summed.

---

## 2. Results versus the pre-registered expectations (pre-registration §3)

Side-by-side comparison of pre-registration §3's predictions against the observed outcomes (matching `DOCS/test_and_benchmark_results/EXP-002/analysis/expected-vs-observed.md`, SHA-256 `97ecd3ab53bdbee2cf22e22e49866843544f70b3803213560978b4185af71789`):

| Hypothesis | Predicted direction (protocol §3) | Predicted magnitude (protocol §3) | Independent basis (protocol §3) | Observed (exact counts and units) | Verdict & expectation match |
|---|---|---|---|---|---|
| **H1** | Complete namespace and ownership preservation | `175/175` resolved; `172/172` owned; zero duplicate/missing/extra names | Frozen reference literal API, WP-001 ownership matrix, PRIN canonical tuple, Migration Guide; inspected statically at E1 | `175/175 api_symbols` resolved (`172` callable, `3` scalar constants); `172/172 legacy_api_names` owned; `175` observed export-list entries; duplicates `0`, removed `0`, unexpected `0`; frozen-contract missing/extra `0/0`; unverifiable rows `0` | **CONFIRMED** — matches prediction in full |
| **H2** | No reversal of registered historical predicates | `62/62` agreements; zero disagreements | Published chimera/topology/Goldilocks claims and previously stored threshold flags, specified per family in §5.2; no new PRIN outcomes used | `62/62 claim_comparator_records` agree (`C01` `5/5`, `C02` `42/42`, `C03` `4/4`, `C04` `5/5`, `C05` `6/6`); `0` disagree | **CONFIRMED** — matches prediction in full |
| **H3 (approved policy, primary)** | Reference-faithful publication representation | `39/39` equal under the registered format-specific comparison | Faithful generator ports; the existing 11-table reference-byte acceptance contract; fixed matched rendering environment and explicitly declared metadata normalization | `21/39 generated_files` equal (`5/14` PDF, `5/14` PNG, `11/11` `.tex`); **`18/39` differ** (`9/14` PDF and `9/14` PNG); missing reference/PRIN `0/0`; extra reference/PRIN `0/0`; PRIN tables equal to archived `11/11`; reference tables inconsistent with archived `0/11` | **REFUTED (D1)** — table prediction (`11/11`) and `5/14` figures hold, but `9/14` figures (`18/39` files) differ |
| **H3 (§11.3 sensitivity policy)** | Registered sensitivity analysis (§11.3 item 1), not a separate prediction | Reported beside the primary H3 verdict | Pre-exposure (`6314532`) comparison policy: raw table bytes, in-place PDF Info value masking, PNG normalization | `5/39 generated_files` equal (`0/14` PDF, `5/14` PNG, `0/11` `.tex`); **`34/39` differ** (`14/14` PDF, `9/14` PNG, `11/11` `.tex`); missing `0/0`; extra `0/0`; PRIN tables equal to archived `11/11`; reference tables inconsistent with archived `11/11` | **REFUTED** — agrees with the primary H3 verdict; H3 does **not** depend on the post-exposure amendment |
| **H4** | Exact same-implementation repeatability | `39/39` raw byte identities; zero projection differences | `tools/reproduce.py` deterministic pipeline, fixed figure dates, explicit output roots, sorted manifests, deterministic table formatting | `39/39 generated_files` raw-identical (`14/14` PDF, `14/14` PNG, `11/11` `.tex`); `0` differ; only in PRIN/repeat `0/0`; canonical projection equal: `true` | **CONFIRMED** — matches prediction in full |

**Clarification on the generated label `"tables equal to archived 11/11"` (carried from `analysis.md` post-run self-audit item F-1).** In the generated `expected-vs-observed.md` and in `summary.json`, the field `tables_equal_to_archived` (`11/11` under both policies) counts the **PRIN** arm's 11 tables against the 11 archived reference tables (`REFERENCE/paper/tables/tab_*.tex`). The reference arm's comparison against the archived tables is recorded in the separate field `reference_tables_inconsistent_with_archived`: `[]` (`0/11` inconsistent) under the approved CRLF→LF policy, and all `11` table paths (`11/11` inconsistent) under the raw-byte sensitivity policy because the reference table writer opens files in text mode without `newline="\n"`, writing CRLF on Windows whereas the archived tables and PRIN's tables use LF.

---

## 3. Per-hypothesis results and E5 independent recount

In session `0163`, before drafting this report, an independent recount script (`EVIDENCE/0163/verification/regeneration/independent-recount.txt`, stdlib-only Python that does **not** import `exp002_e4_analysis.py`, `exp002_driver.py`, `prin`, or `prinet`) parsed the five raw JSON records directly and recomputed every count, classification, operand comparison, policy digest comparison, and projection comparison. Every number below matched the E4 analysis outputs and `report-manifest.json` with **zero discrepancies**.

### 3.1 H1 — API mapping census: `CONFIRMED`

- **Source record:** `benchmarks/results/EXP-002/RUN-20261012T212705Z-fae24c4-api-cpu/api.json` (`97,194` B, SHA-256 `b76aedab424582dec72ede165c6a136e62c802b395519cba56975fa75f0fade9`).
- **Expected population (`175` `api_symbols`):** the `172` unique names in `REFERENCE/src/prinet/__init__.py` literal `__all__` (SHA-256 `ede92afc6771f2e29206534905e2820598ba841662a93d59f669f803a382f182`) union the `3` disjoint PRIN additions (`BackendUnavailableError`, `__version__`, `core_version`).
- **Resolution census:** `175/175` `api_symbols` resolved (`resolved = true`, `error = null`):
  - `172` classified as `callable` (`callable = true`, non-`None` class or function export);
  - `3` classified as scalar `constant` (`callable = false`, `type` in `{"int", "str"}`: `CONTROL_DIM` (`int`), `STATE_DIM` (`int`), and `__version__` (`str`)).
  - `0` `none`, `0` `unsupported`, `0` `unresolved`, `0` `unverifiable`.
- **Legacy ownership census (`172` `legacy_api_names`):** `172/172` have both a Migration Guide row (`DOCS/sphinx/migration_guide.rst` `.. wp036-consolidated-table-begin`..`end`) and a WP-001 ownership row (`DOCS/baselines/wp001_api_traceability.md`); `0` unowned.
- **Observed `prin.__all__` list:** `175` entries, `175` unique (`0` duplicates, `0` removed exports, `0` unexpected exports).
- **Frozen RC1 contract check (`verify_api_surface(prin.__all__)` against `FROZEN_PUBLIC_API` derived from `RC1_PUBLIC_API` at `R`):** `frozen_missing = []` (`0`), `frozen_extra = []` (`0`).
- **Counterexamples:** `0`. Coverage complete (`unverifiable = 0`). Verdict under §4.1: **`CONFIRMED`**.

### 3.2 H2 — Historical conclusion preservation: `CONFIRMED`

- **Source record:** `benchmarks/results/EXP-002/RUN-20261012T213054Z-fae24c4-conclusions-cpu/conclusions.json` (`59,206` B, SHA-256 `2d1cdc5fa76b247da1b8544606708b6fa0ffe9afaaf274604bc4c1115e9bed84`).
- **Population (`62` `claim_comparator_records` across 5 registered families):** every input JSON file is verified against `paper/artefact_manifest.json` (`300cdc09…`), and every operand, JSON pointer path, operator, unit, and expected Boolean was re-derived from the frozen JSON inputs:

| Family | Frozen input JSON | Registered predicate population | Operand unit | Denominator (`claim_comparator_record`) | Agree | Disagree | Missing |
|---|---|---|---|---:|---:|---:|---:|
| `C01` | `phase1_chimera_seeds.json` | `bimodality_coefficient.raw_values[i] > 0.555` for `i = 0..4` (expected `true`; `paper/main.tex` §`sec:chimera`) | `BC` (dimensionless) | `5` | `5` | `0` | `0` |
| `C02` | `benchmark_y4q1_3_k_alpha_sensitivity.json` | All `42` distinct `(K, alpha)` grid rows: `bc_mean > 0.555` compared with that row's stored `chimera_detected` Boolean (`26` `true`, `16` `false`; archival self-consistency, Fig. 4) | `BC` (dimensionless) | `42` | `42` | `0` | `0` |
| `C03` | `phase2_chimera_nsweep.json` | Four `sweep` rows at `n_oscillators` ∈ `{128, 256, 512, 1024}`: `bc_stats.mean > 0.5` (expected `true`; `paper/main.tex`) | `BC` (dimensionless) | `4` | `4` | `0` | `0` |
| `C04` | `y4q1_8_topology_comparison.json` | Ring `bc_mean` > `2community` and `4community` means (2); ring `bc_ci.ci_width` > `2community` and `4community` widths (2); `2community` width > `4community` width (1) (`paper/supplementary.tex` Table `tab:topology`) | `BC` (2); `historical_BC_CI_width` (3) | `5` | `5` | `0` | `0` |
| `C05` | `y3q49_goldilocks_zones.json` | CPU regimes `csr_cpu`, `full_cpu`, `mean_field_cpu`, `sparse_knn_cpu`: `csr_cpu` `zone_width` > each other width (3); `full_cpu` `K_c` < each other onset (3) (`paper/supplementary.tex` Table `tab:goldilocks`) | `stored_coupling_K` | `6` | `6` | `0` | `0` |
| **Total** | — | — | — | **`62`** | **`62`** | **`0`** | **`0`** |

- **Counterexamples:** `0`. Coverage complete (`62/62`). Verdict under §4.1: **`CONFIRMED`**.

### 3.3 H3 — Publication fidelity under the approved §5.4 policy (primary): `REFUTED (D1)`

- **Source records:**
  - Reference arm (`prinet` 3.0.0 frozen generators): `benchmarks/results/EXP-002/RUN-20261012T213821Z-fae24c4-reproduction-reference-cpu/reproduction.json` (`59,584` B, SHA-256 `70f9677c7523c2decf3dc0b9e3e1ba8763ee56838ff63deca93587b42c89e7e3`).
  - PRIN arm (`tools.reproduce.run_reproduction`): `benchmarks/results/EXP-002/RUN-20261012T213936Z-fae24c4-reproduction-prin-cpu/reproduction.json` (`59,572` B, SHA-256 `776a926df8edb333e38d61e9fc4ba2966385df56bcfc3d9eda6540c7c47b590e`).
- **Matched renderer environment (verified identical before and after generation on both arms):** Python `3.14.0`, Matplotlib `3.11.1`, NumPy `2.5.1`, Pillow `12.3.0`, FreeType `2.14.3`, backend `Agg`, font cache `fontlist-v3.11.0.json` (`146,692` B, SHA-256 `9c00441405ce72925562e017858a729b402612a203b0682b2e7fd79329c8f6bb`), 40 bundled `.ttf` fonts (canonical font-map SHA-256 `168e1aee710ca4496f65d7dc0689ed93257ed3e1ab3711dad4494940b51c8189`).
- **Inventory:** Both arms produced all `39` registered `generated_files` (`14` figures × 2 formats `.pdf`/`.png` = `28` figure files, plus `11` `.tex` tables; `0` missing in either arm, `0` extra in either arm).
- **Approved comparison policy (§5.4, `e2-review.md` decision 7):**
  - `.tex` tables: CRLF (`\r\n`) canonicalized to LF (`\n`) symmetrically in both arms and the archived baseline (proven in Lean 4, `CrlfCanonical.lean`, to invert Windows text-mode newline translation without masking any other byte).
  - `.pdf` figures: validated Matplotlib single-revision classic-xref container; the four registered metadata keys (`CreationDate`, `ModDate`, `Creator`, `Producer`) and their values are removed from the flat `/Info` dictionary and the remaining entries re-serialized; trailer `/ID` masked; in-use `xref` offsets and `startxref` canonicalized to `0`; all drawing, image, and font streams preserved untouched.
  - `.png` figures: validated PNG container and decoded pixels (`_validate_png`, Z3-verified against the PNG colour specification); critical chunks `IHDR`/`PLTE`/`tRNS`/`IDAT`/`IEND` retained via `normalize_matplotlib_output`.
- **Outcome by format (`generated_file` unit):**

| Format | Registered denominator (`generated_file`) | Equal (approved policy) | Differ (approved policy) | Missing | Equal (§11.3 sensitivity policy) | Differ (§11.3 sensitivity policy) |
|---|---:|---:|---:|---:|---:|---:|
| `pdf` | `14` | `5` | **`9`** | `0` | `0` | **`14`** |
| `png` | `14` | `5` | **`9`** | `0` | `5` | **`9`** |
| `tex` | `11` | `11` | `0` | `0` | `0` | **`11`** |
| **Total** | **`39`** | **`21`** | **`18`** | **`0`** | **`5`** | **`34`** |

- **The 21 equal files under the approved policy:**
  - All `11/11` LaTeX tables (`tables/tab_ablation.tex`, `tab_binding_params.tex`, `tab_chimera.tex`, `tab_efficiency.tex`, `tab_geometry.tex`, `tab_occlusion.tex`, `tab_oscillosim.tex`, `tab_param_efficiency.tex`, `tab_statistical.tex`, `tab_stress.tex`, `tab_supercritical.tex`), which also match the `11/11` archived tables (`tables_equal_to_archived = 11`, `tables_differing_from_archived = []`, `reference_tables_inconsistent_with_archived = []`).
  - Both `.pdf` and `.png` of `5` figures (`10` files): `fig2_clevr_n_capacity`, `fig3_chimera_metrics`, `fig4_chimera_k_alpha_heatmap`, `fig6_oscillosim_scaling`, and `fig13_representation_geometry`.
- **The 18 differing files under the approved policy (counterexamples = `18`):**
  - Both `.pdf` and `.png` of `9` figures (`18` files):
    1. `figures/fig5_mot_occlusion_comparison.{pdf,png}`
    2. `figures/fig7_ablation_results.{pdf,png}`
    3. `figures/fig8_parameter_efficiency.{pdf,png}`
    4. `figures/fig9_training_curves.{pdf,png}`
    5. `figures/fig10_statistical_summary.{pdf,png}`
    6. `figures/fig11_flops_scaling.{pdf,png}`
    7. `figures/fig12_supercritical_regime.{pdf,png}`
    8. `figures/fig14_gradient_flow.{pdf,png}`
    9. `figures/fig15_noise_velocity.{pdf,png}`
- **Verdict under §4.1:** Because `18` admissible normalized-figure comparisons differ (`counterexample_count = 18`), H3 is **`REFUTED`**, raising a campaign plan §10.4 **D1** flag. **No cause is asserted in this report**; root-cause investigation belongs exclusively to the D1 correction cycle's S1 session (§8).

### 3.4 H3 under the §11.3 sensitivity policy (pre-exposure `6314532` policy): `REFUTED`

- **Why registered (`preregistration.md` §11.3 item 1, `e2-review.md` decision 9):** Because two PR #33 reviews published H2/H3 outcome information before E2, E2 registered a sensitivity analysis under the pre-exposure (`6314532`) comparison policy (raw bytes for `.tex` tables; in-place value masking `/(CreationDate|ModDate|Creator|Producer) (normalized)` in `/Info` without removing keys, so the reference arm's 3 keys and the PRIN arm's 4 keys remain different in key set and byte length; identical `.png` normalization).
- **Outcome:** `5/39` `generated_files` equal (the `5` PNGs `fig2`, `fig3`, `fig4`, `fig6`, `fig13`) and `34/39` `generated_files` differ (`14/14` PDFs, the same `9/14` PNGs as under the approved policy, and `11/11` `.tex` tables). For the archived-table comparison under raw bytes, `11/11` PRIN tables equal the archived tables (`tables_equal_to_archived = 11`, `tables_differing_from_archived = []`), while `11/11` reference-arm tables differ from the archived tables by CRLF vs LF (`reference_tables_inconsistent_with_archived` lists all 11 tables).
- **Agreement of policies:** Both the approved policy and the sensitivity policy return **`REFUTED`** (`h3_policies_agree = true`). Therefore, pre-registration §11.3 item 1's conditional disclosure ("If the two verdicts differ, E5 must state that H3's verdict depends on a comparison amendment made after outcome exposure") is **not triggered**: H3's refutation does not depend on the post-exposure amendment.

### 3.5 H4 — Deterministic reproduction: `CONFIRMED`

- **Source records:**
  - First PRIN process (`prin`): `benchmarks/results/EXP-002/RUN-20261012T213936Z-fae24c4-reproduction-prin-cpu/reproduction.json` (`59,572` B, SHA-256 `776a926df8edb333e38d61e9fc4ba2966385df56bcfc3d9eda6540c7c47b590e`).
  - Second PRIN process (`repeatability`, replicate 0 rerun): `benchmarks/results/EXP-002/RUN-20261012T214040Z-fae24c4-seedrep0-prin-cpu/reproduction.json` (`59,568` B, SHA-256 `ec615eb48008bcc112ad73a10fc6ea42ddf5619ecb33b87e880a1e7977084127`; the 4-byte file-size difference in `reproduction.json` itself is the shorter `config.out_dir` string `...-seedrep0-prin-cpu` vs `...-reproduction-prin-cpu`).
- **Outcome:** `39/39` `generated_files` (`14/14` PDFs, `14/14` PNGs, `11/11` `.tex` tables) have identical filenames, identical `raw_bytes`, and identical `raw_sha256` digests across both separate interpreter processes (`raw_differing_generated_files = []`, `only_in_prin = []`, `only_in_repeat = []`). No normalization is used in H4.
- **Canonical projection (§5.5):** Removing only per-run `environment`, `config.out_dir`, `started_at_utc`, `recorded_at_utc`, and `elapsed_seconds` produces byte-identical canonical JSON projections (`projection_equal = true`).
- **Counterexamples:** `0`. Verdict under §4.1: **`CONFIRMED`**.

---

## 4. Bearing on Project Plan requirements and Definition of Done

Pre-registration header line 13 cites Project Plan §3.1 `F1`, `F2`, `F4`, §5 items 4–5, §6 Phase 7 `C1`, and §9 Definition of Done (`DoD`) items `1`, `3`, `5`, and `12`. Consistent with Experimentation Standards §1.5 ("Claims match evidence"), the table below quotes each cited Plan clause verbatim and states **only** what the registered EXP-002 verdicts support — without declaring any F-item or DoD item closed or failed beyond that evidence.

| Plan clause | Verbatim wording in `DOCS/PRIN_Project_Plan.md` | EXP-002 hypothesis bearing on it | What the registered EXP-002 verdict supports (and does not support) |
|---|---|---|---|
| **§3.1 F1 — Feature parity** | *"every public class/function in PRINet 3.0's 175+-symbol API has an equivalent."* | **H1 (`CONFIRMED`)** | Supports that all `175` expected `prin` exports (`172` frozen `prinet` names + `3` PRIN additions) resolve to non-`None` callables (`172`) or scalar constants (`3`), that `verify_api_surface(prin.__all__)` returns empty missing/extra sets against `FROZEN_PUBLIC_API`, and that all `172` legacy names have Migration Guide and WP-001 ownership rows. Does **not** by itself prove runtime behavioural or numerical equivalence of every callable (`preregistration.md` §2; `e2-review.md` decision 1). |
| **§9 DoD #1** | *"Every PRINet 3.0 public symbol (175+) has a working equivalent; renames documented in the Migration Guide."* | **H1 (`CONFIRMED`)** | Supports the export-resolution and Migration Guide mapping census (`175/175` resolved, `172/172` documented in the Migration Guide table). Behavioural/numerical equivalence of the underlying implementations belongs to the test suite, EXP-001-r1, and C2–C4 replication experiments. |
| **§3.1 F2 — Numerical parity** | *"trajectories, metrics, and benchmark results match 3.0.0 within the documented tolerances (§5)."* | **H2 (`CONFIRMED`)** | Supports that all `62/62` registered elementary direction/threshold predicates across families `C01`–`C05` in the frozen 172-artefact JSON set hold as predicted (`0` reversals). Trajectory and metric numerical parity on the 504-case corpus and 1,000-case fuzz stream was adjudicated separately in `EXP-001-r1`. Fresh benchmark/replication measurements remain owned by EXP-003–EXP-008 (§7). |
| **§5 item 4 — Benchmark-result parity** | *"full re-run of the benchmark suite; scientific conclusions unchanged; deviations documented in the Parity Report."* | **H2 (`CONFIRMED`), H3 (`REFUTED`)** | H2 confirms preservation of the 62 registered CPU-readable archival conclusion predicates from the stored JSON artefacts; it is **not** the full benchmark re-run (`preregistration.md` §1, §5.3). H3's D1 refutation (`18/39` publication files differing from the reference generator) is documented via an erratum in the Parity Report (§8.4). |
| **§9 DoD #3** | *"The parity suite passes at §5 tolerances; the Parity Report is published."* | **H2 (`CONFIRMED`), H3 (`REFUTED`)** | The Parity Report (`DOCS/sphinx/parity_report.rst`) remains a pre-release draft and is updated in this session with an erratum for EXP-002 H3's D1 (§8.4). DoD #3 remains open until the campaign completes. |
| **§3.1 F4 — Reproducibility (amendment #51)** | *"`tools/reproduce.py` regenerates all 14 verifiable figures (figures 2–15; there was never a figure 1) and 11 tables byte-comparably from the same JSON artefacts with a matching SHA-256 manifest (amendment #51)."* | **H3 (`REFUTED`), H4 (`CONFIRMED`)** | **H4 (`CONFIRMED`)** supports **PRIN-versus-PRIN** repeatability: two separate invocations of `tools/reproduce.py` (`prin` and `repeatability` legs, plus the E5 §8.2 reconstruction) regenerate all `39/39` files (`14` figures × 2 formats + `11` tables) raw-byte-identically from the 172 manifest-verified JSON inputs. **H3 (`REFUTED`)** is the **PRIN-versus-reference-generator** (`prinet` 3.0.0) comparison: `11/11` tables match the reference generator (under CRLF→LF canonicalization) and the archived tables (`11/11` raw-identical in PRIN), and `5/14` figures (`10` files) match under the approved normalization, but `9/14` figures (`18/39` files) differ between PRIN and the reference generator. |
| **§5 item 5 — Bit-level reproducibility** | *"all RNG behind the single `Seed` type; exact reproducibility across CPU/GPU and across runs."* | **H4 (`CONFIRMED`)** | Supports exact cross-run raw-byte repeatability (`39/39` files) and canonical-projection identity for PRIN's deterministic publication pipeline on the Windows reference host (`seed_used = false`). |
| **§9 DoD #5** | *"`tools/reproduce.py` regenerates all figures/tables with a matching SHA-256 manifest."* | **H3 (`REFUTED`), H4 (`CONFIRMED`)** | Same distinction as F4 above: PRIN-versus-PRIN regeneration is `39/39` raw-byte-identical (`H4 CONFIRMED`, and E5 reconstruction `39/39`), whereas PRIN-versus-reference-generator comparison is `21/39` equal / `18/39` differing under the approved policy (`H3 REFUTED`, D1 raised). |
| **§9 DoD #12** | *"The Phase 7 campaign is complete: all experiments pre-registered and reported per the Experimentation Standards; campaign summary published."* | **All (`D1 RAISED`)** | EXP-002 is reported in full here, and its H3 refutation triggers a campaign plan §10.4 D1 correction cycle (S1→S4 followed by `EXP-002-r1`), blocking `0164` and downstream campaign sessions until resolved (§8). |

---

## 5. Runs, aborts, exclusions, and resource budget

**No run aborted. No observation aborted. No symbol, claim predicate, or publication file was excluded from any denominator.** Each registered leg ran once, in its own Python interpreter process, at clean source `R = fae24c4393c7a0232e6c8f0a6388b1775aa5fc05`, in the exact order registered in pre-registration §5.5 (`log.md` §§4–5).

| # | Mode | Label | Run ID | Hypotheses | UTC start → end (`2026-10-12`) | Exit | Wrapper wall (s) | Driver `elapsed_seconds` (s) | `status` | Admissible |
|---:|---|---|---|---|---|---:|---:|---:|---|---|
| 1 | `api` | `api-cpu` | `RUN-20261012T212705Z-fae24c4-api-cpu` | H1 | `21:27:05.708Z` → `21:27:16.461Z` | `0` | `10.733` | `0.3224` | `COMPLETED` | yes |
| 2 | `conclusions` | `conclusions-cpu` | `RUN-20261012T213054Z-fae24c4-conclusions-cpu` | H2 | `21:30:54.253Z` → `21:31:04.800Z` | `0` | `10.521` | `0.2890` | `COMPLETED` | yes |
| 3 | `reference` | `reproduction-reference-cpu` | `RUN-20261012T213821Z-fae24c4-reproduction-reference-cpu` | H3 | `21:38:21.711Z` → `21:38:35.945Z` | `0` | `14.212` | `4.0048` | `COMPLETED` | yes |
| 4 | `prin` | `reproduction-prin-cpu` | `RUN-20261012T213936Z-fae24c4-reproduction-prin-cpu` | H3, H4 | `21:39:36.175Z` → `21:39:50.366Z` | `0` | `14.172` | `4.0830` | `COMPLETED` | yes |
| 5 | `repeatability` | `seedrep0-prin-cpu` | `RUN-20261012T214040Z-fae24c4-seedrep0-prin-cpu` | H4 | `21:40:40.138Z` → `21:40:54.339Z` | `0` | `14.183` | `4.1729` | `COMPLETED` | yes |
| **Total** | — | — | **5 runs (`0` aborted, `0` reruns)** | — | — | — | **`63.821`** | **`12.8721`** | — | **5 / 5** |

### Budget accounting against pre-registration §9 and campaign plan §§7.5, 8

| Resource | Measured | Registered cap | Status |
|---|---|---|---|
| H1 Windows CPU wall (all E3 attempts) | `63.821 s` (`0.0177 h`; sum of driver `elapsed_seconds` = `12.8721 s`) | `≤ 12 h` (`43,200 s`) | Within cap (`0.15 %` used) |
| H1 GPU wall | `0 s` (no GPU leg registered or executed) | `≤ 2 h` | Within cap (`0 %` used) |
| Hosted CI wall (experiment legs) | `0 s` (cross-OS `reproduce.py` leg suspended under amendment #48; amendment #50 PR/nightly checks are source validation, logged and not charged per E2 decision 10) | `≤ 2 h` | Within cap (`0 %` used) |
| Single-run tracked JSON size (largest run: `api-cpu`) | `97,963 B` (`0.0934 MiB`; other four runs `60,007` / `60,396` / `60,387` / `60,375 B`) | `≤ 2 MiB` (`2,097,152 B`) | Within cap (`4.67 %` used) |
| EXP-002 raw + record root tracked artefacts (`benchmarks/results/EXP-002/` `341,520 B` + `DOCS/experiments/EXP-002-…/` including this report) | `~0.68 MiB` (`339,128 B` across the 15 run files + `2,392 B` raw-root `README.md` + record root) | `≤ 10 MiB` (`10,485,760 B`) | Within cap (`< 7 %` used) |
| Campaign-wide `benchmarks/results/EXP-*` tracked storage | `13,746,037 B` (`13.109 MiB`: EXP-001 `13,404,517 B` + EXP-002 `341,520 B`; `13,756,033 B` / `13.119 MiB` including `benchmarks/results/` top-level files) | `≤ 64 MiB` (`67,108,864 B`) | Within cap (`20.5 %` used) |

---

## 6. Retained-bytes verification, clean-checkout regeneration, and Protocol §8.2 reconstruction

Pre-registration §8.2 and §11.3 item 2 (`e2-review.md` decision 8) require E5 to **(1) first verify the retained generated publication bytes** under `DOCS/test_and_benchmark_results/EXP-002/<run-id>/publication/` against the raw digests manifested in each run's `reproduction.json`, **(2) regenerate the seven E4 analysis outputs** from a clean checkout of the recorded source and match `report-manifest.json` byte-for-byte, and **(3) only after Step 1 succeeds, reconstruct the 39 publication files** from their frozen 172-input snapshot and source recipe under the matched renderer/font environment. All three steps were executed in order in session `0163` (`EVIDENCE/0163/verification/`).

### 6.1 Step 1 — Verification of the retained publication and input bytes (executed first)

1. **Publication listing digests (`e2-review.md` §8 PowerShell one-liner, run verbatim from PowerShell):**
   - `reference` (`RUN-20261012T213821Z-fae24c4-reproduction-reference-cpu/publication`):
     `d674de7d4b5830c9abf525fcc484a5ebc01e3620ca38b63badd037e289487323` — **exact match** to `log.md` §4.3 and `analysis.md`.
   - `prin` (`RUN-20261012T213936Z-fae24c4-reproduction-prin-cpu/publication`):
     `c1ca4ada167c50a28db2dfe4365d004cdb3621903f43e38cc6de75c2e4904669` — **exact match** to `log.md` §4.4 and `analysis.md`.
   - `repeatability` (`RUN-20261012T214040Z-fae24c4-seedrep0-prin-cpu/publication`):
     `c1ca4ada167c50a28db2dfe4365d004cdb3621903f43e38cc6de75c2e4904669` — **exact match** to `log.md` §4.5 and `analysis.md`.
2. **Independent read-only, no-follow byte verification (`EVIDENCE/0163/verification/retained-bytes/retained-bytes-verification.txt`):**
   - Verified every directory and ancestor with `os.lstat` (`S_ISLNK` false and `st_reparse_tag == 0`).
   - Verified each run's `manifest.json` against `campaign-metadata.json` and `reproduction.json`, and verified the `reproduction.json` SHA-256 against the handoff anchors (`70f9677c…`, `776a926d…`, `ec615eb4…`).
   - For each of the three publication runs, walked `publication/` and compared the on-disk file set, byte sizes, and SHA-256 digests against the 39 file records in that run's `reproduction.json`: **`39/39` files present, `0` missing, `0` extra, `39/39` exact raw byte-size and raw SHA-256 matches** (`1,502,048 B` total in `reference`; `1,500,705 B` total in `prin` and `repeatability`).
   - For each of the three publication runs (which retain `inputs/`, as does the `conclusions` run), walked `inputs/` and compared the on-disk file set, byte sizes, and SHA-256 digests against the 172 records in `paper/artefact_manifest.json` (`300cdc09…`): **`172/172` files present, `0` missing, `0` extra, `172/172` exact byte-size and SHA-256 matches (`16,047,018 B` per run)**.
3. **Additional confirmation with `EVIDENCE/0161/verification/tools/validate_run_record_rev3.py` (`EVIDENCE/0163/verification/preflight/rev3-validation-*.txt`):**
   - All retention checks (`F1`–`F4` and `S1`) and all record/manifest/identity/schema checks passed on all five records (`80/81`, `79/80`, `86/87`, `86/87`, `86/87` passed). The single check returning `FAIL` on each run is `G1`, which diffs `R = fae24c4` against the current working tree across `frozen_paths` (which includes `tests/`) and flags `['tests/test_exp002_e4_analysis.py']`, the synthetic test file committed in session `0162` (`3731fc2`).

### 6.2 Step 2 — Clean-worktree regeneration of the seven E4 analysis outputs

To verify campaign plan §7.4 step 5 and protocol §8.2 without touching the main checkout, a detached git worktree of `HEAD` (`cad9a8c502bfd38800594336663f621990bb8b22`) was created outside the repository tree at `C:\dev\PRIN-0163-e5-wt`, and the frozen E4 analysis module was executed there (`EVIDENCE/0163/verification/regeneration/worktree-regeneration.txt`):

```text
git worktree add --detach C:/dev/PRIN-0163-e5-wt HEAD
C:/dev/PRIN/.venv/Scripts/python.exe -I C:/dev/PRIN-0163-e5-wt/DOCS/experiments/EXP-002-api-benchmark-result-and-reproduction-parity/analysis/exp002_e4_analysis.py
```

- **Run window:** `2026-10-14T19:12:37.329Z` → `2026-10-14T19:13:26.731Z` (`49.402 s`), exit code **`0`**.
- **Result:** All seven generated files under `DOCS/test_and_benchmark_results/EXP-002/analysis/` and `report-manifest.json` in the worktree matched the committed `report-manifest.json` (`6b15dcc112513cdce9cb2d923208f93d3616898225efed545706c56526e68781`) and `analysis.md` **byte-for-byte (`8/8` files identical)**. The worktree was removed immediately afterwards (`git worktree remove --force C:/dev/PRIN-0163-e5-wt`), leaving `C:\dev\PRIN` clean and its `report-manifest.json` untouched.

### 6.3 Step 3 — Protocol §8.2 reconstruction of the 39 publication files

- **Checkout limitation disclosed (protocol §8.2):** Unlike the stdlib-only E4 analysis module (which ran in a separate detached worktree in §6.2), reconstructing the 39 publication files imports `prin` (which requires the gitignored compiled extension `python/prin/_prin_core.pyd`) and `prinet` (installed via editable `.pth` files in `C:\dev\PRIN\.venv\Lib\site-packages` pointing at `C:\dev\PRIN\python` and the reference directory). A separate git worktree has no `_prin_core.pyd` and its editable imports would still resolve to `C:\dev\PRIN`. The reconstruction was therefore executed in the maintainer's clean checkout `C:\dev\PRIN` at `HEAD = cad9a8c502bfd38800594336663f621990bb8b22`, writing exclusively to a fresh gitignored directory `DOCS/test_and_benchmark_results/EXP-002-e5-reconstruction/` (never into `DOCS/test_and_benchmark_results/EXP-002/` or `benchmarks/results/EXP-002/`).
- **Environment match proved before and after rendering:**
  - Python `3.14.0`, Matplotlib `3.11.1`, NumPy `2.5.1`, Pillow `12.3.0`, FreeType `2.14.3`, backend `Agg`.
  - Font cache `fontlist-v3.11.0.json`: `146,692` bytes, SHA-256 `9c00441405ce72925562e017858a729b402612a203b0682b2e7fd79329c8f6bb` (identical to the E3 records).
  - Canonical 40-font map (`font_sha256`): SHA-256 `168e1aee710ca4496f65d7dc0689ed93257ed3e1ab3711dad4494940b51c8189` (identical to the E3 records).
- **Reconstruction results (`2026-10-14T19:15:01.340Z` → `19:15:32.582Z`, exit `0`; `EVIDENCE/0163/verification/reconstruction/reconstruction.txt`):**

| Arm (`implementation`) | Manifested E3 comparator record | Files generated | Raw-digest matches (`raw_bytes` & `raw_sha256`) | Normalized-digest matches (`normalized_bytes` & `normalized_sha256`) | Sensitivity-digest matches (`sensitivity_bytes` & `sensitivity_sha256`) | Listing digest of reconstructed `publication/` |
|---|---|---:|---:|---:|---:|---|
| **`prin`** | `RUN-20261012T213936Z-fae24c4-reproduction-prin-cpu/reproduction.json` (and `report-manifest.json` `publication_outputs`) | `39/39` | **`39/39`** (`14/14` PDF, `14/14` PNG, `11/11` `.tex`) | **`39/39`** | **`39/39`** | `c1ca4ada167c50a28db2dfe4365d004cdb3621903f43e38cc6de75c2e4904669` (**identical** to E3 `prin` and `repeatability`) |
| **`reference`** | `RUN-20261012T213821Z-fae24c4-reproduction-reference-cpu/reproduction.json` | `39/39` | **`25/39`** (`0/14` PDF, `14/14` PNG, `11/11` `.tex`) | **`39/39`** | **`39/39`** | `22dc4d76132d21753dc57a05afdbe1f61f2330830539d44f5bd2bf7f39949ff1` (differs from E3's `d674de7d…` on the 14 raw PDFs) |

- **Interpretation under pre-registration §8.2 and §11.3 item 2:**
  1. Every one of the `39` PRIN-arm publication files listed in `report-manifest.json` (`publication_outputs`) reproduced **raw-byte-identically (`39/39`)** during E5 reconstruction, and both arms reproduced **`39/39` normalized digests** and **`39/39` sensitivity digests** byte-identically.
  2. On the `reference` arm, the `14` PNGs and `11` `.tex` tables (`25/39` files) reproduced raw-byte-identically, while the `14` PDFs differed in `raw_sha256` (with identical `raw_bytes` on all 14 PDFs) because the pinned `prinet` 3.0.0 `_save_fig` passes no fixed `CreationDate` metadata to Matplotlib, so Matplotlib writes the current wall-clock timestamp into `/CreationDate` and hashes it into the PDF trailer `/ID`. Under both the approved normalization and the sensitivity normalization (which strip or mask `/CreationDate` and `/ID`), all `14/14` reference PDFs matched their E3 recorded digests (`39/39`).
  3. Per protocol §11.3 item 2, because the retained E3 bytes were verified `39/39` in Step 1 (§6.1), this reference-arm raw-PDF timestamp difference is recorded as a **reconstruction limitation** of the unpinned reference generator, never as a new H3/H4 observation, and alters no verdict. The scratch directory `DOCS/test_and_benchmark_results/EXP-002-e5-reconstruction/` was removed after capturing the verification transcript so only the original E3/E4 directories remain under `DOCS/test_and_benchmark_results/EXP-002/`.

---

## 7. Coverage and deferrals (pre-registration §5.3)

Pre-registration §5.3 requires E4 and E5 to carry the seven-row scientific-owner table verbatim so that no downstream obligation is silently treated as discharged by EXP-002's archival rendering (`DOCS/test_and_benchmark_results/EXP-002/analysis/coverage-and-deferrals.md`, SHA-256 `ff14a9f8592576f895a559b05d8b0848039d6efefc2b467d4bab97c3f94a18f9`):

| Historical conclusion class / source | Scientific owner | Status after EXP-002 E5 |
|---|---|---|
| CPU throughput, coupling complexity, sweep speedups and CPU scaling | EXP-003, including DV036-F5 at 0166 and the DV-036 CPU gate before 0168 | **OPEN — not discharged by EXP-002** (currently blocked by EXP-002 D1; §8.3) |
| GPU throughput (including OscilloSim's 1.95B claim), Triton/CUDA comparisons, training-step and bridge overhead | EXP-004; GPU/bridge DV-036 gate before 0173; DV-001/DV-003 limitations retained | **OPEN — not discharged by EXP-002** |
| Fresh chimera boundaries, topology/size effects and capacity relation/replication | EXP-005; corrected-SI exception retained | **OPEN — not discharged by EXP-002** |
| CUDA-tagged `y3q49_finite_size_scaling.json` fit ranking and `y3q49_phase_coherence.json` lifetime ranking | EXP-004 backend qualification and EXP-005 scientific replication; their CUDA-derived directions are not substituted with CPU measurements here | **OPEN — not discharged by EXP-002** |
| CLEVR-N/IP accuracy, PT-versus-SA statistical equivalence, ablations, freezing, parameter/FLOP efficiency, trained supercritical regimes, gradient/representation geometry and training curves | EXP-006, with EXP-004 performance dependencies; historical intervals/p-values remain reference-only | **OPEN — not discharged by EXP-002** |
| Daemon p95, MOT/IP evaluation, noise/velocity/occlusion and adversarial robustness | EXP-007, with EXP-006 training dependencies; CPU/DirectML/NPU dispositions retained | **OPEN — not discharged by EXP-002** |
| Linux/macOS/Metal, compiler-free wheel matrix and NPU/new capabilities | EXP-008; amendment #48 suspension and campaign section 5.4 unavailable-hardware rule | **OPEN — not discharged by EXP-002** |

The WP-033 58-script to nine-category traceability matrix (`DOCS/baselines/wp033_benchmark_traceability.md`) remains the full legacy benchmark inventory, and the draft Parity Report's `"CONFIRMATORY — not yet run"` statement for the full benchmark re-run remains in force. Within EXP-002's own registered scope, coverage is complete across all five runs (`0` missing or unverifiable items in H1, H2, H3, or H4).

---

## 8. D1 declaration, correction cycle, and blocking (protocol §4.3; campaign plan §§3.2, 3.3, 10.4)

### 8.1 Declaration

H3 is a track-C1 parity hypothesis (`preregistration.md` §2, §4.3). Its refutation — `18` of `39` `generated_files` differing between PRIN and the frozen reference generator under the approved §5.4 comparison policy (and `34` of `39` under the §11.3 sensitivity policy) — is a C1 conclusion/reproduction reversal under Experimentation Standards §3 and campaign plan §10.4. **The campaign plan §10.4 D1 flag is RAISED** (`"d1_flag": true` in `report-manifest.json` and `summary.json`).

### 8.2 The correction cycle this report opens

Per campaign plan §3.3 and §10.4 item 3, four conditional correction sessions are instantiated in `DOCS/sessions/contingencies/`, to be executed in strict `S1 → S2 → S3 → S4` order after maintainer approval of the S1 scope:

| Stage | Brief | Scope (to be approved by the maintainer before work starts) |
|---|---|---|
| **S1 — Correction implementation** | [`2026-10-14-exp002-d1-s1-correction-implementation.md`](../../sessions/contingencies/2026-10-14-exp002-d1-s1-correction-implementation.md) | First reproduce the H3 refutation with a committed failing regression/parity test; establish the root cause of the 9-figure (`18`-file) divergence between `prin.reporting.figure_generation` and `prinet.utils.figure_generation` (or establish under campaign plan §10.4 item 3, via an EMA-style mathematical audit verified with Z3/SymPy where applicable, if any reference-generator calculation is itself defective); implement the fix with tests in tandem and run the full local and Snyk gates |
| **S2 — Correction audit** | [`2026-10-14-exp002-d1-s2-correction-audit.md`](../../sessions/contingencies/2026-10-14-exp002-d1-s2-correction-audit.md) | Read-only audit of the S1 correction against A1–A10, the EXP-002 evidence, the red→green test transition, and the immutability of EXP-002's record |
| **S3 — Correction remediation** | [`2026-10-14-exp002-d1-s3-correction-remediation.md`](../../sessions/contingencies/2026-10-14-exp002-d1-s3-correction-remediation.md) | Mandatory remediation session: resolve every S2 finding in D1→D4 order and obtain a `CLEAN` delta re-audit |
| **S4 — Correction documentation** | [`2026-10-14-exp002-d1-s4-correction-documentation.md`](../../sessions/contingencies/2026-10-14-exp002-d1-s4-correction-documentation.md) | Issue the next Project State Report (which also formally announces this EXP-002 E5 report and carries the deviation-ledger row), update registers/Parity Report/CHANGELOG, append an erratum pointer here, and authorize **`EXP-002-r1`** |

This E5 session **opens** the correction cycle; it does **not** execute S1, S2, S3, or S4 (campaign plan §12 item 2). **No root cause is claimed by E3, E4, or this E5 report**, and nothing in this record asserts whether PRIN's figure generator or the PRINet 3.0 reference generator is the erroneous side. Under campaign plan §10.4 item 3, declaring the PRINet 3.0 side defective requires an EMA-style mathematical audit claim (Z3/SymPy-verified where applicable), never visual inspection or post-hoc reinterpretation.

### 8.3 What is blocked, and the §3.2 vs §10.4 dependency note

Per campaign plan §3.3 and §10.4 items 2–5:

1. **Session `0163` (this E5 session) completes its reporting work.** Following the session `0158` precedent, `0163` carries status `COMPLETE` in `DOCS/sessions/SESSION_REGISTER.md` and `COMPLETE — report issued; exit gate open on the triggered D1 correction cycle (see the report)` in its session brief, while `SESSION_REGISTER.md`'s line-5 `Current entry point` is set to the open `EXP-002-D1` correction cycle.
2. **Session `0164` (EXP-003 / C2 E1) is `BLOCKED`.** Both `DOCS/sessions/phase-7/0164-exp003-e1-cpu-scaling-and-sweep-performance.md` and row `0164` of `DOCS/sessions/SESSION_REGISTER.md` are set to `BLOCKED` (enforced as a consistent pair by `tools/wp001_baseline.py::validate_session_plan`). Every later campaign session (`0165`–`0194`, covering EXP-003 through EXP-008 and Campaign E6 synthesis) inherits the block in `DOCS/sessions/phase-7/README.md`.
3. **After S4 closes, EXP-002 is re-run as a new experiment record `EXP-002-r1`** with a new pre-registration (E1) and new `RUN-` directories (`benchmarks/results/EXP-002/`). **This `EXP-002` record is never edited**; when `EXP-002-r1` exists, an append-only erratum pointer will be added to §15 while all verdicts, digests, and artefacts here remain unchanged.
4. **Release condition:** No blocked campaign session proceeds until the four contingency sessions (`S1`→`S4`) close **and** `EXP-002-r1`'s E5 report returns a non-reversal verdict verified and accepted by the maintainer (or the maintainer adopts a Project Plan §8.3 amendment accepting a changed conclusion with full justification; campaign plan §10.4 item 5).
5. **Flagged discrepancy between campaign plan §3.2 and §10.4 items 2 & 5 (for maintainer decision):** Campaign plan §3.2's dependency table lists only `EXP-001` as the hard prerequisite for `EXP-003` (`0164`–`0168`) and `EXP-001, EXP-003` for `EXP-004` (`0169`–`0173`), while listing `EXP-002` as a hard prerequisite for `EXP-005`, `EXP-006`, `EXP-007`, `EXP-008`, and `0194`. However, campaign plan §3.3 ("A D1 raised at any E-stage of EXP-*n* blocks the listed successor session and inserts the four conditional correction sessions... before the blocked numbered session resumes"), §10.2 ("Any D1 at any E-stage → Block the successor session... no other campaign work until the correction S4 closes"), and §10.4 items 2 and 5 ("blocks its successor (the next experiment's E1 or 0194)" and "No later campaign session proceeds until step 4's E5 verdict is not a reversal"), as well as `SESSION_REGISTER.md`'s no-reordering rule and the session `0158` precedent, require blocking the immediate numbered successor `0164`. This report strictly follows §3.3 / §10.4 and blocks `0164`. Running `EXP-003` in parallel while `EXP-002-D1` is open would require an explicit Project Plan §8.3 / campaign-plan amendment by the maintainer.

### 8.4 Parity Report erratum and record updates (Experimentation Standards §4; campaign plan §12 item 6)

- **`DOCS/sphinx/parity_report.rst`:** Added a dated `Erratum — 2026-10-14 (EXP-002 E5, H3 REFUTED / D1)` admonition at the top of the Parity Report and qualified the `REFERENCE-HISTORICAL` label row (`"Reproduced byte-comparably by tools/reproduce.py"`) and the `Benchmark re-run comparison` table rows (`paper/artefact_manifest.json` and `tools/reproduce.py, repro.yml`). Those statements previously read as if `tools/reproduce.py`'s output were byte-comparable to the frozen PRINet 3.0 reference generator across all 39 files. They now distinguish what EXP-002 confirmed — **PRIN-versus-PRIN** raw-byte repeatability (`39/39`, H4 `CONFIRMED`), `11/11` LaTeX table parity with the reference generator and archived tables, `5/14` figure parity (`10` files) under the approved normalization, `175/175` API export resolution and `172/172` legacy ownership (`H1 CONFIRMED`), and `62/62` archival conclusion predicates (`H2 CONFIRMED`) — from what EXP-002 refuted: **`9/14` figures (`18/39` files) differ between PRIN and the frozen reference generator (`H3 REFUTED`, D1 raised)**.
- **`CHANGELOG.md`, `DOCS/experiments/README.md`, `DOCS/experiments/EXP-002-api-benchmark-result-and-reproduction-parity/README.md`, and `benchmarks/results/EXP-002/README.md`:** Updated to record the E5 report, the E5 verification/regeneration/reconstruction results, the triggered `EXP-002-D1` correction cycle, and the blocking of session `0164`.

---

## 9. Protocol deviations and procedural disclosures (E1–E5)

Compiled exhaustively from `preregistration.md`, `e2-review.md`, `log.md`, `analysis.md`, and `EVIDENCE/0159`–`EVIDENCE/0163`. Each item is classified as either a **Protocol deviation** (affecting a registered entry condition or protocol-level requirement) or a **Procedural / operational disclosure** (gate execution, tooling, or host-state facts that did not alter any protocol rule). **No hypothesis, prediction, population, denominator, threshold, tolerance, normalization rule, seed pair, or decision rule was changed after the protocol froze at `F = 9a9889d08dcaf2ad0ce31659ed67721b54b114d0`.**

### 9.1 Protocol deviations

1. **PD-E2-1 (Protocol — outcome information published on PR #33 before E2 approval; `preregistration.md` §11.2, `e2-review.md` decision 9).** Two external code-review comments on PR #33 executed or inspected real-input checks before E2 approval: one ran the reference and PRIN publication generators over the 172 inputs and reported per-file H3 comparison counts and all 62 H2 predicates; another noted the C03 `N=128` operand margin. Thus session `0160`'s entry condition ("No result from this experiment has been inspected") did not hold literally at E2 entry. **Disposition (`e2-review.md` decision 9, protocol §11.3 item 1):** (a) H1 and H4 had no published outcomes; (b) H2 remained confirmatory because its 62 predicates, thresholds, and expectations were committed at `7859030` before the reviews and never changed; (c) H3 remained confirmatory under the approved §5.4 policy, paired with a mandatory sensitivity analysis under the pre-exposure (`6314532`) policy. Both policies returned `REFUTED` (`21/39` and `5/39`), so H3's verdict does not depend on the post-exposure amendment. Neither E3, E4, nor E5 used the PR #33 review comments as inputs.
2. **PD-E3-1 (Protocol record format — freeze SHA `F` omitted from line 1 of `log.md` at E3 close; repaired by E4 erratum `7d850ba`).** Campaign plan §12.4 requires the pre-registration freeze SHA to be quoted on line 1 of `log.md`. Session `0161` recorded `F = 9a9889d08dcaf2ad0ce31659ed67721b54b114d0` in `log.md` §1 and §4.1 when the first `RUN-` was created (`2026-10-12T21:27:05Z`), but not on line 1. Session `0162` prepended the required line 1 as an explicit erratum in standalone commit `7d850ba` before any analysis code was committed (`analysis.md` STEP 0).

### 9.2 Procedural and operational disclosures

1. **D-E1-1 (E1 local gate recovery and approved gitleaks checksum exception; session `0159`, `EVIDENCE/0159/`).** During E1 driver validation, an initial full-suite run encountered a Windows `WinError 32` basetemp lock and an interrupted run, preserved in `EVIDENCE/0159/verification/full-gate/`; the final E1 gate passed on `63145325` (`final-6314532/`). Full-history gitleaks exited `1` on a noncredential SHA-256 hex substring in `EVIDENCE/0159/entry-state.json:87`; the maintainer approved the exact fingerprint exception in `.gitleaksignore` (PR33-F34), pinned by `tests/test_wp001_baseline.py`.
2. **D-E1-2 (Pre-E2 multi-review remediation of the DRAFT protocol and driver; session `0159`, commit `0d4278d`).** Seven review sources on PR #33 were adjudicated in `DOCS/audits/PR033-multi-review-audit.md` (38 findings, 0 D1). That pre-E2 round added table CRLF→LF canonicalization, symmetric removal of the four PDF `/Info` keys, font-cache digest capture, and stricter closure/reservation guards (`preregistration.md` §11.1), all reviewed and approved at E2 before any E3 execution.
3. **D-E2-1 (Delegated E2 approval and reviewer independence; session `0160`, `e2-review.md`).** By verbatim directive on `2026-10-12 UTC`, the maintainer delegated the E2 review decisions to the AI pair (`Claude Opus 5.5`). Because `Claude Opus 5.5` had drafted the PR #33 pre-E2 amendments (though not the E1 protocol body or driver, which Devin drafted), two read-only cold reviewers (`Antigravity` `gemini-3.8-flash-high` and `Devin` `swe-2-high`) audited the E2 record and code changes across three rounds (`e2-review.md` §7).
4. **D-E2-2 (E2 `os.walk` access violation, void gate run 4, and forced-nightly variance disposition; session `0160`, `e2-review.md` §§6–7).** During E2 gating, a fast-suite run crashed with Windows access violation `3221225477` inside `os.walk` in the WP-001 repository-inventory test (`G12a`, scanning ~110,800 files including gitignored scratch); `wp001_baseline.py` was narrowed to list git-visible files (~4,500 files) inside a worktree (native crash cause unproven). Gate run 4 was voided because evidence files were packaged into the repository while the gate ran (`G09a`, `G12b` failed two timing-sensitive tests under load); gate run 5 ran on an idle tree and passed completely. Forced nightly `38238913518` on `9a9889d` passed `full-suite` and failed `bench-regression` in two attempts on different smallest-size (~27 µs) benchmarks (`+10.7 %` and `+11.4 %`, each within threshold in the other attempt); dispositioned as runner variance in `e2-review.md` §6.
5. **D-E3-1 (`R` versus `F` single-commit delta; session `0161`, `log.md` §1).** Execution source `R` (`fae24c4393c7a0232e6c8f0a6388b1775aa5fc05`) descends from the E2 approval/freeze commit `F` (`9a9889d08dcaf2ad0ce31659ed67721b54b114d0`) by one commit (`fae24c4`), which recorded the `9a9889d` hosted results and nightly disposition and added 4 evidence filenames to `tests/test_0160_manifest.py`. No product, Rust, driver, protocol, or input file changed between `F` and `R`.
6. **D-E3-2 (Stale installed extension `_prin_core.pyd` and second `.pth` file; session `0161`, `log.md` §2.6).** The installed extension `python/prin/_prin_core.pyd` (`62,792,192 B`, SHA-256 `64ea1a2cf38cdbe43fc029c55e791e244b771b2909360c3890ae6f9224b47349`, written `2026-09-28T23:01:06Z`) predates three Rust commits at `R` (`e4f5b4e` DV-043 guard skip, `199b82a` DV-042 doc attributes, `9a9889d` `cross_band_coupling_cpu` argument validation). It was not rebuilt at E3 (or E5) so the environment stayed identical to the E2 approved-source gate; EXP-002 exercises no Rust numerics. Also `site-packages/prin_core.pth` pointed at `C:\dev\PRIN-r1-amendment\python` while `prin.pth` sorted first and resolved `prin` to `C:\dev\PRIN\python` (enforced by `_check_origin`).
7. **D-E3-3 (E3 per-record validator revisions 1→2→3, PowerShell WSL-bash failure, scratch Snyk finding, and "not examined" clarification; session `0161`, `log.md` §§4.2, 6, 6.1, 10, 12).** The independent E3 validator was updated from revision 1 to revision 2 (catching invalid JSON cleanly in mutation self-tests) and, after cold review, to revision 3 (`validate_run_record_rev3.py`, adding symlink/junction ancestor checks, strict integer/JSON/key-set checks, and 40–49 mutation cases per mode) with zero changes to any record or admissibility result. An initial E3 gate run launched from PowerShell failed 4 `test_wp001_baseline.py` release-workflow tests because `bash` resolved to the Windows WSL launcher (`G09a`, `G12a`); restarting from Git Bash resolved it (`G09`, `G12`). A scratch gate runner (`run_gate.py`) drew 1 Medium Snyk Code finding (`Command Injection` via `subprocess.Popen`, `G14b`) and was not committed; the 10 committed E3 scripts scanned clean (`0` issues, `G14c`). `log.md` §10 clarified that while E3 tools parsed JSON structure and hashed retained bytes, no tool or operator printed, compared across arms, or interpreted any observation value at E3.
8. **D-E4-1 (Phase-A full-suite leg `G13` red on two host-sensitive tests under load — `PD-1` in `analysis.md`; session `0162`).** When `analysis/exp002_e4_analysis.py` and `tests/test_exp002_e4_analysis.py` were gated before any real run (`Phase A`, commit `3731fc2`), the host was under ~58 % CPU load from desktop applications; fast pytest (`G12`, `4,029 passed`), focused pytest (`G09`, `211 passed`, 99 % branch coverage), Ruff, mypy, interrogate, Bandit, Cargo, Snyk Code (`0` issues), and gitleaks all passed, while full pytest (`G13`, `8,634.66 s`) failed 2 host-sensitive tests unrelated to the module (`test_no_gpu_throughput_regression`, ratio `1.60` vs `< 1.30`, DV-032; and `02_clevr_n_binding.ipynb` 900 s cell timeout). On the quieter final candidate (`Phase C`, commit `cad9a8c`) with identical code, the full pytest suite (`G13`) passed **`6,223 passed, 184 skipped, 0 failed`** in `1,486.40 s` (`EVIDENCE/0162/verification/gate-final/`).
9. **D-E4-2 (Void first Phase-C full-suite attempt — `PD-2` in `analysis.md`; session `0162`).** During E4 Phase C, the first full-suite attempt (`G13v-…-VOID-…`) was stopped and voided after a `gh run list` capture was written into `EVIDENCE/0162/` while pytest was running; the file was moved out and `G13`, `R08`, `G18`, and `G17` were rerun from scratch on the unchanged staged tree.
10. **D-E4-3 (Cold-reviewer fabrication in E4 post-run self-audit; session `0162`, `EVIDENCE/0162/verification/delegation/adjudication.md`).** In the E4 Phase-C post-run self-audit, Antigravity (`gemini-3.8-flash-high`) reported `"0 findings"` but cited non-existent file paths (`DOCS/test_and_benchmark_results/EXP-002/analysis.md`), wrong failing test names for `G13`, non-existent §5.3 owner rows, and an incorrect rule that D1 blocks E5 itself. Those errors existed only in the reviewer's output, not in the repository, and underscore the rule that cold-reviewer output must be verified against repository truth before acting.
11. **D-E5-1 (`validate_run_record_rev3.py` check `G1` after E4; session `0163`, `EVIDENCE/0163/verification/preflight/`).** Re-running `validate_run_record_rev3.py` at E5 (`HEAD = cad9a8c`) passes `80/81`, `79/80`, `86/87`, `86/87`, and `86/87` checks; the single check returning `FAIL` on each record is `G1`, which diffs `R` (`fae24c4`) against the working tree over `frozen_paths` (including `tests/`) and flags `['tests/test_exp002_e4_analysis.py']`, the E4 synthetic test file committed in `3731fc2`. By contrast, `git diff --stat fae24c4 HEAD -- python crates tools paper parity Cargo.toml Cargo.lock pyproject.toml benchmarks/campaign benchmarks/_common` shows only `benchmarks/campaign/README.md` (documentation).
12. **D-E5-2 (External red checks — `cargo audit` and hosted `gpu-cuda` unit test; sessions `0161`–`0163`).**
    - **`cargo audit` (local `R08` and hosted `rust` job `audit`):** On `89f21f5`, `73dd6da`, `3731fc2`, and `cad9a8c` (`2026-10-12`..`2026-10-13`, `1,307` advisories in the RustSec database), `cargo audit` exited `1` with **5 vulnerabilities** on `quinn-proto 0.11.16` (`RUSTSEC-2026-0338`, `-0339`, `-0340`, `-0341`, `-0342`, fixed in `>= 0.11.18`), which is in `Cargo.lock` only through `reqwest` → optional `quinn` (`cargo tree --workspace --all-features --target all -e all -i quinn-proto` prints `"nothing to print"`). On `2026-10-14` (`EVIDENCE/0163/verification/gate/R08-cargo-audit.log`, `1,329` advisories in the database), `cargo audit` exits `1` with **9 vulnerabilities**: the same 5 on `quinn-proto 0.11.16` plus **4 new advisories dated `2026-10-14` on `rustls 0.23.45`** (`RUSTSEC-2026-0346` Medium 4.0, `RUSTSEC-2026-0347` Low 2.3, `RUSTSEC-2026-0348` Low 3.7, `RUSTSEC-2026-0349` Low 3.7, all fixed in `>= 0.23.46`, reached through `cubecl-cpu 0.10.0` → `tracel-llvm-bundler` → `reqwest 0.12.28` → `rustls 0.23.45`), alongside the 3 standing allowed warnings (`bincode` DV-017, `paste` DV-008, `chacha20` DV-035). `Cargo.lock` is unchanged since `R`. Not actioned in E3–E5; options presented to the maintainer in §13.3.
    - **Hosted `gpu` run `38447171376` (`gpu-cuda` job `115468476990`) on `cad9a8c`:** `gpu-wgpu` succeeded; `gpu-cuda` failed in step `"Rust kernel-equivalence tests (CUDA)"` on 1 of 447 unit tests in `prin-train`: `flops::tests::measure_wall_time_calls_warmup_and_runs_exact_counts` (`assertion failed: stats.mean_ms <= stats.max_ms` at `crates/prin-train/src/flops.rs:400:9`). `crates/prin-train/src/flops.rs` is unchanged since WP-031, and the identical code passed `gpu-cuda` on `3731fc2` (run `38428378008`). A plausible (unproven) mechanism is IEEE-754 float64 rounding where `mean_ms = sum / n` exceeds `max_ms` by 1 ulp when samples are equal or nearly equal. Recorded verbatim, not fixed in E5 (§13.3).

---

## 10. Threats to validity

1. **Stale installed extension (`python/prin/_prin_core.pyd`).** The compiled extension in `.venv` / `python/prin/_prin_core.pyd` (SHA-256 `64ea1a2c…f47349`, built `2026-09-28T23:01:06Z`) predates three Rust commits at `R` (`e4f5b4e`, `199b82a`, `9a9889d`) and is not hashed by the driver (`log.md` §2.6). Because H1 only inspects symbol presence, callability, scalar type, and ownership rows without invoking numerical routines, and H2–H4 read and render stored JSON artefacts without calling Rust numerics, no registered EXP-002 observation exercises the three post-`2026-09-28` Rust commits.
2. **Execution source `R` versus protocol freeze commit `F`.** `R` (`fae24c4`) differs from `F` (`9a9889d`) by one documentation/evidence commit whose only Python edit added four filenames to `tests/test_0160_manifest.py` (`log.md` §1).
3. **Pre-E2 outcome exposure (protocol §11.2, `e2-review.md` decision 9).** Outcome information for H2 and H3 was posted on PR #33 before E2 approval. H2's predicates and thresholds were fixed at `7859030` before the exposure, and H3 is `REFUTED` under both the approved policy (`21/39`) and the pre-exposure `6314532` sensitivity policy (`5/39`), so the post-exposure amendment did not alter any verdict.
4. **Reference-arm raw PDF reconstruction limitation (protocol §8.2, §11.3 item 2).** While Step 1 verified `39/39` retained files in all three publication runs against their manifested raw digests and Step 3 reconstructed `39/39` PRIN-arm files raw-identically, reconstructing the `reference` arm at E5 produced `25/39` raw-identical files (`14/14` PNGs, `11/11` tables) and `0/14` raw-identical PDFs (`39/39` normalized-identical and `39/39` sensitivity-identical) because the frozen `prinet` 3.0.0 PDF writer does not pass a fixed `CreationDate` to Matplotlib. Retaining the original generated publication roots under E2 decision 8 ensured that primary raw-byte verification at E5 did not depend on re-running an unpinned timestamp writer.
5. **Clean-checkout reconstruction bound to the maintainer checkout (`C:\dev\PRIN`).** As noted in §6.3, reconstructing the publication files requires the compiled `_prin_core.pyd` extension and the `.venv` editable `.pth` links, which reside in `C:\dev\PRIN` and are absent from a bare `git worktree`. By contrast, the stdlib-only E4 analysis module was verified in an isolated detached worktree outside `C:\dev\PRIN` (§6.2).
6. **Single Windows host (`H1`) and renderer stack.** All five E3 legs and the E5 reconstruction executed on a single Windows 11 (`10.0.26300`) workstation with Python `3.14.0`, Matplotlib `3.11.1`, NumPy `2.5.1`, Pillow `12.3.0`, and FreeType `2.14.3` (`Agg` backend). Under Plan amendment #48, Linux and macOS remain suspended and untested for campaign claims (hosted `repro.yml` runs PRIN's `tools/reproduce.py` alone, not the cross-arm H3 comparison).
7. **Scope boundaries of H1 and H2.** H1 establishes namespace and Migration Guide ownership completeness only, not behavioural or numerical parity of the 175 symbols. H2 evaluates 62 archival predicates on frozen JSON inputs (with `C02`'s 42 rows testing archival self-consistency against stored `chimera_detected`, not an independent external prediction) and does not discharge any fresh benchmark or replication claim in §7.
8. **Driver closure gaps identified at E3.** Cold review at E3 noted that `exp002_driver.py` checks symlink ancestors with `is_symlink()` (not Windows junction reparse tags), parses JSON without a duplicate-key hook, and checks subset rather than exact key sets on some nested objects (`log.md` §§10, 12). These are mitigated for EXP-002's records because `validate_run_record_rev3.py`, the E3 reparse-point scan, the E4 analysis module (`exp002_e4_analysis.py`), and the E5 independent recount enforce reparse-tag rejection, duplicate-key rejection, and exact key sets across all five records.
9. **Cold-reviewer model-family overlap and CLI availability at E5.** The E5 author (`Devin`, powered by `Gemini 4 Argon High`) and the `agy` (`gemini-3.8-flash-high`) cold reviewer belong to the Gemini model family, while the standalone `devin` CLI (`swe-2-high`) returned `Error: Not logged in. Run devin.exe auth login to authenticate.` (exit `1`) and `agy --model gpt-oss-120b-medium` returned HTTP `503 UNAVAILABLE` on its direct-review invocation. Every quantitative figure, digest, byte size, and link across the E5 documents was verified by deterministic Python scripts (`independent-recount.txt`, `programmatic-self-audit.txt`), and the maintainer is asked whether to run an additional non-Gemini reviewer.

---

## 11. Exploratory

Everything in this section is **exploratory** (Experimentation Standards §1.1, §2 E4/E5; campaign plan §12 item 5): it was not pre-registered as a decision rule, gates nothing, alters no confirmatory verdict, and **asserts no root cause** for any H3 difference. It provides a purely descriptive inventory of the manifested byte sizes from `reproduction-comparisons.csv` (`424f292d…`) to orient correction session S1.

1. **The 9 figure stems (`18` files) that differ under both H3 policies.** Whenever a figure differs under the approved policy, both its `.pdf` and its `.png` differ, and its normalized byte sizes in the two arms also differ (except where noted below):

| Figure stem | Format | Reference raw (B) | PRIN raw (B) | Reference normalized (B) | PRIN normalized (B) | Normalized Δ (PRIN − Ref, B) |
|---|---|---:|---:|---:|---:|---:|
| `fig5_mot_occlusion_comparison` | `pdf` / `png` | `17,363` / `66,067` | `17,359` / `66,032` | `17,222` / `65,976` | `17,253` / `65,986` | `+31` / `+10` |
| `fig7_ablation_results` | `pdf` / `png` | `17,260` / `88,316` | `17,223` / `88,155` | `17,119` / `88,225` | `17,117` / `88,109` | `−2` / `−116` |
| `fig8_parameter_efficiency` | `pdf` / `png` | `19,837` / `74,727` | `19,790` / `74,815` | `19,696` / `74,636` | `19,684` / `74,769` | `−12` / `+133` |
| `fig9_training_curves` | `pdf` / `png` | `18,268` / `96,422` | `18,236` / `96,317` | `18,127` / `96,331` | `18,130` / `96,271` | `+3` / `−60` |
| `fig10_statistical_summary` | `pdf` / `png` | `25,904` / `45,912` | `25,743` / `44,196` | `25,763` / `45,821` | `25,637` / `44,150` | `−126` / `−1,671` |
| `fig11_flops_scaling` | `pdf` / `png` | `17,786` / `44,362` | `19,616` / `43,947` | `17,645` / `44,271` | `19,510` / `43,901` | `+1,865` / `−370` |
| `fig12_supercritical_regime` | `pdf` / `png` | `23,192` / `70,978` | `22,050` / `71,479` | `23,051` / `70,887` | `21,944` / `71,433` | `−1,107` / `+546` |
| `fig14_gradient_flow` | `pdf` / `png` | `19,681` / `84,798` | `19,597` / `84,199` | `19,540` / `84,707` | `19,491` / `84,153` | `−49` / `−554` |
| `fig15_noise_velocity` | `pdf` / `png` | `23,725` / `179,622` | `24,574` / `180,139` | `23,584` / `179,531` | `24,468` / `180,093` | `+884` / `+562` |

2. **The 5 figure stems (`10` files) that match under the approved policy.** For `fig2_clevr_n_capacity`, `fig3_chimera_metrics`, `fig4_chimera_k_alpha_heatmap`, `fig6_oscillosim_scaling`, and `fig13_representation_geometry`, the normalized `.pdf` and `.png` byte sizes and SHA-256 digests are identical between the reference and PRIN arms (`16,403` / `55,395 B`; `16,091` / `49,122 B`; `21,885` / `83,590 B`; `21,453` / `71,718 B`; and `23,441` / `200,881 B`). In each of those 5 figures, the raw `.pdf` is `35` bytes larger in the reference arm than in the PRIN arm and the raw `.png` is `45` bytes larger in the reference arm (reflecting the metadata differences stripped by the registered normalizers).
3. **The 11 `.tex` tables.** In the PRIN arm, all 11 tables have `raw_bytes == normalized_bytes == archived_bytes` and `raw_sha256 == normalized_sha256 == archived_sha256` (`410` to `998 B`). In the reference arm, each table's `raw_bytes` exceeds `normalized_bytes` by `13` to `25` bytes (the exact number of lines in that table, from Windows text-mode CRLF translation), and `normalized_sha256` equals PRIN's and the archived table's digest on all `11/11` tables.

---

## 12. Complete artefact index (campaign plan §7.4 item 5)

### 12.1 Input runs — tracked raw records under `benchmarks/results/EXP-002/`

All 15 files across the 5 `RUN-` directories are tracked byte-exact (`.gitattributes` `benchmarks/results/** -text whitespace=-trailing-space`):

| Run ID (`benchmarks/results/EXP-002/<Run ID>/`) | Mode / Hypotheses | File | Bytes | SHA-256 |
|---|---|---|---:|---|
| `RUN-20261012T212705Z-fae24c4-api-cpu` | `api` (`H1`) | `api.json` | `97,194` | `b76aedab424582dec72ede165c6a136e62c802b395519cba56975fa75f0fade9` |
| `RUN-20261012T212705Z-fae24c4-api-cpu` | `api` (`H1`) | `campaign-metadata.json` | `215` | `d51f9c7b4ae1f9b32e20cf211a55bfc416470eae1e332c823df645ead8b5e355` |
| `RUN-20261012T212705Z-fae24c4-api-cpu` | `api` (`H1`) | `manifest.json` | `554` | `d4eee92905addee67c210192a7a97a35b4e52e5f623f1fe34b04fcae9f8eaa90` |
| `RUN-20261012T213054Z-fae24c4-conclusions-cpu` | `conclusions` (`H2`) | `conclusions.json` | `59,206` | `2d1cdc5fa76b247da1b8544606708b6fa0ffe9afaaf274604bc4c1115e9bed84` |
| `RUN-20261012T213054Z-fae24c4-conclusions-cpu` | `conclusions` (`H2`) | `campaign-metadata.json` | `239` | `1f59f1e078fce9154703feb93499da62f8d3c183406de9e3ebfded3cc2a04756` |
| `RUN-20261012T213054Z-fae24c4-conclusions-cpu` | `conclusions` (`H2`) | `manifest.json` | `562` | `d5247c24728c26d21bc4677036091ac4665888a526b9825df231ff5ef2439bd9` |
| `RUN-20261012T213821Z-fae24c4-reproduction-reference-cpu` | `reference` (`H3`) | `reproduction.json` | `59,584` | `70f9677c7523c2decf3dc0b9e3e1ba8763ee56838ff63deca93587b42c89e7e3` |
| `RUN-20261012T213821Z-fae24c4-reproduction-reference-cpu` | `reference` (`H3`) | `campaign-metadata.json` | `249` | `722fc141089fc0ece7fb043cb67b0bba574beca85fc3b45c5fceacb8b60b25c2` |
| `RUN-20261012T213821Z-fae24c4-reproduction-reference-cpu` | `reference` (`H3`) | `manifest.json` | `563` | `f5410f4f0d5d3f6835575b377e211d6e704b0759f0457df4751a6ad0abee9d6d` |
| `RUN-20261012T213936Z-fae24c4-reproduction-prin-cpu` | `prin` (`H3`, `H4`) | `reproduction.json` | `59,572` | `776a926df8edb333e38d61e9fc4ba2966385df56bcfc3d9eda6540c7c47b590e` |
| `RUN-20261012T213936Z-fae24c4-reproduction-prin-cpu` | `prin` (`H3`, `H4`) | `campaign-metadata.json` | `252` | `6316a9e03f53cc966d70f8c83d1d70f7962857edc09f7dc8b4c6d4fe507d0e7e` |
| `RUN-20261012T213936Z-fae24c4-reproduction-prin-cpu` | `prin` (`H3`, `H4`) | `manifest.json` | `563` | `0213ac284abf55b04a6cd5641abecb4b25d00be1b8e488e562c9b6cb399e18c8` |
| `RUN-20261012T214040Z-fae24c4-seedrep0-prin-cpu` | `repeatability` (`H4`) | `reproduction.json` | `59,568` | `ec615eb48008bcc112ad73a10fc6ea42ddf5619ecb33b87e880a1e7977084127` |
| `RUN-20261012T214040Z-fae24c4-seedrep0-prin-cpu` | `repeatability` (`H4`) | `campaign-metadata.json` | `244` | `77cf576fb454cd32b9247e1392112d1a67c0a927ab4707c45393e091554a25ec` |
| `RUN-20261012T214040Z-fae24c4-seedrep0-prin-cpu` | `repeatability` (`H4`) | `manifest.json` | `563` | `5722cb93ac87c4bf448ee76b53721c0d030bc0b0d3a465db7ab6db403db78388` |

### 12.2 Generated E4 analysis outputs (gitignored under `DOCS/test_and_benchmark_results/EXP-002/analysis/`) and committed `report-manifest.json`

| Path | Bytes | SHA-256 |
|---|---:|---|
| `DOCS/test_and_benchmark_results/EXP-002/analysis/summary.json` | `13,407` | `2dabdea13d6d963caed4adb35edd2b66deaedc70929afcfb765003b7c3303e13` |
| `DOCS/test_and_benchmark_results/EXP-002/analysis/api-mapping.csv` | `18,375` | `7f2cfd76f62ccecae89f2e52bbf67c39ac067b82b7d4fef6ec499bb2c93c5e19` |
| `DOCS/test_and_benchmark_results/EXP-002/analysis/conclusion-comparisons.csv` | `10,872` | `0c01c59c8e1f32ea3ad173dddde117ad9a94b187289328da760e1c906e0bba85` |
| `DOCS/test_and_benchmark_results/EXP-002/analysis/reproduction-comparisons.csv` | `31,277` | `424f292d7699ab7e7d92ce089201a7d501acd7deae02aff50d393ac06870e0d1` |
| `DOCS/test_and_benchmark_results/EXP-002/analysis/error-distributions.json` | `4,345` | `e28f3e4fad0a5a7ba3dedc686900f7b808815378035d6dab6a402a2067025d9d` |
| `DOCS/test_and_benchmark_results/EXP-002/analysis/expected-vs-observed.md` | `2,397` | `97ecd3ab53bdbee2cf22e22e49866843544f70b3803213560978b4185af71789` |
| `DOCS/test_and_benchmark_results/EXP-002/analysis/coverage-and-deferrals.md` | `4,623` | `ff14a9f8592576f895a559b05d8b0848039d6efefc2b467d4bab97c3f94a18f9` |
| [`DOCS/experiments/EXP-002-api-benchmark-result-and-reproduction-parity/report-manifest.json`](report-manifest.json) (committed) | `18,848` | `6b15dcc112513cdce9cb2d923208f93d3616898225efed545706c56526e68781` |

### 12.3 Retained untracked publication and input roots (`DOCS/test_and_benchmark_results/EXP-002/<run-id>/`)

Retained unmodified on the maintainer host per E2 decision 8 (`preregistration.md` §11.3 item 2). The 39 individual PRIN-arm file paths, byte sizes, and raw SHA-256 digests are indexed in [`report-manifest.json`](report-manifest.json) (`publication_outputs.files`, lines 188–384) and in `reproduction-comparisons.csv`:

| Run ID | Retained `inputs/` snapshot | Retained `publication/` files | Publication listing digest (`e2-review.md` §8 formula) |
|---|---|---|---|
| `RUN-20261012T212705Z-fae24c4-api-cpu` | — | — | n/a |
| `RUN-20261012T213054Z-fae24c4-conclusions-cpu` | `172` JSON files (`16,047,018 B`) | — | n/a |
| `RUN-20261012T213821Z-fae24c4-reproduction-reference-cpu` | `172` JSON files (`16,047,018 B`) | `39` files (`1,502,048 B`) | `d674de7d4b5830c9abf525fcc484a5ebc01e3620ca38b63badd037e289487323` |
| `RUN-20261012T213936Z-fae24c4-reproduction-prin-cpu` | `172` JSON files (`16,047,018 B`) | `39` files (`1,500,705 B`) | `c1ca4ada167c50a28db2dfe4365d004cdb3621903f43e38cc6de75c2e4904669` |
| `RUN-20261012T214040Z-fae24c4-seedrep0-prin-cpu` | `172` JSON files (`16,047,018 B`) | `39` files (`1,500,705 B`) | `c1ca4ada167c50a28db2dfe4365d004cdb3621903f43e38cc6de75c2e4904669` |

### 12.4 Record, driver, test, contingency, and evidence artefacts

| Artefact | Stage / Session | Description |
|---|---|---|
| [`preregistration.md`](preregistration.md) | E1 (`0159`) / E2 (`0160`) | Frozen protocol (`F` = `9a9889d08dcaf2ad0ce31659ed67721b54b114d0`, SHA-256 `0f3073dd…bc8c8b`) |
| [`e1-handoff.md`](e1-handoff.md), [`e2-review-packet.md`](e2-review-packet.md) | E1 (`0159`) | E1 handoff and historical E2 decision packet |
| [`DOCS/audits/PR033-multi-review-audit.md`](../../audits/PR033-multi-review-audit.md) | E1 (`0159`) | Adjudication of the seven pre-E2 PR #33 reviews (`PR33-F1`..`PR33-F38`) |
| [`e2-review.md`](e2-review.md) | E2 (`0160`) | E2 static re-derivation, Lean 4 / Z3 proofs, decisions 1–11, nightly disposition, E3 checklist |
| [`benchmarks/campaign/exp002_driver.py`](../../../benchmarks/campaign/exp002_driver.py) + [`tests/test_exp002_driver.py`](../../../tests/test_exp002_driver.py) | E1/E2 (`0159`–`0160`) | Committed collection driver and synthetic regression tests |
| [`log.md`](log.md) | E3 (`0161`) + erratum (`0162`) | Append-only E3 execution log (`7d850ba` prepended line 1 freeze SHA) |
| [`analysis/exp002_e4_analysis.py`](analysis/exp002_e4_analysis.py), [`analysis/README.md`](analysis/README.md) + [`tests/test_exp002_e4_analysis.py`](../../../tests/test_exp002_e4_analysis.py) | E4 (`0162`) | Frozen E4 analysis module (`3731fc2`, SHA-256 `7a400aa6…6ee4e4`) and 176 synthetic tests |
| [`analysis.md`](analysis.md), [`report-manifest.json`](report-manifest.json) | E4 (`0162`) | E4 analysis record and SHA-256 manifest (`6b15dcc1…68781`) |
| **`report.md` (this file)** | E5 (`0163`) | E5 report |
| [`2026-10-14-exp002-d1-s1..s4`](../../sessions/contingencies/README.md) | E5 (`0163`) | Four conditional correction session briefs opened by this report (§8.2) |
| [`EVIDENCE/0159/`](../../../EVIDENCE/0159/README.md), [`EVIDENCE/0160/`](../../../EVIDENCE/0160/README.md), [`EVIDENCE/0161/`](../../../EVIDENCE/0161/README.md), [`EVIDENCE/0162/`](../../../EVIDENCE/0162/README.md), [`EVIDENCE/0163/`](../../../EVIDENCE/0163/README.md) | E1–E5 (`0159`–`0163`) | Byte-exact verification evidence bundles, each with `verification/SHA256SUMS.txt` |

### 12.5 Commits on branch `campaign/0159-exp002-e1` (E1–E4, base `da53ea11a3f38cd0d5c27c40bbefbeaf6d6dbf53`)

| Session | Commit | Author date (`-0300`) | Subject |
|---:|---|---|---|
| `0159` (E1) | `85b779297be0642f5c64853c1590ef341e7ff77e` | `2026-10-11 08:17:31` | `chore(0159): establish byte-preserving verification evidence attributes` |
| `0159` (E1) | `78590305e1c0a78d92153ef2a55a9e76aeb7af79` | `2026-10-11 09:30:20` | `docs(0159): preregister EXP-002 E1 and adopt validation timeout amendment 49` |
| `0159` (E1) | `63145325c01fd837fd55e2796ea0fa34aa7eb234` | `2026-10-11 11:44:13` | `fix(0159): validate publication containers and preserve recovery evidence` |
| `0159` (E1) | `78d360029028c0571bdc272bef39e901c85f09da` | `2026-10-11 13:39:19` | `docs(0159): record recovered local gates and prepare E2 review packet` |
| `0159` (E1) | `0d4278d484e1fb5e55cd510991f6c8d4bf4374ae` | `2026-10-11 20:23:55` | `fix(0159): remediate the PR #33 review findings PR33-F1..PR33-F38` |
| `0160` (E2) | `ed993e97acbccbd6122a9b4fe65dfb56eea62a0d` | `2026-10-12 01:18:58` | `chore(0160): byte-preserve EXP-002 E2 review evidence` |
| `0160` (E2) | `9a9889d08dcaf2ad0ce31659ed67721b54b114d0` (`F`) | `2026-10-12 07:17:24` | `docs(0160): EXP-002 E2 review and approval; fix hosted failures and flaky fixtures` |
| `0160` (E2) | `fae24c4393c7a0232e6c8f0a6388b1775aa5fc05` (`R`) | `2026-10-12 11:07:06` | `docs(0160): record hosted results for 9a9889d and disposition the nightly` |
| `0161` (E3) | `92cf6963120358646ede43094742ac423a5262e9` | `2026-10-12 18:50:16` | `chore(0161): byte-preserve EXP-002 E3 execution evidence` |
| `0161` (E3) | `89f21f5b42c195e46d172808fb39941c47451de8` | `2026-10-12 20:33:25` | `docs(0161): EXP-002 E3 execution - five registered runs, no verdict computed` |
| `0161` (E3) | `e425971389a85d74da6161fa5f2a9ba92d104232` | `2026-10-12 21:33:38` | `docs(0161): E3 cold-review record, validator rev3, hosted results, cargo-audit finding` |
| `0161` (E3) | `73dd6dafc6a4f2fad88f06be04dba6fc7011e920` | `2026-10-12 21:46:28` | `docs(0161): E3 cold-review round 2 - adjudication, reparse-point scan, log section 12` |
| `0162` (E4) | `7d850babf173c9987fbb34d80af9e4be8238b304` | `2026-10-13 07:20:14` | `docs(0162): erratum - quote the EXP-002 freeze SHA on log.md line 1` |
| `0162` (E4) | `3731fc2590cf86bdb657fce25e4917d26567b23a` | `2026-10-13 13:10:42` | `feat(0162): EXP-002 E4 registered analysis module and synthetic tests` |
| `0162` (E4) | `42f0eb3ea0b580e7c41a8fa9d7ae9679166df2ca` | `2026-10-13 13:16:36` | `chore(0162): byte-preserve EXP-002 E4 analysis evidence` |
| `0162` (E4) | `cad9a8c502bfd38800594336663f621990bb8b22` | `2026-10-13 15:28:55` | `docs(0162): EXP-002 E4 analysis - H3 refuted, D1 flag raised` |

(Session `0163` adds the `.gitattributes` commit for `EVIDENCE/0163/**` and the commit carrying this report; a commit cannot record its own SHA.)

---

## 13. Pull request, hosted check record (campaign plan §12 item 3), and open items for maintainer decision

### 13.1 Pull request and tested head SHA

- **Pull request:** PR #33 (`campaign/0159-exp002-e1` → `main`, base `da53ea11a3f38cd0d5c27c40bbefbeaf6d6dbf53`), carrying the full EXP-002 E1–E5 range. State at E5 pre-flight (`2026-10-14T19:01:34Z`): `OPEN`, `MERGEABLE`, no new comments since `2026-10-11T23:25:34Z` and no new reviews since `2026-10-11T17:48:59Z`.
- **Authoritative gate:** Under Plan amendment #48, the Windows local gate on the maintainer's workstation is the authoritative merge gate; under Plan amendment #50, the seven check workflows (`rust`, `python`, `parity`, `repro`, `snyk`, `gpu`, `nightly`) are enabled for the EXP-002 window (`0159`–`0163`) as additional evidence only.
- **Tested PR head SHA recorded here (campaign plan §12 item 3):** **`cad9a8c502bfd38800594336663f621990bb8b22`** (`cad9a8c`, `"docs(0162): EXP-002 E4 analysis - H3 refuted, D1 flag raised"`), the head of `campaign/0159-exp002-e1` before this E5 report commit. **This is a tested head SHA, not a merge SHA; the merge SHA does not exist and is not claimed, and a commit cannot contain the hosted check results of itself.**

### 13.2 Hosted check results for tested head `cad9a8c502bfd38800594336663f621990bb8b22` (additional evidence only)

Workflow runs (`gh run list -R Symbo-gif/PRIN --commit cad9a8c502bfd38800594336663f621990bb8b22`, captured verbatim in `EVIDENCE/0163/verification/preflight/hosted-cad9a8c.json`):

| Run ID | Workflow | Event | Attempt | Status | Conclusion | Started (UTC, `2026-10-13`) | Updated (UTC, `2026-10-13`) | Notes |
|---:|---|---|---:|---|---|---|---|---|
| `38447159835` | `snyk` | `push` | 1 | `completed` | `success` | `18:29:26Z` | `18:30:18Z` | `Snyk Code` and `Secret Scan` green |
| `38447171329` | `snyk` | `pull_request` | 1 | `completed` | `success` | `18:29:31Z` | `18:30:15Z` | `Snyk Code` and `Secret Scan` green |
| `38447171265` | `repro` | `pull_request` | 1 | `completed` | `success` | `18:29:31Z` | `18:34:38Z` | `reproduce` green |
| `38447171241` | `parity` | `pull_request` | 1 | `completed` | `success` | `18:29:31Z` | `18:35:06Z` | `detect_corpus` and `parity` green |
| `38447171462` | `python` | `pull_request` | 1 | `completed` | `success` | `18:29:31Z` | `18:43:37Z` | All 10 jobs (`lint`, `governance`, `security`, `docs`, and 6 `test` legs on `ubuntu-latest`/`windows-latest` × Python `3.11`/`3.12`/`3.13`) green |
| `38447171301` | `rust` | `pull_request` | 1 | `completed` | **`failure`** | `18:29:31Z` | `19:10:02Z` | 9 of 10 jobs (`fmt`, `clippy`, `clippy-strict`, `test-strict`, `docs` incl. feature-gated `prin-sim` `gpu` rustdoc step, `bench-smoke`, and `test` on `ubuntu-latest`, `macos-latest`, `windows-latest`) `success`; **`audit` job `115468476429` `failure`** (`quinn-proto 0.11.16` advisories; §9.2 D-E5-2) |
| `38447171376` | `gpu` | `pull_request` | 1 | `completed` | **`failure`** | `18:29:31Z` | `19:21:32Z` | `gpu-wgpu` (`115468477285`) `success`; **`gpu-cuda` (`115468476990`) `failure`** on 1 unit test `flops::tests::measure_wall_time_calls_warmup_and_runs_exact_counts` (`mean_ms <= max_ms` at `crates/prin-train/src/flops.rs:400:9`; §9.2 D-E5-2) |

Complete `statusCheckRollup` on PR #33 at `cad9a8c502bfd38800594336663f621990bb8b22` (`gh pr view 33 --json statusCheckRollup`, captured verbatim in `EVIDENCE/0163/verification/preflight/pr33-statusCheckRollup-cad9a8c.json`):
- **26 check runs / contexts `SUCCESS`:** `lint`, `governance`, `security`, `docs` (`python`), `test (ubuntu-latest, 3.11)`, `test (ubuntu-latest, 3.12)`, `test (ubuntu-latest, 3.13)`, `test (windows-latest, 3.11)`, `test (windows-latest, 3.12)`, `test (windows-latest, 3.13)`, `fmt`, `clippy`, `clippy-strict`, `test-strict`, `docs` (`rust`), `bench-smoke`, `test (ubuntu-latest, ubuntu-latest)`, `test (macos-latest, macos-latest)`, `test (windows-latest, windows-latest)`, `detect_corpus`, `parity`, `reproduce`, `Snyk Code` (`pull_request`), `Snyk Code` (`push`), `Secret Scan` (`pull_request`), `Secret Scan` (`push`), `gpu-wgpu`, plus status context `CodeRabbit` (`SUCCESS`).
- **2 check runs `FAILURE`:** `audit` (`rust` run `38447171301`, job `115468476429`) and `gpu-cuda` (`gpu` run `38447171376`, job `115468476990`).
- **1 check run `SKIPPED`:** `Sourcery review` (diff exceeds 150,000-character limit).

For reference, earlier hosted runs during the EXP-002 window:
- `0d4278d` (`0159`): forced nightly `38184198596` (`full-suite` 14 min and `bench-regression` 87 min both `success`); `python` `lint` failed on missing `numpy` and `rust` `clippy` failed on Rust 1.99 `single_element_loop` (both fixed in `9a9889d`).
- `9a9889d` (`0160`, `F`): all 6 PR workflows `success`; forced nightly `38238913518` passed `full-suite` and failed `bench-regression` in attempts 1 and 2 on different ~27 µs smallest-size benchmarks (dispositioned as runner variance in `e2-review.md` §6).
- `fae24c4` (`0160`, `R`): all 7 runs (`38260606024`, `38260614029`, `38260614031`, `38260614034`, `38260614092`, `38260614099`, `38260614101`) `success`.
- `89f21f5` (`0161`): `snyk` push/PR (`38322795453`, `38322799666`), `parity` (`38322799631`), `repro` (`38322799707`), `python` (`38322799742`), `gpu` (`38322799687`) `success`; `rust` (`38322799650`) failed in `audit` only.
- `73dd6da` (`0161`): `snyk` push/PR (`38328901048`, `38328905487`), `parity` (`38328905477`), `repro` (`38328905482`), `python` (`38328905492`), `gpu` (`38328905496`) `success`; `rust` (`38328905471`) failed in `audit` only.
- `3731fc2` (`0162` Phase A): `snyk` push/PR (`38428373413`, `38428378082`), `parity` (`38428377998`), `repro` (`38428378382`), `python` (`38428378236`), `gpu` (`38428378008`) `success`; `rust` (`38428378271`) failed in `audit` only.

### 13.3 Open items not actioned in E5 (options for maintainer decision)

Per E5 scope rules, session `0163` does not modify code, lockfiles, dependencies, workflows, or the DV register. Each open item is described below with concrete options for the maintainer:

1. **`cargo audit` red (`RUSTSEC-2026-0338`..`0342` on `quinn-proto 0.11.16` and `RUSTSEC-2026-0346`..`0349` on `rustls 0.23.45`):**
   - *Facts:* On `cad9a8c` (`2026-10-13`), 5 advisories on `quinn-proto 0.11.16` (fixed in `>= 0.11.18`; unactivated optional transitive entry in `Cargo.lock`, `cargo tree --workspace --all-features --target all -e all -i quinn-proto` empty). On `2026-10-14` (`R08-cargo-audit.log`), 4 additional advisories published `2026-10-14` on `rustls 0.23.45` (`RUSTSEC-2026-0346`..`0349`, fixed in `>= 0.23.46`, reached via `cubecl-cpu` → `tracel-llvm-bundler` → `reqwest`), totaling **9 vulnerabilities** (plus 3 allowed warnings). `Cargo.lock` is unchanged since `R`.
   - *Options:* **(a)** Authorize a governed lockfile-only update (`cargo update -p quinn-proto -p rustls` to `quinn-proto >= 0.11.18` and `rustls >= 0.23.46`) during the S1 correction session (or a dedicated hotfix), validated with `cargo audit`, Snyk Open Source, and the full local gate; or **(b)** authorize a dated Deferred Validation register disposition (in the DV-008/DV-017/DV-035 third-party class) for any non-reachable item while upgrading `rustls`.
2. **Hosted `gpu-cuda` unit-test failure (`prin-train` `flops::tests::measure_wall_time_calls_warmup_and_runs_exact_counts` at `crates/prin-train/src/flops.rs:400:9`):**
   - *Facts:* Failed once in `gpu` run `38447171376` (`cad9a8c`) on `assert!(stats.mean_ms <= stats.max_ms)`; passed in `gpu` run `38428378008` (`3731fc2`) and earlier runs on identical `flops.rs` code (unchanged since WP-031). Plausible mechanism (unproven): `mean_ms = sum / n` rounding 1 ulp above `max_ms` in IEEE-754 float64 when measured durations are equal or near-equal.
   - *Options:* **(a)** Open a DV register row and/or fold a root-cause reproduction + fix (`mean_ms` clamp or exact-arithmetic test) into a governed hotfix or S1 scope; or **(b)** rerun the `gpu` job to check reproducibility while tracking the assertion sensitivity in a new DV row.
3. **Stale installed `python/prin/_prin_core.pyd` (`2026-09-28`) and stale `site-packages/prin_core.pth`:**
   - *Facts:* `_prin_core.pyd` predates three Rust commits (`e4f5b4e`, `199b82a`, `9a9889d`), and `prin_core.pth` points at `C:\dev\PRIN-r1-amendment\python` (though `prin.pth` sorts first and resolves `prin` to `C:\dev\PRIN\python`).
   - *Options:* **(a)** Rebuild `_prin_core.pyd` with `maturin develop --release`, remove the stale `prin_core.pth`, and record `_prin_core.pyd`'s SHA-256 in the driver before `EXP-002-r1` E3; or **(b)** defer until `EXP-002-D1` S1 scope is approved.
4. **Retained generated roots (`DOCS/test_and_benchmark_results/EXP-002/RUN-*/`):**
   - *Recommendation:* Keep the retained untracked roots (`~84 MB`) on disk until `EXP-002-D1` S1 completes, even after E5 report acceptance, so S1 can compare the exact E3-rendered PDFs and PNGs directly against its failing-test reproduction.
5. **Plan amendment #50 end-of-window workflow disabling:**
   - *Rule:* Amendment #50 states that when EXP-002 E5 (session `0163`) closes, or earlier on maintainer instruction, the seven check workflows (`rust`, `python`, `parity`, `repro`, `snyk`, `gpu`, `nightly`) are disabled again with `gh workflow disable` and that disabling is recorded. They have **not** been disabled by this commit so the E5 push's hosted runs can execute and be recorded first; awaiting maintainer confirmation that E5 is closed and whether to disable them now or keep them enabled for the `EXP-002-D1` correction cycle.
6. **Standing carried items (unchanged, not actioned here):** `DV-033` (per-change Python coverage on the Windows host), `DV-034` (single self-hosted GPU runner SPOF), `DV-036` reference-host re-baseline gates before `0168` (CPU) and `0173` (GPU/bridge), `DV036-F5` at `0166`, `EXP-004+` hardware gates (`DV-001`, `DV-006` VitisAI half, Metal), `PSR-040` `S2-F3`/`S2-F4`, `PR32-F13`/`OBS-1`/`OBS-2`, and the full amendment-#48 lift (note: the new `rust.yml` feature-gated `prin-sim` `gpu` rustdoc step added in `PR32-F9` executed and succeeded on hosted CI during amendment #50's window, e.g., run `38447171301` job `115468476594` step 6, though amendment #50 is not the amendment #48 lift).

---

## 14. Approvals, maintainer verification, and open obligations

| Obligation | Owner | Status |
|---|---|---|
| Step 1: Retained publication and input bytes verified against manifested digests | AI pair (`Devin`, `Gemini 4 Argon High`) | **DONE** — §6.1 (`39/39` publication files and `172/172` inputs per run; listing digests match) |
| Step 2: Seven E4 analysis outputs and `report-manifest.json` regenerated in a detached worktree outside the repo | AI pair (`Devin`, `Gemini 4 Argon High`) | **DONE** — §6.2 (`8/8` files byte-identical) |
| Step 3: Protocol §8.2 reconstruction of the 39 publication files for `reference` and `prin` | AI pair (`Devin`, `Gemini 4 Argon High`) | **DONE** — §6.3 (`prin` `39/39` raw-identical; `reference` `25/39` raw-identical and `39/39` normalized/sensitivity-identical) |
| Step 4: Independent recount from the five raw records | AI pair (`Devin`, `Gemini 4 Argon High`) | **DONE** — §3 (`0` discrepancies vs E4) |
| Step 5: E5 report (`report.md`) drafted and issued | AI pair (`Devin`, `Gemini 4 Argon High`) | **DONE** — this document |
| Step 6: D1 correction cycle opened (`2026-10-14-exp002-d1-s1..s4`), `0164` set to `BLOCKED`, Parity Report erratum + CHANGELOG line added | AI pair (`Devin`, `Gemini 4 Argon High`) | **DONE** — §8.2–§8.4 |
| **Maintainer verification of the E4/E5 analysis and acceptance of the verdicts** | **MichaelMaillet** | **OPEN — awaiting maintainer verification** (verification block below left unchecked) |
| **Maintainer approval of the S1 correction-cycle scope** | **MichaelMaillet** | **OPEN — awaiting maintainer approval** |
| Announcement of this report in the next Project State Report | Correction cycle S4 (`2026-10-14-exp002-d1-s4-correction-documentation.md`) | **OPEN** (Experimentation Standards §2 E5; campaign plan §10.4 item 3) |
| Correction cycle `S1 → S2 → S3 → S4` executed and closed | Per contingency briefs | **OPEN** — blocks `0164` and downstream sessions (§8.3) |
| `EXP-002-r1` re-run after S4 closes | Per campaign plan §10.4 item 4 | **OPEN** |

**Maintainer verification block** — left unchecked for the maintainer to complete at acceptance:

```text
Verified by: _________________________ Date (UTC): __________
Verdicts accepted as reported (H1 CONFIRMED, H2 CONFIRMED, H3 REFUTED under approved and sensitivity policies, H4 CONFIRMED): [ ]
D1 declaration and blocking of 0164 accepted:                                                                                 [ ]
Correction-cycle scope in §8.2 / S1 brief approved:                                                                           [ ]
```

**Local gate for this session (session `0163`).** Session `0163` modifies only documentation and byte-preserved evidence files (`.md`, `.rst`, `.txt`, `.json`, `.gitattributes`; zero `.py`, `.rs`, `.toml`, lockfile, or workflow files added or modified in the repository). Accordingly, the documented documentation/evidence delta gate was run from Git Bash on the maintainer's Windows host (`EVIDENCE/0163/verification/gate/`): `git diff --cached --check` (exit `0`), `tools/check_deviation_ledger.py DOCS/reports/039-project-state.md DOCS/reports/040-project-state.md` (exit `0`), `tools/check_dv_register_gates.py` (exit `0`), `tools/check_global_session_registration.py` (exit `0`), `tools/check_skipif_probes.py` (exit `0`), `tools/wp001_baseline.py check` (exit `0`), `pytest tests/test_wp001_baseline.py` (exit `0`), fresh-directory Sphinx build `sphinx.cmd.build -W --keep-going -b html` (exit `0`, 0 warnings), pinned `gitleaks` `8.30.1` on the staged diff and full history (exit `0`, 0 leaks), plus `cargo audit` recorded verbatim (exit `1` on 9 vulnerabilities — the 5 `quinn-proto 0.11.16` advisories `RUSTSEC-2026-0338`..`0342` and the 4 `2026-10-14` `rustls 0.23.45` advisories `RUSTSEC-2026-0346`..`0349` — plus 3 standing allowed warnings; **not** green, disclosed in §9.2 D-E5-2 and §13.3). Because no first-party code in a Snyk-supported language and no dependency manifest changed in session `0163`, Snyk Code, Snyk Open Source, and `pip-audit` have no changed input in this session and are not claimed to have run here (the E4 module's own Snyk Code scan and full local pytest/cargo gate are in `EVIDENCE/0162/`). Local results are local Windows validation under Plan amendment #48, never described as "CI green".

---

## 15. Errata

Corrections to this report after issue are appended as dated errata, never silent edits (Experimentation Standards §1.3, §4; campaign plan §12 item 6).

| # | Date (UTC) | Corrects | Substance | Raised by |
|---|---|---|---|---|
| — | — | — | None at initial issue. | — |
