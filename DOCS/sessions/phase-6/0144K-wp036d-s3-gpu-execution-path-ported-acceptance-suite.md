# Session 0144K — WP-036D S3: Remediation — GPU execution path for the ported acceptance suite

**Status:** PLANNED
**Roadmap phase:** 6 — Benchmarks, reproduction, docs, and RC1
**Execution unit:** WP-036D
**Session type:** S3 — Remediation
**Predecessor:** [0144J — Audit](0144J-wp036d-s2-gpu-execution-path-ported-acceptance-suite.md)
**Successor:** [0144L — Documentation](0144L-wp036d-s4-gpu-execution-path-ported-acceptance-suite.md)
**Authority:** Project Plan §6/§8 and amendments #31/#33/#36; the applicable normative standards. If this brief conflicts with a normative standard, the standard wins.

> This is a prospective execution contract, not completion evidence.

## Mission

Fix every finding in `DOCS/audits/036d-wp036d-audit.md`; no feature work.

## Contract

- **Acceptance:** every finding ends FIXED or AMENDED; CLEAN delta re-audit;
  full local gate green (CPU) and the 8 GPU tests green on the runner.
- **Non-goals:** new features, opportunistic refactors, WP-036C work, DV-005.

## Required reading

- `DOCS/PRIN_Project_Plan.md` and amendments #31/#33/#36
- `DOCS/standards/Development_Workflow_and_Audit_Standards.md`
- `DOCS/audits/036d-wp036d-audit.md` and every cited violated clause

## Entry conditions

- S2 verdict acknowledged; finding list immutable except for appended closure.

## Expected remediation

1. Process every finding D1→D4.
2. Commit each correction with its finding ID; add a regression test where
   applicable (for a GPU-path defect, the regression is the affected
   acceptance test passing on the runner after the binding/dispatch fix).
3. Use an approved, logged plan amendment only when justified reality should
   move the trajectory; never normalize drift silently.
4. Re-run affected A1–A10 checks, the 8 GPU tests, and the CPU acceptance
   suite after each fix.
5. Append the closure table to `DOCS/audits/036d-wp036d-audit.md`.
6. If S2 found nothing, record a no-change delta verification.

## Required outputs

- All finding commits and regression evidence.
- Completed closure table and CLEAN delta re-audit.
- Full local gate green with no newly introduced deviation.

## Prohibited

New features, unapproved scope changes, unresolved D1/D2, or a second carry
of any D4.

## Exit gate

Every finding closed and delta re-audit CLEAN. Hand off to S4.
