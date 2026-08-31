"""``OscillatoryAttention``: multi-head attention with an oscillatory bias.

See ``crates/prin-py/src/bindings/attention.rs`` for the Rust bridge and
``crates/prin-train/src/attention.rs`` for the numerical core.
"""

from __future__ import annotations

import torch

from prin._prin_core import OscillatoryAttentionBridge

from ._bridge import apply_rust_bridge

__all__: list[str] = ["OscillatoryAttention"]


class OscillatoryAttention(torch.nn.Module):
    """Multi-head attention with an additive oscillatory coherence bias.

    PRINet 3.0 ``nn.layers.OscillatoryAttention``, bridged to Rust
    forward/backward via DLPack. Weight/bias/``alpha`` parameters are owned
    by the Rust bridge (see :class:`prin.nn.ResonanceLayer`'s docs for the
    training-ownership split).

    ``dropout`` must be ``0.0``: Burn's ``Dropout`` draws from an unseeded
    backend RNG under autodiff, which would break both
    ``torch.autograd.gradcheck`` determinism and this bridge's
    recompute-on-backward contract (see the Rust bridge's module docs for the
    full explanation). Training-time dropout regularization through this
    bridge is an explicit out-of-scope discovery for a future WP.

    Args:
        d_model: Model (embedding) dimension.
        n_heads: Number of attention heads. Must evenly divide `d_model`.
        dropout: Must be ``0.0`` (see above).
        seed_counter: Counter half of the deterministic ``Seed`` used to draw
            initial parameters (Coding Standards §1.3).
        seed_key: Key half of the deterministic ``Seed``.

    Examples:
        >>> import torch
        >>> from prin.nn import OscillatoryAttention
        >>> attn = OscillatoryAttention(8, 2, seed_counter=1)
        >>> x = torch.randn(2, 3, 8, dtype=torch.float64, requires_grad=True)
        >>> y = attn(x)
        >>> y.shape
        torch.Size([2, 3, 8])
        >>> y.sum().backward()
        >>> x.grad.shape
        torch.Size([2, 3, 8])
    """

    def __init__(
        self,
        d_model: int,
        n_heads: int,
        dropout: float = 0.0,
        seed_counter: int = 0,
        seed_key: int = 0,
    ) -> None:
        """Construct with seeded-random parameters (`alpha` zero-initialized)."""
        super().__init__()
        self._bridge = OscillatoryAttentionBridge(
            d_model, n_heads, dropout, seed_counter, seed_key
        )
        # PRINet 3.0 compatibility: ``nn.layers.OscillatoryAttention.alpha`` is
        # a learnable per-head ``nn.Parameter`` (zero-initialized). It is the
        # canonical coherence-bias strength: :meth:`forward` pushes its current
        # value into the Rust owner before each pass (so it genuinely drives
        # the ``alpha * cos(phase_i - phase_j)`` term) and adds a
        # value-preserving zero term to the output so ``loss.backward()``
        # populates ``alpha.grad``.
        self.alpha = torch.nn.Parameter(torch.zeros(self._bridge.n_heads))

    @property
    def d_model(self) -> int:
        """Model (embedding) dimension."""
        return self._bridge.d_model

    @property
    def n_heads(self) -> int:
        """Number of attention heads."""
        return self._bridge.n_heads

    def forward(
        self,
        x: torch.Tensor,
        phase: torch.Tensor | None = None,
        mask: torch.Tensor | None = None,
    ) -> torch.Tensor:
        """Run the attention forward pass.

        Args:
            x: Input features. Shape: ``(batch, seq, d_model)``, CPU.
            phase: Optional per-head phase. Shape: ``(batch, seq, n_heads)``.
                When omitted, phase is derived from `x` via a learned
                projection (not independently differentiable as a separate
                input in that case).
            mask: Optional attention mask, shape ``(seq, seq)``. Positions
                where ``mask == 0`` are excluded (``-inf`` before softmax).

        Returns:
            Attention output. Shape: ``(batch, seq, d_model)``.

        Raises:
            ValueError: If `x`/`phase`/`mask` is not CPU/contiguous or has an
                unexpected shape.
        """
        self._bridge.set_alpha(self.alpha.detach().double().reshape(-1).tolist())
        result: torch.Tensor = apply_rust_bridge(self._bridge.forward, [x, phase, mask])
        alpha_sum = self.alpha.sum()
        result = result + (alpha_sum - alpha_sum.detach()).to(result.dtype)
        return result

    def rust_state_dict(self) -> bytes:
        """Serialize Rust-owned parameters to opaque checkpoint bytes."""
        return self._bridge.state_dict()

    def load_rust_state_dict(self, state: bytes) -> None:
        """Restore parameters previously produced by :meth:`rust_state_dict`.

        Raises:
            ValueError: If `state` does not decode to a record with this
                layer's `d_model`/`n_heads`.
        """
        self._bridge.load_state_dict(state)
