"""PRINet 3.0-compatible deferred-layer compatibility exports.

WP-036A sub-pass 0144A1 replaces the inhibition/sparsification-family stubs
(``FeedforwardInhibition``, ``DentateGyrusConverter``, ``DGLayer``,
``oscillatory_weight_init``, and ``SparsityRegularizationLoss``) with real
Rust-backed exports from :mod:`prin.nn.inhibition_layers`. Sub-pass 0144A2
replaces the phase-to-rate / autoencoder family (``PhaseToRateConverter``,
``PhaseToRateAutoencoder``, ``DenseAutoencoder``) with real Rust-backed
exports from :mod:`prin.nn.autoencoders`. The remaining symbols retain their
documented D-2.2 dispositions until their assigned WP-036A sub-pass.

Two symbols are a narrower case: ``DiscreteDeltaThetaGamma`` and
``DiscreteDeltaThetaGammaLayer``. The discrete three-band network core has an
audited Rust owner (``prin_train::bands::DiscreteDeltaThetaGamma``, WP-022) but
no PyO3 binding — an explicit out-of-scope discovery recorded since WP-025
(``crates/prin-py/src/bindings/train.rs`` module docs). Binding it (a
``PyResonanceLayerBridge``-style bridge plus a ``torch.autograd.Function`` and
float64 gradcheck) is deferred to the same trainable-layer rebuild WP; the
``DiscreteDeltaThetaGammaLayer`` wrapper additionally needs the net-new
``proj_phase`` / ``proj_amplitude`` projections that have no Rust owner.
"""

from __future__ import annotations

from typing import Any, NoReturn

from .autoencoders import (
    DenseAutoencoder,
    PhaseToRateAutoencoder,
    PhaseToRateConverter,
)
from .inhibition_layers import (
    DentateGyrusConverter,
    DGLayer,
    FeedforwardInhibition,
    SparsityRegularizationLoss,
    oscillatory_weight_init,
)

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


class HierarchicalResonanceLayer:
    """Deferred-rebuild stub for the hierarchical resonance layer.

    PRINet 3.0 ``nn.layers.HierarchicalResonanceLayer``: a trainable
    ``nn.Module`` over a delta/theta/gamma network with learnable input
    projections and per-band phase-amplitude-coupling depths. No Rust owner
    (WP-023 rebuilt only the non-trainable band dynamics).

    Raises:
        NotImplementedError: Always on construction.
    """

    def __init__(self, *_args: Any, **_kwargs: Any) -> None:
        """Raise the D-2.2 disposition."""
        _raise_disposition(
            "HierarchicalResonanceLayer",
            "Trainable nn.Module with learnable projections + PAC depths.",
        )


class PhaseAmplitudeCouplingLayer:
    """Deferred-rebuild stub for the trainable phase-amplitude-coupling layer.

    PRINet 3.0 ``nn.layers.PhaseAmplitudeCouplingLayer``: a trainable
    ``nn.Module`` over :class:`~prin.dynamics.PhaseAmplitudeCoupling` with a
    learnable modulation depth. The non-trainable coupling is Rust-owned
    (WP-013); the learnable-depth wrapper is not.

    Raises:
        NotImplementedError: Always on construction.
    """

    def __init__(self, *_args: Any, **_kwargs: Any) -> None:
        """Raise the D-2.2 disposition."""
        _raise_disposition(
            "PhaseAmplitudeCouplingLayer",
            "Trainable nn.Module with a learnable modulation depth.",
        )


class PRINetModel:
    """Deferred-rebuild stub for the top-level trainable PRINet model.

    PRINet 3.0 ``nn.layers.PRINetModel``: the complete end-to-end trainable
    model (projection -> hierarchical dynamics -> readout). No Rust owner.

    Raises:
        NotImplementedError: Always on construction.
    """

    def __init__(self, *_args: Any, **_kwargs: Any) -> None:
        """Raise the D-2.2 disposition."""
        _raise_disposition(
            "PRINetModel",
            "Top-level trainable model, no Rust owner.",
        )


def compile_model(*_args: Any, **_kwargs: Any) -> NoReturn:
    """Reject calls to the deferred ``torch.compile`` model helper.

    PRINet 3.0 ``nn.layers.compile_model``: wraps a model in ``torch.compile``
    with PRINet-specific options. Depends on the trainable model stack.

    Raises:
        NotImplementedError: Always.
    """
    _raise_disposition(
        "compile_model",
        "torch.compile helper for the trainable model stack, no Rust owner.",
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


class DiscreteDeltaThetaGammaLayer:
    """Deferred-rebuild stub for the discrete three-band trainable layer.

    PRINet 3.0 ``nn.layers.DiscreteDeltaThetaGammaLayer``: a trainable
    ``nn.Module`` wrapping :class:`DiscreteDeltaThetaGamma` with net-new
    learnable ``proj_phase`` / ``proj_amplitude`` input projections. The
    dynamics core has an unbound Rust owner (see
    :class:`DiscreteDeltaThetaGamma`); the projections have none.

    Raises:
        NotImplementedError: Always on construction.
    """

    def __init__(self, *_args: Any, **_kwargs: Any) -> None:
        """Raise the D-2.2 disposition."""
        _raise_disposition(
            "DiscreteDeltaThetaGammaLayer",
            "Trainable nn.Module over the unbound DiscreteDeltaThetaGamma core "
            "plus net-new learnable projections with no Rust owner.",
        )
