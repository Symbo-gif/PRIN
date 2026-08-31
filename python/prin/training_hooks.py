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

import torch

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
    """Training loop hook that bridges the model and subconscious daemon.

    PRINet 3.0 ``nn.training_hooks.StateCollector``: collects training
    metrics (loss EMA, gradient norms, latency percentiles) and submits
    a packed ``SubconsciousState`` to the daemon. Pure bookkeeping —
    no oscillator numerics.

    Args:
        daemon: Running subconscious daemon (or mock).
        loss_ema_alpha: EMA smoothing factor for loss tracking.
        latency_window: Number of recent step latencies to keep.
    """

    def __init__(
        self,
        daemon: Any,
        loss_ema_alpha: float = 0.1,
        latency_window: int = 100,
    ) -> None:
        """Construct the collector with EMA and latency-window settings."""
        self._daemon = daemon
        self._loss_ema: float = 0.0
        self._loss_var: float = 0.0
        self._loss_alpha = loss_ema_alpha
        self._grad_norm_ema: float = 0.0
        self._step_latencies: deque[float] = deque(maxlen=latency_window)
        self._last_step_time: float = time.monotonic()
        self._step_count: int = 0
        self._epoch: int = 0

    def on_step_start(self) -> None:
        """Call at the beginning of each training step to record timing."""
        self._last_step_time = time.monotonic()

    def on_step_end(
        self,
        loss: float | torch.Tensor,
        model: torch.nn.Module | None = None,
    ) -> None:
        """Call at the end of each training step to accumulate metrics.

        Args:
            loss: Current step loss (scalar Tensor or float).
            model: Optional model to compute gradient norm from.
        """
        elapsed = (time.monotonic() - self._last_step_time) * 1000.0
        self._step_latencies.append(elapsed)

        loss_val = float(loss.item() if isinstance(loss, torch.Tensor) else loss)
        alpha = self._loss_alpha
        self._loss_ema = alpha * loss_val + (1 - alpha) * self._loss_ema
        diff = loss_val - self._loss_ema
        self._loss_var = alpha * (diff * diff) + (1 - alpha) * self._loss_var

        if model is not None:
            total_norm = 0.0
            for p in model.parameters():
                if p.grad is not None:
                    total_norm += p.grad.data.norm(2).item() ** 2
            grad_norm = total_norm**0.5
            self._grad_norm_ema = alpha * grad_norm + (1 - alpha) * self._grad_norm_ema

        self._step_count += 1

    def on_epoch_end(
        self,
        epoch: int,
        loss: float | torch.Tensor | None = None,
        r_per_band: list[float] | None = None,
        r_global: float | None = None,
        lr_current: float = 0.0,
        scalr_alpha: float = 1.0,
        regime: str = "mean_field",
    ) -> None:
        """Call at the end of each epoch to submit state to daemon.

        Args:
            epoch: Current epoch number.
            loss: Epoch loss (overrides accumulated EMA if provided).
            r_per_band: Per-band order parameters.
            r_global: Global order parameter.
            lr_current: Current learning rate.
            scalr_alpha: SCALR alpha parameter.
            regime: Current coupling regime name.
        """
        from prin.daemon import SubconsciousState

        self._epoch = epoch

        if loss is not None:
            loss_val = float(loss.item() if isinstance(loss, torch.Tensor) else loss)
            self._loss_ema = loss_val

        rpb = r_per_band if r_per_band is not None else [0.5, 0.5, 0.5]
        r_g = r_global if r_global is not None else sum(rpb) / len(rpb)

        if self._step_latencies:
            sorted_lat = sorted(self._step_latencies)
            n = len(sorted_lat)
            p50 = sorted_lat[n // 2]
            p95 = sorted_lat[min(int(n * 0.95), n - 1)]
            throughput = 1000.0 / (sum(sorted_lat) / n) if n > 0 else 0.0
        else:
            p50 = p95 = 0.0
            throughput = 0.0

        sys_state = SubconsciousState(
            r_per_band=rpb,
            r_global=r_g,
            loss_ema=self._loss_ema,
            loss_variance=self._loss_var,
            grad_norm_ema=self._grad_norm_ema,
            lr_current=lr_current,
            scalr_alpha=scalr_alpha,
            gpu_temp=0.0,
            gpu_util=0.0,
            vram_pct=0.0,
            cpu_util=0.0,
            step_latency_p50=p50,
            step_latency_p95=p95,
            throughput=throughput,
            epoch=epoch,
            regime=regime,
        )

        self._daemon.submit_state(sys_state)

    def latest_control(self) -> Any:
        """Read the latest control signals from the daemon.

        Returns:
            Control signals from daemon.
        """
        return self._daemon.get_control()

    @property
    def loss_ema(self) -> float:
        """Current exponentially-weighted moving average of loss."""
        return self._loss_ema

    @property
    def loss_variance(self) -> float:
        """Current EMA of loss variance."""
        return self._loss_var

    @property
    def grad_norm_ema(self) -> float:
        """Current EMA of gradient norm."""
        return self._grad_norm_ema

    @property
    def step_count(self) -> int:
        """Total number of training steps recorded."""
        return self._step_count


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
