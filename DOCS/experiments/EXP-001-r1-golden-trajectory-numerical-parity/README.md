# EXP-001-r1 — Golden-trajectory numerical parity, re-run (track C1)

**Status:** **E5 REPORTED 2026-09-29 UTC — ALL FIVE HYPOTHESES `CONFIRMED`,
CAMPAIGN PLAN §10.4 D1 FLAG NOT RAISED; MAINTAINER VERIFICATION PENDING.**
[`report.md`](report.md) is issued and §10.4 item 5's **non-reversal**
condition is satisfied, so no correction cycle is triggered. The release of
session 0159, EXP-002 … EXP-008 and 0194 takes effect on the maintainer's
verification recorded in [`report.md`](report.md) §13 — E5's exit gate — and is
**not in force until then**.
**E4 ANALYSED 2026-09-29 UTC.** E4 applied the
frozen §8 decision rule to the six immutable E3 artefacts and detected **no
conclusion reversal** ([`analysis.md`](analysis.md)). H1 504/504 accepted (485
native-parity + 19 explained-dv007, zero unexplained breaches); H2a
**978 pointwise + 22 characterized**; H2b both metrics' 95 % CIs strictly
inside their margins on 657 contributors each; H3 14/14 byte-identical in both
invocations with identical separate-run projections; H4 72/72 on **each** of
CUDA and wgpu with zero failed derivative elements. Nothing aborted.
**E3 EXECUTED 2026-09-29 UTC — PRE-REGISTRATION FROZEN.** The
pre-registration froze at its first `RUN-` creation on
2026-09-29T09:17:35Z at `F = 5d5ae3521317af47a11afa8d689935ac2fc0f447`. All
six registered runs then executed from the clean campaign execution checkout
`R = 5d5ae35…` on the green-main baseline
`M = 9b79d2e5b246bead1243074659dc99d049762a40`: 72-case wgpu kernel-path,
72-case CUDA kernel-path, 504-case corpus, 2× 14-case repeatability and the
1,000-draw fuzz leg — zero aborts, every directory manifested
([`log.md`](log.md)). E3 computed no verdict by design; the verdicts above come
only from E4's application of the frozen §8 rule.
Every §10 entry gate closed before execution. Independent review
(Claude Sonnet 5) verified every E1 provenance/machinery claim against the
repository; the maintainer approved the sample-size justification, the H2b
three-way rule and the storage budget (campaign plan §14.2 amendment #7), and
approved the wgpu H4 companion method and two-build order as a follow-up E2
method decision on 2026-09-29 UTC ([`e2-review.md`](e2-review.md) §8). DV-041
is **CLOSED** on documented merge evidence (PR #25, `5615eda`, required CI
green per `triage-dv043-handoff.md` §2); DV-043 is **CLOSED** (merged `main`
`9b79d2e`, required CI green, forced nightly `36525353031` attempt-2
`bench-regression` green); DV-044's governed ledger correction is **CLOSED**
(S1–S4, hosted governance gate green). See
[`e2-review.md`](e2-review.md) §§5–8.
This is a new experiment record per campaign plan §10.4 item 4. The original
EXP-001 record is immutable; corrections to it are errata. **E4 does not
revise EXP-001's own `REFUTED` verdicts** — r1 is a new record on new runs.
**Predecessor:** [`EXP-001`](../EXP-001-golden-trajectory-numerical-parity/README.md)
(E5 reported 2026-09-23; H1/H2a `REFUTED`, D1 raised).
**Correction cycle:** [`DOCS/audits/2026-09-24-exp001-d1-correction-audit.md`](../../audits/2026-09-24-exp001-d1-correction-audit.md)
(S1 complete, S2 PASS, S3 CLEAN, S4 complete).
**Campaign plan row:** [`campaign-plan.md`](../campaign-plan.md) §2.1 EXP-001 / C1.

The maintainer declared the E1 and E2 sessions, then declared E3, E4 and E5 as
separate sessions in turn — campaign plan §12 rule 2 allows one E-stage per
session, and the r1 stages carry no integer session number, so the register's
next numbered session (0159) is unaffected by them; each stage commits on its
own `campaign/exp001-r1-<stage>` branch per §12 rule 3. The
[pre-registration](preregistration.md), [E1 handoff](e1-handoff.md),
[E2 review](e2-review.md), [E3 log](log.md), [E4 analysis record](analysis.md)
and [E5 report](report.md) record the prospective protocol, local validation,
independent re-verification, the maintainer's E2 decisions, the execution, the
adjudication and the report. Because every §10 entry gate had closed, the first
`RUN-` creation on `R` froze the record and E3 ran to completion; the
pre-registration is never edited after that point. Neither E1, the E2 method
approvals, E3's execution nor E4's clean exit released session 0159: the block
lifts only on a non-reversal E5 verdict or a Project Plan §8.3 amendment
(campaign plan §10.4 item 5).

## What this directory holds

| File | Created by | Frozen when |
|---|---|---|
| `README.md` | E1 | Updated as the experiment progresses |
| [`preregistration.md`](preregistration.md) | E1 (from [`TEMPLATE_Preregistration.md`](../TEMPLATE_Preregistration.md)) | **FROZEN 2026-09-29T09:17:35Z** at `F = 5d5ae3521317af47a11afa8d689935ac2fc0f447` (first `RUN-` created); E2 follow-up H4 method approved 2026-09-29 UTC; executed from `R = 5d5ae35…` on baseline `M = 9b79d2e…` — never edited after freeze |
| [`e1-handoff.md`](e1-handoff.md) | E1 | Entry and verification evidence record |
| [`e2-review.md`](e2-review.md) | E2 | Independent-review and maintainer-decision record |
| [`log.md`](log.md) | E3 | **written** — 6/6 registered runs executed 2026-09-29 (one wgpu + one CUDA kernel-path, corpus, 2× repeatability, fuzz), 0 aborted, all manifested; never edited after E3 close |
| [`analysis/`](analysis/README.md) | E4 | Committed **before** adjudication (campaign plan §7.4 item 2). Never edited to change a verdict; a needed fix is a new commit recorded in `analysis.md` |
| [`analysis.md`](analysis.md) | E4 | **written** — all five hypotheses `CONFIRMED`, D1 flag **not raised** (a non-reversal detection); never edited after E4 close, corrections are errata |
| [`report.md`](report.md) | E5 | **written** — all five hypotheses `CONFIRMED`, D1 not raised, non-reversal; maintainer verification **pending** (§13); never edited after issue, corrections are errata |
| [`report-manifest.json`](report-manifest.json) | E4 | **written** — SHA-256/size of the four regenerated outputs plus every input run manifest; regenerated byte-identically from clean checkouts at `f966921`, `3270699` and `46fea62` |

## Rules inherited from the campaign plan

- This experiment **does not reuse** EXP-001's run IDs or artefacts (campaign
  plan §10.4 item 4).
- Hypotheses, expected results, and failure/abort conditions are committed
  **before** execution (Experimentation Standards §1.1–§1.2).
- Pre-register against the **reconciled** targets in campaign plan §2.1 and
  cite the reconciliation; hardware only from §5; seeds per §6
  (`seed_key = 1`); artefact layout per §7; budget cap per §8;
  statistics per §9; abort/D1 rules per §10.
- Raw artefacts are written only to new `RUN-<UTC>-<SHA>-<label>/` directories
  under `benchmarks/results/EXP-001/` (shared with the original EXP-001; new
  run directories are distinguishable by their own SHA and timestamp) and
  closed with a per-run `manifest.json`.

## Key differences from EXP-001

The correction cycle's S1 established two root causes for EXP-001's H1/H2a
refutations and fixed both:

1. **PRIN's Euler/RK4 guard divergence** — PRIN now defaults to
   `GuardPolicy::NonNegative` (amplitude floor `0.0`, no ceiling; derivative
   clamp only on sparse k-NN paths), matching PRINet 3.0's
   `OscillatorModel._step_euler`/`_step_rk4`. The `Bounded` policy
   (`[1e-6, 10]` amplitude, `±1e4` derivative) is available for OscilloSim
   ports. Plan amendment #47 makes §5.6 path-specific.

2. **DV-007 `complex64` arithmetic** — PRINet 3.0 evaluates Stuart–Landau and
   mean-field derivatives in `complex64` inside a float64 model. The corpus is
   the erroneous side (campaign plan §10.4 item 3, established by 50-digit
   mpmath exactness audit, 67/67 cases). The E1 pre-registration must specify
   how DV-007 cases are registered (explained-divergence clause, float64
   regeneration, or another mechanism).

3. **Ill-conditioned regime** — 22 of H2a's 103 failing cases are
   ill-conditioned: PRINet 3.0's own float64 map breaches the registered
   tolerance under a one-ulp phase change. The E1 pre-registration must
   specify how these cases are handled.

4. **New gates exist** — `parity/test_parity_prin_corpus.py` (504 cases) and
   `parity/test_parity_prin_fuzz.py` (1,000 cases) now run in the `parity` CI
   job, closing EXP001-E5-F1.

## Blocking condition

Session 0159 (EXP-002 E1) and every experiment downstream of EXP-001, plus
0194, were **BLOCKED** until this experiment's E5 verdict is not a reversal, or
the maintainer records a Project Plan §8.3 amendment accepting a changed
conclusion (campaign plan §10.4 item 5).

**E4 detected no reversal and E5 has now reported it** — all five hypotheses
are `CONFIRMED` and the D1 flag is not raised
([`analysis.md`](analysis.md), [`report.md`](report.md)). The §10.4 item 5
condition is therefore **satisfied**, and no §8.3 amendment is needed because
nothing here is a changed conclusion.

**The release is not yet in force.** Experimentation Standards §2 E5 and the E5
exit gate require an *approved* report, so 0159, EXP-002 … EXP-008 and 0194 are
released **on the maintainer's verification recorded in
[`report.md`](report.md) §13** — that block is currently unfilled. Until it is
completed they remain **BLOCKED**, and this README, the session register and the
phase-7 index all say so rather than letting a reader infer a release that has
not been granted. For the same reason the earlier stages released nothing:
neither a correction merge, E1 completion, E2 approval, E3's execution nor E4's
clean exit lifts the block on its own.
