"""Path containment and secret non-exposure enforcement tests."""

from __future__ import annotations

from pathlib import Path

import pytest

from ci_mcp_server.security import PathEscapeError, ensure_contained, redact_evidence


def test_ensure_contained_accepts_path_inside_root(tmp_path: Path) -> None:
    inside = tmp_path / "sub" / "file.py"
    inside.parent.mkdir(parents=True)
    inside.write_text("x")
    result = ensure_contained(inside, (tmp_path,))
    assert result == inside.resolve()


def test_ensure_contained_rejects_path_outside_root(tmp_path: Path) -> None:
    outside = tmp_path.parent / "definitely-outside-file.txt"
    with pytest.raises(PathEscapeError):
        ensure_contained(outside, (tmp_path,))


def test_ensure_contained_rejects_traversal_escape(tmp_path: Path) -> None:
    root = tmp_path / "repo"
    root.mkdir()
    escape_attempt = root / ".." / ".." / "etc" / "passwd"
    with pytest.raises(PathEscapeError):
        ensure_contained(escape_attempt, (root,))


def test_ensure_contained_accepts_second_allowed_root(tmp_path: Path) -> None:
    root_a = tmp_path / "a"
    root_b = tmp_path / "b"
    root_a.mkdir()
    root_b.mkdir()
    target = root_b / "file.txt"
    target.write_text("x")
    result = ensure_contained(target, (root_a, root_b))
    assert result == target.resolve()


def test_redact_evidence_passes_through_ordinary_values() -> None:
    evidence = {"raw_target": "os.path", "line": 3}
    assert redact_evidence(evidence) == evidence


def test_redact_evidence_flags_values_that_look_secret_like_too() -> None:
    # Defense in depth: is_secret_like's glob patterns match substrings
    # like "secret" anywhere in the value, not just exact filenames, so an
    # evidence value that merely mentions something secret-sounding is
    # redacted too rather than assuming it is safe.
    evidence = {"raw_target": "module_with_secret_in_the_name", "line": 3}
    result = redact_evidence(evidence)
    assert result["redacted"] is True


def test_redact_evidence_redacts_when_value_matches_secret_filename_pattern() -> None:
    evidence = {"raw_target": ".env", "line": 1}
    result = redact_evidence(evidence)
    assert result["redacted"] is True
