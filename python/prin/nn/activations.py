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
            z: Input. Shape ``(batch, n)``, dtype ``float64``, CPU, contiguous.

        Returns:
            Activated tensor of the same shape.

        Raises:
            ValueError: If ``z`` is not ``float64``/CPU/contiguous or not 2-D.
        """
        result: torch.Tensor = apply_rust_bridge(self._bridge.forward, [z])
        return result


class PhaseActivation(torch.nn.Module):
    """Phase-aware activation wrapping ``dSiLU(z)`` to ``[0, 2*pi)``.

    Matches PRINet 3.0's ``PhaseActivation`` with its default inner activation.
    A caller-supplied inner activation (PRINet's ``activation=`` argument) has
    no Rust owner yet and raises :class:`NotImplementedError` — a WP-036B/C
    parity item, not this pass.

    Examples:
        >>> import torch
        >>> from prin.nn import PhaseActivation
        >>> act = PhaseActivation()
        >>> y = act(torch.randn(2, 3, dtype=torch.float64))
        >>> bool((y >= 0).all() and (y < 2 * torch.pi).all())
        True
    """

    def __init__(self, activation: torch.nn.Module | None = None) -> None:
        """Construct the phase activation (default ``dSiLU`` inner only).

        Raises:
            NotImplementedError: If ``activation`` is not ``None``.
        """
        super().__init__()
        if activation is not None:
            raise NotImplementedError(
                "prin.nn.PhaseActivation supports only the default dSiLU inner "
                "activation; a custom inner activation is a WP-036B/C parity item"
            )
        self._bridge = PhaseActivationBridge()

    def forward(self, z: torch.Tensor) -> torch.Tensor:
        """Apply ``dSiLU`` then wrap to ``[0, 2*pi)``.

        Args:
            z: Input. Shape ``(batch, n)``, dtype ``float64``, CPU, contiguous.

        Returns:
            Phase-wrapped tensor in ``[0, 2*pi)`` of the same shape.

        Raises:
            ValueError: If ``z`` is not ``float64``/CPU/contiguous or not 2-D.
        """
        result: torch.Tensor = apply_rust_bridge(self._bridge.forward, [z])
        return result


class HolomorphicActivation(torch.nn.Module):
    """Split-complex ``scale*tanh`` activation for complex oscillator states.

    Applies ``tanh`` independently to the real and imaginary parts, each scaled
    by ``scale`` (PRINet 3.0's ``holomorphic=False`` path). For a real input
    this reduces to ``scale*tanh(z)``. The true-complex ``holomorphic=True``
    path has no Burn-autodiff analogue and raises :class:`NotImplementedError`
    (a permanent, documented ``prin-train`` deviation).

    Args:
        scale: Output scaling factor.
        holomorphic: Must be ``False`` (the split-complex path).

    Examples:
        >>> import torch
        >>> from prin.nn import HolomorphicActivation
        >>> act = HolomorphicActivation(scale=2.0)
        >>> z = torch.randn(2, 3, dtype=torch.complex128)
        >>> act(z).dtype
        torch.complex128
    """

    def __init__(self, scale: float = 1.0, holomorphic: bool = False) -> None:
        """Construct the split-complex activation.

        Raises:
            NotImplementedError: If ``holomorphic`` is ``True``.
            ValueError: If ``scale`` is not finite.
        """
        super().__init__()
        if holomorphic:
            raise NotImplementedError(
                "prin.nn.HolomorphicActivation supports only the split-complex "
                "(holomorphic=False) path; Burn has no complex-tensor autodiff "
                "(see crates/prin-train/src/activations.rs)"
            )
        self._bridge = HolomorphicActivationBridge(scale)

    @property
    def scale(self) -> float:
        """Output scaling factor."""
        return self._bridge.scale

    def forward(self, z: torch.Tensor) -> torch.Tensor:
        """Apply the split-complex activation.

        Args:
            z: Real or complex input. Shape ``(batch, n)``, real dtype
                ``float64`` / complex dtype ``complex128``, CPU, contiguous.

        Returns:
            Activated tensor of the same dtype and shape.

        Raises:
            ValueError: If ``z`` (or its parts) is not the right
                dtype/device/layout or not 2-D.
        """
        if torch.is_complex(z):
            re = z.real.contiguous()
            im = z.imag.contiguous()
            out_re, out_im = apply_rust_bridge(self._bridge.forward, [re, im])
            return torch.complex(out_re, out_im)
        out_re, _ = apply_rust_bridge(self._bridge.forward, [z, torch.zeros_like(z)])
        result: torch.Tensor = out_re
        return result
