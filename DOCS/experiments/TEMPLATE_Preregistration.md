# Pre-registration — EXP-NNN: <title>

**Status:** DRAFT | APPROVED (frozen at execution start)
**Authors:** <maintainer; AI pair (Cascade)>
**Date:** YYYY-MM-DD
**Maintainer approval:** <name / date>  ← required before execution (E2)
**Code version:** prin <version> @ <git SHA>
**Session briefs:** <E1 global ID> through <E5 global ID>
**Related plan items:** <Plan §… / campaign track C1–C4>

---

## 1. Background and motivation

<question this experiment answers; citations to paper/3.0 results>

## 2. Hypotheses (falsifiable, quantitative)

- **H1:** <e.g. "PhaseTracker IP ≥ SlotAttention IP + 0.05 on temporal
  CLEVR-6 at matched parameter budget (±10%)">
- **H2:** …

## 3. Expected results

| Hypothesis | Predicted direction | Predicted magnitude | Basis for prediction |
|---|---|---|---|
| H1 | | | PRINet 3.0 Table N / theory / pilot |

## 4. Failure conditions

**Falsification (per hypothesis):**

| Hypothesis | Outcome that refutes it |
|---|---|
| H1 | |

**Abort criteria (invalid run, not a negative result):**

- <e.g. NaN/Inf guard trip; order parameter outside [0,1]; seed
  irreproducibility on re-run; runtime > X h; hardware thermal throttling>

**Reporting commitment on failure:** results are reported in full per
Experimentation Standards §1.2 regardless of outcome.

## 5. Method

- **Configurations:** <models/variants, N, K, dt, integrator, coupling,
  backend, dtype, hardware>
- **Datasets:** <name, version, split, caching>
- **Procedure:** <exact steps; benchrunner invocations>

## 6. Variables and controls

- **Independent:** …
- **Dependent:** …
- **Controlled/confounders:** <matched loss/optimizer/augmentation/parameter
  budgets; identical seeds across arms; same hardware>
- **Baselines:** …

## 7. Sample plan and statistics

- **Seeds:** <n ≥ 10 for confirmatory; list or generation rule>
- **Tests:** <Welch t-test / bootstrap 95% CI (n resamples)>
- **Effect size:** <Cohen's d / Cliff's delta>
- **Multiple comparisons:** <Holm–Bonferroni across … comparisons>
- **α:** 0.05 <or justified alternative>

## 8. Analysis plan

<exact artefacts, figures, tables to be produced; the decision rule mapping
statistics → CONFIRMED / REFUTED / INCONCLUSIVE per hypothesis>

## 9. Resource budget

<GPU/CPU hours, storage, wall-clock estimate>
