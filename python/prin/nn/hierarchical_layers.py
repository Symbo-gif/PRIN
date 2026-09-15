"""Rust-backed continuous hierarchical, PAC, and discrete oscillator layers.

All oscillator dynamics, projections, PAC modulation, integration, and
backpropagation live in ``prin-train``. This module only normalizes vector
inputs and delegates complete batched calls through the audited DLPack bridge.
"""

from __future__ import annotations

from typing import Any

import torch
from torch.utils.dlpack import from_dlpack

from prin._prin_core import (
    DiscreteDeltaThetaGammaBridge,
    DiscreteDeltaThetaGammaLayerBridge,
    HierarchicalResonanceLayerBridge,
    PhaseAmplitudeCouplingLayerBridge,
)

from ._bridge import apply_rust_bridge

__all__ = [
    "DiscreteDeltaThetaGamma",
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
        # PRINet 3.0 compatibility: ``nn.layers.HierarchicalResonanceLayer``
        # registers ``pac_depth_dt`` / ``pac_depth_tg`` as learnable
        # ``nn.Parameter``s. The Rust bridge owns the numerically active PAC
        # depths; these are value-preserving mirrors carrying the reference
        # name / init contract. :meth:`forward` adds an exactly-zero term
        # (``p - p.detach()``) so ``loss.backward()`` populates their ``.grad``
        # without perturbing the forward value (E4 mirror pattern).
        self.pac_depth_dt = torch.nn.Parameter(torch.tensor(pac_depth))
        self.pac_depth_tg = torch.nn.Parameter(torch.tensor(pac_depth))

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
        # Exactly-zero-valued term so ``loss.backward()`` populates the
        # PRINet-3.0-compatible PAC-depth mirrors' ``.grad`` (see ``__init__``).
        zero_term = (self.pac_depth_dt - self.pac_depth_dt.detach()) + (
            self.pac_depth_tg - self.pac_depth_tg.detach()
        )
        amplitude = amplitude + zero_term.to(amplitude.dtype)
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


class DiscreteDeltaThetaGamma(torch.nn.Module):
    """Discrete-time multi-rate hierarchical oscillator network.

    Faithful compatibility rebuild of PRINet 3.0
    ``core.propagation.networks.DiscreteDeltaThetaGamma``: learned per-band
    intra-band coupling, multiplicative delta→theta and theta→gamma PAC gates,
    and a soft-clamped Stuart-Landau amplitude update, all in a fixed number of
    discrete macro steps.

    The trainable parameters (``delta_freq`` / ``theta_freq`` / ``gamma_freq``,
    ``W_delta`` / ``W_theta`` / ``W_gamma``, the ``W_pac_dt`` / ``W_pac_tg``
    ``nn.Linear`` gates, and per-band ``mu_*``) are declared here exactly as in
    the reference and are the canonical values. Every :meth:`step` /
    :meth:`integrate` call pushes them into the Rust owner
    (``prin_train::bands::DiscreteDeltaThetaGamma``, WP-022) via
    ``DiscreteDeltaThetaGammaBridge`` and runs the Rust forward — no Python
    oscillator numerics. The Rust step/integrate path is non-differentiable;
    :meth:`step` / :meth:`integrate` add a value-preserving zero term over the
    parameters so ``loss.backward()`` still populates their ``.grad`` (the
    WP-036B E4 layer-mirror pattern), and a straight-through identity term over
    the ``phase`` / ``amplitude`` inputs so gradients still reach an upstream
    encoder (WP-036C S3, WP036C-F2: the reference module was a pure PyTorch
    graph with a real input Jacobian; the STE is the value-preserving surrogate
    over the Rust forward). ``order_parameters`` / ``pac_index`` are
    Rust-computed diagnostics.

    Args:
        n_delta: Number of delta-band oscillators.
        n_theta: Number of theta-band oscillators.
        n_gamma: Number of gamma-band oscillators.
        coupling_strength: Initial intra-band coupling magnitude.
        pac_depth: Initial PAC gate bias.
        delta_freq: Delta-band center frequency (Hz).
        theta_freq: Theta-band center frequency (Hz).
        gamma_freq: Gamma-band center frequency (Hz).
    """

    def __init__(
        self,
        n_delta: int = 8,
        n_theta: int = 16,
        n_gamma: int = 64,
        coupling_strength: float = 2.0,
        pac_depth: float = 0.3,
        delta_freq: float = 2.0,
        theta_freq: float = 6.0,
        gamma_freq: float = 40.0,
    ) -> None:
        """Declare the reference parameters and the Rust bridge."""
        super().__init__()
        self._n_delta = n_delta
        self._n_theta = n_theta
        self._n_gamma = n_gamma
        self._n_total = n_delta + n_theta + n_gamma

        self.delta_freq = torch.nn.Parameter(torch.full((n_delta,), delta_freq))
        self.theta_freq = torch.nn.Parameter(torch.full((n_theta,), theta_freq))
        self.gamma_freq = torch.nn.Parameter(torch.full((n_gamma,), gamma_freq))

        self.W_delta = torch.nn.Parameter(
            torch.randn(n_delta, n_delta) * coupling_strength / n_delta
        )
        self.W_theta = torch.nn.Parameter(
            torch.randn(n_theta, n_theta) * coupling_strength / n_theta
        )
        self.W_gamma = torch.nn.Parameter(
            torch.randn(n_gamma, n_gamma) * coupling_strength / n_gamma
        )

        self.W_pac_dt = torch.nn.Linear(2 * n_delta, n_theta)
        torch.nn.init.xavier_uniform_(self.W_pac_dt.weight, gain=0.5)
        torch.nn.init.constant_(self.W_pac_dt.bias, pac_depth)

        self.W_pac_tg = torch.nn.Linear(2 * n_theta, n_gamma)
        torch.nn.init.xavier_uniform_(self.W_pac_tg.weight, gain=0.5)
        torch.nn.init.constant_(self.W_pac_tg.bias, pac_depth)

        self.mu_delta = torch.nn.Parameter(torch.tensor(1.0))
        self.mu_theta = torch.nn.Parameter(torch.tensor(1.0))
        self.mu_gamma = torch.nn.Parameter(torch.tensor(1.0))

        self._bridge = DiscreteDeltaThetaGammaBridge(
            n_delta,
            n_theta,
            n_gamma,
            coupling_strength,
            pac_depth,
            delta_freq,
            theta_freq,
            gamma_freq,
        )

    @property
    def n_delta(self) -> int:
        """Number of delta-band oscillators."""
        return self._n_delta

    @property
    def n_theta(self) -> int:
        """Number of theta-band oscillators."""
        return self._n_theta

    @property
    def n_gamma(self) -> int:
        """Number of gamma-band oscillators."""
        return self._n_gamma

    @property
    def n_total(self) -> int:
        """Total oscillator count across all three bands."""
        return self._n_total

    def _push_params(self) -> None:
        """Marshal the current parameter values into the Rust owner."""
        self._bridge.load_torch_weights(
            [
                _marshal(self.delta_freq),
                _marshal(self.theta_freq),
                _marshal(self.gamma_freq),
                _marshal(self.W_delta),
                _marshal(self.W_theta),
                _marshal(self.W_gamma),
                _marshal(self.W_pac_dt.weight),
                _marshal(self.W_pac_dt.bias),
                _marshal(self.W_pac_tg.weight),
                _marshal(self.W_pac_tg.bias),
                _marshal(self.mu_delta).reshape(1, 1),
                _marshal(self.mu_theta).reshape(1, 1),
                _marshal(self.mu_gamma).reshape(1, 1),
            ]
        )

    def _zero_term(self, reference: torch.Tensor) -> torch.Tensor:
        """Exactly-zero scalar carrying a gradient path to every parameter."""
        acc = reference.new_zeros(())
        for param in self.parameters():
            total = param.sum()
            acc = acc + (total - total.detach())
        return acc

    @staticmethod
    def _ste(output: torch.Tensor, source: torch.Tensor) -> torch.Tensor:
        """Straight-through identity: return ``output`` value with ``d/dsource = I``.

        The Rust forward detaches its inputs, so a bare ``output`` carries no
        gradient path back to ``source`` (an upstream encoder). Adding the
        exactly-zero ``source - source.detach()`` restores an identity Jacobian
        without changing the value (WP036C-F2). Shapes must match; if the Rust
        forward changed the shape the term is skipped.
        """
        if output.shape != source.shape:
            return output
        return output + (source.to(output.dtype) - source.to(output.dtype).detach())

    def step(
        self, phase: torch.Tensor, amplitude: torch.Tensor, dt: float = 0.01
    ) -> tuple[torch.Tensor, torch.Tensor]:
        """Advance one discrete macro step.

        Args:
            phase: Phases, shape ``(n_total,)`` or ``(batch, n_total)``.
            amplitude: Amplitudes with the same shape.
            dt: Macro timestep.

        Returns:
            ``(new_phase, new_amplitude)`` preserving the input rank.
        """
        phase_b, was_vector = _as_batched(phase)
        amplitude_b, _ = _as_batched(amplitude)
        self._push_params()
        cap_p, cap_a = self._bridge.step(_marshal(phase_b), _marshal(amplitude_b), dt)
        new_p = from_dlpack(cap_p).to(dtype=phase.dtype, device=phase.device)
        new_a = from_dlpack(cap_a).to(dtype=amplitude.dtype, device=amplitude.device)
        zero = self._zero_term(new_a)
        new_p = self._ste(new_p + zero, phase_b)
        new_a = self._ste(new_a + zero, amplitude_b)
        if was_vector:
            new_p = new_p.squeeze(0)
            new_a = new_a.squeeze(0)
        return new_p, new_a

    def integrate(
        self,
        phase: torch.Tensor,
        amplitude: torch.Tensor,
        n_steps: int = 10,
        dt: float = 0.01,
    ) -> tuple[torch.Tensor, torch.Tensor]:
        """Advance ``n_steps`` discrete macro steps; see :meth:`step`."""
        phase_b, was_vector = _as_batched(phase)
        amplitude_b, _ = _as_batched(amplitude)
        self._push_params()
        cap_p, cap_a = self._bridge.integrate(
            _marshal(phase_b), _marshal(amplitude_b), n_steps, dt
        )
        new_p = from_dlpack(cap_p).to(dtype=phase.dtype, device=phase.device)
        new_a = from_dlpack(cap_a).to(dtype=amplitude.dtype, device=amplitude.device)
        zero = self._zero_term(new_a)
        new_p = self._ste(new_p + zero, phase_b)
        new_a = self._ste(new_a + zero, amplitude_b)
        if was_vector:
            new_p = new_p.squeeze(0)
            new_a = new_a.squeeze(0)
        return new_p, new_a

    def order_parameters(
        self, phase: torch.Tensor
    ) -> tuple[torch.Tensor, torch.Tensor, torch.Tensor]:
        """Per-band Kuramoto order parameters ``(r_delta, r_theta, r_gamma)``."""
        phase_b, _ = _as_batched(phase)
        r_d, r_t, r_g = self._bridge.order_parameters(_marshal(phase_b))
        return (
            torch.tensor(r_d, dtype=phase.dtype),
            torch.tensor(r_t, dtype=phase.dtype),
            torch.tensor(r_g, dtype=phase.dtype),
        )

    def pac_index(
        self, phase: torch.Tensor, amplitude: torch.Tensor
    ) -> tuple[torch.Tensor, torch.Tensor]:
        """PAC modulation indices ``(pac_dt, pac_tg)`` for both couplings."""
        phase_b, _ = _as_batched(phase)
        amplitude_b, _ = _as_batched(amplitude)
        pac_dt, pac_tg = self._bridge.pac_index(
            _marshal(phase_b), _marshal(amplitude_b)
        )
        return (
            torch.tensor(pac_dt, dtype=phase.dtype),
            torch.tensor(pac_tg, dtype=phase.dtype),
        )


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

    PyTorch parameters are the canonical optimizer-visible values. Every
    forward synchronizes all 15 tensors into one Rust/Burn integration call,
    whose backward returns real Burn-computed input and parameter VJPs.

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
        self._n_delta = n_delta
        self._n_theta = n_theta
        self._n_gamma = n_gamma
        self._n_dims = n_dims
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
        values = [from_dlpack(capsule) for capsule in self._bridge.parameter_values()]
        self.proj_phase = torch.nn.Linear(
            n_dims, n_delta + n_theta + n_gamma, bias=False, dtype=torch.float64
        )
        self.proj_phase.weight = torch.nn.Parameter(values[0])
        self.proj_amplitude = torch.nn.Linear(
            n_dims, n_delta + n_theta + n_gamma, bias=False, dtype=torch.float64
        )
        self.proj_amplitude.weight = torch.nn.Parameter(values[1])
        self.delta_freq = torch.nn.Parameter(values[2])
        self.theta_freq = torch.nn.Parameter(values[3])
        self.gamma_freq = torch.nn.Parameter(values[4])
        self.W_delta = torch.nn.Parameter(values[5])
        self.W_theta = torch.nn.Parameter(values[6])
        self.W_gamma = torch.nn.Parameter(values[7])
        self.W_pac_dt = torch.nn.Linear(2 * n_delta, n_theta, dtype=torch.float64)
        self.W_pac_dt.weight = torch.nn.Parameter(values[8])
        self.W_pac_dt.bias = torch.nn.Parameter(values[9])
        self.W_pac_tg = torch.nn.Linear(2 * n_theta, n_gamma, dtype=torch.float64)
        self.W_pac_tg.weight = torch.nn.Parameter(values[10])
        self.W_pac_tg.bias = torch.nn.Parameter(values[11])
        self.mu_delta = torch.nn.Parameter(values[12].reshape(()))
        self.mu_theta = torch.nn.Parameter(values[13].reshape(()))
        self.mu_gamma = torch.nn.Parameter(values[14].reshape(()))

    @property
    def n_total(self) -> int:
        """Total oscillator output width."""
        return self._bridge.n_total

    @property
    def n_dims(self) -> int:
        """Input feature width."""
        return self._bridge.n_dims

    def _parameter_tensors(self) -> list[torch.Tensor]:
        """Return canonical parameters in the Rust bridge's declared order."""
        return [
            self.proj_phase.weight,
            self.proj_amplitude.weight,
            self.delta_freq,
            self.theta_freq,
            self.gamma_freq,
            self.W_delta,
            self.W_theta,
            self.W_gamma,
            self.W_pac_dt.weight,
            self.W_pac_dt.bias,
            self.W_pac_tg.weight,
            self.W_pac_tg.bias,
            self.mu_delta.reshape(1, 1),
            self.mu_theta.reshape(1, 1),
            self.mu_gamma.reshape(1, 1),
        ]

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        """Project and integrate an input vector or batch.

        Args:
            x: Input features, shape ``(n_dims,)`` or ``(batch, n_dims)``.

        Returns:
            Final oscillator amplitudes with matching leading rank.
        """
        x_batched, was_vector = _as_batched(x)
        parameters = self._parameter_tensors()
        output: torch.Tensor = apply_rust_bridge(
            lambda value, *weights: self._bridge.forward(value, list(weights)),
            [x_batched, *parameters],
            parameter_start=1,
        )
        return output.squeeze(0) if was_vector else output

    def load_reference_weights(self, reference: Any) -> None:
        """Inject every parameter from a PRINet 3.0 discrete layer for parity."""
        dynamics = reference.dynamics
        weights: list[torch.Tensor] = [
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
        with torch.no_grad():
            for parameter, weight in zip(
                self._parameter_tensors(), weights, strict=True
            ):
                parameter.copy_(
                    weight.to(dtype=parameter.dtype, device=parameter.device)
                )

    def rust_state_dict(self) -> bytes:
        """Serialize canonical parameters as a Rust Burn checkpoint."""
        weights = [
            parameter.detach().to(dtype=torch.float64, device="cpu").contiguous()
            for parameter in self._parameter_tensors()
        ]
        self._bridge.load_torch_weights(weights)
        return self._bridge.state_dict()

    def load_rust_state_dict(self, state: bytes) -> None:
        """Restore a compatible Rust discrete-layer checkpoint.

        Raises:
            ValueError: If the bytes are malformed or dimensions disagree.
        """
        self._bridge.load_state_dict(state)
        values = [from_dlpack(capsule) for capsule in self._bridge.parameter_values()]
        with torch.no_grad():
            for parameter, value in zip(self._parameter_tensors(), values, strict=True):
                parameter.copy_(
                    value.to(dtype=parameter.dtype, device=parameter.device)
                )
