# Session 0165 — EXP-003 / C2 E2: Review and approval — CPU scaling and sweep performance

**Status:** PLANNED  
**Roadmap phase:** 7 — Experimentation campaign and stable release  
**Execution unit:** EXP-003 / C2  
**Session type:** E2 — Review and approval  
**Predecessor:** [0164 — Pre-registration](0164-exp003-e1-cpu-scaling-and-sweep-performance.md)  
**Successor:** [0166 — Execution](0166-exp003-e3-cpu-scaling-and-sweep-performance.md)  
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
