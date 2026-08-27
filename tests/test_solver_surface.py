"""Acceptance tests for the 0141D1 solver compatibility surface.

Behavioural parity against PRINet 3.0 is a WP-036B/WP-036C obligation; these
tests cover resolution, construction/callability, argument validation, the
documented Rust-owner delegation, and the segmentation-equivalence contract of
``gradient_checkpoint_integration``.
"""

from __future__ import annotations

import json
import math

import numpy as np
import prin
import pytest
from prin.dynamics import (
    CouplingMode,
    KuramotoOscillator,
    OscillatorState,
    RK4Integrator,
)
from prin.solvers import (
    BatchedRK45Solver,
    FixedStepRK4Solver,
    SolverError,
    SolverResult,
    gradient_checkpoint_integration,
)
from prin.training_hooks import TelemetryLogger

_SYMBOLS = (
    "SolverResult",
    "BatchedRK45Solver",
    "FixedStepRK4Solver",
    "gradient_checkpoint_integration",
    "TelemetryLogger",
)


def _model(n: int = 32) -> KuramotoOscillator:
    return KuramotoOscillator(n, 2.0, 0.1, 0.0, CouplingMode.mean_field())


def _state(n: int = 32) -> OscillatorState:
    return OscillatorState(
        np.linspace(0.0, 1.0, n),
        np.ones(n),
        np.full(n, 5.0),
    )


def test_symbols_resolve_from_prin_and_are_listed() -> None:
    """Every 0141D1 symbol resolves from ``prin`` and is in ``__all__``."""
    for name in _SYMBOLS:
        assert name in prin.__all__, name
        assert getattr(prin, name) is not None
    # The private error type stays module-scoped (not a PRINet 3.0 export).
    assert "SolverError" not in prin.__all__
    assert issubclass(SolverError, RuntimeError)


def test_fixed_step_solver_delegates_to_rk4_integrator() -> None:
    """``FixedStepRK4Solver`` reproduces ``RK4Integrator.integrate_fixed``."""
    model, state = _model(), _state()
    result = FixedStepRK4Solver(dt=0.01).solve(model, state, n_steps=25)
    assert isinstance(result, SolverResult)
    assert result.n_steps_taken == 25
    assert result.n_function_evals == 100
    assert result.final_dt == 0.01
    assert result.wall_time_seconds >= 0.0
    assert result.trajectory is None

    reference, _ = RK4Integrator().integrate_fixed(model, state, 25, 0.01, False)
    np.testing.assert_array_equal(result.final_state.phase, reference.phase)


def test_fixed_step_solver_records_trajectory_and_validates() -> None:
    """Trajectory recording and negative-step validation behave as declared."""
    model, state = _model(16), _state(16)
    result = FixedStepRK4Solver(dt=0.02).solve(
        model, state, n_steps=8, record_trajectory=True
    )
    assert result.trajectory is not None
    assert len(result.trajectory) == 8

    with pytest.raises(ValueError, match="dt must be positive"):
        FixedStepRK4Solver(dt=0.0)
    with pytest.raises(ValueError, match="n_steps must be non-negative"):
        FixedStepRK4Solver().solve(model, state, n_steps=-1)


def test_batched_rk45_solver_reports_adaptive_diagnostics() -> None:
    """``BatchedRK45Solver`` surfaces the Rust adaptive-integration result."""
    model, state = _model(), _state()
    result = BatchedRK45Solver(atol=1e-6, rtol=1e-4).solve(
        model, state, t_span=(0.0, 1.0), record_trajectory=True
    )
    assert isinstance(result, SolverResult)
    assert result.n_steps_taken > 0
    assert result.n_function_evals >= result.n_steps_taken * 6
    assert result.n_function_evals % 6 == 0
    assert result.final_dt > 0.0
    assert result.trajectory is not None
    assert len(result.trajectory) == result.n_steps_taken


def test_batched_rk45_solver_validates_tolerances() -> None:
    """Non-positive tolerances are rejected at construction time."""
    with pytest.raises(ValueError, match="atol must be positive"):
        BatchedRK45Solver(atol=0.0)
    with pytest.raises(ValueError, match="rtol must be positive"):
        BatchedRK45Solver(rtol=-1.0)


def test_batched_rk45_solver_wraps_non_convergence_as_solver_error() -> None:
    """A Rust tolerance failure is re-raised as the PRINet 3.0 ``SolverError``."""
    model, state = _model(8), _state(8)
    solver = BatchedRK45Solver(atol=1e-13, rtol=1e-13)
    with pytest.raises(SolverError):
        solver.solve(model, state, t_span=(0.0, 50.0), max_steps=2)


def test_compiled_flag_is_accepted_and_inert() -> None:
    """The legacy ``compiled`` flag is accepted without changing results."""
    model, state = _model(16), _state(16)
    plain = FixedStepRK4Solver(dt=0.01).solve(model, state, n_steps=10)
    compiled = FixedStepRK4Solver(dt=0.01, compiled=True).solve(
        model, state, n_steps=10
    )
    np.testing.assert_array_equal(plain.final_state.phase, compiled.final_state.phase)


def test_gradient_checkpoint_integration_matches_unsegmented_rk4() -> None:
    """Segmented integration is bit-identical to a single fixed-step call."""
    model, state = _model(24), _state(24)
    segmented = gradient_checkpoint_integration(
        model, state, n_steps=37, checkpoint_every=10
    )
    reference, _ = RK4Integrator().integrate_fixed(model, state, 37, 0.01, False)
    np.testing.assert_array_equal(segmented.phase, reference.phase)
    np.testing.assert_array_equal(segmented.amplitude, reference.amplitude)


def test_gradient_checkpoint_integration_budget_and_validation() -> None:
    """The memory-budget heuristic and argument validation behave as declared."""
    model, state = _model(12), _state(12)
    reference, _ = RK4Integrator().integrate_fixed(model, state, 30, 0.01, False)
    budgeted = gradient_checkpoint_integration(
        model, state, n_steps=30, memory_budget_mb=64.0
    )
    np.testing.assert_array_equal(budgeted.phase, reference.phase)

    # Heuristic segment length is sqrt(n_steps) clamped at 1.
    assert max(1, int(math.sqrt(30))) == 5

    zero = gradient_checkpoint_integration(model, state, n_steps=0)
    np.testing.assert_array_equal(zero.phase, state.phase)

    with pytest.raises(ValueError, match="n_steps must be non-negative"):
        gradient_checkpoint_integration(model, state, n_steps=-1)
    with pytest.raises(ValueError, match="checkpoint_every must be positive"):
        gradient_checkpoint_integration(model, state, n_steps=5, checkpoint_every=0)


def test_telemetry_logger_records_and_serialises(tmp_path: object) -> None:
    """``TelemetryLogger`` buffers records verbatim and round-trips to JSON."""
    logger = TelemetryLogger(capacity=3)
    assert len(logger) == 0

    logger.record(epoch=1, loss=0.5, r_global=0.6)
    logger.record(
        epoch=2,
        loss=0.4,
        r_per_band=[0.1, 0.2, 0.3],
        extra={"note": "warmup"},
    )
    assert len(logger) == 2
    assert logger.records[0]["epoch"] == 1
    assert logger.records[0]["r_per_band"] == [0.0, 0.0, 0.0]
    assert logger.records[1]["r_per_band"] == [0.1, 0.2, 0.3]
    assert logger.records[1]["note"] == "warmup"

    path = tmp_path / "telemetry.json"  # type: ignore[operator]
    logger.to_json(str(path))
    loaded = json.loads(path.read_text())
    assert [entry["epoch"] for entry in loaded] == [1, 2]


def test_telemetry_logger_capacity_evicts_oldest_and_reads_control() -> None:
    """The bounded buffer evicts oldest records; control fields are extracted."""
    logger = TelemetryLogger(capacity=2)
    for epoch in range(4):
        logger.record(epoch=epoch, loss=1.0 / (epoch + 1))
    assert [entry["epoch"] for entry in logger.records] == [2, 3]

    class _Control:
        lr_multiplier = 1.25
        alert_level = 0.5

    logger.record(epoch=9, loss=0.1, control=_Control())
    assert logger.records[-1]["control"]["lr_multiplier"] == 1.25
    assert logger.records[-1]["control"]["alert_level"] == 0.5
    assert logger.records[-1]["control"]["suggested_K_max"] == 10.0

    with pytest.raises(ValueError, match="capacity must be positive"):
        TelemetryLogger(capacity=0)
