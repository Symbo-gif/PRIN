"""Re-export the subconscious controller ONNX graph with three-input ``Gemm`` nodes.

WP-036F S1. ``EVIDENCE/0109-wp028-s1-controller-provider-report.json`` (WP-028
S1) established that ONNX Runtime's ``DmlExecutionProvider`` cannot execute the
committed controller graph: DirectML fuses each ``Gemm``+``Relu`` pair into a
``DmlFusedGemm`` node whose schema requires three inputs, and the graph PyTorch
exported carries only two (input, weight) — the bias is omitted because the
trained biases are all zero. ONNX Runtime rejects the model at session-creation
time with ``InvalidGraph: ... has input size 2 not in range [min=3, max=3]``.

This pass makes every ``Gemm`` node carry an explicit third (bias) input: a new
zero-valued ``float32`` initializer named after the layer's weight
(``net.0.weight`` -> ``net.0.bias``). ``Gemm`` computes
``Y = alpha * A' * B' + beta * C``; with ``beta = 1`` (already set) and ``C``
all zeros, ``Y`` is unchanged. The transform is **idempotent** — a ``Gemm`` that
already has three inputs is left untouched — so it also serves as its own
``--check`` verifier.

The transform never touches the external-data companion
(``subconscious_controller.onnx.data``); the new bias tensors are small and are
stored inline in the ``.onnx`` file.

Usage::

    python tools/wp036f_reexport_controller.py           # rewrite models/ + manifest
    python tools/wp036f_reexport_controller.py --check    # verify only, exit 1 on drift
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path

import numpy as np
import onnx
from onnx import numpy_helper

_REPO_ROOT = Path(__file__).resolve().parents[1]
_DEFAULT_MODEL = _REPO_ROOT / "models" / "subconscious_controller.onnx"
_DEFAULT_MANIFEST = _REPO_ROOT / "models" / "manifest.json"

_GEMM_BIAS_SUFFIX = ".bias"
_GEMM_WEIGHT_SUFFIX = ".weight"


def _bias_name(weight_input: str) -> str:
    """Return the bias initializer name for a ``Gemm`` weight input name."""
    if weight_input.endswith(_GEMM_WEIGHT_SUFFIX):
        stem = weight_input[: -len(_GEMM_WEIGHT_SUFFIX)]
    else:
        stem = weight_input
    return f"{stem}{_GEMM_BIAS_SUFFIX}"


def _gemm_out_features(node: onnx.NodeProto, weight: onnx.TensorProto) -> int:
    """Return a ``Gemm`` node's output-feature count from its weight tensor.

    ``Gemm`` computes ``A' * B'`` where ``B' = B`` unless ``transB`` is set, in
    which case ``B' = B.T``. The bias broadcasts over the output-feature axis,
    which is ``B``'s second dimension normally and its first when ``transB``.
    """
    trans_b = 0
    for attribute in node.attribute:
        if attribute.name == "transB":
            trans_b = attribute.i
    dims = list(weight.dims)
    if len(dims) != 2:
        msg = f"Gemm weight {weight.name!r} is not rank-2: dims={dims}"
        raise ValueError(msg)
    return int(dims[0] if trans_b else dims[1])


def transform_graph(model: onnx.ModelProto) -> tuple[onnx.ModelProto, list[str]]:
    """Return a copy of ``model`` with every ``Gemm`` node given a bias input.

    Args:
        model: The source model. Not mutated.

    Returns:
        ``(transformed_model, added_bias_names)``. ``added_bias_names`` is empty
        when every ``Gemm`` already had three inputs (the transform is
        idempotent).

    Raises:
        ValueError: If a ``Gemm`` node has an unexpected input arity, a
            non-rank-2 weight, or a bias name that already collides with an
            unrelated initializer.
    """
    out = onnx.ModelProto()
    out.CopyFrom(model)
    graph = out.graph

    initializers = {tensor.name: tensor for tensor in graph.initializer}
    added: list[str] = []

    for node in graph.node:
        if node.op_type != "Gemm":
            continue
        if len(node.input) == 3:
            continue
        if len(node.input) != 2:
            msg = (
                f"Gemm node {node.name!r} has {len(node.input)} inputs; "
                "expected 2 (input, weight) or 3 (input, weight, bias)"
            )
            raise ValueError(msg)

        weight_name = node.input[1]
        weight = initializers.get(weight_name)
        if weight is None:
            msg = (
                f"Gemm node {node.name!r} weight {weight_name!r} is not an initializer"
            )
            raise ValueError(msg)

        bias_name = _bias_name(weight_name)
        if bias_name in initializers:
            msg = f"bias name {bias_name!r} already present as an initializer"
            raise ValueError(msg)

        out_features = _gemm_out_features(node, weight)
        bias = numpy_helper.from_array(
            np.zeros(out_features, dtype=np.float32), name=bias_name
        )
        graph.initializer.append(bias)
        initializers[bias_name] = bias
        node.input.append(bias_name)
        added.append(bias_name)

    return out, added


def _sha256(path: Path) -> str:
    """Return the hex SHA-256 digest of a file."""
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _write_manifest(manifest_path: Path, model_dir: Path) -> list[dict[str, object]]:
    """Rewrite ``manifest.json`` from the files on disk, preserving its schema.

    Every ``files`` entry keeps its ``path`` and order; ``bytes`` and ``sha256``
    are recomputed from ``model_dir``. Returns the updated ``files`` list.
    """
    manifest: dict[str, object] = json.loads(manifest_path.read_text(encoding="utf-8"))
    files: list[dict[str, object]] = list(manifest["files"])  # type: ignore[arg-type]
    for entry in files:
        artefact = model_dir / str(entry["path"])
        entry["bytes"] = artefact.stat().st_size
        entry["sha256"] = _sha256(artefact)
    manifest["files"] = files
    manifest_path.write_text(
        json.dumps(manifest, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
        newline="\n",
    )
    return files


def _gemm_input_arities(model: onnx.ModelProto) -> list[int]:
    """Return the input count of every ``Gemm`` node, in graph order."""
    return [len(n.input) for n in model.graph.node if n.op_type == "Gemm"]


def _check(model_path: Path, manifest_path: Path) -> list[str]:
    """Return a list of drift descriptions; empty means the artefact is correct."""
    problems: list[str] = []

    model = onnx.load(model_path, load_external_data=False)
    arities = _gemm_input_arities(model)
    if not arities:
        problems.append("no Gemm nodes found in the committed graph")
    if any(arity != 3 for arity in arities):
        problems.append(f"Gemm input arities are {arities}, expected all 3")

    initializers = {t.name: t for t in model.graph.initializer}
    for node in model.graph.node:
        if node.op_type != "Gemm" or len(node.input) != 3:
            continue
        bias = initializers.get(node.input[2])
        if bias is None:
            problems.append(f"Gemm {node.name!r} bias {node.input[2]!r} is not inline")
            continue
        values = numpy_helper.to_array(bias)
        if values.dtype != np.float32 or np.any(values != 0.0):
            problems.append(
                f"Gemm {node.name!r} bias {bias.name!r} is not float32 zero"
            )

    # Idempotency: re-transforming the committed graph must add nothing.
    _, added = transform_graph(model)
    if added:
        problems.append(f"transform is not a fixed point; would add {added}")

    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    for entry in manifest["files"]:
        artefact = model_path.parent / entry["path"]
        if not artefact.is_file():
            problems.append(f"manifest lists a missing file: {entry['path']}")
            continue
        if entry["bytes"] != artefact.stat().st_size:
            problems.append(f"manifest bytes stale for {entry['path']}")
        if entry["sha256"] != _sha256(artefact):
            problems.append(f"manifest sha256 stale for {entry['path']}")

    return problems


def main(argv: list[str] | None = None) -> int:
    """Re-export the controller graph, or verify the committed artefact.

    Args:
        argv: Command-line arguments, or ``None`` to read ``sys.argv``.

    Returns:
        Process exit code: ``0`` on success, ``1`` on verification drift.
    """
    parser = argparse.ArgumentParser(
        description="Re-export the subconscious controller ONNX graph with "
        "three-input Gemm nodes (WP-036F S1)."
    )
    parser.add_argument(
        "--model",
        type=Path,
        default=_DEFAULT_MODEL,
        help="Path to the controller .onnx graph (rewritten in place).",
    )
    parser.add_argument(
        "--manifest",
        type=Path,
        default=_DEFAULT_MANIFEST,
        help="Path to the models/ SHA-256 manifest.",
    )
    parser.add_argument(
        "--check",
        action="store_true",
        help="Verify the committed artefact and manifest without writing.",
    )
    args = parser.parse_args(argv)

    if args.check:
        problems = _check(args.model, args.manifest)
        if problems:
            for problem in problems:
                print(f"DRIFT: {problem}")
            return 1
        arities = _gemm_input_arities(onnx.load(args.model, load_external_data=False))
        print(f"OK: {len(arities)} Gemm nodes, all three-input; manifest current")
        return 0

    source = onnx.load(args.model, load_external_data=False)
    transformed, added = transform_graph(source)
    onnx.save(transformed, args.model)
    onnx.checker.check_model(str(args.model))
    files = _write_manifest(args.manifest, args.model.parent)

    print(f"re-exported {args.model}")
    print(f"  Gemm bias inputs added: {added or '(none - already three-input)'}")
    for entry in files:
        print(f"  {entry['path']}: {entry['bytes']} bytes  sha256={entry['sha256']}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
