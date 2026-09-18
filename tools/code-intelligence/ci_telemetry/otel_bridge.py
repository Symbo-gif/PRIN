"""Best-effort OpenTelemetry bridge — never a hard dependency.

The default, always-available exporter is the local JSONL writer in
``ci_telemetry.spans``. If (and only if) the ``opentelemetry`` API package
is importable *and* a global ``TracerProvider`` has already been configured
by the host environment, this module additionally emits each span through
it. It never configures its own exporter, processor, or network endpoint —
it only republishes onto whatever the environment already set up (which is
a local no-op tracer if nothing was configured), so importing this module
can never cause a network call or require any paid/hosted service.
"""

from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ci_telemetry.spans import Span

try:
    from opentelemetry import trace as _otel_trace
    from opentelemetry.trace import Status, StatusCode

    _OTEL_AVAILABLE = True
except ImportError:  # pragma: no cover - exercised only when otel is installed
    _OTEL_AVAILABLE = False

_SCALAR_TYPES = (str, int, float, bool)


def otel_available() -> bool:
    """Return True if the optional OpenTelemetry bridge can be used.

    Returns:
        True if the ``opentelemetry`` API package is importable.
    """
    return _OTEL_AVAILABLE


def maybe_emit_to_otel(span: Span) -> None:
    """Best-effort: re-emit a completed span through OpenTelemetry.

    Args:
        span: The completed local span.

    No-ops silently (never raises) if OpenTelemetry is unavailable, so this
    can be called unconditionally from the hot path without a feature
    check at every call site.
    """
    if not _OTEL_AVAILABLE:
        return
    try:
        tracer = _otel_trace.get_tracer("prin.devtools.code_intelligence")
        start_ns = _iso_to_epoch_ns(span.start_utc)
        end_ns = _iso_to_epoch_ns(span.end_utc)
        otel_span = tracer.start_span(span.operation_name, start_time=start_ns)
        for key, value in span.attributes.items():
            if isinstance(value, _SCALAR_TYPES):
                otel_span.set_attribute(key, value)
        otel_span.set_attribute("prin.trace_id", span.trace_id)
        otel_span.set_attribute("prin.span_id", span.span_id)
        if span.status == "error":
            otel_span.set_status(Status(StatusCode.ERROR, span.error_class or "error"))
        else:
            otel_span.set_status(Status(StatusCode.OK))
        otel_span.end(end_time=end_ns)
    except Exception:
        return


def _iso_to_epoch_ns(iso_timestamp: str) -> int:
    dt = datetime.fromisoformat(iso_timestamp)
    return int(dt.timestamp() * 1_000_000_000)
