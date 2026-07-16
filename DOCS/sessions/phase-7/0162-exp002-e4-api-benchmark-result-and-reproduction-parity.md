# Session 0162 — EXP-002 / C1 E4: Analysis — API, benchmark-result, and reproduction parity

**Status:** PLANNED  
**Roadmap phase:** 7 — Experimentation campaign and stable release  
**Execution unit:** EXP-002 / C1  
**Session type:** E4 — Analysis  
**Predecessor:** [0161 — Execution](0161-exp002-e3-api-benchmark-result-and-reproduction-parity.md)  
**Successor:** [0163 — Report](0163-exp002-e5-api-benchmark-result-and-reproduction-parity.md)  
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

- E3 log closes execution; raw artefacts are immutable and manifest-verified.

## Expected work — registered analysis

1. Execute the frozen analysis plan exactly; calculate registered effect sizes,
   95% CIs, tests, corrections, and hypothesis decision rules.
2. Regenerate all tables/figures deterministically from raw JSON artefacts.
3. Put any unregistered analysis under an explicit `Exploratory` heading; it
   cannot alter confirmatory verdicts.
4. Preserve negative/inconclusive results and quantify protocol deviations and threats.

## Prohibited

Outcome-driven exclusions, new confirmatory tests, HARKing, p-hacking, or raw
artefact mutation.

## Exit gate

Reproducible analysis outputs and manifest are committed; hand off to E5.
