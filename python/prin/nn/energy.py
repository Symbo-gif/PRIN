"""Holomorphic energy and equilibrium-propagation trainer (compat surface).

Thin wrappers over the Rust ``prin-train::{energy,hep}`` owners (WP-023),
exposed via ``prin._prin_core`` (WP-036 S1 sub-pass 0141B). No numerics here —
see ``crates/prin-train/src/{energy,hep}.rs``.

Documented deviations from the PRINet 3.0 signatures (both owned by the Rust
crate, not introduced here):

- :class:`HolomorphicEnergy` takes a precomputed per-batch ``task_loss``
  ``(B, 1)`` rather than PRINet's ``target_logits`` / ``target_labels``: the
  ``concept_proj`` classification head that produces logits is model-level and
  deferred to WP-027.
- :class:`HolomorphicEPTrainer` exposes the physics-level ``coupling_gradient``
  / ``free_energy`` estimator. The SGD parameter update (``train_step``) and
  loss/grad-norm history belong to the WP-024 optimizers and WP-027 model
  integration; ``loss_history`` / ``grad_norm_history`` are present but stay
  empty.
"""

from __future__ import annotations

import torch
from torch.utils.dlpack import from_dlpack

from prin._prin_core import (
    HolomorphicEnergyBridge,
    HolomorphicEpTrainer,
    ResonanceLayerBridge,
)

from ._bridge import apply_rust_bridge

__all__ = ["HolomorphicEPTrainer", "HolomorphicEnergy"]


def _f64(tensor: torch.Tensor) -> torch.Tensor:
    """Return ``tensor`` as a detached contiguous CPU ``float64`` view."""
    return tensor.detach().to(dtype=torch.float64, device="cpu").contiguous()


class HolomorphicEnergy(torch.nn.Module):
    """Holomorphic energy of a complex oscillator state under real coupling.

    ``E = mean_batch(-sum_ij K[i,j] * Re(conj(z_i) z_j) + sum_i (|z_i|^2 - 1)^2 +
    beta * task_loss)``, bridged to Rust forward/backward via DLPack. Stateless
    (no learnable parameters).

    Args:
        n_oscillators: Number of complex oscillators.

    Examples:
        >>> import torch
        >>> from prin.nn import HolomorphicEnergy
        >>> energy = HolomorphicEnergy(4)
        >>> z = torch.ones(2, 4, dtype=torch.complex128)
        >>> k = torch.zeros(4, 4, dtype=torch.float64)
        >>> float(energy(z, k))
        0.0
    """

    def __init__(self, n_oscillators: int) -> None:
        """Construct the energy function for ``n_oscillators`` oscillators."""
        super().__init__()
        self._bridge = HolomorphicEnergyBridge(n_oscillators)

    @property
    def n_oscillators(self) -> int:
        """Number of complex oscillators."""
        return self._bridge.n_oscillators

    def forward(
        self,
        z: torch.Tensor,
        coupling: torch.Tensor,
        task_loss: torch.Tensor | None = None,
        beta: float = 0.0,
    ) -> torch.Tensor:
        """Compute the scalar batch-averaged energy.

        Args:
            z: Complex oscillator states ``(B, N)`` (``complex128``) or a real
                ``(B, N)`` tensor (imaginary part taken as zero).
            coupling: Real coupling matrix ``(N, N)``, ``float64``.
            task_loss: Optional precomputed per-batch loss ``(B, 1)``,
                ``float64`` (see the module docstring's deviation note).
            beta: Scales ``task_loss``; applied only when non-zero.

        Returns:
            Scalar energy, shape ``(1,)``.

        Raises:
            ValueError: On a dtype/device/shape violation from the Rust owner.
        """
        if torch.is_complex(z):
            re = z.real.contiguous()
            im = z.imag.contiguous()
        else:
            re = z
            im = torch.zeros_like(z)
        task_capsule = _f64(task_loss) if task_loss is not None else None

        def _forward(
            re_t: torch.Tensor, im_t: torch.Tensor, coupling_t: torch.Tensor
        ) -> tuple[object, ...]:
            """Invoke the Rust bridge with the non-tensor arguments bound."""
            return self._bridge.forward(re_t, im_t, coupling_t, task_capsule, beta)

        result: torch.Tensor = apply_rust_bridge(_forward, [re, im, coupling])
        return result


def _find_resonance_bridge(model: object) -> ResonanceLayerBridge:
    """Return the first ``ResonanceLayerBridge`` reachable from ``model``.

    Accepts a :class:`prin.nn.ResonanceLayer` directly or any
    ``torch.nn.Module`` that contains one, matching PRINet 3.0's
    ``HolomorphicEPTrainer`` model-introspection contract.
    """
    direct = getattr(model, "_bridge", None)
    if isinstance(direct, ResonanceLayerBridge):
        return direct
    if isinstance(model, torch.nn.Module):
        for module in model.modules():
            candidate = getattr(module, "_bridge", None)
            if isinstance(candidate, ResonanceLayerBridge):
                return candidate
    raise ValueError("model must contain at least one prin.nn.ResonanceLayer")


class HolomorphicEPTrainer:
    """+/-beta Holomorphic Equilibrium Propagation gradient estimator.

    Runs a :class:`prin.nn.ResonanceLayer`'s dynamics to the free and
    +/-beta-nudged equilibria and returns a closed-form coupling-gradient estimate
    — first-order-accurate gradients without backpropagation through time.

    Args:
        model: A :class:`prin.nn.ResonanceLayer`, or a ``torch.nn.Module``
            containing one.
        beta: Nudge strength (must be positive). PRINet 3.0 typical range
            ``[0.01, 0.5]``.
        free_steps: Integration steps for the free-phase equilibrium.
        nudge_steps: Integration steps for each nudge-phase equilibrium.
        energy_fn: Optional :class:`HolomorphicEnergy`; a fresh one for the
            layer's oscillator count is built when ``None``.

    Examples:
        >>> import torch
        >>> from prin.nn import ResonanceLayer, HolomorphicEPTrainer
        >>> layer = ResonanceLayer(4, 6, n_steps=3, seed_counter=1)
        >>> trainer = HolomorphicEPTrainer(layer, beta=0.1, free_steps=4, nudge_steps=3)
        >>> x = torch.ones(2, 6, dtype=torch.float64)
        >>> g = trainer.coupling_gradient(x, torch.ones(2, 4, dtype=torch.float64))
        >>> g.shape
        torch.Size([4, 4])
    """

    def __init__(
        self,
        model: object,
        beta: float = 0.1,
        free_steps: int = 50,
        nudge_steps: int = 20,
        energy_fn: HolomorphicEnergy | None = None,
    ) -> None:
        """Bind the trainer to ``model``'s first resonance layer."""
        self._layer_bridge = _find_resonance_bridge(model)
        n_osc = self._layer_bridge.n_oscillators
        self._bridge = HolomorphicEpTrainer(n_osc, beta, free_steps, nudge_steps)
        self._energy_fn = (
            energy_fn if energy_fn is not None else HolomorphicEnergy(n_osc)
        )
        self._loss_history: list[float] = []
        self._grad_norm_history: list[float] = []

    @property
    def beta(self) -> float:
        """Nudge strength beta."""
        return self._bridge.beta

    @beta.setter
    def beta(self, value: float) -> None:
        """Set the nudge strength beta (must be positive)."""
        self._bridge.beta = value

    @property
    def loss_history(self) -> list[float]:
        """Training-loss history (empty — the SGD loop is WP-024/WP-027)."""
        return self._loss_history

    @property
    def grad_norm_history(self) -> list[float]:
        """Gradient-norm history (empty — the SGD loop is WP-024/WP-027)."""
        return self._grad_norm_history

    def coupling_gradient(
        self, x: torch.Tensor, target_direction: torch.Tensor
    ) -> torch.Tensor:
        """Closed-form +/-beta coupling-gradient estimate.

        Args:
            x: Input features ``(batch, n_dims)``.
            target_direction: Nudge direction ``(batch, n_oscillators)``.

        Returns:
            Coupling gradient ``(n_oscillators, n_oscillators)``.

        Raises:
            ValueError: On a dtype/device/shape violation from the Rust owner.
        """
        capsule = self._bridge.coupling_gradient(
            self._layer_bridge, _f64(x), _f64(target_direction)
        )
        return from_dlpack(capsule)

    def free_energy(self, x: torch.Tensor, coupling: torch.Tensor) -> torch.Tensor:
        """Physics energy (beta=0) of the free-phase equilibrium.

        Args:
            x: Input features ``(batch, n_dims)``.
            coupling: Real coupling matrix ``(n_oscillators, n_oscillators)``.

        Returns:
            Scalar energy, shape ``(1,)``.

        Raises:
            ValueError: On a dtype/device/shape violation from the Rust owner.
        """
        capsule = self._bridge.free_energy(self._layer_bridge, _f64(x), _f64(coupling))
        return from_dlpack(capsule)
