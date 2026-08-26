# benchmarks/mot/ (multi-object tracking: PhaseTracker vs. SlotAttention)

Clean identity preservation and per-call wall time for both tracker families
on deterministic synthetic sequences (WP-033). Consolidates 14 PRINet 3.0
legacy scripts — see `DOCS/baselines/wp033_benchmark_traceability.md`.

## Contents

- `tracker_comparison.py` — `tracker_identity_preservation`: compares
  `PhaseTracker` and `TemporalSlotAttentionMOT` clean identity preservation
  and timing.

Measurement reuses `prin.experiments.adversarial_evaluate_{phase_tracker,
slot_attention}`, which already generates its deterministic synthetic MOT
sequences and computes identity preservation entirely in
`crates/prin-train/src/adversarial.rs`; no synthetic-data generation or
tracking numerics happens in this package.
