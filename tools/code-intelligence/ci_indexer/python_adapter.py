"""Python adapter: exact AST-based imports, definitions, and calls.

Uses the standard-library :mod:`ast` module (no source execution, no
``eval``/``exec``), so extraction is exact for syntax (imports, class/def
statements) and heuristic only for call-target *resolution*, which is
labeled ``naming_heuristic`` by the orchestrator once it resolves
:class:`~ci_indexer.common.PendingCall` entries across the whole repository.
"""

from __future__ import annotations

import ast

from ci_graph.identity import symbol_node_id
from ci_indexer.common import (
    AdapterOutput,
    Diagnostic,
    ParsedEdge,
    ParsedNode,
    PendingCall,
    PendingImport,
)


def parse(
    file_node_id: str, repo_path: str, content_hash: str, source: str
) -> AdapterOutput:
    """Parse one Python source file.

    Args:
        file_node_id: The node id of the file itself (edge source for
            ``DEFINES``).
        repo_path: POSIX repository-relative path of the file.
        content_hash: SHA-256 hex digest of the file's bytes.
        source: Decoded file text.

    Returns:
        The adapter's findings for this file.
    """
    out = AdapterOutput()
    try:
        tree = ast.parse(source, filename=repo_path)
    except SyntaxError as exc:
        out.diagnostics.append(
            Diagnostic("error", f"Python syntax error at line {exc.lineno}: {exc.msg}")
        )
        out.partial = True
        return out

    _walk_module(tree, file_node_id, repo_path, content_hash, out, scope_prefix="")
    return out


def _walk_module(
    tree: ast.Module,
    file_node_id: str,
    repo_path: str,
    content_hash: str,
    out: AdapterOutput,
    scope_prefix: str,
) -> None:
    for stmt in tree.body:
        _walk_statement(stmt, file_node_id, repo_path, content_hash, out, scope_prefix)


def _walk_statement(
    stmt: ast.stmt,
    file_node_id: str,
    repo_path: str,
    content_hash: str,
    out: AdapterOutput,
    scope_prefix: str,
) -> None:
    if isinstance(stmt, ast.Import):
        for alias in stmt.names:
            out.pending_imports.append(
                PendingImport(
                    src_id=file_node_id,
                    raw_target=alias.name,
                    language="python",
                    line=stmt.lineno,
                )
            )
    elif isinstance(stmt, ast.ImportFrom):
        dots = "." * stmt.level
        base = stmt.module or ""
        for alias in stmt.names:
            # `from X import Y` is ambiguous between "import name Y from
            # module X" and "import submodule Y of package X" without a
            # symbol table; emit the submodule guess (most specific) and
            # let the orchestrator's progressive-shortening fall back to
            # the base module/package when the guess does not resolve.
            if alias.name == "*":
                target = f"{dots}{base}"
            else:
                target = f"{dots}{base}.{alias.name}" if base else f"{dots}{alias.name}"
            out.pending_imports.append(
                PendingImport(
                    src_id=file_node_id,
                    raw_target=target,
                    language="python",
                    line=stmt.lineno,
                )
            )
    elif isinstance(stmt, ast.ClassDef):
        qualified = f"{scope_prefix}{stmt.name}"
        class_id = symbol_node_id("python", repo_path, qualified)
        is_test = _is_test_name(stmt.name)
        out.nodes.append(
            ParsedNode(
                node_id=class_id,
                node_type="test" if is_test else "class",
                language="python",
                repo_path=repo_path,
                qualified_name=qualified,
                start_line=stmt.lineno,
                end_line=getattr(stmt, "end_lineno", stmt.lineno),
                content_hash=content_hash,
                label=stmt.name,
                attributes={"decorators": _decorator_names(stmt.decorator_list)},
            )
        )
        out.edges.append(
            ParsedEdge(
                src_id=file_node_id,
                dst_id=class_id,
                edge_type="DEFINES",
                confidence=1.0,
                provenance="exact_parser",
            )
        )
        for member in stmt.body:
            _walk_statement(
                member,
                file_node_id,
                repo_path,
                content_hash,
                out,
                scope_prefix=f"{qualified}.",
            )
            # Methods and nested classes collect their own calls via the
            # recursive _walk_statement above; only direct class-body
            # statements (e.g. `x = default_factory()`) are walked here, to
            # avoid re-attributing every method-body call to the class node
            # as well as to the method (PR #17 devin-ai-integration review).
            if not isinstance(
                member, ast.FunctionDef | ast.AsyncFunctionDef | ast.ClassDef
            ):
                _collect_calls(member, class_id, out)
    elif isinstance(stmt, ast.FunctionDef | ast.AsyncFunctionDef):
        qualified = f"{scope_prefix}{stmt.name}"
        func_id = symbol_node_id("python", repo_path, qualified)
        is_method = bool(scope_prefix)
        is_test = _is_test_name(stmt.name)
        node_type = "test" if is_test else ("method" if is_method else "function")
        out.nodes.append(
            ParsedNode(
                node_id=func_id,
                node_type=node_type,
                language="python",
                repo_path=repo_path,
                qualified_name=qualified,
                start_line=stmt.lineno,
                end_line=getattr(stmt, "end_lineno", stmt.lineno),
                content_hash=content_hash,
                label=stmt.name,
                attributes={
                    "decorators": _decorator_names(stmt.decorator_list),
                    "is_async": isinstance(stmt, ast.AsyncFunctionDef),
                    "arg_count": len(stmt.args.args),
                },
            )
        )
        out.edges.append(
            ParsedEdge(
                src_id=file_node_id,
                dst_id=func_id,
                edge_type="DEFINES",
                confidence=1.0,
                provenance="exact_parser",
            )
        )
        _collect_calls(stmt, func_id, out)
    # Nested defs inside other statement kinds (if/for/with/try at module
    # scope) are intentionally not descended into: PRIN's public API surface
    # (Coding Standards §3) is defined at module/class scope, and descending
    # into every control-flow branch would blur the "qualified name is a
    # stable symbol identity" guarantee this graph relies on.


def _collect_calls(fn_node: ast.AST, caller_id: str, out: AdapterOutput) -> None:
    for node in ast.walk(fn_node):
        if isinstance(node, ast.Call):
            name = _callee_simple_name(node.func)
            if name is not None:
                out.pending_calls.append(
                    PendingCall(src_id=caller_id, callee_name=name, line=node.lineno)
                )


def _callee_simple_name(func_expr: ast.expr) -> str | None:
    if isinstance(func_expr, ast.Name):
        return func_expr.id
    if isinstance(func_expr, ast.Attribute):
        return func_expr.attr
    return None


def _decorator_names(decorators: list[ast.expr]) -> list[str]:
    names = []
    for dec in decorators:
        target = dec.func if isinstance(dec, ast.Call) else dec
        name = (
            _callee_simple_name(target) if isinstance(target, ast.Attribute) else None
        )
        if isinstance(target, ast.Name):
            name = target.id
        if name:
            names.append(name)
    return names


def _is_test_name(name: str) -> bool:
    return name.startswith("test_") or name.startswith("Test")
