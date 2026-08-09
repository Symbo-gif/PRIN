"""Synchronization, coherence, spectral, energy, and chimera metrics.

All numerical authority lives in the compiled Rust core (``prin._prin_core``).
This module re-exports the Rust-backed metric functions for ergonomic Python
access.
"""

from __future__ import annotations

from prin._prin_core import (
    bimodality_chimera_threshold,
    bimodality_index,
    build_phase_knn,
    chimera_index,
    default_chimera_threshold,
    discontinuity_measure,
    extract_concept_probabilities,
    inter_frame_phase_correlation,
    kuramoto_order_parameter,
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
