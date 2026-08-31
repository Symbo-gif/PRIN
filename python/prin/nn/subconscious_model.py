"""PRINet 3.0 ``nn.subconscious_model`` import-path compatibility.

Re-exports :class:`SubconsciousController` and :func:`retrain_controller`
so that the reference ``from prinet.nn.subconscious_model import ...``
form resolves under the adapted ``prin.nn.subconscious_model`` path.
"""

from __future__ import annotations

from prin.subconscious_compat import (
    SubconsciousController,
    SubconsciousDaemon,
    SubconsciousState,
)
from prin.training_hooks import retrain_controller

__all__ = [
    "SubconsciousController",
    "SubconsciousDaemon",
    "SubconsciousState",
    "retrain_controller",
]
