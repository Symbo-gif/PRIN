"""Configuration constants for the code-intelligence subsystem.

Centralizes the exclusion list, path-containment roots, secret-like file
patterns, and default Mermaid/analytics limits so every module (indexer,
analytics, Mermaid, MCP server) enforces the same policy.
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

#: Directories excluded from indexing regardless of .gitignore contents.
#: Mirrors generated/vendor/cache directories already present in this
#: repository's own .gitignore, plus universal generated-artifact names.
DEFAULT_EXCLUDE_DIR_NAMES = frozenset(
    {
        ".git",
        ".venv",
        "venv",
        "target",
        "dist",
        "build",
        "__pycache__",
        ".mypy_cache",
        ".pytest_cache",
        ".hypothesis",
        ".benchmarks",
        "node_modules",
        ".oberon",
        ".ruff_cache",
        ".tox",
    }
)

#: Path-prefix patterns (repo-relative, POSIX) excluded from indexing even
#: though they are not simple directory-name matches (e.g. the many
#: ``.pytest_basetemp*`` variants and Sphinx build output in this
#: repository).
DEFAULT_EXCLUDE_PATH_PREFIXES = (
    ".pytest_basetemp",
    "DOCS/sphinx/_build",
    "DOCS/archive",
    # This subsystem's own test fixtures are synthetic (deliberately include
    # a fake import cycle and a fake secret file to exercise the cycle
    # detector and the secret-exclusion filter) and must never appear in a
    # real analysis of the PRIN repository itself.
    "tools/code-intelligence/tests/fixtures",
)

#: Filename glob patterns that are never indexed for content and are always
#: excluded from any node/evidence text, regardless of exclusion overrides,
#: to guarantee no secret material can ever reach the graph or an MCP
#: response.
SECRET_LIKE_FILENAME_GLOBS = (
    ".env",
    ".env.*",
    "*.pem",
    "*.key",
    "*.p12",
    "*.pfx",
    "id_rsa*",
    "id_ed25519*",
    "*.jks",
    "*credentials*",
    "*secret*",
    "*.gpg",
)

#: File extensions the indexer knows how to parse, mapped to a language tag.
LANGUAGE_BY_EXTENSION = {
    ".py": "python",
    ".pyi": "python",
    ".rs": "rust",
    ".lean": "lean",
    ".toml": "toml",
    ".json": "json",
    ".yaml": "yaml",
    ".yml": "yaml",
    ".ts": "tsjs",
    ".tsx": "tsjs",
    ".js": "tsjs",
    ".jsx": "tsjs",
}

#: Default Mermaid diagram bounds (task requirement: readable output).
DEFAULT_MAX_NODES = 60
DEFAULT_MAX_EDGES = 150
DEFAULT_MAX_DEPTH = 4

#: Default query/search pagination bound.
DEFAULT_QUERY_LIMIT = 50
MAX_QUERY_LIMIT = 500

#: Forbidden import directions, as ``(from_prefix, to_prefix)`` pairs of
#: repository-relative path prefixes. Empty by default — no PRIN-specific
#: layering rule has been declared. A maintainer wiring this in should add
#: e.g. ``("python/prin/reporting", "python/prin/nn")`` to flag a reporting
#: module importing a neural-network module, if that direction is intended
#: to be forbidden. Consumed by
#: ``ci_analytics.metrics.check_boundary_violations``.
ARCHITECTURE_BOUNDARY_RULES: tuple[tuple[str, str], ...] = ()


@dataclass(frozen=True)
class Settings:
    """Resolved runtime settings for one invocation of the subsystem.

    Attributes:
        repo_root: Absolute, resolved repository root. All file access is
            contained to this path (see ``ci_mcp_server.security``).
        db_path: Absolute path to the SQLite graph database.
        output_dir: Absolute path to the directory Mermaid/export output is
            written to.
        telemetry_dir: Absolute path to the directory JSONL traces are
            written to.
        telemetry_enabled: Whether span emission is active for this process.
        extra_allowed_roots: Additional absolute roots MCP tools may resolve
            paths under, beyond ``repo_root`` (empty by default).
    """

    repo_root: Path
    db_path: Path
    output_dir: Path
    telemetry_dir: Path
    telemetry_enabled: bool
    extra_allowed_roots: tuple[Path, ...] = ()


def resolve_settings(
    repo_root: str | Path | None = None,
    db_path: str | Path | None = None,
) -> Settings:
    """Resolve settings from explicit args, environment, then defaults.

    Args:
        repo_root: Explicit repository root override.
        db_path: Explicit database path override.

    Returns:
        A fully-resolved :class:`Settings` instance.
    """
    root = Path(
        repo_root or os.environ.get("PRIN_CI_REPO_ROOT") or _default_repo_root()
    ).resolve()
    base = Path(__file__).resolve().parent
    resolved_db = Path(
        db_path or os.environ.get("PRIN_CI_DB") or (base / ".data" / "graph.db")
    ).resolve()
    output_dir = (base / "output").resolve()
    telemetry_dir = (base / ".data" / "traces").resolve()
    telemetry_enabled = os.environ.get("PRIN_DEVTOOLS_TELEMETRY", "0") not in (
        "0",
        "",
        "false",
        "False",
    )
    return Settings(
        repo_root=root,
        db_path=resolved_db,
        output_dir=output_dir,
        telemetry_dir=telemetry_dir,
        telemetry_enabled=telemetry_enabled,
    )


def _default_repo_root() -> Path:
    # ci_config.py -> tools/code-intelligence -> tools -> repo root
    return Path(__file__).resolve().parent.parent.parent
