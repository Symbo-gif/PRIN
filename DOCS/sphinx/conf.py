"""Sphinx configuration for the PRIN documentation site."""

from __future__ import annotations

import tomllib
from pathlib import Path

_PYPROJECT = Path(__file__).resolve().parents[2] / "pyproject.toml"


def _read_release() -> str:
    """Read the distribution version from ``pyproject.toml``.

    ReadTheDocs installs only ``DOCS/sphinx/requirements.txt`` (see
    ``.readthedocs.yaml``), so ``importlib.metadata`` cannot resolve the
    ``prin-core`` distribution there. ``pyproject.toml`` is always present in
    the checkout and is the single source of truth that the wheel, the workspace
    ``Cargo.toml``, ``prin.__version__``, and ``CITATION.cff`` are kept in
    step with (``tests/test_wp001_baseline.py``).

    Returns:
        The ``[project]`` version string, or ``"0.0.0"`` when unreadable.
    """
    try:
        with _PYPROJECT.open("rb") as stream:
            return str(tomllib.load(stream)["project"]["version"])
    except (OSError, KeyError, ValueError):
        return "0.0.0"


project = "PRIN"
author = "Michael Maillet, Damien Davison, Sacha Davison"
copyright = "2026, Michael Maillet, Damien Davison, Sacha Davison"  # noqa: A001
release = _read_release()
version = ".".join(release.split(".")[:2])

extensions = [
    "sphinx.ext.autodoc",
    "sphinx.ext.autosummary",
    "sphinx.ext.napoleon",
    "sphinx.ext.intersphinx",
    "sphinx.ext.viewcode",
    "sphinx.ext.mathjax",
    "myst_parser",
]

autosummary_generate = True
napoleon_google_docstring = True
napoleon_numpy_docstring = False

source_suffix = {
    ".rst": "restructuredtext",
    ".md": "markdown",
}

intersphinx_mapping = {
    "python": ("https://docs.python.org/3", None),
    "numpy": ("https://numpy.org/doc/stable/", None),
    "torch": ("https://pytorch.org/docs/stable/", None),
    "matplotlib": ("https://matplotlib.org/stable/", None),
}

templates_path = ["_templates"]
exclude_patterns = [
    "_build",
    "_build_test",
    "Thumbs.db",
    ".DS_Store",
    "README.md",
    "test_and_benchmark_results",
]

# ``prin`` is a single flat namespace re-exporting 175 names from 25 modules
# (`python/prin/__init__.py`). ``api/core.rst`` autodocs that flat namespace
# with ``:no-index:``; the per-module pages under ``api/`` own the index
# entries, and every submodule automodule on those pages is also ``:no-index:``
# so a re-exported object is indexed exactly once. Documenting one object on
# two indexed pages is a Sphinx "duplicate object description" warning, which
# ``-W`` turns into a build failure, so ``tests/test_sphinx_docs.py`` asserts
# the arrangement stays intact.
#
# Deliberately no global ``autodoc_default_options`` and no
# ``autodoc_member_order``: applying ``members`` to every directive, or
# switching member ordering to ``bysource``, makes autodoc emit a second
# object description for each ``@dataclass`` field of a class reachable from
# two modules — a "duplicate object description" warning that ``-W`` turns
# into a build failure. ``tests/test_sphinx_docs.py`` guards the arrangement.

html_theme = "furo"
