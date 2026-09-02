# Session 0144X — WP-036F S4: Documentation — DirectML controller-graph execution

**Status:** COMPLETE — all S4 artefacts committed; DV-006 DirectML half CLOSED,
VitisAI/NPU half re-scoped and OPEN; plan amendment #13 DirectML deferral
discharged; PSR `DOCS/reports/036f-project-state.md` issued. WP-036F is closed.
The batched WP-036F `0144U`–`0144X` push (CI over the full range) is the
maintainer's to execute; local gates are green.
**Roadmap phase:** 6 — Benchmarks, reproduction, docs, and RC1
**Execution unit:** WP-036F
**Session type:** S4 — Documentation
**Predecessor:** [0144W — Remediation](0144W-wp036f-s3-directml-controller-graph-execution.md)
**Successor:** [0144Y — Coding (WP-036G S1)](0144Y-wp036g-s1-dv-register-consolidation-and-permanent-dispositions.md)
**Authority:** Project Plan §6/§8 and amendments #13/#38; the applicable normative standards. If this brief conflicts with a normative standard, the standard wins.

> This is a prospective execution contract, not completion evidence.

## Mission

Document the DirectML controller-graph execution path, issue the WP-036F
Project State Report, close the DirectML half of DV-006, discharge amendment
#13's DirectML deferral, and confirm WP-036G (session `0144Y`) entry
conditions.

## Contract

- **Acceptance:** every touched README updated (`crates/prin-daemon/`,
  `tests/`, and wherever the controller export lives); `CHANGELOG.md` entry;
  Sphinx controller/daemon docs and the Migration Guide current;
  `DOCS/reports/DEFERRED_VALIDATION_REGISTER.md` updated — **DV-006 DirectML
  half CLOSED**, item re-scoped to "VitisAI/Ryzen AI NPU only, hardware-gated"
  and remaining OPEN; F5 / DoD item 7 DirectML condition recorded as met;
  amendment #13's WP-005 DirectML deferral marked discharged; docs gates
  green; PSR `DOCS/reports/036f-project-state.md` issued;
  `tools/check_deviation_ledger.py` and `tools/check_dv_register_gates.py`
  run and green.
- **Non-goals:** functional feature work; WP-036G; NPU/VitisAI; the WP-038
  tag push.

## Required reading

- `DOCS/PRIN_Project_Plan.md` §3.1 F5, §9 item 7, amendments #13/#38
- `DOCS/standards/Documentation_Standards.md` §7
- `DOCS/audits/036f-wp036f-audit.md` including its CLEAN closure table
- `DOCS/reports/DEFERRED_VALIDATION_REGISTER.md` DV-006

## Entry conditions

- S3 delta re-audit is CLEAN; no unresolved D1/D2 finding exists.

## Expected documentation closure

1. Update every README touched in S1–S3.
2. Update `CHANGELOG.md`; update Sphinx controller/daemon pages and the
   Migration Guide for the re-exported graph; note the provider-latency
   figures.
3. Update `DOCS/reports/DEFERRED_VALIDATION_REGISTER.md`: **DV-006** DirectML
   half CLOSED (cite `036f-wp036f-audit.md`, the `0144U` handoff, the
   cross-provider evidence); re-scope the row to the VitisAI/NPU
   hardware-gated remainder, which stays OPEN with the same
   standing-external-disposition class as DV-001; record that plan amendment
   #13's DirectML condition is discharged.
4. Run documentation, link, quality, security, and test gates; confirm CI
   green on the pushed range.
5. Write `DOCS/reports/036f-project-state.md`: metric trends (DirectML
   execution + agreement, latency, differential bit-identity), cumulative
   deviation ledger, amendment #38, risks, trajectory verdict, and the
   **declaration of the next WP (WP-036G)** quoting the `0144Y` brief.
6. Confirm WP-036G (session `0144Y`) entry conditions and record maintainer
   approval before its S1 begins.
7. Update this session's status and the master register from verified
   evidence.

## Required outputs

- Updated READMEs and docs; CHANGELOG entry; warning-free docs gates.
- Approved `DOCS/reports/036f-project-state.md`.
- Green local gates and CI over the batched WP-036F range.
- DV register: DV-006 DirectML half CLOSED; VitisAI/NPU remainder OPEN,
  re-scoped.

## Prohibited

Functional feature work. A code defect discovered here becomes a governed
correction cycle.

## Exit gate

All S4 artefacts committed; the S4 push carries the full WP-036F S1–S4 range
and CI is green. WP-036F is closed; only then may WP-036G (`0144Y`) begin.
