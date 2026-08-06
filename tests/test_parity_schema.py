"""Tests for ``prin.parity.schema``."""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pytest
from prin.parity.schema import (
    CORPUS_SCHEMA_VERSION,
    TOLERANCES,
    CaseArrays,
    CaseSpec,
    CorpusValidationError,
    Coupling,
    Integrator,
    Model,
    Quantity,
    case_quantity,
    get_tolerances,
    validate_case_arrays,
)


def test_tolerances_match_parity_program() -> None:
    """The documented tolerances are exposed exactly."""
    assert TOLERANCES[Quantity.TRAJECTORY] == (1e-6, 1e-8)
    assert TOLERANCES[Quantity.METRIC] == (1e-10, 1e-12)


def test_get_tolerances_rejects_chaotic() -> None:
    """Chaotic quantities cannot be compared pointwise."""
    with pytest.raises(CorpusValidationError, match="statistical comparison"):
        get_tolerances(Quantity.CHAOTIC)


def test_case_quantity_classifies_arrays() -> None:
    """Array names map to the correct quantity class."""
    assert case_quantity("kuramoto", "phase_final") == Quantity.TRAJECTORY
    assert case_quantity("kuramoto", "order_parameter_traj") == Quantity.METRIC
    assert case_quantity("hopf", "mean_phase_coherence_traj") == Quantity.METRIC


def _minimal_arrays(n: int = 4, steps: int = 2) -> CaseArrays:
    rng = np.random.default_rng(0)
    phase_init = rng.random(n)
    amplitude_init = np.ones(n)
    frequency_init = rng.random(n)
    return CaseArrays(
        phase_init=phase_init,
        amplitude_init=amplitude_init,
        frequency_init=frequency_init,
        phase_final=phase_init + 0.01,
        amplitude_final=amplitude_init,
        frequency_final=frequency_init,
        phase_traj=np.stack([phase_init, phase_init + 0.005, phase_init + 0.01]),
        amplitude_traj=np.stack([amplitude_init, amplitude_init, amplitude_init]),
        frequency_traj=np.stack([frequency_init, frequency_init, frequency_init]),
        order_parameter_traj=np.array([0.0, 0.1, 0.2]),
        mean_phase_coherence_traj=np.array([0.0, 0.1, 0.2]),
    )


def test_case_arrays_roundtrip(tmp_path: Path) -> None:
    """``CaseArrays`` serializes to and from ``.npz`` as float64."""
    arrays = _minimal_arrays()
    path = tmp_path / "case.npz"
    arrays.to_npz(path)
    loaded = CaseArrays.from_npz(path)
    assert loaded.n_oscillators == arrays.n_oscillators
    assert loaded.n_steps == arrays.n_steps
    for name in (
        "phase_init",
        "amplitude_init",
        "frequency_init",
        "phase_final",
        "amplitude_final",
        "frequency_final",
    ):
        np.testing.assert_array_equal(getattr(loaded, name), getattr(arrays, name))
    assert loaded.phase_traj.dtype == np.float64


def test_validate_case_arrays_accepts_valid_case() -> None:
    """A matching spec and arrays pass validation."""
    arrays = _minimal_arrays(n=4, steps=2)
    spec = CaseSpec(
        case_id="test",
        model=Model.KURAMOTO.value,
        coupling=Coupling.MEAN_FIELD.value,
        integrator=Integrator.RK4.value,
        n_oscillators=4,
        n_steps=2,
        dt=0.01,
        seed=0,
        parameters={"coupling_strength": 1.0},
    )
    validate_case_arrays(spec, arrays)


def test_validate_case_arrays_rejects_mismatched_shape() -> None:
    """A shape mismatch raises ``CorpusValidationError``."""
    arrays = _minimal_arrays(n=4, steps=2)
    spec = CaseSpec(
        case_id="test",
        model=Model.KURAMOTO.value,
        coupling=Coupling.MEAN_FIELD.value,
        integrator=Integrator.RK4.value,
        n_oscillators=8,
        n_steps=2,
        dt=0.01,
        seed=0,
        parameters={"coupling_strength": 1.0},
    )
    with pytest.raises(CorpusValidationError, match="expected shape"):
        validate_case_arrays(spec, arrays)


def test_validate_case_arrays_rejects_non_float64() -> None:
    """A non-float64 array raises ``CorpusValidationError``."""
    arrays = _minimal_arrays(n=4, steps=2)
    arrays = CaseArrays(
        **{
            name: getattr(arrays, name).astype(np.float32)
            for name in (
                "phase_init",
                "amplitude_init",
                "frequency_init",
                "phase_final",
                "amplitude_final",
                "frequency_final",
                "phase_traj",
                "amplitude_traj",
                "frequency_traj",
                "order_parameter_traj",
                "mean_phase_coherence_traj",
            )
        }
    )
    spec = CaseSpec(
        case_id="test",
        model=Model.KURAMOTO.value,
        coupling=Coupling.MEAN_FIELD.value,
        integrator=Integrator.RK4.value,
        n_oscillators=4,
        n_steps=2,
        dt=0.01,
        seed=0,
        parameters={"coupling_strength": 1.0},
    )
    with pytest.raises(CorpusValidationError, match="must be float64"):
        validate_case_arrays(spec, arrays)


def test_case_spec_from_dict_validates() -> None:
    """``CaseSpec.from_dict`` accepts a valid dictionary."""
    spec = CaseSpec(
        case_id="c",
        model=Model.KURAMOTO.value,
        coupling=Coupling.FULL.value,
        integrator=Integrator.EULER.value,
        n_oscillators=10,
        n_steps=5,
        dt=0.01,
        seed=1,
        parameters={"coupling_strength": 1.0},
    )
    roundtrip = CaseSpec.from_dict(spec.to_dict())
    assert roundtrip == spec


def test_case_spec_from_dict_rejects_missing_field() -> None:
    """``CaseSpec.from_dict`` fails closed on missing or wrong types."""
    with pytest.raises(CorpusValidationError, match="case_id"):
        CaseSpec.from_dict({"parameters": {}})


def test_case_spec_schema_version_default() -> None:
    """A missing schema version defaults to the current version."""
    payload = {
        "case_id": "c",
        "model": "kuramoto",
        "coupling": "full",
        "integrator": "euler",
        "n_oscillators": 4,
        "n_steps": 2,
        "dt": 0.01,
        "seed": 1,
        "parameters": {},
    }
    spec = CaseSpec.from_dict(payload)
    assert spec.schema_version == CORPUS_SCHEMA_VERSION


def test_case_spec_from_dict_rejects_non_dict() -> None:
    """``CaseSpec.from_dict`` fails closed on non-dictionaries."""
    with pytest.raises(CorpusValidationError, match="must be a dictionary"):
        CaseSpec.from_dict("not-a-dict")  # type: ignore[arg-type]


def test_case_spec_from_dict_rejects_non_dict_parameters() -> None:
    """``CaseSpec.from_dict`` rejects a non-dictionary ``parameters`` field."""
    with pytest.raises(CorpusValidationError, match=r"parameters.*dictionary"):
        CaseSpec.from_dict(
            {
                "case_id": "c",
                "model": "kuramoto",
                "coupling": "full",
                "integrator": "euler",
                "n_oscillators": 4,
                "n_steps": 2,
                "dt": 0.01,
                "seed": 1,
                "parameters": [1.0],
            }
        )


def test_case_spec_from_dict_rejects_bool_integer() -> None:
    """Boolean values are rejected for integer fields."""
    payload = {
        "case_id": "c",
        "model": "kuramoto",
        "coupling": "full",
        "integrator": "euler",
        "n_oscillators": 4,
        "n_steps": True,
        "dt": 0.01,
        "seed": 1,
        "parameters": {},
    }
    with pytest.raises(CorpusValidationError, match="n_steps must be an integer"):
        CaseSpec.from_dict(payload)


def test_case_spec_from_dict_accepts_integer_dt() -> None:
    """Integer ``dt`` values are coerced to ``float`` as expected."""
    payload = {
        "case_id": "c",
        "model": "kuramoto",
        "coupling": "full",
        "integrator": "euler",
        "n_oscillators": 4,
        "n_steps": 2,
        "dt": 1,
        "seed": 1,
        "parameters": {},
    }
    spec = CaseSpec.from_dict(payload)
    assert spec.dt == 1.0


def test_case_spec_from_dict_rejects_non_numeric_dt() -> None:
    """Non-numeric ``dt`` values are rejected."""
    payload = {
        "case_id": "c",
        "model": "kuramoto",
        "coupling": "full",
        "integrator": "euler",
        "n_oscillators": 4,
        "n_steps": 2,
        "dt": "bad",
        "seed": 1,
        "parameters": {},
    }
    with pytest.raises(CorpusValidationError, match="dt must be a number"):
        CaseSpec.from_dict(payload)


def test_require_f64_rejects_non_ndarray() -> None:
    """``_require_f64`` rejects values that are not NumPy arrays."""
    from prin.parity.schema import _require_f64

    with pytest.raises(CorpusValidationError, match="must be a NumPy array"):
        _require_f64([1.0, 2.0], "phase_init")  # type: ignore[arg-type]
