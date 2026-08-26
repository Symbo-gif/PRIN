# benchmarks/training/ (training throughput)

Wall time and epochs/sec for the Rust-native `PhaseTracker` training loop
(WP-033). Consolidates 9 PRINet 3.0 legacy scripts — see
`DOCS/baselines/wp033_benchmark_traceability.md`.

## Contents

- `throughput.py` — `training_throughput`: times
  `prin.train.train_phase_tracker` at a small, fast fixed problem size.

All Adam updates, learning-rate scheduling, gradient clipping, and dataset
generation run in `crates/prin-train`; this package only times the call. This
category currently covers *training throughput*; a direct HEP-vs-BPTT
algorithm toggle and the ported `SCALR`/`RIP`/`SyncGD` comparison harness are
not yet exposed at this call boundary — recorded as a limitation rather than
invented (see the WP-033 S1 handoff note).
