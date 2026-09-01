"""WP-036A inhibition/sparsification bridge, parity, and gradient tests."""

from __future__ import annotations

import math

import prin
import pytest
import torch
from prin._deprecation import verify_api_surface
from prin.nn import (
    DentateGyrusConverter,
    DGLayer,
    FeedforwardInhibition,
    SparsityRegularizationLoss,
    oscillatory_weight_init,
)


def _inputs() -> tuple[torch.Tensor, torch.Tensor]:
    phase = torch.tensor(
        [[0.05, 0.8, 1.7, 2.9]], dtype=torch.float64, requires_grad=True
    )
    amplitude = torch.tensor(
        [[4.0, 2.0, 1.0, 0.5]], dtype=torch.float64, requires_grad=True
    )
    return phase, amplitude


def test_feedforward_inhibition_matches_reference() -> None:
    """Rust FFI matches the installed PRINet 3.0 reference."""
    pytest.importorskip("prinet.core.propagation.inhibition")
    from prinet.core.propagation.inhibition import (
        FeedforwardInhibition as ReferenceFeedforwardInhibition,
    )

    phase, amplitude = _inputs()
    actual = FeedforwardInhibition(delay_steps=3, tau=0.07).gate(phase, amplitude)
    expected = ReferenceFeedforwardInhibition(delay_steps=3, tau=0.07).gate(
        phase, amplitude
    )
    torch.testing.assert_close(actual, expected, rtol=1e-10, atol=1e-12)


def test_feedforward_inhibition_gradcheck() -> None:
    """FFI's Rust backward is the adjoint of its forward pass."""
    phase, amplitude = _inputs()
    gate = FeedforwardInhibition(tau=0.2)
    assert torch.autograd.gradcheck(
        gate.gate,
        (phase, amplitude),
        eps=1e-4,
        rtol=1e-3,
        atol=1e-3,
    )


def test_feedforward_inhibition_properties_and_errors() -> None:
    """FFI supports vectors, exposes config, and rejects invalid inputs."""
    ffi = FeedforwardInhibition(delay_steps=2, tau=0.1)
    phase = torch.tensor([0.0, math.pi], dtype=torch.float64)
    amplitude = torch.ones(2, dtype=torch.float64)
    output = ffi.gate(phase, amplitude)
    assert output.shape == phase.shape
    assert torch.all(output >= 0)
    assert ffi.delay_steps == 2
    assert ffi.tau == 0.1
    with pytest.raises(ValueError, match="same shape"):
        ffi.gate(phase, torch.ones(3, dtype=torch.float64))
    with pytest.raises(ValueError, match="tau"):
        FeedforwardInhibition(tau=0.0)


def test_dentate_gyrus_converter_matches_reference_and_is_sparse() -> None:
    """The batched Rust DG pipeline matches PRINet and retains top-k winners."""
    pytest.importorskip("prinet.core.propagation.inhibition")
    from prinet.core.propagation.inhibition import (
        DentateGyrusConverter as ReferenceDentateGyrusConverter,
    )

    phase, amplitude = _inputs()
    kwargs = {
        "n_oscillators": 4,
        "k": 2,
        "ffi_delay": 2,
        "ffi_tau": 0.08,
        "fbi_delay": 7,
        "fbi_temperature": 0.7,
        "integration_alpha": 0.9,
    }
    actual = DentateGyrusConverter(**kwargs).convert(phase, amplitude, 4)
    expected = ReferenceDentateGyrusConverter(**kwargs).convert(phase, amplitude, 4)
    torch.testing.assert_close(actual, expected, rtol=1e-10, atol=1e-12)
    assert int((actual > 0).sum(dim=-1).max()) == 2


def test_dentate_gyrus_converter_gradcheck_at_stationary_ste_point() -> None:
    """DG gradcheck covers a stationary point of its deliberate FBI STE.

    A hard-forward/soft-backward estimator is not globally the derivative of
    one smooth function. At phase pi the FFI cosine readout and its first
    derivative are both zero, so analytical and finite-difference Jacobians
    legitimately coincide; nonzero STE flow is tested independently in Rust.
    """
    phase = torch.full((1, 4), math.pi, dtype=torch.float64, requires_grad=True)
    amplitude = torch.tensor(
        [[4.0, 2.0, 1.0, 0.5]], dtype=torch.float64, requires_grad=True
    )
    converter = DentateGyrusConverter(4, k=2)
    assert torch.autograd.gradcheck(
        lambda p, a: converter.convert(p, a, 3),
        (phase, amplitude),
        eps=1e-4,
        rtol=1e-3,
        atol=1e-3,
    )


def test_dentate_gyrus_converter_vector_and_errors() -> None:
    """DG preserves vector shape and validates public configuration."""
    converter = DentateGyrusConverter(4, k=2)
    phase, amplitude = _inputs()
    assert converter.convert(phase[0], amplitude[0]).shape == (4,)
    assert converter.ffi.delay_steps == 1
    assert converter.fbi.delay_steps == 20
    with pytest.raises(ValueError, match="n_integration_steps"):
        converter.convert(phase, amplitude, 0)
    with pytest.raises(ValueError, match="integration_alpha"):
        DentateGyrusConverter(4, integration_alpha=2.0)


def test_dg_layer_matches_reference() -> None:
    """The Rust-owned trainable DG layer matches reference default parameters."""
    pytest.importorskip("prinet.nn.layers")
    from prinet.nn.layers import DGLayer as ReferenceDGLayer

    phase, amplitude = _inputs()
    actual = DGLayer(4, top_k=2, ffi_delay=2, n_integration_steps=3)(phase, amplitude)
    expected = ReferenceDGLayer(4, top_k=2, ffi_delay=2, n_integration_steps=3)(
        phase, amplitude
    )
    torch.testing.assert_close(actual, expected, rtol=1e-10, atol=1e-12)


def test_dg_layer_gradcheck_and_checkpoint_roundtrip() -> None:
    """DGLayer inputs gradcheck and Rust parameters round-trip exactly."""
    phase, amplitude = _inputs()
    layer = DGLayer(4, top_k=2, n_integration_steps=3)
    original = layer(phase, amplitude)
    state = layer.rust_state_dict()
    layer.load_rust_state_dict(state)
    torch.testing.assert_close(layer(phase, amplitude), original)
    stationary_phase = torch.full(
        (1, 4), math.pi, dtype=torch.float64, requires_grad=True
    )
    stationary_amplitude = amplitude.detach().requires_grad_(True)
    assert torch.autograd.gradcheck(
        layer,
        (stationary_phase, stationary_amplitude),
        eps=1e-4,
        rtol=1e-3,
        atol=1e-3,
    )


def test_dg_layer_properties_and_errors() -> None:
    """DGLayer exposes dimensions, preserves vectors, and validates config."""
    layer = DGLayer(4, top_k=9)
    phase, amplitude = _inputs()
    assert layer.n_input == 4
    assert layer.top_k == 4
    assert layer(phase[0], amplitude[0]).shape == (4,)
    with pytest.raises(ValueError, match="k"):
        DGLayer(4, top_k=0)
    with pytest.raises(ValueError, match="same shape"):
        layer(phase, amplitude[:, :3])


def test_sparsity_regularization_matches_reference() -> None:
    """Rust sigmoid-surrogate density loss matches PRINet 3.0."""
    pytest.importorskip("prinet.nn.layers")
    from prinet.nn.layers import (
        SparsityRegularizationLoss as ReferenceSparsityRegularizationLoss,
    )

    activations = torch.tensor(
        [[-0.4, 0.0, 0.8], [0.2, 1.1, -0.7]], dtype=torch.float64
    )
    actual = SparsityRegularizationLoss(0.65, 0.2)(activations)
    expected = ReferenceSparsityRegularizationLoss(0.65, 0.2)(activations)
    torch.testing.assert_close(actual, expected, rtol=1e-6, atol=1e-8)


def test_sparsity_regularization_gradcheck_and_errors() -> None:
    """Sparsity loss has a finite Rust adjoint and validates hyperparameters."""
    activations = torch.tensor(
        [[-0.4, 0.0, 0.8], [0.2, 1.1, -0.7]],
        dtype=torch.float64,
        requires_grad=True,
    )
    loss = SparsityRegularizationLoss(0.65, 0.2)
    assert loss.target_sparsity == 0.65
    assert loss.temperature == 0.2
    assert torch.autograd.gradcheck(
        loss,
        (activations,),
        eps=1e-4,
        rtol=1e-3,
        atol=1e-3,
    )
    assert loss(activations[0]).ndim == 0
    with pytest.raises(ValueError, match="target_sparsity"):
        SparsityRegularizationLoss(1.1)
    with pytest.raises(ValueError, match="temperature"):
        SparsityRegularizationLoss(0.9, 0.0)


class _InitializationFixture(torch.nn.Module):
    """Small module exposing every reference initialization role."""

    def __init__(self) -> None:
        super().__init__()
        self.coupling = torch.nn.Parameter(
            torch.tensor([[1.0, 2.0], [3.0, 4.0]], dtype=torch.float64)
        )
        self.projection = torch.nn.Linear(3, 2, dtype=torch.float64)


def test_oscillatory_weight_init_matches_reference_roles() -> None:
    """Initialize coupling, bias, and Xavier weights by reference role."""
    first = _InitializationFixture()
    second = _InitializationFixture()
    oscillatory_weight_init(first, seed_counter=7, seed_key=11)
    oscillatory_weight_init(second, seed_counter=7, seed_key=11)
    torch.testing.assert_close(
        first.coupling,
        torch.tensor([[0.0, 0.25], [0.25, 0.0]], dtype=torch.float64),
    )
    assert torch.count_nonzero(first.projection.bias) == 0
    torch.testing.assert_close(first.projection.weight, second.projection.weight)
    bound = 0.5 * math.sqrt(6.0 / 5.0)
    assert float(first.projection.weight.detach().abs().max()) <= bound


def test_replaced_symbols_are_real_and_public_surface_is_frozen() -> None:
    """The five symbols no longer have D-2.2 stub identities."""
    import prin.nn.deferred_layers as deferred
    import prin.nn.inhibition_layers as implemented

    names = {
        "FeedforwardInhibition",
        "DentateGyrusConverter",
        "DGLayer",
        "oscillatory_weight_init",
        "SparsityRegularizationLoss",
    }
    for name in names:
        assert getattr(deferred, name) is getattr(implemented, name)
        assert getattr(prin, name) is getattr(implemented, name)
    assert verify_api_surface(prin.__all__) == (set(), set())
