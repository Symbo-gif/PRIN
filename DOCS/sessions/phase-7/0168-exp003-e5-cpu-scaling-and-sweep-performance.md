# Session 0168 — EXP-003 / C2 E5: Report — CPU scaling and sweep performance

**Status:** PLANNED  
**Roadmap phase:** 7 — Experimentation campaign and stable release  
**Execution unit:** EXP-003 / C2  
**Session type:** E5 — Report  
**Predecessor:** [0167 — Analysis](0167-exp003-e4-cpu-scaling-and-sweep-performance.md)  
**Successor:** [0169 — Pre-registration](0169-exp004-e1-gpu-kernels-and-torch-bridge-performance.md)  
**Authority:** Project Plan §6/§8; the applicable normative standards. If this brief conflicts with a normative standard, the standard wins.

> This is a prospective execution contract, not completion evidence. Status and
> results belong in Audit Reports, Project State Reports, and experiment artefacts.

## Mission

CPU SIMD/rayon dynamics, simulation scaling through N=1M, and 16-core sweep throughput against 3.0 PyTorch.

## Contract

- **Acceptance:** Eligible CPU kernels achieve ≥2× and parameter sweeps ≥8× on controlled same-hardware comparisons without parity loss.
- **Non-goals:** Any non-pre-registered analysis may appear only as explicitly exploratory; no silent protocol changes.

## Scientific contract

- **Registered expectation to formalize:** Eligible CPU kernels achieve ≥2× and parameter sweeps ≥8× on controlled same-hardware comparisons without parity loss.
- **Failure/abort boundary to formalize:** Failure of a normative N1 target is a D1 unless amended; thermal throttling, background load, or parity failure aborts timing.
- **Raw artefact root:** `benchmarks/results/EXP-003/`
- **Record root:** `DOCS/experiments/EXP-003-cpu-scaling-and-sweep-performance/`

## Entry conditions

- Registered analysis is complete and reproducible.

## Expected work — report and adjudication

1. Create `DOCS/experiments/EXP-003-cpu-scaling-and-sweep-performance/report.md` with per-hypothesis CONFIRMED / REFUTED /
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
