"""PRINet 3.0-compatible hybrid-model family stubs (D-2.2 dispositions).

The six symbols in this module are trainable ``torch.nn.Module`` subclasses
with ``nn.Linear`` projections in the PRINet 3.0 reference. A faithful
implementation requires net-new trainable Rust numerics + autodiff, which
WP-036 prohibits ("thin marshalling only", "no numerics added"). They
receive documented D-2.2 dispositions with Migration-Guide rows, subject
to S2 audit veto.

This is consistent with the 0141B rows 31-42 precedent (the trainable
``nn/layers.py`` / ``inhibition.py`` symbols with no Rust owner).

No numerical computation is introduced (Coding Standards Sec. 1.2).
"""

from __future__ import annotations

from typing import Any, NoReturn

__all__ = [
    "AlternatingOptimizer",
    "HybridCLEVRN",
    "HybridPRINet",
    "HybridPRINetV2CLEVRN",
    "InterleavedHybridPRINet",
    "TemporalHybridPRINet",
]


def _raise_disposition(symbol: str) -> NoReturn:
    """Raise the typed D-2.2 disposition for a hybrid-model symbol."""
    raise NotImplementedError(
        f"{symbol} is a deferred-rebuild symbol (WP-036 D-2.2). "
        "Trainable nn.Module with nn.Linear projections; needs a "
        "trainable-layer rebuild in a future WP. "
        "See the Migration Guide for the disposition."
    )


class HybridPRINet:
    """Deferred-rebuild stub for the end-to-end hybrid PRINet model.

    PRINet 3.0 ``nn.hybrid.HybridPRINet``: chains LOBM (oscillatory
    encoding) -> PhaseToRate (sparse conversion) -> GRIM (Transformer
    rate integration) -> classifier head. All stages contain trainable
    ``nn.Linear`` projections.

    Raises:
        NotImplementedError: Always on construction.
    """

    def __init__(self, *_args: Any, **_kwargs: Any) -> None:
        """Raise the D-2.2 disposition."""
        _raise_disposition("HybridPRINet")


class HybridCLEVRN:
    """Deferred-rebuild stub for the hybrid CLEVR-N classifier.

    PRINet 3.0 ``nn.hybrid.HybridCLEVRN``: scene + query -> hybrid
    oscillatory encoding -> binary classification. Contains trainable
    ``nn.Linear`` projections.

    Raises:
        NotImplementedError: Always on construction.
    """

    def __init__(self, *_args: Any, **_kwargs: Any) -> None:
        """Raise the D-2.2 disposition."""
        _raise_disposition("HybridCLEVRN")


class HybridPRINetV2CLEVRN:
    """Deferred-rebuild stub for the HybridPRINetV2 CLEVR-N adapter.

    PRINet 3.0 ``nn.hybrid.HybridPRINetV2CLEVRN``: adapter wrapping
    HybridPRINetV2 for CLEVR-N scene + query classification. Contains
    trainable ``nn.Linear`` projections.

    Raises:
        NotImplementedError: Always on construction.
    """

    def __init__(self, *_args: Any, **_kwargs: Any) -> None:
        """Raise the D-2.2 disposition."""
        _raise_disposition("HybridPRINetV2CLEVRN")


class InterleavedHybridPRINet:
    """Deferred-rebuild stub for the interleaved hybrid model.

    PRINet 3.0 ``nn.hybrid.InterleavedHybridPRINet``: interleaves
    oscillatory and rate-coded layers. Contains trainable ``nn.Linear``
    projections.

    Raises:
        NotImplementedError: Always on construction.
    """

    def __init__(self, *_args: Any, **_kwargs: Any) -> None:
        """Raise the D-2.2 disposition."""
        _raise_disposition("InterleavedHybridPRINet")


class TemporalHybridPRINet:
    """Deferred-rebuild stub for the temporal hybrid model.

    PRINet 3.0 ``nn.hybrid.TemporalHybridPRINet``: extends the hybrid
    architecture with temporal dynamics across frames. Contains trainable
    ``nn.Linear`` projections.

    Raises:
        NotImplementedError: Always on construction.
    """

    def __init__(self, *_args: Any, **_kwargs: Any) -> None:
        """Raise the D-2.2 disposition."""
        _raise_disposition("TemporalHybridPRINet")


class AlternatingOptimizer:
    """Deferred-rebuild stub for the alternating optimizer.

    PRINet 3.0 ``nn.hybrid.AlternatingOptimizer``: joint training of
    oscillatory and rate-coded parameter groups with separate learning
    rates. Contains trainable parameter management.

    Raises:
        NotImplementedError: Always on construction.
    """

    def __init__(self, *_args: Any, **_kwargs: Any) -> None:
        """Raise the D-2.2 disposition."""
        _raise_disposition("AlternatingOptimizer")
