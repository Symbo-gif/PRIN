"""Hypothesis strategies for parity and differential testing.

These strategies generate valid oscillator-case parameters without reproducing
any reference numerics. They are used by the differential harness to produce
fuzzed inputs that can be evaluated against both PRINet 3.0 and the new PRIN
implementation.
"""

from __future__ import annotations

from typing import Any

from hypothesis import strategies as st

from .schema import Coupling, Integrator, Model


def model_strategy() -> st.SearchStrategy[str]:
    """Strategy selecting one of the three oscillator models."""
    return st.sampled_from([m.value for m in Model])


def coupling_strategy(model: str) -> st.SearchStrategy[str]:
    """Strategy selecting a coupling mode valid for ``model``."""
    if model == Model.STUART_LANDAU.value:
        return st.just(Coupling.FULL.value)
    return st.sampled_from([c.value for c in Coupling])


def integrator_strategy() -> st.SearchStrategy[str]:
    """Strategy selecting a basic integrator."""
    return st.sampled_from([i.value for i in Integrator])


def n_oscillators_strategy() -> st.SearchStrategy[int]:
    """Strategy for the number of oscillators."""
    return st.integers(min_value=8, max_value=64)


def n_steps_strategy() -> st.SearchStrategy[int]:
    """Strategy for the number of integration steps."""
    return st.integers(min_value=5, max_value=50)


def dt_strategy() -> st.SearchStrategy[float]:
    """Strategy for the integration timestep."""
    return st.floats(
        min_value=0.001,
        max_value=0.05,
        allow_nan=False,
        allow_infinity=False,
    )


def coupling_strength_strategy() -> st.SearchStrategy[float]:
    """Strategy for the global coupling strength."""
    return st.floats(
        min_value=0.1,
        max_value=4.0,
        allow_nan=False,
        allow_infinity=False,
    )


def seed_strategy() -> st.SearchStrategy[int]:
    """Strategy for deterministic random seeds."""
    return st.integers(min_value=0, max_value=2_147_483_647)


def _finite_floats(min_value: float, max_value: float) -> st.SearchStrategy[float]:
    """Return a finite float strategy on a closed interval."""
    return st.floats(
        min_value=min_value,
        max_value=max_value,
        allow_nan=False,
        allow_infinity=False,
    )


def model_parameters_strategy(
    model: str,
    coupling: str,
) -> st.SearchStrategy[dict[str, Any]]:
    """Strategy for model- and coupling-specific parameters."""
    params: dict[str, st.SearchStrategy[Any]] = {
        "coupling_strength": coupling_strength_strategy(),
    }
    if coupling == Coupling.SPARSE_KNN.value:
        params["sparse_k"] = st.one_of(
            st.none(),
            st.integers(min_value=2, max_value=12),
        )
    if model == Model.KURAMOTO.value:
        params["decay_rate"] = _finite_floats(0.0, 0.5)
        params["freq_adaptation_rate"] = _finite_floats(0.0, 0.05)
    elif model == Model.HOPF.value:
        params["bifurcation_param"] = _finite_floats(-0.5, 2.0)
        params["freq_adaptation_rate"] = _finite_floats(0.0, 0.05)
    elif model == Model.STUART_LANDAU.value:
        params["bifurcation_param"] = _finite_floats(-0.5, 2.0)
    return st.fixed_dictionaries(params)


def case_spec_strategy() -> st.SearchStrategy[dict[str, Any]]:
    """Composite strategy generating a complete case parameter dictionary."""

    @st.composite
    def _build(draw: Any) -> dict[str, Any]:
        """Draw a complete case-spec dictionary from the component strategies."""
        model = draw(model_strategy())
        coupling = draw(coupling_strategy(model))
        integrator = draw(integrator_strategy())
        return {
            "model": model,
            "coupling": coupling,
            "integrator": integrator,
            "n_oscillators": draw(n_oscillators_strategy()),
            "n_steps": draw(n_steps_strategy()),
            "dt": draw(dt_strategy()),
            "seed": draw(seed_strategy()),
            "parameters": draw(model_parameters_strategy(model, coupling)),
        }

    return _build()
