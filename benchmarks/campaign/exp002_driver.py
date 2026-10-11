"""Collect the registered EXP-002 deterministic censuses and publication arms.

This E1 driver collects observations, not hypothesis verdicts. Its CLI refuses
to create a run while the committed pre-registration is DRAFT. Unit tests use
controlled fixtures; importing this module does not execute an experiment.
"""

from __future__ import annotations

import argparse
import ast
import hashlib
import importlib
import json
import math
import re
import shutil
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
from matplotlib import ft2font
from PIL import Image
from PIL import __version__ as pillow_version
from prin._deprecation import verify_api_surface
from prin.reporting.figure_generation import normalize_matplotlib_output

from benchmarks._common.config import BenchmarkConfig
from benchmarks._common.environment import capture_environment
from benchmarks._common.result import write_json_exclusive, write_result
from tools.reproduce import (
    ManifestRecord,
    append_manifest,
    read_no_follow,
    read_verified_no_follow,
    run_reproduction,
    stat_size_and_hash_no_follow,
    verify_manifest,
)

ROOT = Path(__file__).resolve().parents[2]
REFERENCE = ROOT / "DOCS/archive and reference from PRINet 3.0/PRINet-3.0.0-main"
RAW_ROOT = ROOT / "benchmarks/results/EXP-002"
OUTPUT_ROOT = ROOT / "DOCS/test_and_benchmark_results/EXP-002"
PROTOCOL = (
    ROOT
    / "DOCS/experiments/EXP-002-api-benchmark-result-and-reproduction-parity"
    / "preregistration.md"
)
INPUT_MANIFEST = ROOT / "paper/artefact_manifest.json"
INPUT_MANIFEST_SHA = "300cdc094d2b7d27ac8b1e2556b2e6ed4dad3333f0038b45c8f87ea81612cce5"
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
    "api": "api-cpu",
    "conclusions": "conclusions-cpu",
    "reference": "reproduction-reference-cpu",
    "prin": "reproduction-prin-cpu",
    "repeatability": "seedrep0-prin-cpu",
}
MODE_TAGS = {
    "api": ["H1"],
    "conclusions": ["H2"],
    "reference": ["H3"],
    "prin": ["H3", "H4"],
    "repeatability": ["H4"],
}
RUN_PATTERN = re.compile(
    r"RUN-(?P<utc>\d{8}T\d{6}Z)-(?P<sha>[0-9a-f]{7})-(?P<label>[a-z0-9-]+)\Z"
)
RUN_CAP = 2 * 1024 * 1024
RAW_CAP = 10 * 1024 * 1024
CPU_WALL_CAP = 12 * 60 * 60


class DriverError(RuntimeError):
    """Report an invalid or unavailable registered collection operation."""


def _git(*args: str) -> str:
    executable = shutil.which("git")
    if executable is None:
        raise DriverError("git is unavailable; source identity cannot be established")
    result = subprocess.run(
        [executable, *args],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=True,
        timeout=30,
    )
    return result.stdout.strip()


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


def _no_symlink_ancestors(path: Path) -> None:
    for ancestor in (path.absolute(), *path.absolute().parents):
        if ancestor.is_symlink():
            raise DriverError(f"output path has a symlink ancestor: {ancestor}")


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
    legacy = set(_legacy_names())
    expected = legacy | PRIN_ADDITIONS
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
            row = {"name": name, "resolved": False, "error": str(exc)}
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
        DriverError: If the registered input schema or population is invalid.
    """
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
    return {"cases": cases, "unit": "claim_comparator_record"}


def _snapshot(destination: Path) -> tuple[dict[str, dict[str, Any]], dict[str, Any]]:
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
) -> tuple[bytes, list[tuple[int, bytes]], int | None, bytes, bytes]:
    """Validate the registered classic-xref container and locate its objects.

    The PDF subset is Matplotlib's single-revision, classic-xref output. This
    is container validation, not a general PDF interpreter. Canonical
    comparison bytes are not promised to be renderable: raw bytes remain the
    H4/reconstruction input.
    """
    error = "malformed PDF publication output (classic-xref container required)"
    if re.match(rb"%PDF-(?:1\.[0-7]|2\.0)[\r\n]", payload) is None:
        raise DriverError(error)
    footer = re.search(
        rb"(?m)^startxref[ \t]*[\r\n]+([0-9]+)[ \t]*[\r\n]+%%EOF[ \t\r\n]*\Z",
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
        subsection = re.fullmatch(rb"([0-9]+)[ \t]+([0-9]+)", lines[index].strip())
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
    size = re.search(rb"/Size\s+([0-9]+)\b", dictionary.group(1))
    root = re.search(rb"/Root\s+([0-9]+)\s+([0-9]+)\s+R\b", dictionary.group(1))
    if (
        size is None
        or int(size.group(1)) != max(number for number, _ in entries) + 1
        or root is None
    ):
        raise DriverError(error)
    root_key = (int(root.group(1)), int(root.group(2)))
    if entries.get(root_key, (0, b"f"))[1] != b"n":
        raise DriverError(error)
    info = re.search(rb"/Info\s+([0-9]+)\s+([0-9]+)\s+R\b", dictionary.group(1))
    info_number = None
    if info is not None:
        info_key = (int(info.group(1)), int(info.group(2)))
        if entries.get(info_key, (0, b"f"))[1] != b"n":
            raise DriverError(error)
        info_number = info_key[0]
    in_use = sorted(
        (position, number, generation)
        for (number, generation), (position, kind) in entries.items()
        if kind == b"n"
    )
    if not in_use or len({position for position, _, _ in in_use}) != len(in_use):
        raise DriverError(error)
    objects: list[tuple[int, bytes]] = []
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
        if number == info_number and re.search(rb"(?m)^stream[\r\n]", segment):
            raise DriverError(error)
        objects.append((number, segment))
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
        info_number,
        b"".join(canonical),
        canonical_footer,
    )


def _normalized_pdf(payload: bytes) -> bytes:
    """Mask only registered Info fields, document ID and relocation offsets."""
    prefix, objects, info_number, xref, footer = _pdf_parts(payload)
    parts = [prefix]
    for number, segment in objects:
        if number == info_number:
            segment = re.sub(
                rb"/(CreationDate|ModDate|Creator|Producer)\s+\((?:\\.|[^\\)])*\)",
                rb"/\1 (normalized)",
                segment,
            )
        parts.append(segment)
    return b"".join(parts) + xref + footer


def _validate_png(payload: bytes) -> None:
    """Reject missing/invalid critical chunks, bad CRCs and undecodable pixels."""
    error = "malformed PNG publication output"
    if not payload.startswith(b"\x89PNG\r\n\x1a\n"):
        raise DriverError(error)
    offset = 8
    chunks: list[bytes] = []
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

    Args:
        payload: The same raw bytes used for the raw-size/digest observation.
        suffix: One of ``.tex``, ``.pdf`` or ``.png``.

    Returns:
        Format-specific bytes under the pre-registered H3 comparison policy.

    Raises:
        DriverError: If a suffix is unregistered or a registered container is
            malformed.
    """
    if suffix == ".tex":
        return payload
    if suffix == ".pdf":
        return _normalized_pdf(payload)
    if suffix != ".png":
        raise DriverError(f"unregistered publication format: {suffix}")
    _validate_png(payload)
    # The existing path-based normalizer reads a private copy of the captured
    # bytes, so raw and normalized digests never describe two different opens.
    with tempfile.TemporaryDirectory(prefix="prin-exp002-normalize-") as directory:
        snapshot = Path(directory) / f"captured{suffix}"
        snapshot.write_bytes(payload)
        return normalize_matplotlib_output(snapshot)


def _render_environment() -> dict[str, Any]:
    fonts = Path(matplotlib.get_data_path()) / "fonts/ttf"
    return {
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


def collect_reproduction(
    implementation: str, snapshot: Path, output: Path
) -> dict[str, Any]:
    """Render one matched implementation arm and capture every output byte.

    Args:
        implementation: ``reference`` or ``prin``.
        snapshot: The verified 172-input snapshot.
        output: A fresh publication root in the registered output directory.

    Returns:
        Complete output inventory with raw/normalized sizes and digests.

    Raises:
        DriverError: If provenance, output confinement or file format is invalid.
    """
    if (
        not output.absolute().is_relative_to(OUTPUT_ROOT.absolute())
        or output.absolute() == OUTPUT_ROOT.absolute()
    ):
        raise DriverError("publication output is outside the registered output root")
    _no_symlink_ancestors(output)
    if output.exists():
        raise DriverError("publication output directory must be new")
    renderer = _render_environment()
    if implementation == "prin":
        run_reproduction(
            results_dir=snapshot,
            output_dir=output,
            manifest_path=INPUT_MANIFEST,
            verify=True,
        )
    elif implementation == "reference":
        modules = []
        for kind in ("figure", "table"):
            relative = f"src/prinet/utils/{kind}_generation.py"
            module = importlib.import_module(f"prinet.utils.{kind}_generation")
            _check_origin(module, REFERENCE / relative)
            if (
                _digest(read_no_follow(REFERENCE / relative, "reference generator"))
                != REFERENCE_PINS[relative]
            ):
                raise DriverError("reference publication generator changed")
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
        name = path.relative_to(output).as_posix()
        record = {
            "path": name,
            "raw_bytes": len(payload),
            "raw_sha256": _digest(payload),
            "normalized_bytes": len(normalized),
            "normalized_sha256": _digest(normalized),
        }
        if name.startswith("tables/") and name in EXPECTED_FILES:
            archived = read_no_follow(REFERENCE / "paper" / name, "archived table")
            record["archived_bytes"] = len(archived)
            record["archived_sha256"] = _digest(archived)
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


def _admission(source_sha: str) -> dict[str, Any]:
    protocol_bytes = read_no_follow(PROTOCOL, "pre-registration")
    protocol = protocol_bytes.decode("utf-8")
    status = re.search(r"^\*\*Status:\*\*[ \t]*([^\r\n]+)", protocol, re.M)
    if status is None or status.group(1).strip() != "APPROVED":
        raise DriverError("EXP-002 is not APPROVED; E1 must not execute")
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
    datetime.strptime(approval.group(1), "%Y-%m-%d")
    if (
        not re.fullmatch(r"[0-9a-f]{40}", source_sha)
        or _git("rev-parse", "HEAD") != source_sha
    ):
        raise DriverError("--source-sha must be the current full 40-character HEAD")
    protocol_relative = PROTOCOL.relative_to(ROOT).as_posix()
    changed = _git(
        "diff",
        "--name-only",
        "HEAD",
        "--",
        ".",
        ":!benchmarks/results",
        ":!DOCS/experiments/EXP-002-api-benchmark-result-and-reproduction-parity/log.md",
    )
    untracked = _git(
        "ls-files",
        "--others",
        "--exclude-standard",
        "--",
        "crates",
        "python",
        "benchmarks",
        "parity",
        "tools",
        "paper",
        protocol_relative,
    )
    source_untracked = [
        path
        for path in untracked.splitlines()
        if not path.startswith("benchmarks/results/")
    ]
    if changed or source_untracked:
        raise DriverError("uncommitted source/protocol changes invalidate execution")
    committed = _git("show", f"HEAD:{protocol_relative}")
    if committed != protocol.strip():
        raise DriverError("working pre-registration differs from its committed bytes")
    return {
        "source_sha": source_sha,
        "preregistration_sha256": _digest(protocol_bytes),
        "preregistration_commit": _git(
            "log", "-1", "--format=%H", "--", protocol_relative
        ),
        "approval_date_utc": approval.group(1),
    }


def _reserve(mode: str, run_dir: Path, source_sha: str) -> Path:
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
    datetime.strptime(match.group("utc"), "%Y%m%dT%H%M%SZ")
    _no_symlink_ancestors(run)
    if not run.parent.is_dir():
        raise DriverError("EXP-002 raw root is missing")
    try:
        run.mkdir()
    except FileExistsError as exc:
        raise DriverError("a RUN directory is never reused") from exc
    return run


def _storage_check(run: Path) -> None:
    def size(root: Path) -> int:
        return sum(
            stat_size_and_hash_no_follow(path, "campaign storage")[0]
            for path in root.rglob("*")
            if path.is_file() and "__pycache__" not in path.parts
        )

    if size(run) > RUN_CAP:
        raise DriverError("registered 2 MiB per-run cap exceeded")
    record_root = PROTOCOL.parent
    if size(RAW_ROOT) + size(record_root) > RAW_CAP:
        raise DriverError("registered EXP-002 10 MiB tracked-storage cap exceeded")
    campaign_total = sum(
        size(root) for root in RAW_ROOT.parent.glob("EXP-*") if root.is_dir()
    )
    if campaign_total > 64 * 1024 * 1024:
        raise DriverError("campaign-wide 64 MiB tracked-storage cap exceeded")


def check_run_complete(run_dir: Path) -> None:
    """Validate a run's manifest, sidecar, envelope and completion status.

    Args:
        run_dir: The direct-child registered run directory.

    Raises:
        DriverError: If the record is invalid, aborted or incomplete.
    """
    match = RUN_PATTERN.fullmatch(run_dir.name)
    if (
        match is None
        or run_dir.parent.absolute() != RAW_ROOT.absolute()
        or run_dir.is_symlink()
        or RAW_ROOT.is_symlink()
    ):
        raise DriverError("invalid registered run directory")
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
    if set(inventory) != {"campaign-metadata.json", result_name}:
        raise DriverError("run inventory is not exactly the declared sidecar/result")
    if (
        metadata.get("exp_id") != "EXP-002"
        or metadata.get("session") != "0161"
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
        or not re.fullmatch(
            r"[0-9a-f]{64}", str(identity.get("preregistration_sha256", ""))
        )
        or not re.fullmatch(
            r"[0-9a-f]{40}", str(identity.get("preregistration_commit", ""))
        )
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
    _storage_check(run_dir)


def run_registered(
    mode: str,
    run_dir: Path,
    operator: str,
    source_sha: str,
    seed_counter: int = 0,
    seed_key: int = 2,
) -> Path:
    """Collect one approved leg, preserving aborted and incomplete attempts.

    Args:
        mode: One of the five registered mode names.
        run_dir: New, correctly labelled RUN directory under the EXP-002 root.
        operator: Actual operator, recorded in the campaign sidecar.
        source_sha: Exact clean execution HEAD, never the historical baseline.
        seed_counter: The documentary replicate-0 counter.
        seed_key: The registered EXP-002 key.

    Returns:
        The closed, admissible run directory; no scientific verdict is returned.

    Raises:
        DriverError: If approval, admission, collection or closure fails.
    """
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
    if generated.exists() or generated.is_symlink():
        raise DriverError("generated-output run root is never reused")
    generated.mkdir(parents=True)
    result_name = (
        f"{mode}.json" if mode in {"api", "conclusions"} else "reproduction.json"
    )
    write_json_exclusive(
        run / "campaign-metadata.json",
        {
            "exp_id": "EXP-002",
            "session": "0161",
            "run_id": run.name,
            "operator": operator,
            "mode": mode,
            "artefacts": {result_name: MODE_TAGS[mode]},
        },
        conflict_message="campaign sidecar already exists",
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
    write_result(
        run / result_name,
        environment=environment,
        config=config,
        payload=payload,
    )
    append_manifest(run, run / "manifest.json")
    if failed is not None:
        raise DriverError(f"aborted run retained: {run}; {failed}") from failed
    check_run_complete(run)
    return run


def main(argv: list[str] | None = None) -> int:
    """Parse and execute one approved collection leg, propagating failures."""
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
    except (DriverError, OSError, ValueError, subprocess.SubprocessError) as exc:
        print(f"EXP-002 NOT COMPLETED: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
