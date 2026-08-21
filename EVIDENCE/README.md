# EVIDENCE/ — Cycle evidence artefacts

Machine-readable and human-readable evidence files produced during Session
Cycle work (S1 handoffs, S2 audit reproductions, S3 remediation verifications,
S4 gate runs). Each file is named `NNNN-wpNNN-sN-<slug>.<ext>` to match the
session that produced it.

## Current contents

- [`math-audit/`](math-audit/) — Executive Mathematical Audit evidence:
  every `math-audit-mcp` `AuditResult` (`audits/<audit_id>/normalized-result.json`),
  evidence bundle (`audits/bundle-<id>/manifest.json` + `report.md`), the
  append-only `logs/audit-trace.jsonl`, and the consolidated
  `ema-run-summary.json` from `tools/math_audit_run.py`. Append-only per
  `Executive_Mathematical_Audit_Governance_and_Methodology.md` §6; a re-run
  writes fresh evidence with new `audit_id`s rather than overwriting prior
  runs.

- [`0005-wp002-s1-handoff.md`](0005-wp002-s1-handoff.md) — WP-002 S1 handoff
  to the S2 audit for the golden-trajectory corpus and differential harness.
- [`0017-wp005-s1-ort-probe.json`](0017-wp005-s1-ort-probe.json) — WP-005 S1
  ONNX Runtime provider-probe evidence (selected backend, active providers,
  model load/run result, output shape).
- [`0017-wp005-s1-phase0-gate.json`](0017-wp005-s1-phase0-gate.json) — WP-005
  S1 Phase 0 exit-gate evidence (corpus, wheel matrix, spike decisions, ORT
  probe, aggregate readiness).
- [`0109-wp028-s1-controller-provider-report.json`](0109-wp028-s1-controller-provider-report.json)
  — WP-028 S1 subconscious-controller evidence: model manifest verification and
  graph contract, the selection policy over every provider subset, real session
  attempts and their resolved backends on this host, cross-provider output
  agreement, differential parity against PRINet 3.0.0, and the measured
  batch-size sensitivity of the float32 GEMM path.

## Rules

- This directory holds machine-checkable probe/gate artefacts specifically —
  hardware/runtime capability probes, exit-gate readiness snapshots — not a
  mandatory per-WP deliverable. Most work packages verify claims through
  their audit report, Project State Report, and the test/parity/benchmark
  suites themselves; a WP with no hardware probe or gate check of its own
  legitimately adds nothing here (EA-003 finding E-F11, D4 — clarified after
  WP-010..016 added no new files here, which is expected, not a gap).
- Evidence files are committed artefacts; they are not regenerated silently.
- S2 audit reproductions may write fresh evidence with a new timestamp, then
  restore the original S1 baseline to preserve the evidence chain.
- The WP-001 baseline validator and the Phase 0 gate checker reference these
  files by path.
