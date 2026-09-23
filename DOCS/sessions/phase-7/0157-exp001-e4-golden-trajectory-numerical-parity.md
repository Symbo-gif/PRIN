# Session 0157 — EXP-001 / C1 E4: Analysis — Golden-trajectory numerical parity

**Status:** COMPLETE  
**Roadmap phase:** 7 — Experimentation campaign and stable release  
**Execution unit:** EXP-001 / C1  
**Session type:** E4 — Analysis  
**Predecessor:** [0156 — Execution](0156-exp001-e3-golden-trajectory-numerical-parity.md)  
**Successor:** [0158 — Report](0158-exp001-e5-golden-trajectory-numerical-parity.md)  
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
