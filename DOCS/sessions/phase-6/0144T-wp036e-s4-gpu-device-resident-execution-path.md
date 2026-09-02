# Session 0144T — WP-036E S4: Documentation — GPU device-resident execution path

**Status:** COMPLETE
**Roadmap phase:** 6 — Benchmarks, reproduction, docs, and RC1
**Execution unit:** WP-036E
**Session type:** S4 — Documentation
**Predecessor:** [0144S — Remediation](0144S-wp036e-s3-gpu-device-resident-execution-path.md)
**Successor:** [0144U — Coding (WP-036F S1)](0144U-wp036f-s1-directml-controller-graph-execution.md)
**Authority:** Project Plan §6/§8 and amendments #31/#33/#36/#37/#38; the applicable normative standards. If this brief conflicts with a normative standard, the standard wins.

> This is a prospective execution contract, not completion evidence.

## Mission

Document the device-resident GPU execution path, issue the WP-036E Project
State Report, close DV-030 and DV-003, and confirm WP-036F (session `0144U`)
entry conditions.

## Contract

- **Acceptance:** every touched README updated (`crates/prin-kernels/`,
  `crates/prin-sim/`, `crates/prin-py/`, `tests/`); `CHANGELOG.md` entry;
  `DOCS/sphinx/parity_report.rst` GPU-vs-CPU tolerance table current;
  `.pyi` / Migration Guide current for any new binding callable; `gpu.yml`
  documented (8 activated tests); `DOCS/reports/DEFERRED_VALIDATION_REGISTER.md`
  updated — **DV-030 CLOSED**, **DV-003 CLOSED**, with the evidence chain
  cited; docs gates green; PSR `DOCS/reports/036e-project-state.md` issued;
  `tools/check_deviation_ledger.py` and `tools/check_dv_register_gates.py`
  run and green.
- **Non-goals:** functional feature work; WP-036F/WP-036G; DV-005 (record the
  boundary, do not close it here — it is closed as `AMENDED` by amendment
  #38); the WP-038 tag push (DV-010).

## Required reading

- `DOCS/PRIN_Project_Plan.md` and amendments #31/#33/#36/#37/#38
- `DOCS/standards/Documentation_Standards.md` §7
- `DOCS/audits/036e-wp036e-audit.md` including its CLEAN closure table
- `DOCS/reports/DEFERRED_VALIDATION_REGISTER.md` DV-003, DV-030, DV-001, DV-005

## Entry conditions

- S3 delta re-audit is CLEAN; no unresolved D1/D2 finding exists.

## Expected documentation closure

1. Update every README touched in S1–S3; update `tests/README.md` GPU marker
   policy and count (7 → 8).
2. Update `CHANGELOG.md`; update `DOCS/sphinx/parity_report.rst` with the
   final GPU-vs-CPU kernel-equivalence tolerance table and any device-event
   timing note; update the Migration Guide / `.pyi` for any user-visible new
   binding callable.
3. Update `DOCS/reports/DEFERRED_VALIDATION_REGISTER.md`: move **DV-030** and
   **DV-003** to CLOSED with the WP-036E evidence chain
   (`036e-wp036e-audit.md`, `0144Q` handoff, runner evidence); note that
   DV-005 and DV-001 remain and are **not** closed by this WP.
4. Run documentation, link, quality, security, and CPU acceptance-subset
   gates; confirm the latest `gpu.yml` run is green.
5. Write `DOCS/reports/036e-project-state.md`: measured metric trends (8 GPU
   tests activated, device-event timing, VRAM ratio, CPU-suite
   non-regression, coverage), cumulative deviation ledger, amendment #38,
   risks, trajectory verdict, and the **declaration of the next WP (WP-036F)**
   quoting the `0144U` brief.
6. Confirm WP-036F (session `0144U`) entry conditions and record maintainer
   approval before its S1 begins.
7. Update this session's status and the master register from verified
   evidence.

## Required outputs

- Updated READMEs and docs; CHANGELOG entry; warning-free docs gates.
- Approved `DOCS/reports/036e-project-state.md`.
- Green local gates over the batched WP-036E range; green `gpu.yml` run.
- DV register: DV-030 and DV-003 CLOSED.

## Prohibited

Functional feature work. A code defect discovered here becomes a governed
correction cycle.

## Exit gate

All S4 artefacts committed; the S4 push carries the full WP-036E S1–S4 range
and CI (incl. `gpu.yml`) is green. WP-036E is closed; only then may WP-036F
(`0144U`) begin.
