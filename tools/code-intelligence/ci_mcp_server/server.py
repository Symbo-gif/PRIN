"""Local, read-only MCP server exposing the code-intelligence graph.

Transport is STDIO only (per the plan, no network port is opened by
default). Every tool other than ``index_repository`` opens a read-only
SQLite connection per call, so a running server can never mutate the graph
except through the one explicit re-index tool, which only ever writes to
this subsystem's own private database — never to any file in the
repository being analyzed.
"""

from __future__ import annotations

from typing import Any

from mcp.server.fastmcp import FastMCP
from mcp.types import ToolAnnotations

from ci_config import Settings, resolve_settings
from ci_graph.store import GraphStore
from ci_mcp_server import tools as impl
from ci_mcp_server.tools import ToolError

_RO = ToolAnnotations(readOnlyHint=True, destructiveHint=False, openWorldHint=False)
_WRITE_OWN_DB_ONLY = ToolAnnotations(
    readOnlyHint=False, destructiveHint=False, idempotentHint=True, openWorldHint=False
)


def _open_ro(settings: Settings) -> GraphStore:
    return GraphStore(settings.db_path, read_only=True)


def _run_tool(fn: Any, *args: Any, **kwargs: Any) -> dict[str, Any]:
    try:
        result: dict[str, Any] = fn(*args, **kwargs)
        return result
    except ToolError as exc:
        return {"error": str(exc), "error_type": "ToolError"}
    except FileNotFoundError as exc:
        return {
            "error": str(exc),
            "error_type": "NotIndexed",
            "hint": "run the 'index' CLI command or the index_repository tool first",
        }
    except Exception as exc:
        return {"error": f"internal error: {exc}", "error_type": type(exc).__name__}


def build_server(settings: Settings | None = None) -> FastMCP:
    """Construct the FastMCP server with every read-only tool registered.

    Args:
        settings: Resolved settings; defaults to
            :func:`ci_config.resolve_settings`.

    Returns:
        The configured, not-yet-running :class:`FastMCP` server.
    """
    settings = settings or resolve_settings()
    mcp = FastMCP(
        name="prin-code-intelligence",
        instructions=(
            "Read-only local code knowledge graph and runtime-observability "
            "tools for the PRIN repository. All file access is contained to "
            f"{settings.repo_root}. Static-analysis results are heuristic "
            "unless marked provenance='exact_parser'; runtime results are "
            "only as complete as the telemetry that has been ingested."
        ),
    )

    @mcp.tool(annotations=_WRITE_OWN_DB_ONLY)
    def index_repository(force: bool = False) -> dict[str, Any]:
        """Index (or re-index) the repository into the local graph database.

        Only reads source files under the repository root and writes to
        this subsystem's own SQLite database; never modifies any file in
        the repository being analyzed.

        Args:
            force: If True, discard all previously indexed data first.
        """
        return _run_tool(
            impl.index_repository,
            lambda: GraphStore(settings.db_path, read_only=False),
            settings,
            force=force,
        )

    @mcp.tool(annotations=_RO)
    def get_index_status() -> dict[str, Any]:
        """Report whether an index exists and summarize the last index run."""
        with _open_ro(settings) as store:
            return _run_tool(impl.get_index_status, store, settings)

    @mcp.tool(annotations=_RO)
    def search_graph(
        query: str, entity_types: list[str] | None = None, limit: int = 50
    ) -> dict[str, Any]:
        """Search the graph for nodes whose label, name, or path matches a substring.

        Args:
            query: Case-insensitive substring to search for.
            entity_types: Optional restriction to these node types (e.g.
                ``["function", "class"]``).
            limit: Maximum results (capped at 500).
        """
        with _open_ro(settings) as store:
            return _run_tool(impl.search_graph, store, query, entity_types, limit)

    @mcp.tool(annotations=_RO)
    def get_module_dependencies(
        path_or_module: str, direction: str = "both", depth: int = 1
    ) -> dict[str, Any]:
        """Report import dependencies for a file or module.

        Args:
            path_or_module: A node id, repository-relative path, or
                qualified module name.
            direction: ``"in"`` (dependents), ``"out"`` (dependencies), or
                ``"both"``.
            depth: Maximum hop count (1-12).
        """
        with _open_ro(settings) as store:
            return _run_tool(
                impl.get_module_dependencies, store, path_or_module, direction, depth
            )

    @mcp.tool(annotations=_RO)
    def get_symbol_call_graph(
        symbol: str, direction: str = "both", depth: int = 1
    ) -> dict[str, Any]:
        """Report the call-graph neighborhood of a function/method (naming-heuristic).

        Args:
            symbol: A node id, qualified name, or simple name.
            direction: ``"callers"``, ``"callees"``, or ``"both"``.
            depth: Maximum hop count (1-12).
        """
        with _open_ro(settings) as store:
            return _run_tool(
                impl.get_symbol_call_graph, store, symbol, direction, depth
            )

    @mcp.tool(annotations=_RO)
    def find_circular_dependencies(scope: str | None = None) -> dict[str, Any]:
        """Detect circular dependencies (strongly connected components) in the graph.

        Args:
            scope: Optional repository-relative path prefix to restrict
                results to.
        """
        with _open_ro(settings) as store:
            return _run_tool(impl.find_circular_dependencies, store, scope)

    @mcp.tool(annotations=_RO)
    def get_hotspots(metric: str = "pagerank", limit: int = 20) -> dict[str, Any]:
        """Report architectural hotspots by pagerank, fanin, fanout, churn, or latency.

        Args:
            metric: One of ``"pagerank"``, ``"fanin"``, ``"fanout"``,
                ``"churn"``, ``"runtime_latency"``.
            limit: Maximum results.
        """
        with _open_ro(settings) as store:
            return _run_tool(impl.get_hotspots, store, settings, metric, limit)

    @mcp.tool(annotations=_RO)
    def get_impact_analysis(target: str, depth: int = 3) -> dict[str, Any]:
        """Report what may be affected if a file/module/symbol changes.

        Args:
            target: A node id, repository-relative path, or qualified name.
            depth: Maximum hop count.
        """
        with _open_ro(settings) as store:
            return _run_tool(impl.get_impact_analysis, store, target, depth)

    @mcp.tool(annotations=_RO)
    def find_dependency_path(source: str, target: str) -> dict[str, Any]:
        """Find the shortest dependency path between two entities.

        Args:
            source: A node id, repository-relative path, or qualified name.
            target: A node id, repository-relative path, or qualified name.
        """
        with _open_ro(settings) as store:
            return _run_tool(impl.find_dependency_path, store, source, target)

    @mcp.tool(annotations=_RO)
    def get_architecture_summary(scope: str | None = None) -> dict[str, Any]:
        """Summarize repository architecture: node/edge counts, top hotspots, cycles.

        Args:
            scope: Optional repository-relative path prefix restriction.
        """
        with _open_ro(settings) as store:
            return _run_tool(impl.get_architecture_summary, store, scope)

    @mcp.tool(annotations=_RO)
    def generate_mermaid_diagram(
        kind: str,
        target: str | None = None,
        direction: str = "both",
        depth: int = 4,
        max_nodes: int = 60,
        max_edges: int = 150,
    ) -> dict[str, Any]:
        """Generate a bounded Mermaid diagram and save it under output/.

        Args:
            kind: One of ``repo_overview``, ``module_deps``, ``call_graph``,
                ``neighborhood``, ``cycles``, ``data_flow``,
                ``c4_component``, ``pipeline``, ``sequence``.
            target: A node id, path, or qualified name (required for
                ``module_deps``/``call_graph``/``neighborhood``).
            direction: Direction hint (``"in"``/``"out"``/``"both"`` or
                ``"callers"``/``"callees"`` for ``call_graph``).
            depth: Maximum BFS hop count.
            max_nodes: Maximum nodes rendered (capped at 500).
            max_edges: Maximum edges rendered (capped at 1500).
        """
        with _open_ro(settings) as store:
            return _run_tool(
                impl.generate_mermaid_diagram,
                store,
                settings,
                kind,
                target,
                direction,
                depth,
                max_nodes,
                max_edges,
            )

    @mcp.tool(annotations=_RO)
    def list_proof_solver_benchmark_links(scope: str | None = None) -> dict[str, Any]:
        """List detected theorem/proof declarations and their containing files.

        Args:
            scope: Optional repository-relative path prefix restriction.
        """
        with _open_ro(settings) as store:
            return _run_tool(impl.list_proof_solver_benchmark_links, store, scope)

    @mcp.tool(annotations=_RO)
    def query_runtime_summary(time_range: str | None = None) -> dict[str, Any]:
        """Summarize ingested runtime telemetry (p50/p95/p99, error rates).

        Args:
            time_range: Informational only in this version (e.g.
                ``"24h"``); all ingested spans are summarized.
        """
        with _open_ro(settings) as store:
            return _run_tool(impl.query_runtime_summary, store, settings, time_range)

    @mcp.tool(annotations=_RO)
    def get_slowest_operations(metric: str = "p95", limit: int = 20) -> dict[str, Any]:
        """Report the slowest ingested operations by p50/p95/p99 latency.

        Args:
            metric: One of ``"p50"``, ``"p95"``, ``"p99"``.
            limit: Maximum results.
        """
        with _open_ro(settings) as store:
            return _run_tool(impl.get_slowest_operations, store, metric, limit)

    @mcp.tool(annotations=_RO)
    def get_trace_or_flow(trace_id_or_operation: str) -> dict[str, Any]:
        """Return spans for a trace id or operation name, plus a sequence diagram.

        Args:
            trace_id_or_operation: A trace id (exact match) or operation
                name.
        """
        with _open_ro(settings) as store:
            return _run_tool(impl.get_trace_or_flow, store, trace_id_or_operation)

    @mcp.tool(annotations=_RO)
    def explain_graph_evidence(node_or_edge_id: str) -> dict[str, Any]:
        """Explain why a node/edge exists: its stored evidence, confidence, provenance.

        Args:
            node_or_edge_id: A node id, or an edge key
                ``"<src_id>|<edge_type>|<dst_id>"``.
        """
        with _open_ro(settings) as store:
            return _run_tool(impl.explain_graph_evidence, store, node_or_edge_id)

    return mcp


def main() -> None:
    """Entry point used by ``cli.py serve-mcp``: build and run over stdio."""
    server = build_server()
    server.run(transport="stdio")


if __name__ == "__main__":
    main()
