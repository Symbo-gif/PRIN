"""Manifest and SHA-256 validation for the golden-trajectory corpus."""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from .schema import (
    TRAJECTORY_ATOL,
    TRAJECTORY_RTOL,
    CaseSpec,
    CorpusValidationError,
    _validate_float,
)

MANIFEST_SCHEMA_VERSION: int = 1


def _hash_file(path: Path) -> str:
    """Return the SHA-256 hex digest of a file."""
    h = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(8192), b""):
            h.update(chunk)
    return h.hexdigest()


def _validate_str(value: object, name: str) -> str:
    """Return ``value`` as a string or raise ``CorpusValidationError``."""
    if not isinstance(value, str):
        raise CorpusValidationError(f"{name} must be a string, got {type(value)}")
    return value


def _validate_int(value: object, name: str) -> int:
    """Return ``value`` as an integer or raise ``CorpusValidationError``."""
    if not isinstance(value, int) or isinstance(value, bool):
        raise CorpusValidationError(f"{name} must be an integer, got {type(value)}")
    return value


@dataclass(frozen=True)
class ManifestRecord:
    """One row of the corpus manifest describing a single case file."""

    case_id: str
    file: str
    sha256: str
    model: str
    coupling: str
    integrator: str
    n_oscillators: int
    n_steps: int
    dt: float
    seed: int
    parameters: dict[str, object]

    def to_dict(self) -> dict[str, Any]:
        """Serialize this record to a JSON-compatible dictionary."""
        return {
            "case_id": self.case_id,
            "file": self.file,
            "sha256": self.sha256,
            "model": self.model,
            "coupling": self.coupling,
            "integrator": self.integrator,
            "n_oscillators": self.n_oscillators,
            "n_steps": self.n_steps,
            "dt": self.dt,
            "seed": self.seed,
            "parameters": self.parameters,
        }

    @classmethod
    def from_dict(cls, payload: dict[str, Any]) -> ManifestRecord:
        """Deserialize and validate a manifest record."""
        if not isinstance(payload, dict):
            raise CorpusValidationError("manifest record must be a dictionary")
        parameters = payload.get("parameters")
        if not isinstance(parameters, dict):
            raise CorpusValidationError(
                "manifest record 'parameters' must be a dictionary"
            )
        return cls(
            case_id=_validate_str(payload.get("case_id"), "case_id"),
            file=_validate_str(payload.get("file"), "file"),
            sha256=_validate_str(payload.get("sha256"), "sha256"),
            model=_validate_str(payload.get("model"), "model"),
            coupling=_validate_str(payload.get("coupling"), "coupling"),
            integrator=_validate_str(payload.get("integrator"), "integrator"),
            n_oscillators=_validate_int(payload.get("n_oscillators"), "n_oscillators"),
            n_steps=_validate_int(payload.get("n_steps"), "n_steps"),
            dt=_validate_float(payload.get("dt"), "dt"),
            seed=_validate_int(payload.get("seed"), "seed"),
            parameters={str(k): v for k, v in parameters.items()},
        )

    @classmethod
    def from_spec(
        cls,
        spec: CaseSpec,
        relative_path: Path,
        sha256: str,
    ) -> ManifestRecord:
        """Create a manifest record from a validated case spec."""
        return cls(
            case_id=spec.case_id,
            file=relative_path.as_posix(),
            sha256=sha256,
            model=spec.model,
            coupling=spec.coupling,
            integrator=spec.integrator,
            n_oscillators=spec.n_oscillators,
            n_steps=spec.n_steps,
            dt=spec.dt,
            seed=spec.seed,
            parameters=spec.parameters,
        )


@dataclass(frozen=True)
class CorpusManifest:
    """Top-level manifest for an immutable golden-trajectory corpus."""

    schema_version: int
    generator: str
    generator_version: str
    prin_version: str
    created_at: str
    n_cases: int
    reference_source: str
    cases: list[ManifestRecord]
    trajectory_rtol: float = TRAJECTORY_RTOL
    trajectory_atol: float = TRAJECTORY_ATOL

    def to_dict(self) -> dict[str, Any]:
        """Serialize the manifest to a JSON-compatible dictionary."""
        return {
            "schema_version": self.schema_version,
            "generator": self.generator,
            "generator_version": self.generator_version,
            "prin_version": self.prin_version,
            "created_at": self.created_at,
            "n_cases": self.n_cases,
            "reference_source": self.reference_source,
            "trajectory_rtol": self.trajectory_rtol,
            "trajectory_atol": self.trajectory_atol,
            "cases": [case.to_dict() for case in self.cases],
        }

    def to_json(self, path: Path) -> None:
        """Write the manifest to ``path`` as formatted JSON."""
        path.write_text(
            json.dumps(self.to_dict(), indent=2, sort_keys=False, ensure_ascii=False),
            encoding="utf-8",
        )

    @classmethod
    def from_dict(cls, payload: dict[str, Any]) -> CorpusManifest:
        """Deserialize and validate a manifest dictionary."""
        if not isinstance(payload, dict):
            raise CorpusValidationError("manifest must be a dictionary")
        raw_cases = payload.get("cases", [])
        if not isinstance(raw_cases, list):
            raise CorpusValidationError("manifest 'cases' must be a list")
        cases = [ManifestRecord.from_dict(item) for item in raw_cases]
        return cls(
            schema_version=_validate_int(
                payload.get("schema_version"), "schema_version"
            ),
            generator=_validate_str(payload.get("generator"), "generator"),
            generator_version=_validate_str(
                payload.get("generator_version"), "generator_version"
            ),
            prin_version=_validate_str(payload.get("prin_version"), "prin_version"),
            created_at=_validate_str(payload.get("created_at"), "created_at"),
            n_cases=_validate_int(payload.get("n_cases"), "n_cases"),
            reference_source=_validate_str(
                payload.get("reference_source"), "reference_source"
            ),
            cases=cases,
            trajectory_rtol=float(payload.get("trajectory_rtol", TRAJECTORY_RTOL)),
            trajectory_atol=float(payload.get("trajectory_atol", TRAJECTORY_ATOL)),
        )

    @classmethod
    def from_json(cls, path: Path) -> CorpusManifest:
        """Load and validate a manifest from a JSON file."""
        payload = json.loads(path.read_text(encoding="utf-8"))
        manifest = cls.from_dict(payload)
        if len(manifest.cases) != manifest.n_cases:
            raise CorpusValidationError(
                f"manifest claims {manifest.n_cases} cases "
                f"but lists {len(manifest.cases)}"
            )
        return manifest


def create_manifest(
    corpus_dir: Path,
    cases: list[tuple[CaseSpec, Path]],
    generator: str,
    generator_version: str,
    prin_version: str,
    reference_source: str,
) -> CorpusManifest:
    """Build a manifest from generated case files and write it to ``corpus_dir``.

    Args:
        corpus_dir: Directory that will contain ``manifest.json`` and case files.
        cases: List of ``(CaseSpec, absolute_path)`` pairs.
        generator: Name of the generator (e.g. ``prinet``).
        generator_version: Version of the generator.
        prin_version: Version of PRIN being tested.
        reference_source: Path or description of the reference implementation.

    Returns:
        The generated and written manifest.
    """
    records: list[ManifestRecord] = []
    for spec, path in cases:
        sha = _hash_file(path)
        rel = path.relative_to(corpus_dir)
        records.append(ManifestRecord.from_spec(spec, rel, sha))
    manifest = CorpusManifest(
        schema_version=MANIFEST_SCHEMA_VERSION,
        generator=generator,
        generator_version=generator_version,
        prin_version=prin_version,
        created_at=datetime.now(UTC).isoformat(),
        n_cases=len(records),
        reference_source=reference_source,
        cases=records,
    )
    manifest.to_json(corpus_dir / "manifest.json")
    return manifest


def validate_manifest(manifest: CorpusManifest, corpus_dir: Path) -> None:
    """Validate that every case file exists and matches its SHA-256 digest.

    Raises:
        CorpusValidationError: If a file is missing or its digest does not match.
    """
    missing: list[str] = []
    corrupt: list[str] = []
    for record in manifest.cases:
        path = corpus_dir / record.file
        if not path.is_file():
            missing.append(record.file)
            continue
        if _hash_file(path) != record.sha256:
            corrupt.append(record.file)
    if missing:
        raise CorpusValidationError(f"missing case files: {', '.join(missing)}")
    if corrupt:
        raise CorpusValidationError(f"SHA-256 mismatch for files: {', '.join(corrupt)}")
