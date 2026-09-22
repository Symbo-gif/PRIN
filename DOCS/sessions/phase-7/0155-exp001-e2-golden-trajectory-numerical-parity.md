# Session 0155 — EXP-001 / C1 E2: Review and approval — Golden-trajectory numerical parity

**Status:** COMPLETE  
**Roadmap phase:** 7 — Experimentation campaign and stable release  
**Execution unit:** EXP-001 / C1  
**Session type:** E2 — Review and approval  
**Predecessor:** [0154 — Pre-registration](0154-exp001-e1-golden-trajectory-numerical-parity.md)  
**Successor:** [0156 — Execution](0156-exp001-e3-golden-trajectory-numerical-parity.md)  
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
