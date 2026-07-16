# Session 0170 — EXP-004 / C2 E2: Review and approval — GPU kernels and Torch bridge performance

**Status:** PLANNED  
**Roadmap phase:** 7 — Experimentation campaign and stable release  
**Execution unit:** EXP-004 / C2  
**Session type:** E2 — Review and approval  
**Predecessor:** [0169 — Pre-registration](0169-exp004-e1-gpu-kernels-and-torch-bridge-performance.md)  
**Successor:** [0171 — Execution](0171-exp004-e3-gpu-kernels-and-torch-bridge-performance.md)  
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

- E1 draft is committed; no execution or result inspection has occurred.

## Expected work — independent review

1. Review falsifiability, quantitative decision rules, expected-result basis,
   failure/abort criteria, fairness controls, power/seed count, statistics,
   hardware feasibility, and artefact plan.
2. Resolve review findings before approval; log every pre-execution amendment.
3. Record maintainer name/date and set status APPROVED; freeze content at the
   instant E3 starts.

## Prohibited

Approval with missing expected results/failure conditions, or execution before
signed approval.

## Exit gate

Approved pre-registration is committed and frozen; E3 is authorized.
