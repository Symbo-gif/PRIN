"""Ingest local JSONL runtime spans into the SQLite graph store.

Ingestion is idempotent (``INSERT OR REPLACE`` keyed by ``span_id``), so
re-running it against the same telemetry directory is always safe.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from ci_graph.store import GraphStore
from ci_telemetry.spans import discover_span_files, read_spans_from_file

_REQUIRED_FIELDS = (
    "span_id",
    "trace_id",
    "operation_name",
    "start_utc",
    "end_utc",
    "duration_ms",
    "status",
)


@dataclass
class IngestResult:
    """Summary of one telemetry ingestion pass.

    Attributes:
        files_scanned: Number of ``spans-*.jsonl`` files considered.
        spans_ingested: Number of valid spans written to the store.
        spans_skipped: Number of malformed/incomplete span records skipped.
    """

    files_scanned: int
    spans_ingested: int
    spans_skipped: int


def ingest_telemetry(store: GraphStore, telemetry_dir: Path) -> IngestResult:
    """Load every JSONL span file in a directory into the graph store.

    Args:
        store: An open, writable :class:`~ci_graph.store.GraphStore`.
        telemetry_dir: Directory containing ``spans-*.jsonl`` files.

    Returns:
        A summary of what was ingested.
    """
    files = discover_span_files(telemetry_dir)
    ingested = 0
    skipped = 0
    for path in files:
        for raw_span in read_spans_from_file(path):
            if not all(field in raw_span for field in _REQUIRED_FIELDS):
                skipped += 1
                continue
            store.insert_span(raw_span, source_file=path.name)
            ingested += 1
    store.commit()
    return IngestResult(
        files_scanned=len(files), spans_ingested=ingested, spans_skipped=skipped
    )
