"""``daemon``: subconscious controller latency (p50/p95) across backends.

Consolidates PRINet 3.0's `subconscious_benchmark.py` and
`y3q45_comprehensive_benchmarks.py`. See
`DOCS/baselines/wp033_benchmark_traceability.md`.

Measures the native `SubconsciousDaemon` (`prin.daemon`, WP-029/WP-032)
directly through its Python binding -- the same lock-free control buffer
Rust already measures via `crates/prin-daemon/examples/control_buffer_pilot.rs`
(`EVIDENCE/0125-wp032-s1-daemon-latency.json`), here through the
Python-facing call boundary instead of a Rust-only harness. No latency
computation happens in this module.
"""

from __future__ import annotations

from benchmarks.daemon import control_latency

__all__ = ["control_latency"]
