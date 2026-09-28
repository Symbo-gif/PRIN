# Conditional correction sessions

These unnumbered templates are inserted whenever Phase 7 or a release check
raises a D1/D2 outside an active WP cycle. The insertion is recorded in the
Project State Report and deviation ledger; scheduled session numbers do not
change. Execute all four in exact S1→S2→S3→S4 order, then return to the blocked
numbered session. Copy each template to a dated/identified file before use.

## Open corrections

EXP-001 D1 — **OPEN, opened 2026-09-23 UTC by session `0158` (EXP-001 E5).**
Triggered by campaign plan §10.4: EXP-001's H1 (`REFUTED`, 485/504) and H2a
(`REFUTED`, 897/1,000) are C1 parity reversals, and finding `EXP001-E5-F1`
(the `parity` CI corpus gate regenerates with PRINet 3.0, not PRIN, so no CI
gate performs the PRIN-vs-corpus trajectory comparison over the full 504-case
corpus; the only gate that runs PRIN against corpus trajectories covers 4
representative cases, none of them among H1's 19 breaching cases) is a second
D1. The four sessions below run in strict S1 → S2 → S3 → S4 order.
**S1 complete 2026-09-24 UTC** (draft PR #24): the root cause is a PRIN
Euler/RK4 guard divergence (fixed) plus the reference's DV-007 `complex64`
arithmetic (the corpus is the erroneous side, campaign plan §10.4 item 3), and
a full-corpus PRIN gate now runs in the `parity` job. See the
[correction audit](../../audits/2026-09-24-exp001-d1-correction-audit.md).
S2 is next. **Session `0159`
(EXP-002 E1) and every experiment downstream of EXP-001, plus `0194`, stay
blocked until S4 closes and `EXP-001-r1` returns a non-reversal verdict.** No
root cause is claimed by the triggering record; S1 owns it. See the
[EXP-001 E5 report](../../experiments/EXP-001-golden-trajectory-numerical-parity/report.md)
§7–§8.

- [2026-09-23-exp001-d1-s1-correction-implementation.md](2026-09-23-exp001-d1-s1-correction-implementation.md)
- [2026-09-23-exp001-d1-s2-correction-audit.md](2026-09-23-exp001-d1-s2-correction-audit.md)
- [2026-09-23-exp001-d1-s3-correction-remediation.md](2026-09-23-exp001-d1-s3-correction-remediation.md)
- [2026-09-23-exp001-d1-s4-correction-documentation.md](2026-09-23-exp001-d1-s4-correction-documentation.md)

## Closed corrections

DV-036 — **CLOSED 2026-09-23 UTC.** All four conditional sessions executed in
S1→S2→S3→S4 order. Merged to `main` as `b434554`; nightly run `35847692136`
wholly green and independently re-verified from its preserved evidence. Session
0156 released. DV-036's reference-host re-baseline gates (before 0168 and 0173)
remain open and are not part of this correction.

- [2026-09-23-dv036-s1-correction-implementation.md](2026-09-23-dv036-s1-correction-implementation.md)
- [2026-09-23-dv036-s2-correction-audit.md](2026-09-23-dv036-s2-correction-audit.md)
- [2026-09-23-dv036-s3-correction-remediation.md](2026-09-23-dv036-s3-correction-remediation.md)
- [2026-09-23-dv036-s4-correction-documentation.md](2026-09-23-dv036-s4-correction-documentation.md)
