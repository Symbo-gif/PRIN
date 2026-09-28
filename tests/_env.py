"""Shared hardware/runtime capability probes for environment-gated tests.

ETCA-002 finding T-F3 / governance G4: a ``skipif`` guarding a hardware or
runtime feature must probe **executability** (attempt the operation), not
**registration**. ``onnxruntime.get_available_providers()`` returns every
provider *compiled into the wheel* — on a GitHub-hosted ``windows-latest``
runner ``onnxruntime-directml`` registers ``DmlExecutionProvider`` even though
no DirectML-capable adapter is present, so a
``"DmlExecutionProvider" not in ort.get_available_providers()`` guard does not
fire and the guarded test runs and hard-fails.

``directml_executes()`` builds a one-node session pinned to
``DmlExecutionProvider`` and runs it: it is ``True`` only on a host where
DirectML actually executes a graph (the maintainer host, ``PRIN-GPU-Runner``),
``False`` on a hosted runner with the provider registered but no device — so
the test *skips* there instead of failing, and *runs* on the real-GPU runner.
"""

from __future__ import annotations

import functools

_DML = "DmlExecutionProvider"


@functools.lru_cache(maxsize=1)
def directml_executes() -> bool:
    """Whether ``DmlExecutionProvider`` can actually execute a graph on this host."""
    try:
        import numpy as np
        import onnx
        import onnxruntime as ort
    except ImportError:
        return False

    if _DML not in ort.get_available_providers():
        return False

    try:
        graph = onnx.helper.make_graph(
            [onnx.helper.make_node("Identity", ["x"], ["y"])],
            "directml_probe",
            [onnx.helper.make_tensor_value_info("x", onnx.TensorProto.FLOAT, [1])],
            [onnx.helper.make_tensor_value_info("y", onnx.TensorProto.FLOAT, [1])],
        )
        model = onnx.helper.make_model(
            graph, opset_imports=[onnx.helper.make_opsetid("", 13)]
        )
        session = ort.InferenceSession(model.SerializeToString(), providers=[_DML])
        if session.get_providers()[:1] != [_DML]:
            return False
        session.run(None, {"x": np.zeros(1, dtype=np.float32)})
    except Exception:
        return False
    return True


@functools.lru_cache(maxsize=1)
def cuda_kernel_executes() -> bool:
    """Whether ``prin._prin_core.GpuSparseKuramoto`` really dispatches via CUDA.

    The same executability-over-registration rule as :func:`directml_executes`,
    applied to the extension's GPU kernel binding. ``GpuSparseKuramoto``
    compiles under ``cfg(any(feature = "cuda", feature = "wgpu"))``, so its
    presence proves only that *some* GPU feature was built, and
    ``torch.cuda.is_available()`` describes PyTorch's runtime, not which
    backend the Rust extension was compiled against — a wgpu-only build on a
    CUDA host passes both checks and then hard-fails. Even a ``--features
    cuda`` build falls back to ``prin-sim``'s host-slice path when its CubeCL
    client cannot initialise (``crates/prin-sim/src/gpu.rs``).

    This probe therefore does what the code under test does: it runs one tiny
    (``N=4``, ``k=2``) derivative evaluation and checks that **every** returned
    DLPack capsule is CUDA-resident, which only the true CUDA device-resident
    path produces (WP-036E Q3). ``True`` → the H4 success-path tests can run;
    ``False`` → they skip, on a wgpu-only build, a binding-less build, or a
    host whose CUDA runtime is unavailable.

    The probe allocates three length-4 f32 tensors and one throwaway engine;
    it mutates no process or device state, and the ``lru_cache`` means the
    cost is paid at most once per session.
    """
    try:
        import torch
        from prin import _prin_core
        from torch.utils.dlpack import from_dlpack
    except ImportError:
        return False

    engine_cls = getattr(_prin_core, "GpuSparseKuramoto", None)
    if engine_cls is None:
        return False

    try:
        phase = torch.zeros(4, dtype=torch.float32).contiguous()
        amplitude = torch.ones(4, dtype=torch.float32).contiguous()
        frequency = torch.zeros(4, dtype=torch.float32).contiguous()
        engine = engine_cls.from_knn_phase(4, 2, 0.5, 0.0, 0.0, phase)
        capsules = engine.compute_derivatives(phase, amplitude, frequency)
        return all(from_dlpack(capsule).device.type == "cuda" for capsule in capsules)
    except Exception:
        return False


@functools.lru_cache(maxsize=1)
def wgpu_kernel_executes() -> bool:
    """Whether ``prin._prin_core.GpuSparseKuramoto`` really dispatches via wgpu.

    DV-041: unlike CUDA, a wgpu dispatch and the host-slice CPU fallback both
    return a CPU-resident DLPack capsule (``crates/prin-py/src/bindings
    /gpu.rs``'s module doc), so :func:`cuda_kernel_executes`'s trick of
    checking capsule residency does not generalise to wgpu — there was no
    Python-visible signal at all that told the two apart. This probe instead
    reads the engine's own ``backend_name`` property
    (``crates/prin-sim/src/gpu.rs::backend_name_of``: the live CubeCL runtime
    name on the device-resident path, e.g. ``"wgpu<wgsl>"``; the backend
    actually used by the most recent dispatch on the host-slice fallback
    path, ``"cpu-native"`` before any call there — DV041-F5 follow-up), the
    same executability-over-registration rule as
    :func:`directml_executes`/:func:`cuda_kernel_executes` — it reads a live
    runtime fact, not just whether the binding was compiled in.

    A client that merely *initialises* is not proof a kernel actually
    dispatches through it (DV041-F4 finding from code review: kernel
    compilation or launch can still fail on an adapter that otherwise
    reports ready), and on the host-slice fallback path `backend_name`
    is stale until a call actually happens — so this probe calls
    ``compute_derivatives`` once, matching :func:`cuda_kernel_executes`'s
    own pattern, before trusting the result.

    ``True`` only on a build with a live wgpu-dispatching adapter reachable
    (typically a ``--features wgpu`` build without ``cuda`` — wgpu compiles
    out under ``cfg(all(feature = "wgpu", not(feature = "cuda")))`` when
    both are enabled, so a ``--features cuda,wgpu`` build only reports
    `True` here if CUDA's own client failed to initialise while wgpu's did);
    ``False`` on a binding-less build or a wgpu build with no adapter.
    """
    try:
        import torch
        from prin import _prin_core
    except ImportError:
        return False

    engine_cls = getattr(_prin_core, "GpuSparseKuramoto", None)
    if engine_cls is None:
        return False

    try:
        phase = torch.zeros(4, dtype=torch.float32).contiguous()
        amplitude = torch.ones(4, dtype=torch.float32).contiguous()
        frequency = torch.zeros(4, dtype=torch.float32).contiguous()
        engine = engine_cls.from_knn_phase(4, 2, 0.5, 0.0, 0.0, phase)
        engine.compute_derivatives(phase, amplitude, frequency)
        return bool(engine.backend_name.startswith("wgpu"))
    except Exception:
        return False
