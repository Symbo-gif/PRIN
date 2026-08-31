"""Focused regression tests for the 0144E1 internal compatibility facade."""

from __future__ import annotations

import pytest
import torch
from prin._torch_compat import (
    BatchedRK45Solver,
    KuramotoOscillator,
    OscillatorState,
    SolverError,
    extract_concept_probabilities,
    gradient_checkpoint_integration,
)
from prin.tensor import DecompositionError, DimensionsMismatchError, PolyadicTensor


def test_state_batch_and_band_marshalling_paths() -> None:
    """Batched synchronized states and optional bands retain their API shape."""
    state = OscillatorState.create_synchronized(4, batch_size=2)
    assert state.phase.shape == (2, 4)
    state.freq_band = torch.tensor([[0, 0, 1, 1], [0, 0, 1, 1]])
    assert state.n_bands == 2
    assert state.clone().freq_band is not state.freq_band


def test_concept_probabilities_delegate_to_rust() -> None:
    """Concept extraction returns a finite Rust-owned probability vector."""
    probabilities = extract_concept_probabilities(
        torch.ones(8),
        torch.zeros(8),
        torch.tensor([0.0, 4.0]),
        torch.tensor([1.0, 1.0]),
    )
    assert probabilities.shape == (2,)
    assert torch.isfinite(probabilities).all()


def test_model_unconfigured_matrix_and_euler_integration_errors() -> None:
    """Compatibility-only model branches preserve typed legacy failures."""
    model = KuramotoOscillator(4)
    state = OscillatorState.create_synchronized(4)
    with pytest.raises(AttributeError, match="no custom coupling"):
        _ = model.coupling_matrix
    final, trajectory = model.integrate(state, 2, method="euler")
    assert trajectory is None
    assert final.phase.shape == (4,)
    with pytest.raises(ValueError, match="Unknown integration method"):
        model.integrate(state, 1, method="bogus")


def test_solver_failure_and_checkpoint_validation() -> None:
    """Adaptive failures and segmented-integration guards stay typed."""
    model = KuramotoOscillator(4)
    state = OscillatorState.create_random(4, seed=42)
    with pytest.raises(SolverError):
        BatchedRK45Solver(atol=1e-13, rtol=1e-13).solve(
            model, state, t_span=(0.0, 50.0), max_steps=1
        )
    with pytest.raises(ValueError, match="n_steps must be non-negative"):
        gradient_checkpoint_integration(model, state, -1)
    with pytest.raises(ValueError, match="checkpoint_every must be positive"):
        gradient_checkpoint_integration(model, state, 1, checkpoint_every=0)


def test_batched_adaptive_trajectory_uses_common_available_length() -> None:
    """Batched adaptive trajectories never index beyond a row's history."""
    model = KuramotoOscillator(4)
    state = OscillatorState.create_random(4, batch_size=2, seed=42)
    state.phase[1] = torch.tensor([0.0, 0.1, 3.0, 5.0])
    state.amplitude[1] = torch.tensor([0.1, 0.5, 2.0, 4.0])
    result = BatchedRK45Solver(atol=1e-6, rtol=1e-4).solve(
        model, state, t_span=(0.0, 0.2), record_trajectory=True
    )
    assert result.trajectory is not None
    assert len(result.trajectory) == result.n_steps_taken
    assert all(item.phase.shape == (2, 4) for item in result.trajectory)


def test_tensor_error_paths_are_compatibly_typed() -> None:
    """New Rust-backed tensor helpers retain reference exception contracts."""
    decomposition = PolyadicTensor((3, 3), 2)
    with pytest.raises(DimensionsMismatchError, match="Expected shape"):
        decomposition.reconstruction_error(torch.ones(2, 2))
    with pytest.raises(DecompositionError, match="No decomposition"):
        decomposition.reconstruction_error(torch.ones(3, 3))
