"""Tensor decomposition (PRINet-3.0-compatible surface).

Thin wrappers over the Rust ``prin-tensor`` owners (WP-014), exposed via the
compiled ``prin._prin_core`` extension: Tucker / HOSVD (:class:`PolyadicTensor`)
and CP / PARAFAC via alternating least squares (:class:`CPDecomposition`). No
numerics live here — see ``crates/prin-tensor/`` for the algorithms and their
documented deviations from the PRINet 3.0 reference (``core/decomposition.py``).

Numerical note: ``prin-tensor`` computes every decomposition path in
``float64``. The ``dtype``/``device`` constructor arguments are preserved for
call-site compatibility but only control the dtype/device of the tensors these
wrappers *return*; the fit itself is always ``float64`` on CPU.
"""

from __future__ import annotations

import torch
from torch.utils.dlpack import from_dlpack

from prin._prin_core import CPDecompositionBridge, PolyadicTensorBridge

__all__ = ["CPDecomposition", "DecompositionError", "PolyadicTensor"]


class DecompositionError(RuntimeError):
    """Raised when a decomposition result is read before ``decompose()``.

    Mirrors PRINet 3.0's ``core.decomposition.DecompositionError`` for the
    "no decomposition performed yet" case.
    """


def _as_input(tensor: torch.Tensor) -> torch.Tensor:
    """Return ``tensor`` as a detached, contiguous, CPU ``float64`` view."""
    return tensor.detach().to(dtype=torch.float64, device="cpu").contiguous()


class PolyadicTensor:
    """Tucker (HOSVD) tensor decomposition.

    Decomposes an N-way tensor ``X`` into a core tensor ``G`` and orthogonal
    per-mode factor matrices ``U^(n)`` such that
    ``X ~= G x_1 U^(1) x_2 U^(2) ... x_N U^(N)`` (mode-n products).

    Args:
        shape: Shape of the input tensor ``(I_1, ..., I_N)``.
        rank: Number of singular vectors to retain per mode. Clamped per mode
            to the mode-``n`` unfolding rank, matching the PRINet 3.0
            reference.
        device: Torch device for the returned tensors. Defaults to CPU.
        dtype: Data type for the returned tensors. Defaults to ``torch.float32``
            (the fit itself is always ``float64``).

    Examples:
        >>> import torch
        >>> from prin.tensor import PolyadicTensor
        >>> pt = PolyadicTensor(shape=(4, 4, 4), rank=2)
        >>> pt.decompose(torch.randn(4, 4, 4))
        >>> pt.reconstruct().shape
        torch.Size([4, 4, 4])
    """

    def __init__(
        self,
        shape: tuple[int, ...],
        rank: int,
        device: torch.device | str | None = None,
        dtype: torch.dtype = torch.float32,
    ) -> None:
        """Configure (but do not run) the Tucker decomposition."""
        self._bridge = PolyadicTensorBridge(list(shape), rank)
        self._dtype = dtype
        self._device = (
            torch.device(device) if device is not None else torch.device("cpu")
        )

    @property
    def shape(self) -> tuple[int, ...]:
        """Shape of the tensor this decomposition targets."""
        return tuple(self._bridge.shape)

    @property
    def rank(self) -> int:
        """Target rank for the decomposition."""
        return self._bridge.rank

    def _restore(self, capsule: object) -> torch.Tensor:
        """Decode a DLPack capsule to the configured dtype/device."""
        return from_dlpack(capsule).to(dtype=self._dtype, device=self._device)

    def decompose(self, tensor: torch.Tensor) -> None:
        """Fit the HOSVD to ``tensor`` (shape must match ``self.shape``).

        Raises:
            ValueError: If ``tensor``'s shape does not match ``self.shape`` or
                the decomposition fails a ``prin-tensor`` guard.
        """
        self._bridge.decompose(_as_input(tensor))

    def reconstruct(self) -> torch.Tensor:
        """Reconstruct ``G x_1 U^(1) ...`` from the fitted factors.

        Raises:
            DecompositionError: If :meth:`decompose` has not been called.
        """
        if not self._bridge.is_decomposed:
            raise DecompositionError(
                "no decomposition performed yet; call decompose() first"
            )
        return self._restore(self._bridge.reconstruct())

    @property
    def core(self) -> torch.Tensor:
        """Core tensor ``G`` from the Tucker decomposition.

        Raises:
            DecompositionError: If :meth:`decompose` has not been called.
        """
        if not self._bridge.is_decomposed:
            raise DecompositionError(
                "no decomposition performed yet; call decompose() first"
            )
        return self._restore(self._bridge.core())

    @property
    def factors(self) -> list[torch.Tensor]:
        """Orthogonal factor matrices ``U^(n)``, one per mode.

        Raises:
            DecompositionError: If :meth:`decompose` has not been called.
        """
        if not self._bridge.is_decomposed:
            raise DecompositionError(
                "no decomposition performed yet; call decompose() first"
            )
        return [self._restore(cap) for cap in self._bridge.factors()]


class CPDecomposition:
    """Canonical Polyadic (CP / CANDECOMP-PARAFAC) decomposition via ALS.

    Decomposes a tensor into a sum of ``rank`` rank-1 components
    ``X ~= sum_r lambda_r * outer(a_r, b_r, ...)``, fitted by alternating
    least squares.

    Args:
        shape: Shape of the input tensor.
        rank: Number of rank-1 components.
        max_iter: Maximum ALS iterations.
        tol: Convergence tolerance on the relative change in reconstruction
            error.
        device: Torch device for the returned tensors. Defaults to CPU.
        dtype: Data type for the returned tensors. Defaults to
            ``torch.float32`` (the fit itself is always ``float64``).
        seed_counter: Counter half of the deterministic ``Seed`` for factor
            initialization (Coding Standards §1.3); PRINet 3.0 used an
            unseeded ``torch.randn``, a documented ``prin-tensor`` deviation.
        seed_key: Key half of the deterministic ``Seed``.

    Examples:
        >>> import torch
        >>> from prin.tensor import CPDecomposition
        >>> cp = CPDecomposition(shape=(6, 6, 6), rank=3)
        >>> cp.decompose(torch.randn(6, 6, 6))
        >>> cp.weights.shape
        torch.Size([3])
    """

    def __init__(
        self,
        shape: tuple[int, ...],
        rank: int,
        max_iter: int = 100,
        tol: float = 1e-6,
        device: torch.device | str | None = None,
        dtype: torch.dtype = torch.float32,
        seed_counter: int = 0,
        seed_key: int = 0,
    ) -> None:
        """Configure (but do not run) the CP decomposition."""
        self._bridge = CPDecompositionBridge(
            list(shape), rank, max_iter, tol, seed_counter, seed_key
        )
        self._dtype = dtype
        self._device = (
            torch.device(device) if device is not None else torch.device("cpu")
        )

    @property
    def shape(self) -> tuple[int, ...]:
        """Shape of the tensor this decomposition targets."""
        return tuple(self._bridge.shape)

    @property
    def rank(self) -> int:
        """Number of rank-1 components."""
        return self._bridge.rank

    def _restore(self, capsule: object) -> torch.Tensor:
        """Decode a DLPack capsule to the configured dtype/device."""
        return from_dlpack(capsule).to(dtype=self._dtype, device=self._device)

    def decompose(self, tensor: torch.Tensor) -> None:
        """Fit the CP decomposition via ALS to ``tensor``.

        Raises:
            ValueError: If ``tensor``'s shape does not match ``self.shape``,
                or ALS does not converge within ``max_iter`` (a ``prin-tensor``
                guard; PRINet 3.0 instead returned the last iterate).
        """
        self._bridge.decompose(_as_input(tensor))

    def reconstruct(self) -> torch.Tensor:
        """Reconstruct ``sum_r lambda_r * outer(a_r, b_r, ...)`` from the factors.

        Raises:
            DecompositionError: If :meth:`decompose` has not been called.
        """
        if not self._bridge.is_decomposed:
            raise DecompositionError(
                "no decomposition performed yet; call decompose() first"
            )
        return self._restore(self._bridge.reconstruct())

    @property
    def weights(self) -> torch.Tensor:
        """Component weights ``lambda`` of shape ``(rank,)``.

        Raises:
            DecompositionError: If :meth:`decompose` has not been called.
        """
        if not self._bridge.is_decomposed:
            raise DecompositionError(
                "no decomposition performed yet; call decompose() first"
            )
        return self._restore(self._bridge.weights())

    @property
    def factors(self) -> list[torch.Tensor]:
        """Factor matrices of shape ``(I_n, rank)``, one per mode.

        Raises:
            DecompositionError: If :meth:`decompose` has not been called.
        """
        if not self._bridge.is_decomposed:
            raise DecompositionError(
                "no decomposition performed yet; call decompose() first"
            )
        return [self._restore(cap) for cap in self._bridge.factors()]
