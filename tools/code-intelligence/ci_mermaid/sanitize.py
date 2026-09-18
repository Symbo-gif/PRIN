"""Mermaid identifier stabilization and label escaping.

Mermaid node ids must be simple tokens; graph node ids contain ``:``, ``/``,
``.``, and ``::``, none of which are safe. This module derives a short,
deterministic, collision-resistant Mermaid id from each graph node id, and
escapes label text so no diagram can be broken (or have its structure
altered) by a symbol/file name containing quotes, pipes, or newlines.
"""

from __future__ import annotations

import hashlib
import re

_UNSAFE_ID_CHARS = re.compile(r"[^A-Za-z0-9_]")
_LABEL_UNSAFE = re.compile(r'["`<>#|\r\n]')


def mermaid_node_id(graph_node_id: str) -> str:
    """Derive a stable, Mermaid-safe node id from a graph node id.

    Args:
        graph_node_id: The stable graph node id (e.g.
            ``"python:python/prin/nn/layer.py::MyClass.method"``).

    Returns:
        A token starting with ``n_``, safe for use as a Mermaid node id,
        deterministic across calls and diagrams for the same input.
    """
    digest = hashlib.sha256(graph_node_id.encode("utf-8")).hexdigest()[:8]
    readable = _UNSAFE_ID_CHARS.sub("_", graph_node_id)[-40:]
    return f"n_{digest}_{readable}"


def sanitize_label(label: str, max_length: int = 60) -> str:
    """Escape and truncate a label for safe embedding in a Mermaid node.

    Args:
        label: The raw human-readable label.
        max_length: Maximum characters before truncation with an ellipsis.

    Returns:
        A label safe to place inside ``"..."`` in Mermaid node syntax: no
        double quotes, backticks, angle brackets, ``#``, pipes, or newlines.
    """
    cleaned = _LABEL_UNSAFE.sub("'", label.replace("\n", " ").replace("\r", " "))
    cleaned = cleaned.strip() or "(unnamed)"
    if len(cleaned) > max_length:
        cleaned = cleaned[: max_length - 1] + "…"
    return cleaned


def sanitize_subgraph_title(title: str) -> str:
    """Escape a subgraph/cluster title.

    Args:
        title: The raw title.

    Returns:
        A safe title, quoted the same way node labels are.
    """
    return sanitize_label(title, max_length=40)
