"""Tests for the governed publication reproduction pipeline."""

from __future__ import annotations

import ast
import json
from pathlib import Path

import prin.reporting
import pytest

from tools import reproduce


def _write_manifest(root: Path, files: dict[str, bytes]) -> Path:
    for name, payload in files.items():
        (root / name).write_bytes(payload)
    manifest = {
        "schema_version": 1,
        "description": "test manifest",
        "source": "synthetic",
        "files": [
            {
                "path": name,
                "bytes": len(payload),
                "sha256": reproduce.compute_sha256(root / name),
            }
            for name, payload in sorted(files.items())
        ],
    }
    path = root / "manifest.json"
    path.write_text(json.dumps(manifest), encoding="utf-8")
    return path


def test_reproduce_imports_only_public_reporting_surface() -> None:
    """WP035-F1: the pipeline must not reach into ``prin.reporting`` private modules.

    ``ReportingError`` is re-exported through ``prin.reporting.__init__`` and
    listed in its ``__all__``; importing it from ``prin.reporting._artifacts``
    (or any other ``prin.reporting._*`` module) is a private cross-module
    import identical in kind to the WP034-F4 pattern.
    """
    source = Path(reproduce.__file__).read_text(encoding="utf-8")
    tree = ast.parse(source)
    private_reporting_imports = [
        node.module
        for node in ast.walk(tree)
        if isinstance(node, ast.ImportFrom)
        and node.module is not None
        and node.module.startswith("prin.reporting.")
        and node.module.rsplit(".", 1)[1].startswith("_")
    ]
    assert private_reporting_imports == []
    assert reproduce.ReportingError is prin.reporting.ReportingError


def test_repository_manifest_matches_all_stored_json_artefacts() -> None:
    records = reproduce.verify_manifest(
        reproduce.DEFAULT_RESULTS_DIR, reproduce.DEFAULT_MANIFEST
    )
    assert len(records) == 172
    assert records[0].path < records[-1].path


def test_verify_manifest_passes_and_preserves_artefact_bytes(tmp_path: Path) -> None:
    files = {"a.json": b'{"a": 1}\n', "b.json": b'{"b": 2}\n'}
    manifest = _write_manifest(tmp_path, files)
    before = {name: (tmp_path / name).read_bytes() for name in files}

    records = reproduce.verify_manifest(tmp_path, manifest)

    assert [record.path for record in records] == ["a.json", "b.json"]
    assert {name: (tmp_path / name).read_bytes() for name in files} == before


def test_append_manifest_only_adds_new_immutable_records(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(reproduce, "ALLOWED_MANIFEST_ROOTS", (tmp_path.resolve(),))
    manifest = tmp_path / "manifest.json"
    (tmp_path / "a.json").write_bytes(b"a")
    first = reproduce.append_manifest(tmp_path, manifest)
    original_record = first[0]
    original_manifest = manifest.read_bytes()

    unchanged = reproduce.append_manifest(tmp_path, manifest)
    assert unchanged == first
    assert manifest.read_bytes() == original_manifest

    (tmp_path / "b.json").write_bytes(b"b")
    appended = reproduce.append_manifest(tmp_path, manifest)
    assert appended == (
        original_record,
        reproduce.ManifestRecord(
            path="b.json",
            bytes=1,
            sha256=reproduce.compute_sha256(tmp_path / "b.json"),
        ),
    )

    (tmp_path / "a.json").write_bytes(b"changed")
    with pytest.raises(
        reproduce.ManifestMismatchError, match=r"size mismatch: a\.json"
    ):
        reproduce.append_manifest(tmp_path, manifest)
    (tmp_path / "a.json").write_bytes(b"x")
    with pytest.raises(
        reproduce.ManifestMismatchError, match=r"SHA-256 mismatch: a\.json"
    ):
        reproduce.append_manifest(tmp_path, manifest)
    (tmp_path / "a.json").unlink()
    with pytest.raises(
        reproduce.ManifestMismatchError, match=r"missing artefacts: a\.json"
    ):
        reproduce.append_manifest(tmp_path, manifest)


def test_append_manifest_confines_destination(tmp_path: Path) -> None:
    with pytest.raises(
        reproduce.ReproductionConfigurationError, match="outside allowed roots"
    ):
        reproduce.append_manifest(tmp_path, Path("C:/unconfined/manifest.json"))


@pytest.mark.parametrize(
    ("mutation", "message"),
    [
        ("missing", "missing artefacts: a.json"),
        ("corrupt", "SHA-256 mismatch: a.json"),
        ("extra", "unmanifested artefacts: extra.json"),
    ],
)
def test_verify_manifest_fails_closed_on_inventory_tampering(
    tmp_path: Path, mutation: str, message: str
) -> None:
    manifest = _write_manifest(tmp_path, {"a.json": b"original"})
    if mutation == "missing":
        (tmp_path / "a.json").unlink()
    elif mutation == "corrupt":
        (tmp_path / "a.json").write_bytes(b"tampered")
    else:
        (tmp_path / "extra.json").write_text("{}", encoding="utf-8")

    with pytest.raises(reproduce.ManifestMismatchError, match=message):
        reproduce.verify_manifest(tmp_path, manifest)


def test_verify_manifest_detects_size_mismatch_before_hashing(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    manifest = _write_manifest(tmp_path, {"a.json": b"original"})
    payload = json.loads(manifest.read_text(encoding="utf-8"))
    payload["files"][0]["bytes"] = 99
    manifest.write_text(json.dumps(payload), encoding="utf-8")
    monkeypatch.setattr(
        reproduce,
        "compute_sha256",
        lambda _path: pytest.fail("hashing should not run after a size mismatch"),
    )

    with pytest.raises(
        reproduce.ManifestMismatchError, match=r"size mismatch: a\.json"
    ):
        reproduce.verify_manifest(tmp_path, manifest)


@pytest.mark.parametrize(
    ("payload", "message"),
    [
        ([], "manifest must be a JSON object"),
        ({"schema_version": 2, "files": []}, "schema_version must be 1"),
        ({"schema_version": 1, "files": {}}, "files must be a list"),
        ({"schema_version": 1, "files": ["bad"]}, r"files\[0\] must be"),
        (
            {
                "schema_version": 1,
                "files": [{"path": "../escape.json", "bytes": 1, "sha256": "a" * 64}],
            },
            "plain JSON filename",
        ),
        (
            {
                "schema_version": 1,
                "files": [{"path": "a.json", "bytes": True, "sha256": "a" * 64}],
            },
            "bytes must be a non-negative integer",
        ),
        (
            {
                "schema_version": 1,
                "files": [{"path": "a.json", "bytes": 1, "sha256": "bad"}],
            },
            "64 lowercase hexadecimal",
        ),
        (
            {
                "schema_version": 1,
                "files": [
                    {"path": "a.json", "bytes": 1, "sha256": "a" * 64},
                    {"path": "a.json", "bytes": 1, "sha256": "b" * 64},
                ],
            },
            "duplicate manifest path: a.json",
        ),
    ],
)
def test_load_manifest_rejects_malformed_records(
    tmp_path: Path, payload: object, message: str
) -> None:
    manifest = tmp_path / "manifest.json"
    manifest.write_text(json.dumps(payload), encoding="utf-8")
    with pytest.raises(reproduce.ManifestFormatError, match=message):
        reproduce.load_manifest(manifest)


def test_load_manifest_wraps_missing_and_invalid_json(tmp_path: Path) -> None:
    with pytest.raises(reproduce.ManifestFormatError, match="cannot read manifest"):
        reproduce.load_manifest(tmp_path / "missing.json")
    manifest = tmp_path / "manifest.json"
    manifest.write_text("{", encoding="utf-8")
    with pytest.raises(reproduce.ManifestFormatError, match="invalid JSON manifest"):
        reproduce.load_manifest(manifest)


def test_run_reproduction_selects_outputs_and_reports_files(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    manifest = _write_manifest(tmp_path, {"input.json": b"{}"})
    output = tmp_path / "output"
    figure = output / "figures" / "figure.png"
    table = output / "tables" / "table.tex"

    def generate_figures(_results: Path, target: Path) -> dict[str, list[Path]]:
        target.mkdir(parents=True, exist_ok=True)
        figure.write_bytes(b"png")
        return {"figure": [figure]}

    def generate_tables(_results: Path, target: Path) -> dict[str, Path]:
        target.mkdir(parents=True, exist_ok=True)
        table.write_text("table", encoding="utf-8")
        return {"table": table}

    monkeypatch.setattr(reproduce, "generate_all_figures", generate_figures)
    monkeypatch.setattr(reproduce, "generate_all_tables", generate_tables)

    result = reproduce.run_reproduction(
        results_dir=tmp_path,
        output_dir=output,
        manifest_path=manifest,
        verify=True,
    )
    figures_only = reproduce.run_reproduction(
        results_dir=tmp_path,
        output_dir=output,
        manifest_path=manifest,
        figures_only=True,
    )
    tables_only = reproduce.run_reproduction(
        results_dir=tmp_path,
        output_dir=output,
        manifest_path=manifest,
        tables_only=True,
    )

    assert result.manifest_records == 1
    assert result.generated_files == (figure, table)
    assert figures_only.generated_files == (figure,)
    assert tables_only.generated_files == (table,)


def test_run_reproduction_rejects_conflicting_modes(tmp_path: Path) -> None:
    with pytest.raises(
        reproduce.ReproductionConfigurationError, match="mutually exclusive"
    ):
        reproduce.run_reproduction(
            results_dir=tmp_path,
            output_dir=tmp_path,
            figures_only=True,
            tables_only=True,
        )


def test_main_verifies_before_generation_and_returns_failure(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    manifest = _write_manifest(tmp_path, {"input.json": b"original"})
    (tmp_path / "input.json").write_bytes(b"tampered")
    monkeypatch.setattr(
        reproduce,
        "generate_all_figures",
        lambda *_args: pytest.fail("generation must not run after failed verification"),
    )

    result = reproduce.main(
        [
            "--results-dir",
            str(tmp_path),
            "--output-dir",
            str(tmp_path / "output"),
            "--manifest",
            str(manifest),
            "--verify-manifest",
        ]
    )

    assert result == 1
    assert "SHA-256 mismatch" in capsys.readouterr().err


def test_main_append_manifest_mode_and_conflict(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    monkeypatch.setattr(reproduce, "ALLOWED_MANIFEST_ROOTS", (tmp_path.resolve(),))
    (tmp_path / "input.json").write_text("{}", encoding="utf-8")
    manifest = tmp_path / "manifest.json"
    args = [
        "--results-dir",
        str(tmp_path),
        "--manifest",
        str(manifest),
        "--append-manifest",
    ]
    assert reproduce.main(args) == 0
    assert "Manifest contains 1 stored JSON artefacts" in capsys.readouterr().out
    assert reproduce.main([*args, "--verify-manifest"]) == 1
    assert "cannot be combined" in capsys.readouterr().err


def test_main_success_prints_deterministic_file_manifest(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    manifest = _write_manifest(tmp_path, {"input.json": b"{}"})
    generated = tmp_path / "output" / "tables" / "table.tex"

    def generate_tables(_results: Path, target: Path) -> dict[str, Path]:
        target.mkdir(parents=True)
        generated.write_bytes(b"table")
        return {"table": generated}

    monkeypatch.setattr(reproduce, "generate_all_tables", generate_tables)

    result = reproduce.main(
        [
            "--tables-only",
            "--results-dir",
            str(tmp_path),
            "--output-dir",
            str(tmp_path / "output"),
            "--manifest",
            str(manifest),
            "--verify-manifest",
        ]
    )

    output = capsys.readouterr().out
    assert result == 0
    assert "Verified 1 stored JSON artefacts" in output
    assert "tables/table.tex" in output
    assert reproduce.compute_sha256(generated) in output
    assert "Generated 1 files" in output


def _probe_symlink_support() -> bool:
    """True iff this process can create a symlink in a temporary directory.

    Symlink creation needs elevated privilege or Developer Mode on Windows
    (GitHub-hosted `windows-latest` runners have it; an arbitrary local or
    self-hosted Windows host may not), so the PR23-F1 regression tests are
    gated on an executability probe rather than on a platform assumption —
    the same guard class as
    ``tests/test_exp001_driver.py::_probe_symlink_support``.
    """
    import tempfile

    with tempfile.TemporaryDirectory() as raw:
        directory = Path(raw)
        target = directory / "target"
        target.write_text("x", encoding="utf-8")
        link = directory / "link"
        try:
            link.symlink_to(target)
        except OSError:
            return False
        return True


_needs_symlink_support = pytest.mark.skipif(
    not _probe_symlink_support(),
    reason="creating symlinks is not permitted in this environment",
)


class TestManifestSymlinkProvenance:
    """PR23-F1 (Copilot, PR #23): the shared verifier must not follow links.

    ``verify_manifest`` previously established *content* integrity (the bytes
    at this path hash to the recorded digest) but not *path provenance*: its
    ``is_file()``, ``stat()``, and ``open()`` calls all follow symbolic links,
    so a manifest or artefact that was a link to a file outside the governed
    directory verified clean. ``benchmarks/campaign/exp001_driver.py``
    deliberately closed the same CWE-59 class in its own
    ``check_run_complete`` without modifying this shared tool; these tests pin
    the fix in the shared tool itself, which is the path
    ``DOCS/experiments/EXP-001-.../analysis/exp001_e4_analysis.py`` uses.
    """

    @_needs_symlink_support
    def test_verify_manifest_rejects_a_symlinked_artefact(self, tmp_path: Path) -> None:
        governed = tmp_path / "governed"
        governed.mkdir()
        outside = tmp_path / "outside.json"
        payload = b'{"a": 1}\n'
        outside.write_bytes(payload)
        manifest = {
            "schema_version": 1,
            "description": "test manifest",
            "source": "synthetic",
            "files": [
                {
                    "path": "a.json",
                    "bytes": len(payload),
                    "sha256": reproduce.compute_sha256(outside),
                }
            ],
        }
        manifest_path = governed / "manifest.json"
        manifest_path.write_text(json.dumps(manifest), encoding="utf-8")
        (governed / "a.json").symlink_to(outside)

        with pytest.raises(
            reproduce.ManifestMismatchError, match=r"manifested artefact.*symbolic link"
        ):
            reproduce.verify_manifest(governed, manifest_path)

    @_needs_symlink_support
    def test_verify_manifest_rejects_a_symlinked_manifest(self, tmp_path: Path) -> None:
        governed = tmp_path / "governed"
        governed.mkdir()
        outside_manifest = _write_manifest(tmp_path, {"a.json": b'{"a": 1}\n'})
        (governed / "a.json").write_bytes(b'{"a": 1}\n')
        link = governed / "manifest.json"
        link.symlink_to(outside_manifest)

        with pytest.raises(
            reproduce.ManifestMismatchError, match=r"manifest.*symbolic link"
        ):
            reproduce.verify_manifest(governed, link)

    @_needs_symlink_support
    def test_append_manifest_never_blesses_a_symlinked_artefact(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.setattr(reproduce, "ALLOWED_MANIFEST_ROOTS", (tmp_path.resolve(),))
        governed = tmp_path / "governed"
        governed.mkdir()
        outside = tmp_path / "outside.json"
        outside.write_bytes(b'{"a": 1}\n')
        (governed / "a.json").symlink_to(outside)
        manifest_path = governed / "manifest.json"

        with pytest.raises(
            reproduce.ManifestMismatchError, match=r"candidate artefact.*symbolic link"
        ):
            reproduce.append_manifest(governed, manifest_path)
        assert not manifest_path.exists()

    @_needs_symlink_support
    def test_append_manifest_rejects_a_symlinked_destination(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.setattr(reproduce, "ALLOWED_MANIFEST_ROOTS", (tmp_path.resolve(),))
        governed = tmp_path / "governed"
        governed.mkdir()
        (governed / "a.json").write_bytes(b'{"a": 1}\n')
        outside_manifest = tmp_path / "outside-manifest.json"
        outside_manifest.write_text("{}", encoding="utf-8")
        link = governed / "manifest.json"
        link.symlink_to(outside_manifest)

        with pytest.raises(
            reproduce.ManifestMismatchError, match=r"manifest.*symbolic link"
        ):
            reproduce.append_manifest(governed, link)
        assert outside_manifest.read_text(encoding="utf-8") == "{}"

    def test_regular_files_still_verify(self, tmp_path: Path) -> None:
        """The guard must not disturb the ordinary all-regular-files path."""
        manifest = _write_manifest(tmp_path, {"a.json": b'{"a": 1}\n'})
        assert [r.path for r in reproduce.verify_manifest(tmp_path, manifest)] == [
            "a.json"
        ]
