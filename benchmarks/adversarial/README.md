# benchmarks/adversarial/ (FGSM/PGD robustness evaluation)

Clean-vs-adversarial identity-preservation degradation for both tracker
families under FGSM and PGD attacks (WP-033). Consolidates 2 PRINet 3.0
legacy scripts — see `DOCS/baselines/wp033_benchmark_traceability.md`.

## Contents

- `robustness.py` — `adversarial_robustness`: runs FGSM and PGD against
  `PhaseTracker` and `TemporalSlotAttentionMOT` and reports clean/adversarial
  identity preservation and degradation.

Measurement is `prin.experiments.adversarial_evaluate_{phase_tracker,
slot_attention}`-backed (deterministic synthetic sequences, FGSM/PGD attacks,
and degradation all computed in `crates/prin-train/src/adversarial.rs`); no
attack or metric numerics happen in this package.
