# EXP-001-r1 — Golden-trajectory numerical parity, re-run (track C1)

**Status:** **DRAFT — FOLLOW-UP E2 AMENDMENT AWAITS INDEPENDENT REVIEW AND
MAINTAINER APPROVAL** (2026-09-28 UTC). Independent review (Claude Sonnet 5)
verified every E1 provenance/machinery claim against the repository; the
maintainer approved the sample-size justification, the H2b three-way rule,
and the storage budget (campaign plan §14.2 amendment #7). The DV-041
binding capability is **CLOSED** on documented merge evidence (PR #25,
`5615eda`, required CI green per `triage-dv043-handoff.md` §2); the
proposed wgpu H4 companion amendment and two-build order await independent
follow-up E2 review and MichaelMaillet's explicit dated approval. DV-043
remains **OPEN** pending its merge to `main`, required CI, and one green
nightly `bench-regression`. See [`e2-review.md`](e2-review.md) §§5–7. **This
pre-registration does not freeze and E3 does not start while any of those
gates are open.**
This is a new experiment record per campaign plan §10.4 item 4. The original
EXP-001 record is immutable; corrections to it are errata.
**Predecessor:** [`EXP-001`](../EXP-001-golden-trajectory-numerical-parity/README.md)
(E5 reported 2026-09-23; H1/H2a `REFUTED`, D1 raised).
**Correction cycle:** [`DOCS/audits/2026-09-24-exp001-d1-correction-audit.md`](../../audits/2026-09-24-exp001-d1-correction-audit.md)
(S1 complete, S2 PASS, S3 CLEAN, S4 complete).
**Campaign plan row:** [`campaign-plan.md`](../campaign-plan.md) §2.1 EXP-001 / C1.

The maintainer declared this E1 session, then the E2 session. The [draft
pre-registration](preregistration.md), [E1 handoff](e1-handoff.md) and
[E2 review](e2-review.md) record the prospective protocol, local
validation, independent re-verification and the maintainer's E2 decisions.
Three of the four E2 gates are approved; the wgpu coverage gate is a
proposed follow-up amendment awaiting independent review and maintainer
approval, and DV-043's merge/nightly closure is still open — both block
freeze/E3. Neither E1 nor this partial E2 approval
executes E3 or releases session 0159.

## What this directory holds

| File | Created by | Frozen when |
|---|---|---|
| `README.md` | E1 | Updated as the experiment progresses |
| [`preregistration.md`](preregistration.md) | E1 (from [`TEMPLATE_Preregistration.md`](../TEMPLATE_Preregistration.md)) | **DRAFT** — freezes at E3 start; blocked on the unapproved wgpu amendment and DV-043's merge/nightly closure |
| [`e1-handoff.md`](e1-handoff.md) | E1 | Entry and verification evidence record |
| [`e2-review.md`](e2-review.md) | E2 | Independent-review and maintainer-decision record |
| `log.md` | E3 | *Not yet created* — written at E3; never edited after E3 close |
| `report.md` | E5 | *Not yet created* — written at E5; corrections are errata |
| `report-manifest.json` | E4/E5 | *Not yet created* — written at E4; SHA-256 of regenerated outputs |

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
0194, remain **BLOCKED** until this experiment's E5 verdict is not a reversal,
or the maintainer records a Project Plan §8.3 amendment accepting a changed
conclusion (campaign plan §10.4 item 5).
