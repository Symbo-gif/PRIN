"""Feedback inhibition (PRINet-3.0-compatible surface).

Thin wrapper over the Rust ``prin-train::inhibition::FeedbackInhibition`` owner
(WP-023), bridged to ``torch.autograd.Function`` via DLPack (WP-036 S1 sub-pass
0141B). No numerics here — see ``crates/prin-train/src/inhibition.rs``.

``FeedforwardInhibition`` and ``DentateGyrusConverter`` from the same PRINet 3.0
module have no learnable parameters and were deliberately never rebuilt in Rust
(WP-023 audit); they are handled by the WP-036 S1 disposition register, not
this module.
"""

from __future__ import annotations

import torch

from prin._prin_core import FeedbackInhibitionBridge

from ._bridge import apply_rust_bridge

__all__ = ["FeedbackInhibition"]


class FeedbackInhibition:
    """Top-``k`` winner-take-all feedback inhibition (hard-forward STE).

    Uses a hard-forward / soft-backward straight-through estimator.

    The forward pass returns the hard top-``k`` selection of ``rates``; the
    backward pass flows gradients through the temperature-scaled softmax
    ("soft") scores. Because the forward and backward passes compute
    deliberately different functions, this op is **not** ``gradcheck``-able as
    a true adjoint pair (see the Rust module's STE construction note); its
    gradient contract is verified against the closed-form soft-term VJP
    instead.

    Args:
        k: Number of winners. If ``None``, derived from ``sparsity`` and the
            input width at call time: ``k = min(N, max(1, floor(N*sparsity)))``.
        sparsity: Target sparsity (fraction of active units), used when
            ``k is None``.
        delay_steps: Feedback delay in integration steps. Preserved for
            call-site compatibility; the Rust STE is instantaneous (the delay
            is a reference-level concern outside WP-023 scope), so this value
            is inert.
        temperature: Softmax temperature for the soft (backward-pass) scores.

    Examples:
        >>> import torch
        >>> from prin.nn import FeedbackInhibition
        >>> fbi = FeedbackInhibition(k=2, temperature=1.0)
        >>> rates = torch.rand(4, 6, dtype=torch.float64) + 0.1
        >>> int((fbi.compete(rates) > 0).sum(-1)[0])
        2
    """

    def __init__(
        self,
        k: int | None = None,
        sparsity: float = 0.1,
        delay_steps: int = 20,
        temperature: float = 1.0,
    ) -> None:
        """Configure the competition (the Rust bridge is built lazily)."""
        if k is not None and k < 1:
            raise ValueError(f"k must be >= 1, got {k}")
        if not 0.0 < sparsity <= 1.0:
            raise ValueError(f"sparsity must be in (0, 1], got {sparsity}")
        self._k = k
        self._sparsity = sparsity
        self._delay_steps = delay_steps
        self._temperature = max(temperature, 1e-8)
        self._bridge: FeedbackInhibitionBridge | None = None
        self._width: int | None = None

    @property
    def delay_steps(self) -> int:
        """Feedback delay in steps (inert — see the class docstring)."""
        return self._delay_steps

    @property
    def temperature(self) -> float:
        """Softmax temperature (floored at ``1e-8``)."""
        return self._temperature

    def _bridge_for(self, width: int) -> FeedbackInhibitionBridge:
        """Return the bridge for the given input width, building it on demand.

        PRINet 3.0's ``FeedbackInhibition`` derives ``k`` from ``rates`` at
        ``compete`` time rather than at construction, so the Rust bridge (which
        needs the width up front) is built lazily and cached per width.
        """
        if self._bridge is None or self._width != width:
            self._bridge = FeedbackInhibitionBridge(
                width, self._k, self._sparsity, self._temperature
            )
            self._width = width
        return self._bridge

    def compete(self, rates: torch.Tensor) -> torch.Tensor:
        """Apply feedback inhibition to enforce sparse WTA.

        Args:
            rates: Rate tensor. Shape ``(batch, N)``, dtype ``float64``, CPU,
                contiguous. (Arbitrary leading batch dimensions are a WP-036B/C
                parity item.)

        Returns:
            Sparse rate tensor ``(batch, N)`` with only the top-``k`` active.

        Raises:
            ValueError: If ``rates`` is not 2-D / ``float64`` / CPU /
                contiguous.
        """
        if rates.dim() != 2:
            raise ValueError(
                f"prin.nn.FeedbackInhibition.compete requires a 2-D (batch, N) "
                f"tensor, got shape {tuple(rates.shape)}"
            )
        bridge = self._bridge_for(rates.shape[-1])
        result: torch.Tensor = apply_rust_bridge(bridge.forward, [rates])
        return result
