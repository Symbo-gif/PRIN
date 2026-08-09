"""Differential testing harness for the PRIN golden-trajectory corpus."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import numpy as np
from numpy.typing import NDArray

from .loader import LoadedCase
from .schema import (
    CaseArrays,
    Quantity,
    case_quantity,
    get_tolerances,
)


@dataclass(frozen=True)
class ComparisonResult:
    """Result of comparing one pair of arrays."""

    array_name: str
    quantity: Quantity
    within_tolerance: bool
    max_abs_diff: float
    max_rel_diff: float
    failed_count: int
    total_count: int

    def to_dict(self) -> dict[str, Any]:
        """Serialize the result for reports."""
        return {
            "array_name": self.array_name,
            "quantity": self.quantity.value,
            "within_tolerance": self.within_tolerance,
            "max_abs_diff": self.max_abs_diff,
            "max_rel_diff": self.max_rel_diff,
            "failed_count": self.failed_count,
            "total_count": self.total_count,
        }


def _compare_pair(
    reference: NDArray[np.float64],
    test: NDArray[np.float64],
    rtol: float,
    atol: float,
) -> tuple[bool, float, float, int]:
    """Compare two float64 arrays and return allclose-style statistics."""
    diff = np.abs(reference - test)
    with np.errstate(invalid="ignore", divide="ignore"):
        rel = diff / (np.abs(reference) + 1e-300)
    close = np.isclose(reference, test, rtol=rtol, atol=atol)
    within = bool(np.all(close))
    max_abs = float(np.nanmax(diff))
    max_rel = float(np.nanmax(rel))
    failed = int(np.size(close) - int(np.count_nonzero(close)))
    return within, max_abs, max_rel, failed


def compare_arrays(
    reference: NDArray[np.float64],
    test: NDArray[np.float64],
    array_name: str,
    model: str,
) -> ComparisonResult:
    """Compare a single named array against a reference.

    Args:
        reference: Reference float64 array.
        test: Test float64 array.
        array_name: Name of the array, used for quantity classification.
        model: Oscillator model, used for model-specific tolerance rules.

    Returns:
        ComparisonResult with allclose statistics.
    """
    if reference.shape != test.shape:
        return ComparisonResult(
            array_name=array_name,
            quantity=case_quantity(model, array_name),
            within_tolerance=False,
            max_abs_diff=float("inf"),
            max_rel_diff=float("inf"),
            failed_count=int(np.size(reference)),
            total_count=int(np.size(reference)),
        )
    quantity = case_quantity(model, array_name)
    rtol, atol = get_tolerances(quantity)
    within, max_abs, max_rel, failed = _compare_pair(reference, test, rtol, atol)
    return ComparisonResult(
        array_name=array_name,
        quantity=quantity,
        within_tolerance=within,
        max_abs_diff=max_abs,
        max_rel_diff=max_rel,
        failed_count=failed,
        total_count=int(reference.size),
    )


def compare_case(
    reference: CaseArrays,
    test: CaseArrays,
    model: str,
) -> list[ComparisonResult]:
    """Compare all arrays in a test case against a reference.

    Args:
        reference: Reference arrays from the corpus.
        test: Arrays produced by the implementation under test.
        model: Oscillator model name.

    Returns:
        List of per-array comparison results.
    """
    results: list[ComparisonResult] = []
    for name in CaseArrays._ARRAY_NAMES:
        ref = getattr(reference, name)
        tst = getattr(test, name)
        results.append(compare_arrays(ref, tst, name, model))
    return results


def compare_loaded_case(
    loaded: LoadedCase,
    test: CaseArrays,
) -> list[ComparisonResult]:
    """Compare ``test`` arrays against the reference in ``loaded``."""
    return compare_case(loaded.arrays, test, loaded.spec.model)


def all_within_tolerance(results: list[ComparisonResult]) -> bool:
    """Return ``True`` if every comparison is within tolerance."""
    return all(result.within_tolerance for result in results)


def plant_deviation(
    arrays: CaseArrays,
    magnitude: float = 1e-3,
    array_name: str = "phase_final",
    seed: int = 0,
) -> CaseArrays:
    """Return a shallow copy of ``arrays`` with a planted numerical deviation.

    This is used to verify that the differential harness fails when the
    implementation under test diverges from the reference.

    Args:
        arrays: Reference arrays to perturb.
        magnitude: Maximum absolute perturbation.
        array_name: Name of the array to perturb.
        seed: Deterministic seed for the perturbation.

    Returns:
        A new ``CaseArrays`` with the perturbation applied.
    """
    rng = np.random.default_rng(seed)
    field = getattr(arrays, array_name).copy()
    perturbation = rng.uniform(-magnitude, magnitude, size=field.shape)
    new = {name: getattr(arrays, name).copy() for name in CaseArrays._ARRAY_NAMES}
    new[array_name] = field + perturbation
    return CaseArrays(**new)


def assert_parity(
    reference: CaseArrays,
    test: CaseArrays,
    model: str,
) -> None:
    """Assert that ``test`` matches ``reference`` within documented tolerances.

    Raises:
        AssertionError: With a structured message if any array diverges.
    """
    results = compare_case(reference, test, model)
    if all_within_tolerance(results):
        return
    failures = [r for r in results if not r.within_tolerance]
    lines = [f"{len(failures)} array(s) diverged from reference:"]
    for result in failures:
        lines.append(
            f"  {result.array_name}: max_abs_diff={result.max_abs_diff:.6e}, "
            f"max_rel_diff={result.max_rel_diff:.6e}, "
            f"failed={result.failed_count}/{result.total_count}"
        )
    raise AssertionError("\n".join(lines))
