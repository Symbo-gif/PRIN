"""DV-041 — positive GPU backend identification (`GpuSparseKuramoto`,
`GpuMeanFieldEngine`, `GpuBandStepper` `.backend_name`).

Before this, no Python-visible signal distinguished a real wgpu dispatch
from a silent host-slice CPU fallback: only the CUDA device-resident path
returns a zero-copy `kDLCUDA` DLPack capsule (`WP-036E Q3`); wgpu and the
host-slice fallback both copy their result back to host memory before
export, so a CPU-resident capsule alone cannot tell them apart
(`crates/prin-py/src/bindings/gpu.rs` module doc). `.backend_name` reads the
live CubeCL runtime name behind each engine's resolved `ComputeClient`
(`crates/prin-sim/src/gpu.rs::backend_name_of`), or `"cpu-native"` when no
client initialised and the engine fell back to the host-slice path — the
same convention `prin_kernels`' fused `StepReport.backend_name` already
uses (`"cuda"`, `"wgpu<wgsl>"`, `"cpu"`).

These tests use the executability-over-registration probes in
`tests/_env.py` (`cuda_kernel_executes`, `wgpu_kernel_executes`): a build
flag or `hasattr` check proves only that a binding was *compiled*, not that
its backend actually *dispatches* on this host (ETCA-002 T-F3 / governance
G4).
"""

from __future__ import annotations

import pytest
import torch
from _env import cuda_kernel_executes, wgpu_kernel_executes
from prin import _prin_core

_GPU_SPARSE_KNN_BUILT = hasattr(_prin_core, "GpuSparseKuramoto")
_needs_gpu_binding = pytest.mark.skipif(
    not _GPU_SPARSE_KNN_BUILT,
    reason=(
        "prin._prin_core.GpuSparseKuramoto absent "
        "(extension built without --features cuda or --features wgpu)"
    ),
)


def _needs_cuda_dispatch(fn: object) -> object:
    """Stack ``@pytest.mark.gpu`` + a live-CUDA-dispatch ``skipif``.

    Mirrors ``tests/test_wp036e_q3_zero_copy.py``'s ``_needs_cuda_build``:
    composing via ``pytest.mark.gpu(pytest.mark.skipif(...))`` does not chain
    two marks onto a function, it feeds the ``skipif`` ``MarkDecorator`` to
    ``gpu`` as a mark argument and never applies either — the marks must be
    applied to ``fn`` in sequence instead.
    """
    guarded = pytest.mark.skipif(
        not (_GPU_SPARSE_KNN_BUILT and cuda_kernel_executes()),
        reason="needs a --features cuda build with a live CUDA device",
    )(fn)
    return pytest.mark.gpu(guarded)


def _needs_wgpu_dispatch(fn: object) -> object:
    """Stack ``@pytest.mark.gpu`` + a live-wgpu-dispatch ``skipif``."""
    guarded = pytest.mark.skipif(
        not (_GPU_SPARSE_KNN_BUILT and wgpu_kernel_executes()),
        reason="needs a --features wgpu (non-cuda) build with a live adapter",
    )(fn)
    return pytest.mark.gpu(guarded)


def _sparse_kuramoto() -> object:
    """Build a tiny `GpuSparseKuramoto` for `.backend_name` inspection."""
    phase = torch.zeros(4, dtype=torch.float32).contiguous()
    return _prin_core.GpuSparseKuramoto.from_knn_phase(4, 2, 0.5, 0.0, 0.0, phase)


def _mean_field_engine() -> object:
    """Build a tiny `GpuMeanFieldEngine` for `.backend_name` inspection."""
    n = 4
    phase = torch.linspace(0.0, 1.0, n, dtype=torch.float32)
    amp = torch.ones(n, dtype=torch.float32)
    freq = torch.zeros(n, dtype=torch.float32)
    return _prin_core.GpuMeanFieldEngine(phase, amp, freq, 1.0, 0.1, 0.01, 0.01)


def _band_stepper() -> object:
    """Build a tiny `GpuBandStepper` for `.backend_name` inspection."""
    n = 12
    phase = torch.zeros(n, dtype=torch.float32)
    amp = torch.ones(n, dtype=torch.float32)
    freq = torch.zeros(n, dtype=torch.float32)
    return _prin_core.GpuBandStepper(
        phase,
        amp,
        freq,
        [4, 4, 4],
        [1.0, 1.0, 1.0],
        [0.1, 0.1, 0.1],
        [0.01, 0.01, 0.01],
        [0.0, 0.0],
        [0.0, 0.0],
        1e-6,
        10.0,
        0.01,
    )


# ── Presence and vocabulary (any binding-built host) ───────────────────────


@_needs_gpu_binding
@pytest.mark.parametrize("build", [_sparse_kuramoto, _mean_field_engine, _band_stepper])
def test_backend_name_is_one_of_the_registered_values(build: object) -> None:
    """`.backend_name` never returns something outside the documented set.

    A stray or misspelled value here would silently defeat every consumer
    that pattern-matches on it (e.g. a future campaign-driver wgpu leg), so
    this is checked independently of which backend this host happens to run.
    """
    engine = build()  # type: ignore[operator]
    name = engine.backend_name
    assert isinstance(name, str) and name
    assert name == "cpu-native" or name in ("cuda", "cpu") or name.startswith("wgpu")


# ── Positive identification on real hardware ────────────────────────────────


@_needs_cuda_dispatch
@pytest.mark.parametrize("build", [_sparse_kuramoto, _mean_field_engine, _band_stepper])
def test_backend_name_reports_cuda_on_a_cuda_dispatching_build(build: object) -> None:
    """DV-041 positive case: a genuinely CUDA-dispatching build reports it."""
    engine = build()  # type: ignore[operator]
    assert engine.backend_name == "cuda"


@_needs_wgpu_dispatch
@pytest.mark.parametrize("build", [_sparse_kuramoto, _mean_field_engine, _band_stepper])
def test_backend_name_reports_wgpu_on_a_wgpu_dispatching_build(build: object) -> None:
    """DV-041's actual target: a wgpu dispatch is no longer indistinguishable
    from a silent host-slice fallback — this is exactly the positive signal
    the EXP-001-r1/EXP-004 wgpu legs need and, before this, did not have."""
    engine = build()  # type: ignore[operator]
    assert engine.backend_name.startswith("wgpu")


@_needs_gpu_binding
def test_cuda_and_wgpu_dispatch_are_mutually_exclusive() -> None:
    """`SimRuntime` is a compile-time choice (CUDA takes priority over wgpu
    when both features are enabled), so a single build can never dispatch
    through both — this is the invariant the two probes above rely on."""
    assert not (cuda_kernel_executes() and wgpu_kernel_executes())
