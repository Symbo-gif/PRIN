"""Lean 4 adapter: line/regex-based import and declaration extraction.

This adapter is explicitly **non-semantic**: it never checks, elaborates,
or executes a proof, and it never claims a theorem is *proved* — only that a
``theorem``/``lemma`` *declaration* with a given name exists at a given
line. All edges are ``provenance="static_inference"``. See the plan's
assumption #5: the only ``.lean`` files in this repository today are
hand-written manual math-audit artifacts under
``EVIDENCE/math-audit/manual/``, not part of any Lean build.
"""

from __future__ import annotations

import re

from ci_graph.identity import symbol_node_id
from ci_indexer.common import AdapterOutput, ParsedEdge, ParsedNode, PendingImport

_IMPORT_RE = re.compile(r"^\s*import\s+([\w.]+)", re.MULTILINE)
_DECL_RE = re.compile(
    r"^\s*(theorem|lemma|def|abbrev|axiom)\s+([A-Za-z_][A-Za-z0-9_'.]*)", re.MULTILINE
)
_NAMESPACE_RE = re.compile(r"^\s*namespace\s+([\w.]+)", re.MULTILINE)

_KIND_TO_NODE_TYPE = {
    "theorem": "theorem",
    "lemma": "theorem",
    "def": "function",
    "abbrev": "function",
    "axiom": "theorem",
}


def parse(
    file_node_id: str, repo_path: str, content_hash: str, source: str
) -> AdapterOutput:
    """Parse one Lean 4 source file with regex heuristics.

    Args:
        file_node_id: The node id of the file itself.
        repo_path: POSIX repository-relative path of the file.
        content_hash: SHA-256 hex digest of the file's bytes.
        source: Decoded file text.

    Returns:
        The adapter's findings for this file.
    """
    out = AdapterOutput()
    lines_before = _line_starts(source)
    namespaces = [m.group(1) for m in _NAMESPACE_RE.finditer(source)]
    prefix = f"{namespaces[0]}." if namespaces else ""

    for match in _IMPORT_RE.finditer(source):
        target = match.group(1)
        line = _line_of(lines_before, match.start())
        out.pending_imports.append(
            PendingImport(
                src_id=file_node_id, raw_target=target, language="lean", line=line
            )
        )

    for match in _DECL_RE.finditer(source):
        kind = match.group(1)
        name = match.group(2)
        qualified = f"{prefix}{name}"
        line = _line_of(lines_before, match.start())
        node_id = symbol_node_id("lean", repo_path, qualified)
        node_type = _KIND_TO_NODE_TYPE[kind]
        out.nodes.append(
            ParsedNode(
                node_id=node_id,
                node_type=node_type,
                language="lean",
                repo_path=repo_path,
                qualified_name=qualified,
                start_line=line,
                end_line=line,
                content_hash=content_hash,
                label=name,
                attributes={
                    "lean_kind": kind,
                    "semantic_status": "declaration_only_not_checked",
                },
            )
        )
        out.edges.append(
            ParsedEdge(
                src_id=file_node_id,
                dst_id=node_id,
                edge_type="DEFINES",
                confidence=0.8,
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
