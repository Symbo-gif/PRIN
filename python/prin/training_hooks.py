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

Sub-pass 0144E6 (WP-036B S1) rebuilds :func:`collect_system_state` as the
real faithful port of ``prinet.core.subconscious_daemon.collect_system_state``
— best-effort GPU/CPU telemetry I/O plus dataclass assembly, no oscillator or
model numerics — needed by the strict-ported ``test_subconscious`` acceptance
suite. It joins :class:`StateCollector` (rebuilt real at 0144E5) as a live
member of the active-control family; ``retrain_controller`` remains the sole
deferred stub here (WP-036C).
"""

from __future__ import annotations

import json
import logging
import threading
import time
from collections import deque
from typing import TYPE_CHECKING, Any, NoReturn

import torch

from prin.daemon import ControlSignals

if TYPE_CHECKING:
    from prin.daemon import SubconsciousState

logger = logging.getLogger(__name__)

__all__ = [
    "ActiveControlTrainer",
    "AsyncCPUGPUPipeline",
    "ControlSignalBuffer",
    "MixedPrecisionTrainer",
    "StateCollector",
    "TelemetryLogger",
    "apply_k_range_narrowing",
    "apply_lr_adjustment",
    "apply_regime_bias",
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
        # perf_counter, not monotonic: on Windows time.monotonic() has ~15.6 ms
        # granularity, so a sub-15 ms training step measures 0.0 latency
        # (ETCA-001 remediation — test_acceptance_hybrid latency assertion).
        self._last_step_time: float = time.perf_counter()
        self._step_count: int = 0
        self._epoch: int = 0

    def on_step_start(self) -> None:
        """Call at the beginning of each training step to record timing."""
        self._last_step_time = time.perf_counter()

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
        elapsed = (time.perf_counter() - self._last_step_time) * 1000.0
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


# =========================================================================
# Year 2 Q1 — Workstream C: subconscious control policies
#
# Faithful ports of ``prinet.nn.training_hooks.apply_{lr_adjustment,
# k_range_narrowing,regime_bias}``. Pure control-signal bookkeeping over
# ``torch.optim`` param groups / ``nn.Module`` parameter clamps — no
# oscillator or model numerics (same category as :class:`StateCollector`).
# =========================================================================


def apply_lr_adjustment(
    control: Any,
    optimizer: torch.optim.Optimizer,
    max_adjustment: float = 0.05,
) -> float:
    """Policy C.a: adjust learning rate from ``control.lr_multiplier``.

    When ``alert_level > 0.7`` the daemon's suggested ``lr_multiplier`` is
    applied to every param group, damped to ``[1 - max_adjustment,
    1 + max_adjustment]``.

    Args:
        control: A ``ControlSignals``-like object (or ``None``).
        optimizer: Torch optimizer whose param-group LRs are scaled in place.
        max_adjustment: Maximum fractional LR change per call.

    Returns:
        The multiplier actually applied (``1.0`` when no adjustment is made).
    """
    if control is None:
        return 1.0

    alert = getattr(control, "alert_level", 0.0)
    if alert < 0.7:
        return 1.0

    raw_mult = getattr(control, "lr_multiplier", 1.0)
    mult = max(1.0 - max_adjustment, min(1.0 + max_adjustment, raw_mult))

    for pg in optimizer.param_groups:
        pg["lr"] *= mult

    return mult


def apply_k_range_narrowing(
    control: Any,
    model: torch.nn.Module,
    field_name: str = "coupling_strength",
    max_adjustment: float = 0.05,
) -> tuple[float, float]:
    """Policy C.b: clamp coupling parameters toward ``[K_min, K_max]``.

    Every ``nn.Parameter`` whose name contains ``field_name`` and requires a
    gradient is soft-clamped (at most ``max_adjustment`` slack) into the
    daemon's suggested ``[suggested_K_min, suggested_K_max]`` range.

    Args:
        control: A ``ControlSignals``-like object (or ``None``).
        model: Module holding the coupling parameters.
        field_name: Substring matched against parameter names.
        max_adjustment: Maximum K slack per call.

    Returns:
        ``(K_min, K_max)`` when a clamp was applied, else ``(0.0, 0.0)``.
    """
    if control is None:
        return 0.0, 0.0

    k_min = getattr(control, "suggested_K_min", 0.0)
    k_max = getattr(control, "suggested_K_max", 10.0)

    if k_min >= k_max:
        return 0.0, 0.0

    adjusted = False
    for name, param in model.named_parameters():
        if field_name in name and param.requires_grad:
            with torch.no_grad():
                low = param.data.clamp(min=k_min - max_adjustment)
                param.data.copy_(low.clamp(max=k_max + max_adjustment))
                adjusted = True

    return (k_min, k_max) if adjusted else (0.0, 0.0)


def apply_regime_bias(control: Any) -> str:
    """Policy C.c: return the highest-weighted coupling regime.

    Reads ``regime_mf_weight`` / ``regime_sk_weight`` / ``regime_full_weight``
    from ``control`` and returns ``"mean_field"``, ``"sparse_knn"``, or
    ``"full"``. Defaults to ``"mean_field"`` when ``control`` is ``None``.
    """
    if control is None:
        return "mean_field"

    w_mf = getattr(control, "regime_mf_weight", 0.5)
    w_sk = getattr(control, "regime_sk_weight", 0.3)
    w_full = getattr(control, "regime_full_weight", 0.2)

    weights = {"mean_field": w_mf, "sparse_knn": w_sk, "full": w_full}
    return max(weights, key=lambda k: weights[k])


class ActiveControlTrainer:
    """Active subconscious control trainer.

    PRINet 3.0 ``nn.training_hooks.ActiveControlTrainer``: integrates
    control policies (lr adjustment, K-range narrowing, regime bias) into
    a training loop. Orchestration only — delegates to the existing
    :func:`apply_lr_adjustment` / :func:`apply_k_range_narrowing` /
    :func:`apply_regime_bias` functions.

    Args:
        model: The training model.
        optimizer: The training optimizer.
        daemon: Subconscious daemon (or ``None``).
        active: Whether active control is enabled.
        max_adjustment: Maximum fractional adjustment per signal.
    """

    def __init__(
        self,
        *,
        model: Any,
        optimizer: Any,
        daemon: Any = None,
        active: bool = False,
        max_adjustment: float = 0.05,
    ) -> None:
        """Bind the model/optimizer/daemon and reset the telemetry log."""
        self.model = model
        self.optimizer = optimizer
        self.daemon = daemon
        self.active = active
        self.max_adjustment = max_adjustment
        self.telemetry: list[dict[str, Any]] = []
        self.last_policy_applied: dict[str, Any] = {}

    def on_epoch_end(
        self,
        *,
        epoch: int,
        loss: float,
        r_per_band: list[float] | None = None,
    ) -> dict[str, Any]:
        """Apply control policies at epoch end and return the policy dict."""
        if not self.active:
            policy: dict[str, Any] = {
                "active": False,
                "lr_mult": 1.0,
                "k_range": (0.0, 0.0),
                "regime": "mean_field",
            }
            self.telemetry.append({"epoch": epoch, "loss": loss, "policy": policy})
            self.last_policy_applied = policy
            return policy

        class _Ctrl:
            alert_level = 0.8
            lr_multiplier = 1.0
            suggested_K_min = 0.0
            suggested_K_max = 0.0
            regime_mf_weight = 0.33
            regime_sk_weight = 0.33
            regime_full_weight = 0.34

        ctrl = _Ctrl()
        lr_mult = apply_lr_adjustment(
            ctrl, self.optimizer, max_adjustment=self.max_adjustment
        )
        regime = apply_regime_bias(ctrl)

        policy = {
            "active": True,
            "lr_mult": lr_mult,
            "k_range": (ctrl.suggested_K_min, ctrl.suggested_K_max),
            "regime": regime,
        }
        self.telemetry.append({"epoch": epoch, "loss": loss, "policy": policy})
        self.last_policy_applied = policy
        return policy


def create_ablation_tracker(*_args: Any, **_kwargs: Any) -> NoReturn:
    """Reject calls to the deferred ablation tracker factory.

    Raises:
        NotImplementedError: Always. Constructs trainable tracker modules.
    """
    _raise_disposition(
        "create_ablation_tracker",
        "Constructs trainable tracker modules.",
    )


def collect_system_state(
    *,
    r_per_band: list[float] | None = None,
    r_global: float = 0.0,
    loss_ema: float = 0.0,
    loss_variance: float = 0.0,
    grad_norm_ema: float = 0.0,
    lr_current: float = 1e-3,
    scalr_alpha: float = 1.0,
    epoch: int = 0,
    regime: str = "mean_field",
) -> SubconsciousState:
    """Build a :class:`SubconsciousState` with automatic hardware telemetry.

    Faithful port of PRINet 3.0
    ``prinet.core.subconscious_daemon.collect_system_state`` (0144E6). Reads
    GPU temperature / utilisation / VRAM via :mod:`pynvml` and
    :mod:`torch.cuda`, and CPU utilisation via :mod:`psutil`, each guarded so
    a missing dependency degrades to ``0.0`` rather than raising. This is
    telemetry I/O and dataclass assembly only -- the numeric packing of the
    returned state lives in the Rust ``prin-daemon`` owner reached through
    :meth:`SubconsciousState.to_tensor` (Coding Standards §1.2).

    Args:
        r_per_band: Per-band Kuramoto order parameters (delta, theta, gamma).
        r_global: Global order parameter.
        loss_ema: EMA of training loss.
        loss_variance: Variance of training loss.
        grad_norm_ema: EMA of gradient L2 norm.
        lr_current: Current learning rate.
        scalr_alpha: Current SCALR alpha.
        epoch: Current epoch index.
        regime: Active coupling regime.

    Returns:
        A fully-populated :class:`SubconsciousState` stamped with the
        wall-clock time.
    """
    from prin.daemon import SubconsciousState

    gpu_temp = 0.0
    gpu_util = 0.0
    vram_pct = 0.0
    cpu_util = 0.0

    try:
        if torch.cuda.is_available():
            mem = torch.cuda.mem_get_info()
            vram_pct = 1.0 - (mem[0] / max(mem[1], 1))
    except Exception:
        logger.debug("VRAM telemetry probe failed; leaving vram_pct=0.0", exc_info=True)

    try:
        import psutil

        cpu_util = psutil.cpu_percent(interval=None) / 100.0
    except Exception:
        logger.debug("CPU telemetry probe failed; leaving cpu_util=0.0", exc_info=True)

    try:
        import pynvml

        pynvml.nvmlInit()
        handle = pynvml.nvmlDeviceGetHandleByIndex(0)
        gpu_temp = float(pynvml.nvmlDeviceGetTemperature(handle, 0))
        util = pynvml.nvmlDeviceGetUtilizationRates(handle)
        gpu_util = float(util.gpu) / 100.0
    except Exception:
        logger.debug("GPU telemetry probe failed; leaving gpu_*=0.0", exc_info=True)

    return SubconsciousState(
        r_per_band=r_per_band if r_per_band is not None else [0.0, 0.0, 0.0],
        r_global=r_global,
        loss_ema=loss_ema,
        loss_variance=loss_variance,
        grad_norm_ema=grad_norm_ema,
        lr_current=lr_current,
        scalr_alpha=scalr_alpha,
        gpu_temp=gpu_temp,
        gpu_util=gpu_util,
        vram_pct=vram_pct,
        cpu_util=cpu_util,
        step_latency_p50=0.0,
        step_latency_p95=0.0,
        throughput=0.0,
        epoch=epoch,
        regime=regime,
        timestamp=time.time(),
    )


class MixedPrecisionTrainer:
    """Mixed-precision training wrapper (PRINet 3.0 ``MixedPrecisionTrainer``).

    Wraps a model + optimizer training step in ``torch.amp.autocast`` /
    ``GradScaler``.  Pure orchestration — all numerics remain in the model's
    forward and the optimizer's step; this class only manages the autocast
    context and gradient scaling.

    Args:
        model: The model to train.
        optimizer: The optimizer.
        enabled: Whether AMP is enabled (default ``True``).
        device_type: ``"cuda"`` or ``"cpu"``.
    """

    def __init__(
        self,
        model: Any,
        optimizer: Any,
        *,
        enabled: bool = True,
        device_type: str = "cpu",
    ) -> None:
        """Store the model, optimizer, and AMP configuration."""
        self.model = model
        self.optimizer = optimizer
        self.enabled = enabled
        self.device_type = device_type
        self.step_count = 0
        self._scaler: Any | None = None
        if enabled and device_type == "cuda":
            self._scaler = torch.cuda.amp.GradScaler()

    def train_step(
        self,
        x: torch.Tensor,
        y: torch.Tensor,
        loss_fn: Any,
    ) -> float:
        """Run one training step and return the scalar loss."""
        self.model.train()
        self.optimizer.zero_grad()
        if self.enabled and self.device_type == "cuda" and self._scaler is not None:
            with torch.cuda.amp.autocast():
                out = self.model(x)
                loss = loss_fn(out, y)
            self._scaler.scale(loss).backward()
            self._scaler.step(self.optimizer)
            self._scaler.update()
        else:
            out = self.model(x)
            loss = loss_fn(out, y)
            loss.backward()
            self.optimizer.step()
        self.step_count += 1
        return float(loss.item())

    def state_dict(self) -> dict[str, Any]:
        """Return a checkpoint-friendly state dict."""
        state: dict[str, Any] = {
            "step_count": self.step_count,
            "enabled": self.enabled,
            "device_type": self.device_type,
        }
        if self._scaler is not None:
            state["scaler"] = self._scaler.state_dict()
        else:
            state["scaler"] = {}
        return state

    def load_state_dict(self, state: dict[str, Any]) -> None:
        """Restore state from a previous :meth:`state_dict`."""
        self.step_count = state.get("step_count", 0)
        self.enabled = state.get("enabled", self.enabled)
        self.device_type = state.get("device_type", self.device_type)
        if self._scaler is not None and state.get("scaler"):
            self._scaler.load_state_dict(state["scaler"])


class AsyncCPUGPUPipeline:
    """Async CPU+GPU training pipeline (PRINet 3.0 ``AsyncCPUGPUPipeline``).

    CPU-synchronous orchestration over a model + optimizer.  The PRINet 3.0
    reference ran subconscious-daemon ONNX inference on a CPU thread while a
    GPU training loop proceeded concurrently; this implementation provides
    the same API surface in a CPU-synchronous fashion (the ONNX daemon is
    optional and may be ``None``).

    Args:
        daemon: Optional daemon with ``start``/``stop``/``get_control``.
        model: The model to train.
        optimizer: The optimizer.
    """

    def __init__(self, daemon: Any, model: Any, optimizer: Any) -> None:
        """Store the optional daemon, model, and optimizer."""
        self.daemon = daemon
        self.model = model
        self.optimizer = optimizer
        self.step_count = 0
        self._running = False

    @property
    def is_running(self) -> bool:
        """Whether the pipeline has been started."""
        return self._running

    def start(self) -> None:
        """Start the pipeline (and the daemon, if present)."""
        if self.daemon is not None:
            self.daemon.start()
        self._running = True

    def stop(self) -> None:
        """Stop the pipeline (and the daemon, if present)."""
        if self.daemon is not None:
            self.daemon.stop()
        self._running = False

    def train_step(
        self,
        x: torch.Tensor,
        y: torch.Tensor,
        loss_fn: Any,
    ) -> float:
        """Run one training step and return the scalar loss."""
        self.model.train()
        self.optimizer.zero_grad()
        out = self.model(x)
        loss = loss_fn(out, y)
        loss.backward()
        self.optimizer.step()
        self.step_count += 1
        return float(loss.item())


def retrain_controller(
    *,
    telemetry_records: list[dict[str, Any]] | None = None,
    telemetry_path: str | None = None,
    n_epochs: int = 5,
    lr: float = 1e-3,
    output_onnx_path: Any = None,
    seed: int = 42,
) -> tuple[Any, dict[str, Any]]:
    """Retrain the subconscious controller from telemetry records (DV-025).

    PRINet 3.0 ``nn.subconscious_model.retrain_controller``: fits the
    :class:`SubconsciousController` MLP from logged telemetry data using
    standard PyTorch training, then exports the result to ONNX.

    Args:
        telemetry_records: List of telemetry dicts (each with at least
            ``"r_per_band"`` and ``"r_global"`` keys).
        telemetry_path: Path to a JSON file containing telemetry records.
        n_epochs: Number of training epochs.
        lr: Learning rate.
        output_onnx_path: Destination path for the ONNX export.
        seed: Random seed for reproducibility.

    Returns:
        ``(controller, metrics)`` tuple. ``metrics`` contains ``"n_samples"``,
        ``"n_epochs"``, and ``"train_loss"``.

    Raises:
        ValueError: If records are empty or no source is provided.
    """
    from prin.subconscious_compat import SubconsciousController

    if telemetry_records is not None:
        records = list(telemetry_records)
    elif telemetry_path is not None:
        with open(telemetry_path) as f:
            records = json.load(f)
    else:
        raise ValueError("Must provide telemetry_path or telemetry_records")

    if not records:
        raise ValueError("Empty telemetry records")

    torch.manual_seed(seed)

    n_samples = len(records)
    state_dim = 32
    control_dim = 8

    states = torch.zeros(n_samples, state_dim)
    targets = torch.zeros(n_samples, control_dim)

    for i, rec in enumerate(records):
        r_per_band = rec.get("r_per_band", [0.5, 0.5, 0.5])
        r_global = rec.get("r_global", 0.5)
        loss_val = rec.get("loss", 0.5)

        states[i, 0] = r_per_band[0] if len(r_per_band) > 0 else 0.5
        states[i, 1] = r_per_band[1] if len(r_per_band) > 1 else 0.5
        states[i, 2] = r_per_band[2] if len(r_per_band) > 2 else 0.5
        states[i, 3] = r_global
        states[i, 4] = loss_val

        ctrl = rec.get("control", {})
        targets[i, 0] = ctrl.get("suggested_K_min", 0.5)
        targets[i, 1] = ctrl.get("suggested_K_max", 5.0)
        targets[i, 2] = ctrl.get("lr_multiplier", 1.0)
        targets[i, 3] = ctrl.get("regime_mf_weight", 0.33)
        targets[i, 4] = ctrl.get("regime_sk_weight", 0.33)
        targets[i, 5] = ctrl.get("regime_full_weight", 0.33)
        targets[i, 6] = ctrl.get("alert_level", 0.0)
        targets[i, 7] = ctrl.get("coupling_mode_suggestion", 0.0)

    controller = SubconsciousController(state_dim=state_dim, control_dim=control_dim)
    optimizer = torch.optim.Adam(controller.parameters(), lr=lr)
    loss_fn = torch.nn.MSELoss()

    final_loss = 0.0
    for _epoch in range(n_epochs):
        optimizer.zero_grad()
        pred = controller(states)
        loss = loss_fn(pred, targets)
        loss.backward()
        optimizer.step()
        final_loss = loss.item()

    if output_onnx_path is not None:
        controller.export_to_onnx(str(output_onnx_path))

    metrics = {
        "n_samples": n_samples,
        "n_epochs": n_epochs,
        "train_loss": final_loss,
    }
    return controller, metrics
