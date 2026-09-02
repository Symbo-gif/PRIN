"""WP-036F S1 provider + latency evidence for the re-exported controller graph.

Records, on the project host, that the re-exported subconscious controller
graph (three-input ``Gemm`` nodes, ``tools/wp036f_reexport_controller.py``):

* is **mathematically identical** to the pre-transform PRINet 3.0 graph — a
  differential run over a fixed 48-case set on ``CPUExecutionProvider`` is
  bit-identical;
* is executed by ``DmlExecutionProvider`` (the pre-transform graph is rejected
  with ``InvalidGraph``), and its outputs agree with ``CPUExecutionProvider``
  within Testing Standards §3's ``rtol=1e-5, atol=1e-6`` GPU-vs-CPU tolerance;
* has a measured DirectML-vs-CPU inference latency (median over a warm loop).

The DV-006 re-audit gate names "provider and latency acceptance"; this artefact
is that evidence. Output: ``EVIDENCE/0144U-wp036f-s1-controller-provider-report.json``.

Usage::

    python tools/wp036f_provider_latency.py
"""

from __future__ import annotations

import argparse
import hashlib
import json
import platform
import statistics
import sys
import time
from pathlib import Path
from typing import Any

import numpy as np
import onnx
import onnxruntime as ort
from prin.daemon import available_providers, default_model_path

_REPO_ROOT = Path(__file__).resolve().parents[1]
_PRISTINE = (
    _REPO_ROOT
    / "DOCS"
    / "archive and reference from PRINet 3.0"
    / "PRINet-3.0.0-main"
    / "models"
    / "subconscious_controller.onnx"
)
_DEFAULT_OUTPUT = (
    _REPO_ROOT / "EVIDENCE" / "0144U-wp036f-s1-controller-provider-report.json"
)

_CPU = "CPUExecutionProvider"
_DML = "DmlExecutionProvider"
_WARMUP = 50
_MEASURED = 500
_TOL = {"rtol": 1e-5, "atol": 1e-6}


def _state_batch(cases: int = 48) -> np.ndarray:
    """Return a deterministic ``(cases, 32)`` float32 state batch."""
    rng = np.random.default_rng(20260902)
    return rng.standard_normal((cases, 32)).astype(np.float32)


def _session(model_path: Path, providers: list[str]) -> ort.InferenceSession:
    """Create an ONNX Runtime session with the reference session options."""
    opts = ort.SessionOptions()
    opts.graph_optimization_level = ort.GraphOptimizationLevel.ORT_ENABLE_ALL
    return ort.InferenceSession(str(model_path), sess_options=opts, providers=providers)


def _infer(session: ort.InferenceSession, batch: np.ndarray) -> np.ndarray:
    """Run the controller graph and return the first output as an ``ndarray``."""
    return np.asarray(session.run(None, {"state_vector": batch})[0])


def _gemm_arities(model_path: Path) -> list[int]:
    """Return the input count of every ``Gemm`` node in ``model_path``."""
    model = onnx.load(model_path, load_external_data=False)
    return [len(n.input) for n in model.graph.node if n.op_type == "Gemm"]


def _median_latency_ms(session: ort.InferenceSession, batch: np.ndarray) -> float:
    """Return the median single-call latency in milliseconds over a warm loop."""
    feed = {"state_vector": batch}
    for _ in range(_WARMUP):
        session.run(None, feed)
    samples: list[float] = []
    for _ in range(_MEASURED):
        start = time.perf_counter()
        session.run(None, feed)
        samples.append((time.perf_counter() - start) * 1e3)
    return statistics.median(samples)


def _pre_transform_check(committed: Path, batch: np.ndarray) -> dict[str, Any]:
    """Compare the committed graph against the pristine PRINet 3.0 graph on CPU."""
    if not _PRISTINE.is_file():
        return {"available": False}
    old = _infer(_session(_PRISTINE, [_CPU]), batch)
    new = _infer(_session(committed, [_CPU]), batch)
    return {
        "available": True,
        "pristine_gemm_input_arities": _gemm_arities(_PRISTINE),
        "reexported_gemm_input_arities": _gemm_arities(committed),
        "cases": int(batch.shape[0]),
        "bit_identical": bool(np.array_equal(old.view(np.uint32), new.view(np.uint32))),
        "max_abs_diff": float(np.abs(old - new).max()),
    }


def build_report(model_path: Path) -> dict[str, Any]:
    """Build the WP-036F provider + latency evidence dictionary."""
    batch = _state_batch()
    providers = available_providers()
    digest = hashlib.sha256(model_path.read_bytes()).hexdigest()

    cpu_out = _infer(_session(model_path, [_CPU]), batch)
    latency: dict[str, float] = {
        "cpu": _median_latency_ms(_session(model_path, [_CPU]), batch)
    }

    directml: dict[str, Any] = {"registered": _DML in providers}
    if _DML in providers:
        dml_session = _session(model_path, [_DML, _CPU])
        active = list(dml_session.get_providers())
        dml_out = _infer(dml_session, batch)
        directml.update(
            active_providers=active,
            executes=active[0] == _DML,
            agrees_with_cpu=bool(np.allclose(dml_out, cpu_out, **_TOL)),
            max_abs_diff_vs_cpu=float(np.abs(dml_out - cpu_out).max()),
            tolerance=_TOL,
        )
        latency["directml"] = _median_latency_ms(dml_session, batch)

    return {
        "session": "0144U - WP-036F S1",
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%S%z"),
        "environment": {
            "platform": platform.platform(),
            "processor": platform.processor(),
            "python": platform.python_version(),
            "onnxruntime": ort.__version__,
            "numpy": np.__version__,
            "onnx": onnx.__version__,
        },
        "model": {
            "path": model_path.name,
            "sha256": digest,
            "bytes": model_path.stat().st_size,
            "gemm_input_arities": _gemm_arities(model_path),
        },
        "available_providers": providers,
        "pre_transform_differential": _pre_transform_check(model_path, batch),
        "directml": directml,
        "latency_ms_median_batch48": latency,
    }


def main(argv: list[str] | None = None) -> int:
    """Write the WP-036F provider + latency evidence JSON.

    Args:
        argv: Command-line arguments, or ``None`` to read ``sys.argv``.

    Returns:
        ``0`` when DirectML executes the graph and agrees with CPU (or DirectML
        is not registered on this host), ``1`` otherwise.
    """
    parser = argparse.ArgumentParser(
        description="Record WP-036F DirectML provider + latency evidence."
    )
    parser.add_argument("--model", type=Path, default=default_model_path())
    parser.add_argument("--output", type=Path, default=_DEFAULT_OUTPUT)
    args = parser.parse_args(argv)

    report = build_report(args.model)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        json.dumps(report, indent=2, sort_keys=True, ensure_ascii=False) + "\n",
        encoding="utf-8",
        newline="\n",
    )
    print(f"evidence written to {args.output}")
    print(json.dumps(report["latency_ms_median_batch48"], indent=2))
    print(json.dumps(report["directml"], indent=2))

    directml = report["directml"]
    if not directml["registered"]:
        return 0
    return 0 if directml.get("executes") and directml.get("agrees_with_cpu") else 1


if __name__ == "__main__":
    sys.exit(main())
