"""Integration tests for the PyO3/DLPack bridge spike (WP-003)."""

from __future__ import annotations

import ctypes

import prin._prin_core as core
import prin.dlpack as dlpack
import pytest
import torch


class _DLContext(ctypes.Structure):
    _fields_ = [("device_type", ctypes.c_int32), ("device_id", ctypes.c_int32)]


class _DLDataType(ctypes.Structure):
    _fields_ = [
        ("code", ctypes.c_uint8),
        ("bits", ctypes.c_uint8),
        ("lanes", ctypes.c_uint16),
    ]


class _DLTensor(ctypes.Structure):
    _fields_ = [
        ("data", ctypes.c_void_p),
        ("ctx", _DLContext),
        ("ndim", ctypes.c_int32),
        ("dtype", _DLDataType),
        ("shape", ctypes.POINTER(ctypes.c_int64)),
        ("strides", ctypes.POINTER(ctypes.c_int64)),
        ("byte_offset", ctypes.c_uint64),
    ]


class _DLManagedTensor(ctypes.Structure):
    _fields_ = [
        ("dl_tensor", _DLTensor),
        ("manager_ctx", ctypes.c_void_p),
        ("deleter", ctypes.c_void_p),
    ]


def _dlpack_capsule_with_negative_shape() -> tuple[object, tuple[ctypes._CData, ...]]:
    """Return a raw ``dltensor`` PyCapsule whose single dimension is negative.

    The caller must keep the returned backing objects alive for as long as the
    capsule is used; otherwise the C pointers inside the DLPack descriptor may
    be freed before the bridge reads them.
    """
    data = (ctypes.c_float * 1)(1.0)
    shape = (ctypes.c_int64 * 1)(-1)
    strides = (ctypes.c_int64 * 1)(1)
    dtype = _DLDataType(code=2, bits=32, lanes=1)
    ctx = _DLContext(device_type=1, device_id=0)
    tensor = _DLTensor(
        data=ctypes.cast(data, ctypes.c_void_p),
        ctx=ctx,
        ndim=1,
        dtype=dtype,
        shape=shape,
        strides=strides,
        byte_offset=0,
    )
    managed = _DLManagedTensor(
        dl_tensor=tensor,
        manager_ctx=None,
        deleter=None,
    )

    py_capsule_new = ctypes.pythonapi.PyCapsule_New
    py_capsule_new.argtypes = [ctypes.c_void_p, ctypes.c_char_p, ctypes.c_void_p]
    py_capsule_new.restype = ctypes.py_object
    cap = py_capsule_new(ctypes.byref(managed), b"dltensor", None)
    # Keep the managed tensor and its arrays alive for the lifetime of the test.
    return cap, (managed, data, shape, strides)


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

    def test_negative_shape_dimension_rejected(self) -> None:
        cap, _refs = _dlpack_capsule_with_negative_shape()
        with pytest.raises(ValueError, match=r"negative shape dimension -1 at index 0"):
            core.dlpack_negate(cap)


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
