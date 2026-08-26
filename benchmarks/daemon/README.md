# benchmarks/daemon/ (subconscious controller latency)

`SubconsciousDaemon.get_control()` read latency (p50/p95) via the native
Python binding (WP-033). Consolidates 2 PRINet 3.0 legacy scripts — see
`DOCS/baselines/wp033_benchmark_traceability.md`.

## Contents

- `control_latency.py` — `daemon_control_latency`: submits one state, waits
  for the first inference, then times `get_control()` over ≥10 iterations.

Measures the native `SubconsciousDaemon` (`prin.daemon`, WP-029/WP-032)
directly — the same lock-free control buffer Rust already measures via
`crates/prin-daemon/examples/control_buffer_pilot.rs`
(`EVIDENCE/0125-wp032-s1-daemon-latency.json`), here through the Python call
boundary applications actually use instead of a Rust-only harness. No
latency computation happens in this package.
