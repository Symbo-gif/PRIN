# DOCS/audits/ — Audit Reports

One report per Session-Cycle audit (S2), named `NNN-wpNNN-audit.md`
(cycle number, work package). Produced per the
[Development Workflow and Audit Standards](../standards/Development_Workflow_and_Audit_Standards.md);
format mirrors the PRINet 3.0 `Codebase_Assessment_Report.md`.

- Template: [`TEMPLATE_Audit_Report.md`](TEMPLATE_Audit_Report.md)
- Executive Audit Template: [`TEMPLATE_Executive_Audit_Report.md`](TEMPLATE_Executive_Audit_Report.md)
- Audits are append-only history: never edit a committed audit except to add
  the S3 closure table.
- Verdicts: `PASS` / `PASS-WITH-FINDINGS` / `FAIL` (any D1 finding ⇒ `FAIL`;
  feature work freezes until remediation clears it).

## Current reports

- [`001-wp001-audit.md`](001-wp001-audit.md) — WP-001 audit and CLEAN S3
  closure; eleven findings resolved (ten fixed, one approved amendment).
- [`002-wp002-audit.md`](002-wp002-audit.md) — WP-002 "Golden corpus and
  differential harness" audit (`PASS-WITH-FINDINGS`); four findings (F1–F4)
  resolved in S3 with a CLEAN delta re-audit.
- [`003-wp003-audit.md`](003-wp003-audit.md) — WP-003 "PyO3 and DLPack bridge
  spike" audit (`PASS-WITH-FINDINGS`); five findings (F1–F5) resolved in S3
  with a CLEAN delta re-audit (two approved plan/standard amendments #6 and
  #7).
- [`004-wp004-audit.md`](004-wp004-audit.md) — WP-004 "CubeCL fused mean-field
  RK4 spike" audit (`PASS-WITH-FINDINGS`); nine findings (F1–F4 D2, F5–F8 D3,
  F9 D4) resolved in S3 with a CLEAN delta re-audit; closure table and plan
  amendments #8–#12 are on file.
- [`005-wp005-audit.md`](005-wp005-audit.md) — WP-005 "ORT backends, wheel
  matrix, and Phase 0 gate" audit (`PASS-WITH-FINDINGS`); four findings
  (F1–F2 D3, F3–F4 D4) resolved in S3 with a CLEAN delta re-audit; closure
  table and plan amendment #13 are on file.
- [`006-wp006-audit.md`](006-wp006-audit.md) — WP-006 "Oscillator state,
  errors, and deterministic seed" audit (`PASS-WITH-FINDINGS`); three findings
  (F1 D2, F2 D3, F3 D4) resolved in S3 with a CLEAN delta re-audit.
- [`007-wp007-audit.md`](007-wp007-audit.md) — WP-007 "Oscillator dynamics
  models" audit (`PASS-WITH-FINDINGS`); five findings (F1–F2 D2, F3 D3, F4–F5
  D4) resolved in S3 with a CLEAN delta re-audit; closure table and plan
  amendment #14 (f64/f32 complex numerical hazard) are on file.
- [`008-wp008-audit.md`](008-wp008-audit.md) — WP-008 "Basic integrators"
  audit (`PASS-WITH-FINDINGS`); five findings (F1 D2, F2 D3, F3–F5 D4) resolved
  in S3 with a CLEAN delta re-audit; closure table is on file.
- [`009-wp009-audit.md`](009-wp009-audit.md) — WP-009 "PAC, coupling
  topologies, and phase k-NN" audit (`PASS-WITH-FINDINGS`); seven findings
  (F1–F2 D2, F3–F4 D3, F5–F7 D4) resolved in S3 with a CLEAN delta re-audit;
  closure table is on file. `[RETROACTIVE UPDATE - Executive Audit 002]`
  index entry added.
- [`010-wp010-audit.md`](010-wp010-audit.md) — WP-010 "Phase metrics and
  chimera measures" audit (`PASS`); zero findings; S3 no-change closure with
  CLEAN delta re-audit.
- [`011-wp011-audit.md`](011-wp011-audit.md) — WP-011 "Phase 1 Python API and
  dynamics integration" audit (`PASS`); one finding (F1 D4) resolved in S3
  with a CLEAN delta re-audit.
- [`012-wp012-audit.md`](012-wp012-audit.md) — WP-012 "Exponential and
  multi-rate integrators" audit (`FAIL`); five findings (F1–F3 D1, F4 D3, F5
  D4) resolved in S3 (four fixed, one approved amendment #18) with a CLEAN
  delta re-audit.
- [`013-wp013-audit.md`](013-wp013-audit.md) — WP-013 "Continuous band networks
  and temporal propagation" audit (`FAIL`); six findings (F1 D1, F2 D2, F3 D3,
  F4–F6 D4) resolved in S3 (five fixed, one approved amendment #19) with a
  CLEAN delta re-audit. One additional integrator-stage defect found while
  producing the F1 parity evidence was fixed in the same remediation.
- [`014-wp014-audit.md`](014-wp014-audit.md) — WP-014 "Tensor decompositions"
  audit (`FAIL`); seven findings (F1 D1, F2–F4 D2, F5/F7 D3, F6 D4) resolved
  in S3 with a CLEAN delta re-audit. Includes the GitHub Actions billing-block
  restoration evidence recorded in F7.
- [`015-wp015-audit.md`](015-wp015-audit.md) — WP-015 "OscilloSim sparse
  simulation engine" audit (`FAIL`); six findings (F1 D1, F2–F3 D2, F4–F6 D3)
  resolved in S3 (five fixed, one amended #WP015-F2) with a CLEAN delta
  re-audit.
- [`016-wp016-audit.md`](016-wp016-audit.md) — WP-016 "Parallel sweeps, CPU
  optimization, and Phase 2 gate" audit (`FAIL`); seven findings (F1 D1, F2–F4
  D2, F5–F7 D3) resolved in S3 (six fixed, one fixed + amended #21) with a
  CLEAN delta re-audit.
- [`EXECUTIVE_AUDIT_REPORT_001.md`](EXECUTIVE_AUDIT_REPORT_001.md) — First
  project-level executive audit (EA-001, 2026-08-07), `PASS-WITH-REMEDIATION`;
  five findings (E-F1–E-F5) remediated in-session.
  `[RETROACTIVE UPDATE - Executive Audit 002]` index entry added; see the
  correction note at the foot of the report for two claims amended by EA-002.
- [`EXECUTIVE_AUDIT_REPORT_002.md`](EXECUTIVE_AUDIT_REPORT_002.md) — Second
  project-level executive audit (EA-002, 2026-08-08), `PASS-WITH-REMEDIATION`;
  thirteen findings (E-F1–E-F13: two D2, four D3, seven D4) remediated
  in-session or passed forward with owners.
