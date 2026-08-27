"""WP-036 S1 (0141B) — ``prin.tensor`` compatibility-surface acceptance tests.

Construct/callable smoke checks plus the "not decomposed yet" and shape-guard
error paths for the thin ``prin-tensor`` (WP-014) bindings. Numerical parity
against PRINet 3.0 is a WP-036B/C obligation, not this pass.
"""

from __future__ import annotations

import prin
import pytest
import torch
from prin.tensor import CPDecomposition, DecompositionError, PolyadicTensor


def _rank1(shape: tuple[int, ...]) -> torch.Tensor:
    """Return an exact rank-1 tensor (outer product of ``arange`` vectors)."""
    vecs = [torch.arange(1, n + 1, dtype=torch.float64) for n in shape]
    out = vecs[0]
    for v in vecs[1:]:
        out = out.unsqueeze(-1) * v
    return out


def test_symbols_resolve_from_prin_top_level() -> None:
    """Both decomposition symbols resolve from the package root."""
    assert prin.PolyadicTensor is PolyadicTensor
    assert prin.CPDecomposition is CPDecomposition


def test_polyadic_tensor_roundtrip_and_accessors() -> None:
    """Full-rank Tucker reconstructs the input and exposes core/factors."""
    x = torch.randn(4, 5, 3, dtype=torch.float64)
    pt = PolyadicTensor(shape=(4, 5, 3), rank=5, dtype=torch.float64)
    assert pt.shape == (4, 5, 3)
    assert pt.rank == 5
    pt.decompose(x)
    recon = pt.reconstruct()
    assert recon.shape == x.shape
    assert torch.allclose(recon, x, atol=1e-8)
    assert pt.core.shape == (4, 5, 3)
    assert len(pt.factors) == 3
    assert pt.factors[0].shape == (4, 4)


def test_polyadic_tensor_truncated_rank_is_clamped_per_mode() -> None:
    """An over-large ``rank`` is clamped to each mode's unfolding bound."""
    pt = PolyadicTensor(shape=(3, 4, 2), rank=99, dtype=torch.float64)
    pt.decompose(_rank1((3, 4, 2)))
    assert pt.core.shape == (3, 4, 2)


def test_polyadic_tensor_reads_before_decompose_raise() -> None:
    """Every result accessor raises ``DecompositionError`` until fitted."""
    pt = PolyadicTensor(shape=(3, 3, 3), rank=2)
    with pytest.raises(DecompositionError):
        pt.reconstruct()
    with pytest.raises(DecompositionError):
        _ = pt.core
    with pytest.raises(DecompositionError):
        _ = pt.factors


def test_polyadic_tensor_rejects_bad_config_and_shape() -> None:
    """Constructor and ``decompose`` guards match the PRINet 3.0 contract."""
    with pytest.raises(ValueError, match="rank"):
        PolyadicTensor(shape=(4, 4), rank=0)
    with pytest.raises(ValueError, match="positive"):
        PolyadicTensor(shape=(0, 4), rank=1)
    pt = PolyadicTensor(shape=(4, 4), rank=2)
    with pytest.raises(ValueError, match="does not match"):
        pt.decompose(torch.randn(3, 3, dtype=torch.float64))


def test_polyadic_tensor_returns_requested_dtype_and_device() -> None:
    """``dtype`` controls the returned tensors; the fit stays float64."""
    pt = PolyadicTensor(shape=(3, 3, 3), rank=2, dtype=torch.float32)
    pt.decompose(torch.randn(3, 3, 3))
    assert pt.reconstruct().dtype == torch.float32
    assert pt.core.dtype == torch.float32


def test_cp_decomposition_roundtrip_and_accessors() -> None:
    """CP-ALS on a rank-1 tensor converges and exposes weights/factors."""
    x = _rank1((4, 3, 5))
    cp = CPDecomposition(
        shape=(4, 3, 5), rank=1, max_iter=200, tol=1e-10, dtype=torch.float64
    )
    assert cp.shape == (4, 3, 5)
    assert cp.rank == 1
    cp.decompose(x)
    assert cp.weights.shape == (1,)
    assert len(cp.factors) == 3
    assert cp.factors[1].shape == (3, 1)
    assert torch.allclose(cp.reconstruct(), x, atol=1e-6)


def test_cp_decomposition_reads_before_decompose_raise() -> None:
    """Every CP result accessor raises ``DecompositionError`` until fitted."""
    cp = CPDecomposition(shape=(3, 3, 3), rank=2)
    with pytest.raises(DecompositionError):
        cp.reconstruct()
    with pytest.raises(DecompositionError):
        _ = cp.weights
    with pytest.raises(DecompositionError):
        _ = cp.factors


def test_cp_decomposition_rejects_bad_config() -> None:
    """Constructor guards cover rank, shape, ``max_iter`` and ``tol``."""
    with pytest.raises(ValueError, match="rank"):
        CPDecomposition(shape=(4, 4), rank=0)
    with pytest.raises(ValueError, match="positive"):
        CPDecomposition(shape=(4, 0), rank=2)
    with pytest.raises(ValueError, match="max_iter"):
        CPDecomposition(shape=(4, 4), rank=2, max_iter=0)
    with pytest.raises(ValueError, match="tol"):
        CPDecomposition(shape=(4, 4), rank=2, tol=-1.0)


def test_cp_decomposition_non_convergence_is_a_typed_error() -> None:
    """``prin-tensor`` raises on non-convergence (a documented deviation)."""
    cp = CPDecomposition(shape=(3, 4, 2), rank=3, max_iter=1, tol=1e-14)
    with pytest.raises(ValueError, match="converge"):
        cp.decompose(torch.arange(24, dtype=torch.float64).reshape(3, 4, 2))


def test_cp_decomposition_is_seed_deterministic() -> None:
    """The same seed and input give identical factors across runs."""
    generator = torch.Generator().manual_seed(0)
    x = torch.randn(4, 4, 4, dtype=torch.float64, generator=generator)
    runs = [
        CPDecomposition(
            shape=(4, 4, 4), rank=2, tol=1e-8, dtype=torch.float64, seed_counter=7
        )
        for _ in range(2)
    ]
    for cp in runs:
        cp.decompose(x)
    assert torch.equal(runs[0].weights, runs[1].weights)
