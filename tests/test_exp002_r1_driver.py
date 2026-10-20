"""Regression tests for the EXP-002-r1 E1 collection driver.

Every collection fixture is synthetic: fake ``prin`` and ``_prin_core``
namespaces, fabricated historical JSON documents, controlled PDF/PNG byte
fixtures, mocked renderers and faked git/environment captures. No test
executes a real EXP-002-r1 leg or writes to the repository's real
``benchmarks/results/EXP-002-r1/`` or predecessor ``benchmarks/results/EXP-002/``
directories. Dedicated tests verify:
- namespace isolation (explicit rejection of predecessor ``EXP-002`` paths),
- ``allowed_output_roots`` admission of ``EXP-002-r1`` raw and output roots,
- ``_prin_core.pyd`` SHA-256 and byte-size enforcement (DV-047 guard),
- PRIN figure/table generator SHA-256 and origin enforcement, and
- per-run, per-root ``EXP-002-r1``, combined ``EXP-002`` + ``EXP-002-r1``, and
  64 MiB campaign storage caps.
"""

from __future__ import annotations

import hashlib
import importlib
import json
import re
import runpy
import shutil
import struct
import subprocess
import sys
import tempfile
import zlib
from pathlib import Path
from types import ModuleType
from typing import Any

import matplotlib
import pytest
from prin.reporting import _artifacts
from prin.reporting import figure_generation as prin_figure_generation
from prin.reporting import table_generation as prin_table_generation

import benchmarks._common.result as result_module
import tools.reproduce as reproduce
from benchmarks.campaign import exp002_r1_driver as driver
from tools.reproduce import ManifestRecord

SHA = "a" * 40
OTHER_SHA = "b" * 40
COMMIT = "c" * 40
SYNTHETIC_PYD_BYTES = b"synthetic-prin-core-pyd-binary"
SYNTHETIC_PYD_SHA256 = hashlib.sha256(SYNTHETIC_PYD_BYTES).hexdigest()
RESULT_NAMES = {
    mode: f"{mode}.json" if mode in {"api", "conclusions"} else "reproduction.json"
    for mode in driver.MODE_LABELS
}

PROTOCOL_APPROVED = (
    "# EXP-002-r1 pre-registration\n\n"
    "**Status:** APPROVED\n\n"
    "**Maintainer approval:** MichaelMaillet, 2026-10-20 UTC\n"
)
PROTOCOL_DRAFT = PROTOCOL_APPROVED.replace("APPROVED", "DRAFT")
PROTOCOL_APPROVED_SHA = hashlib.sha256(PROTOCOL_APPROVED.encode("utf-8")).hexdigest()


def _sha256(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def _probe_symlink_support() -> bool:
    """True iff this process can create symlinks (mirrors test_reproduce)."""
    try:
        with tempfile.TemporaryDirectory() as scratch:
            root = Path(scratch)
            target = root / "target"
            target.write_text("x", encoding="utf-8")
            link = root / "link"
            link.symlink_to(target)
            return link.exists()
    except OSError:
        return False


_needs_symlink_support = pytest.mark.skipif(
    not _probe_symlink_support(),
    reason="creating symlinks is not permitted in this environment",
)


def _pdf_assemble(objects: list[bytes], identifier: bytes) -> bytes:
    """Assemble the classic-xref container around ``objects``."""
    payload = bytearray(b"%PDF-1.4\n%\xff\xfe\n")
    offsets = []
    for number, value in enumerate(objects, 1):
        offsets.append(len(payload))
        payload += f"{number} 0 obj\n".encode() + value + b"\nendobj\n"
    xref = len(payload)
    payload += b"xref\n0 7\n0000000000 65535 f \n"
    for offset in offsets:
        payload += f"{offset:010d} 00000 n \n".encode()
    payload += (
        b"trailer\n<< /Size 7 /Root 1 0 R /Info 5 0 R /ID [<"
        + identifier
        + b"> <"
        + identifier
        + b">] >>\nstartxref\n"
        + str(xref).encode()
        + b"\n%%EOF\n"
    )
    return bytes(payload)


def _pdf_fixture(
    creator: bytes,
    producer: bytes,
    date: bytes,
    identifier: bytes,
    label: bytes = b"SCIENCE",
    title: bytes = b"unchanged",
) -> bytes:
    """Classic-xref PDF with a real page, stream, Info and font."""
    stream = (
        b"/Artifact <</Creator (SCIENTIFIC PROPERTY)>> BDC\n"
        b"BT /F1 8 Tf 2 2 Td (" + label + b") Tj ET\nEMC\n"
    )
    objects = [
        b"<< /Type /Catalog /Pages 2 0 R >>",
        b"<< /Type /Pages /Count 1 /Kids [3 0 R] >>",
        b"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 10 10] "
        b"/Contents 4 0 R /Resources << /Font << /F1 6 0 R >> >> >>",
        b"<< /Length "
        + str(len(stream)).encode()
        + b" >>\nstream\n"
        + stream
        + b"endstream",
        b"<< /Creator ("
        + creator
        + b") /Producer ("
        + producer
        + b") /CreationDate ("
        + date
        + b") /ModDate ("
        + date
        + b") /Title ("
        + title
        + b") >>",
        b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>",
    ]
    return _pdf_assemble(objects, identifier)


def _pdf_fixture_info_stream() -> bytes:
    """PDF whose referenced Info object carries a stream member."""
    stream = b"BT /F1 8 Tf 2 2 Td (SCIENCE) Tj ET\n"
    objects = [
        b"<< /Type /Catalog /Pages 2 0 R >>",
        b"<< /Type /Pages /Count 1 /Kids [3 0 R] >>",
        b"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 10 10] "
        b"/Contents 4 0 R /Resources << /Font << /F1 6 0 R >> >> >>",
        b"<< /Length "
        + str(len(stream)).encode()
        + b" >>\nstream\n"
        + stream
        + b"endstream",
        b"<< /Creator (ToolOne) /Producer (ToolTwo) /Title (unchanged) >>"
        b"\nstream\nx\nendstream",
        b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>",
    ]
    return _pdf_assemble(objects, b"11" * 16)


def _png_fixture(chunks: list[tuple[bytes, bytes]]) -> bytes:
    """CRC-correct PNG chunks around a real one-pixel RGB image."""
    payload = bytearray(b"\x89PNG\r\n\x1a\n")
    for kind, data in chunks:
        payload += (
            struct.pack(">I", len(data))
            + kind
            + data
            + struct.pack(">I", zlib.crc32(kind + data))
        )
    return bytes(payload)


IHDR = struct.pack(">IIBBBBB", 1, 1, 8, 2, 0, 0, 0)
IDAT_RED = zlib.compress(b"\x00\xff\x00\x00")
IDAT_BLUE = zlib.compress(b"\x00\x00\x00\xff")

PNG_A = _png_fixture(
    [
        (b"IHDR", IHDR),
        (b"tEXt", b"Software\x00first"),
        (b"IDAT", IDAT_RED),
        (b"IEND", b""),
    ]
)
PNG_B = _png_fixture(
    [
        (b"IHDR", IHDR),
        (b"tEXt", b"Software\x00a longer creator"),
        (b"IDAT", IDAT_RED),
        (b"IEND", b""),
    ]
)
PNG_C = _png_fixture([(b"IHDR", IHDR), (b"IDAT", IDAT_BLUE), (b"IEND", b"")])

PDF_A = _pdf_fixture(b"ToolOne", b"ToolTwo", b"D:20200101", b"11" * 16)
PDF_B = _pdf_fixture(
    b"A much longer Matplotlib creator",
    b"Longer producer metadata",
    b"D:20201011130000Z",
    b"22" * 16,
)
PDF_C = _pdf_fixture(
    b"ToolOne", b"ToolTwo", b"D:20200101", b"11" * 16, label=b"CHANGED"
)
PDF_TITLE = _pdf_fixture(
    b"ToolOne", b"ToolTwo", b"D:20200101", b"11" * 16, title=b"CHANGED"
)
PDF_ESCAPED = _pdf_fixture(b"Cr\\(x\\)eator", b"ToolTwo", b"D:20200101", b"11" * 16)
PDF_NO_INFO = PDF_A.replace(b" /Info 5 0 R", b"")
PDF_DUP_OFFSET = PDF_A.replace(
    re.findall(rb"\n([0-9]{10}) 00000 n ", PDF_A)[3],
    re.findall(rb"\n([0-9]{10}) 00000 n ", PDF_A)[2],
)
_PDF_N_ENTRY_LINES = re.findall(rb"[0-9]{10} 00000 n ", PDF_A)
PDF_DUP_ENTRY = PDF_A.replace(b"xref\n0 7\n", b"xref\n0 2\n").replace(
    _PDF_N_ENTRY_LINES[1], b"1 1\n" + _PDF_N_ENTRY_LINES[1]
)
PDF_NO_TRAILER = PDF_A.replace(
    b"trailer\n<< /Size 7 /Root 1 0 R /Info 5 0 R /ID [<"
    + b"11" * 16
    + b"> <"
    + b"11" * 16
    + b">] >>\n",
    b"",
)

TEX_A = b"% synthetic table a\n"

EXPECTED_FIGURE_STEMS = (
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
EXPECTED_TABLE_STEMS = (
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
EXPECTED_PUBLICATION_FILES = frozenset(
    [
        f"figures/{stem}.{fmt}"
        for stem in EXPECTED_FIGURE_STEMS
        for fmt in ("pdf", "png")
    ]
    + [f"tables/{stem}.tex" for stem in EXPECTED_TABLE_STEMS]
)


def _setup_synthetic_prin_core(
    root: Path, monkeypatch: pytest.MonkeyPatch
) -> tuple[Path, dict[str, str]]:
    """Create synthetic ``_prin_core.pyd`` and PRIN reporting modules under ``root``."""
    pyd_path = root / "python" / "prin" / "_prin_core.pyd"
    pyd_path.parent.mkdir(parents=True, exist_ok=True)
    pyd_path.write_bytes(SYNTHETIC_PYD_BYTES)
    fake_core = ModuleType("prin._prin_core")
    fake_core.__file__ = str(pyd_path)
    monkeypatch.setattr(driver, "_prin_core", fake_core)
    monkeypatch.setattr(driver, "PRIN_CORE_PYD", pyd_path)
    monkeypatch.setattr(driver, "PRIN_CORE_PYD_BYTES", len(SYNTHETIC_PYD_BYTES))
    monkeypatch.setattr(driver, "PRIN_CORE_PYD_SHA256", SYNTHETIC_PYD_SHA256)

    pins: dict[str, str] = {}
    for attr, kind in (
        ("prin_figure_generation", "figure"),
        ("prin_table_generation", "table"),
    ):
        rel = f"python/prin/reporting/{kind}_generation.py"
        path = root / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        body = f"# synthetic prin {kind} generator\n".encode()
        path.write_bytes(body)
        pins[rel] = _sha256(body)
        mod = ModuleType(f"prin.reporting.{kind}_generation")
        mod.__file__ = str(path)
        monkeypatch.setattr(driver, attr, mod)
    monkeypatch.setattr(driver, "PRIN_PINS", pins)
    return pyd_path, pins


@pytest.fixture
def workspace(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    """Redirect every driver root and shared write gate under ``tmp_path``."""
    root = tmp_path.resolve()
    monkeypatch.setattr(result_module, "_ALLOWED_ROOTS", (root,))
    monkeypatch.setattr(reproduce, "ALLOWED_MANIFEST_ROOTS", (root,))
    monkeypatch.setattr(driver, "ROOT", root)
    monkeypatch.setattr(driver, "REFERENCE", root / "reference")
    monkeypatch.setattr(
        driver, "RAW_ROOT", root / "benchmarks" / "results" / "EXP-002-r1"
    )
    monkeypatch.setattr(
        driver, "PREDECESSOR_RAW_ROOT", root / "benchmarks" / "results" / "EXP-002"
    )
    monkeypatch.setattr(
        driver,
        "OUTPUT_ROOT",
        root / "DOCS" / "test_and_benchmark_results" / "EXP-002-r1",
    )
    monkeypatch.setattr(
        driver,
        "PREDECESSOR_OUTPUT_ROOT",
        root / "DOCS" / "test_and_benchmark_results" / "EXP-002",
    )
    monkeypatch.setattr(
        driver,
        "PROTOCOL",
        root
        / "DOCS"
        / "experiments"
        / "EXP-002-r1-api-benchmark-result-and-reproduction-parity"
        / "preregistration.md",
    )
    monkeypatch.setattr(
        driver,
        "PREDECESSOR_RECORD_ROOT",
        root
        / "DOCS"
        / "experiments"
        / "EXP-002-api-benchmark-result-and-reproduction-parity",
    )
    monkeypatch.setattr(driver, "INPUT_MANIFEST", root / "manifest.json")
    monkeypatch.setattr(driver, "_git_bytes", _fake_git())
    _setup_synthetic_prin_core(root, monkeypatch)
    driver.RAW_ROOT.mkdir(parents=True)
    driver.PREDECESSOR_RAW_ROOT.mkdir(parents=True)
    driver.OUTPUT_ROOT.mkdir(parents=True)
    driver.PREDECESSOR_OUTPUT_ROOT.mkdir(parents=True)
    driver.PROTOCOL.parent.mkdir(parents=True)
    driver.PREDECESSOR_RECORD_ROOT.mkdir(parents=True)
    return root


def _run_name(mode: str, sha: str = SHA) -> str:
    return f"RUN-20261020T120000Z-{sha[:7]}-{driver.MODE_LABELS[mode]}"


def _fake_environment(sha: str = SHA) -> dict[str, Any]:
    return {
        "prin_version": "1.0.0rc1",
        "git_commit": sha,
        "rust_version": "rustc 1.98.1",
        "python_version": "3.14.0",
        "platform": "Windows-11",
        "processor": "Intel64",
        "logical_cpus": 8,
        "gpu": "none",
        "gpu_vram_mb": 0,
        "backend": "cpu",
        "dtype": "f64",
        "seed": 0,
    }


def _fake_identity(sha: str = SHA) -> dict[str, Any]:
    return {
        "source_sha": sha,
        "preregistration_sha256": PROTOCOL_APPROVED_SHA,
        "preregistration_commit": COMMIT,
        "input_manifest_sha256": driver.INPUT_MANIFEST_SHA,
        "input_record_count": 172,
        "approval_date_utc": "2026-10-20",
        "prin_core_pyd_sha256": driver.PRIN_CORE_PYD_SHA256,
        "prin_core_pyd_bytes": driver.PRIN_CORE_PYD_BYTES,
        "input_records": [],
    }


def _fake_observations(mode: str) -> dict[str, Any]:
    """Schema-valid synthetic observations for each registered mode."""
    if mode == "api":
        names = sorted(f"name_{index:03d}" for index in range(175))
        return {
            "expected_names": names,
            "legacy_names": names[:172],
            "observed_names": names,
            "frozen_missing": [],
            "frozen_extra": [],
            "rows": [
                {
                    "name": name,
                    "resolved": True,
                    "callable": True,
                    "defining_module": "prin",
                    "type": "function",
                    "error": None,
                    "legacy": True,
                    "ownership_present": True,
                }
                for name in names
            ],
            "unit": "api_symbol",
        }
    if mode == "conclusions":
        return {
            "cases": [
                {
                    "case_id": f"C00:{index}",
                    "family": "C00",
                    "input_file": "synthetic.json",
                    "left_path": "/value",
                    "right_path": None,
                    "left": 1.0,
                    "operator": ">",
                    "right": 0.5,
                    "operand_unit": "BC",
                    "expected": True,
                    "observed": True,
                }
                for index in range(62)
            ],
            "unit": "claim_comparator_record",
        }
    return {
        "implementation": "reference" if mode == "reference" else "prin",
        "renderer": {"matplotlib": "synthetic"},
        "expected_files": sorted(EXPECTED_PUBLICATION_FILES),
        "files": [
            {
                "path": "tables/tab_ablation.tex",
                "raw_bytes": 3,
                "raw_sha256": "0" * 64,
                "normalized_bytes": 3,
                "normalized_sha256": "0" * 64,
                "sensitivity_bytes": 3,
                "sensitivity_sha256": "0" * 64,
            }
        ],
        "unit": "generated_file",
    }


def _fake_config(run: Path) -> dict[str, Any]:
    return {
        "iterations": 10,
        "warmup": 0,
        "seed_counter": 0,
        "seed_key": 2,
        "out_dir": str(run),
        "measurement_kind": "deterministic_census",
        "replicates": 1,
    }


def _write_valid_run(
    mode: str = "api",
    sha: str = SHA,
    *,
    name: str | None = None,
    parent: Path | None = None,
) -> Path:
    """Create a closure-valid synthetic run directory."""
    base = parent if parent is not None else driver.RAW_ROOT
    run = base / (name or _run_name(mode, sha))
    run.mkdir(parents=True)
    result_name = RESULT_NAMES[mode]
    (run / "campaign-metadata.json").write_text(
        json.dumps(
            {
                "exp_id": "EXP-002-r1",
                "session": "EXP-002-r1-E3",
                "run_id": run.name,
                "operator": "devin",
                "mode": mode,
                "artefacts": {result_name: driver.MODE_TAGS[mode]},
            }
        ),
        encoding="utf-8",
    )
    (run / result_name).write_text(
        json.dumps(
            {
                "environment": _fake_environment(sha),
                "config": _fake_config(run),
                "identity": _fake_identity(sha),
                "status": "COMPLETED",
                "seed_used": False,
                "observations": _fake_observations(mode),
            }
        ),
        encoding="utf-8",
    )
    reproduce.append_manifest(run, run / "manifest.json")
    return run


def _remanifest(run: Path) -> None:
    (run / "manifest.json").unlink()
    reproduce.append_manifest(run, run / "manifest.json")


def _rewrite_json(run: Path, name: str, mutate: Any) -> None:
    path = run / name
    doc = json.loads(path.read_text(encoding="utf-8"))
    mutate(doc)
    path.write_text(json.dumps(doc), encoding="utf-8")
    _remanifest(run)


def _protocol_file(root: Path, text: str = PROTOCOL_APPROVED) -> Path:
    driver.PROTOCOL.write_bytes(text.encode("utf-8"))
    return driver.PROTOCOL


def _fake_git(
    sha: str = SHA,
    *,
    changed: str = "",
    untracked: str = "",
    shadowing: str = "",
    committed: bytes | None = None,
    commit: str = COMMIT,
    merge_base: str | None = None,
) -> Any:
    """Fake ``_git_bytes``: raw stdout bytes, as the real helper returns."""

    def fake(*args: str) -> bytes:
        if args == ("rev-parse", "HEAD"):
            return sha.encode()
        if args[0] == "diff":
            return changed.encode()
        if args[0] == "ls-files":
            glob = any(arg.startswith(":(glob)") for arg in args)
            return (shadowing if glob else untracked).encode()
        if args[0] == "show":
            if committed is not None:
                return committed
            if driver.PROTOCOL.exists():
                return driver.PROTOCOL.read_bytes()
            return PROTOCOL_APPROVED.encode("utf-8")
        if args[0] == "log":
            return commit.encode()
        if args[0] == "merge-base":
            return (merge_base if merge_base is not None else commit).encode()
        raise AssertionError(f"unexpected git invocation: {args}")

    return fake


@pytest.fixture
def admitted(workspace: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    """Fully fake admission: APPROVED protocol, clean git, matching env."""
    _protocol_file(workspace)
    monkeypatch.setattr(driver, "_git_bytes", _fake_git())
    monkeypatch.setattr(
        driver, "capture_environment", lambda **kwargs: _fake_environment()
    )
    return workspace


class TestNamespaceIsolationAndRealPins:
    """Step 1 & Step 3 governance checks: isolated roots and DV-047 pin."""

    def test_real_driver_constants_bind_isolated_r1_roots(self) -> None:
        repo_root = Path(driver.__file__).resolve().parents[2]
        assert driver.EXP_ID == "EXP-002-r1"
        assert driver.SESSION_ID == "EXP-002-r1-E3"
        assert driver.RAW_ROOT == repo_root / "benchmarks/results/EXP-002-r1"
        assert (
            driver.OUTPUT_ROOT
            == repo_root / "DOCS/test_and_benchmark_results/EXP-002-r1"
        )
        assert driver.PREDECESSOR_RAW_ROOT == repo_root / "benchmarks/results/EXP-002"
        assert (
            driver.PREDECESSOR_OUTPUT_ROOT
            == repo_root / "DOCS/test_and_benchmark_results/EXP-002"
        )
        assert driver.RAW_ROOT != driver.PREDECESSOR_RAW_ROOT
        assert driver.OUTPUT_ROOT != driver.PREDECESSOR_OUTPUT_ROOT
        assert all(label.startswith("r1-") for label in driver.MODE_LABELS.values())

    def test_allowed_output_roots_admits_exp002_r1_roots(self) -> None:
        """Confirm ``allowed_output_roots`` and ``_dirs`` admit ``EXP-002-r1``."""
        repo_root = Path(driver.__file__).resolve().parents[2]
        raw_r1 = (repo_root / "benchmarks/results/EXP-002-r1").resolve()
        out_r1 = (repo_root / "DOCS/test_and_benchmark_results/EXP-002-r1").resolve()
        fig_roots = _artifacts.allowed_output_roots(
            prin_figure_generation.ALLOWED_OUTPUT_ROOTS
        )
        tab_roots = _artifacts.allowed_output_roots(
            prin_table_generation.ALLOWED_OUTPUT_ROOTS
        )
        for candidate in (raw_r1, out_r1, out_r1 / "RUN-x" / "publication" / "figures"):
            assert any(
                candidate == root or root in candidate.parents for root in fig_roots
            )
            assert any(
                candidate == root or root in candidate.parents for root in tab_roots
            )
        _, resolved_fig = prin_figure_generation._dirs(
            None, out_r1 / "RUN-x" / "publication" / "figures"
        )
        _, resolved_tab = prin_table_generation._dirs(
            None, out_r1 / "RUN-x" / "publication" / "tables"
        )
        assert resolved_fig == out_r1 / "RUN-x" / "publication" / "figures"
        assert resolved_tab == out_r1 / "RUN-x" / "publication" / "tables"

    def test_real_prin_core_pyd_and_generator_pins_match_repository(self) -> None:
        """Verify live DV-047 ``_prin_core.pyd`` and generator pins."""
        ext = driver._verify_prin_core_extension()
        assert ext["prin_core_pyd_sha256"] == driver.PRIN_CORE_PYD_SHA256
        assert ext["prin_core_pyd_bytes"] == driver.PRIN_CORE_PYD_BYTES
        driver._verify_prin_generators()

    def test_predecessor_paths_rejected_across_entry_points(
        self, admitted: Path
    ) -> None:
        pred_run = (
            driver.PREDECESSOR_RAW_ROOT / f"RUN-20261020T120000Z-{SHA[:7]}-r1-api-cpu"
        )
        with pytest.raises(driver.DriverError, match="predecessor EXP-002"):
            driver._reserve("api", pred_run, SHA)
        with pytest.raises(driver.DriverError, match="predecessor EXP-002"):
            driver.run_registered("api", pred_run, "devin", SHA)
        with pytest.raises(driver.DriverError, match="predecessor EXP-002"):
            driver.check_run_complete(pred_run)
        with pytest.raises(driver.DriverError, match="predecessor EXP-002"):
            driver._snapshot(driver.PREDECESSOR_OUTPUT_ROOT / "inputs")
        with pytest.raises(driver.DriverError, match="predecessor EXP-002"):
            driver.collect_reproduction(
                "prin",
                driver.OUTPUT_ROOT / "snap",
                driver.PREDECESSOR_OUTPUT_ROOT / "pub",
            )
        with pytest.raises(driver.DriverError, match="predecessor EXP-002"):
            driver.collect_reproduction(
                "prin",
                driver.PREDECESSOR_OUTPUT_ROOT / "snap",
                driver.OUTPUT_ROOT / "pub",
            )
        with pytest.raises(driver.DriverError, match="predecessor EXP-002"):
            driver._reject_predecessor_path(
                driver.PREDECESSOR_RECORD_ROOT / "preregistration.md", "protocol"
            )

    def test_prin_core_extension_mismatch_rejected(
        self, workspace: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.setattr(driver, "PRIN_CORE_PYD_SHA256", "0" * 64)
        with pytest.raises(driver.DriverError, match=r"_prin_core\.pyd"):
            driver._verify_prin_core_extension()
        monkeypatch.setattr(driver, "PRIN_CORE_PYD_SHA256", SYNTHETIC_PYD_SHA256)
        monkeypatch.setattr(driver, "PRIN_CORE_PYD_BYTES", 999999)
        with pytest.raises(driver.DriverError, match=r"_prin_core\.pyd"):
            driver._verify_prin_core_extension()

    def test_prin_generator_digest_mismatch_rejected(
        self, workspace: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        bad_pins = dict(driver.PRIN_PINS)
        bad_pins["python/prin/reporting/figure_generation.py"] = "0" * 64
        monkeypatch.setattr(driver, "PRIN_PINS", bad_pins)
        with pytest.raises(
            driver.DriverError, match="PRIN publication generator digest"
        ):
            driver._verify_prin_generators()


class TestHelpers:
    def test_git_reports_version(self) -> None:
        assert driver._git("--version").startswith("git version")

    def test_git_missing_executable(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setattr(shutil, "which", lambda name: None)
        with pytest.raises(driver.DriverError, match="git is unavailable"):
            driver._git("--version")

    def test_mapping_rejects_non_object(self) -> None:
        with pytest.raises(driver.DriverError, match="expected a JSON object"):
            driver._mapping([1, 2], "ctx")
        with pytest.raises(driver.DriverError, match="expected a JSON object"):
            driver._mapping({1: "x"}, "ctx")

    def test_list_rejects_non_array(self) -> None:
        with pytest.raises(driver.DriverError, match="expected an array"):
            driver._list({"a": 1}, "ctx")

    @pytest.mark.parametrize(
        "value",
        [True, "1.0", float("nan"), float("inf"), -float("inf")],
    )
    def test_number_rejects_non_finite_and_bool(self, value: object) -> None:
        with pytest.raises(driver.DriverError):
            driver._number(value, "ctx")

    def test_number_accepts_finite(self) -> None:
        assert driver._number(3, "ctx") == 3.0

    def test_render_environment_reports_versions(self) -> None:
        environment = driver._render_environment()
        for key in (
            "matplotlib",
            "numpy",
            "pillow",
            "freetype",
            "backend",
            "font_sha256",
        ):
            assert key in environment


class _CallableSentinel:
    def __init__(self) -> None:
        self.calls = 0

    def __call__(self) -> None:
        self.calls += 1


@pytest.fixture
def api_env(workspace: Path, monkeypatch: pytest.MonkeyPatch) -> ModuleType:
    """A fake ``prin`` module, reference ``__all__`` pin, guide and baseline."""
    legacy = ["legacy_alpha", "legacy_beta"] + [
        f"legacy_{index:03d}" for index in range(170)
    ]
    reference_init = workspace / "reference" / "src" / "prinet" / "__init__.py"
    reference_init.parent.mkdir(parents=True)
    payload = ("__all__ = " + repr(legacy) + "\n").encode()
    reference_init.write_bytes(payload)
    pins = dict(driver.REFERENCE_PINS)
    pins["src/prinet/__init__.py"] = _sha256(payload)
    monkeypatch.setattr(driver, "REFERENCE_PINS", pins)

    prin_init = workspace / "python" / "prin" / "__init__.py"
    prin_init.parent.mkdir(parents=True, exist_ok=True)
    prin_init.write_bytes(b'"""fake prin module"""\n')
    fake_mod = ModuleType("prin")
    fake: Any = fake_mod
    fake.__file__ = str(prin_init)
    fake.__all__ = ["legacy_alpha", "legacy_alpha", "unexpected_extra"]
    fake.legacy_alpha = lambda: "value"
    fake.legacy_beta = _CallableSentinel()
    fake.legacy_000 = None
    fake.legacy_001 = object()
    fake.__version__ = "1.0.0rc1"
    fake.core_version = lambda: "1.0.0rc1"
    fake.BackendUnavailableError = type("BackendUnavailableError", (Exception,), {})
    monkeypatch.setattr(driver, "prin", fake_mod)
    monkeypatch.setattr(
        driver,
        "verify_api_surface",
        lambda observed: ({"frozen_missing_x"}, {"frozen_extra_y"}),
    )

    guide_dir = workspace / "DOCS" / "sphinx"
    guide_dir.mkdir(parents=True)
    (guide_dir / "migration_guide.rst").write_text(
        "intro\n.. wp036-consolidated-table-begin\n"
        '   "legacy_alpha", "prin.alpha",\n'
        ".. wp036-consolidated-table-end\n",
        encoding="utf-8",
    )
    baseline_dir = workspace / "DOCS" / "baselines"
    baseline_dir.mkdir(parents=True)
    (baseline_dir / "wp001_api_traceability.md").write_text(
        "| prinet | legacy_alpha | a |\n| prinet | legacy_beta | b |\n",
        encoding="utf-8",
    )
    return fake_mod


class TestCollectApi:
    def test_expected_observed_and_rows(self, api_env: ModuleType) -> None:
        result = driver.collect_api()
        expected = sorted(set(driver._legacy_names()) | driver.PRIN_ADDITIONS)
        assert len(expected) == 175
        assert result["expected_names"] == expected
        assert len(result["legacy_names"]) == 172
        assert result["observed_names"] == [
            "legacy_alpha",
            "legacy_alpha",
            "unexpected_extra",
        ]
        assert result["frozen_missing"] == ["frozen_missing_x"]
        assert result["frozen_extra"] == ["frozen_extra_y"]
        assert result["unit"] == "api_symbol"
        rows = {row["name"]: row for row in result["rows"]}
        assert len(rows) == 175
        assert rows["legacy_alpha"]["resolved"] is True
        assert rows["legacy_alpha"]["callable"] is True
        sentinel = api_env.legacy_beta
        assert isinstance(sentinel, _CallableSentinel)
        assert sentinel.calls == 0
        assert rows["legacy_000"]["resolved"] is False
        assert rows["legacy_000"]["callable"] is False
        assert rows["legacy_000"]["error"] is None
        assert rows["legacy_001"]["resolved"] is False
        missing = rows["legacy_002"]
        assert missing["resolved"] is False
        assert isinstance(missing["error"], str)
        assert missing["error"]
        assert rows["__version__"]["resolved"] is True
        assert rows["__version__"]["callable"] is False
        assert rows["legacy_alpha"]["ownership_present"] is True
        assert rows["legacy_beta"]["ownership_present"] is False
        assert rows["__version__"]["legacy"] is False
        assert rows["legacy_alpha"]["legacy"] is True

    def test_wrong_module_origin_rejected(
        self, api_env: ModuleType, tmp_path: Path
    ) -> None:
        api_env.__file__ = str(tmp_path / "elsewhere" / "prin" / "__init__.py")
        with pytest.raises(driver.DriverError, match="governed source"):
            driver.collect_api()

    def test_missing_guide_aborts(self, api_env: ModuleType) -> None:
        (driver.ROOT / "DOCS" / "sphinx" / "migration_guide.rst").unlink()
        with pytest.raises((driver.DriverError, OSError)):
            driver.collect_api()

    def test_missing_consolidated_table_marks_no_ownership(
        self, api_env: ModuleType
    ) -> None:
        guide = driver.ROOT / "DOCS" / "sphinx" / "migration_guide.rst"
        guide.write_text("no consolidated table markers\n", encoding="utf-8")
        rows = {row["name"]: row for row in driver.collect_api()["rows"]}
        assert rows["legacy_alpha"]["ownership_present"] is False


class TestLegacyNames:
    @pytest.fixture
    def pinned_source(self, workspace: Path, monkeypatch: pytest.MonkeyPatch) -> Any:
        source = workspace / "reference" / "src" / "prinet" / "__init__.py"
        source.parent.mkdir(parents=True)

        def pin(body: str) -> None:
            payload = body.encode()
            source.write_bytes(payload)
            pins = dict(driver.REFERENCE_PINS)
            pins["src/prinet/__init__.py"] = _sha256(payload)
            monkeypatch.setattr(driver, "REFERENCE_PINS", pins)

        return pin

    def test_frozen_list_returned(self, pinned_source: Any) -> None:
        names = [f"n{index:03d}" for index in range(172)]
        pinned_source("__all__ = " + repr(names))
        assert driver._legacy_names() == names

    def test_wrong_digest_rejected(
        self, pinned_source: Any, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        names = [f"n{index:03d}" for index in range(172)]
        pinned_source("__all__ = " + repr(names))
        pins = dict(driver.REFERENCE_PINS)
        pins["src/prinet/__init__.py"] = "0" * 64
        monkeypatch.setattr(driver, "REFERENCE_PINS", pins)
        with pytest.raises(driver.DriverError, match="digest changed"):
            driver._legacy_names()

    def test_literal_missing_rejected(self, pinned_source: Any) -> None:
        pinned_source("NAMES = []\n__all__ += NAMES\n")
        with pytest.raises(driver.DriverError, match="literal __all__ missing"):
            driver._legacy_names()

    def test_non_literal_rejected(self, pinned_source: Any) -> None:
        pinned_source("NAMES = []\n__all__ = list(NAMES)\n")
        with pytest.raises((driver.DriverError, ValueError)):
            driver._legacy_names()

    def test_non_list_literal_rejected(self, pinned_source: Any) -> None:
        pinned_source('__all__ = "abc"\n')
        with pytest.raises(driver.DriverError, match="frozen 172-name list"):
            driver._legacy_names()

    def test_duplicate_names_rejected(self, pinned_source: Any) -> None:
        names = [f"n{index:03d}" for index in range(171)] + ["n000"]
        pinned_source("__all__ = " + repr(names))
        with pytest.raises(driver.DriverError, match="frozen 172-name list"):
            driver._legacy_names()

    @pytest.mark.parametrize("count", [171, 173])
    def test_wrong_cardinality_rejected(self, pinned_source: Any, count: int) -> None:
        names = [f"n{index:03d}" for index in range(count)]
        pinned_source("__all__ = " + repr(names))
        with pytest.raises(driver.DriverError, match="frozen 172-name list"):
            driver._legacy_names()


def _conclusion_docs() -> dict[str, dict[str, Any]]:
    """Synthetic five-file historical input satisfying the registered schema."""
    files = driver.CONCLUSION_FILES
    return {
        files[0]: {
            "bimodality_coefficient": {
                "raw_values": [0.6, 0.5, 0.9, 0.4, 0.7],
                "n_sequences": 5,
            }
        },
        files[1]: {
            "grid": [
                {
                    "K": float(index),
                    "alpha": index / 10.0,
                    "bc_mean": 0.6 if index % 2 else 0.5,
                    "chimera_detected": bool(index % 2),
                }
                for index in range(42)
            ]
        },
        files[2]: {
            "sweep": [
                {"n_oscillators": n, "bc_stats": {"mean": 0.7}}
                for n in (128, 256, 512, 1024)
            ]
        },
        files[3]: {
            "topologies": {
                "ring": {"bc_mean": 0.9, "bc_ci": {"ci_width": 0.3}},
                "2community": {"bc_mean": 0.7, "bc_ci": {"ci_width": 0.2}},
                "4community": {"bc_mean": 0.6, "bc_ci": {"ci_width": 0.1}},
            }
        },
        files[4]: {
            "zones": {
                "csr_cpu": {
                    "device": "cpu",
                    "regime": "csr",
                    "zone_width": 0.9,
                    "K_c": 0.5,
                },
                "full_cpu": {
                    "device": "cpu",
                    "regime": "full",
                    "zone_width": 0.8,
                    "K_c": 0.1,
                },
                "mean_field_cpu": {
                    "device": "cpu",
                    "regime": "mean_field",
                    "zone_width": 0.7,
                    "K_c": 0.2,
                },
                "sparse_knn_cpu": {
                    "device": "cpu",
                    "regime": "sparse_knn",
                    "zone_width": 0.6,
                    "K_c": 0.3,
                },
                "csr_cuda": {
                    "device": "cuda",
                    "regime": "csr",
                    "zone_width": 0.0,
                    "K_c": 9.9,
                },
                "full_cuda": {
                    "device": "cuda",
                    "regime": "full",
                    "zone_width": 0.0,
                    "K_c": 9.9,
                },
            }
        },
    }


class TestCollectConclusions:
    def test_exactly_62_labelled_cases(self) -> None:
        result = driver.collect_conclusions(_conclusion_docs())
        cases = result["cases"]
        assert result["unit"] == "claim_comparator_record"
        assert len(cases) == 62
        assert len({case["case_id"] for case in cases}) == 62
        families: dict[str, int] = {}
        for case in cases:
            families[case["family"]] = families.get(case["family"], 0) + 1
        assert families == {"C01": 5, "C02": 42, "C03": 4, "C04": 5, "C05": 6}
        allowed_keys = {
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
            "K",
            "alpha_radians",
        }
        for case in cases:
            assert set(case) <= allowed_keys
            assert "verdict" not in case
        first = cases[0]
        assert first["left_path"] == "/bimodality_coefficient/raw_values/0"
        assert first["operator"] == ">"
        assert first["right"] == 0.555
        assert first["right_path"] is None
        assert first["operand_unit"] == "BC"
        c04 = [case for case in cases if case["family"] == "C04"]
        assert {case["right_path"] for case in c04} == {
            "/topologies/2community/bc_mean",
            "/topologies/4community/bc_mean",
            "/topologies/2community/bc_ci/ci_width",
            "/topologies/4community/bc_ci/ci_width",
        }
        c05 = [case for case in cases if case["family"] == "C05"]
        assert all(case["operand_unit"] == "stored_coupling_K" for case in c05)
        assert {case["operator"] for case in c05} == {">", "<"}
        assert all(case["observed"] is True for case in c05)
        c02 = [case for case in cases if case["family"] == "C02"]
        assert all("K" in case and "alpha_radians" in case for case in c02)
        false_rows = [case for case in c02 if case["expected"] is False]
        assert len(false_rows) == 21
        assert all(case["observed"] is False for case in false_rows)
        assert all(case["observed"] for case in c02 if case["expected"])

    def test_strict_boundary_at_point_555(self) -> None:
        docs = _conclusion_docs()
        docs[driver.CONCLUSION_FILES[0]]["bimodality_coefficient"]["raw_values"] = [
            0.555
        ] * 5
        result = driver.collect_conclusions(docs)
        c01 = [case for case in result["cases"] if case["family"] == "C01"]
        assert all(case["observed"] is False for case in c01)

    def test_strict_boundary_at_point_5(self) -> None:
        docs = _conclusion_docs()
        docs[driver.CONCLUSION_FILES[2]]["sweep"][0]["bc_stats"]["mean"] = 0.5
        result = driver.collect_conclusions(docs)
        c03 = [case for case in result["cases"] if case["family"] == "C03"]
        assert c03[0]["observed"] is False

    def test_inverted_c04_widths_stay_observed_false(self) -> None:
        docs = _conclusion_docs()
        docs[driver.CONCLUSION_FILES[3]]["topologies"]["ring"]["bc_ci"]["ci_width"] = (
            0.05
        )
        result = driver.collect_conclusions(docs)
        widths = [
            case
            for case in result["cases"]
            if case["family"] == "C04" and "width-ring" in case["case_id"]
        ]
        assert all(case["observed"] is False for case in widths)

    def test_c05_onset_tie_stays_observed_false(self) -> None:
        docs = _conclusion_docs()
        zones = docs[driver.CONCLUSION_FILES[4]]["zones"]
        zones["csr_cpu"]["K_c"] = zones["full_cpu"]["K_c"]
        result = driver.collect_conclusions(docs)
        tie = [
            case for case in result["cases"] if case["case_id"] == "C05:onset-full-csr"
        ]
        assert tie[0]["observed"] is False

    def test_opposite_c02_historical_boolean_retained(self) -> None:
        docs = _conclusion_docs()
        docs[driver.CONCLUSION_FILES[1]]["grid"][0]["chimera_detected"] = True
        result = driver.collect_conclusions(docs)
        row = next(case for case in result["cases"] if case["case_id"] == "C02:0")
        assert row["expected"] is True
        assert row["observed"] is False


def _conclusion_mutations() -> list[tuple[str, Any, type[Exception]]]:
    files = driver.CONCLUSION_FILES

    def missing_file(docs: dict[str, Any]) -> None:
        del docs[files[0]]

    def non_mapping_doc(docs: dict[str, Any]) -> None:
        docs[files[0]] = []

    def short_raw(docs: dict[str, Any]) -> None:
        docs[files[0]]["bimodality_coefficient"]["raw_values"] = [0.6] * 4

    def wrong_nseq(docs: dict[str, Any]) -> None:
        docs[files[0]]["bimodality_coefficient"]["n_sequences"] = 4

    def raw_not_array(docs: dict[str, Any]) -> None:
        docs[files[0]]["bimodality_coefficient"]["raw_values"] = {}

    def short_grid(docs: dict[str, Any]) -> None:
        docs[files[1]]["grid"] = docs[files[1]]["grid"][:41]

    def duplicate_grid(docs: dict[str, Any]) -> None:
        docs[files[1]]["grid"][1]["K"] = docs[files[1]]["grid"][0]["K"]
        docs[files[1]]["grid"][1]["alpha"] = docs[files[1]]["grid"][0]["alpha"]

    def non_bool_flag(docs: dict[str, Any]) -> None:
        docs[files[1]]["grid"][0]["chimera_detected"] = 1

    def grid_row_non_mapping(docs: dict[str, Any]) -> None:
        docs[files[1]]["grid"][0] = 5

    def duplicate_n(docs: dict[str, Any]) -> None:
        docs[files[2]]["sweep"][1]["n_oscillators"] = 128

    def wrong_n(docs: dict[str, Any]) -> None:
        docs[files[2]]["sweep"][1]["n_oscillators"] = 2048

    def bool_n(docs: dict[str, Any]) -> None:
        docs[files[2]]["sweep"][1]["n_oscillators"] = True

    def extra_sweep(docs: dict[str, Any]) -> None:
        docs[files[2]]["sweep"].append(
            {"n_oscillators": 2048, "bc_stats": {"mean": 0.9}}
        )

    def bad_topology(docs: dict[str, Any]) -> None:
        del docs[files[3]]["topologies"]["4community"]

    def wrong_device(docs: dict[str, Any]) -> None:
        docs[files[4]]["zones"]["csr_cpu"]["device"] = "cuda"

    def wrong_regime(docs: dict[str, Any]) -> None:
        docs[files[4]]["zones"]["csr_cpu"]["regime"] = "full"

    def nan_operand(docs: dict[str, Any]) -> None:
        docs[files[0]]["bimodality_coefficient"]["raw_values"][0] = float("nan")

    def inf_operand(docs: dict[str, Any]) -> None:
        docs[files[4]]["zones"]["csr_cpu"]["zone_width"] = float("inf")

    def bool_operand(docs: dict[str, Any]) -> None:
        docs[files[0]]["bimodality_coefficient"]["raw_values"][0] = True

    def missing_zone(docs: dict[str, Any]) -> None:
        del docs[files[4]]["zones"]["csr_cpu"]

    def missing_mean(docs: dict[str, Any]) -> None:
        del docs[files[2]]["sweep"][0]["bc_stats"]["mean"]

    def missing_ci(docs: dict[str, Any]) -> None:
        del docs[files[3]]["topologies"]["ring"]["bc_ci"]

    return [
        ("missing-file", missing_file, driver.DriverError),
        ("non-mapping-doc", non_mapping_doc, driver.DriverError),
        ("short-raw", short_raw, driver.DriverError),
        ("wrong-nseq", wrong_nseq, driver.DriverError),
        ("raw-not-array", raw_not_array, driver.DriverError),
        ("short-grid", short_grid, driver.DriverError),
        ("duplicate-grid", duplicate_grid, driver.DriverError),
        ("non-bool-flag", non_bool_flag, driver.DriverError),
        ("grid-row-non-mapping", grid_row_non_mapping, driver.DriverError),
        ("duplicate-n", duplicate_n, driver.DriverError),
        ("wrong-n", wrong_n, driver.DriverError),
        ("bool-n", bool_n, driver.DriverError),
        ("extra-sweep", extra_sweep, driver.DriverError),
        ("bad-topology", bad_topology, driver.DriverError),
        ("wrong-device", wrong_device, driver.DriverError),
        ("wrong-regime", wrong_regime, driver.DriverError),
        ("nan-operand", nan_operand, driver.DriverError),
        ("inf-operand", inf_operand, driver.DriverError),
        ("bool-operand", bool_operand, driver.DriverError),
        ("missing-zone", missing_zone, driver.DriverError),
        ("missing-mean", missing_mean, driver.DriverError),
        ("missing-ci", missing_ci, driver.DriverError),
    ]


_CONCLUSION_MUTATIONS = _conclusion_mutations()


class TestConclusionValidation:
    @pytest.mark.parametrize(
        "mutate,expected",
        [(mutate, expected) for _, mutate, expected in _CONCLUSION_MUTATIONS],
        ids=[label for label, _, _ in _CONCLUSION_MUTATIONS],
    )
    def test_invalid_input_fails_closed(
        self, mutate: Any, expected: type[Exception]
    ) -> None:
        docs = _conclusion_docs()
        mutate(docs)
        with pytest.raises(expected):
            driver.collect_conclusions(docs)


class TestNormalizedBytes:
    def test_tex_crlf_canonicalizes_to_lf(self) -> None:
        assert driver.normalized_bytes(TEX_A, ".tex") == TEX_A
        assert driver.normalized_bytes(TEX_A.replace(b"\n", b"\r\n"), ".tex") == TEX_A

    @pytest.mark.parametrize(
        "variant",
        [
            TEX_A.replace(b"\n", b"\r"),
            TEX_A.replace(b"\n", b" \n"),
            TEX_A.replace(b"table a", b"table b"),
            TEX_A + b"\n",
        ],
        ids=["lone-cr", "trailing-space", "content", "extra-line"],
    )
    def test_tex_other_bytes_stay_significant(self, variant: bytes) -> None:
        assert driver.normalized_bytes(variant, ".tex") != (
            driver.normalized_bytes(TEX_A, ".tex")
        )

    def test_pdf_metadata_only_difference_normalizes_equal(self) -> None:
        assert PDF_A != PDF_B
        assert driver.normalized_bytes(PDF_A, ".pdf") == (
            driver.normalized_bytes(PDF_B, ".pdf")
        )
        normalized = driver.normalized_bytes(PDF_A, ".pdf")
        assert normalized != PDF_A
        assert b"D:20200101" not in normalized
        assert b"ToolOne" not in normalized

    def test_pdf_content_difference_stays_significant(self) -> None:
        assert driver.normalized_bytes(PDF_A, ".pdf") != (
            driver.normalized_bytes(PDF_C, ".pdf")
        )

    def test_pdf_unregistered_info_field_stays_significant(self) -> None:
        assert driver.normalized_bytes(PDF_A, ".pdf") != (
            driver.normalized_bytes(PDF_TITLE, ".pdf")
        )

    def test_pdf_creator_inside_content_stream_retained(self) -> None:
        normalized = driver.normalized_bytes(PDF_A, ".pdf")
        assert b"/Creator (SCIENTIFIC PROPERTY)" in normalized

    def test_pdf_escaped_info_parentheses_normalize(self) -> None:
        assert driver.normalized_bytes(PDF_A, ".pdf") == (
            driver.normalized_bytes(PDF_ESCAPED, ".pdf")
        )

    def test_pdf_without_info_is_valid_and_not_blind_masked(self) -> None:
        normalized = driver.normalized_bytes(PDF_NO_INFO, ".pdf")
        assert b"ToolOne" in normalized

    @pytest.mark.parametrize(
        "payload",
        [
            b"not-pdf",
            b"%PDF-1.4\njunk",
            PDF_A.replace(b"%%EOF", b"BROKEN"),
            re.sub(rb"(?m)^startxref\n[0-9]+", b"startxref\n1", PDF_A),
            re.sub(rb"(?m)^startxref\n[0-9]+", b"startxref\n999999", PDF_A),
            PDF_A.replace(b"0000000000 65535 f", b"invalid-xref-entry"),
            PDF_A.replace(b"/Root 1 0 R", b"/Root 99 0 R"),
            PDF_A.replace(b"/Info 5 0 R", b"/Info 99 0 R"),
            PDF_DUP_ENTRY,
            PDF_DUP_OFFSET,
            PDF_A.replace(b"2 0 obj", b"9 0 obj"),
            PDF_A.replace(b"endobj", b"endobX", 1),
            PDF_A.replace(b"xref\n0 7\n", b"xref\n0 99\n"),
            PDF_A.replace(b"xref\n0 7\n", b"xref\n0 2\n"),
            PDF_NO_TRAILER,
            PDF_A.replace(b"trailer\n<<", b"trailer\n>>"),
            _pdf_fixture_info_stream(),
            PDF_A.replace(b"/Size 7 ", b""),
            PDF_A.replace(b"/Root 1 0 R ", b""),
        ],
        ids=[
            "bad-magic",
            "bare-header-junk",
            "missing-eof",
            "invalid-startxref-pointer",
            "startxref-out-of-bounds",
            "invalid-xref-entry",
            "missing-root-ref",
            "missing-info-ref",
            "duplicate-xref-entry",
            "duplicate-xref-offset",
            "mismatched-object-header",
            "missing-endobj",
            "truncated-xref-subsection",
            "unexpected-line-after-subsection",
            "xref-without-trailer",
            "trailer-not-a-dictionary",
            "info-object-with-stream",
            "trailer-without-size",
            "trailer-without-root",
        ],
    )
    def test_malformed_pdf_rejected(self, payload: bytes) -> None:
        with pytest.raises(driver.DriverError, match="malformed PDF"):
            driver.normalized_bytes(payload, ".pdf")

    def test_png_ancillary_difference_normalizes_equal(self) -> None:
        assert driver.normalized_bytes(PNG_A, ".png") == (
            driver.normalized_bytes(PNG_B, ".png")
        )

    def test_png_image_data_difference_stays_significant(self) -> None:
        assert driver.normalized_bytes(PNG_A, ".png") != (
            driver.normalized_bytes(PNG_C, ".png")
        )

    @pytest.mark.parametrize("suffix", [".csv", ".svg", ".jpg", ""])
    def test_unsupported_suffix_rejected(self, suffix: str) -> None:
        with pytest.raises(driver.DriverError, match="unregistered"):
            driver.normalized_bytes(b"payload", suffix)

    @pytest.mark.parametrize(
        "payload",
        [
            b"not-a-png",
            b"\x89PNG\r\n\x1a\n",
            b"\x89PNG\r\n\x1a\n" + b"\x00" * 5,
            PNG_A[:-12] + b"\x00\x00\x10\x00" + PNG_A[-8:],
            _png_fixture([(b"IDAT", IDAT_RED), (b"IEND", b"")]),
            _png_fixture([(b"IHDR", IHDR), (b"IEND", b"")]),
            _png_fixture([(b"IHDR", IHDR), (b"IDAT", IDAT_RED)]),
            _png_fixture([(b"IHDR", b""), (b"IDAT", IDAT_RED), (b"IEND", b"")]),
            _png_fixture(
                [
                    (b"IHDR", struct.pack(">IIBBBBB", 0, 1, 8, 2, 0, 0, 0)),
                    (b"IDAT", IDAT_RED),
                    (b"IEND", b""),
                ]
            ),
            PNG_A[:-1] + bytes([PNG_A[-1] ^ 1]),
            _png_fixture([(b"IHDR", IHDR), (b"IDAT", b"not-zlib"), (b"IEND", b"")]),
            PNG_A + b"garbage",
            PNG_A[:-12],
            _png_fixture(
                [
                    (b"IHDR", IHDR),
                    (b"IHDR", IHDR),
                    (b"IDAT", IDAT_RED),
                    (b"IEND", b""),
                ]
            ),
            _png_fixture(
                [
                    (b"IHDR", IHDR),
                    (b"IDAT", IDAT_RED),
                    (b"IEND", b""),
                    (b"IEND", b""),
                ]
            ),
            _png_fixture(
                [
                    (b"IHDR", IHDR),
                    (b"IDAT", IDAT_RED[:2]),
                    (b"tEXt", b"key\x00value"),
                    (b"IDAT", IDAT_RED[2:]),
                    (b"IEND", b""),
                ]
            ),
            _png_fixture(
                [
                    (b"IHDR", IHDR),
                    (b"JUNK", b"x"),
                    (b"IDAT", IDAT_RED),
                    (b"IEND", b""),
                ]
            ),
        ],
        ids=[
            "bad-magic",
            "signature-only",
            "partial-chunk-header",
            "declared-length-overrun",
            "missing-ihdr",
            "missing-idat",
            "missing-iend",
            "empty-ihdr",
            "zero-width-ihdr",
            "bad-crc",
            "correct-crc-invalid-zlib",
            "trailing-bytes",
            "truncated-iend",
            "duplicate-ihdr",
            "duplicate-iend",
            "noncontiguous-idat",
            "unknown-critical-chunk",
        ],
    )
    def test_malformed_png_rejected(self, payload: bytes) -> None:
        with pytest.raises(driver.DriverError, match="malformed PNG"):
            driver.normalized_bytes(payload, ".png")


class TestPublicationInventory:
    def test_registered_stems_and_file_set(self) -> None:
        assert tuple(driver.FIGURE_STEMS) == EXPECTED_FIGURE_STEMS
        assert tuple(driver.TABLE_STEMS) == EXPECTED_TABLE_STEMS
        assert driver.EXPECTED_FILES == EXPECTED_PUBLICATION_FILES
        assert len(driver.EXPECTED_FILES) == 39


def _write_rendered_output(
    output: Path, *, skip: int = 0, extra: dict[str, bytes] | None = None
) -> None:
    for index, name in enumerate(sorted(driver.EXPECTED_FILES)):
        if index < skip:
            continue
        path = output / name
        path.parent.mkdir(parents=True, exist_ok=True)
        if name.endswith(".tex"):
            path.write_bytes(TEX_A)
        elif name.endswith(".pdf"):
            path.write_bytes(PDF_A)
        else:
            path.write_bytes(PNG_A)
    for name, payload in (extra or {}).items():
        path = output / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(payload)


def _write_figures(target: Path) -> None:
    for stem in driver.FIGURE_STEMS:
        for fmt, payload in (("pdf", PDF_A), ("png", PNG_A)):
            path = target / f"{stem}.{fmt}"
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(payload)


def _write_tables(target: Path) -> None:
    for stem in driver.TABLE_STEMS:
        path = target / f"{stem}.tex"
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(TEX_A)


def _archived_tables(workspace: Path) -> Path:
    paper = workspace / "reference" / "paper"
    for stem in driver.TABLE_STEMS:
        path = paper / "tables" / f"{stem}.tex"
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(f"% archived {stem}\n".encode())
    return paper


def _fake_generator_modules(reference: Path) -> dict[str, ModuleType]:
    modules: dict[str, ModuleType] = {}
    for kind, writer in (("figure", _write_figures), ("table", _write_tables)):
        source = reference / "src" / "prinet" / "utils" / f"{kind}_generation.py"
        source.parent.mkdir(parents=True, exist_ok=True)
        source.write_bytes(f"# synthetic {kind} generator\n".encode())
        module = ModuleType(f"prinet.utils.{kind}_generation")
        module.__file__ = str(source)
        setattr(
            module,
            f"generate_all_{kind}s",
            lambda results, out, w=writer: w(out),
        )
        modules[f"prinet.utils.{kind}_generation"] = module
    return modules


def _reference_pins(reference: Path) -> dict[str, str]:
    pins: dict[str, str] = {}
    for kind in ("figure", "table"):
        relative = f"src/prinet/utils/{kind}_generation.py"
        pins[relative] = _sha256((reference / relative).read_bytes())
    return pins


class TestCollectReproduction:
    def _renderer(self, monkeypatch: pytest.MonkeyPatch) -> dict[str, Any]:
        renderer = {"matplotlib": "x", "backend": "Agg", "font_sha256": {}}
        monkeypatch.setattr(driver, "_render_environment", lambda: renderer)
        return renderer

    def test_prin_arm_inventory(
        self, workspace: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        _archived_tables(workspace)
        snapshot = workspace / "snapshot"
        snapshot.mkdir()
        output = driver.OUTPUT_ROOT / "publication"
        renderer = self._renderer(monkeypatch)
        calls = []
        manifest_calls = []

        def fake_repro(
            *,
            results_dir: Path,
            output_dir: Path,
            manifest_path: Path,
            verify: bool,
        ) -> None:
            calls.append((results_dir, output_dir, manifest_path, verify))
            _write_rendered_output(output_dir)

        monkeypatch.setattr(driver, "run_reproduction", fake_repro)
        monkeypatch.setattr(
            driver, "verify_manifest", lambda *args: manifest_calls.append(args)
        )
        result = driver.collect_reproduction("prin", snapshot, output)
        assert result["implementation"] == "prin"
        assert result["renderer"] == renderer
        assert result["expected_files"] == sorted(driver.EXPECTED_FILES)
        assert len(result["files"]) == 39
        assert calls == [(snapshot, output, driver.INPUT_MANIFEST, True)]
        assert manifest_calls == [(snapshot, driver.INPUT_MANIFEST)]
        records = {record["path"]: record for record in result["files"]}
        assert set(records) == set(driver.EXPECTED_FILES)
        figure = records["figures/fig2_clevr_n_capacity.pdf"]
        assert figure["raw_bytes"] == len(PDF_A)
        assert figure["raw_sha256"] == _sha256(PDF_A)
        assert figure["normalized_sha256"] == _sha256(
            driver.normalized_bytes(PDF_A, ".pdf")
        )
        sensitivity = driver.sensitivity_bytes(PDF_A, ".pdf")
        assert figure["sensitivity_bytes"] == len(sensitivity)
        assert figure["sensitivity_sha256"] == _sha256(sensitivity)
        table = records["tables/tab_ablation.tex"]
        assert table["raw_sha256"] == _sha256(TEX_A)
        assert table["normalized_sha256"] == _sha256(TEX_A)
        assert table["sensitivity_bytes"] == len(TEX_A)
        assert table["sensitivity_sha256"] == _sha256(TEX_A)
        assert table["archived_sha256"] == _sha256(b"% archived tab_ablation\n")
        assert (output / "figures" / "fig2_clevr_n_capacity.pdf").read_bytes() == PDF_A

    def test_reference_arm_inventory(
        self, workspace: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        _archived_tables(workspace)
        reference = workspace / "reference"
        modules = _fake_generator_modules(reference)
        monkeypatch.setattr(driver, "REFERENCE_PINS", _reference_pins(reference))
        monkeypatch.setattr(importlib, "import_module", lambda name: modules[name])
        monkeypatch.setattr(driver, "verify_manifest", lambda *args: ())
        self._renderer(monkeypatch)
        snapshot = workspace / "snapshot"
        snapshot.mkdir()
        output = driver.OUTPUT_ROOT / "publication"
        result = driver.collect_reproduction("reference", snapshot, output)
        assert result["implementation"] == "reference"
        assert len(result["files"]) == 39
        records = {record["path"]: record for record in result["files"]}
        assert records["tables/tab_ablation.tex"]["archived_sha256"] == _sha256(
            b"% archived tab_ablation\n"
        )

    def test_unregistered_implementation_rejected(
        self, workspace: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        self._renderer(monkeypatch)
        output = driver.OUTPUT_ROOT / "publication"
        with pytest.raises(driver.DriverError, match="unregistered"):
            driver.collect_reproduction("other", workspace / "snapshot", output)

    def test_output_outside_root_rejected(
        self, workspace: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        self._renderer(monkeypatch)
        snapshot = workspace / "snapshot"
        snapshot.mkdir()
        with pytest.raises(driver.DriverError, match="outside"):
            driver.collect_reproduction(
                "prin", snapshot, workspace / "elsewhere" / "out"
            )
        with pytest.raises(driver.DriverError, match="outside"):
            driver.collect_reproduction("prin", snapshot, driver.OUTPUT_ROOT)

    def test_existing_output_rejected(
        self, workspace: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        self._renderer(monkeypatch)
        output = driver.OUTPUT_ROOT / "publication"
        output.mkdir(parents=True)
        with pytest.raises(driver.DriverError, match="must be new"):
            driver.collect_reproduction("prin", workspace / "snapshot", output)

    @_needs_symlink_support
    def test_output_symlink_ancestor_rejected(
        self, workspace: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        self._renderer(monkeypatch)
        real = workspace / "real-outputs"
        real.mkdir()
        link = workspace / "linked-outputs"
        link.symlink_to(real, target_is_directory=True)
        monkeypatch.setattr(driver, "OUTPUT_ROOT", link)
        snapshot = workspace / "snapshot"
        snapshot.mkdir()
        with pytest.raises(driver.DriverError, match="symlink ancestor"):
            driver.collect_reproduction("prin", snapshot, link / "out")

    def test_generator_failure_propagates(
        self, workspace: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        self._renderer(monkeypatch)

        def broken(**kwargs: Any) -> None:
            raise RuntimeError("render failed")

        monkeypatch.setattr(driver, "run_reproduction", broken)
        with pytest.raises(RuntimeError, match="render failed"):
            driver.collect_reproduction(
                "prin", workspace / "snapshot", driver.OUTPUT_ROOT / "out"
            )

    def test_renderer_change_aborts(
        self, workspace: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        _archived_tables(workspace)
        states = iter([{"renderer": 1}, {"renderer": 2}])
        monkeypatch.setattr(driver, "_render_environment", lambda: next(states))
        monkeypatch.setattr(
            driver,
            "run_reproduction",
            lambda **kwargs: _write_rendered_output(kwargs["output_dir"]),
        )
        monkeypatch.setattr(driver, "verify_manifest", lambda *args: ())
        with pytest.raises(driver.DriverError, match="changed during"):
            driver.collect_reproduction(
                "prin", workspace / "snapshot", driver.OUTPUT_ROOT / "out"
            )

    def test_reference_origin_and_digest_guards(
        self, workspace: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        self._renderer(monkeypatch)
        reference = workspace / "reference"
        modules = _fake_generator_modules(reference)
        pins = _reference_pins(reference)
        pins["src/prinet/utils/table_generation.py"] = "0" * 64
        monkeypatch.setattr(driver, "REFERENCE_PINS", pins)
        snapshot = workspace / "snapshot"
        snapshot.mkdir()
        output = driver.OUTPUT_ROOT / "out"

        wrong_module = ModuleType("prinet.utils.figure_generation")
        wrong_module.__file__ = str(workspace / "elsewhere.py")
        monkeypatch.setattr(importlib, "import_module", lambda name: wrong_module)
        with pytest.raises(driver.DriverError, match="governed source"):
            driver.collect_reproduction("reference", snapshot, output)

        monkeypatch.setattr(importlib, "import_module", lambda name: modules[name])
        with pytest.raises(driver.DriverError, match="generator changed"):
            driver.collect_reproduction("reference", snapshot, output)

    def test_missing_and_extra_outputs_are_retained(
        self, workspace: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        _archived_tables(workspace)
        self._renderer(monkeypatch)
        monkeypatch.setattr(
            driver,
            "run_reproduction",
            lambda **kwargs: _write_rendered_output(
                kwargs["output_dir"],
                skip=1,
                extra={"figures/extra_fig.pdf": PDF_B},
            ),
        )
        monkeypatch.setattr(driver, "verify_manifest", lambda *args: ())
        output = driver.OUTPUT_ROOT / "out"
        result = driver.collect_reproduction("prin", workspace / "snapshot", output)
        names = {record["path"] for record in result["files"]}
        assert "figures/extra_fig.pdf" in names
        assert sorted(driver.EXPECTED_FILES)[0] not in names
        assert len(result["files"]) == 39
        assert len(result["expected_files"]) == 39

    def test_unregistered_output_format_aborts(
        self, workspace: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        _archived_tables(workspace)
        self._renderer(monkeypatch)
        monkeypatch.setattr(
            driver,
            "run_reproduction",
            lambda **kwargs: _write_rendered_output(
                kwargs["output_dir"], extra={"figures/bad.svg": b"<svg/>"}
            ),
        )
        monkeypatch.setattr(driver, "verify_manifest", lambda *args: ())
        with pytest.raises(driver.DriverError, match="unregistered"):
            driver.collect_reproduction(
                "prin", workspace / "snapshot", driver.OUTPUT_ROOT / "out"
            )

    @_needs_symlink_support
    def test_symlinked_output_rejected(
        self, workspace: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        _archived_tables(workspace)
        self._renderer(monkeypatch)
        outside = workspace / "outside.pdf"
        outside.write_bytes(PDF_A)

        def symlink_render(**kwargs: Any) -> None:
            _write_rendered_output(kwargs["output_dir"])
            target = kwargs["output_dir"] / "figures" / "link.pdf"
            target.symlink_to(outside)

        monkeypatch.setattr(driver, "run_reproduction", symlink_render)
        with pytest.raises(driver.DriverError, match="symlink"):
            driver.collect_reproduction(
                "prin", workspace / "snapshot", driver.OUTPUT_ROOT / "out"
            )

    def test_nonregular_output_rejected_before_format_read(
        self, workspace: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        _archived_tables(workspace)
        self._renderer(monkeypatch)
        monkeypatch.setattr(
            driver,
            "run_reproduction",
            lambda **kwargs: _write_rendered_output(kwargs["output_dir"]),
        )
        monkeypatch.setattr(driver, "verify_manifest", lambda *args: ())
        abnormal = "fig2_clevr_n_capacity.pdf"
        real_is_file = Path.is_file
        real_is_dir = Path.is_dir
        monkeypatch.setattr(
            Path,
            "is_file",
            lambda path: False if path.name == abnormal else real_is_file(path),
        )
        monkeypatch.setattr(
            Path,
            "is_dir",
            lambda path: False if path.name == abnormal else real_is_dir(path),
        )
        with pytest.raises(driver.DriverError, match="not a regular file"):
            driver.collect_reproduction(
                "prin", workspace / "snapshot", driver.OUTPUT_ROOT / "out"
            )

    def test_manifest_verification_failure_propagates(
        self, workspace: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        _archived_tables(workspace)
        self._renderer(monkeypatch)
        monkeypatch.setattr(
            driver,
            "run_reproduction",
            lambda **kwargs: _write_rendered_output(kwargs["output_dir"]),
        )

        def failing(*args: Any) -> tuple[Any, ...]:
            raise reproduce.ManifestMismatchError("manifest drift")

        monkeypatch.setattr(driver, "verify_manifest", failing)
        with pytest.raises(reproduce.ManifestMismatchError):
            driver.collect_reproduction(
                "prin", workspace / "snapshot", driver.OUTPUT_ROOT / "out"
            )


def _snapshot_records() -> dict[str, bytes]:
    payloads: dict[str, bytes] = {}
    for index in range(172):
        if index < len(driver.CONCLUSION_FILES):
            name = driver.CONCLUSION_FILES[index]
            payloads[name] = b'{"document": true}\n'
        else:
            payloads[f"input_{index:03d}.json"] = f'{{"i": {index}}}\n'.encode()
    return payloads


class TestSnapshot:
    def _manifest(self, workspace: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        manifest = workspace / "manifest.json"
        manifest.write_bytes(b'{"synthetic": true}\n')
        monkeypatch.setattr(
            driver, "INPUT_MANIFEST_SHA", _sha256(manifest.read_bytes())
        )

    def _records(self, count: int = 172) -> tuple[ManifestRecord, ...]:
        payloads = _snapshot_records()
        return tuple(
            ManifestRecord(path=name, bytes=len(payload), sha256=_sha256(payload))
            for name, payload in list(payloads.items())[:count]
        )

    def test_snapshot_writes_every_verified_byte(
        self, workspace: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        self._manifest(workspace, monkeypatch)
        records = self._records()
        payloads = _snapshot_records()
        verify_calls: list[tuple[Path, Path]] = []
        read_calls: list[str] = []

        def fake_verify(results_dir: Path, manifest_path: Path) -> tuple[Any, ...]:
            verify_calls.append((results_dir, manifest_path))
            return records

        def fake_read(
            path: Path,
            expected_size: int,
            expected_sha256: str,
            name: str,
            role: str,
        ) -> bytes:
            read_calls.append(name)
            record = next(item for item in records if item.path == name)
            assert expected_size == record.bytes
            assert expected_sha256 == record.sha256
            return payloads[name]

        monkeypatch.setattr(driver, "verify_manifest", fake_verify)
        monkeypatch.setattr(driver, "read_verified_no_follow", fake_read)
        reference_results = workspace / "reference" / "benchmarks" / "results"
        for name, payload in payloads.items():
            source = reference_results / name
            source.parent.mkdir(parents=True, exist_ok=True)
            source.write_bytes(payload)
        destination = driver.OUTPUT_ROOT / "inputs"
        documents, identity = driver._snapshot(destination)
        assert len(read_calls) == 172
        assert verify_calls[0][0] == reference_results
        assert verify_calls[1] == (destination, driver.INPUT_MANIFEST)
        for name, payload in payloads.items():
            assert (destination / name).read_bytes() == payload
            assert (reference_results / name).read_bytes() == payload
        assert set(documents) == set(driver.CONCLUSION_FILES)
        assert identity["input_record_count"] == 172
        assert identity["input_manifest_sha256"] == driver.INPUT_MANIFEST_SHA
        assert len(identity["input_records"]) == 172

    def test_manifest_digest_mismatch_aborts(
        self, workspace: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        self._manifest(workspace, monkeypatch)
        monkeypatch.setattr(driver, "INPUT_MANIFEST_SHA", "0" * 64)
        with pytest.raises(driver.DriverError, match="manifest changed"):
            driver._snapshot(driver.OUTPUT_ROOT / "inputs")

    def test_wrong_record_count_aborts(
        self, workspace: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        self._manifest(workspace, monkeypatch)
        monkeypatch.setattr(driver, "verify_manifest", lambda *args: self._records(171))
        with pytest.raises(driver.DriverError, match="exactly 172"):
            driver._snapshot(driver.OUTPUT_ROOT / "inputs")

    def test_failed_record_read_aborts_without_rewriting_source(
        self, workspace: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        self._manifest(workspace, monkeypatch)
        records = self._records()
        monkeypatch.setattr(driver, "verify_manifest", lambda *args: records)
        original = b'{"source": "bytes"}\n'
        reference_results = workspace / "reference" / "benchmarks" / "results"
        for record in records:
            source = reference_results / record.path
            source.parent.mkdir(parents=True, exist_ok=True)
            source.write_bytes(original)

        def failing_read(*args: Any) -> bytes:
            raise reproduce.ManifestMismatchError("per-record mismatch")

        monkeypatch.setattr(driver, "read_verified_no_follow", failing_read)
        with pytest.raises(reproduce.ManifestMismatchError):
            driver._snapshot(driver.OUTPUT_ROOT / "inputs")
        for record in records:
            assert (reference_results / record.path).read_bytes() == original


class TestAdmission:
    def test_draft_protocol_refused_before_any_work(
        self, workspace: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        _protocol_file(workspace, PROTOCOL_DRAFT)
        monkeypatch.setattr(
            driver,
            "_snapshot",
            lambda *args: pytest.fail("snapshot must not run"),
        )
        monkeypatch.setattr(
            driver,
            "collect_api",
            lambda: pytest.fail("collector must not run"),
        )
        run = driver.RAW_ROOT / _run_name("api")
        with pytest.raises(driver.DriverError, match="EXP-002-r1 is not APPROVED"):
            driver.run_registered("api", run, "devin", SHA)
        assert not run.exists()
        assert not (driver.OUTPUT_ROOT / run.name).exists()

    def test_draft_header_not_overridden_by_later_approved_example(
        self, workspace: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        _protocol_file(
            workspace,
            "**Status:** DRAFT\n\n"
            "example only:\n\n**Status:** APPROVED\n\n"
            "**Maintainer approval:** MichaelMaillet, 2026-10-20 UTC\n",
        )
        monkeypatch.setattr(driver, "_git_bytes", _fake_git())
        run = driver.RAW_ROOT / _run_name("api")
        with pytest.raises(driver.DriverError, match="not APPROVED"):
            driver.run_registered("api", run, "devin", SHA)
        assert not run.exists()

    def test_status_choice_list_rejected_before_any_work(
        self, workspace: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        _protocol_file(
            workspace,
            "**Status:** APPROVED | DRAFT\n\n"
            "**Maintainer approval:** MichaelMaillet, 2026-10-20 UTC\n",
        )
        monkeypatch.setattr(driver, "_git_bytes", _fake_git())
        monkeypatch.setattr(
            driver,
            "_snapshot",
            lambda *args: pytest.fail("snapshot must not run"),
        )
        monkeypatch.setattr(
            driver,
            "collect_api",
            lambda: pytest.fail("collector must not run"),
        )
        run = driver.RAW_ROOT / _run_name("api")
        with pytest.raises(driver.DriverError, match="not APPROVED"):
            driver.run_registered("api", run, "devin", SHA)
        assert not run.exists()
        assert not (driver.OUTPUT_ROOT / run.name).exists()

    def test_missing_dated_approval_refused(
        self, workspace: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        _protocol_file(
            workspace,
            PROTOCOL_APPROVED.replace(
                "**Maintainer approval:** MichaelMaillet, 2026-10-20 UTC",
                "**Maintainer approval:** NOT GRANTED",
            ),
        )
        monkeypatch.setattr(driver, "_git_bytes", _fake_git())
        run = driver.RAW_ROOT / _run_name("api")
        with pytest.raises(driver.DriverError, match="approval is missing"):
            driver.run_registered("api", run, "devin", SHA)
        assert not run.exists()

    def test_invalid_approval_date_refused(
        self, workspace: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        _protocol_file(
            workspace,
            PROTOCOL_APPROVED.replace("2026-10-20", "2026-13-45"),
        )
        monkeypatch.setattr(driver, "_git_bytes", _fake_git())
        with pytest.raises((driver.DriverError, ValueError)):
            driver.run_registered(
                "api", driver.RAW_ROOT / _run_name("api"), "devin", SHA
            )

    def test_source_sha_rejected(
        self, workspace: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        _protocol_file(workspace)
        monkeypatch.setattr(driver, "_git_bytes", _fake_git())
        for bad in ("abc", OTHER_SHA, "Z" * 40):
            with pytest.raises(driver.DriverError, match="40-character HEAD"):
                driver.run_registered(
                    "api", driver.RAW_ROOT / _run_name("api"), "devin", bad
                )

    @pytest.mark.parametrize(
        "dirty",
        [
            {"changed": "python/prin/x.py\n"},
            {"untracked": "tools/rogue.py\n"},
            {"untracked": "benchmarks/results/EXP-002/rogue.json\n"},
        ],
        ids=["dirty-tracked", "untracked-source", "untracked-predecessor-exp002"],
    )
    def test_uncommitted_changes_refused(
        self,
        workspace: Path,
        monkeypatch: pytest.MonkeyPatch,
        dirty: dict[str, Any],
    ) -> None:
        _protocol_file(workspace)
        monkeypatch.setattr(driver, "_git_bytes", _fake_git(**dirty))
        with pytest.raises(driver.DriverError, match="uncommitted"):
            driver.run_registered(
                "api", driver.RAW_ROOT / _run_name("api"), "devin", SHA
            )

    def test_benchmark_results_exp002_r1_untracked_is_exempt(
        self, workspace: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        _protocol_file(workspace)
        monkeypatch.setattr(
            driver,
            "_git_bytes",
            _fake_git(untracked="benchmarks/results/EXP-002-r1/x.json\n"),
        )
        monkeypatch.setattr(
            driver, "capture_environment", lambda **kw: _fake_environment()
        )
        monkeypatch.setattr(driver, "_snapshot", lambda dest: ({}, _fake_identity()))
        monkeypatch.setattr(driver, "collect_api", lambda: _fake_observations("api"))
        run = driver.run_registered(
            "api", driver.RAW_ROOT / _run_name("api"), "devin", SHA
        )
        assert run.is_dir()

    def test_working_protocol_divergence_refused(
        self, workspace: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        _protocol_file(workspace)
        monkeypatch.setattr(
            driver, "_git_bytes", _fake_git(committed=b"different committed bytes")
        )
        with pytest.raises(driver.DriverError, match="committed bytes"):
            driver.run_registered(
                "api", driver.RAW_ROOT / _run_name("api"), "devin", SHA
            )

    def test_seed_and_operator_guards(
        self, admitted: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        run = driver.RAW_ROOT / _run_name("api")
        for kwargs in (
            {"seed_counter": 1},
            {"seed_key": 3},
            {"operator": "   "},
        ):
            call: dict[str, Any] = {
                "mode": "api",
                "run_dir": run,
                "operator": "devin",
                "source_sha": SHA,
            }
            call.update(kwargs)
            with pytest.raises(driver.DriverError, match="seed pair"):
                driver.run_registered(**call)


class TestReserve:
    def test_happy_path_creates_directory(self, workspace: Path) -> None:
        run = driver.RAW_ROOT / _run_name("api")
        assert driver._reserve("api", run, SHA) == run
        assert run.is_dir()

    @pytest.mark.parametrize(
        "name",
        [
            "RUN-20261020T120000Z-aaaaaaa-r1-conclusions-cpu",
            "RUN-20261020T120000Z-bbbbbbb-r1-api-cpu",
            "RUN-20261020T120000Z-aaaaaaa-api-cpu",
            "RUN-20261020T120000Z-aaaaaaa-r1-api-cpu\nnewline",
            "RUN-20261020T120000Z-aaaaaaa-R1-API-CPU",
            "RUN-20261020T120000Z-aaaaaaa-",
        ],
        ids=[
            "wrong-label",
            "wrong-sha",
            "unprefixed-legacy-label",
            "newline",
            "case",
            "empty-label",
        ],
    )
    def test_invalid_names_rejected(self, workspace: Path, name: str) -> None:
        with pytest.raises(driver.DriverError, match="registered"):
            driver._reserve("api", driver.RAW_ROOT / name, SHA)

    def test_unknown_mode_rejected(self, workspace: Path) -> None:
        with pytest.raises(driver.DriverError):
            driver._reserve("bogus", driver.RAW_ROOT / _run_name("api"), SHA)

    def test_parent_escape_rejected(self, workspace: Path) -> None:
        with pytest.raises(driver.DriverError, match="direct-child"):
            driver._reserve("api", workspace / _run_name("api"), SHA)

    def test_existing_directory_never_reused(self, workspace: Path) -> None:
        run = driver.RAW_ROOT / _run_name("api")
        run.mkdir()
        with pytest.raises(driver.DriverError, match="never reused"):
            driver._reserve("api", run, SHA)

    def test_missing_raw_root_rejected(self, workspace: Path) -> None:
        driver.RAW_ROOT.rmdir()
        with pytest.raises(driver.DriverError, match="raw root is missing"):
            driver._reserve("api", driver.RAW_ROOT / _run_name("api"), SHA)

    def test_bad_timestamp_rejected(self, workspace: Path) -> None:
        run = driver.RAW_ROOT / "RUN-20261345T120000Z-aaaaaaa-r1-api-cpu"
        with pytest.raises((driver.DriverError, ValueError)):
            driver._reserve("api", run, SHA)

    @_needs_symlink_support
    def test_symlink_ancestor_rejected(
        self, workspace: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        real = workspace / "real-raw"
        real.mkdir()
        link = workspace / "linked-raw"
        link.symlink_to(real, target_is_directory=True)
        monkeypatch.setattr(driver, "RAW_ROOT", link)
        with pytest.raises(driver.DriverError, match="symlink ancestor"):
            driver._reserve("api", link / _run_name("api"), SHA)


class TestRunRegistered:
    @pytest.mark.parametrize("mode", sorted(driver.MODE_LABELS))
    def test_successful_run_writes_exact_inventory(
        self, admitted: Path, monkeypatch: pytest.MonkeyPatch, mode: str
    ) -> None:
        snapshot_calls: list[Path] = []

        def fake_snap(dest: Path) -> tuple[dict[str, Any], dict[str, Any]]:
            snapshot_calls.append(dest)
            return ({"d": {}}, _fake_identity())

        monkeypatch.setattr(driver, "_snapshot", fake_snap)
        monkeypatch.setattr(driver, "collect_api", lambda: _fake_observations("api"))
        monkeypatch.setattr(
            driver,
            "collect_conclusions",
            lambda docs: _fake_observations("conclusions"),
        )
        monkeypatch.setattr(
            driver,
            "collect_reproduction",
            lambda implementation, snapshot, output: _fake_observations(implementation),
        )
        run_dir = driver.RAW_ROOT / _run_name(mode)
        run = driver.run_registered(mode, run_dir, "devin", SHA)
        assert run == run_dir
        assert sorted(path.name for path in run.iterdir()) == sorted(
            [
                "campaign-metadata.json",
                "manifest.json",
                RESULT_NAMES[mode],
            ]
        )
        generated = driver.OUTPUT_ROOT / run.name
        assert generated.is_dir()
        assert snapshot_calls == [generated / "inputs"]
        metadata = json.loads(
            (run / "campaign-metadata.json").read_text(encoding="utf-8")
        )
        assert metadata["exp_id"] == "EXP-002-r1"
        assert metadata["session"] == "EXP-002-r1-E3"
        assert metadata["run_id"] == run.name
        assert metadata["operator"] == "devin"
        assert metadata["mode"] == mode
        assert metadata["artefacts"] == {RESULT_NAMES[mode]: driver.MODE_TAGS[mode]}
        result = json.loads((run / RESULT_NAMES[mode]).read_text(encoding="utf-8"))
        assert result["status"] == "COMPLETED"
        assert result["seed_used"] is False
        assert result["identity"]["source_sha"] == SHA
        assert result["identity"]["input_record_count"] == 172
        assert result["identity"]["prin_core_pyd_sha256"] == driver.PRIN_CORE_PYD_SHA256
        assert result["identity"]["prin_core_pyd_bytes"] == driver.PRIN_CORE_PYD_BYTES
        config = result["config"]
        assert config["seed_counter"] == 0
        assert config["seed_key"] == 2
        assert config["iterations"] == 10
        assert config["warmup"] == 0
        assert config["replicates"] == 1
        assert config["measurement_kind"] == "deterministic_census"
        assert config["out_dir"] == str(run)
        assert isinstance(result["started_at_utc"], str)
        assert isinstance(result["recorded_at_utc"], str)
        assert isinstance(result["elapsed_seconds"], (int, float))
        driver.check_run_complete(run)

    def test_generated_output_root_reuse_rejected(self, admitted: Path) -> None:
        run_dir = driver.RAW_ROOT / _run_name("api")
        stale = driver.OUTPUT_ROOT / run_dir.name
        stale.mkdir()
        with pytest.raises(driver.DriverError, match="never reused"):
            driver.run_registered("api", run_dir, "devin", SHA)
        assert not run_dir.exists()

    def test_collector_crash_retains_aborted_run(
        self, admitted: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.setattr(driver, "_snapshot", lambda dest: ({}, _fake_identity()))

        def crash() -> None:
            raise RuntimeError("collector boom")

        monkeypatch.setattr(driver, "collect_api", crash)
        run_dir = driver.RAW_ROOT / _run_name("api")
        with pytest.raises(driver.DriverError, match="aborted run retained"):
            driver.run_registered("api", run_dir, "devin", SHA)
        result = json.loads((run_dir / "api.json").read_text(encoding="utf-8"))
        assert result["status"] == "ABORTED"
        assert "RuntimeError" in result["abort_reason"]
        assert (run_dir / "campaign-metadata.json").is_file()
        assert (run_dir / "manifest.json").is_file()
        with pytest.raises(driver.DriverError):
            driver.check_run_complete(run_dir)

    def test_environment_mismatch_refused(self, admitted: Path) -> None:
        with pytest.MonkeyPatch.context() as context:
            context.setattr(
                driver,
                "capture_environment",
                lambda **kwargs: _fake_environment(OTHER_SHA),
            )
            with pytest.raises(driver.DriverError, match="source/version"):
                driver.run_registered(
                    "api", driver.RAW_ROOT / _run_name("api"), "devin", SHA
                )

    def test_cpu_wall_cap_records_aborted_run(
        self, admitted: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.setattr(driver, "_snapshot", lambda dest: ({}, _fake_identity()))
        monkeypatch.setattr(driver, "collect_api", lambda: _fake_observations("api"))
        monkeypatch.setattr(driver, "CPU_WALL_CAP", -1)
        run_dir = driver.RAW_ROOT / _run_name("api")
        with pytest.raises(driver.DriverError, match="aborted run retained"):
            driver.run_registered("api", run_dir, "devin", SHA)
        result = json.loads((run_dir / "api.json").read_text(encoding="utf-8"))
        assert result["status"] == "ABORTED"
        assert "CPU wall cap" in result["abort_reason"]

    @_needs_symlink_support
    def test_output_root_symlink_ancestor_rejected(
        self, admitted: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        real = admitted / "real-generated"
        real.mkdir()
        link = admitted / "linked-generated"
        link.symlink_to(real, target_is_directory=True)
        monkeypatch.setattr(driver, "OUTPUT_ROOT", link)
        run_dir = driver.RAW_ROOT / _run_name("api")
        with pytest.raises(driver.DriverError, match="symlink ancestor"):
            driver.run_registered("api", run_dir, "devin", SHA)
        assert not run_dir.exists()


def _edit_env(key: str, value: object) -> Any:
    def apply(doc: dict[str, Any]) -> None:
        doc["environment"][key] = value

    return apply


def _edit_config(key: str, value: object) -> Any:
    def apply(doc: dict[str, Any]) -> None:
        doc["config"][key] = value

    return apply


def _edit_identity(key: str, value: object) -> Any:
    def apply(doc: dict[str, Any]) -> None:
        doc["identity"][key] = value

    return apply


_RESULT_MUTATIONS: list[tuple[str, Any]] = [
    ("status-aborted", lambda d: d.update(status="ABORTED")),
    ("env-sha-malformed", _edit_env("git_commit", "abc")),
    ("env-sha-mismatch", _edit_env("git_commit", OTHER_SHA)),
    ("identity-sha", _edit_identity("source_sha", OTHER_SHA)),
    ("identity-manifest", _edit_identity("input_manifest_sha256", "0" * 64)),
    ("prereg-sha-malformed", _edit_identity("preregistration_sha256", "x")),
    ("prereg-commit-malformed", _edit_identity("preregistration_commit", "y")),
    ("prereg-sha-fabricated", _edit_identity("preregistration_sha256", "f" * 64)),
    ("approval-date-missing", lambda d: d["identity"].pop("approval_date_utc")),
    ("approval-date-mismatch", _edit_identity("approval_date_utc", "2026-10-12")),
    ("approval-date-not-a-date", _edit_identity("approval_date_utc", "not-a-date")),
    ("approval-date-non-str", _edit_identity("approval_date_utc", 20261020)),
    ("pyd-sha-missing", lambda d: d["identity"].pop("prin_core_pyd_sha256")),
    ("pyd-sha-mismatch", _edit_identity("prin_core_pyd_sha256", "0" * 64)),
    ("pyd-bytes-mismatch", _edit_identity("prin_core_pyd_bytes", 123)),
    ("pyd-bytes-bool", _edit_identity("prin_core_pyd_bytes", True)),
    ("observations-missing", lambda d: d.pop("observations")),
    ("observations-non-mapping", lambda d: d.update(observations=[])),
    ("record-count", _edit_identity("input_record_count", 171)),
    ("seed-counter-bool", _edit_config("seed_counter", False)),
    ("seed-counter-float", _edit_config("seed_counter", 0.0)),
    ("seed-counter-value", _edit_config("seed_counter", 1)),
    ("seed-key-bool", _edit_config("seed_key", True)),
    ("seed-key-value", _edit_config("seed_key", 3)),
    ("iterations-type", _edit_config("iterations", "10")),
    ("iterations-value", _edit_config("iterations", 9)),
    ("warmup-value", _edit_config("warmup", 1)),
    ("replicates-value", _edit_config("replicates", 2)),
    ("measurement-kind", _edit_config("measurement_kind", "timing")),
    (
        "out-dir-wrong-tail-predecessor",
        _edit_config(
            "out_dir",
            "/x/benchmarks/results/EXP-002/" + _run_name("api"),
        ),
    ),
    (
        "out-dir-parent-escape",
        _edit_config(
            "out_dir",
            "/x/benchmarks/results/EXP-002-r1/../EXP-002-r1/" + _run_name("api"),
        ),
    ),
    ("out-dir-non-str", _edit_config("out_dir", 5)),
    ("env-seed-bool", _edit_env("seed", False)),
    ("env-seed-value", _edit_env("seed", 1)),
    ("env-backend", _edit_env("backend", "cuda")),
    ("env-dtype", _edit_env("dtype", "f32")),
    ("env-prin-version", _edit_env("prin_version", "9.9.9")),
    ("seed-used", lambda d: d.update(seed_used=True)),
]

_METADATA_MUTATIONS: list[tuple[str, Any]] = [
    ("mode-invalid", lambda d: d.update(mode="bogus")),
    ("mode-non-str", lambda d: d.update(mode=1)),
    ("exp-id-predecessor", lambda d: d.update(exp_id="EXP-002")),
    ("session-predecessor", lambda d: d.update(session="0161")),
    ("run-id", lambda d: d.update(run_id="RUN-other")),
    ("artefacts", lambda d: d.update(artefacts={"api.json": ["H9"]})),
    ("operator-blank", lambda d: d.update(operator="   ")),
    ("operator-non-str", lambda d: d.update(operator=5)),
]


class TestCheckRunComplete:
    def test_valid_run_passes(self, workspace: Path) -> None:
        run = _write_valid_run()
        driver.check_run_complete(run)

    def test_relocation_path_spelling_accepted(self, workspace: Path) -> None:
        run = _write_valid_run()
        for spelling in (
            f"D:/clean/checkout/benchmarks/results/EXP-002-r1/{run.name}",
            f"D:\\clean\\checkout\\benchmarks\\results\\EXP-002-r1\\{run.name}",
        ):
            _rewrite_json(
                run,
                RESULT_NAMES["api"],
                lambda doc, s=spelling: doc["config"].update(out_dir=s),
            )
            driver.check_run_complete(run)

    def test_non_run_name_rejected(self, workspace: Path) -> None:
        bogus = driver.RAW_ROOT / "not-a-run"
        bogus.mkdir()
        with pytest.raises(driver.DriverError, match="invalid registered"):
            driver.check_run_complete(bogus)

    def test_wrong_parent_rejected(self, workspace: Path) -> None:
        moved_parent = workspace / "moved"
        moved_parent.mkdir()
        moved = _write_valid_run(parent=moved_parent)
        with pytest.raises(driver.DriverError, match="invalid registered"):
            driver.check_run_complete(moved)

    @pytest.mark.parametrize(
        "mutate",
        [mutate for _, mutate in _RESULT_MUTATIONS],
        ids=[label for label, _ in _RESULT_MUTATIONS],
    )
    def test_result_mutations_rejected(self, workspace: Path, mutate: Any) -> None:
        run = _write_valid_run()
        _rewrite_json(run, RESULT_NAMES["api"], mutate)
        with pytest.raises(driver.DriverError):
            driver.check_run_complete(run)

    @pytest.mark.parametrize(
        "mutate",
        [mutate for _, mutate in _METADATA_MUTATIONS],
        ids=[label for label, _ in _METADATA_MUTATIONS],
    )
    def test_metadata_mutations_rejected(self, workspace: Path, mutate: Any) -> None:
        run = _write_valid_run()
        _rewrite_json(run, "campaign-metadata.json", mutate)
        with pytest.raises(driver.DriverError):
            driver.check_run_complete(run)

    @pytest.mark.parametrize(
        "field,value",
        [
            ("rust_version", ""),
            ("python_version", None),
            ("platform", "   "),
            ("processor", ""),
        ],
        ids=["rust", "python", "platform", "processor"],
    )
    def test_required_environment_fields(
        self, workspace: Path, field: str, value: object
    ) -> None:
        run = _write_valid_run()

        def mutate(doc: dict[str, Any]) -> None:
            if value is None:
                del doc["environment"][field]
            else:
                doc["environment"][field] = value

        _rewrite_json(run, RESULT_NAMES["api"], mutate)
        with pytest.raises(driver.DriverError, match="environment field"):
            driver.check_run_complete(run)

    @pytest.mark.parametrize("cpus", [0, "8", -1], ids=["zero", "str", "neg"])
    def test_logical_cpus_invalid(self, workspace: Path, cpus: object) -> None:
        run = _write_valid_run()
        _rewrite_json(
            run,
            RESULT_NAMES["api"],
            lambda doc: doc["environment"].update(logical_cpus=cpus),
        )
        with pytest.raises(driver.DriverError, match="logical CPU"):
            driver.check_run_complete(run)

    def test_extra_manifested_file_rejected(self, workspace: Path) -> None:
        run = _write_valid_run()
        (run / "extra.json").write_text("{}", encoding="utf-8")
        _remanifest(run)
        with pytest.raises(driver.DriverError, match="inventory"):
            driver.check_run_complete(run)

    def test_unmanifested_file_rejected(self, workspace: Path) -> None:
        run = _write_valid_run()
        (run / "rogue.json").write_text("{}", encoding="utf-8")
        with pytest.raises(reproduce.ManifestMismatchError):
            driver.check_run_complete(run)

    def test_missing_result_rejected(self, workspace: Path) -> None:
        run = _write_valid_run()
        (run / "api.json").unlink()
        _remanifest(run)
        with pytest.raises(driver.DriverError):
            driver.check_run_complete(run)

    def test_missing_manifest_rejected(self, workspace: Path) -> None:
        run = _write_valid_run()
        (run / "manifest.json").unlink()
        with pytest.raises((driver.DriverError, reproduce.ReproductionError, OSError)):
            driver.check_run_complete(run)

    def test_label_mismatch_rejected(self, workspace: Path) -> None:
        run = _write_valid_run(
            mode="api",
            name="RUN-20261020T120000Z-aaaaaaa-r1-conclusions-cpu",
        )
        with pytest.raises(driver.DriverError, match="metadata/labels"):
            driver.check_run_complete(run)

    def test_changed_bytes_rejected(self, workspace: Path) -> None:
        run = _write_valid_run()
        path = run / "api.json"
        path.write_text(path.read_text(encoding="utf-8") + " ", encoding="utf-8")
        with pytest.raises((driver.DriverError, reproduce.ManifestMismatchError)):
            driver.check_run_complete(run)

    def test_non_mapping_result_rejected(self, workspace: Path) -> None:
        run = _write_valid_run()
        (run / "api.json").write_text("[]", encoding="utf-8")
        _remanifest(run)
        with pytest.raises(driver.DriverError):
            driver.check_run_complete(run)

    @pytest.mark.parametrize(
        "target",
        ["RUN_CAP", "RAW_CAP", "COMBINED_EXP002_CAP"],
        ids=["per-run-cap", "raw-cap", "combined-exp002-cap"],
    )
    def test_storage_caps(
        self,
        workspace: Path,
        monkeypatch: pytest.MonkeyPatch,
        target: str,
    ) -> None:
        run = _write_valid_run()
        monkeypatch.setattr(driver, target, 1)
        with pytest.raises(driver.DriverError, match="cap exceeded"):
            driver.check_run_complete(run)

    def test_combined_exp002_and_r1_storage_cap_enforced(self, workspace: Path) -> None:
        """Combined EXP-002 + EXP-002-r1 > 10 MiB fails even if r1 alone is small."""
        run = _write_valid_run()
        predecessor_file = driver.PREDECESSOR_RAW_ROOT / "prior.json"
        with predecessor_file.open("wb") as stream:
            stream.truncate(driver.COMBINED_EXP002_CAP)
        with pytest.raises(
            driver.DriverError, match="combined EXP-002 \\+ EXP-002-r1 10 MiB"
        ):
            driver.check_run_complete(run)

    def test_campaign_storage_cap(self, workspace: Path) -> None:
        run = _write_valid_run()
        sibling = driver.RAW_ROOT.parent / "EXP-001"
        sibling.mkdir()
        big = sibling / "large.json"
        with big.open("wb") as stream:
            stream.truncate(64 * 1024 * 1024 + 1)
        with pytest.raises(driver.DriverError, match="64 MiB"):
            driver.check_run_complete(run)

    @_needs_symlink_support
    def test_symlinked_run_dir_rejected(self, workspace: Path) -> None:
        run = _write_valid_run()
        link = driver.RAW_ROOT / "RUN-20261020T130000Z-aaaaaaa-r1-api-cpu"
        link.symlink_to(run, target_is_directory=True)
        with pytest.raises(driver.DriverError, match="invalid registered"):
            driver.check_run_complete(link)

    @_needs_symlink_support
    def test_symlinked_manifested_artefact_rejected(self, workspace: Path) -> None:
        run = _write_valid_run()
        outside = workspace / "outside.json"
        outside.write_text("{}", encoding="utf-8")
        (run / "api.json").unlink()
        (run / "api.json").symlink_to(outside)
        with pytest.raises(
            (driver.DriverError, reproduce.ManifestMismatchError, OSError)
        ):
            driver.check_run_complete(run)


class TestMain:
    def _argv(self, run: Path) -> list[str]:
        return [
            "--mode",
            "api",
            "--run-dir",
            str(run),
            "--operator",
            "devin",
            "--source-sha",
            SHA,
        ]

    def test_success_returns_zero(
        self, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
    ) -> None:
        run = tmp_path / "run"
        monkeypatch.setattr(driver, "run_registered", lambda *args, **kwargs: run)
        assert driver.main(self._argv(run)) == 0

    def test_driver_error_returns_one(
        self,
        monkeypatch: pytest.MonkeyPatch,
        capsys: Any,
        tmp_path: Path,
    ) -> None:
        def failing(*args: Any, **kwargs: Any) -> Path:
            raise driver.DriverError("guard tripped")

        monkeypatch.setattr(driver, "run_registered", failing)
        assert driver.main(self._argv(tmp_path / "run")) == 1
        assert "EXP-002-r1 NOT COMPLETED" in capsys.readouterr().err

    def test_invalid_mode_argparse_exits(self) -> None:
        with pytest.raises(SystemExit):
            driver.main(
                [
                    "--mode",
                    "bogus",
                    "--run-dir",
                    "x",
                    "--operator",
                    "o",
                    "--source-sha",
                    SHA,
                ]
            )

    def test_module_main_guard(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.delitem(
            sys.modules, "benchmarks.campaign.exp002_r1_driver", raising=False
        )
        monkeypatch.setattr(sys, "argv", ["exp002_r1_driver.py"])
        with pytest.raises(SystemExit) as excinfo:
            runpy.run_module(
                "benchmarks.campaign.exp002_r1_driver", run_name="__main__"
            )
        assert excinfo.value.code == 2


def _pdf_with_info(info: bytes, label: bytes = b"SCIENCE") -> bytes:
    """Classic-xref layout with an arbitrary Info dictionary body."""
    stream = b"BT /F1 8 Tf 2 2 Td (" + label + b") Tj ET\n"
    objects = [
        b"<< /Type /Catalog /Pages 2 0 R >>",
        b"<< /Type /Pages /Count 1 /Kids [3 0 R] >>",
        b"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 10 10] "
        b"/Contents 4 0 R /Resources << /Font << /F1 6 0 R >> >> >>",
        b"<< /Length "
        + str(len(stream)).encode()
        + b" >>\nstream\n"
        + stream
        + b"endstream",
        info,
        b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>",
    ]
    return _pdf_assemble(objects, b"11" * 16)


PDF_PRIN_INFO = _pdf_with_info(
    b"<< /Creator (PRIN) /Producer (Matplotlib)\n"
    b"/CreationDate (D:20000101000000Z) /ModDate (D:20000101000000Z) >>"
)
PDF_REFERENCE_INFO = _pdf_with_info(
    b"<< /Creator (Matplotlib v3.11.1, https://matplotlib.org)\n"
    b"/Producer (Matplotlib pdf backend v3.11.1)\n"
    b"/CreationDate (D:20261011170217-03'00') >>"
)


class TestPdfInfoCanonicalization:
    def test_key_set_and_wrap_asymmetry_normalizes_equal(self) -> None:
        assert PDF_PRIN_INFO != PDF_REFERENCE_INFO
        assert driver.normalized_bytes(PDF_PRIN_INFO, ".pdf") == (
            driver.normalized_bytes(PDF_REFERENCE_INFO, ".pdf")
        )

    def test_hex_string_registered_values_are_removed(self) -> None:
        hexed = _pdf_with_info(b"<< /Creator <FEFF0041> /Producer (x) >>")
        assert driver.normalized_bytes(hexed, ".pdf") == (
            driver.normalized_bytes(PDF_REFERENCE_INFO, ".pdf")
        )

    def test_unregistered_entries_retained_in_order(self) -> None:
        base = _pdf_with_info(b"<< /Title (T) /Creator (A) /Subject (S) >>")
        normalized = driver.normalized_bytes(base, ".pdf")
        assert b"<< /Title (T) /Subject (S) >>" in normalized
        reordered = _pdf_with_info(b"<< /Subject (S) /Creator (A) /Title (T) >>")
        assert driver.normalized_bytes(reordered, ".pdf") != normalized
        changed = _pdf_with_info(b"<< /Title (U) /Creator (A) /Subject (S) >>")
        assert driver.normalized_bytes(changed, ".pdf") != normalized

    def test_direct_value_kinds_are_tokenized(self) -> None:
        info = (
            b"<< /Trapped /False /Count 3 /Ratio -0.5 /Ref 6 0 R /Flag true "
            b"/Nested (a (b) \\) c) /Hex <0a 0B> /Creator (x) >>"
        )
        normalized = driver.normalized_bytes(_pdf_with_info(info), ".pdf")
        assert (
            b"<< /Trapped /False /Count 3 /Ratio -0.5 /Ref 6 0 R /Flag true "
            b"/Nested (a (b) \\) c) /Hex <0a 0B> >>"
        ) in normalized

    def test_content_difference_stays_significant(self) -> None:
        assert driver.normalized_bytes(PDF_PRIN_INFO, ".pdf") != (
            driver.normalized_bytes(
                _pdf_with_info(
                    b"<< /Creator (PRIN) /Producer (Matplotlib) >>", b"OTHER"
                ),
                ".pdf",
            )
        )

    @pytest.mark.parametrize(
        "info",
        [
            b"<< /Creator (A) /Creator (B) >>",
            b"<< /Keywords [1 2] >>",
            b"<< /Nested << /A 1 >> >>",
            b"<< /Creator (unterminated >>",
            b"<< Creator (A) >>",
            b"<< /Creator >>",
            b"(not a dictionary)",
            b"<< /Creator (A) >> /Extra 1 >>",
        ],
        ids=[
            "duplicate-key",
            "array-value",
            "dictionary-value",
            "unterminated-string",
            "bare-key",
            "missing-value",
            "non-dictionary",
            "content-after-close",
        ],
    )
    def test_malformed_info_rejected(self, info: bytes) -> None:
        with pytest.raises(driver.DriverError, match="Info dictionary"):
            driver.normalized_bytes(_pdf_with_info(info), ".pdf")


class TestPdfDecimalBounds:
    @pytest.mark.parametrize(
        "mutate",
        [
            lambda p: re.sub(rb"startxref\n[0-9]+", b"startxref\n" + b"9" * 5000, p),
            lambda p: re.sub(rb"startxref\n[0-9]+", b"startxref\n" + b"1" * 11, p),
            lambda p: p.replace(b"xref\n0 7\n", b"xref\n" + b"0" * 5000 + b" 7\n"),
            lambda p: p.replace(b"/Size 7", b"/Size " + b"7" * 5000),
            lambda p: p.replace(b"/Root 1 0 R", b"/Root " + b"1" * 5000 + b" 0 R"),
            lambda p: p.replace(b"/Root 1 0 R", b"/Root 1 " + b"0" * 6 + b" R"),
            lambda p: p.replace(b"/Info 5 0 R", b"/Info " + b"5" * 5000 + b" 0 R"),
        ],
        ids=[
            "startxref-5000",
            "startxref-11",
            "subsection",
            "size",
            "root-number",
            "root-generation",
            "info-number",
        ],
    )
    def test_oversized_field_is_driver_error(self, mutate: Any) -> None:
        payload = mutate(PDF_A)
        assert payload != PDF_A
        with pytest.raises(driver.DriverError):
            driver.normalized_bytes(payload, ".pdf")


def _png_rgb_ok() -> bytes:
    return _png_fixture([(b"IHDR", IHDR), (b"IDAT", IDAT_RED), (b"IEND", b"")])


INDEXED_IHDR = struct.pack(">IIBBBBB", 1, 1, 8, 3, 0, 0, 0)
GREY_IHDR = struct.pack(">IIBBBBB", 1, 1, 8, 0, 0, 0, 0)
RGBA_IHDR = struct.pack(">IIBBBBB", 1, 1, 8, 6, 0, 0, 0)
PALETTE = b"\x00\x00\x00\xff\xff\xff"
IDAT_INDEX = zlib.compress(b"\x00\x01")
IDAT_GREY = zlib.compress(b"\x00\x80")
IDAT_RGBA = zlib.compress(b"\x00\xff\x00\x00\xff")


class TestPngColourRules:
    def test_valid_indexed_png_accepted(self) -> None:
        payload = _png_fixture(
            [
                (b"IHDR", INDEXED_IHDR),
                (b"PLTE", PALETTE),
                (b"tRNS", b"\x00"),
                (b"IDAT", IDAT_INDEX),
                (b"IEND", b""),
            ]
        )
        driver.normalized_bytes(payload, ".png")
        driver.normalized_bytes(_png_rgb_ok(), ".png")

    @pytest.mark.parametrize(
        "chunks",
        [
            [
                (b"IHDR", INDEXED_IHDR),
                (b"IDAT", IDAT_INDEX),
                (b"PLTE", PALETTE),
                (b"IEND", b""),
            ],
            [(b"IHDR", INDEXED_IHDR), (b"IDAT", IDAT_INDEX), (b"IEND", b"")],
            [
                (b"IHDR", GREY_IHDR),
                (b"PLTE", PALETTE),
                (b"IDAT", IDAT_GREY),
                (b"IEND", b""),
            ],
            [
                (b"IHDR", INDEXED_IHDR),
                (b"PLTE", PALETTE),
                (b"IDAT", IDAT_INDEX),
                (b"tRNS", b"\x00"),
                (b"IEND", b""),
            ],
            [
                (b"IHDR", INDEXED_IHDR),
                (b"tRNS", b"\x00"),
                (b"PLTE", PALETTE),
                (b"IDAT", IDAT_INDEX),
                (b"IEND", b""),
            ],
            [
                (b"IHDR", RGBA_IHDR),
                (b"tRNS", b"\x00\x00\x00\x00\x00\x00"),
                (b"IDAT", IDAT_RGBA),
                (b"IEND", b""),
            ],
            [
                (b"IHDR", INDEXED_IHDR),
                (b"PLTE", PALETTE[:4]),
                (b"IDAT", IDAT_INDEX),
                (b"IEND", b""),
            ],
            [(b"IHDR", IHDR[:12]), (b"IDAT", IDAT_RED), (b"IEND", b"")],
            [
                (b"IHDR", struct.pack(">IIBBBBB", 1, 1, 16, 3, 0, 0, 0)),
                (b"PLTE", PALETTE),
                (b"IDAT", IDAT_INDEX),
                (b"IEND", b""),
            ],
            [
                (b"IHDR", struct.pack(">IIBBBBB", 0, 1, 8, 2, 0, 0, 0)),
                (b"IDAT", IDAT_RED),
                (b"IEND", b""),
            ],
            [
                (b"IHDR", struct.pack(">IIBBBBB", 1, 1, 8, 2, 1, 0, 0)),
                (b"IDAT", IDAT_RED),
                (b"IEND", b""),
            ],
        ],
        ids=[
            "plte-after-idat",
            "indexed-without-plte",
            "plte-in-greyscale",
            "trns-after-idat",
            "trns-before-plte",
            "trns-with-alpha",
            "plte-not-multiple-of-3",
            "short-ihdr",
            "invalid-depth",
            "zero-width",
            "bad-compression",
        ],
    )
    def test_colour_rule_violations_rejected(
        self, chunks: list[tuple[bytes, bytes]]
    ) -> None:
        with pytest.raises(driver.DriverError, match="malformed PNG"):
            driver.normalized_bytes(_png_fixture(chunks), ".png")


class TestApiCensusInvariants:
    def test_unresolved_row_has_the_resolved_row_schema(
        self, api_env: ModuleType
    ) -> None:
        rows = {row["name"]: row for row in driver.collect_api()["rows"]}
        assert set(rows["legacy_100"]) == set(rows["legacy_alpha"])
        assert rows["legacy_100"]["resolved"] is False
        assert rows["legacy_100"]["callable"] is None
        assert rows["legacy_100"]["defining_module"] is None
        assert rows["legacy_100"]["type"] is None

    def test_overlapping_additions_rejected(
        self, api_env: ModuleType, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        legacy_name = driver._legacy_names()[0]
        monkeypatch.setattr(
            driver, "PRIN_ADDITIONS", {legacy_name, "__version__", "core_version"}
        )
        with pytest.raises(driver.DriverError, match="172 \\+ 3"):
            driver.collect_api()


def _closure_run(mode: str) -> Path:
    run = _write_valid_run(mode)
    driver.check_run_complete(run)
    return run


class TestClosureProvenance:
    def test_draft_protocol_at_recorded_commit_rejected(
        self, workspace: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        run = _closure_run("api")
        draft = PROTOCOL_DRAFT.encode("utf-8")
        monkeypatch.setattr(driver, "_git_bytes", _fake_git(committed=draft))
        _rewrite_json(
            run,
            "api.json",
            lambda d: d["identity"].update(preregistration_sha256=_sha256(draft)),
        )
        with pytest.raises(driver.DriverError, match="not APPROVED"):
            driver.check_run_complete(run)

    def test_non_utf8_committed_protocol_rejected(
        self, workspace: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        run = _closure_run("api")
        undecodable = b"**Status:** APPROVED\xff\n"
        monkeypatch.setattr(driver, "_git_bytes", _fake_git(committed=undecodable))
        _rewrite_json(
            run,
            "api.json",
            lambda d: d["identity"].update(preregistration_sha256=_sha256(undecodable)),
        )
        with pytest.raises(driver.DriverError, match="UTF-8"):
            driver.check_run_complete(run)

    def test_non_ancestor_commit_rejected(
        self, workspace: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        run = _closure_run("api")
        monkeypatch.setattr(driver, "_git_bytes", _fake_git(merge_base="e" * 40))
        with pytest.raises(driver.DriverError, match="ancestor"):
            driver.check_run_complete(run)

    def test_unresolvable_commit_rejected(
        self, workspace: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        run = _closure_run("api")

        def missing(*args: str) -> bytes:
            raise subprocess.CalledProcessError(128, ["git", *args])

        monkeypatch.setattr(driver, "_git_bytes", missing)
        with pytest.raises(driver.DriverError, match="cannot be resolved"):
            driver.check_run_complete(run)


def _observation_mutations() -> list[tuple[str, str, Any]]:
    def obs(mutate: Any) -> Any:
        return lambda d: mutate(d["observations"])

    return [
        ("api-unit", "api", obs(lambda o: o.update(unit="x"))),
        ("api-short-expected", "api", obs(lambda o: o["expected_names"].pop())),
        ("api-row-missing", "api", obs(lambda o: o["rows"].pop())),
        (
            "api-row-schema",
            "api",
            obs(lambda o: o["rows"][0].pop("callable")),
        ),
        ("api-names-non-str", "api", obs(lambda o: o.update(observed_names=[1]))),
        ("cases-short", "conclusions", obs(lambda o: o["cases"].pop())),
        (
            "cases-duplicate-id",
            "conclusions",
            obs(lambda o: o["cases"][1].update(case_id=o["cases"][0]["case_id"])),
        ),
        (
            "cases-id-non-str",
            "conclusions",
            obs(lambda o: o["cases"][0].update(case_id=["x"])),
        ),
        (
            "cases-observed-non-bool",
            "conclusions",
            obs(lambda o: o["cases"][0].update(observed=1)),
        ),
        (
            "cases-missing-key",
            "conclusions",
            obs(lambda o: o["cases"][0].pop("operator")),
        ),
        (
            "reference-carries-prin",
            "reference",
            obs(lambda o: o.update(implementation="prin")),
        ),
        (
            "prin-carries-reference",
            "prin",
            obs(lambda o: o.update(implementation="reference")),
        ),
        (
            "expected-files-changed",
            "prin",
            obs(lambda o: o["expected_files"].pop()),
        ),
        ("renderer-missing", "repeatability", obs(lambda o: o.pop("renderer"))),
        (
            "duplicate-path",
            "prin",
            obs(lambda o: o["files"].append(dict(o["files"][0]))),
        ),
        (
            "negative-size",
            "prin",
            obs(lambda o: o["files"][0].update(raw_bytes=-1)),
        ),
        (
            "bad-digest",
            "reference",
            obs(lambda o: o["files"][0].update(normalized_sha256="z")),
        ),
    ]


class TestClosureObservations:
    @pytest.mark.parametrize(
        "mode,mutate",
        [(mode, mutate) for _, mode, mutate in _observation_mutations()],
        ids=[label for label, _, _ in _observation_mutations()],
    )
    def test_schema_violation_rejected(
        self, workspace: Path, mode: str, mutate: Any
    ) -> None:
        run = _closure_run(mode)
        _rewrite_json(run, RESULT_NAMES[mode], mutate)
        with pytest.raises(driver.DriverError, match=r"observations|expected"):
            driver.check_run_complete(run)

    def test_incomplete_render_stays_admissible(self, workspace: Path) -> None:
        run = _closure_run("prin")
        _rewrite_json(
            run,
            "reproduction.json",
            lambda d: d["observations"].update(
                files=[
                    {
                        "path": "figures/unexpected.png",
                        "raw_bytes": 1,
                        "raw_sha256": "1" * 64,
                        "normalized_bytes": 1,
                        "normalized_sha256": "1" * 64,
                        "sensitivity_bytes": 1,
                        "sensitivity_sha256": "1" * 64,
                    }
                ]
            ),
        )
        driver.check_run_complete(run)


class TestClosureDirectoryHygiene:
    @pytest.mark.parametrize(
        "name,payload",
        [("notes.txt", b"x"), ("stray.bin", b"\x00")],
        ids=["text", "binary"],
    )
    def test_stray_non_json_entry_rejected(
        self, workspace: Path, name: str, payload: bytes
    ) -> None:
        run = _closure_run("api")
        (run / name).write_bytes(payload)
        with pytest.raises(driver.DriverError, match="undeclared"):
            driver.check_run_complete(run)

    def test_subdirectory_rejected(self, workspace: Path) -> None:
        run = _closure_run("api")
        (run / "nested").mkdir()
        with pytest.raises(driver.DriverError, match="undeclared"):
            driver.check_run_complete(run)

    def test_impossible_utc_stamp_rejected(self, workspace: Path) -> None:
        run = _write_valid_run(name="RUN-20261345T120000Z-aaaaaaa-r1-api-cpu")
        with pytest.raises(driver.DriverError, match="real registered time"):
            driver.check_run_complete(run)


class TestStorageMeasurement:
    def test_unmeasurable_sibling_is_driver_error(
        self, workspace: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        run = _closure_run("api")
        sibling = _write_valid_run(
            "conclusions", name="RUN-20261020T130000Z-aaaaaaa-r1-conclusions-cpu"
        )
        original = reproduce.stat_size_and_hash_no_follow

        def measure(path: Path, role: str) -> tuple[int, str]:
            if sibling in path.parents:
                raise reproduce.ManifestMismatchError(f"{role} {path} is a symlink")
            return original(path, role)

        monkeypatch.setattr(driver, "stat_size_and_hash_no_follow", measure)
        with pytest.raises(driver.DriverError, match="cannot be measured"):
            driver.check_run_complete(run)


class TestReservationAtomicity:
    def test_reserve_refuses_reused_generated_root_before_mkdir(
        self, workspace: Path
    ) -> None:
        run = driver.RAW_ROOT / _run_name("api")
        (driver.OUTPUT_ROOT / run.name).mkdir()
        with pytest.raises(driver.DriverError, match="never reused"):
            driver._reserve("api", run, SHA)
        assert not run.exists()

    def test_sidecar_failure_is_recorded_as_aborted(
        self, admitted: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        def refuse(*args: Any, **kwargs: Any) -> None:
            raise OSError("sidecar write refused")

        monkeypatch.setattr(driver, "write_json_exclusive", refuse)
        run_dir = driver.RAW_ROOT / _run_name("api")
        with pytest.raises(driver.DriverError, match="aborted run retained"):
            driver.run_registered("api", run_dir, "devin", SHA)
        result = json.loads((run_dir / "api.json").read_text(encoding="utf-8"))
        assert result["status"] == "ABORTED"
        assert "sidecar write refused" in result["abort_reason"]
        assert (run_dir / "manifest.json").is_file()

    def test_generated_root_creation_failure_is_recorded_as_aborted(
        self, admitted: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        blocker = admitted / "blocked-output"
        blocker.write_text("not a directory", encoding="utf-8")
        monkeypatch.setattr(driver, "OUTPUT_ROOT", blocker)
        run_dir = driver.RAW_ROOT / _run_name("api")
        with pytest.raises(driver.DriverError, match="aborted run retained"):
            driver.run_registered("api", run_dir, "devin", SHA)
        result = json.loads((run_dir / "api.json").read_text(encoding="utf-8"))
        assert result["status"] == "ABORTED"
        assert (run_dir / "campaign-metadata.json").is_file()


class TestRenderEnvironment:
    def test_font_cache_state_recorded(self) -> None:
        state = driver._render_environment()["font_cache"]
        assert state["name"].startswith("fontlist-v")
        assert state["sha256"] is None or re.fullmatch(r"[0-9a-f]{64}", state["sha256"])

    def test_missing_cache_is_recorded_not_invented(
        self, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
    ) -> None:
        monkeypatch.setattr(matplotlib, "get_cachedir", lambda: str(tmp_path))
        assert driver._font_cache_state()["sha256"] is None


def test_generated_output_root_exp002_r1_is_gitignored() -> None:
    """Confirm ``DOCS/test_and_benchmark_results/EXP-002-r1/`` is gitignored."""
    import shutil

    git = shutil.which("git")
    if git is None:
        pytest.skip("git unavailable")
    repository = Path(driver.__file__).resolve().parents[2]
    probe = "DOCS/test_and_benchmark_results/EXP-002-r1/RUN-x/publication/a.pdf"
    result = subprocess.run(
        [git, "check-ignore", "-q", "--no-index", probe],
        cwd=repository,
        check=False,
    )
    assert result.returncode == 0


def _pdf_with_objects(
    objects: list[tuple[int, int, bytes]], trailer: bytes = b"/Info 5 0 R"
) -> bytes:
    """Classic-xref PDF with explicit (number, generation) objects."""
    payload = bytearray(b"%PDF-1.4\n%\xff\xfe\n")
    offsets: list[tuple[int, int, int]] = []
    for number, generation, value in objects:
        offsets.append((number, generation, len(payload)))
        payload += f"{number} {generation} obj\n".encode() + value + b"\nendobj\n"
    xref = len(payload)
    payload += b"xref\n"
    for number, generation, offset in offsets:
        payload += f"{number} 1\n{offset:010d} {generation:05d} n \n".encode()
    size = max(number for number, _, _ in objects) + 1
    payload += (
        b"trailer\n<< /Size "
        + str(size).encode()
        + b" /Root 1 0 R "
        + trailer
        + b" >>\nstartxref\n"
        + str(xref).encode()
        + b"\n%%EOF\n"
    )
    return bytes(payload)


class TestSelfAuditPdfAndPng:
    def test_same_number_other_generation_is_not_info(self) -> None:
        def build(creator: bytes) -> bytes:
            return _pdf_with_objects(
                [
                    (1, 0, b"<< /Type /Catalog >>"),
                    (5, 0, b"<< /Producer (x) >>"),
                    (5, 1, b"<< /Creator (" + creator + b") >>"),
                ]
            )

        assert driver.normalized_bytes(build(b"PRIN"), ".pdf") != (
            driver.normalized_bytes(build(b"reference"), ".pdf")
        )

    def test_flush_hex_value_before_close_is_accepted(self) -> None:
        flush = _pdf_with_objects(
            [(1, 0, b"<< /Type /Catalog >>"), (5, 0, b"<< /Creator (A) /X <AB>>>")]
        )
        spaced = _pdf_with_objects(
            [(1, 0, b"<< /Type /Catalog >>"), (5, 0, b"<< /X <AB> >>")]
        )
        assert driver.normalized_bytes(flush, ".pdf") == (
            driver.normalized_bytes(spaced, ".pdf")
        )

    @pytest.mark.parametrize(
        "trailer",
        [
            b"/Info 5 0 R /Note (see /Info 1 0 R)",
            b"/Info 5 0 R /Root 1 0 R",
        ],
        ids=["info-inside-string", "repeated-root"],
    )
    def test_repeated_structural_key_rejected(self, trailer: bytes) -> None:
        payload = _pdf_with_objects(
            [(1, 0, b"<< /Type /Catalog >>"), (5, 0, b"<< /Creator (A) >>")],
            trailer,
        )
        with pytest.raises(driver.DriverError, match="classic-xref"):
            driver.normalized_bytes(payload, ".pdf")

    @pytest.mark.parametrize(
        "chunks",
        [
            [
                (b"IHDR", struct.pack(">IIBBBBB", 1, 1, 1, 3, 0, 0, 0)),
                (b"PLTE", b"\x00" * 9),
                (b"IDAT", zlib.compress(b"\x00\x00")),
                (b"IEND", b""),
            ],
            [
                (b"IHDR", INDEXED_IHDR),
                (b"PLTE", PALETTE),
                (b"tRNS", b"\x00\x00\x00"),
                (b"IDAT", IDAT_INDEX),
                (b"IEND", b""),
            ],
            [
                (b"IHDR", GREY_IHDR),
                (b"tRNS", b"\x00"),
                (b"IDAT", IDAT_GREY),
                (b"IEND", b""),
            ],
            [
                (b"IHDR", IHDR),
                (b"tRNS", b"\x00\x00"),
                (b"IDAT", IDAT_RED),
                (b"IEND", b""),
            ],
        ],
        ids=[
            "palette-exceeds-depth",
            "trns-exceeds-palette",
            "grey-trns-length",
            "rgb-trns-length",
        ],
    )
    def test_length_violations_rejected(
        self, chunks: list[tuple[bytes, bytes]]
    ) -> None:
        with pytest.raises(driver.DriverError, match="malformed PNG"):
            driver.normalized_bytes(_png_fixture(chunks), ".png")


class TestSensitivityPolicy:
    """§11.1 / §11.3: the non-gating writer-property diagnostic is recorded."""

    def test_tables_keep_raw_line_terminators(self) -> None:
        crlf = TEX_A.replace(b"\n", b"\r\n")
        assert driver.normalized_bytes(crlf, ".tex") == (
            driver.normalized_bytes(TEX_A, ".tex")
        )
        assert driver.sensitivity_bytes(crlf, ".tex") == crlf
        assert driver.sensitivity_bytes(crlf, ".tex") != (
            driver.sensitivity_bytes(TEX_A, ".tex")
        )

    def test_pdf_values_masked_but_key_set_kept(self) -> None:
        assert driver.normalized_bytes(PDF_PRIN_INFO, ".pdf") == (
            driver.normalized_bytes(PDF_REFERENCE_INFO, ".pdf")
        )
        assert driver.sensitivity_bytes(PDF_PRIN_INFO, ".pdf") != (
            driver.sensitivity_bytes(PDF_REFERENCE_INFO, ".pdf")
        )
        assert driver.sensitivity_bytes(PDF_A, ".pdf") == (
            driver.sensitivity_bytes(PDF_B, ".pdf")
        )
        assert b"ToolOne" not in driver.sensitivity_bytes(PDF_A, ".pdf")

    def test_pdf_content_still_significant(self) -> None:
        assert driver.sensitivity_bytes(PDF_A, ".pdf") != (
            driver.sensitivity_bytes(PDF_C, ".pdf")
        )

    def test_png_policy_unchanged(self) -> None:
        assert driver.sensitivity_bytes(PNG_A, ".png") == (
            driver.normalized_bytes(PNG_A, ".png")
        )

    def test_unregistered_suffix_rejected(self) -> None:
        with pytest.raises(driver.DriverError, match="unregistered"):
            driver.sensitivity_bytes(b"x", ".svg")

    def test_missing_sensitivity_digest_rejected_at_closure(
        self, workspace: Path
    ) -> None:
        run = _closure_run("prin")
        _rewrite_json(
            run,
            "reproduction.json",
            lambda d: d["observations"]["files"][0].pop("sensitivity_sha256"),
        )
        with pytest.raises(driver.DriverError, match="observations"):
            driver.check_run_complete(run)
