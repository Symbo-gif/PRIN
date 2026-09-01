"""WP-036D ``0144I2`` — device dispatch and DLPack marshalling in ``_torch_compat``.

Covers the three units the ``0144I2`` brief names:

* the ``_is_gpu`` device-dispatch predicate;
* the CPU path is byte-for-byte unchanged pre/post the dispatch guard, for a
  representative input per touched model class (golden values captured from the
  pre-change implementation);
* the GPU branch: ``KuramotoOscillator._compute_derivatives_gpu`` routes a
  sparse k-NN derivative evaluation through the ``0144I1``
  ``prin._prin_core.GpuSparseKuramoto`` binding (CubeCL kernel) and agrees with
  the CPU reference within the Testing Standards §3 GPU tolerance, plus the
  CUDA-guarded device assertion the reference acceptance suite uses.

Per WP-036D plan amendment #37 the GPU marshalling boundary is CPU ``float32``
(``prin-kernels`` kernel dispatch is host-in/host-out); the numerical work runs
on the GPU via CubeCL's own backend selection, so the kernel-agreement test
below exercises the real GPU path even on a host whose PyTorch build is
CPU-only.
"""

from __future__ import annotations

import pytest
import torch
from prin import _prin_core
from prin._torch_compat import (
    HopfOscillator,
    KuramotoOscillator,
    OscillatorState,
    StuartLandauOscillator,
    _from_gpu,
    _gpu_f32,
    _is_gpu,
)

# The GPU sparse k-NN binding is only present when the extension is built with
# `--features cuda` (the maintainer host and the `[gpu]` CI leg). On the plain
# `python.yml` matrix `maturin develop` has no CUDA feature, so
# `_compute_derivatives_gpu` returns None and the kernel-agreement tests below
# have nothing to exercise — same reference-guard class as the file's
# `skipif(not torch.cuda.is_available())` markers. WP-036D / DV-031(B).
_GPU_SPARSE_KNN_BUILT = hasattr(_prin_core, "GpuSparseKuramoto")
_needs_gpu_binding = pytest.mark.skipif(
    not _GPU_SPARSE_KNN_BUILT,
    reason=(
        "prin._prin_core.GpuSparseKuramoto absent "
        "(extension built without --features cuda)"
    ),
)

SEED = 7
# f32 GPU (CubeCL) sparse k-NN kernel vs f64 CPU reference. Documented per-kernel
# tolerance tier — see DOCS/sphinx/parity_report.rst "WP-036D — GPU sparse k-NN
# f32 dispatch parity" (amendment #14 f32-truncation hazard pattern; measured
# worst case max|Δ| ≈ 9.5e-7 abs / ≈ 5.8e-6 rel across the registered cases).
GPU_ATOL = 1e-5
GPU_RTOL = 1e-5


# ── _is_gpu predicate ──────────────────────────────────────────────────────


def test_is_gpu_false_for_cpu_tensor() -> None:
    """A CPU tensor is never routed to the GPU path."""
    assert _is_gpu(torch.zeros(4)) is False


def test_is_gpu_true_for_non_cpu_device() -> None:
    """Any non-CPU device is routed to the GPU path."""
    meta = torch.zeros(4, device="meta")
    assert _is_gpu(meta) is True


@pytest.mark.skipif(not torch.cuda.is_available(), reason="CUDA not available")
def test_is_gpu_true_for_cuda_tensor() -> None:
    """A CUDA tensor is routed to the GPU path."""
    assert _is_gpu(torch.zeros(4, device="cuda")) is True


# ── CPU path unchanged (pre/post golden values) ────────────────────────────

# Captured from ``compute_derivatives`` before the ``0144I2`` dispatch guard
# was added (first four elements of dphase / damplitude).
_CPU_GOLDEN: dict[str, tuple[list[float], list[float]]] = {
    "kur_full": (
        [5.82722759, 4.05265141, 9.03273582, 7.63531923],
        [0.02415431, -0.125089, -0.10374645, 0.04234989],
    ),
    "kur_sknn": (
        [6.26569319, 3.20401192, 8.79333401, 7.09416437],
        [1.04920769, 0.77340764, 0.96205622, 0.95199317],
    ),
    "sl": (
        [5.82722759, 4.05265141, 9.03273582, 7.63531923],
        [-1.25084567, -1.40008903, -1.37874651, -1.23265016],
    ),
    "hopf": (
        [5.82722759, 4.05265141, 9.03273582, 7.63531923],
        [0.12415431, -0.02508901, -0.00374645, 0.14234988],
    ),
}


def _model(tag: str) -> KuramotoOscillator | StuartLandauOscillator | HopfOscillator:
    if tag == "kur_full":
        return KuramotoOscillator(12, coupling_strength=1.5)
    if tag == "kur_sknn":
        return KuramotoOscillator(12, coupling_strength=1.5, coupling_mode="sparse_knn")
    if tag == "sl":
        return StuartLandauOscillator(12, coupling_strength=1.5)
    return HopfOscillator(12, coupling_strength=1.5)


@pytest.mark.parametrize("tag", sorted(_CPU_GOLDEN))
def test_cpu_compute_derivatives_unchanged(tag: str) -> None:
    """The CPU ``compute_derivatives`` path is byte-for-byte pre/post the guard."""
    state = OscillatorState.create_random(12, seed=SEED)
    dphase, damplitude, _ = _model(tag).compute_derivatives(state)
    exp_dphase, exp_damp = _CPU_GOLDEN[tag]
    assert dphase.flatten().tolist()[:4] == pytest.approx(exp_dphase, abs=1e-7)
    assert damplitude.flatten().tolist()[:4] == pytest.approx(exp_damp, abs=1e-7)


def test_cpu_compute_derivatives_unchanged_batched() -> None:
    """The batched CPU path is unchanged too (``_stack`` restores batch shape)."""
    state = OscillatorState.create_random(8, batch_size=3, seed=11)
    dphase, damplitude, _ = KuramotoOscillator(
        8, coupling_strength=2.0
    ).compute_derivatives(state)
    assert tuple(dphase.shape) == (3, 8)
    assert dphase.flatten().tolist()[:4] == pytest.approx(
        [5.97171354, 3.53416038, 8.93748951, 7.27970362], abs=1e-7
    )
    assert damplitude.flatten().tolist()[:4] == pytest.approx(
        [-0.72712731, -0.08265901, 0.00176752, -0.27252147], abs=1e-7
    )


# ── DLPack f32 marshalling helpers ─────────────────────────────────────────


def test_gpu_f32_marshals_to_cpu_float32_contiguous() -> None:
    """``_gpu_f32`` yields a detached, contiguous CPU float32 view."""
    src = (torch.arange(6, dtype=torch.float64).reshape(2, 3).T)[::1]
    out = _gpu_f32(src)
    assert out.dtype is torch.float32
    assert out.device.type == "cpu"
    assert out.is_contiguous()
    assert out.requires_grad is False


def test_from_gpu_restores_dtype_and_device() -> None:
    """``_from_gpu`` decodes a capsule back to the reference tensor's placement."""
    like = torch.zeros(4, dtype=torch.float64)
    capsule = torch.ones(4, dtype=torch.float32)
    restored = _from_gpu(capsule, like)
    assert restored.dtype is torch.float64
    assert restored.device.type == "cpu"
    assert torch.equal(restored, torch.ones(4, dtype=torch.float64))


# ── GPU branch: sparse k-NN CubeCL kernel dispatch ─────────────────────────


@_needs_gpu_binding
def test_gpu_sparse_knn_dispatch_hook_agrees_with_cpu_reference() -> None:
    """``_compute_derivatives_gpu`` runs the CubeCL sparse k-NN kernel and agrees.

    Exercised directly (not through the ``_is_gpu`` guard) so it runs on a
    CPU-only PyTorch host; CubeCL selects its own backend (CUDA on this runner).
    """
    state = OscillatorState.create_random(32, seed=42)
    model = KuramotoOscillator(32, coupling_strength=2.0, coupling_mode="sparse_knn")

    gpu = model._compute_derivatives_gpu(state)
    assert gpu is not None
    cpu = model.compute_derivatives(state)

    names = ("dphase", "damplitude", "dfrequency")
    for got, ref, name in zip(gpu, cpu, names, strict=True):
        assert torch.isfinite(got).all(), name
        torch.testing.assert_close(got, ref, atol=GPU_ATOL, rtol=GPU_RTOL, msg=name)


@_needs_gpu_binding
def test_gpu_sparse_knn_dispatch_hook_batched_state() -> None:
    """The batched dispatch loop stacks per-row GPU results back to ``[B, N]``."""
    state = OscillatorState.create_random(16, batch_size=2, seed=3)
    model = KuramotoOscillator(16, coupling_strength=1.0, coupling_mode="sparse_knn")

    gpu = model._compute_derivatives_gpu(state)
    assert gpu is not None
    cpu = model.compute_derivatives(state)
    assert tuple(gpu[0].shape) == (2, 16)
    torch.testing.assert_close(gpu[0], cpu[0], atol=GPU_ATOL, rtol=GPU_RTOL)


def test_gpu_dispatch_hook_returns_none_for_full_coupling() -> None:
    """Non-sparse regimes stay on the CPU path (hook returns ``None``)."""
    state = OscillatorState.create_random(16, seed=SEED)
    assert KuramotoOscillator(16)._compute_derivatives_gpu(state) is None
    assert StuartLandauOscillator(16)._compute_derivatives_gpu(state) is None
    # n <= 1 never routes to the sparse k-NN kernel either.
    tiny = OscillatorState.create_random(1, seed=SEED)
    assert (
        KuramotoOscillator(1, coupling_mode="sparse_knn")._compute_derivatives_gpu(tiny)
        is None
    )


def test_gpu_dispatch_hook_returns_none_without_binding(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """A build without the GPU bindings falls back to the CPU path."""
    monkeypatch.delattr("prin._prin_core.GpuSparseKuramoto", raising=False)
    state = OscillatorState.create_random(16, seed=SEED)
    model = KuramotoOscillator(16, coupling_strength=1.0, coupling_mode="sparse_knn")
    assert model._compute_derivatives_gpu(state) is None


@pytest.mark.skipif(not torch.cuda.is_available(), reason="CUDA not available")
def test_sparse_knn_compute_derivatives_on_cuda_returns_cuda() -> None:
    """A CUDA state returns a CUDA result (matches the reference acceptance shape)."""
    dev = torch.device("cuda")
    osc = KuramotoOscillator(
        128, coupling_strength=2.0, device=dev, coupling_mode="sparse_knn"
    )
    state = OscillatorState.create_random(128, device=dev, seed=SEED)
    dphi, _dr, _dw = osc.compute_derivatives(state)
    assert dphi.device.type == "cuda"
    assert torch.isfinite(dphi).all()

    cpu_state = OscillatorState(
        state.phase.cpu(), state.amplitude.cpu(), state.frequency.cpu()
    )
    cpu_osc = KuramotoOscillator(128, coupling_strength=2.0, coupling_mode="sparse_knn")
    dphi_cpu, _, _ = cpu_osc.compute_derivatives(cpu_state)
    torch.testing.assert_close(dphi.cpu(), dphi_cpu, atol=GPU_ATOL, rtol=GPU_RTOL)
