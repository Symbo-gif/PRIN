"""Build an in-memory ``networkx`` view of the SQLite graph for analytics.

Analytics never mutate the SQLite store; they read the whole graph once per
call (or per cached view) and run ``networkx`` algorithms in memory. The
view is cached in-process, keyed by the current index run's
``index_version``, so repeated MCP tool calls against an unchanged index do
not re-read the database on every call.
"""

from __future__ import annotations

from dataclasses import dataclass

import networkx as nx

from ci_graph.store import EdgeRecord, GraphStore, NodeRecord


@dataclass
class GraphView:
    """An in-memory snapshot of the graph plus lookup tables.

    Attributes:
        digraph: A ``networkx.MultiDiGraph`` with one edge per
            ``(src, dst, edge_type)`` triple, edge data carrying
            ``edge_type``, ``confidence``, and ``provenance``.
        nodes_by_id: Node id -> :class:`~ci_graph.store.NodeRecord`.
        index_version: The index version this view was built from.
    """

    digraph: nx.MultiDiGraph
    nodes_by_id: dict[str, NodeRecord]
    index_version: str


_cache: GraphView | None = None


def build_graph_view(store: GraphStore) -> GraphView:
    """Build (or return the cached) in-memory graph view.

    Args:
        store: An open :class:`~ci_graph.store.GraphStore`.

    Returns:
        The current :class:`GraphView`, rebuilt only if the store's latest
        index run has a different ``index_version`` than the cached view.
    """
    global _cache
    latest = store.latest_run()
    version = latest["index_version"] if latest else "empty"
    if _cache is not None and _cache.index_version == version:
        return _cache

    nodes = store.all_nodes()
    edges = store.all_edges()
    digraph = nx.MultiDiGraph()
    nodes_by_id: dict[str, NodeRecord] = {}
    for node in nodes:
        nodes_by_id[node.node_id] = node
        digraph.add_node(node.node_id, node_type=node.node_type, label=node.label)
    for edge in edges:
        _add_edge(digraph, edge)

    view = GraphView(digraph=digraph, nodes_by_id=nodes_by_id, index_version=version)
    _cache = view
    return view


def invalidate_cache() -> None:
    """Drop the cached graph view (used after re-indexing)."""
    global _cache
    _cache = None


def _add_edge(digraph: nx.MultiDiGraph, edge: EdgeRecord) -> None:
    digraph.add_edge(
        edge.src_id,
        edge.dst_id,
        key=edge.edge_type,
        edge_type=edge.edge_type,
        confidence=edge.confidence,
        provenance=edge.provenance,
    )


def subgraph_by_edge_types(view: GraphView, edge_types: list[str]) -> nx.MultiDiGraph:
    """Return a view restricted to the given edge types.

    Args:
        view: The full graph view.
        edge_types: Edge types to keep.

    Returns:
        A new ``MultiDiGraph`` containing only matching edges (and the
        nodes they touch).
    """
    allowed = set(edge_types)
    sub = nx.MultiDiGraph()
    for u, v, data in view.digraph.edges(data=True):
        if data["edge_type"] in allowed:
            sub.add_node(u, **view.digraph.nodes[u])
            sub.add_node(v, **view.digraph.nodes[v])
            sub.add_edge(u, v, **data)
    return sub
