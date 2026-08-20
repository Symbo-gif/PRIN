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

from typing import Any

import torch
from torch.utils.dlpack import from_dlpack

from prin._prin_core import RipBridge, ScalrBridge, SyncGdBridge

__all__: list[str] = ["Rip", "Scalr", "SyncGd"]


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
