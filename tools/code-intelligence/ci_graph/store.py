"""SQLite-backed graph store: typed CRUD and query helpers.

``GraphStore`` is the single point of contact with the SQLite database for
every other module (indexer, analytics, mermaid, MCP server). It never
returns raw file contents beyond the small, index-time-captured evidence
snippet, and every write is UTC-timestamped and deterministic.
"""

from __future__ import annotations

import json
import sqlite3
from dataclasses import dataclass, field
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from ci_graph.schema import EDGE_TYPES, NODE_TYPES, PROVENANCE_VALUES, initialize_schema


def utc_now_iso() -> str:
    """Return the current UTC time as an ISO-8601 string with ``Z`` suffix.

    Returns:
        e.g. ``"2026-09-18T12:00:00.000000+00:00"``.
    """
    return datetime.now(UTC).isoformat()


@dataclass(frozen=True)
class NodeRecord:
    """One node as returned from the store.

    Attributes:
        node_id: Stable node identifier.
        node_type: One of :data:`ci_graph.schema.NODE_TYPES`.
        language: Short language tag, or ``None`` for language-agnostic
            nodes (repository/directory).
        repo_path: POSIX repository-relative path, or ``None``.
        qualified_name: Dotted symbol name, or ``None`` for non-symbol
            nodes.
        start_line: 1-indexed start line, or ``None``.
        end_line: 1-indexed end line, or ``None``.
        content_hash: SHA-256 hex digest of the source file at index time,
            or ``None``.
        label: Human-readable label for diagrams/search results.
        indexed_at_utc: UTC ISO timestamp of the index run that wrote this
            node.
        attributes: Free-form JSON-serializable metadata (e.g. parameter
            counts, decorator names).
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
    indexed_at_utc: str
    attributes: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class EdgeRecord:
    """One edge as returned from the store.

    Attributes:
        src_id: Source node id.
        dst_id: Destination node id.
        edge_type: One of :data:`ci_graph.schema.EDGE_TYPES`.
        confidence: Confidence in ``[0.0, 1.0]``.
        provenance: One of :data:`ci_graph.schema.PROVENANCE_VALUES`.
        evidence: Small JSON-serializable evidence blob (e.g. the matched
            source line), never full file contents.
    """

    src_id: str
    dst_id: str
    edge_type: str
    confidence: float
    provenance: str
    evidence: dict[str, Any] = field(default_factory=dict)


class GraphStore:
    """Owns the SQLite connection and all reads/writes to the code graph."""

    def __init__(self, db_path: Path, *, read_only: bool = False) -> None:
        """Open (and if needed, create) the graph database.

        Args:
            db_path: Filesystem path to the SQLite database file.
            read_only: If True, open in SQLite URI read-only mode. Used by
                the MCP server so a running index can never be mutated by a
                query tool.
        """
        self.db_path = db_path
        if read_only:
            if not db_path.exists():
                msg = f"graph database not found at {db_path}; run 'index' first"
                raise FileNotFoundError(msg)
            uri = f"file:{db_path.as_posix()}?mode=ro"
            self._conn = sqlite3.connect(uri, uri=True, check_same_thread=False)
        else:
            db_path.parent.mkdir(parents=True, exist_ok=True)
            self._conn = sqlite3.connect(str(db_path), check_same_thread=False)
            initialize_schema(self._conn)
        self._conn.row_factory = sqlite3.Row

    def close(self) -> None:
        """Close the underlying SQLite connection."""
        self._conn.close()

    def __enter__(self) -> GraphStore:
        """Return self for use as a context manager."""
        return self

    def __exit__(self, *_exc: object) -> None:
        """Close the connection on context-manager exit."""
        self.close()

    # -- index run lifecycle -------------------------------------------------

    def begin_run(self, repo_root: str, index_version: str) -> int:
        """Start a new index run and return its id.

        Args:
            repo_root: Absolute repository root path being indexed.
            index_version: Opaque version tag (content-hash aggregate) used
                for analytics cache invalidation.

        Returns:
            The new ``run_id``.
        """
        cur = self._conn.execute(
            "INSERT INTO index_runs(started_at_utc, repo_root, index_version, status) "
            "VALUES (?, ?, ?, 'running')",
            (utc_now_iso(), repo_root, index_version),
        )
        self._conn.commit()
        assert cur.lastrowid is not None, "INSERT always assigns a rowid"
        return int(cur.lastrowid)

    def finish_run(
        self,
        run_id: int,
        *,
        files_scanned: int,
        files_indexed: int,
        files_failed: int,
        files_skipped: int,
        index_version: str,
        status: str = "complete",
    ) -> None:
        """Mark an index run finished with summary counters.

        Args:
            run_id: The run to finish.
            files_scanned: Total files considered.
            files_indexed: Files successfully parsed (fully or partially).
            files_failed: Files that raised a parse error.
            files_skipped: Files excluded by ignore rules.
            index_version: The final content-hash-derived version tag,
                replacing the placeholder set by :meth:`begin_run` — this is
                what :func:`ci_analytics.graph_view.build_graph_view` keys
                its cache on, so a stale value here would silently serve a
                pre-reindex graph view for the rest of a long-running MCP
                server process.
            status: ``"complete"`` or ``"failed"``.
        """
        self._conn.execute(
            "UPDATE index_runs SET finished_at_utc = ?, files_scanned = ?, "
            "files_indexed = ?, files_failed = ?, files_skipped = ?, "
            "index_version = ?, status = ? WHERE run_id = ?",
            (
                utc_now_iso(),
                files_scanned,
                files_indexed,
                files_failed,
                files_skipped,
                index_version,
                status,
                run_id,
            ),
        )
        self._conn.commit()

    def latest_run(self) -> sqlite3.Row | None:
        """Return the most recent index run row, or ``None`` if never indexed.

        Returns:
            A ``sqlite3.Row`` with the ``index_runs`` columns, or ``None``.
        """
        cur = self._conn.execute(
            "SELECT * FROM index_runs ORDER BY run_id DESC LIMIT 1"
        )
        row: sqlite3.Row | None = cur.fetchone()
        return row

    def clear_all(self) -> None:
        """Delete all nodes, edges, diagnostics, and index runs (full reset).

        Used by ``index --force`` and by the ``reset`` CLI/troubleshooting
        path. Runtime spans are preserved unless explicitly cleared.
        """
        self._conn.executescript(
            "DELETE FROM edges; DELETE FROM diagnostics; DELETE FROM nodes; "
            "DELETE FROM index_runs;"
        )
        self._conn.commit()

    # -- node/edge writes -----------------------------------------------------

    def upsert_node(
        self,
        *,
        node_id: str,
        node_type: str,
        language: str | None,
        repo_path: str | None,
        qualified_name: str | None,
        start_line: int | None,
        end_line: int | None,
        content_hash: str | None,
        label: str,
        run_id: int,
        attributes: dict[str, Any] | None = None,
    ) -> None:
        """Insert or replace a node.

        Args:
            node_id: Stable node identifier (see ``ci_graph.identity``).
            node_type: One of :data:`ci_graph.schema.NODE_TYPES`.
            language: Short language tag or ``None``.
            repo_path: POSIX repository-relative path or ``None``.
            qualified_name: Dotted symbol name or ``None``.
            start_line: 1-indexed start line or ``None``.
            end_line: 1-indexed end line or ``None``.
            content_hash: SHA-256 hex digest or ``None``.
            label: Human-readable label.
            run_id: The index run writing this node.
            attributes: Extra JSON-serializable metadata.

        Raises:
            ValueError: If ``node_type`` is not a recognized type.
        """
        if node_type not in NODE_TYPES:
            msg = f"unknown node_type {node_type!r}"
            raise ValueError(msg)
        self._conn.execute(
            "INSERT INTO nodes(node_id, node_type, language, repo_path, "
            "qualified_name, start_line, end_line, content_hash, label, "
            "indexed_at_utc, run_id, attributes_json) "
            "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?) "
            "ON CONFLICT(node_id) DO UPDATE SET "
            "node_type=excluded.node_type, language=excluded.language, "
            "repo_path=excluded.repo_path, qualified_name=excluded.qualified_name, "
            "start_line=excluded.start_line, end_line=excluded.end_line, "
            "content_hash=excluded.content_hash, label=excluded.label, "
            "indexed_at_utc=excluded.indexed_at_utc, run_id=excluded.run_id, "
            "attributes_json=excluded.attributes_json",
            (
                node_id,
                node_type,
                language,
                repo_path,
                qualified_name,
                start_line,
                end_line,
                content_hash,
                label,
                utc_now_iso(),
                run_id,
                json.dumps(attributes or {}, sort_keys=True),
            ),
        )

    def upsert_edge(
        self,
        *,
        src_id: str,
        dst_id: str,
        edge_type: str,
        confidence: float,
        provenance: str,
        run_id: int,
        evidence: dict[str, Any] | None = None,
    ) -> None:
        """Insert or replace an edge.

        Args:
            src_id: Source node id (must already exist).
            dst_id: Destination node id (must already exist).
            edge_type: One of :data:`ci_graph.schema.EDGE_TYPES`.
            confidence: Confidence in ``[0.0, 1.0]``.
            provenance: One of :data:`ci_graph.schema.PROVENANCE_VALUES`.
            run_id: The index run writing this edge.
            evidence: Small JSON-serializable evidence (e.g. matched line).

        Raises:
            ValueError: If ``edge_type``/``provenance`` is not recognized.
        """
        if edge_type not in EDGE_TYPES:
            msg = f"unknown edge_type {edge_type!r}"
            raise ValueError(msg)
        if provenance not in PROVENANCE_VALUES:
            msg = f"unknown provenance {provenance!r}"
            raise ValueError(msg)
        self._conn.execute(
            "INSERT INTO edges(src_id, dst_id, edge_type, confidence, "
            "provenance, evidence_json, run_id) VALUES (?, ?, ?, ?, ?, ?, ?) "
            "ON CONFLICT(src_id, dst_id, edge_type) DO UPDATE SET "
            "confidence=excluded.confidence, provenance=excluded.provenance, "
            "evidence_json=excluded.evidence_json, run_id=excluded.run_id",
            (
                src_id,
                dst_id,
                edge_type,
                confidence,
                provenance,
                json.dumps(evidence or {}, sort_keys=True),
                run_id,
            ),
        )

    def add_diagnostic(
        self, run_id: int, repo_path: str, severity: str, message: str
    ) -> None:
        """Record a per-file indexing diagnostic.

        Args:
            run_id: The index run this diagnostic belongs to.
            repo_path: POSIX repository-relative path.
            severity: ``"info"``, ``"warning"``, or ``"error"``.
            message: Human-readable diagnostic message (no raw source).
        """
        self._conn.execute(
            "INSERT INTO diagnostics(run_id, repo_path, severity, message) "
            "VALUES (?, ?, ?, ?)",
            (run_id, repo_path, severity, message),
        )

    def commit(self) -> None:
        """Flush pending writes to disk."""
        self._conn.commit()

    # -- reads ------------------------------------------------------------

    def get_node(self, node_id: str) -> NodeRecord | None:
        """Fetch a single node by id.

        Args:
            node_id: Stable node identifier.

        Returns:
            The node, or ``None`` if absent.
        """
        row = self._conn.execute(
            "SELECT * FROM nodes WHERE node_id = ?", (node_id,)
        ).fetchone()
        return _row_to_node(row) if row else None

    def search_nodes(
        self,
        query: str,
        *,
        entity_types: list[str] | None = None,
        limit: int = 50,
    ) -> list[NodeRecord]:
        """Search nodes by substring match on label/qualified_name/path.

        Args:
            query: Case-insensitive substring to match.
            entity_types: Optional restriction to these node types.
            limit: Maximum rows returned (paginate by narrowing ``query``).

        Returns:
            Matching nodes, most-recently-indexed first.
        """
        sql = (
            "SELECT * FROM nodes WHERE "
            "(label LIKE ? OR qualified_name LIKE ? OR repo_path LIKE ?)"
        )
        like = f"%{query}%"
        params: list[Any] = [like, like, like]
        if entity_types:
            placeholders = ",".join("?" for _ in entity_types)
            sql += f" AND node_type IN ({placeholders})"
            params.extend(entity_types)
        sql += " ORDER BY indexed_at_utc DESC LIMIT ?"
        params.append(max(1, min(limit, 500)))
        rows = self._conn.execute(sql, params).fetchall()
        return [_row_to_node(r) for r in rows]

    def edges_from(
        self, node_id: str, edge_types: list[str] | None = None
    ) -> list[EdgeRecord]:
        """Return outbound edges from a node.

        Args:
            node_id: Source node id.
            edge_types: Optional restriction to these edge types.

        Returns:
            Matching outbound edges.
        """
        sql = "SELECT * FROM edges WHERE src_id = ?"
        params: list[Any] = [node_id]
        if edge_types:
            placeholders = ",".join("?" for _ in edge_types)
            sql += f" AND edge_type IN ({placeholders})"
            params.extend(edge_types)
        rows = self._conn.execute(sql, params).fetchall()
        return [_row_to_edge(r) for r in rows]

    def edges_to(
        self, node_id: str, edge_types: list[str] | None = None
    ) -> list[EdgeRecord]:
        """Return inbound edges to a node.

        Args:
            node_id: Destination node id.
            edge_types: Optional restriction to these edge types.

        Returns:
            Matching inbound edges.
        """
        sql = "SELECT * FROM edges WHERE dst_id = ?"
        params: list[Any] = [node_id]
        if edge_types:
            placeholders = ",".join("?" for _ in edge_types)
            sql += f" AND edge_type IN ({placeholders})"
            params.extend(edge_types)
        rows = self._conn.execute(sql, params).fetchall()
        return [_row_to_edge(r) for r in rows]

    def all_nodes(self) -> list[NodeRecord]:
        """Return every node in the graph (bounded by the graph's own size).

        Returns:
            All nodes, in deterministic ``node_id`` order.
        """
        rows = self._conn.execute("SELECT * FROM nodes ORDER BY node_id").fetchall()
        return [_row_to_node(r) for r in rows]

    def all_edges(self) -> list[EdgeRecord]:
        """Return every edge in the graph (bounded by the graph's own size).

        Returns:
            All edges, in deterministic ``(src_id, dst_id, edge_type)`` order.
        """
        rows = self._conn.execute(
            "SELECT * FROM edges ORDER BY src_id, dst_id, edge_type"
        ).fetchall()
        return [_row_to_edge(r) for r in rows]

    def node_count(self) -> int:
        """Return the total number of nodes.

        Returns:
            Node count.
        """
        return int(self._conn.execute("SELECT COUNT(*) FROM nodes").fetchone()[0])

    def edge_count(self) -> int:
        """Return the total number of edges.

        Returns:
            Edge count.
        """
        return int(self._conn.execute("SELECT COUNT(*) FROM edges").fetchone()[0])

    def diagnostics_for_run(self, run_id: int) -> list[sqlite3.Row]:
        """Return diagnostics recorded during a given index run.

        Args:
            run_id: The index run id.

        Returns:
            Diagnostic rows, insertion order.
        """
        return self._conn.execute(
            "SELECT * FROM diagnostics WHERE run_id = ? ORDER BY diagnostic_id",
            (run_id,),
        ).fetchall()

    # -- runtime spans ------------------------------------------------------

    def insert_span(self, span: dict[str, Any], source_file: str) -> None:
        """Insert one runtime span (idempotent on ``span_id``).

        Args:
            span: A span dict matching ``ci_telemetry.spans.Span.to_dict()``.
            source_file: The JSONL file this span was ingested from, for
                traceability.
        """
        self._conn.execute(
            "INSERT OR REPLACE INTO runtime_spans(span_id, trace_id, "
            "parent_span_id, operation_name, start_utc, end_utc, duration_ms, "
            "status, error_class, attributes_json, ingested_at_utc, source_file) "
            "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (
                span["span_id"],
                span["trace_id"],
                span.get("parent_span_id"),
                span["operation_name"],
                span["start_utc"],
                span["end_utc"],
                span["duration_ms"],
                span["status"],
                span.get("error_class"),
                json.dumps(span.get("attributes", {}), sort_keys=True),
                utc_now_iso(),
                source_file,
            ),
        )

    def spans_by_operation(self, limit: int = 1000) -> dict[str, list[float]]:
        """Return duration samples grouped by operation name.

        Args:
            limit: Maximum spans considered per operation.

        Returns:
            Mapping of operation name to a list of durations in ms.
        """
        rows = self._conn.execute(
            "SELECT operation_name, duration_ms FROM runtime_spans "
            "ORDER BY start_utc DESC LIMIT ?",
            (max(1, min(limit, 100000)),),
        ).fetchall()
        out: dict[str, list[float]] = {}
        for r in rows:
            out.setdefault(r["operation_name"], []).append(float(r["duration_ms"]))
        return out

    def span_count(self) -> int:
        """Return the total number of ingested runtime spans.

        Returns:
            Span count.
        """
        return int(
            self._conn.execute("SELECT COUNT(*) FROM runtime_spans").fetchone()[0]
        )

    def trace(self, trace_id: str) -> list[sqlite3.Row]:
        """Return all spans belonging to one trace, ordered by start time.

        Args:
            trace_id: The trace identifier.

        Returns:
            Span rows for the trace.
        """
        return self._conn.execute(
            "SELECT * FROM runtime_spans WHERE trace_id = ? ORDER BY start_utc",
            (trace_id,),
        ).fetchall()

    def spans_for_operation(self, operation_name: str) -> list[sqlite3.Row]:
        """Return all spans for a given operation name, most recent first.

        Args:
            operation_name: Exact operation name to match.

        Returns:
            Span rows.
        """
        return self._conn.execute(
            "SELECT * FROM runtime_spans WHERE operation_name = ? "
            "ORDER BY start_utc DESC",
            (operation_name,),
        ).fetchall()


def _row_to_node(row: sqlite3.Row) -> NodeRecord:
    return NodeRecord(
        node_id=row["node_id"],
        node_type=row["node_type"],
        language=row["language"],
        repo_path=row["repo_path"],
        qualified_name=row["qualified_name"],
        start_line=row["start_line"],
        end_line=row["end_line"],
        content_hash=row["content_hash"],
        label=row["label"],
        indexed_at_utc=row["indexed_at_utc"],
        attributes=json.loads(row["attributes_json"] or "{}"),
    )


def _row_to_edge(row: sqlite3.Row) -> EdgeRecord:
    return EdgeRecord(
        src_id=row["src_id"],
        dst_id=row["dst_id"],
        edge_type=row["edge_type"],
        confidence=row["confidence"],
        provenance=row["provenance"],
        evidence=json.loads(row["evidence_json"] or "{}"),
    )
