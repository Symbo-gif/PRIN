"""Tests for ``prin.parity.loader``."""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pytest
from prin.parity.loader import CorpusLoader, LoadedCase
from prin.parity.manifest import create_manifest
from prin.parity.schema import (
    CaseArrays,
    CaseSpec,
    CorpusValidationError,
    Coupling,
    Integrator,
    Model,
)


def _make_corpus(tmp_path: Path, n_cases: int = 3) -> Path:
    """Create a synthetic corpus in ``tmp_path`` and return its directory."""
    corpus_dir = tmp_path / "corpus"
    cases_dir = corpus_dir / "cases"
    cases_dir.mkdir(parents=True, exist_ok=True)
    cases: list[tuple[CaseSpec, Path]] = []
    for i in range(n_cases):
        n = 4
        phase = np.linspace(0, 1, n, dtype=np.float64)
        arrays = CaseArrays(
            phase_init=phase,
            amplitude_init=np.ones(n, dtype=np.float64),
            frequency_init=np.ones(n, dtype=np.float64),
            phase_final=phase,
            amplitude_final=np.ones(n, dtype=np.float64),
            frequency_final=np.ones(n, dtype=np.float64),
            phase_traj=np.stack([phase, phase]),
            amplitude_traj=np.ones((2, n), dtype=np.float64),
            frequency_traj=np.ones((2, n), dtype=np.float64),
            order_parameter_traj=np.array([0.1, 0.1], dtype=np.float64),
            mean_phase_coherence_traj=np.array([0.1, 0.1], dtype=np.float64),
        )
        spec = CaseSpec(
            case_id=f"case_{i:03d}",
            model=Model.KURAMOTO.value,
            coupling=Coupling.FULL.value,
            integrator=Integrator.RK4.value,
            n_oscillators=n,
            n_steps=1,
            dt=0.01,
            seed=i,
            parameters={"coupling_strength": 1.0},
        )
        path = cases_dir / f"{spec.case_id}.npz"
        arrays.to_npz(path)
        cases.append((spec, path))
    create_manifest(
        corpus_dir=corpus_dir,
        cases=cases,
        generator="test",
        generator_version="0.0.0",
        prin_version="0.1.0",
        reference_source="synthetic",
    )
    return corpus_dir


def test_loader_initializes_from_manifest(tmp_path: Path) -> None:
    """A loader can be created from a valid corpus directory."""
    corpus_dir = _make_corpus(tmp_path)
    loader = CorpusLoader(corpus_dir)
    assert len(loader) == 3
    assert loader.manifest.n_cases == 3


def test_loader_loads_case(tmp_path: Path) -> None:
    """``load`` returns a ``LoadedCase`` with validated arrays."""
    corpus_dir = _make_corpus(tmp_path)
    loader = CorpusLoader(corpus_dir)
    loaded = loader.load("case_001")
    assert isinstance(loaded, LoadedCase)
    assert loaded.spec.case_id == "case_001"
    assert loaded.arrays.n_oscillators == 4
    assert loaded.arrays.n_steps == 1


def test_loader_iterates_all_cases(tmp_path: Path) -> None:
    """``__iter__`` yields every case in manifest order."""
    corpus_dir = _make_corpus(tmp_path)
    loader = CorpusLoader(corpus_dir)
    ids = [case.spec.case_id for case in loader]
    assert ids == ["case_000", "case_001", "case_002"]


def test_loader_rejects_unknown_case(tmp_path: Path) -> None:
    """Loading an unknown case ID raises ``CorpusValidationError``."""
    corpus_dir = _make_corpus(tmp_path)
    loader = CorpusLoader(corpus_dir)
    with pytest.raises(CorpusValidationError, match="not found"):
        loader.load("missing")


def test_loader_rejects_duplicate_ids(tmp_path: Path) -> None:
    """A manifest with duplicate case IDs fails closed."""
    from dataclasses import replace

    corpus_dir = _make_corpus(tmp_path, n_cases=2)
    manifest = CorpusLoader(corpus_dir).manifest
    duplicate = manifest.cases[0]
    bad_manifest = replace(
        manifest,
        n_cases=3,
        cases=[*manifest.cases, duplicate],
    )
    bad_manifest.to_json(corpus_dir / "manifest.json")
    with pytest.raises(CorpusValidationError, match="duplicate case IDs"):
        CorpusLoader(corpus_dir)
