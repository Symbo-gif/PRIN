"""``SyncGd``/``Scalr``/``Rip`` `torch.optim.Optimizer` wrappers (WP-027).

See ``crates/prin-py/src/bindings/optim.rs`` for the Rust bridge and
``crates/prin-train/src/{sync_gd,scalr,rip}.rs`` for the numerical core
(PRINet 3.0 ``SynchronizedGradientDescent``/``SCALROptimizer``/
``RIPOptimizer``). Every numerical decision (learning-rate scaling, barrier
penalties, Hebbian deltas) is computed in Rust; these classes are a thin
per-parameter loop, per the Rebuild Planning Document's `nn/optimizers.py`
mapping ("SCALR/RIP/SyncGD need order-parameter feedback -> Rust computes
metrics, Python optimizer classes stay thin").

**Deviation from the standard `torch.optim.Optimizer` interface.** These
optimizers need the network's instantaneous Kuramoto order parameter (or,
for :class:`Rip`, its phase/amplitude state) each step, so ``step()`` takes
an additional keyword-only ``order_parameter`` (or ``phase``/``amplitude``)
argument beyond the standard ``closure``. This is a deliberate, documented
adaptation, not an oversight — a caller driving one of these optimizers must
supply that feedback (typically computed via :mod:`prin.metrics` on the
model's current oscillator state) at each ``step()`` call.

**Parameter dtype/layout.** Every bridge call requires ``torch.float64``,
CPU, contiguous tensors (matching the rest of `prin.nn`'s bridges).
:class:`SyncGd`/:class:`Scalr` flatten each parameter to 1-D before calling
the Rust bridge and reshape the result back — the Rust optimizers are
generic per-parameter update rules (any tensor rank); flattening keeps one
Rust bridge instance usable across parameters of different shapes.
:class:`Rip` instead optimizes exactly one square ``[n, n]`` coupling-matrix
parameter (`RIPOptimizer`'s actual single-purpose contract, per
``crates/prin-train/src/rip.rs``'s module docs).

**Checkpointing scope.** :meth:`SyncGd.rust_state_dict`/
:meth:`Scalr.rust_state_dict`/:meth:`Rip.rust_state_dict` round-trip each
optimizer's scalar/history state as JSON. The momentum buffer
(non-empty only when ``momentum != 0.0``, not PRINet 3.0's default) is not
included in this MVP scope — see ``crates/prin-py/src/bindings/optim.rs``'s
module docs.
"""

from __future__ import annotations

import json
from typing import Any

import torch
from torch.utils.dlpack import from_dlpack

from prin._prin_core import RipBridge, ScalrBridge, SyncGdBridge

__all__: list[str] = [
    "RIPOptimizer",
    "Rip",
    "SCALROptimizer",
    "Scalr",
    "SyncGd",
    "SynchronizedGradientDescent",
]


def _bridge_vec(t: torch.Tensor) -> torch.Tensor:
    """Detach ``t`` as a contiguous 1-D float64 CPU tensor for a Rust bridge."""
    return t.detach().to(dtype=torch.float64, device="cpu").reshape(-1).contiguous()


def _bridge_mat(t: torch.Tensor) -> torch.Tensor:
    """Detach ``t`` as a contiguous float64 CPU tensor for a Rust bridge."""
    return t.detach().to(dtype=torch.float64, device="cpu").contiguous()


class SyncGd(torch.optim.Optimizer):
    """SGD with a Kuramoto-order-parameter synchronization-barrier penalty.

    PRINet 3.0 ``SynchronizedGradientDescent``. See the module docs for the
    ``step(order_parameter=...)`` deviation from the standard optimizer
    interface.

    Args:
        params: Iterable of parameters to optimize (any shapes; each is
            flattened internally).
        lr: Learning rate.
        momentum: Momentum factor.
        weight_decay: L2 weight-decay coefficient.
        sync_penalty: Synchronization penalty weight (lambda).
        critical_order: Critical order-parameter threshold (K_c), in
            ``[0, 1]``.
        dampening: Momentum dampening.

    Examples:
        >>> import torch
        >>> from prin.nn.optimizers import SyncGd
        >>> w = torch.zeros(4, dtype=torch.float64, requires_grad=True)
        >>> opt = SyncGd([w], lr=0.1)
        >>> (w.sum() ** 2).backward()
        >>> opt.step(order_parameter=0.5)
    """

    def __init__(
        self,
        params: Any,
        lr: float = 0.01,
        momentum: float = 0.0,
        weight_decay: float = 0.0,
        sync_penalty: float = 0.1,
        critical_order: float = 0.5,
        dampening: float = 0.0,
    ) -> None:
        """Construct with one Rust bridge instance per parameter."""
        defaults = dict(
            lr=lr,
            momentum=momentum,
            weight_decay=weight_decay,
            sync_penalty=sync_penalty,
            critical_order=critical_order,
            dampening=dampening,
        )
        super().__init__(params, defaults)
        for group in self.param_groups:
            for p in group["params"]:
                self.state[p]["_bridge"] = SyncGdBridge(
                    lr=group["lr"],
                    momentum=group["momentum"],
                    weight_decay=group["weight_decay"],
                    sync_penalty=group["sync_penalty"],
                    critical_order=group["critical_order"],
                    dampening=group["dampening"],
                )

    @torch.no_grad()
    def step(
        self,
        closure: Any = None,
        order_parameter: float | None = None,
    ) -> Any:
        """Apply one update to every parameter with a gradient.

        Args:
            closure: Standard PyTorch closure re-evaluating the loss under
                gradient tracking, if supplied.
            order_parameter: The network's current global Kuramoto order
                parameter, or ``None`` for plain (unscaled) SGD this step.
        """
        loss = None
        if closure is not None:
            with torch.enable_grad():
                loss = closure()

        for group in self.param_groups:
            for p in group["params"]:
                if p.grad is None:
                    continue
                bridge = self.state[p]["_bridge"]
                flat_param = p.detach().reshape(-1).contiguous()
                flat_grad = p.grad.detach().reshape(-1).contiguous()
                updated = from_dlpack(
                    bridge.step(flat_param, flat_grad, order_parameter)
                )
                p.data.copy_(updated.reshape(p.shape))

        return loss

    def rust_state_dict(self) -> list[str]:
        """One JSON snapshot per parameter, in ``param_groups`` order."""
        return [
            self.state[p]["_bridge"].state_dict()
            for group in self.param_groups
            for p in group["params"]
        ]

    def load_rust_state_dict(self, states: list[str]) -> None:
        """Restore state previously produced by :meth:`rust_state_dict`.

        Raises:
            ValueError: If `states`'s length does not match the number of
                optimized parameters, or on malformed JSON.
        """
        params = [p for group in self.param_groups for p in group["params"]]
        if len(states) != len(params):
            raise ValueError(f"expected {len(params)} states, got {len(states)}")
        for p, s in zip(params, states, strict=True):
            self.state[p]["_bridge"].load_state_dict(s)


class Scalr(torch.optim.Optimizer):
    """Synchronization-Coupled Adaptive Learning Rate optimizer.

    PRINet 3.0 ``SCALROptimizer``. See the module docs for the
    ``step(order_parameter=...)`` deviation from the standard optimizer
    interface.

    Args:
        params: Iterable of parameters to optimize (any shapes; each is
            flattened internally).
        lr: Base learning rate (eta_base).
        momentum: Momentum factor.
        weight_decay: L2 weight-decay coefficient.
        r_min: Minimum learning-rate fraction when the order parameter
            ``r -> 0``.
        alpha: Synchronization-sensitivity exponent.
        warmup_steps: Steps at full base lr before SCALR scaling kicks in.
        oscillation_window: Window size for oscillation detection.
        oscillation_threshold: Windowed-variance threshold for oscillation
            detection.
        oscillation_decay: Multiplicative lr decay applied once per
            oscillation detection.
        adaptive_r_min: If ``True``, auto-adjust `r_min` from an EMA of the
            order parameter.
        r_min_ema_alpha: EMA smoothing factor for adaptive `r_min`.
    """

    def __init__(
        self,
        params: Any,
        lr: float = 0.01,
        momentum: float = 0.0,
        weight_decay: float = 0.0,
        r_min: float = 0.1,
        alpha: float = 1.0,
        warmup_steps: int = 0,
        oscillation_window: int = 20,
        oscillation_threshold: float = 0.01,
        oscillation_decay: float = 0.95,
        adaptive_r_min: bool = False,
        r_min_ema_alpha: float = 0.1,
    ) -> None:
        """Construct with one Rust bridge instance per parameter."""
        defaults = dict(
            lr=lr,
            momentum=momentum,
            weight_decay=weight_decay,
            r_min=r_min,
            alpha=alpha,
            warmup_steps=warmup_steps,
            oscillation_window=oscillation_window,
            oscillation_threshold=oscillation_threshold,
            oscillation_decay=oscillation_decay,
            adaptive_r_min=adaptive_r_min,
            r_min_ema_alpha=r_min_ema_alpha,
        )
        super().__init__(params, defaults)
        self.order_history: list[float] = []
        self.lr_history: list[float] = []
        for group in self.param_groups:
            for p in group["params"]:
                self.state[p]["_bridge"] = ScalrBridge(
                    lr=group["lr"],
                    momentum=group["momentum"],
                    weight_decay=group["weight_decay"],
                    r_min=group["r_min"],
                    alpha=group["alpha"],
                    warmup_steps=group["warmup_steps"],
                    oscillation_window=group["oscillation_window"],
                    oscillation_threshold=group["oscillation_threshold"],
                    oscillation_decay=group["oscillation_decay"],
                    adaptive_r_min=group["adaptive_r_min"],
                    r_min_ema_alpha=group["r_min_ema_alpha"],
                )

    def compute_lr_scale(self, order_parameter: float) -> float:
        """Return the SCALR learning-rate multiplier for ``order_parameter``."""
        group = self.param_groups[0]
        r_min = float(group["r_min"])
        alpha = float(group["alpha"])
        r = max(0.0, min(1.0, order_parameter))
        return float(r_min + (1.0 - r_min) * (r**alpha))

    @torch.no_grad()
    def step(
        self,
        closure: Any = None,
        order_parameter: float | None = None,
    ) -> Any:
        """Apply one update to every parameter with a gradient.

        Args:
            closure: Standard PyTorch closure re-evaluating the loss under
                gradient tracking, if supplied.
            order_parameter: The network's current global Kuramoto order
                parameter, or ``None`` for full base lr this step.
        """
        loss = None
        if closure is not None:
            with torch.enable_grad():
                loss = closure()

        for group in self.param_groups:
            for p in group["params"]:
                if p.grad is None:
                    continue
                bridge = self.state[p]["_bridge"]
                flat_param = (
                    p.detach()
                    .to(dtype=torch.float64, device="cpu")
                    .reshape(-1)
                    .contiguous()
                )
                flat_grad = (
                    p.grad.detach()
                    .to(dtype=torch.float64, device="cpu")
                    .reshape(-1)
                    .contiguous()
                )
                updated = from_dlpack(
                    bridge.step(flat_param, flat_grad, order_parameter)
                )
                p.data.copy_(updated.reshape(p.shape))

        lr_scale = (
            1.0 if order_parameter is None else self.compute_lr_scale(order_parameter)
        )
        lr = self.param_groups[0]["lr"] * lr_scale
        self.order_history.append(
            order_parameter if order_parameter is not None else 0.0
        )
        self.lr_history.append(lr)
        return loss

    def rust_state_dict(self) -> list[str]:
        """One JSON snapshot per parameter, in ``param_groups`` order."""
        return [
            self.state[p]["_bridge"].state_dict()
            for group in self.param_groups
            for p in group["params"]
        ]

    def load_rust_state_dict(self, states: list[str]) -> None:
        """Restore state previously produced by :meth:`rust_state_dict`.

        Raises:
            ValueError: If `states`'s length does not match the number of
                optimized parameters, or on malformed JSON.
        """
        params = [p for group in self.param_groups for p in group["params"]]
        if len(states) != len(params):
            raise ValueError(f"expected {len(params)} states, got {len(states)}")
        for p, s in zip(params, states, strict=True):
            self.state[p]["_bridge"].load_state_dict(s)


class Rip(torch.optim.Optimizer):
    """Resonance-Induced Plasticity: a phase-coherence Hebbian update.

    PRINet 3.0 ``RIPOptimizer``. Unlike :class:`SyncGd`/:class:`Scalr`,
    `Rip` optimizes exactly one square ``[n, n]`` coupling-matrix parameter
    (matching the reference class's own single-purpose contract — see
    ``crates/prin-train/src/rip.rs``'s module docs). See the module docs for
    the ``step(phase=..., amplitude=...)`` deviation from the standard
    optimizer interface.

    Args:
        params: An iterable containing exactly one square ``[n, n]``
            coupling-matrix parameter.
        lr: Learning rate (eta).
        target_amplitude: Target amplitude (r_target) for the Hebbian rule.

    Raises:
        ValueError: If `params` does not contain exactly one square 2-D
            parameter.
    """

    def __init__(
        self,
        params: Any,
        lr: float = 0.01,
        target_amplitude: float = 1.0,
    ) -> None:
        """Construct over exactly one square coupling-matrix parameter."""
        params = list(params)
        if len(params) != 1:
            raise ValueError(
                f"Rip optimizes exactly one coupling-matrix parameter, "
                f"got {len(params)}"
            )
        (coupling,) = params
        if coupling.dim() != 2 or coupling.shape[0] != coupling.shape[1]:
            raise ValueError(
                f"Rip requires a square [n, n] coupling matrix parameter, "
                f"got shape {tuple(coupling.shape)}"
            )
        defaults = dict(lr=lr, target_amplitude=target_amplitude)
        super().__init__(params, defaults)
        n = int(coupling.shape[0])
        self._bridge = RipBridge(n, lr=lr, target_amplitude=target_amplitude)

    @property
    def n_oscillators(self) -> int:
        """Number of oscillators the coupling matrix couples."""
        n: int = self._bridge.n_oscillators
        return n

    @torch.no_grad()
    def step(
        self,
        closure: Any = None,
        phase: torch.Tensor | None = None,
        amplitude: torch.Tensor | None = None,
    ) -> Any:
        """Apply one Hebbian(+gradient) update to the coupling matrix.

        Args:
            closure: Standard PyTorch closure re-evaluating the loss under
                gradient tracking, if supplied.
            phase: Per-oscillator phase, shape ``(batch, n)``, or ``None``
                to skip the Hebbian term (plain gradient descent only).
            amplitude: Per-oscillator amplitude, shape ``(batch, n)``.
                Must be supplied together with `phase`.
        """
        loss = None
        if closure is not None:
            with torch.enable_grad():
                loss = closure()

        (coupling,) = self.param_groups[0]["params"]
        grad = (
            coupling.grad.detach().contiguous() if coupling.grad is not None else None
        )
        updated = from_dlpack(
            self._bridge.step(coupling.detach().contiguous(), grad, phase, amplitude)
        )
        coupling.data.copy_(updated)

        return loss

    def rust_state_dict(self) -> str:
        """Serialize the optimizer's configuration to JSON."""
        state: str = self._bridge.state_dict()
        return state

    def load_rust_state_dict(self, state: str) -> None:
        """Restore state previously produced by :meth:`rust_state_dict`."""
        self._bridge.load_state_dict(state)


# ======================================================================
# PRINet 3.0 ``nn.optimizers`` compatibility surface
# ======================================================================
#
# :class:`SynchronizedGradientDescent`, :class:`RIPOptimizer`, and
# :class:`SCALROptimizer` reproduce the PRINet 3.0 ``nn/optimizers.py`` public
# API exactly (constructor validation, ``step`` deviations, and the
# metric-history / feedback attributes the acceptance suite inspects). Every
# **parameter tensor update** is delegated to the same Rust bridges the
# WP-027 wrappers use (``SyncGdBridge`` for SGD / SCALR steps,
# ``RipBridge`` for the Hebbian coupling rule); only the scalar
# order-parameter feedback bookkeeping (penalty value, learning-rate scale,
# oscillation-decay and adaptive-``r_min`` state) is mirrored in Python, the
# same split the ``Scalr.compute_lr_scale`` helper already uses.


class SynchronizedGradientDescent(torch.optim.Optimizer):
    """SGD with a synchronization-barrier penalty (PRINet 3.0).

    The total training objective is
    ``L_total = L_task + sync_penalty * max(0, critical_order - r)^2`` where
    ``r`` is the current Kuramoto order parameter. Below ``critical_order``
    the penalty's gradient scale reduces the effective learning rate.

    Args:
        params: Iterable of parameters to optimize.
        lr: Learning rate.
        momentum: Momentum factor.
        weight_decay: L2 weight-decay coefficient.
        sync_penalty: Synchronization penalty weight.
        critical_order: Critical order-parameter threshold in ``[0, 1]``.
        dampening: Momentum dampening.

    Raises:
        ValueError: If any hyperparameter is outside its valid range.
    """

    def __init__(
        self,
        params: Any,
        lr: float = 0.01,
        momentum: float = 0.0,
        weight_decay: float = 0.0,
        sync_penalty: float = 0.1,
        critical_order: float = 0.5,
        dampening: float = 0.0,
    ) -> None:
        """Validate PRINet 3.0 hyperparameters and build one bridge per param."""
        if lr < 0.0:
            raise ValueError(f"Invalid learning rate: {lr}")
        if momentum < 0.0:
            raise ValueError(f"Invalid momentum value: {momentum}")
        if weight_decay < 0.0:
            raise ValueError(f"Invalid weight_decay value: {weight_decay}")
        if sync_penalty < 0.0:
            raise ValueError(f"Invalid sync_penalty value: {sync_penalty}")
        if not 0.0 <= critical_order <= 1.0:
            raise ValueError(f"critical_order must be in [0, 1], got {critical_order}")
        defaults = dict(
            lr=lr,
            momentum=momentum,
            weight_decay=weight_decay,
            sync_penalty=sync_penalty,
            critical_order=critical_order,
            dampening=dampening,
        )
        super().__init__(params, defaults)
        self._order_history: list[float] = []
        self._penalty_history: list[float] = []
        for group in self.param_groups:
            for p in group["params"]:
                self.state[p]["_bridge"] = SyncGdBridge(
                    lr=group["lr"],
                    momentum=group["momentum"],
                    weight_decay=group["weight_decay"],
                    sync_penalty=group["sync_penalty"],
                    critical_order=group["critical_order"],
                    dampening=group["dampening"],
                )

    @property
    def order_history(self) -> list[float]:
        """Order-parameter values recorded across optimization steps."""
        return self._order_history

    @property
    def penalty_history(self) -> list[float]:
        """Synchronization-penalty values recorded across steps."""
        return self._penalty_history

    def compute_sync_penalty(self, order_parameter: float) -> tuple[float, float]:
        """Return ``(penalty, grad_scale)`` and record the step histories.

        ``penalty = sync_penalty * max(0, critical_order - r)^2`` and
        ``grad_scale = 2 * sync_penalty * deficit`` when the deficit is
        positive, matching PRINet 3.0 exactly.
        """
        k_c = self.defaults["critical_order"]
        lam = self.defaults["sync_penalty"]
        deficit = max(0.0, k_c - order_parameter)
        penalty = lam * deficit**2
        grad_scale = 2.0 * lam * deficit if deficit > 0.0 else 0.0
        self._order_history.append(order_parameter)
        self._penalty_history.append(penalty)
        return penalty, grad_scale

    @torch.no_grad()
    def step(
        self,
        closure: Any = None,
        order_parameter: float | None = None,
    ) -> Any:
        """Apply one synchronized SGD step to every parameter with a gradient."""
        loss = None
        if closure is not None:
            with torch.enable_grad():
                loss = closure()

        penalty_value = 0.0
        if order_parameter is not None:
            penalty_value, _ = self.compute_sync_penalty(order_parameter)

        for group in self.param_groups:
            for p in group["params"]:
                if p.grad is None:
                    continue
                bridge = self.state[p]["_bridge"]
                updated = from_dlpack(
                    bridge.step(_bridge_vec(p), _bridge_vec(p.grad), order_parameter)
                )
                p.data.copy_(
                    updated.reshape(p.shape).to(dtype=p.dtype, device=p.device)
                )

        if loss is not None:
            return loss + penalty_value
        return loss


class RIPOptimizer(torch.optim.Optimizer):
    """Resonance-Induced Plasticity optimizer (PRINet 3.0).

    Applies plain gradient descent to every parameter, plus a Hebbian
    coupling update ``dK_ij = lr * cos(phi_i - phi_j) * |r_j| *
    (target_amplitude - r_i)`` (with a zeroed diagonal) to every square 2-D
    parameter when ``phase``/``amplitude`` are supplied to :meth:`step`.

    Args:
        params: Iterable of parameters to optimize.
        lr: Learning rate.
        target_amplitude: Target amplitude for the Hebbian rule.

    Raises:
        ValueError: If ``lr`` is negative or ``target_amplitude`` is
            non-positive.
    """

    def __init__(
        self,
        params: Any,
        lr: float = 0.01,
        target_amplitude: float = 1.0,
    ) -> None:
        """Validate PRINet 3.0 hyperparameters."""
        if lr < 0.0:
            raise ValueError(f"Invalid learning rate: {lr}")
        if target_amplitude <= 0.0:
            raise ValueError(
                f"target_amplitude must be positive, got {target_amplitude}"
            )
        super().__init__(params, dict(lr=lr, target_amplitude=target_amplitude))

    @staticmethod
    def _is_square(p: torch.Tensor) -> bool:
        """Return whether ``p`` is a square 2-D coupling-style parameter."""
        return p.dim() == 2 and p.shape[0] == p.shape[1]

    @torch.no_grad()
    def step(
        self,
        closure: Any = None,
        phase: torch.Tensor | None = None,
        amplitude: torch.Tensor | None = None,
    ) -> Any:
        """Apply a RIP (gradient + optional Hebbian) update."""
        loss = None
        if closure is not None:
            with torch.enable_grad():
                loss = closure()

        for group in self.param_groups:
            lr = group["lr"]
            r_target = group["target_amplitude"]
            for p in group["params"]:
                state = self.state[p]
                if (
                    phase is not None
                    and amplitude is not None
                    and self._is_square(p)
                    and phase.shape[-1] == p.shape[0]
                ):
                    n = int(p.shape[0])
                    bridge = state.get("_rip_bridge")
                    if bridge is None:
                        bridge = state["_rip_bridge"] = RipBridge(
                            n, lr=lr, target_amplitude=r_target
                        )
                    ph = _bridge_mat(phase)
                    am = _bridge_mat(amplitude)
                    if ph.dim() == 1:
                        ph = ph.unsqueeze(0).contiguous()
                    if am.dim() == 1:
                        am = am.unsqueeze(0).contiguous()
                    grad = _bridge_mat(p.grad) if p.grad is not None else None
                    updated = from_dlpack(bridge.step(_bridge_mat(p), grad, ph, am))
                    p.data.copy_(
                        updated.reshape(p.shape).to(dtype=p.dtype, device=p.device)
                    )
                elif p.grad is not None:
                    bridge = state.get("_sgd_bridge")
                    if bridge is None:
                        bridge = state["_sgd_bridge"] = SyncGdBridge(lr=lr)
                    updated = from_dlpack(
                        bridge.step(_bridge_vec(p), _bridge_vec(p.grad), None)
                    )
                    p.data.copy_(
                        updated.reshape(p.shape).to(dtype=p.dtype, device=p.device)
                    )

        return loss


class SCALROptimizer(torch.optim.Optimizer):
    """Synchronization-Coupled Adaptive Learning Rate optimizer (PRINet 3.0).

    Scales the base learning rate by ``f(r) = r_min + (1 - r_min) * r^alpha``
    and applies PRINet 3.0's Q3 enhancements — oscillation-aware exponential
    decay, per-frequency-group order parameters, and EMA-adaptive ``r_min``.
    Every parameter update and every feedback-state transition is computed by
    the Rust ``ScalrBridge``; the Python attributes mirror its state.

    Args:
        params: Iterable of parameters to optimize.
        lr: Base learning rate.
        momentum: Momentum factor.
        weight_decay: L2 weight-decay coefficient.
        r_min: Minimum learning-rate fraction as ``r -> 0``.
        alpha: Synchronization-sensitivity exponent.
        warmup_steps: Steps at full base lr before SCALR scaling starts.
        oscillation_window: Window size for oscillation detection.
        oscillation_threshold: Windowed-variance threshold for detection.
        oscillation_decay: Multiplicative lr decay per detection.
        adaptive_r_min: Auto-adjust ``r_min`` from an EMA of ``r``.
        r_min_ema_alpha: EMA smoothing factor for adaptive ``r_min``.

    Raises:
        ValueError: If any hyperparameter is outside its valid range.
    """

    def __init__(
        self,
        params: Any,
        lr: float = 0.01,
        momentum: float = 0.0,
        weight_decay: float = 0.0,
        r_min: float = 0.1,
        alpha: float = 1.0,
        warmup_steps: int = 0,
        oscillation_window: int = 20,
        oscillation_threshold: float = 0.01,
        oscillation_decay: float = 0.95,
        adaptive_r_min: bool = False,
        r_min_ema_alpha: float = 0.1,
    ) -> None:
        """Validate PRINet 3.0 hyperparameters and build one bridge per param."""
        if lr < 0.0:
            raise ValueError(f"Invalid learning rate: {lr}")
        if momentum < 0.0:
            raise ValueError(f"Invalid momentum value: {momentum}")
        if weight_decay < 0.0:
            raise ValueError(f"Invalid weight_decay: {weight_decay}")
        if not 0.0 <= r_min <= 1.0:
            raise ValueError(f"r_min must be in [0, 1], got {r_min}")
        if alpha <= 0.0:
            raise ValueError(f"alpha must be positive, got {alpha}")
        if warmup_steps < 0:
            raise ValueError(f"warmup_steps must be non-negative, got {warmup_steps}")

        super().__init__(
            params, dict(lr=lr, momentum=momentum, weight_decay=weight_decay)
        )
        self._bridge_cfg: dict[str, Any] = dict(
            lr=lr,
            momentum=momentum,
            weight_decay=weight_decay,
            r_min=r_min,
            alpha=alpha,
            warmup_steps=warmup_steps,
            oscillation_window=oscillation_window,
            oscillation_threshold=oscillation_threshold,
            oscillation_decay=oscillation_decay,
            adaptive_r_min=adaptive_r_min,
            r_min_ema_alpha=r_min_ema_alpha,
        )
        self._r_min = r_min
        self._alpha = alpha
        self._warmup_steps = warmup_steps
        self._step_count = 0
        self._oscillation_window = oscillation_window
        self._oscillation_threshold = oscillation_threshold
        self._oscillation_decay = oscillation_decay
        self._lr_decay_factor = 1.0
        self._adaptive_r_min = adaptive_r_min
        self._r_min_ema_alpha = r_min_ema_alpha
        self._r_ema: float | None = None
        self._lr_history: list[float] = []
        self._order_history: list[float] = []
        for group in self.param_groups:
            for p in group["params"]:
                self.state[p]["_bridge"] = ScalrBridge(**self._bridge_cfg)

    @property
    def lr_history(self) -> list[float]:
        """Effective learning rates recorded across steps."""
        return self._lr_history

    @property
    def order_history(self) -> list[float]:
        """Order-parameter values recorded across steps."""
        return self._order_history

    def compute_lr_scale(self, order_parameter: float) -> float:
        """Return the SCALR learning-rate multiplier for ``order_parameter``."""
        r = max(0.0, min(1.0, order_parameter))
        return float(self._r_min + (1.0 - self._r_min) * (r**self._alpha))

    def _bridges(self) -> list[Any]:
        """Every per-parameter ``ScalrBridge`` in ``param_groups`` order."""
        return [
            self.state[p]["_bridge"]
            for group in self.param_groups
            for p in group["params"]
        ]

    def _push_feedback_state(self) -> None:
        """Mirror the Python feedback state into every Rust bridge."""
        for bridge in self._bridges():
            snap = json.loads(bridge.state_dict())
            snap["order_history"] = list(self._order_history)
            snap["lr_decay_factor"] = self._lr_decay_factor
            snap["r_ema"] = self._r_ema
            snap["r_min"] = self._r_min
            bridge.load_state_dict(json.dumps(snap))

    def _pull_feedback_state(self, bridge: Any) -> None:
        """Refresh the Python feedback state from one Rust bridge."""
        snap = json.loads(bridge.state_dict())
        self._order_history = list(snap["order_history"])
        self._lr_history = list(snap["lr_history"])
        self._lr_decay_factor = float(snap["lr_decay_factor"])
        self._r_ema = None if snap["r_ema"] is None else float(snap["r_ema"])
        self._r_min = float(snap["r_min"])

    @torch.no_grad()
    def step(
        self,
        closure: Any = None,
        order_parameter: float | dict[str, float] | None = None,
    ) -> Any:
        """Apply one SCALR step, delegating all numerics to the Rust bridge."""
        loss = None
        if closure is not None:
            with torch.enable_grad():
                loss = closure()

        self._step_count += 1
        if isinstance(order_parameter, dict):
            values = list(order_parameter.values())
            global_r: float | None = sum(values) / max(len(values), 1)
        elif order_parameter is not None:
            global_r = order_parameter
        else:
            global_r = None

        self._push_feedback_state()

        stepped: Any = None
        for group in self.param_groups:
            for p in group["params"]:
                if p.grad is None:
                    continue
                bridge = self.state[p]["_bridge"]
                updated = from_dlpack(
                    bridge.step(_bridge_vec(p), _bridge_vec(p.grad), global_r)
                )
                p.data.copy_(
                    updated.reshape(p.shape).to(dtype=p.dtype, device=p.device)
                )
                stepped = bridge

        if stepped is None and global_r is not None:
            # No parameter had a gradient; still advance the feedback state so
            # the order-parameter history is recorded (PRINet 3.0 semantics).
            bridges = self._bridges()
            if bridges:
                dummy = torch.zeros(1, dtype=torch.float64)
                bridges[0].step(dummy, None, global_r)
                stepped = bridges[0]

        source = stepped if stepped is not None else self._bridges()[0]
        self._pull_feedback_state(source)
        return loss
