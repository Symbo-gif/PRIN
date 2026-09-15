"""Sphinx documentation-surface regression tests (WP-037 S1, session ``0145``).

The Sphinx build is gated by ``sphinx-build -W`` in CI, but several failures it
catches are expensive to discover there and easy to prevent here:

* an ``api/*.rst`` page dropped from every toctree (Sphinx warns, and the page
  silently disappears from navigation);
* a ``prin`` submodule with no ``automodule`` target anywhere, so its public
  symbols are undocumented — Documentation Standards §2.2 requires 100 % of
  public symbols;
* the same object autodoc'd on two *indexed* pages, which is a "duplicate object
  description" warning. ``:no-index:`` on an ``automodule`` suppresses the class
  description but **not** the descriptions autodoc generates for that class's
  ``@dataclass`` fields, so a re-exporting facade must not autodoc members at
  all. This is the arrangement ``DOCS/sphinx/conf.py`` documents;
* ``conf.py``'s ``release`` drifting away from ``pyproject.toml``'s version,
  which happened once already (``release = "0.1.0"`` against a ``0.3.0``
  distribution) and is why ``conf.py`` now reads the version from
  ``pyproject.toml``.
"""

from __future__ import annotations

import ast
import importlib
import pkgutil
import re
import tomllib
from pathlib import Path

import prin
import pytest

ROOT = Path(__file__).resolve().parents[1]
SPHINX = ROOT / "DOCS" / "sphinx"
API = SPHINX / "api"

#: The three pages the frozen ported contract requires by name
#: (``tests/test_acceptance_y4q3.py::TestSphinxDocs::test_api_rst_files_exist``).
CONTRACT_API_PAGES = ("core.rst", "nn.rst", "utils.rst")

#: Modules deliberately not autodoc'd, with the reason. ``prin._prin_core`` is
#: the compiled PyO3 extension: autodoc renders PyO3 classes poorly and its
#: authoritative typed surface is the shipped ``python/prin/_prin_core.pyi``.
#: The other three are governance internals described in prose on
#: ``api/compat.rst`` and in ``DOCS/experiments/0141-wp036-s1-dd-dispositions.md``.
NOT_AUTODOCED = {
    "prin._prin_core": "compiled PyO3 extension; typed by python/prin/_prin_core.pyi",
    "prin._ort": "Phase 0 ONNX Runtime probe; described in prose on api/compat.rst",
    "prin._phase0": "Phase 0 exit-gate evidence; described in prose on api/compat.rst",
    "prin._public_api": "canonical RC1 name tuple; prose on api/compat.rst",
}

_AUTOMODULE = re.compile(r"^\.\. automodule:: (\S+)\s*$")
_TOCTREE_ENTRY = re.compile(r"^\s{3}(\S+)\s*$")


def _automodule_blocks(path: Path) -> list[tuple[str, bool]]:
    """Return ``(module, no_index)`` for every automodule directive in a page.

    Args:
        path: reStructuredText page to scan.

    Returns:
        One tuple per directive; ``no_index`` is True when the directive's own
        option block contains ``:no-index:``.
    """
    lines = path.read_text(encoding="utf-8").splitlines()
    blocks: list[tuple[str, bool]] = []
    for index, line in enumerate(lines):
        match = _AUTOMODULE.match(line)
        if match is None:
            continue
        no_index = False
        for option in lines[index + 1 :]:
            if not option.startswith("   "):
                break
            if ":no-index:" in option:
                no_index = True
        blocks.append((match.group(1), no_index))
    return blocks


def _all_automodules() -> dict[Path, list[tuple[str, bool]]]:
    """Return the automodule directives of every API page.

    Returns:
        Mapping of page path to its ``(module, no_index)`` blocks.
    """
    return {path: _automodule_blocks(path) for path in sorted(API.glob("*.rst"))}


def _toctree_targets(path: Path) -> set[str]:
    """Return the document names a page's toctrees reference.

    Args:
        path: reStructuredText page to scan.

    Returns:
        Toctree entry names, relative to ``path``'s directory.
    """
    targets: set[str] = set()
    in_toctree = False
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.startswith(".. toctree::"):
            in_toctree = True
            continue
        if in_toctree:
            if line.strip() and not line.startswith(" "):
                in_toctree = False
                continue
            if line.startswith("   ") and not line.strip().startswith(":"):
                entry = line.strip()
                if entry:
                    targets.add(entry)
    return targets


def test_contract_api_pages_exist() -> None:
    """Assert the three pages the frozen acceptance contract names are present."""
    missing = [name for name in CONTRACT_API_PAGES if not (API / name).is_file()]
    assert not missing, f"DOCS/sphinx/api is missing {missing}"


def test_conf_release_matches_pyproject() -> None:
    """Assert ``conf.py`` derives its release from ``pyproject.toml``.

    Guards the regression where ``conf.py`` hard-coded ``release = "0.1.0"``
    against a ``0.3.0`` distribution. ``conf.py`` must read the version rather
    than restate it.
    """
    conf_source = (SPHINX / "conf.py").read_text(encoding="utf-8")
    tree = ast.parse(conf_source)
    assigned = {
        target.id
        for node in ast.walk(tree)
        if isinstance(node, ast.Assign)
        for target in node.targets
        if isinstance(target, ast.Name)
    }
    assert "release" in assigned and "version" in assigned, (
        "conf.py must define both `release` and `version`"
    )
    assert 'release = "' not in conf_source, (
        "conf.py hard-codes `release`; it must be derived from pyproject.toml "
        "so the docs cannot drift from the distribution version"
    )

    with (ROOT / "pyproject.toml").open("rb") as stream:
        expected = tomllib.load(stream)["project"]["version"]
    namespace: dict[str, object] = {"__file__": str(SPHINX / "conf.py")}
    exec(compile(tree, str(SPHINX / "conf.py"), "exec"), namespace)
    assert namespace["release"] == expected, (
        f"conf.py release {namespace['release']!r} != pyproject.toml {expected!r}"
    )


def test_every_api_page_is_in_a_toctree() -> None:
    """Assert no API page is orphaned from navigation."""
    referenced: set[Path] = set()
    for page in [SPHINX / "index.rst", *API.glob("*.rst")]:
        for target in _toctree_targets(page):
            candidate = (page.parent / target).with_suffix(".rst")
            referenced.add(candidate.resolve())
    orphans = sorted(
        path.name for path in API.glob("*.rst") if path.resolve() not in referenced
    )
    assert not orphans, f"api pages in no toctree: {orphans}"


def test_index_toctree_entries_resolve() -> None:
    """Assert every toctree entry in ``index.rst`` names an existing page."""
    missing = []
    for target in sorted(_toctree_targets(SPHINX / "index.rst")):
        if not (SPHINX / target).with_suffix(".rst").is_file():
            missing.append(target)
    assert not missing, f"index.rst toctree references missing pages: {missing}"


def test_every_public_module_is_documented() -> None:
    """Assert every ``prin`` submodule's public names reach a documented page.

    Documentation Standards §2.2 requires 100 % of public symbols documented. A
    submodule satisfies that either by having its own ``automodule`` target, or
    by having every public name re-exported through a module that does — which
    is how ``prin.nn.ablation`` / ``activations`` / ``attention`` / ``inhibition``
    are covered, via ``prin.nn.__all__``. A module with neither, and no entry in
    ``NOT_AUTODOCED``, is an undocumented surface.
    """
    documented = {
        module for blocks in _all_automodules().values() for module, _ in blocks
    }
    submodules = sorted(
        {info.name for info in pkgutil.walk_packages(prin.__path__, "prin.")} | {"prin"}
    )

    reexported: dict[str, set[str]] = {}
    for module in submodules:
        try:
            loaded = importlib.import_module(module)
        except ImportError:  # pragma: no cover - compiled extension, guarded below
            continue
        exported = getattr(loaded, "__all__", None)
        if exported is None:
            continue
        for name in exported:
            value = getattr(loaded, name, None)
            origin = getattr(value, "__module__", None)
            if origin and origin != module:
                reexported.setdefault(origin, set()).add(name)

    gaps = []
    for module in submodules:
        if module in documented or module in NOT_AUTODOCED:
            continue
        try:
            loaded = importlib.import_module(module)
        except ImportError:
            continue
        exported = getattr(loaded, "__all__", None)
        public = (
            set(exported)
            if exported is not None
            else {n for n in dir(loaded) if not n.startswith("_")}
        )
        covered = reexported.get(module, set())
        uncovered = sorted(n for n in public if n not in covered)
        if uncovered:
            gaps.append(f"{module}: {uncovered}")
    assert not gaps, f"public names reachable from no documented page: {gaps}"


def test_not_autodoced_entries_are_real_and_used() -> None:
    """Assert the autodoc exception list names real modules and nothing stale."""
    submodules = {info.name for info in pkgutil.walk_packages(prin.__path__, "prin.")}
    unknown = sorted(name for name in NOT_AUTODOCED if name not in submodules)
    assert not unknown, f"NOT_AUTODOCED names modules that do not exist: {unknown}"
    documented = {
        module for blocks in _all_automodules().values() for module, _ in blocks
    }
    stale = sorted(name for name in NOT_AUTODOCED if name in documented)
    assert not stale, f"NOT_AUTODOCED lists modules that are in fact autodoc'd: {stale}"


def test_no_module_is_autodoced_with_members_on_two_indexed_pages() -> None:
    """Assert each module is member-documented on at most one indexed page.

    Two indexed ``automodule`` directives for the same module make every object
    in it a duplicate description, which ``sphinx-build -W`` rejects.
    """
    owners: dict[str, list[str]] = {}
    for path, blocks in _all_automodules().items():
        for module, no_index in blocks:
            if not no_index:
                owners.setdefault(module, []).append(path.name)
    duplicated = {m: pages for m, pages in owners.items() if len(pages) > 1}
    assert not duplicated, f"modules member-documented on >1 indexed page: {duplicated}"


def test_no_indexed_page_autodocs_a_module_twice() -> None:
    """Assert a page does not repeat a directive, which self-duplicates objects."""
    repeated = {}
    for path, blocks in _all_automodules().items():
        seen: set[str] = set()
        for module, _ in blocks:
            if module in seen:
                repeated.setdefault(path.name, []).append(module)
            seen.add(module)
    assert not repeated, f"pages autodoc'ing the same module twice: {repeated}"


def test_required_guides_exist_and_are_not_stubs() -> None:
    """Assert the Documentation Standards §3 guide set is present and written.

    A stub is a page whose body is only a ``.. note::`` pointing elsewhere, which
    is what ``architecture.rst`` and ``getting_started.rst`` were before WP-037.
    """
    required = (
        "getting_started.rst",
        "architecture.rst",
        "migration_guide.rst",
        "kernel_architecture.rst",
        "parity_report.rst",
        "coupling_topologies.rst",
        "capacity_analysis.rst",
        "rust_api.rst",
        "notebooks.rst",
        "paper.rst",
    )
    for name in required:
        path = SPHINX / name
        assert path.is_file(), f"DOCS/sphinx/{name} missing (Doc Standards s3)"
        body = path.read_text(encoding="utf-8")
        assert len(body.splitlines()) >= 40, (
            f"DOCS/sphinx/{name} is {len(body.splitlines())} lines — still a stub"
        )


#: ``api/utils.rst`` is a lookup index, not an autodoc page: PRIN has no
#: ``prin.utils`` module (the PRINet 3.0 package was dissolved into flat
#: modules), so the page maps each ``prinet.utils.*`` name to its PRIN owner and
#: links to that owner's page. The frozen ported contract
#: (``TestSphinxDocs::test_api_rst_files_exist``) requires the filename, and
#: inventing a ``prin.utils`` namespace to satisfy it would be a public-API
#: change outside WP-037's scope.
INDEX_ONLY_PAGES = {"utils.rst"}


@pytest.mark.parametrize("name", sorted(p.name for p in API.glob("*.rst")))
def test_api_page_has_a_title_and_at_least_one_directive(name: str) -> None:
    """Assert each API page is a well-formed reStructuredText document.

    Args:
        name: API page filename.
    """
    text = (API / name).read_text(encoding="utf-8")
    lines = text.splitlines()
    assert len(lines) >= 2, f"{name} has no title"
    assert set(lines[1].strip()) == {"="} and len(lines[1].strip()) >= len(lines[0]), (
        f"{name} title underline is missing or too short"
    )
    if name not in INDEX_ONLY_PAGES:
        assert ".. automodule::" in text, f"{name} autodocs nothing"
