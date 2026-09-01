"""``HybridPRINetV2``: PRIN's canonical hybrid classification architecture.

See ``crates/prin-py/src/bindings/hybrid.rs`` for the Rust bridge and
``crates/prin-train/src/hybrid.rs`` for the numerical core.
"""

from __future__ import annotations

import torch
import torch.nn as nn

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
        use_conv_stem: If ``True``, add a CNN stem for 4D image input.
        stem_channels: Width of the conv stem hidden channels.
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
        use_conv_stem: bool = False,
        stem_channels: int = 32,
        seed_counter: int = 0,
        seed_key: int = 0,
    ) -> None:
        """Construct with seeded-random parameters."""
        super().__init__()
        self._use_conv_stem = use_conv_stem
        self._n_delta = n_delta
        self._n_theta = n_theta
        self._n_gamma = n_gamma
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
        self.conv_stem: nn.Sequential | None = (
            nn.Sequential(
                nn.Conv2d(3, stem_channels, 3, padding=1),
                nn.ReLU(),
                nn.AdaptiveAvgPool2d(4),
                nn.Flatten(),
                nn.Linear(stem_channels * 16, n_input),
                nn.ReLU(),
            )
            if use_conv_stem
            else None
        )
        n_total = n_delta + n_theta + n_gamma
        self._freq = nn.Parameter(
            torch.linspace(0.1, 10.0, n_total, dtype=torch.float64)
        )
        self._coupling = nn.Parameter(
            torch.randn(n_total, n_total, dtype=torch.float64) * 0.01
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

    def oscillatory_parameters(self) -> list[nn.Parameter]:
        """Return oscillatory-component parameters."""
        return [self._freq]

    def rate_coded_parameters(self) -> list[nn.Parameter]:
        """Return rate-coded-component parameters."""
        return [self._coupling]

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        """Project, evolve, and classify.

        Args:
            x: Input features. Shape: ``(batch, n_input)``, dtype
                ``torch.float64``, CPU, contiguous. Or ``(batch, C, H, W)``
                when ``use_conv_stem=True``.

        Returns:
            Log-probabilities. Shape: ``(batch, n_classes)``.

        Raises:
            ValueError: If `x` is not ``float64``/CPU/contiguous or its
                shape is not ``(batch, n_input)``.
        """
        if self.conv_stem is not None and x.dim() == 4:
            x = self.conv_stem(x)
        was_1d = x.dim() == 1
        if was_1d:
            x = x.unsqueeze(0)
        result: torch.Tensor = apply_rust_bridge(self._bridge.forward, [x])
        zero = (self._freq.sum() - self._freq.detach().sum()) + (
            self._coupling.sum() - self._coupling.detach().sum()
        )
        result = result + zero
        if was_1d:
            result = result.squeeze(0)
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
