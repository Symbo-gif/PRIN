"""Integration tests for the PyO3/DLPack bridge spike (WP-003)."""

from __future__ import annotations

import prin._prin_core as core
import prin.dlpack as dlpack
import pytest
import torch


@pytest.fixture(
    params=[
        (torch.float32, "float32"),
        (torch.float64, "float64"),
    ],
    ids=["float32", "float64"],
)
def dtype_pair(request: pytest.FixtureRequest) -> tuple[torch.dtype, str]:
    """Yield (dtype, label) pairs supported by the DLPack bridge."""
    return request.param  # type: ignore[return-value]


class TestDlpackNegate:
    """CPU round-trip correctness and dtype/device validation."""

    def test_negate_1d(self, dtype_pair: tuple[torch.dtype, str]) -> None:
        dtype, _ = dtype_pair
        x = torch.tensor([1.0, -2.0, 3.0], dtype=dtype)
        y = dlpack.negate(x)
        assert y.shape == x.shape
        assert y.dtype == x.dtype
        torch.testing.assert_close(y, -x)

    def test_negate_2d(self, dtype_pair: tuple[torch.dtype, str]) -> None:
        dtype, _ = dtype_pair
        x = torch.tensor([[1.0, 2.0], [-3.0, 4.0]], dtype=dtype)
        y = dlpack.negate(x)
        assert y.shape == x.shape
        assert y.dtype == x.dtype
        torch.testing.assert_close(y, -x)

    def test_negate_batched(self, dtype_pair: tuple[torch.dtype, str]) -> None:
        dtype, _ = dtype_pair
        x = torch.tensor([1.0, -2.0, 3.0], dtype=dtype)
        ys = dlpack.negate_batched([x, x, x])
        assert len(ys) == 3
        for y in ys:
            assert y.dtype == x.dtype
            torch.testing.assert_close(y, -x)

    def test_round_trip(self, dtype_pair: tuple[torch.dtype, str]) -> None:
        dtype, _ = dtype_pair
        x = torch.tensor([1.0, -2.0, 3.0], dtype=dtype)
        y = dlpack.round_trip(x)
        assert y.shape == x.shape
        assert y.dtype == x.dtype
        torch.testing.assert_close(y, x)

    def test_non_contiguous_rejected(self) -> None:
        x = torch.tensor([[1.0, 2.0], [3.0, 4.0]]).t()
        with pytest.raises(ValueError, match="non-contiguous"):
            dlpack.negate(x)

    def test_integer_dtype_rejected(self) -> None:
        x = torch.tensor([1, 2, 3])
        with pytest.raises(ValueError, match="unsupported DLPack dtype"):
            dlpack.negate(x)

    def test_double_negate_from_raw_capsule(self) -> None:
        x = torch.tensor([1.0, -2.0, 3.0])
        cap1 = core.dlpack_negate(x)
        intermediate = torch.from_dlpack(cap1)
        cap2 = core.dlpack_negate(intermediate)
        y = torch.from_dlpack(cap2)
        torch.testing.assert_close(y, x)


class TestDlpackErrors:
    """Ownership and error-path coverage."""

    def test_batched_empty(self) -> None:
        assert dlpack.negate_batched([]) == []

    def test_rejects_versioned_or_bad_capsule(self) -> None:
        bad = object()
        with pytest.raises((TypeError, ValueError, AttributeError)):
            core.dlpack_negate(bad)


@pytest.mark.slow
class TestDlpackBenchmarks:
    """Microbenchmarks measuring the Rust/Python boundary overhead."""

    def test_negate_round_trip_latency(
        self,
        benchmark: pytest.Fixture,  # pytest-benchmark fixture
        dtype_pair: tuple[torch.dtype, str],
    ) -> None:
        dtype, _ = dtype_pair
        size = 2**14
        x = torch.randn(size, dtype=dtype)

        def round_trip() -> torch.Tensor:
            return dlpack.negate(x)

        result = benchmark(round_trip)
        assert result.shape == x.shape
        assert result.dtype == x.dtype

    def test_negate_batched_latency(
        self,
        benchmark: pytest.Fixture,
        dtype_pair: tuple[torch.dtype, str],
    ) -> None:
        dtype, _ = dtype_pair
        batch = [torch.randn(2**12, dtype=dtype) for _ in range(8)]

        def batched() -> list[torch.Tensor]:
            return dlpack.negate_batched(batch)

        result = benchmark(batched)
        assert len(result) == len(batch)
