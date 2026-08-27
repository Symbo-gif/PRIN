"""Acceptance and equivalence tests for the 0141C kernel compatibility surface."""

from __future__ import annotations

from collections.abc import Callable

import prin
import pytest
import torch
from prin import _prin_core
from torch import Tensor

RTOL = 1e-5
ATOL = 1e-6

KERNEL_NAMES = (
    "pytorch_mean_field_rk4_step",
    "pytorch_sparse_knn_coupling",
    "pytorch_pac_modulation",
    "pytorch_hierarchical_order_param",
    "pytorch_multi_rate_rk4_step",
    "pytorch_multi_rate_derivatives",
    "pytorch_fused_sub_step_rk4",
    "pytorch_cross_band_coupling",
    "pytorch_fused_discrete_step",
    "pytorch_fused_discrete_step_full",
    "csr_coupling_step",
    "sparse_knn_coupling_step",
    "build_knn_neighbors",
    "sparse_coupling_matrix",
    "sparse_coupling_matrix_csr",
)


def _assert_core_equivalent(
    actual: Tensor | tuple[Tensor, ...], expected: object
) -> None:
    tensors = (actual,) if isinstance(actual, Tensor) else actual
    values = (expected,) if isinstance(actual, Tensor) else expected
    assert isinstance(values, tuple | list)
    for tensor, raw in zip(tensors, values, strict=True):
        torch.testing.assert_close(
            tensor.cpu().reshape(-1),
            torch.tensor(raw, dtype=tensor.dtype).reshape(-1),
            rtol=RTOL,
            atol=ATOL,
        )


def _state() -> tuple[Tensor, Tensor, Tensor]:
    return (
        torch.tensor([0.1, 0.8, 1.7], dtype=torch.float64),
        torch.tensor([1.0, 0.9, 1.1], dtype=torch.float64),
        torch.tensor([0.2, -0.1, 0.4], dtype=torch.float64),
    )


def test_kernel_symbols_resolve_and_are_callable() -> None:
    """Every compatibility symbol resolves at module, top-level, and core layers."""
    import prin.kernels as kernels

    for name in KERNEL_NAMES:
        assert name in prin.__all__
        assert name in kernels.__all__
        assert callable(getattr(prin, name))
        assert callable(getattr(_prin_core, name))


def test_mean_field_core_wrapper_equivalence_and_batch() -> None:
    """Mean-field wrapper preserves shape/dtype and delegates each batch row."""
    phase, amp, freq = _state()
    actual = prin.pytorch_mean_field_rk4_step(phase, amp, freq, 0.7, 0.1, 0.02, 0.01)
    expected = _prin_core.pytorch_mean_field_rk4_step(
        phase.float().tolist(),
        amp.float().tolist(),
        freq.float().tolist(),
        0.7,
        0.1,
        0.02,
        0.01,
    )
    _assert_core_equivalent(actual, expected)
    batched = prin.pytorch_mean_field_rk4_step(
        phase.repeat(2, 1), amp.repeat(2, 1), freq.repeat(2, 1), 0.7, 0.1, 0.02, 0.01
    )
    assert all(
        value.shape == (2, 3) and value.dtype == phase.dtype for value in batched
    )


def test_mean_field_rejects_mismatched_batch_dimensions() -> None:
    """The wrapper validates that all state tensors have identical shape."""
    phase, amp, freq = _state()
    mismatched = torch.zeros(2, 2, dtype=phase.dtype)
    with pytest.raises(ValueError, match="amplitude must have shape"):
        prin.pytorch_mean_field_rk4_step(phase, mismatched, freq, 0.7, 0.1, 0.02, 0.01)
    with pytest.raises(ValueError, match="frequency must have shape"):
        prin.pytorch_mean_field_rk4_step(
            phase.repeat(2, 1), amp.repeat(2, 1), freq, 0.7, 0.1, 0.02, 0.01
        )


def test_sparse_knn_family_equivalence() -> None:
    """Both sparse k-NN entry points use flattened Rust neighbor marshalling."""
    phase, amp, freq = _state()
    neighbors = torch.tensor([[1, 2], [0, 2], [0, 1]])
    actual = prin.pytorch_sparse_knn_coupling(
        phase, amp, freq, neighbors, 0.7, 0.1, 0.02
    )
    expected = _prin_core.pytorch_sparse_knn_coupling(
        phase.float().tolist(),
        amp.float().tolist(),
        freq.float().tolist(),
        neighbors.flatten().tolist(),
        0.7,
        0.1,
        0.02,
    )
    _assert_core_equivalent(actual, expected)
    correction = prin.sparse_knn_coupling_step(phase, amp, neighbors, 0.7)
    raw = _prin_core.sparse_knn_coupling_step(
        phase.tolist(), amp.tolist(), neighbors.flatten().tolist(), 0.7
    )
    _assert_core_equivalent(correction, raw)


def test_pac_and_hierarchical_equivalence() -> None:
    """PAC and hierarchical reductions match direct compiled-core calls."""
    slow = torch.tensor([0.1, 0.4], dtype=torch.float64)
    fast = torch.tensor([0.8, 1.2], dtype=torch.float64)
    actual = prin.pytorch_pac_modulation(slow, fast, 0.3)
    raw = _prin_core.pytorch_pac_modulation(
        slow.float().tolist(), fast.float().tolist(), 0.3
    )
    _assert_core_equivalent(actual, raw)
    phases = torch.tensor([0.0, 0.1, 1.0, 1.1], dtype=torch.float64)
    order = prin.pytorch_hierarchical_order_param(phases, [2, 2])
    order_raw = _prin_core.pytorch_hierarchical_order_param(
        phases.float().tolist(), [2, 2]
    )
    _assert_core_equivalent(order, order_raw)


def test_multi_rate_family_equivalence() -> None:
    """All three multi-rate wrappers match their direct core outputs."""
    phase, amp, freq = _state()
    labels = torch.tensor([0, 1, 2])
    calls: list[tuple[tuple[Tensor, ...], object]] = []
    calls.append(
        (
            prin.pytorch_multi_rate_rk4_step(phase, amp, freq, 0.5, 0.1, 0.01, 0.02, 2),
            _prin_core.pytorch_multi_rate_rk4_step(
                phase.float().tolist(),
                amp.float().tolist(),
                freq.float().tolist(),
                0.5,
                0.1,
                0.01,
                0.02,
                2,
                True,
            ),
        )
    )
    calls.append(
        (
            prin.pytorch_multi_rate_derivatives(
                phase, amp, freq, labels, 0.5, 0.1, 0.01
            ),
            _prin_core.pytorch_multi_rate_derivatives(
                phase.float().tolist(),
                amp.float().tolist(),
                freq.float().tolist(),
                labels.tolist(),
                0.5,
                0.1,
                0.01,
                None,
            ),
        )
    )
    calls.append(
        (
            prin.pytorch_fused_sub_step_rk4(
                phase, amp, freq, labels, 0.5, 0.1, 0.01, 0.02, (1, 2, 3)
            ),
            _prin_core.pytorch_fused_sub_step_rk4(
                phase.float().tolist(),
                amp.float().tolist(),
                freq.float().tolist(),
                labels.tolist(),
                0.5,
                0.1,
                0.01,
                0.02,
                [1, 2, 3],
            ),
        )
    )
    for actual, expected in calls:
        _assert_core_equivalent(actual, expected)


def test_cross_band_equivalence() -> None:
    """Parent-index cross-band PAC matches the direct core result."""
    slow = torch.tensor([0.2, 1.0], dtype=torch.float64)
    phase = torch.tensor([0.3, 0.5, 0.7], dtype=torch.float64)
    amp = torch.ones(3, dtype=torch.float64)
    parent = torch.tensor([0, 1, 0])
    actual = prin.pytorch_cross_band_coupling(slow, phase, amp, parent)
    raw = _prin_core.pytorch_cross_band_coupling(
        slow.float().tolist(),
        phase.float().tolist(),
        amp.float().tolist(),
        parent.tolist(),
        0.3,
        1e-6,
    )
    _assert_core_equivalent(actual, raw)


def _dense_args() -> tuple[object, ...]:
    phase = torch.tensor([[0.1, 0.5, 1.0]], dtype=torch.float64)
    amp = torch.ones_like(phase)
    frequencies = [torch.tensor([0.2], dtype=torch.float64) for _ in range(3)]
    weights = [torch.zeros((1, 1), dtype=torch.float64) for _ in range(3)]
    return phase, amp, *frequencies, *weights, 0.2, 0.3, 0.4


def test_discrete_family_core_wrapper_equivalence() -> None:
    """Base and full discrete wrappers match direct compiled-core calls."""
    args = _dense_args()
    actual = prin.pytorch_fused_discrete_step(*args, 1, 1, 1)
    tensors = args[:8]
    raw = _prin_core.pytorch_fused_discrete_step(
        *[value.float().reshape(-1).tolist() for value in tensors],
        *args[8:],
        1,
        1,
        1,
        0.01,
    )
    _assert_core_equivalent(actual, raw)

    pac = (
        torch.zeros((1, 2), dtype=torch.float64),
        torch.zeros(1, dtype=torch.float64),
        torch.zeros((1, 2), dtype=torch.float64),
        torch.zeros(1, dtype=torch.float64),
    )
    full_args = (*args[:8], *pac, *args[8:])
    full = prin.pytorch_fused_discrete_step_full(
        *full_args, n_delta=1, n_theta=1, n_gamma=1
    )
    raw_full = _prin_core.pytorch_fused_discrete_step_full(
        *[value.float().reshape(-1).tolist() for value in full_args[:12]],
        *full_args[12:],
        0.01,
        1,
        1,
        1,
    )
    _assert_core_equivalent(full, raw_full)


def test_sparse_matrix_invariants_and_csr_step() -> None:
    """Rust random matrices have zero diagonals, symmetry, and CSR equivalence."""
    dense = prin.sparse_coupling_matrix(8, sparsity=0.5, symmetric=True, seed=42)
    csr = prin.sparse_coupling_matrix_csr(8, sparsity=0.5, symmetric=True, seed=42)
    assert dense.shape == (8, 8)
    assert csr.layout == torch.sparse_csr
    assert torch.count_nonzero(torch.diagonal(dense)) == 0
    torch.testing.assert_close(dense, dense.T)
    torch.testing.assert_close(dense, csr.to_dense())
    phase = torch.linspace(0.0, 1.0, 8)
    actual = prin.csr_coupling_step(phase, csr)
    raw = _prin_core.csr_coupling_step(
        phase.double().tolist(),
        csr.crow_indices().tolist(),
        csr.col_indices().tolist(),
        csr.values().double().tolist(),
    )
    _assert_core_equivalent(actual, raw)


def test_neighbor_invariants_and_seed_object_flow() -> None:
    """Neighbor generation accepts Seed and is deterministic and non-self."""
    seed = _prin_core.Seed(17, 9)
    first = prin.build_knn_neighbors(10, 3, seed=seed)
    second = prin.build_knn_neighbors(10, 3, seed=_prin_core.Seed(17, 9))
    assert torch.equal(first, second)
    for row, values in enumerate(first):
        assert row not in values.tolist()
        assert len(set(values.tolist())) == 3


@pytest.mark.parametrize(
    ("call", "message"),
    [
        (
            lambda: prin.pytorch_mean_field_rk4_step(
                torch.tensor([]), torch.tensor([]), torch.tensor([]), 1.0, 0.1, 0.1, 0.1
            ),
            "non-empty",
        ),
        (
            lambda: prin.pytorch_hierarchical_order_param(torch.ones(3), [2]),
            "dimension mismatch",
        ),
        (lambda: prin.build_knn_neighbors(2, 2), "neighbor count"),
        (lambda: prin.sparse_coupling_matrix(2, sparsity=1.0), "sparsity"),
    ],
)
def test_value_errors(call: Callable[[], object], message: str) -> None:
    """Owner validation maps to actionable Python ValueError instances."""
    with pytest.raises(ValueError, match=message):
        call()
