"""``adversarial``: FGSM/PGD robustness evaluation.

Consolidates PRINet 3.0's `y4q1_8_benchmarks.py` and `run_q18_individual.py`.
See `DOCS/baselines/wp033_benchmark_traceability.md`.

Measurement is `prin.experiments.adversarial_evaluate_{phase_tracker,
slot_attention}`-backed (deterministic synthetic sequences, FGSM/PGD attacks,
and identity-preservation degradation all computed in
`crates/prin-train/src/adversarial.rs`); this module performs no attack or
metric numerics itself.
"""

from __future__ import annotations

from benchmarks.adversarial import robustness

__all__ = ["robustness"]
