"""Cycle detection, centrality, impact analysis, and dead-code heuristic tests."""

from __future__ import annotations

from ci_analytics import metrics
from ci_analytics.graph_view import build_graph_view
from ci_graph.store import GraphStore


def test_find_cycles_detects_the_fixture_cycle(indexed_store: GraphStore) -> None:
    view = build_graph_view(indexed_store)
    cycles = metrics.find_cycles(view)
    assert ["python:py_pkg/a.py", "python:py_pkg/b.py"] in cycles


def test_pagerank_returns_nonempty_ranked_results(indexed_store: GraphStore) -> None:
    view = build_graph_view(indexed_store)
    ranked = metrics.pagerank(view, limit=5)
    assert ranked
    scores = [r.score for r in ranked]
    assert scores == sorted(scores, reverse=True)


def test_top_fan_in_is_deterministically_ordered(indexed_store: GraphStore) -> None:
    view = build_graph_view(indexed_store)
    ranked_a = metrics.top_fan_in(view, limit=10)
    ranked_b = metrics.top_fan_in(view, limit=10)
    assert [r.node_id for r in ranked_a] == [r.node_id for r in ranked_b]


def test_dead_code_candidate_flags_orphan_function(indexed_store: GraphStore) -> None:
    view = build_graph_view(indexed_store)
    candidates = metrics.dead_code_candidates(view, limit=100)
    ids = {c.node_id for c in candidates}
    assert "python:py_pkg/b.py::unused_orphan" in ids
    assert all(c.heuristic is True for c in candidates)


def test_dead_code_excludes_called_function(indexed_store: GraphStore) -> None:
    view = build_graph_view(indexed_store)
    candidates = metrics.dead_code_candidates(view, limit=100)
    ids = {c.node_id for c in candidates}
    # `bar` is called from `foo` via a CALLS edge; must not be flagged.
    assert "python:py_pkg/b.py::bar" not in ids


def test_impact_analysis_finds_dependents(indexed_store: GraphStore) -> None:
    view = build_graph_view(indexed_store)
    impacted = metrics.impact_analysis(view, "python:py_pkg/a.py", depth=2)
    assert "python:py_pkg/b.py" in impacted


def test_shortest_dependency_path_between_functions(indexed_store: GraphStore) -> None:
    view = build_graph_view(indexed_store)
    path = metrics.shortest_dependency_path(
        view, "python:py_pkg/a.py::foo", "python:py_pkg/b.py::bar"
    )
    assert path == ["python:py_pkg/a.py::foo", "python:py_pkg/b.py::bar"]


def test_shortest_dependency_path_returns_none_when_unreachable(
    indexed_store: GraphStore,
) -> None:
    view = build_graph_view(indexed_store)
    path = metrics.shortest_dependency_path(
        view, "python:py_pkg/b.py::unused_orphan", "python:py_pkg/a.py::foo"
    )
    assert path is None


def test_articulation_points_returns_sorted_list(indexed_store: GraphStore) -> None:
    view = build_graph_view(indexed_store)
    points = metrics.articulation_points(view)
    assert points == sorted(points)


def test_boundary_violations_empty_by_default(indexed_store: GraphStore) -> None:
    view = build_graph_view(indexed_store)
    assert metrics.check_boundary_violations(view, ()) == []


def test_boundary_violations_detects_configured_forbidden_direction(
    indexed_store: GraphStore,
) -> None:
    view = build_graph_view(indexed_store)
    # b.py importing a.py is real (the fixture's deliberate cycle); a rule
    # forbidding py_pkg -> py_pkg self-imports should catch both directions.
    violations = metrics.check_boundary_violations(view, (("py_pkg", "py_pkg"),))
    pairs = {(v.src_id, v.dst_id) for v in violations}
    assert ("python:py_pkg/a.py", "python:py_pkg/b.py") in pairs
    assert ("python:py_pkg/b.py", "python:py_pkg/a.py") in pairs
    assert all(v.rule == ("py_pkg", "py_pkg") for v in violations)
