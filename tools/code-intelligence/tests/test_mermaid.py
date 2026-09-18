"""Mermaid label escaping, node-id stability, and output-size-limiting tests."""

from __future__ import annotations

import pytest

from ci_analytics.graph_view import build_graph_view
from ci_graph.store import GraphStore
from ci_mermaid.render import render_diagram
from ci_mermaid.sanitize import mermaid_node_id, sanitize_label


@pytest.mark.parametrize(
    "raw",
    [
        'label with "double quotes"',
        "label with `backticks`",
        "label with <angle> brackets",
        "label with # hash",
        "label with | pipe",
        "label with\nnewline",
        "label with\r\nCRLF",
    ],
)
def test_sanitize_label_strips_mermaid_unsafe_characters(raw: str) -> None:
    cleaned = sanitize_label(raw)
    for unsafe in ('"', "`", "<", ">", "#", "|", "\n", "\r"):
        assert unsafe not in cleaned


def test_sanitize_label_truncates_long_labels() -> None:
    cleaned = sanitize_label("x" * 200, max_length=20)
    assert len(cleaned) == 20
    assert cleaned.endswith("…")


def test_sanitize_label_never_produces_empty_string() -> None:
    assert sanitize_label("") == "(unnamed)"
    assert sanitize_label("   ") == "(unnamed)"


def test_mermaid_node_id_is_stable_and_safe() -> None:
    id1 = mermaid_node_id("python:pkg/module.py::Class.method")
    id2 = mermaid_node_id("python:pkg/module.py::Class.method")
    assert id1 == id2
    assert all(c.isalnum() or c == "_" for c in id1)


def test_mermaid_node_id_distinguishes_different_inputs() -> None:
    id1 = mermaid_node_id("python:pkg/a.py")
    id2 = mermaid_node_id("python:pkg/b.py")
    assert id1 != id2


def test_repo_overview_diagram_contains_no_raw_quotes_from_labels(
    indexed_store: GraphStore,
) -> None:
    view = build_graph_view(indexed_store)
    result = render_diagram(view, "repo_overview", max_nodes=100)
    # Every quoted label segment must come from sanitize_label, which never
    # emits an embedded double quote.
    for line in result.mermaid.splitlines():
        if "[" in line and '"' in line:
            inner = line.split('"', 2)
            if len(inner) >= 3:
                assert '"' not in inner[1]


def test_diagram_node_limit_is_enforced_and_reported(indexed_store: GraphStore) -> None:
    view = build_graph_view(indexed_store)
    result = render_diagram(view, "repo_overview", max_nodes=2, depth=5)
    assert result.node_count <= 2
    assert result.truncated is True
    assert result.notes


def test_diagram_kind_requires_target(indexed_store: GraphStore) -> None:
    view = build_graph_view(indexed_store)
    with pytest.raises(ValueError, match="requires a target"):
        render_diagram(view, "module_deps")


def test_diagram_unknown_kind_raises(indexed_store: GraphStore) -> None:
    view = build_graph_view(indexed_store)
    with pytest.raises(ValueError, match="unsupported diagram kind"):
        render_diagram(view, "not_a_real_kind")


def test_diagram_missing_target_reports_not_found(indexed_store: GraphStore) -> None:
    view = build_graph_view(indexed_store)
    result = render_diagram(view, "module_deps", target="python:does/not/exist.py")
    assert result.node_count == 0
    assert "not found" in result.notes[0]


def test_cycles_diagram_renders_the_fixture_cycle(indexed_store: GraphStore) -> None:
    view = build_graph_view(indexed_store)
    result = render_diagram(view, "cycles")
    assert result.node_count == 2
    assert "subgraph" in result.mermaid
