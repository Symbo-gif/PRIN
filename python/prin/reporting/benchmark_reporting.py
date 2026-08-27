"""Deterministic Markdown reporting for PRIN benchmark JSON artefacts.

This module ports the public reporting helpers from PRINet 3.0 while removing
its implicit wall-clock timestamp.  Callers may supply ``generated_at`` when a
stored artefact timestamp is required; otherwise generated output is byte
stable for unchanged inputs.  Report writes are confined to the repository's
declared benchmark/documentation output trees and operating-system temp tree.
"""

from __future__ import annotations

import json
import math
import tempfile
from dataclasses import dataclass
from datetime import UTC, datetime
from numbers import Real
from pathlib import Path
from typing import Any

_REPO_ROOT = Path(__file__).resolve().parents[3]
_ALLOWED_OUTPUT_ROOTS = (
    (_REPO_ROOT / "benchmarks" / "results").resolve(),
    (_REPO_ROOT / "DOCS" / "test_and_benchmark_results").resolve(),
    Path(tempfile.gettempdir()).resolve(),
)

__all__ = [
    "ReportInputError",
    "ReportOutputError",
    "generate_benchmark_report",
    "generate_leaderboard",
    "generate_scalr_metrics_report",
]


class ReportInputError(ValueError):
    """Raised when a public reporting input is invalid."""


class ReportOutputError(ValueError):
    """Raised when a report destination escapes the declared output roots."""


class _ArtifactError(ValueError):
    """Raised when one benchmark artefact has an unsupported structure."""


@dataclass(frozen=True)
class _LeaderboardRow:
    """One normalized leaderboard row."""

    model: str
    benchmark: str
    metric: str
    value: float


def generate_benchmark_report(
    results_dir: str | Path,
    output_path: str | Path | None = None,
    title: str = "PRINet Benchmark Report",
    *,
    generated_at: datetime | str | None = None,
) -> str:
    """Aggregate benchmark JSON files into deterministic Markdown.

    This preserves the PRINet 3.0 summary and detail layouts.  Unlike the
    historical implementation, no current time is read implicitly.

    Args:
        results_dir: Directory containing top-level ``*.json`` artefacts.
        output_path: Optional Markdown destination. It must resolve below
            ``benchmarks/results/``, ``DOCS/test_and_benchmark_results/``, or
            the operating-system temporary directory.
        title: Non-empty, single-line report title.
        generated_at: Optional explicit provenance timestamp. A timezone-aware
            datetime is normalized to minute precision in UTC. A non-empty
            string is emitted verbatim after Markdown escaping for compatibility
            with timestamps already stored in historical artefacts.

    Returns:
        The complete Markdown report.

    Raises:
        ReportInputError: If a public input is invalid.
        ReportOutputError: If ``output_path`` escapes the declared roots.
        OSError: If an allowed destination cannot be created or written.

    Examples:
        >>> generate_benchmark_report("benchmarks/results").startswith("# ")
        True
    """
    directory = _validate_results_dir(results_dir)
    clean_title = _validate_title(title)
    timestamp = _normalize_generated_at(generated_at)
    json_files = sorted(directory.glob("*.json"), key=lambda path: path.name)

    sections = [f"# {_escape_markdown(clean_title)}\n"]
    if timestamp is not None:
        sections.append(f"_Generated: {timestamp}_\n")

    if not json_files:
        sections.append("**No benchmark JSON files found.**\n")
        return _finish_report(sections, output_path)

    sections.extend(
        [
            "## Summary\n",
            "| File | Status | Key Metrics |",
            "|------|--------|-------------|",
        ]
    )
    loaded: dict[Path, dict[str, Any] | _ArtifactError] = {}
    for json_file in json_files:
        try:
            data = _read_artifact(json_file)
            loaded[json_file] = data
            status = _escape_markdown(_extract_status(data))
            metrics = _escape_markdown(_extract_key_metrics(data))
            sections.append(f"| `{json_file.name}` | {status} | {metrics} |")
        except _ArtifactError as exc:
            loaded[json_file] = exc
            sections.append(
                f"| `{json_file.name}` | ERROR | Parse error: "
                f"{_escape_markdown(str(exc))} |"
            )

    sections.extend(["", "## Detailed Results\n"])
    for json_file in json_files:
        sections.append(f"### {json_file.stem}\n")
        value = loaded[json_file]
        if isinstance(value, _ArtifactError):
            sections.append("_Error reading file._\n")
        else:
            try:
                sections.append(_format_detail(value))
            except _ArtifactError:
                sections.append("_Error reading file._\n")
    return _finish_report(sections, output_path)


def generate_leaderboard(
    results_dir: str | Path,
    output_path: str | Path | None = None,
    *,
    generated_at: datetime | str | None = None,
) -> str:
    """Generate a deterministic ranked leaderboard from benchmark JSON files.

    The extraction rules preserve the historical CLEVR-N and OscilloBench JSON
    shapes. Values are ranked descending, matching PRINet 3.0 behavior, with
    deterministic textual tie-breakers.

    Args:
        results_dir: Directory containing top-level ``*.json`` artefacts.
        output_path: Optional confined Markdown destination.
        generated_at: Optional explicit timestamp or provenance string. Aware
            datetimes are normalized to UTC; ``None`` emits no timestamp.

    Returns:
        The complete Markdown leaderboard.

    Raises:
        ReportInputError: If a public input is invalid.
        ReportOutputError: If ``output_path`` escapes the declared roots.
        OSError: If an allowed destination cannot be created or written.
    """
    directory = _validate_results_dir(results_dir)
    timestamp = _normalize_generated_at(generated_at)
    rows: list[_LeaderboardRow] = []
    for json_file in sorted(directory.glob("*.json"), key=lambda path: path.name):
        try:
            rows.extend(
                _extract_leaderboard_rows(json_file.stem, _read_artifact(json_file))
            )
        except _ArtifactError:
            continue

    rows.sort(
        key=lambda row: (
            -row.value,
            row.model.casefold(),
            row.benchmark.casefold(),
            row.metric.casefold(),
        )
    )
    sections = ["# PRINet Leaderboard\n"]
    if timestamp is not None:
        sections.append(f"_Generated: {timestamp}_\n")
    if not rows:
        sections.append("No leaderboard data found.\n")
    else:
        sections.extend(
            [
                "| Rank | Model | Benchmark | Metric | Value |",
                "|------|-------|-----------|--------|-------|",
            ]
        )
        for rank, row in enumerate(rows, 1):
            sections.append(
                f"| {rank} | {_escape_markdown(row.model)} | "
                f"{_escape_markdown(row.benchmark)} | "
                f"{_escape_markdown(row.metric)} | {row.value:.4f} |"
            )
    sections.append("")
    return _finish_report(sections, output_path)


def generate_scalr_metrics_report(
    r_history: list[float],
    window: int = 50,
    output_path: str | Path | None = None,
) -> str:
    """Generate the legacy SCALR synchronization-stability report.

    This reporting-only normalization computes the population coefficient of
    variation over sliding windows and lists at most 20 windows whose CV is
    greater than 0.1. It does not implement or replace any Rust model numeric.

    Args:
        r_history: Non-empty order-parameter history. Every value must be a
            finite real number in the closed interval ``[0, 1]``.
        window: Positive integer sliding-window size.
        output_path: Optional confined Markdown destination.

    Returns:
        The complete Markdown report.

    Raises:
        ReportInputError: If history values or ``window`` are invalid.
        ReportOutputError: If ``output_path`` escapes the declared roots.
        OSError: If an allowed destination cannot be created or written.
    """
    history = _validate_r_history(r_history)
    if isinstance(window, bool) or not isinstance(window, int) or window <= 0:
        raise ReportInputError(f"window must be a positive integer, got {window!r}")

    sections = [
        "# SCALR Metrics Report\n",
        f"- Total epochs: {len(history)}",
        f"- Analysis window: {window}\n",
    ]
    if len(history) < window:
        sections.append("_Insufficient data for windowed analysis._\n")
        return _finish_report(sections, output_path)

    cvs: list[float] = []
    for end in range(window, len(history) + 1):
        values = history[end - window : end]
        mean = sum(values) / len(values)
        variance = sum((value - mean) ** 2 for value in values) / len(values)
        cvs.append(math.sqrt(variance) / max(mean, 1e-8))
    desync_events = [(index + window, cv) for index, cv in enumerate(cvs) if cv > 0.1]

    sections.extend(
        [
            "## Order Parameter Summary\n",
            f"- Final r(t): {history[-1]:.4f}",
            f"- Mean r(t): {sum(history) / len(history):.4f}",
            f"- Mean CV: {sum(cvs) / len(cvs):.4f}",
            f"- Max CV: {max(cvs):.4f}",
            f"- Desync events (CV > 0.1): {len(desync_events)}\n",
        ]
    )
    if desync_events:
        sections.extend(
            [
                "### Desynchronization Events\n",
                "| Epoch | CV |",
                "|-------|----|",
            ]
        )
        sections.extend(f"| {epoch} | {cv:.4f} |" for epoch, cv in desync_events[:20])
        sections.append("")
    return _finish_report(sections, output_path)


def _coerce_path(value: str | Path, name: str) -> Path:
    """Convert a supported path-like public value into ``Path``."""
    if not isinstance(value, (str, Path)):
        raise ReportInputError(
            f"{name} must be a string or Path, got {type(value).__name__}"
        )
    if isinstance(value, str) and not value.strip():
        raise ReportInputError(f"{name} must not be empty")
    return Path(value)


def _validate_results_dir(value: str | Path) -> Path:
    """Resolve and validate an input artefact directory."""
    path = _coerce_path(value, "results_dir")
    try:
        resolved = path.resolve(strict=True)
    except FileNotFoundError as exc:
        raise ReportInputError(f"results_dir does not exist: {path}") from exc
    except OSError as exc:
        raise ReportInputError(f"results_dir cannot be resolved: {path}") from exc
    if not resolved.is_dir():
        raise ReportInputError(f"results_dir is not a directory: {path}")
    return resolved


def _validate_title(title: str) -> str:
    """Validate the report title."""
    if (
        not isinstance(title, str)
        or not title.strip()
        or "\n" in title
        or "\r" in title
    ):
        raise ReportInputError("title must be a non-empty single-line string")
    return title.strip()


def _normalize_generated_at(value: datetime | str | None) -> str | None:
    """Return a deterministic display timestamp from explicit caller input."""
    if value is None:
        return None
    if isinstance(value, datetime):
        if value.tzinfo is None or value.utcoffset() is None:
            raise ReportInputError("generated_at datetime must be timezone-aware")
        return value.astimezone(UTC).strftime("%Y-%m-%d %H:%M UTC")
    if (
        isinstance(value, str)
        and value.strip()
        and "\n" not in value
        and "\r" not in value
    ):
        return _escape_markdown(value.strip())
    raise ReportInputError(
        "generated_at must be None, a timezone-aware datetime, or a non-empty "
        "single-line string"
    )


def _validate_output_path(value: str | Path) -> Path:
    """Resolve an output path and enforce declared-root confinement."""
    path = _coerce_path(value, "output_path")
    resolved = path.resolve()
    if any(
        resolved == root or root in resolved.parents for root in _ALLOWED_OUTPUT_ROOTS
    ):
        return resolved
    raise ReportOutputError(
        f"{path} resolves outside the declared output roots "
        "(benchmarks/results/, DOCS/test_and_benchmark_results/, temp dirs): "
        f"{resolved}"
    )


def _finish_report(sections: list[str], output_path: str | Path | None) -> str:
    """Join report sections and optionally write the confined result."""
    report = "\n".join(sections)
    if output_path is not None:
        destination = _validate_output_path(output_path)
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_text(report, encoding="utf-8")
    return report


def _read_artifact(path: Path) -> dict[str, Any]:
    """Read one JSON artefact and require an object at its root."""
    try:
        value: Any = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise _ArtifactError(
            f"invalid JSON at line {exc.lineno}, column {exc.colno}"
        ) from exc
    except (OSError, UnicodeError) as exc:
        raise _ArtifactError("file could not be read as UTF-8 JSON") from exc
    if not isinstance(value, dict):
        raise _ArtifactError("top-level JSON value must be an object")
    return value


def _extract_status(data: dict[str, Any]) -> str:
    """Extract the historical summary status from one artefact."""
    if "status" in data:
        return str(data["status"])
    benchmarks = data.get("benchmarks")
    if isinstance(benchmarks, list):
        statuses = [
            str(benchmark.get("status", "UNKNOWN"))
            for benchmark in benchmarks
            if isinstance(benchmark, dict)
        ]
        if statuses and all(status == "PASS" for status in statuses):
            return "ALL PASS"
        failures = sum(status in {"FAIL", "ERROR"} for status in statuses)
        return f"{len(statuses) - failures}/{len(statuses)} PASS"
    return "OK"


def _finite_number(value: Any, name: str) -> float:
    """Return one finite, non-boolean real as a float."""
    if isinstance(value, bool) or not isinstance(value, Real):
        raise _ArtifactError(f"{name} must be a finite real number")
    number = float(value)
    if not math.isfinite(number):
        raise _ArtifactError(f"{name} must be a finite real number")
    return number


def _extract_key_metrics(data: dict[str, Any]) -> str:
    """Extract key metrics using the PRINet 3.0 field conventions."""
    parts: list[str] = []
    for key in ("test_acc", "accuracy", "final_accuracy"):
        if key in data:
            parts.append(f"{key}={_finite_number(data[key], key):.4f}")
    for key in ("wall_time_s", "elapsed_s"):
        if key in data:
            parts.append(f"time={_finite_number(data[key], key):.1f}s")
    if "param_count" in data:
        parts.append(f"params={data['param_count']}")
    if isinstance(data.get("benchmarks"), list):
        parts.append(f"{len(data['benchmarks'])} sub-benchmarks")
    return ", ".join(parts) if parts else "—"


def _format_detail(data: dict[str, Any]) -> str:
    """Format one benchmark object as a historical Markdown detail block."""
    lines: list[str] = []
    for key, value in data.items():
        if key in {"benchmarks", "results", "raw_data"}:
            continue
        if isinstance(value, (str, int, float, bool)):
            lines.append(
                f"- **{_escape_markdown(str(key))}**: {_escape_markdown(str(value))}"
            )

    benchmarks = data.get("benchmarks")
    if isinstance(benchmarks, list):
        lines.append("\n**Sub-benchmarks:**\n")
        for benchmark in benchmarks:
            if isinstance(benchmark, dict):
                name = benchmark.get("name", benchmark.get("benchmark", "?"))
                status = benchmark.get("status", "?")
                lines.append(
                    f"- {_escape_markdown(str(name))}: {_escape_markdown(str(status))}"
                )

    results = data.get("results")
    if isinstance(results, dict):
        lines.extend(
            [
                "\n**Model Results:**\n",
                "| Model | Metric | Value |",
                "|-------|--------|-------|",
            ]
        )
        for model_name, model_results in results.items():
            if isinstance(model_results, list):
                for result in model_results:
                    if isinstance(result, dict) and "test_acc" in result:
                        accuracy = _finite_number(result["test_acc"], "test_acc")
                        count = result.get("n_items", "?")
                        lines.append(
                            f"| {_escape_markdown(str(model_name))} "
                            f"(N={_escape_markdown(str(count))}) | test_acc | "
                            f"{accuracy:.4f} |"
                        )
            elif isinstance(model_results, Real) and not isinstance(
                model_results, bool
            ):
                value = _finite_number(model_results, str(model_name))
                lines.append(
                    f"| {_escape_markdown(str(model_name))} | value | {value} |"
                )
    lines.append("")
    return "\n".join(lines)


def _extract_leaderboard_rows(
    benchmark_name: str, data: dict[str, Any]
) -> list[_LeaderboardRow]:
    """Normalize historical CLEVR-N and OscilloBench result shapes."""
    rows: list[_LeaderboardRow] = []
    for model, values in data.items():
        if not isinstance(values, list):
            continue
        for entry in values:
            if isinstance(entry, dict) and "test_acc" in entry:
                try:
                    value = _finite_number(entry["test_acc"], "test_acc")
                except _ArtifactError:
                    continue
                count = entry.get("n_items", "?")
                rows.append(
                    _LeaderboardRow(
                        model=str(model),
                        benchmark=f"{benchmark_name} (N={count})",
                        metric="test_acc",
                        value=value,
                    )
                )

    benchmarks = data.get("benchmarks")
    if not isinstance(benchmarks, list):
        return rows
    for benchmark in benchmarks:
        if not isinstance(benchmark, dict):
            continue
        name = str(benchmark.get("name", benchmark_name))
        results = benchmark.get("results")
        if isinstance(results, dict):
            for model, metrics in results.items():
                if not isinstance(metrics, dict):
                    continue
                for metric, raw_value in metrics.items():
                    try:
                        value = _finite_number(raw_value, str(metric))
                    except _ArtifactError:
                        continue
                    rows.append(_LeaderboardRow(str(model), name, str(metric), value))
        for metric in ("test_acc", "accuracy"):
            if metric not in benchmark:
                continue
            try:
                value = _finite_number(benchmark[metric], metric)
            except _ArtifactError:
                continue
            rows.append(
                _LeaderboardRow(
                    str(benchmark.get("model", "PRINet")), name, metric, value
                )
            )
    return rows


def _validate_r_history(values: list[float]) -> list[float]:
    """Validate and normalize an order-parameter history."""
    if not isinstance(values, list):
        raise ReportInputError("r_history must be a list of finite real numbers")
    if not values:
        raise ReportInputError("r_history must not be empty")
    normalized: list[float] = []
    for index, value in enumerate(values):
        if isinstance(value, bool) or not isinstance(value, Real):
            raise ReportInputError(
                f"r_history[{index}] must be a finite real number, got {value!r}"
            )
        number = float(value)
        if not math.isfinite(number):
            raise ReportInputError(f"r_history[{index}] must be finite")
        if not 0.0 <= number <= 1.0:
            raise ReportInputError(
                f"r_history[{index}] must be in [0, 1], got {number}"
            )
        normalized.append(number)
    return normalized


def _escape_markdown(value: str) -> str:
    """Escape controls that can alter generated Markdown structure."""
    return (
        value.replace("\\", "\\\\")
        .replace("|", "\\|")
        .replace("\r\n", "<br>")
        .replace("\n", "<br>")
        .replace("\r", "<br>")
    )
