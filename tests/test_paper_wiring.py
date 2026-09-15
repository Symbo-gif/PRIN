"""Paper artefact wiring regression tests (WP-037 S1, session ``0145``).

``paper/main.tex`` and ``paper/supplementary.tex`` reference generated figures
and tables by relative path. The generated files themselves are gitignored
derived output — ``python tools/reproduce.py --output-dir paper`` recreates them
— so nothing in the repository asserts that a given reference still resolves.
These tests close that gap: they parse the two sources and check every
``\\includegraphics`` and ``\\input`` target against the generator registries in
:mod:`prin.reporting`, so renaming a generator or a figure breaks the build
here rather than at ``pdflatex`` time.

They also pin the output-root contract the ported acceptance suite asserts
(``tests/test_acceptance_y4q2.py::TestStyleConsistency``): the publication
generators write into ``paper/`` by default and ``paper/`` is a permitted
output root.
"""

from __future__ import annotations

import re
from pathlib import Path

import pytest
from prin.reporting import figure_generation, table_generation

ROOT = Path(__file__).resolve().parents[1]
PAPER = ROOT / "paper"
SOURCES = ("main.tex", "supplementary.tex")

_INCLUDEGRAPHICS = re.compile(r"\\includegraphics\s*(?:\[[^\]]*\])?\s*\{([^}]+)\}")
_INPUT = re.compile(r"\\input\s*\{([^}]+)\}")


def _references(name: str, pattern: re.Pattern[str]) -> list[str]:
    """Extract every artefact path referenced by one paper source.

    Args:
        name: Source filename under ``paper/``.
        pattern: Compiled regular expression with one path group.

    Returns:
        Referenced paths in document order, duplicates preserved.
    """
    text = (PAPER / name).read_text(encoding="utf-8")
    return pattern.findall(text)


def _figure_stems() -> set[str]:
    """Return every filename stem the figure generators can write.

    Three ``FIGURE_GENERATORS`` keys are abbreviated relative to the stems they
    actually save (``fig4_chimera_k_alpha`` writes
    ``fig4_chimera_k_alpha_heatmap``), so the accepted set is the union of the
    registry keys and the reference tree's on-disk names.

    Returns:
        Set of accepted figure stems without extension.
    """
    stems = set(figure_generation.FIGURE_GENERATORS)
    reference = (
        ROOT
        / "DOCS"
        / "archive and reference from PRINet 3.0"
        / "PRINet-3.0.0-main"
        / "paper"
        / "figures"
    )
    if reference.is_dir():
        stems.update(path.stem for path in reference.glob("*.pdf"))
    return stems


@pytest.mark.parametrize("name", SOURCES)
def test_paper_source_exists(name: str) -> None:
    """Assert both carried-over LaTeX sources are present."""
    assert (PAPER / name).is_file(), f"paper/{name} is missing"


@pytest.mark.parametrize("name", SOURCES)
def test_every_included_figure_is_generatable(name: str) -> None:
    """Assert each ``\\includegraphics`` target names a generated figure.

    Args:
        name: Source filename under ``paper/``.
    """
    stems = _figure_stems()
    for path in _references(name, _INCLUDEGRAPHICS):
        assert path.startswith("figures/"), (
            f"paper/{name} includes {path!r} outside figures/; the paper tree "
            "has no \\graphicspath, so a relative figures/ path is required"
        )
        assert Path(path).suffix == ".pdf", (
            f"paper/{name} includes {path!r}; the reference sources use an "
            "explicit .pdf extension and the generators emit both .pdf and .png"
        )
        assert Path(path).stem in stems, (
            f"paper/{name} includes {path!r}, which no entry of "
            "FIGURE_GENERATORS produces"
        )


@pytest.mark.parametrize("name", SOURCES)
def test_every_input_table_is_generatable(name: str) -> None:
    """Assert each ``\\input`` target names a generated table.

    Args:
        name: Source filename under ``paper/``.
    """
    for path in _references(name, _INPUT):
        assert path.startswith("tables/"), (
            f"paper/{name} inputs {path!r} outside tables/"
        )
        assert not path.endswith(".tex"), (
            f"paper/{name} inputs {path!r} with an explicit extension; the "
            "reference sources \\input the stem only"
        )
        assert Path(path).name in table_generation.TABLE_GENERATORS, (
            f"paper/{name} inputs {path!r}, which no entry of TABLE_GENERATORS produces"
        )


def test_figure_default_output_dir_is_the_paper_tree() -> None:
    """Assert figures default to ``paper/figures`` inside the repository."""
    assert figure_generation.DEFAULT_OUTPUT_DIR == PAPER / "figures"
    assert figure_generation.DEFAULT_RESULTS_DIR == ROOT / "benchmarks" / "results"


def test_table_default_output_dir_is_the_paper_tree() -> None:
    """Assert tables default to ``paper/tables`` inside the repository."""
    assert table_generation.DEFAULT_OUTPUT_DIR == PAPER / "tables"
    assert table_generation.DEFAULT_RESULTS_DIR == ROOT / "benchmarks" / "results"


@pytest.mark.parametrize("module", [figure_generation, table_generation])
def test_paper_is_an_allowed_output_root(module: object) -> None:
    """Assert ``paper/`` is permitted without widening the guard further.

    Args:
        module: ``figure_generation`` or ``table_generation``.
    """
    roots = module.ALLOWED_OUTPUT_ROOTS
    assert PAPER.resolve() in roots
    # The confinement guard must still reject an arbitrary repository path, or
    # adding `paper/` would have made it meaningless.
    assert (ROOT / "not_a_declared_output_root").resolve() not in roots


def test_generated_artefacts_are_not_tracked_sources() -> None:
    """Assert the gitignore policy for derived publication artefacts holds.

    ``paper/figures/README.md`` and ``paper/tables/README.md`` are tracked
    descriptions; the regenerated binaries are not. If this test starts
    failing, either a generated artefact was committed or the ignore rules in
    ``.gitignore`` were dropped.
    """
    ignore = (ROOT / ".gitignore").read_text(encoding="utf-8")
    patterns = ("paper/figures/*.pdf", "paper/figures/*.png", "paper/tables/tab_*.tex")
    for pattern in patterns:
        assert pattern in ignore, f".gitignore no longer ignores {pattern}"
    assert (PAPER / "figures" / "README.md").is_file()
    assert (PAPER / "tables" / "README.md").is_file()


def test_every_generator_is_referenced_or_documented_as_unreferenced() -> None:
    """Assert the referenced/unreferenced split matches ``paper/README.md``.

    Four figures and two tables are generated but included by neither source.
    They are retained because ``tests/test_publication_generation.py`` asserts
    the full 14 / 11 ported set by name; ``paper/README.md`` names them so the
    orphans are a documented decision rather than drift.
    """
    used_figures = {
        Path(path).stem
        for name in SOURCES
        for path in _references(name, _INCLUDEGRAPHICS)
    }
    used_tables = {
        Path(path).name for name in SOURCES for path in _references(name, _INPUT)
    }
    readme = (PAPER / "README.md").read_text(encoding="utf-8")

    unreferenced_tables = set(table_generation.TABLE_GENERATORS) - used_tables
    assert unreferenced_tables == {"tab_geometry", "tab_supercritical"}
    for table in unreferenced_tables:
        assert table in readme, f"paper/README.md does not document orphan {table}"

    unreferenced_figures = {
        stem for stem in _figure_stems() if stem.startswith("fig")
    } - used_figures
    for figure in unreferenced_figures:
        assert figure in readme, f"paper/README.md does not document orphan {figure}"
