"""Trainable layers and models (PyTorch-facing).

``torch.nn.Module`` wrappers around ``torch.autograd.Function`` bridges whose
forward and backward call into the Rust core (``prin-train``) via DLPack
zero-copy tensor exchange (WP-025, WP-026, Exec-WP-026 S1). Every
differentiable bridge follows the same contract:

- Forward and backward each cross the Rust/Python boundary exactly once per
  call (Coding Standards §3.2: "boundary crossings are batched — one call per
  integration, not per step"); an entire multi-step Rust integration (e.g.
  :class:`ResonanceLayer`'s Kuramoto steps) runs inside a single ``forward``
  call.
- ``ResonanceLayer`` and ``DiscreteDeltaThetaGammaLayer`` use canonical
  PyTorch ``nn.Parameter`` values. Each batched forward synchronizes them into
  a Burn module in the Rust bridge; backward returns Burn-computed input and
  parameter VJPs, so ordinary ``torch.optim`` steps alter the next Rust
  forward. Rust-native checkpoints remain available through
  ``rust_state_dict``/``load_rust_state_dict``. Other compatibility modules
  document their own ownership model; value-preserving parameter mirrors are
  not Burn VJPs.
- Regular differentiable inputs must share dtype/device and CPU placement;
  the bridge marshals them as contiguous ``float64`` tensors for Rust and
  restores the caller-visible dtype/device on output. Float64 remains the
  required dtype for ``torch.autograd.gradcheck`` (Testing Standards §2).

Some WP-026 entry points are **non-differentiable** evaluation utilities
(greedy frame-to-frame matching, oscillator-count allocation) rather than
trainable ops — see :mod:`prin.nn.phase_tracker`'s module docs for the split
rationale and the `forward` → `match_frames` naming adaptation.

Symbols, by submodule: :mod:`prin.nn.attention` (`OscillatoryAttention`),
:mod:`prin.nn.phase_tracker` (`PhaseTracker`, `TrackingResult`),
:mod:`prin.nn.hybrid` (`HybridPRINetV2`), :mod:`prin.nn.slot_attention`
(`SlotAttentionModule`, `TemporalSlotAttentionMOT`), :mod:`prin.nn.ablation`
(`PhaseTrackerFrozen`, `PhaseTrackerStatic`, `SlotAttentionNoGRU`,
`SlotAttentionFrozen`), :mod:`prin.nn.allocation`
(`AdaptiveOscillatorAllocator`, `DynamicPhaseTracker`, `OscillatorBudget`,
`estimate_complexity`), :mod:`prin.nn.mot_evaluation` (`AttentionTracker`,
`Detection`, `TrackingResult`, `evaluate_tracking`, the synthetic MOT
sequence generators, `run_subconscious_ab_test` — WP-036C S1 0144M3;
`prin.nn.TrackingResult` re-exports this module's, matching PRINet 3.0),
:mod:`prin.nn.optimizers` (`SyncGd`, `Scalr`, `Rip`
— WP-027 `torch.optim.Optimizer` wrappers) — all re-exported here.

WP-036 S1 sub-pass 0141B adds the WP-023 trainable primitives as the
PRINet-3.0-compatible surface: :mod:`prin.nn.activations` (`dSiLU`,
`PhaseActivation`, `HolomorphicActivation`), :mod:`prin.nn.inhibition`
(`FeedbackInhibition`), and :mod:`prin.nn.energy` (`HolomorphicEnergy`,
`HolomorphicEPTrainer`) — all re-exported here.

WP-036A sub-pass 0144A1 replaces the inhibition and sparsification family
(`FeedforwardInhibition`, `DentateGyrusConverter`, `DGLayer`,
`SparsityRegularizationLoss`, and `oscillatory_weight_init`) with real
Rust-backed implementations in :mod:`prin.nn.inhibition_layers`. Sub-pass
0144A2 replaces the phase-to-rate / autoencoder family (`PhaseToRateConverter`,
`PhaseToRateAutoencoder`, `DenseAutoencoder`) with real Rust-backed
implementations in :mod:`prin.nn.autoencoders`. Sub-pass 0144A3 replaces the
hierarchical, PAC, and discrete-layer family (`HierarchicalResonanceLayer`,
`PhaseAmplitudeCouplingLayer`, `DiscreteDeltaThetaGammaLayer`) with real
implementations in :mod:`prin.nn.hierarchical_layers`. Sub-pass 0144A4
replaces `PRINetModel` (Rust-backed) and `compile_model` (pure-Python
``torch.compile`` passthrough) with :mod:`prin.nn.model`; WP-036C S1 sub-pass
0144M1 then replaced the final `DiscreteDeltaThetaGamma` stub with the real
bridge re-exported through :mod:`prin.nn.deferred_layers`.
"""

from __future__ import annotations

import math
from typing import TYPE_CHECKING

import torch
from torch.utils.dlpack import from_dlpack

from prin._prin_core import GatedPhaseActivationBridge, ResonanceLayerBridge

# PRINet 3.0 compatibility: ``prinet.nn`` re-exports the Workstream-C
# training-observation / control-policy surface. In PRIN these live in
# ``prin.training_hooks`` (top-level); re-export them here so the reference
# ``from prinet.nn import TelemetryLogger, apply_lr_adjustment, ...`` form
# resolves under the adapted ``prin.nn`` path.
from prin.training_hooks import (
    TelemetryLogger,
    apply_k_range_narrowing,
    apply_lr_adjustment,
    apply_regime_bias,
)

from ._bridge import apply_rust_bridge
from .ablation import (
    PhaseTrackerFrozen,
    PhaseTrackerStatic,
    SlotAttentionFrozen,
    SlotAttentionNoGRU,
)
from .activations import HolomorphicActivation, PhaseActivation, dSiLU
from .allocation import (
    AdaptiveOscillatorAllocator,
    DynamicPhaseTracker,
    OscillatorBudget,
    estimate_complexity,
)
from .attention import OscillatoryAttention
from .autoencoders import (
    DenseAutoencoder,
    PhaseToRateAutoencoder,
    PhaseToRateConverter,
)
from .deferred_layers import DiscreteDeltaThetaGamma
from .energy import HolomorphicEnergy, HolomorphicEPTrainer
from .hierarchical_layers import (
    DiscreteDeltaThetaGammaLayer,
    HierarchicalResonanceLayer,
    PhaseAmplitudeCouplingLayer,
)
from .hybrid import HybridPRINetV2
from .hybrid_compat import (
    AlternatingOptimizer,
    HybridCLEVRN,
    HybridPRINet,
    HybridPRINetV2CLEVRN,
    InterleavedHybridPRINet,
    TemporalHybridPRINet,
)
from .inhibition import FeedbackInhibition
from .inhibition_layers import (
    DentateGyrusConverter,
    DGLayer,
    FeedforwardInhibition,
    SparsityRegularizationLoss,
    oscillatory_weight_init,
)
from .model import PRINetModel, compile_model
from .mot_evaluation import (
    AttentionTracker,
    Detection,
    TrackingResult,
    evaluate_tracking,
    generate_crowded_mot_sequence,
    generate_linear_mot_sequence,
    generate_temporal_reasoning_sequence,
    run_subconscious_ab_test,
)
from .optimizers import (
    Rip,
    RIPOptimizer,
    Scalr,
    SCALROptimizer,
    SyncGd,
    SynchronizedGradientDescent,
)
from .phase_tracker import PhaseTracker
from .slot_attention import (
    SlotAttentionCLEVRN,
    SlotAttentionModule,
    TemporalSlotAttentionMOT,
)

__all__: list[str] = [
    "AdaptiveOscillatorAllocator",
    "AlternatingOptimizer",
    "AttentionTracker",
    "DGLayer",
    "DenseAutoencoder",
    "DentateGyrusConverter",
    "Detection",
    "DiscreteDeltaThetaGamma",
    "DiscreteDeltaThetaGammaLayer",
    "DynamicPhaseTracker",
    "FeedbackInhibition",
    "FeedforwardInhibition",
    "GatedPhaseActivation",
    "HierarchicalResonanceLayer",
    "HolomorphicActivation",
    "HolomorphicEPTrainer",
    "HolomorphicEnergy",
    "HybridCLEVRN",
    "HybridPRINet",
    "HybridPRINetV2",
    "HybridPRINetV2CLEVRN",
    "InterleavedHybridPRINet",
    "OscillatorBudget",
    "OscillatoryAttention",
    "PRINetModel",
    "PhaseActivation",
    "PhaseAmplitudeCouplingLayer",
    "PhaseToRateAutoencoder",
    "PhaseToRateConverter",
    "PhaseTracker",
    "PhaseTrackerFrozen",
    "PhaseTrackerStatic",
    "RIPOptimizer",
    "ResonanceLayer",
    "Rip",
    "SCALROptimizer",
    "Scalr",
    "SlotAttentionCLEVRN",
    "SlotAttentionFrozen",
    "SlotAttentionModule",
    "SlotAttentionNoGRU",
    "SparsityRegularizationLoss",
    "SyncGd",
    "SynchronizedGradientDescent",
    "TelemetryLogger",
    "TemporalHybridPRINet",
    "TemporalSlotAttentionMOT",
    "TrackingResult",
    "apply_k_range_narrowing",
    "apply_lr_adjustment",
    "apply_regime_bias",
    "compile_model",
    "dSiLU",
    "estimate_complexity",
    "evaluate_tracking",
    "generate_crowded_mot_sequence",
    "generate_linear_mot_sequence",
    "generate_temporal_reasoning_sequence",
    "oscillatory_weight_init",
    "run_subconscious_ab_test",
]

if TYPE_CHECKING:
    from prin._prin_core import GatedPhaseActivationCtx


class ResonanceLayer(torch.nn.Module):
    """Trainable single-layer Kuramoto resonance primitive.

    PRINet 3.0 ``nn.layers.ResonanceLayer``, bridged to Rust forward/backward
    via DLPack. Coupling/decay/input-projection/modulation/base-frequency
    ``nn.Parameter`` objects are the canonical optimizer-visible values. Each
    call synchronizes them into ``prin-train::layers::ResonanceLayer`` for the
    complete Rust forward, and Burn returns their real VJPs during backward.
    Consequently ordinary ``torch.optim`` steps alter subsequent Rust-owned
    forward behavior without moving oscillator numerics into Python.

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
        """Construct the layer and canonical parameters from the Rust seed."""
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
        self._coupling_scale = 1.0 / math.sqrt(n_oscillators)
        values = [from_dlpack(capsule) for capsule in self._bridge.parameter_values()]
        self.coupling = torch.nn.Parameter(values[0])
        self.decay = torch.nn.Parameter(values[1])
        self.input_proj = torch.nn.Linear(n_dims, n_oscillators, bias=False).to(
            torch.float64
        )
        self.input_proj.weight = torch.nn.Parameter(values[2])
        self.modulation = torch.nn.Parameter(values[3])
        self.base_frequency = torch.nn.Parameter(values[4])

    @property
    def n_oscillators(self) -> int:
        """Number of coupled oscillators (the output feature width)."""
        return self._bridge.n_oscillators

    @property
    def n_dims(self) -> int:
        """Input feature dimension."""
        return self._bridge.n_dims

    def _parameter_tensors(self) -> list[torch.Tensor]:
        """Return canonical parameters in the Rust bridge's declared order."""
        return [
            self.coupling,
            self.decay,
            self.input_proj.weight,
            self.modulation,
            self.base_frequency,
        ]

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        """Run the Kuramoto integration and return final amplitudes.

        Args:
            x: Input features. Shape: ``(batch, n_dims)``, dtype
                ``torch.float64`` or ``torch.float32``, CPU, contiguous.

        Returns:
            Final oscillator amplitudes. Shape: ``(batch, n_oscillators)``.

        Raises:
            ValueError: If ``x`` is not CPU/contiguous or its shape is not
                ``(batch, n_dims)`` / ``(n_dims,)``.
        """
        was_vector = x.dim() == 1
        batched = x.unsqueeze(0) if was_vector else x
        parameters = self._parameter_tensors()
        result: torch.Tensor = apply_rust_bridge(
            lambda value, *weights: self._bridge.forward(value, list(weights)),
            [batched, *parameters],
            parameter_start=1,
        )
        return result.squeeze(0) if was_vector else result

    def get_order_parameter(self, x: torch.Tensor) -> torch.Tensor:
        """Return the per-input Kuramoto order parameter (PRINet 3.0 hook).

        Args:
            x: Input tensor of shape ``(batch, n_dims)`` or ``(n_dims,)``.

        Returns:
            Order parameter(s) in ``[0, 1]``; shape ``(batch,)`` or scalar.
        """
        was_vector = x.dim() == 1
        batched = x.unsqueeze(0) if was_vector else x
        marshalled = batched.detach().to(dtype=torch.float64, device="cpu").contiguous()
        weights = [
            parameter.detach().to(dtype=torch.float64, device="cpu").contiguous()
            for parameter in self._parameter_tensors()
        ]
        result: torch.Tensor = from_dlpack(
            self._bridge.order_parameter(marshalled, weights)
        )
        return result.squeeze(0) if was_vector else result

    def rust_state_dict(self) -> bytes:
        """Serialize the canonical parameters as a Rust Burn checkpoint."""
        weights = [
            parameter.detach().to(dtype=torch.float64, device="cpu").contiguous()
            for parameter in self._parameter_tensors()
        ]
        self._bridge.load_torch_weights(weights)
        return self._bridge.state_dict()

    def load_rust_state_dict(self, state: bytes) -> None:
        """Restore a Burn checkpoint into the canonical PyTorch parameters.

        Args:
            state: Bytes from a prior :meth:`rust_state_dict` call on a
                layer with the same ``n_oscillators``/``n_dims``.

        Raises:
            ValueError: If ``state`` does not decode to a record with this
                layer's parameter shapes.
        """
        self._bridge.load_state_dict(state)
        values = [from_dlpack(capsule) for capsule in self._bridge.parameter_values()]
        with torch.no_grad():
            for parameter, value in zip(self._parameter_tensors(), values, strict=True):
                parameter.copy_(
                    value.to(dtype=parameter.dtype, device=parameter.device)
                )


class _GatedPhaseActivationFunction(torch.autograd.Function):
    """``torch.autograd.Function`` gluing :class:`GatedPhaseActivation`.

    Forward and backward each cross the Rust boundary once.
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
    (matching PRINet 3.0). Unlike :class:`ResonanceLayer`, this module does not
    expose canonical ``torch.nn.Parameter`` weights; its Rust-owned gate is
    trained by a ``prin-train`` ``OscillatorOptimizer`` rather than
    ``torch.optim``.

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
                ``torch.float64`` or ``torch.float32``, CPU, contiguous.

        Returns:
            Activated output. Shape: ``(batch, n_dims)``, values in
            ``[0, 2*pi)`` scaled by the sigmoid gate.

        Raises:
            ValueError: If ``z`` is not CPU/contiguous or its shape is not
                ``(batch, n_dims)``.
        """
        result: torch.Tensor = apply_rust_bridge(self._bridge.forward, [z])
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
