"""``training``: training throughput, HEP vs. BPTT, optimizer comparisons.

Consolidates PRINet 3.0's `mnist_subset.py`, `oscillobench.py`,
`phase1_bf_extension.py`, `phase1_bf_tost_resolution.py`,
`phase3_scientific_experiments.py`, `phase4_theoretical_verification.py`,
`phase_to_rate_benchmark.py`, `q2_benchmarks.py`, and
`scalr_vs_adam_benchmark.py`. See
`DOCS/baselines/wp033_benchmark_traceability.md`.

Measurement uses the Rust-native training loop (`prin.train.train_phase_tracker`,
`crates/prin-train/src/trainer.rs`: Adam + warmup/cosine LR + gradient
clipping + early stopping); this module performs no training numerics
itself. This category currently covers *training throughput*; a direct
HEP-vs-BPTT algorithm toggle and the ported `SCALR`/`RIP`/`SyncGD`
comparison harness are not yet exposed at this call boundary -- recorded as
a limitation in the traceability doc rather than invented.
"""

from __future__ import annotations

from benchmarks.training import throughput

__all__ = ["throughput"]
