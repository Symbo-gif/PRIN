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

**DV-007 explained divergence.** PRINet 3.0 evaluates its Stuart-Landau and
mean-field derivatives in ``complex64`` inside a float64 model (Deferred
Validation item DV-007); PRIN evaluates them in float64. On those paths the
stored corpus carries float32 rounding that PRIN does not reproduce, and 19
cases breach the registered tolerance for that reason alone (EXP-001 H1). The
EXP-001 D1 correction established, to the campaign plan §10.4 item 3 standard,
that the stored arrays are the erroneous side there: an arbitrary-precision
evaluation of PRINet 3.0's own map puts PRIN within ``2e-15`` and the corpus
outside tolerance (``EVIDENCE/exp001-d1-s1/dv007-exactness-audit.json``). A
breach therefore passes only when the case is on a DV-007 path **and** PRIN
matches the reference re-evaluated with only those casts widened
(:func:`parity.prinet_f64.f64_corrected_reference`) at the same registered
tolerance — a positive demonstration that the breach is exactly DV-007 and
nothing else (the amendment #25 pattern). Any other breach fails the gate.
"""

from __future__ import annotations

from pathlib import Path

import pytest
from prin.parity.harness import ComparisonResult, compare_case
from prin.parity.loader import CorpusLoader
from prin.parity.manifest import CorpusManifest

pytest.importorskip("prinet")

from benchmarks.campaign.exp001_driver import run_prin_case, run_prinet_trajectory
from parity.prinet_f64 import f64_corrected_reference, on_dv007_path

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


def _describe(breaches: list[ComparisonResult]) -> str:
    return "; ".join(
        f"{r.array_name} max_abs_diff={r.max_abs_diff:.6e} "
        f"failed={r.failed_count}/{r.total_count}"
        for r in breaches
    )


@pytest.mark.parametrize("case_id", _all_corpus_case_ids())
def test_prin_reproduces_corpus_case(loader: CorpusLoader, case_id: str) -> None:
    """PRIN matches the stored case, or the breach is exactly DV-007."""
    loaded = loader.load(case_id)
    spec, stored = loaded.spec, loaded.arrays
    produced = run_prin_case(spec, stored)
    breaches = [
        result
        for result in compare_case(stored, produced, spec.model)
        if not result.within_tolerance
    ]
    if not breaches:
        return
    assert on_dv007_path(spec.model, spec.coupling), (
        f"PRIN diverges from the stored corpus off the DV-007 paths: "
        f"{_describe(breaches)}"
    )
    with f64_corrected_reference():
        corrected = run_prinet_trajectory(
            model=spec.model,
            coupling=spec.coupling,
            integrator=spec.integrator,
            n_oscillators=spec.n_oscillators,
            n_steps=spec.n_steps,
            dt=spec.dt,
            parameters=dict(spec.parameters),
            phase_init=stored.phase_init,
            amplitude_init=stored.amplitude_init,
            frequency_init=stored.frequency_init,
        )
    residual = [
        result
        for result in compare_case(corrected, produced, spec.model)
        if not result.within_tolerance
    ]
    assert not residual, (
        "PRIN's breach of the stored corpus is not explained by DV-007: it also "
        f"diverges from the float64-evaluated reference: {_describe(residual)}"
    )


def test_gate_covers_the_whole_corpus() -> None:
    """The parametrization is the full 504-case corpus, not a subset."""
    ids = _all_corpus_case_ids()
    assert len(ids) == len(set(ids)) == 504
