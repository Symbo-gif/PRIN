"""MCP tool schema, read-only annotation, and no-secret-exposure tests."""

from __future__ import annotations

import asyncio
import json
from pathlib import Path
from typing import Any

import pytest

from ci_config import Settings
from ci_graph.store import GraphStore
from ci_mcp_server.server import build_server

_EXPECTED_TOOL_NAMES = {
    "index_repository",
    "get_index_status",
    "search_graph",
    "get_module_dependencies",
    "get_symbol_call_graph",
    "find_circular_dependencies",
    "get_hotspots",
    "get_impact_analysis",
    "find_dependency_path",
    "get_architecture_summary",
    "generate_mermaid_diagram",
    "list_proof_solver_benchmark_links",
    "query_runtime_summary",
    "get_slowest_operations",
    "get_trace_or_flow",
    "explain_graph_evidence",
}


def _call_tool_json(server: Any, name: str, args: dict[str, Any]) -> dict[str, Any]:
    """Call an MCP tool and return its JSON payload regardless of FastMCP's
    structured-vs-unstructured content shape for this SDK version."""
    result = asyncio.run(server.call_tool(name, args))
    if isinstance(result, tuple):
        _content, structured = result
        payload: dict[str, Any] = structured
        return payload
    parsed: dict[str, Any] = json.loads(result[0].text)
    return parsed


@pytest.fixture
def mcp_settings(tmp_path: Path, fixture_repo: Path) -> Settings:
    db_path = tmp_path / "graph.db"
    store = GraphStore(db_path)
    from ci_indexer.orchestrator import run_index

    run_index(store, fixture_repo, force=True)
    store.close()
    return Settings(
        repo_root=fixture_repo,
        db_path=db_path,
        output_dir=tmp_path / "output",
        telemetry_dir=tmp_path / "traces",
        telemetry_enabled=False,
    )


def test_all_expected_tools_are_registered(mcp_settings: Settings) -> None:
    server = build_server(mcp_settings)
    tools = asyncio.run(server.list_tools())
    names = {t.name for t in tools}
    assert names == _EXPECTED_TOOL_NAMES


def test_every_tool_except_index_is_marked_read_only(mcp_settings: Settings) -> None:
    server = build_server(mcp_settings)
    tools = asyncio.run(server.list_tools())
    for tool in tools:
        assert tool.annotations is not None
        if tool.name == "index_repository":
            assert tool.annotations.readOnlyHint is False
        else:
            assert tool.annotations.readOnlyHint is True
        assert tool.annotations.destructiveHint is False


def test_no_tool_exposes_an_arbitrary_filesystem_path_parameter(
    mcp_settings: Settings,
) -> None:
    server = build_server(mcp_settings)
    tools = asyncio.run(server.list_tools())
    forbidden_param_names = {"file_path", "filepath", "path", "cwd", "command", "shell"}
    for tool in tools:
        props = set((tool.inputSchema or {}).get("properties", {}).keys())
        assert not (props & forbidden_param_names), (
            f"{tool.name} exposes a raw filesystem/command parameter: {props}"
        )


def test_search_graph_tool_call_returns_structured_json(mcp_settings: Settings) -> None:
    server = build_server(mcp_settings)
    payload = _call_tool_json(server, "search_graph", {"query": "foo"})
    assert "results" in payload
    assert payload["result_count"] >= 1


def test_explain_graph_evidence_never_exposes_secret_file_content(
    mcp_settings: Settings,
) -> None:
    server = build_server(mcp_settings)
    payload = _call_tool_json(
        server,
        "explain_graph_evidence",
        {"node_or_edge_id": "json:config/credentials.json"},
    )
    serialized = json.dumps(payload)
    assert "should-never-be-indexed" not in serialized
    assert "api_key" not in serialized


def test_unknown_symbol_returns_actionable_tool_error(mcp_settings: Settings) -> None:
    server = build_server(mcp_settings)
    payload = _call_tool_json(
        server, "get_symbol_call_graph", {"symbol": "totally_nonexistent_symbol_xyz"}
    )
    assert "error" in payload
    assert "no node found" in payload["error"]


def test_get_hotspots_labels_static_vs_runtime_evidence(mcp_settings: Settings) -> None:
    server = build_server(mcp_settings)
    static_payload = _call_tool_json(server, "get_hotspots", {"metric": "pagerank"})
    assert static_payload["evidence_kind"] == "static_centrality"

    runtime_payload = _call_tool_json(
        server, "get_hotspots", {"metric": "runtime_latency"}
    )
    assert runtime_payload["evidence_kind"] == "runtime_evidence"
