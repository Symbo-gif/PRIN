"""Rust-backed phase-to-rate conversion and autoencoder comparison models.

The numerical implementations live in ``prin-train``
(``prin_train::autoencoders``). This module provides PRINet-3.0-compatible
``torch.nn.Module`` wrappers whose forward/backward cross the Rust boundary
exactly once per call through the audited DLPack bridge.

``PhaseToRateConverter`` keeps its temperature a Rust-owned parameter that
receives a softmax gradient in the ``soft`` / ``annealed`` regimes; PRINet
3.0 detaches it with ``.item()``. This is a forward-identical superset of the
reference (see ``prin_train::autoencoders`` module docs). The
encoder/decoder/classifier ``Linear`` stacks are Rust-owned too and are
trained with a ``prin-train`` oscillator-aware optimizer, not ``torch.optim``
(the ``ResonanceLayer`` / ``HybridPRINetV2`` training-ownership split).
"""

from __future__ import annotations

from typing import Any

import torch

from prin._prin_core import (
    DenseAutoencoderBridge,
    PhaseToRateAutoencoderBridge,
    PhaseToRateConverterBridge,
)

from ._bridge import apply_rust_bridge

__all__ = [
    "DenseAutoencoder",
    "PhaseToRateAutoencoder",
    "PhaseToRateConverter",
]


def _as_batched(tensor: torch.Tensor) -> tuple[torch.Tensor, bool]:
    """Normalize a ``(N,)`` tensor to ``(1, N)``; pass ``(B, N)`` through."""
    if tensor.dim() == 1:
        return tensor.unsqueeze(0), True
    if tensor.dim() == 2:
        return tensor, False
    raise ValueError(f"expected a 1-D or 2-D tensor, got shape {tuple(tensor.shape)}")


def _marshal(tensor: torch.Tensor) -> torch.Tensor:
    """Detach to a contiguous float64 CPU tensor for the DLPack bridge."""
    return tensor.detach().to(dtype=torch.float64, device="cpu").contiguous()


class PhaseToRateConverter(torch.nn.Module):
    """Trainable phase-amplitude to rate-code converter.

    Args:
        n_oscillators: Input oscillator dimension.
        mode: Winner-take-all mode (``"soft"``, ``"hard"``, ``"annealed"``).
        sparsity: Target fraction of active units (``hard`` / ``annealed``).
        initial_temperature: Starting softmax temperature.
        learnable_temperature: Accepted for PRINet 3.0 API compatibility. The
            temperature is always a Rust-owned parameter; pass it out of the
            optimizer to freeze it.
    """

    def __init__(
        self,
        n_oscillators: int,
        mode: str = "soft",
        sparsity: float = 0.1,
        initial_temperature: float = 1.0,
        learnable_temperature: bool = True,
    ) -> None:
        """Construct the Rust-backed converter."""
        super().__init__()
        del learnable_temperature
        self._bridge = PhaseToRateConverterBridge(
            n_oscillators, mode, sparsity, initial_temperature
        )

    @property
    def n_oscillators(self) -> int:
        """Input oscillator dimension."""
        return self._bridge.n_oscillators

    @property
    def mode(self) -> str:
        """Winner-take-all mode."""
        return self._bridge.mode

    @property
    def sparsity(self) -> float:
        """Target sparsity fraction."""
        return self._bridge.sparsity

    def forward(self, phase: torch.Tensor, amplitude: torch.Tensor) -> torch.Tensor:
        """Convert phase/amplitude to rate codes.

        Args:
            phase: Phase tensor, shape ``(N,)`` or ``(batch, N)``.
            amplitude: Matching amplitude tensor.

        Returns:
            Non-negative rate codes with the input shape.

        Raises:
            ValueError: If shapes/ranks disagree or violate the bridge
                contract.
        """
        if phase.shape != amplitude.shape:
            raise ValueError(
                f"phase and amplitude must have the same shape, got "
                f"{tuple(phase.shape)} and {tuple(amplitude.shape)}"
            )
        phase_b, was_vector = _as_batched(phase)
        amplitude_b, _ = _as_batched(amplitude)
        output: torch.Tensor = apply_rust_bridge(
            self._bridge.forward, [phase_b, amplitude_b]
        )
        return output.squeeze(0) if was_vector else output

    def rust_state_dict(self) -> bytes:
        """Serialize the Rust-owned temperature parameter."""
        return self._bridge.state_dict()

    def load_rust_state_dict(self, state: bytes) -> None:
        """Restore a compatible Rust parameter record.

        Raises:
            ValueError: If the record is malformed or incompatible.
        """
        self._bridge.load_state_dict(state)


class PhaseToRateAutoencoder(torch.nn.Module):
    """Autoencoder with a trainable phase-to-rate bottleneck.

    Architecture: encoder (dense -> phase / softplus amplitude) ->
    :class:`PhaseToRateConverter` -> decoder (rate -> reconstruction), plus a
    classifier head on the bottleneck codes.

    Args:
        n_input: Input feature dimension.
        n_oscillators: Bottleneck oscillator count.
        sparsity: Target bottleneck sparsity.
        mode: Winner-take-all mode for the bottleneck.
        hidden: Encoder/decoder hidden width (PRINet 3.0 uses ``256``).
        n_classes: Classifier-head class count (PRINet 3.0 uses ``10``).
        seed_counter: Counter half of the deterministic init ``Seed``.
        seed_key: Key half of the deterministic init ``Seed``.
    """

    def __init__(
        self,
        n_input: int = 784,
        n_oscillators: int = 64,
        sparsity: float = 0.1,
        mode: str = "soft",
        hidden: int = 256,
        n_classes: int = 10,
        seed_counter: int = 0,
        seed_key: int = 0,
    ) -> None:
        """Construct the Rust-owned autoencoder."""
        super().__init__()
        self._bridge = PhaseToRateAutoencoderBridge(
            n_input,
            n_oscillators,
            hidden,
            n_classes,
            sparsity,
            mode,
            seed_counter,
            seed_key,
        )
        # PRINet 3.0 compatibility: the reference autoencoder is a trainable
        # ``torch.nn.Module``; this zero-valued mirror keeps ``.parameters()``
        # non-empty and lets ``loss.backward()`` populate a gradient. The Rust
        # bridge remains the numerical owner of ``forward`` / ``classify``.
        self._compat_gain = torch.nn.Parameter(torch.zeros((), dtype=torch.float64))

    @property
    def n_input(self) -> int:
        """Input feature dimension."""
        return self._bridge.n_input

    @property
    def n_oscillators(self) -> int:
        """Bottleneck oscillator count."""
        return self._bridge.n_oscillators

    def forward(self, x: torch.Tensor) -> tuple[torch.Tensor, torch.Tensor]:
        """Return ``(reconstruction, sparse_rates)`` for input ``x``.

        Args:
            x: Input tensor, shape ``(batch, n_input)``.

        Returns:
            The reconstruction ``(batch, n_input)`` and the bottleneck rate
            codes ``(batch, n_oscillators)``.
        """
        recon, rates = apply_rust_bridge(self._bridge.forward, [x])
        gain = self._compat_gain.to(dtype=recon.dtype)
        return recon + gain, rates + gain

    def classify(self, x: torch.Tensor) -> torch.Tensor:
        """Return ``log_softmax`` class log-probabilities for input ``x``.

        Args:
            x: Input tensor, shape ``(batch, n_input)``.

        Returns:
            Log-probabilities, shape ``(batch, n_classes)``.
        """
        result: torch.Tensor = apply_rust_bridge(self._bridge.classify, [x])
        return result

    def load_reference_weights(self, reference: Any) -> None:
        """Copy weights from a ``prinet.nn.layers.PhaseToRateAutoencoder``.

        Used by the forward-parity tests: PRIN's seeded initialization differs
        from PyTorch's default ``nn.Linear`` init, so parity is measured with
        the reference model's exact parameters.
        """
        weights: list[object] = [
            _marshal(reference.encoder_phase[0].weight),
            _marshal(reference.encoder_phase[0].bias),
            _marshal(reference.encoder_phase[2].weight),
            _marshal(reference.encoder_phase[2].bias),
            _marshal(reference.encoder_amp[0].weight),
            _marshal(reference.encoder_amp[0].bias),
            _marshal(reference.encoder_amp[2].weight),
            _marshal(reference.encoder_amp[2].bias),
            _marshal(reference.decoder[0].weight),
            _marshal(reference.decoder[0].bias),
            _marshal(reference.decoder[2].weight),
            _marshal(reference.decoder[2].bias),
            _marshal(reference.classifier.weight),
            _marshal(reference.classifier.bias),
            _marshal(reference.converter.temperature).reshape(1),
        ]
        self._bridge.load_torch_weights(weights)

    def rust_state_dict(self) -> bytes:
        """Serialize the Rust-owned parameters to checkpoint bytes."""
        return self._bridge.state_dict()

    def load_rust_state_dict(self, state: bytes) -> None:
        """Restore a compatible Rust parameter record.

        Raises:
            ValueError: If the record is malformed or incompatible.
        """
        self._bridge.load_state_dict(state)


class DenseAutoencoder(torch.nn.Module):
    """Non-oscillatory dense-MLP autoencoder baseline with a classifier head.

    Args:
        n_input: Input feature dimension.
        n_bottleneck: Bottleneck dimension.
        hidden: Encoder/decoder hidden width (PRINet 3.0 uses ``256``).
        n_classes: Classifier-head class count (PRINet 3.0 uses ``10``).
        seed_counter: Counter half of the deterministic init ``Seed``.
        seed_key: Key half of the deterministic init ``Seed``.
    """

    def __init__(
        self,
        n_input: int = 784,
        n_bottleneck: int = 64,
        hidden: int = 256,
        n_classes: int = 10,
        seed_counter: int = 0,
        seed_key: int = 0,
    ) -> None:
        """Construct the Rust-owned baseline autoencoder."""
        super().__init__()
        self._bridge = DenseAutoencoderBridge(
            n_input, n_bottleneck, hidden, n_classes, seed_counter, seed_key
        )

    @property
    def n_input(self) -> int:
        """Input feature dimension."""
        return self._bridge.n_input

    @property
    def n_bottleneck(self) -> int:
        """Bottleneck dimension."""
        return self._bridge.n_bottleneck

    def forward(self, x: torch.Tensor) -> tuple[torch.Tensor, torch.Tensor]:
        """Return ``(reconstruction, bottleneck_codes)`` for input ``x``."""
        result: tuple[torch.Tensor, torch.Tensor] = apply_rust_bridge(
            self._bridge.forward, [x]
        )
        return result

    def classify(self, x: torch.Tensor) -> torch.Tensor:
        """Return ``log_softmax`` class log-probabilities for input ``x``."""
        result: torch.Tensor = apply_rust_bridge(self._bridge.classify, [x])
        return result

    def load_reference_weights(self, reference: Any) -> None:
        """Copy weights from a ``prinet.nn.layers.DenseAutoencoder``."""
        weights: list[object] = [
            _marshal(reference.encoder[0].weight),
            _marshal(reference.encoder[0].bias),
            _marshal(reference.encoder[2].weight),
            _marshal(reference.encoder[2].bias),
            _marshal(reference.decoder[0].weight),
            _marshal(reference.decoder[0].bias),
            _marshal(reference.decoder[2].weight),
            _marshal(reference.decoder[2].bias),
            _marshal(reference.classifier.weight),
            _marshal(reference.classifier.bias),
        ]
        self._bridge.load_torch_weights(weights)

    def rust_state_dict(self) -> bytes:
        """Serialize the Rust-owned parameters to checkpoint bytes."""
        return self._bridge.state_dict()

    def load_rust_state_dict(self, state: bytes) -> None:
        """Restore a compatible Rust parameter record.

        Raises:
            ValueError: If the record is malformed or incompatible.
        """
        self._bridge.load_state_dict(state)
