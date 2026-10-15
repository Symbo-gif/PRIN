"""Session-0160 (EXP-002 E2) evidence-bundle manifest regression tests.

The same EA-007 validators as ``test_0159_manifest.py``, pointed at
``EVIDENCE/0160/``: every hashed file matches its committed bytes, every file
is hashed (except the two unhashed-by-design files), every hashed file is
tracked by git, and the manifest equals the immutable ``REQUIRED_BUNDLE``
exactly, so a file deleted together with its manifest line cannot pass
unnoticed (the PR33-F6 lesson).
"""

from __future__ import annotations

import subprocess
from pathlib import Path

import pytest
import test_ea007_manifest as ea007

REPO_ROOT = Path(__file__).resolve().parents[1]
EVIDENCE_ROOT = REPO_ROOT / "EVIDENCE" / "0160"
MANIFEST_DIR = "verification"
MANIFEST = EVIDENCE_ROOT / MANIFEST_DIR / "SHA256SUMS.txt"
_UNHASHED_BY_DESIGN = {"README.md", f"{MANIFEST_DIR}/SHA256SUMS.txt"}

# Exact-case POSIX paths relative to EVIDENCE/0160/.
REQUIRED_BUNDLE = {
    "README.md",
    f"{MANIFEST_DIR}/SHA256SUMS.txt",
    # bundle-start
    f"{MANIFEST_DIR}/ci-fixes/C1-hosted-python-lint-38184181265.log",
    f"{MANIFEST_DIR}/ci-fixes/C2-hosted-rust-clippy-38184181298.log",
    f"{MANIFEST_DIR}/ci-fixes/C3a-mypy-experiments-without-numpy.log",
    f"{MANIFEST_DIR}/ci-fixes/C3b-mypy-prin-without-numpy.log",
    f"{MANIFEST_DIR}/ci-fixes/C3c-mypy-experiments-with-numpy.log",
    f"{MANIFEST_DIR}/ci-fixes/C3d-mypy-prin-with-numpy.log",
    f"{MANIFEST_DIR}/ci-fixes/H1-forced-nightly-38184198596.json",
    f"{MANIFEST_DIR}/ci-fixes/H2-forced-nightly-38238913518.json",
    f"{MANIFEST_DIR}/ci-fixes/H2a-forced-nightly-38238913518-attempt1-bench-regression.log",
    f"{MANIFEST_DIR}/ci-fixes/H2b-forced-nightly-38238913518-attempt2-bench-regression.log",
    f"{MANIFEST_DIR}/ci-fixes/H3-hosted-runs-9a9889d.json",
    f"{MANIFEST_DIR}/delegation/agy-e2-report.txt",
    f"{MANIFEST_DIR}/delegation/agy-e2-task.md",
    f"{MANIFEST_DIR}/delegation/agy-round2-report.txt",
    f"{MANIFEST_DIR}/delegation/agy-round3-report.txt",
    f"{MANIFEST_DIR}/delegation/devin-e2-report.txt",
    f"{MANIFEST_DIR}/delegation/devin-e2-task.md",
    f"{MANIFEST_DIR}/delegation/devin-round2-attempt2-aborted.txt",
    f"{MANIFEST_DIR}/delegation/devin-round2-report.txt",
    f"{MANIFEST_DIR}/delegation/devin-round3-report.txt",
    f"{MANIFEST_DIR}/delegation/round2-task.md",
    f"{MANIFEST_DIR}/delegation/round3-code.diff",
    f"{MANIFEST_DIR}/delegation/round3-task.md",
    f"{MANIFEST_DIR}/e2-review/CrlfCanonical.lean",
    f"{MANIFEST_DIR}/e2-review/E1-e2-static-verification.log",
    f"{MANIFEST_DIR}/e2-review/E2-crlf-crosscheck.log",
    f"{MANIFEST_DIR}/e2-review/E3-z3-png.log",
    f"{MANIFEST_DIR}/e2-review/E4-lean-check.log",
    f"{MANIFEST_DIR}/e2-review/crlf_model_crosscheck.py",
    f"{MANIFEST_DIR}/e2-review/e2_static_verification.py",
    f"{MANIFEST_DIR}/e2-review/z3_png_colour_rules.py",
    f"{MANIFEST_DIR}/gate/G01-ruff-check.log",
    f"{MANIFEST_DIR}/gate/G02-ruff-format-check.log",
    f"{MANIFEST_DIR}/gate/G03-ruff-format-check-experiments.log",
    f"{MANIFEST_DIR}/gate/G04-mypy-prin.log",
    f"{MANIFEST_DIR}/gate/G05-mypy-experiments.log",
    f"{MANIFEST_DIR}/gate/G06-mypy-exp002-driver.log",
    f"{MANIFEST_DIR}/gate/G07-interrogate.log",
    f"{MANIFEST_DIR}/gate/G08-bandit.log",
    f"{MANIFEST_DIR}/gate/G09-focused-coverage.json",
    f"{MANIFEST_DIR}/gate/G09-focused-pytest.log",
    f"{MANIFEST_DIR}/gate/G09a-focused-pytest-unpackaged-round3.log",
    f"{MANIFEST_DIR}/gate/G10-governance-deviation-ledger.log",
    f"{MANIFEST_DIR}/gate/G10b-governance-dv-gates.log",
    f"{MANIFEST_DIR}/gate/G10c-governance-session-registration.log",
    f"{MANIFEST_DIR}/gate/G10d-governance-skipif-probes.log",
    f"{MANIFEST_DIR}/gate/G10e-governance-wp001.log",
    f"{MANIFEST_DIR}/gate/G10f-git-diff-check.log",
    f"{MANIFEST_DIR}/gate/G10fa-git-diff-check-trailing-space.log",
    f"{MANIFEST_DIR}/gate/G11-sphinx.log",
    f"{MANIFEST_DIR}/gate/G11a-sphinx-changelog-link.log",
    f"{MANIFEST_DIR}/gate/G12-pytest-fast.log",
    f"{MANIFEST_DIR}/gate/G12a-pytest-fast-access-violation.log",
    f"{MANIFEST_DIR}/gate/G12b-pytest-fast-contended.log",
    f"{MANIFEST_DIR}/gate/G13-pytest-full.log",
    f"{MANIFEST_DIR}/gate/G13b-pytest-full-void-run4.log",
    f"{MANIFEST_DIR}/gate/G14-sast-copy-attestation.txt",
    f"{MANIFEST_DIR}/gate/G14-snyk-code.log",
    f"{MANIFEST_DIR}/gate/G14b-snyk-code-low-threshold.log",
    f"{MANIFEST_DIR}/gate/G14c-snyk-code-low-threshold-HEAD-baseline.log",
    f"{MANIFEST_DIR}/gate/G15-pip-audit-numpy-pin.log",
    f"{MANIFEST_DIR}/gate/G15b-snyk-open-source-numpy-pin.log",
    f"{MANIFEST_DIR}/gate/G16-post-package-manifest-tests.log",
    f"{MANIFEST_DIR}/gate/G16a-post-package-manifest-tests-logs-unstaged.log",
    f"{MANIFEST_DIR}/gate/G17-gitleaks-full-history.log",
    f"{MANIFEST_DIR}/gate/G18-gitleaks-staged.log",
    f"{MANIFEST_DIR}/gate/R01-cargo-version.log",
    f"{MANIFEST_DIR}/gate/R02-cargo-fmt.log",
    f"{MANIFEST_DIR}/gate/R03-cargo-clippy.log",
    f"{MANIFEST_DIR}/gate/R04-cargo-clippy-strict.log",
    f"{MANIFEST_DIR}/gate/R05-cargo-test.log",
    f"{MANIFEST_DIR}/gate/R06-cargo-test-strict.log",
    f"{MANIFEST_DIR}/gate/R07-cargo-llvm-cov-kernels.log",
    f"{MANIFEST_DIR}/test-reliability/W1-repro-without-hook.log",
    f"{MANIFEST_DIR}/test-reliability/W2-repro-with-hook.log",
    f"{MANIFEST_DIR}/test-reliability/W3-repro-hook-holder-never-releases.log",
    f"{MANIFEST_DIR}/test-reliability/winerror32-repro.py.txt",
    # bundle-end
}


def _git_tracked_0160() -> set[str] | None:
    """Files git tracks under `EVIDENCE/0160/` (exact case), or None."""
    try:
        listing = subprocess.run(
            ["git", "ls-files", "-z", "--", "EVIDENCE/0160"],
            cwd=REPO_ROOT,
            capture_output=True,
            check=True,
        ).stdout
    except (OSError, subprocess.CalledProcessError):
        return None
    prefix = "EVIDENCE/0160/"
    return {
        name[len(prefix) :]
        for name in listing.decode("utf-8").split("\0")
        if name.startswith(prefix)
    }


@pytest.fixture
def real_bundle(monkeypatch: pytest.MonkeyPatch) -> None:
    """Point the imported EA-007 validators at the real 0160 bundle."""
    monkeypatch.setattr(ea007, "EVIDENCE_ROOT", EVIDENCE_ROOT)
    monkeypatch.setattr(ea007, "MANIFEST_DIR", MANIFEST_DIR)
    monkeypatch.setattr(ea007, "MANIFEST", MANIFEST)
    monkeypatch.setattr(ea007, "_UNHASHED_BY_DESIGN", set(_UNHASHED_BY_DESIGN))
    monkeypatch.setattr(ea007, "_git_tracked", _git_tracked_0160)


@pytest.mark.usefixtures("real_bundle")
class TestRealBundle:
    def test_required_files_present_with_exact_case(self) -> None:
        missing = [
            relative
            for relative in REQUIRED_BUNDLE
            if not (EVIDENCE_ROOT / relative).is_file()
        ]
        assert not missing, f"bundle files missing: {missing}"

    def test_manifest_equals_required_hashed_set(self) -> None:
        entries = set(ea007._entries())
        assert entries == REQUIRED_BUNDLE - _UNHASHED_BY_DESIGN
        assert entries.isdisjoint(_UNHASHED_BY_DESIGN)

    def test_every_manifest_entry_matches_the_committed_bytes(self) -> None:
        ea007.test_every_manifest_entry_matches_the_committed_bytes()

    def test_manifest_covers_every_evidence_file(self) -> None:
        ea007.test_manifest_covers_every_evidence_file()

    def test_every_hashed_evidence_file_is_tracked_by_git(self) -> None:
        ea007.test_every_hashed_evidence_file_is_tracked_by_git()
