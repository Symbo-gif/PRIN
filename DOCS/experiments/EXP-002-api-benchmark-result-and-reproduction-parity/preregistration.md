# Pre-registration - EXP-002: API, benchmark-result, and reproduction parity

**Status:** DRAFT
**Authors:** MichaelMaillet (maintainer); Devin (AI pair of record, drafting)
**Date:** 2026-10-11 UTC
**Pre-E2 amendments:** section 11 (PR #33 review remediation, 2026-10-11 UTC)
**Maintainer approval:** NOT GRANTED - reserved for session 0160
**Code version:** `prin-core 1.0.0rc1` / Rust `1.0.0-rc1`
**Source baseline:** `da53ea11a3f38cd0d5c27c40bbefbeaf6d6dbf53`
**Session briefs:** 0159 E1, 0160 E2, 0161 E3, 0162 E4, 0163 E5
**Related plan items:** Plan F1/F2/F4, section 5 items 4-5, Phase 7 C1,
DoD 1/3/5/12; campaign sections 2.1, 6-10 and 12

This is a prospective contract, not an EXP-002 result. No EXP-002 execution,
pilot, hypothesis adjudication, or scientific-output regeneration occurs at E1.
The timeout directive approves validation governance, not this protocol.
The maintainer's subsequent permission to create necessary completion artefacts
permits preparing and testing the E1 driver; it does not supply E2 approval.

## 1. Background and motivation

EXP-001-r1's accepted non-reversal report releases this experiment's E1.
Its five confirmed hypotheses are predecessor evidence, not EXP-002 findings.
The historical merge is
`32cfed8a0b4d915a04e18efbfadd146a2ecb7e32`; the verbatim predecessor checker
output is retained in `EVIDENCE/ea007/exp001-r1-merge-ci-green.log` and in
0159's entry record. It is historical pre-pause evidence, not current CI.

The actual E1 baseline is PR #32's merge, `da53ea11...`, not EA-007's original
`add7386a` head. PR #32 merged on 2026-10-11 at 10:39:51 UTC and includes
`18d9c5b`, `0a0f700` and the later evidence-record commit `8b4d180`.
Its audit records 15 findings: 14 fixed, PR32-F13 declined/carried, and
subsequent self-review of the remediation. Those dispositions remain intact.

Campaign section 2.1's Reconciliation column governs over the old brief:

- PRIN has 175 unique literal exports; the reference's canonical `__all__`
  has 172. The three PRIN additions are `BackendUnavailableError`,
  `__version__`, and `core_version`. The reference's older 98-name
  `FROZEN_PUBLIC_API` is not the reference target.
- `verify_api_surface(prin.__all__)` compares against PRIN's own
  `FROZEN_PUBLIC_API`, derived from `RC1_PUBLIC_API`, and must return
  `(set(), set())`. Set equality alone cannot detect duplicate list entries.
- The verifiable publication set is figures 2-15: 14 figures in PDF and PNG,
  plus 11 LaTeX tables, exactly 39 publication files. Figure 1 never existed.
  `paper/artefact_manifest.json` inventories 172 historical JSON inputs;
  it is not an output manifest.
- Historical conclusion preservation is not a fresh training, dynamics or
  timing replication. Stored training/GPU numbers may be rendered on a CPU,
  but that does not satisfy the experiments owning those scientific claims.

Bases: `python/prin/{__init__,_public_api,_deprecation}.py`,
`DOCS/baselines/wp001_api_traceability.md`,
`DOCS/baselines/wp033_benchmark_traceability.md`,
`DOCS/sphinx/parity_report.rst`, `paper/{main,supplementary}.tex`,
`tools/reproduce.py`, the frozen reference publication generators, and
`tests/test_publication_generation.py`. E1 reads these existing sources and
input schemas only; it does not execute the registered collection methods.

### 1.1 Input and implementation provenance

`REFERENCE` means
`DOCS/archive and reference from PRINet 3.0/PRINet-3.0.0-main/`.
It is a frozen scientific comparator, never current governance authority.
All paths in the following table are relative to the repository.

| Input | SHA-256 at the E1 baseline |
|---|---|
| `paper/artefact_manifest.json` | `300cdc094d2b7d27ac8b1e2556b2e6ed4dad3333f0038b45c8f87ea81612cce5` |
| `python/prin/__init__.py` | `cd43a8ff75422f8bfb5beca19f52c2cbfdcaddb330a358aad172aeb39c54c6bb` |
| `python/prin/_public_api.py` | `dd5745ababa809483b8d52198a096a1e9fa0de7e13e246245b13f47066853a6d` |
| `python/prin/_deprecation.py` | `132e86e991669d0abe65d89b624227250bfd61e54c2f97cb814366a0012f4e9a` |
| `tools/reproduce.py` | `12333a02e18f29ff52c42b2d17d7ac6ef53d3756217f10a7b9a964f75150b5b9` |
| `python/prin/reporting/figure_generation.py` | `e0f59253202746e0548fb9711229040ec7beeae05c3501fc0b3eca0cf997d533` |
| `python/prin/reporting/table_generation.py` | `1593f52d9a652842ee7d62163d9e6b397989e9c6489aa5cc43a8416b1083c8af` |
| `REFERENCE/src/prinet/__init__.py` | `ede92afc6771f2e29206534905e2820598ba841662a93d59f669f803a382f182` |
| `REFERENCE/src/prinet/utils/figure_generation.py` | `575eca5a6436a25f957702091a6a0b5b7f3d77f1f496f9e6b423550cf79e1520` |
| `REFERENCE/src/prinet/utils/table_generation.py` | `9ac382c487f7177465805a49686568b8ac323128cebeae342cca2b05814704cc` |

The manifest supplies exact filename, byte size and digest for every JSON
input. Scientific reads must use `read_verified_no_follow`, not a successful
verification followed by an unrelated unverified open. Rendering uses a new,
byte-verified input snapshot, never a rewritten reference directory.

The new versioned driver is `benchmarks/campaign/exp002_driver.py`.
E2 records the reviewed source commit and any pre-execution amendments.
E3 records its actual clean execution SHA R and the last preregistration
commit F at first `RUN-` creation. Neither future SHA is fabricated here.
Changes to the baseline follow campaign section 10.2 and are reported at E5.

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
- **H3 - Publication fidelity:** one PRIN render and an independent frozen
  reference-generator render produce the exact 39-file publication inventory;
  all 11 line-terminator-canonical table byte strings and all 28 normalized
  figure byte strings agree (section 5.4).
- **H4 - Deterministic reproduction:** two separate PRIN render processes,
  including the campaign replicate-0 rerun, produce the same 39 filenames,
  raw byte sizes and raw SHA-256 digests, and identical canonical scientific
  result projections. Normalization cannot rescue H4.

H1 proves export/mapping completeness, not numerical or behavioral parity of
every callable. No-argument calls to arbitrary exports are not used: they can
start training, allocate devices, or write to default output roots. Existing
acceptance/smoke tests remain mandatory code checks; they are not substituted
for the campaign census or declared to be EXP-002 observations.

## 3. Expected results

| Hypothesis | Predicted direction | Predicted magnitude | Independent basis |
|---|---|---|---|
| H1 | Complete namespace and ownership preservation | 175/175 resolved; 172/172 owned; zero duplicate/missing/extra names | Frozen reference literal API, WP-001 ownership matrix, PRIN canonical tuple, Migration Guide; inspected statically at E1 |
| H2 | No reversal of registered historical predicates | 62/62 agreements; zero disagreements | Published chimera/topology/Goldilocks claims and previously stored threshold flags, specified per family in section 5.2; no new PRIN outcomes used |
| H3 | Reference-faithful publication representation | 39/39 equal under the registered format-specific comparison | Faithful generator ports; the existing 11-table reference-byte acceptance contract; fixed matched rendering environment and explicitly declared metadata normalization |
| H4 | Exact same-implementation repeatability | 39/39 raw byte identities; zero projection differences | `tools/reproduce.py` deterministic pipeline, fixed figure dates, explicit output roots, sorted manifests, deterministic table formatting |

These are predictions, not counts of an E1 campaign run. H3 is stronger than
the current figure acceptance tests, which establish completeness and valid
normalization, not equivalence of every figure to the independent reference.

## 4. Failure conditions

### 4.1 Exact decision rules

Only authenticated, source-matched, non-aborted run records are admissible.
For each hypothesis, first apply its valid-counterexample rule, then its
complete-coverage rule; otherwise return `INCONCLUSIVE`.

| Hypothesis | CONFIRMED | REFUTED | INCONCLUSIVE |
|---|---|---|---|
| H1 | One complete admissible census meets every section 2 condition | Any missing/unresolvable/`None`/unsupported export, duplicate, unexpected name, missing ownership row, or nonempty frozen-contract difference in a valid complete census | No admissible complete census, including unavailable core/reference software or invalid provenance |
| H2 | All five registered families and all 62 identified predicates are present and agree | At least one admissible predicate contradicts its registered independent prediction | No valid contradiction but a required predicate/family cannot be evaluated; aborted records are not counted as passes |
| H3 | Complete admissible reference and PRIN inventories are exactly the registered 39 files and all comparisons equal | A valid completed render omits/adds an output, or at least one admissible table/normalized-figure comparison differs | No valid completed comparable pair, including a renderer/environment abort; a partial invalid render is not a negative result |
| H4 | Both admissible PRIN processes contain all 39 files with equal raw sizes/digests and equal canonical projections | At least one comparable admissible raw output or scientific projection differs | No valid mismatch but either comparable complete run is unavailable/invalid |

No significance test, pooled pass rate, rounded display value, normalization
change, or favorable subset can rescue a falsifier. Preserve mixed valid and
invalid observations separately; a rerun never erases an earlier valid
counterexample or turns an aborted record into a completed one.

### 4.2 Invalid-run abort criteria

1. Missing E2 approval; wrong source/version; uncommitted source/protocol
   changes; an import resolving outside the governed PRIN/reference source.
2. Input or run-manifest failure, symlink/non-regular input, missing required
   schema field, wrong registered labels/cardinality, non-finite numeric
   input, or malformed output format. Preserve the offending record.
3. Incomplete required environment/metadata capture; wrong `(counter,key)`;
   wrong backend/dtype; a renderer/font-stack change between compared runs.
4. A crash, failed process, resource exhaustion, output-path escape, attempt
   to reuse a run/output directory, or required software unavailable.
5. Campaign CPU/GPU/CI/storage cap exceeded. Verification timeout governance
   does not remove or extend these experiment abort limits.
6. An unexpected stochastic/training/GPU operation, or unexpected input
   mutation. No GPU timing, training, new simulation, fitting or bootstrap
   operation is registered for this experiment.

Campaign section 10.1's numerical guards and timing/provider controls remain
in force if such operations are ever introduced by an approved pre-E3 change;
they are not claimed as exercised by this read/render-only protocol.
An unexplained seed/projection mismatch is retained as a reproducibility
falsifier and escalated under section 4.3, as campaign section 6.5 requires.

### 4.3 Campaign D1 escalation and reporting

An unexplained missing API, historical conclusion reversal, publication
fidelity mismatch or deterministic-reproduction mismatch breaches C1/F1/F2/F4.
E4 flags it as D1 under campaign section 10.4; E5 still reports it in full,
then blocks the successor, including dependent experiments and synthesis.
The four contingency correction sessions run in order before resumption;
any corrected experiment uses a new `EXP-002-r1` record and new run IDs.
Declaring the reference erroneous requires the campaign's mathematical-audit
standard, not an E4 reinterpretation of a failed prediction.

Aborts are invalid observations, not refutations by themselves. Log every
abort, incomplete run and unavailable-software/hardware leg; report their
effect on coverage and the resulting `INCONCLUSIVE` verdicts. No successful
rerun, negative result or favorable historical figure may hide them.

## 5. Method

### 5.1 Configurations and API mapping

H1 uses the CPU-installed PRIN package at R, its own frozen RC1 contract,
the statically read reference `__all__`, and the committed Migration Guide
table. The independent expected set is the 172 reference names union the
three named PRIN additions, not whatever names a candidate package exports.
Collect one row per expected name with its defining module/type, resolution
error if any, callable/constant classification and ownership-row presence.
Collect the complete observed export list, including duplicates/extras.
Record the two sets returned by `verify_api_surface` as separate fields.

No model is trained or arbitrarily invoked. No optimizer, loss, dataset
split, warmup, N/K/dt grid, GPU dispatch or timing arm is part of H1.
Numerical behavior remains owned by EXP-001-r1 and downstream replication;
hardware-dependent names must still resolve, with availability dispositions
reported rather than treated as successful hardware execution.

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
C02 is a census of all grid rows, including negative classifications.
Preserve `(K,alpha)` labels; never compare only a sorted unlabeled value vector.
C01/C03/C04/C05 test published directions rather than assuming that a stored
caption is true. A disagreement between paper and stored input is reported,
not resolved by selecting a different input/threshold/backend after inspection.

The gold-standard metric display in
`benchmark_y4q1_3_gold_standard_chimera.json` and the K/alpha heatmap are also
included in H3's entire publication census. The archival SI values are
rendered faithfully; this does not assert that corrected PRIN SI must equal
the defective reference implementation (Plan amendment #25 / EXP-005).

The CPU Goldilocks comparison is an archival direction check, not an
estimate of current PRIN critical coupling or a performance gate.
Recomputing boundaries, bootstrap intervals, finite-size fits or coherence
lifetimes from fresh trajectories is not registered here.

### 5.3 Claims explicitly owned elsewhere

No owner below is discharged by successful archival rendering. Include this
coverage table in E4/E5 and keep every unavailable/deferred claim visible.
The 58-script to nine-category WP-033 traceability matrix supplies the full
legacy benchmark inventory; it is not replaced by five historical families.

| Historical conclusion class / source | Scientific owner |
|---|---|
| CPU throughput, coupling complexity, sweep speedups and CPU scaling | EXP-003, including DV036-F5 at 0166 and the DV-036 CPU gate before 0168 |
| GPU throughput (including OscilloSim's 1.95B claim), Triton/CUDA comparisons, training-step and bridge overhead | EXP-004; GPU/bridge DV-036 gate before 0173; DV-001/DV-003 limitations retained |
| Fresh chimera boundaries, topology/size effects and capacity relation/replication | EXP-005; corrected-SI exception retained |
| CUDA-tagged `y3q49_finite_size_scaling.json` fit ranking and `y3q49_phase_coherence.json` lifetime ranking | EXP-004 backend qualification and EXP-005 scientific replication; their CUDA-derived directions are not substituted with CPU measurements here |
| CLEVR-N/IP accuracy, PT-versus-SA statistical equivalence, ablations, freezing, parameter/FLOP efficiency, trained supercritical regimes, gradient/representation geometry and training curves | EXP-006, with EXP-004 performance dependencies; historical intervals/p-values remain reference-only |
| Daemon p95, MOT/IP evaluation, noise/velocity/occlusion and adversarial robustness | EXP-007, with EXP-006 training dependencies; CPU/DirectML/NPU dispositions retained |
| Linux/macOS/Metal, compiler-free wheel matrix and NPU/new capabilities | EXP-008; amendment #48 suspension and campaign section 5.4 unavailable-hardware rule |

The draft Parity Report's "benchmark re-run not yet run" distinction remains
true for claims not executed by their owners. H2 is deterministic preservation
of the explicitly registered historical conclusion set; it is not permission
to call a report-rendering exercise the full PRIN benchmark re-run.

### 5.4 Publication census, reference arm and comparison

Use matched Python/Matplotlib/NumPy versions, Agg renderer, font files and
font-cache state for both implementations. Log exact versions, font-file
digests and the Matplotlib font-cache file digest before rendering; a change
during generation aborts the run. The reference arm imports the frozen `prinet`
publication modules, verifies their source paths/digests, and calls only
their figure/table generators with explicit snapshot and output paths.
It never calls a reference benchmark/training entry point.

The PRIN arm calls `tools.reproduce.run_reproduction` with `verify=True`,
the verified snapshot, pinned input manifest and explicit fresh output root.
Master generators can degrade gracefully: their exit status alone cannot
prove completeness. Inventory all resulting files and compare exact paths.

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

H3 compares tables after line-terminator canonicalization only: every CRLF
pair becomes LF, identically in both arms and in the archived baseline. The
pinned reference writer opens each table in text mode with no `newline=`
argument, so the Windows I/O layer writes CRLF, while PRIN's writer passes
`newline="\n"`; the line terminator is a property of the host I/O layer, not
of the generated table. A lone CR, all other whitespace and every content
byte stay significant, raw sizes/digests are recorded unchanged, and H4
compares raw bytes. PNG
comparison retains IHDR/PLTE/tRNS/IDAT/IEND under the existing
`normalize_matplotlib_output` policy, after CRC, critical-chunk and
decoded-image validation. PDF comparison admits the registered Matplotlib
single-revision classic-xref container, validating its EOF/startxref,
cross-reference entries, object boundaries and Root/Info references. It is
container validation, not a general PDF interpreter. Within the referenced
Info object only, parse a flat dictionary of direct values and remove the
four registered entries CreationDate, ModDate, Creator and Producer - key
and value - whichever of them each arm wrote: PRIN's writer sets all four,
while the pinned reference writer passes no metadata, so Matplotlib writes
only Creator, Producer and CreationDate. Re-serialize the remaining entries
in their original order with single-space separators, so the original value
lengths leave no line-wrap residue; an Info object that is not such a
dictionary is malformed. Mask document ID only in the trailer. Canonicalize in-use xref byte offsets and
the startxref pointer to zero: metadata-field length changes relocate
objects, and those offsets are structural addresses, not scientific content.
Preserve object identities/generations/status, every drawing/image/font
stream, other Info fields, and every scientific label/value. No pixel
tolerance, raster resampling, whitespace stripping, numeric rounding or
scientific-content masking. Record raw and normalized byte sizes/digests
separately. This metadata-only policy, including pointer canonicalization,
needs explicit E2 approval. It never applies to H4; raw files are retained
unchanged.

The 11 archived table files supply an additional independent reference in
H3, compared under the same line-terminator canonicalization (their raw
digests are recorded too). If a reference-generator table differs from its frozen
archived table, report that inconsistency; do not silently redefine the
baseline to the new render. Archived figure digests are provenance, not an
unmatched-renderer comparison substituted for the matched reference arm.

### 5.5 Registered E3 procedure and command interface

The committed driver accepts `--mode`, `--run-dir`, `--operator`,
`--source-sha`, `--seed-counter`, and `--seed-key`. It refuses execution while
this document is DRAFT, checks committed approval/source identity and a
clean checkout (no tracked change; no untracked, non-ignored file outside
the raw record root and the E3 operator log; no untracked top-level
`*.py`/`*.pth`, even if ignored, that could shadow a module), reserves
each new run directory only after refusing a reused generated-output root, captures campaign metadata, collects the selected
leg, writes through `write_result`, and closes a per-run manifest. It
collects observations only; hypothesis verdicts are E4 work.

Admission requires the first header status to be exactly `APPROVED` and the
first approval field to begin `MichaelMaillet, YYYY-MM-DD UTC`. A later
example, a template choice list, or timeout-policy approval cannot authorize
execution. The driver checks a per-leg wall overrun and storage at closure;
the E3 operator must enforce the unchanged <=12 h aggregate CPU cap across
all attempts, including invalid/incomplete ones. A nonzero closure exit
renders a record inadmissible even if its raw status says `COMPLETED`.
Every failure after a run directory is reserved, including sidecar or
output-root creation, is retained as an `ABORTED` record.

Closure re-derives provenance from git: the recorded protocol digest must
be the protocol blob at the recorded commit, that blob must be `APPROVED`
with the recorded dated approval, and the commit must be an ancestor of the
execution source. Closure validates each mode's observation schema and
identifiers, including the full 175-name and 62-case populations of the
`api` and `conclusions` legs, whose collectors refuse anything else. It never
counts publication files: an omitted or added output is H3's registered
falsifier, not an invalid record. The run directory may hold only its
sidecar, result and manifest.

Run each row once, in a separate interpreter process, in the listed order:

| Mode | Required run label | Payload | Hypotheses |
|---|---|---|---|
| `api` | `api-cpu` | `api.json` | H1 |
| `conclusions` | `conclusions-cpu` | `conclusions.json` | H2 |
| `reference` | `reproduction-reference-cpu` | `reproduction.json` | H3 |
| `prin` | `reproduction-prin-cpu` | `reproduction.json` | H3/H4 |
| `repeatability` | `seedrep0-prin-cpu` | `reproduction.json` | H4 |

The command below is a future approved-E3 interface, **not an E1 invocation**.
Replace UTC/R/label with the actual values from the execution log; R is the
full 40-character SHA, and the directory embeds its first seven characters.

```powershell
.venv\Scripts\python -m benchmarks.campaign.exp002_driver --mode api --run-dir "benchmarks/results/EXP-002/RUN-<UTC>-<R7>-api-cpu" --operator MichaelMaillet --source-sha <R40> --seed-counter 0 --seed-key 2
```

Use the other four registered mode/label pairs without changing any scientific
input. Each generated-output root is
`DOCS/test_and_benchmark_results/EXP-002/<run-id>/publication/`; snapshots
are in the corresponding `inputs/` directory. Both are fresh and gitignored.
The repeatability projection removes per-run `environment`, `config.out_dir`,
run ID, timestamps, elapsed duration and generated-output root, but not
implementation, seed pair, source/protocol/input identity, filenames,
raw/normalized sizes/digests, API rows or conclusion operands.

Before accepting a record, independently validate its complete metadata,
result envelope, exact declared artefact mapping, manifest and source/input
identity. An aborted record cannot be admissible merely because it hashes.
Raw records stay under new `RUN-` roots, including aborted/incomplete runs.

## 6. Variables and controls

- **Independent:** implementation (`prinet` frozen reference versus PRIN) for
  H3; process invocation for H4; symbol/claim/file identity for the censuses.
- **Dependent:** resolution/ownership differences, predicate disagreements,
  exact inventory differences, raw/normalized byte differences.
- **Controlled:** all 172 input bytes, source/protocol SHA, version, backend
  CPU, double-precision JSON scalar decoding, fonts/renderer/package versions,
  generator settings, output stem/format, seed metadata and result schema.
- **Baselines:** frozen reference API/ownership map; published directions and
  stored C02 flags; independent frozen reference generators and 11 archived
  tables; the first PRIN render for repeatability. No favorable subset.
- **Not measured:** throughput, device events, model accuracy, training
  efficiency or statistical power. No claims about CUDA/wgpu execution,
  DirectML, NPU, Linux, macOS or the wheel matrix follow from these controls.

Do not borrow reference-host timing outcomes as experimental observations.
All historical configurations are labels/provenance, not new executions:
C01 historical five sequences; C02 N=256, k=90, A=0.995, dt=0.05, 4,000
steps, 42 K/alpha rows; C03 N={128,256,512,1024}, dt=0.01, 5,000 steps,
seven historical seeds; C04 N=256, three topologies, five historical seeds;
C05 four CPU-tagged stored regimes. Those samples are neither regenerated
nor shortened here; fresh replication remains with the owners in section 5.3.

## 7. Sample plan and statistics

**Explicit E2 exception requested:** one deterministic census per leg, not
ten newly drawn seeds. Every run uses the enumerated pair `(counter,key) =
(0,2)`; the fifth run is a second invocation of replicate 0 of the same
PRIN reproduction configuration. No RNG is consumed by this protocol.
Keep `seed_counter=0`, `seed_key=2` in config; environment `seed=0` is the
registered counter and `seed_used=false` states that it is documentary.

The common BenchmarkConfig envelope retains `iterations=10`, `warmup=0`
for schema compatibility. These unused timing fields do not mean ten
measurements or ten replicates: `measurement_kind=deterministic_census` and
`replicates=1` are explicit. E2 must accept this representation or request a
prospective schema disposition before E3, never reinterpret ten as sample n.

- **Populations, not sampled estimates:** 175 exports, 172 ownership names,
  62 elementary claim predicates, 39 publication files. These denominators
  are fixed before outcomes; a missing member remains a coverage defect.
- **Statistics:** exact pass/disagreement counts per population/family;
  maximum absolute numeric discrepancy only where two scalar representations
  are actually compared; raw/normalized byte mismatch inventories otherwise.
  Report the operands and units, not an invented numerical relative error
  for a digest, namespace, Boolean or byte-identity predicate.
- **Uncertainty/effect sizes:** CIs, Cohen's d, Cliff's delta, alpha, power
  calculations, bootstrap resampling and significance tests are not applicable
  to these deterministic censuses. The exact mismatch count/rate is descriptive
  of this finite population, not a population-estimated effect with uncertainty.
- **Historical intervals:** copy their units and reference-only status when
  rendered. C04 compares already stored interval widths; it does not estimate
  new intervals or claim new statistical significance.
- **Multiple comparisons:** no inferential tests are performed, so no
  multiplicity correction is applied. All predicates are retained and each
  can falsify its family; aggregation cannot hide a failed comparison.

This departure is justified by campaign section 9.1's deterministic C1 rule,
not by insufficient resources. Repeating identical deterministic inputs ten
times would not create ten independent scientific samples or increase power.

## 8. Analysis plan

At 0162, commit the analysis implementation **before** analysis starts:
`analysis/exp002_e4_analysis.py`, a globally unique module basename under
this record root. No such module is created or executed by session 0159.
DV-040 option (a), strengthened by PR #32, governs the module: source-only
Ruff formatting, Ruff lint, strict mypy and non-vacuous Bandit include
`DOCS/experiments/`; Snyk Code applies. The retained prospective workflows
are not hosted-validated while amendment #48 is in force.

The analysis accepts exactly the five registered run records and their
manifests, verifies provenance and input-byte identity before reading, and
re-derives section 4.1 decisions from retained operands, names and digest
records. It must not trust a driver-provided success label as a verdict.
No current source rerun or fresh measurement is needed to compute a decision
from the committed raw records and frozen inputs.

### 8.1 Registered output files

Seven analysis outputs regenerate deterministically under
`DOCS/test_and_benchmark_results/EXP-002/analysis/`:

| File | Required contents and units |
|---|---|
| `summary.json` | H1-H4 three-way verdicts, expected/observed denominators, aborts, D1 flag, input/source/protocol/manifest digests; distinct `api_symbol_count`, `claim_comparator_record_count`, `generated_file_count` |
| `api-mapping.csv` | Exactly one row per independently expected export plus separately labelled unexpected exports; defining module/type, callable/constant, ownership, resolution failure |
| `conclusion-comparisons.csv` | All 62 uniquely labelled predicates, with family, input JSON path, operands/operator, expected/observed Boolean and `operand_unit`; BC dimensionless, K in the stored coupling convention |
| `reproduction-comparisons.csv` | All 39 output identities; reference/PRIN/repeat raw and normalized sizes/digests, format, equality and missing/extra-output diagnostics; sizes in bytes |
| `error-distributions.json` | Separate categorical pass/fail/missing populations by symbol, claim family and file format; no pooled histogram with an ambiguous denominator |
| `expected-vs-observed.md` | Side-by-side section 3 predictions and observed values/verdicts; deterministic uncertainty explicitly N/A |
| `coverage-and-deferrals.md` | Section 5.3 owner matrix, invalid/unavailable coverage, hardware/hosted/coverage limits and downstream gates, with no silently closed obligation |

The paper reproduction set is **39 files**, separate from these seven
analysis files; do not report 46 as the figure/table count.
`report-manifest.json` in the record root hashes both declared output sets,
with path, raw byte size and raw digest; generated files remain gitignored.
Its input index names every raw run manifest, exact source SHA and input
manifest digest. Freeze generator versions/fonts and explicit metadata.
Exclude wall-clock generation times from deterministic analysis text.

EXP-001-r1 report section 9 item 11 distinguishes **216 retained comparator
records** from **72 per-case worst values**. Neither is an EXP-002 denominator.
Any future histogram field must state its unit, e.g.
`..._over_claim_comparator_records` versus `..._over_generated_files`;
never reuse an unlabeled `abs_diff_decade_histogram`. No numeric histogram is
registered for the Boolean/byte censuses here.

### 8.2 Clean-checkout regeneration

At E5, from a clean checkout of the recorded source, validate input/run
manifests, regenerate the seven analysis files from the captured observations,
and reproduce the 39 publication outputs from their frozen 172-input
snapshot/source recipe with the same renderer/font environment.
All raw output digests must match `report-manifest.json`. Reference/PRIN
arm generation is not to be repeated merely to reformat an already captured
summary; presentation reads frozen observations.
Any unavailable reconstruction requirement is disclosed as a limitation
and cannot be called byte-verified.

## 9. Resource budget

| Resource | Expected workload | Unchanged campaign cap |
|---|---|---|
| H1 Windows CPU wall | Namespace walk and frozen JSON predicates; three publication renders; budget expectation under 1 h, not a measured E1 duration | <=12 h |
| GPU wall | 0 h planned; no GPU leg | <=2 h, retained but unused |
| Hosted CI wall | 0 h while amendment #48 is in force | <=2 h, retained, not permission to dispatch workflows |
| New tracked raw/record artefacts | Text/JSON/CSV inventories and digests only; no tracked publication binaries/checkpoints/snapshots | <=10 MiB |

Keep the generic <=2 MiB tracked-JSON per-run cap and the campaign-wide
<=64 MiB cap. Large rendering/snapshot files live only in the declared
gitignored output root. Record elapsed wall time and actual tracked byte
totals, including aborted attempts, in E3/E5; abort or seek an approved
campaign amendment before exceeding a cap. No cap is changed by Plan #49.

Only the maintainer's Windows H1 device is planned. Its actual OS, CPU/core
count, RAM, Python/Rust/package/font versions and installed extension
features are captured at E3, not copied from stale campaign host prose.
H2's cross-OS reproduction rerun is suspended under amendment #48; Windows
success is not Linux/macOS/wheel-matrix success.

## 10. Reporting commitments and E2 handoff

0163 reports every registered run and all H1-H4 verdicts, negative outcomes,
invalid/incomplete runs, unavailable software/hardware, expected-versus-observed
differences, deviations, exploratory work (if any), threats and the complete
artefact index. The maintainer verifies/accepts the report; the next actual PSR
announces it. No new PSR/WP/audit cycle is invented at E1.
Scientific approval is recorded only by 0160; freeze occurs at first E3 run,
not at E1 draft completion or timeout-policy adoption.

0160 must independently review and resolve:

1. H1's export/mapping scope versus behavioral/numerical claims; the three
   PRIN additions and the separate 175-name/172-name contracts.
2. H2's five-family/62-predicate closed archival scope, independent published
   predictions, CPU Goldilocks selection, and the complete downstream owner
   matrix. No source inconsistency may be fixed by post-outcome selection.
3. H3's matched independent reference arm, raw table reference, exact 39
   filenames, metadata-only normalization and renderer/font controls.
4. H4's separate-process raw-byte identity and exact scientific projection.
5. The justified n=1/no-inference exception and unused common timing-envelope
   fields, `(0,2)` metadata, deterministic regeneration and storage sanity.
6. The tested driver, source provenance/admission/abort guards, actual reviewed
   execution baseline, local evidence and publication status. Approval cannot
   precede closure of driver/review findings.
7. The two pre-E2 H3 comparison amendments of section 11 (table CRLF
   canonicalization; PDF Info-dictionary canonicalization): approve them,
   amend them, or declare the affected H3 leg unrunnable on the registered
   Windows host. Without them H3 would report every table and every PDF
   unequal for host-I/O and metadata reasons alone.
8. Raw publication-byte verification: each run manifest covers only the
   sidecar and result JSON, while the generated PDF/PNG/table bytes live in
   the gitignored output root, so section 8.2's clean-checkout byte check
   depends on reconstruction under a matched renderer. Decide whether that
   suffices or whether the generated bytes must also be preserved and hashed
   outside git before E3.
9. Pre-E2 outcome exposure (section 11.2): decide whether H2 and H3 may still
   be reported as confirmatory, and record the decision and its reason.

Carry forward, do not action or close here: DV-033 per-change coverage and
its historical incomplete attempts; DV-034 single-runner SPOF; DV-040's 0162
re-audit; DV036-F5 at 0166; DV-036 reference-host gates before 0168/0173;
EXP-004+ hardware gates; PSR-040's S2-F3/S2-F4 dispositions;
PR32-F13/OBS-1/OBS-2 and the unvalidated hosted rustdoc step at re-enable.
OBS-3 is historical: this E1 checkout was already non-shallow before work
and no history restoration or ignore-fingerprint change was performed.
Native push protection remains a flagged external control, not a pass.

## 11. Pre-E2 amendment log

### 11.1 PR #33 review remediation (session 0159, 2026-10-11 UTC)

Seven review sources on PR #33 were adjudicated in
`DOCS/audits/PR033-multi-review-audit.md`. These DRAFT edits answer its
findings; each needs E2 review under section 10. Every basis is a static
reading of the committed source plus synthetic fixtures. No registered input,
no real generator run over the input snapshot, and no EXP-002 outcome was
used.

| Change | Finding | Basis |
|---|---|---|
| Section 5.4: tables compared after CRLF to LF canonicalization in both arms and the archived baseline | PR33-F1 | The pinned reference `_save_table` uses `open(path, "w")` with no `newline=`; PRIN's uses `newline="\n"`. A synthetic table written by both writers on Windows differs only in CRLF |
| Section 5.4: registered Info entries removed, not value-masked; remaining entries re-serialized | PR33-F2 | PRIN `_save_fig` passes four metadata keys; the reference passes none. Synthetic Matplotlib PDFs differ only in Info key set and line wrapping after value masking |
| Section 5.4: font-cache digest logged | PR33-F29 | The registered control was named but not captured |
| Section 5.2 C03: selected by `n_oscillators` | PR33-F22 | The input schema key, as the driver already reads it |
| Section 2 H2: C02 basis described as archival self-consistency | PR33-F24 | Matches section 3; no predicate, expected value or population changes |
| Section 5.5: admission scope, reservation order, abort retention, closure provenance/schema | PR33-F3/F4/F5/F23/F30 | Driver guards; no scientific parameter changes |
| Section 10 items 7-9 | PR33-F1/F2/F9/F38 | Decisions that belong to E2 |

No hypothesis, predicted direction or magnitude, population or denominator,
threshold, tolerance, sample/seed plan, statistic, budget or abort criterion
changes. H4 still compares raw bytes, so neither canonicalization can rescue
it.

### 11.2 Disclosure: outcome information was published before E2

Two independent PR #33 reviews posted outcome information on the public PR
thread before E2. One executed the real reference and PRIN publication
generators over the verified 172-input snapshot. It reported per-file H3
table and figure comparison results, including which PDFs it attributed to
metadata and which to content. It also evaluated all 62 H2 predicates
against the archived inputs and reported that they hold. Another reported
the C03 N=128 operand margin. Section 4.1's decision rules and section 3's
predictions were committed at `7859030` and unchanged since; the protocol's
last pre-review change (`6314532`, section 5.4 only) also predates those
reviews. Session 0159's entry condition, "No result from this experiment has
been inspected," was true at entry, but E2's entry condition no longer holds
as written. The remediation auditor read those outcomes only as review text;
it did not reproduce them, run any generator over registered inputs, or use
them to choose a change. Its
section 5.4 changes rest only on the bases in section 11.1, and each is a
symmetric, metadata-only canonicalization that does not depend on which
files would match. E2 records the disposition under section 10 item 9.

**No EXP-002 experiment execution occurs in session 0159. This protocol
remains DRAFT. Hosted checks follow Plan amendment #50's EXP-002-scoped
window (amendment #48 otherwise remains in force).**
