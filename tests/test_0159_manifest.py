"""Session-0159 evidence-bundle manifest regression tests.

These reuse the EA-007 manifest validators verbatim (imported as
``test_ea007_manifest``; pytest puts ``tests/`` on ``sys.path``) with the
0159 root, manifest path, unhashed-by-design exemptions and git prefix
monkeypatched in. Positive cases run against the real bundle and the real
Git index — never a stub. Negative cases run against controlled throwaway
manifest/file fixtures so the real evidence is never mutated.

The bundle layout mirrors EA-007: ``EVIDENCE/0159/verification/`` holds the
byte-exact captures and ``SHA256SUMS.txt``; the top-level ``README.md``
(the editable narrative index) and the manifest itself are the only
unhashed-by-design files. Entries are relative to ``verification/``; the
frozen E1 entry observations are hashed through the ``../entry-state.json``
relative entry.
"""

from __future__ import annotations

import hashlib
import subprocess
from pathlib import Path

import pytest
import test_ea007_manifest as ea007

REPO_ROOT = Path(__file__).resolve().parents[1]
EVIDENCE_ROOT = REPO_ROOT / "EVIDENCE" / "0159"
MANIFEST_DIR = "verification"
MANIFEST = EVIDENCE_ROOT / MANIFEST_DIR / "SHA256SUMS.txt"
_UNHASHED_BY_DESIGN = {"README.md", f"{MANIFEST_DIR}/SHA256SUMS.txt"}

# The complete set of bundle files the manifest and Git index must cover.
# Exact-case POSIX paths relative to EVIDENCE/0159/.
REQUIRED_BUNDLE = {
    "README.md",
    "entry-state.json",
    f"{MANIFEST_DIR}/README.md",
    f"{MANIFEST_DIR}/SHA256SUMS.txt",
    f"{MANIFEST_DIR}/0159-focused-campaign-quality-gates.log",
    f"{MANIFEST_DIR}/0159-focused-ea007-manifest.log",
    f"{MANIFEST_DIR}/0159-ps51-parse-check.log",
    f"{MANIFEST_DIR}/0159-ps51-parse-check.ps1",
    f"{MANIFEST_DIR}/0159-driver-lint-type.log",
    f"{MANIFEST_DIR}/0159-driver-pytest-coverage.log",
    f"{MANIFEST_DIR}/0159-driver-coverage.json",
    f"{MANIFEST_DIR}/0159-driver-final-lint-type.log",
    f"{MANIFEST_DIR}/0159-driver-final-pytest-coverage.log",
    f"{MANIFEST_DIR}/0159-driver-final-coverage.json",
    f"{MANIFEST_DIR}/0159-driver-initial-red-run.log",
    f"{MANIFEST_DIR}/source-hashes.txt",
    # Full-gate capture set (EVIDENCE/0159/verification/full-gate/): every
    # closed leg log from the 7859030 gate including failed/interrupted
    # attempts, diagnostics, correction-verification logs, the corrected
    # Snyk scans and copy attestation, the redacted gitleaks report, the
    # interrupted full-suite raw prefix and resumption note, the
    # lead-authored validation recipes and proof log, the status matrix,
    # and the operator note for the 09c inventory failure.
    f"{MANIFEST_DIR}/full-gate/01-ruff-check.log",
    f"{MANIFEST_DIR}/full-gate/02-ruff-format-check.log",
    f"{MANIFEST_DIR}/full-gate/03-ruff-format-check-experiments.log",
    f"{MANIFEST_DIR}/full-gate/04-mypy-prin.log",
    f"{MANIFEST_DIR}/full-gate/05-mypy-experiments.log",
    f"{MANIFEST_DIR}/full-gate/06-mypy-exp002-driver.log",
    f"{MANIFEST_DIR}/full-gate/07-interrogate.log",
    f"{MANIFEST_DIR}/full-gate/08-bandit.log",
    f"{MANIFEST_DIR}/full-gate/09-pytest-fast.log",
    f"{MANIFEST_DIR}/full-gate/09b-pytest-fast-crash-diagnostic.log",
    f"{MANIFEST_DIR}/full-gate/09c-pytest-fast-rerun.log",
    f"{MANIFEST_DIR}/full-gate/09d-pytest-fast-diagnostic.log",
    f"{MANIFEST_DIR}/full-gate/10-cargo-fmt.log",
    f"{MANIFEST_DIR}/full-gate/11-cargo-clippy.log",
    f"{MANIFEST_DIR}/full-gate/12-cargo-clippy-strict.log",
    f"{MANIFEST_DIR}/full-gate/13-cargo-test.log",
    f"{MANIFEST_DIR}/full-gate/14-cargo-test-strict.log",
    f"{MANIFEST_DIR}/full-gate/15-cargo-llvm-cov-kernels.log",
    f"{MANIFEST_DIR}/full-gate/16-cargo-llvm-cov-dynamics.log",
    f"{MANIFEST_DIR}/full-gate/17-cargo-llvm-cov-dynamics-strict.log",
    f"{MANIFEST_DIR}/full-gate/18-cargo-doc.log",
    f"{MANIFEST_DIR}/full-gate/19-cargo-doc-prin-sim-cpu.log",
    f"{MANIFEST_DIR}/full-gate/20-cargo-audit.log",
    f"{MANIFEST_DIR}/full-gate/21-pip-audit.log",
    f"{MANIFEST_DIR}/full-gate/22-pip-audit-sphinx.log",
    f"{MANIFEST_DIR}/full-gate/23-snyk-code.log",
    f"{MANIFEST_DIR}/full-gate/24-gitleaks.log",
    f"{MANIFEST_DIR}/full-gate/24b-snyk-code-correction.log",
    f"{MANIFEST_DIR}/full-gate/24c-snyk-code-final.log",
    f"{MANIFEST_DIR}/full-gate/25-pytest-full-interrupted.log",
    f"{MANIFEST_DIR}/full-gate/25-pytest-full-raw-prefix.log",
    f"{MANIFEST_DIR}/full-gate/25-pytest-full-resumption-note.md",
    f"{MANIFEST_DIR}/full-gate/c01-focused-pytest-correction.log",
    f"{MANIFEST_DIR}/full-gate/c02-focused-pytest-correction.log",
    f"{MANIFEST_DIR}/full-gate/c03-focused-pytest-correction.log",
    f"{MANIFEST_DIR}/full-gate/c04-focused-pytest-correction.log",
    f"{MANIFEST_DIR}/full-gate/c05-focused-pytest-correction.log",
    f"{MANIFEST_DIR}/full-gate/0159-driver-correction-coverage.json",
    f"{MANIFEST_DIR}/full-gate/correction-source-hashes.txt",
    f"{MANIFEST_DIR}/full-gate/sast-copy-attestation.txt",
    f"{MANIFEST_DIR}/full-gate/gitleaks-7859030.json",
    f"{MANIFEST_DIR}/full-gate/GATE-STATUS.md",
    f"{MANIFEST_DIR}/full-gate/README.md",
    f"{MANIFEST_DIR}/full-gate/09c-inventory-failure-facts.md",
    f"{MANIFEST_DIR}/full-gate/0159-publication-validation-proposal.py.txt",
    f"{MANIFEST_DIR}/full-gate/0159-publication-validation-proof.py.txt",
    f"{MANIFEST_DIR}/full-gate/0159-publication-validation-proof.log",
    # Final local-gate capture set on source 6314532
    # (EVIDENCE/0159/verification/final-6314532/): headed leg logs from the
    # external capture root, both FULL attempts plus the isolated
    # diagnostic, the coverage JSON, the gitleaks report with its empty
    # SESSION shallow-file, and the nested index.
    f"{MANIFEST_DIR}/final-6314532/00-environment.log",
    f"{MANIFEST_DIR}/final-6314532/01-ruff-narrow.log",
    f"{MANIFEST_DIR}/final-6314532/02-focused-pytest.log",
    f"{MANIFEST_DIR}/final-6314532/03-pytest-fast.log",
    f"{MANIFEST_DIR}/final-6314532/04-pytest-full.log",
    f"{MANIFEST_DIR}/final-6314532/04b-error-diagnostic.log",
    f"{MANIFEST_DIR}/final-6314532/04c-pytest-full-isolated.log",
    f"{MANIFEST_DIR}/final-6314532/05-sphinx.log",
    f"{MANIFEST_DIR}/final-6314532/06-governance.log",
    f"{MANIFEST_DIR}/final-6314532/07-gitleaks.log",
    f"{MANIFEST_DIR}/final-6314532/focused-coverage.json",
    f"{MANIFEST_DIR}/final-6314532/gitleaks-6314532.json",
    f"{MANIFEST_DIR}/final-6314532/SESSION",
    f"{MANIFEST_DIR}/final-6314532/README.md",
    # Post-packaging controls captured on 6314532 after the bundle/index was
    # completed (PR33-F6: omitted here before the PR #33 review audit, which
    # let a file be deleted together with its manifest line undetected).
    f"{MANIFEST_DIR}/final-6314532/08-manifest-tests-postpackage.log",
    f"{MANIFEST_DIR}/final-6314532/08b-snyk-manifest-test.log",
    f"{MANIFEST_DIR}/final-6314532/09-sphinx-postchangelog.log",
    f"{MANIFEST_DIR}/final-6314532/10-sphinx-final-fullcapture.log",
    f"{MANIFEST_DIR}/final-6314532/11-manifest-tests-final.log",
    f"{MANIFEST_DIR}/final-6314532/sast-e-copy-attestation.txt",
    # PR #33 review-round evidence (EVIDENCE/0159/verification/pr33-review/):
    # ground-truth probes before/after the fix, the mutation proof, the local
    # gate captures and the read-only delegated reviews.
    f"{MANIFEST_DIR}/pr33-review/G01-ruff-check.log",
    f"{MANIFEST_DIR}/pr33-review/G02-ruff-format-check.log",
    f"{MANIFEST_DIR}/pr33-review/G03-ruff-format-check-experiments.log",
    f"{MANIFEST_DIR}/pr33-review/G04-mypy-prin.log",
    f"{MANIFEST_DIR}/pr33-review/G05-mypy-experiments.log",
    f"{MANIFEST_DIR}/pr33-review/G06-mypy-exp002-driver.log",
    f"{MANIFEST_DIR}/pr33-review/G07-interrogate.log",
    f"{MANIFEST_DIR}/pr33-review/G08-bandit.log",
    f"{MANIFEST_DIR}/pr33-review/G09-focused-coverage.json",
    f"{MANIFEST_DIR}/pr33-review/G09-focused-pytest.log",
    f"{MANIFEST_DIR}/pr33-review/G09a-focused-pytest-winerror32.log",
    f"{MANIFEST_DIR}/pr33-review/G10-governance-deviation-ledger.log",
    f"{MANIFEST_DIR}/pr33-review/G10b-governance-dv-gates.log",
    f"{MANIFEST_DIR}/pr33-review/G10c-governance-session-registration.log",
    f"{MANIFEST_DIR}/pr33-review/G10d-governance-skipif-probes.log",
    f"{MANIFEST_DIR}/pr33-review/G10e-governance-wp001.log",
    f"{MANIFEST_DIR}/pr33-review/G10f-git-diff-check.log",
    f"{MANIFEST_DIR}/pr33-review/G11-sphinx.log",
    f"{MANIFEST_DIR}/pr33-review/G12-pytest-fast.log",
    f"{MANIFEST_DIR}/pr33-review/G12a-pytest-fast-ignore-guard-failure.log",
    f"{MANIFEST_DIR}/pr33-review/G13-pytest-full.log",
    f"{MANIFEST_DIR}/pr33-review/G13a-error-node-diagnostic.log",
    f"{MANIFEST_DIR}/pr33-review/G13b-pytest-full-rerun.log",
    f"{MANIFEST_DIR}/pr33-review/G14-sast-copy-attestation.txt",
    f"{MANIFEST_DIR}/pr33-review/G14-snyk-code.log",
    f"{MANIFEST_DIR}/pr33-review/G14a-sast-copy-attestation.txt",
    f"{MANIFEST_DIR}/pr33-review/G14a-snyk-code-initial.log",
    f"{MANIFEST_DIR}/pr33-review/G15-gitleaks-full-history.log",
    f"{MANIFEST_DIR}/pr33-review/G15b-gitleaks-staged.log",
    f"{MANIFEST_DIR}/pr33-review/G16-postpackage-manifest-and-driver-tests.log",
    f"{MANIFEST_DIR}/pr33-review/G16a-postpackage-wrong-interpreter.log",
    f"{MANIFEST_DIR}/pr33-review/P1-ground-truth-probes-78d3600.log",
    f"{MANIFEST_DIR}/pr33-review/P1b-ground-truth-probes-p9-symlink-78d3600.log",
    f"{MANIFEST_DIR}/pr33-review/P1c-ground-truth-probes-remediated.log",
    f"{MANIFEST_DIR}/pr33-review/P1d-ground-truth-probes-p9-symlink-remediated.log",
    f"{MANIFEST_DIR}/pr33-review/P2-mutation-proof.log",
    f"{MANIFEST_DIR}/pr33-review/README.md",
    f"{MANIFEST_DIR}/pr33-review/delegation/agy-ground-truth-docs-report.txt",
    f"{MANIFEST_DIR}/pr33-review/delegation/agy-ground-truth-task.md",
    f"{MANIFEST_DIR}/pr33-review/delegation/agy-selfaudit-report.txt",
    f"{MANIFEST_DIR}/pr33-review/delegation/agy-selfaudit-task.md",
    f"{MANIFEST_DIR}/pr33-review/delegation/devin-ground-truth-code-report.txt",
    f"{MANIFEST_DIR}/pr33-review/delegation/devin-ground-truth-task.md",
    f"{MANIFEST_DIR}/pr33-review/delegation/devin-selfaudit-report.txt",
    f"{MANIFEST_DIR}/pr33-review/delegation/devin-selfaudit-task.md",
    f"{MANIFEST_DIR}/pr33-review/gitleaks-history-78d3600.json",
    f"{MANIFEST_DIR}/pr33-review/gitleaks-staged-remediation.json",
    f"{MANIFEST_DIR}/pr33-review/ground-truth-probes-p9-symlink.py.txt",
    f"{MANIFEST_DIR}/pr33-review/ground-truth-probes.py.txt",
    f"{MANIFEST_DIR}/pr33-review/proof_defect_catching.py",
    f"{MANIFEST_DIR}/pr33-review/proof_plugin.py",
}


def _unrequired_entries(entries: set[str], required: set[str]) -> set[str]:
    """Manifest entries that the immutable required set does not name."""
    return entries - (required - _UNHASHED_BY_DESIGN)


def _git_tracked_0159() -> set[str] | None:
    """Files git tracks under `EVIDENCE/0159/` (exact case), or None."""
    try:
        listing = subprocess.run(
            ["git", "ls-files", "-z", "--", "EVIDENCE/0159"],
            cwd=REPO_ROOT,
            capture_output=True,
            check=True,
        ).stdout
    except (OSError, subprocess.CalledProcessError):
        return None
    prefix = "EVIDENCE/0159/"
    return {
        name[len(prefix) :]
        for name in listing.decode("utf-8").split("\0")
        if name.startswith(prefix)
    }


@pytest.fixture
def real_bundle(monkeypatch: pytest.MonkeyPatch) -> None:
    """Point the imported EA-007 validators at the real 0159 bundle."""
    monkeypatch.setattr(ea007, "EVIDENCE_ROOT", EVIDENCE_ROOT)
    monkeypatch.setattr(ea007, "MANIFEST_DIR", MANIFEST_DIR)
    monkeypatch.setattr(ea007, "MANIFEST", MANIFEST)
    monkeypatch.setattr(ea007, "_UNHASHED_BY_DESIGN", set(_UNHASHED_BY_DESIGN))
    monkeypatch.setattr(ea007, "_git_tracked", _git_tracked_0159)


@pytest.mark.usefixtures("real_bundle")
class TestRealBundle:
    def test_required_files_present_with_exact_case(self) -> None:
        missing = [
            relative
            for relative in REQUIRED_BUNDLE
            if not (EVIDENCE_ROOT / relative).is_file()
        ]
        assert not missing, f"bundle files missing: {missing}"

    def test_manifest_entries_cover_required_files(self) -> None:
        entries = set(ea007._entries())
        expected_hashed = REQUIRED_BUNDLE - _UNHASHED_BY_DESIGN
        missing = expected_hashed - entries
        assert not missing, f"required files absent from manifest: {missing}"
        # The unhashed-by-design narrative and manifest are never hashed.
        assert entries.isdisjoint(_UNHASHED_BY_DESIGN)

    def test_manifest_entries_are_all_required(self) -> None:
        """PR33-F6: the manifest may hash nothing ``REQUIRED_BUNDLE`` omits.

        Together with ``test_manifest_entries_cover_required_files`` this makes
        the manifest exactly the required hashed set, so deleting a file *and*
        its manifest line can no longer pass unnoticed.
        """
        extra = _unrequired_entries(set(ea007._entries()), REQUIRED_BUNDLE)
        assert not extra, f"manifest entries missing from REQUIRED_BUNDLE: {extra}"

    def test_every_manifest_entry_matches_the_committed_bytes(self) -> None:
        ea007.test_every_manifest_entry_matches_the_committed_bytes()

    def test_manifest_covers_every_evidence_file(self) -> None:
        ea007.test_manifest_covers_every_evidence_file()

    def test_every_hashed_evidence_file_is_tracked_by_git(self) -> None:
        ea007.test_every_hashed_evidence_file_is_tracked_by_git()


def _fixture_bundle(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    *,
    files: dict[str, bytes],
    manifest_lines: list[str],
) -> Path:
    """A throwaway 0159-shaped bundle under ``tmp_path``."""
    root = tmp_path / "bundle"
    manifest_dir = root / MANIFEST_DIR
    manifest_dir.mkdir(parents=True)
    for relative, payload in files.items():
        path = root / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(payload)
    (manifest_dir / "SHA256SUMS.txt").write_text(
        "\n".join(manifest_lines) + "\n", encoding="utf-8"
    )
    monkeypatch.setattr(ea007, "EVIDENCE_ROOT", root)
    monkeypatch.setattr(ea007, "MANIFEST_DIR", MANIFEST_DIR)
    monkeypatch.setattr(ea007, "MANIFEST", manifest_dir / "SHA256SUMS.txt")
    monkeypatch.setattr(ea007, "_UNHASHED_BY_DESIGN", set(_UNHASHED_BY_DESIGN))
    return root


def _line(relative: str, payload: bytes) -> str:
    return f"{hashlib.sha256(payload).hexdigest()} *./{relative}"


class TestControlledNegatives:
    def test_changed_bytes_fail(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        _fixture_bundle(
            tmp_path,
            monkeypatch,
            files={"verification/capture.log": b"changed bytes"},
            manifest_lines=[_line("capture.log", b"original bytes")],
        )
        with pytest.raises(AssertionError, match="digest mismatch"):
            ea007.test_every_manifest_entry_matches_the_committed_bytes()

    def test_omitted_file_fails(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        _fixture_bundle(
            tmp_path,
            monkeypatch,
            files={
                "README.md": b"i",
                "verification/capture.log": b"x",
                "verification/unlisted.log": b"y",
            },
            manifest_lines=[_line("capture.log", b"x")],
        )
        with pytest.raises(AssertionError, match="absent from SHA256SUMS"):
            ea007.test_manifest_covers_every_evidence_file()

    def test_wrong_case_fails(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        _fixture_bundle(
            tmp_path,
            monkeypatch,
            files={"verification/capture.log": b"x"},
            manifest_lines=[_line("CAPTURE.LOG", b"x")],
        )
        with pytest.raises(AssertionError, match="missing file"):
            ea007.test_every_manifest_entry_matches_the_committed_bytes()

    @pytest.mark.parametrize(
        "lines",
        [
            ["not-a-manifest-line"],
            [f"{'0' * 64} */absolute/path.log"],
            [f"{'0' * 64} *../../escape.log"],
            [f"{'0' * 64} *.\\windows\\separator.log"],
        ],
        ids=["malformed", "absolute", "escaping", "windows-separator"],
    )
    def test_malformed_manifest_lines_fail(
        self,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
        lines: list[str],
    ) -> None:
        _fixture_bundle(
            tmp_path,
            monkeypatch,
            files={"verification/a.log": b"a"},
            manifest_lines=lines,
        )
        with pytest.raises(AssertionError):
            ea007._entries()

    def test_duplicate_entry_fails(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        _fixture_bundle(
            tmp_path,
            monkeypatch,
            files={"verification/a.log": b"a"},
            manifest_lines=[_line("a.log", b"a"), _line("a.log", b"a")],
        )
        with pytest.raises(AssertionError, match="duplicate"):
            ea007._entries()

    def test_parent_relative_entry_reaches_top_level(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """The ``../entry-state.json`` mechanism hashes a top-level file."""
        _fixture_bundle(
            tmp_path,
            monkeypatch,
            files={
                "entry-state.json": b"frozen",
                "verification/a.log": b"a",
            },
            manifest_lines=[
                f"{hashlib.sha256(b'frozen').hexdigest()} *../entry-state.json",
                _line("a.log", b"a"),
            ],
        )
        assert set(ea007._entries()) == {
            "entry-state.json",
            "verification/a.log",
        }

    def test_missing_file_fails(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        _fixture_bundle(
            tmp_path,
            monkeypatch,
            files={"verification/a.log": b"a"},
            manifest_lines=[_line("ghost.log", b"g")],
        )
        with pytest.raises(AssertionError, match="missing file"):
            ea007.test_every_manifest_entry_matches_the_committed_bytes()

    def test_unhashed_narrative_absent_fails(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        _fixture_bundle(
            tmp_path,
            monkeypatch,
            files={"verification/a.log": b"a"},
            manifest_lines=[_line("a.log", b"a")],
        )
        with pytest.raises(AssertionError, match="unhashed-by-design"):
            ea007.test_manifest_covers_every_evidence_file()

    def test_double_deletion_is_caught(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """PR33-F6 regression: a required file deleted with its manifest line."""
        _fixture_bundle(
            tmp_path,
            monkeypatch,
            files={"README.md": b"i", "verification/kept.log": b"k"},
            manifest_lines=[_line("kept.log", b"k")],
        )
        required = {"README.md", "verification/kept.log", "verification/gone.log"}
        entries = set(ea007._entries())
        assert required - _UNHASHED_BY_DESIGN - entries == {"verification/gone.log"}
        # The superset direction alone (the pre-fix state) would not notice:
        assert not _unrequired_entries(entries, required)

    def test_unrequired_manifest_entry_is_caught(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        _fixture_bundle(
            tmp_path,
            monkeypatch,
            files={"verification/a.log": b"a", "verification/late.log": b"l"},
            manifest_lines=[_line("a.log", b"a"), _line("late.log", b"l")],
        )
        assert _unrequired_entries(set(ea007._entries()), {"verification/a.log"}) == {
            "verification/late.log"
        }

    def test_hashed_but_untracked_log_fails(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        _fixture_bundle(
            tmp_path,
            monkeypatch,
            files={
                "README.md": b"index",
                "verification/README.md": b"sub-index",
                "verification/rogue.log": b"r",
            },
            manifest_lines=[
                _line("README.md", b"sub-index"),
                _line("rogue.log", b"r"),
            ],
        )
        tracked = {
            "README.md",
            "verification/README.md",
            "verification/SHA256SUMS.txt",
        }
        monkeypatch.setattr(ea007, "_git_tracked", lambda: tracked)
        with pytest.raises(AssertionError, match="not tracked"):
            ea007.test_every_hashed_evidence_file_is_tracked_by_git()
