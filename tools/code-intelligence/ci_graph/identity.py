"""Stable node identity and content-hashing helpers for the code graph.

Node identity is derived from a normalized, POSIX-style, repository-relative
path plus an optional qualified symbol name, never from a database auto
-increment key, so IDs are stable across re-indexing runs and are
human-readable in Mermaid diagrams and MCP tool output.
"""

from __future__ import annotations

import hashlib
from dataclasses import dataclass
from pathlib import PurePosixPath


def normalize_repo_path(repo_root: str, absolute_or_relative_path: str) -> str:
    """Normalize a filesystem path to a repository-relative POSIX path.

    Args:
        repo_root: Absolute path to the repository root.
        absolute_or_relative_path: A path inside the repository, absolute or
            already relative.

    Returns:
        A forward-slash, repository-relative path with no leading ``./`` or
        drive letter, suitable for use in a stable node identifier.
    """
    from pathlib import Path

    root = Path(repo_root).resolve()
    candidate = Path(absolute_or_relative_path)
    if not candidate.is_absolute():
        candidate = (root / candidate).resolve()
    else:
        candidate = candidate.resolve()
    try:
        rel = candidate.relative_to(root)
    except ValueError:
        # Outside the repository root: still normalize but keep the absolute
        # form so path-containment checks upstream can reject it explicitly
        # rather than silently rewriting it into a false in-repo identity.
        return PurePosixPath(candidate.as_posix()).as_posix()
    return PurePosixPath(rel.as_posix()).as_posix()


def file_node_id(language: str, repo_relative_path: str) -> str:
    """Build the stable node id for a file-level node.

    Args:
        language: Short language tag, e.g. ``"python"``, ``"rust"``,
            ``"lean"``, ``"toml"``, ``"json"``, ``"yaml"``, ``"tsjs"``.
        repo_relative_path: POSIX repository-relative path.

    Returns:
        The stable node id, e.g. ``"python:python/prin/__init__.py"``.
    """
    return f"{language}:{repo_relative_path}"


def symbol_node_id(language: str, repo_relative_path: str, qualified_name: str) -> str:
    """Build the stable node id for a symbol defined in a file.

    Args:
        language: Short language tag (see :func:`file_node_id`).
        repo_relative_path: POSIX repository-relative path of the defining
            file.
        qualified_name: Dotted/namespaced symbol name, unique within the
            file (e.g. ``"MyClass.my_method"``).

    Returns:
        The stable node id, e.g.
        ``"python:python/prin/nn/layer.py::MyClass.my_method"``.
    """
    return f"{language}:{repo_relative_path}::{qualified_name}"


def directory_node_id(repo_relative_dir: str) -> str:
    """Build the stable node id for a directory node.

    Args:
        repo_relative_dir: POSIX repository-relative directory path (``""``
            for the repository root).

    Returns:
        The stable node id, e.g. ``"dir:crates/prin-kernels"``.
    """
    return f"dir:{repo_relative_dir}" if repo_relative_dir else "dir:."


def content_hash(data: bytes) -> str:
    """Compute the SHA-256 content hash used for change detection.

    Args:
        data: Raw file bytes.

    Returns:
        Lowercase hex-encoded SHA-256 digest.
    """
    return hashlib.sha256(data).hexdigest()


@dataclass(frozen=True)
class RepoPath:
    """A validated, normalized, repository-relative path.

    Attributes:
        relative: POSIX repository-relative path string.
        absolute: Absolute filesystem path string.
    """

    relative: str
    absolute: str
