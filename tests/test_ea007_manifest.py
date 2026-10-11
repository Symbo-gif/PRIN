"""PR32-F7 regression: the EA-007 evidence manifest is executable and fail-closed.

`EVIDENCE/ea007/verification/SHA256SUMS.txt` is the integrity inventory for the
byte-exact EA-007 evidence. Before this test nothing executed it: a stale or
partial manifest (it failed 36 of 82 entries at commit `0738714`, when the
`.gitattributes` byte-exactness rule landed in the same commit as the files it
protects) could be committed unnoticed. The check fails closed on a malformed
line, a duplicate, a path that is absolute or escapes `EVIDENCE/ea007/`, a
missing file, a digest mismatch, an evidence file the manifest omits, and a
hashed file that git does not track.

Paths are relative to the manifest's directory, so the documented
`sha256sum -c SHA256SUMS.txt` (run from `verification/`) agrees with this test.
They are compared as exact-case POSIX strings rather than resolved on disk, so a
wrong letter case fails here on Windows and macOS exactly as it does on Linux.
"""

from __future__ import annotations

import hashlib
import posixpath
import re
import subprocess
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
EVIDENCE_ROOT = REPO_ROOT / "EVIDENCE" / "ea007"
MANIFEST_DIR = "verification"
MANIFEST = EVIDENCE_ROOT / MANIFEST_DIR / "SHA256SUMS.txt"

# POSIX paths relative to EVIDENCE/ea007/. The manifest cannot hash itself, and
# the top-level index is deliberately the one editable narrative file (it
# documents this very exemption).
_UNHASHED_BY_DESIGN = {"README.md", f"{MANIFEST_DIR}/SHA256SUMS.txt"}
# Operating-system metadata that appears beside evidence on a developer machine.
_OS_JUNK_NAMES = {".DS_Store", "Thumbs.db", "desktop.ini"}

_ENTRY = re.compile(r"^(?P<digest>[0-9a-f]{64}) \*(?P<path>\S.*)$")


def _entries() -> dict[str, str]:
    """`{posix path relative to EVIDENCE/ea007: sha256}`; any irregularity fails."""
    entries: dict[str, str] = {}
    lines = MANIFEST.read_bytes().decode("utf-8").splitlines()
    assert lines, "manifest is empty"
    for number, line in enumerate(lines, start=1):
        match = _ENTRY.match(line)
        assert match, f"SHA256SUMS.txt:{number}: malformed entry: {line!r}"
        raw = match.group("path")
        assert not posixpath.isabs(raw) and "\\" not in raw, (
            f"line {number}: path must be relative and POSIX-style: {raw}"
        )
        relative = posixpath.normpath(posixpath.join(MANIFEST_DIR, raw))
        assert relative != ".." and not relative.startswith("../"), (
            f"line {number}: {raw} escapes EVIDENCE/ea007/"
        )
        assert relative not in entries, f"line {number}: duplicate entry {raw}"
        entries[relative] = match.group("digest")
    return entries


def _present() -> set[str]:
    """Evidence files on disk as exact-case POSIX paths relative to EVIDENCE/ea007."""
    present = set()
    for path in EVIDENCE_ROOT.rglob("*"):
        if not path.is_file() or "__pycache__" in path.parts:
            continue
        if path.name in _OS_JUNK_NAMES or path.name.endswith(("~", ".swp")):
            continue
        present.add(path.relative_to(EVIDENCE_ROOT).as_posix())
    return present


def test_every_manifest_entry_matches_the_committed_bytes() -> None:
    present = _present()
    mismatched = []
    for relative, digest in _entries().items():
        assert relative in present, (
            f"manifest lists a missing file (check the letter case): {relative}"
        )
        actual = hashlib.sha256((EVIDENCE_ROOT / relative).read_bytes()).hexdigest()
        if actual != digest:
            mismatched.append(relative)
    assert not mismatched, (
        f"digest mismatch (manifest stale or bytes altered): {mismatched}"
    )


def test_manifest_covers_every_evidence_file() -> None:
    present = _present()
    missing_by_design = _UNHASHED_BY_DESIGN - present
    assert not missing_by_design, (
        f"the unhashed-by-design files must exist: {sorted(missing_by_design)}"
    )
    unhashed = present - set(_entries()) - _UNHASHED_BY_DESIGN
    assert not unhashed, (
        f"evidence files absent from SHA256SUMS.txt: {sorted(unhashed)}"
    )


def _git_tracked() -> set[str] | None:
    """Files git tracks under `EVIDENCE/ea007/` (exact case), or None outside git."""
    try:
        listing = subprocess.run(
            ["git", "ls-files", "-z", "--", "EVIDENCE/ea007"],
            cwd=REPO_ROOT,
            capture_output=True,
            check=True,
        ).stdout
    except (OSError, subprocess.CalledProcessError):
        return None
    prefix = "EVIDENCE/ea007/"
    return {
        name[len(prefix) :]
        for name in listing.decode("utf-8").split("\0")
        if name.startswith(prefix)
    }


def test_every_hashed_evidence_file_is_tracked_by_git() -> None:
    """A manifest entry must survive a fresh clone, not just this working tree.

    `*.log` is gitignored repository-wide, so an evidence log that was written
    and hashed but never `git add -f`-ed verifies locally and then goes missing
    on every clone (this nearly happened to the post-commit gitleaks logs).
    """
    tracked = _git_tracked()
    if tracked is None:
        pytest.skip("not a git checkout")
    missing = (set(_entries()) | _UNHASHED_BY_DESIGN) - tracked
    assert not missing, (
        "evidence files not tracked by git (use `git add -f` for ignored *.log): "
        f"{sorted(missing)}"
    )
