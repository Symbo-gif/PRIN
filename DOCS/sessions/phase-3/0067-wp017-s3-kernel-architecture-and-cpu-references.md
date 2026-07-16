# Session 0067 — WP-017 S3: Remediation — Kernel architecture and CPU references

**Status:** PLANNED  
**Roadmap phase:** 3 — GPU kernels  
**Execution unit:** WP-017  
**Session type:** S3 — Remediation  
**Predecessor:** [0066 — Audit](0066-wp017-s2-kernel-architecture-and-cpu-references.md)  
**Successor:** [0068 — Documentation](0068-wp017-s4-kernel-architecture-and-cpu-references.md)  
**Authority:** Project Plan §6/§8; the applicable normative standards. If this brief conflicts with a normative standard, the standard wins.

> This is a prospective execution contract, not completion evidence. Status and
> results belong in Audit Reports, Project State Reports, and experiment artefacts.

## Mission

Establish prin-kernels backend abstraction, CubeCL build path, device/dtype dispatch, preallocated buffers, and authoritative CPU references.

## Contract

- **Acceptance:** One-algorithm-one-implementation invariant is demonstrable; unsupported devices fall back safely; no runtime compiler dependency; equivalence harness is operational.
- **Non-goals:** Production GPU kernels.

## Required reading

- `DOCS/PRIN_Project_Plan.md`
- `DOCS/standards/Development_Workflow_and_Audit_Standards.md`
- The latest `DOCS/reports/NNN-project-state.md` and cumulative deviation ledger
- This session brief and its immediate predecessor's closure evidence
- `DOCS/audits/017-wp017-audit.md` and every cited violated clause

## Entry conditions

- S2 verdict is acknowledged and its finding list is immutable except for
  appended closure information.

## Expected remediation

1. Process every finding D1→D4; do no feature work.
2. Commit each correction with its finding ID and add a regression test where applicable.
3. Use an approved, logged plan amendment only when justified reality should
   move the trajectory; never normalize drift silently.
4. Re-run affected A1–A10 checks and the WP acceptance evidence after each fix.
5. Append the closure table to `DOCS/audits/017-wp017-audit.md` with FIXED / AMENDED / permitted
   CARRIED(1), commit/amendment reference, and delta evidence.
6. If S2 found nothing, perform and record a no-change delta verification so
   this mandatory session remains explicit and auditable.

## Required outputs

- All finding commits and regression tests.
- Completed closure table and CLEAN delta re-audit.
- Full local gate green with no newly introduced deviation.

## Prohibited

New features, opportunistic refactors, unapproved scope changes, unresolved
D1/D2 findings, or a second carry of any D4.

## Exit gate

Every finding is closed and delta re-audit is CLEAN. Hand off to S4; if not,
repeat remediation/delta verification within this session until clean.
