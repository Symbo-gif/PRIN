# Session 0159 — EXP-002 / C1 E1: Pre-registration — API, benchmark-result, and reproduction parity

**Status:** BLOCKED — EXP-001 raised a campaign plan §10.4 D1 at E5
(session 0158); this session is released only after the four contingency
correction sessions close and `EXP-001-r1` returns a non-reversal verdict
(campaign plan §3.3, §10.4 items 2–5)  
**Roadmap phase:** 7 — Experimentation campaign and stable release  
**Execution unit:** EXP-002 / C1  
**Session type:** E1 — Pre-registration  
**Predecessor:** [0158 — Report](0158-exp001-e5-golden-trajectory-numerical-parity.md)  
**Successor:** [0160 — Review and approval](0160-exp002-e2-api-benchmark-result-and-reproduction-parity.md)  
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

- Campaign plan is approved; predecessor report/correction cycle is closed.
- No result from this experiment has been inspected.

## Expected work — pre-registration only

1. Create `DOCS/experiments/EXP-002-api-benchmark-result-and-reproduction-parity/preregistration.md` from the template.
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
