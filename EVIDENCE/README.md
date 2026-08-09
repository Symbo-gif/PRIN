# EVIDENCE/ — Cycle evidence artefacts

Machine-readable and human-readable evidence files produced during Session
Cycle work (S1 handoffs, S2 audit reproductions, S3 remediation verifications,
S4 gate runs). Each file is named `NNNN-wpNNN-sN-<slug>.<ext>` to match the
session that produced it.

## Current contents

- [`0005-wp002-s1-handoff.md`](0005-wp002-s1-handoff.md) — WP-002 S1 handoff
  to the S2 audit for the golden-trajectory corpus and differential harness.
- [`0017-wp005-s1-ort-probe.json`](0017-wp005-s1-ort-probe.json) — WP-005 S1
  ONNX Runtime provider-probe evidence (selected backend, active providers,
  model load/run result, output shape).
- [`0017-wp005-s1-phase0-gate.json`](0017-wp005-s1-phase0-gate.json) — WP-005
  S1 Phase 0 exit-gate evidence (corpus, wheel matrix, spike decisions, ORT
  probe, aggregate readiness).

## Rules

- Evidence files are committed artefacts; they are not regenerated silently.
- S2 audit reproductions may write fresh evidence with a new timestamp, then
  restore the original S1 baseline to preserve the evidence chain.
- The WP-001 baseline validator and the Phase 0 gate checker reference these
  files by path.
