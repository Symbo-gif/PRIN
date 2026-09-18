"""Graph analytics: fan-in/out, centrality, cycles, paths, and heuristics.

Every function here documents, in its return shape, whether a result is a
proven structural fact (e.g. "this edge exists in the parsed graph") or an
inferred heuristic (e.g. "this function looks unused"); callers (the CLI and
the MCP server) surface that distinction rather than collapsing it.
"""

from __future__ import annotations

from dataclasses import dataclass, field

import networkx as nx

from ci_analytics.graph_view import GraphView

#: Edge types treated as "dependency" edges for cycle/impact/path analytics
#: by default. Callers may override.
DEFAULT_DEPENDENCY_EDGE_TYPES = ("IMPORTS", "DEPENDS_ON", "CALLS", "REFERENCES")

_ENTRY_POINT_SIMPLE_NAMES = frozenset({"main", "__main__", "run", "cli"})
_DUNDER_PREFIX_SUFFIX = "__"


@dataclass
class FanCount:
    """Inbound/outbound edge count for one node.

    Attributes:
        node_id: The node.
        label: Human-readable label.
        count: Number of matching edges.
    """

    node_id: str
    label: str
    count: int


@dataclass
class CentralityScore:
    """A centrality score for one node.

    Attributes:
        node_id: The node.
        label: Human-readable label.
        score: The metric's raw value (e.g. PageRank probability mass).
    """

    node_id: str
    label: str
    score: float


@dataclass
class DeadCodeCandidate:
    """A heuristic dead-code candidate.

    Attributes:
        node_id: The node.
        label: Human-readable label.
        reason: Why it was flagged.
        heuristic: Always ``True`` — never a proof of dead code.
    """

    node_id: str
    label: str
    reason: str
    heuristic: bool = field(default=True, init=False)


def restrict_edges(
    view: GraphView, edge_types: tuple[str, ...] | list[str] | None
) -> nx.MultiDiGraph:
    """Return the graph restricted to the given edge types (public helper).

    Args:
        view: The graph view.
        edge_types: Edge types to keep, or ``None`` for the full graph.

    Returns:
        The full graph if ``edge_types`` is ``None``, else a filtered
        ``MultiDiGraph`` (see
        :func:`ci_analytics.graph_view.subgraph_by_edge_types`).
    """
    if edge_types is None:
        return view.digraph
    from ci_analytics.graph_view import subgraph_by_edge_types

    return subgraph_by_edge_types(view, list(edge_types))


# Backward-compatible private alias used internally within this module.
_restricted = restrict_edges


def fan_in(view: GraphView, node_id: str, edge_types: list[str] | None = None) -> int:
    """Count inbound edges to a node.

    Args:
        view: The graph view.
        node_id: Target node id.
        edge_types: Optional restriction to these edge types.

    Returns:
        Inbound edge count (0 if the node is absent).
    """
    graph = _restricted(view, edge_types)
    return graph.in_degree(node_id) if node_id in graph else 0


def fan_out(view: GraphView, node_id: str, edge_types: list[str] | None = None) -> int:
    """Count outbound edges from a node.

    Args:
        view: The graph view.
        node_id: Source node id.
        edge_types: Optional restriction to these edge types.

    Returns:
        Outbound edge count (0 if the node is absent).
    """
    graph = _restricted(view, edge_types)
    return graph.out_degree(node_id) if node_id in graph else 0


def top_fan_in(
    view: GraphView, edge_types: list[str] | None = None, limit: int = 20
) -> list[FanCount]:
    """Return the nodes with the highest inbound edge count.

    Args:
        view: The graph view.
        edge_types: Optional restriction to these edge types.
        limit: Maximum results.

    Returns:
        Nodes sorted by descending fan-in, ties broken by node id for
        determinism.
    """
    graph = _restricted(view, edge_types)
    scored = [
        FanCount(
            nid, view.nodes_by_id[nid].label if nid in view.nodes_by_id else nid, d
        )
        for nid, d in graph.in_degree()
    ]
    scored.sort(key=lambda item: (-item.count, item.node_id))
    return scored[: max(1, limit)]


def top_fan_out(
    view: GraphView, edge_types: list[str] | None = None, limit: int = 20
) -> list[FanCount]:
    """Return the nodes with the highest outbound edge count.

    Args:
        view: The graph view.
        edge_types: Optional restriction to these edge types.
        limit: Maximum results.

    Returns:
        Nodes sorted by descending fan-out, ties broken by node id.
    """
    graph = _restricted(view, edge_types)
    scored = [
        FanCount(
            nid, view.nodes_by_id[nid].label if nid in view.nodes_by_id else nid, d
        )
        for nid, d in graph.out_degree()
    ]
    scored.sort(key=lambda item: (-item.count, item.node_id))
    return scored[: max(1, limit)]


def pagerank(
    view: GraphView, edge_types: list[str] | None = None, limit: int = 20
) -> list[CentralityScore]:
    """Compute PageRank centrality over the (restricted) dependency graph.

    Args:
        view: The graph view.
        edge_types: Optional restriction; defaults to
            :data:`DEFAULT_DEPENDENCY_EDGE_TYPES`.
        limit: Maximum results.

    Returns:
        Nodes sorted by descending PageRank score. Returns an empty list if
        the restricted graph has no edges (PageRank is undefined/trivial on
        an empty graph).
    """
    graph = _restricted(view, edge_types or list(DEFAULT_DEPENDENCY_EDGE_TYPES))
    if graph.number_of_edges() == 0:
        return []
    simple = nx.DiGraph(graph)
    scores = nx.pagerank(simple)
    ranked = [
        CentralityScore(
            nid, view.nodes_by_id[nid].label if nid in view.nodes_by_id else nid, s
        )
        for nid, s in scores.items()
    ]
    ranked.sort(key=lambda item: (-item.score, item.node_id))
    return ranked[: max(1, limit)]


def find_cycles(
    view: GraphView, edge_types: list[str] | None = None
) -> list[list[str]]:
    """Find circular-dependency groups via strongly connected components.

    Args:
        view: The graph view.
        edge_types: Optional restriction; defaults to
            :data:`DEFAULT_DEPENDENCY_EDGE_TYPES`.

    Returns:
        A list of cycles, each a sorted list of node ids belonging to one
        non-trivial strongly connected component (size > 1), sorted by
        component size then lexicographically for determinism. A
        self-loop (a node importing/calling itself) is also reported as a
        one-element cycle.
    """
    graph = _restricted(view, edge_types or list(DEFAULT_DEPENDENCY_EDGE_TYPES))
    simple = nx.DiGraph(graph)
    cycles = [
        sorted(comp)
        for comp in nx.strongly_connected_components(simple)
        if len(comp) > 1
    ]
    self_loops = sorted({n for n in simple.nodes if simple.has_edge(n, n)})
    cycles.extend([n] for n in self_loops)
    cycles.sort(key=lambda c: (-len(c), c))
    return cycles


def articulation_points(
    view: GraphView, edge_types: list[str] | None = None
) -> list[str]:
    """Find fragile bridge components via articulation points.

    Args:
        view: The graph view.
        edge_types: Optional restriction; defaults to
            :data:`DEFAULT_DEPENDENCY_EDGE_TYPES`.

    Returns:
        Node ids whose removal (on the undirected projection of the
        restricted graph) would disconnect part of the graph, sorted for
        determinism.
    """
    graph = _restricted(view, edge_types or list(DEFAULT_DEPENDENCY_EDGE_TYPES))
    undirected = nx.Graph(graph)
    return sorted(nx.articulation_points(undirected))


def shortest_dependency_path(
    view: GraphView,
    source: str,
    target: str,
    edge_types: list[str] | None = None,
) -> list[str] | None:
    """Find the shortest path between two nodes.

    Args:
        view: The graph view.
        source: Source node id.
        target: Target node id.
        edge_types: Optional restriction; defaults to
            :data:`DEFAULT_DEPENDENCY_EDGE_TYPES`.

    Returns:
        The path as a list of node ids (inclusive of endpoints), or
        ``None`` if no path exists or either endpoint is absent.
    """
    graph = _restricted(view, edge_types or list(DEFAULT_DEPENDENCY_EDGE_TYPES))
    if source not in graph or target not in graph:
        return None
    try:
        path: list[str] = nx.shortest_path(graph, source, target)
    except nx.NetworkXNoPath:
        return None
    return path


def impact_analysis(
    view: GraphView,
    target: str,
    depth: int = 3,
    edge_types: list[str] | None = None,
) -> dict[str, int]:
    """Find nodes that may be affected if ``target`` changes.

    Walks edges in reverse (i.e. finds nodes that depend on ``target``,
    directly or transitively) up to ``depth`` hops.

    Args:
        view: The graph view.
        target: The node id whose change impact is being assessed.
        depth: Maximum hop count.
        edge_types: Optional restriction; defaults to
            :data:`DEFAULT_DEPENDENCY_EDGE_TYPES`.

    Returns:
        Mapping of affected node id to its hop distance from ``target``
        (``target`` itself is not included). Empty if ``target`` is absent
        or nothing depends on it.
    """
    graph = _restricted(view, edge_types or list(DEFAULT_DEPENDENCY_EDGE_TYPES))
    if target not in graph:
        return {}
    reversed_graph = graph.reverse(copy=False)
    distances: dict[str, int] = {}
    frontier = {target}
    for hop in range(1, max(1, depth) + 1):
        next_frontier: set[str] = set()
        for node in frontier:
            for neighbor in reversed_graph.successors(node):
                if neighbor not in distances and neighbor != target:
                    distances[neighbor] = hop
                    next_frontier.add(neighbor)
        if not next_frontier:
            break
        frontier = next_frontier
    return distances


@dataclass
class BoundaryViolation:
    """One import that crosses a configured forbidden architecture boundary.

    Attributes:
        src_id: The importing node id.
        dst_id: The imported node id.
        rule: The ``(from_prefix, to_prefix)`` rule this edge violated.
        confidence: The underlying edge's confidence.
        provenance: The underlying edge's provenance.
    """

    src_id: str
    dst_id: str
    rule: tuple[str, str]
    confidence: float
    provenance: str


def check_boundary_violations(
    view: GraphView, rules: tuple[tuple[str, str], ...]
) -> list[BoundaryViolation]:
    """Find ``IMPORTS``/``DEPENDS_ON`` edges that cross a forbidden boundary.

    Args:
        view: The graph view.
        rules: ``(from_prefix, to_prefix)`` repository-relative path-prefix
            pairs; see ``ci_config.ARCHITECTURE_BOUNDARY_RULES``. Empty by
            default — no rule fires unless a maintainer configures one.

    Returns:
        Every matching edge, sorted by ``(src_id, dst_id)`` for
        determinism. Empty if ``rules`` is empty.
    """
    if not rules:
        return []
    graph = restrict_edges(view, ["IMPORTS", "DEPENDS_ON"])
    violations: list[BoundaryViolation] = []
    for u, v, data in graph.edges(data=True):
        src_path = view.nodes_by_id[u].repo_path if u in view.nodes_by_id else None
        dst_path = view.nodes_by_id[v].repo_path if v in view.nodes_by_id else None
        if not src_path or not dst_path:
            continue
        for from_prefix, to_prefix in rules:
            if src_path.startswith(from_prefix) and dst_path.startswith(to_prefix):
                violations.append(
                    BoundaryViolation(
                        src_id=u,
                        dst_id=v,
                        rule=(from_prefix, to_prefix),
                        confidence=data["confidence"],
                        provenance=data["provenance"],
                    )
                )
    violations.sort(key=lambda item: (item.src_id, item.dst_id))
    return violations


def dead_code_candidates(view: GraphView, limit: int = 50) -> list[DeadCodeCandidate]:
    """Heuristically flag functions/methods/classes with no inbound reference.

    A node is flagged only if it is a function, method, or class; has zero
    inbound ``CALLS``/``REFERENCES``/``IMPORTS`` edges; is not a test; and
    its simple name is not a common entry-point name (``main``, ``run``,
    ``cli``) or a dunder method. This is a **heuristic candidate list**,
    never a proof of dead code: static analysis cannot see dynamic
    dispatch, reflection, string-based lookups, or external callers outside
    the indexed repository.

    Args:
        view: The graph view.
        limit: Maximum results.

    Returns:
        Candidates sorted by node id for determinism.
    """
    candidates: list[DeadCodeCandidate] = []
    graph = view.digraph
    for node_id, node in view.nodes_by_id.items():
        if node.node_type not in ("function", "method", "class"):
            continue
        if node.node_type == "class" and _looks_like_trait_or_interface(node):
            continue
        simple_name = (node.qualified_name or node.label).rsplit(".", 1)[-1]
        if simple_name in _ENTRY_POINT_SIMPLE_NAMES:
            continue
        if simple_name.startswith(_DUNDER_PREFIX_SUFFIX) and simple_name.endswith(
            _DUNDER_PREFIX_SUFFIX
        ):
            continue
        inbound = [
            d["edge_type"]
            for _, _, d in graph.in_edges(node_id, data=True)
            if d["edge_type"] in ("CALLS", "REFERENCES", "IMPORTS")
        ]
        if inbound:
            continue
        candidates.append(
            DeadCodeCandidate(
                node_id=node_id,
                label=node.label,
                reason=(
                    "no inbound CALLS/REFERENCES/IMPORTS edge found anywhere "
                    "in the indexed repository"
                ),
            )
        )
        if len(candidates) >= limit:
            break
    return candidates


def _looks_like_trait_or_interface(node: object) -> bool:
    attrs = getattr(node, "attributes", {}) or {}
    return attrs.get("rust_kind") in ("trait",)
