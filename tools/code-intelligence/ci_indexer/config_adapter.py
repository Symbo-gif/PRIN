"""Configuration adapter: TOML/JSON/YAML key extraction via real parsers.

Unlike the Rust/Lean/TS-JS adapters, this one uses exact parsers
(:mod:`tomllib`, :mod:`json`, and PyYAML's ``safe_load``), so structural
edges (``DEFINES`` file -> config key) are ``provenance="exact_parser"``.
Linking a config key to the *code* that reads it is a much less reliable
inference (would require tracking every ``os.environ``/config-object
access) and is out of scope for this pass; only the well-known,
exactly-parseable dependency-manifest case (``pyproject.toml``'s
``[project.dependencies]``, ``Cargo.toml``'s ``[dependencies]``) produces a
``DEPENDS_ON`` edge to an external module placeholder, since that mapping is
unambiguous by construction.
"""

from __future__ import annotations

import json
import tomllib
from typing import Any

import yaml

from ci_graph.identity import symbol_node_id
from ci_indexer.common import AdapterOutput, Diagnostic, ParsedEdge, ParsedNode

_MAX_KEY_DEPTH = 2
_MAX_KEYS_PER_FILE = 200


def parse(
    file_node_id: str,
    repo_path: str,
    content_hash: str,
    source: str,
    language: str,
) -> AdapterOutput:
    """Parse one TOML/JSON/YAML file.

    Args:
        file_node_id: The node id of the file itself.
        repo_path: POSIX repository-relative path of the file.
        content_hash: SHA-256 hex digest of the file's bytes.
        source: Decoded file text.
        language: ``"toml"``, ``"json"``, or ``"yaml"``.

    Returns:
        The adapter's findings for this file.
    """
    out = AdapterOutput()
    try:
        data = _load(language, source)
    except (
        tomllib.TOMLDecodeError,
        json.JSONDecodeError,
        yaml.YAMLError,
    ) as exc:
        out.diagnostics.append(Diagnostic("error", f"{language} parse error: {exc}"))
        out.partial = True
        return out

    if not isinstance(data, dict):
        return out

    count = 0
    for key_path in _walk_keys(data, depth=_MAX_KEY_DEPTH):
        if count >= _MAX_KEYS_PER_FILE:
            out.diagnostics.append(
                Diagnostic(
                    "info",
                    f"config key extraction truncated at {_MAX_KEYS_PER_FILE} keys",
                )
            )
            break
        key_id = symbol_node_id(language, repo_path, key_path)
        out.nodes.append(
            ParsedNode(
                node_id=key_id,
                node_type="config_key",
                language=language,
                repo_path=repo_path,
                qualified_name=key_path,
                start_line=None,
                end_line=None,
                content_hash=content_hash,
                label=key_path,
            )
        )
        out.edges.append(
            ParsedEdge(
                src_id=file_node_id,
                dst_id=key_id,
                edge_type="DEFINES",
                confidence=1.0,
                provenance="exact_parser",
            )
        )
        count += 1

    for dep_name in _extract_dependency_names(repo_path, data):
        dep_id = f"external:{dep_name}"
        out.nodes.append(
            ParsedNode(
                node_id=dep_id,
                node_type="module",
                language=None,
                repo_path=None,
                qualified_name=dep_name,
                start_line=None,
                end_line=None,
                content_hash=None,
                label=dep_name,
                attributes={"external": True},
            )
        )
        out.edges.append(
            ParsedEdge(
                src_id=file_node_id,
                dst_id=dep_id,
                edge_type="DEPENDS_ON",
                confidence=0.95,
                provenance="exact_parser",
                evidence={"manifest_key": dep_name},
            )
        )

    return out


def _load(language: str, source: str) -> Any:
    if language == "toml":
        return tomllib.loads(source)
    if language == "json":
        return json.loads(source)
    if language == "yaml":
        return yaml.safe_load(source)
    msg = f"unsupported config language {language!r}"
    raise ValueError(msg)


def _walk_keys(obj: dict[str, Any], depth: int, prefix: str = "") -> list[str]:
    keys: list[str] = []
    for key, value in obj.items():
        path = f"{prefix}{key}" if not prefix else f"{prefix}.{key}"
        keys.append(path)
        if depth > 0 and isinstance(value, dict):
            keys.extend(_walk_keys(value, depth - 1, prefix=path))
    return keys


def _extract_dependency_names(repo_path: str, data: dict[str, Any]) -> list[str]:
    names: list[str] = []
    if repo_path.endswith("pyproject.toml"):
        project = data.get("project", {})
        if isinstance(project, dict):
            for dep in project.get("dependencies", []) or []:
                if isinstance(dep, str):
                    names.append(_pep508_name(dep))
    elif repo_path.endswith("Cargo.toml"):
        deps = data.get("dependencies", {})
        if isinstance(deps, dict):
            names.extend(str(k) for k in deps)
        ws = data.get("workspace", {})
        if isinstance(ws, dict):
            ws_deps = ws.get("dependencies", {})
            if isinstance(ws_deps, dict):
                names.extend(str(k) for k in ws_deps)
    return sorted(set(names))


def _pep508_name(requirement: str) -> str:
    for sep in ("[", ">", "<", "=", "!", "~", " "):
        idx = requirement.find(sep)
        if idx != -1:
            requirement = requirement[:idx]
    return requirement.strip()
