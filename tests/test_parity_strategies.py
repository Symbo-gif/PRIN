"""Tests for ``prin.parity.strategies``."""

from __future__ import annotations

from hypothesis import given
from prin.parity.schema import Coupling, Integrator, Model
from prin.parity.strategies import (
    case_spec_strategy,
    coupling_strategy,
    model_parameters_strategy,
    model_strategy,
)


def test_model_strategy_draws_valid_models() -> None:
    """``model_strategy`` only draws supported models."""
    valid = {m.value for m in Model}

    @given(model_strategy())
    def _check(value: str) -> None:
        assert value in valid

    _check()


def test_coupling_strategy_restricts_stuart_landau() -> None:
    """Stuart-Landau is only generated with full coupling."""

    @given(coupling_strategy(Model.STUART_LANDAU.value))
    def _check(value: str) -> None:
        assert value == Coupling.FULL.value

    _check()


@given(model_parameters_strategy(Model.KURAMOTO.value, Coupling.FULL.value))
def test_kuramoto_parameters_include_required_keys(params: dict) -> None:
    """Kuramoto full-coupling parameters include the expected keys."""
    assert "coupling_strength" in params
    assert "decay_rate" in params
    assert "freq_adaptation_rate" in params


@given(model_parameters_strategy(Model.HOPF.value, Coupling.SPARSE_KNN.value))
def test_hopf_sparse_parameters_include_sparse_k(params: dict) -> None:
    """Hopf sparse-kNN parameters may include ``sparse_k``."""
    assert "coupling_strength" in params
    assert "bifurcation_param" in params
    assert "freq_adaptation_rate" in params


@given(model_parameters_strategy(Model.STUART_LANDAU.value, Coupling.FULL.value))
def test_stuart_landau_parameters_restricted_to_full(params: dict) -> None:
    """Stuart-Landau only exposes the bifurcation parameter."""
    assert "coupling_strength" in params
    assert "bifurcation_param" in params
    assert "decay_rate" not in params
    assert "freq_adaptation_rate" not in params


@given(case_spec_strategy())
def test_case_spec_strategy_is_consistent(spec: dict) -> None:
    """Generated case specs are internally consistent."""
    assert spec["model"] in {m.value for m in Model}
    assert spec["integrator"] in {i.value for i in Integrator}
    assert spec["n_oscillators"] >= 8
    assert spec["n_steps"] >= 5
    assert spec["dt"] > 0.0
    assert "parameters" in spec
    if spec["model"] == Model.STUART_LANDAU.value:
        assert spec["coupling"] == Coupling.FULL.value
