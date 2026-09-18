"""Telemetry disabled-by-default behavior, JSONL round-trip, and ingestion tests."""

from __future__ import annotations

from pathlib import Path

import pytest

from ci_graph.store import GraphStore
from ci_telemetry import summary as telemetry_summary
from ci_telemetry.ingest import ingest_telemetry
from ci_telemetry.instrument import new_trace, traced
from ci_telemetry.spans import discover_span_files, read_spans_from_file


def test_traced_is_a_true_noop_when_disabled(tmp_path: Path) -> None:
    telemetry_dir = tmp_path / "traces"
    with new_trace():
        with traced("test.op", enabled=False, telemetry_dir=telemetry_dir):
            pass
    # No directory or file should have been created at all.
    assert not telemetry_dir.exists()


def test_traced_writes_a_span_when_enabled(tmp_path: Path) -> None:
    telemetry_dir = tmp_path / "traces"
    with new_trace():
        with traced(
            "test.op", enabled=True, telemetry_dir=telemetry_dir, attributes={"n": 1}
        ):
            pass
    files = discover_span_files(telemetry_dir)
    assert len(files) == 1
    spans = read_spans_from_file(files[0])
    assert len(spans) == 1
    assert spans[0]["operation_name"] == "test.op"
    assert spans[0]["status"] == "ok"
    assert spans[0]["attributes"] == {"n": 1}


def test_traced_records_error_status_and_reraises(tmp_path: Path) -> None:
    telemetry_dir = tmp_path / "traces"
    with pytest.raises(ValueError, match="boom"):
        with (
            new_trace(),
            traced("test.failing", enabled=True, telemetry_dir=telemetry_dir),
        ):
            raise ValueError("boom")
    files = discover_span_files(telemetry_dir)
    spans = [
        s
        for f in files
        for s in read_spans_from_file(f)
        if s["operation_name"] == "test.failing"
    ]
    assert spans[0]["status"] == "error"
    assert spans[0]["error_class"] == "ValueError"


def test_nested_traced_spans_share_a_trace_id(tmp_path: Path) -> None:
    telemetry_dir = tmp_path / "traces"
    with new_trace() as trace_id:
        with traced("outer", enabled=True, telemetry_dir=telemetry_dir):
            with traced("inner", enabled=True, telemetry_dir=telemetry_dir):
                pass
    files = discover_span_files(telemetry_dir)
    spans = [s for f in files for s in read_spans_from_file(f)]
    assert all(s["trace_id"] == trace_id for s in spans)
    inner = next(s for s in spans if s["operation_name"] == "inner")
    outer = next(s for s in spans if s["operation_name"] == "outer")
    assert inner["parent_span_id"] == outer["span_id"]


def test_ingest_telemetry_is_idempotent(tmp_path: Path) -> None:
    telemetry_dir = tmp_path / "traces"
    with new_trace():
        with traced("cli.index", enabled=True, telemetry_dir=telemetry_dir):
            pass
    store = GraphStore(tmp_path / "graph.db")
    result1 = ingest_telemetry(store, telemetry_dir)
    result2 = ingest_telemetry(store, telemetry_dir)
    assert result1.spans_ingested == 1
    assert result2.spans_ingested == 1  # re-ingest replaces, does not duplicate
    assert store.span_count() == 1
    store.close()


def test_operation_stats_percentiles(tmp_path: Path) -> None:
    telemetry_dir = tmp_path / "traces"
    for _ in range(10):
        with new_trace():
            with traced("cli.query", enabled=True, telemetry_dir=telemetry_dir):
                pass
    store = GraphStore(tmp_path / "graph.db")
    ingest_telemetry(store, telemetry_dir)
    stats = telemetry_summary.operation_stats(store)
    assert len(stats) == 1
    assert stats[0].count == 10
    assert stats[0].p50_ms <= stats[0].p95_ms <= stats[0].p99_ms
    store.close()


def _make_span(*, index: int, operation_name: str, status: str) -> dict[str, object]:
    # Explicit, strictly increasing timestamps (rather than back-to-back
    # `traced()` calls) so ordering by `start_utc` is deterministic.
    stamp = f"2026-09-18T00:00:{index:02d}.000000+00:00"
    return {
        "span_id": f"span-{index}",
        "trace_id": f"trace-{index}",
        "parent_span_id": None,
        "operation_name": operation_name,
        "start_utc": stamp,
        "end_utc": stamp,
        "duration_ms": 1.0,
        "status": status,
        "error_class": "ValueError" if status == "error" else None,
        "attributes": {},
    }


def test_error_rate_never_exceeds_one_under_a_tight_global_limit(
    tmp_path: Path,
) -> None:
    # Regression test (PR #17 devin-ai-integration review): error_count used
    # to be drawn from every span ever ingested for an operation while
    # `count` was drawn from a globally-bounded recent-N sample, so an
    # operation with few recent samples but many historical errors could
    # report error_rate > 1.0 and error_count > count.
    store = GraphStore(tmp_path / "graph.db")
    index = 0
    # Oldest: five historical errors for "cli.rare".
    for _ in range(5):
        store.insert_span(
            _make_span(index=index, operation_name="cli.rare", status="error"),
            source_file="test.jsonl",
        )
        index += 1
    # One more-recent ok span for "cli.rare".
    store.insert_span(
        _make_span(index=index, operation_name="cli.rare", status="ok"),
        source_file="test.jsonl",
    )
    index += 1
    # Newest: a flood of an unrelated operation.
    for _ in range(10):
        store.insert_span(
            _make_span(index=index, operation_name="cli.flood", status="ok"),
            source_file="test.jsonl",
        )
        index += 1

    # A global limit of 11 captures the 10 flood spans plus the single
    # newest "cli.rare" span, excluding its 5 older error spans.
    stats = {
        s.operation_name: s for s in telemetry_summary.operation_stats(store, limit=11)
    }
    rare = stats["cli.rare"]
    assert rare.count == 1
    assert rare.error_count == 0  # the 5 historical errors fell outside the window
    assert rare.error_count <= rare.count
    assert rare.error_rate <= 1.0
    store.close()


def test_malformed_span_lines_are_skipped_not_fatal(tmp_path: Path) -> None:
    telemetry_dir = tmp_path / "traces"
    telemetry_dir.mkdir(parents=True)
    bad_file = telemetry_dir / "spans-20260101.jsonl"
    bad_file.write_text("not json\n{}\n", encoding="utf-8")
    store = GraphStore(tmp_path / "graph.db")
    result = ingest_telemetry(store, telemetry_dir)
    assert result.spans_skipped >= 1
    assert result.spans_ingested == 0
    store.close()
