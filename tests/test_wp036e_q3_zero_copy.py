"""WP-036E Q3 — export-direction zero-copy ``kDLCUDA`` DLPack.

Sub-pass ``0144Q3`` exposes the ``0144Q2`` device-resident engines to Python
with an export-direction zero-copy path: on a CUDA build,
``GpuMeanFieldEngine.state()`` and ``GpuSparseKuramoto.compute_derivatives()``
return ``kDLCUDA`` capsules over the engines' live device buffers, so
``torch.utils.dlpack.from_dlpack`` adopts them with no host round-trip.

Per plan amendment #43 the *input* boundary stays a single host ``float32``
upload (``cubecl 0.10`` cannot adopt an external CUDA device pointer as a
kernel-input ``Handle``); these tests cover the reachable export half plus the
snapshot-stability contract the capsule lifetime relies on.

The CUDA tests are ``@pytest.mark.gpu`` and additionally guarded on the CUDA
extension build (``--features cuda``) and a live CUDA device, mirroring the
existing WP-036D GPU acceptance suite; the CPU-path regression check runs in
the default gate.
"""

from __future__ import annotations

import pytest
import torch
from prin import _prin_core
from prin._torch_compat import KuramotoOscillator, OscillatorState
from torch.utils.dlpack import from_dlpack

_GPU_ENGINES_BUILT = hasattr(_prin_core, "GpuMeanFieldEngine")


def _needs_cuda_build(fn: object) -> object:
    """Stack the repo GPU-guard pair: ``@pytest.mark.gpu`` + a CUDA ``skipif``.

    Mirrors the ported acceptance suite's marker policy (``tests/README.md``):
    ``-m gpu`` selects the test on ``PRIN-GPU-Runner``; the ``skipif`` covers a
    CPU-only host or a build without ``--features cuda``.
    """
    guarded = pytest.mark.skipif(
        not _GPU_ENGINES_BUILT or not torch.cuda.is_available(),
        reason=(
            "needs the CUDA extension build (maturin --features cuda) and a "
            "live CUDA device (PRIN-GPU-Runner)"
        ),
    )(fn)
    return pytest.mark.gpu(guarded)


SEED = 7
# f32 GPU (CubeCL) vs f64 CPU reference — the WP-036D per-kernel tolerance tier.
GPU_ATOL = 1e-5
GPU_RTOL = 1e-5


def _mean_field_engine(n: int) -> object:
    phase = torch.linspace(0.0, 1.0, n, dtype=torch.float32)
    amp = torch.ones(n, dtype=torch.float32)
    freq = torch.linspace(-0.2, 0.2, n, dtype=torch.float32)
    return _prin_core.GpuMeanFieldEngine(phase, amp, freq, 1.0, 0.1, 0.01, 0.01)


# ── GpuMeanFieldEngine.state() zero-copy export ────────────────────────────


@_needs_cuda_build
def test_mean_field_state_exports_kdlcuda_capsules() -> None:
    """``state()`` returns CUDA tensors adopted with no host round-trip."""
    engine = _mean_field_engine(96)
    for _ in range(3):
        engine.step()

    phase, amp, freq = (from_dlpack(c) for c in engine.state())
    for name, t in (("phase", phase), ("amplitude", amp), ("frequency", freq)):
        assert t.is_cuda, f"{name} must be a CUDA tensor (zero-copy kDLCUDA)"
        assert t.shape == (96,), name
        assert torch.isfinite(t).all(), name


@_needs_cuda_build
def test_mean_field_state_export_is_deterministic() -> None:
    """Two identically-seeded engines produce bit-identical exported state."""
    a = _mean_field_engine(64)
    b = _mean_field_engine(64)
    for _ in range(5):
        a.step()
        b.step()
    pa = from_dlpack(a.state()[0]).cpu()
    pb = from_dlpack(b.state()[0]).cpu()
    assert torch.equal(pa, pb)


@_needs_cuda_build
def test_mean_field_state_export_is_a_stable_snapshot() -> None:
    """An exported ``state()`` tensor is not mutated by the next ``step()``.

    The capsule pins its CubeCL ``Handle``; the next ``step()`` allocates fresh
    state handles, so the snapshot taken beforehand keeps its values (standard
    DLPack producer semantics — the lifetime the zero-copy path relies on).
    """
    engine = _mean_field_engine(48)
    engine.step()

    snapshot = from_dlpack(engine.state()[0])
    before = snapshot.clone()

    engine.step()
    engine.step()

    assert torch.equal(snapshot, before), "export must be a stable snapshot"


# ── GpuSparseKuramoto sparse k-NN derivative export ────────────────────────


@_needs_cuda_build
def test_sparse_knn_cuda_dispatch_returns_zero_copy_cuda_result() -> None:
    """A CUDA sparse k-NN derivative comes back on-device and matches CPU."""
    dev = torch.device("cuda")
    model = KuramotoOscillator(
        128, coupling_strength=2.0, device=dev, coupling_mode="sparse_knn"
    )
    state = OscillatorState.create_random(128, device=dev, seed=SEED)

    dphase, damp, dfreq = model.compute_derivatives(state)
    assert dphase.is_cuda and damp.is_cuda and dfreq.is_cuda
    assert torch.isfinite(dphase).all()

    cpu_model = KuramotoOscillator(
        128, coupling_strength=2.0, coupling_mode="sparse_knn"
    )
    cpu_state = OscillatorState(
        state.phase.cpu(), state.amplitude.cpu(), state.frequency.cpu()
    )
    ref_dphase, _, _ = cpu_model.compute_derivatives(cpu_state)
    torch.testing.assert_close(dphase.cpu(), ref_dphase, atol=GPU_ATOL, rtol=GPU_RTOL)


@_needs_cuda_build
def test_sparse_knn_dispatch_hook_keeps_cuda_input_on_device() -> None:
    """With a CUDA input the hook keeps the whole round trip on-device.

    ``_from_gpu`` restores the result to the *input's* device, so a CPU input
    yields a CPU result even though the kernel ran via the zero-copy CUDA
    export; a CUDA input must stay CUDA end to end (no host bounce).
    """
    dev = torch.device("cuda")
    state = OscillatorState.create_random(64, device=dev, seed=42)
    model = KuramotoOscillator(64, coupling_strength=2.0, coupling_mode="sparse_knn")

    gpu = model._compute_derivatives_gpu(state)
    assert gpu is not None
    assert all(t.is_cuda for t in gpu)
    assert all(torch.isfinite(t).all() for t in gpu)


# ── CPU path unchanged ────────────────────────────────────────────────────


def test_cpu_compute_derivatives_still_cpu_and_finite() -> None:
    """The CPU dispatch path is untouched by the Q3 export changes."""
    state = OscillatorState.create_random(12, seed=SEED)
    dphase, damp, dfreq = KuramotoOscillator(
        12, coupling_strength=1.5, coupling_mode="sparse_knn"
    ).compute_derivatives(state)
    assert dphase.device.type == "cpu"
    assert torch.isfinite(dphase).all()
    assert torch.isfinite(damp).all()
    assert torch.isfinite(dfreq).all()
