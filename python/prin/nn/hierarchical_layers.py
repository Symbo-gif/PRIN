"""Rust-backed continuous hierarchical, PAC, and discrete oscillator layers.

All oscillator dynamics, projections, PAC modulation, integration, and
backpropagation live in ``prin-train``. This module only normalizes vector
inputs and delegates complete batched calls through the audited DLPack bridge.
"""

from __future__ import annotations

from typing import Any

import torch

from prin._prin_core import (
    DiscreteDeltaThetaGammaLayerBridge,
    HierarchicalResonanceLayerBridge,
    PhaseAmplitudeCouplingLayerBridge,
)

from ._bridge import apply_rust_bridge

__all__ = [
    "DiscreteDeltaThetaGammaLayer",
    "HierarchicalResonanceLayer",
    "PhaseAmplitudeCouplingLayer",
]


def _as_batched(tensor: torch.Tensor) -> tuple[torch.Tensor, bool]:
    """Normalize a vector to one batch row and reject all other ranks."""
    if tensor.dim() == 1:
        return tensor.unsqueeze(0), True
    if tensor.dim() == 2:
        return tensor, False
    raise ValueError(f"expected a 1-D or 2-D tensor, got shape {tuple(tensor.shape)}")


def _marshal(tensor: torch.Tensor) -> torch.Tensor:
    """Detach one reference parameter as contiguous float64 CPU storage."""
    return tensor.detach().to(dtype=torch.float64, device="cpu").contiguous()


class HierarchicalResonanceLayer(torch.nn.Module):
    """Fully batched continuous delta/theta/gamma resonance layer.

    The Rust owner reproduces the reference sparse phase-kNN Kuramoto RK4
    stepping order, amplitude dynamics, delta-to-theta and theta-to-gamma PAC,
    and fixed 2/6/40 frequency hierarchy without the reference's per-sample
    Python loop.

    Args:
        n_delta: Number of delta-band oscillators.
        n_theta: Number of theta-band oscillators.
        n_gamma: Number of gamma-band oscillators.
        n_dims: Input feature width.
        n_steps: Number of outer integration steps.
        dt: Outer timestep.
        coupling_strength: Intra-band sparse Kuramoto coupling strength.
        pac_depth: Initial depth for both PAC links.
        sparse_k: Common sparse neighbour count. ``None`` selects
            ``ceil(log2(n_band))`` separately for each band.
        seed_counter: Counter half of the deterministic initialization seed.
        seed_key: Key half of the deterministic initialization seed.
    """

    def __init__(
        self,
        n_delta: int = 8,
        n_theta: int = 16,
        n_gamma: int = 64,
        n_dims: int = 256,
        n_steps: int = 10,
        dt: float = 0.01,
        coupling_strength: float = 2.0,
        pac_depth: float = 0.3,
        sparse_k: int | None = None,
        seed_counter: int = 0,
        seed_key: int = 0,
    ) -> None:
        """Construct the Rust-owned hierarchical layer."""
        super().__init__()
        self._n_steps = n_steps
        self._bridge = HierarchicalResonanceLayerBridge(
            n_delta,
            n_theta,
            n_gamma,
            n_dims,
            n_steps,
            dt,
            coupling_strength,
            pac_depth,
            sparse_k,
            seed_counter,
            seed_key,
        )

    @property
    def n_steps(self) -> int:
        """Number of configured outer integration steps."""
        return self._n_steps

    @property
    def n_delta(self) -> int:
        """Number of delta-band oscillators."""
        return self._bridge.n_delta

    @property
    def n_theta(self) -> int:
        """Number of theta-band oscillators."""
        return self._bridge.n_theta

    @property
    def n_gamma(self) -> int:
        """Number of gamma-band oscillators."""
        return self._bridge.n_gamma

    @property
    def n_total(self) -> int:
        """Total oscillator output width."""
        return self._bridge.n_total

    @property
    def n_dims(self) -> int:
        """Input feature width."""
        return self._bridge.n_dims

    def forward(
        self, x: torch.Tensor, return_phase: bool = False
    ) -> torch.Tensor | tuple[torch.Tensor, torch.Tensor]:
        """Run the continuous hierarchy and return amplitudes and optionally phase.

        Args:
            x: Input features, shape ``(n_dims,)`` or ``(batch, n_dims)``.
            return_phase: Return ``(amplitude, wrapped_phase)`` when true.

        Returns:
            Final amplitudes, or amplitudes plus phases, preserving vector rank.

        Raises:
            ValueError: If the input rank or width is invalid.
        """
        x_batched, was_vector = _as_batched(x)
        result: tuple[torch.Tensor, torch.Tensor] = apply_rust_bridge(
            self._bridge.forward, [x_batched]
        )
        amplitude, phase = result
        if was_vector:
            amplitude = amplitude.squeeze(0)
            phase = phase.squeeze(0)
        if return_phase:
            return amplitude, phase
        return amplitude

    def load_reference_weights(self, reference: Any) -> None:
        """Inject a PRINet 3.0 layer's projections and PAC depths for parity."""
        self._bridge.load_torch_weights(
            _marshal(reference.proj_delta.weight),
            _marshal(reference.proj_theta.weight),
            _marshal(reference.proj_gamma.weight),
            _marshal(reference.pac_depth_dt).reshape(1),
            _marshal(reference.pac_depth_tg).reshape(1),
        )

    def rust_state_dict(self) -> bytes:
        """Serialize all Rust-owned projections and PAC depths."""
        return self._bridge.state_dict()

    def load_rust_state_dict(self, state: bytes) -> None:
        """Restore a compatible Rust checkpoint.

        Raises:
            ValueError: If the bytes are malformed or dimensions disagree.
        """
        self._bridge.load_state_dict(state)


class PhaseAmplitudeCouplingLayer(torch.nn.Module):
    """Learnable mean-slow-phase PAC layer backed entirely by Rust.

    Args:
        initial_depth: Initial modulation depth in ``[0, 1]``.
    """

    def __init__(self, initial_depth: float = 0.3) -> None:
        """Construct the Rust-owned PAC parameter."""
        super().__init__()
        self.modulation_depth = torch.nn.Parameter(torch.tensor(initial_depth))
        self._bridge = PhaseAmplitudeCouplingLayerBridge(initial_depth)

    def forward(
        self, slow_phase: torch.Tensor, fast_amplitude: torch.Tensor
    ) -> torch.Tensor:
        """Modulate fast amplitudes from each row's mean slow phase.

        Args:
            slow_phase: Slow phases, shape ``(n_slow,)`` or ``(batch, n_slow)``.
            fast_amplitude: Fast amplitudes with the same batch dimension.

        Returns:
            Modulated amplitudes preserving vector rank.

        Raises:
            ValueError: If ranks or batch dimensions are incompatible.
        """
        depth = float(self.modulation_depth.detach().clamp(0.0, 1.0).item())
        self._bridge = PhaseAmplitudeCouplingLayerBridge(depth)
        phase_batched, phase_vector = _as_batched(slow_phase)
        amplitude_batched, amplitude_vector = _as_batched(fast_amplitude)
        if phase_vector != amplitude_vector:
            raise ValueError("slow_phase and fast_amplitude must have matching ranks")
        output: torch.Tensor = apply_rust_bridge(
            self._bridge.forward, [phase_batched, amplitude_batched]
        )
        return output.squeeze(0) if phase_vector else output

    def rust_state_dict(self) -> bytes:
        """Serialize the Rust-owned modulation depth."""
        return self._bridge.state_dict()

    def load_rust_state_dict(self, state: bytes) -> None:
        """Restore a compatible Rust PAC checkpoint.

        Raises:
            ValueError: If the bytes are malformed.
        """
        self._bridge.load_state_dict(state)


class DiscreteDeltaThetaGammaLayer(torch.nn.Module):
    """Bias-free input projections over the existing discrete three-band core.

    Args:
        n_delta: Number of delta-band oscillators.
        n_theta: Number of theta-band oscillators.
        n_gamma: Number of gamma-band oscillators.
        n_dims: Input feature width.
        n_steps: Number of discrete macro steps.
        dt: Timestep per macro step.
        coupling_strength: Initial intra-band coupling scale.
        pac_depth: Initial PAC gate bias.
        seed_counter: Counter half of the deterministic initialization seed.
        seed_key: Key half of the deterministic initialization seed.
    """

    def __init__(
        self,
        n_delta: int = 8,
        n_theta: int = 16,
        n_gamma: int = 64,
        n_dims: int = 256,
        n_steps: int = 10,
        dt: float = 0.01,
        coupling_strength: float = 2.0,
        pac_depth: float = 0.3,
        seed_counter: int = 0,
        seed_key: int = 0,
    ) -> None:
        """Construct projections and nested discrete dynamics in Rust."""
        super().__init__()
        self._bridge = DiscreteDeltaThetaGammaLayerBridge(
            n_delta,
            n_theta,
            n_gamma,
            n_dims,
            n_steps,
            dt,
            coupling_strength,
            pac_depth,
            seed_counter,
            seed_key,
        )

    @property
    def n_total(self) -> int:
        """Total oscillator output width."""
        return self._bridge.n_total

    @property
    def n_dims(self) -> int:
        """Input feature width."""
        return self._bridge.n_dims

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        """Project and integrate an input vector or batch.

        Args:
            x: Input features, shape ``(n_dims,)`` or ``(batch, n_dims)``.

        Returns:
            Final oscillator amplitudes with matching leading rank.
        """
        x_batched, was_vector = _as_batched(x)
        output: torch.Tensor = apply_rust_bridge(self._bridge.forward, [x_batched])
        return output.squeeze(0) if was_vector else output

    def load_reference_weights(self, reference: Any) -> None:
        """Inject every parameter from a PRINet 3.0 discrete layer for parity."""
        dynamics = reference.dynamics
        weights: list[object] = [
            _marshal(reference.proj_phase.weight),
            _marshal(reference.proj_amplitude.weight),
            _marshal(dynamics.delta_freq),
            _marshal(dynamics.theta_freq),
            _marshal(dynamics.gamma_freq),
            _marshal(dynamics.W_delta),
            _marshal(dynamics.W_theta),
            _marshal(dynamics.W_gamma),
            _marshal(dynamics.W_pac_dt.weight),
            _marshal(dynamics.W_pac_dt.bias),
            _marshal(dynamics.W_pac_tg.weight),
            _marshal(dynamics.W_pac_tg.bias),
            _marshal(dynamics.mu_delta).reshape(1, 1),
            _marshal(dynamics.mu_theta).reshape(1, 1),
            _marshal(dynamics.mu_gamma).reshape(1, 1),
        ]
        self._bridge.load_torch_weights(weights)

    def rust_state_dict(self) -> bytes:
        """Serialize projections and nested discrete dynamics."""
        return self._bridge.state_dict()

    def load_rust_state_dict(self, state: bytes) -> None:
        """Restore a compatible Rust discrete-layer checkpoint.

        Raises:
            ValueError: If the bytes are malformed or dimensions disagree.
        """
        self._bridge.load_state_dict(state)
