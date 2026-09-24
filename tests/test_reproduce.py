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


def test_allowed_manifest_roots_does_not_transitively_admit_the_checkout() -> None:
    """CodeRabbit follow-up review, PR #23 head `d9d4f2a`: the temp-directory
    entry in ``ALLOWED_MANIFEST_ROOTS`` must not transitively legitimize the
    whole checkout. Containment walks every ancestor, so if the checkout
    itself were under the temp root, admitting the temp root would silently
    admit every file in the checkout, including this module's own source.
    """
    checkout_root = reproduce._REPOSITORY_ROOT.resolve()
    for root in reproduce.ALLOWED_MANIFEST_ROOTS:
        assert not (root == checkout_root or root in checkout_root.parents)


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
    # PR23-F (Copilot follow-up review): size+hash now come from a single
    # no-follow-opened descriptor (`_verify_size_and_hash_no_follow`), so the
    # short-circuit is pinned against the function that actually hashes,
    # `_hash_fd` — patching the (now unrelated) public `compute_sha256` would
    # no longer be exercised by this path and the test would pass vacuously.
    monkeypatch.setattr(
        reproduce,
        "_hash_fd",
        lambda _fd: pytest.fail("hashing should not run after a size mismatch"),
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

        # Caught during the inventory scan (PR23-F: every `*.json` candidate is
        # now rejected up front, not just manifested paths individually), so
        # the role in the message is "candidate artefact" rather than
        # "manifested artefact" — both roles reject the same symlink, this is
        # just which pass reaches it first.
        with pytest.raises(
            reproduce.ManifestMismatchError, match=r"candidate artefact.*symbolic link"
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

    @_needs_symlink_support
    def test_verify_manifest_rejects_an_unmanifested_symlink(
        self, tmp_path: Path
    ) -> None:
        """PR23-F (Copilot follow-up review): a stray symlink must fail closed.

        Before this fix, ``actual`` was built with ``is_file()``, which
        follows links: a symlink named ``rogue.json`` that points at a
        directory (or a broken target) is not a file post-resolution, so it
        silently dropped out of the inventory instead of tripping "unmanifested
        artefacts" — the fail-closed guarantee held for content but not for an
        untracked link sitting in the governed directory.
        """
        governed = tmp_path / "governed"
        governed.mkdir()
        manifest = _write_manifest(governed, {"a.json": b'{"a": 1}\n'})
        outside_dir = tmp_path / "outside"
        outside_dir.mkdir()
        (governed / "rogue.json").symlink_to(outside_dir)

        with pytest.raises(
            reproduce.ManifestMismatchError, match=r"candidate artefact.*symbolic link"
        ):
            reproduce.verify_manifest(governed, manifest)

    def test_regular_files_still_verify(self, tmp_path: Path) -> None:
        """The guard must not disturb the ordinary all-regular-files path."""
        manifest = _write_manifest(tmp_path, {"a.json": b'{"a": 1}\n'})
        assert [r.path for r in reproduce.verify_manifest(tmp_path, manifest)] == [
            "a.json"
        ]

    def test_verify_manifest_rejects_a_directory_named_like_json(
        self, tmp_path: Path
    ) -> None:
        """PR23-F (Copilot follow-up review, "previously missed"): non-symlink,
        non-regular inventory entries must also fail closed.

        A directory named ``rogue.json`` is not a symlink, so
        ``_reject_symlink`` alone would not catch it, and the later
        ``is_file()`` filter would silently drop it from the inventory — the
        same failure mode as an unmanifested symlink, for a different reason.
        """
        governed = tmp_path / "governed"
        governed.mkdir()
        manifest = _write_manifest(governed, {"a.json": b'{"a": 1}\n'})
        (governed / "rogue.json").mkdir()

        with pytest.raises(
            reproduce.ManifestMismatchError,
            match=r"candidate artefact.*not a regular file",
        ):
            reproduce.verify_manifest(governed, manifest)

    def test_append_manifest_rejects_a_directory_named_like_json(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.setattr(reproduce, "ALLOWED_MANIFEST_ROOTS", (tmp_path.resolve(),))
        governed = tmp_path / "governed"
        governed.mkdir()
        (governed / "a.json").write_bytes(b'{"a": 1}\n')
        (governed / "rogue.json").mkdir()
        manifest_path = governed / "manifest.json"

        with pytest.raises(
            reproduce.ManifestMismatchError,
            match=r"candidate artefact.*not a regular file",
        ):
            reproduce.append_manifest(governed, manifest_path)
        assert not manifest_path.exists()

    def test_verify_manifest_rejects_a_manifest_path_that_is_a_directory(
        self, tmp_path: Path
    ) -> None:
        """PR23-F (Copilot follow-up review, PR #23 head `900a68f`): the
        manifest path itself, not just candidate artefacts, must be rejected
        when it is not a regular file.

        Before this fix, ``verify_manifest``/``append_manifest`` only
        ``_reject_symlink``'d the manifest path (a symlink-only check), so a
        FIFO there would hang inside ``load_manifest``'s blocking open, and a
        directory there would reach ``write_no_follow`` and fail as a raw
        ``OSError`` rather than the documented ``ManifestMismatchError``.
        """
        governed = tmp_path / "governed"
        governed.mkdir()
        (governed / "manifest.json").mkdir()

        with pytest.raises(
            reproduce.ManifestMismatchError, match=r"manifest.*not a regular file"
        ):
            reproduce.verify_manifest(governed, governed / "manifest.json")

    def test_append_manifest_rejects_a_manifest_path_that_is_a_directory(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """The manifest destination lives *outside* ``results_dir`` here (the
        realistic shape — see ``DEFAULT_MANIFEST``/``DEFAULT_RESULTS_DIR``),
        so it is never swept up by the ``results_dir`` candidate scan that
        already rejects a non-regular candidate there (`PR23-F17`). Only the
        manifest-path check this test targets can catch it.
        """
        monkeypatch.setattr(reproduce, "ALLOWED_MANIFEST_ROOTS", (tmp_path.resolve(),))
        governed = tmp_path / "governed"
        governed.mkdir()
        (governed / "a.json").write_bytes(b'{"a": 1}\n')
        manifest_path = tmp_path / "manifest-dir" / "manifest.json"
        manifest_path.mkdir(parents=True)

        with pytest.raises(
            reproduce.ManifestMismatchError, match=r"manifest.*not a regular file"
        ):
            reproduce.append_manifest(governed, manifest_path)

    def test_append_manifest_writes_through_the_unresolved_manifest_path(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """PR23-F (Copilot follow-up review): I/O must use ``manifest_path``, not
        a ``.resolve()`` of it.

        Before this fix, ``destination = manifest_path.resolve()`` was reused
        for the containment check *and* every subsequent read/write. A
        concurrent symlink swap of the final path component between the
        initial ``_reject_symlink`` check and that ``.resolve()`` call would
        have made every later read/write silently follow the swapped-in
        link. Proven here without a real race: ``Path.resolve`` is patched so
        that resolving ``manifest_path`` specifically returns a decoy path
        that is still inside the allowed roots (so containment still
        passes), and the manifest is confirmed to land at the real
        ``manifest_path`` — never at the decoy ``.resolve()`` returned.
        """
        allowed_root = tmp_path.resolve()
        monkeypatch.setattr(reproduce, "ALLOWED_MANIFEST_ROOTS", (allowed_root,))
        governed = tmp_path / "governed"
        governed.mkdir()
        (governed / "a.json").write_bytes(b'{"a": 1}\n')
        manifest_path = governed / "manifest.json"
        decoy = allowed_root / "decoy-manifest.json"
        real_resolve = Path.resolve

        def fake_resolve(self: Path, strict: bool = False) -> Path:
            if str(self) == str(manifest_path):
                return decoy
            return real_resolve(self, strict)

        monkeypatch.setattr(Path, "resolve", fake_resolve)

        reproduce.append_manifest(governed, manifest_path)

        assert manifest_path.is_file()
        assert not decoy.exists()


class TestOpenNoFollow:
    """PR23-F (Copilot follow-up review): close the check-then-open race.

    ``_reject_symlink`` alone is a check-then-use probe: a concurrent writer
    can replace a regular file with a symlink between the check and a later
    ``stat()``/``open()``. ``_open_no_follow`` (and the helpers built on it)
    fold the check into the ``open()`` itself on POSIX via ``O_NOFOLLOW``, so
    there is no such window there; these tests pin that behaviour directly
    rather than through the higher-level manifest functions.
    """

    def test_regular_file_opens_and_reads(self, tmp_path: Path) -> None:
        target = tmp_path / "a.json"
        target.write_bytes(b'{"a": 1}\n')
        assert reproduce.read_no_follow(target, "artefact") == b'{"a": 1}\n'

    def test_stat_size_and_hash_match_compute_sha256(self, tmp_path: Path) -> None:
        target = tmp_path / "a.json"
        payload = b'{"a": 1}\n'
        target.write_bytes(payload)
        size, digest = reproduce.stat_size_and_hash_no_follow(target, "artefact")
        assert size == len(payload)
        assert digest == reproduce.compute_sha256(target)

    @_needs_symlink_support
    def test_symlink_is_rejected_at_open(self, tmp_path: Path) -> None:
        outside = tmp_path / "outside.json"
        outside.write_bytes(b"{}")
        link = tmp_path / "link.json"
        link.symlink_to(outside)

        with pytest.raises(reproduce.ManifestMismatchError, match="symbolic link"):
            reproduce._open_no_follow(link, "artefact")


class TestWriteNoFollow:
    """PR23-F (Copilot follow-up review): the write-side no-follow mirror.

    ``Path.write_text``/``write_bytes`` follow a symlink at the destination,
    so a caller that resolved and contained a destination path but then wrote
    to it with a plain ``write_text`` call could have the write silently
    redirected if the destination were swapped for a symlink between the
    containment check and the write.
    """

    def test_writes_a_new_file(self, tmp_path: Path) -> None:
        target = tmp_path / "out.json"
        reproduce.write_no_follow(target, b'{"a": 1}\n', "generated output")
        assert target.read_bytes() == b'{"a": 1}\n'

    def test_truncates_an_existing_file(self, tmp_path: Path) -> None:
        target = tmp_path / "out.json"
        target.write_bytes(b"a much longer previous payload\n")
        reproduce.write_no_follow(target, b"{}\n", "generated output")
        assert target.read_bytes() == b"{}\n"

    @_needs_symlink_support
    def test_refuses_to_write_through_a_symlinked_destination(
        self, tmp_path: Path
    ) -> None:
        outside = tmp_path / "outside.json"
        outside.write_bytes(b"original\n")
        link = tmp_path / "link.json"
        link.symlink_to(outside)

        with pytest.raises(reproduce.ManifestMismatchError, match="symbolic link"):
            reproduce.write_no_follow(
                link, b"attacker-controlled\n", "generated output"
            )
        assert outside.read_bytes() == b"original\n"
