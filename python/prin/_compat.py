"""PRINet 3.0 compatibility aliases and unavailable-backend stubs.

This module contains only name adaptation and fail-closed backend dispositions.
All numerical behavior remains in the Rust-backed PRIN owners.
"""

from __future__ import annotations

from typing import NoReturn, Protocol, runtime_checkable

from prin.dynamics import (
    BandNetwork,
    OscillatorState,
    StateDerivatives,
    TemporalPropagator,
)
from prin.eval import recovery_speed
from prin.nn import Rip, Scalr, SyncGd

__all__: list[str] = [
    "BackendUnavailableError",
    "DeltaThetaGammaNetwork",
    "OscillatorModel",
    "RIPOptimizer",
    "SCALROptimizer",
    "SynchronizedGradientDescent",
    "TemporalPhasePropagator",
    "ThetaGammaNetwork",
    "cuda_fused_kernel_available",
    "fused_discrete_step_cuda",
    "temporal_recovery_speed",
    "triton_available",
    "triton_fused_discrete_step",
    "triton_fused_mean_field_rk4_step",
    "triton_hierarchical_order_param",
    "triton_pac_modulation",
    "triton_sparse_knn_coupling",
]


class BackendUnavailableError(RuntimeError):
    """Report that a deliberately unsupported legacy backend was requested."""


@runtime_checkable
class OscillatorModel(Protocol):
    """Structural compatibility contract for Rust-backed oscillator models."""

    @property
    def n_oscillators(self) -> int:
        """Return the number of oscillators owned by the model."""
        ...

    def compute_derivatives(self, state: OscillatorState) -> StateDerivatives:
        """Compute derivatives through the model's Rust implementation."""
        ...


SCALROptimizer = Scalr
RIPOptimizer = Rip
SynchronizedGradientDescent = SyncGd
TemporalPhasePropagator = TemporalPropagator
temporal_recovery_speed = recovery_speed
ThetaGammaNetwork = BandNetwork.theta_gamma
DeltaThetaGammaNetwork = BandNetwork.delta_theta_gamma


def triton_available() -> bool:
    """Return whether PRIN provides the retired Triton backend.

    Returns:
        Always ``False``. PRIN uses Rust-backed CPU, CUDA, or wgpu dispatch.
    """
    return False


def cuda_fused_kernel_available() -> bool:
    """Return whether PRIN provides the retired Python CUDA extension.

    Returns:
        Always ``False``. Use PRIN's Rust-backed kernel dispatch instead.
    """
    return False


def _raise_backend_unavailable(symbol: str) -> NoReturn:
    """Raise the shared typed error with migration guidance."""
    raise BackendUnavailableError(
        f"{symbol} is a retired GPU-only PRINet 3.0 path. PRIN migration: "
        "use the corresponding pytorch_* CPU binding when available, or use "
        "the Rust-backed kernel through prin.dynamics."
    )


def triton_fused_mean_field_rk4_step(*_args: object, **_kwargs: object) -> NoReturn:
    """Reject calls to the retired Triton mean-field RK4 kernel.

    Raises:
        BackendUnavailableError: Always; use PRIN's Rust-backed kernel path.
    """
    _raise_backend_unavailable("triton_fused_mean_field_rk4_step")


def triton_sparse_knn_coupling(*_args: object, **_kwargs: object) -> NoReturn:
    """Reject calls to the retired Triton sparse k-NN kernel.

    Raises:
        BackendUnavailableError: Always; use the CPU binding or Rust dispatch.
    """
    _raise_backend_unavailable("triton_sparse_knn_coupling")


def triton_pac_modulation(*_args: object, **_kwargs: object) -> NoReturn:
    """Reject calls to the retired Triton PAC kernel.

    Raises:
        BackendUnavailableError: Always; use the CPU binding or Rust dispatch.
    """
    _raise_backend_unavailable("triton_pac_modulation")


def triton_hierarchical_order_param(*_args: object, **_kwargs: object) -> NoReturn:
    """Reject calls to the retired Triton hierarchical reduction.

    Raises:
        BackendUnavailableError: Always; use the CPU binding or Rust dispatch.
    """
    _raise_backend_unavailable("triton_hierarchical_order_param")


def triton_fused_discrete_step(*_args: object, **_kwargs: object) -> NoReturn:
    """Reject calls to the retired Triton fused discrete step.

    Raises:
        BackendUnavailableError: Always; use the CPU binding or Rust dispatch.
    """
    _raise_backend_unavailable("triton_fused_discrete_step")


def fused_discrete_step_cuda(*_args: object, **_kwargs: object) -> NoReturn:
    """Reject calls to the retired Python CUDA fused discrete step.

    Raises:
        BackendUnavailableError: Always; use PRIN's Rust-backed kernel path.
    """
    _raise_backend_unavailable("fused_discrete_step_cuda")
