"""``HybridPRINetV2``: PRIN's canonical hybrid classification architecture.

See ``crates/prin-py/src/bindings/hybrid.rs`` for the Rust bridge and
``crates/prin-train/src/hybrid.rs`` for the numerical core.
"""

from __future__ import annotations

import torch

from prin._prin_core import HybridPRINetV2Bridge

from ._bridge import apply_rust_bridge

__all__: list[str] = ["HybridPRINetV2"]


class HybridPRINetV2(torch.nn.Module):
    """Hybrid oscillator + attention architecture (PRIN's canonical classifier).

    PRINet 3.0 ``nn.hybrid.HybridPRINetV2``, bridged to Rust forward/backward
    via DLPack: the whole multi-layer attention+dynamics+classifier pass is
    one Rust call per `forward` (Coding Standards §3.2, "boundary crossings
    are batched"). All parameters are Rust-owned (see
    :class:`prin.nn.ResonanceLayer`'s docs for the training-ownership split).

    ``dropout`` must be ``0.0`` — see :class:`prin.nn.OscillatoryAttention`'s
    docs for why (this network owns its own ``Dropout`` field in addition to
    composing `OscillatoryAttention`, which owns another).

    Args:
        n_input: Input feature dimension.
        n_classes: Number of output classes.
        d_model: Model dimension for attention/FFN layers.
        n_heads: Number of attention heads.
        n_layers: Number of interleaved attention+FFN blocks.
        n_delta: Delta-band oscillators.
        n_theta: Theta-band oscillators.
        n_gamma: Gamma-band oscillators.
        n_discrete_steps: Discrete dynamics steps per layer.
        coupling_strength: Initial intra-band coupling strength.
        pac_depth: Initial PAC modulation depth.
        dropout: Must be ``0.0`` (see above).
        seed_counter: Counter half of the deterministic ``Seed``.
        seed_key: Key half of the deterministic ``Seed``.

    Examples:
        >>> import torch
        >>> from prin.nn import HybridPRINetV2
        >>> net = HybridPRINetV2(6, 3, d_model=8, n_heads=2, n_layers=1,
        ...     n_delta=2, n_theta=2, n_gamma=2, n_discrete_steps=1,
        ...     seed_counter=1)
        >>> x = torch.randn(2, 6, dtype=torch.float64, requires_grad=True)
        >>> y = net(x)
        >>> y.shape
        torch.Size([2, 3])
        >>> y.sum().backward()
    """

    def __init__(
        self,
        n_input: int,
        n_classes: int,
        d_model: int = 64,
        n_heads: int = 4,
        n_layers: int = 2,
        n_delta: int = 4,
        n_theta: int = 8,
        n_gamma: int = 32,
        n_discrete_steps: int = 5,
        coupling_strength: float = 2.0,
        pac_depth: float = 0.3,
        dropout: float = 0.0,
        seed_counter: int = 0,
        seed_key: int = 0,
    ) -> None:
        """Construct with seeded-random parameters."""
        super().__init__()
        self._bridge = HybridPRINetV2Bridge(
            n_input,
            n_classes,
            d_model,
            n_heads,
            n_layers,
            n_delta,
            n_theta,
            n_gamma,
            n_discrete_steps,
            coupling_strength,
            pac_depth,
            dropout,
            seed_counter,
            seed_key,
        )

    @property
    def n_input(self) -> int:
        """Input feature dimension."""
        return self._bridge.n_input

    @property
    def n_classes(self) -> int:
        """Number of output classes."""
        return self._bridge.n_classes

    @property
    def n_tokens(self) -> int:
        """Total oscillator/token count."""
        return self._bridge.n_tokens

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        """Project, evolve, and classify.

        Args:
            x: Input features. Shape: ``(batch, n_input)``, dtype
                ``torch.float64``, CPU, contiguous.

        Returns:
            Log-probabilities. Shape: ``(batch, n_classes)``.

        Raises:
            ValueError: If `x` is not ``float64``/CPU/contiguous or its
                shape is not ``(batch, n_input)``.
        """
        result: torch.Tensor = apply_rust_bridge(self._bridge.forward, [x])
        return result

    def rust_state_dict(self) -> bytes:
        """Serialize Rust-owned parameters to opaque checkpoint bytes."""
        return self._bridge.state_dict()

    def load_rust_state_dict(self, state: bytes) -> None:
        """Restore parameters previously produced by :meth:`rust_state_dict`.

        Raises:
            ValueError: If `state` does not decode to a record with this
                network's `n_input`/`n_classes`/`n_tokens`.
        """
        self._bridge.load_state_dict(state)
