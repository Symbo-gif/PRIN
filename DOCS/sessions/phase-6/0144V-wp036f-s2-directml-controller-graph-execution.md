# Session 0144V — WP-036F S2: Audit — DirectML controller-graph execution

**Status:** COMPLETE
**Audit verdict:** `PASS-WITH-FINDINGS` — two findings (one D2, one D4) handed to mandatory S3 (`0144W`); report `DOCS/audits/036f-wp036f-audit.md`
**Roadmap phase:** 6 — Benchmarks, reproduction, docs, and RC1
**Execution unit:** WP-036F
**Session type:** S2 — Audit
**Predecessor:** [0144U — Coding](0144U-wp036f-s1-directml-controller-graph-execution.md)
**Successor:** [0144W — Remediation](0144W-wp036f-s3-directml-controller-graph-execution.md)
**Authority:** Project Plan §6/§8 and amendments #13/#38; the applicable normative standards. If this brief conflicts with a normative standard, the standard wins.

> This is a prospective execution contract, not completion evidence.

## Mission

Read-only audit of the WP-036F S1 range: the re-exported three-input-`Gemm`
controller graph, the regenerated artefact + checksum, the extended
cross-provider agreement test, and the DirectML/CPU latency measurement.

## Contract

- **Acceptance:** as `0144U` — the re-exported graph is bit-identical to the
  current one on `CPUExecutionProvider` over the 48-case set;
  `DmlExecutionProvider` executes it and agrees with CPU and the 3.0
  references within Testing Standards §3 tolerance; latency recorded; the
  committed artefact + checksum + fixtures are consistent; the controller
  algorithm is unchanged; no `prin.__all__` change; F5 / DoD item 7 DirectML
  condition is met and amendment #13's DirectML deferral is discharged.
- **Non-goals:** any source fix (S3 owns that).

## Required reading

- `DOCS/PRIN_Project_Plan.md` §3.1 F5, §9 item 7, amendments #13/#38
- `DOCS/standards/Development_Workflow_and_Audit_Standards.md` §4 (A1–A10)
- `DOCS/standards/Testing_Standards.md` §1, §3
- `DOCS/audits/TEMPLATE_Audit_Report.md`
- `DOCS/reports/DEFERRED_VALIDATION_REGISTER.md` DV-006
- `EVIDENCE/0109-wp028-s1-controller-provider-report.json` (the prior failure
  evidence)
- WP-036F S1 handoff `DOCS/experiments/0144U-wp036f-s1-handoff.md` and the
  commit range

## Entry conditions

- S1 has claimed its exit gate and supplied its evidence map.
- The repository and S1 commit range are fixed for inspection.

## Expected audit (read-only with respect to source)

1. Create `DOCS/audits/036f-wp036f-audit.md` from the template.
2. Execute A1–A10 with command evidence.
3. Independently re-run the CPU-provider differential test on the re-exported
   graph and confirm bit-identity (within tolerance) with the pre-change
   graph — the graph function must be unchanged.
4. Independently re-run the cross-provider agreement test with
   `DmlExecutionProvider` on the project host; record provider state live; if
   DirectML is unavailable at audit time, record that and rely on the S1
   evidence plus the next CI run.
5. Confirm the committed graph artefact, its checksum, and every reference
   fixture are mutually consistent and regenerable.
6. Confirm the change is confined to the export path (or a graph-transform
   pass) — no controller algorithm, daemon runtime, or backend-selection
   change; no Python numerics; no new `prin` public symbol.
7. Confirm the WP-036F / DV-025 / NPU boundary was respected.
8. Give each finding `WP036F-Fn`, severity D1–D4, evidence, violated clause,
   remedy. Assign PASS / PASS-WITH-FINDINGS / FAIL.

## Required outputs

- Committed `DOCS/audits/036f-wp036f-audit.md`.
- Deviation-ledger delta and an ordered S3 action list.
- Maintainer acknowledgment of the verdict.

## Prohibited

No source fix, plan rewrite, finding suppression, or evidence-free assertion.

## Exit gate

Audit Report and verdict committed. Hand off to S3 even with zero findings.
