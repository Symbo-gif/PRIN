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

``DiscreteDeltaThetaGamma`` is the last remaining stub here: its audited Rust
owner (``prin_train::bands::DiscreteDeltaThetaGamma``, WP-022) is composed by
the real ``DiscreteDeltaThetaGammaLayer`` but is not independently bound to
Python. That standalone binding remains assigned to WP-036B.
"""

from __future__ import annotations

from typing import Any, NoReturn

from .autoencoders import (
    DenseAutoencoder,
    PhaseToRateAutoencoder,
    PhaseToRateConverter,
)
from .hierarchical_layers import (
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


def _raise_disposition(symbol: str, detail: str) -> NoReturn:
    """Raise the typed D-2.2 disposition error for a deferred trainable layer."""
    raise NotImplementedError(
        f"{symbol} is a deferred-rebuild symbol (WP-036 D-2.2). {detail} "
        "It is a trainable component with no faithful non-numeric PRIN "
        "implementation in WP-036 S1; the rebuild is owned by a future work "
        "package. See the Migration Guide for the disposition and the owning WP."
    )


class DiscreteDeltaThetaGamma:
    """Deferred-binding stub for the discrete three-band trainable network.

    PRINet 3.0 ``core.propagation.networks.DiscreteDeltaThetaGamma``: a
    discrete-time delta/theta/gamma network with learned coupling weights and
    multiplicative phase-amplitude-coupling gates.

    The Rust owner ``prin_train::bands::DiscreteDeltaThetaGamma`` exists and is
    audited (WP-022) but has no PyO3 binding — an explicit out-of-scope
    discovery recorded since WP-025 (``crates/prin-py/src/bindings/train.rs``
    module docs). Binding it (a bridge plus a ``torch.autograd.Function`` with
    float64 gradcheck) is deferred to the trainable-layer rebuild WP; this stub
    keeps the symbol resolvable so the WP-036 S1 172-symbol surface is
    complete. S2 (session 0142) retains veto.

    Raises:
        NotImplementedError: Always on construction.
    """

    def __init__(self, *_args: Any, **_kwargs: Any) -> None:
        """Raise the D-2.2 disposition."""
        _raise_disposition(
            "DiscreteDeltaThetaGamma",
            "Audited Rust owner (prin_train::bands, WP-022) exists but is "
            "unbound; the PyO3 bridge is a recorded out-of-scope discovery.",
        )
