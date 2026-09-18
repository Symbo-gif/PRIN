"""TypeScript/JavaScript adapter: line/regex-based import/definition extraction.

As of this writing there is no first-party TypeScript/JavaScript in this
repository (only vendored third-party assets under ``.venv/``, which are
excluded like any vendor directory). This adapter exists so the system is
not silently Python/Rust-only if PRIN ever gains a JS-based tool, and is
exercised only against the test fixture — see
``DOCS/devtools/visualization-mcp-plan.md`` assumption #7. Like the Rust and
Lean adapters, it is regex-based and every edge is
``provenance="static_inference"``.
"""

from __future__ import annotations

import re

from ci_graph.identity import symbol_node_id
from ci_indexer.common import AdapterOutput, ParsedEdge, ParsedNode, PendingImport

_IMPORT_RE = re.compile(
    r"""^\s*import\s+(?:[\w*{}, \n]+\s+from\s+)?['"]([^'"]+)['"]""",
    re.MULTILINE,
)
_REQUIRE_RE = re.compile(r"""require\(\s*['"]([^'"]+)['"]\s*\)""")
_DEF_RE = re.compile(
    r"^\s*export\s+(?:default\s+)?(?:async\s+)?(?P<kind>function|class)\s+"
    r"(?P<name>[A-Za-z_$][A-Za-z0-9_$]*)",
    re.MULTILINE,
)

_KIND_TO_NODE_TYPE = {"function": "function", "class": "class"}


def parse(
    file_node_id: str, repo_path: str, content_hash: str, source: str
) -> AdapterOutput:
    """Parse one TS/JS source file with regex heuristics.

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

    for match in _IMPORT_RE.finditer(source):
        line = _line_of(lines_before, match.start())
        out.pending_imports.append(
            PendingImport(
                src_id=file_node_id,
                raw_target=match.group(1),
                language="tsjs",
                line=line,
            )
        )
    for match in _REQUIRE_RE.finditer(source):
        line = _line_of(lines_before, match.start())
        out.pending_imports.append(
            PendingImport(
                src_id=file_node_id,
                raw_target=match.group(1),
                language="tsjs",
                line=line,
            )
        )

    for match in _DEF_RE.finditer(source):
        kind = match.group("kind")
        name = match.group("name")
        line = _line_of(lines_before, match.start())
        node_id = symbol_node_id("tsjs", repo_path, name)
        out.nodes.append(
            ParsedNode(
                node_id=node_id,
                node_type=_KIND_TO_NODE_TYPE[kind],
                language="tsjs",
                repo_path=repo_path,
                qualified_name=name,
                start_line=line,
                end_line=line,
                content_hash=content_hash,
                label=name,
                attributes={"tsjs_kind": kind, "exported": True},
            )
        )
        out.edges.append(
            ParsedEdge(
                src_id=file_node_id,
                dst_id=node_id,
                edge_type="DEFINES",
                confidence=0.85,
                provenance="static_inference",
                evidence={"matched": f"export {kind} {name}", "line": line},
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
