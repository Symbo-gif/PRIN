"""Differential parity tests against PRINet 3.0 on the golden corpus."""

from __future__ import annotations

from pathlib import Path

import pytest

from prin.parity.harness import assert_parity, compare_case, plant_deviation
from prin.parity.loader import CorpusLoader
from prin.parity.manifest import ManifestRecord
from prin.parity.schema import CaseArrays

prinet = pytest.importorskip("prinet")

from parity.generate_corpus import _run_case

pytestmark = [pytest.mark.parity, pytest.mark.slow]


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


@pytest.mark.parametrize(
    "case_id",
    [
        "kuramoto_mean_field_euler_n8_s20_dt0_005_K0_5_seed1000000",
        "kuramoto_full_rk4_n8_s20_dt0_005_K0_5_seed1300000",
        "hopf_sparse_knn_rk4_n8_s20_dt0_005_K0_5_seed2100000",
        "stuart_landau_full_euler_n8_s20_dt0_005_K0_5_seed2200000",
        "kuramoto_mean_field_euler_n16_s20_dt0_01_K1_seed1000022",
    ],
)
def test_corpus_regenerates_identically(case_id: str) -> None:
    """The reference implementation reproduces each stored case bit-for-bit."""
    root = Path(__file__).resolve().parent
    loader = CorpusLoader(root / "corpus")
    loaded = loader.load(case_id)
    regenerated = _regenerate(loader.get_record(case_id))
    assert_parity(loaded.arrays, regenerated, loaded.spec.model)


def test_harness_detects_planted_deviation_on_corpus() -> None:
    """The differential harness fails when a regenerated case is perturbed."""
    root = Path(__file__).resolve().parent
    loader = CorpusLoader(root / "corpus")
    loaded = loader.load("kuramoto_mean_field_euler_n8_s20_dt0_005_K0_5_seed1000000")
    perturbed = plant_deviation(
        loaded.arrays,
        magnitude=1e-3,
        array_name="phase_final",
        seed=0,
    )
    results = compare_case(loaded.arrays, perturbed, loaded.spec.model)
    assert not all(result.within_tolerance for result in results)
