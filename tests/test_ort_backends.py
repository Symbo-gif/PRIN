"""Tests for the ONNX Runtime provider probe (WP-005)."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import numpy as np
import pytest
from prin._ort import (
    OrtProbeError,
    OrtProbeReport,
    available_providers,
    build_provider_list,
    probe_model,
    select_best_backend,
    try_create_session,
)


class _FakeTensorInfo:
    def __init__(self, name: str, shape: list[Any], type_: str) -> None:
        self.name = name
        self.shape = shape
        self.type = type_


class _FakeSession:
    def __init__(
        self,
        model_path: str,
        providers: list[str] | None = None,
        provider_options: list[dict[str, Any]] | None = None,
        sess_options: Any = None,
    ) -> None:
        providers = providers or ["CPUExecutionProvider"]
        if providers and providers[0] == "DmlExecutionProvider":
            raise RuntimeError("simulated DirectML graph failure")
        self._providers = providers
        self._inputs = [_FakeTensorInfo("state_vector", ["batch", 32], "tensor(float)")]
        self._outputs = [
            _FakeTensorInfo("control_signals", ["batch", 8], "tensor(float)")
        ]

    def get_inputs(self) -> list[_FakeTensorInfo]:
        return self._inputs

    def get_outputs(self) -> list[_FakeTensorInfo]:
        return self._outputs

    def get_providers(self) -> list[str]:
        return [p for p in self._providers if p != "VitisAIExecutionProvider"]

    def run(self, output_names: Any, feed: dict[str, Any]) -> list[np.ndarray]:
        return [np.zeros((1, 8), dtype=np.float32)]


class _FakeOrt:
    def __init__(self, available: list[str]) -> None:
        self._available = available
        self.InferenceSession = _FakeSession

    def get_available_providers(self) -> list[str]:
        return self._available


def _fake_import_ort(available: list[str]) -> Any:
    return _FakeOrt(available)


class TestAvailableProviders:
    def test_returns_empty_when_ort_missing(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        def _raise() -> Any:
            raise OrtProbeError("missing")

        monkeypatch.setattr("prin._ort._import_ort", _raise)
        assert available_providers() == []

    def test_returns_providers_when_ort_present(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.setattr(
            "prin._ort._import_ort", lambda: _fake_import_ort(["CPUExecutionProvider"])
        )
        assert available_providers() == ["CPUExecutionProvider"]


class TestSelectBestBackend:
    @pytest.mark.parametrize(
        ("providers", "expected"),
        [
            (
                [
                    "VitisAIExecutionProvider",
                    "DmlExecutionProvider",
                    "CPUExecutionProvider",
                ],
                "npu",
            ),
            (["DmlExecutionProvider", "CPUExecutionProvider"], "directml"),
            (["CPUExecutionProvider"], "cpu"),
        ],
    )
    def test_priority_selection(self, providers: list[str], expected: str) -> None:
        assert select_best_backend(providers) == expected

    def test_override_selects_when_available(self) -> None:
        providers = ["DmlExecutionProvider", "CPUExecutionProvider"]
        assert select_best_backend(providers, override="directml") == "directml"

    def test_override_falls_back_when_unavailable(self) -> None:
        providers = ["CPUExecutionProvider"]
        assert select_best_backend(providers, override="directml") == "cpu"

    def test_env_override(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setenv("PRIN_SUBCONSCIOUS_BACKEND", "npu")
        providers = ["VitisAIExecutionProvider", "CPUExecutionProvider"]
        assert select_best_backend(providers) == "npu"

    def test_raises_when_no_provider_matches(self) -> None:
        with pytest.raises(OrtProbeError):
            select_best_backend(["AzureExecutionProvider"])


class TestBuildProviderList:
    def test_cpu(self) -> None:
        providers, options = build_provider_list("cpu")
        assert providers == ["CPUExecutionProvider"]
        assert options == [{}]

    def test_directml(self) -> None:
        providers, options = build_provider_list("directml")
        assert providers == ["DmlExecutionProvider", "CPUExecutionProvider"]
        assert options == [{}, {}]

    def test_npu(self, monkeypatch: pytest.MonkeyPatch) -> None:
        def _fake_firmware() -> Path:
            return Path("/fake/firmware.xclbin")

        monkeypatch.setattr("prin._ort._resolve_firmware_path", _fake_firmware)
        monkeypatch.setattr("prin._ort._CACHE_DIR", Path("/fake/cache"))
        providers, options = build_provider_list("npu")
        assert providers == ["VitisAIExecutionProvider", "CPUExecutionProvider"]
        assert Path(options[0]["xclbin"]).name == "firmware.xclbin"
        assert options[0]["target"] == "X1"
        assert options[1] == {}

    def test_npu_raises_without_firmware(self, monkeypatch: pytest.MonkeyPatch) -> None:
        def _raise() -> Path:
            raise FileNotFoundError("simulated missing firmware")

        monkeypatch.setattr("prin._ort._resolve_firmware_path", _raise)
        with pytest.raises(FileNotFoundError):
            build_provider_list("npu")


class TestTryCreateSession:
    def test_creates_session_and_reports_active_providers(
        self, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
    ) -> None:
        model = tmp_path / "dummy.onnx"
        model.write_text("")
        monkeypatch.setattr(
            "prin._ort._import_ort",
            lambda: _fake_import_ort(["CPUExecutionProvider"]),
        )
        session, active = try_create_session(model)
        assert active == ["CPUExecutionProvider"]
        assert session.get_inputs()[0].name == "state_vector"

    def test_falls_back_to_cpu_on_preferred_failure(
        self, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
    ) -> None:
        model = tmp_path / "dummy.onnx"
        model.write_text("")
        monkeypatch.setattr(
            "prin._ort._import_ort",
            lambda: _fake_import_ort(["DmlExecutionProvider", "CPUExecutionProvider"]),
        )
        _session, active = try_create_session(model)
        assert "CPUExecutionProvider" in active

    def test_raises_for_missing_model(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setattr(
            "prin._ort._import_ort",
            lambda: _fake_import_ort(["CPUExecutionProvider"]),
        )
        with pytest.raises(FileNotFoundError):
            try_create_session("/nonexistent/model.onnx")


class TestProbeModel:
    def test_probe_with_fake_ort(
        self, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
    ) -> None:
        model = tmp_path / "dummy.onnx"
        model.write_text("onnx")
        monkeypatch.setattr(
            "prin._ort._import_ort",
            lambda: _fake_import_ort(["DmlExecutionProvider", "CPUExecutionProvider"]),
        )
        report = probe_model(model)
        assert isinstance(report, OrtProbeReport)
        assert report.can_run
        assert report.output_shape == (1, 8)
        assert "CPUExecutionProvider" in report.active_providers
        assert report.error is None

    def test_probe_reports_error_when_no_providers(
        self, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
    ) -> None:
        model = tmp_path / "dummy.onnx"
        model.write_text("onnx")
        monkeypatch.setattr("prin._ort._import_ort", lambda: _fake_import_ort([]))
        report = probe_model(model)
        assert not report.can_run
        assert report.error is not None

    def test_probe_report_to_dict(self, tmp_path: Path) -> None:
        model = tmp_path / "dummy.onnx"
        model.write_text("onnx")
        report = probe_model(model)
        d = report.to_dict()
        assert d["model_path"] == report.model_path
        assert d["can_run"] == report.can_run
        assert "output_shape" in d

    def test_probe_raises_for_missing_model(self) -> None:
        with pytest.raises(FileNotFoundError):
            probe_model("/nonexistent/model.onnx")


class TestOrtUtilities:
    def test_import_ort_raises_clear_error(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        def _raise(name: str) -> Any:
            raise ModuleNotFoundError("simulated")

        monkeypatch.setattr("prin._ort.importlib.import_module", _raise)
        with pytest.raises(OrtProbeError):
            from prin._ort import _import_ort

            _import_ort()

    def test_resolve_firmware_from_env(
        self, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
    ) -> None:
        fw = tmp_path / "fw.xclbin"
        fw.write_text("fake")
        monkeypatch.setenv("XLNX_VART_FIRMWARE", str(fw))
        from prin._ort import _resolve_firmware_path

        assert _resolve_firmware_path() == fw.resolve()

    def test_resolve_firmware_default_path(
        self, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
    ) -> None:
        monkeypatch.delenv("XLNX_VART_FIRMWARE", raising=False)
        default_dir = tmp_path / "xclbins" / "phoenix"
        default_dir.mkdir(parents=True, exist_ok=True)
        fw = default_dir / "1x4.xclbin"
        fw.write_text("fake")
        from prin._ort import _resolve_firmware_path

        assert _resolve_firmware_path(xclbin_dir=default_dir) == fw.resolve()

    def test_resolve_firmware_missing(
        self, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
    ) -> None:
        monkeypatch.delenv("XLNX_VART_FIRMWARE", raising=False)
        from prin._ort import _resolve_firmware_path

        with pytest.raises(FileNotFoundError):
            _resolve_firmware_path(xclbin_dir=tmp_path / "missing")

    def test_np_dtype_for_ort_type(self) -> None:
        from prin._ort import _np_dtype_for_ort_type

        assert _np_dtype_for_ort_type("tensor(float)") == "float32"
        assert _np_dtype_for_ort_type("tensor(double)") == "float64"
        assert _np_dtype_for_ort_type("tensor(int64)") == "int64"
        assert _np_dtype_for_ort_type("tensor(bfloat16)") == "float32"


class TestTryCreateSessionErrors:
    def test_raises_when_no_providers_available(
        self, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
    ) -> None:
        model = tmp_path / "dummy.onnx"
        model.write_text("")
        monkeypatch.setattr("prin._ort._import_ort", lambda: _fake_import_ort([]))
        with pytest.raises(OrtProbeError):
            try_create_session(model)

    def test_raises_when_cpu_fallback_impossible(
        self, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
    ) -> None:
        model = tmp_path / "dummy.onnx"
        model.write_text("")
        monkeypatch.setattr(
            "prin._ort._import_ort",
            lambda: _fake_import_ort(["DmlExecutionProvider"]),
        )
        with pytest.raises(OrtProbeError):
            try_create_session(model)


class _FailingSession:
    def __init__(self, *args: Any, **kwargs: Any) -> None:
        pass

    def get_inputs(self) -> list[Any]:
        return [_FakeTensorInfo("state_vector", ["batch", 32], "tensor(float)")]

    def get_outputs(self) -> list[Any]:
        return [_FakeTensorInfo("control_signals", ["batch", 8], "tensor(float)")]

    def get_providers(self) -> list[str]:
        return ["CPUExecutionProvider"]

    def run(self, output_names: Any, feed: dict[str, Any]) -> list[np.ndarray]:
        raise RuntimeError("inference failure")


class _FailingOrt:
    def __init__(self, available: list[str]) -> None:
        self._available = available
        self.InferenceSession = _FailingSession

    def get_available_providers(self) -> list[str]:
        return self._available


class TestProbeModelErrors:
    def test_probe_catches_unsupported_provider(
        self, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
    ) -> None:
        model = tmp_path / "dummy.onnx"
        model.write_text("onnx")
        monkeypatch.setattr(
            "prin._ort._import_ort",
            lambda: _FailingOrt(["AzureExecutionProvider"]),
        )
        report = probe_model(model)
        assert not report.can_run
        assert report.error is not None

    def test_probe_catches_inference_failure(
        self, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
    ) -> None:
        model = tmp_path / "dummy.onnx"
        model.write_text("onnx")
        monkeypatch.setattr(
            "prin._ort._import_ort", lambda: _FailingOrt(["CPUExecutionProvider"])
        )
        report = probe_model(model)
        assert not report.can_run
        assert "inference failed" in (report.error or "")


def test_available_providers_catches_query_error(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    class _BadOrt:
        def get_available_providers(self) -> list[str]:
            raise RuntimeError("bad provider list")

    monkeypatch.setattr("prin._ort._import_ort", lambda: _BadOrt())
    assert available_providers() == []


def test_probe_real_subconscious_model() -> None:
    """End-to-end probe of the actual subconscious controller model."""
    pytest.importorskip("onnxruntime")
    import onnxruntime as ort

    report = probe_model("models/subconscious_controller.onnx")
    assert report.can_run
    assert report.output_shape == (1, 8)
    assert report.active_providers
    assert "CPUExecutionProvider" in ort.get_available_providers()
