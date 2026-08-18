# DOCS/audits/ — Audit Reports

One report per Session-Cycle audit (S2), named `NNN-wpNNN-audit.md`
(cycle number, work package). Produced per the
[Development Workflow and Audit Standards](../standards/Development_Workflow_and_Audit_Standards.md);
format mirrors the PRINet 3.0 `Codebase_Assessment_Report.md`.

- Template: [`TEMPLATE_Audit_Report.md`](TEMPLATE_Audit_Report.md)
- Executive Audit Template: [`TEMPLATE_Executive_Audit_Report.md`](TEMPLATE_Executive_Audit_Report.md)
- Executive Mathematical Audit Template: [`TEMPLATE_Executive_Math_Audit_Report.md`](TEMPLATE_Executive_Math_Audit_Report.md)
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
- [`017-wp017-audit.md`](017-wp017-audit.md) — WP-017 "Kernel architecture and
  CPU references" audit (`FAIL`); five findings (F1 D1, F2–F4 D2, F5 D4)
  resolved in S3 (four fixed, one fixed + amended) with a CLEAN delta re-audit.
  `DV-012` `prin-kernels` half closed; `prin-py` sweep/engine bindings remain
  deferred.
- [`018-wp018-audit.md`](018-wp018-audit.md) — WP-018 "Fused mean-field RK4
  kernel" audit (`PASS`); zero findings; S3 no-change closure with CLEAN
  delta re-audit.
- [`019-wp019-audit.md`](019-wp019-audit.md) — WP-019 "Sparse k-NN and PAC
  kernels" audit (`PASS-WITH-FINDINGS`); one D4 finding (WP019-F1, factual
  inaccuracy in S1 handoff note coverage table) resolved in S3 with a CLEAN
  delta re-audit.
- [`020-wp020-audit.md`](020-wp020-audit.md) — WP-020 "Fused discrete step and
  reductions" audit (`PASS`); zero S2 findings; one self-discovered D4
  finding (WP020-F1, `cargo test --features cpu` count transcription error
  in this report's own §2) resolved in S3 with a CLEAN delta re-audit.
- [`021-wp021-audit.md`](021-wp021-audit.md) — WP-021 "GPU integration and
  Phase 3 gate" audit (`PASS-WITH-FINDINGS`); one D4 finding (WP021-F1,
  session register status mismatch for session 0081) resolved in S3, plus
  self-discovered stale bookkeeping (session 0082's own status/register
  entries never flipped to `COMPLETE` when S2 closed), with a CLEAN delta
  re-audit.
- [`022-wp022-audit.md`](022-wp022-audit.md) — WP-022 "Trainable bands and
  resonance primitives" audit (`PASS-WITH-FINDINGS`); two D4 findings
  (WP022-F1: `bincode` RUSTSEC-2025-0141 advisory governance gap, AMENDED via
  Project Plan amendment #27; WP022-F2: `Params` structs not re-exported at
  the `prin-train` crate root, FIXED with a compile-time regression test)
  resolved in S3 with a CLEAN delta re-audit.
- [`EXECUTIVE_AUDIT_REPORT_001.md`](EXECUTIVE_AUDIT_REPORT_001.md) — First
  project-level executive audit (EA-001, 2026-08-07), `PASS-WITH-REMEDIATION`;
  five findings (E-F1–E-F5) remediated in-session.
  `[RETROACTIVE UPDATE - Executive Audit 002]` index entry added; see the
  correction note at the foot of the report for two claims amended by EA-002.
- [`EXECUTIVE_AUDIT_REPORT_002.md`](EXECUTIVE_AUDIT_REPORT_002.md) — Second
  project-level executive audit (EA-002, 2026-08-08), `PASS-WITH-REMEDIATION`;
  thirteen findings (E-F1–E-F13: two D2, four D3, seven D4) remediated
  in-session or passed forward with owners.
- [`EXECUTIVE_AUDIT_REPORT_003.md`](EXECUTIVE_AUDIT_REPORT_003.md) — Third
  project-level executive audit (EA-003, 2026-08-14), `PASS-WITH-REMEDIATION`;
  fourteen findings (E-F1–E-F14) remediated in-session (E-F7 risk-accepted,
  E-F6 tag/publish deliberately deferred by maintainer directive). `[Index
  entry added retroactively by EMA-001, 2026-08-14 — never added by EA-003
  itself.]`
- [`EXECUTIVE_AUDIT_REPORT_004.md`](EXECUTIVE_AUDIT_REPORT_004.md) — Fourth
  project-level executive audit (EA-004, 2026-08-17), `PASS-WITH-REMEDIATION`;
  two D1 findings (E-F1: live GitHub Actions billing block, passed forward as
  DV-014; E-F2: cumulative deviation-ledger corruption recurrence at WP-020
  S4, restored with durable CI enforcement closing DV-015).
- [`EXECUTIVE_MATH_AUDIT_REPORT_001.md`](EXECUTIVE_MATH_AUDIT_REPORT_001.md) —
  First Executive Mathematical Audit (EMA-001, 2026-08-14), `FAIL`; introduces
  `math-audit-mcp` independent tool-executed re-verification (SymPy/SciPy/
  Z3/NetworkX) as a new audit type (plan amendment #23). 23 claims audited
  across `prin-dynamics`/`prin-metrics`; one open D1 finding (M-F1: a
  Z3-confirmed phase-wrap defect in `prin-metrics::chimera::
  strength_of_incoherence`), one D3 evidentiary gap (M-F2), and a discovered
  D2 policy-design interaction (M-F3). Remediation deliberately deferred to a
  follow-up EMA-001 remediation session (this session's mandate was audit and
  reporting only).
- [`EXECUTIVE_MATH_AUDIT_PREPARATION_002.md`](EXECUTIVE_MATH_AUDIT_PREPARATION_002.md) —
  EMA-002 pre-audit preparation (2026-08-17): EMA-001 methodology review,
  scope analysis, and claim-ledger plan for the Phase 3 close mathematical
  audit.
- [`EXECUTIVE_MATH_AUDIT_REPORT_002.md`](EXECUTIVE_MATH_AUDIT_REPORT_002.md) —
  Second Executive Mathematical Audit (EMA-002, 2026-08-17), Phase 3 close,
  `PASS-WITH-REMEDIATION`; re-verified all 25 EMA-001 claims against
  `1604bd6` (zero regressions) and added 3 new `prin-kernels` GPU kernel
  claims (GPU-RK4-01, GPU-RED-01, GPU-KNN-01), all reaching genuine SymPy
  symbolic proof `PASS`. 28 total claims across 6 ledgers; 21 PASS, 7
  `REQUIRES_HUMAN_REVIEW` carried under the M-F3/DV-013 sign-off precedent
  (zero new findings).
