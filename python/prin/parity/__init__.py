"""PRIN parity package: golden-trajectory corpus and differential harness.

This package contains no oscillator numerics. It provides the schema, loader,
manifest validator, and comparison harness used by the parity suite that runs
old (PRINet 3.0) and new (PRIN) implementations side-by-side.
"""

from __future__ import annotations

from .harness import (
    ComparisonResult,
    all_within_tolerance,
    assert_parity,
    compare_arrays,
    compare_case,
    compare_loaded_case,
    plant_deviation,
)
from .loader import CorpusLoader, LoadedCase
from .manifest import CorpusManifest, ManifestRecord, create_manifest, validate_manifest
from .schema import (
    CORPUS_SCHEMA_VERSION,
    TOLERANCES,
    TRAJECTORY_ATOL,
    TRAJECTORY_RTOL,
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
from .strategies import case_spec_strategy

__all__: list[str] = [
    "CORPUS_SCHEMA_VERSION",
    "TOLERANCES",
    "TRAJECTORY_ATOL",
    "TRAJECTORY_RTOL",
    "CaseArrays",
    "CaseSpec",
    "ComparisonResult",
    "CorpusLoader",
    "CorpusManifest",
    "CorpusValidationError",
    "Coupling",
    "Integrator",
    "LoadedCase",
    "ManifestRecord",
    "Model",
    "Quantity",
    "all_within_tolerance",
    "assert_parity",
    "case_quantity",
    "case_spec_strategy",
    "compare_arrays",
    "compare_case",
    "compare_loaded_case",
    "create_manifest",
    "get_tolerances",
    "plant_deviation",
    "validate_case_arrays",
    "validate_manifest",
]
