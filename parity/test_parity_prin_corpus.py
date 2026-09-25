"""Full-corpus PRIN-vs-corpus differential gate (EXP-001 D1, finding EXP001-E5-F1).

``test_parity_differential.py::test_corpus_exhaustive_differential_parity``
regenerates each golden case with PRINet 3.0 and compares it with the stored
corpus: a reference self-consistency check that never runs PRIN. This module
is the gate EXP001-E5-F1 found missing. It integrates **PRIN's** Rust dynamics
core from every stored initial state — through the same execution path EXP-001
H1 used (``benchmarks.campaign.exp001_driver.run_prin_case``) — and compares
every array with the stored PRINet 3.0 reference at the registered corpus
tolerances (trajectories ``rtol=1e-6, atol=1e-8``; metrics ``rtol=2e-6,
atol=1e-12``). All 504 cases run; none is sampled, skipped, or given a wider
tolerance.
"""

from __future__ import annotations

from pathlib import Path

import pytest
from prin.parity.harness import compare_case
from prin.parity.loader import CorpusLoader
from prin.parity.manifest import CorpusManifest

pytest.importorskip("prinet")

from benchmarks.campaign.exp001_driver import run_prin_case

pytestmark = [pytest.mark.parity, pytest.mark.slow]

_CORPUS_DIR = Path(__file__).resolve().parent / "corpus"


def _all_corpus_case_ids() -> list[str]:
    """Return every case ID from the corpus manifest."""
    manifest = CorpusManifest.from_json(_CORPUS_DIR / "manifest.json")
    return [record.case_id for record in manifest.cases]


@pytest.fixture(scope="module")
def loader() -> CorpusLoader:
    """Load the golden corpus once per module (per xdist worker)."""
    return CorpusLoader(_CORPUS_DIR)


@pytest.mark.parametrize("case_id", _all_corpus_case_ids())
def test_prin_reproduces_corpus_case(loader: CorpusLoader, case_id: str) -> None:
    """PRIN re-integrated from the stored initial state matches the stored case."""
    loaded = loader.load(case_id)
    produced = run_prin_case(loaded.spec, loaded.arrays)
    breaches = [
        result
        for result in compare_case(loaded.arrays, produced, loaded.spec.model)
        if not result.within_tolerance
    ]
    assert not breaches, "PRIN diverges from the stored corpus: " + "; ".join(
        f"{r.array_name} max_abs_diff={r.max_abs_diff:.6e} "
        f"failed={r.failed_count}/{r.total_count}"
        for r in breaches
    )


def test_gate_covers_the_whole_corpus() -> None:
    """The parametrization is the full 504-case corpus, not a subset."""
    ids = _all_corpus_case_ids()
    assert len(ids) == len(set(ids)) == 504
