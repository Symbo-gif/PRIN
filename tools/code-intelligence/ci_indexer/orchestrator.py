"""Repository walk, exclusion handling, adapter dispatch, and edge resolution.

This is the only module that talks to :class:`~ci_graph.store.GraphStore`
during indexing. It is responsible for:

1. Discovering files, honoring ``.gitignore`` (via ``pathspec``) plus the
   subsystem's own default exclusion list (``ci_config``).
2. Refusing to read the *content* of anything that looks like a secret file,
   regardless of exclusion configuration.
3. Dispatching each file to the matching per-language adapter and writing
   the nodes/edges it returns.
4. Resolving cross-file imports and best-effort call targets once every
   file has been parsed once (a two-pass design, since an importer may be
   discovered before its target).
"""

from __future__ import annotations

import fnmatch
from collections import defaultdict
from dataclasses import dataclass, field
from pathlib import Path

import pathspec

from ci_config import (
    DEFAULT_EXCLUDE_DIR_NAMES,
    DEFAULT_EXCLUDE_PATH_PREFIXES,
    LANGUAGE_BY_EXTENSION,
    SECRET_LIKE_FILENAME_GLOBS,
)
from ci_graph.identity import (
    content_hash as compute_content_hash,
)
from ci_graph.identity import (
    directory_node_id,
    file_node_id,
    normalize_repo_path,
)
from ci_graph.store import GraphStore
from ci_indexer import (
    config_adapter,
    lean_adapter,
    python_adapter,
    rust_adapter,
    tsjs_adapter,
)
from ci_indexer.common import AdapterOutput, PendingCall, PendingImport

_CONFIG_LANGUAGES = {"toml", "json", "yaml"}
_MAX_AMBIGUOUS_CALL_TARGETS = 3
#: Naming-heuristic call resolution has no type information, so an
#: attribute-call name like ``.get(...)`` or ``.to(device)`` is recorded
#: identically regardless of the receiver's actual type. A repo-wide call
#: site occurring this many times or more is overwhelmingly likely to be a
#: generic/stdlib-shaped accessor name (``len``, ``get``, ``to``, ``new``)
#: rather than a specific, resolvable in-repo function, and resolving it
#: would flood fan-in/PageRank hotspots with false positives. Such names
#: are skipped entirely rather than resolved with low confidence, since a
#: skipped edge is honest (no edge = no claim) while a low-confidence edge
#: at this volume would still dominate aggregate rankings.
_MAX_CALL_SITE_OCCURRENCES_FOR_RESOLUTION = 30


@dataclass
class IndexResult:
    """Summary of one indexing run, returned to the CLI/MCP status tools.

    Attributes:
        run_id: The completed run's id.
        index_version: Aggregate content-hash version tag.
        files_scanned: Files considered after exclusion.
        files_indexed: Files successfully parsed (fully or partially).
        files_failed: Files that raised a parse error.
        files_skipped: Files excluded by ignore rules.
        node_count: Total nodes in the graph after this run.
        edge_count: Total edges in the graph after this run.
        diagnostics: Human-readable diagnostic messages (capped).
    """

    run_id: int
    index_version: str
    files_scanned: int
    files_indexed: int
    files_failed: int
    files_skipped: int
    node_count: int
    edge_count: int
    diagnostics: list[str] = field(default_factory=list)


def is_secret_like(filename: str) -> bool:
    """Return True if a filename matches a secret-like pattern.

    Args:
        filename: The bare filename (no directory component).

    Returns:
        True if content of this file must never be read or stored.
    """
    return any(fnmatch.fnmatch(filename, pat) for pat in SECRET_LIKE_FILENAME_GLOBS)


def _load_gitignore_spec(repo_root: Path) -> pathspec.PathSpec:  # type: ignore[type-arg]
    gitignore = repo_root / ".gitignore"
    lines: list[str] = []
    if gitignore.exists():
        lines = gitignore.read_text(encoding="utf-8", errors="replace").splitlines()
    return pathspec.PathSpec.from_lines("gitignore", lines)


def _is_excluded(rel_path: str, spec: pathspec.PathSpec) -> bool:  # type: ignore[type-arg]
    parts = rel_path.split("/")
    if any(p in DEFAULT_EXCLUDE_DIR_NAMES for p in parts):
        return True
    if any(rel_path.startswith(prefix) for prefix in DEFAULT_EXCLUDE_PATH_PREFIXES):
        return True
    return spec.match_file(rel_path)


def discover_files(repo_root: Path) -> list[str]:
    """Walk the repository and return indexable, non-excluded relative paths.

    Args:
        repo_root: Absolute repository root.

    Returns:
        Sorted, POSIX, repository-relative paths whose extension is
        recognized (see ``ci_config.LANGUAGE_BY_EXTENSION``) and which are
        not excluded by ``.gitignore`` or the default exclusion list.
    """
    # Resolve first: ``rglob`` on a relative ``repo_root`` yields paths that
    # already carry that relative prefix, and re-joining them onto a
    # separately resolved root in ``normalize_repo_path`` would double it.
    repo_root = repo_root.resolve()
    spec = _load_gitignore_spec(repo_root)
    found: list[str] = []
    for path in repo_root.rglob("*"):
        if path.is_dir():
            continue
        if path.suffix not in LANGUAGE_BY_EXTENSION:
            continue
        rel = normalize_repo_path(str(repo_root), str(path))
        if _is_excluded(rel, spec):
            continue
        found.append(rel)
    return sorted(found)


def _ensure_directory_chain(
    store: GraphStore, repo_relative_path: str, run_id: int
) -> str:
    """Create directory nodes + CONTAINS edges for every ancestor directory.

    Returns:
        The node id of the immediate parent directory.
    """
    parts = repo_relative_path.split("/")[:-1]
    parent_id = directory_node_id("")
    store.upsert_node(
        node_id=parent_id,
        node_type="directory",
        language=None,
        repo_path="",
        qualified_name=None,
        start_line=None,
        end_line=None,
        content_hash=None,
        label=".",
        run_id=run_id,
    )
    accumulated = ""
    for part in parts:
        accumulated = f"{accumulated}/{part}" if accumulated else part
        node_id = directory_node_id(accumulated)
        store.upsert_node(
            node_id=node_id,
            node_type="directory",
            language=None,
            repo_path=accumulated,
            qualified_name=None,
            start_line=None,
            end_line=None,
            content_hash=None,
            label=part,
            run_id=run_id,
        )
        store.upsert_edge(
            src_id=parent_id,
            dst_id=node_id,
            edge_type="CONTAINS",
            confidence=1.0,
            provenance="exact_parser",
            run_id=run_id,
        )
        parent_id = node_id
    return parent_id


def run_index(
    store: GraphStore, repo_root: Path, *, force: bool = False
) -> IndexResult:
    """Index the repository into ``store``.

    Args:
        store: An open, writable :class:`~ci_graph.store.GraphStore`.
        repo_root: Absolute repository root to index.
        force: If True, clear all previously indexed data first.

    Returns:
        A summary of the run.
    """
    repo_root = repo_root.resolve()
    if force:
        store.clear_all()

    files = discover_files(repo_root)
    all_diagnostics: list[str] = []

    # Pass 1: create directory + file nodes, run per-language adapters,
    # collect deferred (cross-file) imports and calls.
    hashes: list[str] = []
    pending_imports: list[PendingImport] = []
    pending_calls: list[PendingCall] = []
    files_indexed = 0
    files_failed = 0
    files_skipped = 0

    run_id = store.begin_run(str(repo_root), index_version="pending")

    module_index: dict[str, str] = {}  # dotted/module key -> node_id, all languages
    name_index: dict[str, list[str]] = defaultdict(
        list
    )  # simple symbol name -> [node_id]
    file_node_ids: dict[str, str] = {}  # repo_path -> file node_id

    for rel_path in files:
        language = LANGUAGE_BY_EXTENSION[Path(rel_path).suffix]
        abs_path = repo_root / rel_path
        try:
            raw = abs_path.read_bytes()
        except OSError as exc:
            files_failed += 1
            msg = f"could not read file: {exc}"
            store.add_diagnostic(run_id, rel_path, "error", msg)
            all_diagnostics.append(f"{rel_path}: {msg}")
            continue

        chash = compute_content_hash(raw)
        hashes.append(chash)
        fid = file_node_id(language, rel_path)
        file_node_ids[rel_path] = fid
        parent_dir_id = _ensure_directory_chain(store, rel_path, run_id)

        filename = Path(rel_path).name
        secret = is_secret_like(filename)
        node_type = "config_file" if language in _CONFIG_LANGUAGES else "file"
        store.upsert_node(
            node_id=fid,
            node_type=node_type,
            language=language,
            repo_path=rel_path,
            qualified_name=None,
            start_line=None,
            end_line=None,
            content_hash=chash,
            label=filename,
            run_id=run_id,
            attributes={"secret_like": secret},
        )
        store.upsert_edge(
            src_id=parent_dir_id,
            dst_id=fid,
            edge_type="CONTAINS",
            confidence=1.0,
            provenance="exact_parser",
            run_id=run_id,
        )

        if secret:
            # Content is never read for parsing; the file is represented
            # structurally only (name + location), never its text.
            files_skipped += 1
            store.add_diagnostic(
                run_id, rel_path, "info", "secret-like filename: content not indexed"
            )
            continue

        try:
            text = raw.decode("utf-8")
        except UnicodeDecodeError:
            files_skipped += 1
            store.add_diagnostic(
                run_id, rel_path, "warning", "not valid UTF-8: skipped"
            )
            continue

        output = _dispatch_adapter(language, fid, rel_path, chash, text)
        for diag in output.diagnostics:
            store.add_diagnostic(run_id, rel_path, diag.severity, diag.message)
            all_diagnostics.append(f"{rel_path}: {diag.message}")
        if output.partial:
            files_failed += 1
        else:
            files_indexed += 1

        _register_module_keys(module_index, language, rel_path, fid)
        for node in output.nodes:
            store.upsert_node(
                node_id=node.node_id,
                node_type=node.node_type,
                language=node.language,
                repo_path=node.repo_path,
                qualified_name=node.qualified_name,
                start_line=node.start_line,
                end_line=node.end_line,
                content_hash=node.content_hash,
                label=node.label,
                run_id=run_id,
                attributes=node.attributes,
            )
            if node.qualified_name:
                simple = node.qualified_name.rsplit(".", 1)[-1]
                name_index[simple].append(node.node_id)
        for edge in output.edges:
            store.upsert_edge(
                src_id=edge.src_id,
                dst_id=edge.dst_id,
                edge_type=edge.edge_type,
                confidence=edge.confidence,
                provenance=edge.provenance,
                run_id=run_id,
                evidence=edge.evidence,
            )
        pending_imports.extend(output.pending_imports)
        pending_calls.extend(output.pending_calls)

    # Pass 2: resolve deferred imports and calls now that every file's
    # nodes are known.
    for imp in pending_imports:
        _resolve_import(store, repo_root, imp, module_index, file_node_ids, run_id)
    call_site_frequency: dict[str, int] = defaultdict(int)
    for call in pending_calls:
        call_site_frequency[call.callee_name] += 1
    for call in pending_calls:
        if (
            call_site_frequency[call.callee_name]
            >= _MAX_CALL_SITE_OCCURRENCES_FOR_RESOLUTION
        ):
            continue
        _resolve_call(store, call, name_index, run_id)

    store.commit()
    index_version = compute_content_hash("\n".join(sorted(hashes)).encode("utf-8"))
    store.finish_run(
        run_id,
        files_scanned=len(files),
        files_indexed=files_indexed,
        files_failed=files_failed,
        files_skipped=files_skipped,
        index_version=index_version,
        status="complete",
    )

    return IndexResult(
        run_id=run_id,
        index_version=index_version,
        files_scanned=len(files),
        files_indexed=files_indexed,
        files_failed=files_failed,
        files_skipped=files_skipped,
        node_count=store.node_count(),
        edge_count=store.edge_count(),
        diagnostics=all_diagnostics[:200],
    )


def _dispatch_adapter(
    language: str, fid: str, rel_path: str, chash: str, text: str
) -> AdapterOutput:
    if language == "python":
        return python_adapter.parse(fid, rel_path, chash, text)
    if language == "rust":
        return rust_adapter.parse(fid, rel_path, chash, text)
    if language == "lean":
        return lean_adapter.parse(fid, rel_path, chash, text)
    if language in _CONFIG_LANGUAGES:
        return config_adapter.parse(fid, rel_path, chash, text, language)
    if language == "tsjs":
        return tsjs_adapter.parse(fid, rel_path, chash, text)
    return AdapterOutput()


def _register_module_keys(
    module_index: dict[str, str], language: str, rel_path: str, fid: str
) -> None:
    if language != "python":
        return
    stem_path = rel_path[:-3] if rel_path.endswith(".py") else rel_path
    is_init = stem_path.endswith("/__init__") or stem_path == "__init__"
    module_path = stem_path[: -len("/__init__")] if is_init else stem_path
    dotted_from_root = module_path.replace("/", ".")
    module_index[dotted_from_root] = fid
    if module_path.startswith("python/"):
        dotted_from_src = module_path[len("python/") :].replace("/", ".")
        module_index[dotted_from_src] = fid


def _resolve_import(
    store: GraphStore,
    repo_root: Path,
    imp: PendingImport,
    module_index: dict[str, str],
    file_node_ids: dict[str, str],
    run_id: int,
) -> None:
    del repo_root  # filesystem access is not needed by any resolver below;
    # internal targets are resolved purely from the in-memory node-id maps
    # built during pass 1, which is both faster and keeps resolution
    # reproducible without re-touching the filesystem mid-run.
    if imp.language == "python":
        _resolve_python_import(store, imp, module_index, run_id)
    elif imp.language == "rust":
        _resolve_rust_import(store, imp, file_node_ids, run_id)
    elif imp.language == "lean":
        _resolve_lean_import(store, imp, run_id)
    elif imp.language == "tsjs":
        _resolve_tsjs_import(store, imp, file_node_ids, run_id)


def _external_module_node(store: GraphStore, name: str, run_id: int) -> str:
    node_id = f"external:{name}"
    store.upsert_node(
        node_id=node_id,
        node_type="module",
        language=None,
        repo_path=None,
        qualified_name=name,
        start_line=None,
        end_line=None,
        content_hash=None,
        label=name,
        run_id=run_id,
        attributes={"external": True},
    )
    return node_id


def _resolve_python_import(
    store: GraphStore, imp: PendingImport, module_index: dict[str, str], run_id: int
) -> None:
    target = imp.raw_target
    resolved: str | None = None
    if target.startswith("."):
        importer_repo_path = imp.src_id.split(":", 1)[1]
        resolved = _resolve_relative_python(target, importer_repo_path, module_index)
    else:
        candidate = target
        while candidate:
            if candidate in module_index:
                resolved = module_index[candidate]
                break
            if "." not in candidate:
                break
            candidate = candidate.rsplit(".", 1)[0]

    dst_id = resolved or _external_module_node(
        store, target.lstrip(".") or "relative_import", run_id
    )
    store.upsert_edge(
        src_id=imp.src_id,
        dst_id=dst_id,
        edge_type="IMPORTS",
        confidence=0.95,
        provenance="exact_parser",
        run_id=run_id,
        evidence={"raw_target": target, "line": imp.line},
    )


def _resolve_relative_python(
    target: str, importer_repo_path: str, module_index: dict[str, str]
) -> str | None:
    level = len(target) - len(target.lstrip("."))
    remainder = target[level:]
    stem = (
        importer_repo_path[:-3]
        if importer_repo_path.endswith(".py")
        else importer_repo_path
    )
    is_init = stem.endswith("/__init__")
    importer_package = (
        stem[: -len("/__init__")]
        if is_init
        else stem.rsplit("/", 1)[0]
        if "/" in stem
        else ""
    )
    package_parts = [p for p in importer_package.split("/") if p]
    levels_up = level - 1
    if levels_up > len(package_parts):
        return None
    base_parts = (
        package_parts[: len(package_parts) - levels_up] if levels_up else package_parts
    )
    remainder_parts = remainder.split(".") if remainder else []
    full_parts = base_parts + remainder_parts
    # Progressive shortening mirrors `_resolve_python_import`'s absolute-import
    # loop: try the most specific guess (submodule) first, then fall back
    # toward the base package, since `from .pkg import name` is ambiguous
    # between "import a submodule named `name`" and "import an attribute
    # named `name` from `.pkg`" without a symbol table.
    while len(full_parts) >= len(base_parts):
        candidate_slash = "/".join(full_parts)
        candidate_dotted = ".".join(full_parts)
        for candidate in (candidate_slash, candidate_dotted):
            if candidate in module_index:
                return module_index[candidate]
            prefixed = f"python/{candidate}"
            if prefixed in module_index:
                return module_index[prefixed]
        if len(full_parts) == len(base_parts):
            break
        full_parts = full_parts[:-1]
    return None


def _resolve_rust_import(
    store: GraphStore,
    imp: PendingImport,
    file_node_ids: dict[str, str],
    run_id: int,
) -> None:
    importer_repo_path = imp.src_id.split(":", 1)[1]
    importer_dir = str(Path(importer_repo_path).parent).replace("\\", "/")
    importer_stem = Path(importer_repo_path).stem

    if imp.raw_target.startswith("mod::"):
        mod_name = imp.raw_target.removeprefix("mod::")
        base_dirs = [importer_dir]
        if importer_stem not in ("mod", "lib", "main"):
            base_dirs.append(
                f"{importer_dir}/{importer_stem}"
                if importer_dir != "."
                else importer_stem
            )
        for base in base_dirs:
            for candidate in (f"{base}/{mod_name}.rs", f"{base}/{mod_name}/mod.rs"):
                candidate = candidate.lstrip("/")
                if candidate in file_node_ids:
                    store.upsert_edge(
                        src_id=imp.src_id,
                        dst_id=file_node_ids[candidate],
                        edge_type="IMPORTS",
                        confidence=0.9,
                        provenance="static_inference",
                        run_id=run_id,
                        evidence={"raw_target": imp.raw_target, "line": imp.line},
                    )
                    return
        dst_id = _external_module_node(store, f"mod::{mod_name} (unresolved)", run_id)
        store.upsert_edge(
            src_id=imp.src_id,
            dst_id=dst_id,
            edge_type="IMPORTS",
            confidence=0.4,
            provenance="static_inference",
            run_id=run_id,
            evidence={
                "raw_target": imp.raw_target,
                "line": imp.line,
                "unresolved": True,
            },
        )
        return

    # `use` path: only the leading identifier is used to decide
    # internal-vs-external; the full mapping to a specific file is not
    # attempted (see module docstring) — heuristic by construction.
    head = imp.raw_target.split("::", 1)[0].strip().lstrip("{").strip()
    dst_id = _external_module_node(store, head, run_id)
    store.upsert_edge(
        src_id=imp.src_id,
        dst_id=dst_id,
        edge_type="IMPORTS",
        confidence=0.5,
        provenance="naming_heuristic",
        run_id=run_id,
        evidence={"raw_target": imp.raw_target, "line": imp.line},
    )


def _resolve_lean_import(store: GraphStore, imp: PendingImport, run_id: int) -> None:
    dst_id = _external_module_node(store, imp.raw_target, run_id)
    store.upsert_edge(
        src_id=imp.src_id,
        dst_id=dst_id,
        edge_type="IMPORTS",
        confidence=0.5,
        provenance="naming_heuristic",
        run_id=run_id,
        evidence={"raw_target": imp.raw_target, "line": imp.line},
    )


def _resolve_tsjs_import(
    store: GraphStore,
    imp: PendingImport,
    file_node_ids: dict[str, str],
    run_id: int,
) -> None:
    target = imp.raw_target
    if target.startswith("."):
        importer_repo_path = imp.src_id.split(":", 1)[1]
        importer_dir = Path(importer_repo_path).parent
        base = (importer_dir / target).as_posix()
        base = _normalize_dotdot(base)
        candidates = (
            [base]
            + [f"{base}{ext}" for ext in (".ts", ".tsx", ".js", ".jsx")]
            + [f"{base}/index{ext}" for ext in (".ts", ".tsx", ".js", ".jsx")]
        )
        for candidate in candidates:
            if candidate in file_node_ids:
                store.upsert_edge(
                    src_id=imp.src_id,
                    dst_id=file_node_ids[candidate],
                    edge_type="IMPORTS",
                    confidence=0.75,
                    provenance="static_inference",
                    run_id=run_id,
                    evidence={"raw_target": target, "line": imp.line},
                )
                return
    dst_id = _external_module_node(store, target, run_id)
    store.upsert_edge(
        src_id=imp.src_id,
        dst_id=dst_id,
        edge_type="IMPORTS",
        confidence=0.6,
        provenance="static_inference",
        run_id=run_id,
        evidence={"raw_target": target, "line": imp.line},
    )


def _normalize_dotdot(path: str) -> str:
    parts: list[str] = []
    for part in path.split("/"):
        if part == "..":
            if parts:
                parts.pop()
        elif part not in (".", ""):
            parts.append(part)
    return "/".join(parts)


def _resolve_call(
    store: GraphStore,
    call: PendingCall,
    name_index: dict[str, list[str]],
    run_id: int,
) -> None:
    candidates = [c for c in name_index.get(call.callee_name, []) if c != call.src_id]
    if not candidates or len(candidates) > _MAX_AMBIGUOUS_CALL_TARGETS:
        return
    confidence = 0.6 if len(candidates) == 1 else 0.35
    for callee_id in candidates:
        store.upsert_edge(
            src_id=call.src_id,
            dst_id=callee_id,
            edge_type="CALLS",
            confidence=confidence,
            provenance="naming_heuristic",
            run_id=run_id,
            evidence={"callee_name": call.callee_name, "line": call.line},
        )
