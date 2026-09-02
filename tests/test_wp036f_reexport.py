"""WP-036F S1: the re-exported subconscious controller graph.

Covers ``tools/wp036f_reexport_controller.py`` and
``tools/wp036f_provider_latency.py``, and the two acceptance gates:

* **R3 (mathematical identity).** Adding an explicit zero bias to every ``Gemm``
  node must not change the graph's function — a differential run over a fixed
  48-case set on ``CPUExecutionProvider`` is bit-identical, both against an
  in-memory bias-stripped copy of the committed graph and against the pristine
  PRINet 3.0 graph in the archive.
* **DirectML execution.** ``DmlExecutionProvider`` rejects the pre-transform
  graph (``InvalidGraph``) and executes the re-exported one, agreeing with CPU
  within Testing Standards §3's ``rtol=1e-5, atol=1e-6``.
"""

from __future__ import annotations

import shutil
from pathlib import Path

import numpy as np
import pytest

onnx = pytest.importorskip("onnx")
ort = pytest.importorskip("onnxruntime")

from onnx import numpy_helper  # noqa: E402
from prin.daemon import default_model_path, default_models_dir  # noqa: E402

from tools import wp036f_provider_latency as latency_tool  # noqa: E402
from tools import wp036f_reexport_controller as reexport  # noqa: E402

_PRISTINE = (
    Path(__file__).resolve().parents[1]
    / "DOCS"
    / "archive and reference from PRINet 3.0"
    / "PRINet-3.0.0-main"
    / "models"
    / "subconscious_controller.onnx"
)
_CPU = "CPUExecutionProvider"
_DML = "DmlExecutionProvider"


def _state_batch(cases: int = 48) -> np.ndarray:
    """A deterministic spread of state vectors for the differential runs."""
    rng = np.random.default_rng(20260902)
    return rng.standard_normal((cases, 32)).astype(np.float32)


def _run(model_path: Path, providers: list[str], batch: np.ndarray) -> np.ndarray:
    opts = ort.SessionOptions()
    opts.graph_optimization_level = ort.GraphOptimizationLevel.ORT_ENABLE_ALL
    session = ort.InferenceSession(
        str(model_path), sess_options=opts, providers=providers
    )
    return np.asarray(session.run(None, {"state_vector": batch})[0])


def _strip_gemm_bias(model: onnx.ModelProto) -> onnx.ModelProto:
    """Return a copy of ``model`` with every three-input ``Gemm`` bias removed."""
    out = onnx.ModelProto()
    out.CopyFrom(model)
    bias_names = set()
    for node in out.graph.node:
        if node.op_type == "Gemm" and len(node.input) == 3:
            bias_names.add(node.input[2])
            del node.input[2]
    keep = [t for t in out.graph.initializer if t.name not in bias_names]
    del out.graph.initializer[:]
    out.graph.initializer.extend(keep)
    return out


@pytest.fixture(scope="module")
def committed_model() -> onnx.ModelProto:
    """The committed controller graph, external data left on disk."""
    return onnx.load(default_model_path(), load_external_data=False)


class TestCommittedArtefact:
    def test_every_gemm_has_a_three_input_form(self, committed_model):
        arities = [
            len(n.input) for n in committed_model.graph.node if n.op_type == "Gemm"
        ]
        assert arities == [3, 3, 3]

    def test_each_added_bias_is_inline_float32_zero(self, committed_model):
        inits = {t.name: t for t in committed_model.graph.initializer}
        for node in committed_model.graph.node:
            if node.op_type != "Gemm":
                continue
            bias = inits[node.input[2]]
            values = numpy_helper.to_array(bias)
            assert bias.name.endswith(".bias")
            assert values.dtype == np.float32
            assert np.all(values == 0.0)

    def test_io_contract_is_unchanged(self, committed_model):
        assert [i.name for i in committed_model.graph.input] == ["state_vector"]
        assert [o.name for o in committed_model.graph.output] == ["control_signals"]

    def test_external_data_companion_is_untouched(self):
        # The bias tensors are inline; the weight companion keeps its digest.
        manifest = default_models_dir() / "manifest.json"
        text = manifest.read_text(encoding="utf-8")
        assert (
            "35e7eb0985180e928baca8ef08be8ae8d2257e15f9f7c3720c672bb7696d2597" in text
        )

    def test_check_mode_passes_on_the_committed_artefact(self):
        assert reexport.main(["--check"]) == 0

    def test_manifest_digest_matches_the_file(self):
        import hashlib
        import json

        manifest = json.loads(
            (default_models_dir() / "manifest.json").read_text(encoding="utf-8")
        )
        for entry in manifest["files"]:
            artefact = default_models_dir() / entry["path"]
            assert entry["bytes"] == artefact.stat().st_size
            assert entry["sha256"] == hashlib.sha256(artefact.read_bytes()).hexdigest()


class TestTransformFunction:
    def test_transform_is_idempotent_on_the_committed_graph(self, committed_model):
        _, added = reexport.transform_graph(committed_model)
        assert added == []

    def test_transform_adds_three_biases_to_a_stripped_graph(self, committed_model):
        stripped = _strip_gemm_bias(committed_model)
        rebuilt, added = reexport.transform_graph(stripped)
        assert added == ["net.0.bias", "net.3.bias", "net.6.bias"]
        arities = [len(n.input) for n in rebuilt.graph.node if n.op_type == "Gemm"]
        assert arities == [3, 3, 3]

    def test_bias_name_derivation(self):
        assert reexport._bias_name("net.0.weight") == "net.0.bias"
        assert reexport._bias_name("dense") == "dense.bias"

    def test_transform_rejects_a_bad_gemm_arity(self):
        model = onnx.helper.make_model(
            onnx.helper.make_graph(
                [onnx.helper.make_node("Gemm", ["a"], ["y"], name="bad")],
                "g",
                [
                    onnx.helper.make_tensor_value_info(
                        "a", onnx.TensorProto.FLOAT, [1, 2]
                    )
                ],
                [
                    onnx.helper.make_tensor_value_info(
                        "y", onnx.TensorProto.FLOAT, [1, 2]
                    )
                ],
            )
        )
        with pytest.raises(ValueError, match="has 1 inputs"):
            reexport.transform_graph(model)

    def test_transform_rejects_a_non_initializer_weight(self):
        node = onnx.helper.make_node("Gemm", ["a", "w"], ["y"], name="g0")
        model = onnx.helper.make_model(
            onnx.helper.make_graph(
                [node],
                "g",
                [
                    onnx.helper.make_tensor_value_info(
                        "a", onnx.TensorProto.FLOAT, [1, 2]
                    ),
                    onnx.helper.make_tensor_value_info(
                        "w", onnx.TensorProto.FLOAT, [2, 2]
                    ),
                ],
                [
                    onnx.helper.make_tensor_value_info(
                        "y", onnx.TensorProto.FLOAT, [1, 2]
                    )
                ],
            )
        )
        with pytest.raises(ValueError, match="not an initializer"):
            reexport.transform_graph(model)


class TestReexportMain:
    def test_reexport_then_check_roundtrips(self, tmp_path):
        model = tmp_path / "subconscious_controller.onnx"
        shutil.copy(_pristine_or_skip(), model)
        shutil.copy(
            _PRISTINE.parent / "subconscious_controller.onnx.data",
            tmp_path / "subconscious_controller.onnx.data",
        )
        manifest = tmp_path / "manifest.json"
        shutil.copy(default_models_dir() / "manifest.json", manifest)

        rc = reexport.main(["--model", str(model), "--manifest", str(manifest)])
        assert rc == 0
        assert (
            reexport.main(
                ["--check", "--model", str(model), "--manifest", str(manifest)]
            )
            == 0
        )

        rebuilt = onnx.load(model, load_external_data=False)
        arities = [len(n.input) for n in rebuilt.graph.node if n.op_type == "Gemm"]
        assert arities == [3, 3, 3]

    def test_check_flags_a_stale_manifest(self, tmp_path):
        model = tmp_path / "subconscious_controller.onnx"
        shutil.copy(default_model_path(), model)
        shutil.copy(
            default_models_dir() / "subconscious_controller.onnx.data",
            tmp_path / "subconscious_controller.onnx.data",
        )
        manifest = tmp_path / "manifest.json"
        manifest.write_text(
            (default_models_dir() / "manifest.json")
            .read_text(encoding="utf-8")
            .replace("19428", "111"),
            encoding="utf-8",
        )
        assert (
            reexport.main(
                ["--check", "--model", str(model), "--manifest", str(manifest)]
            )
            == 1
        )

    def test_check_flags_a_two_input_gemm(self, tmp_path):
        model_path = tmp_path / "subconscious_controller.onnx"
        stripped = _strip_gemm_bias(onnx.load(default_model_path()))
        onnx.save(stripped, model_path)
        manifest = tmp_path / "manifest.json"
        manifest.write_text('{"files": []}', encoding="utf-8")
        assert (
            reexport.main(
                ["--check", "--model", str(model_path), "--manifest", str(manifest)]
            )
            == 1
        )


def _pristine_or_skip() -> Path:
    if not _PRISTINE.is_file():
        pytest.skip("archived PRINet 3.0 controller graph not present")
    return _PRISTINE


class TestMathematicalIdentity:
    """Acceptance R3: the re-export does not change the graph's function."""

    def test_cpu_bit_identical_vs_bias_stripped_copy(self, committed_model, tmp_path):
        batch = _state_batch()
        stripped_path = tmp_path / "subconscious_controller.onnx"
        onnx.save(_strip_gemm_bias(committed_model), stripped_path)
        shutil.copy(
            default_models_dir() / "subconscious_controller.onnx.data",
            tmp_path / "subconscious_controller.onnx.data",
        )
        pre = _run(stripped_path, [_CPU], batch)
        post = _run(default_model_path(), [_CPU], batch)
        assert np.array_equal(pre.view(np.uint32), post.view(np.uint32))

    def test_cpu_bit_identical_vs_pristine_archive(self):
        pristine = _pristine_or_skip()
        batch = _state_batch()
        pre_arities = [
            len(n.input)
            for n in onnx.load(pristine, load_external_data=False).graph.node
            if n.op_type == "Gemm"
        ]
        assert pre_arities == [2, 2, 2], "archive graph is expected pre-transform"
        pre = _run(pristine, [_CPU], batch)
        post = _run(default_model_path(), [_CPU], batch)
        assert np.array_equal(pre.view(np.uint32), post.view(np.uint32))


@pytest.mark.skipif(
    _DML not in ort.get_available_providers(),
    reason="DmlExecutionProvider is not registered on this host",
)
class TestDirectMLExecution:
    """Acceptance: DirectML executes the re-exported graph and agrees with CPU."""

    def test_pre_transform_graph_is_rejected_by_directml(self):
        pristine = _pristine_or_skip()
        with pytest.raises(Exception, match=r"INVALID_GRAPH|DmlFusedGemm|input size 2"):
            ort.InferenceSession(str(pristine), providers=[_DML])

    def test_directml_executes_the_reexported_graph(self):
        session = ort.InferenceSession(
            str(default_model_path()), providers=[_DML, _CPU]
        )
        assert session.get_providers()[0] == _DML

    def test_directml_agrees_with_cpu_within_tolerance(self):
        batch = _state_batch()
        cpu = _run(default_model_path(), [_CPU], batch)
        dml = _run(default_model_path(), [_DML, _CPU], batch)
        np.testing.assert_allclose(dml, cpu, rtol=1e-5, atol=1e-6)


def _single_gemm_model(
    inputs: list[str],
    initializers: list[onnx.TensorProto],
    *,
    name: str = "g0",
) -> onnx.ModelProto:
    """A minimal one-``Gemm`` model, checker-free, for the error-path tests."""
    node = onnx.helper.make_node("Gemm", inputs, ["y"], name=name)
    graph = onnx.helper.make_graph([node], "g", [], [], initializer=initializers)
    return onnx.helper.make_model(graph)


class TestTransformErrorPaths:
    """WP036F-F1: the ``transform_graph`` guard clauses (reexport 71-72, 121-122)."""

    def test_transform_rejects_a_non_rank2_weight(self):
        weight = numpy_helper.from_array(
            np.zeros((2, 2, 2), dtype=np.float32), name="w"
        )
        model = _single_gemm_model(["a", "w"], [weight])
        with pytest.raises(ValueError, match="not rank-2"):
            reexport.transform_graph(model)

    def test_transform_rejects_a_colliding_bias_name(self):
        weight = numpy_helper.from_array(
            np.zeros((2, 3), dtype=np.float32), name="net.0.weight"
        )
        collision = numpy_helper.from_array(
            np.zeros(3, dtype=np.float32), name="net.0.bias"
        )
        model = _single_gemm_model(["a", "net.0.weight"], [weight, collision])
        with pytest.raises(ValueError, match="already present as an initializer"):
            reexport.transform_graph(model)


class TestCheckDriftBranches:
    """WP036F-F1: the drift branches of ``reexport._check`` (174, 184-188, 201-206)."""

    def _empty_manifest(self, tmp_path: Path) -> Path:
        manifest = tmp_path / "manifest.json"
        manifest.write_text('{"files": []}', encoding="utf-8")
        return manifest

    def test_check_reports_no_gemm_nodes(self, tmp_path):
        model = onnx.helper.make_model(
            onnx.helper.make_graph(
                [onnx.helper.make_node("Identity", ["a"], ["y"], name="id")],
                "g",
                [],
                [],
            )
        )
        model_path = tmp_path / "m.onnx"
        onnx.save(model, model_path)
        problems = reexport._check(model_path, self._empty_manifest(tmp_path))
        assert any("no Gemm nodes" in p for p in problems)

    def test_check_reports_a_non_initializer_bias(self, tmp_path):
        weight = numpy_helper.from_array(np.zeros((4, 2), dtype=np.float32), name="w")
        model = _single_gemm_model(["a", "w", "b"], [weight])
        model_path = tmp_path / "m.onnx"
        onnx.save(model, model_path)
        problems = reexport._check(model_path, self._empty_manifest(tmp_path))
        assert any("is not inline" in p for p in problems)

    def test_check_reports_a_non_zero_bias(self, tmp_path):
        weight = numpy_helper.from_array(np.zeros((4, 2), dtype=np.float32), name="w")
        bias = numpy_helper.from_array(np.ones(4, dtype=np.float32), name="b")
        model = _single_gemm_model(["a", "w", "b"], [weight, bias])
        model_path = tmp_path / "m.onnx"
        onnx.save(model, model_path)
        problems = reexport._check(model_path, self._empty_manifest(tmp_path))
        assert any("is not float32 zero" in p for p in problems)

    def test_check_reports_a_manifest_missing_file(self, tmp_path):
        manifest = tmp_path / "manifest.json"
        manifest.write_text(
            '{"files": [{"path": "gone.bin", "bytes": 1, "sha256": "0"}]}',
            encoding="utf-8",
        )
        problems = reexport._check(default_model_path(), manifest)
        assert any("manifest lists a missing file" in p for p in problems)

    def test_check_reports_a_stale_manifest_digest(self, tmp_path):
        import json

        model_path = default_model_path()
        manifest = tmp_path / "manifest.json"
        entry = {
            "path": model_path.name,
            "bytes": model_path.stat().st_size,
            "sha256": "0" * 64,
        }
        manifest.write_text(json.dumps({"files": [entry]}), encoding="utf-8")
        problems = reexport._check(model_path, manifest)
        assert any("sha256 stale" in p for p in problems)
        assert not any("bytes stale" in p for p in problems)


class TestProviderLatencyToolEdgeCases:
    """WP036F-F1: the latency tool's degraded-host branches (latency lines 99, 191)."""

    def test_pre_transform_check_handles_an_absent_archive(self, tmp_path, monkeypatch):
        monkeypatch.setattr(latency_tool, "_PRISTINE", tmp_path / "not-here.onnx")
        result = latency_tool._pre_transform_check(
            default_model_path(), latency_tool._state_batch()
        )
        assert result == {"available": False}

    def test_main_returns_zero_when_directml_unregistered(self, tmp_path, monkeypatch):
        import json

        monkeypatch.setattr(
            latency_tool, "available_providers", lambda: [latency_tool._CPU]
        )
        out = tmp_path / "report.json"
        rc = latency_tool.main(["--output", str(out)])
        assert rc == 0
        report = json.loads(out.read_text(encoding="utf-8"))
        assert report["directml"] == {"registered": False}
        assert "directml" not in report["latency_ms_median_batch48"]


class TestProviderLatencyTool:
    def test_build_report_records_the_acceptance_evidence(self):
        report = latency_tool.build_report(default_model_path())
        assert report["model"]["gemm_input_arities"] == [3, 3, 3]
        assert report["pre_transform_differential"]["bit_identical"] is True
        assert "cpu" in report["latency_ms_median_batch48"]
        directml = report["directml"]
        if directml["registered"]:
            assert directml["executes"] is True
            assert directml["agrees_with_cpu"] is True
            assert "directml" in report["latency_ms_median_batch48"]

    def test_main_writes_the_evidence_json(self, tmp_path):
        out = tmp_path / "report.json"
        rc = latency_tool.main(["--output", str(out)])
        assert rc == 0
        assert out.is_file()
