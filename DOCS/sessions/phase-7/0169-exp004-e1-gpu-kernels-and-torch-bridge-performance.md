# Session 0169 — EXP-004 / C2 E1: Pre-registration — GPU kernels and Torch bridge performance

**Status:** PLANNED  
**Roadmap phase:** 7 — Experimentation campaign and stable release  
**Execution unit:** EXP-004 / C2  
**Session type:** E1 — Pre-registration  
**Predecessor:** [0168 — Report](0168-exp003-e5-cpu-scaling-and-sweep-performance.md)  
**Successor:** [0170 — Review and approval](0170-exp004-e2-gpu-kernels-and-torch-bridge-performance.md)  
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

- Campaign plan is approved; predecessor report/correction cycle is closed.
- No result from this experiment has been inspected.

## Expected work — pre-registration only

1. Create `DOCS/experiments/EXP-004-gpu-kernels-and-torch-bridge-performance/preregistration.md` from the template.
2. State quantitative, falsifiable H1…Hn; expected direction, magnitude/range,
   and basis independently for each hypothesis.
3. Convert the registered expectation and failure boundary above into exact
   decision rules, abort criteria, controls, sample/seed plan, alpha, effect
   sizes, CIs, multiple-comparison correction, analysis code/outputs, and budget.
4. Distinguish negative results from invalid/aborted runs and define how both are reported.

## Prohibited

No experiment execution, pilot outcome inspection, post-hoc hypothesis, or
analysis selected after seeing results.

## Exit gate

A complete DRAFT pre-registration is committed and handed to E2.
