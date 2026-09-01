"""Marshal tensors for Rust-owned compatibility kernels and parameter sweeps.

This module is the thin Python compatibility layer in the PRIN rebuild of
PRINet 3.0. It performs shape orchestration and tensor/list conversion only;
Rust functions exposed by :mod:`prin._prin_core` own every numerical result.
"""

from __future__ import annotations

import os
import subprocess
import sys
import warnings
from collections.abc import Callable, Sequence
from pathlib import Path
from typing import TypeAlias

import torch
from torch import Tensor

from prin import _prin_core
from prin._compat import cuda_fused_kernel_available
from prin._prin_core import Seed

__all__ = [
    "_ensure_msvc_on_path",
    "_find_msvc_cl",
    "build_knn_neighbors",
    "csr_coupling_step",
    "cuda_fused_kernel_available",
    "detect_oscillation",
    "phase_to_rate",
    "pytorch_cross_band_coupling",
    "pytorch_fused_discrete_step",
    "pytorch_fused_discrete_step_full",
    "pytorch_fused_sub_step_rk4",
    "pytorch_hierarchical_order_param",
    "pytorch_mean_field_rk4_step",
    "pytorch_multi_rate_derivatives",
    "pytorch_multi_rate_rk4_step",
    "pytorch_pac_modulation",
    "pytorch_sparse_knn_coupling",
    "sparse_coupling_matrix",
    "sparse_coupling_matrix_csr",
    "sparse_knn_coupling_step",
    "sweep_coupling_params",
]

SeedLike: TypeAlias = int | Seed
_CoreTriple: TypeAlias = tuple[list[float], list[float], list[float]]


def _float_list(value: Tensor, *, double: bool = False) -> list[float]:
    """Convert a tensor to a flat list of floats on the CPU."""
    dtype = torch.float64 if double else torch.float32
    return (
        value.detach().to(device="cpu", dtype=dtype).contiguous().reshape(-1).tolist()
    )


def _int_list(value: Tensor) -> list[int]:
    """Convert a tensor to a flat list of 64-bit integers on the CPU."""
    return (
        value.detach()
        .to(device="cpu", dtype=torch.int64)
        .contiguous()
        .reshape(-1)
        .tolist()
    )


def _tensor(values: Sequence[float], like: Tensor, shape: torch.Size) -> Tensor:
    """Rebuild a tensor from a flat sequence, preserving dtype and device."""
    return torch.tensor(values, dtype=like.dtype, device=like.device).reshape(shape)


def _seed_parts(value: SeedLike | None) -> tuple[int, int]:
    """Normalize a ``Seed``, integer, or ``None`` to a (counter, key) pair."""
    if value is None:
        return 0, 0
    if isinstance(value, Seed):
        return int(value.counter), int(value.key)
    return int(value), 0


def _require_same_shape(first: Tensor, second: Tensor, name: str) -> None:
    """Raise ``ValueError`` unless two tensors share the exact shape."""
    if first.shape != second.shape:
        raise ValueError(
            f"{name} must have shape {tuple(first.shape)}, got {tuple(second.shape)}"
        )


def _rows(value: Tensor) -> Tensor:
    """Reshape a tensor to ``(batch, last_dim)`` and validate it is non-empty."""
    if value.ndim == 0:
        raise ValueError("tensor inputs must have at least one dimension")
    if value.numel() == 0:
        raise ValueError("tensor inputs must be non-empty")
    return value.reshape(-1, value.shape[-1])


def _batched_triple(
    owner: Callable[[list[float], list[float], list[float]], _CoreTriple],
    phase: Tensor,
    amplitude: Tensor,
    frequency: Tensor,
) -> tuple[Tensor, Tensor, Tensor]:
    """Call a three-tuple Rust owner once per batch row and reassemble tensors."""
    _require_same_shape(phase, amplitude, "amplitude")
    _require_same_shape(phase, frequency, "frequency")
    outputs = [
        owner(_float_list(p), _float_list(a), _float_list(f))
        for p, a, f in zip(
            _rows(phase), _rows(amplitude), _rows(frequency), strict=True
        )
    ]
    phase_values = [value for output in outputs for value in output[0]]
    amplitude_values = [value for output in outputs for value in output[1]]
    frequency_values = [value for output in outputs for value in output[2]]
    return (
        _tensor(phase_values, phase, phase.shape),
        _tensor(amplitude_values, amplitude, amplitude.shape),
        _tensor(frequency_values, frequency, frequency.shape),
    )


def pytorch_mean_field_rk4_step(
    phase: Tensor,
    amplitude: Tensor,
    frequency: Tensor,
    K: float,
    decay: float,
    gamma: float,
    dt: float,
) -> tuple[Tensor, Tensor, Tensor]:
    """Advance oscillator states with the Rust mean-field RK4 owner.

    This compatibility wrapper for the PRINet 3.0 rebuild only marshals batches;
    ``prin-kernels`` owns the numerical integration.

    Args:
        phase: Oscillator phase angles in radians. Shape: ``(..., N)``.
        amplitude: Dimensionless oscillator amplitudes. Shape: ``(..., N)``.
        frequency: Oscillator angular frequencies in radians per second.
            Shape: ``(..., N)``.
        K: Mean-field coupling strength in radians per second.
        decay: Amplitude decay rate in inverse seconds.
        gamma: Frequency-adaptation rate in inverse seconds.
        dt: Integration timestep in seconds.

    Returns:
        Updated phase in radians, dimensionless amplitude, and angular frequency
        in radians per second. Each tensor has shape ``(..., N)`` and preserves
        the dtype and device of its corresponding input.

    Raises:
        ValueError: If tensor shapes differ, an input is scalar or empty, or the
            Rust owner rejects a numerical parameter.

    Notes:
        PRINet 3.0 computed the mean-field order parameter with
        ``torch.complex64`` intermediates; PRIN accumulates the same real and
        imaginary components in ``f64`` and stores the final state in ``f32``,
        which can produce ~1e-7 per-step rounding differences on the paths
        affected by that intermediate type. This is an accepted preserved
        numerical hazard (Project Plan amendment #14); parity tests use
        ``rtol=1e-5, atol=1e-6``.

    Examples:
        >>> phase = torch.zeros(4)
        >>> amplitude = torch.ones(4)
        >>> frequency = torch.ones(4)
        >>> p, a, f = pytorch_mean_field_rk4_step(
        ...     phase, amplitude, frequency, 0.2, 0.1, 0.0, 0.01
        ... )
        >>> p.shape == a.shape == f.shape
        True
    """
    return _batched_triple(
        lambda p, a, f: _prin_core.pytorch_mean_field_rk4_step(
            p, a, f, K, decay, gamma, dt
        ),
        phase,
        amplitude,
        frequency,
    )


def pytorch_sparse_knn_coupling(
    phase: Tensor,
    amplitude: Tensor,
    frequency: Tensor,
    nbr_idx: Tensor,
    K: float,
    decay: float,
    gamma: float,
) -> tuple[Tensor, Tensor, Tensor]:
    """Evaluate sparse k-nearest-neighbor derivatives with the Rust owner.

    The Python layer only marshals the PRINet 3.0 compatibility inputs;
    ``prin-kernels`` owns the derivative calculation.

    Args:
        phase: Oscillator phase angles in radians. Shape: ``(N,)``.
        amplitude: Dimensionless oscillator amplitudes. Shape: ``(N,)``.
        frequency: Oscillator angular frequencies in radians per second.
            Shape: ``(N,)``.
        nbr_idx: Neighbor indices. Shape: ``(N, k)``.
        K: Sparse coupling strength in radians per second.
        decay: Amplitude decay rate in inverse seconds.
        gamma: Frequency-adaptation rate in inverse seconds.

    Returns:
        Phase, amplitude, and angular-frequency derivatives with shape ``(N,)``.
        Units are radians per second, inverse seconds, and radians per second
        squared, respectively; tensors preserve ``phase`` dtype and device.

    Raises:
        ValueError: If state shapes differ, ``phase`` is not one-dimensional,
            ``nbr_idx`` is not shaped ``(N, k)``, or the Rust owner rejects the
            graph or parameters.

    Examples:
        >>> phase = torch.zeros(3)
        >>> amplitude = torch.ones(3)
        >>> frequency = torch.ones(3)
        >>> neighbors = torch.tensor([[1], [2], [0]])
        >>> derivatives = pytorch_sparse_knn_coupling(
        ...     phase, amplitude, frequency, neighbors, 0.2, 0.1, 0.0
        ... )
        >>> derivatives[0].shape
        torch.Size([3])
    """
    _require_same_shape(phase, amplitude, "amplitude")
    _require_same_shape(phase, frequency, "frequency")
    if phase.ndim != 1 or nbr_idx.ndim != 2 or nbr_idx.shape[0] != phase.shape[0]:
        raise ValueError("phase must be (N,) and nbr_idx must be (N, k)")
    result = _prin_core.pytorch_sparse_knn_coupling(
        _float_list(phase),
        _float_list(amplitude),
        _float_list(frequency),
        _int_list(nbr_idx),
        K,
        decay,
        gamma,
    )
    return tuple(_tensor(values, phase, phase.shape) for values in result)  # type: ignore[return-value]


def pytorch_pac_modulation(
    slow_phase: Tensor,
    fast_amplitude: Tensor,
    modulation_depth: float,
    amp_min: float = 1e-6,
    amp_max: float = 10.0,
) -> Tensor:
    """Apply phase-amplitude-coupling modulation with the Rust owner.

    This PRINet 3.0 rebuild wrapper only marshals batch rows; ``prin-kernels``
    owns PAC modulation and amplitude clamping.

    Args:
        slow_phase: Slow-band phase angles in radians. Shape: ``(..., N_slow)``.
        fast_amplitude: Dimensionless fast-band amplitudes.
            Shape: ``(..., N_fast)`` with the same flattened batch size as
            ``slow_phase``.
        modulation_depth: Dimensionless PAC modulation depth.
        amp_min: Dimensionless minimum output amplitude.
        amp_max: Dimensionless maximum output amplitude.

    Returns:
        Modulated fast-band amplitudes. Shape: ``(..., N_fast)``; dtype and
        device match ``fast_amplitude``.

    Raises:
        ValueError: If an input is scalar or empty, flattened batch sizes differ,
            or the Rust owner rejects the lengths or clamp parameters.

    Examples:
        >>> slow = torch.tensor([0.0, 3.1415927])
        >>> fast = torch.ones(2)
        >>> pytorch_pac_modulation(slow, fast, 0.3).shape
        torch.Size([2])
    """
    slow_rows = _rows(slow_phase)
    fast_rows = _rows(fast_amplitude)
    if slow_rows.shape[0] != fast_rows.shape[0]:
        raise ValueError(
            "slow_phase and fast_amplitude must have matching batch dimensions"
        )
    values = [
        value
        for slow, fast in zip(slow_rows, fast_rows, strict=True)
        for value in _prin_core.pytorch_pac_modulation(
            _float_list(slow), _float_list(fast), modulation_depth, amp_min, amp_max
        )
    ]
    return _tensor(values, fast_amplitude, fast_amplitude.shape)


def pytorch_hierarchical_order_param(phase: Tensor, band_sizes: list[int]) -> Tensor:
    """Compute per-band Kuramoto order parameters with the Rust owner.

    ``prin-kernels`` owns this hierarchical reduction for the PRINet 3.0
    rebuild; Python only converts the returned values to a tensor.

    Args:
        phase: Concatenated oscillator phase angles in radians. Shape: ``(N,)``.
        band_sizes: Oscillator count for each contiguous frequency band; values
            must sum to ``N``.

    Returns:
        Dimensionless order parameter for each band, with values in ``[0, 1]``.
        Shape: ``(n_bands,)``; dtype and device match ``phase``.

    Raises:
        ValueError: If ``phase`` is not one-dimensional or the Rust owner rejects
            an empty, zero-sized, or inconsistent band partition.

    Examples:
        >>> phase = torch.tensor([0.0, 0.0, 1.0, 1.0])
        >>> pytorch_hierarchical_order_param(phase, [2, 2])
        tensor([1., 1.])
    """
    if phase.ndim != 1:
        raise ValueError("phase must be one-dimensional")
    values = _prin_core.pytorch_hierarchical_order_param(_float_list(phase), band_sizes)
    return _tensor(values, phase, torch.Size([len(band_sizes)]))


def pytorch_multi_rate_rk4_step(
    phase: Tensor,
    amplitude: Tensor,
    frequency: Tensor,
    K: float,
    decay: float,
    gamma: float,
    dt: float,
    sub_steps: int,
    mean_field: bool = True,
) -> tuple[Tensor, Tensor, Tensor]:
    """Run repeated inner RK4 steps with the Rust multi-rate owner.

    This PRINet 3.0 rebuild wrapper preserves tensor placement while
    ``prin-kernels`` owns all numerical stepping.

    Args:
        phase: Oscillator phase angles in radians. Shape: ``(N,)``.
        amplitude: Dimensionless oscillator amplitudes. Shape: ``(N,)``.
        frequency: Oscillator angular frequencies in radians per second.
            Shape: ``(N,)``.
        K: Coupling strength in radians per second.
        decay: Amplitude decay rate in inverse seconds.
        gamma: Frequency-adaptation rate in inverse seconds.
        dt: Outer integration timestep in seconds.
        sub_steps: Number of equal inner RK4 steps.
        mean_field: Whether to use mean-field rather than uncoupled derivatives.

    Returns:
        Updated phase in radians, dimensionless amplitude, and angular frequency
        in radians per second. Each tensor has shape ``(N,)`` and preserves the
        dtype and device of ``phase``.

    Raises:
        ValueError: If ``phase`` is not one-dimensional or the Rust owner rejects
            mismatched state lengths, an empty state, or invalid parameters.

    Examples:
        >>> state = torch.zeros(3), torch.ones(3), torch.ones(3)
        >>> output = pytorch_multi_rate_rk4_step(
        ...     *state, 0.2, 0.1, 0.0, 0.01, 2
        ... )
        >>> output[0].shape
        torch.Size([3])
    """
    if phase.ndim != 1:
        raise ValueError("phase must be one-dimensional")
    result = _prin_core.pytorch_multi_rate_rk4_step(
        _float_list(phase),
        _float_list(amplitude),
        _float_list(frequency),
        K,
        decay,
        gamma,
        dt,
        sub_steps,
        mean_field,
    )
    return tuple(_tensor(values, phase, phase.shape) for values in result)  # type: ignore[return-value]


def pytorch_multi_rate_derivatives(
    phase: Tensor,
    amplitude: Tensor,
    frequency: Tensor,
    freq_band: Tensor,
    K: float,
    decay: float,
    gamma: float,
    band_frequencies: tuple[float, float, float] | None = None,
) -> tuple[Tensor, Tensor, Tensor]:
    """Compute band-selected mean-field derivatives with the Rust owner.

    ``prin-kernels`` owns the multi-rate derivative calculation in the PRINet
    3.0 rebuild; Python only marshals flat state arrays.

    Args:
        phase: Oscillator phase angles in radians. Shape: ``(N,)``.
        amplitude: Dimensionless oscillator amplitudes. Shape: ``(N,)``.
        frequency: Oscillator angular frequencies in radians per second.
            Shape: ``(N,)``.
        freq_band: Integer band labels ``0`` (delta), ``1`` (theta), or ``2``
            (gamma). Shape: ``(N,)``.
        K: Mean-field coupling strength in radians per second.
        decay: Amplitude decay rate in inverse seconds.
        gamma: Frequency-adaptation rate in inverse seconds.
        band_frequencies: Optional delta, theta, and gamma frequencies in Hz.

    Returns:
        Phase, amplitude, and angular-frequency derivatives with shape ``(N,)``.
        Units are radians per second, inverse seconds, and radians per second
        squared, respectively; tensors preserve ``phase`` dtype and device.

    Raises:
        ValueError: If state or band-label lengths differ, inputs are empty, a
            band label is invalid, or the Rust owner rejects a parameter.

    Examples:
        >>> state = torch.zeros(3), torch.ones(3), torch.ones(3)
        >>> bands = torch.tensor([0, 1, 2])
        >>> output = pytorch_multi_rate_derivatives(
        ...     *state, bands, 0.2, 0.1, 0.0
        ... )
        >>> output[0].shape
        torch.Size([3])
    """
    values = None if band_frequencies is None else list(band_frequencies)
    result = _prin_core.pytorch_multi_rate_derivatives(
        _float_list(phase),
        _float_list(amplitude),
        _float_list(frequency),
        _int_list(freq_band),
        K,
        decay,
        gamma,
        values,
    )
    return tuple(_tensor(item, phase, phase.shape) for item in result)  # type: ignore[return-value]


def pytorch_fused_sub_step_rk4(
    phase: Tensor,
    amplitude: Tensor,
    frequency: Tensor,
    freq_band: Tensor,
    K: float,
    decay: float,
    gamma: float,
    dt: float,
    sub_steps_per_band: tuple[int, int, int] | None = None,
) -> tuple[Tensor, Tensor, Tensor]:
    """Run fused band-specific RK4 substeps with the Rust owner.

    This compatibility entry point for the PRINet 3.0 rebuild marshals one flat
    population; ``prin-kernels`` owns band scheduling and integration.

    Args:
        phase: Oscillator phase angles in radians. Shape: ``(N,)``.
        amplitude: Dimensionless oscillator amplitudes. Shape: ``(N,)``.
        frequency: Oscillator angular frequencies in radians per second.
            Shape: ``(N,)``.
        freq_band: Integer band labels ``0`` (delta), ``1`` (theta), or ``2``
            (gamma). Shape: ``(N,)``.
        K: Mean-field coupling strength in radians per second.
        decay: Amplitude decay rate in inverse seconds.
        gamma: Frequency-adaptation rate in inverse seconds.
        dt: Outer integration timestep in seconds.
        sub_steps_per_band: Optional inner-step counts for the delta, theta, and
            gamma bands.

    Returns:
        Updated phase in radians, dimensionless amplitude, and angular frequency
        in radians per second. Each tensor has shape ``(N,)`` and preserves the
        dtype and device of ``phase``.

    Raises:
        ValueError: If state or band-label lengths differ, inputs are empty, a
            band label is invalid, or the Rust owner rejects step parameters.

    Examples:
        >>> state = torch.zeros(3), torch.ones(3), torch.ones(3)
        >>> bands = torch.tensor([0, 1, 2])
        >>> output = pytorch_fused_sub_step_rk4(
        ...     *state, bands, 0.2, 0.1, 0.0, 0.01, (1, 2, 4)
        ... )
        >>> output[0].shape
        torch.Size([3])
    """
    values = None if sub_steps_per_band is None else list(sub_steps_per_band)
    result = _prin_core.pytorch_fused_sub_step_rk4(
        _float_list(phase),
        _float_list(amplitude),
        _float_list(frequency),
        _int_list(freq_band),
        K,
        decay,
        gamma,
        dt,
        values,
    )
    return tuple(_tensor(item, phase, phase.shape) for item in result)  # type: ignore[return-value]


def pytorch_cross_band_coupling(
    slow_phase: Tensor,
    fast_phase: Tensor,
    fast_amplitude: Tensor,
    parent_idx: Tensor,
    modulation_depth: float = 0.3,
    epsilon: float = 1e-6,
) -> tuple[Tensor, Tensor]:
    """Apply parent-index cross-band PAC coupling with the Rust owner.

    ``prin-kernels`` owns the PAC calculation in the PRINet 3.0 rebuild; this
    wrapper only marshals population arrays and restores tensor placement.

    Args:
        slow_phase: Slow-band parent phase angles in radians. Shape: ``(N_slow,)``.
        fast_phase: Fast-band phase angles in radians. Shape: ``(N_fast,)``.
        fast_amplitude: Dimensionless fast-band amplitudes. Shape: ``(N_fast,)``.
        parent_idx: Parent index in ``slow_phase`` for each fast oscillator.
            Shape: ``(N_fast,)``.
        modulation_depth: Dimensionless PAC modulation depth.
        epsilon: Positive dimensionless stability floor.

    Returns:
        A pair containing modulated fast amplitudes and fast phase corrections
        in radians. Both have shape ``(N_fast,)`` and preserve the dtype and
        device of ``fast_amplitude`` and ``fast_phase``, respectively.

    Raises:
        ValueError: If fast-array lengths differ, a parent index is out of range,
            an input is empty, or the Rust owner rejects a parameter.

    Examples:
        >>> slow = torch.tensor([0.0, 1.0])
        >>> fast = torch.tensor([0.2, 0.4, 0.6])
        >>> amplitude = torch.ones(3)
        >>> parent = torch.tensor([0, 0, 1])
        >>> modulated, correction = pytorch_cross_band_coupling(
        ...     slow, fast, amplitude, parent
        ... )
        >>> modulated.shape == correction.shape
        True
    """
    result = _prin_core.pytorch_cross_band_coupling(
        _float_list(slow_phase),
        _float_list(fast_phase),
        _float_list(fast_amplitude),
        _int_list(parent_idx),
        modulation_depth,
        epsilon,
    )
    return _tensor(result[0], fast_amplitude, fast_amplitude.shape), _tensor(
        result[1], fast_phase, fast_phase.shape
    )


def pytorch_fused_discrete_step(
    phase: Tensor,
    amplitude: Tensor,
    freq_delta: Tensor,
    freq_theta: Tensor,
    freq_gamma: Tensor,
    W_delta: Tensor,
    W_theta: Tensor,
    W_gamma: Tensor,
    mu_delta: float,
    mu_theta: float,
    mu_gamma: float,
    n_delta: int,
    n_theta: int,
    n_gamma: int,
    dt: float = 0.01,
) -> tuple[Tensor, Tensor]:
    """Run one dense three-band discrete step with the Rust owner.

    This wrapper supplies flattened batches to the ``prin-kernels`` numerical
    owner used by the PRINet 3.0 rebuild.

    Args:
        phase: Batched delta/theta/gamma phase angles in radians.
            Shape: ``(..., N)``, where ``N = n_delta + n_theta + n_gamma``.
        amplitude: Batched dimensionless amplitudes. Shape: ``(..., N)``.
        freq_delta: Delta-band angular frequencies in radians per second.
            Shape: ``(n_delta,)``.
        freq_theta: Theta-band angular frequencies in radians per second.
            Shape: ``(n_theta,)``.
        freq_gamma: Gamma-band angular frequencies in radians per second.
            Shape: ``(n_gamma,)``.
        W_delta: Delta-band coupling matrix in inverse seconds.
            Shape: ``(n_delta, n_delta)``.
        W_theta: Theta-band coupling matrix in inverse seconds.
            Shape: ``(n_theta, n_theta)``.
        W_gamma: Gamma-band coupling matrix in inverse seconds.
            Shape: ``(n_gamma, n_gamma)``.
        mu_delta: Delta-band Stuart-Landau growth rate in inverse seconds.
        mu_theta: Theta-band Stuart-Landau growth rate in inverse seconds.
        mu_gamma: Gamma-band Stuart-Landau growth rate in inverse seconds.
        n_delta: Number of delta-band oscillators.
        n_theta: Number of theta-band oscillators.
        n_gamma: Number of gamma-band oscillators.
        dt: Integration timestep in seconds.

    Returns:
        Updated phase angles in radians and dimensionless amplitudes. Both have
        shape ``(..., N)`` and preserve the dtype and device of ``phase`` and
        ``amplitude``, respectively.

    Raises:
        ValueError: If state, frequency, or coupling shapes are inconsistent;
            values are non-finite; a band is empty; or ``dt`` is not positive.

    Examples:
        >>> phase = torch.zeros(3)
        >>> amplitude = torch.ones(3)
        >>> frequency = torch.ones(1)
        >>> weight = torch.zeros(1, 1)
        >>> output = pytorch_fused_discrete_step(
        ...     phase, amplitude, frequency, frequency, frequency,
        ...     weight, weight, weight, 1.0, 1.0, 1.0, 1, 1, 1
        ... )
        >>> output[0].shape
        torch.Size([3])
    """
    result = _prin_core.pytorch_fused_discrete_step(
        _float_list(phase),
        _float_list(amplitude),
        _float_list(freq_delta),
        _float_list(freq_theta),
        _float_list(freq_gamma),
        _float_list(W_delta),
        _float_list(W_theta),
        _float_list(W_gamma),
        mu_delta,
        mu_theta,
        mu_gamma,
        n_delta,
        n_theta,
        n_gamma,
        dt,
    )
    return _tensor(result[0], phase, phase.shape), _tensor(
        result[1], amplitude, amplitude.shape
    )


def pytorch_fused_discrete_step_full(
    phase: Tensor,
    amplitude: Tensor,
    freq_delta: Tensor,
    freq_theta: Tensor,
    freq_gamma: Tensor,
    W_delta: Tensor,
    W_theta: Tensor,
    W_gamma: Tensor,
    W_pac_dt_weight: Tensor,
    W_pac_dt_bias: Tensor,
    W_pac_tg_weight: Tensor,
    W_pac_tg_bias: Tensor,
    mu_delta: float,
    mu_theta: float,
    mu_gamma: float,
    dt: float = 0.01,
    n_delta: int = 4,
    n_theta: int = 8,
    n_gamma: int = 32,
) -> tuple[Tensor, Tensor]:
    """Run a dense three-band step with Rust-owned PAC projections.

    ``prin-kernels`` owns the discrete update and learned sigmoid PAC gates for
    this PRINet 3.0 rebuild compatibility function.

    Args:
        phase: Batched delta/theta/gamma phase angles in radians.
            Shape: ``(..., N)``, where ``N = n_delta + n_theta + n_gamma``.
        amplitude: Batched dimensionless amplitudes. Shape: ``(..., N)``.
        freq_delta: Delta angular frequencies in radians per second.
            Shape: ``(n_delta,)``.
        freq_theta: Theta angular frequencies in radians per second.
            Shape: ``(n_theta,)``.
        freq_gamma: Gamma angular frequencies in radians per second.
            Shape: ``(n_gamma,)``.
        W_delta: Delta coupling matrix in inverse seconds.
            Shape: ``(n_delta, n_delta)``.
        W_theta: Theta coupling matrix in inverse seconds.
            Shape: ``(n_theta, n_theta)``.
        W_gamma: Gamma coupling matrix in inverse seconds.
            Shape: ``(n_gamma, n_gamma)``.
        W_pac_dt_weight: Delta-to-theta PAC projection weights.
            Shape: ``(n_theta, 2 * n_delta)``.
        W_pac_dt_bias: Delta-to-theta PAC projection biases.
            Shape: ``(n_theta,)``.
        W_pac_tg_weight: Theta-to-gamma PAC projection weights.
            Shape: ``(n_gamma, 2 * n_theta)``.
        W_pac_tg_bias: Theta-to-gamma PAC projection biases.
            Shape: ``(n_gamma,)``.
        mu_delta: Delta Stuart-Landau growth rate in inverse seconds.
        mu_theta: Theta Stuart-Landau growth rate in inverse seconds.
        mu_gamma: Gamma Stuart-Landau growth rate in inverse seconds.
        dt: Integration timestep in seconds.
        n_delta: Number of delta-band oscillators.
        n_theta: Number of theta-band oscillators.
        n_gamma: Number of gamma-band oscillators.

    Returns:
        Updated phase angles in radians and dimensionless amplitudes. Both have
        shape ``(..., N)`` and preserve the dtype and device of ``phase`` and
        ``amplitude``, respectively.

    Raises:
        ValueError: If state, frequency, coupling, or PAC projection shapes are
            inconsistent; values are non-finite; a band is empty; or ``dt`` is
            not positive.

    Examples:
        >>> phase = torch.zeros(3)
        >>> amplitude = torch.ones(3)
        >>> frequency = torch.ones(1)
        >>> weight = torch.zeros(1, 1)
        >>> pac_weight = torch.zeros(1, 2)
        >>> pac_bias = torch.zeros(1)
        >>> output = pytorch_fused_discrete_step_full(
        ...     phase, amplitude, frequency, frequency, frequency,
        ...     weight, weight, weight, pac_weight, pac_bias,
        ...     pac_weight, pac_bias, 1.0, 1.0, 1.0,
        ...     n_delta=1, n_theta=1, n_gamma=1
        ... )
        >>> output[1].shape
        torch.Size([3])
    """
    result = _prin_core.pytorch_fused_discrete_step_full(
        _float_list(phase),
        _float_list(amplitude),
        _float_list(freq_delta),
        _float_list(freq_theta),
        _float_list(freq_gamma),
        _float_list(W_delta),
        _float_list(W_theta),
        _float_list(W_gamma),
        _float_list(W_pac_dt_weight),
        _float_list(W_pac_dt_bias),
        _float_list(W_pac_tg_weight),
        _float_list(W_pac_tg_bias),
        mu_delta,
        mu_theta,
        mu_gamma,
        dt,
        n_delta,
        n_theta,
        n_gamma,
    )
    return _tensor(result[0], phase, phase.shape), _tensor(
        result[1], amplitude, amplitude.shape
    )


def build_knn_neighbors(
    n_oscillators: int,
    k: int = 8,
    device: torch.device | str | None = None,
    seed: SeedLike | None = None,
) -> Tensor:
    """Build deterministic Rust-owned unique non-self neighbor rows.

    Args:
        n_oscillators: Number of oscillators, must be at least 2.
        k: Number of neighbors per oscillator, must satisfy ``1 <= k < n``.
        device: Optional target device for the returned tensor.
        seed: Optional deterministic seed. An ``int`` is used as the counter
            with key 0; a ``prin.Seed`` object is split into counter and key.

    Returns:
        Neighbor index table of shape ``(n_oscillators, k)`` and dtype
        ``torch.long``.

    Raises:
        ValueError: If ``n_oscillators < 2``, ``k < 1``, ``k >= n_oscillators``,
            or the requested shape overflows.

    Notes:
        The same PRIN ``Seed`` or integer counter always yields the same table,
        but PRINet 3.0 used ``torch.Generator`` streams with a different
        sampling order. A PRIN seed value is therefore not guaranteed to match
        a PRINet 3.0 seed value for the same topology; compare topologies only
        through the same PRIN call path.

    Examples:
        >>> neighbors = build_knn_neighbors(4, 2, seed=0)
        >>> neighbors.shape
        torch.Size([4, 2])
        >>> all(i not in neighbors[i].tolist() for i in range(4))
        True
    """
    counter, key = _seed_parts(seed)
    values = _prin_core.build_knn_neighbors(n_oscillators, k, counter, key)
    return torch.tensor(values, dtype=torch.long, device=device).reshape(
        n_oscillators, k
    )


def sparse_coupling_matrix(
    n_oscillators: int,
    sparsity: float = 0.9,
    coupling_strength: float = 1.0,
    symmetric: bool = True,
    device: torch.device | str | None = None,
    dtype: torch.dtype = torch.float32,
    seed: SeedLike | None = None,
) -> Tensor:
    """Generate a dense coupling tensor from Rust-owned random draws.

    An edge is retained when a uniform draw exceeds ``sparsity``; retained
    magnitudes are half-normal draws scaled by ``coupling_strength / N``. The
    diagonal is always zero. In symmetric mode the upper-triangle mask is
    mirrored and opposite-direction magnitudes are averaged.

    Args:
        n_oscillators: Number of oscillators, must be positive.
        sparsity: Sparsity threshold in ``[0, 1)``.
        coupling_strength: Finite non-negative coupling scale.
        symmetric: Whether to mirror the upper triangle.
        device: Optional target device for the returned tensor.
        dtype: Floating-point dtype for the returned tensor.
        seed: Optional deterministic seed.

    Returns:
        Dense ``(n_oscillators, n_oscillators)`` coupling tensor.

    Raises:
        ValueError: If ``n_oscillators == 0``, ``sparsity`` is invalid,
            ``coupling_strength`` is non-finite, or the requested shape
            overflows.
    """
    counter, key = _seed_parts(seed)
    values = _prin_core.sparse_coupling_matrix(
        n_oscillators, sparsity, coupling_strength, symmetric, counter, key
    )
    return torch.tensor(values, dtype=dtype, device=device).reshape(
        n_oscillators, n_oscillators
    )


def sparse_coupling_matrix_csr(
    n_oscillators: int,
    sparsity: float = 0.95,
    coupling_strength: float = 1.0,
    symmetric: bool = True,
    device: torch.device | str | None = None,
    dtype: torch.dtype = torch.float32,
    seed: SeedLike | None = None,
) -> Tensor:
    """Generate a CSR coupling tensor from Rust-owned CSR arrays.

    Uses the same draw rules as ``sparse_coupling_matrix`` but returns a
    ``torch.sparse_csr_tensor`` that can be passed to ``csr_coupling_step``.

    Args:
        n_oscillators: Number of oscillators, must be positive.
        sparsity: Sparsity threshold in ``[0, 1)``.
        coupling_strength: Finite non-negative coupling scale.
        symmetric: Whether to mirror the upper triangle.
        device: Optional target device for the returned tensor.
        dtype: Floating-point dtype for the returned tensor.
        seed: Optional deterministic seed.

    Returns:
        Sparse CSR coupling tensor of shape ``(n_oscillators, n_oscillators)``.

    Raises:
        ValueError: If ``n_oscillators == 0``, ``sparsity`` is invalid,
            ``coupling_strength`` is non-finite, or the requested shape
            overflows.
    """
    counter, key = _seed_parts(seed)
    crow, col, values = _prin_core.sparse_coupling_matrix_csr(
        n_oscillators, sparsity, coupling_strength, symmetric, counter, key
    )
    with warnings.catch_warnings():
        warnings.simplefilter("ignore", UserWarning)
        return torch.sparse_csr_tensor(
            crow,
            col,
            values,
            size=(n_oscillators, n_oscillators),
            dtype=dtype,
            device=device,
        )


def csr_coupling_step(phase: Tensor, coupling_csr: Tensor) -> Tensor:
    """Compute Kuramoto sine corrections from a sparse CSR coupling matrix.

    Evaluates ``sum_j W[i,j] * sin(phase[j] - phase[i])`` for each oscillator.

    Args:
        phase: Oscillator phase angles in radians. Shape: ``(..., N)``.
        coupling_csr: Sparse CSR coupling matrix. Shape: ``(N, N)`` with
            ``torch.sparse_csr`` layout.

    Returns:
        Sine correction tensor with the same shape and dtype as ``phase``.

    Raises:
        ValueError: If ``coupling_csr`` is not a CSR tensor, shapes mismatch,
            or the Rust owner rejects a non-finite phase.
    """
    if coupling_csr.layout != torch.sparse_csr:
        raise ValueError("coupling_csr must use torch.sparse_csr layout")
    rows = _rows(phase)
    crow = _int_list(coupling_csr.crow_indices())
    col = _int_list(coupling_csr.col_indices())
    values = _float_list(coupling_csr.values(), double=True)
    output = [
        value
        for row in rows
        for value in _prin_core.csr_coupling_step(
            _float_list(row, double=True), crow, col, values
        )
    ]
    return _tensor(output, phase, phase.shape)


def sparse_knn_coupling_step(
    phase: Tensor,
    amplitude: Tensor,
    neighbors: Tensor,
    coupling_strength: float = 2.0,
) -> Tensor:
    """Compute sparse k-NN phase corrections, with batch orchestration.

    Evaluates ``K/k * sum_j sin(phase[j] - phase[i])`` over the neighbor table.
    The archived compatibility formula does not use amplitude values, but
    ``amplitude`` is still validated for length and finiteness.

    Args:
        phase: Oscillator phase angles in radians. Shape: ``(..., N)``.
        amplitude: Dimensionless amplitudes. Shape: ``(..., N)``.
        neighbors: Neighbor index table. Shape: ``(N, k)``.
        coupling_strength: Sparse coupling strength in radians per second.

    Returns:
        Sine correction tensor with the same shape and dtype as ``phase``.

    Raises:
        ValueError: If shapes differ, ``neighbors`` is not a valid table, or
            the Rust owner rejects a parameter.
    """
    _require_same_shape(phase, amplitude, "amplitude")
    neighbor_values = _int_list(neighbors)
    output = [
        value
        for p, a in zip(_rows(phase), _rows(amplitude), strict=True)
        for value in _prin_core.sparse_knn_coupling_step(
            _float_list(p, double=True),
            _float_list(a, double=True),
            neighbor_values,
            coupling_strength,
        )
    ]
    return _tensor(output, phase, phase.shape)


def sweep_coupling_params(
    n_oscillators: int = 64,
    k_values: list[float] | None = None,
    m_values: list[float] | None = None,
    n_steps: int = 100,
    dt: float = 0.01,
    seed: SeedLike | None = 0,
    device: torch.device | str | None = None,
) -> list[dict[str, float]]:
    """Run the deterministic Rust coupling/PAC parameter sweep.

    Computes a Cartesian grid of ``(K, m)`` points using the audited
    delta-theta-gamma band network owner in Rust. Every point starts from the
    same explicit seed, so repeated calls with the same arguments are identical.

    Args:
        n_oscillators: Number of oscillators in the synthetic population.
        k_values: Coupling strengths ``K``; defaults to ``[0.5, 1.0, 2.0, 4.0]``.
        m_values: PAC modulation depths ``m``; defaults to
            ``[0.1, 0.3, 0.5, 0.7]`` and each value must lie in ``[0, 1]``.
        n_steps: Number of RK4 integration steps per grid point.
        dt: Positive integration timestep.
        seed: Optional deterministic seed. An ``int`` is used as the counter
            with key 0; a ``prin.Seed`` object is split into counter and key.
        device: Unused; present for API symmetry with other kernel functions.

    Returns:
        One dictionary per ``(K, m)`` pair with keys ``"K"``, ``"m"``,
        ``"r_delta"``, ``"r_theta"``, and ``"r_gamma"``.

    Raises:
        ValueError: If the parameter grid is empty, ``m_values`` outside
            ``[0, 1]``, ``n_steps == 0``, ``dt <= 0``, or the Rust owner fails.

    Examples:
        >>> results = sweep_coupling_params(
        ...     n_oscillators=6, k_values=[0.5, 1.0], m_values=[0.1, 0.3],
        ...     n_steps=1, dt=0.01, seed=0
        ... )
        >>> len(results)
        4
        >>> set(results[0])
        {'K', 'm', 'r_delta', 'r_theta', 'r_gamma'}
    """
    del device
    counter, key = _seed_parts(seed)
    return _prin_core.sweep_coupling_params(
        n_oscillators, k_values, m_values, n_steps, dt, counter, key
    )


def detect_oscillation(
    r_history: list[float], window: int = 20, threshold: float = 0.01
) -> bool:
    """Detect oscillatory instability in an order-parameter history.

    Splits ``r_history`` into overlapping windows of length ``window`` and
    returns ``True`` as soon as one window's variance exceeds ``threshold``.

    Args:
        r_history: One-dimensional list of order-parameter magnitudes.
        window: Positive window length for the variance computation.
        threshold: Non-negative variance threshold.

    Returns:
        ``True`` when a destabilizing oscillation is detected, ``False``
        otherwise.

    Raises:
        ValueError: If ``r_history`` contains non-finite values,
            ``window <= 0``, or ``threshold`` is negative or non-finite.

    Examples:
        >>> detect_oscillation([0.5] * 30)
        False
        >>> detect_oscillation([0.0, 1.0] * 10, window=10, threshold=0.01)
        True
    """
    return _prin_core.detect_oscillation(r_history, window, threshold)


def phase_to_rate(
    phase: Tensor,
    amplitude: Tensor,
    mode: str = "soft",
    sparsity: float = 0.1,
    temperature: float = 1.0,
) -> Tensor:
    """Convert phase/amplitude rows to sparse winner-take-all rates.

    Computes the instantaneous rate ``amplitude * (1 + cos(phase)) / 2`` and
    applies a soft, hard, or annealed winner-take-all rule.

    Args:
        phase: Oscillator phase angles in radians. Shape: ``(..., N)``.
        amplitude: Dimensionless amplitudes. Shape: ``(..., N)``.
        mode: One of ``"soft"`` (temperature-scaled softmax), ``"hard"``
            (top-k), or ``"annealed"`` (sigmoid blend of soft and hard).
        sparsity: Fraction of active rates; must lie in ``[0, 1]``.
        temperature: Positive temperature for the soft rule.

    Returns:
        Sparse rates with the same shape and dtype as ``phase``.

    Raises:
        ValueError: If shapes differ, an input is empty, ``mode`` is unknown,
            ``sparsity`` is outside ``[0, 1]``, ``temperature <= 0``, or the
            Rust owner rejects an input.

    Examples:
        >>> phase = torch.tensor([0.0, 3.1415927])
        >>> amplitude = torch.ones(2)
        >>> phase_to_rate(phase, amplitude, mode="hard", sparsity=0.5)
        tensor([0., 1.])
    """
    _require_same_shape(phase, amplitude, "amplitude")
    output = [
        value
        for p, a in zip(_rows(phase), _rows(amplitude), strict=True)
        for value in _prin_core.phase_to_rate(
            _float_list(p, double=True),
            _float_list(a, double=True),
            mode,
            sparsity,
            temperature,
        )
    ]
    return _tensor(output, phase, phase.shape)


def _find_msvc_cl() -> str | None:
    """Locate the MSVC ``cl.exe`` compiler via ``vswhere`` (Windows only).

    Returns the path to ``cl.exe`` or ``None`` if Visual Studio is not
    installed or ``vswhere`` cannot find it.  On non-Windows platforms
    always returns ``None``.
    """
    if sys.platform != "win32":
        return None
    vswhere = Path(
        r"C:\Program Files (x86)\Microsoft Visual Studio\Installer\vswhere.exe"
    )
    if not vswhere.exists():
        return None
    try:
        out = subprocess.check_output(
            [
                str(vswhere),
                "-latest",
                "-property",
                "installationPath",
            ],
            text=True,
            stderr=subprocess.DEVNULL,
        )
    except (subprocess.CalledProcessError, OSError):
        return None
    vs_root = Path(out.strip())
    cl_candidates = sorted(vs_root.rglob("cl.exe"))
    for cl in cl_candidates:
        if "Hostx64" in str(cl) or "Hostx86" in str(cl):
            return str(cl)
    return str(cl_candidates[0]) if cl_candidates else None


def _ensure_msvc_on_path() -> bool:
    """Ensure the MSVC ``cl.exe`` directory is on ``PATH`` (Windows only).

    Returns ``True`` if ``cl.exe`` was found and its directory was added to
    ``PATH`` (or was already there).  Returns ``False`` on non-Windows or
    when no installation is found.
    """
    cl = _find_msvc_cl()
    if cl is None:
        return False
    cl_dir = str(Path(cl).parent)
    current = os.environ.get("PATH", "")
    if cl_dir not in current:
        os.environ["PATH"] = cl_dir + os.pathsep + current
    return True
