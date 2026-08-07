"""Tests for the Phase 0 exit-gate consolidation (WP-005)."""

from __future__ import annotations

import json
from pathlib import Path

import pytest
from prin._phase0 import (
    Phase0GateError,
    Phase0GateReport,
    _check_corpus,
    _check_ort,
    _check_spike_decisions,
    _check_wheel_matrix,
    phase0_gate_report,
    write_gate_report,
)


def _write_empty_manifest(corpus_dir: Path) -> None:
    corpus_dir.mkdir(parents=True, exist_ok=True)
    manifest = {
        "schema_version": 1,
        "generator": "pytest",
        "generator_version": "0.0.0",
        "prin_version": "0.1.0",
        "created_at": "2026-08-06T00:00:00+00:00",
        "n_cases": 0,
        "reference_source": "pytest fake corpus",
        "trajectory_rtol": 1e-6,
        "trajectory_atol": 1e-8,
        "cases": [],
    }
    (corpus_dir / "manifest.json").write_text(
        json.dumps(manifest, indent=2), encoding="utf-8"
    )


class TestCheckCorpus:
    def test_empty_corpus_mismatches_expected(self, tmp_path: Path) -> None:
        corpus_dir = tmp_path / "parity" / "corpus"
        _write_empty_manifest(corpus_dir)
        result = _check_corpus(tmp_path)
        assert result["status"] == "fail"
        assert result["n_cases"] == 0

    def test_missing_corpus(self, tmp_path: Path) -> None:
        result = _check_corpus(tmp_path)
        assert result["status"] == "fail"


class TestCheckOrt:
    def test_existing_evidence(self, tmp_path: Path) -> None:
        evidence_dir = tmp_path / "EVIDENCE"
        evidence_dir.mkdir(parents=True, exist_ok=True)
        model = tmp_path / "models" / "subconscious_controller.onnx"
        model.parent.mkdir(parents=True, exist_ok=True)
        model.write_text("dummy")
        evidence = {
            "model_path": str(model),
            "model_sha256": "a" * 64,
            "available_providers": ["CPUExecutionProvider"],
            "selected_backend": "cpu",
            "active_providers": ["CPUExecutionProvider"],
            "input_metadata": [],
            "output_metadata": [],
            "can_run": True,
            "output_shape": [1, 8],
            "error": None,
            "timestamp": "2026-08-06T00:00:00+00:00",
        }
        evidence_path = evidence_dir / "0017-wp005-s1-ort-probe.json"
        evidence_path.write_text(json.dumps(evidence, indent=2), encoding="utf-8")
        result = _check_ort(tmp_path, evidence_path=evidence_path)
        assert result["status"] == "ok"
        assert result["selected_backend"] == "cpu"

    def test_missing_model(self, tmp_path: Path) -> None:
        result = _check_ort(tmp_path)
        assert result["status"] == "fail"

    def test_missing_evidence(self, tmp_path: Path) -> None:
        model = tmp_path / "models" / "subconscious_controller.onnx"
        model.parent.mkdir(parents=True, exist_ok=True)
        model.write_text("dummy")
        result = _check_ort(tmp_path)
        assert result["status"] == "fail"


class TestCheckWheelMatrix:
    _RELEASE_YML = (
        "      matrix:\n"
        "        include:\n"
        "          - os: ubuntu-latest\n"
        "            target: x86_64\n"
        "          - os: windows-latest\n"
        "            target: x86_64\n"
        "          - os: macos-latest\n"
        "            target: universal2-apple-darwin\n"
        "      - name: Wheel smoke test\n"
        "        run: |\n"
        "          pip install dist/*.whl\n"
    )

    def test_valid_config(self, tmp_path: Path) -> None:
        workflows = tmp_path / ".github" / "workflows"
        workflows.mkdir(parents=True, exist_ok=True)
        (workflows / "release.yml").write_text(self._RELEASE_YML, encoding="utf-8")
        crates = tmp_path / "crates" / "prin-py"
        crates.mkdir(parents=True, exist_ok=True)
        (crates / "Cargo.toml").write_text(
            'features = ["abi3-py311"]', encoding="utf-8"
        )
        (tmp_path / "pyproject.toml").write_text(
            "Operating System :: OS Independent\n", encoding="utf-8"
        )
        result = _check_wheel_matrix(tmp_path)
        assert result["status"] == "ok"
        assert result["findings"]["three_os_matrix"] is True
        assert result["findings"]["macos_universal2"] is True

    def test_missing_os(self, tmp_path: Path) -> None:
        workflows = tmp_path / ".github" / "workflows"
        workflows.mkdir(parents=True, exist_ok=True)
        (workflows / "release.yml").write_text("target: x86_64\n", encoding="utf-8")
        result = _check_wheel_matrix(tmp_path)
        assert result["status"] == "fail"


class TestCheckSpikeDecisions:
    def test_all_recorded(self, tmp_path: Path) -> None:
        docs = tmp_path / "DOCS"
        docs.mkdir(parents=True, exist_ok=True)
        plan = docs / "PRIN_Project_Plan.md"
        plan.write_text(
            "| 7 | DLPack\n| 11 | CubeCL\n| 13 | ORT ONNX VitisAI\n",
            encoding="utf-8",
        )
        evidence = tmp_path / "EVIDENCE" / "0017-wp005-s1-ort-probe.json"
        evidence.parent.mkdir(parents=True, exist_ok=True)
        evidence.write_text("{}", encoding="utf-8")
        result = _check_spike_decisions(tmp_path)
        assert result["status"] == "ok"

    def test_missing_ort_evidence(self, tmp_path: Path) -> None:
        docs = tmp_path / "DOCS"
        docs.mkdir(parents=True, exist_ok=True)
        plan = docs / "PRIN_Project_Plan.md"
        plan.write_text(
            "| 7 | DLPack\n| 11 | CubeCL\n| 13 | ORT ONNX VitisAI\n",
            encoding="utf-8",
        )
        result = _check_spike_decisions(tmp_path)
        assert result["status"] == "fail"

    def test_missing_ort_amendment_in_plan(self, tmp_path: Path) -> None:
        """Regression for WP005-F1: gate must fail when amendment 13 is absent."""
        docs = tmp_path / "DOCS"
        docs.mkdir(parents=True, exist_ok=True)
        plan = docs / "PRIN_Project_Plan.md"
        plan.write_text("| 7 | DLPack\n| 11 | CubeCL\n", encoding="utf-8")
        evidence = tmp_path / "EVIDENCE" / "0017-wp005-s1-ort-probe.json"
        evidence.parent.mkdir(parents=True, exist_ok=True)
        evidence.write_text("{}", encoding="utf-8")
        result = _check_spike_decisions(tmp_path)
        assert result["status"] == "fail"
        assert "amendment_13_ort" in result["errors"][0]


class TestPhase0GateReport:
    _RELEASE_YML = (
        "      matrix:\n"
        "        include:\n"
        "          - os: ubuntu-latest\n"
        "            target: x86_64\n"
        "          - os: windows-latest\n"
        "            target: x86_64\n"
        "          - os: macos-latest\n"
        "            target: universal2-apple-darwin\n"
        "      - name: Wheel smoke test\n"
        "        run: |\n"
        "          pip install dist/*.whl\n"
    )

    def test_full_gate_ready(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.setattr("prin._phase0._EXPECTED_CORPUS_CASES", 0)
        _write_empty_manifest(tmp_path / "parity" / "corpus")
        model = tmp_path / "models" / "subconscious_controller.onnx"
        model.parent.mkdir(parents=True, exist_ok=True)
        model.write_text("dummy")
        evidence = tmp_path / "EVIDENCE" / "0017-wp005-s1-ort-probe.json"
        evidence.parent.mkdir(parents=True, exist_ok=True)
        evidence.write_text(
            json.dumps(
                {
                    "can_run": True,
                    "selected_backend": "cpu",
                    "active_providers": ["CPUExecutionProvider"],
                    "output_shape": [1, 8],
                    "error": None,
                }
            ),
            encoding="utf-8",
        )
        workflows = tmp_path / ".github" / "workflows"
        workflows.mkdir(parents=True, exist_ok=True)
        (workflows / "release.yml").write_text(self._RELEASE_YML, encoding="utf-8")
        crates = tmp_path / "crates" / "prin-py"
        crates.mkdir(parents=True, exist_ok=True)
        (crates / "Cargo.toml").write_text(
            'features = ["abi3-py311"]', encoding="utf-8"
        )
        (tmp_path / "pyproject.toml").write_text(
            "Operating System :: OS Independent\n", encoding="utf-8"
        )
        docs = tmp_path / "DOCS"
        docs.mkdir(parents=True, exist_ok=True)
        (docs / "PRIN_Project_Plan.md").write_text(
            "| 7 | DLPack\n| 11 | CubeCL\n| 13 | ORT ONNX VitisAI\n",
            encoding="utf-8",
        )

        report = phase0_gate_report(tmp_path)
        assert isinstance(report, Phase0GateReport)
        assert report.ready is True
        assert all(check["status"] == "ok" for check in report.checks.values())


class TestPhase0Utilities:
    def test_report_to_dict(self) -> None:
        report = Phase0GateReport(
            timestamp="2026-08-06T00:00:00+00:00",
            ready=True,
            checks={"corpus": {"status": "ok"}},
        )
        d = report.to_dict()
        assert d["ready"] is True
        assert d["checks"]["corpus"]["status"] == "ok"

    def test_write_gate_report(self, tmp_path: Path) -> None:
        report = Phase0GateReport(
            timestamp="2026-08-06T00:00:00+00:00",
            ready=False,
            checks={},
        )
        out = tmp_path / "gate.json"
        write_gate_report(report, out)
        payload = json.loads(out.read_text(encoding="utf-8"))
        assert payload["ready"] is False


class TestPhase0EdgeCases:
    def test_read_json_missing_file(self, tmp_path: Path) -> None:
        from prin._phase0 import _read_json

        with pytest.raises(Phase0GateError):
            _read_json(tmp_path / "missing.json")

    def test_read_json_invalid_json(self, tmp_path: Path) -> None:
        from prin._phase0 import _read_json

        bad = tmp_path / "bad.json"
        bad.write_text("not json", encoding="utf-8")
        with pytest.raises(Phase0GateError):
            _read_json(bad)

    def test_read_json_non_object(self, tmp_path: Path) -> None:
        from prin._phase0 import _read_json

        bad = tmp_path / "bad.json"
        bad.write_text("[1, 2]", encoding="utf-8")
        with pytest.raises(Phase0GateError):
            _read_json(bad)

    def test_corpus_oserror(
        self, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
    ) -> None:
        class _BadLoader:
            def __init__(self, *args: object, **kwargs: object) -> None:
                raise OSError("simulated")

        monkeypatch.setattr("prin._phase0.CorpusLoader", _BadLoader)
        result = _check_corpus(tmp_path)
        assert result["status"] == "fail"

    def test_ort_refresh_failure(
        self, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
    ) -> None:
        model = tmp_path / "models" / "subconscious_controller.onnx"
        model.parent.mkdir(parents=True, exist_ok=True)
        model.write_text("dummy")

        def _fail(*args: object, **kwargs: object) -> object:
            raise RuntimeError("probe failed")

        monkeypatch.setattr("prin._ort.probe_model", _fail)
        result = _check_ort(tmp_path, refresh=True)
        assert result["status"] == "fail"

    def test_ort_invalid_evidence(self, tmp_path: Path) -> None:
        model = tmp_path / "models" / "subconscious_controller.onnx"
        model.parent.mkdir(parents=True, exist_ok=True)
        model.write_text("dummy")
        evidence = tmp_path / "EVIDENCE" / "0017-wp005-s1-ort-probe.json"
        evidence.parent.mkdir(parents=True, exist_ok=True)
        evidence.write_text("not json", encoding="utf-8")
        result = _check_ort(tmp_path, evidence_path=evidence)
        assert result["status"] == "fail"

    def test_wheel_matrix_missing_cargo(self, tmp_path: Path) -> None:
        release = tmp_path / ".github" / "workflows" / "release.yml"
        release.parent.mkdir(parents=True, exist_ok=True)
        release.write_text("os: ubuntu-latest\n", encoding="utf-8")
        (tmp_path / "pyproject.toml").write_text("", encoding="utf-8")
        result = _check_wheel_matrix(tmp_path)
        assert result["status"] == "fail"

    def test_wheel_matrix_missing_pyproject(self, tmp_path: Path) -> None:
        release = tmp_path / ".github" / "workflows" / "release.yml"
        release.parent.mkdir(parents=True, exist_ok=True)
        release.write_text("os: ubuntu-latest\n", encoding="utf-8")
        (tmp_path / "crates" / "prin-py").mkdir(parents=True, exist_ok=True)
        (tmp_path / "crates" / "prin-py" / "Cargo.toml").write_text(
            "", encoding="utf-8"
        )
        result = _check_wheel_matrix(tmp_path)
        assert result["status"] == "fail"

    def test_wheel_matrix_missing_universal(self, tmp_path: Path) -> None:
        release = tmp_path / ".github" / "workflows" / "release.yml"
        release.parent.mkdir(parents=True, exist_ok=True)
        release.write_text(
            "      matrix:\n"
            "        include:\n"
            "          - os: ubuntu-latest\n"
            "            target: x86_64\n"
            "          - os: windows-latest\n"
            "            target: x86_64\n"
            "          - os: macos-latest\n"
            "            target: x86_64\n"
            "      - name: Wheel smoke test\n"
            "        run: |\n"
            "          pip install dist/*.whl\n",
            encoding="utf-8",
        )
        (tmp_path / "crates" / "prin-py").mkdir(parents=True, exist_ok=True)
        (tmp_path / "crates" / "prin-py" / "Cargo.toml").write_text(
            "abi3-py311", encoding="utf-8"
        )
        (tmp_path / "pyproject.toml").write_text(
            "Operating System :: OS Independent", encoding="utf-8"
        )
        result = _check_wheel_matrix(tmp_path)
        assert result["status"] == "fail"
        assert "macOS universal2" in result["errors"][0]

    def test_wheel_matrix_missing_smoke(self, tmp_path: Path) -> None:
        release = tmp_path / ".github" / "workflows" / "release.yml"
        release.parent.mkdir(parents=True, exist_ok=True)
        release.write_text(
            "      matrix:\n"
            "        include:\n"
            "          - os: ubuntu-latest\n"
            "            target: x86_64\n"
            "          - os: windows-latest\n"
            "            target: x86_64\n"
            "          - os: macos-latest\n"
            "            target: universal2-apple-darwin\n",
            encoding="utf-8",
        )
        (tmp_path / "crates" / "prin-py").mkdir(parents=True, exist_ok=True)
        (tmp_path / "crates" / "prin-py" / "Cargo.toml").write_text(
            "abi3-py311", encoding="utf-8"
        )
        (tmp_path / "pyproject.toml").write_text(
            "Operating System :: OS Independent", encoding="utf-8"
        )
        result = _check_wheel_matrix(tmp_path)
        assert result["status"] == "fail"

    def test_wheel_matrix_missing_abi3(self, tmp_path: Path) -> None:
        release = tmp_path / ".github" / "workflows" / "release.yml"
        release.parent.mkdir(parents=True, exist_ok=True)
        release.write_text(
            "      matrix:\n"
            "        include:\n"
            "          - os: ubuntu-latest\n"
            "            target: x86_64\n"
            "          - os: windows-latest\n"
            "            target: x86_64\n"
            "          - os: macos-latest\n"
            "            target: universal2-apple-darwin\n"
            "      - name: Wheel smoke test\n"
            "        run: |\n"
            "          pip install dist/*.whl\n",
            encoding="utf-8",
        )
        (tmp_path / "crates" / "prin-py").mkdir(parents=True, exist_ok=True)
        (tmp_path / "crates" / "prin-py" / "Cargo.toml").write_text(
            "", encoding="utf-8"
        )
        (tmp_path / "pyproject.toml").write_text(
            "Operating System :: OS Independent", encoding="utf-8"
        )
        result = _check_wheel_matrix(tmp_path)
        assert result["status"] == "fail"

    def test_wheel_matrix_missing_classifier(self, tmp_path: Path) -> None:
        release = tmp_path / ".github" / "workflows" / "release.yml"
        release.parent.mkdir(parents=True, exist_ok=True)
        release.write_text(
            "      matrix:\n"
            "        include:\n"
            "          - os: ubuntu-latest\n"
            "            target: x86_64\n"
            "          - os: windows-latest\n"
            "            target: x86_64\n"
            "          - os: macos-latest\n"
            "            target: universal2-apple-darwin\n"
            "      - name: Wheel smoke test\n"
            "        run: |\n"
            "          pip install dist/*.whl\n",
            encoding="utf-8",
        )
        (tmp_path / "crates" / "prin-py").mkdir(parents=True, exist_ok=True)
        (tmp_path / "crates" / "prin-py" / "Cargo.toml").write_text(
            "abi3-py311", encoding="utf-8"
        )
        (tmp_path / "pyproject.toml").write_text("", encoding="utf-8")
        result = _check_wheel_matrix(tmp_path)
        assert result["status"] == "fail"

    def test_spike_decisions_missing_plan(self, tmp_path: Path) -> None:
        result = _check_spike_decisions(tmp_path)
        assert result["status"] == "fail"

    def test_wheel_matrix_missing_release_yml(self, tmp_path: Path) -> None:
        result = _check_wheel_matrix(tmp_path)
        assert result["status"] == "fail"
        assert "release.yml missing" in result["error"]

    def test_wheel_matrix_missing_os_with_files_present(self, tmp_path: Path) -> None:
        workflows = tmp_path / ".github" / "workflows"
        workflows.mkdir(parents=True, exist_ok=True)
        (workflows / "release.yml").write_text(
            "      matrix:\n"
            "        include:\n"
            "          - os: ubuntu-latest\n"
            "            target: x86_64\n"
            "          - os: windows-latest\n"
            "            target: x86_64\n"
            "      - name: Wheel smoke test\n"
            "        run: |\n"
            "          pip install dist/*.whl\n",
            encoding="utf-8",
        )
        (tmp_path / "crates" / "prin-py").mkdir(parents=True, exist_ok=True)
        (tmp_path / "crates" / "prin-py" / "Cargo.toml").write_text(
            "abi3-py311", encoding="utf-8"
        )
        (tmp_path / "pyproject.toml").write_text(
            "Operating System :: OS Independent", encoding="utf-8"
        )
        result = _check_wheel_matrix(tmp_path)
        assert result["status"] == "fail"


def test_phase0_gate_integration_with_ort() -> None:
    """Run the real Phase 0 gate, refreshing ORT evidence if onnxruntime is present."""
    pytest.importorskip("onnxruntime")
    report = phase0_gate_report(refresh_ort=True)
    assert report.ready is True
