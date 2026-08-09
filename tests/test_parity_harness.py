"""Tests for ``prin.parity.harness``."""

from __future__ import annotations

import numpy as np
import pytest
from prin.parity.harness import (
    all_within_tolerance,
    assert_parity,
    compare_arrays,
    compare_case,
    compare_loaded_case,
    plant_deviation,
)
from prin.parity.schema import (
    CaseArrays,
    CaseSpec,
    Coupling,
    Integrator,
    Model,
    Quantity,
)


def _make_arrays(n: int = 4, steps: int = 2) -> CaseArrays:
    phase = np.linspace(0, 1, n, dtype=np.float64)
    return CaseArrays(
        phase_init=phase,
        amplitude_init=np.ones(n, dtype=np.float64),
        frequency_init=np.ones(n, dtype=np.float64),
        phase_final=phase,
        amplitude_final=np.ones(n, dtype=np.float64),
        frequency_final=np.ones(n, dtype=np.float64),
        phase_traj=np.stack([phase, phase, phase]),
        amplitude_traj=np.ones((steps + 1, n), dtype=np.float64),
        frequency_traj=np.ones((steps + 1, n), dtype=np.float64),
        order_parameter_traj=np.array([0.1, 0.2, 0.3], dtype=np.float64),
        mean_phase_coherence_traj=np.array([0.1, 0.2, 0.3], dtype=np.float64),
    )


def test_compare_arrays_passes_for_equal() -> None:
    """Identical arrays compare within tolerance."""
    arrays = _make_arrays()
    result = compare_arrays(
        arrays.phase_final, arrays.phase_final, "phase_final", "kuramoto"
    )
    assert result.within_tolerance
    assert result.max_abs_diff == 0.0
    assert result.array_name == "phase_final"
    assert result.quantity == Quantity.TRAJECTORY


def test_compare_arrays_fails_for_shape_mismatch() -> None:
    """Different shapes fail immediately."""
    a = _make_arrays(n=4).phase_final
    b = _make_arrays(n=8).phase_final
    result = compare_arrays(a, b, "phase_final", "kuramoto")
    assert not result.within_tolerance
    assert result.failed_count == a.size


def test_compare_case_passes_for_equal_arrays() -> None:
    """A case compared with itself is fully within tolerance."""
    arrays = _make_arrays()
    results = compare_case(arrays, arrays, "kuramoto")
    assert all_within_tolerance(results)


def test_plant_deviation_detected_by_harness() -> None:
    """A planted deviation exceeds the trajectory tolerance."""
    arrays = _make_arrays()
    perturbed = plant_deviation(arrays, magnitude=1e-3, array_name="phase_final")
    results = compare_case(arrays, perturbed, "kuramoto")
    assert not all_within_tolerance(results)
    phase_result = next(r for r in results if r.array_name == "phase_final")
    assert not phase_result.within_tolerance
    assert phase_result.max_abs_diff > 1e-8


def test_plant_deviation_does_not_mutate_reference() -> None:
    """``plant_deviation`` copies the reference arrays before perturbing."""
    arrays = _make_arrays()
    original = arrays.phase_final.copy()
    plant_deviation(arrays, magnitude=1e-3, array_name="phase_final")
    np.testing.assert_array_equal(arrays.phase_final, original)


def test_assert_parity_raises_on_divergence() -> None:
    """``assert_parity`` raises ``AssertionError`` for a planted deviation."""
    arrays = _make_arrays()
    perturbed = plant_deviation(arrays, magnitude=1e-3, array_name="amplitude_final")
    with pytest.raises(AssertionError, match="diverged"):
        assert_parity(arrays, perturbed, "kuramoto")


def test_harness_detects_planted_deviation_at_tolerance() -> None:
    """A deviation below the tolerance is not detected; above it is."""
    arrays = _make_arrays()
    small = plant_deviation(arrays, magnitude=1e-9, array_name="phase_final")
    results = compare_case(arrays, small, "kuramoto")
    assert all_within_tolerance(results)

    large = plant_deviation(arrays, magnitude=1e-7, array_name="phase_final")
    results = compare_case(arrays, large, "kuramoto")
    assert not all_within_tolerance(results)


def test_harness_uses_metric_tolerances_for_order_parameters() -> None:
    """Order parameters use the documented metric tolerance tier."""
    arrays = _make_arrays()
    perturbed = dict(
        (name, getattr(arrays, name).copy()) for name in CaseArrays._ARRAY_NAMES
    )
    perturbed["order_parameter_traj"][1] += 5e-7
    test = CaseArrays(**perturbed)
    result = compare_arrays(
        arrays.order_parameter_traj,
        test.order_parameter_traj,
        "order_parameter_traj",
        "kuramoto",
    )
    assert not result.within_tolerance
    assert result.quantity == Quantity.METRIC


def test_comparison_result_to_dict() -> None:
    """``ComparisonResult.to_dict`` serializes every field."""
    arrays = _make_arrays()
    result = compare_arrays(
        arrays.phase_final, arrays.phase_final, "phase_final", "kuramoto"
    )
    payload = result.to_dict()
    assert payload["array_name"] == "phase_final"
    assert payload["quantity"] == "trajectory"
    assert payload["within_tolerance"] is True
    assert payload["failed_count"] == 0


def test_compare_loaded_case_uses_spec_model() -> None:
    """``compare_loaded_case`` compares against the loaded spec's model."""
    from prin.parity.loader import LoadedCase

    arrays = _make_arrays()
    spec = CaseSpec(
        case_id="test",
        model=Model.KURAMOTO.value,
        coupling=Coupling.FULL.value,
        integrator=Integrator.RK4.value,
        n_oscillators=4,
        n_steps=2,
        dt=0.01,
        seed=0,
        parameters={},
    )
    loaded = LoadedCase(spec=spec, arrays=arrays)
    results = compare_loaded_case(loaded, arrays)
    assert all_within_tolerance(results)


def test_assert_parity_passes_for_equal_arrays() -> None:
    """``assert_parity`` returns without raising for identical arrays."""
    arrays = _make_arrays()
    assert_parity(arrays, arrays, "kuramoto")
