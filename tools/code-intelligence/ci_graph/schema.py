"""SQLite schema for the local code knowledge graph.

The schema models the entities and edges required by the visualization/MCP
subsystem plan (``DOCS/devtools/visualization-mcp-plan.md``): typed nodes
with source-location metadata, directed typed edges with confidence and
provenance, index-run bookkeeping for cache invalidation, and an optional
runtime-span table for the observability layer. SQLite is the only storage
backend so the system works entirely locally on Windows with no server
process.
"""

from __future__ import annotations

#: Node types the indexer may emit. Kept as a plain tuple (not an enum) so
#: the SQLite ``CHECK`` constraint and Python-side validation share one
#: source of truth without a runtime dependency on a shared enum module.
NODE_TYPES = (
    "repository",
    "directory",
    "file",
    "module",
    "class",
    "function",
    "method",
    "test",
    "cli_command",
    "config_file",
    "config_key",
    "solver_invocation",
    "theorem",
    "proof_artifact",
    "benchmark",
    "experiment_config",
    "result_artifact",
    "external_service",
    "unknown",
)

#: Edge types. Directed, typed, and always carrying confidence/provenance.
EDGE_TYPES = (
    "CONTAINS",
    "IMPORTS",
    "DEFINES",
    "CALLS",
    "REFERENCES",
    "IMPLEMENTS",
    "TESTS",
    "CONFIGURES",
    "INVOKES",
    "PROVES",
    "DEPENDS_ON",
    "PRODUCES",
    "CONSUMES",
    "EMITS",
    "VALIDATES",
)

#: Provenance values. Never claim ``exact_parser`` for a relationship that
#: was actually inferred by naming convention or textual heuristic.
PROVENANCE_VALUES = (
    "exact_parser",
    "static_inference",
    "naming_heuristic",
    "runtime_trace",
    "manual_annotation",
)

SCHEMA_VERSION = 1

DDL = f"""
PRAGMA journal_mode = WAL;
PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS schema_meta (
    key   TEXT PRIMARY KEY,
    value TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS index_runs (
    run_id          INTEGER PRIMARY KEY AUTOINCREMENT,
    started_at_utc  TEXT NOT NULL,
    finished_at_utc TEXT,
    repo_root       TEXT NOT NULL,
    files_scanned   INTEGER NOT NULL DEFAULT 0,
    files_indexed   INTEGER NOT NULL DEFAULT 0,
    files_failed    INTEGER NOT NULL DEFAULT 0,
    files_skipped   INTEGER NOT NULL DEFAULT 0,
    index_version   TEXT NOT NULL,
    status          TEXT NOT NULL DEFAULT 'running'
        CHECK (status IN ('running', 'complete', 'failed'))
);

CREATE TABLE IF NOT EXISTS nodes (
    node_id       TEXT PRIMARY KEY,
    node_type     TEXT NOT NULL CHECK (node_type IN {NODE_TYPES!r}),
    language      TEXT,
    repo_path     TEXT,
    qualified_name TEXT,
    start_line    INTEGER,
    end_line      INTEGER,
    content_hash  TEXT,
    label         TEXT NOT NULL,
    indexed_at_utc TEXT NOT NULL,
    run_id        INTEGER NOT NULL REFERENCES index_runs(run_id),
    attributes_json TEXT NOT NULL DEFAULT '{{}}'
);

CREATE INDEX IF NOT EXISTS idx_nodes_type ON nodes(node_type);
CREATE INDEX IF NOT EXISTS idx_nodes_repo_path ON nodes(repo_path);
CREATE INDEX IF NOT EXISTS idx_nodes_language ON nodes(language);

CREATE TABLE IF NOT EXISTS edges (
    edge_id      INTEGER PRIMARY KEY AUTOINCREMENT,
    src_id       TEXT NOT NULL REFERENCES nodes(node_id) ON DELETE CASCADE,
    dst_id       TEXT NOT NULL REFERENCES nodes(node_id) ON DELETE CASCADE,
    edge_type    TEXT NOT NULL CHECK (edge_type IN {EDGE_TYPES!r}),
    confidence   REAL NOT NULL CHECK (confidence >= 0.0 AND confidence <= 1.0),
    provenance   TEXT NOT NULL CHECK (provenance IN {PROVENANCE_VALUES!r}),
    evidence_json TEXT NOT NULL DEFAULT '{{}}',
    run_id       INTEGER NOT NULL REFERENCES index_runs(run_id),
    UNIQUE (src_id, dst_id, edge_type)
);

CREATE INDEX IF NOT EXISTS idx_edges_src ON edges(src_id, edge_type);
CREATE INDEX IF NOT EXISTS idx_edges_dst ON edges(dst_id, edge_type);
CREATE INDEX IF NOT EXISTS idx_edges_type ON edges(edge_type);

CREATE TABLE IF NOT EXISTS diagnostics (
    diagnostic_id INTEGER PRIMARY KEY AUTOINCREMENT,
    run_id        INTEGER NOT NULL REFERENCES index_runs(run_id),
    repo_path     TEXT NOT NULL,
    severity      TEXT NOT NULL CHECK (severity IN ('info', 'warning', 'error')),
    message       TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS runtime_spans (
    span_id        TEXT PRIMARY KEY,
    trace_id       TEXT NOT NULL,
    parent_span_id TEXT,
    operation_name TEXT NOT NULL,
    start_utc      TEXT NOT NULL,
    end_utc        TEXT NOT NULL,
    duration_ms    REAL NOT NULL,
    status         TEXT NOT NULL CHECK (status IN ('ok', 'error')),
    error_class    TEXT,
    attributes_json TEXT NOT NULL DEFAULT '{{}}',
    ingested_at_utc TEXT NOT NULL,
    source_file    TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_spans_op ON runtime_spans(operation_name);
CREATE INDEX IF NOT EXISTS idx_spans_trace ON runtime_spans(trace_id);
"""


def initialize_schema(conn: object) -> None:
    """Create all tables/indexes if absent and record the schema version.

    Args:
        conn: An open ``sqlite3.Connection``.
    """
    conn.executescript(DDL)  # type: ignore[attr-defined]
    conn.execute(  # type: ignore[attr-defined]
        "INSERT OR REPLACE INTO schema_meta(key, value) VALUES ('schema_version', ?)",
        (str(SCHEMA_VERSION),),
    )
    conn.commit()  # type: ignore[attr-defined]
