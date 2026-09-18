"""Shared, read-only tool implementations used by both the MCP server and the CLI.

Keeping the logic here (rather than duplicated between ``cli.py`` and
``ci_mcp_server/server.py``) guarantees the CLI and the MCP tools always
return the same answer for the same question. Every function takes an
already-open :class:`~ci_graph.store.GraphStore` and the resolved
:class:`~ci_config.Settings`, and returns a plain, JSON-serializable dict.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from ci_analytics import churn, metrics
from ci_analytics.graph_view import build_graph_view
from ci_config import ARCHITECTURE_BOUNDARY_RULES, MAX_QUERY_LIMIT, Settings
from ci_graph.store import GraphStore, NodeRecord
from ci_indexer.orchestrator import IndexResult, run_index
from ci_mermaid.render import (
    SUPPORTED_KINDS,
    render_diagram,
    render_sequence_from_spans,
)
from ci_telemetry import summary as telemetry_summary
from ci_telemetry.ingest import ingest_telemetry


class ToolError(ValueError):
    """Raised for any user-facing tool failure (bad input, not found, etc.).

    Both ``cli.py`` and ``ci_mcp_server/server.py`` catch this and turn it
    into a structured, actionable error response instead of a stack trace.
    """


def _node_to_dict(node: NodeRecord) -> dict[str, Any]:
    return {
        "node_id": node.node_id,
        "node_type": node.node_type,
        "language": node.language,
        "repo_path": node.repo_path,
        "qualified_name": node.qualified_name,
        "start_line": node.start_line,
        "end_line": node.end_line,
        "label": node.label,
        "indexed_at_utc": node.indexed_at_utc,
        "attributes": node.attributes,
    }


def _resolve_node(store: GraphStore, identifier: str) -> NodeRecord:
    node = store.get_node(identifier)
    if node is not None:
        return node
    matches = store.search_nodes(identifier, limit=10)
    if not matches:
        msg = (
            f"no node found matching {identifier!r}; try search_graph first to "
            "find the exact node id or a repository-relative path"
        )
        raise ToolError(msg)
    for candidate in matches:
        if candidate.repo_path == identifier or candidate.qualified_name == identifier:
            return candidate
    return matches[0]


def index_repository(
    store_factory: Any, settings: Settings, *, force: bool = False
) -> dict[str, Any]:
    """Re-index the repository (writes only to the subsystem's own database).

    Args:
        store_factory: A zero-arg callable returning a writable
            :class:`~ci_graph.store.GraphStore` (a fresh connection is
            required here because query tools hold a read-only handle).
        settings: Resolved settings.
        force: If True, discard all previously indexed data before
            re-indexing.

    Returns:
        A summary of the index run.
    """
    store: GraphStore = store_factory()
    try:
        result: IndexResult = run_index(store, settings.repo_root, force=force)
    finally:
        store.close()
    return {
        "run_id": result.run_id,
        "index_version": result.index_version,
        "files_scanned": result.files_scanned,
        "files_indexed": result.files_indexed,
        "files_failed": result.files_failed,
        "files_skipped": result.files_skipped,
        "node_count": result.node_count,
        "edge_count": result.edge_count,
        "diagnostics_sample": result.diagnostics,
    }


def get_index_status(store: GraphStore, settings: Settings) -> dict[str, Any]:
    """Report whether an index exists and its last-run summary.

    Args:
        store: An open, read-only store.
        settings: Resolved settings.

    Returns:
        Index status, or ``{"indexed": False, ...}`` if never indexed.
    """
    latest = store.latest_run()
    if latest is None:
        return {
            "indexed": False,
            "message": "no index found; run the 'index' command or the "
            "index_repository tool first",
            "db_path": str(settings.db_path),
        }
    diagnostics = store.diagnostics_for_run(latest["run_id"])
    return {
        "indexed": True,
        "run_id": latest["run_id"],
        "started_at_utc": latest["started_at_utc"],
        "finished_at_utc": latest["finished_at_utc"],
        "status": latest["status"],
        "index_version": latest["index_version"],
        "files_scanned": latest["files_scanned"],
        "files_indexed": latest["files_indexed"],
        "files_failed": latest["files_failed"],
        "files_skipped": latest["files_skipped"],
        "node_count": store.node_count(),
        "edge_count": store.edge_count(),
        "diagnostic_count": len(diagnostics),
        "diagnostics_sample": [
            {
                "repo_path": d["repo_path"],
                "severity": d["severity"],
                "message": d["message"],
            }
            for d in diagnostics[:20]
        ],
        "db_path": str(settings.db_path),
    }


def search_graph(
    store: GraphStore,
    query: str,
    entity_types: list[str] | None = None,
    limit: int = 50,
) -> dict[str, Any]:
    """Search nodes by substring match.

    Args:
        store: An open, read-only store.
        query: Substring to search for.
        entity_types: Optional restriction to these node types.
        limit: Maximum results (capped).

    Returns:
        Matching nodes with a total-result-cap note if truncated.
    """
    if not query or not query.strip():
        msg = "query must be a non-empty string"
        raise ToolError(msg)
    limit = max(1, min(limit, MAX_QUERY_LIMIT))
    results = store.search_nodes(query, entity_types=entity_types, limit=limit)
    return {
        "query": query,
        "entity_types": entity_types,
        "result_count": len(results),
        "limit": limit,
        "results": [_node_to_dict(n) for n in results],
    }


def get_module_dependencies(
    store: GraphStore,
    path_or_module: str,
    direction: str = "both",
    depth: int = 1,
) -> dict[str, Any]:
    """Report import dependencies for a file/module.

    Args:
        store: An open, read-only store.
        path_or_module: A node id, repository-relative path, or qualified
            module name.
        direction: ``"in"`` (dependents), ``"out"`` (dependencies), or
            ``"both"``.
        depth: Maximum hop count.

    Returns:
        Structured dependency information with confidence/provenance per
        edge.
    """
    if direction not in ("in", "out", "both"):
        msg = "direction must be 'in', 'out', or 'both'"
        raise ToolError(msg)
    view = build_graph_view(store)
    node = _resolve_node(store, path_or_module)
    if node.node_id not in view.digraph:
        return {
            "target": _node_to_dict(node),
            "dependencies": [],
            "note": "isolated node",
        }
    from ci_mermaid.render import bfs_bounded  # local: shares BFS with diagrams

    restricted = metrics.restrict_edges(view, ["IMPORTS"])
    visited, truncated = bfs_bounded(
        restricted, node.node_id, direction, depth, max_nodes=500
    )
    visited.discard(node.node_id)
    deps = []
    for nid in sorted(visited):
        n = view.nodes_by_id.get(nid)
        deps.append(
            {
                "node_id": nid,
                "label": n.label if n else nid,
                "repo_path": n.repo_path if n else None,
                "external": bool(n and n.attributes.get("external")),
            }
        )
    return {
        "target": _node_to_dict(node),
        "direction": direction,
        "depth": depth,
        "dependency_count": len(deps),
        "dependencies": deps,
        "truncated": truncated,
    }


def get_symbol_call_graph(
    store: GraphStore,
    symbol: str,
    direction: str = "both",
    depth: int = 1,
) -> dict[str, Any]:
    """Report the call-graph neighborhood of a symbol.

    Args:
        store: An open, read-only store.
        symbol: A node id, qualified name, or simple name.
        direction: ``"callers"``, ``"callees"``, or ``"both"``.
        depth: Maximum hop count.

    Returns:
        Structured caller/callee information. All ``CALLS`` edges are
        ``provenance="naming_heuristic"`` — this is name-based resolution,
        not type-checked call resolution.
    """
    if direction not in ("callers", "callees", "both"):
        msg = "direction must be 'callers', 'callees', or 'both'"
        raise ToolError(msg)
    bfs_direction = {"callers": "in", "callees": "out", "both": "both"}[direction]
    view = build_graph_view(store)
    node = _resolve_node(store, symbol)
    from ci_mermaid.render import bfs_bounded

    restricted = metrics.restrict_edges(view, ["CALLS"])
    if node.node_id not in restricted:
        return {
            "target": _node_to_dict(node),
            "direction": direction,
            "related": [],
            "note": "no CALLS edges found for this symbol",
        }
    visited, truncated = bfs_bounded(
        restricted, node.node_id, bfs_direction, depth, max_nodes=500
    )
    visited.discard(node.node_id)
    related = [
        _node_to_dict(view.nodes_by_id[nid])
        for nid in sorted(visited)
        if nid in view.nodes_by_id
    ]
    return {
        "target": _node_to_dict(node),
        "direction": direction,
        "depth": depth,
        "related_count": len(related),
        "related": related,
        "truncated": truncated,
        "confidence_note": (
            "CALLS edges are naming-heuristic (unqualified name match), "
            "not type-resolved"
        ),
    }


def find_circular_dependencies(
    store: GraphStore, scope: str | None = None
) -> dict[str, Any]:
    """Detect circular dependencies via strongly connected components.

    Args:
        store: An open, read-only store.
        scope: Optional repository-relative path prefix to restrict results
            to (a cycle is included if any of its nodes' ``repo_path``
            starts with this prefix).

    Returns:
        The detected cycles, each with its member nodes.
    """
    view = build_graph_view(store)
    cycles = metrics.find_cycles(view)
    if scope:
        cycles = [
            c
            for c in cycles
            if any(
                (view.nodes_by_id[n].repo_path or "").startswith(scope)
                for n in c
                if n in view.nodes_by_id
            )
        ]
    return {
        "scope": scope,
        "cycle_count": len(cycles),
        "cycles": [
            {
                "size": len(cycle),
                "members": [
                    _node_to_dict(view.nodes_by_id[n])
                    for n in cycle
                    if n in view.nodes_by_id
                ],
            }
            for cycle in cycles[:100]
        ],
        "truncated": len(cycles) > 100,
        "method": (
            "networkx strongly_connected_components over "
            "IMPORTS/DEPENDS_ON/CALLS/REFERENCES edges"
        ),
    }


def get_hotspots(
    store: GraphStore,
    settings: Settings,
    metric: str = "pagerank",
    limit: int = 20,
) -> dict[str, Any]:
    """Report architectural hotspots by a chosen metric.

    Args:
        store: An open, read-only store.
        settings: Resolved settings (used for the repo root on ``churn``).
        metric: One of ``"pagerank"``, ``"fanin"``, ``"fanout"``,
            ``"churn"``, ``"runtime_latency"``.
        limit: Maximum results.

    Returns:
        Ranked hotspots, clearly labeled ``static_centrality`` or
        ``runtime_evidence``.
    """
    view = build_graph_view(store)
    limit = max(1, min(limit, MAX_QUERY_LIMIT))
    if metric == "pagerank":
        ranked = metrics.pagerank(view, limit=limit)
        return {
            "metric": metric,
            "evidence_kind": "static_centrality",
            "results": [
                {"node_id": r.node_id, "label": r.label, "score": r.score}
                for r in ranked
            ],
        }
    if metric == "fanin":
        fan_ranked = metrics.top_fan_in(view, limit=limit)
        return {
            "metric": metric,
            "evidence_kind": "static_centrality",
            "results": [
                {"node_id": r.node_id, "label": r.label, "count": r.count}
                for r in fan_ranked
            ],
        }
    if metric == "fanout":
        fan_ranked = metrics.top_fan_out(view, limit=limit)
        return {
            "metric": metric,
            "evidence_kind": "static_centrality",
            "results": [
                {"node_id": r.node_id, "label": r.label, "count": r.count}
                for r in fan_ranked
            ],
        }
    if metric == "churn":
        churn_result = churn.compute_churn(settings.repo_root)
        if not churn_result.available:
            return {
                "metric": metric,
                "evidence_kind": "static_centrality",
                "results": [],
                "note": (
                    "git history unavailable in this environment; "
                    "churn cannot be computed"
                ),
            }
        churn_ranked = sorted(
            churn_result.counts.items(), key=lambda kv: (-kv[1], kv[0])
        )[:limit]
        return {
            "metric": metric,
            "evidence_kind": "static_centrality",
            "commits_examined": churn_result.commits_examined,
            "results": [
                {"repo_path": repo_path, "commit_touch_count": count}
                for repo_path, count in churn_ranked
            ],
        }
    if metric == "runtime_latency":
        stats = telemetry_summary.slowest_operations(store, limit=limit)
        return {
            "metric": metric,
            "evidence_kind": "runtime_evidence",
            "results": [_stats_to_dict(s) for s in stats],
        }
    msg = (
        f"unknown metric {metric!r}; expected "
        "pagerank|fanin|fanout|churn|runtime_latency"
    )
    raise ToolError(msg)


def get_impact_analysis(
    store: GraphStore, target: str, depth: int = 3
) -> dict[str, Any]:
    """Report what may be affected if a node changes.

    Args:
        store: An open, read-only store.
        target: A node id, repository-relative path, or qualified name.
        depth: Maximum hop count.

    Returns:
        Affected nodes with hop distance from ``target``.
    """
    view = build_graph_view(store)
    node = _resolve_node(store, target)
    distances = metrics.impact_analysis(view, node.node_id, depth=depth)
    affected = [
        {**_node_to_dict(view.nodes_by_id[nid]), "hops": hops}
        for nid, hops in sorted(distances.items(), key=lambda kv: (kv[1], kv[0]))
        if nid in view.nodes_by_id
    ]
    return {
        "target": _node_to_dict(node),
        "depth": depth,
        "affected_count": len(affected),
        "affected": affected,
        "method": "reverse BFS over IMPORTS/DEPENDS_ON/CALLS/REFERENCES edges",
    }


def find_dependency_path(store: GraphStore, source: str, target: str) -> dict[str, Any]:
    """Find the shortest dependency path between two entities.

    Args:
        store: An open, read-only store.
        source: A node id, path, or qualified name.
        target: A node id, path, or qualified name.

    Returns:
        The path, or ``None`` if unreachable.
    """
    view = build_graph_view(store)
    src_node = _resolve_node(store, source)
    dst_node = _resolve_node(store, target)
    path = metrics.shortest_dependency_path(view, src_node.node_id, dst_node.node_id)
    return {
        "source": _node_to_dict(src_node),
        "target": _node_to_dict(dst_node),
        "path_found": path is not None,
        "path": [
            _node_to_dict(view.nodes_by_id[nid])
            for nid in (path or [])
            if nid in view.nodes_by_id
        ],
    }


def get_architecture_summary(
    store: GraphStore, scope: str | None = None
) -> dict[str, Any]:
    """Summarize the repository's architecture: counts, hotspots, cycles.

    Args:
        store: An open, read-only store.
        scope: Optional repository-relative path prefix to restrict node
            counts to.

    Returns:
        A summary suitable as a starting point before drilling into
        specific tools.
    """
    view = build_graph_view(store)
    nodes = [
        n
        for n in view.nodes_by_id.values()
        if not scope or (n.repo_path or "").startswith(scope)
    ]
    type_counts: dict[str, int] = {}
    language_counts: dict[str, int] = {}
    for n in nodes:
        type_counts[n.node_type] = type_counts.get(n.node_type, 0) + 1
        if n.language:
            language_counts[n.language] = language_counts.get(n.language, 0) + 1
    top_pagerank = metrics.pagerank(view, limit=10)
    cycles = metrics.find_cycles(view)
    articulation = metrics.articulation_points(view)
    dead_code = metrics.dead_code_candidates(view, limit=10)
    boundary_violations = metrics.check_boundary_violations(
        view, ARCHITECTURE_BOUNDARY_RULES
    )
    return {
        "scope": scope,
        "node_count": len(nodes),
        "edge_count": store.edge_count(),
        "node_type_counts": dict(sorted(type_counts.items())),
        "language_counts": dict(sorted(language_counts.items())),
        "top_pagerank_hotspots": [
            {"node_id": r.node_id, "label": r.label, "score": r.score}
            for r in top_pagerank
        ],
        "circular_dependency_count": len(cycles),
        "articulation_point_count": len(articulation),
        "dead_code_candidate_count_sample": len(dead_code),
        "architecture_boundary_rules_configured": len(ARCHITECTURE_BOUNDARY_RULES),
        "architecture_boundary_violations": [
            {
                "src_id": v.src_id,
                "dst_id": v.dst_id,
                "rule": list(v.rule),
                "confidence": v.confidence,
                "provenance": v.provenance,
            }
            for v in boundary_violations[:50]
        ],
        "note": (
            "hotspot/cycle counts are static-analysis evidence; see "
            "get_hotspots(metric='runtime_latency') for runtime evidence"
        ),
    }


def generate_mermaid_diagram(
    store: GraphStore,
    settings: Settings,
    kind: str,
    target: str | None = None,
    direction: str = "both",
    depth: int = 4,
    max_nodes: int = 60,
    max_edges: int = 150,
    write_file: bool = True,
) -> dict[str, Any]:
    """Generate a bounded Mermaid diagram.

    Args:
        store: An open, read-only store.
        settings: Resolved settings (used for the output directory).
        kind: One of :data:`ci_mermaid.render.SUPPORTED_KINDS`.
        target: A node id, path, or qualified name (required for
            ``module_deps``/``call_graph``/``neighborhood``).
        direction: Direction hint passed to the underlying renderer.
        depth: Maximum BFS hop count.
        max_nodes: Maximum nodes rendered.
        max_edges: Maximum edges rendered.
        write_file: If True, also write the diagram to
            ``output/<kind>-<timestamp>.mmd``.

    Returns:
        The Mermaid source plus truncation metadata and, if written, the
        output file path.
    """
    if kind not in SUPPORTED_KINDS:
        msg = f"kind must be one of {SUPPORTED_KINDS}"
        raise ToolError(msg)
    view = build_graph_view(store)
    resolved_target = None
    if target:
        resolved_target = _resolve_node(store, target).node_id
    try:
        result = render_diagram(
            view,
            kind,
            target=resolved_target,
            direction=direction,
            depth=depth,
            max_nodes=max_nodes,
            max_edges=max_edges,
        )
    except ValueError as exc:
        raise ToolError(str(exc)) from exc

    output_path = None
    if write_file:
        output_path = _write_diagram_file(settings.output_dir, kind, result.mermaid)
    return {
        "kind": result.kind,
        "mermaid": result.mermaid,
        "node_count": result.node_count,
        "edge_count": result.edge_count,
        "truncated": result.truncated,
        "omitted_nodes": result.omitted_nodes,
        "omitted_edges": result.omitted_edges,
        "notes": result.notes,
        "output_file": str(output_path) if output_path else None,
    }


def _write_diagram_file(output_dir: Path, kind: str, mermaid: str) -> Path:
    from ci_graph.store import utc_now_iso

    output_dir.mkdir(parents=True, exist_ok=True)
    timestamp = utc_now_iso().replace(":", "").replace("+00:00", "Z").replace(".", "")
    path = output_dir / f"{kind}-{timestamp}.mmd"
    path.write_text(mermaid, encoding="utf-8")
    return path


def list_proof_solver_benchmark_links(
    store: GraphStore, scope: str | None = None
) -> dict[str, Any]:
    """List theorem/proof/benchmark/solver nodes and their known relationships.

    Args:
        store: An open, read-only store.
        scope: Optional repository-relative path prefix restriction.

    Returns:
        Currently-detected theorem declarations (from the Lean adapter) and
        their containing files. Detection of solver invocations (e.g. Z3),
        benchmarks, and result artifacts beyond Lean declarations is a
        known limitation of this indexing pass (see
        ``DOCS/devtools/visualization-mcp-plan.md`` §9) — this tool reports
        exactly what is structurally detected today rather than fabricating
        coverage it does not have.
    """
    theorem_nodes = [
        n
        for n in store.search_nodes("", entity_types=["theorem"], limit=500)
        if not scope or (n.repo_path or "").startswith(scope)
    ]
    links = []
    for node in theorem_nodes:
        defines_edges = store.edges_to(node.node_id, edge_types=["DEFINES"])
        links.append(
            {
                "theorem": _node_to_dict(node),
                "defined_in": [e.src_id for e in defines_edges],
                "semantic_status": node.attributes.get(
                    "semantic_status", "declaration_only_not_checked"
                ),
            }
        )
    return {
        "scope": scope,
        "theorem_count": len(links),
        "theorems": links,
        "known_limitation": (
            "solver_invocation/benchmark/experiment_config/result_artifact node "
            "types are defined in the schema but not yet populated by any "
            "adapter; only Lean theorem/lemma/def declarations are detected "
            "in this pass"
        ),
    }


def query_runtime_summary(
    store: GraphStore, settings: Settings, time_range: str | None = None
) -> dict[str, Any]:
    """Summarize ingested runtime telemetry.

    Args:
        store: An open, read-only store.
        settings: Resolved settings.
        time_range: Currently informational only (e.g. ``"24h"``); spans
            are not yet filtered by it (see known limitations) — all
            ingested spans are summarized.

    Returns:
        Per-operation statistics, or a note if telemetry was never
        enabled/ingested.
    """
    total = store.span_count()
    if total == 0:
        return {
            "span_count": 0,
            "note": (
                "no runtime spans ingested; set PRIN_DEVTOOLS_TELEMETRY=1, run "
                "some subsystem commands, then run 'telemetry-summary --ingest'"
            ),
        }
    stats = telemetry_summary.operation_stats(store)
    return {
        "span_count": total,
        "time_range_requested": time_range,
        "operation_count": len(stats),
        "operations": [_stats_to_dict(s) for s in stats],
    }


def get_slowest_operations(
    store: GraphStore, metric: str = "p95", limit: int = 20
) -> dict[str, Any]:
    """Report the slowest operations by a chosen percentile.

    Args:
        store: An open, read-only store.
        metric: One of ``"p50"``, ``"p95"``, ``"p99"``.
        limit: Maximum results.

    Returns:
        Operations sorted by descending value of the chosen percentile.
    """
    if metric not in ("p50", "p95", "p99"):
        msg = "metric must be 'p50', 'p95', or 'p99'"
        raise ToolError(msg)
    stats = telemetry_summary.operation_stats(store)
    key = f"{metric}_ms"
    stats.sort(key=lambda s: (-getattr(s, key), s.operation_name))
    return {
        "metric": metric,
        "results": [_stats_to_dict(s) for s in stats[: max(1, limit)]],
    }


def get_trace_or_flow(store: GraphStore, trace_id_or_operation: str) -> dict[str, Any]:
    """Return the spans for a trace id or an operation name.

    Args:
        store: An open, read-only store.
        trace_id_or_operation: A trace id (exact match) or operation name.

    Returns:
        The matching spans and, if any were found, a rendered Mermaid
        sequence diagram.
    """
    rows = store.trace(trace_id_or_operation)
    lookup_kind = "trace_id"
    if not rows:
        rows = store.spans_for_operation(trace_id_or_operation)
        lookup_kind = "operation_name"
    if not rows:
        msg = f"no spans found for trace id or operation name {trace_id_or_operation!r}"
        raise ToolError(msg)
    spans = [dict(r) for r in rows]
    diagram = render_sequence_from_spans(spans)
    return {
        "lookup_kind": lookup_kind,
        "span_count": len(spans),
        "spans": spans,
        "mermaid_sequence": diagram.mermaid,
    }


def explain_graph_evidence(store: GraphStore, node_or_edge_id: str) -> dict[str, Any]:
    """Explain why a node or edge exists in the graph.

    Args:
        store: An open, read-only store.
        node_or_edge_id: A node id, or an edge key formatted
            ``"<src_id>|<edge_type>|<dst_id>"`` (as produced by this same
            tool's edge listings).

    Returns:
        The node/edge with its stored evidence (a small snippet captured
        at index time, never full file contents) and confidence/provenance.
    """
    from ci_mcp_server.security import redact_evidence

    if "|" in node_or_edge_id:
        src_id, edge_type, dst_id = node_or_edge_id.split("|", 2)
        for edge in store.edges_from(src_id, edge_types=[edge_type]):
            if edge.dst_id == dst_id:
                return {
                    "kind": "edge",
                    "src_id": edge.src_id,
                    "dst_id": edge.dst_id,
                    "edge_type": edge.edge_type,
                    "confidence": edge.confidence,
                    "provenance": edge.provenance,
                    "evidence": redact_evidence(edge.evidence),
                }
        msg = f"no edge found matching {node_or_edge_id!r}"
        raise ToolError(msg)

    node = _resolve_node(store, node_or_edge_id)
    outbound = store.edges_from(node.node_id)
    inbound = store.edges_to(node.node_id)
    return {
        "kind": "node",
        "node": _node_to_dict(node),
        "outbound_edge_count": len(outbound),
        "inbound_edge_count": len(inbound),
        "outbound_sample": [
            {
                "edge_key": f"{e.src_id}|{e.edge_type}|{e.dst_id}",
                "edge_type": e.edge_type,
                "dst_id": e.dst_id,
                "confidence": e.confidence,
                "provenance": e.provenance,
                "evidence": redact_evidence(e.evidence),
            }
            for e in outbound[:20]
        ],
        "inbound_sample": [
            {
                "edge_key": f"{e.src_id}|{e.edge_type}|{e.dst_id}",
                "edge_type": e.edge_type,
                "src_id": e.src_id,
                "confidence": e.confidence,
                "provenance": e.provenance,
                "evidence": redact_evidence(e.evidence),
            }
            for e in inbound[:20]
        ],
    }


def telemetry_ingest(store: GraphStore, settings: Settings) -> dict[str, Any]:
    """Ingest all local JSONL telemetry files into the graph store.

    Args:
        store: An open, writable store.
        settings: Resolved settings (telemetry directory).

    Returns:
        Ingestion counts.
    """
    result = ingest_telemetry(store, settings.telemetry_dir)
    return {
        "files_scanned": result.files_scanned,
        "spans_ingested": result.spans_ingested,
        "spans_skipped": result.spans_skipped,
    }


def _stats_to_dict(s: telemetry_summary.OperationStats) -> dict[str, Any]:
    return {
        "operation_name": s.operation_name,
        "count": s.count,
        "p50_ms": round(s.p50_ms, 3),
        "p95_ms": round(s.p95_ms, 3),
        "p99_ms": round(s.p99_ms, 3),
        "mean_ms": round(s.mean_ms, 3),
        "error_count": s.error_count,
        "error_rate": round(s.error_rate, 4),
    }
