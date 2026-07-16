# Session 0190 — EXP-008 / C4 E2: Review and approval — Cross-platform and new-capability characterization

**Status:** PLANNED  
**Roadmap phase:** 7 — Experimentation campaign and stable release  
**Execution unit:** EXP-008 / C4  
**Session type:** E2 — Review and approval  
**Predecessor:** [0189 — Pre-registration](0189-exp008-e1-cross-platform-and-new-capability-characterization.md)  
**Successor:** [0191 — Execution](0191-exp008-e3-cross-platform-and-new-capability-characterization.md)  
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
