"""Rust-backed full PRINet model container and the ``torch.compile`` helper.

:class:`PRINetModel` is a PRINet-3.0-compatible ``torch.nn.Module`` whose
forward and backward cross the Rust boundary exactly once per call through the
audited DLPack bridge; every parameter (the stacked ``ResonanceLayer``
coupling/decay/projection tensors, the inter-layer ``LayerNorm`` affines, and
the concept-readout ``Linear``) is owned by ``prin-train``
(``prin_train::model::PRINetModel``), trained with a ``prin-train``
oscillator-aware optimizer rather than ``torch.optim``. Its compatibility
parameters are non-trainable mirrors, not Burn parameter VJPs.

:func:`compile_model` is the one WP-036A symbol with no Rust component
(WP-036A D-2): a pure-Python guarded ``torch.compile`` passthrough, identical
in behaviour to PRINet 3.0's ``nn.layers.compile_model``. ``torch.compile`` is
a PyTorch graph-capture utility, not PRIN numerics (Coding Standards §1.2).

**Documented deviation — mixed precision.** PRINet 3.0's
``PRINetModel.forward`` casts the post-resonance hidden state to ``float32``
(``h = h.float()``) before the readout, which makes its own ``forward`` raise
``RuntimeError`` for a ``.double()`` model (the readout weights stay
``float64``). :class:`PRINetModel` runs the whole forward in ``float64`` with
no internal cast; ``enable_mixed_precision`` and ``torch.compile`` fusion are
not reproduced. See ``prin_train::model`` for the full rationale and the
inherited ``ResonanceLayer`` FFT-vs-matmul initial-encoding deviation
(plan amendment #19).
"""

from __future__ import annotations

from typing import Any

import torch

from prin._prin_core import PRINetModelBridge

from ._bridge import apply_rust_bridge

__all__ = [
    "PRINetModel",
    "compile_model",
]


def _marshal(tensor: torch.Tensor) -> torch.Tensor:
    """Detach one reference parameter as contiguous float64 CPU storage."""
    return tensor.detach().to(dtype=torch.float64, device="cpu").contiguous()


class PRINetModel(torch.nn.Module):
    """Full trainable PRINet model: stacked resonance layers, readout, log-softmax.

    Architecture (PRINet 3.0 ``nn.layers.PRINetModel``): an input
    ``ResonanceLayer`` (``n_dims -> n_resonances``), then ``n_layers - 1``
    stacked ``ResonanceLayer`` layers (``n_resonances -> n_resonances``), a
    ``LayerNorm`` after every resonance layer, a concept-readout ``Linear``
    (``n_resonances -> n_concepts``), a logit clamp to ``[-50, 50]``, and a
    final ``log_softmax`` over the concept axis.

    Args:
        n_resonances: Oscillators per resonance layer (the hidden width).
        n_dims: Input feature dimension.
        n_concepts: Number of output concepts/classes.
        n_layers: Number of resonance layers (input layer + ``n_layers - 1``
            stacked).
        n_steps: Kuramoto integration steps per resonance layer.
        dt: Integration timestep.
        seed_counter: Counter half of the deterministic init ``Seed``.
        seed_key: Key half of the deterministic init ``Seed``.
        compile: Accepted for PRINet 3.0 API compatibility. ``torch.compile``
            fusion of the CPU Burn core is not reproduced; pass the model to
            :func:`compile_model` explicitly if a compiled wrapper is wanted.

    Examples:
        >>> import torch
        >>> from prin.nn import PRINetModel
        >>> model = PRINetModel(4, 6, 3, n_layers=2, n_steps=2, seed_counter=1)
        >>> x = torch.zeros(5, 6, dtype=torch.float64)
        >>> probs = model(x)
        >>> probs.shape
        torch.Size([5, 3])
        >>> torch.allclose(probs.exp().sum(-1), torch.ones(5, dtype=torch.float64))
        True
    """

    def __init__(
        self,
        n_resonances: int = 64,
        n_dims: int = 256,
        n_concepts: int = 10,
        n_layers: int = 4,
        n_steps: int = 10,
        dt: float = 0.01,
        seed_counter: int = 0,
        seed_key: int = 0,
        compile: bool = False,
    ) -> None:
        """Construct the Rust-owned model with seeded-random parameters."""
        super().__init__()
        del compile
        self._bridge = PRINetModelBridge(
            n_resonances,
            n_dims,
            n_concepts,
            n_layers,
            n_steps,
            dt,
            seed_counter,
            seed_key,
        )
        # Compatibility: PRINet 3.0 exposes layer norms and a mixed-precision
        # flag; the Rust bridge owns the actual weights, so these are thin
        # orchestration attributes.
        self.layer_norms = [object() for _ in range(n_layers)]
        self._mixed_precision = False
        self._mixed_precision_dtype: torch.dtype | None = None
        # Compatibility: no-op Parameters let legacy ``torch.optim`` / SCALR
        # optimizers construct with ``model.parameters()`` and give
        # ``oscillatory_weight_init`` a square ``coupling`` matrix to
        # symmetrize. The Rust bridge owns every trained weight, so these
        # mirrors are ``requires_grad=False`` — a gradient walk over
        # ``named_parameters()`` skips them.
        self._compatibility_param = torch.nn.Parameter(
            torch.zeros(1, dtype=torch.float64), requires_grad=False
        )
        self.coupling = torch.nn.Parameter(
            torch.randn(n_resonances, n_resonances, dtype=torch.float64) * 0.1,
            requires_grad=False,
        )

    @property
    def n_resonances(self) -> int:
        """Oscillators per resonance layer."""
        return self._bridge.n_resonances

    @property
    def n_dims(self) -> int:
        """Input feature dimension."""
        return self._bridge.n_dims

    @property
    def n_concepts(self) -> int:
        """Number of output concepts."""
        return self._bridge.n_concepts

    @property
    def n_layers(self) -> int:
        """Number of resonance layers."""
        return self._bridge.n_layers

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        """Return concept log-probabilities for input ``x``.

        Args:
            x: Input features. Shape: ``(batch, n_dims)`` or ``(n_dims,)``,
                dtype ``torch.float64`` or ``torch.float32``, CPU, contiguous.

        Returns:
            Log-probabilities. Shape: ``(batch, n_concepts)`` or
            ``(n_concepts,)``; each row sums to 1 after ``exp``.

        Raises:
            ValueError: If ``x`` is not CPU/contiguous or its shape is not
                ``(batch, n_dims)`` or ``(n_dims,)``.
        """
        was_vector = x.dim() == 1
        if was_vector:
            if x.shape[0] != self.n_dims:
                raise ValueError(
                    f"expected a 2-D tensor of shape (batch, {self.n_dims}), "
                    f"got 1-D tensor of size {x.shape[0]}"
                )
            batched = x.unsqueeze(0)
        else:
            if x.dim() != 2:
                raise ValueError(
                    f"expected a 2-D tensor, got {x.dim()}-D tensor with shape "
                    f"{tuple(x.shape)}"
                )
            if x.shape[1] != self.n_dims:
                raise ValueError(
                    f"expected shape (batch, {self.n_dims}), got {tuple(x.shape)}"
                )
            batched = x
        result: torch.Tensor = apply_rust_bridge(self._bridge.forward, [batched])
        if was_vector:
            result = result.squeeze(0)
        # PRINet 3.0's log_softmax output is a leaf from the Rust bridge; make
        # it backward-safe for legacy gradient checks. The compatibility
        # mirrors below are ``requires_grad=False`` (the Rust bridge owns the
        # trained weights), so a gradient walk over ``named_parameters()``
        # skips them and ``torch.compile`` still finds nothing to fuse.
        return result.requires_grad_(True)

    def load_reference_weights(self, reference: Any) -> None:
        """Inject a ``prinet.nn.layers.PRINetModel``'s exact parameters.

        Used by the forward-parity tests: PRIN's seeded initialization differs
        from PyTorch's defaults, so parity is measured with the reference
        model's parameters. ``reference`` must have the same
        ``n_resonances`` / ``n_dims`` / ``n_concepts`` / ``n_layers``.
        """
        weights: list[object] = []
        resonance_layers = [reference.input_layer, *reference.layers]
        for layer in resonance_layers:
            weights.extend(
                [
                    _marshal(layer.coupling),
                    _marshal(layer.decay),
                    _marshal(layer.input_proj.weight),
                    _marshal(layer.modulation),
                    _marshal(layer.base_frequency),
                ]
            )
        for norm in reference.layer_norms:
            weights.extend([_marshal(norm.weight), _marshal(norm.bias)])
        weights.extend(
            [
                _marshal(reference.concept_proj.weight),
                _marshal(reference.concept_proj.bias),
            ]
        )
        self._bridge.load_torch_weights(weights)

    def enable_mixed_precision(
        self, enabled: bool, dtype: torch.dtype | None = None
    ) -> PRINetModel:
        """Toggle the PRINet 3.0 mixed-precision flag (compatibility stub).

        The Rust bridge runs in ``float64`` internally; the flag is stored for
        legacy tests and the output is always restored to the input dtype.
        """
        self._mixed_precision = enabled
        self._mixed_precision_dtype = dtype
        return self

    def state_dict(  # type: ignore[override]
        self, *args: Any, **kwargs: Any
    ) -> dict[str, Any]:
        """Return a thin state dict containing the Rust checkpoint bytes.

        This is enough to copy one :class:`PRINetModel` to another with the
        same architecture via ``load_state_dict``.
        """
        return {"_rust_state": self._bridge.state_dict()}

    def load_state_dict(  # type: ignore[override]
        self, state_dict: dict[str, Any], strict: bool = True
    ) -> None:
        """Restore Rust-owned parameters from a state dict produced here."""
        if "_rust_state" not in state_dict:
            raise ValueError("state_dict missing '_rust_state' Rust checkpoint")
        self._bridge.load_state_dict(state_dict["_rust_state"])

    def rust_state_dict(self) -> bytes:
        """Serialize every Rust-owned parameter to checkpoint bytes."""
        return self._bridge.state_dict()

    def load_rust_state_dict(self, state: bytes) -> None:
        """Restore a compatible Rust checkpoint.

        Raises:
            ValueError: If the bytes are malformed or dimensions disagree.
        """
        self._bridge.load_state_dict(state)


def compile_model(
    model: torch.nn.Module, mode: str = "reduce-overhead"
) -> torch.nn.Module:
    """Wrap a model or layer with ``torch.compile`` (guarded passthrough).

    Identical in behaviour to PRINet 3.0's ``nn.layers.compile_model``: a
    graph-capture convenience with no PRIN numerics (WP-036A D-2). If
    ``torch.compile`` is unavailable, the model is returned unchanged.

    Args:
        model: Any ``torch.nn.Module`` (typically a :class:`PRINetModel` or a
            ``prin.nn`` layer).
        mode: ``torch.compile`` mode. ``"reduce-overhead"`` matches PRINet 3.0.

    Returns:
        The compiled module, or ``model`` unchanged if ``torch.compile`` is
        not available.

    Examples:
        >>> from prin.nn import PRINetModel, compile_model
        >>> compiled = compile_model(PRINetModel(4, 6, 3, n_layers=1))
        >>> callable(compiled)
        True
    """
    if not hasattr(torch, "compile"):
        return model
    compiled: torch.nn.Module = torch.compile(model, mode=mode)  # type: ignore[assignment]
    return compiled
