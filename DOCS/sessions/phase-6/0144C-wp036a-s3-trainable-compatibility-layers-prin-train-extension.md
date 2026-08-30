---

# Session 0144C — WP-036A S3: Remediation — Trainable compatibility layers (`prin-train` extension)

**Status:** PLANNED
**Roadmap phase:** 6 — Benchmarks, reproduction, docs, and RC1
**Execution unit:** WP-036A
**Session type:** S3 — Remediation
**Predecessor:** [0144B — Audit](0144B-wp036a-s2-trainable-compatibility-layers-prin-train-extension.md)
**Successor:** [0144D — Documentation](0144D-wp036a-s4-trainable-compatibility-layers-prin-train-extension.md)
**Authority:** Project Plan §6/§8 and amendment #33; the applicable normative standards. If this brief conflicts with a normative standard, the standard wins.

> This is a prospective execution contract, not completion evidence.

## Mission

Remediate every finding in `DOCS/audits/036a-wp036a-audit.md` against the
WP-036A trainable-compatibility-layers scope; no feature work.

## Contract

- **Acceptance:** Every finding ends FIXED or AMENDED; CLEAN delta re-audit;
  the 13-symbol real-implementation delivery and `verify_api_surface` stay green.
- **Non-goals:** Acceptance-suite porting; final documentation prose.

## Required reading

- `DOCS/PRIN_Project_Plan.md` and amendments #31, #33
- `DOCS/standards/Development_Workflow_and_Audit_Standards.md`
- `DOCS/audits/036a-wp036a-audit.md` and every cited violated clause
- The latest `DOCS/reports/NNN-project-state.md` and cumulative deviation ledger

## Entry conditions

- S2 verdict is acknowledged and its finding list is immutable except for
  appended closure information.

## Expected remediation

1. Process every finding D1→D4; do no feature work.
2. Commit each correction with its finding ID and add a regression test where applicable.
3. Re-run affected A1–A10 checks after each fix.
4. Append the closure table to `DOCS/audits/036a-wp036a-audit.md`.
5. If S2 found nothing, perform and record a no-change delta verification.

## Prohibited

New features, opportunistic refactors, unapproved scope changes, unresolved
D1/D2 findings, or a second carry of any D4.

## Exit gate

Every finding is closed and delta re-audit is CLEAN. Hand off to S4.
