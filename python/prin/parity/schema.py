"""Canonical schema for the PRIN golden-trajectory corpus.

A corpus is a collection of deterministic oscillator-trajectory cases
generated from a reference implementation (PRINet 3.0.0). Each case
contains the initial oscillator state, the final state after a fixed
number of integration steps, and a per-step trajectory, together with all
parameters needed to reproduce it.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum
from pathlib import Path
from typing import Any

import numpy as np
from numpy.typing import NDArray

CORPUS_SCHEMA_VERSION: int = 1

# Tolerances from the parity program (project plan §5).
TRAJECTORY_RTOL: float = 1e-6
TRAJECTORY_ATOL: float = 1e-8
# Cross-platform PRINet/torch regeneration of the derived metric arrays
# (order parameter, mean phase coherence) exhibits reduction-order noise up to
# ~1e-9 relative between OS/torch builds; the corpus was authored on Windows
# torch and CI regenerates on Linux/macOS torch (plan amendment #16).
METRIC_RTOL: float = 1e-8
METRIC_ATOL: float = 1e-12


def _validate_str(value: object, name: str) -> str:
    """Return ``value`` as a string or raise ``CorpusValidationError``."""
    if not isinstance(value, str):
        raise CorpusValidationError(f"{name} must be a string, got {type(value)}")
    return value


def _validate_int(value: object, name: str) -> int:
    """Return ``value`` as an integer or raise ``CorpusValidationError``."""
    if not isinstance(value, int) or isinstance(value, bool):
        raise CorpusValidationError(f"{name} must be an integer, got {type(value)}")
    return value


def _validate_float(value: object, name: str) -> float:
    """Return ``value`` as a float or raise ``CorpusValidationError``."""
    if isinstance(value, int) and not isinstance(value, bool):
        return float(value)
    if not isinstance(value, float):
        raise CorpusValidationError(f"{name} must be a number, got {type(value)}")
    return value


class CorpusValidationError(ValueError):
    """Raised when a corpus case or manifest fails schema validation."""


class Quantity(StrEnum):
    """Quantity classes for tolerance-aware comparison."""

    TRAJECTORY = "trajectory"
    METRIC = "metric"
    CHAOTIC = "chaotic"


class Model(StrEnum):
    """Oscillator models covered by the golden corpus."""

    KURAMOTO = "kuramoto"
    HOPF = "hopf"
    STUART_LANDAU = "stuart_landau"


class Coupling(StrEnum):
    """Coupling modes used for reference cases."""

    MEAN_FIELD = "mean_field"
    FULL = "full"
    SPARSE_KNN = "sparse_knn"


class Integrator(StrEnum):
    """Basic integrators used for reference cases."""

    EULER = "euler"
    RK4 = "rk4"


@dataclass(frozen=True)
class CaseSpec:
    """Metadata describing one golden-trajectory case.

    Args:
        case_id: Stable, filesystem-safe identifier.
        model: Oscillator model name.
        coupling: Coupling mode name.
        integrator: Integration method name.
        n_oscillators: Number of oscillators ``N``.
        n_steps: Number of integration steps taken.
        dt: Timestep size.
        seed: Deterministic seed used to create the initial state.
        parameters: Model- and coupling-specific parameters.
        schema_version: Corpus schema version.
    """

    case_id: str
    model: str
    coupling: str
    integrator: str
    n_oscillators: int
    n_steps: int
    dt: float
    seed: int
    parameters: dict[str, object]
    schema_version: int = CORPUS_SCHEMA_VERSION

    def to_dict(self) -> dict[str, Any]:
        """Serialize this spec to a JSON-compatible dictionary."""
        return {
            "case_id": self.case_id,
            "model": self.model,
            "coupling": self.coupling,
            "integrator": self.integrator,
            "n_oscillators": self.n_oscillators,
            "n_steps": self.n_steps,
            "dt": self.dt,
            "seed": self.seed,
            "parameters": self.parameters,
            "schema_version": self.schema_version,
        }

    @classmethod
    def from_dict(cls, payload: dict[str, Any]) -> CaseSpec:
        """Deserialize and validate a case spec dictionary."""
        if not isinstance(payload, dict):
            raise CorpusValidationError("case spec must be a dictionary")
        parameters = payload.get("parameters")
        if not isinstance(parameters, dict):
            raise CorpusValidationError("case spec 'parameters' must be a dictionary")
        return cls(
            case_id=_validate_str(payload.get("case_id"), "case_id"),
            model=_validate_str(payload.get("model"), "model"),
            coupling=_validate_str(payload.get("coupling"), "coupling"),
            integrator=_validate_str(payload.get("integrator"), "integrator"),
            n_oscillators=_validate_int(payload.get("n_oscillators"), "n_oscillators"),
            n_steps=_validate_int(payload.get("n_steps"), "n_steps"),
            dt=_validate_float(payload.get("dt"), "dt"),
            seed=_validate_int(payload.get("seed"), "seed"),
            parameters={str(k): v for k, v in parameters.items()},
            schema_version=_validate_int(
                payload.get("schema_version", CORPUS_SCHEMA_VERSION),
                "schema_version",
            ),
        )


@dataclass(frozen=True)
class CaseArrays:
    """Numeric arrays for a single golden-trajectory case.

    Trajectory arrays have shape ``(n_steps + 1, N)`` with the initial state at
    index ``0``. ``order_parameter_traj`` and ``mean_phase_coherence_traj`` have
    shape ``(n_steps + 1,)``.
    """

    phase_init: NDArray[np.float64]
    amplitude_init: NDArray[np.float64]
    frequency_init: NDArray[np.float64]
    phase_final: NDArray[np.float64]
    amplitude_final: NDArray[np.float64]
    frequency_final: NDArray[np.float64]
    phase_traj: NDArray[np.float64]
    amplitude_traj: NDArray[np.float64]
    frequency_traj: NDArray[np.float64]
    order_parameter_traj: NDArray[np.float64]
    mean_phase_coherence_traj: NDArray[np.float64]

    _ARRAY_NAMES: tuple[str, ...] = (
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

    @property
    def n_oscillators(self) -> int:
        """Number of oscillators in this case."""
        return int(self.phase_init.shape[-1])

    @property
    def n_steps(self) -> int:
        """Number of recorded integration steps (trajectory length minus one)."""
        return int(self.phase_traj.shape[0]) - 1

    def to_npz(self, path: Path) -> None:
        """Write all arrays to a compressed ``.npz`` file."""
        np.savez_compressed(
            path,
            phase_init=self.phase_init,
            amplitude_init=self.amplitude_init,
            frequency_init=self.frequency_init,
            phase_final=self.phase_final,
            amplitude_final=self.amplitude_final,
            frequency_final=self.frequency_final,
            phase_traj=self.phase_traj,
            amplitude_traj=self.amplitude_traj,
            frequency_traj=self.frequency_traj,
            order_parameter_traj=self.order_parameter_traj,
            mean_phase_coherence_traj=self.mean_phase_coherence_traj,
        )

    @classmethod
    def from_npz(cls, path: Path) -> CaseArrays:
        """Load arrays from a ``.npz`` file."""
        with np.load(path) as data:
            return cls(
                phase_init=_require_f64(data["phase_init"], "phase_init"),
                amplitude_init=_require_f64(data["amplitude_init"], "amplitude_init"),
                frequency_init=_require_f64(data["frequency_init"], "frequency_init"),
                phase_final=_require_f64(data["phase_final"], "phase_final"),
                amplitude_final=_require_f64(
                    data["amplitude_final"], "amplitude_final"
                ),
                frequency_final=_require_f64(
                    data["frequency_final"], "frequency_final"
                ),
                phase_traj=_require_f64(data["phase_traj"], "phase_traj"),
                amplitude_traj=_require_f64(data["amplitude_traj"], "amplitude_traj"),
                frequency_traj=_require_f64(data["frequency_traj"], "frequency_traj"),
                order_parameter_traj=_require_f64(
                    data["order_parameter_traj"], "order_parameter_traj"
                ),
                mean_phase_coherence_traj=_require_f64(
                    data["mean_phase_coherence_traj"], "mean_phase_coherence_traj"
                ),
            )


def _require_f64(array: NDArray[Any], name: str) -> NDArray[np.float64]:
    """Return ``array`` as a float64 contiguous ndarray."""
    if not isinstance(array, np.ndarray):
        raise CorpusValidationError(f"{name} must be a NumPy array")
    return np.ascontiguousarray(array, dtype=np.float64)


def validate_case_arrays(spec: CaseSpec, arrays: CaseArrays) -> None:
    """Validate that ``arrays`` are consistent with ``spec``.

    Raises:
        CorpusValidationError: If any array has the wrong shape or dtype.
    """
    n = spec.n_oscillators
    steps = spec.n_steps
    expected_1d = {
        "phase_init": (n,),
        "amplitude_init": (n,),
        "frequency_init": (n,),
        "phase_final": (n,),
        "amplitude_final": (n,),
        "frequency_final": (n,),
    }
    expected_traj = {
        "phase_traj": (steps + 1, n),
        "amplitude_traj": (steps + 1, n),
        "frequency_traj": (steps + 1, n),
    }
    expected_scalar = {
        "order_parameter_traj": (steps + 1,),
        "mean_phase_coherence_traj": (steps + 1,),
    }
    for name, shape in {**expected_1d, **expected_traj, **expected_scalar}.items():
        arr = getattr(arrays, name)
        if arr.dtype != np.float64:
            raise CorpusValidationError(f"{name} must be float64, got {arr.dtype}")
        if arr.shape != shape:
            raise CorpusValidationError(
                f"{name} expected shape {shape}, got {arr.shape}"
            )


TOLERANCES: dict[Quantity, tuple[float, float]] = {
    Quantity.TRAJECTORY: (TRAJECTORY_RTOL, TRAJECTORY_ATOL),
    Quantity.METRIC: (METRIC_RTOL, METRIC_ATOL),
}


def get_tolerances(quantity: Quantity) -> tuple[float, float]:
    """Return ``(rtol, atol)`` for the given quantity class.

    Raises:
        CorpusValidationError: For ``Quantity.CHAOTIC``, which is not a
            pointwise comparison and must be handled by the caller.
    """
    if quantity == Quantity.CHAOTIC:
        raise CorpusValidationError(
            "chaotic quantities require a statistical comparison, not pointwise"
        )
    return TOLERANCES[quantity]


def case_quantity(model: str, array_name: str) -> Quantity:
    """Classify an array name for tolerance selection.

    Args:
        model: Oscillator model (unused, kept for future model-specific rules).
        array_name: Name of the array being compared.

    Returns:
        Quantity classification for the array.
    """
    _ = model
    if "order_parameter" in array_name or "coherence" in array_name:
        return Quantity.METRIC
    return Quantity.TRAJECTORY
