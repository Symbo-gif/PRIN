# Conditional correction sessions

These unnumbered templates are inserted whenever Phase 7 or a release check
raises a D1/D2 outside an active WP cycle. The insertion is recorded in the
Project State Report and deviation ledger; scheduled session numbers do not
change. Execute all four in exact S1→S2→S3→S4 order, then return to the blocked
numbered session. Copy each template to a dated/identified file before use.

## Open corrections

None.

## Closed corrections

EXP-001 D1 — **CLOSED 2026-09-27 UTC.** All four conditional sessions executed
in S1→S2→S3→S4 order. S1 established root cause (PRIN guard divergence fixed;
reference DV-007 `complex64` is the erroneous side, 67/67 exactness audit);
S2 audit **PASS** (zero findings above D4); S3 delta re-audit **CLEAN**; S4
documentation complete (PSR-039, registers updated, `EXP-001-r1` authorized).
See the [correction audit](../../audits/2026-09-24-exp001-d1-correction-audit.md).
**Session `0159` (EXP-002 E1) and every experiment downstream of EXP-001,
plus `0194`, stay BLOCKED until `EXP-001-r1` returns a non-reversal verdict**
(campaign plan §10.4 item 5). The correction branch
(`hotfix/exp001-d1-parity-correction`, PR #24) is not yet merged; CI-green
evidence for the merge SHA will be recorded by the next governed session.

- [2026-09-23-exp001-d1-s1-correction-implementation.md](2026-09-23-exp001-d1-s1-correction-implementation.md)
- [2026-09-23-exp001-d1-s2-correction-audit.md](2026-09-23-exp001-d1-s2-correction-audit.md)
- [2026-09-23-exp001-d1-s3-correction-remediation.md](2026-09-23-exp001-d1-s3-correction-remediation.md)
- [2026-09-23-exp001-d1-s4-correction-documentation.md](2026-09-23-exp001-d1-s4-correction-documentation.md)

DV-036 — **CLOSED 2026-09-23 UTC.** All four conditional sessions executed in
S1→S2→S3→S4 order. Merged to `main` as `b434554`; nightly run `35847692136`
wholly green and independently re-verified from its preserved evidence. Session
0156 released. DV-036's reference-host re-baseline gates (before 0168 and 0173)
remain open and are not part of this correction.

- [2026-09-23-dv036-s1-correction-implementation.md](2026-09-23-dv036-s1-correction-implementation.md)
- [2026-09-23-dv036-s2-correction-audit.md](2026-09-23-dv036-s2-correction-audit.md)
- [2026-09-23-dv036-s3-correction-remediation.md](2026-09-23-dv036-s3-correction-remediation.md)
- [2026-09-23-dv036-s4-correction-documentation.md](2026-09-23-dv036-s4-correction-documentation.md)
