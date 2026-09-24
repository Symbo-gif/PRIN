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
import errno
import hashlib
import json
import os
import re
import stat
import sys
import tempfile
import uuid
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from prin.reporting import ReportingError as ReportingError
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
# The system temp root exists in ALLOWED_MANIFEST_ROOTS purely to support a
# test's scratch directory. Containment below is "is the destination under
# this root", checked by walking every ancestor — so if this checkout itself
# happened to live under the system temp directory (an ephemeral CI
# workspace, a sandboxed clone, ...), admitting the temp root at all would
# transitively admit every path in the checkout, defeating containment
# entirely. Omitted in that one case; scratch-directory support degrades
# there (a test would need a temp location outside the checkout), but the
# containment guarantee for the checkout's own files never does.
_TEMP_ROOT = Path(tempfile.gettempdir()).resolve()
_CHECKOUT_ROOT = _REPOSITORY_ROOT.resolve()
_TEMP_ROOT_IS_SAFE = not (
    _CHECKOUT_ROOT == _TEMP_ROOT or _TEMP_ROOT in _CHECKOUT_ROOT.parents
)
ALLOWED_MANIFEST_ROOTS = (
    (_REPOSITORY_ROOT / "paper").resolve(),
    (_REPOSITORY_ROOT / "benchmarks" / "results").resolve(),
    *((_TEMP_ROOT,) if _TEMP_ROOT_IS_SAFE else ()),
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


def _reject_non_regular(path: Path, role: str) -> None:
    """Refuse an inventory entry that exists but is not a regular file.

    ``_reject_symlink`` closes the symlink case; a directory or FIFO named
    like a manifested artefact has the same failure mode without being a
    link: the later ``is_file()`` inventory filter silently excludes it
    instead of the mismatch surfacing as "missing" or "unmanifested". Checked
    after :func:`_reject_symlink` so the more specific symlink message wins
    when both apply.

    Args:
        path: Candidate path, unresolved.
        role: Human-readable role used in the failure message.

    Raises:
        ManifestMismatchError: If ``path`` is a symbolic link (via
            :func:`_reject_symlink`), or exists and is not a regular file.
    """
    _reject_symlink(path, role)
    if path.exists() and not path.is_file():
        raise ManifestMismatchError(
            f"{role} {path} exists but is not a regular file (a directory, "
            "FIFO, or other special file); refusing to verify it"
        )


def _dir_relative_open(path: Path, flags: int, mode: int, role: str) -> int | None:
    """Open ``path``'s final component relative to a pinned parent descriptor.

    ``O_NOFOLLOW`` on ``path`` itself only refuses a symlink at the *final*
    path component (POSIX ``open(2)``): it does not stop a concurrent
    replacement of the *immediate parent* directory (for example the
    governed ``output_dir`` itself) with a symlink between an earlier
    resolve-and-contain check and this open, which would silently redirect
    the open outside the checked root while the final filename remains a
    plain, non-symlinked name (CWE-59; independent review, PR #23 head
    `2264771`). Opening that immediate parent directory as a descriptor pins
    its exact directory inode: a later replacement of the path string's
    parent cannot repoint an open performed relative to that descriptor,
    closing the window for *that one level* rather than narrowing it. As a
    side effect this also rejects a parent that is *already* a symlink at
    call time, not only one swapped in mid-race.

    This closes the race for the immediate parent only, not for every
    ancestor along ``path``: a symlink swapped in at a *grandparent* or
    higher directory, before this function's own ``os.open(parent, ...)``
    call runs, is still followed by that call — POSIX path resolution
    transparently traverses any non-final symlinked component, and
    ``O_NOFOLLOW`` here only guards the component this function itself
    opens. Every caller in this module constructs ``path`` as a fixed
    relative name under an already-validated governed root
    (``run_dir``/``output_dir``/``results_dir``, checked by
    :func:`allowed_output_roots`-style callers before any of these
    functions run), so the immediate parent is the level that check
    actually names and the level realistically exposed to a local
    concurrent writer; closing every deeper ancestor as well would require
    walking and pinning each path component from a trusted anchor down
    (independent review, PR #23 head `e946a3c` — declined as
    disproportionate to this module's own threat model of a governed
    CI/local checkout, not an adversarial remote filesystem, the same
    threat model already invoked for the Windows fallback below).

    Only attempted where the platform supports it (POSIX with
    ``dir_fd``-relative :func:`os.open` and ``O_DIRECTORY``); returns
    ``None`` on Windows so the caller falls back to its existing
    final-component-only guarantee.

    Args:
        path: Candidate manifest, artefact, or destination path, unresolved.
        flags: Open flags for the final component. ``O_NOFOLLOW`` is added
            here; the caller must not include it.
        mode: Permission bits, used only when ``flags`` includes ``O_CREAT``.
        role: Human-readable role used in the failure message.

    Returns:
        An open file descriptor for ``path``, or ``None`` if this platform
        does not support ``dir_fd``-relative opens.

    Raises:
        ManifestMismatchError: If the parent directory or ``path`` itself is
            a symbolic link.
        OSError: If the parent directory cannot be opened, or the file
            cannot be opened/created.
    """
    parent_fd = _open_parent_dir_fd(path.parent, role)
    if parent_fd is None:
        return None
    no_follow = getattr(os, "O_NOFOLLOW", 0)
    try:
        try:
            return os.open(path.name, flags | no_follow, mode, dir_fd=parent_fd)
        except OSError as error:
            if error.errno == errno.ELOOP:
                raise ManifestMismatchError(
                    f"{role} {path} is a symbolic link, not a regular file "
                    "held by the governed directory; refusing to open it"
                ) from error
            raise
    finally:
        os.close(parent_fd)


def _open_parent_dir_fd(parent: Path, role: str) -> int | None:
    """Open ``parent`` as a no-follow directory descriptor.

    Split out of :func:`_dir_relative_open` so :func:`write_no_follow` can
    keep the same descriptor open across both its temporary file's creation
    *and* the final :func:`os.replace` — reusing one pinned descriptor for
    both, rather than opening and closing it once per call, is what keeps
    the parent-directory guarantee alive through the rename too (see
    :func:`write_no_follow`).

    Returns ``None`` (platform fallback signal, not an error) when
    ``dir_fd``-relative opens aren't supported here (Windows).

    Args:
        parent: The directory to pin, unresolved.
        role: Human-readable role used in the failure message.

    Returns:
        An open, caller-owned directory file descriptor, or ``None``.

    Raises:
        ManifestMismatchError: If ``parent`` is a symbolic link.
        OSError: If ``parent`` cannot be opened for another reason.
    """
    if (
        os.open not in os.supports_dir_fd
        or not hasattr(os, "O_DIRECTORY")
        or not hasattr(os, "O_NOFOLLOW")
    ):
        return None
    dir_flags = os.O_RDONLY | os.O_DIRECTORY | getattr(os, "O_NOFOLLOW", 0)
    try:
        return os.open(parent, dir_flags)
    except OSError as error:
        # Linux reports ENOTDIR, not ELOOP, for O_DIRECTORY | O_NOFOLLOW on a
        # symlink (observed on the ubuntu CI legs, PR #23 head `e946a3c`).
        # The open has already failed closed; the no-follow lstat only
        # separates that case from a parent that is genuinely not a directory.
        if error.errno == errno.ELOOP or (
            error.errno == errno.ENOTDIR and parent.is_symlink()
        ):
            raise ManifestMismatchError(
                f"{role} has a symbolic link ancestor directory ({parent}); "
                "refusing to open it"
            ) from error
        raise


def _reject_non_regular_fd(fd: int, path: Path, role: str) -> None:
    """Refuse an already-open descriptor that is not a regular file.

    A check-then-open race can swap a candidate for a FIFO (or another
    special file) after :func:`_reject_non_regular`'s pre-check and before
    the open that follows it; opening a FIFO for reading with no writer
    present (or for writing with no reader) blocks indefinitely on POSIX
    (``fifo(7)``), turning a fail-closed verification into a hang instead of
    a clean rejection (independent review, PR #23 head `2264771`). Paired
    with ``O_NONBLOCK`` on the open itself (a no-op on a regular file, but
    what prevents that hang on a FIFO), this closes the race for good:
    whatever the open returned, this checks what it actually is before the
    caller uses it.

    Args:
        fd: An already-open file descriptor.
        path: The path that was opened, for the failure message.
        role: Human-readable role used in the failure message.

    Raises:
        ManifestMismatchError: If the descriptor is not a regular file. The
            descriptor is closed before raising.
    """
    if not stat.S_ISREG(os.fstat(fd).st_mode):
        os.close(fd)
        raise ManifestMismatchError(
            f"{role} {path} is not a regular file (a FIFO, device, or other "
            "special file); refusing to use it"
        )


def _open_no_follow(path: Path, role: str) -> int:
    """Open a file read-only, refusing a symbolic link at the ``open`` itself.

    ``_reject_symlink`` is a fast pre-check; on its own it leaves a
    check-then-use window in which a concurrent writer can replace a regular
    file with a symlink between the check and a later ``stat()``/``open()``
    (TOCTOU, still CWE-59). On POSIX, ``O_NOFOLLOW`` closes that window for
    the final path component: the ``open`` syscall itself fails with
    ``ELOOP`` if the final path component is a symbolic link, so there is no
    separate moment at which the check has passed but the open has not yet
    happened. :func:`_dir_relative_open` closes the same window for the
    *immediate parent* directory too, where the platform supports it (see
    its own docstring for why this does not extend to every ancestor).
    Windows does not define ``O_NOFOLLOW`` or ``dir_fd``-relative opens;
    there this falls
    back to ``is_symlink()`` immediately before ``open()`` on the full path,
    which narrows but does not close the window — the repository's own
    concurrent-writer threat here is a governed CI/local checkout, not an
    adversarial remote filesystem. ``O_NONBLOCK`` (where defined) and a
    post-open :func:`_reject_non_regular_fd` check additionally guard
    against a FIFO swapped in for the candidate, which would otherwise block
    this open indefinitely instead of failing closed.

    Args:
        path: Candidate manifest or artefact path, unresolved.
        role: Human-readable role used in the failure message.

    Returns:
        An open read-only file descriptor; the caller owns it.

    Raises:
        ManifestMismatchError: If ``path`` (or an ancestor directory, where
            supported) is a symbolic link, or the opened descriptor is not a
            regular file.
    """
    flags = os.O_RDONLY | getattr(os, "O_NONBLOCK", 0) | getattr(os, "O_BINARY", 0)
    fd = _dir_relative_open(path, flags, 0, role)
    if fd is None:
        if hasattr(os, "O_NOFOLLOW"):
            try:
                fd = os.open(path, flags | os.O_NOFOLLOW)
            except OSError as error:
                if error.errno == errno.ELOOP:
                    raise ManifestMismatchError(
                        f"{role} {path} is a symbolic link, not a regular file "
                        "held by the governed directory; refusing to verify it"
                    ) from error
                raise
        else:
            if path.is_symlink():
                raise ManifestMismatchError(
                    f"{role} {path} is a symbolic link, not a regular file held "
                    "by the governed directory; refusing to verify it"
                )
            fd = os.open(path, flags)
    _reject_non_regular_fd(fd, path, role)
    return fd


def read_no_follow(path: Path, role: str) -> bytes:
    """Read a whole file's bytes through :func:`_open_no_follow`.

    Public: a caller that has already verified a path through this module
    (for example, an artefact ``verify_manifest`` just accepted) must keep
    reading it through this function rather than through a plain
    ``Path.read_text``/``Path.open``, or the no-follow guarantee only covers
    verification and not the caller's own subsequent read (TOCTOU, CWE-59).

    Args:
        path: Candidate manifest or artefact path, unresolved.
        role: Human-readable role used in the failure message.

    Returns:
        The file's raw bytes.

    Raises:
        ManifestMismatchError: If ``path`` is a symbolic link.
        OSError: If the file cannot be read.
    """
    fd = _open_no_follow(path, role)
    with os.fdopen(fd, "rb") as stream:
        return stream.read()


def write_no_follow(path: Path, data: bytes, role: str) -> None:
    """Write bytes to a file, refusing to write through a symbolic link or a hard link.

    The write-side mirror of :func:`_open_no_follow`: ``Path.write_text`` and
    ``Path.write_bytes`` both follow a symbolic link at the destination, so a
    caller that resolved and contained a destination path (for example,
    against :data:`ALLOWED_MANIFEST_ROOTS`) but then wrote to it with a plain
    ``write_text`` call could have that write silently redirected to
    whatever the link points at if the destination were replaced with a
    symlink between the containment check and this write (CWE-59).

    A no-follow *open* of ``path`` itself is not enough, though: a local
    process can create ``path`` as a *hard link* to an unrelated existing
    file — a genuine regular file, indistinguishable from any other by
    every check above, since a hard link is not a symlink and has no
    special file type of its own. Opening such a path with ``O_TRUNC`` and
    writing to it modifies *every* name that inode has, silently corrupting
    whatever else it is linked to (for example, a governed manifest
    filename hard-linked to an unrelated frozen report; independent review,
    PR #23 head `d5f47d6`). To close this, the bytes are instead written to
    a freshly, exclusively created sibling file (``O_EXCL`` guarantees a
    brand new inode, never an existing hard link) and then atomically
    swapped into place with :func:`os.replace`, which repoints only
    ``path``'s own directory entry — whatever else the old entry's inode
    was linked to, if anything, is never opened, truncated, or touched.

    On POSIX, ``O_CREAT | O_EXCL | O_NOFOLLOW`` makes the *temporary* file's
    ``open`` itself the symlink check: it fails with ``ELOOP`` if the final
    path component is an existing symlink (vanishingly unlikely for a fresh
    unique name, but checked all the same), and otherwise creates a new
    regular file in one syscall. :func:`_open_parent_dir_fd` closes the same
    window for the *immediate parent* directory too, where the platform
    supports it (see its own docstring for why this does not extend to
    every ancestor) — and the final swap reuses that same pinned
    descriptor, performed as a ``dir_fd``-relative :func:`os.rename`
    wherever ``os.rename in os.supports_dir_fd`` confirms, at runtime, that
    the platform actually supports it, so a parent directory swapped for a
    symlink between the temporary file's creation and the swap cannot
    redirect the rename either (independent review, PR #23 head
    `f370a29`). Everywhere else it falls back to a plain
    :func:`os.replace`, which re-resolves ``path``'s parent by string —
    the same narrowing-only posture already documented for the Windows
    fallback below. The runtime capability gate is the load-bearing part:
    on real Linux CI, ``os.replace`` does *not* support ``dir_fd``-relative
    operation (``os.replace not in os.supports_dir_fd`` on Ubuntu/Python
    3.12, despite ``os.open`` supporting it) — an earlier
    ``dir_fd``-relative attempt at this rename shipped without that check,
    broke required CI twice, and was reverted (independent review, PR #23
    head `949e5e1`; reverted at head `4ed9f14`; re-attempted with the gate,
    per the audit's own §17.4 prescription, at this head). Windows has no
    ``O_NOFOLLOW`` or ``dir_fd``-relative opens either; there this falls
    back to ``is_symlink()`` immediately
    before ``open()`` on the full path (see :func:`_open_no_follow`).
    ``O_NONBLOCK`` (where defined) and a post-open
    :func:`_reject_non_regular_fd` check additionally guard against a FIFO
    swapped in for the temporary name, which would otherwise block this
    open indefinitely instead of failing closed. ``path`` itself is checked
    for a symlink immediately before the final swap, preserving this
    function's documented refusal — though :func:`os.replace` never
    follows a trailing symlink on either side even without that check, so
    this is belt and suspenders, not the sole guard.

    Args:
        path: Destination path, unresolved.
        data: Bytes to write.
        role: Human-readable role used in the failure message.

    Raises:
        ManifestMismatchError: If ``path`` (or an ancestor directory, where
            supported) is a symbolic link, or the opened descriptor is not a
            regular file.
        OSError: If the file cannot be written.
    """
    flags = (
        os.O_WRONLY
        | os.O_CREAT
        | os.O_EXCL
        | getattr(os, "O_NONBLOCK", 0)
        | getattr(os, "O_BINARY", 0)
    )
    tmp_path = path.with_name(f".{path.name}.tmp-{os.getpid()}-{uuid.uuid4().hex}")
    parent_fd = _open_parent_dir_fd(path.parent, role)
    try:
        no_follow = getattr(os, "O_NOFOLLOW", 0)
        if parent_fd is not None:
            try:
                fd = os.open(tmp_path.name, flags | no_follow, 0o644, dir_fd=parent_fd)
            except OSError as error:
                if error.errno == errno.ELOOP:
                    raise ManifestMismatchError(
                        f"{role} {path} is a symbolic link, not a regular file "
                        "held by the governed directory; refusing to write it"
                    ) from error
                raise
        elif hasattr(os, "O_NOFOLLOW"):
            try:
                fd = os.open(tmp_path, flags | os.O_NOFOLLOW, 0o644)
            except OSError as error:
                if error.errno == errno.ELOOP:
                    raise ManifestMismatchError(
                        f"{role} {path} is a symbolic link, not a regular file "
                        "held by the governed directory; refusing to write it"
                    ) from error
                raise
        else:
            if tmp_path.is_symlink():
                raise ManifestMismatchError(
                    f"{role} {path} is a symbolic link, not a regular file held "
                    "by the governed directory; refusing to write it"
                )
            fd = os.open(tmp_path, flags, 0o644)
        try:
            _reject_non_regular_fd(fd, tmp_path, role)
            with os.fdopen(fd, "wb") as stream:
                stream.write(data)
            if path.is_symlink():
                raise ManifestMismatchError(
                    f"{role} {path} is a symbolic link, not a regular file held "
                    "by the governed directory; refusing to write it"
                )
            if parent_fd is not None and os.rename in os.supports_dir_fd:
                # dir_fd-relative final swap through the same pinned parent
                # descriptor used to create the temporary file, gated on a
                # *runtime* capability check — `os.replace not in
                # os.supports_dir_fd` on real Ubuntu/Python 3.12 even though
                # `os.open` supports dir_fd there, the unverified assumption
                # that broke required Linux CI twice at PR23-F39 (audit §16,
                # §17.4). POSIX rename(2) atomically replaces an existing
                # destination; Windows never reaches this branch
                # (os.supports_dir_fd is empty there), so its
                # existing-destination rename semantics are irrelevant here.
                os.rename(
                    tmp_path.name,
                    path.name,
                    src_dir_fd=parent_fd,
                    dst_dir_fd=parent_fd,
                )
            else:
                os.replace(tmp_path, path)
        except BaseException:
            # dir_fd-relative when the same pinned descriptor used to
            # create the temporary file is still available and os.unlink
            # supports it (checked, not assumed — see PR23-F39's own
            # correction above for what happens when that assumption goes
            # unverified): a plain-path unlink here would re-resolve
            # tmp_path's parent by string, so a symlink swapped into it
            # during this call could delete a same-named file elsewhere
            # instead of the temporary file this function actually created
            # (independent review, PR #23 head `4ed9f14`).
            if parent_fd is not None and os.unlink in os.supports_dir_fd:
                try:
                    os.unlink(tmp_path.name, dir_fd=parent_fd)
                except FileNotFoundError:
                    pass
            else:
                tmp_path.unlink(missing_ok=True)
            raise
    finally:
        if parent_fd is not None:
            os.close(parent_fd)


def _hash_fd(fd: int) -> str:
    """SHA-256 digest of an already-open file descriptor.

    Consumes and closes ``fd`` (via ``os.fdopen``). Split out of
    :func:`stat_size_and_hash_no_follow` so a caller that already knows the
    expected size can fstat first and skip hashing on a mismatch, without
    re-opening the file (see :func:`_verify_size_and_hash_no_follow`).

    Args:
        fd: An open, readable file descriptor.

    Returns:
        Lowercase hexadecimal SHA-256 digest.
    """
    digest = hashlib.sha256()
    with os.fdopen(fd, "rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def stat_size_and_hash_no_follow(path: Path, role: str) -> tuple[int, str]:
    """Size and SHA-256 digest of one file, from a single no-follow open.

    Public: a caller recording integrity fields for a path it just wrote or
    verified (for example, a manifest entry for a generated output) must
    compute them this way rather than with ``Path.stat()`` +
    ``compute_sha256()``, both of which follow a symlink — recording bytes
    from a swapped-in target instead of the file actually written/verified
    (TOCTOU, CWE-59).

    Both figures come from the same file descriptor, opened exactly once, so
    there is no window between "checked" and "read" in which the path could
    be repointed (see :func:`_open_no_follow`). Unconditional: use
    :func:`_verify_size_and_hash_no_follow` instead when there is an expected
    size to short-circuit hashing against.

    Args:
        path: Candidate manifest or artefact path, unresolved.
        role: Human-readable role used in the failure message.

    Returns:
        ``(size_in_bytes, lowercase_hex_sha256)``.

    Raises:
        ManifestMismatchError: If ``path`` is a symbolic link.
        OSError: If the file cannot be read.
    """
    fd = _open_no_follow(path, role)
    try:
        size = os.fstat(fd).st_size
    except OSError:
        os.close(fd)
        raise
    return size, _hash_fd(fd)


def _verify_size_and_hash_no_follow(
    path: Path, expected_size: int, name: str, role: str
) -> str:
    """Digest a file no-follow, short-circuiting before hashing on a size mismatch.

    Hashing a large corrupted or mismatched artefact is wasted work once its
    size alone proves it cannot match; this keeps that short-circuit while
    still reading size and content from a single no-follow-opened descriptor
    — no re-open between the size check and the hash, so the guarantee in
    :func:`_open_no_follow` still covers both.

    Args:
        path: Candidate manifest or artefact path, unresolved.
        expected_size: The manifest-recorded size to compare against.
        name: The manifested path name, for the size-mismatch message.
        role: Human-readable role passed to :func:`_open_no_follow`.

    Returns:
        The lowercase hexadecimal SHA-256 digest.

    Raises:
        ManifestMismatchError: If ``path`` is a symbolic link, or its size
            does not match ``expected_size``.
        OSError: If the file cannot be read.
    """
    fd = _open_no_follow(path, role)
    try:
        size = os.fstat(fd).st_size
    except OSError:
        os.close(fd)
        raise
    if size != expected_size:
        os.close(fd)
        raise ManifestMismatchError(f"size mismatch: {name}")
    return _hash_fd(fd)


def read_verified_no_follow(
    path: Path, expected_size: int, expected_sha256: str, name: str, role: str
) -> bytes:
    """Read a file's bytes from one no-follow open, verified against a record.

    Public: a caller that must both prove a specific file still matches a
    manifest record *and* consume its bytes (for example, an analysis
    module parsing a result artefact after :func:`verify_manifest` already
    checked the directory) must read this way rather than calling
    :func:`verify_manifest` and then a separate :func:`read_no_follow` on
    the same path. The two-open pattern proves the second open is not a
    symlink, but nothing ties its *content* to what verification saw: a
    concurrent replacement with another regular file between the two opens
    — restored afterward or not — would otherwise be read as if it were
    the verified bytes (TOCTOU, CWE-59). Here, the size and digest checks
    run against the same descriptor the caller then reads, so the returned
    bytes are provably the ones ``expected_sha256`` describes, independent
    of whatever happened to the path before this call.

    Args:
        path: Candidate manifest or artefact path, unresolved.
        expected_size: The manifest-recorded size to verify.
        expected_sha256: The manifest-recorded digest to verify.
        name: The manifested path name, for the failure message.
        role: Human-readable role passed to :func:`_open_no_follow`.

    Returns:
        The file's raw bytes, proven to match ``expected_size`` and
        ``expected_sha256``.

    Raises:
        ManifestMismatchError: If ``path`` is a symbolic link, or its size
            or digest does not match the expected values.
        OSError: If the file cannot be read.
    """
    fd = _open_no_follow(path, role)
    try:
        size = os.fstat(fd).st_size
    except OSError:
        os.close(fd)
        raise
    if size != expected_size:
        os.close(fd)
        raise ManifestMismatchError(f"size mismatch: {name}")
    with os.fdopen(fd, "rb") as stream:
        data = stream.read()
    digest = hashlib.sha256(data).hexdigest()
    if digest != expected_sha256:
        raise ManifestMismatchError(f"SHA-256 mismatch: {name}")
    return data


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
        raw_bytes = read_no_follow(path, "manifest")
    except OSError as error:
        raise ManifestFormatError(f"cannot read manifest {path}: {error}") from error
    try:
        payload: Any = json.loads(raw_bytes.decode("utf-8"))
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
    failure rather than silently blessing it with a new digest. A symbolic link,
    or any non-regular entry (directory, FIFO, ...), is never manifested: the
    manifest destination and every candidate ``*.json`` in ``results_dir`` are
    rejected up front if they are not a regular file (see
    :func:`_reject_non_regular`), and every read and the eventual write go
    through :func:`read_no_follow`/:func:`write_no_follow` on the original,
    unresolved path — never on a path already passed through ``.resolve()``,
    which would silently follow a symlink swapped in after the check.

    Args:
        results_dir: Directory containing stored JSON artefacts.
        manifest_path: Manifest to create or append.

    Returns:
        The complete, sorted manifest records.

    Raises:
        ReproductionConfigurationError: If the manifest destination is outside
            the governed output roots.
        ManifestFormatError: If an existing manifest is malformed.
        ManifestMismatchError: If an existing record was removed or modified,
            or if the manifest or any candidate artefact is not a regular
            file.
    """
    _reject_non_regular(manifest_path, "manifest")
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
    # `manifest_path` (unresolved) is used for every read/write below;
    # `destination` (resolved) is only for the containment check above and
    # the self-exclusion comparison — using the *resolved* path for I/O would
    # silently follow whatever a swapped-in symlink pointed at, defeating the
    # no-follow guarantee `read_no_follow`/`write_no_follow` provide on the
    # original path (Copilot follow-up review, PR #23 head `0cb6156`).
    records = load_manifest(manifest_path) if manifest_path.is_file() else ()
    existing = {record.path: record for record in records}
    candidates = sorted(results.glob("*.json"))
    # Self-exclusion by file identity, computed once before any per-candidate
    # check — not by comparing each candidate's `.resolve()` against
    # `destination` (an earlier approach): that followed a symlink per
    # candidate, so a candidate swapped for a symlink targeting `destination`
    # between the glob and this comparison would resolve equal to it and
    # silently vanish from `actual_paths` — never surfacing as "missing" or
    # "unmanifested" — instead of being rejected as non-regular below
    # (CWE-59; independent review, PR #23 head `e946a3c`). Mirrors
    # :func:`verify_manifest`'s already-safe self-exclusion. Compared via
    # `os.path.samestat` on `lstat()` results, not a name string: an earlier
    # `os.path.normcase`-based comparison self-excluded correctly on Windows
    # (case-folding) but not on a case-insensitive-yet-case-preserving
    # filesystem (macOS default), where `normcase` is the identity function
    # on POSIX but the filesystem itself still treats `MANIFEST.JSON` and
    # `manifest.json` as the same file — `glob` returns the stored casing,
    # so a name comparison against the caller's casing missed the alias and
    # let the manifest re-add itself as an "unmanifested" candidate
    # (independent review, PR #23 head `f370a29`). Comparing device/inode via
    # `lstat` instead is filesystem-identity-based, not string-based, so it
    # is correct on every platform without a per-platform case rule; using
    # `lstat` rather than `stat` on the candidate side also means a symlinked
    # candidate is compared by its own identity, not its target's, so it is
    # never mistaken for the manifest and still reaches the non-regular
    # rejection below. Identity comparison cuts both ways, though: a *hard
    # link* to the manifest is inode-identical, so `samestat` alone would
    # silently drop `rogue.json` (created via `os.link(manifest, rogue)`)
    # from the inventory too — an unmanifested name evading the fail-closed
    # contract entirely (independent review, PR #23 head `3dfe299`). A
    # governed manifest legitimately has exactly one directory entry, so
    # `st_nlink > 1` is refused outright before any exclusion: with a link
    # count of one, the single `samestat` match can only be the manifest's
    # own entry (in whatever casing the filesystem stores), never an alias.
    if destination.parent == results and manifest_path.is_file():
        manifest_stat = manifest_path.lstat()
        if manifest_stat.st_nlink > 1:
            raise ManifestMismatchError(
                f"manifest {manifest_path} has {manifest_stat.st_nlink} hard "
                "links; a governed manifest must have exactly one directory "
                "entry, or a hard-linked alias could evade the inventory"
            )
        candidates = [
            candidate
            for candidate in candidates
            if not os.path.samestat(candidate.lstat(), manifest_stat)
        ]
    for candidate in candidates:
        _reject_non_regular(candidate, "candidate artefact")
    actual_paths = {path.name: path for path in candidates}
    missing = sorted(set(existing) - set(actual_paths))
    if missing:
        raise ManifestMismatchError(f"missing artefacts: {', '.join(missing)}")
    for name, record in existing.items():
        path = actual_paths[name]
        digest = _verify_size_and_hash_no_follow(
            path, record.bytes, name, "candidate artefact"
        )
        if digest != record.sha256:
            raise ManifestMismatchError(f"SHA-256 mismatch: {name}")
    appended = []
    for name, path in actual_paths.items():
        if name in existing:
            continue
        size, digest = stat_size_and_hash_no_follow(path, "candidate artefact")
        appended.append(ManifestRecord(path=name, bytes=size, sha256=digest))
    complete = tuple(sorted((*records, *appended), key=lambda record: record.path))
    if appended or not manifest_path.is_file():
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
        write_no_follow(
            manifest_path,
            (json.dumps(payload, indent=2, ensure_ascii=True) + "\n").encode("utf-8"),
            "manifest",
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
    every ``*.json`` entry in ``results_dir`` — manifested or not — must also
    be a regular file held by ``results_dir`` itself, never a symbolic link or
    other non-regular entry (see :func:`_reject_non_regular`); a stray
    unmanifested entry of either kind is rejected outright rather than
    silently dropped from the inventory, since it would otherwise never
    surface as either "missing" or "unmanifested".

    Args:
        results_dir: Directory containing immutable stored JSON artefacts.
        manifest_path: Governed SHA-256 manifest.

    Returns:
        The validated manifest records.

    Raises:
        ManifestFormatError: If the manifest is malformed.
        ManifestMismatchError: If inventory, size, or digest checks fail, or if
            the manifest or any ``*.json`` entry in ``results_dir`` is not a
            regular file.
    """
    _reject_non_regular(manifest_path, "manifest")
    results = results_dir.resolve()
    records = load_manifest(manifest_path)
    expected = {record.path for record in records}
    candidates = sorted(results.glob("*.json"))
    if manifest_path.resolve().parent == results:
        # File-identity comparison, not name comparison — see
        # :func:`append_manifest`'s matching filter for why `lstat` +
        # `os.path.samestat` is required on every platform, not only
        # `os.path.normcase` on Windows (independent review, PR #23 head
        # `f370a29`), and why a multi-linked manifest must be refused before
        # any exclusion: a hard link to the manifest is inode-identical, so
        # `samestat` alone would silently exclude the alias from the
        # inventory instead of reporting it as unmanifested (independent
        # review, PR #23 head `3dfe299`). `load_manifest` above already
        # proved `manifest_path` exists, so no existence check is needed
        # before `lstat` here.
        manifest_stat = manifest_path.lstat()
        if manifest_stat.st_nlink > 1:
            raise ManifestMismatchError(
                f"manifest {manifest_path} has {manifest_stat.st_nlink} hard "
                "links; a governed manifest must have exactly one directory "
                "entry, or a hard-linked alias could evade the inventory"
            )
        candidates = [
            candidate
            for candidate in candidates
            if not os.path.samestat(candidate.lstat(), manifest_stat)
        ]
    for candidate in candidates:
        _reject_non_regular(candidate, "candidate artefact")
    actual = {path.name for path in candidates}
    missing = sorted(expected - actual)
    unexpected = sorted(actual - expected)
    if missing:
        raise ManifestMismatchError(f"missing artefacts: {', '.join(missing)}")
    if unexpected:
        raise ManifestMismatchError(f"unmanifested artefacts: {', '.join(unexpected)}")
    for record in records:
        path = results / record.path
        _reject_symlink(path, "manifested artefact")
        digest = _verify_size_and_hash_no_follow(
            path, record.bytes, record.path, "manifested artefact"
        )
        if digest != record.sha256:
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
