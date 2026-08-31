"""Rust-backed feedforward inhibition and sparsification layers.

The numerical implementations live in ``prin-train``. This module provides
PRINet-3.0-compatible Python orchestration and ``torch.autograd.Function`` glue
through the audited DLPack bridge.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

import torch

from prin._prin_core import (
    DentateGyrusConverterBridge,
    DGLayerBridge,
    FeedforwardInhibitionBridge,
    OscillatoryWeightInitBridge,
    SparsityRegularizationLossBridge,
)

from ._bridge import apply_rust_bridge
from .inhibition import FeedbackInhibition

if TYPE_CHECKING:
    from collections.abc import Iterator

__all__ = [
    "DGLayer",
    "DentateGyrusConverter",
    "FeedforwardInhibition",
    "SparsityRegularizationLoss",
    "oscillatory_weight_init",
]


def _batched_pair(
    phase: torch.Tensor, amplitude: torch.Tensor
) -> tuple[torch.Tensor, torch.Tensor, bool]:
    """Validate a phase/amplitude pair and normalize a vector to one batch."""
    if phase.shape != amplitude.shape:
        raise ValueError(
            f"phase and amplitude must have the same shape, got "
            f"{tuple(phase.shape)} and {tuple(amplitude.shape)}"
        )
    if phase.dim() not in (1, 2):
        raise ValueError(
            f"phase and amplitude must be 1-D or 2-D, got {tuple(phase.shape)}"
        )
    was_vector = phase.dim() == 1
    if was_vector:
        return phase.unsqueeze(0), amplitude.unsqueeze(0), True
    return phase, amplitude, False


def _restore_vector(output: torch.Tensor, was_vector: bool) -> torch.Tensor:
    """Restore an unbatched output to the reference's vector shape."""
    return output.squeeze(0) if was_vector else output


class FeedforwardInhibition:
    """Parameter-free phase-delay / exponential-decay inhibition gate.

    Args:
        delay_steps: Compatibility delay in integration steps. The PRINet 3.0
            formula records this value but uses ``delay_fraction`` for its
            numerical phase shift.
        tau: Positive exponential-envelope time constant.
        delay_fraction: Fraction of one cycle used for the phase shift.
    """

    def __init__(
        self,
        delay_steps: int = 1,
        tau: float = 0.05,
        delay_fraction: float = 0.1,
    ) -> None:
        """Construct the Rust-backed gate."""
        self._bridge = FeedforwardInhibitionBridge(delay_steps, tau, delay_fraction)

    @property
    def delay_steps(self) -> int:
        """Compatibility delay in integration steps."""
        return self._bridge.delay_steps

    @property
    def tau(self) -> float:
        """Exponential-envelope time constant."""
        return self._bridge.tau

    def gate(self, phase: torch.Tensor, amplitude: torch.Tensor) -> torch.Tensor:
        """Apply feedforward inhibition.

        Args:
            phase: Phase tensor with shape ``(N,)`` or ``(batch, N)``.
            amplitude: Matching amplitude tensor.

        Returns:
            Non-negative gated rates with the input shape.

        Raises:
            ValueError: If shapes/ranks differ or tensors are not contiguous
                float64 CPU tensors.
        """
        phase, amplitude, was_vector = _batched_pair(phase, amplitude)
        output: torch.Tensor = apply_rust_bridge(
            self._bridge.forward, [phase, amplitude]
        )
        return _restore_vector(output, was_vector)


class DentateGyrusConverter:
    """Dentate-gyrus-inspired FFI → EMA → FBI sparsification pipeline.

    Args:
        n_oscillators: Input oscillator count.
        k: Explicit number of FBI winners, or ``None`` to derive it from
            ``target_sparsity``.
        target_sparsity: Active fraction used when ``k`` is omitted.
        ffi_delay: FFI compatibility delay.
        ffi_tau: FFI decay time constant.
        fbi_delay: FBI compatibility delay.
        fbi_temperature: FBI softmax temperature.
        integration_alpha: EMA retention coefficient in ``[0, 1]``.
    """

    def __init__(
        self,
        n_oscillators: int,
        k: int | None = None,
        target_sparsity: float = 0.1,
        ffi_delay: int = 1,
        ffi_tau: float = 0.05,
        fbi_delay: int = 20,
        fbi_temperature: float = 1.0,
        integration_alpha: float = 0.95,
    ) -> None:
        """Construct the Rust-backed conversion pipeline."""
        self._bridge = DentateGyrusConverterBridge(
            n_oscillators,
            k,
            target_sparsity,
            ffi_delay,
            ffi_tau,
            fbi_delay,
            fbi_temperature,
            integration_alpha,
        )
        self._ffi = FeedforwardInhibition(ffi_delay, ffi_tau)
        self._fbi = FeedbackInhibition(
            k=k,
            sparsity=target_sparsity,
            delay_steps=fbi_delay,
            temperature=fbi_temperature,
        )

    @property
    def ffi(self) -> FeedforwardInhibition:
        """Feedforward inhibition component."""
        return self._ffi

    @property
    def fbi(self) -> FeedbackInhibition:
        """Feedback inhibition component."""
        return self._fbi

    def convert(
        self,
        phase: torch.Tensor,
        amplitude: torch.Tensor,
        n_integration_steps: int = 5,
    ) -> torch.Tensor:
        """Run FFI gating, EMA integration, and FBI competition.

        Args:
            phase: Phase tensor with shape ``(N,)`` or ``(batch, N)``.
            amplitude: Matching amplitude tensor.
            n_integration_steps: Positive number of EMA samples.

        Returns:
            Sparse rates with the input shape.

        Raises:
            ValueError: If input or configuration values violate the Rust
                contract.
        """
        phase, amplitude, was_vector = _batched_pair(phase, amplitude)
        output: torch.Tensor = apply_rust_bridge(
            lambda p, a: self._bridge.forward(p, a, n_integration_steps),
            [phase, amplitude],
        )
        return _restore_vector(output, was_vector)


class DGLayer(torch.nn.Module):
    """Trainable dentate-gyrus layer with Rust-owned scalar parameters.

    ``ffi_scale`` and ``fbi_temperature`` are Burn parameters serialized via
    :meth:`rust_state_dict`; they are intentionally not duplicated as
    ``torch.nn.Parameter`` objects.

    Args:
        n_input: Input oscillator count.
        top_k: Number of FBI winners.
        ffi_delay: FFI compatibility delay.
        fbi_delay: FBI compatibility delay.
        n_integration_steps: Positive number of EMA samples.
    """

    def __init__(
        self,
        n_input: int,
        top_k: int = 8,
        ffi_delay: int = 2,
        fbi_delay: int = 20,
        n_integration_steps: int = 5,
    ) -> None:
        """Construct the Rust-owned trainable layer."""
        super().__init__()
        self._bridge = DGLayerBridge(
            n_input, top_k, ffi_delay, fbi_delay, n_integration_steps
        )

    @property
    def n_input(self) -> int:
        """Input oscillator count."""
        return self._bridge.n_input

    @property
    def top_k(self) -> int:
        """Resolved FBI winner count."""
        return self._bridge.top_k

    def forward(self, phase: torch.Tensor, amplitude: torch.Tensor) -> torch.Tensor:
        """Convert phase/amplitude inputs to sparse rates.

        Args:
            phase: Phase tensor with shape ``(N,)`` or ``(batch, N)``.
            amplitude: Matching amplitude tensor.

        Returns:
            Sparse rates with the input shape.
        """
        phase, amplitude, was_vector = _batched_pair(phase, amplitude)
        output: torch.Tensor = apply_rust_bridge(
            self._bridge.forward, [phase, amplitude]
        )
        return _restore_vector(output, was_vector)

    def rust_state_dict(self) -> bytes:
        """Serialize the Rust-owned scalar parameters."""
        return self._bridge.state_dict()

    def load_rust_state_dict(self, state: bytes) -> None:
        """Restore a compatible Rust parameter record.

        Args:
            state: Bytes returned by :meth:`rust_state_dict`.

        Raises:
            ValueError: If the record is malformed or incompatible.
        """
        self._bridge.load_state_dict(state)


class SparsityRegularizationLoss(torch.nn.Module):
    """Sigmoid-surrogate L0 sparsity regularization loss.

    Args:
        target_sparsity: Target inactive fraction in ``[0, 1]``.
        temperature: Positive sigmoid-surrogate temperature.
    """

    def __init__(self, target_sparsity: float = 0.9, temperature: float = 0.1) -> None:
        """Construct the Rust-backed loss."""
        super().__init__()
        self._bridge = SparsityRegularizationLossBridge(target_sparsity, temperature)

    @property
    def target_sparsity(self) -> float:
        """Target inactive fraction."""
        return self._bridge.target_sparsity

    @property
    def temperature(self) -> float:
        """Sigmoid-surrogate temperature."""
        return self._bridge.temperature

    def forward(self, activations: torch.Tensor) -> torch.Tensor:
        """Compute the scalar density-penalty loss.

        Args:
            activations: One- or two-dimensional rate-coded activations.

        Returns:
            Scalar loss tensor.

        Raises:
            ValueError: If activations have unsupported rank or violate the
                DLPack bridge contract.
        """
        if activations.dim() not in (1, 2):
            raise ValueError(
                f"activations must be 1-D or 2-D, got {tuple(activations.shape)}"
            )
        batched = activations.unsqueeze(0) if activations.dim() == 1 else activations
        output: torch.Tensor = apply_rust_bridge(self._bridge.forward, [batched])
        return output.squeeze(0)


def _named_parameters(
    module: torch.nn.Module,
) -> Iterator[tuple[str, torch.nn.Parameter]]:
    """Return the module's named parameters for role-based Rust dispatch."""
    return module.named_parameters()


def oscillatory_weight_init(
    module: torch.nn.Module,
    coupling_scale: float = 0.1,
    proj_gain: float = 0.5,
    *,
    seed_counter: int = 0,
    seed_key: int = 0,
) -> None:
    """Apply deterministic oscillator-aware initialization in Rust.

    Coupling matrices are symmetrized and zero-diagonal, projection weights use
    Xavier-uniform draws, and biases are zeroed. Parameters must be float64 CPU
    tensors, matching every trainable PRIN DLPack bridge.

    Args:
        module: Module whose named parameters are initialized in place.
        coupling_scale: Multiplicative scale for coupling matrices.
        proj_gain: Xavier gain for projection matrices.
        seed_counter: Counter half of the deterministic Rust seed.
        seed_key: Key half of the deterministic Rust seed.

    Raises:
        ValueError: If a selected parameter violates the Rust bridge contract.
    """
    bridge = OscillatoryWeightInitBridge()
    with torch.no_grad():
        for index, (name, parameter) in enumerate(_named_parameters(module)):
            if "coupling" in name and parameter.dim() == 2:
                initialized = torch.utils.dlpack.from_dlpack(
                    bridge.matrix(
                        parameter.detach(),
                        True,
                        coupling_scale,
                        proj_gain,
                        seed_counter + index,
                        seed_key,
                    )
                )
                parameter.copy_(initialized)
            elif "weight" in name and parameter.dim() == 2:
                initialized = torch.utils.dlpack.from_dlpack(
                    bridge.matrix(
                        parameter.detach(),
                        False,
                        coupling_scale,
                        proj_gain,
                        seed_counter + index,
                        seed_key,
                    )
                )
                parameter.copy_(initialized)
            elif "bias" in name and parameter.dim() == 1:
                initialized = torch.utils.dlpack.from_dlpack(
                    bridge.bias(parameter.detach())
                )
                parameter.copy_(initialized)
