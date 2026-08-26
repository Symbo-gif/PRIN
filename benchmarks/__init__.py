"""Unified benchmark suite: nine topic-named category packages plus the
shared ``benchrunner`` CLI and driver infrastructure (WP-033).

Reorganization of PRINet 3.0's 62 quarterly (`y2q*`/`y3q*`/`y4q*`) benchmark
scripts into topic-named category packages sharing common drivers. See
``benchmarks/README.md`` for the category list and usage, and
``DOCS/baselines/wp033_benchmark_traceability.md`` for the legacy-script to
new-module mapping.

All measured quantities are computed by the Rust-backed ``prin`` API or, for
GPU kernel performance, by the existing ``criterion`` benches in
``crates/prin-kernels``; this package contributes only orchestration, timing,
environment capture, and JSON serialization (Coding Standards §1: "the Python
layer contains no numerics").
"""

from __future__ import annotations
