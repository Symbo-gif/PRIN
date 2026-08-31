"""Phase-3 profiling and gradient-flow support over current PRIN models.

The model adapters delegate phase and slot computations to Rust-backed PRIN
components; profiling and hook collection remain Python experiment tooling.
"""

from __future__ import annotations

from phase2_scaling_analysis import (
    _build_pt,
    _build_sa,
    _gen,
    _TrackerAdapter,
    _train_model,
)

__all__ = [
    "_TrackerAdapter",
    "_build_pt",
    "_build_sa",
    "_gen",
    "_train_model",
]
