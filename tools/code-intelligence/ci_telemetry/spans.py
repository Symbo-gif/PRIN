"""Dependency-free runtime span model and JSONL writer/reader.

This is the default and always-available telemetry exporter: local JSONL
files, UTC timestamps, no network calls, no hosted collector. Disabled by
default; enabled only via ``PRIN_DEVTOOLS_TELEMETRY=1`` (see ``ci_config``).
Every attribute is a plain JSON scalar/string — never a raw prompt, secret,
or full file content — matching the plan's non-invasive observability
requirement.
"""

from __future__ import annotations

import json
import uuid
from dataclasses import dataclass, field
from datetime import UTC, datetime
from pathlib import Path
from typing import Any


def new_id() -> str:
    """Generate a short random id suitable for span/trace ids.

    Returns:
        A 32-character lowercase hex string.
    """
    return uuid.uuid4().hex


@dataclass
class Span:
    """One completed unit of work.

    Attributes:
        span_id: Unique id for this span.
        trace_id: Groups related spans (e.g. one CLI invocation).
        parent_span_id: The enclosing span's id, or ``None`` at the root.
        operation_name: A short, stable operation name (e.g.
            ``"cli.index"``, ``"mcp.get_hotspots"``, ``"adapter.python"``).
        start_utc: ISO-8601 UTC start timestamp.
        end_utc: ISO-8601 UTC end timestamp.
        duration_ms: Wall-clock duration in milliseconds.
        status: ``"ok"`` or ``"error"``.
        error_class: The exception class name, if ``status == "error"``.
        attributes: Small, non-sensitive JSON-serializable metadata (e.g.
            file counts, node counts — never file contents or secrets).
    """

    span_id: str
    trace_id: str
    parent_span_id: str | None
    operation_name: str
    start_utc: str
    end_utc: str
    duration_ms: float
    status: str
    error_class: str | None
    attributes: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        """Serialize to a plain JSON-compatible dict.

        Returns:
            The span as a dict, ready for ``json.dumps``.
        """
        return {
            "span_id": self.span_id,
            "trace_id": self.trace_id,
            "parent_span_id": self.parent_span_id,
            "operation_name": self.operation_name,
            "start_utc": self.start_utc,
            "end_utc": self.end_utc,
            "duration_ms": self.duration_ms,
            "status": self.status,
            "error_class": self.error_class,
            "attributes": self.attributes,
        }


def utc_now_iso() -> str:
    """Return the current UTC time as an ISO-8601 string.

    Returns:
        e.g. ``"2026-09-18T12:00:00.000000+00:00"``.
    """
    return datetime.now(UTC).isoformat()


class JsonlSpanWriter:
    """Appends spans to a UTC-dated JSONL file, one object per line."""

    def __init__(self, telemetry_dir: Path) -> None:
        """Create a writer targeting a telemetry directory.

        Args:
            telemetry_dir: Directory spans are written into. Created if
                absent.
        """
        self.telemetry_dir = telemetry_dir
        self.telemetry_dir.mkdir(parents=True, exist_ok=True)
        date_tag = datetime.now(UTC).strftime("%Y%m%d")
        self.file_path = self.telemetry_dir / f"spans-{date_tag}.jsonl"

    def write(self, span: Span) -> None:
        """Append one span as a single JSON line.

        Args:
            span: The completed span.
        """
        with self.file_path.open("a", encoding="utf-8") as fh:
            fh.write(json.dumps(span.to_dict(), sort_keys=True))
            fh.write("\n")


def read_spans_from_file(path: Path) -> list[dict[str, Any]]:
    """Read all spans from one JSONL file.

    Args:
        path: Path to a ``spans-*.jsonl`` file.

    Returns:
        Parsed span dicts, skipping any malformed lines (recorded nowhere
        but not fatal — telemetry ingestion must never break on a partial
        write from a crashed process).
    """
    spans: list[dict[str, Any]] = []
    if not path.exists():
        return spans
    with path.open(encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if not line:
                continue
            try:
                spans.append(json.loads(line))
            except json.JSONDecodeError:
                continue
    return spans


def discover_span_files(telemetry_dir: Path) -> list[Path]:
    """List all span JSONL files in a telemetry directory.

    Args:
        telemetry_dir: The directory to scan.

    Returns:
        Sorted paths to ``spans-*.jsonl`` files (empty if the directory does
        not exist).
    """
    if not telemetry_dir.exists():
        return []
    return sorted(telemetry_dir.glob("spans-*.jsonl"))
