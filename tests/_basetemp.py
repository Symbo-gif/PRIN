"""Remove a stale ``--basetemp`` before the session, retrying sharing violations.

Given ``--basetemp=X``, pytest deletes the previous session's ``X`` lazily in
``TempPathFactory.getbasetemp()``, i.e. while setting up the first test that
requests ``tmp_path``. On Windows another process (an indexer, a scanner, an
editor's file watcher) can briefly hold a handle on a leftover file or
directory; ``shutil.rmtree`` then raises ``PermissionError`` (WinError 32,
sharing violation), that test errors at setup, the factory's base directory
stays unset, and the next tests retry and may error too. Evidence:
``EVIDENCE/0159/verification/pr33-review/G09a-…`` and ``G13-…`` (PR #33 review
audit). Deleting the same directory up front, retrying a bounded number of
times, removes that failure mode without changing what pytest deletes.
"""

from __future__ import annotations

import os
import shutil
import stat
import sys
import time
from collections.abc import Callable
from pathlib import Path
from typing import Any

ATTEMPTS = 30
DELAY_SECONDS = 0.5


def _make_writable_and_retry(
    function: Callable[..., Any], path: str, error: BaseException
) -> None:
    """Clear a read-only bit (e.g. git object files) and retry, as pytest does."""
    if not isinstance(error, PermissionError) or not os.path.lexists(path):
        raise error
    # As pytest's ``on_rm_rf_error``: add owner read/write (and search, for a
    # directory) to the entry and its parent, then retry the operation.
    for target in (path, os.path.dirname(path)):
        mode = os.lstat(target).st_mode
        if stat.S_ISLNK(mode):
            continue
        extra = stat.S_IRUSR | stat.S_IWUSR
        if stat.S_ISDIR(mode):
            extra |= stat.S_IXUSR
        os.chmod(target, mode | extra)
    function(path)


def remove_tree(path: Path) -> None:
    """``shutil.rmtree`` that also deletes read-only files."""
    if sys.version_info >= (3, 12):
        shutil.rmtree(path, onexc=_make_writable_and_retry)
    else:  # pragma: no cover - Python 3.11 hosts (``onexc`` is 3.12+)
        shutil.rmtree(
            path,
            onerror=lambda function, name, info: _make_writable_and_retry(
                function, name, info[1]
            ),
        )


def clear_stale_basetemp(
    basetemp: Path,
    rootdir: Path,
    *,
    attempts: int = ATTEMPTS,
    delay: float = DELAY_SECONDS,
    sleep: Callable[[float], None] = time.sleep,
    remove: Callable[[Path], None] = remove_tree,
) -> int:
    """Delete ``basetemp`` (which pytest would delete anyway) with retries.

    Args:
        basetemp: The user-given ``--basetemp`` directory.
        rootdir: The pytest root; ``basetemp`` may never be it or an ancestor.
        attempts: Maximum deletion attempts.
        delay: Seconds to wait after a failed attempt.
        sleep: Injected for tests.
        remove: Injected for tests.

    The path is made absolute exactly as pytest does (``os.path.abspath``,
    relative to the invocation directory), so the hook deletes the directory
    pytest would delete. A symbolic link, a plain file or a missing path is
    left alone for pytest's own handling. A directory that vanishes mid-way
    (another process removed it) counts as done.

    Returns:
        The number of failed attempts before success (0 if nothing to do).

    Raises:
        ValueError: If ``basetemp`` is the root directory or one of its
            ancestors.
        PermissionError: If the directory is still held after ``attempts``.
    """
    target = Path(os.path.abspath(basetemp))
    root = rootdir.resolve()
    resolved = target.resolve()
    if resolved == root or resolved in root.parents:
        raise ValueError(f"refusing to delete {target}: it contains {root}")
    failures = 0
    for _ in range(attempts):
        if target.is_symlink() or not target.is_dir():
            break
        try:
            remove(target)
        except (FileNotFoundError, NotADirectoryError):
            continue
        except PermissionError:
            failures += 1
            if failures >= attempts:
                raise
            sleep(delay)
        except OSError:
            # Anything else (e.g. a directory refilled concurrently) is left
            # to pytest's own deletion, exactly as without this hook.
            return failures
    else:
        if target.is_dir() and not target.is_symlink():
            raise PermissionError(f"{target} still exists after {attempts} attempts")
    return failures
