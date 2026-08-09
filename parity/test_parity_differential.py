"""Differential parity tests against PRINet 3.0 on the golden corpus."""

from __future__ import annotations

from pathlib import Path

import pytest

from prin.parity.harness import assert_parity, compare_case, plant_deviation
from prin.parity.loader import CorpusLoader
from prin.parity.manifest import CorpusManifest, ManifestRecord
from prin.parity.schema import CaseArrays

prinet = pytest.importorskip("prinet")

from parity.generate_corpus import _run_case

pytestmark = [pytest.mark.parity, pytest.mark.slow]

_CORPUS_DIR = Path(__file__).resolve().parent / "corpus"


def _regenerate(record: ManifestRecord) -> CaseArrays:
    """Regenerate a single case against PRINet 3.0.0."""
    parameters = dict(record.parameters)
    _, arrays = _run_case(
        model=record.model,
        coupling=record.coupling,
        integrator=record.integrator,
        n_oscillators=record.n_oscillators,
        n_steps=record.n_steps,
        dt=record.dt,
        seed=record.seed,
        parameters=parameters,
    )
    return arrays


def _all_corpus_case_ids() -> list[str]:
    """Return every case ID from the corpus manifest."""
    manifest = CorpusManifest.from_json(_CORPUS_DIR / "manifest.json")
    return [record.case_id for record in manifest.cases]


# Representative smoke-test subset (5 cases).  Fast enough for local runs;
# the exhaustive 504-case parametrization below runs in CI.
_REPRESENTATIVE_CASES = [
    "kuramoto_mean_field_euler_n8_s20_dt0_005_K0_5_seed1000000",
    "kuramoto_full_rk4_n8_s20_dt0_005_K0_5_seed1300000",
    "hopf_sparse_knn_rk4_n8_s20_dt0_005_K0_5_seed2100000",
    "stuart_landau_full_euler_n8_s20_dt0_005_K0_5_seed2200000",
    "kuramoto_mean_field_euler_n16_s20_dt0_01_K1_seed1000022",
]


@pytest.mark.parametrize("case_id", _REPRESENTATIVE_CASES)
def test_corpus_regenerates_identically(case_id: str) -> None:
    """The reference implementation reproduces each stored case bit-for-bit."""
    loader = CorpusLoader(_CORPUS_DIR)
    loaded = loader.load(case_id)
    regenerated = _regenerate(loader.get_record(case_id))
    assert_parity(loaded.arrays, regenerated, loaded.spec.model)


@pytest.mark.parametrize("case_id", _all_corpus_case_ids())
def test_corpus_exhaustive_differential_parity(case_id: str) -> None:
    """Exhaustive differential parity: every corpus case against PRINet 3.0.

    Validates the full Python -> Rust -> reference pipeline for all 504
    golden-trajectory cases.  This is the end-to-end validation that
    complements the Rust-level parity tests (``parity_models.rs``,
    ``parity_integrators.rs``, etc.).
    """
    loader = CorpusLoader(_CORPUS_DIR)
    loaded = loader.load(case_id)
    regenerated = _regenerate(loader.get_record(case_id))
    assert_parity(loaded.arrays, regenerated, loaded.spec.model)


def test_harness_detects_planted_deviation_on_corpus() -> None:
    """The differential harness fails when a regenerated case is perturbed."""
    loader = CorpusLoader(_CORPUS_DIR)
    loaded = loader.load("kuramoto_mean_field_euler_n8_s20_dt0_005_K0_5_seed1000000")
    perturbed = plant_deviation(
        loaded.arrays,
        magnitude=1e-3,
        array_name="phase_final",
        seed=0,
    )
    results = compare_case(loaded.arrays, perturbed, loaded.spec.model)
    assert not all(result.within_tolerance for result in results)
