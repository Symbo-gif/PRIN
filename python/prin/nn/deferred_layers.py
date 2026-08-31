"""PRINet 3.0-compatible deferred-layer compatibility exports.

WP-036A sub-pass 0144A1 replaces the inhibition/sparsification-family stubs
(``FeedforwardInhibition``, ``DentateGyrusConverter``, ``DGLayer``,
``oscillatory_weight_init``, and ``SparsityRegularizationLoss``) with real
Rust-backed exports from :mod:`prin.nn.inhibition_layers`. Sub-pass 0144A2
replaces the phase-to-rate / autoencoder family (``PhaseToRateConverter``,
``PhaseToRateAutoencoder``, ``DenseAutoencoder``) with real Rust-backed
exports from :mod:`prin.nn.autoencoders`. Sub-pass 0144A3 replaces the
hierarchical, PAC, and discrete-layer family with exports from
:mod:`prin.nn.hierarchical_layers`. Sub-pass 0144A4 replaces ``PRINetModel``
(Rust-backed) and ``compile_model`` (pure-Python ``torch.compile``
passthrough, WP-036A D-2) with exports from :mod:`prin.nn.model`.

WP-036C S1 sub-pass 0144M1 (plan amendment #40) replaces the final
``DiscreteDeltaThetaGamma`` stub with the real Rust-backed export from
:mod:`prin.nn.hierarchical_layers`: a new ``DiscreteDeltaThetaGammaBridge``
PyO3 binding over the audited Burn owner ``prin_train::bands`` (WP-022), with
``order_parameters`` / ``pac_index`` added to that module. The ``test_y2q1``
strict port exercises its full ``step`` / ``integrate`` / diagnostics surface.
"""

from __future__ import annotations

from .autoencoders import (
    DenseAutoencoder,
    PhaseToRateAutoencoder,
    PhaseToRateConverter,
)
from .hierarchical_layers import (
    DiscreteDeltaThetaGamma,
    DiscreteDeltaThetaGammaLayer,
    HierarchicalResonanceLayer,
    PhaseAmplitudeCouplingLayer,
)
from .inhibition_layers import (
    DentateGyrusConverter,
    DGLayer,
    FeedforwardInhibition,
    SparsityRegularizationLoss,
    oscillatory_weight_init,
)
from .model import PRINetModel, compile_model

__all__ = [
    "DGLayer",
    "DenseAutoencoder",
    "DentateGyrusConverter",
    "DiscreteDeltaThetaGamma",
    "DiscreteDeltaThetaGammaLayer",
    "FeedforwardInhibition",
    "HierarchicalResonanceLayer",
    "PRINetModel",
    "PhaseAmplitudeCouplingLayer",
    "PhaseToRateAutoencoder",
    "PhaseToRateConverter",
    "SparsityRegularizationLoss",
    "compile_model",
    "oscillatory_weight_init",
]
