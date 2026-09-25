"""Validation of the test-local float64 PRINet 3.0 instrument (``prinet_f64``).

The EXP-001 D1 gates use :func:`parity.prinet_f64.f64_corrected_reference` as
a measuring instrument, so it is checked here: it must leave every non-DV-007
path bit-identical, visibly change every DV-007 path, and restore the archived
methods on exit. Every comparison is against a native regeneration on the same
host, never against the stored corpus: the corpus was authored on Windows and
PRINet 3.0's torch arithmetic is not bit-reproducible across platforms
(amendments #16/#17).
"""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pytest
from prin.parity.manifest import CorpusManifest, ManifestRecord
from prin.parity.schema import CaseArrays

pytest.importorskip("prinet")

from parity.generate_corpus import _run_case
from parity.prinet_f64 import f64_corrected_reference, on_dv007_path

pytestmark = [pytest.mark.parity, pytest.mark.slow]

_CORPUS_DIR = Path(__file__).resolve().parent / "corpus"


def _first_case_per_cell() -> list[ManifestRecord]:
    """Return the first manifest case of each (model, coupling, integrator) cell."""
    manifest = CorpusManifest.from_json(_CORPUS_DIR / "manifest.json")
    seen: dict[tuple[str, str, str], ManifestRecord] = {}
    for record in manifest.cases:
        seen.setdefault((record.model, record.coupling, record.integrator), record)
    return list(seen.values())


_CELLS = _first_case_per_cell()


def _regenerate(record: ManifestRecord) -> CaseArrays:
    _, arrays = _run_case(
        model=record.model,
        coupling=record.coupling,
        integrator=record.integrator,
        n_oscillators=record.n_oscillators,
        n_steps=record.n_steps,
        dt=record.dt,
        seed=record.seed,
        parameters=dict(record.parameters),
    )
    return arrays


def _bit_identical(a: CaseArrays, b: CaseArrays) -> bool:
    return all(
        np.array_equal(getattr(a, name), getattr(b, name))
        for name in CaseArrays._ARRAY_NAMES
    )


def test_cells_cover_the_corpus_grid() -> None:
    """Fourteen grid cells, six of them on the DV-007 complex64 paths."""
    assert len(_CELLS) == 14
    assert sum(on_dv007_path(r.model, r.coupling) for r in _CELLS) == 6


@pytest.mark.parametrize("record", _CELLS, ids=lambda r: r.case_id)
def test_instrument_changes_only_dv007_paths(record: ManifestRecord) -> None:
    """Non-DV-007 cells are bit-identical under the instrument; DV-007 cells move."""
    native = _regenerate(record)
    with f64_corrected_reference():
        corrected = _regenerate(record)
    if on_dv007_path(record.model, record.coupling):
        assert not _bit_identical(native, corrected)
    else:
        assert _bit_identical(native, corrected)


def test_instrument_restores_the_archived_reference() -> None:
    """After the block, a DV-007 case regenerates bit-identically again."""
    record = next(r for r in _CELLS if r.model == "stuart_landau")
    native = _regenerate(record)
    with f64_corrected_reference():
        _regenerate(record)
    assert _bit_identical(native, _regenerate(record))


def test_instrument_restores_on_error() -> None:
    """An exception inside the block still restores the archived methods."""
    record = next(r for r in _CELLS if r.model == "stuart_landau")
    native = _regenerate(record)
    with pytest.raises(RuntimeError, match="boom"), f64_corrected_reference():
        raise RuntimeError("boom")
    assert _bit_identical(native, _regenerate(record))


@pytest.mark.parametrize(
    ("model", "coupling", "expected"),
    [
        ("stuart_landau", "full", True),
        ("kuramoto", "mean_field", True),
        ("hopf", "mean_field", True),
        ("kuramoto", "full", False),
        ("kuramoto", "sparse_knn", False),
        ("hopf", "full", False),
        ("hopf", "sparse_knn", False),
    ],
)
def test_dv007_path_predicate(model: str, coupling: str, expected: bool) -> None:
    """The DV-007 predicate names exactly the three complex64 code paths."""
    assert on_dv007_path(model, coupling) is expected
