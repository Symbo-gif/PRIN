# Session 0163 — EXP-002 / C1 E5: Report — API, benchmark-result, and reproduction parity

**Status:** PLANNED  
**Roadmap phase:** 7 — Experimentation campaign and stable release  
**Execution unit:** EXP-002 / C1  
**Session type:** E5 — Report  
**Predecessor:** [0162 — Analysis](0162-exp002-e4-api-benchmark-result-and-reproduction-parity.md)  
**Successor:** [0164 — Pre-registration](0164-exp003-e1-cpu-scaling-and-sweep-performance.md)  
**Authority:** Project Plan §6/§8; the applicable normative standards. If this brief conflicts with a normative standard, the standard wins.

> This is a prospective execution contract, not completion evidence. Status and
> results belong in Audit Reports, Project State Reports, and experiment artefacts.

## Mission

Public API mapping, legacy benchmark conclusion equivalence, and byte-comparable figure/table regeneration.

## Contract

- **Acceptance:** 175+ mapped symbols pass; all historical scientific conclusion orderings remain unchanged; 15 figures/11 tables match the manifest.
- **Non-goals:** Any non-pre-registered analysis may appear only as explicitly exploratory; no silent protocol changes.

## Scientific contract

- **Registered expectation to formalize:** 175+ mapped symbols pass; all historical scientific conclusion orderings remain unchanged; 15 figures/11 tables match the manifest.
- **Failure/abort boundary to formalize:** Missing symbols, changed scientific conclusions, or unexplained artefact mismatch is a D1; corrupt source artefacts abort.
- **Raw artefact root:** `benchmarks/results/EXP-002/`
- **Record root:** `DOCS/experiments/EXP-002-api-benchmark-result-and-reproduction-parity/`

## Entry conditions

- Registered analysis is complete and reproducible.

## Expected work — report and adjudication

1. Create `DOCS/experiments/EXP-002-api-benchmark-result-and-reproduction-parity/report.md` with per-hypothesis CONFIRMED / REFUTED /
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
