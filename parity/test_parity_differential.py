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
    """Reference self-consistency: PRINet 3.0 regenerates every corpus case.

    Regenerates each of the 504 golden cases with PRINet 3.0 itself
    (``parity.generate_corpus._run_case`` builds ``prinet`` models and
    metrics) and compares the regeneration with the stored corpus, which is
    also PRINet 3.0 output. No ``prin`` code runs on this path, so this test is
    evidence that the corpus has not drifted from its reference, not of PRIN
    parity. It is ``test_corpus_regenerates_identically`` extended to the whole
    corpus; both compare at the registered tolerances, which hold across
    platforms (amendments #16/#17).

    PRIN-vs-corpus parity over all 504 cases is
    ``parity/test_parity_prin_corpus.py``. This docstring previously claimed to
    validate "the full Python -> Rust -> reference pipeline"; EXP-001 finding
    EXP001-E5-F1 showed that claim was wrong, and the EXP-001 D1 correction
    fixed it.
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
