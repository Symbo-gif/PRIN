#!/usr/bin/env python
"""Registered E4 analysis for EXP-002 - API, benchmark-result and reproduction parity.

This is the committed analysis code that campaign plan section 7.4 item 2 and
pre-registration section 8 require. It applies the **frozen** decision rules
(pre-registration sections 4.1, 5.2, 5.4, 5.5 and 11.3) to the five immutable
E3 run records and writes the seven registered outputs plus the committed
``report-manifest.json``.

What it does, in order:

1. **Global provenance (fail closed).** Verifies with read-only ``git`` that
   the execution source ``R`` descends from the protocol commit ``F`` and that
   ``HEAD`` descends from ``R``; that the protocol blob at ``F`` (and at ``R``,
   and in the working tree) has the pinned SHA-256 and the dated
   ``APPROVED`` header; that ``paper/artefact_manifest.json`` has its pinned
   digest; that the ``*.json`` inventory of the frozen reference result
   directory is exactly the 172 manifested inputs, with their manifested
   sizes and digests (the inventory rule of ``tools.reproduce.verify_manifest``,
   which the driver used); that the pinned reference ``__all__`` is the
   172-name literal list; and that PRIN's frozen RC1 contract
   (``_public_api.py`` and ``_deprecation.py`` at ``R``) has its
   pre-registration section 1.1 digests. The raw
   record root may hold only its ``README.md`` and the five indexed runs. Any
   failure raises :class:`AnalysisError` and no output is written.
2. **Per-record admissibility, before any observation is read.** Only the
   explicit five-entry index :data:`REGISTERED` is read - never a ``RUN-*``
   glob. For each run the directory inventory, the pinned manifest digest,
   the manifested (and pinned) sidecar and result bytes, strict JSON, the
   sidecar, the result envelope, the configuration, the environment and the
   identity block (source, protocol and the 172 input records) are verified.
   Only then is the ``observations`` member opened. A failure makes that one
   record inadmissible (:class:`RecordError`); it is reported, never fatal,
   and never counted as a pass.
3. **Re-derivation from retained data.** H1's expected population, legacy
   flags and ownership rows are re-derived from the pinned reference source
   and the Migration Guide / WP-001 baseline at ``R``; the frozen-contract
   missing/extra sets are re-derived from the observed export list and the
   RC1 tuple at ``R``; each row's resolution class is re-derived from its
   retained type and callable fields. H2's 62
   claim-comparator records are re-derived from the manifest-verified frozen
   inputs (operands, paths, units, operators, expected values) and must agree
   with the record exactly. Publication file records are checked for internal
   consistency. A disagreement makes the record inadmissible; it is not a
   verdict. No driver-provided status is trusted as a verdict.
4. **Adjudication (section 4.1).** For each hypothesis the valid-counterexample
   rule is applied first, then the complete-coverage rule; otherwise the
   verdict is ``INCONCLUSIVE``. H3 is decided under the approved policy
   (primary) and the section 11.3 sensitivity policy, side by side. Any
   primary ``REFUTED`` sets the section 4.3 / campaign plan section 10.4 D1
   flag.

This module never imports ``prin``, ``prinet``, the E3 driver or
``tools.reproduce`` (which imports ``prin``), never renders, never resolves an
export and never reads the retained publication roots: E5 verifies those bytes
(pre-registration section 11.3 item 2). It reads no wall clock and draws no
randomness. JSON is written with sorted keys and ``allow_nan=False``, CSV and
Markdown with LF line endings and fixed row orders, so a second run over the
same records reproduces every output byte for byte (campaign plan section 7.4
step 5).

Usage (from the repository root)::

    python "<record root>/analysis/exp002_e4_analysis.py"

where ``<record root>`` is
``DOCS/experiments/EXP-002-api-benchmark-result-and-reproduction-parity``.
"""

from __future__ import annotations

import argparse
import ast
import csv
import hashlib
import io
import json
import math
import os
import re
import shutil
import stat

# Only read-only git queries with a fixed argv use subprocess (see _git).
import subprocess  # nosec B404
import sys
import tempfile
from collections.abc import Iterable, Mapping, Sequence
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path, PurePosixPath
from typing import Any

# ---------------------------------------------------------------------------
# Registered identities (pre-registration, e2-review.md, E3 log)
# ---------------------------------------------------------------------------

EXPERIMENT_ID = "EXP-002"
SESSION = "0162"
STAGE = "E4"
#: Fixed analysis date; outputs never carry a wall-clock time.
ANALYSIS_DATE_UTC = "2026-10-13"

RECORD_ROOT = "DOCS/experiments/EXP-002-api-benchmark-result-and-reproduction-parity"
MODULE_RELATIVE_PATH = f"{RECORD_ROOT}/analysis/exp002_e4_analysis.py"
PROTOCOL_PATH = f"{RECORD_ROOT}/preregistration.md"
REPORT_MANIFEST_PATH = f"{RECORD_ROOT}/report-manifest.json"
RAW_ROOT = "benchmarks/results/EXP-002"
GENERATED_ROOT = "DOCS/test_and_benchmark_results/EXP-002"
OUTPUT_DIR = f"{GENERATED_ROOT}/analysis"
INPUT_MANIFEST_PATH = "paper/artefact_manifest.json"
REFERENCE_ROOT = "DOCS/archive and reference from PRINet 3.0/PRINet-3.0.0-main"
REFERENCE_RESULTS = f"{REFERENCE_ROOT}/benchmarks/results"
REFERENCE_API_PATH = f"{REFERENCE_ROOT}/src/prinet/__init__.py"
PUBLIC_API_PATH = "python/prin/_public_api.py"
DEPRECATION_PATH = "python/prin/_deprecation.py"
MIGRATION_GUIDE_PATH = "DOCS/sphinx/migration_guide.rst"
OWNERSHIP_BASELINE_PATH = "DOCS/baselines/wp001_api_traceability.md"

OPERATOR = "MichaelMaillet"
E3_SESSION = "0161"
PRIN_VERSION = "1.0.0rc1"

API_SYMBOL_COUNT = 175
LEGACY_NAME_COUNT = 172
CLAIM_COMPARATOR_RECORD_COUNT = 62
GENERATED_FILE_COUNT = 39
INPUT_RECORD_COUNT = 172
ANALYSIS_OUTPUT_COUNT = 7

PRIN_ADDITIONS = ("BackendUnavailableError", "__version__", "core_version")
#: Type names whose instances the driver classes as scalar constants.
SCALAR_TYPE_NAMES = frozenset({"int", "float", "str", "bool", "bytes"})

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
REGISTERED_TABLES = tuple(sorted(f"tables/{stem}.tex" for stem in TABLE_STEMS))
REGISTERED_FILES = tuple(
    sorted(
        [f"figures/{stem}.{fmt}" for stem in FIGURE_STEMS for fmt in ("pdf", "png")]
        + list(REGISTERED_TABLES)
    )
)
REGISTERED_FORMATS = ("pdf", "png", "tex")

CONCLUSION_FILES = (
    "phase1_chimera_seeds.json",
    "benchmark_y4q1_3_k_alpha_sensitivity.json",
    "phase2_chimera_nsweep.json",
    "y4q1_8_topology_comparison.json",
    "y3q49_goldilocks_zones.json",
)
FAMILY_COUNTS = {"C01": 5, "C02": 42, "C03": 4, "C04": 5, "C05": 6}
BC_THRESHOLD = 0.555
C03_THRESHOLD = 0.5

MODES = {
    "api": ("api-cpu", "api.json", ("H1",)),
    "conclusions": ("conclusions-cpu", "conclusions.json", ("H2",)),
    "reference": ("reproduction-reference-cpu", "reproduction.json", ("H3",)),
    "prin": ("reproduction-prin-cpu", "reproduction.json", ("H3", "H4")),
    "repeatability": ("seedrep0-prin-cpu", "reproduction.json", ("H4",)),
}
MODE_ORDER = ("api", "conclusions", "reference", "prin", "repeatability")
SIDECAR = "campaign-metadata.json"
MANIFEST = "manifest.json"

CONFIRMED = "CONFIRMED"
REFUTED = "REFUTED"
INCONCLUSIVE = "INCONCLUSIVE"
APPROVED_POLICY = "approved"
SENSITIVITY_POLICY = "sensitivity"

_RUN_PATTERN = re.compile(
    r"RUN-(?P<utc>\d{8}T\d{6}Z)-(?P<sha>[0-9a-f]{7})-(?P<label>[a-z0-9-]+)\Z"
)
_HEX40 = re.compile(r"[0-9a-f]{40}\Z")
_HEX64 = re.compile(r"[0-9a-f]{64}\Z")

_SIDECAR_KEYS = frozenset(
    {"exp_id", "session", "run_id", "operator", "mode", "artefacts"}
)
_ENVELOPE_KEYS = frozenset(
    {
        "environment",
        "config",
        "identity",
        "seed_used",
        "observations",
        "status",
        "elapsed_seconds",
        "started_at_utc",
        "recorded_at_utc",
    }
)
_ENVIRONMENT_KEYS = frozenset(
    {
        "prin_version",
        "git_commit",
        "rust_version",
        "python_version",
        "platform",
        "processor",
        "logical_cpus",
        "gpu",
        "gpu_vram_mb",
        "backend",
        "dtype",
        "seed",
    }
)
_CONFIG_KEYS = frozenset(
    {
        "iterations",
        "warmup",
        "seed_counter",
        "seed_key",
        "out_dir",
        "measurement_kind",
        "replicates",
    }
)
_IDENTITY_KEYS = frozenset(
    {
        "source_sha",
        "preregistration_sha256",
        "preregistration_commit",
        "approval_date_utc",
        "input_manifest_sha256",
        "input_record_count",
        "input_records",
    }
)
_MANIFEST_KEYS = frozenset({"schema_version", "description", "source", "files"})
_MANIFEST_ENTRY_KEYS = frozenset({"path", "bytes", "sha256"})
_API_OBSERVATION_KEYS = frozenset(
    {
        "expected_names",
        "legacy_names",
        "observed_names",
        "frozen_missing",
        "frozen_extra",
        "rows",
        "unit",
    }
)
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
_C02_EXTRA_KEYS = frozenset({"K", "alpha_radians"})
_PUBLICATION_KEYS = frozenset(
    {"implementation", "renderer", "expected_files", "files", "unit"}
)
_RENDERER_KEYS = frozenset(
    {
        "font_cache",
        "matplotlib",
        "numpy",
        "pillow",
        "freetype",
        "backend",
        "font_sha256",
    }
)
_FILE_KEYS = frozenset(
    {
        "path",
        "raw_bytes",
        "raw_sha256",
        "normalized_bytes",
        "normalized_sha256",
        "sensitivity_bytes",
        "sensitivity_sha256",
    }
)
_ARCHIVED_KEYS = frozenset(
    {
        "archived_bytes",
        "archived_sha256",
        "archived_normalized_bytes",
        "archived_normalized_sha256",
    }
)
#: Members removed by the section 5.5 repeatability projection.
_PROJECTION_DROPPED = (
    "environment",
    "started_at_utc",
    "recorded_at_utc",
    "elapsed_seconds",
)

_NOT_APPLICABLE = "not applicable (deterministic census; pre-registration section 7)"

OUTPUT_FILENAMES = (
    "summary.json",
    "api-mapping.csv",
    "conclusion-comparisons.csv",
    "reproduction-comparisons.csv",
    "error-distributions.json",
    "expected-vs-observed.md",
    "coverage-and-deferrals.md",
)

#: Pre-registration section 5.3 owner matrix (no owner is discharged here).
OWNER_MATRIX = (
    (
        "CPU throughput, coupling complexity, sweep speedups and CPU scaling",
        "EXP-003, including DV036-F5 at 0166 and the DV-036 CPU gate before 0168",
    ),
    (
        "GPU throughput (including OscilloSim's 1.95B claim), Triton/CUDA "
        "comparisons, training-step and bridge overhead",
        "EXP-004; GPU/bridge DV-036 gate before 0173; DV-001/DV-003 limitations "
        "retained",
    ),
    (
        "Fresh chimera boundaries, topology/size effects and capacity "
        "relation/replication",
        "EXP-005; corrected-SI exception retained",
    ),
    (
        "CUDA-tagged `y3q49_finite_size_scaling.json` fit ranking and "
        "`y3q49_phase_coherence.json` lifetime ranking",
        "EXP-004 backend qualification and EXP-005 scientific replication; "
        "their CUDA-derived directions are not substituted with CPU "
        "measurements here",
    ),
    (
        "CLEVR-N/IP accuracy, PT-versus-SA statistical equivalence, ablations, "
        "freezing, parameter/FLOP efficiency, trained supercritical regimes, "
        "gradient/representation geometry and training curves",
        "EXP-006, with EXP-004 performance dependencies; historical "
        "intervals/p-values remain reference-only",
    ),
    (
        "Daemon p95, MOT/IP evaluation, noise/velocity/occlusion and "
        "adversarial robustness",
        "EXP-007, with EXP-006 training dependencies; CPU/DirectML/NPU "
        "dispositions retained",
    ),
    (
        "Linux/macOS/Metal, compiler-free wheel matrix and NPU/new capabilities",
        "EXP-008; amendment #48 suspension and campaign section 5.4 "
        "unavailable-hardware rule",
    ),
)


@dataclass(frozen=True)
class RunSpec:
    """One entry of the explicit E3 run index.

    Attributes:
        mode: Registered driver mode.
        run_id: The ``RUN-...`` directory name.
        result_sha256: Pinned digest of the result file (E3 log).
        manifest_sha256: Pinned digest of ``manifest.json`` (E3 log).
        sidecar_sha256: Pinned digest of ``campaign-metadata.json`` (E3 log).
    """

    mode: str
    run_id: str
    result_sha256: str
    manifest_sha256: str
    sidecar_sha256: str

    @property
    def label(self) -> str:
        """Registered run label for this mode."""
        return MODES[self.mode][0]

    @property
    def result_name(self) -> str:
        """Registered result filename for this mode."""
        return MODES[self.mode][1]

    @property
    def hypotheses(self) -> tuple[str, ...]:
        """Hypotheses the sidecar maps the result file to."""
        return MODES[self.mode][2]


@dataclass(frozen=True)
class Registration:
    """Every identity the analysis is pinned to.

    Attributes:
        source_sha: Execution source ``R`` of all five runs.
        protocol_commit: Last protocol commit ``F`` at the first ``RUN-``.
        protocol_sha256: SHA-256 of the frozen protocol blob.
        approval_date_utc: Dated maintainer approval in the protocol header.
        input_manifest_sha256: Pinned digest of ``paper/artefact_manifest.json``.
        reference_api_sha256: Pinned digest of the reference ``__init__.py``.
        public_api_sha256: Section 1.1 digest of ``_public_api.py`` (at ``R``).
        deprecation_sha256: Section 1.1 digest of ``_deprecation.py`` (at ``R``).
        runs: The explicit run index, in registered order.
    """

    source_sha: str
    protocol_commit: str
    protocol_sha256: str
    approval_date_utc: str
    input_manifest_sha256: str
    reference_api_sha256: str
    public_api_sha256: str
    deprecation_sha256: str
    runs: tuple[RunSpec, ...]


REGISTERED = Registration(
    source_sha="fae24c4393c7a0232e6c8f0a6388b1775aa5fc05",
    protocol_commit="9a9889d08dcaf2ad0ce31659ed67721b54b114d0",
    protocol_sha256="0f3073dd2ed73b64071bcf3ae182510a69a26bd575b81b5a97cc5a1f9bbc8c8b",
    approval_date_utc="2026-10-12",
    input_manifest_sha256=(
        "300cdc094d2b7d27ac8b1e2556b2e6ed4dad3333f0038b45c8f87ea81612cce5"
    ),
    reference_api_sha256=(
        "ede92afc6771f2e29206534905e2820598ba841662a93d59f669f803a382f182"
    ),
    public_api_sha256=(
        "dd5745ababa809483b8d52198a096a1e9fa0de7e13e246245b13f47066853a6d"
    ),
    deprecation_sha256=(
        "132e86e991669d0abe65d89b624227250bfd61e54c2f97cb814366a0012f4e9a"
    ),
    runs=(
        RunSpec(
            mode="api",
            run_id="RUN-20261012T212705Z-fae24c4-api-cpu",
            result_sha256=(
                "b76aedab424582dec72ede165c6a136e62c802b395519cba56975fa75f0fade9"
            ),
            manifest_sha256=(
                "d4eee92905addee67c210192a7a97a35b4e52e5f623f1fe34b04fcae9f8eaa90"
            ),
            sidecar_sha256=(
                "d51f9c7b4ae1f9b32e20cf211a55bfc416470eae1e332c823df645ead8b5e355"
            ),
        ),
        RunSpec(
            mode="conclusions",
            run_id="RUN-20261012T213054Z-fae24c4-conclusions-cpu",
            result_sha256=(
                "2d1cdc5fa76b247da1b8544606708b6fa0ffe9afaaf274604bc4c1115e9bed84"
            ),
            manifest_sha256=(
                "d5247c24728c26d21bc4677036091ac4665888a526b9825df231ff5ef2439bd9"
            ),
            sidecar_sha256=(
                "1f59f1e078fce9154703feb93499da62f8d3c183406de9e3ebfded3cc2a04756"
            ),
        ),
        RunSpec(
            mode="reference",
            run_id="RUN-20261012T213821Z-fae24c4-reproduction-reference-cpu",
            result_sha256=(
                "70f9677c7523c2decf3dc0b9e3e1ba8763ee56838ff63deca93587b42c89e7e3"
            ),
            manifest_sha256=(
                "f5410f4f0d5d3f6835575b377e211d6e704b0759f0457df4751a6ad0abee9d6d"
            ),
            sidecar_sha256=(
                "722fc141089fc0ece7fb043cb67b0bba574beca85fc3b45c5fceacb8b60b25c2"
            ),
        ),
        RunSpec(
            mode="prin",
            run_id="RUN-20261012T213936Z-fae24c4-reproduction-prin-cpu",
            result_sha256=(
                "776a926df8edb333e38d61e9fc4ba2966385df56bcfc3d9eda6540c7c47b590e"
            ),
            manifest_sha256=(
                "0213ac284abf55b04a6cd5641abecb4b25d00be1b8e488e562c9b6cb399e18c8"
            ),
            sidecar_sha256=(
                "6316a9e03f53cc966d70f8c83d1d70f7962857edc09f7dc8b4c6d4fe507d0e7e"
            ),
        ),
        RunSpec(
            mode="repeatability",
            run_id="RUN-20261012T214040Z-fae24c4-seedrep0-prin-cpu",
            result_sha256=(
                "ec615eb48008bcc112ad73a10fc6ea42ddf5619ecb33b87e880a1e7977084127"
            ),
            manifest_sha256=(
                "5722cb93ac87c4bf448ee76b53721c0d030bc0b0d3a465db7ab6db403db78388"
            ),
            sidecar_sha256=(
                "77cf576fb454cd32b9247e1392112d1a67c0a927ab4707c45393e091554a25ec"
            ),
        ),
    ),
)

REPOSITORY_ROOT = Path(__file__).resolve().parents[4]


# ---------------------------------------------------------------------------
# Errors and small validators
# ---------------------------------------------------------------------------


class AnalysisError(RuntimeError):
    """A global precondition failed; the analysis writes nothing."""


class RecordError(ValueError):
    """One run record is inadmissible; its hypotheses lose that coverage."""


def _sha256(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def _require(condition: bool, message: str, error: type[Exception]) -> None:
    if not condition:
        raise error(message)


def _is_int(value: object) -> bool:
    return type(value) is int


def _is_hex64(value: object) -> bool:
    return isinstance(value, str) and _HEX64.fullmatch(value) is not None


def _mapping(value: object, context: str, error: type[Exception]) -> dict[str, Any]:
    if not isinstance(value, dict) or any(not isinstance(key, str) for key in value):
        raise error(f"{context}: expected a JSON object")
    return value


def _exact_keys(
    value: Mapping[str, Any],
    keys: Iterable[str],
    context: str,
    error: type[Exception],
) -> None:
    expected = set(keys)
    if set(value) != expected:
        missing = sorted(expected - set(value))
        extra = sorted(set(value) - expected)
        raise error(f"{context}: key set differs (missing {missing}, extra {extra})")


def _string_list(value: object, context: str, error: type[Exception]) -> list[str]:
    if not isinstance(value, list) or not all(isinstance(item, str) for item in value):
        raise error(f"{context}: expected a list of strings")
    return list(value)


def _finite_number(value: object, context: str, error: type[Exception]) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise error(f"{context}: expected a finite number, not {type(value).__name__}")
    number = float(value)
    if not math.isfinite(number):
        raise error(f"{context}: non-finite number")
    return number


def _real_time(value: str, layout: str) -> bool:
    try:
        datetime.strptime(value, layout)  # calendar validity only, no time zone
    except ValueError:
        return False
    return True


def _check_registration(registration: Registration) -> None:
    """Refuse a malformed registration before any git argv is built from it."""
    for name in ("source_sha", "protocol_commit"):
        value = getattr(registration, name)
        _require(
            _HEX40.fullmatch(value) is not None,
            f"registration {name} is not a 40-character SHA",
            AnalysisError,
        )
    for name in (
        "protocol_sha256",
        "input_manifest_sha256",
        "reference_api_sha256",
        "public_api_sha256",
        "deprecation_sha256",
    ):
        _require(
            _is_hex64(getattr(registration, name)),
            f"registration {name} is not a SHA-256 digest",
            AnalysisError,
        )
    modes = tuple(spec.mode for spec in registration.runs)
    _require(
        modes == MODE_ORDER,
        "run index must hold exactly the five registered modes in order",
        AnalysisError,
    )
    for spec in registration.runs:
        match = _RUN_PATTERN.fullmatch(spec.run_id)
        _require(
            match is not None
            and match.group("label") == spec.label
            and match.group("sha") == registration.source_sha[:7]
            and _real_time(match.group("utc"), "%Y%m%dT%H%M%SZ"),
            f"run index entry is not a registered run name: {spec.run_id}",
            AnalysisError,
        )
        for digest in (spec.result_sha256, spec.manifest_sha256, spec.sidecar_sha256):
            _require(
                _is_hex64(digest),
                f"run index digest malformed: {spec.run_id}",
                AnalysisError,
            )


# ---------------------------------------------------------------------------
# No-follow file access and strict JSON
# ---------------------------------------------------------------------------


def _is_link(path: Path) -> bool:
    """Return whether ``path`` is a symbolic link or any reparse point."""
    try:
        status = os.lstat(path)
    except FileNotFoundError:
        return False
    if stat.S_ISLNK(status.st_mode):
        return True
    attributes = getattr(status, "st_file_attributes", 0)
    return bool(attributes & getattr(stat, "FILE_ATTRIBUTE_REPARSE_POINT", 0x400))


def _check_no_links(path: Path, error: type[Exception]) -> None:
    """Refuse ``path`` if it or any ancestor is a link or junction."""
    absolute = Path(os.path.abspath(path))
    for candidate in (absolute, *absolute.parents):
        if _is_link(candidate):
            raise error(f"path or ancestor is a link or junction: {candidate}")


def _read_regular(path: Path, error: type[Exception]) -> bytes:
    """Read a regular, unlinked file through one descriptor tied to its lstat."""
    _check_no_links(path, error)
    try:
        before = os.lstat(path)
    except OSError as exc:
        raise error(f"cannot stat {path}: {exc}") from exc
    if not stat.S_ISREG(before.st_mode):
        raise error(f"not a regular file: {path}")
    flags = os.O_RDONLY | getattr(os, "O_BINARY", 0) | getattr(os, "O_NOFOLLOW", 0)
    try:
        descriptor = os.open(path, flags)
    except OSError as exc:
        raise error(f"cannot open {path}: {exc}") from exc
    with os.fdopen(descriptor, "rb") as stream:
        after = os.fstat(stream.fileno())
        if not stat.S_ISREG(after.st_mode) or (after.st_dev, after.st_ino) != (
            before.st_dev,
            before.st_ino,
        ):
            raise error(f"file changed identity while being opened: {path}")
        try:
            return stream.read()
        except OSError as exc:
            raise error(f"cannot read {path}: {exc}") from exc


def _read_verified(path: Path, size: int, digest: str, error: type[Exception]) -> bytes:
    payload = _read_regular(path, error)
    if len(payload) != size:
        raise error(f"size mismatch against its manifest record: {path}")
    if _sha256(payload) != digest:
        raise error(f"SHA-256 mismatch against its manifest record: {path}")
    return payload


def _strict_json(payload: bytes, context: str, error: type[Exception]) -> Any:
    """Parse JSON refusing a byte-order mark, duplicate keys and non-finite numbers."""
    if payload.startswith(b"\xef\xbb\xbf"):
        raise error(f"{context}: byte-order mark")
    try:
        text = payload.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise error(f"{context}: not UTF-8") from exc

    def pairs(items: list[tuple[str, Any]]) -> dict[str, Any]:
        result: dict[str, Any] = {}
        for key, value in items:
            if key in result:
                raise error(f"{context}: duplicate JSON key {key!r}")
            result[key] = value
        return result

    def constant(name: str) -> Any:
        raise error(f"{context}: non-finite JSON constant {name}")

    try:
        return json.loads(text, object_pairs_hook=pairs, parse_constant=constant)
    except json.JSONDecodeError as exc:
        raise error(f"{context}: invalid JSON ({exc.msg})") from exc


@dataclass(frozen=True)
class ManifestEntry:
    """One ``path``/``bytes``/``sha256`` manifest record."""

    path: str
    bytes: int
    sha256: str

    def as_dict(self) -> dict[str, Any]:
        """Return the record as the manifest's JSON object."""
        return {"path": self.path, "bytes": self.bytes, "sha256": self.sha256}


def _parse_manifest(
    payload: bytes, context: str, error: type[Exception]
) -> tuple[ManifestEntry, ...]:
    document = _mapping(_strict_json(payload, context, error), context, error)
    _exact_keys(document, _MANIFEST_KEYS, context, error)
    _require(
        _is_int(document["schema_version"]) and document["schema_version"] == 1,
        f"{context}: schema_version must be the integer 1",
        error,
    )
    files = document["files"]
    _require(isinstance(files, list), f"{context}: files must be a list", error)
    entries = []
    for index, item in enumerate(files):
        record = _mapping(item, f"{context} files[{index}]", error)
        _exact_keys(record, _MANIFEST_ENTRY_KEYS, f"{context} files[{index}]", error)
        name, size, digest = record["path"], record["bytes"], record["sha256"]
        _require(
            isinstance(name, str)
            and name.endswith(".json")
            and PurePosixPath(name).name == name
            and "\\" not in name,
            f"{context} files[{index}]: path must be a plain JSON filename",
            error,
        )
        _require(
            _is_int(size) and size >= 0 and _is_hex64(digest),
            f"{context} files[{index}]: bytes/sha256 malformed",
            error,
        )
        entries.append(ManifestEntry(name, size, digest))
    names = [entry.path for entry in entries]
    _require(len(set(names)) == len(names), f"{context}: duplicate path", error)
    return tuple(sorted(entries, key=lambda entry: entry.path))


# ---------------------------------------------------------------------------
# Read-only git
# ---------------------------------------------------------------------------


def _git_environment() -> dict[str, str]:
    """Return the environment without ``GIT_*`` overrides (``GIT_DIR`` etc.)."""
    return {
        key: value for key, value in os.environ.items() if not key.startswith("GIT_")
    }


def _git(repository_root: Path, *args: str) -> tuple[int, bytes]:
    """Run one read-only git query; argv is fixed text plus validated SHAs."""
    executable = shutil.which("git")
    if executable is None:
        raise AnalysisError("git is unavailable; provenance cannot be verified")
    try:
        # Absolute git path, list argv, no shell; every argument is a constant
        # or a validated 40-character hex SHA.
        completed = subprocess.run(  # noqa: S603  # nosec B603
            [executable, *args],
            cwd=repository_root,
            env=_git_environment(),
            capture_output=True,
            check=False,
            timeout=120,
            stdin=subprocess.DEVNULL,
        )
    except (OSError, subprocess.SubprocessError) as exc:
        raise AnalysisError(f"git query failed: {exc}") from exc
    return completed.returncode, completed.stdout


def _git_blob(repository_root: Path, commit: str, path: str) -> bytes:
    code, payload = _git(repository_root, "cat-file", "blob", f"{commit}:{path}")
    _require(code == 0, f"cannot read {path} at {commit}", AnalysisError)
    return payload


def _approval_date(protocol: bytes) -> str:
    """Return the dated approval of an ``APPROVED`` protocol header."""
    text = protocol.decode("utf-8")
    status = re.search(r"^\*\*Status:\*\*[ \t]*([^\r\n]+)", text, re.M)
    _require(
        status is not None and status.group(1).strip() == "APPROVED",
        "protocol header status is not APPROVED",
        AnalysisError,
    )
    approval = re.search(
        r"^\*\*Maintainer approval:\*\*[ \t]*MichaelMaillet, (\d{4}-\d{2}-\d{2}) UTC\b",
        text,
        re.M,
    )
    if approval is None or not _real_time(approval.group(1), "%Y-%m-%d"):
        raise AnalysisError("protocol has no dated approval")
    return approval.group(1)


# ---------------------------------------------------------------------------
# Global context
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class Context:
    """Verified global inputs shared by every record check.

    Attributes:
        repository_root: Checkout holding the records and frozen inputs.
        registration: The pinned identities.
        input_records: The 172 manifest records, sorted by path.
        documents: Parsed frozen inputs for the five H2 conclusion files.
        legacy_names: Reference ``__all__`` in source order.
        guide_names: Names in the Migration Guide consolidated table at ``R``.
        owned_names: ``prinet`` rows of the WP-001 baseline at ``R``.
        frozen_contract: PRIN's frozen RC1 export contract at ``R``.
        module_sha256: SHA-256 of this module's own bytes.
        module_commit: Last commit touching this module, if it is tracked.
        module_matches_commit: Whether the running bytes equal that commit.
    """

    repository_root: Path
    registration: Registration
    input_records: tuple[ManifestEntry, ...]
    documents: dict[str, Any]
    legacy_names: tuple[str, ...]
    guide_names: frozenset[str]
    owned_names: frozenset[str]
    frozen_contract: frozenset[str]
    module_sha256: str
    module_commit: str | None
    module_matches_commit: bool


def _literal(payload: bytes, name: str, context: str) -> Any:
    """Return the literal value assigned to ``name`` at module level."""
    try:
        tree = ast.parse(payload)
    except (SyntaxError, ValueError) as exc:
        raise AnalysisError(f"{context}: source does not parse") from exc
    for node in tree.body:
        targets: list[ast.expr]
        value: ast.expr | None
        if isinstance(node, ast.Assign):
            targets, value = list(node.targets), node.value
        elif isinstance(node, ast.AnnAssign):
            targets, value = [node.target], node.value
        else:
            continue
        if value is not None and any(
            isinstance(target, ast.Name) and target.id == name for target in targets
        ):
            try:
                return ast.literal_eval(value)
            except (SyntaxError, ValueError, TypeError) as exc:
                raise AnalysisError(f"{context}: {name} is not a literal") from exc
    raise AnalysisError(f"{context}: literal {name} missing")


def _frozen_contract(payload: bytes) -> frozenset[str]:
    """Re-derive ``FROZEN_PUBLIC_API = frozenset(RC1_PUBLIC_API)`` at ``R``."""
    names = _literal(payload, "RC1_PUBLIC_API", "PRIN public API")
    _require(
        isinstance(names, tuple) and all(isinstance(name, str) for name in names),
        "RC1_PUBLIC_API is not a tuple of names",
        AnalysisError,
    )
    return frozenset(names)


def _reference_names(payload: bytes) -> tuple[str, ...]:
    names = _literal(payload, "__all__", "reference API")
    _require(
        isinstance(names, list)
        and all(isinstance(name, str) for name in names)
        and len(names) == LEGACY_NAME_COUNT
        and len(set(names)) == LEGACY_NAME_COUNT,
        "reference __all__ is not the frozen 172-name list",
        AnalysisError,
    )
    return tuple(names)


def _ownership_sources(
    guide: bytes, baseline: bytes
) -> tuple[frozenset[str], frozenset[str]]:
    """Re-derive the Migration Guide and WP-001 ownership name sets."""
    try:
        guide_text, baseline_text = guide.decode("utf-8"), baseline.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise AnalysisError("ownership sources are not UTF-8") from exc
    table = re.search(
        r"\.\. wp036-consolidated-table-begin(.*?)\.\. wp036-consolidated-table-end",
        guide_text,
        re.S,
    )
    guide_names = frozenset(
        re.findall(
            r'^\s*"([^"]+)", "prin\.[^"]+",', table.group(1) if table else "", re.M
        )
    )
    owned = frozenset(
        re.findall(r"^\|\s*prinet\s*\|\s*([^| ]+)\s*\|", baseline_text, re.M)
    )
    return guide_names, owned


def _module_identity(repository_root: Path) -> tuple[str, str | None, bool]:
    own = _read_regular(Path(__file__), AnalysisError)
    code, out = _git(
        repository_root, "log", "-1", "--format=%H", "--", MODULE_RELATIVE_PATH
    )
    commit = out.decode("ascii", "replace").strip() if code == 0 else ""
    if _HEX40.fullmatch(commit) is None:
        return _sha256(own), None, False
    code, blob = _git(
        repository_root, "cat-file", "blob", f"{commit}:{MODULE_RELATIVE_PATH}"
    )
    return _sha256(own), commit, code == 0 and blob == own


def verify_context(repository_root: Path, registration: Registration) -> Context:
    """Verify every global precondition, failing closed.

    Args:
        repository_root: The checkout to analyse.
        registration: The pinned identities and run index.

    Returns:
        The verified context.

    Raises:
        AnalysisError: If provenance, the frozen inputs, the reference API or
            the raw-root inventory cannot be verified.
    """
    _check_registration(registration)
    root = repository_root
    source, freeze = registration.source_sha, registration.protocol_commit
    code, head = _git(root, "rev-parse", "HEAD")
    _require(code == 0, "cannot resolve HEAD", AnalysisError)
    head_sha = head.decode("ascii", "replace").strip()
    _require(_HEX40.fullmatch(head_sha) is not None, "HEAD is not a SHA", AnalysisError)
    code, _ = _git(root, "merge-base", "--is-ancestor", source, head_sha)
    _require(
        code == 0, "HEAD does not descend from the execution source R", AnalysisError
    )
    code, _ = _git(root, "merge-base", "--is-ancestor", freeze, source)
    _require(code == 0, "protocol commit F is not an ancestor of R", AnalysisError)
    protocol = _git_blob(root, freeze, PROTOCOL_PATH)
    _require(
        _sha256(protocol) == registration.protocol_sha256,
        "protocol blob at F does not have the pinned digest",
        AnalysisError,
    )
    _require(
        _approval_date(protocol) == registration.approval_date_utc,
        "protocol approval date is not the registered one",
        AnalysisError,
    )
    _require(
        _git_blob(root, source, PROTOCOL_PATH) == protocol,
        "protocol at R differs from the frozen blob",
        AnalysisError,
    )
    _require(
        _read_regular(root / PROTOCOL_PATH, AnalysisError) == protocol,
        "working protocol differs from the frozen blob",
        AnalysisError,
    )

    manifest_bytes = _read_regular(root / INPUT_MANIFEST_PATH, AnalysisError)
    _require(
        _sha256(manifest_bytes) == registration.input_manifest_sha256,
        "input manifest does not have the pinned digest",
        AnalysisError,
    )
    records = _parse_manifest(manifest_bytes, "input manifest", AnalysisError)
    _require(
        len(records) == INPUT_RECORD_COUNT,
        "input manifest is not the registered 172-record inventory",
        AnalysisError,
    )
    results_dir = root / REFERENCE_RESULTS
    _check_no_links(results_dir, AnalysisError)
    try:
        present = sorted(path.name for path in results_dir.glob("*.json"))
    except OSError as exc:
        raise AnalysisError(f"cannot list the frozen input directory: {exc}") from exc
    _require(
        present == [record.path for record in records],
        "frozen input directory is not exactly the manifested 172 JSON files",
        AnalysisError,
    )
    documents: dict[str, Any] = {}
    for record in records:
        payload = _read_verified(
            results_dir / record.path, record.bytes, record.sha256, AnalysisError
        )
        if record.path in CONCLUSION_FILES:
            # Plain json.loads: the same double-precision decoding the driver used.
            documents[record.path] = json.loads(payload)
    _require(
        set(documents) == set(CONCLUSION_FILES),
        "a registered H2 input is not in the input manifest",
        AnalysisError,
    )

    reference_api = _read_regular(root / REFERENCE_API_PATH, AnalysisError)
    _require(
        _sha256(reference_api) == registration.reference_api_sha256,
        "reference API source does not have the pinned digest",
        AnalysisError,
    )
    legacy = _reference_names(reference_api)
    _require(
        not set(legacy) & set(PRIN_ADDITIONS),
        "PRIN additions overlap the reference names",
        AnalysisError,
    )
    guide_names, owned = _ownership_sources(
        _git_blob(root, source, MIGRATION_GUIDE_PATH),
        _git_blob(root, source, OWNERSHIP_BASELINE_PATH),
    )
    public_api = _git_blob(root, source, PUBLIC_API_PATH)
    _require(
        _sha256(public_api) == registration.public_api_sha256
        and _sha256(_git_blob(root, source, DEPRECATION_PATH))
        == registration.deprecation_sha256,
        "PRIN frozen-contract sources at R do not have their section 1.1 digests",
        AnalysisError,
    )
    frozen_contract = _frozen_contract(public_api)

    raw_root = root / RAW_ROOT
    _check_no_links(raw_root, AnalysisError)
    _require(raw_root.is_dir(), "raw record root is missing", AnalysisError)
    allowed = {"README.md", *(spec.run_id for spec in registration.runs)}
    try:
        unexpected = sorted(
            entry.name for entry in raw_root.iterdir() if entry.name not in allowed
        )
    except OSError as exc:
        raise AnalysisError(f"cannot list the raw record root: {exc}") from exc
    _require(
        not unexpected,
        f"raw record root holds unindexed entries: {unexpected}",
        AnalysisError,
    )
    module_sha, module_commit, module_matches = _module_identity(root)
    return Context(
        repository_root=root,
        registration=registration,
        input_records=records,
        documents=documents,
        legacy_names=legacy,
        guide_names=guide_names,
        owned_names=owned,
        frozen_contract=frozen_contract,
        module_sha256=module_sha,
        module_commit=module_commit,
        module_matches_commit=module_matches,
    )


# ---------------------------------------------------------------------------
# Re-derivation: H1 census, H2 claim cases, publication records
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class ApiRow:
    """One expected-name row with its re-derived resolution class."""

    name: str
    legacy: bool
    ownership_present: bool
    resolved: bool
    callable: bool | None
    defining_module: str | None
    type_name: str | None
    error: str | None
    classification: str


@dataclass(frozen=True)
class ApiCensus:
    """A verified ``api`` observation."""

    rows: tuple[ApiRow, ...]
    observed_names: tuple[str, ...]
    frozen_missing: tuple[str, ...]
    frozen_extra: tuple[str, ...]


def _classify_row(row: Mapping[str, Any]) -> str:
    """Re-derive one row's resolution class from its retained fields."""
    name = row["name"]
    resolved, callable_flag = row["resolved"], row["callable"]
    module, type_name, error = row["defining_module"], row["type"], row["error"]
    _require(type(resolved) is bool, f"{name}: resolved is not a Boolean", RecordError)
    _require(
        error is None or isinstance(error, str),
        f"{name}: error must be a string or null",
        RecordError,
    )
    if error is not None:
        _require(
            resolved is False
            and callable_flag is None
            and module is None
            and type_name is None,
            f"{name}: an unresolved row carries resolution fields",
            RecordError,
        )
        return "unresolved"
    _require(
        type(callable_flag) is bool
        and isinstance(type_name, str)
        and bool(type_name)
        and (module is None or isinstance(module, str)),
        f"{name}: a resolved row lacks callable/type fields",
        RecordError,
    )
    if type_name == "NoneType":
        _require(not resolved, f"{name}: a None export is marked resolved", RecordError)
        return "none"
    if callable_flag:
        _require(
            resolved, f"{name}: a callable export is marked unresolved", RecordError
        )
        return "callable"
    if type_name in SCALAR_TYPE_NAMES:
        _require(resolved, f"{name}: a scalar export is marked unresolved", RecordError)
        return "constant"
    # Neither callable nor a built-in scalar type: unsupported if the record
    # says so; if it claims support, the retained type name cannot prove it.
    return "unverifiable" if resolved else "unsupported"


def check_api(observations: Mapping[str, Any], context: Context) -> ApiCensus:
    """Verify an ``api`` observation against the re-derived population.

    Args:
        observations: The record's ``observations`` member.
        context: The verified global context.

    Returns:
        The verified census.

    Raises:
        RecordError: If the schema, population, legacy flags or ownership
            disagree with the re-derivation, or a row is self-inconsistent.
    """
    _exact_keys(observations, _API_OBSERVATION_KEYS, "api observations", RecordError)
    _require(observations["unit"] == "api_symbol", "api unit", RecordError)
    legacy = set(context.legacy_names)
    expected = sorted(legacy | set(PRIN_ADDITIONS))
    _require(
        _string_list(observations["expected_names"], "expected_names", RecordError)
        == expected,
        "expected_names differ from the re-derived 175-name population",
        RecordError,
    )
    _require(
        _string_list(observations["legacy_names"], "legacy_names", RecordError)
        == sorted(legacy),
        "legacy_names differ from the pinned reference __all__",
        RecordError,
    )
    observed = _string_list(
        observations["observed_names"], "observed_names", RecordError
    )
    missing = _string_list(
        observations["frozen_missing"], "frozen_missing", RecordError
    )
    extra = _string_list(observations["frozen_extra"], "frozen_extra", RecordError)
    # verify_api_surface(prin.__all__) = (FROZEN - observed, observed - FROZEN),
    # FROZEN = frozenset(RC1_PUBLIC_API); the driver stored both sorted.
    _require(
        missing == sorted(context.frozen_contract - set(observed))
        and extra == sorted(set(observed) - context.frozen_contract),
        "frozen-contract missing/extra sets disagree with the RC1 tuple at R",
        RecordError,
    )
    raw_rows = observations["rows"]
    _require(isinstance(raw_rows, list), "api rows must be a list", RecordError)
    rows = [_mapping(item, "api row", RecordError) for item in raw_rows]
    for row in rows:
        _exact_keys(row, _API_ROW_KEYS, "api row", RecordError)
    _require(
        [row["name"] for row in rows] == expected,
        "api rows are not one row per expected name in sorted order",
        RecordError,
    )
    census = []
    for row in rows:
        name = row["name"]
        is_legacy = name in legacy
        owned = (not is_legacy) or (
            name in context.owned_names and name in context.guide_names
        )
        _require(
            row["legacy"] is is_legacy, f"{name}: legacy flag disagrees", RecordError
        )
        _require(
            row["ownership_present"] is owned,
            f"{name}: ownership flag disagrees with the Migration Guide/WP-001 rows",
            RecordError,
        )
        census.append(
            ApiRow(
                name=name,
                legacy=is_legacy,
                ownership_present=owned,
                resolved=row["resolved"],
                callable=row["callable"],
                defining_module=row["defining_module"],
                type_name=row["type"],
                error=row["error"],
                classification=_classify_row(row),
            )
        )
    return ApiCensus(tuple(census), tuple(observed), tuple(missing), tuple(extra))


def _pointer(document: Any, path: str) -> Any:
    value = document
    for part in path.strip("/").split("/"):
        value = value[int(part)] if isinstance(value, list) else value[part]
    return value


def derive_claim_cases(documents: Mapping[str, Any]) -> list[dict[str, Any]]:
    """Re-derive the 62 registered claim-comparator records (section 5.2).

    Args:
        documents: Parsed frozen inputs keyed by registered filename.

    Returns:
        The records, in registered family order, with the driver's schema.

    Raises:
        AnalysisError: If a frozen input does not have the registered schema
            or population.
    """
    try:
        return _derive_claim_cases(documents)
    except (KeyError, TypeError, IndexError, ValueError) as exc:
        raise AnalysisError(f"frozen H2 input schema invalid: {exc!r}") from exc


def _derive_claim_cases(documents: Mapping[str, Any]) -> list[dict[str, Any]]:
    cases: list[dict[str, Any]] = []

    def add(
        family: str,
        label: str,
        filename: str,
        left_path: str,
        operator: str,
        right: float | str,
        unit: str,
        expected: bool = True,
    ) -> dict[str, Any]:
        left = _finite_number(
            _pointer(documents[filename], left_path), left_path, AnalysisError
        )
        if isinstance(right, str):
            right_path: str | None = right
            right_value = _finite_number(
                _pointer(documents[filename], right), right, AnalysisError
            )
        else:
            right_path, right_value = None, right
        case = {
            "case_id": f"{family}:{label}",
            "family": family,
            "input_file": filename,
            "left_path": left_path,
            "right_path": right_path,
            "left": left,
            "operator": operator,
            "right": right_value,
            "operand_unit": unit,
            "expected": expected,
            "observed": left > right_value if operator == ">" else left < right_value,
        }
        cases.append(case)
        return case

    c01, c02, c03, c04, c05 = CONCLUSION_FILES
    bc = documents[c01]["bimodality_coefficient"]
    _require(
        len(bc["raw_values"]) == 5 and bc["n_sequences"] == 5,
        "C01 requires exactly five historical sequences",
        AnalysisError,
    )
    for index in range(5):
        path = f"/bimodality_coefficient/raw_values/{index}"
        add("C01", str(index), c01, path, ">", BC_THRESHOLD, "BC")

    grid = documents[c02]["grid"]
    _require(len(grid) == 42, "C02 requires all 42 grid rows", AnalysisError)
    labels: set[tuple[float, float]] = set()
    for index, row in enumerate(grid):
        label = (
            _finite_number(row["K"], "C02 K", AnalysisError),
            _finite_number(row["alpha"], "C02 alpha", AnalysisError),
        )
        _require(label not in labels, "C02 duplicate (K,alpha) label", AnalysisError)
        labels.add(label)
        stored = row["chimera_detected"]
        _require(
            isinstance(stored, bool),
            "C02 stored classification must be a Boolean",
            AnalysisError,
        )
        case = add(
            "C02",
            str(index),
            c02,
            f"/grid/{index}/bc_mean",
            ">",
            BC_THRESHOLD,
            "BC",
            stored,
        )
        case["K"], case["alpha_radians"] = label

    sweep = documents[c03]["sweep"]
    sizes = []
    for index, row in enumerate(sweep):
        size = row["n_oscillators"]
        _require(
            _is_int(size) and size not in sizes,
            "C03 invalid or duplicate oscillator count",
            AnalysisError,
        )
        sizes.append(size)
        add(
            "C03",
            str(size),
            c03,
            f"/sweep/{index}/bc_stats/mean",
            ">",
            C03_THRESHOLD,
            "BC",
        )
    _require(
        sorted(sizes) == [128, 256, 512, 1024],
        "C03 requires exactly N=128/256/512/1024",
        AnalysisError,
    )

    topologies = documents[c04]["topologies"]
    _require(
        set(topologies) == {"ring", "2community", "4community"},
        "C04 requires the three registered topologies",
        AnalysisError,
    )
    for name in ("2community", "4community"):
        add(
            "C04",
            f"mean-ring-{name}",
            c04,
            "/topologies/ring/bc_mean",
            ">",
            f"/topologies/{name}/bc_mean",
            "BC",
        )
        add(
            "C04",
            f"width-ring-{name}",
            c04,
            "/topologies/ring/bc_ci/ci_width",
            ">",
            f"/topologies/{name}/bc_ci/ci_width",
            "historical_BC_CI_width",
        )
    add(
        "C04",
        "width-2community-4community",
        c04,
        "/topologies/2community/bc_ci/ci_width",
        ">",
        "/topologies/4community/bc_ci/ci_width",
        "historical_BC_CI_width",
    )

    zones = documents[c05]["zones"]
    for name in ("csr", "full", "mean_field", "sparse_knn"):
        record = zones[f"{name}_cpu"]
        _require(
            record["device"] == "cpu" and record["regime"] == name,
            "C05 selected records are not the registered CPU regimes",
            AnalysisError,
        )
    for name in ("full", "mean_field", "sparse_knn"):
        add(
            "C05",
            f"width-csr-{name}",
            c05,
            "/zones/csr_cpu/zone_width",
            ">",
            f"/zones/{name}_cpu/zone_width",
            "stored_coupling_K",
        )
    for name in ("csr", "mean_field", "sparse_knn"):
        add(
            "C05",
            f"onset-full-{name}",
            c05,
            "/zones/full_cpu/K_c",
            "<",
            f"/zones/{name}_cpu/K_c",
            "stored_coupling_K",
        )
    _require(
        len(cases) == CLAIM_COMPARATOR_RECORD_COUNT
        and len({case["case_id"] for case in cases}) == CLAIM_COMPARATOR_RECORD_COUNT,
        "re-derived claim population is not 62 unique records",
        AnalysisError,
    )
    return cases


@dataclass(frozen=True)
class ClaimCase:
    """One verified claim-comparator record."""

    case_id: str
    family: str
    input_file: str
    left_path: str
    right_path: str | None
    left: float
    operator: str
    right: float
    operand_unit: str
    expected: bool
    observed: bool
    k: float | None
    alpha_radians: float | None

    @property
    def agrees(self) -> bool:
        """Whether the observed predicate equals its registered expectation."""
        return self.observed is self.expected


def _same_value(recorded: object, derived: object) -> bool:
    if isinstance(derived, bool) or derived is None or isinstance(derived, str):
        return type(recorded) is type(derived) and recorded == derived
    if isinstance(recorded, bool) or not isinstance(recorded, (int, float)):
        return False
    return math.isfinite(float(recorded)) and float(recorded) == derived


def check_conclusions(
    observations: Mapping[str, Any], context: Context
) -> tuple[ClaimCase, ...]:
    """Verify a ``conclusions`` observation against the re-derived records.

    Args:
        observations: The record's ``observations`` member.
        context: The verified global context (frozen inputs).

    Returns:
        The 62 verified records, in registered order.

    Raises:
        RecordError: If any field of any record disagrees with the
            re-derivation from the manifest-verified frozen inputs.
    """
    _exact_keys(
        observations, {"cases", "unit"}, "conclusions observations", RecordError
    )
    _require(
        observations["unit"] == "claim_comparator_record",
        "conclusions unit",
        RecordError,
    )
    raw_cases = observations["cases"]
    _require(isinstance(raw_cases, list), "claim cases must be a list", RecordError)
    recorded = [_mapping(item, "claim case", RecordError) for item in raw_cases]
    by_id: dict[str, dict[str, Any]] = {}
    for case in recorded:
        case_id = case.get("case_id")
        if not isinstance(case_id, str) or case_id in by_id:
            raise RecordError("claim case_id missing or duplicated")
        by_id[case_id] = case
    derived = derive_claim_cases(context.documents)
    _require(
        set(by_id) == {case["case_id"] for case in derived},
        "claim case identities differ from the registered 62-record population",
        RecordError,
    )
    verified = []
    for expected in derived:
        case = by_id[expected["case_id"]]
        keys = _CASE_KEYS | (_C02_EXTRA_KEYS if expected["family"] == "C02" else set())
        _exact_keys(case, keys, f"claim case {expected['case_id']}", RecordError)
        for key, value in expected.items():
            _require(
                _same_value(case[key], value),
                f"claim case {expected['case_id']}: {key} disagrees with the "
                "frozen input",
                RecordError,
            )
        verified.append(
            ClaimCase(
                case_id=expected["case_id"],
                family=expected["family"],
                input_file=expected["input_file"],
                left_path=expected["left_path"],
                right_path=expected["right_path"],
                left=expected["left"],
                operator=expected["operator"],
                right=expected["right"],
                operand_unit=expected["operand_unit"],
                expected=expected["expected"],
                observed=expected["observed"],
                k=expected.get("K"),
                alpha_radians=expected.get("alpha_radians"),
            )
        )
    return tuple(verified)


@dataclass(frozen=True)
class FileRecord:
    """One generated-file record of a publication arm."""

    path: str
    raw: tuple[int, str]
    normalized: tuple[int, str]
    sensitivity: tuple[int, str]
    archived_raw: tuple[int, str] | None
    archived_normalized: tuple[int, str] | None

    def policy(self, policy: str) -> tuple[int, str]:
        """Size and digest compared under ``policy``."""
        return self.normalized if policy == APPROVED_POLICY else self.sensitivity

    def archived(self, policy: str) -> tuple[int, str] | None:
        """Archived-table size and digest under ``policy`` (raw for sensitivity)."""
        return (
            self.archived_normalized if policy == APPROVED_POLICY else self.archived_raw
        )


@dataclass(frozen=True)
class PublicationArm:
    """A verified publication-arm observation."""

    run_id: str
    implementation: str
    renderer: dict[str, Any]
    files: dict[str, FileRecord]


def _valid_output_path(path: object) -> bool:
    if not isinstance(path, str) or not path or "\\" in path:
        return False
    parts = PurePosixPath(path).parts
    return (
        not PurePosixPath(path).is_absolute() and ".." not in parts and "." not in parts
    )


def _pair(
    record: Mapping[str, Any], size_key: str, digest_key: str, context: str
) -> tuple[int, str]:
    size, digest = record[size_key], record[digest_key]
    _require(
        _is_int(size) and size >= 0 and _is_hex64(digest),
        f"{context}: {size_key}/{digest_key} malformed",
        RecordError,
    )
    return size, digest


def check_publication(observations: Mapping[str, Any], spec: RunSpec) -> PublicationArm:
    """Verify a publication-arm observation's schema and internal consistency.

    The file list is a population that may hold missing or extra outputs
    (H3's registered falsifier), so it is never required to be the 39 files.

    Args:
        observations: The record's ``observations`` member.
        spec: The run index entry.

    Returns:
        The verified arm.

    Raises:
        RecordError: If the schema, the renderer capture or a file record's
            internal consistency is invalid.
    """
    _exact_keys(
        observations, _PUBLICATION_KEYS, "publication observations", RecordError
    )
    implementation = "reference" if spec.mode == "reference" else "prin"
    _require(
        observations["unit"] == "generated_file"
        and observations["implementation"] == implementation
        and observations["expected_files"] == list(REGISTERED_FILES),
        "publication unit/implementation/expected_files are not the registered ones",
        RecordError,
    )
    renderer = _mapping(observations["renderer"], "renderer", RecordError)
    _exact_keys(renderer, _RENDERER_KEYS, "renderer", RecordError)
    cache = _mapping(renderer["font_cache"], "font cache", RecordError)
    _exact_keys(cache, {"name", "sha256"}, "font cache", RecordError)
    _require(
        _is_hex64(cache["sha256"]),
        "font-cache digest missing (required by section 5.4)",
        RecordError,
    )
    fonts = _mapping(renderer["font_sha256"], "font digests", RecordError)
    _require(
        bool(fonts) and all(_is_hex64(value) for value in fonts.values()),
        "font digests malformed",
        RecordError,
    )
    raw_files = observations["files"]
    _require(
        isinstance(raw_files, list), "publication files must be a list", RecordError
    )
    files: dict[str, FileRecord] = {}
    for item in raw_files:
        record = _mapping(item, "publication file", RecordError)
        path = record.get("path")
        if not isinstance(path, str) or not _valid_output_path(path):
            raise RecordError(f"invalid output path {path!r}")
        _require(path not in files, f"duplicate output path {path}", RecordError)
        is_table = path in REGISTERED_TABLES
        _exact_keys(
            record,
            _FILE_KEYS | (_ARCHIVED_KEYS if is_table else set()),
            path,
            RecordError,
        )
        suffix = PurePosixPath(path).suffix
        _require(
            suffix in {".pdf", ".png", ".tex"},
            f"{path}: unregistered format (the driver cannot complete with it)",
            RecordError,
        )
        raw = _pair(record, "raw_bytes", "raw_sha256", path)
        normalized = _pair(record, "normalized_bytes", "normalized_sha256", path)
        sensitivity = _pair(record, "sensitivity_bytes", "sensitivity_sha256", path)
        if suffix == ".tex":
            _require(
                sensitivity == raw, f"{path}: table sensitivity is not raw", RecordError
            )
        if suffix == ".png":
            _require(
                sensitivity == normalized,
                f"{path}: PNG sensitivity is not its normalization",
                RecordError,
            )
        archived_raw = archived_normalized = None
        if is_table:
            archived_raw = _pair(record, "archived_bytes", "archived_sha256", path)
            archived_normalized = _pair(
                record, "archived_normalized_bytes", "archived_normalized_sha256", path
            )
        files[path] = FileRecord(
            path, raw, normalized, sensitivity, archived_raw, archived_normalized
        )
    return PublicationArm(
        run_id=spec.run_id,
        implementation=implementation,
        renderer=renderer,
        files=dict(sorted(files.items())),
    )


# ---------------------------------------------------------------------------
# Record loading (admissibility before any observation is read)
# ---------------------------------------------------------------------------


@dataclass
class LoadedRecord:
    """One indexed run and what could be verified about it."""

    spec: RunSpec
    admissible: bool = False
    reason: str | None = None
    status: str | None = None
    manifest: ManifestEntry | None = None
    files: tuple[ManifestEntry, ...] = ()
    result: dict[str, Any] | None = None
    census: ApiCensus | None = None
    cases: tuple[ClaimCase, ...] | None = None
    arm: PublicationArm | None = None


def _check_envelope(result: Mapping[str, Any], context: Context, run_dir: Path) -> None:
    registration = context.registration
    status = result.get("status")
    _require(
        status == "COMPLETED",
        f"result status is {status!r}, not COMPLETED "
        "(aborted records are never counted)",
        RecordError,
    )
    _exact_keys(result, _ENVELOPE_KEYS, "result envelope", RecordError)
    _require(result["seed_used"] is False, "seed_used must be false", RecordError)
    elapsed = result["elapsed_seconds"]
    _require(
        isinstance(elapsed, (int, float))
        and not isinstance(elapsed, bool)
        and math.isfinite(elapsed)
        and elapsed >= 0,
        "elapsed_seconds must be finite and non-negative",
        RecordError,
    )
    _require(
        isinstance(result["started_at_utc"], str)
        and isinstance(result["recorded_at_utc"], str),
        "timestamps must be strings",
        RecordError,
    )
    environment = _mapping(result["environment"], "environment", RecordError)
    _exact_keys(environment, _ENVIRONMENT_KEYS, "environment", RecordError)
    _require(
        environment["git_commit"] == registration.source_sha
        and environment["backend"] == "cpu"
        and environment["dtype"] == "f64"
        and _is_int(environment["seed"])
        and environment["seed"] == 0
        and environment["prin_version"] == PRIN_VERSION
        and _is_int(environment["logical_cpus"])
        and environment["logical_cpus"] >= 1
        and all(
            isinstance(environment[key], str) and environment[key].strip()
            for key in ("rust_version", "python_version", "platform", "processor")
        ),
        "environment is not the registered CPU/f64 capture at R",
        RecordError,
    )
    config = _mapping(result["config"], "config", RecordError)
    _exact_keys(config, _CONFIG_KEYS, "config", RecordError)
    out_dir = config["out_dir"]
    tail = (
        PurePosixPath(out_dir.replace("\\", "/")).parts
        if isinstance(out_dir, str)
        else ()
    )
    _require(
        all(
            _is_int(config[key])
            for key in (
                "iterations",
                "warmup",
                "seed_counter",
                "seed_key",
                "replicates",
            )
        )
        and (config["iterations"], config["warmup"], config["replicates"]) == (10, 0, 1)
        and (config["seed_counter"], config["seed_key"]) == (0, 2)
        and config["measurement_kind"] == "deterministic_census"
        and ".." not in tail
        and tail[-4:] == (*PurePosixPath(RAW_ROOT).parts, run_dir.name),
        "config is not the registered deterministic-census configuration",
        RecordError,
    )
    identity = _mapping(result["identity"], "identity", RecordError)
    _exact_keys(identity, _IDENTITY_KEYS, "identity", RecordError)
    _require(
        identity["source_sha"] == registration.source_sha
        and identity["preregistration_commit"] == registration.protocol_commit
        and identity["preregistration_sha256"] == registration.protocol_sha256
        and identity["approval_date_utc"] == registration.approval_date_utc,
        "identity does not carry the registered source/protocol/approval",
        RecordError,
    )
    _require(
        identity["input_manifest_sha256"] == registration.input_manifest_sha256
        and _is_int(identity["input_record_count"])
        and identity["input_record_count"] == INPUT_RECORD_COUNT
        and identity["input_records"]
        == [record.as_dict() for record in context.input_records],
        "identity input records are not the verified 172-record manifest",
        RecordError,
    )


def _load_verified_files(
    spec: RunSpec, run_dir: Path, loaded: LoadedRecord
) -> tuple[dict[str, Any], dict[str, Any]]:
    _check_no_links(run_dir, RecordError)
    _require(run_dir.is_dir(), f"run directory missing: {spec.run_id}", RecordError)
    try:
        entries = sorted(entry.name for entry in run_dir.iterdir())
    except OSError as exc:
        raise RecordError(f"cannot list run directory: {exc}") from exc
    _require(
        entries == sorted({SIDECAR, spec.result_name, MANIFEST}),
        f"run directory inventory is not exactly sidecar/result/manifest: {entries}",
        RecordError,
    )
    manifest_bytes = _read_regular(run_dir / MANIFEST, RecordError)
    loaded.manifest = ManifestEntry(
        MANIFEST, len(manifest_bytes), _sha256(manifest_bytes)
    )
    _require(
        loaded.manifest.sha256 == spec.manifest_sha256,
        "manifest.json differs from its pinned E3 digest",
        RecordError,
    )
    entries_by_name = {
        entry.path: entry
        for entry in _parse_manifest(manifest_bytes, "run manifest", RecordError)
    }
    _require(
        set(entries_by_name) == {SIDECAR, spec.result_name},
        "run manifest does not list exactly the sidecar and the result",
        RecordError,
    )
    loaded.files = tuple(entries_by_name[name] for name in sorted(entries_by_name))
    pins = {SIDECAR: spec.sidecar_sha256, spec.result_name: spec.result_sha256}
    parsed: dict[str, dict[str, Any]] = {}
    for name, entry in entries_by_name.items():
        _require(
            entry.sha256 == pins[name],
            f"{name}: manifest digest differs from its pinned E3 digest",
            RecordError,
        )
        payload = _read_verified(run_dir / name, entry.bytes, entry.sha256, RecordError)
        parsed[name] = _mapping(
            _strict_json(payload, name, RecordError), name, RecordError
        )
    return parsed[SIDECAR], parsed[spec.result_name]


def load_record(context: Context, spec: RunSpec) -> LoadedRecord:
    """Verify one indexed run and only then read its observations.

    Args:
        context: The verified global context.
        spec: The run index entry.

    Returns:
        The record, admissible or with the reason it is not.
    """
    loaded = LoadedRecord(spec=spec)
    run_dir = context.repository_root / RAW_ROOT / spec.run_id
    try:
        sidecar, result = _load_verified_files(spec, run_dir, loaded)
        _exact_keys(sidecar, _SIDECAR_KEYS, "campaign sidecar", RecordError)
        _require(
            sidecar["exp_id"] == EXPERIMENT_ID
            and sidecar["session"] == E3_SESSION
            and sidecar["run_id"] == spec.run_id
            and sidecar["operator"] == OPERATOR
            and sidecar["mode"] == spec.mode
            and sidecar["artefacts"] == {spec.result_name: list(spec.hypotheses)},
            "campaign sidecar is not the registered run's",
            RecordError,
        )
        loaded.status = (
            result.get("status") if isinstance(result.get("status"), str) else None
        )
        _check_envelope(result, context, run_dir)
        loaded.result = result
        # Provenance and input-byte identity are verified: only now is the
        # observation payload read.
        observations = _mapping(result["observations"], "observations", RecordError)
        if spec.mode == "api":
            loaded.census = check_api(observations, context)
        elif spec.mode == "conclusions":
            loaded.cases = check_conclusions(observations, context)
        else:
            loaded.arm = check_publication(observations, spec)
        loaded.admissible = True
    except RecordError as exc:
        loaded.admissible = False
        loaded.reason = str(exc)
        loaded.census = loaded.cases = loaded.arm = None
    return loaded


def reproduction_projection(result: Mapping[str, Any]) -> bytes:
    """Return the section 5.5 repeatability projection as canonical JSON bytes.

    Removes the per-run ``environment``, ``config.out_dir``, the timestamps
    and the elapsed duration (the run ID and the generated-output root live
    only in the sidecar and in ``out_dir``); keeps implementation, seed pair,
    identity, filenames and every raw/normalized/sensitivity size and digest.

    Args:
        result: A verified ``reproduction.json`` document.

    Returns:
        Canonical bytes of the projection.
    """
    projection = {
        key: value for key, value in result.items() if key not in _PROJECTION_DROPPED
    }
    projection["config"] = {
        key: value for key, value in result["config"].items() if key != "out_dir"
    }
    return _canonical_json(projection)


# ---------------------------------------------------------------------------
# Adjudication (section 4.1)
# ---------------------------------------------------------------------------


def _verdict(counterexamples: int, complete: bool) -> str:
    """Apply the valid-counterexample rule first, then complete coverage."""
    if counterexamples:
        return REFUTED
    return CONFIRMED if complete else INCONCLUSIVE


def adjudicate_h1(record: LoadedRecord) -> dict[str, Any]:
    """Decide H1 from the verified ``api`` census.

    Args:
        record: The loaded ``api`` record.

    Returns:
        The verdict and its exact counts.
    """
    base: dict[str, Any] = {
        "hypothesis": "H1",
        "run_id": record.spec.run_id,
        "denominator_api_symbols": API_SYMBOL_COUNT,
        "denominator_legacy_api_names": LEGACY_NAME_COUNT,
    }
    census = record.census
    if census is None:
        return {
            **base,
            "verdict": INCONCLUSIVE,
            "reason": f"no admissible census: {record.reason}",
        }
    classes = {
        name: 0
        for name in (
            "callable",
            "constant",
            "none",
            "unsupported",
            "unresolved",
            "unverifiable",
        )
    }
    for row in census.rows:
        classes[row.classification] += 1
    expected = {row.name for row in census.rows}
    observed = list(census.observed_names)
    counts: dict[str, int] = {}
    for name in observed:
        counts[name] = counts.get(name, 0) + 1
    duplicates = sorted(name for name, count in counts.items() if count > 1)
    unexpected = sorted(set(observed) - expected)
    removed = sorted(expected - set(observed))
    failing_rows = sorted(
        row.name
        for row in census.rows
        if row.classification in {"none", "unsupported", "unresolved"}
    )
    unowned = sorted(
        row.name for row in census.rows if row.legacy and not row.ownership_present
    )
    counterexamples = (
        len(failing_rows)
        + len(unowned)
        + len(duplicates)
        + len(unexpected)
        + len(removed)
        + (len(observed) != API_SYMBOL_COUNT)
        + len(census.frozen_missing)
        + len(census.frozen_extra)
    )
    unverifiable = sorted(
        row.name for row in census.rows if row.classification == "unverifiable"
    )
    verdict = _verdict(counterexamples, not unverifiable)
    resolved = classes["callable"] + classes["constant"]
    return {
        **base,
        "verdict": verdict,
        "resolved_api_symbols": resolved,
        "classification_api_symbols": classes,
        "failing_api_symbols": failing_rows,
        "unverifiable_api_symbols": unverifiable,
        "owned_legacy_api_names": sum(
            1 for row in census.rows if row.legacy and row.ownership_present
        ),
        "unowned_legacy_api_names": unowned,
        "observed_export_list_entries": len(observed),
        "duplicate_exports": duplicates,
        "unexpected_exports": unexpected,
        "removed_exports": removed,
        "frozen_contract_missing": list(census.frozen_missing),
        "frozen_contract_extra": list(census.frozen_extra),
        "counterexample_count": counterexamples,
    }


def adjudicate_h2(record: LoadedRecord) -> dict[str, Any]:
    """Decide H2 from the verified claim-comparator records.

    Args:
        record: The loaded ``conclusions`` record.

    Returns:
        The verdict, per-family counts and every disagreement.
    """
    base: dict[str, Any] = {
        "hypothesis": "H2",
        "run_id": record.spec.run_id,
        "denominator_claim_comparator_records": CLAIM_COMPARATOR_RECORD_COUNT,
    }
    if record.cases is None:
        return {
            **base,
            "verdict": INCONCLUSIVE,
            "reason": f"no admissible record: {record.reason}",
        }
    families: dict[str, dict[str, int]] = {}
    for family, expected_count in FAMILY_COUNTS.items():
        members = [case for case in record.cases if case.family == family]
        agree = sum(1 for case in members if case.agrees)
        families[family] = {
            "denominator_claim_comparator_records": expected_count,
            "present_claim_comparator_records": len(members),
            "agree_claim_comparator_records": agree,
            "disagree_claim_comparator_records": len(members) - agree,
            "missing_claim_comparator_records": expected_count - len(members),
        }
    disagreements = [case.case_id for case in record.cases if not case.agrees]
    complete = len(record.cases) == CLAIM_COMPARATOR_RECORD_COUNT and all(
        block["missing_claim_comparator_records"] == 0 for block in families.values()
    )
    return {
        **base,
        "verdict": _verdict(len(disagreements), complete),
        "agree_claim_comparator_records": len(record.cases) - len(disagreements),
        "disagree_claim_comparator_records": len(disagreements),
        "disagreeing_case_ids": disagreements,
        "families": families,
    }


def _comparable(
    first: LoadedRecord, second: LoadedRecord
) -> tuple[PublicationArm, PublicationArm] | str:
    """Return both arms of a valid comparable pair, or why the pair is not one."""
    if first.arm is None:
        return f"{first.spec.run_id} is inadmissible: {first.reason}"
    if second.arm is None:
        return f"{second.spec.run_id} is inadmissible: {second.reason}"
    a, b = first.arm, second.arm
    if a.renderer != b.renderer:
        return (
            "renderer/font-stack capture differs between the compared runs "
            "(section 4.2 item 3)"
        )
    for path in REGISTERED_TABLES:
        x, y = a.files.get(path), b.files.get(path)
        if (
            x is not None
            and y is not None
            and (x.archived_raw, x.archived_normalized)
            != (
                y.archived_raw,
                y.archived_normalized,
            )
        ):
            return f"archived-table fields for {path} differ between the compared runs"
    return a, b


def adjudicate_h3(
    reference: LoadedRecord, prin: LoadedRecord, policy: str
) -> dict[str, Any]:
    """Decide H3 under one comparison policy.

    Args:
        reference: The loaded reference-arm record.
        prin: The loaded PRIN-arm record.
        policy: ``approved`` (primary) or ``sensitivity`` (section 11.3).

    Returns:
        The verdict, inventories and every differing comparison.
    """
    base: dict[str, Any] = {
        "hypothesis": "H3",
        "policy": policy,
        "reference_run_id": reference.spec.run_id,
        "prin_run_id": prin.spec.run_id,
        "denominator_generated_files": GENERATED_FILE_COUNT,
        "denominator_table_files_vs_archived": len(REGISTERED_TABLES),
    }
    pair = _comparable(reference, prin)
    if isinstance(pair, str):
        return {
            **base,
            "verdict": INCONCLUSIVE,
            "reason": f"no valid completed comparable pair: {pair}",
        }
    registered = set(REGISTERED_FILES)
    ref_files, prin_files = pair[0].files, pair[1].files
    missing_reference = sorted(registered - set(ref_files))
    missing_prin = sorted(registered - set(prin_files))
    extra_reference = sorted(set(ref_files) - registered)
    extra_prin = sorted(set(prin_files) - registered)
    common = sorted(set(ref_files) & set(prin_files))
    differing = [
        path
        for path in common
        if ref_files[path].policy(policy) != prin_files[path].policy(policy)
    ]
    equal_registered = sum(
        1 for path in common if path in registered and path not in differing
    )
    archived_differing: list[str] = []
    reference_archived_inconsistent: list[str] = []
    archived_equal = 0
    for path in REGISTERED_TABLES:
        prin_record, ref_record = prin_files.get(path), ref_files.get(path)
        if prin_record is not None:
            if prin_record.policy(policy) == prin_record.archived(policy):
                archived_equal += 1
            else:
                archived_differing.append(path)
        if ref_record is not None and ref_record.policy(policy) != ref_record.archived(
            policy
        ):
            reference_archived_inconsistent.append(path)
    counterexamples = (
        len(missing_reference)
        + len(missing_prin)
        + len(extra_reference)
        + len(extra_prin)
        + len(differing)
        + len(archived_differing)
    )
    complete = equal_registered == GENERATED_FILE_COUNT and archived_equal == len(
        REGISTERED_TABLES
    )
    formats: dict[str, dict[str, int]] = {}
    for fmt in REGISTERED_FORMATS:
        paths = [path for path in REGISTERED_FILES if path.endswith(f".{fmt}")]
        present = [path for path in paths if path in ref_files and path in prin_files]
        formats[fmt] = {
            "denominator_generated_files": len(paths),
            "equal_generated_files": sum(
                1 for path in present if path not in differing
            ),
            "differ_generated_files": sum(1 for path in present if path in differing),
            "missing_generated_files": len(paths) - len(present),
        }
    return {
        **base,
        "verdict": _verdict(counterexamples, complete),
        "equal_generated_files": equal_registered,
        "differing_generated_files": differing,
        "missing_in_reference": missing_reference,
        "missing_in_prin": missing_prin,
        "extra_in_reference": extra_reference,
        "extra_in_prin": extra_prin,
        "reference_inventory_generated_files": len(ref_files),
        "prin_inventory_generated_files": len(prin_files),
        "tables_equal_to_archived": archived_equal,
        "tables_differing_from_archived": archived_differing,
        "reference_tables_inconsistent_with_archived": reference_archived_inconsistent,
        "by_format": formats,
        "counterexample_count": counterexamples,
    }


def adjudicate_h4(prin: LoadedRecord, repeat: LoadedRecord) -> dict[str, Any]:
    """Decide H4 from the two PRIN processes; raw bytes only, no normalization.

    Args:
        prin: The loaded PRIN-arm record.
        repeat: The loaded repeatability record.

    Returns:
        The verdict, inventories, raw differences and the projection result.
    """
    base: dict[str, Any] = {
        "hypothesis": "H4",
        "prin_run_id": prin.spec.run_id,
        "repeat_run_id": repeat.spec.run_id,
        "denominator_generated_files": GENERATED_FILE_COUNT,
    }
    pair = _comparable(prin, repeat)
    if isinstance(pair, str) or prin.result is None or repeat.result is None:
        return {
            **base,
            "verdict": INCONCLUSIVE,
            "reason": f"no valid comparable pair: {pair}",
        }
    first, second = pair[0].files, pair[1].files
    only_prin = sorted(set(first) - set(second))
    only_repeat = sorted(set(second) - set(first))
    common = sorted(set(first) & set(second))
    raw_differing = [path for path in common if first[path].raw != second[path].raw]
    projection_equal = reproduction_projection(prin.result) == reproduction_projection(
        repeat.result
    )
    counterexamples = (
        len(only_prin) + len(only_repeat) + len(raw_differing) + (not projection_equal)
    )
    registered = set(REGISTERED_FILES)
    complete = registered <= set(first) and set(first) == set(second)
    formats: dict[str, dict[str, int]] = {}
    for fmt in REGISTERED_FORMATS:
        paths = [path for path in REGISTERED_FILES if path.endswith(f".{fmt}")]
        present = [path for path in paths if path in first and path in second]
        formats[fmt] = {
            "denominator_generated_files": len(paths),
            "raw_equal_generated_files": sum(
                1 for path in present if path not in raw_differing
            ),
            "raw_differ_generated_files": sum(
                1 for path in present if path in raw_differing
            ),
            "missing_generated_files": len(paths) - len(present),
        }
    return {
        **base,
        "verdict": _verdict(counterexamples, complete),
        "raw_equal_generated_files": sum(
            1 for path in common if path in registered and path not in raw_differing
        ),
        "raw_differing_generated_files": raw_differing,
        "only_in_prin": only_prin,
        "only_in_repeat": only_repeat,
        "prin_inventory_generated_files": len(first),
        "repeat_inventory_generated_files": len(second),
        "projection_equal": projection_equal,
        "by_format": formats,
        "counterexample_count": counterexamples,
    }


def is_d1(verdicts: Mapping[str, str]) -> bool:
    """Return the section 4.3 D1 flag: any primary verdict ``REFUTED``.

    Args:
        verdicts: Primary verdicts keyed ``H1``..``H4``.

    Returns:
        Whether a registered falsifier occurred.
    """
    return any(verdicts[name] == REFUTED for name in ("H1", "H2", "H3", "H4"))


# ---------------------------------------------------------------------------
# Output rendering
# ---------------------------------------------------------------------------


def _canonical_json(value: Any) -> bytes:
    return (
        json.dumps(value, sort_keys=True, indent=2, ensure_ascii=False, allow_nan=False)
        + "\n"
    ).encode("utf-8")


def _cell(value: object) -> str:
    if value is None:
        return "n/a"
    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, float):
        return repr(value)
    return str(value)


def _csv(header: Sequence[str], rows: Iterable[Sequence[object]]) -> bytes:
    buffer = io.StringIO()
    writer = csv.writer(buffer, lineterminator="\n")
    writer.writerow(header)
    for row in rows:
        writer.writerow([_cell(value) for value in row])
    return buffer.getvalue().encode("utf-8")


def build_api_mapping(record: LoadedRecord) -> bytes:
    """Render ``api-mapping.csv``: one row per expected name, then unexpected exports.

    Args:
        record: The loaded ``api`` record.

    Returns:
        CSV bytes.
    """
    header = (
        "row_kind",
        "name",
        "legacy_reference_name",
        "prin_addition",
        "classification",
        "resolved",
        "callable",
        "defining_module",
        "type",
        "ownership_row_present",
        "resolution_failure",
        "observed_export_occurrences",
        "passes_h1_row_conditions",
    )
    census = record.census
    if census is None:
        return _csv(
            header,
            [
                (
                    "inadmissible_record",
                    record.spec.run_id,
                    *([None] * 10),
                    record.reason,
                )
            ],
        )
    counts: dict[str, int] = {}
    for name in census.observed_names:
        counts[name] = counts.get(name, 0) + 1
    rows: list[Sequence[object]] = []
    for row in census.rows:
        passes = (
            row.classification in {"callable", "constant"} and row.ownership_present
        )
        rows.append(
            (
                "expected",
                row.name,
                row.legacy,
                not row.legacy,
                row.classification,
                row.resolved,
                row.callable,
                row.defining_module,
                row.type_name,
                row.ownership_present if row.legacy else None,
                row.error,
                counts.get(row.name, 0),
                passes and counts.get(row.name, 0) == 1,
            )
        )
    expected = {row.name for row in census.rows}
    for name in sorted(set(census.observed_names) - expected):
        rows.append(
            (
                "unexpected_export",
                name,
                False,
                False,
                "unexpected",
                None,
                None,
                None,
                None,
                None,
                None,
                counts[name],
                False,
            )
        )
    return _csv(header, rows)


def build_conclusion_comparisons(record: LoadedRecord) -> bytes:
    """Render ``conclusion-comparisons.csv`` with every claim-comparator record.

    Args:
        record: The loaded ``conclusions`` record.

    Returns:
        CSV bytes.
    """
    header = (
        "case_id",
        "family",
        "input_file",
        "left_path",
        "left",
        "operator",
        "right_path",
        "right",
        "operand_unit",
        "K",
        "alpha_radians",
        "expected",
        "expected_basis",
        "observed",
        "agrees",
    )
    if record.cases is None:
        return _csv(
            header,
            [
                (
                    f"inadmissible_record:{record.spec.run_id}",
                    *([None] * 13),
                    record.reason,
                )
            ],
        )
    rows = [
        (
            case.case_id,
            case.family,
            case.input_file,
            case.left_path,
            case.left,
            case.operator,
            case.right_path if case.right_path is not None else "registered_threshold",
            case.right,
            case.operand_unit,
            case.k,
            case.alpha_radians,
            case.expected,
            "stored_chimera_detected" if case.family == "C02" else "published_claim",
            case.observed,
            case.agrees,
        )
        for case in record.cases
    ]
    return _csv(header, rows)


def _arm_fields(arm: PublicationArm | None, path: str) -> list[object]:
    record = arm.files.get(path) if arm is not None else None
    if record is None:
        return [False, None, None, None, None, None, None]
    return [True, *record.raw, *record.normalized, *record.sensitivity]


def _equal(
    first: PublicationArm | None, second: PublicationArm | None, path: str, kind: str
) -> bool | None:
    a = first.files.get(path) if first is not None else None
    b = second.files.get(path) if second is not None else None
    if a is None or b is None:
        return None
    if kind == "raw":
        return a.raw == b.raw
    return a.policy(kind) == b.policy(kind)


def _archived_equal(arm: PublicationArm | None, path: str, policy: str) -> bool | None:
    record = arm.files.get(path) if arm is not None else None
    if record is None or record.archived(policy) is None:
        return None
    return record.policy(policy) == record.archived(policy)


def build_reproduction_comparisons(
    reference: LoadedRecord, prin: LoadedRecord, repeat: LoadedRecord
) -> bytes:
    """Render ``reproduction-comparisons.csv`` (sizes in bytes).

    Args:
        reference: The loaded reference-arm record.
        prin: The loaded PRIN-arm record.
        repeat: The loaded repeatability record.

    Returns:
        CSV bytes: the registered files, then any extra outputs.
    """
    arms = (reference.arm, prin.arm, repeat.arm)
    columns = []
    for arm_name in ("reference", "prin", "repeat"):
        columns += [
            f"{arm_name}_present",
            f"{arm_name}_raw_bytes",
            f"{arm_name}_raw_sha256",
            f"{arm_name}_normalized_bytes",
            f"{arm_name}_normalized_sha256",
            f"{arm_name}_sensitivity_bytes",
            f"{arm_name}_sensitivity_sha256",
        ]
    header = (
        "path",
        "format",
        "registered",
        *columns,
        "archived_raw_bytes",
        "archived_raw_sha256",
        "archived_normalized_bytes",
        "archived_normalized_sha256",
        "h3_equal_approved_policy",
        "h3_equal_sensitivity_policy",
        "h3_prin_equals_archived_approved_policy",
        "h3_prin_equals_archived_sensitivity_policy",
        "reference_equals_archived_approved_policy",
        "reference_equals_archived_sensitivity_policy",
        "h4_raw_equal",
        "diagnostic",
    )
    paths = set(REGISTERED_FILES)
    for arm in arms:
        if arm is not None:
            paths |= set(arm.files)
    rows = []
    for path in sorted(paths, key=lambda item: (item not in REGISTERED_FILES, item)):
        archived: list[object] = [None, None, None, None]
        for arm in arms:
            source = arm.files.get(path) if arm is not None else None
            if (
                source is not None
                and source.archived_raw
                and source.archived_normalized
            ):
                archived = [*source.archived_raw, *source.archived_normalized]
                break
        notes = []
        for arm_name, arm in zip(("reference", "prin", "repeat"), arms, strict=True):
            if arm is None:
                notes.append(f"{arm_name} record inadmissible")
            elif path not in arm.files:
                notes.append(f"missing in {arm_name}")
            elif path not in REGISTERED_FILES:
                notes.append(f"extra (unregistered) output in {arm_name}")
        rows.append(
            (
                path,
                PurePosixPath(path).suffix.lstrip("."),
                path in REGISTERED_FILES,
                *_arm_fields(reference.arm, path),
                *_arm_fields(prin.arm, path),
                *_arm_fields(repeat.arm, path),
                *archived,
                _equal(reference.arm, prin.arm, path, APPROVED_POLICY),
                _equal(reference.arm, prin.arm, path, SENSITIVITY_POLICY),
                _archived_equal(prin.arm, path, APPROVED_POLICY),
                _archived_equal(prin.arm, path, SENSITIVITY_POLICY),
                _archived_equal(reference.arm, path, APPROVED_POLICY),
                _archived_equal(reference.arm, path, SENSITIVITY_POLICY),
                _equal(prin.arm, repeat.arm, path, "raw"),
                "; ".join(notes) if notes else "none",
            )
        )
    return _csv(header, rows)


def build_error_distributions(adjudications: Mapping[str, Any]) -> dict[str, Any]:
    """Return categorical populations, each count labelled with its unit.

    Args:
        adjudications: The per-hypothesis adjudication records.

    Returns:
        The ``error-distributions.json`` document.
    """
    h1, h2 = adjudications["H1"], adjudications["H2"]
    h3, h3s, h4 = (
        adjudications["H3"],
        adjudications["H3_sensitivity"],
        adjudications["H4"],
    )
    api: dict[str, Any] = {
        "unit": "api_symbol",
        "denominator_api_symbols": API_SYMBOL_COUNT,
    }
    if "classification_api_symbols" in h1:
        api.update(
            {
                "by_classification_api_symbols": h1["classification_api_symbols"],
                "pass_api_symbols": h1["resolved_api_symbols"],
                "fail_api_symbols": len(h1["failing_api_symbols"]),
                "unverifiable_api_symbols": len(h1["unverifiable_api_symbols"]),
                "missing_from_observed_export_list_api_symbols": len(
                    h1["removed_exports"]
                ),
                "legacy_ownership": {
                    "unit": "legacy_api_name",
                    "denominator_legacy_api_names": LEGACY_NAME_COUNT,
                    "owned_legacy_api_names": h1["owned_legacy_api_names"],
                    "unowned_legacy_api_names": len(h1["unowned_legacy_api_names"]),
                },
            }
        )
    else:
        api["inadmissible"] = h1["reason"]
    claims: dict[str, Any] = {
        "unit": "claim_comparator_record",
        "denominator_claim_comparator_records": CLAIM_COMPARATOR_RECORD_COUNT,
    }
    if "families" in h2:
        claims["by_family"] = h2["families"]
    else:
        claims["inadmissible"] = h2["reason"]

    def files(record: Mapping[str, Any]) -> dict[str, Any]:
        if "by_format" not in record:
            return {"inadmissible": record["reason"]}
        return {"by_format": record["by_format"]}

    return {
        "note": (
            "Separate categorical pass/fail/missing populations; every count "
            "is labelled with its unit. No pooled histogram and no numeric "
            "error distribution is registered for these Boolean/byte censuses "
            "(pre-registration section 8.1)."
        ),
        "api_symbols": api,
        "claim_comparator_records": claims,
        "generated_files": {
            "unit": "generated_file",
            "denominator_generated_files": GENERATED_FILE_COUNT,
            "h3_approved_policy_reference_vs_prin": files(h3),
            "h3_sensitivity_policy_reference_vs_prin": files(h3s),
            "h4_raw_prin_vs_repeat": files(h4),
        },
    }


def _verdict_cell(record: Mapping[str, Any]) -> str:
    return f"**{record['verdict']}**"


def _observed_text(name: str, record: Mapping[str, Any]) -> str:
    if "reason" in record:
        return f"not evaluable - {record['reason']}"
    if name == "H1":
        resolved = record["resolved_api_symbols"]
        owned = record["owned_legacy_api_names"]
        frozen = (
            f"{len(record['frozen_contract_missing'])}/"
            f"{len(record['frozen_contract_extra'])}"
        )
        return (
            f"{resolved}/{API_SYMBOL_COUNT} api_symbols resolved; "
            f"{owned}/{LEGACY_NAME_COUNT} legacy_api_names owned; "
            f"{record['observed_export_list_entries']} observed export-list entries; "
            f"duplicates {len(record['duplicate_exports'])}, removed "
            f"{len(record['removed_exports'])}, unexpected "
            f"{len(record['unexpected_exports'])}; frozen-contract missing/extra "
            f"{frozen}; unverifiable rows {len(record['unverifiable_api_symbols'])}"
        )
    if name == "H2":
        per_family = ", ".join(
            f"{family} {block['agree_claim_comparator_records']}/"
            f"{block['denominator_claim_comparator_records']}"
            for family, block in record["families"].items()
        )
        agree = record["agree_claim_comparator_records"]
        return (
            f"{agree}/{CLAIM_COMPARATOR_RECORD_COUNT} "
            f"claim_comparator_records agree ({per_family}); "
            f"{record['disagree_claim_comparator_records']} disagree"
        )
    if name.startswith("H3"):
        return (
            f"{record['equal_generated_files']}/{GENERATED_FILE_COUNT} generated_files "
            f"equal; {len(record['differing_generated_files'])} differ; missing "
            f"reference/PRIN {len(record['missing_in_reference'])}/"
            f"{len(record['missing_in_prin'])}; extra reference/PRIN "
            f"{len(record['extra_in_reference'])}/{len(record['extra_in_prin'])}; "
            f"tables equal to archived {record['tables_equal_to_archived']}/"
            f"{len(REGISTERED_TABLES)}"
        )
    return (
        f"{record['raw_equal_generated_files']}/{GENERATED_FILE_COUNT} generated_files "
        f"raw-identical; {len(record['raw_differing_generated_files'])} differ; only "
        f"in PRIN/repeat {len(record['only_in_prin'])}/"
        f"{len(record['only_in_repeat'])}; "
        f"canonical projection equal: {_cell(record['projection_equal'])}"
    )


def build_expected_vs_observed(
    summary: Mapping[str, Any], adjudications: Mapping[str, Any]
) -> bytes:
    """Render ``expected-vs-observed.md`` (section 3 predictions side by side).

    Args:
        summary: The summary document.
        adjudications: The per-hypothesis adjudication records.

    Returns:
        Markdown bytes.
    """
    predictions = {
        "H1": (
            "Complete namespace and ownership preservation",
            "175/175 resolved; 172/172 owned; zero duplicate/missing/extra names",
        ),
        "H2": (
            "No reversal of registered historical predicates",
            "62/62 agreements; zero disagreements",
        ),
        "H3": (
            "Reference-faithful publication representation",
            "39/39 equal under the registered format-specific comparison",
        ),
        "H3_sensitivity": (
            "Registered sensitivity analysis (section 11.3 item 1), not a "
            "separate prediction",
            "Reported beside the primary H3 verdict",
        ),
        "H4": (
            "Exact same-implementation repeatability",
            "39/39 raw byte identities; zero projection differences",
        ),
    }
    labels = {
        "H1": "H1",
        "H2": "H2",
        "H3": "H3 (approved policy, primary)",
        "H3_sensitivity": "H3 (section 11.3 sensitivity policy)",
        "H4": "H4",
    }
    lines = [
        "# EXP-002 - expected versus observed (E4, session 0162)",
        "",
        f"Generated by `{MODULE_RELATIVE_PATH}` from the five indexed E3 records "
        f"(source `R` = `{summary['provenance']['execution_commit']}`, protocol "
        f"`F` = `{summary['provenance']['freeze_commit']}`). Predictions are "
        "pre-registration section 3, verbatim.",
        "",
        "| Hypothesis | Predicted direction | Predicted magnitude "
        "| Observed (exact counts, units) | Verdict |",
        "|---|---|---|---|---|",
    ]
    for key in ("H1", "H2", "H3", "H3_sensitivity", "H4"):
        direction, magnitude = predictions[key]
        lines.append(
            f"| {labels[key]} | {direction} | {magnitude} | "
            f"{_observed_text(key, adjudications[key])} | "
            f"{_verdict_cell(adjudications[key])} |"
        )
    lines += [
        "",
        "**Uncertainty:** not applicable. These are deterministic censuses of "
        "fixed populations (pre-registration section 7): no confidence "
        "interval, effect size, significance test or multiplicity correction "
        "is computed, and the exact counts above are descriptive of the finite "
        "population.",
        "",
        f"**D1 flag (section 4.3, campaign plan section 10.4):** "
        f"{'RAISED' if summary['d1_flag'] else 'not raised'} - basis: "
        f"{summary['d1_basis']}.",
        "",
    ]
    if summary["h3_policies_agree"]:
        lines.append(
            "**H3 under both comparison policies:** the approved and the "
            "sensitivity verdicts agree."
        )
    else:
        lines.append(
            "**H3 under both comparison policies:** the verdicts DIFFER. Under "
            "pre-registration section 11.3 item 1, H3's verdict depends on a "
            "comparison amendment made after outcome exposure; neither verdict "
            "may be reported alone."
        )
    lines.append("")
    return "\n".join(lines).encode("utf-8")


def build_coverage(
    summary: Mapping[str, Any],
    records: Sequence[LoadedRecord],
    adjudications: Mapping[str, Any],
) -> bytes:
    """Render ``coverage-and-deferrals.md`` (section 5.3 owner matrix and limits).

    Args:
        summary: The summary document.
        records: The five loaded records.
        adjudications: The per-hypothesis adjudication records.

    Returns:
        Markdown bytes.
    """
    lines = [
        "# EXP-002 - coverage and deferrals (E4, session 0162)",
        "",
        "## Claims owned elsewhere (pre-registration section 5.3)",
        "",
        "No owner below is discharged by EXP-002's archival rendering or by this "
        "analysis. Every row stays open with its owner.",
        "",
        "| Historical conclusion class / source | Scientific owner "
        "| Status after EXP-002 E4 |",
        "|---|---|---|",
    ]
    for claim, owner in OWNER_MATRIX:
        lines.append(f"| {claim} | {owner} | OPEN - not discharged by EXP-002 |")
    lines += [
        "",
        "The WP-033 58-script to nine-category traceability matrix remains the "
        "full legacy benchmark inventory; it is not replaced by the five H2 "
        'families. The draft Parity Report\'s "benchmark re-run not yet run" '
        "distinction remains true for every claim not executed by its owner.",
        "",
        "## Registered coverage of this experiment",
        "",
        "| Run | Mode | Hypotheses | Status | Admissible | Reason if not |",
        "|---|---|---|---|---|---|",
    ]
    for record in records:
        lines.append(
            f"| `{record.spec.run_id}` | {record.spec.mode} | "
            f"{', '.join(record.spec.hypotheses)} | {record.status or 'unread'} | "
            f"{'yes' if record.admissible else 'no'} | {record.reason or '-'} |"
        )
    lines += ["", "Coverage gaps by hypothesis:", ""]
    for key in ("H1", "H2", "H3", "H3_sensitivity", "H4"):
        record = adjudications[key]
        if "reason" in record:
            gap = record["reason"]
        elif key == "H1":
            gap = f"unverifiable rows: {record['unverifiable_api_symbols'] or 'none'}"
        elif key == "H2":
            missing = {
                family: block["missing_claim_comparator_records"]
                for family, block in record["families"].items()
                if block["missing_claim_comparator_records"]
            }
            gap = f"missing claim_comparator_records by family: {missing or 'none'}"
        elif key.startswith("H3"):
            gap = (
                f"missing in reference: {record['missing_in_reference'] or 'none'}; "
                f"missing in PRIN: {record['missing_in_prin'] or 'none'}"
            )
        else:
            gap = (
                f"only in PRIN: {record['only_in_prin'] or 'none'}; "
                f"only in repeat: {record['only_in_repeat'] or 'none'}"
            )
        lines.append(f"- **{key}** ({record['verdict']}): {gap}")
    lines += [
        "",
        "## Limits and downstream gates",
        "",
        "- **Scope of H1.** Export/mapping completeness only; no behavioural or "
        "numerical parity of any callable (EXP-001 owns numerical parity; "
        "e2-review.md decision 1).",
        "- **Scope of H2.** The 62 registered archival predicates only; C02's "
        "basis is archival self-consistency (stored `chimera_detected`), not an "
        "independent prediction. No fresh dynamics were run.",
        "- **Retained publication bytes.** This analysis decides H3/H4 from the "
        "manifested digest records and does not read the retained publication "
        "roots. E5 must first verify those bytes against the raw digests in each "
        "manifested `reproduction.json`, then reconstruct from a clean checkout "
        "(pre-registration sections 8.2 and 11.3 item 2). Until then the "
        "publication reconstruction is not byte-verified.",
        "- **Hardware and platforms.** One Windows host (H1) only. Linux, macOS, "
        "Metal, NPU and the wheel matrix are not tested and not claimed "
        "(Plan amendment #48; EXP-008).",
        "- **Hosted checks.** Plan amendment #50 hosted runs are additional "
        "evidence only; the Windows local gate is authoritative.",
        "- **Coverage tooling.** DV-033 (per-change coverage on the maintainer "
        "host) stays OPEN; this analysis does not close it.",
        "- **Downstream gates carried, not actioned:** DV036-F5 at 0166; the "
        "DV-036 reference-host gates before 0168 (CPU) and 0173 (GPU/bridge); "
        "EXP-004+ hardware gates (campaign plan section 5.4); DV-034; "
        "PSR-040 S2-F3/S2-F4; PR32-F13/OBS-1/OBS-2.",
        "",
        f"D1 flag: {'RAISED' if summary['d1_flag'] else 'not raised'}.",
        "",
    ]
    return "\n".join(lines).encode("utf-8")


def _run_summary(record: LoadedRecord) -> dict[str, Any]:
    return {
        "run_id": record.spec.run_id,
        "mode": record.spec.mode,
        "label": record.spec.label,
        "hypotheses": list(record.spec.hypotheses),
        "status": record.status,
        "admissible": record.admissible,
        "inadmissibility_reason": record.reason,
    }


def build_summary(
    context: Context, records: Sequence[LoadedRecord], adjudications: Mapping[str, Any]
) -> dict[str, Any]:
    """Return the ``summary.json`` document.

    Args:
        context: The verified global context.
        records: The five loaded records, in registered order.
        adjudications: The per-hypothesis adjudication records.

    Returns:
        The summary document.
    """
    registration = context.registration
    primary = {
        name: adjudications[name]["verdict"] for name in ("H1", "H2", "H3", "H4")
    }
    sensitivity = adjudications["H3_sensitivity"]["verdict"]
    d1 = is_d1(primary)
    refuted = [name for name, verdict in primary.items() if verdict == REFUTED]
    return {
        "experiment": EXPERIMENT_ID,
        "session": SESSION,
        "stage": STAGE,
        "analysis_date_utc": ANALYSIS_DATE_UTC,
        "analysis_module": {
            "path": MODULE_RELATIVE_PATH,
            "sha256": context.module_sha256,
            "commit": context.module_commit,
            "matches_commit": context.module_matches_commit,
        },
        "provenance": {
            "execution_commit": registration.source_sha,
            "freeze_commit": registration.protocol_commit,
            "protocol_path": PROTOCOL_PATH,
            "protocol_sha256": registration.protocol_sha256,
            "approval_date_utc": registration.approval_date_utc,
            "input_manifest_path": INPUT_MANIFEST_PATH,
            "input_manifest_sha256": registration.input_manifest_sha256,
            "input_record_count": len(context.input_records),
            "reference_api_sha256": registration.reference_api_sha256,
            "public_api_sha256": registration.public_api_sha256,
            "deprecation_sha256": registration.deprecation_sha256,
        },
        "populations": {
            "api_symbol_count": API_SYMBOL_COUNT,
            "legacy_api_name_count": LEGACY_NAME_COUNT,
            "claim_comparator_record_count": CLAIM_COMPARATOR_RECORD_COUNT,
            "generated_file_count": GENERATED_FILE_COUNT,
            "generated_figure_file_count": 2 * len(FIGURE_STEMS),
            "generated_table_file_count": len(TABLE_STEMS),
            "analysis_output_file_count": ANALYSIS_OUTPUT_COUNT,
            "note": (
                "The 39 generated publication files are separate from the 7 "
                "analysis outputs; they are never summed."
            ),
        },
        "runs": [_run_summary(record) for record in records],
        "aborted_runs": [
            record.spec.run_id for record in records if record.status == "ABORTED"
        ],
        "inadmissible_runs": [
            {"run_id": record.spec.run_id, "reason": record.reason}
            for record in records
            if not record.admissible
        ],
        "verdicts": {**primary, "H3_sensitivity_policy": sensitivity},
        "h3_policies_agree": primary["H3"] == sensitivity,
        "h3_policy_note": (
            "H3 is decided under the approved section 5.4 policy (primary, "
            "confirmatory per e2-review.md decision 9) and under the section 11.3 "
            "sensitivity policy. If they differ, H3's verdict depends on a "
            "comparison amendment made after outcome exposure and neither "
            "verdict may be reported alone."
        ),
        "hypotheses": dict(adjudications),
        "d1_flag": d1,
        "d1_hypotheses": refuted,
        "d1_basis": (
            "any primary verdict REFUTED (pre-registration section 4.3; campaign "
            "plan section 10.4)"
        ),
        "h3_sensitivity_policy_refuted": sensitivity == REFUTED,
        "statistics": {
            "confidence_intervals": _NOT_APPLICABLE,
            "effect_sizes": _NOT_APPLICABLE,
            "significance_tests": "none registered",
        },
    }


# ---------------------------------------------------------------------------
# Writing (confined to the two registered destinations)
# ---------------------------------------------------------------------------


def _write_confined(path: Path, payload: bytes) -> None:
    """Atomically replace a regular file whose ancestors are not links."""
    _check_no_links(path, AnalysisError)
    if path.exists() and not path.is_file():
        raise AnalysisError(f"output destination is not a regular file: {path}")
    descriptor, temporary = tempfile.mkstemp(prefix=".exp002-e4-", dir=path.parent)
    try:
        with os.fdopen(descriptor, "wb") as stream:
            stream.write(payload)
        os.replace(temporary, path)
    except BaseException:
        if os.path.exists(temporary):
            os.unlink(temporary)
        raise


def write_outputs(
    repository_root: Path, outputs: Mapping[str, bytes], report_manifest: bytes
) -> None:
    """Write the seven outputs and ``report-manifest.json``; nothing else.

    Args:
        repository_root: The checkout.
        outputs: The seven analysis files keyed by registered filename.
        report_manifest: The committed record-root manifest bytes.

    Raises:
        AnalysisError: If a destination is not the registered one or has a
            link ancestor.
    """
    _require(
        tuple(outputs) == OUTPUT_FILENAMES, "unregistered output set", AnalysisError
    )
    output_dir = repository_root / OUTPUT_DIR
    _check_no_links(output_dir, AnalysisError)
    output_dir.mkdir(parents=True, exist_ok=True)
    for name, payload in outputs.items():
        _write_confined(output_dir / name, payload)
    _write_confined(repository_root / REPORT_MANIFEST_PATH, report_manifest)


def build_report_manifest(
    context: Context,
    records: Sequence[LoadedRecord],
    outputs: Mapping[str, bytes],
    summary: Mapping[str, Any],
) -> bytes:
    """Return ``report-manifest.json`` (campaign plan section 7.4 item 4).

    Args:
        context: The verified global context.
        records: The five loaded records.
        outputs: The seven analysis files.
        summary: The summary document.

    Returns:
        Canonical JSON bytes.
    """
    registration = context.registration
    prin = next(record for record in records if record.spec.mode == "prin")
    publication_root = f"{GENERATED_ROOT}/{prin.spec.run_id}/publication"
    publication = (
        [
            {
                "path": f"{publication_root}/{record.path}",
                "bytes": record.raw[0],
                "sha256": record.raw[1],
            }
            for record in prin.arm.files.values()
        ]
        if prin.arm is not None
        else []
    )
    document = {
        "experiment": EXPERIMENT_ID,
        "session": SESSION,
        "generator": MODULE_RELATIVE_PATH,
        "generator_commit": context.module_commit,
        "generator_sha256": context.module_sha256,
        "decision_rule": (
            "preregistration.md sections 4.1, 5.2, 5.4, 5.5 and 11.3, frozen at "
            f"F = {registration.protocol_commit}"
        ),
        "execution_commit": registration.source_sha,
        "freeze_commit": registration.protocol_commit,
        "protocol_sha256": registration.protocol_sha256,
        "input_manifest": {
            "path": INPUT_MANIFEST_PATH,
            "sha256": registration.input_manifest_sha256,
            "record_count": len(context.input_records),
        },
        "inputs": [
            {
                "run_id": record.spec.run_id,
                "mode": record.spec.mode,
                "label": record.spec.label,
                "hypotheses": list(record.spec.hypotheses),
                "admissible": record.admissible,
                "manifest": {
                    "path": f"{RAW_ROOT}/{record.spec.run_id}/{MANIFEST}",
                    "bytes": record.manifest.bytes if record.manifest else None,
                    "sha256": record.manifest.sha256 if record.manifest else None,
                },
                "files": [
                    {
                        "path": f"{RAW_ROOT}/{record.spec.run_id}/{entry.path}",
                        "bytes": entry.bytes,
                        "sha256": entry.sha256,
                    }
                    for entry in record.files
                ],
            }
            for record in records
        ],
        "analysis_outputs": [
            {
                "path": f"{OUTPUT_DIR}/{name}",
                "bytes": len(payload),
                "sha256": _sha256(payload),
            }
            for name, payload in outputs.items()
        ],
        "analysis_output_file_count": len(outputs),
        "publication_outputs": {
            "source_run_id": prin.spec.run_id,
            "note": (
                "Raw size and SHA-256 of each generated publication file of the "
                "PRIN arm, as manifested in its reproduction.json. These 39 "
                "registered files are separate from the 7 analysis outputs. E5 "
                "verifies the retained bytes first, then reconstructs "
                "(pre-registration sections 8.2 and 11.3 item 2)."
            ),
            "generated_file_count": len(publication),
            "files": publication,
        },
        "verdicts": summary["verdicts"],
        "d1_flag": summary["d1_flag"],
    }
    return _canonical_json(document)


# ---------------------------------------------------------------------------
# Orchestration
# ---------------------------------------------------------------------------


def adjudicate_all(records: Mapping[str, LoadedRecord]) -> dict[str, Any]:
    """Decide H1-H4 and the H3 sensitivity verdict.

    Args:
        records: Loaded records keyed by mode.

    Returns:
        Adjudication records keyed ``H1``, ``H2``, ``H3``, ``H3_sensitivity``, ``H4``.
    """
    return {
        "H1": adjudicate_h1(records["api"]),
        "H2": adjudicate_h2(records["conclusions"]),
        "H3": adjudicate_h3(records["reference"], records["prin"], APPROVED_POLICY),
        "H3_sensitivity": adjudicate_h3(
            records["reference"], records["prin"], SENSITIVITY_POLICY
        ),
        "H4": adjudicate_h4(records["prin"], records["repeatability"]),
    }


def run_analysis(repository_root: Path, registration: Registration) -> dict[str, Any]:
    """Run the registered E4 analysis and write its outputs.

    Args:
        repository_root: The checkout holding the records and frozen inputs.
        registration: The pinned identities and the explicit run index.

    Returns:
        The summary document and the digests of everything written.

    Raises:
        AnalysisError: If a global precondition fails (nothing is written).
    """
    return analyse(verify_context(repository_root, registration))


def analyse(context: Context) -> dict[str, Any]:
    """Load, adjudicate and write, given an already verified global context.

    Args:
        context: The result of :func:`verify_context`.

    Returns:
        The summary document and the digests of everything written.

    Raises:
        AnalysisError: If an output destination is refused.
    """
    loaded = [load_record(context, spec) for spec in context.registration.runs]
    by_mode = {record.spec.mode: record for record in loaded}
    adjudications = adjudicate_all(by_mode)
    summary = build_summary(context, loaded, adjudications)
    outputs = {
        "summary.json": _canonical_json(summary),
        "api-mapping.csv": build_api_mapping(by_mode["api"]),
        "conclusion-comparisons.csv": build_conclusion_comparisons(
            by_mode["conclusions"]
        ),
        "reproduction-comparisons.csv": build_reproduction_comparisons(
            by_mode["reference"], by_mode["prin"], by_mode["repeatability"]
        ),
        "error-distributions.json": _canonical_json(
            build_error_distributions(adjudications)
        ),
        "expected-vs-observed.md": build_expected_vs_observed(summary, adjudications),
        "coverage-and-deferrals.md": build_coverage(summary, loaded, adjudications),
    }
    report_manifest = build_report_manifest(context, loaded, outputs, summary)
    write_outputs(context.repository_root, outputs, report_manifest)
    return {
        "summary": summary,
        "outputs": {name: _sha256(payload) for name, payload in outputs.items()},
        "report_manifest_sha256": _sha256(report_manifest),
    }


def main(argv: Sequence[str] | None = None) -> int:
    """Run the registered analysis on this checkout; print verdicts and digests.

    Args:
        argv: Command-line arguments (none are accepted).

    Returns:
        ``0`` when the analysis completed (whatever the verdicts), ``1`` when
        a global precondition failed and nothing was written.
    """
    parser = argparse.ArgumentParser(description="EXP-002 registered E4 analysis.")
    parser.parse_args(argv)
    try:
        outcome = run_analysis(REPOSITORY_ROOT, REGISTERED)
    except AnalysisError as exc:
        print(f"EXP-002 E4 ANALYSIS NOT COMPLETED: {exc}", file=sys.stderr)
        return 1
    summary = outcome["summary"]
    for name, verdict in summary["verdicts"].items():
        print(f"{name}: {verdict}")
    print(f"D1 flag: {summary['d1_flag']}")
    for name, digest in outcome["outputs"].items():
        print(f"{OUTPUT_DIR}/{name} {digest}")
    print(f"{REPORT_MANIFEST_PATH} {outcome['report_manifest_sha256']}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
