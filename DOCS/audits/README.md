# DOCS/audits/ — Audit Reports

One report per Session-Cycle audit (S2), named `NNN-wpNNN-audit.md`
(cycle number, work package). Produced per the
[Development Workflow and Audit Standards](../standards/Development_Workflow_and_Audit_Standards.md);
format mirrors the PRINet 3.0 `Codebase_Assessment_Report.md`.

- Template: [`TEMPLATE_Audit_Report.md`](TEMPLATE_Audit_Report.md)
- Executive Audit Template: [`TEMPLATE_Executive_Audit_Report.md`](TEMPLATE_Executive_Audit_Report.md)
- Executive Mathematical Audit Template: [`TEMPLATE_Executive_Math_Audit_Report.md`](TEMPLATE_Executive_Math_Audit_Report.md)
- Executive Documentation Audit Template: [`TEMPLATE_Executive_Documentation_Audit_Report.md`](TEMPLATE_Executive_Documentation_Audit_Report.md)
- Executive Testing and CI Audit Template: [`TEMPLATE_Executive_Testing_and_CI_Audit_Report.md`](TEMPLATE_Executive_Testing_and_CI_Audit_Report.md)
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
- [`023-wp023-audit.md`](023-wp023-audit.md) — WP-023 "Inhibition, activations,
  and HEP" audit (`PASS-WITH-FINDINGS`); one D4 finding (WP023-F1: `public_api.rs`
  regression test missing `GatedPhaseActivationParams` coverage, FIXED in S3
  with extended compile-time check) resolved in S3 with a CLEAN delta re-audit.
- [`024-wp024-audit.md`](024-wp024-audit.md) — WP-024 "Oscillator-aware
  optimizers" audit (`PASS-WITH-FINDINGS`); one D3 finding (WP024-F1: PSR-023 §7
  WP-024 declaration named non-existent classes, AMENDED via plan amendment #29)
  resolved in S3 with a CLEAN delta re-audit.

- [`025-wp025-audit.md`](025-wp025-audit.md) — WP-025 "Production Torch
  autograd bridge" audit (`PASS-WITH-FINDINGS`); four findings (WP025-F1 D2:
  checkpoint shape validation gap, FIXED; WP025-F2 D3: single-pilot-run
  boundary-overhead evidence, FIXED at evidentiary level with DV-021
  recorded; WP025-F3/F4 D4: coverage margin and test-count transcription
  errors, both FIXED) resolved in S3 with a CLEAN delta re-audit. S3-exec
  addendum: DV-021 performance investigation (redundant copy elimination)
  and register-wide deferred-item review.
- [`026-wp026-audit.md`](026-wp026-audit.md) — WP-026 "PhaseTracker, Hybrid,
  baselines, and allocation" audit (`PASS-WITH-FINDINGS`); two D4 findings
  (WP026-F1: allocator strategy-mismatch detection gap, FIXED; WP026-F2: no
  whole-module HybridPRINetV2 parity test, FIXED — parity test revealed and
  fixed missing ReLU in classifier head) resolved in S3 with a CLEAN delta
  re-audit.
- [`027-wp027-audit.md`](027-wp027-audit.md) — WP-027 "Trainable-stack
  integration and Phase 4 gate" audit (`PASS`); zero findings. DV-021
  bridge-overhead gap independently re-corroborated; DV-019 new recurrence
  evidence recorded; DV-005 CUDA Burn backend recommendation recorded for
  S4 register-review.
- [`028-wp028-audit.md`](028-wp028-audit.md) — WP-028 "ONNX controller and
  backend selection" audit (`PASS`); zero findings; S3 no-change closure with
  CLEAN delta re-audit (full gate suite re-run against a byte-for-byte
  unchanged source tree). Independently regenerated every bit-exact parity
  golden value from the live `prinet==3.0.0` reference, re-derived the ONNX
  field-number table from the installed `onnx` package, and re-verified the
  model SHA-256 digests from disk — all matched exactly. DV-005/DV-006
  re-audits confirmed consistent with the register.
- [`029-wp029-audit.md`](029-wp029-audit.md) — WP-029 "Daemon runtime and
  lock-free control buffer" audit (`PASS`); zero findings; S3 no-change
  closure with CLEAN delta re-audit (full gate suite re-run against a
  byte-for-byte unchanged source tree, with S2 bookkeeping synchronization).
- [`030-wp030-audit.md`](030-wp030-audit.md) — WP-030 "Training hooks and
  MOT evaluation" audit (`PASS`); zero findings; S3 no-change closure with
  CLEAN delta re-audit (full gate suite re-run against a byte-for-byte
  unchanged source tree); 10/10 MOT scenarios match real `motmetrics` 1.4.0;
  coverage ≥98% on all three new modules.
- [`031-wp031-audit.md`](031-wp031-audit.md) — WP-031 "Temporal experiments,
  statistics, and adversarial tooling" audit (`PASS`); zero findings; S3
  no-change closure with CLEAN delta re-audit (full gate suite re-run against
  an unchanged source tree); Welch parity, attack bounds, deterministic seeds,
  and ≥95% touched-file coverage independently re-verified.
- [`032-wp032-audit.md`](032-wp032-audit.md) — WP-032 "Daemon/evaluation
  integration and Phase 5 gate" audit (`PASS`); zero findings; S3 no-change
  closure with CLEAN delta re-audit (full gate suite re-run against a
  byte-for-byte unchanged source tree); MOT equivalence and daemon
  latency/provider acceptance re-confirmed on unchanged evidence; Snyk Code
  0 findings across all four touched scopes.
- [`033-wp033-audit.md`](033-wp033-audit.md) — WP-033 "Unified benchmark runner
  and category migration" audit (`PASS-WITH-FINDINGS`); one D2 finding
  (WP033-F1: two tests failed under the documented `--basetemp` Windows pytest
  invocation, FIXED in S3 `6eb4e8b`) resolved with a CLEAN delta re-audit.
  (Index entry backfilled at WP-034 S4.)
- [`034-wp034-audit.md`](034-wp034-audit.md) — WP-034 "Reporting, figures,
  tables, and profiling" audit (`PASS-WITH-FINDINGS`); four D4 findings
  (WP034-F1: session-brief 15-vs-14 figure-count discrepancy, documentation
  correction carried to S4; WP034-F2: bare `ValueError` in
  `normalize_matplotlib_output`, FIXED `11a97cb`; WP034-F3: inconsistent
  reporting error hierarchy, FIXED `8dbf55d`; WP034-F4: private cross-module
  import between `table_generation` and `figure_generation`, FIXED `8dbf55d`)
  resolved in S3 with a CLEAN delta re-audit.
- [`035-wp035-audit.md`](035-wp035-audit.md) — WP-035 "Reproduction pipeline
  and manifest" audit (`PASS-WITH-FINDINGS`); findings resolved in S3 with a
  CLEAN delta re-audit.
- [`036-wp036-audit.md`](036-wp036-audit.md) — WP-036 "API completion,
  acceptance suite, and migration" audit (`PASS-WITH-FINDINGS`); two D4
  findings (WP036-F1: per-module stub coverage gaps, FIXED in S3; WP036-F2:
  handoff drafting process deviation, AMENDED in S3). Delta re-audit CLEAN.
  Closure table appended with S3 addendum (amendment #33, owning-WP decision
  for D-D rows 31–44).
- [`036b-wp036b-audit.md`](036b-wp036b-audit.md) — WP-036B "Acceptance
  suite port — core, dynamics, model stack, subconscious" audit (`PASS`);
  zero findings; S3 no-change closure with CLEAN delta re-audit. 13
  reference files strict-ported (498 test functions, 8,085 reference
  lines); 489 passed, 9 skipped (all matching reference guards).
- [`036c-wp036c-audit.md`](036c-wp036c-audit.md) — WP-036C "Acceptance
  suite port — integration, y-series, kernels; DV-025" audit (`FAIL`);
  eight findings (two D1, two D2, one D3, four D4) resolved in S3 with
  CLEAN delta re-audit; DV-031 opened; plan amendment #41. 24 reference
  files strict-ported (1,097 test functions, ~15,810 reference lines).
- [`036d-wp036d-audit.md`](036d-wp036d-audit.md) — WP-036D "GPU execution
  path for the ported acceptance suite" audit (`PASS-WITH-FINDINGS`);
  three D4 findings (WP036D-F1/F2/F3) resolved in S3 with CLEAN delta
  re-audit; DV-030 opened.
- [`036e-wp036e-audit.md`](036e-wp036e-audit.md) — WP-036E "GPU
  device-resident execution path" audit (`FAIL`); four findings: CUDA reports
  system rather than device-event timing (D1), the CUDA feature clippy and
  changed-line coverage gates are not green/proven (two D2), and S1 evidence
  metadata is inaccurate (D4). Mandatory S3 owns all four.
- [`036f-wp036f-audit.md`](036f-wp036f-audit.md) — WP-036F "DirectML
  controller-graph execution" audit (`PASS-WITH-FINDINGS`); two findings:
  changed-code coverage on the two new tools is 94% (< 95%) with untested
  error/drift branches (WP036F-F1, D2), and `mypy --strict` nits in the new
  tools (WP036F-F2, D4). The re-exported three-input-`Gemm` controller graph
  is independently verified bit-identical to the PRINet 3.0 reference on CPU
  and `DmlExecutionProvider` executes it within tolerance. Both findings
  `FIXED` in S3 (`0144W`) with a CLEAN delta re-audit (§7 closure table);
  DV-006 DirectML half CLOSED at S4 (`0144X`).
- [`036g-wp036g-audit.md`](036g-wp036g-audit.md) — WP-036G "Deferred-Validation
  register consolidation and permanent dispositions" audit (`PASS`); zero
  findings. Every DV register row maps to one disposition class (terminal,
  permanent, standing external, standing third-party, `AMENDED`, or routed);
  the `chacha20` row (DV-035) meets the Coding Standards §6.2 advisory bar;
  the dormant `gpu-triton.yml` is valid and trigger-dormant; both fragile
  tests pass under independent re-runs. Mandatory S3 no-change closure with a
  CLEAN delta re-audit (§7). Permanent dispositions signed at S4 (`0144AB`,
  PSR-036G §3.3).
- [`037-wp037-audit.md`](037-wp037-audit.md) — WP-037 "Documentation,
  notebooks, paper, and Parity Report draft" audit (`FAIL`); eight findings:
  two trainable Python layers did not train their Rust-owned behavior (WP037-F1,
  D1), four test/process/CI pinning gaps (F2–F5, D2), predecessor-push and
  recurring-nightly-red drift (F6–F7, D3), and notebook output hygiene (F8,
  D4). S3 closed all eight after the corrective canonical-parameter /
  Burn-VJP second delta; F6 is CARRIED(1) to the S4 push gate, F7 is AMENDED
  into DV-036, and the delta re-audit is CLEAN.
- [`036a-wp036a-audit.md`](036a-wp036a-audit.md) — WP-036A "Trainable
  compatibility layers (`prin-train` extension)" audit (`PASS`); zero findings;
  all 13 D-D trainable-layer / discrete-network symbols (rows 31–42, 44)
  delivered as real `prin-train` Rust implementations + thin PyO3 bindings +
  Python `nn.Module` wrappers. S3 (session 0144C) no-change closure with CLEAN
  delta re-audit: the full gate suite re-run against a byte-for-byte unchanged
  source tree (`cargo test --workspace` 1540 passed / 1 ignored; `pytest`
  1266 passed / 9 deselected; fmt/clippy/doc/ruff/mypy/interrogate 97.4%/
  bandit/`cargo audit`/`pip-audit`/Sphinx `-W` all clean;
  `verify_api_surface` `(set(), set())`). One S2 prose figure corrected in the
  closure (`test_wp001_baseline.py` collects 46, not 43) with no verdict
  impact.
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
- [`EXECUTIVE_AUDIT_REPORT_005.md`](EXECUTIVE_AUDIT_REPORT_005.md) — Fifth
  project-level executive audit (EA-005, 2026-08-20), `PASS-WITH-REMEDIATION`;
  delta audit of Phase 4 (WP-022..WP-027, sessions 0085–0108) plus EMA-003/
  EMA-004. Five findings: E-F1 (D2, mypy lint failure — torch missing in CI,
  FIXED), E-F2 (D3, ubuntu runner disk exhaustion, DV-022), E-F3 (D3,
  windows-latest CubeCL timeout, DV-023), E-F4 (D4, phase-4 README status
  mismatch, FIXED), E-F5 (D4, CHANGELOG missing WP-027, FIXED).
- [`EXECUTIVE_AUDIT_REPORT_006.md`](EXECUTIVE_AUDIT_REPORT_006.md) — Sixth
  project-level executive audit (EA-006, 2026-08-26), `PASS-WITH-REMEDIATION`;
  delta audit of Phase 5 close (WP-028..WP-032, sessions 0109–0128) plus two
  post-close CI hotfix commits (`cb5660b`, `5d90427`). Two findings: E-F1
  (D3, hotfix commits never recorded in the deviation ledger, DV-024 left
  stale, FIXED), E-F2 (D3, Phase 4 recommendation R28's precondition — a
  dedicated hotfix/correction session for flaky-test DV-019 before WP-028 S1
  — was never honored and Phase 5 closed anyway; remediated at the
  governance level with a hard entry-condition gate now on WP-033 S1).
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
- [`EXECUTIVE_MATH_AUDIT_REPORT_003.md`](EXECUTIVE_MATH_AUDIT_REPORT_003.md) —
  Third Executive Mathematical Audit (EMA-003, 2026-08-19), Phase 4 close,
  `PASS-WITH-REMEDIATION`; re-verified all 28 existing claims against
  `6e33ca5` (zero regressions) and added 10 new `prin-train`
  trainable-stack claims (first EMA coverage of Phase 4's mathematical
  surface) — 9/10 genuine SymPy/Z3 `PASS`; one new D3 finding (M-F8:
  SCALR-LR-02 `INCONCLUSIVE`, closed by EMA-004). 38 total claims across 7
  ledgers; 30 PASS, 1 INCONCLUSIVE, 7 `REQUIRES_HUMAN_REVIEW` (same M-F3/M-F7
  policy-gate, re-confirmed under DV-013/R20). `[Index entry, plus this
  session's SESSION_REGISTER.md/DEFERRED_VALIDATION_REGISTER.md/CHANGELOG.md
  entries, added retroactively by EMA-004, 2026-08-20 — never added by
  EMA-003 itself; same governance §8.6 gap class as EA-003's own omission
  above.]`
- [`EXECUTIVE_MATH_AUDIT_REPORT_004.md`](EXECUTIVE_MATH_AUDIT_REPORT_004.md) —
  Fourth Executive Mathematical Audit (EMA-004, 2026-08-20), **tool
  remediation session**, `PASS-WITH-REMEDIATION`. Fixed M-F8 (root cause in
  `math-audit-mcp`'s `verify_identity`, not a SymPy limitation as previously
  characterized) and M-F5 (added numeric reconstruction-value comparison to
  `audit_tensor_contract`, closing a gap open since EMA-001, demonstrated
  against real PRINet-3.0 HOSVD reference data). Added a new optional PySAT
  adapter/tool (independent CNF-cardinality/CDCL-SAT solver family) and gave
  `math-audit-mcp` its first-ever git history (M-F6, also open since
  EMA-001). M-F7 unchanged, resolved-by-design. 40 total claims across 8
  ledgers (2 new); zero regressions, 33 PASS, 0 FAIL, 0 INCONCLUSIVE, 7
  `REQUIRES_HUMAN_REVIEW` — all 7 signed off by the maintainer this session
  (report §8), per the DV-013 recorded-sign-off precedent.
- [`EXECUTIVE_MATH_AUDIT_REPORT_005.md`](EXECUTIVE_MATH_AUDIT_REPORT_005.md) —
  Fifth Executive Mathematical Audit (EMA-005, 2026-08-26), Phase 5 close,
  `PASS-WITH-REMEDIATION`. Re-verified all 40 existing claims against
  `79cf971` (zero regressions); authored and executed 6 new
  `prin-daemon-phase5-properties.json` claims (HUN-01, IOU-01, COHEN-01,
  WELCH-DF-01, GAMMA-REFLECT-01, BETA-SYM-01), 6/6 genuine `PASS`. 46 total
  claims across 9 ledgers; 39 PASS, 7 `REQUIRES_HUMAN_REVIEW` (unchanged
  composition from EMA-004). Maintainer sign-off granted 2026-08-26.
- [`EXECUTIVE_MATH_AUDIT_REPORT_006.md`](EXECUTIVE_MATH_AUDIT_REPORT_006.md) —
  Sixth Executive Mathematical Audit (EMA-006, 2026-09-01), Phase 6 mid-phase,
  `PASS-WITH-REMEDIATION`. Re-verified all 46 existing claims against
  `fa427ad` (zero regressions); authored and executed 13 new claims across 2
  new ledgers (`prin-sim-phase6-stats-properties.json`: POLYFIT-01/02,
  SPATCORR-01, BOOTSTRAP-01, LNGAMMA-INT-01, BETAI-BOUND-01;
  `prin-train-phase6-properties.json`: VJP-DYN-01, SPARSITY-01,
  WEIGHTINIT-SYM-01, WEIGHTINIT-XAV-01, ORDERPARAM-01, PACINDEX-01,
  CLAMP-01), 13/13 genuine `PASS`. 59 total claims across 11 ledgers;
  52 PASS, 7 `REQUIRES_HUMAN_REVIEW` (unchanged composition from EMA-005).
  All 13 new claims independently corroborated via Wolfram Engine.
  Maintainer sign-off pending for the 7 `REQUIRES_HUMAN_REVIEW` claims.
- [`EXECUTIVE_DOCUMENTATION_AUDIT_REPORT_001.md`](EXECUTIVE_DOCUMENTATION_AUDIT_REPORT_001.md) —
  First Executive Documentation Audit (EDA-001, 2026-09-01), Phase 6
  mid-phase, `PASS-WITH-REMEDIATION`. Establishes the EDA audit type
  (governance at `DOCS/standards/Executive_Documentation_Audit_Governance_and_Methodology.md`).
  Systematic verification of Phase 6 documentation across 8 dimensions
  (D1–D8): CHANGELOG accuracy, session register consistency, PSR integrity,
  directory README/index currency, cross-reference consistency, DV register
  accuracy, Sphinx build health, and plan amendment traceability. Four
  findings: D-F1 (D2, Sphinx 19 duplicate-object warnings — same
  napoleon/autodoc class as PA4-F2/R26), D-F2 (D3, reports README missing
  036b/c/d entries), D-F3 (D3, audits README missing 036b/c/d entries),
  D-F4 (D3, deviation-ledger CI gate functionally inert for sub-PSRs).
- [`EXECUTIVE_TESTING_AND_CI_AUDIT_REPORT_001.md`](EXECUTIVE_TESTING_AND_CI_AUDIT_REPORT_001.md) —
  First Executive Testing and CI Audit (ETCA-001, 2026-09-01), Phase 6
  mid-phase, `PASS-WITH-REMEDIATION`. Establishes the ETCA audit type
  (governance at `DOCS/standards/Executive_Testing_and_CI_Audit_Governance_and_Methodology.md`,
  plan amendment #42). In-depth verification of the test suite and CI/CD gate
  machinery (EA dimensions E3/E9) across 8 dimensions T1–T8 against the
  Phase 6 test/CI delta. Ten findings, zero D1: T-F1 (D2, `python.yml`
  bandit gate exits 1 → the R17 deviation-ledger and R34 DV-register CI
  enforcement steps never run), T-F2 (D2, ~13 WP-036A reference-parity tests
  hard-fail CI with `ModuleNotFoundError: prinet`), T-F3 (D2, `wp001_baseline`
  gate + 3 tests red from a 12-line session-brief parser cap hit by the
  `0144P` brief), T-F4 (D3, the entire 28-commit WP-036C cycle is unpushed
  and has never been through CI), T-F5 (D3, `repro.yml`/`python.yml` ubuntu
  disk exhaustion — DV-022 class), T-F6 (D3, self-hosted Windows `rust` leg
  24 h runner hang — DV-024 class), T-F7 (D3, no enforcing benchmark-regression
  gate / no `schedule:`d full-suite workflow), T-F8 (D3, perf flake
  quarantined without a DV item), T-F9/T-F10 (D4, local/CI gate drift).
  Read-only; all findings passed to a dedicated remediation session.
  Blocking recommendation: no Phase 6 close push until T-F1/T-F2/T-F3/T-F5/T-F6
  fixed and `origin/main` CI green.
