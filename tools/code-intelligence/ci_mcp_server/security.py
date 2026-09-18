"""Path containment and secret-exposure defense-in-depth for MCP tools.

Every MCP tool is read-only against the SQLite store, but this module is
the second, independent layer: even if a future tool were to accept a
filesystem path, it could never resolve outside the repository root (or an
explicitly permitted extra root), and any evidence string is re-checked
against secret-like patterns before being returned, even though the indexer
already refuses to read such files' content at index time.
"""

from __future__ import annotations

from pathlib import Path

from ci_indexer.orchestrator import is_secret_like


class PathEscapeError(ValueError):
    """Raised when a requested path would resolve outside allowed roots."""


def ensure_contained(candidate: str | Path, allowed_roots: tuple[Path, ...]) -> Path:
    """Resolve ``candidate`` and confirm it stays within an allowed root.

    Args:
        candidate: A path, absolute or relative, requested by a tool caller.
        allowed_roots: One or more absolute directories the result must be
            contained within.

    Returns:
        The resolved, contained path.

    Raises:
        PathEscapeError: If the resolved path is not under any allowed
            root.
    """
    resolved = Path(candidate).resolve()
    for root in allowed_roots:
        try:
            resolved.relative_to(root)
            return resolved
        except ValueError:
            continue
    msg = f"path {candidate!r} resolves outside all permitted roots"
    raise PathEscapeError(msg)


def redact_evidence(evidence: dict[str, object]) -> dict[str, object]:
    """Strip evidence values that look like they came from a secret file.

    Args:
        evidence: The stored evidence blob for a node/edge.

    Returns:
        The same evidence, or a redaction placeholder if any string value
        matches a secret-like pattern. Defense in depth: the indexer never
        stores content from secret-like files in the first place (see
        ``ci_indexer.orchestrator.is_secret_like``), so this should never
        trigger in practice.
    """
    for value in evidence.values():
        if isinstance(value, str) and is_secret_like(value):
            return {
                "redacted": True,
                "reason": "evidence matched a secret-like pattern",
            }
    return evidence
