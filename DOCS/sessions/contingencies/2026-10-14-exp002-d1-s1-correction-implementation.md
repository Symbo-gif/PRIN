# EXP-002 D1 S1 — Correction implementation

**Status:** COMPLETE (S1, 2026-10-15 UTC; pushed to draft PR #34 as authorized) — scope approved 2026-10-15 UTC (see "Approved scope and decisions"); S2 is next
**Triggering deviation:** `EXP-002 H3 REFUTED` (campaign plan §10.4 D1; pre-registration §4.3)
**Blocked numbered session:** `0164` (EXP-003 E1), and every later campaign session (`0165`–`0194`, per campaign plan §3.3 and §10.4 items 2 and 5)
**Opened by:** session `0163` (EXP-002 E5), 2026-10-14 UTC
**Governing record:** [EXP-002 E5 report](../../experiments/EXP-002-api-benchmark-result-and-reproduction-parity/report.md) §§3, 6, 8, 11, 14; [E4 analysis](../../experiments/EXP-002-api-benchmark-result-and-reproduction-parity/analysis.md); [E3 log](../../experiments/EXP-002-api-benchmark-result-and-reproduction-parity/log.md); [pre-registration](../../experiments/EXP-002-api-benchmark-result-and-reproduction-parity/preregistration.md); [E2 review](../../experiments/EXP-002-api-benchmark-result-and-reproduction-parity/e2-review.md); [`report-manifest.json`](../../experiments/EXP-002-api-benchmark-result-and-reproduction-parity/report-manifest.json)

## Expectation

Declare a correction WP scoped only to the triggering deviation; reproduce it with a failing regression/parity test, implement the root-cause fix with tests in tandem, and run all affected gates.

## Exit evidence

Record commands, artefacts, approvals, commits, and handoff in the correction
WP's audit and Project State Report. The blocked session remains blocked until
all four conditional sessions close.

## What triggered this cycle

At EXP-002 E4 (session `0162`) and E5 (session `0163`), applying the frozen decision rules (`preregistration.md` §§4.1, 5.2, 5.4, 5.5, 11.3; freeze commit `F = 9a9889d08dcaf2ad0ce31659ed67721b54b114d0`) to the five admissible, manifest-verified E3 run records at source `R = fae24c4393c7a0232e6c8f0a6388b1775aa5fc05` returned:

- **H1 `CONFIRMED`** (`175/175` `api_symbols` resolved; `172/172` `legacy_api_names` owned; `0` duplicate/removed/unexpected; frozen-contract sets empty).
- **H2 `CONFIRMED`** (`62/62` `claim_comparator_records` agree across `C01`–`C05`).
- **H3 `REFUTED` (approved §5.4 policy, primary — campaign plan §10.4 D1):** both the frozen reference generator (`prinet` 3.0.0) and PRIN (`tools.reproduce.run_reproduction`) produced all `39/39` registered `generated_files` (`0` missing, `0` extra), and all `11/11` `.tex` tables matched between the arms and against the `11/11` archived tables, plus `5/14` figures (`10` files: `fig2_clevr_n_capacity`, `fig3_chimera_metrics`, `fig4_chimera_k_alpha_heatmap`, `fig6_oscillosim_scaling`, `fig13_representation_geometry`) matched in both `.pdf` and `.png`. However, **`18/39` `generated_files` differed** — both the `.pdf` and `.png` of `9/14` figures (`fig5_mot_occlusion_comparison`, `fig7_ablation_results`, `fig8_parameter_efficiency`, `fig9_training_curves`, `fig10_statistical_summary`, `fig11_flops_scaling`, `fig12_supercritical_regime`, `fig14_gradient_flow`, `fig15_noise_velocity`).
- **H3 `REFUTED` (§11.3 sensitivity policy):** `5/39` `generated_files` equal, `34/39` differ. The two policies agree, so H3's refutation does not depend on the post-exposure amendment.
- **H4 `CONFIRMED`** (`39/39` `generated_files` raw-byte-identical between the two separate PRIN processes; canonical projections equal; E5 reconstruction also reproduced `39/39` PRIN-arm raw files byte-identically).

**No root cause is claimed by E3, E4, or E5.** Establishing the root cause of the 9-figure (`18`-file) divergence is this S1 session's work. Neither PRIN nor the PRINet 3.0 reference generator has been declared erroneous.

## Scope (approved by the maintainer 2026-10-15 UTC — see "Approved scope and decisions")

In scope:

- **Reproduce the refutation first** with a committed failing regression/parity test before any fix lands (Development Workflow §3; Testing Standards §1.3), exercising the 9 differing figure stems (`18` files) under the registered comparison rules.
- **Determine and fix the root cause** of the divergence between `python/prin/reporting/figure_generation.py` and the frozen reference `src/prinet/utils/figure_generation.py`, **or** establish under campaign plan §10.4 item 3 whether any part of the PRINet 3.0 reference generator is itself the defective side — which requires an EMA-style mathematical audit claim, Z3/SymPy-verified where applicable, and is **not** discharged by visual inspection or post-hoc reinterpretation. (Nothing in this brief asserts which side is defective.)
- Add regression tests in tandem ensuring the 9 figure stems (and all 39 publication outputs) pass on the post-fix tree.
- Follow Coding Standards §5 and §6: Snyk Code on all new or modified first-party source; Snyk Open Source and ecosystem-native audits (`cargo audit`, `pip-audit`) if any dependency or lockfile is touched; full local gate (`ruff`, `ruff format`, `mypy --strict`, `interrogate`, `bandit`, pytest fast and full suites with `--basetemp=.pytest_basetemp`, `cargo`, Sphinx clean build, `gitleaks`).

Out of scope (explicitly, to keep the correction bounded):

- Any edit, deletion, or re-manifesting of `EXP-002`'s frozen `preregistration.md`, `e2-review.md`, `log.md`, `analysis/exp002_e4_analysis.py`, `analysis.md`, `report.md` (except dated errata appended at S4), `report-manifest.json`, or any raw run directory under `benchmarks/results/EXP-002/RUN-*`. The `EXP-002` record is immutable and stays as issued (campaign plan §10.4 item 4).
- Any campaign experiment execution. After S4 closes, the experiment is re-run as a new record **`EXP-002-r1`** with a new pre-registration (E1) and new `RUN-` directories; `EXP-002-r1` is authorized at S4, not here.
- Any unrelated performance, feature, or refactoring work.

## Acceptance

- The H3 refutation is reproduced by a committed failing test **before** the fix.
- Root cause of all 9 differing figure stems (`18` files) is identified with evidence, or the campaign plan §10.4 item 3 alternative is established to its own stricter EMA mathematical-audit standard.
- All affected gates pass locally under the Plan amendment #48 local-validation regime.
- Neither S1 completion nor a green local gate authorizes `EXP-002-r1` or releases session `0164`; S2, S3, and S4 must close in order first, followed by a non-reversal `EXP-002-r1` E5 report (or a Project Plan §8.3 amendment; campaign plan §10.4 items 3–5).

## Approved scope and decisions

MichaelMaillet, 2026-10-15 UTC, in answer to the E5 close-out questions
(verbatim: "approve correction cycle scope"; recorded in
`EVIDENCE/0163/verification/acceptance/maintainer-decisions-2026-10-15.md`).
The scope above is **approved as written**; no refinements were stated.

Related decisions recorded at the same time:

- The `DOCS/test_and_benchmark_results/EXP-002/RUN-*/{inputs,publication}`
  retained roots stay on disk until this S1 completes, so the exact
  E3-rendered bytes are available to the failing-test reproduction.
- `cargo audit` (`quinn-proto`/`rustls`), the `gpu-cuda` `flops` test, and the
  stale `python/prin/_prin_core.pyd` are **not** folded into this scope: they
  are dispositioned as dated DV register rows `DV-045`/`DV-046`/`DV-047` under
  established governance, for a dedicated hotfix or a maintainer-authorized
  session. Any pull of those items into S1 would itself need an explicit
  maintainer scope extension.
- **Push and draft PR pre-authorized** (MichaelMaillet, 2026-10-15 UTC, in
  the instruction that started this S1 session; mirrors the 2026-09-23
  EXP-001 S1 brief's approved decision 3). The hotfix branch
  `hotfix/exp002-d1-figure-parity` is created from `origin/main` @
  `fd8854ed87a21e01f16e2f7128b431e74085a26e` (the PR #33 merge) and pushed,
  and a **draft** PR is opened. The failing-test commit is pushed before the
  fix commit, so the red → green transition is recorded on the remote. The
  seven hosted check workflows are disabled (`gh workflow list --all`:
  `rust`, `python`, `parity`, `repro`, `snyk`, `gpu`, `nightly` all
  `disabled_manually`; the Plan amendment #50 window closed at the PR #33
  merge), so **no hosted check runs** on these pushes; the Windows local gate
  stays authoritative under Plan amendment #48, and a local full-history
  secret scan precedes every push (amendment #48 item 6). Merging stays with
  the maintainer. This authorizes neither a merge, `EXP-002-r1`, nor the
  release of session `0164`.

## Completion and handoff (2026-10-15 UTC)

**Root cause (PRIN side; campaign plan §10.4 item 3 not invoked).** The
WP-034 S1 port (`d88a331`) of the nine PRINet 3.0 figure generators dropped
or re-encoded 34 drawing arguments. These were keyword arguments such as
`markersize`, `linewidth`, `alpha`, `zorder`, `va`, `bbox`, `edgecolor` and
legend `loc`, plus an omitted `tick_params` call. Unicode label strings
(`×`, `³`, δ/θ/γ, en dash) were rewritten as mathtext, in line with `ruff`
`RUF001`. Controlled substitution on the frozen reference shows that these
34, and nothing else, explain every differing byte:

- the reference with all 34 applied equals the pre-fix port on 9/9 stems
  and 18/18 files;
- 26 of the 34 are byte-material alone;
- 0 stems are unexplained.

No plotted value differs and no reference calculation is implicated.

**Acceptance.**

- [x] H3 refutation reproduced by a committed failing test before the fix:
  `parity/test_parity_publication.py` at `d90eeab`. It failed exactly the
  18 E3 files and was pushed before the fix.
- [x] Root cause of all 9 stems (18 files) evidenced by controlled
  substitution, with 0 unexplained
  (`EVIDENCE/exp002-d1-s1/root-cause-decomposition-prefix.json`).
- [x] Fix with tests in tandem (`10d84f2`). All 39 publication outputs equal
  the frozen reference under the registered H3 comparison. The 21 outputs
  that already matched stay raw-byte-identical to E3, and H4's two-process
  raw identity holds (`root-cause-decomposition-postfix.json`). Nine new
  fast-gate tests fail on the pre-fix module and pass after the fix.
- [x] Affected local gates, under Plan amendment #48, on `af89499`:
  - Green: ruff, ruff format, `mypy --strict`, interrogate, bandit, the four
    governance checkers, the Sphinx `-W` clean build, `cargo fmt`, `cargo
    clippy`, gitleaks (history and staged), and Snyk Code (0 findings in
    changed files).
  - The fast and full pytest suites both **exited 1**: 4,037 passed with 1
    failure, and 6,323 passed with 2 failures. The three failures are in code
    this change does not touch. Two are Windows `WinError 5` file-contention
    errors and one is a load-induced notebook cell timeout. All three pass
    when re-run alone on the same commit.
  - The verbatim record is in
    [`EVIDENCE/exp002-d1-s1/local-gate.txt`](../../../EVIDENCE/exp002-d1-s1/local-gate.txt),
    summarized in the audit record §S1.7. A clean single-pass suite run on
    an idle host is left for S2's reproduction.

**Evidence:**

- reproduction `d90eeab`;
- decomposition `dd05afa`;
- fix `10d84f2`;
- post-fix evidence `9371596`/`10d196c`;
- the [correction audit](../../audits/2026-10-15-exp002-d1-correction-audit.md) S1 record, which covers approvals, root
  cause, commits, the red → green transition, the local gate, out-of-scope
  observations and the S2 handoff;
- [`EVIDENCE/exp002-d1-s1/`](../../../EVIDENCE/exp002-d1-s1/README.md).

**Records not changed by S1.** The Project State Report, its cumulative
deviation ledger and the Parity Report stay as they are. Under the
`DOCS/reports/README.md` rule (one report per closed cycle, written in S4,
append-only), S4 issues the next PSR, which carries this cycle's ledger row;
the S4 brief also assigns it the Parity Report alignment.

**Handoff.** S2
([brief](2026-10-14-exp002-d1-s2-correction-audit.md)) audits `ab9e422..HEAD`
read-only. S1 completion releases nothing: merging PR #34 stays with the
maintainer, `EXP-002-r1` is authorized only at S4, and session `0164` stays
`BLOCKED`.
