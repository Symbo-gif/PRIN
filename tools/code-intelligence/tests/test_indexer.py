"""Indexing, import/dependency extraction, and secret-exclusion tests."""

from __future__ import annotations

from pathlib import Path

import pytest

from ci_graph.store import GraphStore
from ci_indexer import python_adapter
from ci_indexer.orchestrator import discover_files, is_secret_like, run_index


def test_index_fixture_repo_counts(tmp_path: Path, fixture_repo: Path) -> None:
    store = GraphStore(tmp_path / "graph.db")
    result = run_index(store, fixture_repo, force=True)
    assert result.files_scanned >= 12
    assert result.files_failed == 0
    assert result.node_count > 0
    assert result.edge_count > 0
    store.close()


def test_gitignore_exclusion_respected(indexed_store: GraphStore) -> None:
    nodes = indexed_store.all_nodes()
    assert not any(n.repo_path and "ignored_dir" in n.repo_path for n in nodes)


def test_secret_like_files_never_have_content_indexed(
    indexed_store: GraphStore,
) -> None:
    node = indexed_store.get_node("json:config/credentials.json")
    assert node is not None
    assert node.attributes["secret_like"] is True
    # No config_key children were extracted from the secret-like file.
    children = indexed_store.edges_from(node.node_id, edge_types=["DEFINES"])
    assert children == []


def test_is_secret_like_matches_expected_patterns() -> None:
    assert is_secret_like(".env")
    assert is_secret_like(".env.production")
    assert is_secret_like("id_rsa")
    assert is_secret_like("service-credentials.json")
    assert not is_secret_like("settings.yaml")
    assert not is_secret_like("main.py")


def test_python_import_cycle_detected_structurally(indexed_store: GraphStore) -> None:
    edges = indexed_store.edges_from("python:py_pkg/a.py", edge_types=["IMPORTS"])
    targets = {e.dst_id for e in edges}
    assert "python:py_pkg/b.py" in targets
    back_edges = indexed_store.edges_from("python:py_pkg/b.py", edge_types=["IMPORTS"])
    assert "python:py_pkg/a.py" in {e.dst_id for e in back_edges}


def test_python_submodule_import_resolves_to_file_not_init(
    indexed_store: GraphStore,
) -> None:
    # `from py_pkg import b` in a.py must resolve to py_pkg/b.py, not
    # py_pkg/__init__.py (regression test for the ambiguous from-import fix).
    edges = indexed_store.edges_from("python:py_pkg/a.py", edge_types=["IMPORTS"])
    targets = {e.dst_id for e in edges}
    assert "python:py_pkg/b.py" in targets


def test_rust_mod_declaration_resolves_to_sibling_file(
    indexed_store: GraphStore,
) -> None:
    edges = indexed_store.edges_from(
        "rust:rust_crate/src/lib.rs", edge_types=["IMPORTS"]
    )
    targets = {e.dst_id for e in edges}
    assert "rust:rust_crate/src/foo.rs" in targets


def test_rust_definitions_are_static_inference_not_exact(
    indexed_store: GraphStore,
) -> None:
    edges = indexed_store.edges_from(
        "rust:rust_crate/src/lib.rs", edge_types=["DEFINES"]
    )
    assert edges
    assert all(e.provenance == "static_inference" for e in edges)
    assert all(e.confidence < 1.0 for e in edges)


def test_lean_declarations_are_marked_non_semantic(indexed_store: GraphStore) -> None:
    node = indexed_store.get_node("lean:lean/Sample.lean::Fixture.add_comm_fixture")
    assert node is not None
    assert node.node_type == "theorem"
    assert node.attributes["semantic_status"] == "declaration_only_not_checked"


def test_config_dependency_extraction_is_exact_parser(
    indexed_store: GraphStore,
) -> None:
    edges = indexed_store.edges_from("toml:pyproject.toml", edge_types=["DEPENDS_ON"])
    deps = {e.dst_id for e in edges}
    assert "external:requests" in deps
    assert "external:click" in deps
    assert all(e.provenance == "exact_parser" for e in edges)


def test_tsjs_relative_import_resolves(indexed_store: GraphStore) -> None:
    edges = indexed_store.edges_from("tsjs:web/app.ts", edge_types=["IMPORTS"])
    targets = {e.dst_id for e in edges}
    assert "tsjs:web/lib.ts" in targets


def test_discover_files_works_with_relative_repo_root(
    fixture_repo: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    # Regression test: discover_files used to double-join a relative
    # repo_root against paths already relative to it, causing every file
    # read to fail silently.
    monkeypatch.chdir(fixture_repo.parent)
    relative_root = Path(fixture_repo.name)
    files = discover_files(relative_root)
    assert any(f.endswith("py_pkg/a.py") for f in files)


def test_class_method_calls_are_not_double_attributed_to_the_class() -> None:
    # Regression test (PR #17 devin-ai-integration review): the class-level
    # call walk used to re-visit every method body already covered by that
    # method's own call collection, so each method-body call was recorded
    # once against the method and again against the enclosing class.
    source = (
        "class Foo:\n"
        "    def a(self):\n"
        "        helper()\n"
        "    def b(self):\n"
        "        helper()\n"
    )
    out = python_adapter.parse("file:foo.py", "foo.py", "hash", source)
    class_node = next(n for n in out.nodes if n.node_type == "class")
    class_calls = [c for c in out.pending_calls if c.src_id == class_node.node_id]
    method_calls = [c for c in out.pending_calls if c.src_id != class_node.node_id]
    assert not class_calls
    assert len(method_calls) == 2
    assert len(out.pending_calls) == 2


def test_class_body_level_calls_are_still_attributed_to_the_class() -> None:
    # A call made directly in the class body (not inside a method) must
    # still be collected against the class node -- the fix above narrows
    # collection to direct class-body statements, it must not drop them.
    source = "class Foo:\n    x = default_factory()\n    def a(self):\n        pass\n"
    out = python_adapter.parse("file:foo.py", "foo.py", "hash", source)
    class_node = next(n for n in out.nodes if n.node_type == "class")
    assert any(
        c.src_id == class_node.node_id and c.callee_name == "default_factory"
        for c in out.pending_calls
    )
