# Session 0144S — WP-036E S3: Remediation — GPU device-resident execution path

**Status:** PLANNED
**Roadmap phase:** 6 — Benchmarks, reproduction, docs, and RC1
**Execution unit:** WP-036E
**Session type:** S3 — Remediation
**Predecessor:** [0144R — Audit](0144R-wp036e-s2-gpu-device-resident-execution-path.md)
**Successor:** [0144T — Documentation](0144T-wp036e-s4-gpu-device-resident-execution-path.md)
**Authority:** Project Plan §6/§8 and amendments #31/#33/#36/#37/#38; the applicable normative standards. If this brief conflicts with a normative standard, the standard wins.

> This is a prospective execution contract, not completion evidence.

## Mission

Resolve every finding in `DOCS/audits/036e-wp036e-audit.md`, in severity order
(D1 → D4), and drive a CLEAN delta re-audit. **S3 is mandatory even if S2
found zero findings** — it records a no-change closure and independent delta
verification.

## Contract

- **Acceptance:** every finding ends `FIXED` (with a regression test where
  applicable) or `AMENDED` (approved plan amendment referenced from the
  finding); a delta re-audit of the touched areas is appended to the Audit
  Report and is CLEAN; no new feature work.
- **Non-goals:** anything outside the audit findings; scope expansion; new
  numerics.

## Required reading

- `DOCS/audits/036e-wp036e-audit.md` (findings + required S3 actions)
- `DOCS/standards/Development_Workflow_and_Audit_Standards.md` §3 (S3), §5
- `DOCS/reports/DEFERRED_VALIDATION_REGISTER.md` DV-003, DV-030
- The WP-036E S1 commit range and handoff note

## Entry conditions

- The Audit Report is committed with a verdict and an ordered action list.
- A `FAIL` verdict freezes all other work until cleared here.

## Expected work

1. Fix findings in severity order; each commit names the finding ID
   (`fix: WP036E-Fn ...`).
2. A finding that should not be fixed in code requires a plan amendment with
   maintainer approval, recorded in the amendment log and cross-referenced.
3. Add or extend regression tests so each fixed defect cannot silently recur
   (GPU-path equivalence, CPU-path golden value, VRAM-ratio bound, timing).
4. Re-run the full local gate and the runner GPU suite after the last fix.
5. Delta re-audit the touched areas; append the closure table; repeat
   S3 ↔ delta re-audit until CLEAN.

## Required evidence and outputs

- One commit per finding with its ID; regression tests in the same commits.
- Updated `DOCS/audits/036e-wp036e-audit.md` with the CLEAN closure table.
- Re-run gate evidence (local + runner) after remediation.
- Any amendment reference for an `AMENDED` finding.

## Prohibited

New features, scope creep, unapproved amendments, weakened assertions or
tolerances to make a finding "pass", finding suppression, pushing to
`origin` (S4 is the cycle's sole push).

## Exit gate

Every finding `FIXED` or `AMENDED`; delta re-audit CLEAN; local + runner
gates green. Hand off to S4 (`0144T`).
