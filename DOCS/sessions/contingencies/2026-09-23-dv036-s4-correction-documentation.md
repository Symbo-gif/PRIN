# DV-036 S4 — Correction documentation

**Status:** COMPLETE\
**Triggering deviation:** `DV036-F1 / DV036-F2`  
**Blocked numbered session:** `0156`

## Expectation

Update affected READMEs/changelog/reports/experiment protocol-deviation records, close the deviation ledger entry, and authorize return to the blocked session.

## Exit evidence

Record commands, artefacts, approvals, commits, and handoff in the correction
WP's audit and Project State Report. The blocked session remains blocked until
all four conditional sessions close.

**Historical status entry — round 1, 2026-09-23 UTC (superseded; retained as
the dated log, not the current disposition):** local documentation preparation
only; branch nightly, required CI, main-merge confirmation, and the final
correction Project State Report remain pending. Session 0156 remains blocked.

**Hosted validation round 2 (2026-09-23 UTC):** runs `35811372090` and
`35826531821` breached on identical-source measurements. DV036-F4 was
AMENDED by campaign amendment 4, and DV036-F5 was deferred to 0166; see the
[correction audit](../../audits/2026-09-23-dv036-nightly-correction-audit.md).
At that point S4 stayed IN PROGRESS pending a green hosted nightly with the
counterbalanced design. **Superseded by round 3 below.**

**Hosted validation round 3 — CLOSED (2026-09-23 UTC).** PR #22 merged as
`b43455405055d189b74441642ab32c96513b2e57`; nightly `workflow_dispatch` run
`35847692136` at that SHA concluded **success** for the whole workflow
(`full-suite` and `bench-regression` both green), and
`tools/check_ci_green.py b434554 --limit 120` reports all six required
workflows green. The comparison was substantive — 69 benchmarks, 63 gated,
none past +10%, 2 reference and 2 candidate passes — and was independently
re-derived in this session by re-running the committed checker against the
preserved evidence artefact. DV036-F1/F2/F3 are FIXED and DV036-F4 is CLOSED;
DV036-F5 remains DEFERRED to 0166.

Directory indexes, the deviation ledger, the campaign plan gap dispositions,
and the CHANGELOG are updated in the same commit. This correction has no
numbered Session Cycle, so its report of record is the
[correction audit](../../audits/2026-09-23-dv036-nightly-correction-audit.md)
(ETCA-002 remediation precedent) rather than a `NNN-project-state.md`, which
`DOCS/reports/README.md` reserves for closed Session Cycles.

**Final disposition (supersedes the round-1 and round-2 status entries
above): S4 is COMPLETE. All four conditional sessions are closed. Session 0156
is released to proceed**, subject to its own remaining entry conditions.
DV-036's reference-host re-baseline gates before 0168 and 0173 stay open, and
DV036-F5 stays DEFERRED to 0166. The report of record for this correction is
the [correction audit](../../audits/2026-09-23-dv036-nightly-correction-audit.md),
not a Project State Report.
