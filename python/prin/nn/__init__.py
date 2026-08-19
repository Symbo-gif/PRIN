"""Trainable layers and models (PyTorch-facing).

``torch.nn.Module`` wrappers around ``torch.autograd.Function`` bridges whose
forward and backward call into the Rust core (``prin-train``) via DLPack
zero-copy tensor exchange (WP-025). Every bridge follows the same contract:

- Forward and backward each cross the Rust/Python boundary exactly once per
  call (Coding Standards §3.2: "boundary crossings are batched — one call per
  integration, not per step"); an entire multi-step Rust integration (e.g.
  :class:`ResonanceLayer`'s Kuramoto steps) runs inside a single ``forward``
  call.
- Trainable parameters (coupling matrices, gate weights, ...) live in Rust,
  not as ``torch.nn.Parameter``. They are trained by the ``prin-train``
  oscillator-aware optimizers (``SyncGd``/``Rip``/``Scalr``), not
  ``torch.optim``; these modules only make the *input*/*output* boundary
  differentiable so a larger PyTorch model can chain gradients through them.
  Checkpointing uses :meth:`ResonanceLayer.rust_state_dict`/
  :meth:`ResonanceLayer.load_rust_state_dict` (Rust-native ``burn::record``
  bytes), not ``torch.nn.Module.state_dict``.
- Every bridge requires ``float64`` CPU, contiguous input, matching
  ``torch.autograd.gradcheck``'s double-precision requirement (Testing
  Standards §2).

Planned symbols (Phase 4, PRINet-3.0 compatible), most not yet bridged:
PRINetModel, HierarchicalResonanceLayer, OscillatoryAttention,
PhaseToRateConverter, HybridPRINet, HybridPRINetV2, PhaseTracker,
SlotAttentionModule, TemporalSlotAttentionMOT, optimizers (SyncGD, SCALR,
RIP, Alternating — Rust implementations exist in ``prin-train``; a thin
``torch.optim.Optimizer`` wrapper is future WP-025+ scope), the remaining
activations (HolomorphicActivation), and the HEP trainer.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

__all__: list[str] = ["GatedPhaseActivation", "ResonanceLayer"]

import torch
from torch.utils.dlpack import from_dlpack

from prin._prin_core import GatedPhaseActivationBridge, ResonanceLayerBridge

if TYPE_CHECKING:
    from prin._prin_core import GatedPhaseActivationCtx, ResonanceLayerCtx


class _ResonanceLayerFunction(torch.autograd.Function):
    """``torch.autograd.Function`` gluing :class:`ResonanceLayer` to Rust.

    ``forward``/``backward`` each make exactly one call into the Rust bridge;
    the entire ``n_steps``-step Kuramoto integration runs inside that single
    Rust call.
    """

    @staticmethod
    def forward(
        ctx: torch.autograd.function.FunctionCtx,
        x: torch.Tensor,
        bridge: ResonanceLayerBridge,
    ) -> torch.Tensor:
        """Decode ``x``, run the Rust forward pass, save the Rust context."""
        out_capsule, rust_ctx = bridge.forward(x.detach())
        output: torch.Tensor = from_dlpack(out_capsule)
        ctx.rust_ctx = rust_ctx  # type: ignore[attr-defined]
        return output

    @staticmethod
    def backward(
        ctx: torch.autograd.function.FunctionCtx, grad_output: torch.Tensor
    ) -> tuple[torch.Tensor, None]:
        """Run the Rust backward pass for the saved context."""
        rust_ctx: ResonanceLayerCtx = ctx.rust_ctx  # type: ignore[attr-defined]
        grad_x_capsule = rust_ctx.backward(grad_output.contiguous())
        grad_x: torch.Tensor = from_dlpack(grad_x_capsule)
        return grad_x, None


class ResonanceLayer(torch.nn.Module):
    """Trainable single-layer Kuramoto resonance primitive.

    PRINet 3.0 ``nn.layers.ResonanceLayer``, bridged to Rust forward/backward
    via DLPack. Coupling/decay/input-projection/modulation/base-frequency
    parameters are owned by the Rust bridge
    (``prin-train::layers::ResonanceLayer``), not exposed as
    ``torch.nn.Parameter``; train them with a ``prin-train``
    ``OscillatorOptimizer`` (``SyncGd``/``Rip``/``Scalr``). ``forward``
    remains fully differentiable end to end through DLPack-bridged Rust
    forward/backward, so this module composes inside a larger PyTorch model
    whose *other* layers use ``torch.optim``.

    Args:
        n_oscillators: Number of coupled oscillators (output feature width).
        n_dims: Input feature dimension.
        n_steps: Number of Kuramoto integration steps per forward call.
        dt: Integration timestep.
        decay_rate: Initial per-oscillator amplitude decay rate.
        freq_adaptation_rate: Frequency-modulation rate.
        seed_counter: Counter half of the deterministic ``Seed`` used to draw
            initial parameters (Coding Standards §1.3).
        seed_key: Key half of the deterministic ``Seed``.

    Examples:
        >>> import torch
        >>> from prin.nn import ResonanceLayer
        >>> layer = ResonanceLayer(4, 3, n_steps=2, seed_counter=1)
        >>> x = torch.randn(2, 3, dtype=torch.float64, requires_grad=True)
        >>> y = layer(x)
        >>> y.shape
        torch.Size([2, 4])
        >>> y.sum().backward()
        >>> x.grad.shape
        torch.Size([2, 3])
    """

    def __init__(
        self,
        n_oscillators: int,
        n_dims: int,
        n_steps: int = 10,
        dt: float = 0.01,
        decay_rate: float = 0.1,
        freq_adaptation_rate: float = 0.01,
        seed_counter: int = 0,
        seed_key: int = 0,
    ) -> None:
        """Construct the layer with seeded-random Rust-owned parameters."""
        super().__init__()
        self._bridge = ResonanceLayerBridge(
            n_oscillators,
            n_dims,
            n_steps,
            dt,
            decay_rate,
            freq_adaptation_rate,
            seed_counter,
            seed_key,
        )

    @property
    def n_oscillators(self) -> int:
        """Number of coupled oscillators (the output feature width)."""
        return self._bridge.n_oscillators

    @property
    def n_dims(self) -> int:
        """Input feature dimension."""
        return self._bridge.n_dims

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        """Run the Kuramoto integration and return final amplitudes.

        Args:
            x: Input features. Shape: ``(batch, n_dims)``, dtype
                ``torch.float64``, CPU, contiguous.

        Returns:
            Final oscillator amplitudes. Shape: ``(batch, n_oscillators)``.

        Raises:
            ValueError: If ``x`` is not ``float64``/CPU/contiguous or its
                shape is not ``(batch, n_dims)``.
        """
        result: torch.Tensor = _ResonanceLayerFunction.apply(x, self._bridge)  # type: ignore[no-untyped-call]
        return result

    def rust_state_dict(self) -> bytes:
        """Serialize Rust-owned parameters to opaque checkpoint bytes.

        Returns:
            Bytes produced by ``burn::record`` (``BinBytesRecorder<
            DoublePrecisionSettings>``); pass to :meth:`load_rust_state_dict`
            to restore. Not interchangeable with
            ``torch.nn.Module.state_dict`` (there is no ``torch.nn.Parameter``
            on this module).
        """
        return self._bridge.state_dict()

    def load_rust_state_dict(self, state: bytes) -> None:
        """Restore parameters previously produced by :meth:`rust_state_dict`.

        Args:
            state: Bytes from a prior :meth:`rust_state_dict` call on a
                layer with the same ``n_oscillators``/``n_dims``.

        Raises:
            ValueError: If ``state`` does not decode to a record with this
                layer's parameter shapes.
        """
        self._bridge.load_state_dict(state)


class _GatedPhaseActivationFunction(torch.autograd.Function):
    """``torch.autograd.Function`` gluing :class:`GatedPhaseActivation`.

    See :class:`_ResonanceLayerFunction` for the general contract.
    """

    @staticmethod
    def forward(
        ctx: torch.autograd.function.FunctionCtx,
        z: torch.Tensor,
        bridge: GatedPhaseActivationBridge,
    ) -> torch.Tensor:
        """Decode ``z``, run the Rust forward pass, save the Rust context."""
        out_capsule, rust_ctx = bridge.forward(z.detach())
        output: torch.Tensor = from_dlpack(out_capsule)
        ctx.rust_ctx = rust_ctx  # type: ignore[attr-defined]
        return output

    @staticmethod
    def backward(
        ctx: torch.autograd.function.FunctionCtx, grad_output: torch.Tensor
    ) -> tuple[torch.Tensor, None]:
        """Run the Rust backward pass for the saved context."""
        rust_ctx: GatedPhaseActivationCtx = ctx.rust_ctx  # type: ignore[attr-defined]
        grad_z_capsule = rust_ctx.backward(grad_output.contiguous())
        grad_z: torch.Tensor = from_dlpack(grad_z_capsule)
        return grad_z, None


class GatedPhaseActivation(torch.nn.Module):
    """Phase activation with a learnable per-feature gate.

    PRINet 3.0 ``GatedPhaseActivation``: ``y = sigmoid(w_g*z + b_g) *
    phase_activation(z)``, bridged to Rust forward/backward via DLPack. Gate
    weight/bias are owned by the Rust bridge
    (``prin-train::activations::GatedPhaseActivation``), zero-initialized
    (matching PRINet 3.0); see :class:`ResonanceLayer`'s docs for the same
    training-ownership split (a ``prin-train`` ``OscillatorOptimizer``, not
    ``torch.optim``).

    Args:
        n_dims: Input/output feature dimension.

    Examples:
        >>> import torch
        >>> from prin.nn import GatedPhaseActivation
        >>> act = GatedPhaseActivation(3)
        >>> z = torch.randn(2, 3, dtype=torch.float64, requires_grad=True)
        >>> y = act(z)
        >>> y.shape
        torch.Size([2, 3])
    """

    def __init__(self, n_dims: int) -> None:
        """Construct with zero-initialized gate weight/bias."""
        super().__init__()
        self._bridge = GatedPhaseActivationBridge(n_dims)

    @property
    def n_dims(self) -> int:
        """Input/output feature dimension."""
        return self._bridge.n_dims

    def forward(self, z: torch.Tensor) -> torch.Tensor:
        """Apply the gated phase activation.

        Args:
            z: Input features. Shape: ``(batch, n_dims)``, dtype
                ``torch.float64``, CPU, contiguous.

        Returns:
            Activated output. Shape: ``(batch, n_dims)``, values in
            ``[0, 2*pi)`` scaled by the sigmoid gate.

        Raises:
            ValueError: If ``z`` is not ``float64``/CPU/contiguous or its
                shape is not ``(batch, n_dims)``.
        """
        result: torch.Tensor = _GatedPhaseActivationFunction.apply(z, self._bridge)  # type: ignore[no-untyped-call]
        return result

    def rust_state_dict(self) -> bytes:
        """Serialize the Rust-owned gate parameters to checkpoint bytes.

        Returns:
            Bytes produced by ``burn::record``; pass to
            :meth:`load_rust_state_dict` to restore.
        """
        return self._bridge.state_dict()

    def load_rust_state_dict(self, state: bytes) -> None:
        """Restore gate parameters previously produced by this class.

        Args:
            state: Bytes from a prior :meth:`rust_state_dict` call on a
                layer with the same ``n_dims``.

        Raises:
            ValueError: If ``state`` does not decode to a record with this
                layer's parameter shape.
        """
        self._bridge.load_state_dict(state)
