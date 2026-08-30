# Session 0144K — WP-036C S3: Remediation — Acceptance suite port (integration, y-series, kernels; DV-025)

**Status:** PLANNED
**Roadmap phase:** 6 — Benchmarks, reproduction, docs, and RC1
**Execution unit:** WP-036C
**Session type:** S3 — Remediation
**Predecessor:** [0144J — Audit](0144J-wp036c-s2-acceptance-suite-port-integration-y-series-kernels.md)
**Successor:** [0144L — Documentation](0144L-wp036c-s4-acceptance-suite-port-integration-y-series-kernels.md)
**Authority:** Project Plan §6/§8 and amendment #31; the applicable normative standards. If this brief conflicts with a normative standard, the standard wins.

> This is a prospective execution contract, not completion evidence.

## Mission

Fix every finding in `DOCS/audits/036c-wp036c-audit.md`; no feature work.

## Contract

- **Acceptance:** every finding ends FIXED or AMENDED; CLEAN delta re-audit;
  full local gate and full ported acceptance suite green.
- **Non-goals:** new features, opportunistic refactors.

## Required reading

- `DOCS/PRIN_Project_Plan.md` and amendment #31
- `DOCS/standards/Development_Workflow_and_Audit_Standards.md`
- `DOCS/audits/036c-wp036c-audit.md` and every cited violated clause

## Entry conditions

- S2 verdict acknowledged; finding list immutable except for appended closure.

## Expected remediation

1. Process every finding D1→D4.
2. Commit each correction with its finding ID; add regression evidence.
3. Approved, logged plan amendment only where justified reality should move the
   trajectory; never normalize drift silently.
4. Re-run affected A1–A10 checks and the full ported acceptance suite after
   each fix.
5. Append the closure table to `DOCS/audits/036c-wp036c-audit.md`.
6. If S2 found nothing, record a no-change delta verification.

## Required outputs

- All finding commits and regression evidence.
- Completed closure table and CLEAN delta re-audit.
- Full local gate green with no newly introduced deviation.

## Prohibited

New features, unapproved scope changes, unresolved D1/D2, or a second carry of
any D4.

## Exit gate

Every finding closed and delta re-audit CLEAN. Hand off to S4.
