# Session 0154 — EXP-001 / C1 E1: Pre-registration — Golden-trajectory numerical parity

**Status:** COMPLETE  
**Roadmap phase:** 7 — Experimentation campaign and stable release  
**Execution unit:** EXP-001 / C1  
**Session type:** E1 — Pre-registration  
**Predecessor:** [0153 — Campaign planning](0153-campaign-e0-planning.md)  
**Successor:** [0155 — Review and approval](0155-exp001-e2-golden-trajectory-numerical-parity.md)  
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

- Campaign plan is approved; predecessor report/correction cycle is closed.
- No result from this experiment has been inspected.

## Expected work — pre-registration only

1. Create `DOCS/experiments/EXP-001-golden-trajectory-numerical-parity/preregistration.md` from the template.
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
