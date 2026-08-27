#!/usr/bin/env python
"""Build and validate the deterministic WP-001 foundation baseline."""

from __future__ import annotations

import argparse
import ast
import json
import os
import re
import sys
import tomllib
from collections import Counter
from dataclasses import dataclass
from pathlib import Path
from typing import Any

_ARCHIVE = Path(
    "DOCS/archive and reference from PRINet 3.0/PRINet-3.0.0-main/src/prinet"
)
_DEFAULT_OWNERSHIP = Path("tools/wp001_ownership.json")
_EVIDENCE_OUTPUT = Path("DOCS/baselines")
_EXCLUDED_FILES = frozenset({".coverage", "coverage.xml"})
_EXCLUDED_DIRECTORIES = frozenset(
    {
        ".aicb",
        ".benchmarks",
        ".git",
        ".hypothesis",
        ".mypy_cache",
        ".pytest_cache",
        ".ruff_cache",
        ".tox",
        ".venv",
        "__pycache__",
        "build",
        "dist",
        "target",
        "venv",
    }
)
_REQUIRED_WORKFLOWS = (
    "gpu.yml",
    "parity.yml",
    "python.yml",
    "release.yml",
    "repro.yml",
    "rust.yml",
)
_TEXT_SUFFIXES = frozenset(
    {
        "",
        ".cff",
        ".css",
        ".gitignore",
        ".html",
        ".json",
        ".md",
        ".py",
        ".pyi",
        ".rs",
        ".rst",
        ".toml",
        ".txt",
        ".yml",
        ".yaml",
    }
)
_SESSION_ROW = re.compile(
    r"^\|\s*(?P<sequence>\d{4}[A-H]?)\s*\|\s*(?P<phase>\d+)\s*\|"
    r"\s*(?P<unit>[^|]+?)\s*\|\s*(?P<type>[^|]+?)\s*\|"
    r"\s*\[[^]]+\]\((?P<target>[^)]+)\)\s*\|"
    r"\s*(?P<status>[^|]+?)\s*\|$"
)
_WP_ID = re.compile(r"^WP-(\d{3})$")

# Plan amendments #31 and #32 add planned two-part sub-sessions inserted
# between existing integer sessions with two-part identifiers, without
# renumbering the gap-free 0001..0198 integer sequence (TRACEABILITY invariant
# 4 is preserved). This is the same additive-by-amendment principle already
# used for the EA/EMA global sessions, applied inside the phase order.
#   #32: WP-036 S1 executed as five coding sub-passes 0141A..0141E.
#   #31: WP-036 split into WP-036 / WP-036B / WP-036C; WP-036B/WP-036C occupy
#        eight mini-cycle sub-sessions 0144A..0144H.
_PLANNED_INTEGER_COUNT = 198
# Each block is (anchor_integer_session, ordered_two_part_sub_session_ids). The
# block's rows appear in the register contiguously immediately after the anchor
# row. Blocks are listed in register order.
#   #32: WP-036 S1 executed as five coding sub-passes 0141A..0141E.
#   #31: WP-036B/WP-036C occupy eight mini-cycle sub-sessions 0144A..0144H.
_SUBSESSION_BLOCKS = (
    ("0141", tuple(f"0141{letter}" for letter in "ABCDE")),
    ("0144", tuple(f"0144{letter}" for letter in "ABCDEFGH")),
)
_SUBSESSION_SEQUENCES = tuple(
    sequence for _, block in _SUBSESSION_BLOCKS for sequence in block
)
_PLANNED_SESSION_COUNT = _PLANNED_INTEGER_COUNT + len(_SUBSESSION_SEQUENCES)


class BaselineValidationError(ValueError):
    """Report an invalid or incomplete WP-001 baseline contract."""


@dataclass(frozen=True)
class _ModuleApi:
    module: str
    source_path: str
    is_package: bool
    symbols: tuple[str, ...]
    symbol_source: str
    definitions: frozenset[str]
    imports: dict[str, tuple[str, str]]


def _read_toml(path: Path) -> dict[str, Any]:
    with path.open("rb") as stream:
        return tomllib.load(stream)


def _module_identity(path: Path, archive: Path) -> tuple[str, bool]:
    relative = path.relative_to(archive).with_suffix("")
    parts = list(relative.parts)
    is_package = parts[-1] == "__init__"
    if is_package:
        parts.pop()
    return ".".join(("prinet", *parts)), is_package


def _assignment_names(node: ast.Assign | ast.AnnAssign) -> list[str]:
    targets = node.targets if isinstance(node, ast.Assign) else [node.target]
    return [target.id for target in targets if isinstance(target, ast.Name)]


def _literal_all(node: ast.AST, source_path: str) -> tuple[str, ...]:
    try:
        value = ast.literal_eval(node)
    except (TypeError, ValueError) as exc:
        raise BaselineValidationError(
            f"{source_path}: __all__ must be a static list or tuple of strings"
        ) from exc
    if not isinstance(value, (list, tuple)) or not all(
        isinstance(item, str) for item in value
    ):
        raise BaselineValidationError(
            f"{source_path}: __all__ must be a static list or tuple of strings"
        )
    if len(value) != len(set(value)):
        raise BaselineValidationError(f"{source_path}: __all__ contains duplicates")
    return tuple(sorted(value))


def _resolve_import_module(
    current_module: str,
    is_package: bool,
    imported_module: str | None,
    level: int,
) -> str:
    if level == 0:
        if imported_module is None:
            raise BaselineValidationError(
                f"{current_module}: absolute import has no module"
            )
        return imported_module
    base = current_module.split(".")
    if not is_package:
        base.pop()
    ascents = level - 1
    if ascents > len(base):
        raise BaselineValidationError(
            f"{current_module}: relative import escapes the archive package"
        )
    if ascents:
        base = base[:-ascents]
    if imported_module:
        base.extend(imported_module.split("."))
    return ".".join(base)


def _parse_module(path: Path, archive: Path, root: Path) -> _ModuleApi:
    module, is_package = _module_identity(path, archive)
    source_path = path.relative_to(root).as_posix()
    tree = ast.parse(path.read_text(encoding="utf-8"), filename=source_path)
    definitions: set[str] = set()
    imports: dict[str, tuple[str, str]] = {}
    explicit_all: tuple[str, ...] | None = None
    for node in tree.body:
        if isinstance(node, (ast.ClassDef, ast.FunctionDef, ast.AsyncFunctionDef)):
            definitions.add(node.name)
        elif isinstance(node, (ast.Assign, ast.AnnAssign)):
            names = _assignment_names(node)
            definitions.update(names)
            if "__all__" in names:
                value = node.value
                if value is None:
                    raise BaselineValidationError(
                        f"{source_path}: __all__ has no value"
                    )
                explicit_all = _literal_all(value, source_path)
        elif isinstance(node, ast.ImportFrom):
            origin_module = _resolve_import_module(
                module, is_package, node.module, node.level
            )
            for alias in node.names:
                if alias.name == "*":
                    raise BaselineValidationError(
                        f"{source_path}: wildcard imports cannot be traced statically"
                    )
                imports[alias.asname or alias.name] = (origin_module, alias.name)
    symbols = (
        explicit_all
        if explicit_all is not None
        else tuple(sorted(name for name in definitions if not name.startswith("_")))
    )
    return _ModuleApi(
        module=module,
        source_path=source_path,
        is_package=is_package,
        symbols=symbols,
        symbol_source="__all__" if explicit_all is not None else "declaration",
        definitions=frozenset(definitions),
        imports=imports,
    )


def _discover_api(root: Path) -> dict[str, _ModuleApi]:
    archive = root / _ARCHIVE
    if not archive.is_dir():
        raise BaselineValidationError(f"archive package is missing: {_ARCHIVE}")
    records: dict[str, _ModuleApi] = {}
    for path in sorted(archive.rglob("*.py")):
        record = _parse_module(path, archive, root)
        if record.module in records:
            raise BaselineValidationError(
                f"duplicate archived module identity: {record.module}"
            )
        records[record.module] = record
    return records


def _frozen_api_symbols(path: Path) -> frozenset[str]:
    tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    for node in tree.body:
        value: ast.AST | None = None
        if isinstance(node, ast.Assign) and "FROZEN_PUBLIC_API" in _assignment_names(
            node
        ):
            value = node.value
        elif (
            isinstance(node, ast.AnnAssign)
            and isinstance(node.target, ast.Name)
            and node.target.id == "FROZEN_PUBLIC_API"
        ):
            value = node.value
        if value is None:
            continue
        if isinstance(value, ast.Call) and len(value.args) == 1:
            value = value.args[0]
        symbols = _literal_all(value, str(path))
        return frozenset(symbols)
    raise BaselineValidationError(f"{path}: FROZEN_PUBLIC_API is missing")


def _resolve_symbol_origin(
    records: dict[str, _ModuleApi],
    module: str,
    symbol: str,
    trail: tuple[tuple[str, str], ...] = (),
) -> tuple[str, str]:
    key = (module, symbol)
    if key in trail:
        chain = " -> ".join(f"{item[0]}.{item[1]}" for item in (*trail, key))
        raise BaselineValidationError(f"cyclic archived re-export: {chain}")
    record = records.get(module)
    if record is None:
        raise BaselineValidationError(
            f"{module}.{symbol}: re-export source module is absent from archive"
        )
    if symbol in record.definitions:
        return key
    imported = record.imports.get(symbol)
    if imported is None:
        raise BaselineValidationError(
            f"{module}.{symbol}: public symbol has no static definition or import"
        )
    return _resolve_symbol_origin(records, *imported, (*trail, key))


def _load_ownership(path: Path) -> dict[str, Any]:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise BaselineValidationError(
            f"cannot load ownership map {path}: {exc}"
        ) from exc
    if payload.get("schema_version") != 1:
        raise BaselineValidationError("ownership map schema_version must equal 1")
    if not isinstance(payload.get("modules"), dict) or not isinstance(
        payload.get("symbols"), dict
    ):
        raise BaselineValidationError(
            "ownership map requires object-valued modules and symbols"
        )
    return payload


def _future_wp_ids(root: Path) -> set[str]:
    identifiers: set[str] = set()
    for path in (root / "DOCS/sessions").glob("phase-*/*-s1-*.md"):
        match = re.search(r"-wp(\d{3})-s1-", path.name)
        if match:
            identifiers.add(f"WP-{match.group(1)}")
    return identifiers


def _validate_owner(
    owner: object,
    label: str,
    future_wps: set[str],
) -> tuple[str, str]:
    if not isinstance(owner, dict):
        raise BaselineValidationError(f"{label}: ownership entry must be an object")
    future_wp = owner.get("future_wp")
    basis = owner.get("basis")
    match = _WP_ID.fullmatch(future_wp) if isinstance(future_wp, str) else None
    if match is None or future_wp == "WP-001" or future_wp not in future_wps:
        raise BaselineValidationError(
            f"{label}: future WP must be an approved post-WP-001 work package, "
            f"got {future_wp!r}"
        )
    if not isinstance(basis, str) or not basis.strip():
        raise BaselineValidationError(f"{label}: ownership basis must be non-empty")
    return future_wp, basis


def _validate_root_path(path: Path) -> Path:
    """Resolve a repository root and ensure it is an existing directory."""
    resolved = path.resolve()
    if not resolved.is_dir():
        raise BaselineValidationError(f"root is not a directory: {resolved}")
    return resolved


def _validate_ownership_path(path: Path) -> Path:
    """Resolve an alternate ownership file and ensure it exists."""
    resolved = path.resolve()
    if not resolved.is_file():
        raise BaselineValidationError(f"ownership file not found: {resolved}")
    return resolved


def collect_api_traceability(
    root: Path,
    ownership_path: Path | None = None,
) -> dict[str, Any]:
    """Collect complete static module and public-symbol ownership traceability."""
    root = _validate_root_path(root)
    records = _discover_api(root)
    if ownership_path is not None:
        ownership_file = _validate_ownership_path(ownership_path)
    else:
        ownership_file = root / _DEFAULT_OWNERSHIP
    ownership = _load_ownership(ownership_file)
    module_owners: dict[str, object] = ownership["modules"]
    symbol_owners: dict[str, object] = ownership["symbols"]
    missing = sorted(set(records) - set(module_owners))
    extra = sorted(set(module_owners) - set(records))
    if missing:
        raise BaselineValidationError(f"unowned module(s): {', '.join(missing)}")
    if extra:
        raise BaselineValidationError(
            f"ownership map has unknown module(s): {', '.join(extra)}"
        )
    future_wps = _future_wp_ids(root)
    modules: list[dict[str, str]] = []
    for module, record in sorted(records.items()):
        future_wp, basis = _validate_owner(
            module_owners[module], f"module {module}", future_wps
        )
        modules.append(
            {
                "module": module,
                "source_path": record.source_path,
                "future_wp": future_wp,
                "basis": basis,
            }
        )
    definition_keys = {
        f"{module}.{symbol}"
        for module, record in records.items()
        for symbol in record.definitions
    }
    unknown_overrides = sorted(set(symbol_owners) - definition_keys)
    if unknown_overrides:
        raise BaselineValidationError(
            "ownership map has unknown symbol override(s): "
            + ", ".join(unknown_overrides)
        )
    for key, owner in sorted(symbol_owners.items()):
        _validate_owner(owner, f"symbol {key}", future_wps)
    symbols: list[dict[str, str]] = []
    for module, record in sorted(records.items()):
        for symbol in record.symbols:
            origin_module, origin_symbol = _resolve_symbol_origin(
                records, module, symbol
            )
            origin_key = f"{origin_module}.{origin_symbol}"
            owner = symbol_owners.get(origin_key, module_owners[origin_module])
            future_wp, basis = _validate_owner(
                owner, f"symbol {module}.{symbol}", future_wps
            )
            symbols.append(
                {
                    "module": module,
                    "symbol": symbol,
                    "source_path": record.source_path,
                    "discovery": record.symbol_source,
                    "definition": origin_key,
                    "future_wp": future_wp,
                    "basis": basis,
                }
            )
    symbols.sort(key=lambda row: (row["module"], row["symbol"]))
    top_level_symbols = frozenset(records["prinet"].symbols)
    frozen_path = root / _ARCHIVE / "_deprecation.py"
    frozen_symbols = (
        _frozen_api_symbols(frozen_path) if frozen_path.is_file() else frozenset()
    )
    missing_frozen = sorted(frozen_symbols - top_level_symbols)
    if missing_frozen:
        raise BaselineValidationError(
            "archived FROZEN_PUBLIC_API symbols missing from prinet.__all__: "
            + ", ".join(missing_frozen)
        )
    return {
        "schema_version": 1,
        "extraction_policy": (
            "Literal __all__ when present; otherwise public top-level classes, "
            "functions, and assignments. Re-exports resolve statically by AST."
        ),
        "module_count": len(modules),
        "symbol_count": len(symbols),
        "top_level_public_symbol_count": len(top_level_symbols),
        "frozen_public_symbol_count": len(frozen_symbols),
        "top_level_symbols_not_frozen": len(top_level_symbols - frozen_symbols),
        "modules": modules,
        "symbols": symbols,
    }


def _python_string_assignment(path: Path, name: str) -> str | None:
    tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    for node in tree.body:
        if isinstance(node, ast.Assign) and name in _assignment_names(node):
            try:
                value = ast.literal_eval(node.value)
            except (TypeError, ValueError):
                return None
            return value if isinstance(value, str) else None
    return None


def _cff_scalar(path: Path, key: str) -> str | None:
    pattern = re.compile(rf"^{re.escape(key)}:\s*[\"']?([^\"'\r\n]+?)[\"']?\s*$")
    for line in path.read_text(encoding="utf-8").splitlines():
        match = pattern.fullmatch(line)
        if match:
            return match.group(1)
    return None


def _workspace_inherited(package: dict[str, Any], field: str) -> bool:
    value = package.get(field)
    return isinstance(value, dict) and value.get("workspace") is True


def _workflow_python_versions(path: Path) -> set[str]:
    text = path.read_text(encoding="utf-8")
    match = re.search(r"python-version:\s*\[([^]]+)\]", text)
    if match is None:
        return set()
    return set(re.findall(r"[\"'](3\.\d+)[\"']", match.group(1)))


def validate_metadata(root: Path) -> list[str]:
    """Validate cross-file project, packaging, toolchain, and CI metadata."""
    root = _validate_root_path(root)
    errors: list[str] = []
    required = [
        "Cargo.toml",
        "pyproject.toml",
        "CITATION.cff",
        "LICENSE",
        "rust-toolchain.toml",
        "python/prin/__init__.py",
    ]
    missing = [relative for relative in required if not (root / relative).is_file()]
    if missing:
        return [
            f"required metadata file is missing: {relative}" for relative in missing
        ]
    cargo = _read_toml(root / "Cargo.toml")
    pyproject = _read_toml(root / "pyproject.toml")
    workspace_package = cargo.get("workspace", {}).get("package", {})
    project = pyproject.get("project", {})
    versions = {
        "Cargo.toml": workspace_package.get("version"),
        "pyproject.toml": project.get("version"),
        "python/prin/__init__.py": _python_string_assignment(
            root / "python/prin/__init__.py", "__version__"
        ),
        "CITATION.cff": _cff_scalar(root / "CITATION.cff", "version"),
    }
    if len(set(versions.values())) != 1 or None in versions.values():
        details = ", ".join(f"{name}={value}" for name, value in versions.items())
        errors.append(f"project version mismatch: {details}")
    pyproject_license = project.get("license", {})
    licenses = {
        "Cargo.toml": workspace_package.get("license"),
        "pyproject.toml": (
            pyproject_license.get("text")
            if isinstance(pyproject_license, dict)
            else pyproject_license
        ),
        "CITATION.cff": _cff_scalar(root / "CITATION.cff", "license"),
    }
    if set(licenses.values()) != {"MIT"}:
        details = ", ".join(f"{name}={value}" for name, value in licenses.items())
        errors.append(f"project license mismatch: {details}")
    if not (root / "LICENSE").read_text(encoding="utf-8").startswith("MIT License"):
        errors.append("LICENSE does not contain the MIT license text")
    urls = project.get("urls", {})
    repositories = {
        "Cargo.toml": workspace_package.get("repository"),
        "pyproject.toml": urls.get("Repository"),
        "CITATION.cff": _cff_scalar(root / "CITATION.cff", "repository-code"),
    }
    if len(set(repositories.values())) != 1 or None in repositories.values():
        details = ", ".join(f"{name}={value}" for name, value in repositories.items())
        errors.append(f"repository URL mismatch: {details}")
    members = cargo.get("workspace", {}).get("members", [])
    if not isinstance(members, list) or not all(
        isinstance(member, str) for member in members
    ):
        errors.append("Cargo workspace members must be a list of paths")
        members = []
    expected_fields = (
        "version",
        "edition",
        "rust-version",
        "license",
        "authors",
        "repository",
    )
    for member in members:
        manifest_path = root / member / "Cargo.toml"
        relative_manifest = f"{member}/Cargo.toml"
        if not manifest_path.is_file():
            errors.append(f"workspace member manifest is missing: {relative_manifest}")
            continue
        manifest = _read_toml(manifest_path)
        package = manifest.get("package", {})
        expected_name = Path(member).name
        if package.get("name") != expected_name:
            errors.append(
                f"{relative_manifest}: package name {package.get('name')!r} "
                f"does not match directory {expected_name!r}"
            )
        for field in expected_fields:
            if not _workspace_inherited(package, field):
                errors.append(
                    f"{relative_manifest}: package.{field} must inherit "
                    "workspace metadata"
                )
    maturin = pyproject.get("tool", {}).get("maturin", {})
    manifest_path = maturin.get("manifest-path")
    if manifest_path != "crates/prin-py/Cargo.toml":
        errors.append(
            "pyproject.toml: maturin manifest-path must be crates/prin-py/Cargo.toml"
        )
    elif "crates/prin-py" not in members:
        errors.append("maturin manifest is not a Cargo workspace member")
    if maturin.get("python-source") != "python":
        errors.append("pyproject.toml: maturin python-source must equal 'python'")
    if maturin.get("module-name") != "prin._prin_core":
        errors.append(
            "pyproject.toml: maturin module-name must equal 'prin._prin_core'"
        )
    py_crate_path = root / "crates/prin-py/Cargo.toml"
    if py_crate_path.is_file():
        py_crate = _read_toml(py_crate_path)
        if py_crate.get("lib", {}).get("name") != "_prin_core":
            errors.append("prin-py library name must equal '_prin_core'")
        pyo3 = py_crate.get("dependencies", {}).get("pyo3", {})
        features = pyo3.get("features", []) if isinstance(pyo3, dict) else []
        if "abi3-py311" not in features:
            errors.append("prin-py pyo3 dependency must enable abi3-py311")
    classifiers = project.get("classifiers", [])
    classifier_versions = {
        match.group(1)
        for classifier in classifiers
        if isinstance(classifier, str)
        and (
            match := re.fullmatch(
                r"Programming Language :: Python :: (3\.\d+)", classifier
            )
        )
    }
    expected_python_versions = {"3.11", "3.12", "3.13"}
    if project.get("requires-python") != ">=3.11":
        errors.append("pyproject.toml: requires-python must equal '>=3.11'")
    if classifier_versions != expected_python_versions:
        errors.append(
            "pyproject.toml Python classifiers must equal 3.11, 3.12, and 3.13"
        )
    python_workflow = root / ".github/workflows/python.yml"
    if python_workflow.is_file():
        ci_versions = _workflow_python_versions(python_workflow)
        if ci_versions != expected_python_versions:
            errors.append(
                "python.yml test matrix must equal Python 3.11, 3.12, and 3.13"
            )
    workflows = root / ".github/workflows"
    for workflow in _REQUIRED_WORKFLOWS:
        if not (workflows / workflow).is_file():
            errors.append(f"required CI workflow is missing: {workflow}")
    toolchain = _read_toml(root / "rust-toolchain.toml").get("toolchain", {})
    if toolchain.get("channel") != "stable":
        errors.append("rust-toolchain.toml channel must equal 'stable'")
    components = set(toolchain.get("components", []))
    required = {"rustfmt", "clippy"}
    allowed = {"rustfmt", "clippy", "llvm-tools", "llvm-tools-preview"}
    if not required.issubset(components) or not components.issubset(allowed):
        errors.append(
            "rust-toolchain.toml components must include rustfmt and clippy; "
            "optional llvm-tools or llvm-tools-preview"
        )
    return errors


def _numbered_briefs(
    sessions: Path,
) -> tuple[dict[str, Path], list[str], int]:
    briefs: dict[str, Path] = {}
    duplicates: list[str] = []
    physical_count = 0
    for path in sessions.glob("phase-*/*.md"):
        match = re.match(r"^(\d{4}[A-H]?)-", path.name)
        if match:
            physical_count += 1
            sequence = match.group(1)
            if sequence in briefs:
                duplicates.append(sequence)
            else:
                briefs[sequence] = path
    return briefs, duplicates, physical_count


def _normalize_unit(value: str) -> str:
    return re.sub(r"\s+", "", value)


def _linked_target(line: str, brief: Path) -> Path | None:
    match = re.search(r"\[[^]]+\]\(([^)]+)\)", line)
    return (brief.parent / match.group(1)).resolve() if match else None


def validate_session_plan(root: Path) -> list[str]:
    """Validate the complete numbered session register and link structure."""
    root = _validate_root_path(root)
    sessions = root / "DOCS/sessions"
    register_path = sessions / "SESSION_REGISTER.md"
    if not register_path.is_file():
        return ["session register is missing: DOCS/sessions/SESSION_REGISTER.md"]
    rows: list[dict[str, str]] = []
    for line in register_path.read_text(encoding="utf-8").splitlines():
        match = _SESSION_ROW.fullmatch(line)
        if match:
            rows.append(match.groupdict())
    errors: list[str] = []
    expected_integer_sequences = [
        f"{number:04d}" for number in range(1, _PLANNED_INTEGER_COUNT + 1)
    ]
    row_sequences = [row["sequence"] for row in rows]
    integer_sequences = [seq for seq in row_sequences if seq.isdigit()]
    subsession_sequences = [seq for seq in row_sequences if not seq.isdigit()]
    if len(rows) != _PLANNED_SESSION_COUNT:
        errors.append(
            f"session register must contain {_PLANNED_SESSION_COUNT} rows "
            f"({_PLANNED_INTEGER_COUNT} integer + {len(_SUBSESSION_SEQUENCES)} "
            f"amendment-inserted sub-sessions), found {len(rows)}"
        )
    if integer_sequences != expected_integer_sequences:
        errors.append(
            "session register integer sequence must be unique and gap-free "
            f"0001..{_PLANNED_INTEGER_COUNT:04d}"
        )
    if subsession_sequences != list(_SUBSESSION_SEQUENCES):
        errors.append(
            "amendment-inserted sub-sessions must be exactly "
            f"{', '.join(_SUBSESSION_SEQUENCES)} in order"
        )
    else:
        expected_row_order: list[str] = []
        for sequence in expected_integer_sequences:
            expected_row_order.append(sequence)
            for anchor, block in _SUBSESSION_BLOCKS:
                if sequence == anchor:
                    expected_row_order.extend(block)
        if row_sequences != expected_row_order:
            anchors = ", ".join(anchor for anchor, _ in _SUBSESSION_BLOCKS)
            errors.append(
                "amendment-inserted sub-sessions must appear contiguously "
                f"right after their anchor session ({anchors})"
            )
    briefs, duplicate_sequences, physical_count = _numbered_briefs(sessions)
    if duplicate_sequences:
        errors.append(
            "duplicate session brief sequence IDs: "
            + ", ".join(sorted(set(duplicate_sequences)))
        )
    if physical_count != _PLANNED_SESSION_COUNT:
        errors.append(
            f"expected {_PLANNED_SESSION_COUNT} numbered session briefs, found "
            f"{physical_count} physical numbered session briefs"
        )
    if len(briefs) != _PLANNED_SESSION_COUNT:
        errors.append(
            f"expected {_PLANNED_SESSION_COUNT} unique session brief IDs, "
            f"found {len(briefs)}"
        )
    allowed_statuses = {"PLANNED", "READY", "IN_PROGRESS", "BLOCKED", "COMPLETE"}
    for index, row in enumerate(rows):
        sequence = row["sequence"]
        target = (sessions / row["target"]).resolve()
        if not target.is_file():
            errors.append(
                f"session {sequence}: register target does not exist: {row['target']}"
            )
            continue
        if target.name != briefs.get(sequence, Path()).name:
            errors.append(
                f"session {sequence}: register target does not match numbered brief"
            )
        lines = target.read_text(encoding="utf-8").splitlines()
        if not lines or not lines[0].startswith(f"# Session {sequence} "):
            errors.append(f"session {sequence}: heading does not match sequence")
        metadata: dict[str, str] = {}
        for line in lines[:12]:
            match = re.match(r"^\*\*(.+?):\*\*\s*(.+?)\s*$", line)
            if match:
                metadata[match.group(1)] = match.group(2).rstrip()
        status_value = metadata.get("Status", "")
        status_match = re.match(
            r"^(PLANNED|READY|IN_PROGRESS|BLOCKED|COMPLETE)\b", status_value
        )
        brief_status = status_match.group(1) if status_match else status_value
        if brief_status != row["status"]:
            errors.append(f"session {sequence}: brief/register status mismatch")
        if _normalize_unit(metadata.get("Execution unit", "")) != _normalize_unit(
            row["unit"]
        ):
            errors.append(f"session {sequence}: brief/register execution unit mismatch")
        if metadata.get("Session type") != row["type"]:
            errors.append(f"session {sequence}: brief/register session type mismatch")
        if row["status"] not in allowed_statuses:
            errors.append(f"session {sequence}: invalid status {row['status']!r}")
        predecessor_line = next(
            (line for line in lines if line.startswith("**Predecessor:**")), ""
        )
        successor_line = next(
            (line for line in lines if line.startswith("**Successor:**")), ""
        )
        predecessor = _linked_target(predecessor_line, target)
        successor = _linked_target(successor_line, target)
        if index == 0:
            if (
                predecessor is not None
                or "Project execution start" not in predecessor_line
            ):
                errors.append("session 0001 must start at Project execution start")
        else:
            expected = (sessions / rows[index - 1]["target"]).resolve()
            if predecessor != expected:
                previous_sequence = rows[index - 1]["sequence"]
                errors.append(
                    f"session {sequence}: predecessor is not session "
                    f"{previous_sequence}"
                )
        if index == len(rows) - 1:
            if successor is not None or "Project complete" not in successor_line:
                errors.append("session 0198 must end at Project complete")
        else:
            expected = (sessions / rows[index + 1]["target"]).resolve()
            if successor != expected:
                next_sequence = rows[index + 1]["sequence"]
                errors.append(
                    f"session {sequence}: successor is not session {next_sequence}"
                )
    return errors


def _count_text_lines(path: Path) -> int:
    content = path.read_bytes()
    return content.count(b"\n") + int(bool(content) and not content.endswith(b"\n"))


def _active_project_files(root: Path) -> list[Path]:
    files: list[Path] = []
    archive_root = (root / "DOCS/archive and reference from PRINet 3.0").resolve()
    evidence_root = (root / _EVIDENCE_OUTPUT).resolve()
    for current, directory_names, file_names in os.walk(root):
        current_path = Path(current)
        directory_names[:] = sorted(
            name
            for name in directory_names
            if name not in _EXCLUDED_DIRECTORIES
            and (current_path / name).resolve() not in {archive_root, evidence_root}
        )
        for file_name in sorted(file_names):
            if file_name in _EXCLUDED_FILES or file_name.startswith(".coverage."):
                continue
            files.append(current_path / file_name)
    return sorted(files, key=lambda path: path.relative_to(root).as_posix())


def _file_inventory(root: Path, files: list[Path]) -> dict[str, Any]:
    suffixes: Counter[str] = Counter()
    top_level: Counter[str] = Counter()
    text_lines = 0
    text_files = 0
    total_bytes = 0
    for path in files:
        relative = path.relative_to(root)
        suffixes[path.suffix.lower() or "<none>"] += 1
        top_level[relative.parts[0]] += 1
        total_bytes += path.stat().st_size
        if path.suffix.lower() in _TEXT_SUFFIXES or not path.suffix:
            text_lines += _count_text_lines(path)
            text_files += 1
    return {
        "file_count": len(files),
        "total_bytes": total_bytes,
        "text_file_count": text_files,
        "text_line_count": text_lines,
        "files_by_suffix": dict(sorted(suffixes.items())),
        "files_by_top_level": dict(sorted(top_level.items())),
    }


def collect_repository_inventory(root: Path) -> dict[str, Any]:
    """Collect a deterministic, archive-separated repository-state inventory."""
    root = _validate_root_path(root)
    cargo = _read_toml(root / "Cargo.toml")
    pyproject = _read_toml(root / "pyproject.toml")
    active_files = _active_project_files(root)
    archive_root = root / "DOCS/archive and reference from PRINet 3.0/PRINet-3.0.0-main"
    archive_files = sorted(path for path in archive_root.rglob("*") if path.is_file())
    archive_python = sorted((archive_root / "src/prinet").rglob("*.py"))
    workflows = sorted(path.name for path in (root / ".github/workflows").glob("*.yml"))
    members = cargo.get("workspace", {}).get("members", [])
    workspace_members = []
    for member in members:
        manifest = _read_toml(root / member / "Cargo.toml")
        workspace_members.append(
            {
                "path": member,
                "package": manifest.get("package", {}).get("name"),
                "dependencies": sorted(manifest.get("dependencies", {})),
                "features": sorted(manifest.get("features", {})),
            }
        )
    python_modules = sorted(
        path.relative_to(root).as_posix()
        for path in (root / "python/prin").rglob("*.py")
    )
    test_files = sorted(
        path.relative_to(root).as_posix() for path in (root / "tests").glob("test_*.py")
    )
    session_briefs, _, physical_brief_count = _numbered_briefs(root / "DOCS/sessions")
    project = pyproject.get("project", {})
    return {
        "schema_version": 1,
        "scope": (
            "Active PRIN files excluding build/cache/VCS directories; archived "
            "PRINet 3.0 is measured separately and never executed."
        ),
        "excluded_directories": sorted(_EXCLUDED_DIRECTORIES),
        "excluded_files": sorted(_EXCLUDED_FILES),
        "excluded_paths": [_EVIDENCE_OUTPUT.as_posix()],
        "project": {
            "name": project.get("name"),
            "version": project.get("version"),
            "license": project.get("license", {}).get("text"),
            "requires_python": project.get("requires-python"),
            "rust_channel": _read_toml(root / "rust-toolchain.toml")
            .get("toolchain", {})
            .get("channel"),
        },
        "active_repository": _file_inventory(root, active_files),
        "archive": {
            "file_count": len(archive_files),
            "total_bytes": sum(path.stat().st_size for path in archive_files),
            "python_modules": len(archive_python),
            "python_line_count": sum(
                _count_text_lines(path) for path in archive_python
            ),
        },
        "workspace": {
            "member_count": len(workspace_members),
            "members": workspace_members,
        },
        "python": {
            "module_count": len(python_modules),
            "modules": python_modules,
        },
        "tests": {
            "pytest_file_count": len(test_files),
            "pytest_files": test_files,
        },
        "ci": {
            "workflow_count": len(workflows),
            "workflows": workflows,
        },
        "session_plan": {
            "numbered_briefs": physical_brief_count,
            "unique_sequence_ids": len(session_briefs),
            "first": min(session_briefs) if session_briefs else None,
            "last": max(session_briefs) if session_briefs else None,
        },
    }


def _escape_markdown(value: object) -> str:
    return str(value).replace("|", "\\|").replace("\n", " ")


def render_traceability_markdown(traceability: dict[str, Any]) -> str:
    """Render a complete human-readable API ownership matrix."""
    lines = [
        "# WP-001 PRINet 3.0 API traceability",
        "",
        "This matrix is generated by static AST analysis. Archived code is never",
        "imported or executed. A literal `__all__` is authoritative when present;",
        "otherwise public top-level declarations are included. Re-exports resolve",
        "to their defining module before ownership is assigned.",
        "",
        "## Summary",
        "",
        f"- Archived modules: **{traceability['module_count']}**",
        f"- Module-symbol rows: **{traceability['symbol_count']}**",
        "- Canonical top-level `prinet.__all__` symbols: "
        f"**{traceability['top_level_public_symbol_count']}**",
        "- Symbols in archived `FROZEN_PUBLIC_API`: "
        f"**{traceability['frozen_public_symbol_count']}**",
        "- Later top-level symbols absent from the frozen set: "
        f"**{traceability['top_level_symbols_not_frozen']}**",
        "",
        "## Module ownership",
        "",
        "| Module | Archived source | Future WP | Basis |",
        "|---|---|---|---|",
    ]
    for row in traceability["modules"]:
        lines.append(
            "| "
            + " | ".join(
                _escape_markdown(row[key])
                for key in ("module", "source_path", "future_wp", "basis")
            )
            + " |"
        )
    lines.extend(
        [
            "",
            "## Public symbol ownership",
            "",
            "| Exporting module | Symbol | Static definition | Discovery | "
            "Future WP | Basis |",
            "|---|---|---|---|---|---|",
        ]
    )
    for row in traceability["symbols"]:
        lines.append(
            "| "
            + " | ".join(
                _escape_markdown(row[key])
                for key in (
                    "module",
                    "symbol",
                    "definition",
                    "discovery",
                    "future_wp",
                    "basis",
                )
            )
            + " |"
        )
    lines.append("")
    return "\n".join(lines)


def validate_baseline(
    root: Path,
    ownership_path: Path | None = None,
) -> list[str]:
    """Run all WP-001 consistency and traceability validation checks."""
    errors = [*validate_metadata(root), *validate_session_plan(root)]
    try:
        traceability = collect_api_traceability(root, ownership_path)
    except BaselineValidationError as exc:
        errors.append(str(exc))
    else:
        if traceability["module_count"] != 43:
            errors.append(
                "archived PRINet module contract changed: expected 43, found "
                f"{traceability['module_count']}"
            )
        if traceability["top_level_public_symbol_count"] != 172:
            errors.append(
                "archived top-level API contract changed: expected 172, found "
                f"{traceability['top_level_public_symbol_count']}"
            )
        if traceability["symbol_count"] != 657:
            errors.append(
                "archived module-symbol contract changed: expected 657, found "
                f"{traceability['symbol_count']}"
            )
    return sorted(set(errors))


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--root",
        type=Path,
        default=Path(__file__).resolve().parents[1],
        help="PRIN repository root (default: inferred from this script)",
    )
    parser.add_argument(
        "--ownership",
        type=Path,
        default=None,
        help="alternate ownership JSON used for validation or rendering",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)
    subparsers.add_parser("check", help="validate metadata, sessions, and ownership")
    subparsers.add_parser("inventory", help="emit repository inventory JSON")
    subparsers.add_parser("traceability", help="emit API traceability Markdown")
    return parser


def main(argv: list[str] | None = None) -> int:
    """Run WP-001 baseline validation or emit deterministic evidence."""
    arguments = _parser().parse_args(argv)
    try:
        root = _validate_root_path(arguments.root)
        ownership = None
        if arguments.ownership is not None:
            ownership = _validate_ownership_path(arguments.ownership)
        if arguments.command == "check":
            errors = validate_baseline(root, ownership)
            if errors:
                for error in errors:
                    print(f"ERROR: {error}", file=sys.stderr)
                return 1
            print("WP-001 baseline validation passed.")
            return 0
        if arguments.command == "inventory":
            print(
                json.dumps(collect_repository_inventory(root), indent=2, sort_keys=True)
            )
            return 0
        if arguments.command == "traceability":
            print(
                render_traceability_markdown(collect_api_traceability(root, ownership)),
                end="",
            )
            return 0
    except (BaselineValidationError, OSError, tomllib.TOMLDecodeError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1
    raise AssertionError(f"unhandled command: {arguments.command}")


if __name__ == "__main__":
    raise SystemExit(main())
