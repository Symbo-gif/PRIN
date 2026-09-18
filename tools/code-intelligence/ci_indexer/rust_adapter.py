"""Rust adapter: line/regex-based module, import, and item extraction.

This is a **heuristic, textual** adapter, not a `rustc`/`syn`-backed parser:
it does not resolve macros, cannot see through `include!`, and can
mis-detect an item declared inside a string or comment in pathological
cases. Every edge it emits is recorded with ``provenance="static_inference"``
(never ``exact_parser``) precisely because of this. It is deliberately
dependency-free so indexing never fails when a full Rust parser/grammar is
unavailable, per the plan's "graceful partial indexing" requirement.
"""

from __future__ import annotations

import re

from ci_graph.identity import symbol_node_id
from ci_indexer.common import (
    AdapterOutput,
    ParsedEdge,
    ParsedNode,
    PendingImport,
)

_USE_RE = re.compile(
    r"^\s*(?:pub(?:\([^)]*\))?\s+)?use\s+([\w:{}, ]+?)\s*;", re.MULTILINE
)
_MOD_RE = re.compile(r"^\s*(?:pub(?:\([^)]*\))?\s+)?mod\s+(\w+)\s*;", re.MULTILINE)
_ITEM_RE = re.compile(
    r"^\s*(?:#\[([^\]]*)\]\s*\n\s*)?"
    r"(?P<vis>pub(?:\([^)]*\))?\s+)?"
    r"(?P<kind>fn|struct|trait|enum)\s+"
    r"(?P<name>[A-Za-z_][A-Za-z0-9_]*)",
    re.MULTILINE,
)

_KIND_TO_NODE_TYPE = {
    "fn": "function",
    "struct": "class",
    "trait": "class",
    "enum": "class",
}


def parse(
    file_node_id: str, repo_path: str, content_hash: str, source: str
) -> AdapterOutput:
    """Parse one Rust source file with regex heuristics.

    Args:
        file_node_id: The node id of the file itself.
        repo_path: POSIX repository-relative path of the file.
        content_hash: SHA-256 hex digest of the file's bytes.
        source: Decoded file text.

    Returns:
        The adapter's findings for this file. ``partial`` is always
        implicitly true in spirit for this adapter (it is heuristic by
        construction), but the ``partial`` flag itself is reserved for
        genuine parse failures, of which a regex scan has none.
    """
    out = AdapterOutput()
    lines_before = _line_starts(source)

    for match in _USE_RE.finditer(source):
        target = match.group(1).strip()
        line = _line_of(lines_before, match.start())
        out.pending_imports.append(
            PendingImport(
                src_id=file_node_id, raw_target=target, language="rust", line=line
            )
        )

    for match in _MOD_RE.finditer(source):
        mod_name = match.group(1)
        line = _line_of(lines_before, match.start())
        out.pending_imports.append(
            PendingImport(
                src_id=file_node_id,
                raw_target=f"mod::{mod_name}",
                language="rust",
                line=line,
            )
        )

    for match in _ITEM_RE.finditer(source):
        kind = match.group("kind")
        name = match.group("name")
        attrs_text = match.group(1) or ""
        is_pub = bool(match.group("vis"))
        line = _line_of(lines_before, match.start())
        node_type = _KIND_TO_NODE_TYPE[kind]
        is_test = "test" in attrs_text
        if is_test:
            node_type = "test"
        item_id = symbol_node_id("rust", repo_path, name)
        out.nodes.append(
            ParsedNode(
                node_id=item_id,
                node_type=node_type,
                language="rust",
                repo_path=repo_path,
                qualified_name=name,
                start_line=line,
                end_line=line,
                content_hash=content_hash,
                label=name,
                attributes={"rust_kind": kind, "is_pub": is_pub, "is_test": is_test},
            )
        )
        out.edges.append(
            ParsedEdge(
                src_id=file_node_id,
                dst_id=item_id,
                edge_type="DEFINES",
                confidence=0.85,
                provenance="static_inference",
                evidence={"matched": f"{kind} {name}", "line": line},
            )
        )

    return out


def _line_starts(source: str) -> list[int]:
    starts = [0]
    for i, ch in enumerate(source):
        if ch == "\n":
            starts.append(i + 1)
    return starts


def _line_of(line_starts: list[int], offset: int) -> int:
    import bisect

    idx = bisect.bisect_right(line_starts, offset) - 1
    return idx + 1
