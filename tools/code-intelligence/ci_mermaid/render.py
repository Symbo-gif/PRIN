"""Bounded, deterministic Mermaid diagram generation.

Every generator here enforces the same three limits (max nodes, max edges,
max depth), orders nodes/edges deterministically (sorted by graph node id),
and reports an explicit omission summary when a limit truncates the result,
so "the diagram looks complete but silently isn't" can never happen.
"""

from __future__ import annotations

from collections import deque
from dataclasses import dataclass, field
from typing import Any

import networkx as nx

from ci_analytics import metrics
from ci_analytics.graph_view import GraphView, subgraph_by_edge_types
from ci_config import DEFAULT_MAX_DEPTH, DEFAULT_MAX_EDGES, DEFAULT_MAX_NODES
from ci_mermaid.sanitize import (
    mermaid_node_id,
    sanitize_label,
    sanitize_subgraph_title,
)

SUPPORTED_KINDS = (
    "repo_overview",
    "module_deps",
    "call_graph",
    "neighborhood",
    "cycles",
    "data_flow",
    "c4_component",
    "pipeline",
    "sequence",
)

_LOW_CONFIDENCE_THRESHOLD = 0.7


@dataclass
class MermaidResult:
    """The rendered diagram plus truncation/provenance metadata.

    Attributes:
        kind: The diagram kind requested.
        mermaid: The Mermaid diagram source text.
        node_count: Nodes actually rendered.
        edge_count: Edges actually rendered.
        truncated: True if any limit caused omissions.
        omitted_nodes: Nodes discovered but not rendered.
        omitted_edges: Edges discovered but not rendered.
        notes: Human-readable notes (e.g. "target not found").
    """

    kind: str
    mermaid: str
    node_count: int
    edge_count: int
    truncated: bool
    omitted_nodes: int = 0
    omitted_edges: int = 0
    notes: list[str] = field(default_factory=list)


def render_diagram(
    view: GraphView,
    kind: str,
    *,
    target: str | None = None,
    direction: str = "both",
    depth: int = DEFAULT_MAX_DEPTH,
    max_nodes: int = DEFAULT_MAX_NODES,
    max_edges: int = DEFAULT_MAX_EDGES,
) -> MermaidResult:
    """Render one of the supported diagram kinds.

    Args:
        view: The graph view to render from.
        kind: One of :data:`SUPPORTED_KINDS`.
        target: A node id required by ``module_deps``/``call_graph``/
            ``neighborhood``/``data_flow``/``pipeline`` (optional for the
            latter two, which fall back to a bounded global view).
        direction: ``"in"``, ``"out"``, or ``"both"`` — which edge
            direction(s) to follow from ``target``.
        depth: Maximum BFS hop count.
        max_nodes: Maximum nodes rendered.
        max_edges: Maximum edges rendered.

    Returns:
        The rendered diagram.

    Raises:
        ValueError: If ``kind`` is unsupported, or a required ``target`` is
            missing/absent from the graph.
    """
    if kind not in SUPPORTED_KINDS:
        msg = f"unsupported diagram kind {kind!r}; supported: {SUPPORTED_KINDS}"
        raise ValueError(msg)
    depth = max(1, min(depth, 12))
    max_nodes = max(1, min(max_nodes, 500))
    max_edges = max(1, min(max_edges, 1500))

    if kind == "repo_overview":
        return _render_repo_overview(view, depth, max_nodes, max_edges)
    if kind == "module_deps":
        resolved_target = _require_target(target, kind)
        return _render_neighborhood(
            view,
            "module_deps",
            resolved_target,
            ["IMPORTS"],
            direction,
            depth,
            max_nodes,
            max_edges,
        )
    if kind == "call_graph":
        resolved_target = _require_target(target, kind)
        call_direction = {"callers": "in", "callees": "out"}.get(direction, direction)
        return _render_neighborhood(
            view,
            "call_graph",
            resolved_target,
            ["CALLS"],
            call_direction,
            depth,
            max_nodes,
            max_edges,
        )
    if kind == "neighborhood":
        resolved_target = _require_target(target, kind)
        return _render_neighborhood(
            view,
            "neighborhood",
            resolved_target,
            None,
            direction,
            depth,
            max_nodes,
            max_edges,
        )
    if kind == "data_flow":
        edge_types = ["PRODUCES", "CONSUMES", "EMITS"]
        if target:
            return _render_neighborhood(
                view,
                "data_flow",
                target,
                edge_types,
                direction,
                depth,
                max_nodes,
                max_edges,
            )
        return _render_bounded_global(
            view, "data_flow", edge_types, max_nodes, max_edges
        )
    if kind == "pipeline":
        edge_types = ["INVOKES", "PROVES", "VALIDATES", "PRODUCES"]
        if target:
            return _render_neighborhood(
                view,
                "pipeline",
                target,
                edge_types,
                direction,
                depth,
                max_nodes,
                max_edges,
            )
        return _render_bounded_global(
            view, "pipeline", edge_types, max_nodes, max_edges
        )
    if kind == "cycles":
        return _render_cycles(view, max_nodes, max_edges)
    if kind == "c4_component":
        return _render_c4_component(view, max_nodes, max_edges)
    msg = f"kind {kind!r} requires ci_mermaid.render.render_sequence_from_spans"
    raise ValueError(msg)


def _require_target(target: str | None, kind: str) -> str:
    if not target:
        msg = f"diagram kind {kind!r} requires a target node id"
        raise ValueError(msg)
    return target


def bfs_bounded(
    graph: nx.MultiDiGraph,
    seed: str,
    direction: str,
    depth: int,
    max_nodes: int,
) -> tuple[set[str], bool]:
    """Breadth-first search from ``seed``, bounded by depth and node count.

    Args:
        graph: The graph to search.
        seed: The starting node id.
        direction: ``"out"`` (successors only), ``"in"`` (predecessors
            only), or ``"both"``.
        depth: Maximum hop count from ``seed``.
        max_nodes: Maximum total nodes to visit, including ``seed``.

    Returns:
        A tuple of (visited node ids including ``seed``, whether the node
        limit truncated the search before it would have naturally ended).
    """
    visited = {seed}
    frontier = deque([(seed, 0)])
    truncated = False
    while frontier:
        node, dist = frontier.popleft()
        if dist >= depth:
            continue
        neighbors: list[str] = []
        if direction in ("out", "both") and node in graph:
            neighbors.extend(sorted(graph.successors(node)))
        if direction in ("in", "both") and node in graph:
            neighbors.extend(sorted(graph.predecessors(node)))
        for nb in neighbors:
            if nb in visited:
                continue
            if len(visited) >= max_nodes:
                truncated = True
                continue
            visited.add(nb)
            frontier.append((nb, dist + 1))
    return visited, truncated


def _collect_edges(
    graph: nx.MultiDiGraph, nodes: set[str], max_edges: int
) -> tuple[list[tuple[str, str, dict[str, Any]]], bool]:
    edges = sorted(
        (
            (u, v, data)
            for u, v, data in graph.edges(data=True)
            if u in nodes and v in nodes
        ),
        key=lambda e: (e[0], e[1], e[2]["edge_type"]),
    )
    truncated = len(edges) > max_edges
    return edges[:max_edges], truncated


def _render_neighborhood(
    view: GraphView,
    kind: str,
    target: str,
    edge_types: list[str] | None,
    direction: str,
    depth: int,
    max_nodes: int,
    max_edges: int,
) -> MermaidResult:
    if target not in view.digraph:
        return MermaidResult(
            kind=kind,
            mermaid=(
                f'flowchart LR\n  missing["target not found: '
                f'{sanitize_label(target)}"]\n'
            ),
            node_count=0,
            edge_count=0,
            truncated=False,
            notes=[f"target node id {target!r} was not found in the current index"],
        )
    graph = _restricted(view, edge_types)
    nodes, node_truncated = bfs_bounded(graph, target, direction, depth, max_nodes)
    edges, edge_truncated = _collect_edges(graph, nodes, max_edges)
    mermaid = _emit_flowchart(view, nodes, edges, highlight={target})
    total_reachable = len(
        bfs_bounded(graph, target, direction, depth, max_nodes=10_000)[0]
    )
    return MermaidResult(
        kind=kind,
        mermaid=mermaid,
        node_count=len(nodes),
        edge_count=len(edges),
        truncated=node_truncated or edge_truncated,
        omitted_nodes=max(0, total_reachable - len(nodes)),
        omitted_edges=0,
        notes=_truncation_notes(node_truncated, edge_truncated, max_nodes, max_edges),
    )


def _render_bounded_global(
    view: GraphView,
    kind: str,
    edge_types: list[str],
    max_nodes: int,
    max_edges: int,
) -> MermaidResult:
    graph = _restricted(view, edge_types)
    all_nodes = sorted(graph.nodes)
    truncated = len(all_nodes) > max_nodes
    nodes = set(all_nodes[:max_nodes])
    edges, edge_truncated = _collect_edges(graph, nodes, max_edges)
    mermaid = _emit_flowchart(view, nodes, edges)
    return MermaidResult(
        kind=kind,
        mermaid=mermaid,
        node_count=len(nodes),
        edge_count=len(edges),
        truncated=truncated or edge_truncated,
        omitted_nodes=max(0, len(all_nodes) - len(nodes)),
        notes=_truncation_notes(truncated, edge_truncated, max_nodes, max_edges),
    )


def _render_repo_overview(
    view: GraphView, depth: int, max_nodes: int, max_edges: int
) -> MermaidResult:
    graph = _restricted(view, ["CONTAINS"])
    dir_nodes = {
        nid for nid, n in view.nodes_by_id.items() if n.node_type == "directory"
    }
    sub = graph.subgraph(dir_nodes)
    root = "dir:."
    if root not in sub:
        return MermaidResult(
            kind="repo_overview",
            mermaid='flowchart TD\n  empty["no directories indexed"]\n',
            node_count=0,
            edge_count=0,
            truncated=False,
        )
    nodes, node_truncated = bfs_bounded(sub, root, "out", depth, max_nodes)
    edges, edge_truncated = _collect_edges(sub, nodes, max_edges)
    mermaid = _emit_flowchart(view, nodes, edges, direction="TD")
    return MermaidResult(
        kind="repo_overview",
        mermaid=mermaid,
        node_count=len(nodes),
        edge_count=len(edges),
        truncated=node_truncated or edge_truncated,
        notes=_truncation_notes(node_truncated, edge_truncated, max_nodes, max_edges),
    )


def _render_cycles(view: GraphView, max_nodes: int, max_edges: int) -> MermaidResult:
    cycles = metrics.find_cycles(view)
    if not cycles:
        return MermaidResult(
            kind="cycles",
            mermaid='flowchart LR\n  none["no circular dependencies detected"]\n',
            node_count=0,
            edge_count=0,
            truncated=False,
            notes=[
                "static analysis found zero strongly-connected components of size > 1"
            ],
        )
    graph = _restricted(view, list(metrics.DEFAULT_DEPENDENCY_EDGE_TYPES))
    all_nodes: set[str] = set()
    omitted_cycles = 0
    lines = ["flowchart LR"]
    rendered_nodes: set[str] = set()
    rendered_edges: list[tuple[str, str, dict[str, Any]]] = []
    for i, cycle in enumerate(cycles):
        if len(rendered_nodes) + len(cycle) > max_nodes:
            omitted_cycles += 1
            continue
        title = sanitize_subgraph_title(f"cycle {i + 1} ({len(cycle)} nodes)")
        lines.append(f'  subgraph cyc{i} ["{title}"]')
        for nid in cycle:
            lines.append(f"    {_node_line(view, nid)}")
            rendered_nodes.add(nid)
        lines.append("  end")
        cyc_edges, _ = _collect_edges(graph, set(cycle), max_edges)
        rendered_edges.extend(cyc_edges)
        all_nodes.update(cycle)
    edges_capped = rendered_edges[:max_edges]
    for u, v, data in edges_capped:
        lines.append(_edge_line(u, v, data))
    mermaid = "\n".join(lines) + "\n"
    notes = []
    if omitted_cycles:
        notes.append(
            f"omitted {omitted_cycles} additional cycle(s) to stay within max_nodes"
        )
    return MermaidResult(
        kind="cycles",
        mermaid=mermaid,
        node_count=len(rendered_nodes),
        edge_count=len(edges_capped),
        truncated=bool(omitted_cycles) or len(rendered_edges) > max_edges,
        omitted_nodes=len(all_nodes) - len(rendered_nodes),
        omitted_edges=max(0, len(rendered_edges) - len(edges_capped)),
        notes=notes,
    )


def _render_c4_component(
    view: GraphView, max_nodes: int, max_edges: int
) -> MermaidResult:
    def component_of(repo_path: str | None) -> str | None:
        if not repo_path:
            return None
        parts = repo_path.split("/")
        return "/".join(parts[:2]) if len(parts) > 1 else parts[0]

    graph = _restricted(view, ["IMPORTS", "DEPENDS_ON", "CALLS"])
    component_edges: dict[tuple[str, str], int] = {}
    components: set[str] = set()
    for u, v, _data in graph.edges(data=True):
        cu = (
            component_of(view.nodes_by_id[u].repo_path)
            if u in view.nodes_by_id
            else None
        )
        cv = (
            component_of(view.nodes_by_id[v].repo_path)
            if v in view.nodes_by_id
            else None
        )
        if not cu or not cv or cu == cv:
            continue
        components.add(cu)
        components.add(cv)
        key = (cu, cv)
        component_edges[key] = component_edges.get(key, 0) + 1

    ordered_components = sorted(components)[:max_nodes]
    truncated = len(components) > len(ordered_components)
    kept = set(ordered_components)
    ordered_edges = sorted(
        ((u, v, c) for (u, v), c in component_edges.items() if u in kept and v in kept)
    )[:max_edges]

    lines = ["flowchart LR"]
    for comp in ordered_components:
        cid = mermaid_node_id(f"component:{comp}")
        lines.append(f'  {cid}["{sanitize_label(comp)}"]')
    for u, v, count in ordered_edges:
        uid, vid = mermaid_node_id(f"component:{u}"), mermaid_node_id(f"component:{v}")
        lines.append(f'  {uid} -->|"{count} ref(s)"| {vid}')
    mermaid = "\n".join(lines) + "\n"
    return MermaidResult(
        kind="c4_component",
        mermaid=mermaid,
        node_count=len(ordered_components),
        edge_count=len(ordered_edges),
        truncated=truncated or len(component_edges) > len(ordered_edges),
        omitted_nodes=len(components) - len(ordered_components),
        notes=(
            [
                "component = top two path segments; "
                "edge weight = aggregated reference count"
            ]
        ),
    )


def render_sequence_from_spans(
    spans: list[dict[str, Any]], max_nodes: int = DEFAULT_MAX_NODES
) -> MermaidResult:
    """Render a Mermaid sequence diagram from ingested runtime spans.

    Args:
        spans: Span dict rows (as returned by ``GraphStore.trace``), each
            with ``operation_name``, ``start_utc``, ``duration_ms``,
            ``status``.
        max_nodes: Maximum number of spans rendered as sequence steps.

    Returns:
        The rendered sequence diagram, grouped into one "participant" per
        distinct operation name.
    """
    ordered = sorted(spans, key=lambda s: s["start_utc"])
    truncated = len(ordered) > max_nodes
    ordered = ordered[:max_nodes]
    participants = sorted({s["operation_name"] for s in ordered})
    lines = ["sequenceDiagram"]
    for p in participants:
        lines.append(f"  participant {mermaid_node_id(p)} as {sanitize_label(p)}")
    prev = "caller"
    caller_id = mermaid_node_id("caller")
    lines.insert(1, f"  participant {caller_id} as {sanitize_label('caller')}")
    for span in ordered:
        pid = mermaid_node_id(span["operation_name"])
        status = span["status"]
        arrow = "->>" if status == "ok" else "-x"
        label = sanitize_label(
            f"{span['operation_name']} ({span['duration_ms']:.1f}ms, {status})"
        )
        lines.append(f"  {caller_id}{arrow}{pid}: {label}")
        prev = pid
    del prev
    mermaid = "\n".join(lines) + "\n"
    return MermaidResult(
        kind="sequence",
        mermaid=mermaid,
        node_count=len(participants),
        edge_count=len(ordered),
        truncated=truncated,
        omitted_edges=max(0, len(spans) - len(ordered)),
        notes=[
            "runtime evidence: rendered from ingested trace spans, not static analysis"
        ],
    )


def _restricted(view: GraphView, edge_types: list[str] | None) -> nx.MultiDiGraph:
    if edge_types is None:
        return view.digraph
    return subgraph_by_edge_types(view, edge_types)


def _node_line(view: GraphView, node_id: str, highlight: bool = False) -> str:
    node = view.nodes_by_id.get(node_id)
    label = sanitize_label(node.label if node else node_id)
    shape = "([" if highlight else "["
    close = "])" if highlight else "]"
    return f'{mermaid_node_id(node_id)}{shape}"{label}"{close}'


def _edge_line(u: str, v: str, data: dict[str, Any]) -> str:
    style = "-.->" if data["confidence"] < _LOW_CONFIDENCE_THRESHOLD else "-->"
    return f'  {mermaid_node_id(u)} {style}|"{data["edge_type"]}"| {mermaid_node_id(v)}'


def _emit_flowchart(
    view: GraphView,
    nodes: set[str],
    edges: list[tuple[str, str, dict[str, Any]]],
    *,
    highlight: set[str] | None = None,
    direction: str = "LR",
) -> str:
    highlight = highlight or set()
    lines = [f"flowchart {direction}"]
    for nid in sorted(nodes):
        lines.append(f"  {_node_line(view, nid, highlight=nid in highlight)}")
    for u, v, data in edges:
        lines.append(_edge_line(u, v, data))
    return "\n".join(lines) + "\n"


def _truncation_notes(
    node_truncated: bool, edge_truncated: bool, max_nodes: int, max_edges: int
) -> list[str]:
    notes = []
    if node_truncated:
        notes.append(
            f"node limit reached (max_nodes={max_nodes}); raise --max-nodes for more"
        )
    if edge_truncated:
        notes.append(
            f"edge limit reached (max_edges={max_edges}); raise --max-edges for more"
        )
    return notes
