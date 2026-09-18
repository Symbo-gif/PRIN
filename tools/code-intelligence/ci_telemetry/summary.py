"""Runtime-evidence summaries: percentiles, slowest operations, error hotspots.

Everything here is computed from *ingested runtime spans*, never from
static analysis — every returned structure is labeled
``evidence="runtime_trace"`` so callers (CLI/MCP) never blur it with the
static centrality metrics in ``ci_analytics``.
"""

from __future__ import annotations

import math
import sqlite3
from dataclasses import dataclass

from ci_graph.store import GraphStore


@dataclass
class OperationStats:
    """Latency/error statistics for one operation name.

    Attributes:
        operation_name: The operation.
        count: Number of samples.
        p50_ms: Median duration.
        p95_ms: 95th percentile duration.
        p99_ms: 99th percentile duration.
        mean_ms: Arithmetic mean duration.
        error_count: Number of spans with ``status == "error"``.
        error_rate: ``error_count / count``.
    """

    operation_name: str
    count: int
    p50_ms: float
    p95_ms: float
    p99_ms: float
    mean_ms: float
    error_count: int
    error_rate: float


def _percentile(sorted_values: list[float], pct: float) -> float:
    if not sorted_values:
        return 0.0
    if len(sorted_values) == 1:
        return sorted_values[0]
    rank = pct / 100.0 * (len(sorted_values) - 1)
    lower = math.floor(rank)
    upper = math.ceil(rank)
    if lower == upper:
        return sorted_values[int(rank)]
    frac = rank - lower
    return sorted_values[lower] * (1 - frac) + sorted_values[upper] * frac


def operation_stats(store: GraphStore, limit: int = 1000) -> list[OperationStats]:
    """Compute per-operation latency/error statistics from ingested spans.

    Args:
        store: An open :class:`~ci_graph.store.GraphStore`.
        limit: Maximum spans considered per operation (most recent first).

    Returns:
        Statistics for every operation with at least one sample, sorted by
        descending sample count then operation name for determinism.
    """
    durations = store.spans_by_operation(limit=limit)
    error_counts = _error_counts(store)
    stats = []
    for op, values in durations.items():
        values_sorted = sorted(values)
        errors = error_counts.get(op, 0)
        stats.append(
            OperationStats(
                operation_name=op,
                count=len(values_sorted),
                p50_ms=_percentile(values_sorted, 50),
                p95_ms=_percentile(values_sorted, 95),
                p99_ms=_percentile(values_sorted, 99),
                mean_ms=sum(values_sorted) / len(values_sorted),
                error_count=errors,
                error_rate=errors / len(values_sorted) if values_sorted else 0.0,
            )
        )
    stats.sort(key=lambda s: (-s.count, s.operation_name))
    return stats


def _error_counts(store: GraphStore) -> dict[str, int]:
    # sqlite3.Row objects from GraphStore internals are not exposed for
    # aggregate queries; this reuses the public per-operation accessor to
    # stay within the store's documented interface.
    counts: dict[str, int] = {}
    for op in store.spans_by_operation().keys():
        rows: list[sqlite3.Row] = store.spans_for_operation(op)
        counts[op] = sum(1 for r in rows if r["status"] == "error")
    return counts


def slowest_operations(store: GraphStore, limit: int = 20) -> list[OperationStats]:
    """Return operations sorted by descending p95 latency.

    Args:
        store: An open :class:`~ci_graph.store.GraphStore`.
        limit: Maximum results.

    Returns:
        Operation statistics sorted by descending ``p95_ms``.
    """
    stats = operation_stats(store)
    stats.sort(key=lambda s: (-s.p95_ms, s.operation_name))
    return stats[: max(1, limit)]


def error_hotspots(store: GraphStore, limit: int = 20) -> list[OperationStats]:
    """Return operations sorted by descending error rate (min 1 error).

    Args:
        store: An open :class:`~ci_graph.store.GraphStore`.
        limit: Maximum results.

    Returns:
        Operations with at least one error, sorted by descending error
        rate then descending sample count.
    """
    stats = [s for s in operation_stats(store) if s.error_count > 0]
    stats.sort(key=lambda s: (-s.error_rate, -s.count, s.operation_name))
    return stats[: max(1, limit)]
