"""Tests for subconscious controller state, backend selection, and validation.

These exercise the Rust-backed layer through ``prin._prin_core`` and the thin
Python orchestration in ``prin.daemon``. Nothing here needs ONNX Runtime: the
provider list is injected, so the selection policy and its fallback ladder are
tested for every provider combination including the ones this host does not
have.
"""

from __future__ import annotations

import hashlib
import json
import logging
from pathlib import Path

import numpy as np
import pytest
from prin.daemon import (
    CONTROL_DIM,
    CONTROLLER_INPUT_NAME,
    CONTROLLER_OUTPUT_NAME,
    DEFAULT_NPU_CACHE_KEY,
    DEFAULT_NPU_TARGET,
    DEFAULT_NPU_XCLBIN,
    ENV_BACKEND,
    ENV_MODEL_PATH,
    MODEL_MANIFEST_FILE_NAME,
    STATE_DIM,
    ControlSignals,
    SubconsciousController,
    SubconsciousState,
    backend_info,
    backend_priority,
    backend_provider_names,
    backend_provider_options,
    default_model_path,
    default_models_dir,
    detect_best_backend,
    directml_available,
    inspect_onnx_model,
    model_sha256,
    npu_available,
    npu_firmware_candidates,
    resolve_npu_firmware,
    select_backend,
    validate_controller_model,
    verify_model_artefacts,
)

VITISAI = "VitisAIExecutionProvider"
DIRECTML = "DmlExecutionProvider"
CPU = "CPUExecutionProvider"
ALL_PROVIDERS = [VITISAI, DIRECTML, CPU]


class TestConstants:
    def test_dimensions_match_the_reference(self):
        assert STATE_DIM == 32
        assert CONTROL_DIM == 8

    def test_graph_io_names_match_the_reference_export(self):
        assert CONTROLLER_INPUT_NAME == "state_vector"
        assert CONTROLLER_OUTPUT_NAME == "control_signals"

    def test_npu_defaults_match_the_ryzen_ai_sdk(self):
        assert DEFAULT_NPU_TARGET == "X1"
        assert DEFAULT_NPU_CACHE_KEY == "subconscious_v1"
        assert DEFAULT_NPU_XCLBIN == "1x4.xclbin"

    def test_backend_priority_is_npu_directml_cpu(self):
        assert backend_priority() == ["npu", "directml", "cpu"]


class TestSubconsciousState:
    def test_defaults_match_the_reference_dataclass(self):
        state = SubconsciousState()
        assert state.r_per_band == [0.0, 0.0, 0.0]
        assert state.lr_current == pytest.approx(1e-3)
        assert state.scalr_alpha == 1.0
        assert state.epoch == 0
        assert state.regime == "mean_field"
        assert state.timestamp == 0.0

    def test_to_tensor_shape_and_dtype(self):
        vector = SubconsciousState().to_tensor()
        assert vector.shape == (STATE_DIM,)
        assert vector.dtype == np.float32

    def test_fields_are_mutable(self):
        state = SubconsciousState()
        state.r_global = 0.75
        state.epoch = 42
        state.regime = "full"
        state.timestamp = 86400.0
        state.r_per_band = [0.1, 0.2, 0.3]
        assert state.r_global == 0.75
        assert state.epoch == 42
        assert state.regime == "full"
        assert state.to_tensor()[17] == pytest.approx(1.0)

    def test_unknown_regime_falls_back_to_mean_field(self):
        state = SubconsciousState(regime="chimera")
        assert state.regime == "mean_field"
        assert state.to_tensor()[17] == 0.0

    def test_timestamp_fraction_uses_python_modulo_semantics(self):
        state = SubconsciousState(timestamp=-1.0)
        assert state.timestamp_fraction == pytest.approx(86399.0 / 86400.0)

    def test_short_band_vectors_are_zero_filled(self):
        vector = SubconsciousState(r_per_band=[0.5]).to_tensor()
        assert vector[0] == np.float32(0.5)
        assert vector[1] == 0.0
        assert vector[2] == 0.0

    def test_padding_is_zero(self):
        vector = SubconsciousState(r_global=1.0, throughput=1e6, epoch=9999).to_tensor()
        assert np.all(vector[19:] == 0.0)

    def test_clone_is_independent(self):
        state = SubconsciousState(r_global=0.5)
        copy = state.clone_state()
        copy.r_global = 0.9
        assert state.r_global == 0.5
        assert copy.r_global == 0.9

    def test_repr_is_informative(self):
        assert "SubconsciousState(" in repr(SubconsciousState())


class TestControlSignals:
    def test_defaults_match_the_reference_dataclass(self):
        control = ControlSignals()
        assert control.suggested_K_min == pytest.approx(0.5)
        assert control.suggested_K_max == pytest.approx(5.0)
        assert control.lr_multiplier == pytest.approx(1.0)
        assert control.regime_full_weight == pytest.approx(0.34)
        assert control.is_finite()
        assert control.preferred_regime == "full"

    def test_from_tensor_clamps_like_numpy_clip(self):
        control = ControlSignals.from_tensor(
            np.array([0.25, 9.75, 42.0, 0.2, 0.3, 0.5, 7.5, -3.25])
        )
        assert control.lr_multiplier == pytest.approx(10.0)
        assert control.alert_level == pytest.approx(1.0)
        assert control.coupling_mode_suggestion == pytest.approx(-3.25)

    def test_from_tensor_rejects_short_arrays(self):
        with pytest.raises(ValueError, match="at least 8 elements"):
            ControlSignals.from_tensor(np.zeros(7))

    def test_from_tensor_accepts_extra_elements(self):
        control = ControlSignals.from_tensor(np.arange(12, dtype=np.float64))
        assert control.suggested_K_min == 0.0

    def test_nan_propagates_through_the_clamp(self):
        raw = np.zeros(8)
        raw[6] = np.nan
        control = ControlSignals.from_tensor(raw)
        assert np.isnan(control.alert_level)
        assert not control.is_finite()

    def test_preferred_regime_breaks_ties_towards_mean_field(self):
        control = ControlSignals(
            regime_mf_weight=0.5, regime_sk_weight=0.5, regime_full_weight=0.5
        )
        assert control.preferred_regime == "mean_field"

    def test_to_tensor_round_trip(self):
        control = ControlSignals(suggested_K_min=0.75, alert_level=0.25)
        again = ControlSignals.from_tensor(control.to_tensor().astype(np.float64))
        assert again.suggested_K_min == pytest.approx(0.75)
        assert again.alert_level == pytest.approx(0.25)

    def test_repr_is_informative(self):
        assert "ControlSignals(" in repr(ControlSignals())


class TestBackendSelection:
    def test_auto_detection_prefers_the_npu(self):
        selection = select_backend(ALL_PROVIDERS)
        assert selection.backend == "npu"
        assert selection.reason == "auto_detected"
        assert selection.attempt_order == ["npu", "directml", "cpu"]
        assert not selection.is_degraded
        assert selection.requested is None
        assert selection.available_providers == ALL_PROVIDERS

    def test_auto_detection_falls_back_through_the_priority_order(self):
        assert select_backend([DIRECTML, CPU]).backend == "directml"
        assert select_backend([CPU]).backend == "cpu"

    def test_an_available_request_is_honoured(self):
        selection = select_backend(ALL_PROVIDERS, "cpu")
        assert selection.backend == "cpu"
        assert selection.reason == "requested"
        assert selection.requested == "cpu"
        assert selection.attempt_order == ["cpu"]

    def test_an_unavailable_request_degrades_and_says_so(self):
        selection = select_backend([DIRECTML, CPU], "npu")
        assert selection.backend == "directml"
        assert selection.reason == "requested_unavailable"
        assert selection.is_degraded
        assert selection.attempt_order == ["directml", "cpu"]

    def test_unknown_providers_are_ignored(self):
        selection = select_backend(["TensorrtExecutionProvider", CPU])
        assert selection.backend == "cpu"

    def test_no_supported_provider_raises(self):
        with pytest.raises(ValueError, match="no supported execution provider"):
            select_backend([])

    def test_unknown_requested_backend_raises(self):
        with pytest.raises(ValueError, match="unknown backend"):
            select_backend(ALL_PROVIDERS, "tpu")

    def test_ladder_is_cpu_terminated_for_every_subset(self):
        subsets = [
            [VITISAI, DIRECTML, CPU],
            [VITISAI, CPU],
            [DIRECTML, CPU],
            [CPU],
        ]
        for providers in subsets:
            assert select_backend(providers).attempt_order[-1] == "cpu"

    def test_detect_best_backend_matches_selection(self):
        assert detect_best_backend(ALL_PROVIDERS) == "npu"
        assert detect_best_backend([DIRECTML, CPU]) == "directml"
        assert detect_best_backend([CPU]) == "cpu"

    def test_environment_override_is_honoured(self, monkeypatch):
        monkeypatch.setenv(ENV_BACKEND, "cpu")
        assert detect_best_backend(ALL_PROVIDERS) == "cpu"

    def test_environment_override_is_case_and_space_insensitive(self, monkeypatch):
        monkeypatch.setenv(ENV_BACKEND, "  CPU  ")
        assert detect_best_backend(ALL_PROVIDERS) == "cpu"

    def test_invalid_environment_override_is_logged_and_ignored(
        self, monkeypatch, caplog
    ):
        monkeypatch.setenv(ENV_BACKEND, "quantum")
        with caplog.at_level(logging.WARNING, logger="prin.daemon"):
            assert detect_best_backend(ALL_PROVIDERS) == "npu"
        assert "unrecognised" in caplog.text

    def test_explicit_request_wins_over_the_environment(self, monkeypatch):
        monkeypatch.setenv(ENV_BACKEND, "cpu")
        assert detect_best_backend(ALL_PROVIDERS, "directml") == "directml"

    def test_provider_availability_helpers(self):
        assert npu_available(ALL_PROVIDERS)
        assert directml_available(ALL_PROVIDERS)
        assert not npu_available([CPU])
        assert not directml_available([CPU])


class TestProviderConfiguration:
    def test_accelerator_chains_are_cpu_terminated(self):
        assert backend_provider_names("npu") == [VITISAI, CPU]
        assert backend_provider_names("directml") == [DIRECTML, CPU]
        assert backend_provider_names("cpu") == [CPU]

    def test_unknown_backend_names_raise(self):
        with pytest.raises(ValueError, match="unknown backend"):
            backend_provider_names("tpu")

    def test_non_npu_options_are_empty_and_aligned_with_the_chain(self):
        options = backend_provider_options("directml")
        assert options == [{}, {}]
        assert len(options) == len(backend_provider_names("directml"))

    def test_npu_options_carry_the_vitisai_keys(self, tmp_path):
        firmware = tmp_path / "1x4.xclbin"
        firmware.write_bytes(b"overlay")
        options = backend_provider_options(
            "npu", tmp_path, firmware, tmp_path / "cache", "X2"
        )
        assert len(options) == 2
        assert list(options[0]) == [
            "config_file",
            "xclbin",
            "target",
            "cache_dir",
            "cache_key",
        ]
        assert options[0]["target"] == "X2"
        assert options[0]["cache_key"] == DEFAULT_NPU_CACHE_KEY
        assert options[0]["config_file"].endswith("vaip_config.json")
        assert options[1] == {}

    def test_npu_options_without_a_configuration_raise(self):
        with pytest.raises(ValueError, match="firmware"):
            backend_provider_options("npu")


class TestFirmwareResolution:
    def test_candidates_prefer_a_non_empty_override(self, tmp_path):
        candidates = npu_firmware_candidates("C:/explicit.xclbin", tmp_path)
        assert candidates[0] == "C:/explicit.xclbin"
        assert len(candidates) == 2

    def test_blank_overrides_are_discarded(self, tmp_path):
        assert len(npu_firmware_candidates("   ", tmp_path)) == 1
        assert len(npu_firmware_candidates(None, tmp_path)) == 1

    def test_an_existing_firmware_file_resolves(self, tmp_path):
        firmware = tmp_path / "1x4.xclbin"
        firmware.write_bytes(b"overlay")
        assert Path(resolve_npu_firmware(str(firmware), tmp_path)) == firmware

    def test_missing_firmware_reports_every_probed_path(self, tmp_path):
        with pytest.raises(ValueError, match="NPU firmware not found"):
            resolve_npu_firmware(None, tmp_path / "absent")


class TestModelValidation:
    def test_manifest_verifies_the_committed_artefacts(self):
        records = verify_model_artefacts()
        assert len(records) == 2
        names = {Path(r["path"]).name for r in records}
        assert names == {
            "subconscious_controller.onnx",
            "subconscious_controller.onnx.data",
        }
        for record in records:
            assert len(record["sha256"]) == 64
            assert record["bytes"] > 0

    def test_manifest_digests_match_an_independent_hash(self):
        for record in verify_model_artefacts():
            digest = hashlib.sha256(Path(record["path"]).read_bytes()).hexdigest()
            assert record["sha256"] == digest

    def test_model_sha256_matches_hashlib(self):
        path = default_model_path()
        assert model_sha256(path) == hashlib.sha256(path.read_bytes()).hexdigest()

    def test_manifest_covers_the_files_on_disk(self):
        manifest = json.loads(
            (default_models_dir() / MODEL_MANIFEST_FILE_NAME).read_text()
        )
        assert manifest["schema_version"] == 1
        assert len(manifest["files"]) == 2

    def test_tampered_artefacts_are_detected(self, tmp_path):
        source = default_models_dir()
        (tmp_path / MODEL_MANIFEST_FILE_NAME).write_bytes(
            (source / MODEL_MANIFEST_FILE_NAME).read_bytes()
        )
        (tmp_path / "subconscious_controller.onnx").write_bytes(b"tampered")
        (tmp_path / "subconscious_controller.onnx.data").write_bytes(b"tampered")
        with pytest.raises(ValueError, match="SHA-256 mismatch"):
            verify_model_artefacts(tmp_path)

    def test_missing_artefacts_raise_oserror(self, tmp_path):
        source = default_models_dir()
        (tmp_path / MODEL_MANIFEST_FILE_NAME).write_bytes(
            (source / MODEL_MANIFEST_FILE_NAME).read_bytes()
        )
        with pytest.raises(OSError, match="subconscious_controller"):
            verify_model_artefacts(tmp_path)

    def test_graph_metadata_matches_the_reference_export(self):
        info = inspect_onnx_model(default_model_path())
        assert info["ir_version"] == 10
        assert info["default_opset"] == 18
        assert info["producer_name"] == "pytorch"
        assert info["graph_name"] == "main_graph"
        assert info["op_types"].count("Gemm") == 3
        assert "Softmax" in info["op_types"]
        assert info["external_data_files"] == ["subconscious_controller.onnx.data"]

    def test_graph_contract_shapes_match_the_state_and_control_dims(self):
        info = inspect_onnx_model(default_model_path())
        assert len(info["inputs"]) == 1
        assert info["inputs"][0]["name"] == CONTROLLER_INPUT_NAME
        assert info["inputs"][0]["shape"] == ["batch", STATE_DIM]
        assert len(info["outputs"]) == 1
        assert info["outputs"][0]["name"] == CONTROLLER_OUTPUT_NAME
        assert info["outputs"][0]["shape"] == ["batch", CONTROL_DIM]

    def test_full_validation_returns_digest_companions_and_info(self):
        report = validate_controller_model(default_model_path())
        assert len(report["sha256"]) == 64
        assert len(report["external_data"]) == 1
        assert report["info"]["graph_name"] == "main_graph"

    def test_full_validation_rejects_a_wrong_digest(self):
        with pytest.raises(ValueError, match="SHA-256 mismatch"):
            validate_controller_model(default_model_path(), "0" * 64)

    def test_full_validation_rejects_a_malformed_digest(self):
        with pytest.raises(ValueError, match="invalid SHA-256 digest"):
            validate_controller_model(default_model_path(), "not-a-digest")

    def test_non_onnx_files_are_rejected(self, tmp_path):
        bogus = tmp_path / "bogus.onnx"
        bogus.write_bytes(b"\xff\xfe\x00not protobuf")
        with pytest.raises(ValueError, match="ONNX"):
            validate_controller_model(bogus)

    def test_missing_external_data_is_detected(self, tmp_path):
        orphan = tmp_path / "subconscious_controller.onnx"
        orphan.write_bytes(default_model_path().read_bytes())
        with pytest.raises(ValueError, match="external data"):
            validate_controller_model(orphan)

    def test_missing_model_raises_oserror(self, tmp_path):
        with pytest.raises(OSError, match=r"absent\.onnx"):
            validate_controller_model(tmp_path / "absent.onnx")


class TestModelPathResolution:
    def test_default_path_points_at_the_committed_model(self):
        assert default_model_path().is_file()
        assert default_model_path().parent == default_models_dir()

    def test_environment_override_is_honoured(self, monkeypatch, tmp_path):
        target = tmp_path / "other.onnx"
        monkeypatch.setenv(ENV_MODEL_PATH, str(target))
        assert default_model_path() == target

    def test_blank_environment_override_is_ignored(self, monkeypatch):
        monkeypatch.setenv(ENV_MODEL_PATH, "   ")
        assert default_model_path().name == "subconscious_controller.onnx"


class TestBackendInfo:
    def test_report_has_the_documented_keys(self):
        info = backend_info()
        expected = {
            "ort_available",
            "ort_version",
            "available_providers",
            "best_backend",
            "selection_reason",
            "attempt_order",
            "npu_available",
            "directml_available",
            "npu_firmware_found",
            "npu_firmware_path",
            "npu_firmware_candidates",
            "sdk_install_dir",
            "npu_target",
            "cache_dir",
        }
        assert set(info) == expected

    def test_report_is_json_serialisable(self):
        json.dumps(backend_info())

    def test_report_is_internally_consistent(self):
        info = backend_info()
        if info["best_backend"] is not None:
            assert info["best_backend"] in backend_priority()
            assert info["attempt_order"][0] == info["best_backend"]
            assert info["attempt_order"][-1] in backend_priority()
        assert info["npu_available"] == (
            "VitisAIExecutionProvider" in info["available_providers"]
        )

    def test_report_survives_ort_being_absent(self, monkeypatch):
        import prin.daemon as daemon

        def _missing():
            raise daemon.OrtUnavailableError("simulated")

        monkeypatch.setattr(daemon, "_import_ort", _missing)
        info = daemon.backend_info()
        assert info["ort_available"] is False
        assert info["ort_version"] is None
        assert info["available_providers"] == []
        assert info["best_backend"] is None
        assert info["attempt_order"] == []


class TestOrtUnavailable:
    def test_available_providers_is_empty_without_ort(self, monkeypatch):
        import prin.daemon as daemon

        def _missing():
            raise daemon.OrtUnavailableError("simulated")

        monkeypatch.setattr(daemon, "_import_ort", _missing)
        assert daemon.available_providers() == []

    def test_create_session_raises_without_ort(self, monkeypatch):
        import prin.daemon as daemon

        def _missing():
            raise daemon.OrtUnavailableError("simulated")

        monkeypatch.setattr(daemon, "_import_ort", _missing)
        with pytest.raises(daemon.OrtUnavailableError):
            daemon.create_session(default_model_path())

    def test_controller_raises_without_ort(self, monkeypatch):
        import prin.daemon as daemon

        def _missing():
            raise daemon.OrtUnavailableError("simulated")

        monkeypatch.setattr(daemon, "_import_ort", _missing)
        with pytest.raises(daemon.OrtUnavailableError):
            SubconsciousController()

    def test_create_session_rejects_a_missing_model(self, tmp_path):
        with pytest.raises(FileNotFoundError):
            from prin.daemon import create_session

            create_session(tmp_path / "absent.onnx")


class TestNpuProviderConfiguration:
    """The VitisAI path, exercised without an NPU by staging the SDK layout."""

    @staticmethod
    def _stage_sdk(tmp_path, monkeypatch):
        import prin.daemon as daemon

        firmware = tmp_path / "1x4.xclbin"
        firmware.write_bytes(b"overlay")
        monkeypatch.setenv(daemon.ENV_SDK_ROOT, str(tmp_path))
        monkeypatch.setenv(daemon.ENV_FIRMWARE, str(firmware))
        monkeypatch.setenv("LOCALAPPDATA", str(tmp_path / "appdata"))
        return firmware

    def test_vitisai_options_are_built_from_the_environment(
        self, tmp_path, monkeypatch
    ):
        import prin.daemon as daemon

        firmware = self._stage_sdk(tmp_path, monkeypatch)
        monkeypatch.setenv(daemon.ENV_NPU_TARGET, "X2")
        options = daemon._vitisai_options()
        assert len(options) == 2
        assert options[0]["xclbin"] == str(firmware)
        assert options[0]["target"] == "X2"
        assert options[0]["cache_key"] == DEFAULT_NPU_CACHE_KEY
        assert options[1] == {}
        # The compilation-cache directory is created eagerly.
        assert (tmp_path / "appdata" / "prin" / "vitisai_cache").is_dir()

    def test_npu_target_defaults_when_the_environment_is_blank(
        self, tmp_path, monkeypatch
    ):
        import prin.daemon as daemon

        self._stage_sdk(tmp_path, monkeypatch)
        monkeypatch.setenv(daemon.ENV_NPU_TARGET, "   ")
        assert daemon._vitisai_options()[0]["target"] == DEFAULT_NPU_TARGET

    def test_provider_config_routes_npu_through_the_vitisai_builder(
        self, tmp_path, monkeypatch
    ):
        import prin.daemon as daemon

        self._stage_sdk(tmp_path, monkeypatch)
        providers, options = daemon._provider_config("npu")
        assert providers == [VITISAI, CPU]
        assert options[0]["cache_key"] == DEFAULT_NPU_CACHE_KEY

    def test_provider_config_leaves_other_backends_optionless(self):
        import prin.daemon as daemon

        providers, options = daemon._provider_config("cpu")
        assert providers == [CPU]
        assert options == [{}]

    def test_missing_firmware_makes_the_npu_path_raise(self, tmp_path, monkeypatch):
        import prin.daemon as daemon

        monkeypatch.setenv(daemon.ENV_SDK_ROOT, str(tmp_path / "absent"))
        monkeypatch.delenv(daemon.ENV_FIRMWARE, raising=False)
        with pytest.raises(ValueError, match="NPU firmware not found"):
            daemon._provider_config("npu")

    def test_backend_info_reports_absent_firmware_as_none(self, tmp_path, monkeypatch):
        import prin.daemon as daemon

        monkeypatch.setenv(daemon.ENV_SDK_ROOT, str(tmp_path / "absent"))
        monkeypatch.setenv(daemon.ENV_FIRMWARE, str(tmp_path / "absent.xclbin"))
        info = daemon.backend_info()
        assert info["npu_firmware_found"] is False
        assert info["npu_firmware_path"] is None
        assert len(info["npu_firmware_candidates"]) == 2

    def test_sdk_root_falls_back_to_the_documented_default(self, monkeypatch):
        import prin.daemon as daemon

        monkeypatch.setenv(daemon.ENV_SDK_ROOT, "   ")
        assert str(daemon._sdk_root()) == daemon.DEFAULT_SDK_ROOT

    def test_cache_dir_falls_back_to_the_home_directory(self, monkeypatch):
        import prin.daemon as daemon

        monkeypatch.setenv("LOCALAPPDATA", "")
        assert daemon._npu_cache_dir().parts[-2:] == ("prin", "vitisai_cache")


class TestOrtImportFailure:
    def test_a_missing_onnxruntime_raises_a_helpful_error(self, monkeypatch):
        import prin.daemon as daemon

        def _no_module(name):
            raise ModuleNotFoundError(name)

        monkeypatch.setattr(daemon.importlib, "import_module", _no_module)
        with pytest.raises(daemon.OrtUnavailableError, match="onnx"):
            daemon._import_ort()


class TestSessionCreationFailure:
    def test_exhausting_the_ladder_raises_with_every_failure_listed(self, monkeypatch):
        import prin.daemon as daemon

        def _always_fails(backend):
            raise RuntimeError(f"simulated {backend} failure")

        monkeypatch.setattr(daemon, "_provider_config", _always_fails)
        with pytest.raises(RuntimeError, match="could not create an ONNX Runtime"):
            daemon.create_session(default_model_path())


class TestManifestDigestLookup:
    def test_a_model_without_a_manifest_skips_the_digest_check(self, tmp_path):
        import prin.daemon as daemon

        model = tmp_path / "subconscious_controller.onnx"
        model.write_bytes(b"stub")
        assert daemon._manifest_digest(model) is None

    def test_a_manifest_that_does_not_cover_the_model_returns_none(self, tmp_path):
        import prin.daemon as daemon

        source = default_models_dir()
        for name in (
            MODEL_MANIFEST_FILE_NAME,
            "subconscious_controller.onnx",
            "subconscious_controller.onnx.data",
        ):
            (tmp_path / name).write_bytes((source / name).read_bytes())
        (tmp_path / "other.onnx").write_bytes(b"stub")
        assert daemon._manifest_digest(tmp_path / "other.onnx") is None

    def test_a_failing_manifest_is_logged_and_re_raised(self, tmp_path, caplog):
        import prin.daemon as daemon

        source = default_models_dir()
        (tmp_path / MODEL_MANIFEST_FILE_NAME).write_bytes(
            (source / MODEL_MANIFEST_FILE_NAME).read_bytes()
        )
        model = tmp_path / "subconscious_controller.onnx"
        model.write_bytes(b"tampered")
        (tmp_path / "subconscious_controller.onnx.data").write_bytes(b"tampered")
        with caplog.at_level(logging.WARNING, logger="prin.daemon"):
            with pytest.raises(ValueError, match="SHA-256 mismatch"):
                daemon._manifest_digest(model)
        assert "manifest verification failed" in caplog.text

    def test_the_committed_model_resolves_its_manifest_digest(self):
        import prin.daemon as daemon

        digest = daemon._manifest_digest(default_model_path())
        assert digest == model_sha256(default_model_path())
