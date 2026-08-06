"""High-level DLPack bridge between PyTorch and the PRIN Rust core.

This module is intentionally thin: it only converts PyTorch tensors into
DLPack capsules, calls into the audited Rust extension, and converts the
result back to ``torch.Tensor``. No numerics live in Python.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

import torch
from torch.utils.dlpack import from_dlpack

from prin._prin_core import (
    dlpack_negate,
    dlpack_negate_batched,
    dlpack_round_trip,
)

if TYPE_CHECKING:
    from collections.abc import Sequence


def negate(tensor: torch.Tensor) -> torch.Tensor:
    """Return a new CPU tensor containing the element-wise negation.

    Args:
        tensor: A contiguous CPU ``torch.Tensor`` with dtype ``float32`` or
            ``float64``.

    Returns:
        A new ``torch.Tensor`` with the same shape and dtype as ``tensor``.

    Raises:
        ValueError: If the input is on another device, is not contiguous, or
            uses an unsupported dtype.
    """
    return from_dlpack(dlpack_negate(tensor))


def round_trip(tensor: torch.Tensor) -> torch.Tensor:
    """Copy a tensor through the DLPack bridge without modifying values.

    This is a zero-copy exchange smoke test: the data is read from the input
    capsule and wrapped in a new Rust-owned capsule.

    Args:
        tensor: A contiguous CPU ``torch.Tensor`` with dtype ``float32`` or
            ``float64``.

    Returns:
        A new ``torch.Tensor`` with the same values, shape, and dtype.
    """
    return from_dlpack(dlpack_round_trip(tensor))


def negate_batched(tensors: Sequence[torch.Tensor]) -> list[torch.Tensor]:
    """Negate a batch of tensors through one Rust boundary call each.

    Args:
        tensors: A sequence of contiguous CPU ``torch.Tensor`` values with
            dtype ``float32`` or ``float64``.

    Returns:
        A list of negated ``torch.Tensor`` values.
    """
    return [from_dlpack(cap) for cap in dlpack_negate_batched(list(tensors))]
