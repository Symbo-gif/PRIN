"""Shared data structures produced by every per-language adapter.

Each adapter parses one file's bytes and returns an :class:`AdapterOutput`;
the orchestrator (``ci_indexer.orchestrator``) is the only component that
writes to the :class:`~ci_graph.store.GraphStore`, resolves cross-file
imports/calls, and assigns run ids. This keeps every adapter a pure,
independently testable function with no database dependency.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Literal

Severity = Literal["info", "warning", "error"]


@dataclass
class ParsedNode:
    """A node discovered by an adapter, not yet written to the store.

    Attributes:
        node_id: Stable node id (see ``ci_graph.identity``).
        node_type: One of :data:`ci_graph.schema.NODE_TYPES`.
        language: Short language tag.
        repo_path: POSIX repository-relative path.
        qualified_name: Dotted symbol name, or ``None`` for file/dir nodes.
        start_line: 1-indexed start line, or ``None``.
        end_line: 1-indexed end line, or ``None``.
        content_hash: SHA-256 hex digest, or ``None``.
        label: Human-readable label.
        attributes: Extra JSON-serializable metadata.
    """

    node_id: str
    node_type: str
    language: str | None
    repo_path: str | None
    qualified_name: str | None
    start_line: int | None
    end_line: int | None
    content_hash: str | None
    label: str
    attributes: dict[str, Any] = field(default_factory=dict)


@dataclass
class ParsedEdge:
    """An edge discovered by an adapter, not yet written to the store.

    Attributes:
        src_id: Source node id (must be produced by the same or an earlier
            adapter pass).
        dst_id: Destination node id.
        edge_type: One of :data:`ci_graph.schema.EDGE_TYPES`.
        confidence: Confidence in ``[0.0, 1.0]``.
        provenance: One of :data:`ci_graph.schema.PROVENANCE_VALUES`.
        evidence: Small JSON-serializable evidence (e.g. matched line).
    """

    src_id: str
    dst_id: str
    edge_type: str
    confidence: float
    provenance: str
    evidence: dict[str, Any] = field(default_factory=dict)


@dataclass
class PendingImport:
    """An import/dependency reference whose target must be resolved later.

    Resolution happens in the orchestrator once every file in the
    repository has been parsed, because the target file may not have been
    visited yet (or may resolve to an external, non-repository package).

    Attributes:
        src_id: The importing node id (usually a file node).
        raw_target: The raw text of the import target (module path,
            crate::path, relative path, etc.) exactly as written.
        language: Short language tag of the importing file, used to select
            the correct resolution strategy.
        line: 1-indexed source line of the import statement, for evidence.
    """

    src_id: str
    raw_target: str
    language: str
    line: int | None = None


@dataclass
class PendingCall:
    """A call reference whose callee must be resolved by simple name later.

    Attributes:
        src_id: The calling symbol's node id.
        callee_name: The simple (unqualified) name of the called function.
        line: 1-indexed source line of the call, for evidence.
    """

    src_id: str
    callee_name: str
    line: int | None = None


@dataclass
class Diagnostic:
    """A per-file indexing diagnostic surfaced to ``status``/``verify-installation``.

    Attributes:
        severity: ``"info"``, ``"warning"``, or ``"error"``.
        message: Human-readable message. Never includes raw file contents.
    """

    severity: Severity
    message: str


@dataclass
class AdapterOutput:
    """Everything one adapter invocation produced for one file.

    Attributes:
        nodes: Nodes defined in this file (the file node itself is created
            by the orchestrator, not the adapter).
        edges: Edges fully resolvable within this single-file pass (e.g.
            ``DEFINES`` from the file to a symbol it declares).
        pending_imports: Import targets to resolve after the full repository
            has been parsed.
        pending_calls: Call targets to resolve after the full repository has
            been parsed.
        diagnostics: Parse diagnostics for this file.
        partial: True if the adapter could only partially parse the file
            (e.g. a syntax error midway through) — still reports what it
            found, per the "graceful partial indexing" requirement.
    """

    nodes: list[ParsedNode] = field(default_factory=list)
    edges: list[ParsedEdge] = field(default_factory=list)
    pending_imports: list[PendingImport] = field(default_factory=list)
    pending_calls: list[PendingCall] = field(default_factory=list)
    diagnostics: list[Diagnostic] = field(default_factory=list)
    partial: bool = False
