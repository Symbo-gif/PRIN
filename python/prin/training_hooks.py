"""PRINet 3.0-compatible training-observation hooks (non-numeric orchestration).

This module is the thin Python compatibility layer for the PRINet 3.0
``prinet.nn.training_hooks`` observation surface. It performs bookkeeping only
-- accumulating telemetry records and serialising them -- and contains no
numerics (Coding Standards Sec. 1.2).

Sub-pass 0141D1 delivers :class:`TelemetryLogger` (self-contained, no model or
daemon dependency). The active-control family (``StateCollector``,
``ActiveControlTrainer``, ``create_ablation_tracker``) is carried to sub-pass
0141D2.
"""

from __future__ import annotations

import json
import time
from collections import deque
from typing import Any

__all__ = ["TelemetryLogger"]


class TelemetryLogger:
    """Observation-mode telemetry buffer for subconscious training integration.

    Records daemon-state / control-signal pairs alongside training metrics
    without applying any control adjustments. Used to gather telemetry datasets
    for later controller retraining. This is a faithful non-numeric port of the
    PRINet 3.0 class: it stores whatever scalar values the caller supplies and
    never computes over them.

    Args:
        capacity: Maximum number of records retained in memory. Older records
            are discarded once the buffer is full.

    Example:
        >>> logger = TelemetryLogger(capacity=8)
        >>> logger.record(epoch=1, loss=0.5, r_global=0.7)
        >>> len(logger)
        1
        >>> logger.records[0]["epoch"]
        1
    """

    def __init__(self, capacity: int = 10000) -> None:
        """Create the bounded record buffer with the given capacity."""
        if capacity <= 0:
            raise ValueError(f"capacity must be positive, got {capacity}")
        self._records: deque[dict[str, Any]] = deque(maxlen=capacity)

    def record(
        self,
        epoch: int,
        loss: float,
        r_per_band: list[float] | None = None,
        r_global: float = 0.0,
        control: Any = None,
        extra: dict[str, Any] | None = None,
    ) -> None:
        """Append a telemetry snapshot to the buffer.

        Args:
            epoch: Current epoch.
            loss: Current loss value (stored verbatim).
            r_per_band: Per-band order parameters. Defaults to ``[0.0, 0.0,
                0.0]`` when not supplied.
            r_global: Global order parameter (stored verbatim).
            control: Optional control-signal object; its
                ``lr_multiplier`` / ``alert_level`` / ``suggested_K_min`` /
                ``suggested_K_max`` / ``regime_mf_weight`` /
                ``regime_sk_weight`` / ``regime_full_weight`` /
                ``coupling_mode_suggestion`` attributes are read if present.
            extra: Additional key/value pairs merged into the record.
        """
        entry: dict[str, Any] = {
            "epoch": epoch,
            "loss": loss,
            "r_per_band": list(r_per_band) if r_per_band else [0.0, 0.0, 0.0],
            "r_global": r_global,
            "timestamp": time.time(),
        }

        if control is not None:
            entry["control"] = {
                "lr_multiplier": getattr(control, "lr_multiplier", 1.0),
                "alert_level": getattr(control, "alert_level", 0.0),
                "suggested_K_min": getattr(control, "suggested_K_min", 0.0),
                "suggested_K_max": getattr(control, "suggested_K_max", 10.0),
                "regime_mf_weight": getattr(control, "regime_mf_weight", 0.5),
                "regime_sk_weight": getattr(control, "regime_sk_weight", 0.3),
                "regime_full_weight": getattr(control, "regime_full_weight", 0.2),
                "coupling_mode_suggestion": getattr(
                    control, "coupling_mode_suggestion", 0.0
                ),
            }

        if extra:
            entry.update(extra)

        self._records.append(entry)

    def to_json(self, path: str) -> None:
        """Write the accumulated telemetry to a JSON file.

        Args:
            path: Output file path.
        """
        with open(path, "w", encoding="utf-8") as handle:
            json.dump(list(self._records), handle, indent=2)

    @property
    def records(self) -> list[dict[str, Any]]:
        """Return all accumulated records as a list (oldest first)."""
        return list(self._records)

    def __len__(self) -> int:
        """Return the number of buffered records."""
        return len(self._records)
