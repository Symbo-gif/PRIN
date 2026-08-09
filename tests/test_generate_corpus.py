"""Tests for the PRINet 3.0 golden-corpus generator."""

from __future__ import annotations

from pathlib import Path

import pytest

from prin.parity.loader import CorpusLoader
from prin.parity.manifest import create_manifest

prinet = pytest.importorskip("prinet")

from parity.generate_corpus import generate_corpus

pytestmark = [pytest.mark.slow, pytest.mark.parity]


def test_generate_corpus_writes_loadable_cases(tmp_path: Path) -> None:
    """The generator writes cases that pass the loader validation."""
    out_dir = tmp_path / "corpus"
    cases = generate_corpus(out_dir, limit=4)
    create_manifest(
        corpus_dir=out_dir,
        cases=cases,
        generator="prinet",
        generator_version=str(getattr(prinet, "__version__", "3.0.0")),
        prin_version="0.1.0",
        reference_source=(
            "DOCS/archive and reference from PRINet 3.0/PRINet-3.0.0-main"
        ),
    )
    assert (out_dir / "manifest.json").is_file()
    loader = CorpusLoader(out_dir)
    assert len(loader) == 4
    for spec, _ in cases:
        loaded = loader.load(spec.case_id)
        assert loaded.spec == spec


def test_generate_corpus_respects_limit(tmp_path: Path) -> None:
    """The ``limit`` argument caps the number of generated cases."""
    out_dir = tmp_path / "corpus"
    cases = generate_corpus(out_dir, limit=1)
    assert len(cases) == 1
