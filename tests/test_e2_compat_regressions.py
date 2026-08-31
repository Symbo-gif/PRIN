"""Focused regressions for 0144E2 compatibility behavior."""

from __future__ import annotations

import math

import pytest
import torch
from prin._torch_compat import (
    KuramotoOscillator,
    MultiRateIntegrator,
    OscillatorState,
    PhaseAmplitudeCoupling,
)
from prin.nn import (
    HierarchicalResonanceLayer,
    PhaseAmplitudeCouplingLayer,
    PhaseToRateConverter,
)

from benchmarks.phase1_statistical_hardening import (
    bayes_factor_interpretation,
    cliffs_delta_interpretation,
)
from benchmarks.phase2_scaling_analysis import _build_sa, _cliffs_delta, _gen


def test_float32_bridge_restores_dtype_and_gradient() -> None:
    """Float32 calls marshal through Rust float64 and restore Torch placement."""
    converter = PhaseToRateConverter(8, mode="soft", sparsity=0.25)
    phase = torch.linspace(0.0, 1.0, 8)
    amplitude = torch.ones(8, requires_grad=True)
    output = converter(phase, amplitude)
    output.square().sum().backward()
    assert output.dtype == torch.float32
    assert amplitude.grad is not None
    assert torch.isfinite(amplitude.grad).all()


def test_bridge_rejects_mixed_tensor_placement() -> None:
    """Mixed tensor dtypes fail instead of silently downcasting outputs."""
    converter = PhaseToRateConverter(8, mode="soft", sparsity=0.25)
    with pytest.raises(ValueError, match="must share dtype and device"):
        converter(
            torch.zeros(8, dtype=torch.float32), torch.ones(8, dtype=torch.float64)
        )


def test_multirate_step_uses_rust_vjp() -> None:
    """Multi-rate compatibility steps retain amplitude gradients."""
    state = OscillatorState.create_random(6, seed=42)
    amplitude = state.amplitude.clone().requires_grad_(True)
    differentiable = OscillatorState(state.phase, amplitude, state.frequency)
    output = MultiRateIntegrator(sub_steps=2).step(
        KuramotoOscillator(6, coupling_strength=1.5), differentiable, 0.001
    )
    output.amplitude.sum().backward()
    assert amplitude.grad is not None
    assert torch.isfinite(amplitude.grad).all()


def test_phase_offset_delegates_to_rust_pac_owner() -> None:
    """Non-zero PAC offsets execute the existing Rust dynamics primitive."""
    coupling = PhaseAmplitudeCoupling(modulation_depth=0.5)
    output = coupling.modulate(torch.zeros(3), torch.ones(4), phase_offset=math.pi)
    torch.testing.assert_close(output, torch.full((4,), 0.5))


def test_legacy_hierarchical_module_contracts_remain_visible() -> None:
    """Legacy parameter/property contracts coexist with Rust-backed forwards."""
    pac = PhaseAmplitudeCouplingLayer(initial_depth=0.4)
    assert pac.modulation_depth in list(pac.parameters())
    hierarchy = HierarchicalResonanceLayer(
        n_delta=1, n_theta=1, n_gamma=1, n_dims=3, n_steps=2
    )
    assert hierarchy.n_steps == 2
    output = hierarchy(torch.ones(1, 3))
    assert output.shape == (1, 3)


def test_statistical_interpretation_and_empty_effect_branches() -> None:
    """Restored statistical helpers cover every governed interpretation band."""
    assert cliffs_delta_interpretation(0.2) == "small"
    assert cliffs_delta_interpretation(0.4) == "medium"
    assert bayes_factor_interpretation(float("nan")) == "computation_error"
    assert bayes_factor_interpretation(50.0) == "very strong"
    assert bayes_factor_interpretation(20.0) == "strong"
    assert bayes_factor_interpretation(5.0) == "moderate"
    assert bayes_factor_interpretation(2.0) == "anecdotal"
    assert bayes_factor_interpretation(0.5) == "evidence_for_H0"
    assert _cliffs_delta([], [1.0]) == 0.0


def test_slot_adapter_tracks_and_rejects_phase_encoding() -> None:
    """Slot benchmark support delegates tracking while keeping APIs explicit."""
    adapter = _build_sa(42)
    sequences = _gen(1, n_objects=2, n_frames=2, base_seed=42)
    result = adapter.track_sequence(sequences[0].frames)
    assert 0.0 <= result["identity_preservation"] <= 1.0
    with pytest.raises(TypeError, match="only available for PhaseTracker"):
        adapter.encode(sequences[0].frames[0])
