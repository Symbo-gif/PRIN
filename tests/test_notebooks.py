"""Notebook execution and structure tests (WP-037 S1, session ``0145``).

Definition of Done #8 requires "all four notebooks run end-to-end" and
``notebooks/README.md`` requires them to run in CI documentation builds. The
executing tests here are that evidence: each notebook is run through
``nbclient`` against the current interpreter's kernel and any error output
fails the test with the offending cell's source and traceback.

The frozen ported contract in ``tests/test_acceptance_y4q3.py::TestNotebooks``
asserts existence, ``nbformat == 4``, and minimum cell counts for the three
reference-named notebooks. These tests add what PRIN requires on top: the
fourth (net-new) notebook, and that every notebook was committed **already
executed** — an unexecuted notebook is a claim that it runs, not evidence that
it does.

Execution is marked ``slow`` (Testing Standards §4: ``slow`` is >5 s, and the
default CI gate runs ``-m "not slow and not gpu"``); the structural tests are
cheap and run in the default gate.
"""

from __future__ import annotations

import json
import math
from pathlib import Path
from typing import Any

import pytest

NOTEBOOK_DIR = Path(__file__).resolve().parents[1] / "notebooks"

#: The four notebooks PRIN ships. ``01``-``03`` carry the PRINet 3.0 names
#: because ``tests/test_acceptance_y4q3.py::TestNotebooks.EXPECTED`` is
#: parametrized over them and Project Plan amendment #35 froze ported-test
#: parametrization; ``04`` is net-new (Definition of Done #8's fourth notebook).
CONTRACT_NOTEBOOKS = (
    "01_oscillosim_quickstart.ipynb",
    "02_clevr_n_binding.ipynb",
    "03_custom_coupling.ipynb",
    "04_torch_bridge.ipynb",
)

MIN_CODE_CELLS = 3
MIN_MARKDOWN_CELLS = 2

#: Per-notebook ``nbclient`` per-cell timeout, in seconds (Testing Standards
#: section 7 item 2: finite bounds are workload- and evidence-based).
#:
#: EXP002D1-S2-F2. One bound of 900 s, sized from the notebooks' stated ~40 s
#: runtime budget, was exceeded by ``02_clevr_n_binding`` in two consecutive
#: full-suite runs. The notebook is not the cause: alone it completes in 71 s.
#: Inside the full suite on the maintainer host the kernel receives a sixth to a
#: third of one core while processes outside PRIN (an IDE's ripgrep scans and
#: security software) hold the whole host at ~100% CPU, and the leg slows 8-43x
#: (``EVIDENCE/exp002-d1-s3/f2/``). Each bound is BOUND_MARGIN x the largest
#: *completed* contended duration recorded for that notebook, rounded up to a
#: multiple of BOUND_ROUNDING_SECONDS. The recorded duration is the whole
#: notebook's, which is an upper bound on any single cell's, so each bound is
#: conservative per cell. Each bound stays 37-152 times above the notebook's
#: quiet-host duration (37-73 s), so it still ends a genuine hang, but it no
#: longer fails a leg that is merely starved. A test below ties each bound to its
#: recorded worst case in both directions.
NOTEBOOK_CELL_TIMEOUT_SECONDS = {
    "01_oscillosim_quickstart.ipynb": 2700,
    "02_clevr_n_binding.ipynb": 10800,
    "03_custom_coupling.ipynb": 1800,
    "04_torch_bridge.ipynb": 1800,
}

#: Largest *completed* duration, in seconds, of each notebook's execution on this
#: host while it was CPU-starved: S1 ``local-gate.txt`` and S2 ``pytest-suites.txt``
#: (full suite), the S3 observed full-suite run, and, for notebook 02, the S3
#: contention experiment (the notebook beside only the ``test_exp002_*`` tests),
#: which was the slowest at 3484 s. Runs killed at the old 900 s bound are
#: censored and are not used.
RECORDED_CONTENDED_MAX_SECONDS = {
    "01_oscillosim_quickstart.ipynb": 800.07,
    "02_clevr_n_binding.ipynb": 3484.0,
    "03_custom_coupling.ipynb": 408.96,
    "04_torch_bridge.ipynb": 389.81,
}

#: Safety factor between the recorded worst case and the bound.
BOUND_MARGIN = 3.0

#: Bounds are rounded up to a multiple of this many seconds.
BOUND_ROUNDING_SECONDS = 900


def _discover() -> list[Path]:
    """Return every notebook in ``notebooks/``, sorted by name.

    Returns:
        Notebook paths, discovered by glob rather than a hardcoded list so a
        new notebook is picked up automatically instead of silently untested.
    """
    return sorted(NOTEBOOK_DIR.glob("*.ipynb"))


def _load(path: Path) -> dict[str, Any]:
    """Read a notebook as raw JSON.

    Args:
        path: Notebook file to read.

    Returns:
        The parsed notebook document.
    """
    document: dict[str, Any] = json.loads(path.read_text(encoding="utf-8"))
    return document


def _cells(document: dict[str, Any], cell_type: str) -> list[dict[str, Any]]:
    """Return the cells of one type.

    Args:
        document: Parsed notebook document.
        cell_type: ``"code"`` or ``"markdown"``.

    Returns:
        Matching cells in document order.
    """
    return [cell for cell in document["cells"] if cell["cell_type"] == cell_type]


def _ids() -> list[str]:
    """Return pytest ids for the discovered notebooks.

    Returns:
        Notebook filenames, so a failure names the notebook.
    """
    return [path.name for path in _discover()]


def test_notebook_directory_exists() -> None:
    """Assert the notebook tree exists at the documented location."""
    assert NOTEBOOK_DIR.is_dir(), f"{NOTEBOOK_DIR} not found"


def test_contract_notebooks_are_present() -> None:
    """Assert all four shipped notebooks exist under their contract names."""
    present = {path.name for path in _discover()}
    missing = [name for name in CONTRACT_NOTEBOOKS if name not in present]
    assert not missing, f"missing notebooks: {missing}"


def test_no_unexpected_notebooks() -> None:
    """Assert the notebook tree holds exactly the four shipped notebooks.

    A stray scratch notebook would be executed by the ``slow`` tests and would
    also inflate ``test_acceptance_y4q4.py::TestArtefactCounts``; keeping the
    set explicit makes an accidental addition a named failure.
    """
    extra = sorted({path.name for path in _discover()} - set(CONTRACT_NOTEBOOKS))
    assert not extra, f"unexpected notebooks in notebooks/: {extra}"


@pytest.mark.parametrize("name", _ids())
def test_notebook_is_nbformat_4(name: str) -> None:
    """Assert the notebook declares nbformat 4 with a Python 3 kernel.

    Args:
        name: Notebook filename.
    """
    document = _load(NOTEBOOK_DIR / name)
    assert document["nbformat"] == 4, f"{name}: expected nbformat 4"
    assert "cells" in document and "metadata" in document
    kernelspec = document["metadata"].get("kernelspec", {})
    assert kernelspec.get("name") == "python3", f"{name}: kernelspec is {kernelspec!r}"


@pytest.mark.parametrize("name", _ids())
def test_notebook_cell_counts(name: str) -> None:
    """Assert each notebook has enough code and prose cells to be a tutorial.

    Mirrors the minimums the frozen acceptance contract asserts for ``01``-``03``
    and applies them to ``04`` as well.

    Args:
        name: Notebook filename.
    """
    document = _load(NOTEBOOK_DIR / name)
    code = _cells(document, "code")
    markdown = _cells(document, "markdown")
    assert len(code) >= MIN_CODE_CELLS, (
        f"{name}: {len(code)} code cells < {MIN_CODE_CELLS}"
    )
    assert len(markdown) >= MIN_MARKDOWN_CELLS, (
        f"{name}: {len(markdown)} markdown cells < {MIN_MARKDOWN_CELLS}"
    )


@pytest.mark.parametrize("name", _ids())
def test_notebook_is_committed_executed(name: str) -> None:
    """Assert the committed notebook carries real execution output.

    An unexecuted notebook asserts nothing: Definition of Done #8 is about the
    notebook *running*, so the committed artefact must show that it did.

    Args:
        name: Notebook filename.
    """
    document = _load(NOTEBOOK_DIR / name)
    code = _cells(document, "code")
    unexecuted = [
        i for i, cell in enumerate(code) if cell.get("execution_count") is None
    ]
    assert not unexecuted, f"{name}: code cells {unexecuted} have no execution_count"
    assert any(cell.get("outputs") for cell in code), f"{name}: no cell produced output"


@pytest.mark.parametrize("name", _ids())
def test_notebook_states_a_runtime_budget(name: str) -> None:
    """Assert the title cell states a runtime budget.

    Documentation Standards §3: "Notebooks live in ``notebooks/``, numbered,
    with a stated runtime budget."

    Args:
        name: Notebook filename.
    """
    document = _load(NOTEBOOK_DIR / name)
    markdown = _cells(document, "markdown")
    assert markdown, f"{name}: no markdown cells"
    first = "".join(markdown[0]["source"]).lower()
    assert "runtime budget" in first, (
        f"{name}: first markdown cell states no runtime budget"
    )


@pytest.mark.parametrize("name", _ids())
def test_notebook_seeds_explicitly(name: str) -> None:
    """Assert no notebook relies on unseeded randomness.

    Testing Standards §1.5: every stochastic test seeds explicitly. A notebook
    that calls a PRIN generator without a seed is not reproducible, and PRIN has
    no hidden RNG to fall back on.

    Args:
        name: Notebook filename.
    """
    document = _load(NOTEBOOK_DIR / name)
    source = "\n".join("".join(cell["source"]) for cell in _cells(document, "code"))
    assert "seed" in source, f"{name}: no cell mentions a seed"


@pytest.mark.parametrize("name", _ids())
def test_notebook_decodes_under_the_windows_locale_encoding(name: str) -> None:
    """Assert the notebook bytes decode as cp1252, not just as UTF-8.

    ``tests/test_acceptance_y4q3.py::TestNotebooks`` is a byte-unchanged port
    that reads notebooks with a bare ``open(path)``, so on Windows it decodes
    them with the locale codepage (cp1252). Any character whose UTF-8 encoding
    contains one of the five bytes cp1252 leaves undefined — 0x81, 0x8D, 0x8F,
    0x90, 0x9D — makes that test raise ``UnicodeDecodeError``. U+207B
    (``rad s⁻¹``) and U+2074 (``h⁴``) are the usual offenders.

    Definition of Done #2 requires the ported suite to pass on Linux **and**
    Windows, so this is a real constraint on notebook prose rather than a
    Windows quirk to route around.

    Args:
        name: Notebook filename.
    """
    raw = (NOTEBOOK_DIR / name).read_bytes()
    try:
        raw.decode("cp1252")
    except UnicodeDecodeError as exc:
        offending = raw[max(0, exc.start - 12) : exc.start + 12]
        pytest.fail(
            f"{name} is not readable under the Windows locale encoding: {exc}. "
            f"Bytes around the failure: {offending!r}. Replace the character "
            "with an ASCII equivalent (for example 'rad/s' for 'rad s^-1')."
        )


def test_every_notebook_has_a_sized_cell_timeout() -> None:
    """Assert each shipped notebook has an evidence-sized per-cell bound (F2).

    A notebook added without a recorded in-suite duration and a bound sized from
    it would otherwise silently inherit nothing; this makes that a named failure.
    """
    contract = set(CONTRACT_NOTEBOOKS)
    assert set(NOTEBOOK_CELL_TIMEOUT_SECONDS) == contract
    assert set(RECORDED_CONTENDED_MAX_SECONDS) == contract


@pytest.mark.parametrize("name", CONTRACT_NOTEBOOKS)
def test_cell_timeout_is_the_rule_applied_to_the_recorded_contended_maximum(
    name: str,
) -> None:
    """Assert each bound is exactly the sizing rule applied to its recorded worst case.

    Testing Standards section 7 item 2 sizes a finite bound from cited evidence
    plus substantial margin for host variability. The rule used here is
    BOUND_MARGIN x the recorded worst case, rounded up to a multiple of
    BOUND_ROUNDING_SECONDS. Asserting equality ties the two constants together in
    both directions: a bound cannot be lowered below the margin, nor raised beyond
    what the evidence supports, and a slower worst case cannot be recorded without
    the bound following it.

    Args:
        name: Notebook filename.
    """
    recorded = RECORDED_CONTENDED_MAX_SECONDS[name]
    expected = (
        math.ceil(BOUND_MARGIN * recorded / BOUND_ROUNDING_SECONDS)
        * BOUND_ROUNDING_SECONDS
    )
    assert NOTEBOOK_CELL_TIMEOUT_SECONDS[name] == expected, (
        f"{name}: bound {NOTEBOOK_CELL_TIMEOUT_SECONDS[name]} s != {expected} s "
        f"({BOUND_MARGIN} x the recorded contended maximum {recorded} s, rounded "
        f"up to a multiple of {BOUND_ROUNDING_SECONDS} s); re-size it from new "
        "evidence (Testing Standards section 7)"
    )


@pytest.mark.slow
@pytest.mark.parametrize("name", _ids())
def test_notebook_executes_end_to_end(name: str) -> None:
    """Execute one notebook and fail on any error output.

    Runs against a fresh kernel in a temporary working directory with network
    access unneeded; every notebook is CPU-only and seeded.

    Args:
        name: Notebook filename.

    Raises:
        AssertionError: If any cell raises, with the cell source and traceback.
    """
    nbformat = pytest.importorskip(
        "nbformat", reason="notebook execution needs nbformat"
    )
    NotebookClient = pytest.importorskip(
        "nbclient", reason="notebook execution needs nbclient"
    ).NotebookClient

    path = NOTEBOOK_DIR / name
    document = nbformat.read(path, as_version=4)
    client = NotebookClient(
        document,
        timeout=NOTEBOOK_CELL_TIMEOUT_SECONDS[name],
        kernel_name="python3",
        resources={"metadata": {"path": str(NOTEBOOK_DIR.parent)}},
    )
    client.execute()

    failures = []
    for index, cell in enumerate(_cells(document, "code")):
        for output in cell.get("outputs", []):
            if output.get("output_type") == "error":
                failures.append(
                    f"{name} cell {index} raised {output.get('ename')}: "
                    f"{output.get('evalue')}\n" + "\n".join(output.get("traceback", []))
                )
    assert not failures, "\n\n".join(failures)


def test_committed_notebook_outputs_have_no_maintainer_artifacts() -> None:
    """Assert committed notebook outputs contain no host paths or warnings (WP037-F8).

    Scans every code cell output in every committed notebook for absolute
    maintainer-host paths (``C:\\Users\\there``), ``ipykernel`` temp paths,
    ``UserWarning`` traces, and ``Traceback`` blocks. A release-facing
    committed artefact must not embed host identity or transient noise.
    """
    import re

    host_path = re.compile(r"C:\\Users\\", re.IGNORECASE)
    ipykernel_temp = re.compile(r"ipykernel_\d+")
    user_warning = re.compile(r"UserWarning:")
    traceback_marker = re.compile(r"Traceback \(most recent call last\)")

    violations: list[str] = []
    for nb_path in sorted(NOTEBOOK_DIR.glob("*.ipynb")):
        text = nb_path.read_text(encoding="utf-8")
        nb = json.loads(text)
        for cell_idx, cell in enumerate(nb.get("cells", [])):
            if cell.get("cell_type") != "code":
                continue
            for out in cell.get("outputs", []):
                content = ""
                if "text" in out:
                    content = "".join(out["text"])
                elif "data" in out:
                    for mime_content in out["data"].values():
                        if isinstance(mime_content, list):
                            content += "".join(mime_content)
                        elif isinstance(mime_content, str):
                            content += mime_content
                for pattern, label in [
                    (host_path, "maintainer-host path"),
                    (ipykernel_temp, "ipykernel temp path"),
                    (user_warning, "UserWarning"),
                    (traceback_marker, "Traceback"),
                ]:
                    if pattern.search(content):
                        violations.append(
                            f"{nb_path.name} cell {cell_idx}: {label} in output"
                        )
    assert not violations, "\n".join(violations)
