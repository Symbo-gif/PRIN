"""Oscillator-compatible activations (PRINet-3.0-compatible surface).

``torch.nn.Module`` wrappers over the Rust ``prin-train::activations`` owners
(WP-023), bridged to ``torch.autograd.Function`` via DLPack (WP-036 S1 sub-pass
0141B). No numerics here — see ``crates/prin-train/src/activations.rs``.

- :class:`dSiLU` — the exact SiLU derivative
  ``sigmoid(z) * (1 + z * (1 - sigmoid(z)))``.
- :class:`PhaseActivation` — ``dSiLU`` followed by wrapping to ``[0, 2*pi)``.
- :class:`HolomorphicActivation` — split-complex ``scale * tanh`` on the real and
  imaginary parts independently (PRINet 3.0's ``holomorphic=False`` path; the
  true-complex path has no Burn-autodiff analogue and is out of scope — see the
  Rust module's "Complex representation" note).

``dSiLU`` and ``PhaseActivation`` inherit ``burn-tensor`` 0.16.1's
``f32``-internal ``sigmoid`` precision floor
(``DOCS/reports/DEFERRED_VALIDATION_REGISTER.md`` DV-018); their gradcheck
tests use the DV-018 epsilon.
"""

from __future__ import annotations

import math

import torch

from prin._prin_core import (
    DSiLUBridge,
    HolomorphicActivationBridge,
    PhaseActivationBridge,
)

from ._bridge import apply_rust_bridge

__all__ = ["HolomorphicActivation", "PhaseActivation", "dSiLU"]


class dSiLU(torch.nn.Module):
    """Derivative of SiLU (Swish): ``sigmoid(z) * (1 + z * (1 - sigmoid(z)))``.

    Non-monotonic and naturally bounded (``dSiLU(0) = 0.5``), which PRINet 3.0
    notes suits phase-coupled oscillatory layers. Stateless; bridged to Rust
    forward/backward via DLPack.

    Examples:
        >>> import torch
        >>> from prin.nn import dSiLU
        >>> act = dSiLU()
        >>> act(torch.zeros(2, 3, dtype=torch.float64))[0, 0].item()
        0.5
    """

    def __init__(self) -> None:
        """Construct the stateless activation."""
        super().__init__()
        self._bridge = DSiLUBridge()

    def forward(self, z: torch.Tensor) -> torch.Tensor:
        """Apply ``dSiLU`` elementwise.

        Args:
            z: Input. Shape ``(batch, n)``, ``(n,)`` or scalar, dtype
                ``float64`` or ``float32``, CPU, contiguous.

        Returns:
            Activated tensor of the same shape.

        Raises:
            ValueError: If ``z`` is not CPU/contiguous or not 2-D/1-D/0-D.
        """
        was_scalar = z.dim() == 0
        was_vector = z.dim() == 1
        if was_scalar:
            batched = z.view(1, 1)
        elif was_vector:
            batched = z.unsqueeze(0)
        else:
            batched = z
        result: torch.Tensor = apply_rust_bridge(self._bridge.forward, [batched])
        if was_scalar:
            return result.view(())
        if was_vector:
            return result.squeeze(0)
        return result


class PhaseActivation(torch.nn.Module):
    """Phase-aware activation wrapping an inner activation to ``[0, 2*pi)``.

    Matches PRINet 3.0's ``PhaseActivation``. The default inner activation is
    the Rust-backed ``dSiLU`` owner; a caller-supplied ``torch.nn.Module`` is
    applied in PyTorch and then phase-wrapped.

    Examples:
        >>> import torch
        >>> from prin.nn import PhaseActivation
        >>> act = PhaseActivation()
        >>> y = act(torch.randn(2, 3, dtype=torch.float64))
        >>> bool((y >= 0).all() and (y < 2 * torch.pi).all())
        True
    """

    def __init__(self, activation: torch.nn.Module | None = None) -> None:
        """Construct the phase activation."""
        super().__init__()
        self._inner = activation
        self._bridge = None if activation is not None else PhaseActivationBridge()

    def forward(self, z: torch.Tensor) -> torch.Tensor:
        """Apply the inner activation then wrap to ``[0, 2*pi)``.

        Args:
            z: Input. Shape ``(batch, n)``, dtype ``float64`` or ``float32``,
                CPU, contiguous.

        Returns:
            Phase-wrapped tensor in ``[0, 2*pi)`` of the same shape.

        Raises:
            ValueError: If ``z`` is not CPU/contiguous or not 2-D.
        """
        if self._inner is not None:
            y = self._inner(z)
            return torch.remainder(y, 2.0 * math.pi)
        if self._bridge is None:
            raise RuntimeError(
                "PhaseActivation has no Rust bridge for the default path"
            )
        result: torch.Tensor = apply_rust_bridge(self._bridge.forward, [z])
        return result


class HolomorphicActivation(torch.nn.Module):
    """Complex ``scale*tanh`` activation for oscillator states.

    For ``holomorphic=False`` (PRINet 3.0's split-complex path) the real and
    imaginary parts are passed independently through ``scale*tanh``. For
    ``holomorphic=True`` the true-complex ``scale*tanh(z)`` is applied with
    ``torch.tanh``.

    Args:
        scale: Output scaling factor.
        holomorphic: ``False`` for the split-complex path, ``True`` for the
            true-complex path.

    Examples:
        >>> import torch
        >>> from prin.nn import HolomorphicActivation
        >>> act = HolomorphicActivation(scale=2.0)
        >>> z = torch.randn(2, 3, dtype=torch.complex128)
        >>> act(z).dtype
        torch.complex128
    """

    def __init__(self, scale: float = 1.0, holomorphic: bool = False) -> None:
        """Construct the activation."""
        super().__init__()
        self._scale = scale
        self._holomorphic = holomorphic
        self._bridge = HolomorphicActivationBridge(scale)

    @property
    def scale(self) -> float:
        """Output scaling factor."""
        return self._scale

    def forward(self, z: torch.Tensor) -> torch.Tensor:
        """Apply the holomorphic or split-complex activation.

        Args:
            z: Real or complex input. Shape ``(batch, n)``.

        Returns:
            Activated tensor of the same dtype and shape.
        """
        if self._holomorphic:
            return self._scale * torch.tanh(z)
        if torch.is_complex(z):
            return self._scale * torch.complex(torch.tanh(z.real), torch.tanh(z.imag))
        return self._scale * torch.tanh(z)
