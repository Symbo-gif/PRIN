# Session 0158 — EXP-001 / C1 E5: Report — Golden-trajectory numerical parity

**Status:** PLANNED  
**Roadmap phase:** 7 — Experimentation campaign and stable release  
**Execution unit:** EXP-001 / C1  
**Session type:** E5 — Report  
**Predecessor:** [0157 — Analysis](0157-exp001-e4-golden-trajectory-numerical-parity.md)  
**Successor:** [0159 — Pre-registration](0159-exp002-e1-api-benchmark-result-and-reproduction-parity.md)  
**Authority:** Project Plan §6/§8; the applicable normative standards. If this brief conflicts with a normative standard, the standard wins.

> This is a prospective execution contract, not completion evidence. Status and
> results belong in Audit Reports, Project State Reports, and experiment artefacts.

## Mission

Full corpus and hypothesis-fuzzed trajectory/metric/decomposition parity across supported CPU and accelerated paths.

## Contract

- **Acceptance:** All non-chaotic cases satisfy registered tolerances; chaotic cases preserve registered distributional conclusions; bit-level seeded repeatability holds.
- **Non-goals:** Any non-pre-registered analysis may appear only as explicitly exploratory; no silent protocol changes.

## Scientific contract

- **Registered expectation to formalize:** All non-chaotic cases satisfy registered tolerances; chaotic cases preserve registered distributional conclusions; bit-level seeded repeatability holds.
- **Failure/abort boundary to formalize:** Any unexplained tolerance breach, invariant violation, or cross-run seed mismatch is a D1; environment/schema/manifest failure aborts a run.
- **Raw artefact root:** `benchmarks/results/EXP-001/`
- **Record root:** `DOCS/experiments/EXP-001-golden-trajectory-numerical-parity/`

## Entry conditions

- Registered analysis is complete and reproducible.

## Expected work — report and adjudication

1. Create `DOCS/experiments/EXP-001-golden-trajectory-numerical-parity/report.md` with per-hypothesis CONFIRMED / REFUTED /
   INCONCLUSIVE verdict, effect size, CI, and exact evidence link.
2. Include side-by-side expected-vs-observed results, all aborts/exclusions,
   protocol deviations, exploratory findings, threats to validity, AI-assistance
   disclosure, and complete artefact index.
3. Trigger and close a D1 correction cycle before proceeding if a C1–C3
   published conclusion or any normative requirement is contradicted.
4. Obtain maintainer verification and announce the report for campaign synthesis.

## Prohibited

Spin, omitted runs, conclusion inflation, or proceeding with an unresolved D1.

## Exit gate

Approved report and any required correction-cycle evidence are committed; the
next registered experiment may begin.
