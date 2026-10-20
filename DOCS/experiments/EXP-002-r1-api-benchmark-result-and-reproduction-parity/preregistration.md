# Pre-registration - EXP-002-r1: API, benchmark-result, and reproduction parity (re-run)

**Status:** DRAFT
**Authors:** MichaelMaillet (maintainer, session declaration and pre-E1 decision ratification); Devin (AI pair of record, drafting)
**Date:** 2026-10-20 UTC
**Maintainer approval:** NOT GRANTED (E1 DRAFT — scientific review and approval belong to `EXP-002-r1-E2`)
**Outcome-exposure disclosure (Experimentation Standards §1.1, §4; `EXP002D1-S2-F1`):** This re-run protocol is drafted **after full exposure** to `EXP-002`'s E3–E5 outcomes (`H1 CONFIRMED`, `H2 CONFIRMED`, `H3 REFUTED` at `21/39` under §5.4 and `5/39` under §11.3, `H4 CONFIRMED`) and to `EXP-002-D1` S1–S4's root-cause decomposition and residual classification (`39/39` equal under §5.4 and `14/39` equal under §11.3 on the corrected generator, with all `25` sensitivity-policy residuals proven in `EVIDENCE/exp002-d1-s2/both-policies-post-fix.txt` to be writer/host I/O properties and `0` unclassified). This disclosure is repeated in §1, §10, and §11 below and must be repeated verbatim in the E5 report.
**Code version:** `prin-core 1.0.0rc1` / Rust `1.0.0-rc1`
**Source baseline (`M`):** `5677858c15d784d881b23d43dff5029d199b0a18` (`origin/main` after PR #34 `305416fb` and PR #35 `5677858c`; `tools/check_ci_green.py 5677858c15d784d881b23d43dff5029d199b0a18` exit 0, all 6 required workflows green)
**Session sequence:** `EXP-002-r1-E1` (this pre-registration), `EXP-002-r1-E2` (review and approval), `EXP-002-r1-E3` (execution), `EXP-002-r1-E4` (analysis), `EXP-002-r1-E5` (report). Numbered sessions `0159`–`0163` remain permanently closed on `EXP-002`; session `0164` (`EXP-003 E1`) and `0165`–`0194` remain `BLOCKED` until `EXP-002-r1` E5 returns a non-reversal verdict verified and accepted by the maintainer (campaign plan §10.4 item 5).
**Record root:** `DOCS/experiments/EXP-002-r1-api-benchmark-result-and-reproduction-parity/`
**Raw-artefact root (isolated):** `benchmarks/results/EXP-002-r1/` (`RUN-<UTC>-<SHA>-r1-<label>/` directories only; `exp_id="EXP-002-r1"`, `session="EXP-002-r1-E3"`). Predecessor `benchmarks/results/EXP-002/` is immutable and never written to.
**Generated-output root (isolated, gitignored):** `DOCS/test_and_benchmark_results/EXP-002-r1/` (never `DOCS/test_and_benchmark_results/EXP-002/`).
**Stage verification evidence root (isolated):** `EVIDENCE/exp002-r1-e1/` (and `-e2`..`-e5` for subsequent stages).
**Related plan items:** Plan F1/F2/F4, section 5 items 4-5, Phase 7 C1, DoD 1/3/5/12; campaign plan sections 2.1, 6-10, 12, and 14.2 amendment #10; Plan amendments #49 and #52.

This is a prospective contract for `EXP-002-r1`, not an execution record or a
result. No `EXP-002-r1` execution, pilot, `RUN-` directory creation, hypothesis
adjudication, or scientific-output regeneration occurs at E1. The maintainer's
pre-E1 ratification of the Re-run Namespace & Evidence Isolation Rule, the
`EXP002D1-S2-F1` H3 comparison-policy registration, and DV-047 closure
authorizes drafting this protocol and `benchmarks/campaign/exp002_r1_driver.py`;
it does not supply E2 scientific approval or authorize E3 execution.

## 1. Background and motivation

`EXP-002` (sessions `0159`–`0163`, [`../EXP-002-api-benchmark-result-and-reproduction-parity/report.md`](../EXP-002-api-benchmark-result-and-reproduction-parity/report.md))
confirmed H1 (`175/175` API symbols resolved, `172/172` legacy names owned),
H2 (`62/62` historical claim predicates preserved), and H4 (`39/39` raw-byte
deterministic across two PRIN processes), and **refuted H3** (`21/39` generated
files equal under the approved §5.4 policy, `5/39` under the §11.3 pre-exposure
sensitivity policy; `18` figure files — `.pdf` and `.png` of figures 5, 7, 8,
9, 10, 11, 12, 14, 15 — differed from the frozen `prinet==3.0.0` reference
render). That `H3 REFUTED` verdict raised a campaign plan §10.4 **D1**, blocked
session `0164` (`EXP-003 E1`) and `0165`–`0194`, and opened the four-session
contingency correction cycle `EXP-002-D1`
([`DOCS/audits/2026-10-15-exp002-d1-correction-audit.md`](../../audits/2026-10-15-exp002-d1-correction-audit.md)).

`EXP-002`'s record, its `preregistration.md`, its verdicts, and its five `RUN-`
directories under `benchmarks/results/EXP-002/` are **permanently frozen and
immutable**. `EXP-002-r1` does not revise `EXP-002`'s `H3 REFUTED` verdict; it
is a new experiment record authorized under campaign plan §10.4 item 4 after
`EXP-002-D1` S1–S4 closed (`PR #34` merged at
`305416fb0f85e690b12640b3f32fad48b55d9077`, followed by `PR #35` merged at
`5677858c15d784d881b23d43dff5029d199b0a18`).

The `EXP-002-D1` correction cycle established that the root cause of H3's
refutation was exclusively on the **PRIN side**: the WP-034 port of nine figure
generators in `python/prin/reporting/figure_generation.py` dropped or
re-encoded **34 drawing arguments** (line widths, marker sizes, text alignments,
z-orders, bar edge colours, legend locations/frame alphas, a twin-axis
`tick_params` call, and three mathtext rewrites of Unicode multiplication/Greek
labels). Controlled substitution on the frozen `prinet==3.0.0` reference
attributed every differing byte to those 34 divergences with **0 unexplained**,
and artist-level inspection verified that no plotted data array or computed
quantity differed (`14/14` figure stems equal). Consequently, campaign plan
§10.4 item 3 (declaring the 3.0 reference erroneous via an EMA-style
mathematical audit) was **not** invoked and is not used here.

**Outcome-exposure disclosure.** Unlike a blind first run, this re-run is a
prospective **verification of a known correction on a known fixed input
population**. When drafting this protocol, the authors had full knowledge of:

1. `EXP-002`'s E3–E5 outcomes (`H1` `175/175`, `H2` `62/62`, `H3` `21/39` under
   §5.4 and `5/39` under §11.3, `H4` `39/39`).
2. `EXP-002-D1` S1–S2's post-fix measurements on the corrected generator
   ([`EVIDENCE/exp002-d1-s2/both-policies-post-fix.txt`](../../../EVIDENCE/exp002-d1-s2/both-policies-post-fix.txt)),
   showing `39/39` equal under the §5.4 policy and `14/39` equal under the
   §11.3 pre-exposure policy, with all `25` residuals classified as two
   writer/host I/O properties (`14` PDFs differing only in the `/Info`
   dictionary key set — 3 reference keys vs 4 fixed PRIN keys including
   `ModDate` — and `11` `.tex` tables differing only in Windows text-mode CRLF
   vs LF line terminators) and `0` unclassified residuals.

Old outcomes and S1/S2 diagnostic measurements are **never** reused as
`EXP-002-r1` observations. Every `EXP-002-r1` verdict must be computed at E4
solely from fresh `RUN-*-r1-*` directories created at E3 under the isolated raw
root `benchmarks/results/EXP-002-r1/`.

Campaign section 2.1's Reconciliation column governs unchanged:

- PRIN has 175 unique literal exports; the reference's canonical `__all__`
  has 172. The three PRIN additions are `BackendUnavailableError`,
  `__version__`, and `core_version`.
- `verify_api_surface(prin.__all__)` compares against PRIN's own
  `FROZEN_PUBLIC_API`, derived from `RC1_PUBLIC_API`, and must return
  `(set(), set())`.
- The verifiable publication set is figures 2-15: 14 figures in PDF and PNG,
  plus 11 LaTeX tables, exactly 39 publication files. Figure 1 never existed.
  `paper/artefact_manifest.json` inventories 172 historical JSON inputs.
- Historical conclusion preservation is not a fresh training, dynamics, or
  timing replication; downstream scientific owners (§5.3) remain unchanged.

### 1.1 Input, implementation, and compiled-extension provenance (DV-047 closed)

`REFERENCE` means
`DOCS/archive and reference from PRINet 3.0/PRINet-3.0.0-main/`.
It is a frozen scientific comparator, never current governance authority.
Before authoring the driver, **DV-047** was discharged at the E1 baseline
`5677858c15d784d881b23d43dff5029d199b0a18`: the stale
`.venv/Lib/site-packages/prin_core.pth` (which pointed at
`C:\dev\PRIN-r1-amendment\python`) was removed, `.venv/Lib/site-packages/prin.pth`
was verified to point solely to `C:\dev\PRIN\python`, and
`python/prin/_prin_core.pyd` was rebuilt from clean `main` using
`.venv\Scripts\python.exe -m maturin develop --release -m crates/prin-py/Cargo.toml`.

All paths in the following table are relative to the repository root:

| Input / implementation file | Byte size | SHA-256 at the E1 baseline (`5677858c`) |
|---|---:|---|
| `paper/artefact_manifest.json` | 28,645 | `300cdc094d2b7d27ac8b1e2556b2e6ed4dad3333f0038b45c8f87ea81612cce5` |
| `python/prin/__init__.py` | 11,536 | `cd43a8ff75422f8bfb5beca19f52c2cbfdcaddb330a358aad172aeb39c54c6bb` |
| `python/prin/_public_api.py` | 6,141 | `dd5745ababa809483b8d52198a096a1e9fa0de7e13e246245b13f47066853a6d` |
| `python/prin/_deprecation.py` | 3,239 | `132e86e991669d0abe65d89b624227250bfd61e54c2f97cb814366a0012f4e9a` |
| `python/prin/_prin_core.pyd` (rebuilt at `5677858c`, DV-047 closed) | 9,290,240 | `37392d067efa3983e384c94f4ac2268c4fad2f5ea929c529b3db50bff4fee99e` |
| `tools/reproduce.py` | 50,321 | `12333a02e18f29ff52c42b2d17d7ac6ef53d3756217f10a7b9a964f75150b5b9` |
| `python/prin/reporting/figure_generation.py` (corrected in `EXP-002-D1`) | 41,869 | `e216fec4f45ab71cfc5ef1286701c920731df278120e0afa0d216515b4bb19a7` |
| `python/prin/reporting/table_generation.py` | 29,173 | `1593f52d9a652842ee7d62163d9e6b397989e9c6489aa5cc43a8416b1083c8af` |
| `python/prin/reporting/_artifacts.py` | 5,834 | `845a398f7b849e2173cd81a6d673f28900114fec880561e812b9e7ef2217d90a` |
| `REFERENCE/src/prinet/__init__.py` | 11,959 | `ede92afc6771f2e29206534905e2820598ba841662a93d59f669f803a382f182` |
| `REFERENCE/src/prinet/utils/figure_generation.py` | 35,239 | `575eca5a6436a25f957702091a6a0b5b7f3d77f1f496f9e6b423550cf79e1520` |
| `REFERENCE/src/prinet/utils/table_generation.py` | 26,962 | `9ac382c487f7177465805a49686568b8ac323128cebeae342cca2b05814704cc` |

The new versioned driver is `benchmarks/campaign/exp002_r1_driver.py`. It pins
and verifies the SHA-256 and byte size of `python/prin/_prin_core.pyd`, the
corrected `python/prin/reporting/figure_generation.py`,
`python/prin/reporting/table_generation.py`, `paper/artefact_manifest.json`, and
the three `REFERENCE` files before admitting or closing any run. E2 records the
reviewed source commit and any pre-execution amendments. E3 records its actual
clean execution SHA `R` and the last pre-registration commit `F` at first `RUN-`
creation under `benchmarks/results/EXP-002-r1/`. Neither future SHA is
fabricated here.

## 2. Hypotheses (falsifiable, quantitative)

- **H1 - API mapping census:** all 175 independently expected PRIN names
  resolve to non-`None` callable/class or scalar-constant exports; all 172
  reference names have a Migration Guide ownership row; the observed export
  list has exactly 175 entries and no duplicates, removals or additions;
  the frozen-contract missing and extra sets are both empty.
- **H2 - Historical conclusion preservation:** all 62 registered elementary
  direction/threshold predicates in section 5.2 agree with their registered
  historical predictions: independent published claims for C01 and C03-C05,
  and for C02 each grid row's previously stored `chimera_detected`
  classification (archival self-consistency, not an independent
  prediction; section 3). Zero disagreements are allowed.
- **H3 - Publication fidelity (primary decision rule = section 5.4 policy):**
  one PRIN render and an independent frozen reference-generator render produce
  the exact 39-file publication inventory; all 11 line-terminator-canonical
  table byte strings and all 28 metadata-normalized figure byte strings agree
  under the section 5.4 comparison policy (`39/39` equal). In addition, the
  section 11.3 pre-exposure sensitivity policy is evaluated and reported
  alongside the primary verdict as a non-gating writer-property diagnostic,
  requiring every residual between section 5.4 and section 11.3 to be
  classified as one of the two known writer/host I/O properties (PDF `/Info`
  key-set asymmetry or `.tex` Windows CRLF vs LF line terminators) with `0`
  unclassified residuals.
- **H4 - Deterministic reproduction:** two separate PRIN render processes,
  including the campaign replicate-0 rerun, produce the same 39 filenames,
  raw byte sizes and raw SHA-256 digests, and identical canonical scientific
  result projections. Normalization cannot rescue H4.

H1 proves export/mapping completeness, not numerical or behavioral parity of
every callable. No-argument calls to arbitrary exports are not used: they can
start training, allocate devices, or write to default output roots. Existing
acceptance/smoke tests remain mandatory code checks; they are not substituted
for the campaign census or declared to be `EXP-002-r1` observations.

## 3. Expected results

| Hypothesis | Predicted direction | Predicted magnitude | Basis (with outcome-exposure disclosure) |
|---|---|---|---|
| H1 | Complete namespace and ownership preservation | 175/175 resolved; 172/172 owned; zero duplicate/missing/extra names | Frozen reference literal API, WP-001 ownership matrix, PRIN canonical tuple, Migration Guide; confirmed `175/175` in predecessor `EXP-002` and unchanged by `EXP-002-D1` |
| H2 | No reversal of registered historical predicates | 62/62 agreements; zero disagreements | Published chimera/topology/Goldilocks claims and previously stored threshold flags, specified per family in section 5.2; confirmed `62/62` in predecessor `EXP-002` and unchanged by `EXP-002-D1` |
| H3 | Reference-faithful publication representation under the primary §5.4 rule, with known writer/host I/O diagnostic under §11.3 | **Primary (§5.4 policy): 39/39 equal** (14 PDF + 14 PNG + 11 `.tex` tables). **Diagnostic (§11.3 pre-exposure policy, non-gating): 14/39 equal** (14 PNGs equal; 25 classified writer/host I/O residuals: 14 PDFs differing only in `/Info` key set and 11 `.tex` tables differing only in CRLF vs LF; **0 unclassified residuals**) | `EXP-002-D1` S1 restoration of the 34 dropped/re-encoded figure-generator arguments in `python/prin/reporting/figure_generation.py` (`e216fec4…`), verified in S2 (`EVIDENCE/exp002-d1-s2/both-policies-post-fix.txt`) and S3/S4 delta re-audits (`parity/test_parity_publication.py`); outcome exposure disclosed in header and §11 |
| H4 | Exact same-implementation repeatability | 39/39 raw byte identities; zero projection differences | `tools/reproduce.py` deterministic pipeline, fixed figure dates (`2000-01-01T00:00:00Z`), explicit output roots, sorted manifests, deterministic table formatting; confirmed `39/39` in predecessor `EXP-002` and preserved by `EXP-002-D1` |

These are predictions for `EXP-002-r1`'s fresh E3 runs, not counts from an E1
campaign execution.

## 4. Failure conditions

### 4.1 Exact decision rules

Only authenticated, source-matched, extension-verified (`_prin_core.pyd`
matching `PRIN_CORE_PYD_SHA256`), non-aborted run records under
`benchmarks/results/EXP-002-r1/` are admissible. For each hypothesis, first
apply its valid-counterexample rule, then its complete-coverage rule; otherwise
return `INCONCLUSIVE`.

| Hypothesis | CONFIRMED | REFUTED | INCONCLUSIVE |
|---|---|---|---|
| H1 | One complete admissible census meets every section 2 condition | Any missing/unresolvable/`None`/unsupported export, duplicate, unexpected name, missing ownership row, or nonempty frozen-contract difference in a valid complete census | No admissible complete census, including unavailable core/reference software or invalid provenance |
| H2 | All five registered families and all 62 identified predicates are present and agree | At least one admissible predicate contradicts its registered independent prediction | No valid contradiction but a required predicate/family cannot be evaluated; aborted records are not counted as passes |
| H3 (primary decision rule: §5.4 policy) | Complete admissible reference and PRIN inventories are exactly the registered 39 files, all 39/39 comparisons equal under the primary §5.4 policy, **and** all residuals under the §11.3 diagnostic policy have 0 unclassified entries outside the two registered writer/host I/O classes | A valid completed render omits/adds an output, or at least one admissible table/normalized-figure comparison differs under the primary §5.4 policy, **or** any residual between §5.4 and §11.3 is unclassified (not explained solely by PDF `/Info` key-set asymmetry or `.tex` CRLF vs LF line terminators) | No valid completed comparable pair, including a renderer/environment abort; a partial invalid render is not a negative result |
| H4 | Both admissible PRIN processes contain all 39 files with equal raw sizes/digests and equal canonical projections | At least one comparable admissible raw output or scientific projection differs | No valid mismatch but either comparable complete run is unavailable/invalid |

No significance test, pooled pass rate, rounded display value, normalization
change, or favorable subset can rescue a falsifier. Preserve mixed valid and
invalid observations separately; a rerun never erases an earlier valid
counterexample or turns an aborted record into a completed one.

### 4.2 Invalid-run abort criteria

1. Missing E2 approval; wrong source/version; uncommitted source/protocol
   changes; an import resolving outside the governed PRIN/reference source; or
   `python/prin/_prin_core.pyd` byte size or SHA-256 differing from the pinned
   E1 build (`PRIN_CORE_PYD_BYTES`, `PRIN_CORE_PYD_SHA256`, DV-047 guard).
2. Input or run-manifest failure, symlink/non-regular input, missing required
   schema field, wrong registered labels/cardinality, non-finite numeric
   input, or malformed output format. Preserve the offending record.
3. Incomplete required environment/metadata capture; wrong `(counter,key)`;
   wrong backend/dtype; a renderer/font-stack change between compared runs.
4. A crash, failed process, resource exhaustion, output-path escape, attempt
   to reuse a run/output directory, attempt to target or open predecessor
   `benchmarks/results/EXP-002/` or `DOCS/test_and_benchmark_results/EXP-002/`,
   or required software unavailable.
5. Campaign CPU/GPU/CI/storage cap exceeded — including the 2 MiB per-run cap,
   the 10 MiB per-root `EXP-002-r1` cap, the **10 MiB combined `EXP-002` +
   `EXP-002-r1` cap** (both raw roots plus both record roots), or the 64 MiB
   campaign-wide cap. Verification timeout governance (Plan amendment #49) does
   not remove or extend these experiment abort limits.
6. An unexpected stochastic/training/GPU operation, or unexpected input
   mutation. No GPU timing, training, new simulation, fitting or bootstrap
   operation is registered for this experiment.

### 4.3 Campaign D1 escalation and reporting

An unexplained missing API, historical conclusion reversal, publication
fidelity mismatch under §5.4 (or unclassified §11.3 residual), or
deterministic-reproduction mismatch breaches C1/F1/F2/F4. E4 flags it as D1
under campaign section 10.4; E5 still reports it in full, then keeps session
`0164` and downstream experiments blocked until a new contingency correction
cycle (`EXP-002-r1-D1` S1→S4) closes and a subsequent `EXP-002-r2` record
returns a non-reversal verdict (or a Plan §8.3 amendment is adopted).

Aborts are invalid observations, not refutations by themselves. Log every
abort, incomplete run and unavailable-software/hardware leg; report their
effect on coverage and the resulting `INCONCLUSIVE` verdicts.

## 5. Method

### 5.1 Configurations and API mapping

H1 uses the CPU-installed PRIN package at `R`, its rebuilt extension
`python/prin/_prin_core.pyd` verified against `PRIN_CORE_PYD_SHA256`, its own
frozen RC1 contract, the statically read reference `__all__`, and the committed
Migration Guide table. The independent expected set is the 172 reference names
union the three named PRIN additions (`BackendUnavailableError`, `__version__`,
`core_version`), not whatever names a candidate package exports. Collect one
row per expected name with its defining module/type, resolution error if any,
callable/constant classification and ownership-row presence. Collect the
complete observed export list, including duplicates/extras. Record the two sets
returned by `verify_api_surface` as separate fields.

### 5.2 Closed historical conclusion inventory (H2)

Every JSON path below is within `REFERENCE/benchmarks/results/` and must be
in the 172-record manifest. These are CPU-readable archival predicates, not
new dynamics measurements. Operands are unrounded stored numbers. For each
predicate retain its unique ID, input filename/JSON path, operands,
operator, independent expected Boolean, observed Boolean and units.

| Family | Inputs and exact predicate population | Count | Independent expected result / citation |
|---|---|---:|---|
| C01 | `phase1_chimera_seeds.json`: each indexed `bimodality_coefficient.raw_values[i] > 0.555`, i=0..4 | 5 | Each true; `paper/main.tex` section `sec:chimera`: all five sequences exceed the published BC threshold |
| C02 | `benchmark_y4q1_3_k_alpha_sensitivity.json`: each of the 42 distinct `(K,alpha)` rows, `bc_mean > 0.555` | 42 | Equal to that row's previously stored `chimera_detected` Boolean; the historical Fig. 4 threshold/contour classification, not a newly selected favorable region |
| C03 | `phase2_chimera_nsweep.json`: the four `sweep` rows whose `n_oscillators` is 128/256/512/1024, `bc_stats.mean > 0.5` | 4 | Each true; `paper/main.tex` Analysis, "Chimera as computational primitive", strength persists above 0.5 at all four sizes |
| C04 | `y4q1_8_topology_comparison.json`: ring `bc_mean` greater than each community mean (2 predicates); ring `bc_ci.ci_width` greater than each community width (2); 2community width greater than 4community width (1) | 5 | Each true; `paper/supplementary.tex` table `tab:topology`: ring highest mean/widest interval, 4-community narrowest. No ordering of the two rounded community means is asserted |
| C05 | `y3q49_goldilocks_zones.json`: only `csr_cpu`, `full_cpu`, `mean_field_cpu`, `sparse_knn_cpu`; CSR `zone_width` greater than each other width (3); full `K_c` less than each other onset (3) | 6 | Each true; Supplementary table `tab:goldilocks` and coupling-mode heuristic, CSR widest operating zone and full lowest onset. The CPU entries, not CUDA entries, are the registered archival comparator |

Total: exactly 62 elementary claim-comparator records, in five families.

### 5.3 Claims explicitly owned elsewhere

No owner below is discharged by successful archival rendering. Include this
coverage table in E4/E5 and keep every unavailable/deferred claim visible.

| Historical conclusion class / source | Scientific owner |
|---|---|
| CPU throughput, coupling complexity, sweep speedups and CPU scaling | EXP-003, including DV036-F5 at 0166 and the DV-036 CPU gate before 0168 |
| GPU throughput (including OscilloSim's 1.95B claim), Triton/CUDA comparisons, training-step and bridge overhead | EXP-004; GPU/bridge DV-036 gate before 0173; DV-001/DV-003 limitations retained |
| Fresh chimera boundaries, topology/size effects and capacity relation/replication | EXP-005; corrected-SI exception retained |
| CUDA-tagged `y3q49_finite_size_scaling.json` fit ranking and `y3q49_phase_coherence.json` lifetime ranking | EXP-004 backend qualification and EXP-005 scientific replication; their CUDA-derived directions are not substituted with CPU measurements here |
| CLEVR-N/IP accuracy, PT-versus-SA statistical equivalence, ablations, freezing, parameter/FLOP efficiency, trained supercritical regimes, gradient/representation geometry and training curves | EXP-006, with EXP-004 performance dependencies; historical intervals/p-values remain reference-only |
| Daemon p95, MOT/IP evaluation, noise/velocity/occlusion and adversarial robustness | EXP-007, with EXP-006 training dependencies; CPU/DirectML/NPU dispositions retained |
| Linux/macOS/Metal, compiler-free wheel matrix and NPU/new capabilities | EXP-008; amendment #48 suspension and campaign section 5.4 unavailable-hardware rule |

### 5.4 Publication census, reference arm, and primary H3 comparison policy

Use matched Python/Matplotlib/NumPy versions, Agg renderer, font files and
font-cache state for both implementations. Log exact versions, font-file
digests and the Matplotlib font-cache file digest before rendering; a change
during generation aborts the run. The reference arm imports the frozen `prinet`
publication modules, verifies their source paths/digests against
`REFERENCE_PINS`, and calls only their figure/table generators with explicit
snapshot and output paths under `DOCS/test_and_benchmark_results/EXP-002-r1/`.
It never calls a reference benchmark/training entry point.

The PRIN arm verifies the origin and SHA-256 digests of
`python/prin/reporting/figure_generation.py` (`PRIN_FIGURE_GENERATION_SHA256`)
and `python/prin/reporting/table_generation.py`
(`PRIN_TABLE_GENERATION_SHA256`), then calls `tools.reproduce.run_reproduction`
with `verify=True`, the verified snapshot, pinned input manifest, and explicit
fresh output root under `DOCS/test_and_benchmark_results/EXP-002-r1/`.

Registered figure stems (each must have `.pdf` and `.png` under `figures/`):

```text
fig2_clevr_n_capacity
fig3_chimera_metrics
fig4_chimera_k_alpha_heatmap
fig5_mot_occlusion_comparison
fig6_oscillosim_scaling
fig7_ablation_results
fig8_parameter_efficiency
fig9_training_curves
fig10_statistical_summary
fig11_flops_scaling
fig12_supercritical_regime
fig13_representation_geometry
fig14_gradient_flow
fig15_noise_velocity
```

Registered table stems (each must have `.tex` under `tables/`):

```text
tab_ablation
tab_param_efficiency
tab_chimera
tab_statistical
tab_occlusion
tab_oscillosim
tab_efficiency
tab_binding_params
tab_stress
tab_supercritical
tab_geometry
```

**Primary H3 comparison policy (sole deciding rule for H3, ratified for
`EXP002D1-S2-F1`):**

- **LaTeX tables (`.tex`):** compared after line-terminator canonicalization
  only (`CRLF` → `LF`, identically in both arms and in the archived baseline).
  The pinned reference writer opens each table in text mode with no `newline=`
  argument (so Windows translates `LF` to `CRLF`), while PRIN's writer passes
  `newline="\n"`. A lone `CR`, all other whitespace, and every content byte stay
  significant; raw sizes and digests are recorded unchanged, and H4 compares raw
  bytes.
- **PNG figures (`.png`):** retain `IHDR`/`PLTE`/`tRNS`/`IDAT`/`IEND` critical
  chunks under `normalize_matplotlib_output`, after CRC, critical-chunk, IHDR
  colour-rule, and decoded-image validation.
- **PDF figures (`.pdf`):** validate the registered Matplotlib single-revision
  classic-xref container (EOF/startxref, cross-reference entries, object
  boundaries, and Root/Info references). Within the referenced `/Info` object
  only, parse a flat dictionary of direct values and remove the four registered
  metadata entries (`CreationDate`, `ModDate`, `Creator`, `Producer` — key and
  value — whichever of them each arm wrote: PRIN sets all four fixed keys so H4
  raw determinism holds, while the reference passes no metadata so Matplotlib
  writes `Creator`, `Producer`, and wall-clock `CreationDate`). Re-serialize any
  remaining `/Info` entries in their original order with single-space
  separators; mask `/ID` only in the trailer; and canonicalize in-use `xref`
  byte offsets and the `startxref` pointer to zero. Preserve object
  identities/generations/status, every drawing/image/font stream, unregistered
  `/Info` fields, and every scientific label/value.

The 11 archived table files in `REFERENCE/paper/tables/` supply an additional
independent reference in H3, compared under the same line-terminator
canonicalization (their raw and normalized digests are recorded in every table
record). Neither writer is altered to chase §11.3 equality: PRIN's fixed PDF
metadata is required for H4 raw determinism, and the frozen `prinet==3.0.0`
reference is immutable.

### 5.5 Registered E3 procedure, namespace isolation, and command interface

Under the **Re-run (`-r1`/`-rN`) Namespace & Evidence Isolation Rule** (campaign
plan §7.1, §10.4 item 4, amendment #10), `EXP-002-r1` uses completely disjoint
roots from `EXP-002`:

- `RAW_ROOT = benchmarks/results/EXP-002-r1`
- `OUTPUT_ROOT = DOCS/test_and_benchmark_results/EXP-002-r1`
- `EXP_ID = "EXP-002-r1"`
- `SESSION_ID = "EXP-002-r1-E3"`

The committed driver `benchmarks/campaign/exp002_r1_driver.py` accepts
`--mode`, `--run-dir`, `--operator`, `--source-sha`, `--seed-counter`, and
`--seed-key`. It refuses execution while this document is `DRAFT`, checks
committed approval/source identity, verifies `python/prin/_prin_core.pyd` byte
size and SHA-256 (`PRIN_CORE_PYD_BYTES`, `PRIN_CORE_PYD_SHA256`), verifies a
clean checkout (exempting only untracked files under
`benchmarks/results/EXP-002-r1/` and the E3 operator `log.md`; any untracked or
modified file under predecessor `benchmarks/results/EXP-002/` is **rejected**),
explicitly rejects any path under `benchmarks/results/EXP-002/` or
`DOCS/test_and_benchmark_results/EXP-002/`, reserves each new `RUN-` directory
under `benchmarks/results/EXP-002-r1/` only after refusing a reused
generated-output root, writes `campaign-metadata.json` (`exp_id="EXP-002-r1"`,
`session="EXP-002-r1-E3"`), collects the selected leg, writes through
`write_result`, and closes a per-run `manifest.json`.

Run each row once, in a separate interpreter process, in the listed order:

| Mode | Required run label | Payload | Hypotheses |
|---|---|---|---|
| `api` | `r1-api-cpu` | `api.json` | H1 |
| `conclusions` | `r1-conclusions-cpu` | `conclusions.json` | H2 |
| `reference` | `r1-reproduction-reference-cpu` | `reproduction.json` | H3 |
| `prin` | `r1-reproduction-prin-cpu` | `reproduction.json` | H3/H4 |
| `repeatability` | `r1-seedrep0-prin-cpu` | `reproduction.json` | H4 |

The command below is the approved-E3 interface, **not an E1 invocation**.
Replace `UTC`/`R`/`label` with the actual values from the E3 execution log; `R`
is the full 40-character SHA, and the directory embeds its first seven
characters:

```powershell
.venv\Scripts\python -m benchmarks.campaign.exp002_r1_driver --mode api --run-dir "benchmarks/results/EXP-002-r1/RUN-<UTC>-<R7>-r1-api-cpu" --operator MichaelMaillet --source-sha <R40> --seed-counter 0 --seed-key 2
```

Each generated-output root is
`DOCS/test_and_benchmark_results/EXP-002-r1/<run-id>/publication/`; snapshots
are in the corresponding `inputs/` directory. Both are fresh and gitignored.

## 6. Variables and controls

- **Independent:** implementation (`prinet` frozen reference versus corrected
  PRIN) for H3; process invocation for H4; symbol/claim/file identity for the
  censuses.
- **Dependent:** resolution/ownership differences, predicate disagreements,
  exact inventory differences, raw/normalized/sensitivity byte differences and
  residual classifications.
- **Controlled:** all 172 input bytes (`INPUT_MANIFEST_SHA`), source/protocol
  SHA, rebuilt `_prin_core.pyd` binary digest (`PRIN_CORE_PYD_SHA256`), corrected
  `figure_generation.py` (`PRIN_FIGURE_GENERATION_SHA256`) and
  `table_generation.py` (`PRIN_TABLE_GENERATION_SHA256`) digests, version
  `1.0.0rc1`, backend CPU, double-precision JSON scalar decoding,
  fonts/renderer/package versions, generator settings, output stem/format, seed
  metadata `(0, 2)`, and result schema.
- **Baselines:** frozen reference API/ownership map; published directions and
  stored C02 flags; independent frozen reference generators and 11 archived
  tables; the first PRIN render for repeatability. No favorable subset.
- **Not measured:** throughput, device events, model accuracy, training
  efficiency or statistical power.

## 7. Sample plan and statistics

**Explicit E2 exception requested (same deterministic C1 justification as
`EXP-002`):** one deterministic census per leg, not ten newly drawn seeds.
Every run uses the enumerated pair `(counter,key) = (0,2)`; the fifth run is a
second invocation of replicate 0 of the same PRIN reproduction configuration.
No RNG is consumed by this protocol. Keep `seed_counter=0`, `seed_key=2` in
config; environment `seed=0` is the registered counter and `seed_used=false`
states that it is documentary.

The common `BenchmarkConfig` envelope retains `iterations=10`, `warmup=0` for
schema compatibility, with `measurement_kind="deterministic_census"` and
`replicates=1` explicit.

- **Populations, not sampled estimates:** 175 exports, 172 ownership names,
  62 elementary claim predicates, 39 publication files.
- **Statistics:** exact pass/disagreement counts per population/family; raw,
  normalized (§5.4 primary), and sensitivity (§11.3 diagnostic) byte mismatch
  inventories; exact classification of every sensitivity residual by writer/host
  I/O mechanism.
- **Uncertainty/effect sizes:** CIs, Cohen's *d*, Cliff's δ, α, power
  calculations, bootstrap resampling and significance tests are not applicable
  to these deterministic censuses (campaign plan §9.1).

## 8. Analysis plan

At `EXP-002-r1-E4`, commit the analysis implementation **before** analysis
starts: `analysis/exp002_r1_e4_analysis.py`, a globally unique module basename
under this record root (`tests/test_campaign_quality_gates.py`, PR32-F12). No
such module is created or executed in E1. DV-040 option (a) gates (source-only
Ruff formatting, Ruff lint, strict mypy, and non-vacuous Bandit over
`DOCS/experiments/`) and Snyk Code apply.

The analysis accepts only the five registered `EXP-002-r1` run records under
`benchmarks/results/EXP-002-r1/` and their manifests (never reading
`benchmarks/results/EXP-002/`), verifies provenance (`exp_id="EXP-002-r1"`,
`session="EXP-002-r1-E3"`, `prin_core_pyd_sha256`), and re-derives the §4.1
decisions from retained operands, names, and digest records without trusting any
driver-provided success label.

### 8.1 Registered output files

Seven analysis outputs regenerate deterministically under
`DOCS/test_and_benchmark_results/EXP-002-r1/analysis/`:

| File | Required contents and units |
|---|---|
| `summary.json` | H1-H4 three-way verdicts (with H3 decided by the primary §5.4 policy), the non-gating §11.3 writer-property diagnostic counts (`equal_count`, `residual_count`, `pdf_info_keyset_residual_count`, `tex_crlf_residual_count`, `unclassified_residual_count`), expected/observed denominators, aborts, D1 flag, input/source/protocol/extension/manifest digests; distinct `api_symbol_count`, `claim_comparator_record_count`, `generated_file_count` |
| `api-mapping.csv` | Exactly one row per independently expected export plus separately labelled unexpected exports; defining module/type, callable/constant, ownership, resolution failure |
| `conclusion-comparisons.csv` | All 62 uniquely labelled predicates, with family, input JSON path, operands/operator, expected/observed Boolean and `operand_unit`; BC dimensionless, K in the stored coupling convention |
| `reproduction-comparisons.csv` | All 39 output identities; reference/PRIN/repeat raw, normalized (§5.4 primary) and sensitivity (§11.3 diagnostic) sizes/digests, format, equality under both policies, residual classification (`none` \| `pdf_info_keyset` \| `tex_crlf_line_terminator` \| `unclassified`), and missing/extra-output diagnostics; sizes in bytes |
| `error-distributions.json` | Separate categorical pass/fail/missing populations by symbol, claim family and file format (plus the §11.3 diagnostic residual breakdown); no pooled histogram with an ambiguous denominator |
| `expected-vs-observed.md` | Side-by-side section 3 predictions and observed values/verdicts; deterministic uncertainty explicitly N/A |
| `coverage-and-deferrals.md` | Section 5.3 owner matrix, invalid/unavailable coverage, hardware/hosted/coverage limits and downstream gates, with no silently closed obligation |

`report-manifest.json` in `DOCS/experiments/EXP-002-r1-api-benchmark-result-and-reproduction-parity/`
hashes both the seven analysis outputs and, separately, the 39 PRIN-arm
publication files under `DOCS/test_and_benchmark_results/EXP-002-r1/`, along
with the input index of every `EXP-002-r1` run manifest, `R`, `F`,
`_prin_core.pyd` digest, and the input manifest digest.

### 8.2 Clean-checkout regeneration and retained-bytes verification

As in `EXP-002` (§11.3 item 2), the generated output roots
`DOCS/test_and_benchmark_results/EXP-002-r1/<run-id>/publication/` and `inputs/`
are retained unmodified, outside git, until the `EXP-002-r1` E5 report is
accepted. At E5, **first** verify the retained publication bytes (`39/39` per
publication run) against the raw digests in each manifested `reproduction.json`
and the retained input snapshots (`172/172` per run) against
`paper/artefact_manifest.json`; **second**, regenerate the seven E4 analysis
files and `report-manifest.json` in a clean detached worktree and confirm
byte-for-byte identity (`8/8`); **third**, perform the clean-checkout
reconstruction of both publication arms into a fresh gitignored directory under
 the matched renderer/font environment. Any reference-arm raw PDF difference due
to the reference writer's unpinned wall-clock `CreationDate` (while normalized
and sensitivity digests match `39/39`) is recorded as a reconstruction
limitation, never as a new H3/H4 observation.

## 9. Resource and storage budget

| Resource | Expected workload | Campaign cap |
|---|---|---|
| H1 Windows CPU wall | Namespace walk and frozen JSON predicates; three publication renders; expected < 5 min (~64 s observed in `EXP-002` E3) | <= 12 h (`EXP-002` allocation) |
| GPU wall | 0 h planned; no GPU leg | <= 2 h, retained but unused |
| Hosted CI wall | 0 h of experiment legs; Plan amendment #52 hosted workflow runs on PR/merge commits are source validation recorded verbatim, not charged as experiment legs | <= 2 h, retained |
| Tracked storage (`EXP-002-r1` alone **and** combined `EXP-002` + `EXP-002-r1`) | Text/JSON/CSV inventories and digests only (~340 KiB in `EXP-002`; expected ~350 KiB in `EXP-002-r1`, combined < 1 MiB) | <= 2 MiB per run; **<= 10 MiB for `EXP-002-r1` (`benchmarks/results/EXP-002-r1/` + record root) AND <= 10 MiB combined (`EXP-002` + `EXP-002-r1` raw roots + both record roots)**; <= 64 MiB campaign-wide (campaign plan §7.5, §8, §14.2 amendment #10) |

Both the per-root `EXP-002-r1` cap and the combined `EXP-002` + `EXP-002-r1`
10 MiB cap are enforced mechanically at run closure by
`exp002_r1_driver._storage_check`.

## 10. Reporting commitments and E2 handoff

`EXP-002-r1-E5` reports every registered run and all H1-H4 verdicts, the §11.3
writer-property diagnostic and its 25-residual classification table, negative
outcomes, invalid/incomplete runs, unavailable software/hardware,
expected-versus-observed differences, protocol deviations (including the `M..R`
source delta if any), the outcome-exposure disclosure, threats to validity, and
the complete artefact index. It also updates the Parity Report and appends an
append-only erratum to `EXP-002/report.md` §15 cross-referencing the completed
re-run report without altering `EXP-002`'s own `H3 REFUTED` verdict.

`EXP-002-r1-E2` must independently review and resolve:

1. **H1–H4 scope and decision rules (§2–§4):** confirm H1's 175-symbol/172-legacy
   census, H2's 62-predicate archival census and §5.3 downstream owner matrix,
   H3's 39-file publication census under the primary §5.4 comparison policy, and
   H4's two-process raw-byte identity and canonical projection rule.
2. **Resolution of `EXP002D1-S2-F1` (§5.4, §11.1, §11.3):** confirm the
   maintainer-ratified registration of §5.4 as the sole primary deciding rule
   for H3, §11.3 as the non-gating writer-property diagnostic requiring 0
   unclassified residuals outside the two known writer/host I/O classes, the
   replacement of `EXP-002`'s §11.3 item 1 clause, and the outcome-exposure
   disclosure.
3. **Namespace and evidence isolation (§5.5, §9; campaign plan amendment #10):**
   confirm the disjoint roots (`benchmarks/results/EXP-002-r1/`,
   `DOCS/test_and_benchmark_results/EXP-002-r1/`, `EVIDENCE/exp002-r1-e1/`..`e5/`),
   the `r1-` run labels, the predecessor-path rejection guards in
   `exp002_r1_driver.py`, and the combined 10 MiB (`EXP-002` + `EXP-002-r1`)
   storage cap enforcement.
4. **DV-047 closure and provenance pins (§1.1):** verify the rebuilt
   `python/prin/_prin_core.pyd` (`9,290,240 B`, SHA-256 `37392d06…ee99e`), removal
   of the stale `prin_core.pth`, and runtime enforcement in
   `exp002_r1_driver.py`.
5. **Sample/seed plan and retained-bytes verification (§7, §8.2):** confirm the
   `n=1` deterministic-census exception, `(counter,key) = (0,2)`, and the
   retained-bytes-first verification order for E5.
6. **Independent retro-audit of `EXP002D1-S4-F2` and `EXP002D1-S4-F3`
   (Development Workflow §7; `2026-10-15-exp002-d1-correction-audit.md`
   §S4.16 item 4):** perform the queued S2-class retro-audit of the two
   maintainer-authorized code changes made inside `EXP-002-D1` S4
   (`814b670c` in `parity/test_parity_publication.py` and `67100a69` in
   `tests/test_acceptance_subconscious.py`), using the checklist in
   [`e2-review-packet.md`](e2-review-packet.md) §4.

Carry forward, do not action or close here: DV-033, DV-034, DV-036 (`DV036-F5`
at `0166`, reference-host gates before `0168`/`0173`), DV-037, DV-046 (per-run
`gpu-cuda` check), `S2-F3`/`S2-F4`, and the EXP-004+ hardware gates.

## 11. Pre-registration disclosures and `EXP002D1-S2-F1` resolution

### 11.1 Resolution of `EXP002D1-S2-F1` — primary H3 rule vs writer-property diagnostic

In `EXP-002`, §11.3 item 1 carried the clause: *"If the two verdicts differ, E5
must state that H3's verdict depends on a comparison amendment made after
outcome exposure, and must not report either verdict alone."* That clause was
drafted before `EXP-002` E3, when both policies gave `REFUTED` (`21/39` and
`5/39`) because of the 34 dropped/re-encoded figure-generator arguments. After
`EXP-002-D1` restored those 34 arguments, the approved §5.4 policy gives
**`39/39` equal** while the §11.3 pre-exposure policy gives **`14/39` equal**
(`EVIDENCE/exp002-d1-s2/both-policies-post-fix.txt`). Every one of the `25`
residuals under §11.3 is a proven writer or host I/O property, not a scientific
or rendering divergence:

- **14 PDF figures (`figures/fig2_*.pdf` .. `figures/fig15_*.pdf`):** the §11.3
  policy masks the *values* of `/CreationDate`, `/ModDate`, `/Creator`, and
  `/Producer` in place (`/\1 (normalized)`) while keeping the `/Info` dictionary
  *key set* and line wrapping intact. PRIN's `_save_fig` passes all 4 keys
  (including a fixed `ModDate = 2000-01-01T00:00:00Z`, which is what makes H4
  raw-byte determinism hold), whereas the frozen `prinet==3.0.0` reference
  passes no `metadata=` argument, so Matplotlib writes only 3 keys (`Creator`,
  `Producer`, and wall-clock `CreationDate`, with no `ModDate`). Thus a 4-key
  `/Info` dictionary can never equal a 3-key `/Info` dictionary under
  value-only masking, even when every drawing, font, and content stream is
  byte-identical.
- **11 LaTeX tables (`tables/tab_*.tex`):** the §11.3 policy compares raw table
  bytes without line-terminator canonicalization. The frozen `prinet==3.0.0`
  reference `_save_table` opens files in text mode (`open(path, "w")`) with no
  `newline=` parameter, so on the Windows reference host the C/Python I/O layer
  translates `\n` to `\r\n` (`CRLF`), whereas PRIN's `_save_table` passes
  `newline="\n"` (`LF`). Every non-`CR` byte is identical.

Retaining `EXP-002`'s §11.3 item 1 wording unchanged in `EXP-002-r1` would force
E5 to refuse a single H3 verdict solely because PRIN writes `ModDate` and `LF`
while the frozen reference on Windows writes no `ModDate` and `CRLF`, and
changing either writer to chase §11.3 equality is forbidden (removing PRIN's
fixed metadata would break H4 or alter shipped behaviour; editing the frozen
`prinet==3.0.0` reference is prohibited).

Accordingly, by maintainer ratification before `EXP-002-r1` E1 (2026-10-20 UTC),
`EXP-002-r1` registers the following rule in place of `EXP-002` §11.3 item 1:

1. **Primary deciding rule for H3:** The **§5.4 comparison policy** (`CRLF`→`LF`
   table canonicalization + 4-key PDF `/Info` removal and `xref`/`startxref`
   pointer canonicalization + PNG critical-chunk normalization) is the **sole
   primary decision rule** that determines whether H3 is `CONFIRMED`, `REFUTED`,
   or `INCONCLUSIVE`, subject to the residual-classification requirement in (2).
2. **Non-gating writer-property diagnostic (§11.3 policy):** Every publication
   file record continues to capture `sensitivity_bytes` and `sensitivity_sha256`
   under the §11.3 pre-exposure policy (`6314532`). E4 and E5 report the §11.3
   comparison counts (`14/39` expected) side by side with the primary §5.4
   verdict in `summary.json`, `reproduction-comparisons.csv`, and `report.md`,
   and classify every file that passes §5.4 but differs under §11.3. **Every
   such residual must belong to one of the two registered writer/host I/O
   classes** (`pdf_info_keyset` for `.pdf` files whose §5.4 normalized bytes
   are identical; `tex_crlf_line_terminator` for `.tex` files whose `CRLF`→`LF`
   normalized bytes are identical), with **`0` unclassified residuals**. Any
   unclassified residual refutes H3 (§4.1). When all residuals belong to the two
   registered writer/host I/O classes (`0` unclassified) and §5.4 is `39/39`
   equal, H3's single verdict is **`CONFIRMED`**, and E5 reports the §11.3
   `14/39` count and 25-residual classification alongside it as a disclosed
   writer-property diagnostic rather than as a conflicting hypothesis verdict.

### 11.2 Outcome-exposure disclosure

This pre-registration is drafted with full knowledge of `EXP-002`'s E3–E5
outcomes and `EXP-002-D1` S1–S4's root-cause and residual-classification
evidence. All four hypotheses (H1–H4) are prospective verification tests of the
corrected `prin-core 1.0.0rc1` codebase at `5677858c` on fresh `EXP-002-r1` E3
runs; this exposure must be stated in the header, in §1, here in §11.2, in the
E2 review record, and in the E5 report.

### 11.3 Retained publication bytes and hosted-CI accounting

1. **Retained publication bytes:** The generated output roots
   `DOCS/test_and_benchmark_results/EXP-002-r1/<run-id>/publication/` and
   `inputs/` are retained unmodified, outside git, until the `EXP-002-r1` E5
   report is accepted. The E3 log records, per publication leg, the SHA-256 of
   a deterministic listing of the root (one `path size sha256` line per file,
   sorted by path). E5 verifies the retained bytes against the raw digests in
   each manifested `reproduction.json` before performing the §8.2
   clean-checkout reconstruction.
2. **Hosted CI accounting (Plan amendment #52):** Hosted workflow runs on
   `campaign/exp002-r1-*` PRs and merges validate the repository source under
   Plan amendment #52; they are recorded verbatim (workflow, run ID, head SHA,
   conclusion, link) in each stage's handoff/evidence record and are not charged
   against §9's hosted experiment-leg cap.

**DRAFT at E1 (2026-10-20 UTC). E2 scientific review and maintainer approval are
pending. No `EXP-002-r1` execution or `RUN-` directory creation has occurred.
Sessions `0164`–`0194` remain `BLOCKED`.**
