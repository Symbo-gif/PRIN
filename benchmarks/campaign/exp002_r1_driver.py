"""Collect the registered EXP-002-r1 deterministic censuses and publication arms.

This E1 driver collects observations for the isolated ``EXP-002-r1`` re-run
record, not hypothesis verdicts. Its CLI refuses to create a run while the
committed pre-registration is DRAFT, enforces the rebuilt ``_prin_core.pyd``
SHA-256/size pin (DV-047 closure), and strictly forbids any path under the
immutable predecessor roots ``benchmarks/results/EXP-002/`` or
``DOCS/test_and_benchmark_results/EXP-002/`` (campaign plan §7.1, §10.4 item 4,
amendment #10). Unit tests use controlled synthetic fixtures; importing this
module does not execute an experiment.
"""

from __future__ import annotations

import argparse
import ast
import hashlib
import importlib
import importlib.util
import json
import math
import re
import shutil
import site
import subprocess
import sys
import tempfile
import time
import zlib
from collections.abc import Mapping
from datetime import UTC, datetime
from io import BytesIO
from pathlib import Path, PurePosixPath
from types import ModuleType
from typing import Any, cast

import matplotlib
import numpy
import prin
from matplotlib import font_manager, ft2font
from PIL import Image
from PIL import __version__ as pillow_version
from prin import _prin_core
from prin._deprecation import verify_api_surface
from prin.reporting import figure_generation as prin_figure_generation
from prin.reporting import table_generation as prin_table_generation
from prin.reporting.figure_generation import normalize_matplotlib_output

from benchmarks._common.config import BenchmarkConfig
from benchmarks._common.environment import capture_environment
from benchmarks._common.result import write_json_exclusive, write_result
from tools.reproduce import (
    ManifestRecord,
    ReproductionError,
    append_manifest,
    read_no_follow,
    read_verified_no_follow,
    run_reproduction,
    stat_size_and_hash_no_follow,
    verify_manifest,
)

ROOT = Path(__file__).resolve().parents[2]
REFERENCE = ROOT / "DOCS/archive and reference from PRINet 3.0/PRINet-3.0.0-main"
EXP_ID = "EXP-002-r1"
SESSION_ID = "EXP-002-r1-E3"
RAW_ROOT = ROOT / "benchmarks/results/EXP-002-r1"
PREDECESSOR_RAW_ROOT = ROOT / "benchmarks/results/EXP-002"
OUTPUT_ROOT = ROOT / "DOCS/test_and_benchmark_results/EXP-002-r1"
PREDECESSOR_OUTPUT_ROOT = ROOT / "DOCS/test_and_benchmark_results/EXP-002"
PROTOCOL = (
    ROOT
    / "DOCS/experiments/EXP-002-r1-api-benchmark-result-and-reproduction-parity"
    / "preregistration.md"
)
PREDECESSOR_RECORD_ROOT = (
    ROOT / "DOCS/experiments/EXP-002-api-benchmark-result-and-reproduction-parity"
)
INPUT_MANIFEST = ROOT / "paper/artefact_manifest.json"
INPUT_MANIFEST_SHA = "300cdc094d2b7d27ac8b1e2556b2e6ed4dad3333f0038b45c8f87ea81612cce5"
PRIN_CORE_PYD = ROOT / "python/prin/_prin_core.pyd"
PRIN_CORE_PYD_SHA256 = (
    "37392d067efa3983e384c94f4ac2268c4fad2f5ea929c529b3db50bff4fee99e"
)
PRIN_CORE_PYD_BYTES = 9290240
PRIN_PINS = {
    "python/prin/reporting/figure_generation.py": (
        "e216fec4f45ab71cfc5ef1286701c920731df278120e0afa0d216515b4bb19a7"
    ),
    "python/prin/reporting/table_generation.py": (
        "1593f52d9a652842ee7d62163d9e6b397989e9c6489aa5cc43a8416b1083c8af"
    ),
}
REFERENCE_PINS = {
    "src/prinet/__init__.py": (
        "ede92afc6771f2e29206534905e2820598ba841662a93d59f669f803a382f182"
    ),
    "src/prinet/utils/figure_generation.py": (
        "575eca5a6436a25f957702091a6a0b5b7f3d77f1f496f9e6b423550cf79e1520"
    ),
    "src/prinet/utils/table_generation.py": (
        "9ac382c487f7177465805a49686568b8ac323128cebeae342cca2b05814704cc"
    ),
}
PRIN_ADDITIONS = {"BackendUnavailableError", "__version__", "core_version"}
FIGURE_STEMS = (
    "fig2_clevr_n_capacity",
    "fig3_chimera_metrics",
    "fig4_chimera_k_alpha_heatmap",
    "fig5_mot_occlusion_comparison",
    "fig6_oscillosim_scaling",
    "fig7_ablation_results",
    "fig8_parameter_efficiency",
    "fig9_training_curves",
    "fig10_statistical_summary",
    "fig11_flops_scaling",
    "fig12_supercritical_regime",
    "fig13_representation_geometry",
    "fig14_gradient_flow",
    "fig15_noise_velocity",
)
TABLE_STEMS = (
    "tab_ablation",
    "tab_param_efficiency",
    "tab_chimera",
    "tab_statistical",
    "tab_occlusion",
    "tab_oscillosim",
    "tab_efficiency",
    "tab_binding_params",
    "tab_stress",
    "tab_supercritical",
    "tab_geometry",
)
EXPECTED_FILES = frozenset(
    [f"figures/{stem}.{fmt}" for stem in FIGURE_STEMS for fmt in ("pdf", "png")]
    + [f"tables/{stem}.tex" for stem in TABLE_STEMS]
)
CONCLUSION_FILES = (
    "phase1_chimera_seeds.json",
    "benchmark_y4q1_3_k_alpha_sensitivity.json",
    "phase2_chimera_nsweep.json",
    "y4q1_8_topology_comparison.json",
    "y3q49_goldilocks_zones.json",
)
MODE_LABELS = {
    "api": "r1-api-cpu",
    "conclusions": "r1-conclusions-cpu",
    "reference": "r1-reproduction-reference-cpu",
    "prin": "r1-reproduction-prin-cpu",
    "repeatability": "r1-seedrep0-prin-cpu",
}
MODE_TAGS = {
    "api": ["H1"],
    "conclusions": ["H2"],
    "reference": ["H3"],
    "prin": ["H3", "H4"],
    "repeatability": ["H4"],
}
RUN_PATTERN = re.compile(
    r"RUN-(?P<utc>\d{8}T\d{6}Z)-(?P<sha>[0-9a-f]{7})-(?P<label>r1-[a-z0-9-]+)\Z"
)
RUN_CAP = 2 * 1024 * 1024
RAW_CAP = 10 * 1024 * 1024
COMBINED_EXP002_CAP = 10 * 1024 * 1024
CPU_WALL_CAP = 12 * 60 * 60
# Conservative upper bound on the manifest.json + abort.json bytes appended
# after the prospective storage check, so the pre-publication cap decision
# accounts for finalization overhead rather than only the run's current bytes.
_FINALIZATION_ALLOWANCE = 4096
API_SYMBOL_COUNT = 175
CLAIM_CASE_COUNT = 62
# Import-shadowing threat model for the admission scan: only paths that can
# actually resolve to code the driver (or its imports) execute. Top-level
# ``*.py``/``*.pth`` shadow sys.path[0] entries; files under ``python/``,
# ``benchmarks/``, and ``tools/`` shadow the governed ``prin`` package, the
# ``benchmarks._common`` helpers, and ``tools.reproduce`` respectively.
# ``tools/code-intelligence`` is excluded: its hyphenated path component can
# never name an importable module, and it deliberately carries ignored
# fixture sources. The interpreter-level half of this threat model (site
# ``.pth`` directory entries and effective ``prin``/``prinet`` resolution)
# is covered by ``_environment_shadowing``.
_SHADOW_PATHSPECS = (
    ":(glob)*.py",
    ":(glob)*.pth",
    ":(glob)python/**/*.py",
    ":(glob)python/**/*.pth",
    ":(glob)benchmarks/**/*.py",
    ":(glob)benchmarks/**/*.pth",
    ":(glob)tools/**/*.py",
    ":(glob)tools/**/*.pth",
    ":(exclude)tools/code-intelligence",
)
# Registered Info entries removed (key and value) before PDF comparison.
PDF_INFO_MASKED_KEYS = frozenset({b"CreationDate", b"ModDate", b"Creator", b"Producer"})
_PDF_NAME = re.compile(rb"/[^\x00\t\n\x0c\r ()<>\[\]{}/%]+")
_PDF_TOKEN_END = rb"(?![^\x00\t\n\x0c\r ()<>\[\]{}/%])"
_PDF_REFERENCE = re.compile(
    rb"[0-9]{1,10}[\x00\t\n\x0c\r ]+[0-9]{1,5}[\x00\t\n\x0c\r ]+R" + _PDF_TOKEN_END
)
_PDF_ATOM = re.compile(
    rb"(?:true|false|null|[+-]?(?:[0-9]+\.?[0-9]*|\.[0-9]+))" + _PDF_TOKEN_END
)
_PDF_HEX = re.compile(rb"<[0-9A-Fa-f\x00\t\n\x0c\r ]*>")
_PDF_WHITESPACE = b"\x00\t\n\x0c\r "
# Per-mode observation keys every genuine COMPLETED record carries.
_API_ROW_KEYS = frozenset(
    {
        "name",
        "resolved",
        "callable",
        "defining_module",
        "type",
        "error",
        "legacy",
        "ownership_present",
    }
)
_CASE_KEYS = frozenset(
    {
        "case_id",
        "family",
        "input_file",
        "left_path",
        "right_path",
        "left",
        "operator",
        "right",
        "operand_unit",
        "expected",
        "observed",
    }
)
_FILE_INT_KEYS = ("raw_bytes", "normalized_bytes", "sensitivity_bytes")
_FILE_DIGEST_KEYS = ("raw_sha256", "normalized_sha256", "sensitivity_sha256")


class DriverError(RuntimeError):
    """Report an invalid or unavailable registered collection operation."""


def _git_bytes(*args: str) -> bytes:
    executable = shutil.which("git")
    if executable is None:
        raise DriverError("git is unavailable; source identity cannot be established")
    result = subprocess.run(
        [executable, *args],
        cwd=ROOT,
        capture_output=True,
        check=True,
        timeout=30,
    )
    return result.stdout


def _git(*args: str) -> str:
    return _git_bytes(*args).decode("utf-8").strip()


def _mapping(value: object, context: str) -> dict[str, Any]:
    if not isinstance(value, dict) or any(not isinstance(k, str) for k in value):
        raise DriverError(f"{context}: expected a JSON object")
    return cast("dict[str, Any]", value)


def _list(value: object, context: str) -> list[Any]:
    if not isinstance(value, list):
        raise DriverError(f"{context}: expected an array")
    return value


def _number(value: object, context: str) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise DriverError(f"{context}: expected a finite number, not a Boolean")
    number = float(value)
    if not math.isfinite(number):
        raise DriverError(f"{context}: non-finite input")
    return number


def _digest(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def _check_origin(module: ModuleType, expected: Path) -> None:
    if module.__file__ is None or Path(module.__file__).resolve() != expected.resolve():
        raise DriverError(f"{module.__name__}: import is not the governed source")


def _resolved_confinement_path(path: Path, role: str) -> Path:
    """Resolve ``path`` for confinement checks, refusing parent traversal.

    ``Path.absolute()`` preserves ``..`` components, so a lexical ancestry
    check over ``OUTPUT_ROOT / ".." / "EXP-002" / "x"`` aliases into the
    immutable predecessor tree. Confinement decisions therefore reject
    parent-traversal components and compare fully resolved paths. This
    helper is deliberately separate from the unresolved paths passed to
    ``read_no_follow``/``write_no_follow``: resolved paths are only ever
    used for comparison, never for I/O, so a symlink swapped in between
    the check and the operation cannot be silently followed.
    """
    if ".." in path.parts:
        raise DriverError(f"{role} contains parent-traversal components: {path}")
    return path.resolve()


def _no_symlink_ancestors(path: Path) -> None:
    for ancestor in (path.absolute(), *path.absolute().parents):
        if ancestor.is_symlink():
            raise DriverError(f"output path has a symlink ancestor: {ancestor}")


def _reject_predecessor_path(path: Path, role: str) -> None:
    """Refuse any path inside the immutable predecessor EXP-002 roots."""
    candidate = _resolved_confinement_path(path, role)
    for forbidden in (
        PREDECESSOR_RAW_ROOT,
        PREDECESSOR_OUTPUT_ROOT,
        PREDECESSOR_RECORD_ROOT,
    ):
        resolved = forbidden.resolve()
        if candidate == resolved or candidate.is_relative_to(resolved):
            raise DriverError(
                f"{role} targets immutable predecessor EXP-002 root: {path}"
            )


def _verify_prin_core_extension() -> dict[str, Any]:
    """Verify that the imported ``prin._prin_core`` binary matches the DV-047 pin.

    The pin binds the platform-specific compiled artefact registered on the
    governed E3 host (Windows x86_64 ``.pyd``) to the imported module's exact
    origin, byte size, and SHA-256. On other platforms the imported extension
    is a platform build (``*.so``/``*.dylib``) in the active environment, so
    this check is host-registered by design: governed module resolution is
    additionally covered by :func:`_environment_shadowing` at admission.
    """
    _check_origin(_prin_core, PRIN_CORE_PYD)
    payload = read_no_follow(PRIN_CORE_PYD, "compiled _prin_core.pyd extension")
    digest = _digest(payload)
    if len(payload) != PRIN_CORE_PYD_BYTES or digest != PRIN_CORE_PYD_SHA256:
        raise DriverError(
            "_prin_core.pyd digest or byte size does not match the pinned E1 build"
        )
    return {
        "prin_core_pyd_sha256": digest,
        "prin_core_pyd_bytes": len(payload),
    }


def _legacy_names() -> list[str]:
    path = REFERENCE / "src/prinet/__init__.py"
    payload = read_no_follow(path, "reference API")
    if _digest(payload) != REFERENCE_PINS["src/prinet/__init__.py"]:
        raise DriverError("reference API source digest changed")
    for node in ast.parse(payload).body:
        if isinstance(node, ast.Assign) and any(
            isinstance(target, ast.Name) and target.id == "__all__"
            for target in node.targets
        ):
            names = ast.literal_eval(node.value)
            if (
                not isinstance(names, list)
                or not all(isinstance(name, str) for name in names)
                or len(names) != 172
                or len(set(names)) != 172
            ):
                raise DriverError("reference __all__ is not the frozen 172-name list")
            return cast("list[str]", names)
    raise DriverError("reference literal __all__ missing")


def collect_api() -> dict[str, Any]:
    """Capture export resolution and independent legacy ownership.

    Returns:
        Complete observed names, frozen-contract differences and per-name rows.

    Raises:
        DriverError: If an import or the frozen reference has invalid provenance.
    """
    _check_origin(prin, ROOT / "python/prin/__init__.py")
    _verify_prin_core_extension()
    legacy = set(_legacy_names())
    expected = legacy | PRIN_ADDITIONS
    if legacy & PRIN_ADDITIONS or len(expected) != API_SYMBOL_COUNT:
        raise DriverError("expected API population is not the registered 172 + 3")
    guide = read_no_follow(ROOT / "DOCS/sphinx/migration_guide.rst", "Migration Guide")
    baseline = read_no_follow(
        ROOT / "DOCS/baselines/wp001_api_traceability.md", "API ownership"
    )
    table = re.search(
        r"\.\. wp036-consolidated-table-begin(.*?)"
        r"\.\. wp036-consolidated-table-end",
        guide.decode("utf-8"),
        re.S,
    )
    guide_names = set(
        re.findall(
            r'^\s*"([^"]+)", "prin\.[^"]+",',
            table.group(1) if table else "",
            re.M,
        )
    )
    owned = set(
        re.findall(r"^\|\s*prinet\s*\|\s*([^| ]+)\s*\|", baseline.decode("utf-8"), re.M)
    )
    rows = []
    for name in sorted(expected):
        try:
            obj = getattr(prin, name)
            callable_export = callable(obj)
            supported = obj is not None and (
                callable_export or isinstance(obj, (int, float, str, bool, bytes))
            )
            row = {
                "name": name,
                "resolved": supported,
                "callable": callable_export,
                "defining_module": getattr(obj, "__module__", None),
                "type": type(obj).__name__,
                "error": None,
            }
        except AttributeError as exc:
            row = {
                "name": name,
                "resolved": False,
                "callable": None,
                "defining_module": None,
                "type": None,
                "error": str(exc),
            }
        row["legacy"] = name in legacy
        row["ownership_present"] = name not in legacy or (
            name in owned and name in guide_names
        )
        rows.append(row)
    missing, extra = verify_api_surface(prin.__all__)
    return {
        "expected_names": sorted(expected),
        "legacy_names": sorted(legacy),
        "observed_names": list(prin.__all__),
        "frozen_missing": sorted(missing),
        "frozen_extra": sorted(extra),
        "rows": rows,
        "unit": "api_symbol",
    }


def collect_conclusions(documents: Mapping[str, dict[str, Any]]) -> dict[str, Any]:
    """Collect the 62 predeclared archival predicates, without adjudication.

    Args:
        documents: Verified JSON objects for the five registered input files.

    Returns:
        Labelled operands, independent predictions and observed predicate values.

    Raises:
        DriverError: If the registered input schema or population is invalid,
            including a missing key or a wrongly typed container.
    """
    try:
        return _collect_conclusions(documents)
    except (KeyError, TypeError, IndexError) as exc:
        raise DriverError(
            f"registered historical input schema invalid: {exc!r}"
        ) from exc


def _collect_conclusions(documents: Mapping[str, dict[str, Any]]) -> dict[str, Any]:
    cases: list[dict[str, Any]] = []

    def add(
        family: str,
        label: str,
        filename: str,
        left_path: str,
        left: object,
        operator: str,
        right: object,
        unit: str,
        expected: bool = True,
        right_path: str | None = None,
    ) -> None:
        a = _number(left, f"{filename}:{left_path}")
        b = _number(right, f"{filename}:{right_path or 'registered threshold'}")
        cases.append(
            {
                "case_id": f"{family}:{label}",
                "family": family,
                "input_file": filename,
                "left_path": left_path,
                "right_path": right_path,
                "left": a,
                "operator": operator,
                "right": b,
                "operand_unit": unit,
                "expected": expected,
                "observed": a > b if operator == ">" else a < b,
            }
        )

    def document(index: int) -> dict[str, Any]:
        name = CONCLUSION_FILES[index]
        if name not in documents:
            raise DriverError(f"required historical input missing: {name}")
        return _mapping(documents[name], name)

    bc = _mapping(document(0)["bimodality_coefficient"], "C01 BC")
    raw = _list(bc["raw_values"], "C01 raw values")
    if len(raw) != 5 or bc["n_sequences"] != 5:
        raise DriverError("C01 requires exactly five historical sequences")
    for index, value in enumerate(raw):
        add(
            "C01",
            str(index),
            CONCLUSION_FILES[0],
            f"/bimodality_coefficient/raw_values/{index}",
            value,
            ">",
            0.555,
            "BC",
        )

    grid = _list(document(1)["grid"], "C02 grid")
    if len(grid) != 42:
        raise DriverError("C02 requires all 42 grid rows")
    labels: set[tuple[float, float]] = set()
    for index, item in enumerate(grid):
        row = _mapping(item, "C02 row")
        label = (_number(row["K"], "C02 K"), _number(row["alpha"], "C02 alpha"))
        if label in labels:
            raise DriverError("C02 duplicate (K,alpha) label")
        labels.add(label)
        expected = row["chimera_detected"]
        if not isinstance(expected, bool):
            raise DriverError("C02 historical classification must be a Boolean")
        add(
            "C02",
            str(index),
            CONCLUSION_FILES[1],
            f"/grid/{index}/bc_mean",
            row["bc_mean"],
            ">",
            0.555,
            "BC",
            expected,
        )
        cases[-1]["K"] = label[0]
        cases[-1]["alpha_radians"] = label[1]

    sweep = _list(document(2)["sweep"], "C03 sweep")
    populations: set[int] = set()
    for index, item in enumerate(sweep):
        row = _mapping(item, "C03 row")
        n = row["n_oscillators"]
        if isinstance(n, bool) or not isinstance(n, int) or n in populations:
            raise DriverError("C03 invalid/duplicate oscillator-count label")
        populations.add(n)
        stats = _mapping(row["bc_stats"], "C03 BC stats")
        add(
            "C03",
            str(n),
            CONCLUSION_FILES[2],
            f"/sweep/{index}/bc_stats/mean",
            stats["mean"],
            ">",
            0.5,
            "BC",
        )
    if populations != {128, 256, 512, 1024} or len(sweep) != 4:
        raise DriverError("C03 requires exactly N=128/256/512/1024")

    topologies = _mapping(document(3)["topologies"], "C04 topologies")
    if set(topologies) != {"ring", "2community", "4community"}:
        raise DriverError("C04 requires the three registered topology labels")
    rows = {name: _mapping(row, name) for name, row in topologies.items()}
    widths = {
        name: _mapping(row["bc_ci"], f"{name} CI")["ci_width"]
        for name, row in rows.items()
    }
    for name in ("2community", "4community"):
        add(
            "C04",
            f"mean-ring-{name}",
            CONCLUSION_FILES[3],
            "/topologies/ring/bc_mean",
            rows["ring"]["bc_mean"],
            ">",
            rows[name]["bc_mean"],
            "BC",
            right_path=f"/topologies/{name}/bc_mean",
        )
        add(
            "C04",
            f"width-ring-{name}",
            CONCLUSION_FILES[3],
            "/topologies/ring/bc_ci/ci_width",
            widths["ring"],
            ">",
            widths[name],
            "historical_BC_CI_width",
            right_path=f"/topologies/{name}/bc_ci/ci_width",
        )
    add(
        "C04",
        "width-2community-4community",
        CONCLUSION_FILES[3],
        "/topologies/2community/bc_ci/ci_width",
        widths["2community"],
        ">",
        widths["4community"],
        "historical_BC_CI_width",
        right_path="/topologies/4community/bc_ci/ci_width",
    )

    zones = _mapping(document(4)["zones"], "C05 zones")
    cpu = {
        name: _mapping(zones[f"{name}_cpu"], f"C05 {name}")
        for name in ("csr", "full", "mean_field", "sparse_knn")
    }
    if any(
        row["device"] != "cpu" or row["regime"] != name for name, row in cpu.items()
    ):
        raise DriverError("C05 selected records are not the registered CPU regimes")
    for name in ("full", "mean_field", "sparse_knn"):
        add(
            "C05",
            f"width-csr-{name}",
            CONCLUSION_FILES[4],
            "/zones/csr_cpu/zone_width",
            cpu["csr"]["zone_width"],
            ">",
            cpu[name]["zone_width"],
            "stored_coupling_K",
            right_path=f"/zones/{name}_cpu/zone_width",
        )
    for name in ("csr", "mean_field", "sparse_knn"):
        add(
            "C05",
            f"onset-full-{name}",
            CONCLUSION_FILES[4],
            "/zones/full_cpu/K_c",
            cpu["full"]["K_c"],
            "<",
            cpu[name]["K_c"],
            "stored_coupling_K",
            right_path=f"/zones/{name}_cpu/K_c",
        )
    if (
        len(cases) != CLAIM_CASE_COUNT
        or len({case["case_id"] for case in cases}) != CLAIM_CASE_COUNT
    ):
        raise DriverError("registered claim population is not 62 unique cases")
    return {"cases": cases, "unit": "claim_comparator_record"}


def _snapshot(destination: Path) -> tuple[dict[str, dict[str, Any]], dict[str, Any]]:
    _reject_predecessor_path(destination, "input snapshot")
    resolved = _resolved_confinement_path(destination, "input snapshot")
    output_root = OUTPUT_ROOT.resolve()
    if resolved == output_root or not resolved.is_relative_to(output_root):
        raise DriverError("input snapshot is outside the registered output root")
    manifest_bytes = read_no_follow(INPUT_MANIFEST, "paper input manifest")
    if _digest(manifest_bytes) != INPUT_MANIFEST_SHA:
        raise DriverError("paper input manifest changed from the E1 baseline")
    records = verify_manifest(REFERENCE / "benchmarks/results", INPUT_MANIFEST)
    if len(records) != 172:
        raise DriverError("paper input manifest must contain exactly 172 records")
    destination.mkdir()
    documents = {}
    for record in records:
        payload = read_verified_no_follow(
            REFERENCE / "benchmarks/results" / record.path,
            record.bytes,
            record.sha256,
            record.path,
            "historical input",
        )
        with (destination / record.path).open("xb") as stream:
            stream.write(payload)
        if record.path in CONCLUSION_FILES:
            documents[record.path] = _mapping(json.loads(payload), record.path)
    verify_manifest(destination, INPUT_MANIFEST)
    return documents, {
        "input_manifest_sha256": INPUT_MANIFEST_SHA,
        "input_record_count": len(records),
        "input_records": [
            {"path": item.path, "bytes": item.bytes, "sha256": item.sha256}
            for item in records
        ],
    }


def _pdf_parts(
    payload: bytes,
) -> tuple[
    bytes, list[tuple[tuple[int, int], bytes]], tuple[int, int] | None, bytes, bytes
]:
    """Validate the registered classic-xref container and locate its objects."""
    error = "malformed PDF publication output (classic-xref container required)"
    if re.match(rb"%PDF-(?:1\.[0-7]|2\.0)[\r\n]", payload) is None:
        raise DriverError(error)
    footer = re.search(
        rb"(?m)^startxref[ \t]*[\r\n]+([0-9]{1,10})[ \t]*[\r\n]+%%EOF[ \t\r\n]*\Z",
        payload,
    )
    if footer is None:
        raise DriverError(error)
    offset = int(footer.group(1))
    if not 0 < offset < footer.start():
        raise DriverError(error)
    lines = payload[offset : footer.start()].splitlines(keepends=True)
    if not lines or lines[0].strip() != b"xref":
        raise DriverError(error)
    entries: dict[tuple[int, int], tuple[int, bytes]] = {}
    canonical = [lines[0]]
    index = 1
    while index < len(lines) and lines[index].strip() != b"trailer":
        subsection = re.fullmatch(
            rb"([0-9]{1,10})[ \t]+([0-9]{1,10})", lines[index].strip()
        )
        if subsection is None:
            raise DriverError(error)
        first, count = (int(value) for value in subsection.groups())
        if count < 1 or count > len(lines) - index - 1:
            raise DriverError(error)
        canonical.append(lines[index])
        index += 1
        for number in range(first, first + count):
            line = lines[index]
            entry = re.fullmatch(
                rb"([0-9]{10})[ \t]([0-9]{5})[ \t]([nf])[ \t]*",
                line.strip(),
            )
            if entry is None:
                raise DriverError(error)
            position, generation, kind = entry.groups()
            key = (number, int(generation))
            if key in entries:
                raise DriverError(error)
            entries[key] = (int(position), kind)
            canonical.append(b"0000000000" + line[10:] if kind == b"n" else line)
            index += 1
    if index >= len(lines):
        raise DriverError(error)
    trailer = b"".join(lines[index:])
    dictionary = re.fullmatch(rb"trailer\s*<<(.*)>>\s*", trailer, re.S)
    if dictionary is None or not entries:
        raise DriverError(error)
    if any(
        len(re.findall(key, dictionary.group(1))) > 1
        for key in (rb"/Size\b", rb"/Root\b", rb"/Info\b")
    ):
        raise DriverError(error)
    size = re.search(rb"/Size\s+([0-9]{1,10})\b", dictionary.group(1))
    root = re.search(
        rb"/Root\s+([0-9]{1,10})\s+([0-9]{1,5})\s+R\b", dictionary.group(1)
    )
    if (
        size is None
        or int(size.group(1)) != max(number for number, _ in entries) + 1
        or root is None
    ):
        raise DriverError(error)
    root_key = (int(root.group(1)), int(root.group(2)))
    if entries.get(root_key, (0, b"f"))[1] != b"n":
        raise DriverError(error)
    info = re.search(
        rb"/Info\s+([0-9]{1,10})\s+([0-9]{1,5})\s+R\b", dictionary.group(1)
    )
    info_key: tuple[int, int] | None = None
    if info is None and re.search(rb"/Info\b", dictionary.group(1)):
        raise DriverError(error)
    if info is not None:
        info_key = (int(info.group(1)), int(info.group(2)))
        if entries.get(info_key, (0, b"f"))[1] != b"n":
            raise DriverError(error)
    in_use = sorted(
        (position, number, generation)
        for (number, generation), (position, kind) in entries.items()
        if kind == b"n"
    )
    if not in_use or len({position for position, _, _ in in_use}) != len(in_use):
        raise DriverError(error)
    objects: list[tuple[tuple[int, int], bytes]] = []
    for item, (position, number, generation) in enumerate(in_use):
        end = in_use[item + 1][0] if item + 1 < len(in_use) else offset
        segment = payload[position:end]
        header = f"{number} {generation} obj".encode("ascii")
        if (
            not 0 < position < end <= offset
            or not segment.startswith(header)
            or segment[len(header) : len(header) + 1] not in {b" ", b"\r", b"\n"}
            or not segment.rstrip().endswith(b"endobj")
        ):
            raise DriverError(error)
        key = (number, generation)
        if key == info_key and re.search(rb"(?m)^stream[\r\n]", segment):
            raise DriverError(error)
        objects.append((key, segment))
    trailer = re.sub(
        rb"/ID\s*\[\s*<[0-9a-fA-F]+>\s*<[0-9a-fA-F]+>\s*\]",
        b"/ID [<normalized> <normalized>]",
        trailer,
    )
    canonical.append(trailer)
    canonical_footer = re.sub(rb"[0-9]+", b"0", payload[footer.start() :], count=1)
    return (
        payload[: in_use[0][0]],
        objects,
        info_key,
        b"".join(canonical),
        canonical_footer,
    )


def _pdf_value_end(body: bytes, start: int, error: str) -> int:
    """Return the end of one direct PDF value (no arrays/dictionaries)."""
    if body[start : start + 1] == b"(":
        depth = 0
        index = start
        while index < len(body):
            character = body[index]
            if character == 0x5C:
                index += 2
                continue
            if character == 0x28:
                depth += 1
            elif character == 0x29:
                depth -= 1
                if depth == 0:
                    return index + 1
            index += 1
        raise DriverError(error)
    if body[start : start + 2] != b"<<":
        for pattern in (_PDF_HEX, _PDF_NAME, _PDF_REFERENCE, _PDF_ATOM):
            match = pattern.match(body, start)
            if match is not None:
                return match.end()
    raise DriverError(error)


def _canonical_info(segment: bytes) -> bytes:
    """Remove the registered Info entries and re-serialize the rest."""
    error = "malformed PDF Info dictionary (flat direct-value dictionary required)"
    match = re.match(rb"([0-9]{1,10}) ([0-9]{1,5}) obj[\x00\t\n\x0c\r ]*<<", segment)
    if match is None:
        raise DriverError(error)
    body = segment
    kept: list[bytes] = []
    seen: set[bytes] = set()
    index = match.end()
    while True:
        while index < len(body) and body[index] in _PDF_WHITESPACE:
            index += 1
        if body[index : index + 2] == b">>":
            if re.fullmatch(
                rb"[\x00\t\n\x0c\r ]*endobj[\x00\t\n\x0c\r ]*", body[index + 2 :]
            ):
                break
            raise DriverError(error)
        name = _PDF_NAME.match(body, index)
        if name is None or name.group() in seen:
            raise DriverError(error)
        seen.add(name.group())
        index = name.end()
        while index < len(body) and body[index] in _PDF_WHITESPACE:
            index += 1
        end = _pdf_value_end(body, index, error)
        if name.group()[1:] not in PDF_INFO_MASKED_KEYS:
            kept.append(name.group() + b" " + body[index:end])
        index = end
    entries = b"".join(b" " + entry for entry in kept)
    return b"%s %s obj\n<<%s >>\nendobj\n" % (match.group(1), match.group(2), entries)


def _normalized_pdf(payload: bytes) -> bytes:
    """Canonicalize only the registered Info entries, document ID and offsets."""
    prefix, objects, info_key, xref, footer = _pdf_parts(payload)
    parts = [prefix]
    for key, segment in objects:
        parts.append(_canonical_info(segment) if key == info_key else segment)
    return b"".join(parts) + xref + footer


def _validate_png(payload: bytes) -> None:
    """Reject missing/invalid critical chunks, bad CRCs and undecodable pixels."""
    error = "malformed PNG publication output"
    if not payload.startswith(b"\x89PNG\r\n\x1a\n"):
        raise DriverError(error)
    offset = 8
    chunks: list[bytes] = []
    ihdr = b""
    palette_entries = 0
    transparency_length = 0
    while offset < len(payload):
        if offset + 12 > len(payload):
            raise DriverError(error)
        length = int.from_bytes(payload[offset : offset + 4], "big")
        end = offset + 12 + length
        if end > len(payload):
            raise DriverError(error)
        kind = payload[offset + 4 : offset + 8]
        data = payload[offset + 8 : end - 4]
        crc = int.from_bytes(payload[end - 4 : end], "big")
        if (
            re.fullmatch(rb"[A-Za-z]{4}", kind) is None
            or kind[2] & 32
            or (not kind[0] & 32 and kind not in {b"IHDR", b"PLTE", b"IDAT", b"IEND"})
            or zlib.crc32(kind + data) != crc
        ):
            raise DriverError(error)
        chunks.append(kind)
        if kind == b"IEND" and (length != 0 or end != len(payload)):
            raise DriverError(error)
        if kind == b"IHDR":
            ihdr = data
        elif kind == b"PLTE":
            if length == 0 or length % 3 or length > 768:
                raise DriverError(error)
            palette_entries = length // 3
        elif kind == b"tRNS":
            transparency_length = length
        offset = end
    if (
        not chunks
        or chunks[0] != b"IHDR"
        or chunks.count(b"IHDR") != 1
        or b"IDAT" not in chunks
        or chunks[-1] != b"IEND"
        or chunks.count(b"IEND") != 1
        or chunks.count(b"PLTE") > 1
    ):
        raise DriverError(error)
    data_indices = [index for index, kind in enumerate(chunks) if kind == b"IDAT"]
    if data_indices != list(range(data_indices[0], data_indices[-1] + 1)):
        raise DriverError(error)
    valid_depths = {
        0: {1, 2, 4, 8, 16},
        2: {8, 16},
        3: {1, 2, 4, 8},
        4: {8, 16},
        6: {8, 16},
    }
    if len(ihdr) != 13:
        raise DriverError(error)
    width = int.from_bytes(ihdr[:4], "big")
    height = int.from_bytes(ihdr[4:8], "big")
    depth, colour, compression, filtering, interlace = ihdr[8:13]
    palette = b"PLTE" in chunks
    transparency = b"tRNS" in chunks
    if (
        not 0 < width < 2**31
        or not 0 < height < 2**31
        or depth not in valid_depths.get(colour, set())
        or (compression, filtering) != (0, 0)
        or interlace not in {0, 1}
        or (colour == 3 and not palette)
        or (colour in {0, 4} and palette)
        or (colour in {4, 6} and transparency)
        or chunks.count(b"tRNS") > 1
        or (palette and chunks.index(b"PLTE") > data_indices[0])
        or (transparency and chunks.index(b"tRNS") > data_indices[0])
        or (palette and transparency and chunks.index(b"tRNS") < chunks.index(b"PLTE"))
        or (colour == 3 and palette_entries > 2**depth)
        or (colour == 3 and transparency and transparency_length > palette_entries)
        or (colour == 0 and transparency and transparency_length != 2)
        or (colour == 2 and transparency and transparency_length != 6)
    ):
        raise DriverError(error)
    try:
        with Image.open(BytesIO(payload)) as image:
            if image.format != "PNG":
                raise DriverError(error)
            image.verify()
        with Image.open(BytesIO(payload)) as image:
            image.load()
    except (OSError, SyntaxError, ValueError, Image.DecompressionBombError) as exc:
        raise DriverError(error) from exc


def normalized_bytes(payload: bytes, suffix: str) -> bytes:
    """Normalize only the registered publication metadata from captured bytes.

    The normalized representation is a comparison-digest input, not a
    regenerated valid document: PDF normalization rewrites the trailer and
    footer offsets (``startxref 0``), so the result deliberately fails
    ``_pdf_parts`` re-validation. The transform is one-way and deliberately
    non-idempotent — ``normalized_bytes(normalized_bytes(x), ".pdf")``
    raises ``DriverError``. Raw bytes remain the durability artefact.

    Args:
        payload: The same raw bytes used for the raw-size/digest observation.
        suffix: One of ``.tex``, ``.pdf`` or ``.png``.

    Returns:
        Format-specific bytes under the primary §5.4 H3 comparison policy.

    Raises:
        DriverError: If a suffix is unregistered or a registered container is
            malformed.
    """
    if suffix == ".tex":
        return payload.replace(b"\r\n", b"\n")
    if suffix == ".pdf":
        return _normalized_pdf(payload)
    if suffix != ".png":
        raise DriverError(f"unregistered publication format: {suffix}")
    _validate_png(payload)
    with tempfile.TemporaryDirectory(prefix="prin-exp002-r1-normalize-") as directory:
        snapshot = Path(directory) / f"captured{suffix}"
        snapshot.write_bytes(payload)
        return normalize_matplotlib_output(snapshot)


def sensitivity_bytes(payload: bytes, suffix: str) -> bytes:
    """Compare bytes under the pre-exposure §11.3 writer-property diagnostic.

    Args:
        payload: The same raw bytes used for the raw-size/digest observation.
        suffix: One of ``.tex``, ``.pdf`` or ``.png``.

    Returns:
        Format-specific bytes under the pre-exposure sensitivity policy.

    Raises:
        DriverError: If a suffix is unregistered or a container is malformed.
    """
    if suffix == ".tex":
        return payload
    if suffix != ".pdf":
        return normalized_bytes(payload, suffix)
    prefix, objects, info_key, xref, footer = _pdf_parts(payload)
    parts = [prefix]
    for key, segment in objects:
        if info_key is not None and key[0] == info_key[0]:
            segment = re.sub(
                rb"/(CreationDate|ModDate|Creator|Producer)\s+\((?:\\.|[^\\)])*\)",
                rb"/\1 (normalized)",
                segment,
            )
        parts.append(segment)
    return b"".join(parts) + xref + footer


def _font_cache_state() -> dict[str, Any]:
    cache = (
        Path(matplotlib.get_cachedir())
        / f"fontlist-v{font_manager.FontManager.__version__}.json"
    )
    if not cache.exists():
        return {"name": cache.name, "sha256": None}
    return {"name": cache.name, "sha256": _digest(read_no_follow(cache, "font cache"))}


def _render_environment() -> dict[str, Any]:
    fonts = Path(matplotlib.get_data_path()) / "fonts/ttf"
    return {
        "font_cache": _font_cache_state(),
        "matplotlib": matplotlib.__version__,
        "numpy": numpy.__version__,
        "pillow": pillow_version,
        "freetype": ft2font.__freetype_version__,
        "backend": str(matplotlib.get_backend()),
        "font_sha256": {
            path.name: _digest(read_no_follow(path, "renderer font"))
            for path in sorted(fonts.glob("*.ttf"))
        },
    }


def _verify_prin_generators() -> None:
    """Verify origin and SHA-256 pins of PRIN's figure and table generators."""
    for module, relative in (
        (prin_figure_generation, "python/prin/reporting/figure_generation.py"),
        (prin_table_generation, "python/prin/reporting/table_generation.py"),
    ):
        _check_origin(module, ROOT / relative)
        if (
            _digest(read_no_follow(ROOT / relative, "PRIN publication generator"))
            != PRIN_PINS[relative]
        ):
            raise DriverError(f"PRIN publication generator digest changed: {relative}")


def _verify_reference_sources() -> None:
    """Verify every frozen ``prinet`` source pin before it may execute."""
    for relative, pinned in REFERENCE_PINS.items():
        if _digest(read_no_follow(REFERENCE / relative, "reference source")) != pinned:
            raise DriverError(f"reference source digest changed: {relative}")


def _verify_all_pins() -> dict[str, Any]:
    """Re-verify every live governed-source pin registered for E3.

    The pre-registration promises complete pin enforcement at admission and
    finalization — not only inside the branch that happens to use each file —
    so a governed source mutated mid-collection is caught before the run is
    published. Retrospective closure (:func:`check_run_complete`) validates
    the *recorded* provenance claims instead, so analysis hosts are not
    required to hold the registered Windows binary.
    """
    extension = _verify_prin_core_extension()
    _verify_prin_generators()
    _verify_reference_sources()
    return extension


def _pth_directories() -> list[Path]:
    """Return the active interpreter's ``.pth``-processed site directories."""
    candidates: list[Path] = []
    try:
        candidates.extend(Path(entry) for entry in site.getsitepackages())
    except AttributeError:
        pass
    try:
        user_site = site.getusersitepackages()
    except AttributeError:
        user_site = None
    if isinstance(user_site, str):
        candidates.append(Path(user_site))
    candidates.extend(
        Path(entry)
        for entry in sys.path
        if entry and Path(entry).name in {"site-packages", "dist-packages"}
    )
    directories: list[Path] = []
    for candidate in candidates:
        resolved = candidate.resolve()
        if resolved.is_dir() and resolved not in directories:
            directories.append(resolved)
    return directories


def _environment_shadowing() -> list[str]:
    """Detect interpreter paths that could shadow the governed sources.

    Interpreter-level analogue of the repository shadowing scan: a site
    ``.pth`` directory entry or an earlier ``sys.path`` resolution can place
    a second ``prin``/``prinet`` ahead of the governed checkout — the DV-047
    stale-``.pth`` defect class. ``import`` lines inside ``.pth`` files are
    honoured site machinery and out of scope. Absent ``prinet`` is not a
    problem (the reference leg bootstraps ``REFERENCE / "src"`` itself), but
    any ``prinet`` that *does* resolve must resolve to the frozen reference.
    """
    problems: list[str] = []
    governed = {
        (ROOT / "python").resolve(),
        (REFERENCE / "src").resolve(),
    }
    for directory in _pth_directories():
        for pth in sorted(directory.glob("*.pth")):
            try:
                text = read_no_follow(pth, "site .pth").decode("utf-8")
            except (OSError, ReproductionError, UnicodeDecodeError) as exc:
                problems.append(f"site .pth {pth} cannot be assessed: {exc}")
                continue
            for raw_line in text.splitlines():
                line = raw_line.strip()
                if not line or line.startswith(("#", "import ")):
                    continue
                entry = Path(line)
                resolved = (
                    entry.resolve()
                    if entry.is_absolute()
                    else (directory / entry).resolve()
                )
                if resolved in governed or not resolved.is_dir():
                    continue
                if (resolved / "prin").is_dir() or (resolved / "prinet").is_dir():
                    problems.append(
                        f"site path entry {resolved} via {pth} can shadow the "
                        "governed prin/prinet sources"
                    )
    for package, expected in (
        ("prin", ROOT / "python/prin/__init__.py"),
        ("prinet", REFERENCE / "src/prinet/__init__.py"),
    ):
        module = sys.modules.get(package)
        if module is not None:
            module_file = getattr(module, "__file__", None)
            if module_file is None or Path(module_file).resolve() != expected.resolve():
                problems.append(f"preloaded {package} is not the governed source")
            continue
        try:
            spec = importlib.util.find_spec(package)
        except (ImportError, AttributeError, ValueError):
            spec = None
        if spec is None or spec.origin is None:
            if package == "prin":
                problems.append("prin does not resolve at all")
            continue
        if Path(spec.origin).resolve() != expected.resolve():
            problems.append(f"{package} resolves to a non-governed source")
    return problems


def collect_reproduction(
    implementation: str, snapshot: Path, output: Path
) -> dict[str, Any]:
    """Render one matched implementation arm and capture every output byte.

    Args:
        implementation: ``reference`` or ``prin``.
        snapshot: The verified 172-input snapshot.
        output: A fresh publication root in the registered EXP-002-r1 output directory.

    Returns:
        Complete output inventory with raw/normalized/sensitivity sizes and digests.

    Raises:
        DriverError: If provenance, output confinement or file format is invalid.
    """
    _reject_predecessor_path(snapshot, "input snapshot")
    _reject_predecessor_path(output, "publication output")
    resolved_output = _resolved_confinement_path(output, "publication output")
    output_root = OUTPUT_ROOT.resolve()
    if resolved_output == output_root or not resolved_output.is_relative_to(
        output_root
    ):
        raise DriverError("publication output is outside the registered output root")
    _no_symlink_ancestors(output)
    if output.exists():
        raise DriverError("publication output directory must be new")
    renderer = _render_environment()
    if implementation == "prin":
        _verify_prin_core_extension()
        _verify_prin_generators()
        run_reproduction(
            results_dir=snapshot,
            output_dir=output,
            manifest_path=INPUT_MANIFEST,
            verify=True,
        )
    elif implementation == "reference":
        reference_src = (REFERENCE / "src").resolve()
        expected_init = reference_src / "prinet" / "__init__.py"
        if any(name == "prinet" or name.startswith("prinet.") for name in sys.modules):
            raise DriverError(
                "frozen prinet package must not be preloaded before the reference leg"
            )
        _verify_reference_sources()
        if str(reference_src) not in sys.path:
            sys.path.insert(0, str(reference_src))
        importlib.invalidate_caches()
        try:
            spec = importlib.util.find_spec("prinet")
        except (ImportError, AttributeError, ValueError):
            spec = None
        if (
            spec is None
            or spec.origin is None
            or Path(spec.origin).resolve() != expected_init
        ):
            raise DriverError("prinet does not resolve to the frozen reference source")
        modules = []
        for kind in ("figure", "table"):
            relative = f"src/prinet/utils/{kind}_generation.py"
            module = importlib.import_module(f"prinet.utils.{kind}_generation")
            _check_origin(module, REFERENCE / relative)
            modules.append(module)
        modules[0].generate_all_figures(snapshot, output / "figures")
        modules[1].generate_all_tables(snapshot, output / "tables")
    else:
        raise DriverError(f"unregistered implementation: {implementation}")
    files = []
    for path in sorted(output.rglob("*")):
        if path.is_symlink():
            raise DriverError(f"publication output is a symlink: {path}")
        if path.is_dir():
            continue
        if not path.is_file():
            raise DriverError(f"publication output is not a regular file: {path}")
        payload = read_no_follow(path, "generated publication")
        normalized = normalized_bytes(payload, path.suffix)
        sensitivity = sensitivity_bytes(payload, path.suffix)
        name = path.relative_to(output).as_posix()
        record = {
            "path": name,
            "raw_bytes": len(payload),
            "raw_sha256": _digest(payload),
            "normalized_bytes": len(normalized),
            "normalized_sha256": _digest(normalized),
            "sensitivity_bytes": len(sensitivity),
            "sensitivity_sha256": _digest(sensitivity),
        }
        if name.startswith("tables/") and name in EXPECTED_FILES:
            archived = read_no_follow(REFERENCE / "paper" / name, "archived table")
            archived_normalized = normalized_bytes(archived, ".tex")
            record["archived_bytes"] = len(archived)
            record["archived_sha256"] = _digest(archived)
            record["archived_normalized_bytes"] = len(archived_normalized)
            record["archived_normalized_sha256"] = _digest(archived_normalized)
        files.append(record)
    verify_manifest(snapshot, INPUT_MANIFEST)
    if renderer != _render_environment():
        raise DriverError("renderer/font environment changed during generation")
    return {
        "implementation": implementation,
        "renderer": renderer,
        "expected_files": sorted(EXPECTED_FILES),
        "files": files,
        "unit": "generated_file",
    }


def _approval_date(protocol_bytes: bytes) -> str:
    """Return the dated MichaelMaillet approval of an APPROVED protocol."""
    try:
        protocol = protocol_bytes.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise DriverError("pre-registration is not UTF-8 text") from exc
    status = re.search(r"^\*\*Status:\*\*[ \t]*([^\r\n]+)", protocol, re.M)
    if status is None or status.group(1).strip() != "APPROVED":
        raise DriverError("EXP-002-r1 is not APPROVED; E1 must not execute")
    approval_field = re.search(
        r"^\*\*Maintainer approval:\*\*[ \t]*([^\r\n]+)",
        protocol,
        re.M,
    )
    approval = re.match(
        r"MichaelMaillet, (\d{4}-\d{2}-\d{2}) UTC\b",
        approval_field.group(1) if approval_field else "",
    )
    if approval is None:
        raise DriverError("dated MichaelMaillet scientific approval is missing")
    try:
        datetime.strptime(approval.group(1), "%Y-%m-%d")
    except ValueError as exc:
        raise DriverError("dated MichaelMaillet approval is not a real date") from exc
    return approval.group(1)


def _admission(source_sha: str) -> dict[str, Any]:
    protocol_bytes = read_no_follow(PROTOCOL, "pre-registration")
    approval_date = _approval_date(protocol_bytes)
    extension = _verify_all_pins()
    if (
        not re.fullmatch(r"[0-9a-f]{40}", source_sha)
        or _git("rev-parse", "HEAD") != source_sha
    ):
        raise DriverError("--source-sha must be the current full 40-character HEAD")
    protocol_relative = PROTOCOL.relative_to(ROOT).as_posix()
    log_relative = PROTOCOL.parent.relative_to(ROOT).as_posix() + "/log.md"
    raw_relative = RAW_ROOT.relative_to(ROOT).as_posix()
    changed = _git(
        "diff",
        "--name-only",
        "HEAD",
        "--",
        ".",
        f":!{log_relative}",
    )
    untracked = _git(
        "ls-files",
        "--others",
        "--exclude-standard",
        "--",
        ".",
        f":!{raw_relative}",
        f":!{log_relative}",
    )
    shadowing = _git("ls-files", "--others", "--", *_SHADOW_PATHSPECS)
    source_untracked = [
        path
        for path in untracked.splitlines()
        if not path.startswith(f"{raw_relative}/")
    ]
    if changed or source_untracked or shadowing:
        raise DriverError("uncommitted source/protocol changes invalidate execution")
    if _git_bytes("show", f"HEAD:{protocol_relative}") != protocol_bytes:
        raise DriverError("working pre-registration differs from its committed bytes")
    environment_problems = _environment_shadowing()
    if environment_problems:
        raise DriverError(
            "import-shadowing environment is unsafe: " + "; ".join(environment_problems)
        )
    return {
        "source_sha": source_sha,
        "preregistration_sha256": _digest(protocol_bytes),
        "preregistration_commit": _git(
            "log", "-1", "--format=%H", "--", protocol_relative
        ),
        "approval_date_utc": approval_date,
        **extension,
    }


def _utc_stamp(stamp: str) -> None:
    try:
        datetime.strptime(stamp, "%Y%m%dT%H%M%SZ")
    except ValueError as exc:
        raise DriverError("run name UTC stamp is not a real registered time") from exc


def _reserve(mode: str, run_dir: Path, source_sha: str) -> Path:
    _reject_predecessor_path(run_dir, "run directory")
    # Direct-child equality on the unresolved absolute path is correct here:
    # `..` was already rejected above, and resolving now would silently
    # follow a symlinked RAW_ROOT before `_no_symlink_ancestors` can see it.
    run = run_dir.absolute()
    match = RUN_PATTERN.fullmatch(run.name)
    if (
        mode not in MODE_LABELS
        or match is None
        or match.group("label") != MODE_LABELS[mode]
        or match.group("sha") != source_sha[:7]
        or run.parent != RAW_ROOT.absolute()
    ):
        raise DriverError("run path/label/SHA is not the registered direct-child path")
    _utc_stamp(match.group("utc"))
    _no_symlink_ancestors(run)
    if not run.parent.is_dir():
        raise DriverError("EXP-002-r1 raw root is missing")
    generated = OUTPUT_ROOT / run.name
    _reject_predecessor_path(generated, "generated output")
    if generated.exists() or generated.is_symlink():
        raise DriverError("generated-output run root is never reused")
    try:
        run.mkdir()
    except FileExistsError as exc:
        raise DriverError("a RUN directory is never reused") from exc
    return run


def _storage_check(run: Path, prospective_bytes: int = 0) -> None:
    """Validate the run's tracked storage, including pending final bytes.

    ``prospective_bytes`` accounts for the result/manifest bytes not yet on
    disk when the check runs before publication: an over-budget run must be
    rejected *before* its completed record is published, not only after the
    fact. ``run`` is already inside ``RAW_ROOT``, so the pending bytes are
    added exactly once.
    """

    def size(root: Path) -> int:
        return sum(
            stat_size_and_hash_no_follow(path, "campaign storage")[0]
            for path in root.rglob("*")
            if path.is_file() and "__pycache__" not in path.parts
        )

    try:
        if size(run) + prospective_bytes > RUN_CAP:
            raise DriverError("registered 2 MiB per-run cap exceeded")
        record_root = PROTOCOL.parent
        r1_total = size(RAW_ROOT) + size(record_root) + prospective_bytes
        if r1_total > RAW_CAP:
            raise DriverError(
                "registered EXP-002-r1 10 MiB tracked-storage cap exceeded"
            )
        predecessor_total = (
            size(PREDECESSOR_RAW_ROOT) if PREDECESSOR_RAW_ROOT.is_dir() else 0
        ) + (size(PREDECESSOR_RECORD_ROOT) if PREDECESSOR_RECORD_ROOT.is_dir() else 0)
        if r1_total + predecessor_total > COMBINED_EXP002_CAP:
            raise DriverError(
                "combined EXP-002 + EXP-002-r1 10 MiB tracked-storage cap exceeded"
            )
        campaign_total = (
            sum(size(root) for root in RAW_ROOT.parent.glob("EXP-*") if root.is_dir())
            + prospective_bytes
        )
    except (OSError, ReproductionError) as exc:
        raise DriverError(f"tracked storage cannot be measured: {exc}") from exc
    if campaign_total > 64 * 1024 * 1024:
        raise DriverError("campaign-wide 64 MiB tracked-storage cap exceeded")


def _check_provenance(identity: Mapping[str, Any], source_sha: str) -> None:
    """Bind a presented record to the committed protocol that authorized it."""
    digest = identity.get("preregistration_sha256")
    commit = identity.get("preregistration_commit")
    approval_date = identity.get("approval_date_utc")
    pyd_sha = identity.get("prin_core_pyd_sha256")
    pyd_bytes = identity.get("prin_core_pyd_bytes")
    if (
        not isinstance(digest, str)
        or not re.fullmatch(r"[0-9a-f]{64}", digest)
        or not isinstance(commit, str)
        or not re.fullmatch(r"[0-9a-f]{40}", commit)
        or not isinstance(approval_date, str)
        or pyd_sha != PRIN_CORE_PYD_SHA256
        or type(pyd_bytes) is not int
        or pyd_bytes != PRIN_CORE_PYD_BYTES
    ):
        raise DriverError("pre-registration provenance fields are missing or malformed")
    protocol_relative = PROTOCOL.relative_to(ROOT).as_posix()
    try:
        committed = _git_bytes("show", f"{commit}:{protocol_relative}")
        merge_base = _git("merge-base", commit, source_sha)
    except subprocess.SubprocessError as exc:
        raise DriverError(
            "recorded pre-registration commit cannot be resolved"
        ) from exc
    if _digest(committed) != digest:
        raise DriverError(
            "recorded pre-registration digest is not the committed protocol"
        )
    if _approval_date(committed) != approval_date:
        raise DriverError("recorded approval date is not the committed protocol's")
    if merge_base != commit:
        raise DriverError("pre-registration commit is not an ancestor of the source")


def _string_list(value: object, context: str) -> list[str]:
    items = _list(value, context)
    if not all(isinstance(item, str) for item in items):
        raise DriverError(f"{context}: expected strings")
    return cast("list[str]", items)


def _check_observations(mode: str, value: object) -> None:
    """Validate the collected payload's schema and identities, not its outcome."""
    observations = _mapping(value, "observations")
    if mode == "api":
        expected = _string_list(observations.get("expected_names"), "expected names")
        _string_list(observations.get("legacy_names"), "legacy names")
        _string_list(observations.get("observed_names"), "observed names")
        _string_list(observations.get("frozen_missing"), "frozen missing")
        _string_list(observations.get("frozen_extra"), "frozen extra")
        rows = [
            _mapping(row, "API row")
            for row in _list(observations.get("rows"), "API rows")
        ]
        if (
            observations.get("unit") != "api_symbol"
            or len(expected) != API_SYMBOL_COUNT
            or len(set(expected)) != API_SYMBOL_COUNT
            or any(set(row) != _API_ROW_KEYS for row in rows)
            or [row["name"] for row in rows] != sorted(expected)
        ):
            raise DriverError("api observations are not the registered census schema")
    elif mode == "conclusions":
        cases = [
            _mapping(case, "claim case")
            for case in _list(observations.get("cases"), "claim cases")
        ]
        if (
            observations.get("unit") != "claim_comparator_record"
            or len(cases) != CLAIM_CASE_COUNT
            or any(not _CASE_KEYS <= set(case) for case in cases)
            or any(not isinstance(case["case_id"], str) for case in cases)
            or len({case["case_id"] for case in cases}) != CLAIM_CASE_COUNT
            or any(type(case["observed"]) is not bool for case in cases)
            or any(type(case["expected"]) is not bool for case in cases)
        ):
            raise DriverError("claim observations are not the registered census schema")
    else:
        files = [
            _mapping(item, "publication file")
            for item in _list(observations.get("files"), "publication files")
        ]
        paths = [item.get("path") for item in files]
        if (
            observations.get("unit") != "generated_file"
            or observations.get("implementation")
            != ("reference" if mode == "reference" else "prin")
            or observations.get("expected_files") != sorted(EXPECTED_FILES)
            or not isinstance(observations.get("renderer"), dict)
            or not all(isinstance(path, str) for path in paths)
            or len(set(paths)) != len(paths)
            or any(
                type(item.get(key)) is not int or item[key] < 0
                for item in files
                for key in _FILE_INT_KEYS
            )
            or any(
                not isinstance(item.get(key), str)
                or not re.fullmatch(r"[0-9a-f]{64}", item[key])
                for item in files
                for key in _FILE_DIGEST_KEYS
            )
        ):
            raise DriverError("publication observations are not the registered schema")


def check_run_complete(run_dir: Path) -> None:
    """Validate a run's manifest, sidecar, envelope and completion status.

    Args:
        run_dir: The direct-child registered run directory under ``EXP-002-r1``.

    Raises:
        DriverError: If the record is invalid, aborted, incomplete, or under
            the forbidden predecessor ``EXP-002`` root.
    """
    _reject_predecessor_path(run_dir, "run directory")
    match = RUN_PATTERN.fullmatch(run_dir.name)
    if (
        match is None
        or run_dir.parent.absolute() != RAW_ROOT.absolute()
        or run_dir.is_symlink()
        or RAW_ROOT.is_symlink()
    ):
        raise DriverError("invalid registered run directory")
    _utc_stamp(match.group("utc"))
    _no_symlink_ancestors(run_dir)
    records = verify_manifest(run_dir, run_dir / "manifest.json")
    inventory = {record.path: record for record in records}

    def read(name: str) -> dict[str, Any]:
        record: ManifestRecord | None = inventory.get(name)
        if record is None:
            raise DriverError(f"required manifested file missing: {name}")
        return _mapping(
            json.loads(
                read_verified_no_follow(
                    run_dir / name, record.bytes, record.sha256, name, "run record"
                )
            ),
            name,
        )

    metadata = read("campaign-metadata.json")
    mode = metadata.get("mode")
    if not isinstance(mode, str) or mode not in MODE_LABELS:
        raise DriverError("invalid metadata mode")
    result_name = (
        f"{mode}.json" if mode in {"api", "conclusions"} else "reproduction.json"
    )
    declared = {"campaign-metadata.json", result_name}
    if not declared <= set(inventory) <= declared | {"abort.json"}:
        raise DriverError("run inventory is not exactly the declared sidecar/result")
    if {entry.name for entry in run_dir.iterdir()} != set(inventory) | {
        "manifest.json"
    }:
        raise DriverError("run inventory holds an undeclared directory entry")
    if "abort.json" in inventory:
        raise DriverError(
            "run carries a manifested abort record and can never be admissible"
        )
    if (
        metadata.get("exp_id") != EXP_ID
        or metadata.get("session") != SESSION_ID
        or metadata.get("run_id") != run_dir.name
        or metadata.get("artefacts") != {result_name: MODE_TAGS[mode]}
        or not isinstance(metadata.get("operator"), str)
        or not metadata["operator"].strip()
        or match.group("label") != MODE_LABELS[mode]
    ):
        raise DriverError("campaign metadata/labels do not match the registered run")
    result = read(result_name)
    environment = _mapping(result.get("environment"), "environment")
    config = _mapping(result.get("config"), "config")
    identity = _mapping(result.get("identity"), "identity")
    source_sha = environment.get("git_commit")
    stored_out = config.get("out_dir")
    stored_parts = (
        PurePosixPath(stored_out.replace("\\", "/")).parts
        if isinstance(stored_out, str)
        else ()
    )
    expected_tail = (*RAW_ROOT.parts[-3:], run_dir.name)
    if (
        result.get("status") != "COMPLETED"
        or not isinstance(source_sha, str)
        or not re.fullmatch(r"[0-9a-f]{40}", source_sha)
        or source_sha[:7] != match.group("sha")
        or identity.get("source_sha") != source_sha
        or identity.get("input_manifest_sha256") != INPUT_MANIFEST_SHA
        or identity.get("input_record_count") != 172
        or type(config.get("seed_counter")) is not int
        or type(config.get("seed_key")) is not int
        or config.get("seed_counter") != 0
        or config.get("seed_key") != 2
        or type(config.get("iterations")) is not int
        or config.get("iterations") != 10
        or type(config.get("warmup")) is not int
        or config.get("warmup") != 0
        or type(config.get("replicates")) is not int
        or config.get("replicates") != 1
        or config.get("measurement_kind") != "deterministic_census"
        or ".." in stored_parts
        or stored_parts[-4:] != expected_tail
        or type(environment.get("seed")) is not int
        or environment.get("seed") != 0
        or environment.get("backend") != "cpu"
        or environment.get("dtype") != "f64"
        or environment.get("prin_version") != "1.0.0rc1"
        or result.get("seed_used") is not False
    ):
        raise DriverError("result status/provenance/config is not admissible")
    for name in (
        "prin_version",
        "rust_version",
        "python_version",
        "platform",
        "processor",
    ):
        if not isinstance(environment.get(name), str) or not environment[name].strip():
            raise DriverError(f"required environment field missing: {name}")
    if (
        type(environment.get("logical_cpus")) is not int
        or environment["logical_cpus"] < 1
    ):
        raise DriverError("required logical CPU count is invalid")
    _check_observations(mode, result.get("observations"))
    _check_provenance(identity, source_sha)
    _storage_check(run_dir)


def run_registered(
    mode: str,
    run_dir: Path,
    operator: str,
    source_sha: str,
    seed_counter: int = 0,
    seed_key: int = 2,
) -> Path:
    """Collect one approved EXP-002-r1 leg, preserving aborted attempts.

    Args:
        mode: One of the five registered mode names.
        run_dir: New, correctly labelled RUN directory under ``EXP-002-r1``.
        operator: Actual operator, recorded in the campaign sidecar.
        source_sha: Exact clean execution HEAD, never the historical baseline.
        seed_counter: The documentary replicate-0 counter.
        seed_key: The registered EXP-002-r1 key (2).

    Returns:
        The closed, admissible run directory; no scientific verdict is returned.

    Raises:
        DriverError: If approval, admission, collection or closure fails.
    """
    _reject_predecessor_path(run_dir, "run directory")
    identity = _admission(source_sha)
    if (seed_counter, seed_key) != (0, 2) or not operator.strip():
        raise DriverError(
            "registered seed pair (0,2) and a named operator are required"
        )
    environment = capture_environment(backend="cpu", dtype="f64", seed=0)
    if (
        environment["git_commit"] != source_sha
        or environment["prin_version"] != "1.0.0rc1"
    ):
        raise DriverError("environment source/version does not match the execution")
    started = time.monotonic()
    started_at = datetime.now(UTC).isoformat()
    _no_symlink_ancestors(OUTPUT_ROOT)
    run = _reserve(mode, run_dir, source_sha)
    generated = OUTPUT_ROOT / run.name
    result_name = (
        f"{mode}.json" if mode in {"api", "conclusions"} else "reproduction.json"
    )
    config_object = BenchmarkConfig(
        iterations=10,
        warmup=0,
        seed_counter=0,
        seed_key=2,
        out_dir=run,
    )
    config = {
        "iterations": config_object.iterations,
        "warmup": config_object.warmup,
        "seed_counter": 0,
        "seed_key": 2,
        "out_dir": str(run),
        "measurement_kind": "deterministic_census",
        "replicates": 1,
    }
    payload: dict[str, Any] = {"identity": identity, "seed_used": False}
    failed: Exception | None = None
    try:
        write_json_exclusive(
            run / "campaign-metadata.json",
            {
                "exp_id": EXP_ID,
                "session": SESSION_ID,
                "run_id": run.name,
                "operator": operator,
                "mode": mode,
                "artefacts": {result_name: MODE_TAGS[mode]},
            },
            conflict_message="campaign sidecar already exists",
        )
        OUTPUT_ROOT.mkdir(parents=True, exist_ok=True)
        generated.mkdir()
        _no_symlink_ancestors(generated)
        documents, input_identity = _snapshot(generated / "inputs")
        identity.update(input_identity)
        if mode == "api":
            observations = collect_api()
        elif mode == "conclusions":
            observations = collect_conclusions(documents)
        else:
            observations = collect_reproduction(
                "reference" if mode == "reference" else "prin",
                generated / "inputs",
                generated / "publication",
            )
        payload["observations"] = observations
        payload["status"] = "COMPLETED"
        if time.monotonic() - started > CPU_WALL_CAP:
            raise DriverError("registered CPU wall cap exceeded")
    except Exception as exc:
        failed = exc
        payload["status"] = "ABORTED"
        payload["abort_reason"] = f"{type(exc).__name__}: {exc}"
    payload["elapsed_seconds"] = time.monotonic() - started
    payload["started_at_utc"] = started_at
    payload["recorded_at_utc"] = datetime.now(UTC).isoformat()
    if failed is None:
        # Live pin re-verification and the prospective storage-cap check run
        # before the completed record is published: a governed source mutated
        # mid-collection or a run that would exceed a registered cap aborts
        # here instead of leaving a manifested COMPLETED record.
        try:
            _verify_all_pins()
            artefact = {"environment": environment, "config": config, **payload}
            prospective = len(
                json.dumps(
                    artefact,
                    indent=2,
                    sort_keys=True,
                    ensure_ascii=False,
                ).encode("utf-8")
            )
            _storage_check(run, prospective + _FINALIZATION_ALLOWANCE)
        except Exception as exc:
            failed = exc
            payload["status"] = "ABORTED"
            payload["abort_reason"] = f"finalization: {type(exc).__name__}: {exc}"
    write_result(
        run / result_name,
        environment=environment,
        config=config,
        payload=payload,
    )
    if failed is not None:
        # The manifested abort record makes the rejected run durably
        # inadmissible: manifest verification forbids removing it, and
        # append-only writes forbid adding one to an accepted run.
        write_json_exclusive(
            run / "abort.json",
            {
                "exp_id": EXP_ID,
                "session": SESSION_ID,
                "run_id": run.name,
                "abort_reason": payload["abort_reason"],
                "recorded_at_utc": payload["recorded_at_utc"],
            },
            conflict_message="abort record already exists",
        )
    append_manifest(run, run / "manifest.json")
    if failed is not None:
        raise DriverError(f"aborted run retained: {run}; {failed}") from failed
    check_run_complete(run)
    return run


def main(argv: list[str] | None = None) -> int:
    """Parse and execute one approved EXP-002-r1 collection leg."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--mode", choices=tuple(MODE_LABELS), required=True)
    parser.add_argument("--run-dir", type=Path, required=True)
    parser.add_argument("--operator", required=True)
    parser.add_argument("--source-sha", required=True)
    parser.add_argument("--seed-counter", type=int, default=0)
    parser.add_argument("--seed-key", type=int, default=2)
    args = parser.parse_args(argv)
    try:
        run_registered(
            args.mode,
            args.run_dir,
            args.operator,
            args.source_sha,
            args.seed_counter,
            args.seed_key,
        )
    except (
        DriverError,
        OSError,
        ValueError,
        ReproductionError,
        subprocess.SubprocessError,
    ) as exc:
        print(f"EXP-002-r1 NOT COMPLETED: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
