# Session 0193 — EXP-008 / C4 E5: Report — Cross-platform and new-capability characterization

**Status:** PLANNED  
**Roadmap phase:** 7 — Experimentation campaign and stable release  
**Execution unit:** EXP-008 / C4  
**Session type:** E5 — Report  
**Predecessor:** [0192 — Analysis](0192-exp008-e4-cross-platform-and-new-capability-characterization.md)  
**Successor:** [0194 — Campaign synthesis](0194-campaign-e6-synthesis.md)  
**Authority:** Project Plan §6/§8; the applicable normative standards. If this brief conflicts with a normative standard, the standard wins.

> This is a prospective execution contract, not completion evidence. Status and
> results belong in Audit Reports, Project State Reports, and experiment artefacts.

## Mission

Characterize Metal/wgpu, DirectML/VitisAI, compiler-free wheels, and expanded large-scale PRIN capabilities unavailable in 3.0.

## Contract

- **Acceptance:** Pre-registered capability-specific predictions hold with parity-safe behavior; platform support satisfies N2/N4/F5.
- **Non-goals:** Any non-pre-registered analysis may appear only as explicitly exploratory; no silent protocol changes.

## Scientific contract

- **Registered expectation to formalize:** Pre-registered capability-specific predictions hold with parity-safe behavior; platform support satisfies N2/N4/F5.
- **Failure/abort boundary to formalize:** Violation of N2/N4/F5 is D1; new-capability hypothesis misses are reported negative unless they breach a normative requirement; unavailable hardware is inconclusive, not silently skipped.
- **Raw artefact root:** `benchmarks/results/EXP-008/`
- **Record root:** `DOCS/experiments/EXP-008-cross-platform-and-new-capability-characterization/`

## Entry conditions

- Registered analysis is complete and reproducible.

## Expected work — report and adjudication

1. Create `DOCS/experiments/EXP-008-cross-platform-and-new-capability-characterization/report.md` with per-hypothesis CONFIRMED / REFUTED /
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
