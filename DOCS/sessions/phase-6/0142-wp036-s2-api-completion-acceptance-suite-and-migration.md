# Session 0142 — WP-036 S2: Audit — API completion, acceptance suite, and migration

**Status:** COMPLETE
**Roadmap phase:** 6 — Benchmarks, reproduction, docs, and RC1
**Execution unit:** WP-036
**Session type:** S2 — Audit
**Predecessor:** [0141E — Coding sub-pass 5/5](0141E-wp036-s1e-consolidation-and-handoff.md) (WP-036 S1 executed as `0141A`–`0141E` per amendment #32; this S2 audits the contiguous `0141`+`0141A`–`0141E` commit range)
**Successor:** [0143 — Remediation](0143-wp036-s3-api-completion-acceptance-suite-and-migration.md)
**Verdict:** PASS-WITH-FINDINGS (2 D4: WP036-F1 per-module coverage gaps in D-2.2 stubs, WP036-F2 handoff drafting process deviation). Audit report: `DOCS/audits/036-wp036-audit.md`.
**Authority:** Project Plan §6/§8 and **amendment #31**; the applicable normative standards. If this brief conflicts with a normative standard, the standard wins.

> This is a prospective execution contract, not completion evidence. Status and
> results belong in Audit Reports, Project State Reports, and experiment artefacts.

> **Scope note (amendment #31):** WP-036 covers the compatibility surface,
> freeze machinery, stubs, DV-012 bindings, and Migration Guide symbol table.
> The acceptance-suite port is audited under WP-036B/WP-036C.

## Mission

Audit WP-036 S1: the `prin` compatibility symbol surface, `prin._deprecation`
machinery, `.pyi` stubs, DV-012 sweep/engine bindings, and the Migration Guide
symbol table.

## Contract

- **Acceptance:** Every one of the 172 `prinet.__all__` symbols resolves from
  `prin` and passes a construct/callable smoke check; `verify_api_surface`
  green; the Migration Guide table is machine-checked; no silent removals; no
  Python numerics; the D-D per-symbol GPU/Triton dispositions are sound (S2
  veto right).
- **Non-goals:** The acceptance-suite port; final documentation prose or
  release publishing.

## Required reading

- `DOCS/PRIN_Project_Plan.md`
- `DOCS/standards/Development_Workflow_and_Audit_Standards.md`
- The latest `DOCS/reports/NNN-project-state.md` and cumulative deviation ledger
- This session brief and its immediate predecessor's closure evidence
- `DOCS/audits/TEMPLATE_Audit_Report.md`
- Coding/Testing/Documentation security and coverage gates

## Entry conditions

- S1 has claimed its exit gate and supplied an evidence map.
- The repository and S1 commit range are fixed for inspection.

## Expected audit (read-only with respect to source)

1. Create `DOCS/audits/036-wp036-audit.md` from the audit template.
2. Execute A1–A10: scope, architecture, tests-in-tandem/coverage, parity,
   quality, security, documentation, hygiene, CI/regressions, artefact trail.
3. Independently reproduce the WP-specific acceptance evidence: every one of the 172 `prinet.__all__` symbols resolves from `prin` and smoke-checks; `verify_api_surface` green; Migration Guide table machine-checked; no silent removals or Python numerics.
4. Inspect diffs for weakened tests, tolerance drift, new dependencies,
   unapproved unsafe/code generation, Python numerics, and undocumented exports.
5. Give each finding `WP036-Fn`, severity D1–D4, exact evidence,
   violated clause, and proposed remedy. Assign PASS / PASS-WITH-FINDINGS / FAIL.

## Required outputs

- Committed evidence-backed Audit Report at `DOCS/audits/036-wp036-audit.md`.
- Updated deviation-ledger delta and an ordered S3 action list.
- Maintainer acknowledgment of the verdict.

## Prohibited

No source fix, plan rewrite, finding suppression, or evidence-free assertion in
S2. Discovery and correction remain separate for audit independence.

## Exit gate

Audit Report and verdict are committed. Hand off to S3 **even with zero
findings**; a zero-finding S3 records no-change closure and delta verification.
