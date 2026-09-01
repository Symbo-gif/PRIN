"""Synchronization, coherence, spectral, energy, and chimera metrics.

All numerical authority lives in the compiled Rust core (``prin._prin_core``).
This module re-exports the Rust-backed metric functions for ergonomic Python
access.
"""

from __future__ import annotations

from typing import Any

import torch

from prin._prin_core import (
    bimodality_chimera_threshold,
    bimodality_index,
    build_phase_knn,
    chimera_index,
    default_chimera_threshold,
    discontinuity_measure,
    extract_concept_probabilities,
    kuramoto_order_parameter_complex,
    local_order_parameter,
    mean_phase_coherence,
    metastability,
    order_parameter_series,
    phase_coherence_matrix,
    power_spectral_density,
    sparse_mean_phase_coherence,
    sparse_synchronization_energy,
    strength_of_incoherence,
    strength_of_incoherence_temporal,
    synchronization_energy,
)
from prin._prin_core import (
    inter_frame_phase_correlation as _rust_inter_frame_phase_correlation,
)
from prin._torch_compat import (
    kuramoto_order_parameter as kuramoto_order_parameter,
)


def inter_frame_phase_correlation(
    phase_t: torch.Tensor, phase_t_prev: torch.Tensor
) -> torch.Tensor:
    """Inter-frame phase correlation — torch-compatible wrapper.

    Delegates the numerical work to the Rust
    ``prin._prin_core.inter_frame_phase_correlation`` owner; this wrapper
    handles torch↔numpy marshalling and batched inputs only.

    Args:
        phase_t: Current-frame phases. Shape ``(N,)`` or ``(B, N)``.
        phase_t_prev: Previous-frame phases. Same shape as ``phase_t``.

    Returns:
        Scalar tensor (1D input) or ``(B,)`` tensor (batched input).

    Raises:
        ValueError: Shape mismatch or empty tensors.
    """
    if phase_t.numel() == 0 or phase_t_prev.numel() == 0:
        raise ValueError("inter_frame_phase_correlation: empty tensor")
    if phase_t.shape != phase_t_prev.shape:
        raise ValueError(f"Shape mismatch: {phase_t.shape} vs {phase_t_prev.shape}")

    def _np(t: torch.Tensor) -> Any:
        """Marshal a tensor to a contiguous CPU float64 NumPy array."""
        return t.detach().to(dtype=torch.float64, device="cpu").contiguous().numpy()

    if phase_t.dim() == 1:
        result = _rust_inter_frame_phase_correlation(_np(phase_t), _np(phase_t_prev))
        return torch.tensor(result, dtype=phase_t.dtype, device=phase_t.device)

    results = []
    for i in range(phase_t.shape[0]):
        results.append(
            _rust_inter_frame_phase_correlation(_np(phase_t[i]), _np(phase_t_prev[i]))
        )
    return torch.tensor(results, dtype=phase_t.dtype, device=phase_t.device)


__all__ = [
    "bimodality_chimera_threshold",
    "bimodality_index",
    "build_phase_knn",
    "chimera_index",
    "default_chimera_threshold",
    "discontinuity_measure",
    "extract_concept_probabilities",
    "inter_frame_phase_correlation",
    "kuramoto_order_parameter",
    "kuramoto_order_parameter_complex",
    "local_order_parameter",
    "mean_phase_coherence",
    "metastability",
    "order_parameter_series",
    "phase_coherence_matrix",
    "power_spectral_density",
    "sparse_mean_phase_coherence",
    "sparse_synchronization_energy",
    "strength_of_incoherence",
    "strength_of_incoherence_temporal",
    "synchronization_energy",
]
