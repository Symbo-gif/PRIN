# Session 0173 — EXP-004 / C2 E5: Report — GPU kernels and Torch bridge performance

**Status:** PLANNED  
**Roadmap phase:** 7 — Experimentation campaign and stable release  
**Execution unit:** EXP-004 / C2  
**Session type:** E5 — Report  
**Predecessor:** [0172 — Analysis](0172-exp004-e4-gpu-kernels-and-torch-bridge-performance.md)  
**Successor:** [0174 — Pre-registration](0174-exp005-e1-dynamics-chimera-and-capacity-replication.md)  
**Authority:** Project Plan §6/§8; the applicable normative standards. If this brief conflicts with a normative standard, the standard wins.

> This is a prospective execution contract, not completion evidence. Status and
> results belong in Audit Reports, Project State Reports, and experiment artefacts.

## Mission

CUDA/wgpu kernels, N=1M fused RK4, N=16K k-NN, fused discrete step, and trainable bridge overhead.

## Contract

- **Acceptance:** GPU workloads meet or exceed registered 3.0 baselines; training parity is ±10%; bridge overhead <5% with correctness intact.
- **Non-goals:** Any non-pre-registered analysis may appear only as explicitly exploratory; no silent protocol changes.

## Scientific contract

- **Registered expectation to formalize:** GPU workloads meet or exceed registered 3.0 baselines; training parity is ±10%; bridge overhead <5% with correctness intact.
- **Failure/abort boundary to formalize:** Normative target miss or correctness drift is a D1; unavailable backend, asynchronous timing error, or throttling aborts affected runs.
- **Raw artefact root:** `benchmarks/results/EXP-004/`
- **Record root:** `DOCS/experiments/EXP-004-gpu-kernels-and-torch-bridge-performance/`

## Entry conditions

- Registered analysis is complete and reproducible.

## Expected work — report and adjudication

1. Create `DOCS/experiments/EXP-004-gpu-kernels-and-torch-bridge-performance/report.md` with per-hypothesis CONFIRMED / REFUTED /
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
