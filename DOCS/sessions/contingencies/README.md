# Conditional correction sessions

These unnumbered templates are inserted whenever Phase 7 or a release check
raises a D1/D2 outside an active WP cycle. The insertion is recorded in the
Project State Report and deviation ledger; scheduled session numbers do not
change. Execute all four in exact S1→S2→S3→S4 order, then return to the blocked
numbered session. Copy each template to a dated/identified file before use.

## Open corrections

DV-044 — **S1–S3 COMPLETE 2026-09-29 UTC; S4 pending.** PSR-039's
cumulative deviation ledger was invisible to `tools/check_deviation_ledger.py`
(eight local five-column rows mistaken for the six-column cumulative table;
128 inherited IDs reported missing, `python.yml` gate exit 1) and PSR-038
never supplied the six WP-038 rows its prose claims. Maintainer-authorized
separately governed correction on `hotfix/dv044-ledger-delta`: an explicit
canonical PSR-039 §3.4 delta (14 rows) plus a fail-closed parser/CLI —
the exact failing comparison exits 0 (128→142). S2 independent audit:
PASS-WITH-FINDINGS, seven findings (1×D3 code, 5×D4, 1×D3 index drift);
all seven remediated in S3 with a sixth tandem test batch (12/12 pass) and
Snyk Code clean. S4 record, register disposition and a green governance CI
gate remain required before closure; EXP-001-r1 E3 stays blocked meanwhile.

- [2026-09-29-dv044-s1-correction-implementation.md](2026-09-29-dv044-s1-correction-implementation.md)
- [2026-09-29-dv044-s2-correction-audit.md](2026-09-29-dv044-s2-correction-audit.md)
- [2026-09-29-dv044-s3-correction-remediation.md](2026-09-29-dv044-s3-correction-remediation.md)

## Closed corrections

EXP-001 D1 — **CLOSED 2026-09-27 UTC.** S1→S2→S3→S4 all completed; S2 PASS
and S3 delta CLEAN
([`2026-09-24-exp001-d1-correction-audit.md`](../../audits/2026-09-24-exp001-d1-correction-audit.md));
S4 issued PSR-039 and authorized EXP-001-r1. PR #24 merged to `main` as
`149cf2d88ab6be401951b63d1d7e8fad209f52a5` (2026-09-28 UTC); six required CI
workflows green
([`EXP-001-r1/e1-handoff.md`](../../experiments/EXP-001-r1-golden-trajectory-numerical-parity/e1-handoff.md)).
Session 0159 and later dependencies remain blocked until r1 E5 returns a
non-reversal verdict (or approved Project Plan §8.3 amendment). No r1 run is
authorized by this correction closure.

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
