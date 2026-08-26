"""Benchmark artefact JSON writer.

Merges the environment block, config envelope, and a category module's
measurement payload into one artefact and writes it as JSON, confining
writes to the declared output directories (Coding Standards §6.1:
"File-system writes confined to declared output directories
(`benchmarks/results/`, `DOCS/test_and_benchmark_results/`, temp dirs)").
"""

from __future__ import annotations

import json
import tempfile
from pathlib import Path
from typing import Any

_REPO_ROOT = Path(__file__).resolve().parents[2]
_ALLOWED_ROOTS = (
    (_REPO_ROOT / "benchmarks" / "results").resolve(),
    (_REPO_ROOT / "DOCS" / "test_and_benchmark_results").resolve(),
    Path(tempfile.gettempdir()).resolve(),
)


class OutputPathError(ValueError):
    """Raised when a benchmark result path escapes the declared output roots."""


def _validate_output_path(path: Path) -> Path:
    resolved = path.resolve()
    for root in _ALLOWED_ROOTS:
        if resolved == root or root in resolved.parents:
            return resolved
    raise OutputPathError(
        f"{path} resolves outside the declared output roots "
        f"(benchmarks/results/, DOCS/test_and_benchmark_results/, temp dirs): "
        f"{resolved}"
    )


def write_result(
    path: Path,
    *,
    environment: dict[str, Any],
    config: dict[str, Any],
    payload: dict[str, Any],
) -> Path:
    """Write a benchmark artefact, confined to a declared output directory.

    Args:
        path: Destination file. Must resolve inside ``benchmarks/results/``,
            ``DOCS/test_and_benchmark_results/``, or a temp directory.
        environment: The :func:`benchmarks._common.environment.capture_environment`
            output.
        config: A JSON-safe summary of the
            :class:`~benchmarks._common.config.BenchmarkConfig` used.
        payload: The category module's measurement payload. Its top-level
            keys must not collide with ``environment``/``config`` (checked).

    Returns:
        The resolved path actually written.

    Raises:
        OutputPathError: If ``path`` escapes the declared output roots, or
            ``payload`` collides with the reserved ``environment``/``config``
            envelope keys.
    """
    resolved = _validate_output_path(path)
    if "environment" in payload or "config" in payload:
        raise OutputPathError(
            "payload must not define reserved keys 'environment'/'config'"
        )
    artefact = {"environment": environment, "config": config, **payload}
    resolved.parent.mkdir(parents=True, exist_ok=True)
    resolved.write_text(
        json.dumps(artefact, indent=2, sort_keys=True, ensure_ascii=False),
        encoding="utf-8",
    )
    return resolved
