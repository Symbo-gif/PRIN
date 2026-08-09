"""Load and validate golden-trajectory corpus cases from disk."""

from __future__ import annotations

from collections.abc import Iterator
from dataclasses import dataclass
from pathlib import Path

from .manifest import CorpusManifest, ManifestRecord, validate_manifest
from .schema import CaseArrays, CaseSpec, CorpusValidationError, validate_case_arrays


@dataclass(frozen=True)
class LoadedCase:
    """A case spec paired with its validated numeric arrays."""

    spec: CaseSpec
    arrays: CaseArrays


class CorpusLoader:
    """Load golden-trajectory cases from a corpus directory.

    The corpus directory must contain a ``manifest.json`` and the case ``.npz``
    files referenced by that manifest. The loader validates file integrity and
    array shapes/dtypes on every load.
    """

    def __init__(self, corpus_dir: Path) -> None:
        """Initialize the loader for ``corpus_dir``.

        Args:
            corpus_dir: Directory containing ``manifest.json`` and case files.

        Raises:
            CorpusValidationError: If the manifest cannot be loaded or validated.
        """
        self._corpus_dir = corpus_dir.resolve()
        self._manifest_path = self._corpus_dir / "manifest.json"
        if not self._manifest_path.is_file():
            raise CorpusValidationError(
                f"corpus manifest not found: {self._manifest_path}"
            )
        self._manifest = CorpusManifest.from_json(self._manifest_path)
        validate_manifest(self._manifest, self._corpus_dir)
        self._by_id: dict[str, int] = {
            record.case_id: index for index, record in enumerate(self._manifest.cases)
        }
        if len(self._by_id) != len(self._manifest.cases):
            raise CorpusValidationError("manifest contains duplicate case IDs")

    @property
    def manifest(self) -> CorpusManifest:
        """The validated corpus manifest."""
        return self._manifest

    @property
    def corpus_dir(self) -> Path:
        """Root directory of the loaded corpus."""
        return self._corpus_dir

    def __len__(self) -> int:
        """Number of cases in the corpus."""
        return len(self._manifest.cases)

    def __iter__(self) -> Iterator[LoadedCase]:
        """Yield every case in manifest order."""
        for record in self._manifest.cases:
            yield self.load(record.case_id)

    def load(self, case_id: str) -> LoadedCase:
        """Load and validate a single case by ID.

        Args:
            case_id: The stable case identifier.

        Returns:
            The loaded and validated case.

        Raises:
            CorpusValidationError: If the case is unknown or its data is invalid.
        """
        if case_id not in self._by_id:
            raise CorpusValidationError(f"case not found in manifest: {case_id}")
        record = self._manifest.cases[self._by_id[case_id]]
        path = self._corpus_dir / record.file
        if not path.is_file():
            raise CorpusValidationError(f"case file missing: {path}")
        spec = CaseSpec.from_dict(record.to_dict())
        arrays = CaseArrays.from_npz(path)
        validate_case_arrays(spec, arrays)
        return LoadedCase(spec=spec, arrays=arrays)

    def get_record(self, case_id: str) -> ManifestRecord:
        """Return the manifest record for ``case_id`` without loading arrays."""
        if case_id not in self._by_id:
            raise CorpusValidationError(f"case not found in manifest: {case_id}")
        return self._manifest.cases[self._by_id[case_id]]
