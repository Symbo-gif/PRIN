# Conditional correction sessions

These unnumbered templates are inserted whenever Phase 7 or a release check
raises a D1/D2 outside an active WP cycle. The insertion is recorded in the
Project State Report and deviation ledger; scheduled session numbers do not
change. Execute all four in exact S1→S2→S3→S4 order, then return to the blocked
numbered session. Copy each template to a dated/identified file before use.

## Open corrections

EXP-002 D1 — **OPEN, opened 2026-10-14 UTC by session `0163` (EXP-002 E5).**
Triggered by campaign plan §10.4 (pre-registration §4.3): EXP-002's H3 is
`REFUTED` under both the approved §5.4 comparison policy (`21/39`
`generated_files` equal, `18/39` differing: both the `.pdf` and `.png` of
figures 5, 7, 8, 9, 10, 11, 12, 14, and 15, while all `11/11` `.tex` tables
and `5/14` figures match) and the §11.3 sensitivity policy (`5/39` equal,
`34/39` differing), while H1 (`175/175` `api_symbols`, `172/172`
`legacy_api_names`), H2 (`62/62` `claim_comparator_records`), and H4 (`39/39`
raw-identical across two PRIN processes) are `CONFIRMED`. The four sessions
below run in strict `S1 → S2 → S3 → S4` order after maintainer approval of the
S1 scope. **Session `0164` (EXP-003 E1) and every later campaign session
(`0165`–`0194`) stay blocked until S4 closes and `EXP-002-r1` returns a
non-reversal verdict** (or the maintainer adopts a Project Plan §8.3
amendment; campaign plan §3.3, §10.4 items 2–5). No root cause is claimed by
the triggering record; S1 owns it.
**S1 COMPLETE 2026-10-15 UTC** on `hotfix/exp002-d1-figure-parity` (draft
PR #34). The root cause is on the PRIN side: the WP-034 port dropped or
re-encoded 34 drawing arguments in the nine figure generators, and
controlled substitution on the frozen reference explains every differing
byte with 0 unexplained. The failing-test-first gate went from 18 failures
to green, and all 39 outputs now equal the reference (campaign plan §10.4
item 3 not invoked;
[correction audit](../../audits/2026-10-15-exp002-d1-correction-audit.md)).
**S2 COMPLETE 2026-10-15 UTC** — read-only audit of `ab9e4225..8fd0ecc9`,
verdict **`PASS-WITH-FINDINGS`**: one D2, one D3, six D4, **no D1**, no
systemic drift. All five brief-specific items were **VERIFIED** by independent
re-execution rather than accepted on authority — the pre-fix gate red on
exactly the 18 E3 files and all 9 argument tests; the decomposition reproducing
field-for-field; **34/34** divergence specifications validated statically
against the frozen reference source; an artist-level comparison **14/14 EQUAL**
so no plotted value differs; `verify_manifest` green on all five runs; the
frozen E4 module reproducing all seven outputs and `report-manifest.json`
`6b15dcc1…68781` byte-for-byte from a clean worktree outside the repository;
and Snyk Code **0 findings** in the four changed files on **both** routes — the
MCP integration, and the CLI leg the brief named once the maintainer
re-authenticated it (Test Summary **0 HIGH / 0 MEDIUM / 77 LOW**, so the §6.2
"0 medium+" gate is met; the earlier blocked-CLI state is retained in the record
rather than overwritten). The fast suite achieved the clean
single pass S1 handed over (4038 passed, 0 failed); the full suite is
**exit 1** on a pre-existing notebook cell timeout (`EXP002D1-S2-F2`, D2). The
D3 (`EXP002D1-S2-F1`) is that the two registered H3 policies now disagree about
the verdict — approved §5.4 **39/39 equal**, §11.3 sensitivity **14/39 equal**,
with all 25 residuals classified as writer/host properties (PDF Info key sets,
`.tex` line terminators) and 0 unclassified — which S4 must carry into the
`EXP-002-r1` authorization so its E1/E2 registers both policies deliberately.
Of the eight findings, `-F3` is **RESOLVED** (the CLI leg completed) and `-F8`
is **RATIFIED** (two residual LOW `python/PT` findings in S2's own instruments,
remediated twice on the `PR23-F1` pattern and accepted with a recorded §6.2
threat assessment), so **six remain for S3**.
Evidence: [`EVIDENCE/exp002-d1-s2/`](../../../EVIDENCE/exp002-d1-s2/README.md).
Committed locally only; **nothing pushed** — the maintainer delegated the push
call and Development Workflow §3 plus amendment #28 put the cycle's push point
at S4. S3 is next and is mandatory even
though no D1 was found. See the
[EXP-002 E5 report](../../experiments/EXP-002-api-benchmark-result-and-reproduction-parity/report.md)
§§3, 6, 8, 11, 14.

- [2026-10-14-exp002-d1-s1-correction-implementation.md](2026-10-14-exp002-d1-s1-correction-implementation.md)
- [2026-10-14-exp002-d1-s2-correction-audit.md](2026-10-14-exp002-d1-s2-correction-audit.md)
- [2026-10-14-exp002-d1-s3-correction-remediation.md](2026-10-14-exp002-d1-s3-correction-remediation.md)
- [2026-10-14-exp002-d1-s4-correction-documentation.md](2026-10-14-exp002-d1-s4-correction-documentation.md)

## Closed corrections

DV-044 — **CLOSED 2026-09-29 UTC.** All four stages executed in S1→S4 order
on `hotfix/dv044-ledger-delta` (merged into this campaign branch `9cda4e5`).
PSR-039's cumulative deviation ledger is now represented by an explicit
§3.4 canonical delta (14 rows) and `tools/check_deviation_ledger.py`
merges marked deltas while rejecting five-column local tables as cumulative
ledgers — the exact failing PSR-038→039 comparison exits 0 (128→142) locally
and on hosted CI (PR #27 `governance` job, run `36526332612`). S2
PASS-WITH-FINDINGS; all seven findings remediated in S3 (12/12 tests, Snyk
clean). The refreshed tool reaches `main` with this amendment at E5.

- [2026-09-29-dv044-s1-correction-implementation.md](2026-09-29-dv044-s1-correction-implementation.md)
- [2026-09-29-dv044-s2-correction-audit.md](2026-09-29-dv044-s2-correction-audit.md)
- [2026-09-29-dv044-s3-correction-remediation.md](2026-09-29-dv044-s3-correction-remediation.md)
- [2026-09-29-dv044-s4-correction-documentation.md](2026-09-29-dv044-s4-correction-documentation.md)

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
