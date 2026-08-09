"""Oscillator dynamics: state, models, integrators, coupling, and PAC.

All numerical authority lives in the compiled Rust core (``prin._prin_core``).
This module re-exports the Rust-backed types for ergonomic Python access.
"""

from __future__ import annotations

from prin._prin_core import (
    AMPLITUDE_MAX,
    AMPLITUDE_MIN,
    DERIV_CLAMP,
    SPARSE_EPS,
    TAU,
    AdaptiveResult,
    CouplingMode,
    EulerIntegrator,
    HopfOscillator,
    KuramotoOscillator,
    OscillatorState,
    PhaseAmplitudeCoupling,
    RK4Integrator,
    RK45Integrator,
    Seed,
    StateDerivatives,
    StuartLandauOscillator,
    Topology,
)

__all__ = [
    "AMPLITUDE_MAX",
    "AMPLITUDE_MIN",
    "DERIV_CLAMP",
    "SPARSE_EPS",
    "TAU",
    "AdaptiveResult",
    "CouplingMode",
    "EulerIntegrator",
    "HopfOscillator",
    "KuramotoOscillator",
    "OscillatorState",
    "PhaseAmplitudeCoupling",
    "RK4Integrator",
    "RK45Integrator",
    "Seed",
    "StateDerivatives",
    "StuartLandauOscillator",
    "Topology",
]
