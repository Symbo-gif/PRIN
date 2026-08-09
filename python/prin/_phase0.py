"""Phase 0 exit-gate evidence consolidation.

This module validates the three foundation spikes (DLPack, CubeCL, ORT), the
golden-trajectory corpus, the abi3 wheel smoke matrix, and the recorded go/no-go
decisions before the Phase 0 pre-release tag.
"""

from __future__ import annotations

import importlib
import json
import re
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, cast

from .parity.loader import CorpusLoader
from .parity.schema import CorpusValidationError

_DEFAULT_ORT_EVIDENCE = Path("EVIDENCE") / "0017-wp005-s1-ort-probe.json"
_EXPECTED_CORPUS_CASES = 504


class Phase0GateError(Exception):
    """Raised when a Phase 0 gate check fails."""


@dataclass(frozen=True)
class Phase0GateReport:
    """Aggregated result of all Phase 0 gate checks."""

    timestamp: str
    ready: bool
    checks: dict[str, dict[str, Any]]

    def to_dict(self) -> dict[str, Any]:
        """Serialize the report to a JSON-compatible dictionary."""
        return {
            "timestamp": self.timestamp,
            "ready": self.ready,
            "checks": self.checks,
        }


def _json_status(ok: bool, **kwargs: Any) -> dict[str, Any]:
    """Return a standard check result dictionary."""
    result: dict[str, Any] = {"status": "ok" if ok else "fail"}
    result.update(kwargs)
    return result


def _read_json(path: Path) -> dict[str, Any]:
    """Load and return a JSON file, raising ``Phase0GateError`` on failure."""
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise Phase0GateError(f"cannot read JSON at {path}: {exc}") from exc
    if not isinstance(payload, dict):
        raise Phase0GateError(f"JSON at {path} is not an object")
    return cast(dict[str, Any], payload)


def _check_corpus(root: Path) -> dict[str, Any]:
    """Validate the golden-trajectory corpus manifest and case files."""
    corpus_dir = root / "parity" / "corpus"
    try:
        loader = CorpusLoader(corpus_dir)
    except CorpusValidationError as exc:
        return _json_status(False, error=f"corpus validation failed: {exc}")
    except OSError as exc:
        return _json_status(False, error=f"corpus not readable: {exc}")

    n_cases = len(loader)
    ok = n_cases == _EXPECTED_CORPUS_CASES
    return _json_status(
        ok,
        n_cases=n_cases,
        manifest_path=str(loader.corpus_dir / "manifest.json"),
        expected_cases=_EXPECTED_CORPUS_CASES,
        cases_match=ok,
        error=None
        if ok
        else f"expected {_EXPECTED_CORPUS_CASES} cases, found {n_cases}",
    )


def _check_ort(
    root: Path,
    evidence_path: Path = _DEFAULT_ORT_EVIDENCE,
    refresh: bool = False,
) -> dict[str, Any]:
    """Validate the ONNX Runtime provider probe evidence.

    If ``refresh`` is ``True`` and ``onnxruntime`` is installed, the probe is
    re-run against ``models/subconscious_controller.onnx`` and the evidence file
    is overwritten. Otherwise the existing evidence file is read.
    """
    if not evidence_path.is_absolute():
        evidence_path = root / evidence_path
    model_path = root / "models" / "subconscious_controller.onnx"
    if not model_path.is_file():
        return _json_status(False, error=f"controller model missing: {model_path}")

    if refresh:
        try:
            ort = importlib.import_module("prin._ort")
            report = ort.probe_model(model_path)
            evidence_path.parent.mkdir(parents=True, exist_ok=True)
            evidence_path.write_text(
                json.dumps(
                    report.to_dict(), indent=2, sort_keys=True, ensure_ascii=False
                ),
                encoding="utf-8",
            )
        except Exception as exc:
            return _json_status(False, error=f"ORT probe failed: {exc}")

    if not evidence_path.is_file():
        return _json_status(
            False,
            error=f"ORT evidence missing: {evidence_path}; run with refresh=True",
        )

    try:
        payload = _read_json(evidence_path)
    except Phase0GateError as exc:
        return _json_status(False, error=str(exc))

    can_run = payload.get("can_run", False)
    return _json_status(
        can_run,
        evidence_path=str(evidence_path),
        available_providers=payload.get("available_providers", []),
        selected_backend=payload.get("selected_backend"),
        active_providers=payload.get("active_providers", []),
        output_shape=payload.get("output_shape"),
        error=payload.get("error"),
    )


def _check_wheel_matrix(root: Path) -> dict[str, Any]:
    """Validate the release workflow wheel matrix and abi3 configuration."""
    release_yml = root / ".github" / "workflows" / "release.yml"
    prin_py_toml = root / "crates" / "prin-py" / "Cargo.toml"
    pyproject = root / "pyproject.toml"

    if not release_yml.is_file():
        return _json_status(False, error=".github/workflows/release.yml missing")
    if not prin_py_toml.is_file():
        return _json_status(False, error="crates/prin-py/Cargo.toml missing")
    if not pyproject.is_file():
        return _json_status(False, error="pyproject.toml missing")

    release_text = release_yml.read_text(encoding="utf-8")
    prin_py_text = prin_py_toml.read_text(encoding="utf-8")
    pyproject_text = pyproject.read_text(encoding="utf-8")

    findings: dict[str, Any] = {}
    errors: list[str] = []

    os_list = re.findall(r"^\s*-\s*os:\s*([\w-]+)", release_text, re.MULTILINE)
    targets = re.findall(
        r"^\s{10,}target:\s*([\w-]+(?:-[\w-]+)?)", release_text, re.MULTILINE
    )
    if {"ubuntu-latest", "windows-latest", "macos-latest"}.issubset(set(os_list)):
        findings["three_os_matrix"] = True
    else:
        findings["three_os_matrix"] = False
        errors.append("release.yml wheel matrix does not cover three OS targets")

    findings["targets"] = targets
    if "universal2-apple-darwin" in targets:
        findings["macos_universal2"] = True
    else:
        findings["macos_universal2"] = False
        errors.append("release.yml missing macOS universal2 target")

    if "Wheel smoke test" in release_text and "pip install dist/*.whl" in release_text:
        findings["wheel_smoke_step"] = True
    else:
        findings["wheel_smoke_step"] = False
        errors.append("release.yml missing wheel smoke test")

    if "abi3-py311" in prin_py_text:
        findings["pyo3_abi3"] = True
    else:
        findings["pyo3_abi3"] = False
        errors.append("prin-py/Cargo.toml missing pyo3 abi3-py311 feature")

    if "Operating System :: OS Independent" in pyproject_text:
        findings["os_independent_classifier"] = True
    else:
        findings["os_independent_classifier"] = False
        errors.append("pyproject.toml missing OS Independent classifier")

    ok = not errors
    return _json_status(
        ok,
        findings=findings,
        errors=errors,
    )


def _check_spike_decisions(root: Path) -> dict[str, Any]:
    """Check that the three Phase 0 spike go/no-go decisions are recorded."""
    plan = root / "DOCS" / "PRIN_Project_Plan.md"
    if not plan.is_file():
        return _json_status(False, error="project plan missing")

    text = plan.read_text(encoding="utf-8")
    evidence = root / "EVIDENCE" / "0017-wp005-s1-ort-probe.json"
    amendments = {
        "amendment_7_dlpack": "| 7 |" in text and "DLPack" in text,
        "amendment_11_cubecl": "| 11 |" in text and "CubeCL" in text,
        "amendment_13_ort": (
            "| 13 |" in text
            and ("ORT" in text or "ONNX" in text)
            and "VitisAI" in text
            and evidence.is_file()
        ),
    }

    ok = all(amendments.values())
    return _json_status(
        ok,
        amendments=amendments,
        errors=[]
        if ok
        else [f"{k} not recorded" for k, v in amendments.items() if not v],
    )


def phase0_gate_report(
    root: Path | None = None,
    refresh_ort: bool = False,
    evidence_path: Path = _DEFAULT_ORT_EVIDENCE,
) -> Phase0GateReport:
    """Run the complete Phase 0 exit-gate check and return an evidence report.

    Args:
        root: Repository root. Defaults to the current working directory.
        refresh_ort: If ``True``, re-run the ORT probe before checking evidence.
        evidence_path: Path to the ORT probe evidence JSON.

    Returns:
        A :class:`Phase0GateReport` with every gate and the overall ``ready``
        verdict.
    """
    if root is None:
        root = Path.cwd()

    checks = {
        "corpus": _check_corpus(root),
        "ort": _check_ort(root, evidence_path, refresh_ort),
        "wheel_matrix": _check_wheel_matrix(root),
        "spike_decisions": _check_spike_decisions(root),
    }
    ready = all(check["status"] == "ok" for check in checks.values())

    return Phase0GateReport(
        timestamp=datetime.now(UTC).isoformat(),
        ready=ready,
        checks=checks,
    )


def write_gate_report(
    report: Phase0GateReport,
    path: Path,
) -> None:
    """Write ``report`` to ``path`` as formatted JSON."""
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(report.to_dict(), indent=2, sort_keys=True, ensure_ascii=False),
        encoding="utf-8",
    )


__all__: list[str] = [
    "Phase0GateError",
    "Phase0GateReport",
    "phase0_gate_report",
    "write_gate_report",
]
