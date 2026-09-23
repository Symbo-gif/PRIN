#!/usr/bin/env python
"""Regenerate PRIN publication figures and tables from immutable JSON artefacts.

The pipeline renders all fourteen verifiable historical figures (figures 2-15)
and eleven LaTeX tables without training, GPU execution, or random sampling.
The governed manifest covers every stored JSON artefact and fails closed on
missing, modified, or unmanifested files.

Usage:
    python tools/reproduce.py [--figures-only | --tables-only] [--verify-manifest]
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
import tempfile
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from prin.reporting import ReportingError
from prin.reporting.figure_generation import generate_all_figures
from prin.reporting.table_generation import generate_all_tables

_REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
_REFERENCE_ROOT = (
    _REPOSITORY_ROOT
    / "DOCS"
    / "archive and reference from PRINet 3.0"
    / "PRINet-3.0.0-main"
)
DEFAULT_RESULTS_DIR = _REFERENCE_ROOT / "benchmarks" / "results"
DEFAULT_MANIFEST = _REPOSITORY_ROOT / "paper" / "artefact_manifest.json"
DEFAULT_OUTPUT_DIR = (
    _REPOSITORY_ROOT / "DOCS" / "test_and_benchmark_results" / "reproduction"
)
MANIFEST_SCHEMA_VERSION = 1
ALLOWED_MANIFEST_ROOTS = (
    (_REPOSITORY_ROOT / "paper").resolve(),
    (_REPOSITORY_ROOT / "benchmarks" / "results").resolve(),
    Path(tempfile.gettempdir()).resolve(),
)
_SHA256_PATTERN = re.compile(r"[0-9a-f]{64}")


class ReproductionError(Exception):
    """Base class for reproduction-pipeline failures."""


class ReproductionConfigurationError(ReproductionError, ValueError):
    """Report an invalid combination of reproduction options."""


class ManifestFormatError(ReproductionError, ValueError):
    """Report a malformed or unreadable artefact manifest."""


class ManifestMismatchError(ReproductionError):
    """Report stored artefacts that do not match the governed manifest."""


@dataclass(frozen=True)
class ManifestRecord:
    """One immutable stored-artefact record.

    Attributes:
        path: Plain JSON filename relative to the stored-results directory.
        bytes: Exact file size in bytes.
        sha256: Lowercase SHA-256 hexadecimal digest.
    """

    path: str
    bytes: int
    sha256: str


@dataclass(frozen=True)
class ReproductionResult:
    """Summary of one successful reproduction run.

    Attributes:
        generated_files: Deterministically ordered generated output paths.
        manifest_records: Number of stored artefacts verified, or zero when
            full manifest verification was not requested.
    """

    generated_files: tuple[Path, ...]
    manifest_records: int


def compute_sha256(path: Path) -> str:
    """Compute the SHA-256 digest of a file.

    Args:
        path: File to hash.

    Returns:
        Lowercase hexadecimal SHA-256 digest.

    Raises:
        OSError: If the file cannot be read.
    """
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _reject_symlink(path: Path, role: str) -> None:
    """Refuse a symbolic link before any link-following operation reads it.

    ``Path.is_file``, ``Path.stat``, ``Path.read_text``, and ``Path.open`` all
    follow symbolic links, so a manifest or artefact that is a link to a file
    living outside the governed directory would be read, hashed, and accepted
    as if the directory itself held it: content integrity would be verified
    while path provenance silently would not be (CWE-59). The check is
    no-follow and runs *before* any of those calls, mirroring the discipline
    ``benchmarks/campaign/exp001_driver.py::check_run_complete`` already
    applies to a run's sidecar, its ``manifest.json``, and every declared
    artefact. Raised as a mismatch, not a format error: the manifest may be
    perfectly well-formed and still not attest what the directory holds.

    The governed directory itself is deliberately *not* checked. It is chosen
    by the caller (a governed tool or a test fixture), not attested by the
    manifest, and on macOS the standard temporary root is itself a symbolic
    link.

    Args:
        path: Candidate manifest or artefact path, unresolved.
        role: Human-readable role used in the failure message.

    Raises:
        ManifestMismatchError: If ``path`` is a symbolic link.
    """
    if path.is_symlink():
        raise ManifestMismatchError(
            f"{role} {path} is a symbolic link, not a regular file held by the "
            "governed directory; refusing to verify it"
        )


def _record_from_dict(payload: object, index: int) -> ManifestRecord:
    if not isinstance(payload, dict):
        raise ManifestFormatError(f"files[{index}] must be a JSON object")
    path = payload.get("path")
    size = payload.get("bytes")
    sha256 = payload.get("sha256")
    if (
        not isinstance(path, str)
        or "/" in path
        or "\\" in path
        or Path(path).name != path
        or Path(path).suffix != ".json"
    ):
        raise ManifestFormatError(f"files[{index}].path must be a plain JSON filename")
    if not isinstance(size, int) or isinstance(size, bool) or size < 0:
        raise ManifestFormatError(
            f"files[{index}].bytes must be a non-negative integer"
        )
    if not isinstance(sha256, str) or _SHA256_PATTERN.fullmatch(sha256) is None:
        raise ManifestFormatError(
            f"files[{index}].sha256 must be 64 lowercase hexadecimal characters"
        )
    return ManifestRecord(path=path, bytes=size, sha256=sha256)


def load_manifest(path: Path) -> tuple[ManifestRecord, ...]:
    """Load and validate the governed stored-artefact manifest.

    Args:
        path: JSON manifest path.

    Returns:
        Manifest records sorted by relative path.

    Raises:
        ManifestFormatError: If the manifest cannot be read or violates its
            schema.
    """
    try:
        payload: Any = json.loads(path.read_text(encoding="utf-8"))
    except OSError as error:
        raise ManifestFormatError(f"cannot read manifest {path}: {error}") from error
    except json.JSONDecodeError as error:
        raise ManifestFormatError(f"invalid JSON manifest {path}: {error}") from error
    if not isinstance(payload, dict):
        raise ManifestFormatError("manifest must be a JSON object")
    if payload.get("schema_version") != MANIFEST_SCHEMA_VERSION:
        raise ManifestFormatError(
            f"manifest schema_version must be {MANIFEST_SCHEMA_VERSION}"
        )
    raw_files = payload.get("files")
    if not isinstance(raw_files, list):
        raise ManifestFormatError("manifest files must be a list")
    records = tuple(
        _record_from_dict(item, index) for index, item in enumerate(raw_files)
    )
    paths = [record.path for record in records]
    duplicates = sorted({name for name in paths if paths.count(name) > 1})
    if duplicates:
        raise ManifestFormatError(f"duplicate manifest path: {', '.join(duplicates)}")
    return tuple(sorted(records, key=lambda record: record.path))


def append_manifest(
    results_dir: Path = DEFAULT_RESULTS_DIR,
    manifest_path: Path = DEFAULT_MANIFEST,
) -> tuple[ManifestRecord, ...]:
    """Create or append to a governed artefact manifest without rewriting history.

    Existing records must still match exactly. Only previously unmanifested JSON
    files are added, making mutation or removal of an accepted artefact a hard
    failure rather than silently blessing it with a new digest. A symbolic link
    is never manifested: the manifest destination and every candidate ``*.json``
    in ``results_dir`` are rejected up front if they are links, so a digest is
    only ever recorded for a regular file the directory itself holds (see
    :func:`_reject_symlink`).

    Args:
        results_dir: Directory containing stored JSON artefacts.
        manifest_path: Manifest to create or append.

    Returns:
        The complete, sorted manifest records.

    Raises:
        ReproductionConfigurationError: If the manifest destination is outside
            the governed output roots.
        ManifestFormatError: If an existing manifest is malformed.
        ManifestMismatchError: If an existing record was removed or modified, or
            if the manifest or any candidate artefact is a symbolic link.
    """
    _reject_symlink(manifest_path, "manifest")
    results = results_dir.resolve()
    destination = manifest_path.resolve()
    if not any(
        destination == root or root in destination.parents
        for root in ALLOWED_MANIFEST_ROOTS
    ):
        roots = ", ".join(str(root) for root in ALLOWED_MANIFEST_ROOTS)
        raise ReproductionConfigurationError(
            f"manifest {destination} is outside allowed roots: {roots}"
        )
    records = load_manifest(destination) if destination.is_file() else ()
    existing = {record.path: record for record in records}
    for candidate in sorted(results.glob("*.json")):
        _reject_symlink(candidate, "candidate artefact")
    actual_paths = {
        path.name: path
        for path in results.glob("*.json")
        if path.is_file() and path.resolve() != destination
    }
    missing = sorted(set(existing) - set(actual_paths))
    if missing:
        raise ManifestMismatchError(f"missing artefacts: {', '.join(missing)}")
    for name, record in existing.items():
        path = actual_paths[name]
        if path.stat().st_size != record.bytes:
            raise ManifestMismatchError(f"size mismatch: {name}")
        if compute_sha256(path) != record.sha256:
            raise ManifestMismatchError(f"SHA-256 mismatch: {name}")
    appended = [
        ManifestRecord(
            path=name,
            bytes=path.stat().st_size,
            sha256=compute_sha256(path),
        )
        for name, path in actual_paths.items()
        if name not in existing
    ]
    complete = tuple(sorted((*records, *appended), key=lambda record: record.path))
    if appended or not destination.is_file():
        payload = {
            "schema_version": MANIFEST_SCHEMA_VERSION,
            "description": (
                "SHA-256 manifest for the immutable PRINet 3.0 benchmark JSON "
                "artefacts used by tools/reproduce.py. Existing records are "
                "append-only."
            ),
            "source": "PRINet 3.0 stored benchmark JSON artefacts",
            "files": [
                {"path": record.path, "bytes": record.bytes, "sha256": record.sha256}
                for record in complete
            ],
        }
        destination.write_text(
            json.dumps(payload, indent=2, ensure_ascii=True) + "\n",
            encoding="utf-8",
            newline="\n",
        )
    return complete


def verify_manifest(
    results_dir: Path = DEFAULT_RESULTS_DIR,
    manifest_path: Path = DEFAULT_MANIFEST,
) -> tuple[ManifestRecord, ...]:
    """Verify the exact stored-JSON inventory against its SHA-256 manifest.

    The function is read-only. Existing artefacts can never be silently
    replaced: missing, modified, resized, or newly appended JSON files require a
    reviewed manifest update before reproduction succeeds. The manifest and
    every manifested artefact must also be a regular file held by
    ``results_dir`` itself, never a symbolic link into it (see
    :func:`_reject_symlink`).

    Args:
        results_dir: Directory containing immutable stored JSON artefacts.
        manifest_path: Governed SHA-256 manifest.

    Returns:
        The validated manifest records.

    Raises:
        ManifestFormatError: If the manifest is malformed.
        ManifestMismatchError: If inventory, size, or digest checks fail, or if
            the manifest or any manifested artefact is a symbolic link.
    """
    _reject_symlink(manifest_path, "manifest")
    results = results_dir.resolve()
    records = load_manifest(manifest_path)
    expected = {record.path for record in records}
    actual = {path.name for path in results.glob("*.json") if path.is_file()}
    if manifest_path.resolve().parent == results:
        actual.discard(manifest_path.name)
    missing = sorted(expected - actual)
    unexpected = sorted(actual - expected)
    if missing:
        raise ManifestMismatchError(f"missing artefacts: {', '.join(missing)}")
    if unexpected:
        raise ManifestMismatchError(f"unmanifested artefacts: {', '.join(unexpected)}")
    for record in records:
        path = results / record.path
        _reject_symlink(path, "manifested artefact")
        if path.stat().st_size != record.bytes:
            raise ManifestMismatchError(f"size mismatch: {record.path}")
        if compute_sha256(path) != record.sha256:
            raise ManifestMismatchError(f"SHA-256 mismatch: {record.path}")
    return records


def run_reproduction(
    *,
    results_dir: Path = DEFAULT_RESULTS_DIR,
    output_dir: Path = DEFAULT_OUTPUT_DIR,
    manifest_path: Path = DEFAULT_MANIFEST,
    figures_only: bool = False,
    tables_only: bool = False,
    verify: bool = False,
) -> ReproductionResult:
    """Run the deterministic publication reproduction pipeline.

    Args:
        results_dir: Directory containing stored benchmark JSON artefacts.
        output_dir: Base destination containing ``figures/`` and ``tables/``.
        manifest_path: Governed SHA-256 input manifest.
        figures_only: Generate figures and skip tables.
        tables_only: Generate tables and skip figures.
        verify: Verify the complete stored-artefact manifest before rendering.

    Returns:
        Generated paths and manifest-verification count.

    Raises:
        ReproductionConfigurationError: If both output-selection flags are set.
        ReproductionError: If manifest verification fails.
        ReportingError: If publication generation fails.
    """
    if figures_only and tables_only:
        raise ReproductionConfigurationError(
            "--figures-only and --tables-only are mutually exclusive"
        )
    records = verify_manifest(results_dir, manifest_path) if verify else ()
    generated: list[Path] = []
    if not tables_only:
        figures = generate_all_figures(results_dir, output_dir / "figures")
        generated.extend(path for paths in figures.values() for path in paths)
    if not figures_only:
        tables = generate_all_tables(results_dir, output_dir / "tables")
        generated.extend(tables.values())
    return ReproductionResult(
        generated_files=tuple(generated), manifest_records=len(records)
    )


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--results-dir",
        type=Path,
        default=DEFAULT_RESULTS_DIR,
        help="directory containing stored JSON benchmark artefacts",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=DEFAULT_OUTPUT_DIR,
        help="base output directory for figures and tables",
    )
    parser.add_argument(
        "--manifest",
        type=Path,
        default=DEFAULT_MANIFEST,
        help="governed SHA-256 artefact manifest",
    )
    modes = parser.add_mutually_exclusive_group()
    modes.add_argument("--figures-only", action="store_true", help="skip tables")
    modes.add_argument("--tables-only", action="store_true", help="skip figures")
    parser.add_argument(
        "--verify-manifest",
        action="store_true",
        help="fail before rendering unless every stored artefact matches",
    )
    parser.add_argument(
        "--append-manifest",
        action="store_true",
        help="append new JSON artefacts after verifying all existing records",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    """Execute the command-line reproduction pipeline.

    Args:
        argv: Optional argument list. Uses ``sys.argv`` when omitted.

    Returns:
        Zero on success and one for a typed reproduction failure.
    """
    args = _parser().parse_args(argv)
    try:
        if args.append_manifest:
            if args.figures_only or args.tables_only or args.verify_manifest:
                raise ReproductionConfigurationError(
                    "--append-manifest cannot be combined with generation modes or "
                    "--verify-manifest"
                )
            records = append_manifest(args.results_dir, args.manifest)
            print(f"Manifest contains {len(records)} stored JSON artefacts.")
            return 0
        result = run_reproduction(
            results_dir=args.results_dir,
            output_dir=args.output_dir,
            manifest_path=args.manifest,
            figures_only=args.figures_only,
            tables_only=args.tables_only,
            verify=args.verify_manifest,
        )
    except (ReproductionError, ReportingError, OSError) as error:
        print(f"ERROR: {error}", file=sys.stderr)
        return 1
    if args.verify_manifest:
        print(f"Verified {result.manifest_records} stored JSON artefacts.")
    output_root = args.output_dir.resolve()
    for path in result.generated_files:
        relative = path.resolve().relative_to(output_root).as_posix()
        print(f"sha256:{compute_sha256(path)}  {relative}")
    print(f"Generated {len(result.generated_files)} files.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
