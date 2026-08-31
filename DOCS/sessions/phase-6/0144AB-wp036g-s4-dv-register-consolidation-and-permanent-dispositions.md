# Session 0144AB — WP-036G S4: Documentation — Deferred-Validation register consolidation and permanent dispositions

**Status:** PLANNED
**Roadmap phase:** 6 — Benchmarks, reproduction, docs, and RC1
**Execution unit:** WP-036G
**Session type:** S4 — Documentation
**Predecessor:** [0144AA — Remediation](0144AA-wp036g-s3-dv-register-consolidation-and-permanent-dispositions.md)
**Successor:** [0145 — Coding (WP-037 S1)](0145-wp037-s1-documentation-notebooks-paper-and-parity-report-draft.md)
**Authority:** Project Plan §6/§8 and amendment #38; the applicable normative standards. If this brief conflicts with a normative standard, the standard wins.

> This is a prospective execution contract, not completion evidence.

## Mission

Commit the consolidated Deferred Validation Register, issue the WP-036G
Project State Report with the maintainer-signed permanent dispositions and
the Phase 7 entry statement, and confirm WP-037 (session `0145`) entry
conditions. This S4 closes the amendment-#38 DV-closure block.

## Contract

- **Acceptance:**
  - `DOCS/reports/DEFERRED_VALIDATION_REGISTER.md` finalised: every row is
    `CLOSED`, `AMENDED`, permanent-disposition (dated, maintainer-signed in
    this PSR, no re-audit gate), or standing-external-disposition (dated,
    evidenced, "not a Phase 7 entry blocker"). The `chacha20` row is present.
    DV-005 appears as `AMENDED` (amendment #38); DV-030/DV-003 as `CLOSED`
    (WP-036E); DV-006 DirectML half `CLOSED`, NPU remainder OPEN & re-scoped
    (WP-036F). DV-010 → WP-038 S1; DV-027 → EMA-006.
  - `DOCS/reports/036g-project-state.md` issued with: the metric trends,
    cumulative deviation ledger, amendment #38, the **maintainer sign-off
    block** for the DV-007/DV-013/DV-018/DV-028 permanent dispositions
    (MichaelMaillet, dated), the consolidated re-verification evidence
    summary, and the **Phase 7 entry statement** — every remaining OPEN DV
    item with a per-item "does not block campaign pre-registration or
    execution" assertion.
  - READMEs touched in S1–S3 updated; `CHANGELOG.md` entry; Sphinx build
    clean; `tools/check_deviation_ledger.py` and
    `tools/check_dv_register_gates.py` run and green; the full batched
    WP-036G range pushed and CI green.
  - WP-037 (`0145`) entry conditions confirmed and maintainer approval
    recorded.
- **Non-goals:** functional feature work; the WP-038 tag push; any Phase 7
  session.

## Required reading

- `DOCS/PRIN_Project_Plan.md` §6, §8.3 amendment #38, §9 (DoD item 11)
- `DOCS/standards/Documentation_Standards.md` §7 (incl. items 6 and 7 — the
  two check tools)
- `DOCS/audits/036g-wp036g-audit.md` including its CLEAN closure table
- `DOCS/reports/DEFERRED_VALIDATION_REGISTER.md`
- The WP-036G S1–S3 commit range and handoff/audit artefacts

## Entry conditions

- S3 delta re-audit is CLEAN; no unresolved D1/D2 finding exists.

## Expected documentation closure

1. Finalise `DEFERRED_VALIDATION_REGISTER.md` from the S1/S3 drafts; move
   fully-closed items to "Closed items"; keep OPEN-but-dispositioned items in
   "Active deferred items" with their dated disposition and class label.
2. Update every touched README; update `CHANGELOG.md`; confirm the Sphinx
   Parity Report and Migration Guide reflect the DV-007 permanent-hazard
   language.
3. Write `DOCS/reports/036g-project-state.md` with the maintainer sign-off
   block, the re-verification summary, and the Phase 7 entry statement.
4. Run all documentation, link, quality, security, and check-tool gates;
   push the batched WP-036G range and confirm CI green.
5. Confirm WP-037 (`0145`) entry conditions; record maintainer approval.
6. Update this session's status and the master register; mark WP-036E/F/G
   COMPLETE; set `0145`'s predecessor pointer to this session (already wired
   by amendment #38).
7. Verify Documentation Standards §7 item 9 cross-cutting documents: Project
   Plan §6 roadmap table, `DOCS/experiments/README.md` index,
   `SESSION_REGISTER.md` Global Sessions section.

## Required outputs

- Finalised `DEFERRED_VALIDATION_REGISTER.md`; approved
  `DOCS/reports/036g-project-state.md` with sign-off and Phase 7 entry
  statement.
- Updated READMEs and docs; CHANGELOG entry; warning-free docs gates.
- Green local gates and CI over the batched WP-036G range.

## Prohibited

Functional feature work. A code defect discovered here becomes a governed
correction cycle.

## Exit gate

All S4 artefacts committed; the S4 push carries the full WP-036G S1–S4 range
and CI is green; the DV register is fully consolidated; the Phase 7 entry
statement is signed. WP-036G is closed; the amendment-#38 DV-closure block is
complete; only then may WP-037 (`0145`) begin.
