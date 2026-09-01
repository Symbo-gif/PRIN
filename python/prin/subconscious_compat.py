"""PRINet 3.0-compatible subconscious controller surface (WP-036B S1, 0144E6).

Single acceptance owner for the four PRINet 3.0 reference modules the
``test_subconscious`` suite imports:

* ``prinet.core.subconscious`` — :class:`SubconsciousState` /
  :class:`ControlSignals` data types and the thread-safe
  :class:`ControlSignalBuffer`;
* ``prinet.core.subconscious_daemon`` — the :class:`SubconsciousDaemon`
  background thread and :func:`collect_system_state` helper;
* ``prinet.nn.subconscious_model`` — the PyTorch :class:`SubconsciousController`
  MLP and its ONNX export;
* ``prinet.utils.npu_backend`` — :func:`detect_best_backend` /
  :func:`npu_available` / :func:`directml_available` / :func:`backend_info`.

Division of labour (Coding Standards §1.2, Project Plan §4 design rule 2):

* Every numeric transformation of the state/control vectors — the 32-float
  packing, the 8-float decode with its ``np.clip`` semantics, the regime
  encoding, the timestamp reduction — lives in the Rust ``prin-daemon`` crate
  and is reached through ``prin._prin_core`` / :mod:`prin.daemon`. The
  :class:`SubconsciousState` / :class:`ControlSignals` classes here are thin
  delegating wrappers that add only the PRINet 3.0 constructor-side helpers
  the frozen Rust ``#[pyclass]`` cannot expose (``default()``, ``clone()``,
  dtype/shape-tolerant ``from_tensor``).
* :class:`SubconsciousController` is a plain ``torch.nn`` MLP with per-channel
  activation heads — the reference is itself pure PyTorch with no oscillator
  numerics, the same "standard PyTorch composition" category as
  :mod:`prin.nn.hybrid_compat` / ``benchmarks.oscillobench`` (0144E4/0144E5).
* :class:`SubconsciousDaemon` and :func:`collect_system_state` are threading /
  telemetry-I/O orchestration only — no numerics — matching the
  :class:`prin.training_hooks.StateCollector` disposition.

The PRINet 3.0 class ``SubconsciousController`` bundled the PyTorch training
half and the ONNX inference half; PRIN keeps them apart. The inference-time,
model-validating controller is :class:`prin.daemon.SubconsciousController`
(WP-028). The training/export half is the class in this module. INT8
``quantize_onnx`` and telemetry-supervised ``retrain_controller`` remain
WP-036C-owned and are not part of this surface (the ``test_subconscious``
suite references neither).
"""

from __future__ import annotations

import logging
import queue
import threading
import time
from collections import deque
from collections.abc import Callable
from pathlib import Path
from typing import TYPE_CHECKING, Any

import numpy as np
import torch
import torch.nn as nn
import torch.nn.functional as F

import prin.daemon as _daemon
from prin._prin_core import CONTROL_DIM, STATE_DIM
from prin._prin_core import ControlSignals as _CoreControlSignals
from prin._prin_core import SubconsciousState as _CoreSubconsciousState
from prin.daemon import BackendType
from prin.training_hooks import ControlSignalBuffer, collect_system_state

if TYPE_CHECKING:
    from numpy.typing import NDArray
    from torch import Tensor

logger = logging.getLogger(__name__)

__all__ = [
    "CONTROL_DIM",
    "STATE_DIM",
    "BackendType",
    "ControlSignalBuffer",
    "ControlSignals",
    "SubconsciousController",
    "SubconsciousDaemon",
    "SubconsciousState",
    "backend_info",
    "collect_system_state",
    "detect_best_backend",
    "directml_available",
    "npu_available",
]

# The env var PRINet 3.0's ``npu_backend`` honours for a forced backend.
_ENV_BACKEND = "PRINET_SUBCONSCIOUS_BACKEND"
_BACKENDS = frozenset({"npu", "directml", "cpu"})


# ======================================================================
# SubconsciousState / ControlSignals — thin wrappers over the Rust owners
# ======================================================================


class SubconsciousState:
    """Compressed system snapshot handed to the subconscious controller.

    Delegates every field and the numeric :meth:`to_tensor` packing to the
    Rust ``prin._prin_core.SubconsciousState`` owner; adds the PRINet 3.0
    :meth:`default` / :meth:`clone` constructor helpers.
    """

    __slots__ = ("_core",)

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        """Forward all arguments to the Rust ``SubconsciousState`` constructor."""
        object.__setattr__(self, "_core", _CoreSubconsciousState(*args, **kwargs))

    @classmethod
    def _wrap(cls, core: _CoreSubconsciousState) -> SubconsciousState:
        """Adopt an existing Rust state instance without copying."""
        obj = object.__new__(cls)
        object.__setattr__(obj, "_core", core)
        return obj

    @staticmethod
    def default() -> SubconsciousState:
        """Return a zero-initialised snapshot stamped with the wall clock."""
        return SubconsciousState(timestamp=time.time())

    def clone(self) -> SubconsciousState:
        """Return an independent copy of this snapshot."""
        return SubconsciousState._wrap(self._core.clone_state())

    def to_tensor(self) -> NDArray[np.float32]:
        """Pack this snapshot into the controller's ``(32,)`` float32 vector."""
        packed: NDArray[np.float32] = self._core.to_tensor()
        return packed

    def __getattr__(self, name: str) -> Any:
        """Delegate unknown attribute reads to the Rust owner."""
        if name == "_core":
            raise AttributeError(name)
        return getattr(self._core, name)

    def __setattr__(self, name: str, value: Any) -> None:
        """Delegate attribute writes to the Rust owner's setters."""
        setattr(self._core, name, value)

    def __repr__(self) -> str:
        """Mirror the Rust owner's representation."""
        return repr(self._core)


class ControlSignals:
    """Control suggestions produced by the subconscious controller.

    Delegates every field, :meth:`to_tensor`, :meth:`is_finite`, and
    :attr:`preferred_regime` to the Rust ``prin._prin_core.ControlSignals``
    owner (which reproduces PRINet 3.0's ``np.clip`` decode semantics); adds
    the :meth:`default` helper and a dtype/shape-tolerant :meth:`from_tensor`.
    """

    __slots__ = ("_core",)

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        """Forward all arguments to the Rust ``ControlSignals`` constructor."""
        object.__setattr__(self, "_core", _CoreControlSignals(*args, **kwargs))

    @classmethod
    def _wrap(cls, core: _CoreControlSignals) -> ControlSignals:
        """Adopt an existing Rust control-signal instance without copying."""
        obj = object.__new__(cls)
        object.__setattr__(obj, "_core", core)
        return obj

    @staticmethod
    def default() -> ControlSignals:
        """Return safe no-op control signals."""
        return ControlSignals()

    @staticmethod
    def from_tensor(arr: Any) -> ControlSignals:
        """Decode control signals from a model-output array.

        Accepts any shape (``ravel``-ed) and any float dtype, matching the
        reference's ``np.asarray(arr, dtype=np.float32).ravel()``. The
        length check and clamping are the Rust owner's.

        Raises:
            ValueError: If fewer than :data:`CONTROL_DIM` elements are given.
        """
        flat = np.ascontiguousarray(np.asarray(arr, dtype=np.float64).ravel())
        return ControlSignals._wrap(_CoreControlSignals.from_tensor(flat))

    def to_tensor(self) -> NDArray[np.float32]:
        """Pack these control signals into an ``(8,)`` float32 array."""
        packed: NDArray[np.float32] = self._core.to_tensor()
        return packed

    def is_finite(self) -> bool:
        """Whether every control signal is finite (no NaN, no infinity)."""
        finite: bool = self._core.is_finite()
        return finite

    def __getattr__(self, name: str) -> Any:
        """Delegate unknown attribute reads to the Rust owner."""
        if name == "_core":
            raise AttributeError(name)
        return getattr(self._core, name)

    def __setattr__(self, name: str, value: Any) -> None:
        """Reject attribute writes; the Rust owner's fields are read-only."""
        raise AttributeError(f"{name!r} is read-only on ControlSignals")

    def __repr__(self) -> str:
        """Mirror the Rust owner's representation."""
        return repr(self._core)


# ======================================================================
# Backend detection — faithful port of prinet.utils.npu_backend
# ======================================================================


def _env_override() -> str | None:
    """Return the backend forced through :data:`_ENV_BACKEND`, if valid."""
    import os

    raw = os.environ.get(_ENV_BACKEND, "").strip().lower()
    return raw if raw in _BACKENDS else None


def detect_best_backend() -> BackendType:
    """Auto-detect the most capable ONNX Runtime execution provider.

    Detection order: :data:`_ENV_BACKEND` override, then VitisAI (NPU), then
    DirectML, then CPU — the priority PRINet 3.0's ``detect_best_backend``
    uses. An unrecognised override value is ignored (fail-soft).

    Returns:
        The selected backend identifier.
    """
    override = _env_override()
    if override is not None:
        logger.info("Backend override via env: %s", override)
        return override  # type: ignore[return-value]
    backend: BackendType = _daemon.detect_best_backend()
    return backend


def npu_available() -> bool:
    """Whether the VitisAI (NPU) execution provider is registered."""
    available: bool = _daemon.npu_available()
    return available


def directml_available() -> bool:
    """Whether the DirectML execution provider is registered."""
    available: bool = _daemon.directml_available()
    return available


def backend_info() -> dict[str, Any]:
    """Summarise the current backend configuration for telemetry and reports.

    Returns the PRINet 3.0 ``npu_backend.backend_info`` key set
    (``ort_available``, ``ort_version``, ``available_eps``, ``best_backend``,
    ``npu_firmware_found``, ``npu_firmware_path``, ``sdk_install_dir``,
    ``npu_target``, ``cache_dir``) built from the Rust-backed
    :func:`prin.daemon.backend_info` probe.
    """
    info = _daemon.backend_info()
    best = info["best_backend"] or detect_best_backend()
    return {
        "ort_available": info["ort_available"],
        "ort_version": info["ort_version"] or "",
        "available_eps": list(info["available_providers"]),
        "best_backend": best,
        "npu_firmware_found": info["npu_firmware_found"],
        "npu_firmware_path": info["npu_firmware_path"] or "",
        "sdk_install_dir": info["sdk_install_dir"],
        "npu_target": info["npu_target"],
        "cache_dir": info["cache_dir"],
    }


# ======================================================================
# SubconsciousController — PyTorch MLP + ONNX export
# ======================================================================

_HIDDEN: int = 128
"""Default hidden-layer width."""

_DROPOUT: float = 0.1
"""Dropout probability for regularization."""


class SubconsciousController(nn.Module):
    """Small MLP that maps system state → control signals.

    Faithful port of ``prinet.nn.subconscious_model.SubconsciousController``
    (the PyTorch training/export half). The architecture is deliberately
    small (~22 K parameters) so it can run on the NPU or CPU with
    sub-millisecond latency.

    Args:
        state_dim: Dimensionality of the input state vector.
        hidden: Width of the hidden layers.
        control_dim: Dimensionality of the output control vector.
        dropout: Dropout probability (0 disables).
    """

    def __init__(
        self,
        state_dim: int = STATE_DIM,
        hidden: int = _HIDDEN,
        control_dim: int = CONTROL_DIM,
        dropout: float = _DROPOUT,
    ) -> None:
        """Build the two-hidden-layer MLP and initialise its weights."""
        super().__init__()
        self.state_dim = state_dim
        self.control_dim = control_dim

        self.net = nn.Sequential(
            nn.Linear(state_dim, hidden),
            nn.ReLU(inplace=True),
            nn.Dropout(p=dropout),
            nn.Linear(hidden, hidden),
            nn.ReLU(inplace=True),
            nn.Dropout(p=dropout),
            nn.Linear(hidden, control_dim),
        )

        self._init_weights()

    def _init_weights(self) -> None:
        """Initialise linear weights with Kaiming uniform and zero biases."""
        for module in self.net:
            if isinstance(module, nn.Linear):
                nn.init.kaiming_uniform_(module.weight, nonlinearity="relu")
                if module.bias is not None:
                    nn.init.zeros_(module.bias)

    def forward(self, z: Tensor) -> Tensor:
        """Compute control signals from system state.

        Output layout (8 dims): indices 0-1 ``suggested_K_min, K_max`` via
        Softplus; index 2 ``lr_multiplier`` via Softplus; indices 3-5 regime
        weights via Softmax; index 6 ``alert_level`` via Sigmoid; index 7
        ``coupling_mode_suggestion`` as a raw logit.

        Args:
            z: State tensor of shape ``(B, state_dim)``.

        Returns:
            Control tensor of shape ``(B, control_dim)``.
        """
        raw = self.net(z)

        k_range = F.softplus(raw[:, 0:2])
        lr_mult = F.softplus(raw[:, 2:3])
        regime = F.softmax(raw[:, 3:6], dim=-1)
        alert = torch.sigmoid(raw[:, 6:7])
        coupling = raw[:, 7:8]

        return torch.cat([k_range, lr_mult, regime, alert, coupling], dim=-1)

    def export_to_onnx(
        self,
        output_path: str | Path,
        *,
        opset_version: int = 18,
        dynamic_batch: bool = True,
    ) -> Path:
        """Export the model to ONNX format.

        The exported graph uses the standard input name ``"state_vector"``
        and output name ``"control_signals"`` expected by
        :func:`prin.daemon.create_session`.

        Args:
            output_path: Destination ``.onnx`` file.
            opset_version: ONNX opset to target.
            dynamic_batch: If ``True``, mark the batch dimension dynamic so
                the model accepts any batch size.

        Returns:
            Resolved :class:`Path` to the written ONNX file.
        """
        resolved = Path(output_path)
        resolved.parent.mkdir(parents=True, exist_ok=True)

        self.eval()
        dummy = (torch.randn(1, self.state_dim),)

        dynamic_axes = (
            {"state_vector": {0: "batch"}, "control_signals": {0: "batch"}}
            if dynamic_batch
            else None
        )

        torch.onnx.export(
            self,
            dummy,
            str(resolved),
            input_names=["state_vector"],
            output_names=["control_signals"],
            opset_version=opset_version,
            dynamic_axes=dynamic_axes,
            dynamo=False,
        )

        logger.info("ONNX model exported to %s", resolved)
        return resolved.resolve()

    @property
    def num_parameters(self) -> int:
        """Total number of trainable parameters."""
        return sum(p.numel() for p in self.parameters() if p.requires_grad)


# ======================================================================
# SubconsciousDaemon — background inference thread
# ======================================================================

_DEFAULT_INTERVAL: float = 15.0
"""Default polling interval in seconds."""

_DEFAULT_QUEUE_SIZE: int = 100
"""Maximum pending state snapshots before the oldest is dropped."""

_WARMUP_SENTINEL = np.zeros((1, STATE_DIM), dtype=np.float32)
"""Dummy input used for the warm-up inference pass."""


class SubconsciousDaemon(threading.Thread):
    """Background daemon that runs the subconscious controller model.

    Faithful port of ``prinet.core.subconscious_daemon.SubconsciousDaemon``: a
    standard :class:`threading.Thread` (``daemon=True``) that dequeues
    :class:`SubconsciousState` snapshots, runs ONNX inference through the
    backend chosen by :func:`detect_best_backend`, and publishes
    :class:`ControlSignals` to a :class:`ControlSignalBuffer`. All numerics
    (state packing, control decode) belong to the Rust owner; this class is
    threading and ONNX-session orchestration only.

    Args:
        model_path: Path to the ONNX model file.
        backend: Execution-provider backend. ``None`` for auto-detect.
        interval: Maximum seconds to wait for a new state before looping.
        queue_size: Bounded queue capacity for pending states.
        warmup: If ``True``, run a single dummy inference on start.
        dlq_maxlen: Maximum number of failed-inference records retained in
            the dead-letter queue (oldest evicted past this bound).
        max_errors_before_escalation: Total error count at which
            ``error_escalation_callback`` fires (``0`` disables escalation).
        error_escalation_callback: Optional callable invoked with a
            ``{"error_count", "dlq_tail"}`` dict once the error threshold is
            reached.
    """

    def __init__(
        self,
        model_path: str | Path,
        backend: BackendType | None = None,
        interval: float = _DEFAULT_INTERVAL,
        queue_size: int = _DEFAULT_QUEUE_SIZE,
        *,
        warmup: bool = True,
        dlq_maxlen: int = 100,
        max_errors_before_escalation: int = 10,
        error_escalation_callback: Callable[[dict[str, Any]], None] | None = None,
    ) -> None:
        """Configure the daemon; the ONNX session is created in :meth:`run`."""
        super().__init__(daemon=True, name="PRIN-Subconscious")
        self._model_path = str(model_path)
        self._backend = backend
        self._interval = interval
        self._warmup = warmup

        self._state_queue: queue.Queue[SubconsciousState] = queue.Queue(
            maxsize=queue_size
        )
        self._control_buffer = ControlSignalBuffer()
        self._stop_event = threading.Event()

        self._inferences: int = 0
        self._errors: int = 0
        self._start_time: float = 0.0

        # Dead-letter queue for failed inference records
        self._dead_letter_queue: deque[dict[str, Any]] = deque(maxlen=dlq_maxlen)
        self._max_errors_before_escalation: int = max_errors_before_escalation
        self._error_escalation_callback: Callable[[dict[str, Any]], None] | None = (
            error_escalation_callback
        )

        self._session: Any | None = None
        self._input_name: str = "state_vector"

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def submit_state(self, state: SubconsciousState) -> None:
        """Non-blocking enqueue of a system state snapshot.

        If the queue is full the oldest state is dropped silently and the
        new state is enqueued.

        Args:
            state: The current system snapshot.
        """
        try:
            self._state_queue.put_nowait(state)
        except queue.Full:
            try:
                self._state_queue.get_nowait()
            except queue.Empty:
                pass
            try:
                self._state_queue.put_nowait(state)
            except queue.Full:
                pass

    def get_control(self) -> _CoreControlSignals:
        """Read the latest control signals (non-blocking).

        Returns:
            The most recent control signals (the Rust ``ControlSignals``
            owner), or safe defaults if no inference has completed yet.
        """
        return self._control_buffer.latest()

    def stop(self, timeout: float = 5.0) -> None:
        """Signal the daemon to stop and wait for it to finish.

        Args:
            timeout: Maximum seconds to wait for thread termination.
        """
        self._stop_event.set()
        self.join(timeout=timeout)
        if self.is_alive():
            logger.warning("SubconsciousDaemon did not stop within %.1fs.", timeout)

    @property
    def inference_count(self) -> int:
        """Number of successful inferences completed."""
        return self._inferences

    @property
    def error_count(self) -> int:
        """Number of inference errors encountered."""
        return self._errors

    @property
    def dead_letter_queue(self) -> list[dict[str, Any]]:
        """Snapshot of the dead-letter queue (most-recent first).

        Each entry is a ``dict`` with keys ``"error"`` (str),
        ``"error_count"`` (int), and ``"timestamp"`` (float).
        """
        return list(reversed(self._dead_letter_queue))

    @property
    def dlq_size(self) -> int:
        """Number of entries currently in the dead-letter queue."""
        return len(self._dead_letter_queue)

    @property
    def uptime(self) -> float:
        """Seconds since the daemon started running."""
        if self._start_time == 0.0:
            return 0.0
        return time.monotonic() - self._start_time

    # ------------------------------------------------------------------
    # Thread entry point
    # ------------------------------------------------------------------

    def run(self) -> None:
        """Execute the daemon loop (called by :meth:`start`)."""
        self._start_time = time.monotonic()
        logger.info(
            "SubconsciousDaemon starting (model=%s, interval=%.1fs).",
            self._model_path,
            self._interval,
        )

        try:
            self._init_session()
        except Exception:
            logger.exception("Failed to create ORT session — daemon aborting.")
            return

        while not self._stop_event.is_set():
            try:
                state = self._state_queue.get(timeout=self._interval)
            except queue.Empty:
                continue
            self._run_inference(state)

        logger.info(
            "SubconsciousDaemon stopped after %d inferences (%d errors, %.1fs).",
            self._inferences,
            self._errors,
            self.uptime,
        )

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _init_session(self) -> None:
        """Create the ONNX session and optionally warm it up."""
        backend = self._backend or detect_best_backend()
        session, _resolved, _providers = _daemon.create_session(
            self._model_path, backend
        )
        self._session = session

        inputs = session.get_inputs()
        if inputs:
            self._input_name = inputs[0].name

        if self._warmup:
            try:
                session.run(None, {self._input_name: _WARMUP_SENTINEL})
            except Exception:
                logger.debug(
                    "Warm-up inference raised (may be expected).", exc_info=True
                )

    def _run_inference(self, state: SubconsciousState) -> None:
        """Run a single inference pass and update the control buffer."""
        try:
            z = np.asarray(state.to_tensor(), dtype=np.float32).reshape(1, STATE_DIM)
            outputs = self._session.run(None, {self._input_name: z})  # type: ignore[union-attr]
            flat = np.ascontiguousarray(
                np.asarray(outputs[0], dtype=np.float64).ravel()
            )
            signals = _CoreControlSignals.from_tensor(flat)

            if not signals.is_finite():
                logger.warning("Non-finite control signals detected - using defaults.")
                signals = _CoreControlSignals()

            self._control_buffer.update(signals)
            self._inferences += 1
        except Exception as exc:
            self._errors += 1
            logger.exception("Inference error in SubconsciousDaemon.")
            entry: dict[str, Any] = {
                "error": str(exc),
                "error_count": self._errors,
                "timestamp": time.monotonic(),
            }
            self._dead_letter_queue.append(entry)
            if (
                self._max_errors_before_escalation > 0
                and self._errors >= self._max_errors_before_escalation
                and self._error_escalation_callback is not None
            ):
                try:
                    self._error_escalation_callback(
                        {"error_count": self._errors, "dlq_tail": entry}
                    )
                except Exception:
                    logger.debug("Error escalation callback raised.", exc_info=True)
