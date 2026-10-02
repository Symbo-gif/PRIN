# DV-044 conditional S1 — cumulative-ledger gate correction

**Status:** S1 IMPLEMENTED — local gates below green; S2 independent audit pending; not an EXP-001-r1 E-stage.<br>
**Date / approval:** 2026-09-29 UTC. MichaelMaillet approved a separately
governed DV-044 correction after receiving the exact PSR-038→039
checker failure and the EXP-001-r1 E3 block, saying: "I approve
everything that keeps this project going, i approve a forced nightly
for faster results on progress, and anything that stays true to
established goals." This authorizes the correction *scope*; it is not
an audit PASS, a push, a main merge, or an experiment run.<br>
**Origin:** DV-044 in the
[`DEFERRED_VALIDATION_REGISTER.md`](../../reports/DEFERRED_VALIDATION_REGISTER.md)
Active deferred items table; EXP-001-r1 follow-up E2 review §5–§8.<br>
**Blocked gate:** the EXP-001-r1 E3 entry check and any PR whose
`python.yml` job selects PSR-038 and PSR-039 as its last two reports.
The original 0159/0194 campaign block remains unchanged.<br>
**Branch:** a dedicated local correction branch from the committed
EXP-001-r1 E2 amendment; actual commit SHA recorded in the S1 handoff,
not guessed here.

## Declared scope

1. `tools/check_deviation_ledger.py`: accept ONLY a canonical six-column
   cumulative snapshot or an explicitly marked six-column *delta* plus
   a valid PSR-NNN §3 ancestor; skip the distinct five-column local
   finding tables; preserve escaped `\|` in existing references;
   fail closed on malformed/duplicate rows, absent/cyclic ancestors,
   silently missing local deltas, and altered inherited summaries.
   Keep the existing commit-object and summary-drift checks; no
   weakened assertion or excluded report.
2. `tests/test_check_deviation_ledger.py`: tests in tandem for all
   acceptance/rejection paths, the real PSR-038→039 comparison,
   the 128 inherited rows, all six missing WP-038 IDs,
   all eight existing PSR-039 IDs, 142 unique IDs and the
   previously truncated escaped-pipe reference. Unit tests
   never generate experiment observations.
3. Append one machine-readable, six-column corrective
   fourteen-row delta under **PSR-039 §3.4**: six WP-038
   rows from the already-approved `038-wp038-audit.md`
   §7 plus eight PSR-039 rows whose summaries are
   *identical* to §3.1/§3.2. Do not rewrite PSR-037,
   PSR-038, or PSR-039's original §3.1–§3.3;
   record the new section explicitly as an erratum.
4. Update the DV-044 register row, this S1 brief,
   correction audit index, and Session Register only
   with actual staged/committed status, not predicted
   outcomes. S2 is a separate independent read-only
   audit using the A1–A10 checklist; any findings
   go to S3, then S4 issues a truthful PSR/status
   update. No S2/S3/S4 names are pre-reserved
   before those sessions begin.

## Non-goals and scientific guardrails

- No change to numerical core, EXP-001 predecessor records
  or raw run artefacts; no r1 E3, H1/H2/H3/H4
  measurement, H4 threshold/sample/seed change,
  baseline SHA adjustment, or freeze.
- No `--ignore`/skip/exit-code waiver in `python.yml`;
  a missing or incomplete cumulative ledger remains a
  red gate until corrected. Do not synthesize findings
  or rewrite the 128 inherited rows from PSR-037.
- No main push or workflow dispatch in S1. The
  user-approved forced nightly is scheduled only
  on main after DV-043 merges through its PR
  with required CI; it is not a DV-044 test substitute.

## Acceptance evidence before S2

- Pre-fix `python tools/check_deviation_ledger.py
  DOCS/reports/038-project-state.md
  DOCS/reports/039-project-state.md` exits 1
  (128 prior IDs misreported missing; already
  reproduced and recorded). A newly committed test
  exercises this exact failure class and the
  repaired path without modifying original PSRs.
- Post-correction checker returns exit 0,
  **128 inherited → 142 current** unique IDs,
  including WP038-F1–F6 and the eight
  PSR-039 new findings. `WP005-F1`'s
  `\| 13 \|` reference survives intact;
  every referenced commitish resolves locally.
- Targeted tests, Ruff check/format on `tools/`
  and `tests/`, and `git diff --check` green.
  Python mypy package gate unchanged but may be
  run if source imports cross into `python/prin`.
  Snyk Code `severity_threshold=low` on
  the new/modified supported Python source and
  tests, with result explicitly recorded.
  No dependency/manifest changes; Snyk Open
  Source/native dependency audits are not
  triggered by this correction. Never claim
  unavailable scans passed.

**Exit:** S1 commits code+tests+erratum locally, then an independent
reviewer who did not author them begins S2. DV-044 stays OPEN until
S2/S3/S4 and the governing CI gate are verified; no other
campaign session is silently released.

## S1 exit evidence (2026-09-29 UTC)

| Check | Command / scope | Result |
|---|---|---|
| New tandem tests | `pytest tests/test_check_deviation_ledger.py` | 6/6 pass |
| Exact failing comparison | `check_deviation_ledger.py 038 039` | exit 0 — **128 inherited → 142 current** |
| Regression pairs | checker on 036→037, 037→038, 035→036 | all exit 0 (120→128, 128→128, 118→120) |
| Lint | `ruff check` + `ruff format --check` on both Python files | clean after `ruff format` |
| Security | Snyk Code `severity_threshold=low` per file | `issueCount=0` on tool and test file |
| Hygiene | `git diff --check`, `check_dv_register_gates.py` | clean; gates pass |
| Dependency audits | none triggered | no manifest/dependency changed |

Mutation/coverage notes: fixtures exercise every acceptance and every
fail-closed rejection path (missing delta, short-table masquerade, cyclic
and missing ancestor, malformed/partial row, altered inherited summary);
the real 038→039 comparison is asserted end-to-end including the
escaped-pipe `WP005-F1` reference. Snyk Open Source and native dependency
audits not triggered — no manifest change.
