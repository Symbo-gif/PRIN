"""``benchrunner``: the single CLI entry point for all nine benchmark categories.

Mission: "Implement benchrunner CLI, shared configuration/environment
capture, and migrate all legacy scripts into nine topic categories without
schema changes." Benchmarking and Reproducibility Standards §2.1: "Benchmarks
live in `benchmarks/` as 9 topic-named category packages sharing common
drivers, executed via the single `benchrunner` CLI. No one-off scripts."

Usage:
    python -m benchmarks.benchrunner --list
    python -m benchmarks.benchrunner --category scaling --out benchmarks/results/
"""

from __future__ import annotations
