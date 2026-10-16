"""Publication-fidelity gate: PRIN versus the frozen PRINet 3.0 generators.

EXP-002 hypothesis H3 (pre-registration §2, §5.4) predicted that PRIN's
``tools.reproduce.run_reproduction`` and the frozen PRINet 3.0 reference
generators render the same 39 registered ``generated_files`` from the archived
172-input set. E3 found 18 of 39 files different under the approved comparison
policy, the ``.pdf`` and ``.png`` of nine figures (EXP-002 E5 report §3.3,
campaign plan §10.4 D1). Before the EXP-002 D1 correction no gate compared the
two arms: ``tests/test_publication_generation.py`` checks table bytes against
the archived tables and figure completeness, not figure equality.

This module is that comparison. In one process it renders the reference arm
(the frozen ``prinet.utils`` figure and table generators, origin and digest
pinned exactly as the E3 driver pins them) and the PRIN arm (the registered
``run_reproduction`` call with ``verify=True``). It then compares every
registered file under the registered H3 rule,
:func:`benchmarks.campaign.exp002_driver.normalized_bytes`: tables after CRLF
to LF canonicalization only, PNG critical chunks after validation, and PDF
with only the four registered Info entries removed and xref offsets zeroed.
That is the function E4 applied. No file is skipped, sampled, or compared with
a tolerance.

The gate deliberately imports the frozen EXP-002 driver and reads the
committed E3 run records. That couples a permanent gate to an immutable
campaign record, as the EXP-001 D1 gates do, and guarantees that it applies
H3's comparison exactly and that its reference arm is E3's reference arm.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

import pytest

pytest.importorskip("prinet")

import prinet.utils.figure_generation as reference_figures
import prinet.utils.table_generation as reference_tables

from benchmarks.campaign import exp002_driver as driver
from tools.reproduce import run_reproduction

pytestmark = [pytest.mark.parity, pytest.mark.slow]

_RESULTS = driver.REFERENCE / "benchmarks" / "results"
_RUN_ROOT = driver.RAW_ROOT
_E3_REFERENCE_RUN = "RUN-20261012T213821Z-fae24c4-reproduction-reference-cpu"
_E3_PRIN_RUN = "RUN-20261012T213936Z-fae24c4-reproduction-prin-cpu"

#: The nine figure stems whose files differed at E3 (E5 report §3.3).
D1_FIGURE_STEMS = (
    "fig5_mot_occlusion_comparison",
    "fig7_ablation_results",
    "fig8_parameter_efficiency",
    "fig9_training_curves",
    "fig10_statistical_summary",
    "fig11_flops_scaling",
    "fig12_supercritical_regime",
    "fig14_gradient_flow",
    "fig15_noise_velocity",
)
D1_FILES = frozenset(
    f"figures/{stem}.{suffix}" for stem in D1_FIGURE_STEMS for suffix in ("pdf", "png")
)


def _sha256(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def _inventory(root: Path) -> list[str]:
    return sorted(
        path.relative_to(root).as_posix() for path in root.rglob("*") if path.is_file()
    )


def _e3_files(run: str) -> dict[str, dict[str, Any]]:
    """Return one committed E3 reproduction record's files, keyed by path."""
    record = json.loads((_RUN_ROOT / run / "reproduction.json").read_text("utf-8"))
    files: list[dict[str, Any]] = record["observations"]["files"]
    return {item["path"]: item for item in files}


@pytest.fixture(scope="module")
def rendered(tmp_path_factory: pytest.TempPathFactory) -> dict[str, Path]:
    """Render the reference and PRIN arms once per module."""
    root = tmp_path_factory.mktemp("exp002-publication")
    reference = root / "reference"
    reference_figures.generate_all_figures(_RESULTS, reference / "figures")
    reference_tables.generate_all_tables(_RESULTS, reference / "tables")
    prin = root / "prin"
    run_reproduction(
        results_dir=_RESULTS,
        output_dir=prin,
        manifest_path=driver.INPUT_MANIFEST,
        verify=True,
    )
    return {"reference": reference, "prin": prin}


def test_reference_arm_is_the_frozen_generator() -> None:
    """The reference modules are the archived files E3 pinned by digest."""
    for module, kind in ((reference_figures, "figure"), (reference_tables, "table")):
        relative = f"src/prinet/utils/{kind}_generation.py"
        origin = Path(str(module.__file__)).resolve()
        assert origin == (driver.REFERENCE / relative).resolve()
        assert _sha256(origin.read_bytes()) == driver.REFERENCE_PINS[relative]


def test_d1_population_is_the_e3_population() -> None:
    """The committed E3 records differ on exactly the nine-stem D1 file set."""
    reference = _e3_files(_E3_REFERENCE_RUN)
    prin = _e3_files(_E3_PRIN_RUN)
    assert set(reference) == set(prin) == driver.EXPECTED_FILES
    differing = {
        name
        for name in driver.EXPECTED_FILES
        if reference[name]["normalized_sha256"] != prin[name]["normalized_sha256"]
    }
    assert differing == D1_FILES


def test_both_arms_render_exactly_the_registered_inventory(
    rendered: dict[str, Path],
) -> None:
    """Neither arm omits or adds a file (H3 inventory rule)."""
    expected = sorted(driver.EXPECTED_FILES)
    assert _inventory(rendered["reference"]) == expected
    assert _inventory(rendered["prin"]) == expected


@pytest.mark.parametrize("name", sorted(driver.EXPECTED_FILES))
def test_reference_arm_reproduces_e3_reference_arm(
    rendered: dict[str, Path], name: str
) -> None:
    """The in-process reference render is E3's reference render.

    Equal normalized digests tie this gate's reference arm to the committed E3
    record. Raw reference PDFs cannot match, because the reference writer
    stamps a wall-clock CreationDate.
    """
    path = rendered["reference"] / name
    normalized = driver.normalized_bytes(path.read_bytes(), path.suffix)
    expected = _e3_files(_E3_REFERENCE_RUN)[name]["normalized_sha256"]
    assert _sha256(normalized) == expected


@pytest.mark.parametrize("name", sorted(driver.EXPECTED_FILES))
def test_prin_matches_reference_under_registered_comparison(
    rendered: dict[str, Path], name: str
) -> None:
    """PRIN's output equals the reference output under the H3 rule."""
    suffix = Path(name).suffix
    reference = driver.normalized_bytes(
        (rendered["reference"] / name).read_bytes(), suffix
    )
    prin = driver.normalized_bytes((rendered["prin"] / name).read_bytes(), suffix)
    assert _sha256(prin) == _sha256(reference), (
        f"{name}: PRIN differs from the frozen PRINet 3.0 generator under the "
        "registered H3 comparison"
    )


@pytest.mark.parametrize(
    "name", sorted(name for name in driver.EXPECTED_FILES if name.endswith(".tex"))
)
def test_prin_tables_match_archived_tables(
    rendered: dict[str, Path], name: str
) -> None:
    """PRIN's tables equal the archived PRINet 3.0 tables (H3's extra reference)."""
    archived = (driver.REFERENCE / "paper" / name).read_bytes()
    prin = (rendered["prin"] / name).read_bytes()
    assert driver.normalized_bytes(prin, ".tex") == driver.normalized_bytes(
        archived, ".tex"
    )


def test_prin_rerender_is_raw_byte_identical(
    rendered: dict[str, Path], tmp_path: Path
) -> None:
    """A second PRIN render repeats every raw byte (H4's same-process half)."""
    again = tmp_path / "prin-again"
    run_reproduction(
        results_dir=_RESULTS,
        output_dir=again,
        manifest_path=driver.INPUT_MANIFEST,
        verify=True,
    )
    assert _inventory(again) == sorted(driver.EXPECTED_FILES)
    for name in sorted(driver.EXPECTED_FILES):
        assert (again / name).read_bytes() == (rendered["prin"] / name).read_bytes()
