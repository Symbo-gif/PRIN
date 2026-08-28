"""PRINet 3.0-compatible training-observation and active-control hooks.

This module is the thin Python compatibility layer for the PRINet 3.0
``prinet.nn.training_hooks`` and ``prinet.core.subconscious`` observation /
control surface. It performs bookkeeping only -- accumulating telemetry
records, buffering control signals, and serialising them -- and contains no
numerics (Coding Standards Sec. 1.2).

Sub-pass 0141D1 delivered :class:`TelemetryLogger`. Sub-pass 0141D2 adds
:class:`ControlSignalBuffer` (real, non-numeric) and the D-2.2 stubs for
the active-control family (``StateCollector``, ``ActiveControlTrainer``,
``create_ablation_tracker``, ``collect_system_state``).

Sub-pass 0141E completes the 172-symbol surface with three further D-2.2
stubs: :class:`MixedPrecisionTrainer` and :class:`AsyncCPUGPUPipeline`
(``torch.amp`` training-step wrappers — training loops, Python numerics) and
:func:`retrain_controller`. ``retrain_controller`` (DV-025) has its real
telemetry-supervised implementation owned by WP-036C S1 (session 0144E); the
stub here keeps the symbol resolvable so the WP-036 S1 surface is complete
(register row unchanged; S2 veto retained).
"""

from __future__ import annotations

import json
import threading
import time
from collections import deque
from typing import Any, NoReturn

from prin.daemon import ControlSignals

__all__ = [
    "ActiveControlTrainer",
    "AsyncCPUGPUPipeline",
    "ControlSignalBuffer",
    "MixedPrecisionTrainer",
    "StateCollector",
    "TelemetryLogger",
    "collect_system_state",
    "create_ablation_tracker",
    "retrain_controller",
]


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


class ControlSignalBuffer:
    """Thread-safe buffer for storing the latest control signals.

    Faithful non-numeric port of the PRINet 3.0
    ``prinet.core.subconscious.ControlSignalBuffer``. The daemon writes via
    :meth:`update` and the main training loop reads via :meth:`latest`. Both
    operations acquire a :class:`threading.Lock` and are safe from data races.

    Example:
        >>> buf = ControlSignalBuffer()
        >>> buf.latest().alert_level
        0.0
    """

    def __init__(self) -> None:
        """Create the buffer with default control signals."""
        self._lock = threading.Lock()
        self._signals: ControlSignals = ControlSignals()

    def update(self, signals: ControlSignals) -> None:
        """Atomically replace the stored control signals.

        Args:
            signals: New control signals to store.
        """
        with self._lock:
            self._signals = signals

    def latest(self) -> ControlSignals:
        """Read the most recent control signals.

        Returns:
            The latest ``ControlSignals`` (safe defaults if never updated).
        """
        with self._lock:
            return self._signals


def _raise_disposition(symbol: str, detail: str) -> NoReturn:
    """Raise the typed D-2.2 disposition error."""
    raise NotImplementedError(
        f"{symbol} is a deferred-rebuild symbol (WP-036 D-2.2). {detail} "
        "See the Migration Guide for the disposition and the owning WP."
    )


class StateCollector:
    """Deferred-rebuild stub for the training-loop daemon bridge.

    PRINet 3.0 ``nn.training_hooks.StateCollector``: collects training
    metrics (loss EMA, gradient norms, latency percentiles) and submits
    a packed ``SubconsciousState`` to the daemon. Computes loss EMA /
    variance (Python numerics).

    Raises:
        NotImplementedError: Always on construction.
    """

    def __init__(self, *_args: Any, **_kwargs: Any) -> None:
        """Raise the D-2.2 disposition."""
        _raise_disposition(
            "StateCollector",
            "Computes loss EMA / gradient norms (Python numerics).",
        )


class ActiveControlTrainer:
    """Deferred-rebuild stub for the active subconscious control trainer.

    PRINet 3.0 ``nn.training_hooks.ActiveControlTrainer``: integrates
    control policies (lr adjustment, K-range narrowing, regime bias) into
    a training loop. Requires a running model + optimizer (Python numerics).

    Raises:
        NotImplementedError: Always on construction.
    """

    def __init__(self, *_args: Any, **_kwargs: Any) -> None:
        """Raise the D-2.2 disposition."""
        _raise_disposition(
            "ActiveControlTrainer",
            "Training loop with control policies (Python numerics).",
        )


def create_ablation_tracker(*_args: Any, **_kwargs: Any) -> NoReturn:
    """Reject calls to the deferred ablation tracker factory.

    Raises:
        NotImplementedError: Always. Constructs trainable tracker modules.
    """
    _raise_disposition(
        "create_ablation_tracker",
        "Constructs trainable tracker modules.",
    )


def collect_system_state(*_args: Any, **_kwargs: Any) -> NoReturn:
    """Reject calls to the deferred system-state collector.

    Raises:
        NotImplementedError: Always. Reads GPU telemetry via pynvml /
            torch.cuda and constructs a SubconsciousState (Python numerics).
    """
    _raise_disposition(
        "collect_system_state",
        "Reads GPU telemetry and constructs SubconsciousState (Python numerics).",
    )


class MixedPrecisionTrainer:
    """Deferred-rebuild stub for the mixed-precision training wrapper.

    PRINet 3.0 ``utils.fused_kernels.MixedPrecisionTrainer``: wraps a model +
    optimizer training step in ``torch.amp.autocast`` / ``GradScaler``. It is a
    training-loop wrapper (``loss.backward()`` / ``optimizer.step()`` /
    gradient scaling), the same category as the 0141D2 ``TemporalTrainer`` /
    ``train_multi_seed`` stubs; delivering it faithfully requires exercising a
    trainable model (Python numerics), out of scope for WP-036 S1.

    Raises:
        NotImplementedError: Always on construction.
    """

    def __init__(self, *_args: Any, **_kwargs: Any) -> None:
        """Raise the D-2.2 disposition."""
        _raise_disposition(
            "MixedPrecisionTrainer",
            "torch.amp training-step wrapper (training loop, Python numerics).",
        )


class AsyncCPUGPUPipeline:
    """Deferred-rebuild stub for the overlapped CPU/GPU training pipeline.

    PRINet 3.0 ``utils.fused_kernels.AsyncCPUGPUPipeline``: runs the
    ``SubconsciousDaemon`` ONNX inference on a CPU thread while a GPU training
    loop proceeds concurrently, with double-buffered state passing. It is a
    training-loop wrapper (``loss.backward()`` / ``optimizer.step()``), the
    same category as :class:`MixedPrecisionTrainer`; a CPU-synchronous shim
    would still have to drive a trainable model, out of scope for WP-036 S1.

    Raises:
        NotImplementedError: Always on construction.
    """

    def __init__(self, *_args: Any, **_kwargs: Any) -> None:
        """Raise the D-2.2 disposition."""
        _raise_disposition(
            "AsyncCPUGPUPipeline",
            "Async CPU/GPU training-loop wrapper (Python numerics).",
        )


def retrain_controller(*_args: Any, **_kwargs: Any) -> NoReturn:
    """Reject calls to the deferred telemetry-supervised controller retrainer.

    PRINet 3.0 ``nn.subconscious_model.retrain_controller``: fits the
    subconscious controller network from a logged telemetry dataset (a
    supervised training loop). DV-025 assigns the real implementation to
    WP-036C S1 (session 0144E), which also owns the reference
    ``test_subconscious`` / y-series retraining tests; this stub keeps the
    symbol resolvable at WP-036 S1 close. The DV-025 register row is unchanged.

    Raises:
        NotImplementedError: Always.
    """
    _raise_disposition(
        "retrain_controller",
        "Telemetry-supervised controller retraining loop; real implementation "
        "owned by WP-036C S1 (session 0144E) per DV-025.",
    )
