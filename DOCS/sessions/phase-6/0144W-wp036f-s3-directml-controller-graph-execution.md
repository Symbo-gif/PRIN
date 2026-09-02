# Session 0144W — WP-036F S3: Remediation — DirectML controller-graph execution

**Status:** COMPLETE — WP036F-F1 and WP036F-F2 both `FIXED`; delta re-audit
CLEAN (`DOCS/audits/036f-wp036f-audit.md` §7). Fix commits `a9ad913` /
`70781ca`; closure commit local only (push at S4 `0144X` per amendment #28).
**Roadmap phase:** 6 — Benchmarks, reproduction, docs, and RC1
**Execution unit:** WP-036F
**Session type:** S3 — Remediation
**Predecessor:** [0144V — Audit](0144V-wp036f-s2-directml-controller-graph-execution.md)
**Successor:** [0144X — Documentation](0144X-wp036f-s4-directml-controller-graph-execution.md)
**Authority:** Project Plan §6/§8 and amendments #13/#38; the applicable normative standards. If this brief conflicts with a normative standard, the standard wins.

> This is a prospective execution contract, not completion evidence.

## Mission

Resolve every finding in `DOCS/audits/036f-wp036f-audit.md` in severity order
(D1 → D4) and drive a CLEAN delta re-audit. **S3 is mandatory even if S2
found zero findings.**

## Contract

- **Acceptance:** every finding ends `FIXED` (with a regression test where
  applicable) or `AMENDED` (approved plan amendment referenced from the
  finding); a delta re-audit of the touched areas is appended and CLEAN; no
  new feature work.
- **Non-goals:** anything outside the audit findings; scope expansion;
  NPU/VitisAI work; DV-025 symbols.

## Required reading

- `DOCS/audits/036f-wp036f-audit.md` (findings + required S3 actions)
- `DOCS/standards/Development_Workflow_and_Audit_Standards.md` §3 (S3), §5
- `DOCS/reports/DEFERRED_VALIDATION_REGISTER.md` DV-006
- The WP-036F S1 commit range and handoff note

## Entry conditions

- The Audit Report is committed with a verdict and an ordered action list.
- A `FAIL` verdict freezes all other work until cleared here.

## Expected work

1. Fix findings in severity order; each commit names the finding ID
   (`fix: WP036F-Fn ...`).
2. A finding that should not be fixed in code requires a plan amendment with
   maintainer approval, recorded and cross-referenced.
3. Add or extend regression tests (graph function bit-identity, cross-provider
   agreement, checksum/fixture consistency).
4. Re-run the full local gate and the cross-provider test after the last fix.
5. Delta re-audit; append the closure table; repeat until CLEAN.

## Required evidence and outputs

- One commit per finding with its ID; regression tests in the same commits.
- Updated `DOCS/audits/036f-wp036f-audit.md` with the CLEAN closure table.
- Re-run gate evidence after remediation.
- Any amendment reference for an `AMENDED` finding.

## Prohibited

New features, scope creep, unapproved amendments, weakened
assertions/tolerances, finding suppression, pushing to `origin`.

## Exit gate

Every finding `FIXED` or `AMENDED`; delta re-audit CLEAN; local gates green.
Hand off to S4 (`0144X`).
