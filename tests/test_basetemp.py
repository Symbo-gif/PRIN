"""Tests for the stale ``--basetemp`` pre-clean (``tests/_basetemp.py``)."""

from __future__ import annotations

from pathlib import Path

import pytest
from _basetemp import clear_stale_basetemp


def _stale(tmp_path: Path) -> Path:
    basetemp = tmp_path / "basetemp"
    (basetemp / "test_old0" / "RUN-x").mkdir(parents=True)
    (basetemp / "test_old0" / "RUN-x" / "held.json").write_text("{}", encoding="utf-8")
    return basetemp


def test_missing_basetemp_is_a_no_op(tmp_path: Path) -> None:
    assert clear_stale_basetemp(tmp_path / "absent", tmp_path / "root") == 0


def test_real_deletion(tmp_path: Path) -> None:
    basetemp = _stale(tmp_path)
    assert clear_stale_basetemp(basetemp, tmp_path / "root") == 0
    assert not basetemp.exists()


def test_sharing_violation_is_retried_until_released(tmp_path: Path) -> None:
    import shutil

    basetemp = _stale(tmp_path)
    calls: list[Path] = []
    sleeps: list[float] = []

    def flaky(path: Path) -> None:
        calls.append(path)
        if len(calls) < 3:
            raise PermissionError(32, "being used by another process")
        shutil.rmtree(path)

    failures = clear_stale_basetemp(
        basetemp, tmp_path / "root", remove=flaky, sleep=sleeps.append, delay=0.25
    )
    assert failures == 2
    assert sleeps == [0.25, 0.25]
    assert not basetemp.exists()


def test_persistent_holder_raises_after_budget(tmp_path: Path) -> None:
    basetemp = _stale(tmp_path)
    sleeps: list[float] = []

    def held(path: Path) -> None:
        raise PermissionError(32, "being used by another process")

    with pytest.raises(PermissionError):
        clear_stale_basetemp(
            basetemp, tmp_path / "root", remove=held, sleep=sleeps.append, attempts=4
        )
    assert len(sleeps) == 3
    assert basetemp.exists()


@pytest.mark.parametrize("relation", ["same", "ancestor"])
def test_refuses_root_or_its_ancestor(tmp_path: Path, relation: str) -> None:
    root = tmp_path / "repo"
    root.mkdir()
    target = root if relation == "same" else tmp_path
    with pytest.raises(ValueError, match="refusing"):
        clear_stale_basetemp(target, root)
    assert root.exists()


def test_read_only_files_are_deleted(tmp_path: Path) -> None:
    """Git object files are read-only; pytest's own deletion copes with them."""
    import os
    import stat

    basetemp = _stale(tmp_path)
    frozen = basetemp / "test_old0" / "RUN-x" / "held.json"
    os.chmod(frozen, stat.S_IREAD)
    assert clear_stale_basetemp(basetemp, tmp_path / "root") == 0
    assert not basetemp.exists()


def test_directory_vanishing_mid_delete_counts_as_done(tmp_path: Path) -> None:
    import shutil

    basetemp = _stale(tmp_path)

    def racing(path: Path) -> None:
        shutil.rmtree(path)  # another process got there first
        raise FileNotFoundError(2, "gone")

    assert clear_stale_basetemp(basetemp, tmp_path / "root", remove=racing) == 0
    assert not basetemp.exists()


def test_plain_file_is_left_for_pytest(tmp_path: Path) -> None:
    target = tmp_path / "basetemp"
    target.write_text("not a directory", encoding="utf-8")
    assert clear_stale_basetemp(target, tmp_path / "root") == 0
    assert target.read_text(encoding="utf-8") == "not a directory"


def test_relative_path_is_resolved_like_pytest(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """pytest uses ``os.path.abspath`` (invocation directory), not rootpath."""
    cwd = tmp_path / "invoked-here"
    cwd.mkdir()
    (cwd / "bt" / "old").mkdir(parents=True)
    elsewhere = tmp_path / "root" / "bt"
    (elsewhere / "keep").mkdir(parents=True)
    monkeypatch.chdir(cwd)
    clear_stale_basetemp(Path("bt"), tmp_path / "root")
    assert not (cwd / "bt").exists()
    assert (elsewhere / "keep").is_dir()


def test_bounded_when_directory_keeps_reappearing(tmp_path: Path) -> None:
    basetemp = _stale(tmp_path)

    def resurrect(path: Path) -> None:
        return None  # "deleted", but the directory is still there

    with pytest.raises(PermissionError, match="still exists"):
        clear_stale_basetemp(basetemp, tmp_path / "root", remove=resurrect, attempts=3)


def test_other_os_errors_are_left_to_pytest(tmp_path: Path) -> None:
    basetemp = _stale(tmp_path)

    def refilled(path: Path) -> None:
        raise OSError(39, "directory not empty")

    assert clear_stale_basetemp(basetemp, tmp_path / "root", remove=refilled) == 0
    assert basetemp.exists()


def test_read_only_directory_is_deleted(tmp_path: Path) -> None:
    """POSIX: a read-only directory needs owner write/search, as in pytest."""
    import os
    import stat

    basetemp = _stale(tmp_path)
    frozen_dir = basetemp / "test_old0" / "RUN-x"
    os.chmod(frozen_dir / "held.json", stat.S_IREAD)
    os.chmod(frozen_dir, stat.S_IREAD | stat.S_IXUSR)
    try:
        assert clear_stale_basetemp(basetemp, tmp_path / "root") == 0
    finally:
        if frozen_dir.exists():
            os.chmod(frozen_dir, stat.S_IRWXU)
    assert not basetemp.exists()
