# Session 0144G — WP-036B S3: Remediation — Acceptance suite port (core, dynamics, model stack, subconscious)

**Status:** COMPLETE (2026-08-31)
**Roadmap phase:** 6 — Benchmarks, reproduction, docs, and RC1
**Execution unit:** WP-036B
**Session type:** S3 — Remediation
**Predecessor:** [0144F — Audit](0144F-wp036b-s2-acceptance-suite-port-core-dynamics-model-stack.md)
**Successor:** [0144H — Documentation](0144H-wp036b-s4-acceptance-suite-port-core-dynamics-model-stack.md)
**Authority:** Project Plan §6/§8 and amendment #31; the applicable normative standards. If this brief conflicts with a normative standard, the standard wins.

> This is a prospective execution contract, not completion evidence.

## Mission

Fix every finding in `DOCS/audits/036b-wp036b-audit.md`; no feature work.

## Contract

- **Acceptance:** every finding ends FIXED or AMENDED; CLEAN delta re-audit;
  full local gate green.
- **Non-goals:** new features, opportunistic refactors, WP-036C work.

## Required reading

- `DOCS/PRIN_Project_Plan.md` and amendment #31
- `DOCS/standards/Development_Workflow_and_Audit_Standards.md`
- `DOCS/audits/036b-wp036b-audit.md` and every cited violated clause

## Entry conditions

- S2 verdict acknowledged; finding list immutable except for appended closure.

## Expected remediation

1. Process every finding D1→D4.
2. Commit each correction with its finding ID; add a regression test where
   applicable (for a ported-test defect, the regression is the ported test
   itself passing after the underlying crate/module fix).
3. Use an approved, logged plan amendment only when justified reality should
   move the trajectory (e.g. a newly discovered upstream-defect non-parity, in
   the amendment #25 class); never normalize drift silently.
4. Re-run affected A1–A10 checks and the ported subset after each fix.
5. Append the closure table to `DOCS/audits/036b-wp036b-audit.md`.
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

---

## Closure (session 0144G, 2026-08-31)

S2 audit `DOCS/audits/036b-wp036b-audit.md` returned **PASS with zero
findings**. Mandatory S3 executed per Development Workflow and Audit Standards
§3. No source change, no plan amendment, no finding commit.

- **No-change delta verification recorded** in the audit report §7 closure
  table: `git diff 47390d4..HEAD -- crates/ python/ tests/` empty; ported
  subset re-run **489 passed / 9 skipped**; `ruff` and `mypy --strict` clean.
- **Deviation-ledger delta:** none.
- **Result:** delta re-audit **CLEAN**. Handed off to S4 (session 0144H).
