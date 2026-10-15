# EXP-002 — E4 analysis record

**Status:** ANALYSED — the frozen decision rules (pre-registration §4.1, §5.2, §5.4, §5.5, §11.3) were
applied to the five immutable E3 records. **H1 `CONFIRMED`, H2 `CONFIRMED`, H3 `REFUTED` (approved
policy, primary), H4 `CONFIRMED`; H3 under the §11.3 sensitivity policy is also `REFUTED`. The campaign
plan §10.4 D1 flag is RAISED (H3, publication-fidelity mismatch).**
**Record date:** 2026-10-13 UTC.
**Session:** 0162 — EXP-002 / C1, E4 (Analysis). Predecessor 0161 (E3), successor 0163 (E5).
**Branch / PR:** `campaign/0159-exp002-e1` / PR #33.
**AI pair drafting this analysis:** Claude Opus 5.5 (Experimentation Standards §4 authorship
disclosure). It did not draft the E1 protocol body or the driver (Devin did); it drafted the PR #33
pre-E2 amendments, the E2 review record, and this module. Read-only cold reviewers: Antigravity
(`gemini-3.8-flash-high`) and Devin (`swe-2-high`). **The maintainer verifies this analysis at E5;
this record does not claim that verification has happened.**
**Pre-registration freeze SHA `F`:** `9a9889d08dcaf2ad0ce31659ed67721b54b114d0` (`log.md` line 1 since
the erratum below; campaign plan §12.4). Protocol SHA-256
`0f3073dd2ed73b64071bcf3ae182510a69a26bd575b81b5a97cc5a1f9bbc8c8b`.
**Execution source `R`:** `fae24c4393c7a0232e6c8f0a6388b1775aa5fc05`.
**Analysis code (campaign plan §7.4 item 2):** [`analysis/exp002_e4_analysis.py`](analysis/exp002_e4_analysis.py)
at commit **`3731fc2590cf86bdb657fce25e4917d26567b23a`** (module SHA-256
`7a400aa66d1edd9a8aa41967f22ed77b720f0534bba6f9fe99f3af703d6ee4e4`), committed and pushed at
2026-10-13T16:10:53Z, before the first run on a real record (16:11:43Z).

> This record interprets nothing beyond the registered rules. It makes no root-cause claim for the H3
> differences, introduces no tolerance, normalization, denominator or exclusion, and does not declare
> the reference erroneous.

## STEP 0 — erratum to the closed E3 log

Campaign plan §12.4 requires the freeze SHA on `log.md` line 1. The E3 log quoted `F` in §1 and §4.1
but not on line 1. Commit **`7d850ba`** (its own commit, nothing else changed) prepends one line and a
blank line:

> Pre-registration freeze: **`9a9889d08dcaf2ad0ce31659ed67721b54b114d0`** - the git SHA of the last
> `preregistration.md` edit, recorded at the creation of the first `RUN-` directory
> (2026-10-12T21:27:05Z; campaign plan section 12.4); the pre-registration is frozen from that point.
> (Line added at session 0162 as an erratum.)

No other E3 file was touched.

## Pre-flight (read-only; 2026-10-13, before any analysis code existed)

All commands from `C:\dev\PRIN`, Git Bash unless noted; started 2026-10-13T10:14:27Z.
Captures: `EVIDENCE/0162/verification/preflight/`.

| Check | Command | Result |
|---|---|---|
| HEAD | `git rev-parse HEAD` | `73dd6dafc6a4f2fad88f06be04dba6fc7011e920` = the handoff HEAD |
| Tree | `git status --porcelain` | empty |
| New commits | `git log --oneline 73dd6da..HEAD`; `git fetch origin campaign/0159-exp002-e1`, `git log HEAD..FETCH_HEAD` | none locally or on the remote branch; no change to `python/`, `crates/`, `benchmarks/`, `tools/`, `paper/`, `parity/`, `tests/`, the protocol, `e2-review.md`, a raw record or `EVIDENCE/0161`; no `Cargo.lock`/`Cargo.toml` change |
| PR #33 activity | `gh pr view 33 --json comments,reviews` and the inline-comment API, timestamps only | last comment 2026-10-11T23:25:34Z, last review 2026-10-11T17:48:59Z; nothing new since E2. Bodies were not opened (the pre-E2 outcome statements are never inputs, E2 decision 9) |
| Shallow clone | `ls .git/shallow` | absent |
| Record anchors | `sha256sum` of the 5 result files, 5 manifests and 5 sidecars | all 15 equal the E3 log and the handoff anchors |
| Protocol / freeze | `sha256sum preregistration.md`; `git log -1 --format=%H -- preregistration.md` | `0f3073dd…bc8c8b`; `9a9889d…` = `F` |
| Input manifest | `sha256sum paper/artefact_manifest.json` | `300cdc094d2b7d27ac8b1e2556b2e6ed4dad3333f0038b45c8f87ea81612cce5` |
| **E4 entry condition** | `.venv/Scripts/python -I EVIDENCE/0161/verification/tools/validate_run_record_rev3.py benchmarks/results/EXP-002/<RUN> --mode <mode>` | api **81/81**, conclusions **80/80**, reference **87/87**, prin **87/87**, repeatability **87/87** passed, 0 failed, exit 0 each |
| Retained publication roots | e2-review.md §8 listing-digest command, verbatim, from PowerShell | reference `d674de7d4b5830c9abf525fcc484a5ebc01e3620ca38b63badd037e289487323`; prin and repeatability `c1ca4ada167c50a28db2dfe4365d004cdb3621903f43e38cc6de75c2e4904669` — **all equal the E3 log; no abort** |
| Hosted runs for HEAD | `gh run list -R Symbo-gif/PRIN --commit 73dd6da…` | snyk push `38328901048`, snyk PR `38328905487`, parity `38328905477`, repro `38328905482`, python `38328905492`, gpu `38328905496` success; rust `38328905471` **failure** in its `audit` job (the known `quinn-proto` advisories, `log.md` §9). No nightly dispatched |

**Host and toolchain.** HP OMEN 16L; Windows 11 Home 10.0.26300 (`Windows-11-10.0.26300-SP0`);
AMD Ryzen 7 8700F, 8 cores / 16 logical CPUs; 31.6 GiB RAM; Python 3.14.0 (`.venv`); NumPy 2.5.1;
Matplotlib 3.11.1; rustc 1.99.0 (b940084d7 2026-09-28) / cargo 1.99.0; git 2.51.2.windows.1;
ruff 0.16.1; mypy 2.3.0; bandit 1.9.4; pytest 9.1.1; Snyk CLI 1.1306.2; gitleaks 8.30.1 (pinned).
The analysis module imports none of NumPy, Matplotlib, `prin` or `prinet`.

## Analysis code (Phase A — implemented and gated before any outcome was seen)

| Item | Value |
|---|---|
| Module | [`analysis/exp002_e4_analysis.py`](analysis/exp002_e4_analysis.py) — standard library only; never imports `prin`, `prinet`, the driver or `tools.reproduce` (which imports `prin`), never renders, resolves an export or reads a retained publication root |
| Tests | [`tests/test_exp002_e4_analysis.py`](../../../tests/test_exp002_e4_analysis.py) — **176** synthetic tests; **99 %** branch coverage of the module (1,030 statements, 8 missed; uncovered: an `os.open` failure, an open-time identity race, a mid-read `OSError`, and two branches) |
| Commit / push | **`3731fc2`**, its own commit, pushed 2026-10-13T16:10:53Z |
| Run index | explicit, five entries (`REGISTERED`), each pinned to its run ID and the result, manifest and sidecar SHA-256 from the E3 log — never a `RUN-*` glob; the raw root may hold only `README.md` and these five runs |

**Order of operations in the module.** (1) Global provenance, failing closed with nothing written:
`R` descends from `F` and `HEAD` from `R`; the protocol blob at `F` has the pinned digest, the dated
`APPROVED` header and is byte-identical at `R` and in the working tree; the input manifest digest; the
`*.json` inventory and every byte of the 172 frozen inputs; the pinned reference `__all__`; the RC1
contract sources at `R` against protocol §1.1 (`_public_api.py` `dd5745ab…`, `_deprecation.py`
`132e86e9…`). (2) Per record, before `observations` is opened: directory inventory, pinned manifest,
manifested and pinned sidecar/result bytes, strict JSON (no BOM, duplicate key or non-finite constant),
sidecar, status `COMPLETED`, environment, configuration, identity (source, protocol, approval, the 172
input records). (3) Re-derivation: the H1 population (172 + 3), legacy flags, ownership (Migration Guide
and WP-001 baseline at `R`), the frozen-contract missing/extra sets (RC1 tuple at `R`) and every row's
resolution class; all 62 H2 records, field by field, from the manifest-verified frozen inputs;
internal consistency of every publication file record. A disagreement makes the record inadmissible —
it is never a verdict. (4) §4.1 adjudication: valid-counterexample rule first, then complete coverage,
else `INCONCLUSIVE`; H3 under both policies; D1 = any primary `REFUTED`.

**Decisions fixed before any outcome, from the registered text.** H3's table comparisons include PRIN
against the 11 archived tables (§5.4: "an additional independent reference in H3"; "do not silently
redefine the baseline to the new render"), and reference-versus-archived inconsistencies are reported.
D1 follows the primary (approved-policy) H3 verdict, which is the confirmatory one (e2-review.md
decision 9); the sensitivity verdict is reported beside it and never hidden. A resolved row that is
neither callable nor a built-in scalar type is "unverifiable" (a coverage gap). In H4 an identical extra
output in both PRIN runs does not refute (H3 catches it), and the same file missing from both is
`INCONCLUSIVE`. None of these choices was exercised by the real records (no extra output, no
unverifiable row, no missing file).

### Phase-A local gate (Git Bash; authoritative regime, Plan amendment #48)

Candidate: `7d850ba` with the module and tests staged. Captures with verbatim `COMMAND:`, `UTC-START:`,
`ELAPSED_S:` and `EXIT_CODE:` are in `EVIDENCE/0162/verification/gate-phase-a/`. Nothing else of mine ran
during a leg. The maintainer's desktop applications were running throughout (the Devin desktop app,
started 2026-10-12, at about 58 % host CPU load together with the IDE services), and every process spawn
was slow; trivial legs took about 10 s.

| Leg | What | Exit | Result |
|---|---|---|---|
| G01 | `ruff check python/ tests/ benchmarks/ tools/ parity/ DOCS/experiments/` | 0 | all checks passed |
| G02 / G03 | `ruff format --check` (product roots; `DOCS/experiments/` source-only) | 0 / 0 | already formatted (G03: 3 files) |
| G04 / G05 / G06 | `mypy --strict` on `python/prin`, `DOCS/experiments/`, `exp002_driver.py` | 0 / 0 / 0 | no issues (G05: 3 source files) |
| G07 | `interrogate -c pyproject.toml python/prin` | 0 | 97.6 % (minimum 95 %) |
| G08 | `bandit -r python/prin DOCS/experiments -c pyproject.toml` | 0 | no issues; 27,804 LOC (0161: 24,864) |
| G09 | focused pytest: the new tests, `test_campaign_quality_gates`, `test_basetemp`, `--cov` of the module | 0 | 211 passed; module 99 % (branch) |
| G10–G10f | deviation ledger 039→040; DV-register gates; global-session registration; skipif probes; WP-001 baseline; `git diff --cached --check` | 0 each | passed |
| G11 | Sphinx `-W --keep-going` full build into scratch | 0 | build succeeded |
| G12 | fast pytest `tests/ -m "not slow and not gpu" --cov=prin` | 0 | **4,029 passed**, 178 skipped, 55 deselected; TOTAL 95 % (0161: 3,853 + the 176 new) |
| **G13** | full pytest `tests/ parity/ --cov=prin` | **1** | **2 failed**, 6,221 passed, 184 skipped, in 8,634.66 s (0161: 1,985.99 s). Failed: `test_acceptance_subconscious.py::TestIntegration::test_no_gpu_throughput_regression` (ratio 1.60, limit `< 1.30`; registered host-sensitive under DV-032) and `test_notebooks.py::test_notebook_executes_end_to_end[02_clevr_n_binding.ipynb]` (a cell exceeded its 900 s timeout) |
| G13a | the two failures rerun in isolation (diagnostic; G13 stays failed) | 1 | notebook **passed** (165 s); throughput test **failed** again (ratio 3.32) |
| G14 | Snyk Code on byte-identical copies of the 2 new files, `--severity-threshold=medium --org=symbo-gif` | 0 | **0 issues** (also 0 on the pre-review and post-review copies) |
| G17 / G18 | gitleaks (pinned 8.30.1) full history / staged | 0 / 0 | 723 commits, no leaks / no leaks |
| R01–R04 | cargo version, fmt, clippy, clippy `strict-checks` | 0 each | clean |
| R05 / R06 | `cargo test --workspace` (default / `strict-checks`) | 0 / 0 | 1,604 and 1,608 passed, 0 failed (identical to 0161) |
| R07 | `cargo llvm-cov -p prin-kernels --features wgpu,cpu` | 0 | TOTAL regions 85.10 %, functions 88.54 %, lines 84.24 % (identical to 0161) |
| **R08** | `cargo audit` | **1** | **not green:** 5 vulnerabilities, all `quinn-proto 0.11.16` (RUSTSEC-2026-0338…0342), the open item of `log.md` §9; `Cargo.lock` unchanged; not actioned (maintainer decision) |

**The red G13 leg.** Neither failing test imports or exercises the new module, and nothing else in the
product, test or Rust trees changed. The throughput test is a registered wall-clock ratio (DV-032) and
failed again in isolation on this loaded host; its assertion was not touched. The notebook passed in
isolation. I judged both failures environmental and committed and pushed the Phase-A code so that the
analysis code would demonstrably precede any real run. The local gate is **not** claimed green: G13 and
G13a are kept as failed captures, and the full suite was run again on the final candidate (Phase C,
below). This judgement is reported to the maintainer.

### Phase-A cold review (read-only; the reviewers could not see any outcome)

Antigravity and Devin reviewed the module and the tests twice, before any real run, under a hard rule not
to open the run records, the retained roots, the frozen reference inputs, the E3 transcripts or PR #33
comments. Neither report contains outcome content. Round 1: Antigravity found no defect; Devin raised
F1 (Medium, test fast path) and F2–F8 (Low). Round 2 confirmed the fixes and raised four Low items.
Every item was verified before acting: real items were fixed with tests (frozen-contract re-derivation,
verbatim owner matrix, wrapped I/O errors, calendar validation, `GIT_*` scrubbing, registered key sets,
the fast-path guard and its distinguishing test); three were declined with evidence (the `*.json`
inventory rule is `verify_manifest`'s; `os.environ` already upper-cases keys on Windows; the driver
stores the frozen sets sorted, lines 333–334). No item implicated a decision rule, the protocol or the
data. Task files, verbatim reports and the adjudication: `EVIDENCE/0162/verification/delegation/`.

## Phase B — the run

| | Run 1 | Run 2 (determinism) |
|---|---|---|
| Command (from `C:\dev\PRIN`) | `.venv/Scripts/python.exe -I DOCS/experiments/EXP-002-api-benchmark-result-and-reproduction-parity/analysis/exp002_e4_analysis.py` | same |
| Tree | clean, HEAD = `3731fc2` | HEAD = `3731fc2`; only run 1's `report-manifest.json` untracked |
| UTC start → end | 2026-10-13T16:11:43.984Z → 16:12:15.419Z | 16:12:54.139Z → 16:12:58.578Z |
| Elapsed | 31.435 s | 4.439 s |
| Exit code | **0** | **0** |

**Determinism:** all seven outputs and `report-manifest.json` are **byte-identical** between the two
runs (`cmp`). After the first real run nothing in the module, the tests or the decision logic changed.

**Output digests** (raw SHA-256; the seven files are gitignored under
`DOCS/test_and_benchmark_results/EXP-002/analysis/`, the manifest is committed in this record root):

| File | Bytes | SHA-256 |
|---|---:|---|
| `summary.json` | 13,407 | `2dabdea13d6d963caed4adb35edd2b66deaedc70929afcfb765003b7c3303e13` |
| `api-mapping.csv` | 18,375 | `7f2cfd76f62ccecae89f2e52bbf67c39ac067b82b7d4fef6ec499bb2c93c5e19` |
| `conclusion-comparisons.csv` | 10,872 | `0c01c59c8e1f32ea3ad173dddde117ad9a94b187289328da760e1c906e0bba85` |
| `reproduction-comparisons.csv` | 31,277 | `424f292d7699ab7e7d92ce089201a7d501acd7deae02aff50d393ac06870e0d1` |
| `error-distributions.json` | 4,345 | `e28f3e4fad0a5a7ba3dedc686900f7b808815378035d6dab6a402a2067025d9d` |
| `expected-vs-observed.md` | 2,397 | `97ecd3ab53bdbee2cf22e22e49866843544f70b3803213560978b4185af71789` |
| `coverage-and-deferrals.md` | 4,623 | `ff14a9f8592576f895a559b05d8b0848039d6efefc2b467d4bab97c3f94a18f9` |
| [`report-manifest.json`](report-manifest.json) | 18,848 | `6b15dcc112513cdce9cb2d923208f93d3616898225efed545706c56526e68781` |

`report-manifest.json` indexes the seven analysis outputs (path, raw bytes, raw SHA-256), separately the
**39 generated publication files** of the PRIN arm (raw size and digest as manifested in its
`reproduction.json`), every run manifest and file of the five runs, `R`, `F`, the protocol digest, the
input-manifest digest and the module path, commit and digest. The 39 publication files and the 7
analysis files are never summed.

## Admissibility

All five records are **admissible**; none is aborted; no record disagreed with any re-derivation. The
raw root holds only its `README.md` and the five indexed runs. Mixed valid and invalid observations: none
(no invalid observation exists).

| Run | Mode | Hypotheses | Status | Admissible |
|---|---|---|---|---|
| `RUN-20261012T212705Z-fae24c4-api-cpu` | api | H1 | COMPLETED | yes |
| `RUN-20261012T213054Z-fae24c4-conclusions-cpu` | conclusions | H2 | COMPLETED | yes |
| `RUN-20261012T213821Z-fae24c4-reproduction-reference-cpu` | reference | H3 | COMPLETED | yes |
| `RUN-20261012T213936Z-fae24c4-reproduction-prin-cpu` | prin | H3, H4 | COMPLETED | yes |
| `RUN-20261012T214040Z-fae24c4-seedrep0-prin-cpu` | repeatability | H4 | COMPLETED | yes |

## Verdicts (pre-registration §4.1)

Exact counts only; confidence intervals, effect sizes and significance tests are **not applicable** to
these deterministic censuses (§7). Every denominator carries its unit.

### H1 — API mapping census: **CONFIRMED**

175/175 api_symbols resolved (172 callable, 3 scalar constants; 0 `None`, 0 unsupported, 0 unresolved,
0 unverifiable); 172/172 legacy_api_names have both a Migration Guide row and a WP-001 ownership row;
the observed export list has 175 entries with 0 duplicates, 0 removals and 0 unexpected names; the
frozen-contract missing and extra sets are both empty (and equal the re-derivation from the RC1 tuple at
`R`). H1 is a namespace/ownership census only; it makes no behavioural or numerical parity claim
(e2-review.md decision 1).

### H2 — Historical conclusion preservation: **CONFIRMED**

62/62 claim_comparator_records agree with their registered expectation; 0 disagree. Per family: C01
5/5, C02 42/42, C03 4/4, C04 5/5, C05 6/6. Every record's operands, paths, operators, units and expected
values were re-derived from the manifest-verified frozen inputs and equal the record. C02's basis is
archival self-consistency (the stored `chimera_detected` flag), not an independent prediction (§2).

### H3 — Publication fidelity: **REFUTED** (approved policy, primary)

Both arms produced exactly the 39 registered files (0 missing, 0 extra in either arm). Under the approved
§5.4 policy, **21/39 generated_files are equal and 18 differ**:

| Format | Denominator (generated_files) | Equal | Differ | Missing |
|---|---:|---:|---:|---:|
| pdf | 14 | 5 | 9 | 0 |
| png | 14 | 5 | 9 | 0 |
| tex | 11 | 11 | 0 | 0 |

The 18 differing files are the PDF and PNG of nine figures: `fig5_mot_occlusion_comparison`,
`fig7_ablation_results`, `fig8_parameter_efficiency`, `fig9_training_curves`,
`fig10_statistical_summary`, `fig11_flops_scaling`, `fig12_supercritical_regime`,
`fig14_gradient_flow`, `fig15_noise_velocity`. For each, the normalized byte sizes of the two arms also
differ (`reproduction-comparisons.csv`). All 11 tables are equal between the arms and equal to the 11
archived tables (11/11); no reference table is inconsistent with its archived table under this policy.
**No cause is asserted here.**

### H3 under the §11.3 sensitivity policy: **REFUTED**

5/39 generated_files equal, 34 differ: all 14 PDFs, the same 9 PNGs as above, and all 11 tables. Under
this policy (tables compared as raw bytes) PRIN's 11 tables equal the archived tables (11/11), while all
11 reference-arm tables are inconsistent with the archived tables, and so differ from PRIN's. **The two
policies give the same verdict**, so §11.3 item 1's "depends on a post-exposure amendment" statement is
not triggered. Both verdicts are reported side by side in `summary.json` and
`reproduction-comparisons.csv`. In the generated `expected-vs-observed.md` and in `summary.json`, the
label "tables equal to archived" (`tables_equal_to_archived`) counts the **PRIN** arm's tables; the
reference arm's archived comparison is the separate `reference_tables_inconsistent_with_archived` field
(post-run self-audit item F-1; the module is not changed after its first real run).

### H4 — Deterministic reproduction: **CONFIRMED**

39/39 generated_files have equal raw sizes and raw SHA-256 between the two separate PRIN processes;
0 differ; 0 files in one run only; the §5.5 canonical projection of the two records is equal.
Normalization was not used.

## D1 flag (pre-registration §4.3; campaign plan §10.4)

**RAISED.** H3 is `REFUTED` by a registered falsifier — a publication-fidelity mismatch in 18 of the 39
generated files under the approved comparison — which breaches C1/F1/F2/F4. Under campaign plan §10.4,
E5 (0163) still completes and reports it in full, then blocks its successor (0164, EXP-003 E1, and the
dependent experiments and synthesis); the four contingency correction sessions run before resumption, and
any corrected experiment uses a new `EXP-002-r1` record and new run IDs. Declaring the reference
erroneous requires the campaign's mathematical-audit standard, not an E4 reinterpretation. **This
session started no correction session, changed no tolerance or policy, and kept every artefact.**

## Expected versus observed (pre-registration §3)

| Hypothesis | Predicted magnitude | Observed | Verdict |
|---|---|---|---|
| H1 | 175/175 resolved; 172/172 owned; zero duplicate/missing/extra | 175/175; 172/172; 0/0/0; frozen sets empty | CONFIRMED |
| H2 | 62/62 agreements | 62/62 claim_comparator_records | CONFIRMED |
| H3 (approved) | 39/39 equal | 21/39 generated_files equal; 18 differ (9 pdf, 9 png); tables 11/11 | REFUTED |
| H3 (sensitivity, §11.3) | reported beside H3 | 5/39 equal; 34 differ | REFUTED |
| H4 | 39/39 raw identities; zero projection differences | 39/39; projection equal | CONFIRMED |

## Coverage and deferrals (pre-registration §5.3)

`coverage-and-deferrals.md` carries the seven-row §5.3 owner matrix verbatim (a test compares it with the
protocol), each row **OPEN — not discharged by EXP-002**: CPU throughput/scaling (EXP-003, DV036-F5 at
0166, DV-036 CPU gate before 0168); GPU/bridge (EXP-004, DV-036 gate before 0173, DV-001/DV-003); fresh
chimera/topology/capacity (EXP-005); CUDA-tagged finite-size and coherence rankings (EXP-004/EXP-005);
CLEVR-N/IP, ablations, efficiency, training curves (EXP-006); daemon, MOT, robustness (EXP-007);
Linux/macOS/Metal, wheel matrix, NPU (EXP-008). The WP-033 traceability matrix remains the full legacy
inventory; the Parity Report's "benchmark re-run not yet run" stays true. No obligation is silently
closed. Coverage of this experiment is complete: five admissible records, no gap in any hypothesis.

## Protocol deviations

- **PD-1 (procedure, not a rule):** the Phase-A full-suite leg (G13) was red on two host-sensitive tests
  unrelated to the change when the module was committed and pushed; see "The red G13 leg". No rule,
  tolerance, normalization or population was affected.
- **PD-2 (procedure):** the first attempt of the final-candidate full suite was **void**: while it ran I
  wrote one evidence file (a `gh run list` capture) into `EVIDENCE/0162/`, which breaks the rule of no
  repository writes during a pytest leg. I stopped the leg within minutes, moved the file out, kept the
  partial capture (`gate-final/G13v-…-VOID-…`) and reran G13, R08, G18 and G17 from scratch on the
  unchanged staged candidate; that rerun is the recorded result.
- None other. No defect was found after the first real run; the module ran exactly as committed.

## Threats to validity

1. **Stale extension.** `python/prin/_prin_core.pyd` (SHA-256 `64ea1a2c…7b47349`, 2026-09-28) predates
   three Rust commits at `R` (`log.md` §2.6) and is not recorded by the driver. H1 resolved names
   against it; H2–H4 render stored JSON and exercise no Rust numerics. Disclosed, not actioned.
2. **`R` versus `F`.** `R` = `F` + one docs/evidence commit (`fae24c4`), whose only Python change lists
   evidence files in a manifest test (`log.md` §1).
3. **Pre-E2 outcome exposure** (protocol §11.2, e2-review.md decision 9). Reviewers published H2/H3
   outcome information before E2. H2 stays confirmatory (rules and predictions committed at `7859030`).
   H3 is confirmatory under the approved policy with the registered sensitivity analysis; both policies
   give `REFUTED`, so H3's verdict does not depend on the post-exposure amendment. This analysis did not
   read those statements.
4. **Retained publication bytes are not yet byte-verified.** H3/H4 are decided from the manifested digest
   records; E4 did not read the retained roots beyond the pre-flight listing digest. E5 must first verify
   the retained bytes against the raw digests in each manifested `reproduction.json`, then reconstruct
   from a clean checkout (§8.2, §11.3 item 2).
5. **Single Windows host;** Linux/macOS not tested (amendment #48).
6. **Driver residual gaps** found at E3 (junction ancestors, last-wins JSON, subset key checks): this
   module re-checks links (including reparse points), rejects duplicate keys and checks exact key sets on
   every record it reads; none of these conditions occurs.
7. **Loaded host during the gate** (the maintainer's desktop applications): affects test wall-clock only;
   EXP-002 measures no timing and the analysis outputs are byte-deterministic.

## Exploratory

None. No unregistered analysis was performed.

## Final local gate (Phase C) and hosted evidence

Candidate: `42f0eb3` with this record, the documentation updates, `report-manifest.json` and
`EVIDENCE/0162/` staged. The product, test and Rust trees are byte-identical to the Phase-A commit
`3731fc2` (`git diff --cached 3731fc2 -- crates Cargo.toml Cargo.lock python tests benchmarks tools parity
paper` is empty), so the Phase-A cargo build/test/coverage legs (R01–R07) carry over and the Phase-A Snyk
Code scan covers the same bytes. Captures: `EVIDENCE/0162/verification/gate-final/`. The host was quieter
than during Phase A.

| Leg | Exit | Result |
|---|---|---|
| G01–G08 (ruff, source-only format, mypy ×3, interrogate, bandit) | 0 each | clean; G03 3 files; G05 3 sources |
| G09 focused pytest | 0 | 211 passed |
| G10–G10f governance, `git diff --cached --check` | 0 each | passed (DV-register gate: 44 rows) |
| G11 Sphinx `-W` | 0 | build succeeded (with the new CHANGELOG entry) |
| G12 fast pytest | 0 | 4,029 passed, 178 skipped, 55 deselected in 446.51 s |
| G13v full pytest, first attempt | — | **void** (PD-2), stopped |
| **G13 full pytest** | **0** | **6,223 passed, 184 skipped, 0 failed** in 1,486.40 s; coverage TOTAL 95 % |
| R08 `cargo audit` | **1** | 5 vulnerabilities (`quinn-proto 0.11.16`), 3 allowed warnings — unchanged, not actioned |
| G18 / G17 gitleaks (staged / full history) | 0 / 0 | no leaks; 725 commits |

So the full local suite **is** green on the final candidate, with the same code that was red in Phase A
on two host-sensitive tests (PD-1). `cargo audit` is **not** green. A post-gate delta check
(`git diff --cached --check` and gitleaks on the staged set, after the gate logs were added) is in
`gate-final/` as well.

**Hosted (Plan amendment #50; additional evidence only)** for the module commit `3731fc2`: snyk push
`38428373413`, snyk PR `38428378082`, parity `38428377998`, repro `38428378382`, **python
`38428378236`** (all ten jobs, including `lint` — the first hosted validation of the module under
DV-040 — and the six test legs on ubuntu and windows) and gpu `38428378008` **success**; rust
`38428378271` **failure in exactly one job, `audit`** (the same advisories; every other rust job
succeeded). The hosted runs of the commit that carries this record cannot be written here.

**DV-040 re-audit.** The new module is covered non-vacuously by every option (a) leg, locally and in the
hosted lint job (`EVIDENCE/0162/verification/dv040/`). DV-040 stays CLOSED, with a dated disposition
appended to its register row.

## Handoff to E5

E5 (0163) is READY. It must: (1) verify the retained publication bytes under
`DOCS/test_and_benchmark_results/EXP-002/<run-id>/publication/` against the raw digests manifested in
each `reproduction.json` **before** anything else, then reconstruct from a clean checkout (§8.2, §11.3
item 2), recording any reconstruction difference as a limitation, never as a new H3/H4 observation;
(2) regenerate the seven outputs with this module at `3731fc2` and match `report-manifest.json`
(`6b15dcc1…68781`); (3) report H1–H4 with H3 under both policies, the D1 flag and every disclosure above
in full, obtain the maintainer's verification, and then block the successor under campaign plan §10.4.
