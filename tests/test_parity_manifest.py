"""Tests for ``prin.parity.manifest``."""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pytest
from prin.parity.manifest import (
    CorpusManifest,
    ManifestRecord,
    create_manifest,
    validate_manifest,
)
from prin.parity.schema import (
    CaseArrays,
    CaseSpec,
    CorpusValidationError,
    Coupling,
    Integrator,
    Model,
)


def _write_corpus(root: Path, n_cases: int = 2) -> list[CaseSpec]:
    """Write ``n_cases`` synthetic cases into ``root/cases``."""
    specs: list[CaseSpec] = []
    cases_dir = root / "cases"
    cases_dir.mkdir(parents=True, exist_ok=True)
    for i in range(n_cases):
        n = 4 + i
        steps = 2
        phase = np.linspace(0, 1, n, dtype=np.float64)
        arrays = CaseArrays(
            phase_init=phase,
            amplitude_init=np.ones(n, dtype=np.float64),
            frequency_init=np.ones(n, dtype=np.float64),
            phase_final=phase + 0.01,
            amplitude_final=np.ones(n, dtype=np.float64),
            frequency_final=np.ones(n, dtype=np.float64),
            phase_traj=np.stack([phase, phase + 0.005, phase + 0.01]),
            amplitude_traj=np.ones((steps + 1, n), dtype=np.float64),
            frequency_traj=np.ones((steps + 1, n), dtype=np.float64),
            order_parameter_traj=np.array([0.1, 0.2, 0.3], dtype=np.float64),
            mean_phase_coherence_traj=np.array([0.1, 0.2, 0.3], dtype=np.float64),
        )
        spec = CaseSpec(
            case_id=f"case_{i:03d}",
            model=Model.KURAMOTO.value,
            coupling=Coupling.FULL.value,
            integrator=Integrator.RK4.value,
            n_oscillators=n,
            n_steps=steps,
            dt=0.01,
            seed=i,
            parameters={"coupling_strength": 1.0},
        )
        path = cases_dir / f"{spec.case_id}.npz"
        arrays.to_npz(path)
        specs.append(spec)
    return specs


def test_create_manifest_writes_json(tmp_path: Path) -> None:
    """``create_manifest`` writes a loadable manifest with SHA-256 records."""
    specs = _write_corpus(tmp_path)
    cases = [(spec, tmp_path / "cases" / f"{spec.case_id}.npz") for spec in specs]
    manifest = create_manifest(
        corpus_dir=tmp_path,
        cases=cases,
        generator="test",
        generator_version="0.0.0",
        prin_version="0.1.0",
        reference_source="synthetic",
    )
    assert (tmp_path / "manifest.json").is_file()
    loaded = CorpusManifest.from_json(tmp_path / "manifest.json")
    assert loaded == manifest
    assert loaded.n_cases == 2
    assert loaded.generator == "test"
    assert len(loaded.cases) == 2
    assert all(record.sha256 for record in loaded.cases)


def test_validate_manifest_passes_for_good_corpus(tmp_path: Path) -> None:
    """A corpus with matching files and digests passes validation."""
    specs = _write_corpus(tmp_path)
    cases = [(spec, tmp_path / "cases" / f"{spec.case_id}.npz") for spec in specs]
    manifest = create_manifest(
        corpus_dir=tmp_path,
        cases=cases,
        generator="test",
        generator_version="0.0.0",
        prin_version="0.1.0",
        reference_source="synthetic",
    )
    validate_manifest(manifest, tmp_path)


def test_validate_manifest_detects_missing_file(tmp_path: Path) -> None:
    """Validation fails closed when a referenced ``.npz`` is missing."""
    specs = _write_corpus(tmp_path)
    cases = [(spec, tmp_path / "cases" / f"{spec.case_id}.npz") for spec in specs]
    manifest = create_manifest(
        corpus_dir=tmp_path,
        cases=cases,
        generator="test",
        generator_version="0.0.0",
        prin_version="0.1.0",
        reference_source="synthetic",
    )
    (tmp_path / "cases" / "case_000.npz").unlink()
    with pytest.raises(CorpusValidationError, match="missing case files"):
        validate_manifest(manifest, tmp_path)


def test_validate_manifest_detects_corrupt_file(tmp_path: Path) -> None:
    """Validation fails closed when a file digest does not match."""
    specs = _write_corpus(tmp_path)
    cases = [(spec, tmp_path / "cases" / f"{spec.case_id}.npz") for spec in specs]
    manifest = create_manifest(
        corpus_dir=tmp_path,
        cases=cases,
        generator="test",
        generator_version="0.0.0",
        prin_version="0.1.0",
        reference_source="synthetic",
    )
    path = tmp_path / "cases" / "case_000.npz"
    original = path.read_bytes()
    path.write_bytes(original + b"\x00")
    with pytest.raises(CorpusValidationError, match="SHA-256 mismatch"):
        validate_manifest(manifest, tmp_path)


def test_manifest_record_from_dict_validates() -> None:
    """``ManifestRecord.from_dict`` rejects malformed records."""
    with pytest.raises(CorpusValidationError, match="sha256"):
        ManifestRecord.from_dict(
            {
                "case_id": "c",
                "file": "cases/c.npz",
                "sha256": 123,
                "model": "kuramoto",
                "coupling": "full",
                "integrator": "rk4",
                "n_oscillators": 8,
                "n_steps": 2,
                "dt": 0.01,
                "seed": 0,
                "parameters": {"coupling_strength": 1.0},
            }
        )


def test_manifest_record_from_dict_rejects_non_dict() -> None:
    """``ManifestRecord.from_dict`` fails closed on non-dictionaries."""
    with pytest.raises(CorpusValidationError, match="must be a dictionary"):
        ManifestRecord.from_dict("not-a-dict")  # type: ignore[arg-type]


def test_manifest_record_from_dict_rejects_non_dict_parameters() -> None:
    """``ManifestRecord.from_dict`` rejects non-dictionary parameters."""
    with pytest.raises(CorpusValidationError, match=r"parameters.*dictionary"):
        ManifestRecord.from_dict(
            {
                "case_id": "c",
                "file": "cases/c.npz",
                "sha256": "a" * 64,
                "model": "kuramoto",
                "coupling": "full",
                "integrator": "rk4",
                "n_oscillators": 8,
                "n_steps": 2,
                "dt": 0.01,
                "seed": 0,
                "parameters": [1.0],
            }
        )


def test_manifest_record_from_dict_rejects_non_integer() -> None:
    """``ManifestRecord.from_dict`` rejects non-integer integer fields."""
    with pytest.raises(CorpusValidationError, match="n_oscillators must be an integer"):
        ManifestRecord.from_dict(
            {
                "case_id": "c",
                "file": "cases/c.npz",
                "sha256": "a" * 64,
                "model": "kuramoto",
                "coupling": "full",
                "integrator": "rk4",
                "n_oscillators": "8",
                "n_steps": 2,
                "dt": 0.01,
                "seed": 0,
                "parameters": {},
            }
        )


def test_corpus_manifest_from_dict_rejects_non_dict() -> None:
    """``CorpusManifest.from_dict`` fails closed on non-dictionaries."""
    with pytest.raises(CorpusValidationError, match="must be a dictionary"):
        CorpusManifest.from_dict("not-a-dict")  # type: ignore[arg-type]


def test_corpus_manifest_from_dict_rejects_non_list_cases() -> None:
    """``CorpusManifest.from_dict`` rejects a non-list ``cases`` field."""
    with pytest.raises(CorpusValidationError, match=r"cases.*list"):
        CorpusManifest.from_dict({"cases": "not-a-list"})


def test_corpus_manifest_from_json_rejects_count_mismatch(tmp_path: Path) -> None:
    """``CorpusManifest.from_json`` detects an ``n_cases`` mismatch."""
    import json as _json

    specs = _write_corpus(tmp_path)
    cases = [(spec, tmp_path / "cases" / f"{spec.case_id}.npz") for spec in specs]
    create_manifest(
        corpus_dir=tmp_path,
        cases=cases,
        generator="test",
        generator_version="0.0.0",
        prin_version="0.1.0",
        reference_source="synthetic",
    )
    payload = _json.loads((tmp_path / "manifest.json").read_text())
    payload["n_cases"] = 99
    (tmp_path / "manifest.json").write_text(_json.dumps(payload))
    with pytest.raises(CorpusValidationError, match="claims 99 cases"):
        CorpusManifest.from_json(tmp_path / "manifest.json")
