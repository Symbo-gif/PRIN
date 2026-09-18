"""Opt-in span instrumentation for the code-intelligence subsystem's own entry points.

Import and use :func:`traced` at the boundaries this subsystem controls
(CLI commands, MCP tool handlers, indexer adapter passes). When telemetry is
disabled (the default), ``traced`` is a true no-op: it does not construct a
writer, touch the filesystem, or measure time, so behavior is identical to
having no instrumentation at all.

Per the plan's assumption #4, this module is *not* wired into
``crates/prin-*`` or ``python/prin`` — doing so would edit governed,
audited core code from an "isolated" add-on. It is exported so a future,
separately-governed PR could choose to import and apply it there.
"""

from __future__ import annotations

import contextvars
import time
from collections.abc import Generator, Iterator
from contextlib import contextmanager
from pathlib import Path
from typing import Any

from ci_telemetry.otel_bridge import maybe_emit_to_otel
from ci_telemetry.spans import JsonlSpanWriter, Span, new_id, utc_now_iso

_current_trace_id: contextvars.ContextVar[str | None] = contextvars.ContextVar(
    "prin_ci_trace_id", default=None
)
_current_span_id: contextvars.ContextVar[str | None] = contextvars.ContextVar(
    "prin_ci_span_id", default=None
)

_writer: JsonlSpanWriter | None = None
_writer_dir: Path | None = None


def _get_writer(telemetry_dir: Path) -> JsonlSpanWriter:
    global _writer, _writer_dir
    if _writer is None or _writer_dir != telemetry_dir:
        _writer = JsonlSpanWriter(telemetry_dir)
        _writer_dir = telemetry_dir
    return _writer


@contextmanager
def traced(
    operation_name: str,
    *,
    enabled: bool,
    telemetry_dir: Path | None = None,
    attributes: dict[str, Any] | None = None,
) -> Iterator[None]:
    """Time a block of code and emit a span if telemetry is enabled.

    Args:
        operation_name: A short, stable operation name (e.g.
            ``"cli.index"``).
        enabled: Whether telemetry emission is active. Callers pass this
            explicitly (from ``ci_config.Settings.telemetry_enabled``)
            rather than re-reading the environment on every call.
        telemetry_dir: Required when ``enabled`` is True; the directory
            JSONL span files are written into.
        attributes: Small, non-sensitive JSON-serializable metadata.

    Yields:
        Nothing; the block runs as normal. On exception, a span with
        ``status="error"`` is emitted (if enabled) and the exception is
        re-raised unchanged.
    """
    if not enabled:
        yield
        return

    assert telemetry_dir is not None, "telemetry_dir is required when enabled=True"
    trace_id = _current_trace_id.get() or new_id()
    parent_span_id = _current_span_id.get()
    span_id = new_id()
    trace_token = _current_trace_id.set(trace_id)
    span_token = _current_span_id.set(span_id)
    start_perf = time.perf_counter()
    start_utc = utc_now_iso()
    status = "ok"
    error_class: str | None = None
    try:
        yield
    except Exception as exc:
        status = "error"
        error_class = type(exc).__name__
        raise
    finally:
        duration_ms = (time.perf_counter() - start_perf) * 1000.0
        span = Span(
            span_id=span_id,
            trace_id=trace_id,
            parent_span_id=parent_span_id,
            operation_name=operation_name,
            start_utc=start_utc,
            end_utc=utc_now_iso(),
            duration_ms=duration_ms,
            status=status,
            error_class=error_class,
            attributes=attributes or {},
        )
        _get_writer(telemetry_dir).write(span)
        maybe_emit_to_otel(span)
        _current_span_id.reset(span_token)
        _current_trace_id.reset(trace_token)


@contextmanager
def new_trace() -> Generator[str, None, None]:
    """Force a new trace id for the duration of a block (e.g. one CLI run).

    Yields:
        The new trace id.
    """
    trace_id = new_id()
    token = _current_trace_id.set(trace_id)
    try:
        yield trace_id
    finally:
        _current_trace_id.reset(token)
