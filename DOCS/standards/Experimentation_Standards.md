# PRIN Experimentation Standards

**Status:** Normative. Governs the comprehensive Experimentation and
Benchmarking Campaign that begins when all roadmap phases are complete
(Development Workflow Standards §3, "Campaign trigger"), and any ad-hoc
scientific experiment run before then. Complements — and never overrides — the
[Benchmarking and Reproducibility Standards](Benchmarking_and_Reproducibility_Standards.md).

---

## 1. Principles

1. **Pre-registration is mandatory.** No experiment executes before its
   pre-registration document — including expected results and failure
   conditions — is committed. Post-hoc hypotheses are labeled exploratory and
   can never be reported as confirmatory.
2. **Failure conditions are declared up front.** Every experiment states, in
   advance, what outcome would falsify the hypothesis, what constitutes an
   invalid run (abort criteria), and what will be reported if the experiment
   fails. Negative results are reported with the same rigor as positive ones.
3. **One experiment, one immutable record.** Pre-registration documents are
   frozen at execution time; deviations from protocol are recorded in the
   report as protocol deviations, never edited into the pre-registration.
4. **Reproducibility is a precondition, not an afterthought.** An experiment
   that cannot be re-run from its artefacts (seeds, config, environment
   capture, code SHA) is invalid regardless of its results.
5. **Claims match evidence.** Every scientific claim in a report traces to a
   stored artefact; effect sizes and uncertainty are always reported alongside
   significance.

## 2. Experiment lifecycle

```
E1 Pre-registration ──► E2 Review/approval ──► E3 Execution ──► E4 Analysis ──► E5 Report
        (frozen)            (maintainer)          (logged)        (per plan)      (archived)
```

### E1 — Pre-registration

Create `DOCS/experiments/EXP-NNN-<slug>/preregistration.md` from
`DOCS/experiments/TEMPLATE_Preregistration.md`. Required sections:

1. **Identification** — EXP ID, title, authors, date, code version (git SHA +
   `prin` version), related plan requirement(s).
2. **Background and motivation** — what question this answers; citations.
3. **Hypotheses** — numbered `H1..Hn`, each falsifiable and quantitative
   (e.g. "H1: PhaseTracker IP ≥ SlotAttention IP + 0.05 on temporal CLEVR-6
   at matched parameter budget").
4. **Expected results** — per hypothesis: predicted direction, predicted
   magnitude (point estimate or range), and the basis for the prediction
   (PRINet 3.0 results, theory, pilot data).
5. **Failure conditions** — per hypothesis: the outcome that falsifies it;
   plus experiment-level **abort criteria** (e.g. NaN guard trips, order
   parameter leaves [0,1], run-time budget exceeded, seed irreproducibility)
   that render a run invalid rather than negative.
6. **Method** — exact configurations: model variants, datasets, N/K/dt
   parameter grids, integrator, backend, hardware, dtype.
7. **Variables and controls** — independent/dependent variables, confounders
   controlled (matched loss/optimizer/augmentation/parameter budgets per the
   fair-training framework), baselines.
8. **Sample plan and statistics** — number of seeds (≥10 for confirmatory
   claims unless justified), statistical tests (Welch t-test, bootstrap CIs
   at 95%), effect-size measure (Cohen's d or Cliff's delta), multiple-
   comparison correction (Holm–Bonferroni when >2 comparisons), and the
   significance threshold (α = 0.05 unless justified).
9. **Analysis plan** — exactly which artefacts, figures, and tables will be
   produced and how each hypothesis will be adjudicated from them.
10. **Resource budget** — expected GPU/CPU hours and storage.

### E2 — Review and approval

- The maintainer reviews for: falsifiability, statistical adequacy, fair
  baselines, and resource sanity. Approval is recorded in the
  pre-registration header (name + date).
- Unapproved experiments do not execute. Amendments before execution are
  normal edits; after execution starts, the pre-registration is **frozen**.

### E3 — Execution

- Run through `benchrunner`/experiment drivers only — no unversioned scripts.
- Every run captures the full environment per the Benchmarking Standards §1.4
  (versions, SHA, hardware, backend, dtype, seed) into the run's JSON
  artefacts under `benchmarks/results/EXP-NNN/`.
- An execution log (`DOCS/experiments/EXP-NNN-<slug>/log.md`) records start/
  end times, operator, anomalies, and any abort-criterion trips.
- Aborted runs are recorded, never deleted; re-runs get new run IDs.

### E4 — Analysis

- Follow the pre-registered analysis plan exactly. Additional analyses are
  permitted but reported under an explicit "Exploratory" heading.
- Analysis code is committed; figures/tables regenerate deterministically from
  stored artefacts via `prin.reporting` (SHA-256 manifest).

### E5 — Report

Create `DOCS/experiments/EXP-NNN-<slug>/report.md`. Required sections:
summary verdict per hypothesis (`CONFIRMED | REFUTED | INCONCLUSIVE`, with
effect size and CI), results vs the pre-registered expectations (including a
side-by-side expected-vs-observed table), protocol deviations, exploratory
findings, threats to validity, and artefact index. Reports are announced in
the next Project State Report and linked from the CHANGELOG when they affect
public claims.

## 3. The Experimentation and Benchmarking Campaign

The terminal campaign (roadmap Phase 7) consists of, at minimum:

| Track | Contents | Baseline for comparison |
|---|---|---|
| C1 Parity | Full golden-corpus + benchmark-result parity vs PRINet 3.0 (Parity Report input) | PRINet 3.0.0 artefacts |
| C2 Performance | All Benchmarking Standards §2.4 targets, all backends and platforms | 3.0 Triton/CUDA + torch CPU |
| C3 Scientific replication | Chimera phase diagrams, capacity analyses, MOT/IP studies, ablation orderings, adversarial robustness | Published 3.0 figures/tables |
| C4 New capability | Anything PRIN enables beyond 3.0 (e.g. 1M-oscillator CPU runs, Metal backend) | Pre-registered predictions |

Campaign rules:

- Every track item is one or more pre-registered experiments (E1–E5).
- The campaign plan (ordered experiment list with dependencies) is itself an
  artefact: `DOCS/experiments/campaign-plan.md`, approved before the first
  campaign experiment starts.
- C1–C3 failure conditions include "scientific conclusion differs from
  PRINet 3.0" — any such outcome is a D1 trajectory breach feeding back into
  the Session Cycle (audit → remediation), not a publishable novelty.
- The campaign closes with the published Parity Report plus a campaign
  summary report; both are Definition-of-Done items.

## 4. Scientific integrity rules

- No cherry-picking: all pre-registered runs are reported; excluded runs
  require a pre-registered abort criterion as justification.
- No HARKing (hypothesizing after results are known); no p-hacking (the
  sample plan fixes seeds and tests in advance).
- Data/artefact immutability: raw JSON artefacts are append-only; corrections
  happen by re-running with a new run ID.
- Authorship and AI assistance: reports state which analyses were drafted by
  the AI pair and verified by the maintainer.
- Errata: if a published claim is later invalidated, an erratum is added to
  the experiment report and the Parity Report, and the CHANGELOG notes it.
