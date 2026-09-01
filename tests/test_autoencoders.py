"""WP-036A phase-to-rate and autoencoder bridge, parity, and gradient tests."""

from __future__ import annotations

import math

import prin
import pytest
import torch
from prin._deprecation import verify_api_surface
from prin.nn import DenseAutoencoder, PhaseToRateAutoencoder, PhaseToRateConverter


def _phase_amp(batch: int = 3, n: int = 5) -> tuple[torch.Tensor, torch.Tensor]:
    torch.manual_seed(0)
    phase = (torch.rand(batch, n, dtype=torch.float64) * 2 * math.pi).requires_grad_(
        True
    )
    amplitude = (0.2 + torch.rand(batch, n, dtype=torch.float64)).requires_grad_(True)
    return phase, amplitude


# --- PhaseToRateConverter --------------------------------------------


def test_phase_to_rate_converter_soft_matches_reference() -> None:
    """The Rust soft converter matches PRINet 3.0 float64 within 1e-9."""
    pytest.importorskip("prinet.nn.layers")
    from prinet.nn.layers import PhaseToRateConverter as Reference

    phase, amplitude = _phase_amp()
    actual = PhaseToRateConverter(5, mode="soft", sparsity=0.2)(phase, amplitude)
    expected = Reference(5, mode="soft", sparsity=0.2).double()(phase, amplitude)
    torch.testing.assert_close(actual, expected, rtol=1e-9, atol=1e-12)
    assert torch.allclose(actual.sum(dim=-1), torch.ones(3, dtype=torch.float64))


def test_phase_to_rate_converter_hard_matches_reference() -> None:
    """Hard top-k selection is forward-identical to the reference."""
    pytest.importorskip("prinet.nn.layers")
    from prinet.nn.layers import PhaseToRateConverter as Reference

    phase, amplitude = _phase_amp()
    actual = PhaseToRateConverter(5, mode="hard", sparsity=0.5)(phase, amplitude)
    expected = Reference(5, mode="hard", sparsity=0.5).double()(phase, amplitude)
    torch.testing.assert_close(actual, expected, rtol=1e-12, atol=1e-14)
    assert int((actual > 0).sum(dim=-1).max()) == 2


def test_phase_to_rate_converter_annealed_matches_reference() -> None:
    """Annealed mode matches the reference to machine precision.

    At the default unit temperature the blend coefficient
    ``sigmoid(1/T - 1) = sigmoid(0) = 0.5`` is exact in both float32 and
    float64, so no D-4 tolerance loosening is needed here; the reference's
    ``torch.tensor(...)`` float32 blend is a latent hazard only at non-unit
    temperature.
    """
    pytest.importorskip("prinet.nn.layers")
    from prinet.nn.layers import PhaseToRateConverter as Reference

    phase, amplitude = _phase_amp()
    actual = PhaseToRateConverter(5, mode="annealed", sparsity=0.4)(phase, amplitude)
    expected = Reference(5, mode="annealed", sparsity=0.4).double()(phase, amplitude)
    torch.testing.assert_close(actual, expected, rtol=1e-9, atol=1e-12)


def test_phase_to_rate_converter_soft_gradcheck() -> None:
    """Soft mode passes a float64 gradcheck w.r.t. phase and amplitude."""
    phase, amplitude = _phase_amp(batch=2, n=4)
    converter = PhaseToRateConverter(4, mode="soft")
    assert torch.autograd.gradcheck(
        converter, (phase, amplitude), eps=1e-6, rtol=1e-3, atol=1e-3
    )


def test_phase_to_rate_converter_hard_ste_gradient_is_finite() -> None:
    """Hard mode routes a finite straight-through gradient to the inputs."""
    phase, amplitude = _phase_amp(batch=2, n=4)
    out = PhaseToRateConverter(4, mode="hard", sparsity=0.5)(phase, amplitude)
    out.sum().backward()
    assert phase.grad is not None
    assert amplitude.grad is not None
    assert amplitude.grad.shape == amplitude.shape
    assert torch.isfinite(amplitude.grad).all()
    assert amplitude.grad.abs().sum() > 0


def test_phase_to_rate_converter_properties_vectors_and_errors() -> None:
    """The converter exposes config, accepts vectors, and validates inputs."""
    converter = PhaseToRateConverter(4, mode="annealed", sparsity=0.25)
    assert converter.n_oscillators == 4
    assert converter.mode == "annealed"
    assert converter.sparsity == 0.25
    phase = torch.zeros(4, dtype=torch.float64)
    amplitude = torch.ones(4, dtype=torch.float64)
    assert converter(phase, amplitude).shape == (4,)
    with pytest.raises(ValueError, match="same shape"):
        converter(phase, torch.ones(3, dtype=torch.float64))
    with pytest.raises(ValueError, match="1-D or 2-D"):
        converter(torch.zeros(1, 2, 4, dtype=torch.float64), torch.zeros(1, 2, 4))
    with pytest.raises(ValueError, match="mode"):
        PhaseToRateConverter(4, mode="bogus")
    with pytest.raises(ValueError, match="sparsity"):
        PhaseToRateConverter(4, sparsity=2.0)


def test_phase_to_rate_converter_checkpoint_roundtrip() -> None:
    """The Rust-owned temperature parameter round-trips exactly."""
    phase, amplitude = _phase_amp(batch=1, n=4)
    converter = PhaseToRateConverter(4, mode="soft")
    original = converter(phase, amplitude)
    converter.load_rust_state_dict(converter.rust_state_dict())
    torch.testing.assert_close(converter(phase, amplitude), original)


# --- PhaseToRateAutoencoder / DenseAutoencoder ----------------------


def _reference_ptr_autoencoder() -> torch.nn.Module:
    pytest.importorskip("prinet.nn.layers")
    from prinet.nn.layers import PhaseToRateAutoencoder as Reference

    torch.manual_seed(1)
    return Reference(n_input=12, n_oscillators=6, sparsity=0.2, mode="soft").double()


def test_phase_to_rate_autoencoder_matches_reference() -> None:
    """Forward and classify match the reference with its exact weights."""
    reference = _reference_ptr_autoencoder()
    model = PhaseToRateAutoencoder(n_input=12, n_oscillators=6, sparsity=0.2)
    model.load_reference_weights(reference)

    x = torch.randn(4, 12, dtype=torch.float64)
    recon, rates = model(x)
    ref_recon, ref_rates = reference(x)
    torch.testing.assert_close(recon, ref_recon, rtol=1e-9, atol=1e-11)
    torch.testing.assert_close(rates, ref_rates, rtol=1e-9, atol=1e-11)

    logits = model.classify(x)
    ref_logits = reference.classify(x)
    torch.testing.assert_close(logits, ref_logits, rtol=1e-9, atol=1e-11)
    assert torch.allclose(
        logits.exp().sum(dim=-1), torch.ones(4, dtype=torch.float64), atol=1e-9
    )


def test_phase_to_rate_autoencoder_gradcheck_wrt_input() -> None:
    """The autoencoder forward is differentiable w.r.t. its input."""
    model = PhaseToRateAutoencoder(
        n_input=5, n_oscillators=3, hidden=4, n_classes=3, seed_counter=2
    )
    x = torch.randn(2, 5, dtype=torch.float64, requires_grad=True)
    assert torch.autograd.gradcheck(model, (x,), eps=1e-6, rtol=1e-3, atol=1e-3)
    assert torch.autograd.gradcheck(
        model.classify, (x,), eps=1e-6, rtol=1e-3, atol=1e-3
    )


def test_phase_to_rate_autoencoder_construction_and_errors() -> None:
    """The wrapper reports dimensions and rejects invalid configuration."""
    model = PhaseToRateAutoencoder(n_input=8, n_oscillators=4, hidden=5, n_classes=3)
    assert model.n_input == 8
    assert model.n_oscillators == 4
    recon, rates = model(torch.randn(2, 8, dtype=torch.float64))
    assert recon.shape == (2, 8)
    assert rates.shape == (2, 4)
    with pytest.raises(ValueError, match="sparsity"):
        PhaseToRateAutoencoder(n_input=8, n_oscillators=4, sparsity=1.5)
    with pytest.raises(ValueError):
        model(torch.randn(2, 7, dtype=torch.float64))


def test_dense_autoencoder_matches_reference() -> None:
    """Forward and classify match the reference dense baseline exactly."""
    pytest.importorskip("prinet.nn.layers")
    from prinet.nn.layers import DenseAutoencoder as Reference

    torch.manual_seed(3)
    reference = Reference(n_input=12, n_bottleneck=6).double()
    model = DenseAutoencoder(n_input=12, n_bottleneck=6)
    model.load_reference_weights(reference)

    x = torch.randn(4, 12, dtype=torch.float64)
    recon, codes = model(x)
    ref_recon, ref_codes = reference(x)
    torch.testing.assert_close(recon, ref_recon, rtol=1e-9, atol=1e-11)
    torch.testing.assert_close(codes, ref_codes, rtol=1e-9, atol=1e-11)
    torch.testing.assert_close(
        model.classify(x), reference.classify(x), rtol=1e-9, atol=1e-11
    )


def test_dense_autoencoder_gradcheck_and_errors() -> None:
    """The dense baseline gradchecks w.r.t. its input and validates config."""
    model = DenseAutoencoder(n_input=5, n_bottleneck=3, hidden=4, seed_counter=4)
    x = torch.randn(2, 5, dtype=torch.float64, requires_grad=True)
    assert torch.autograd.gradcheck(model, (x,), eps=1e-6, rtol=1e-3, atol=1e-3)
    assert model.n_bottleneck == 3
    with pytest.raises(ValueError):
        DenseAutoencoder(n_input=5, n_bottleneck=0)
    with pytest.raises(ValueError):
        model(torch.randn(2, 4, dtype=torch.float64))


def test_autoencoder_checkpoint_roundtrips() -> None:
    """Both autoencoder classes round-trip their Rust-owned parameters."""
    x = torch.randn(2, 6, dtype=torch.float64)
    ptr = PhaseToRateAutoencoder(n_input=6, n_oscillators=4, hidden=5, n_classes=3)
    ptr_before = ptr(x)[0]
    ptr.load_rust_state_dict(ptr.rust_state_dict())
    torch.testing.assert_close(ptr(x)[0], ptr_before)

    dense = DenseAutoencoder(n_input=6, n_bottleneck=4, hidden=5, n_classes=3)
    dense_before = dense.classify(x)
    dense.load_rust_state_dict(dense.rust_state_dict())
    torch.testing.assert_close(dense.classify(x), dense_before)


def test_replaced_symbols_are_real_and_public_surface_is_frozen() -> None:
    """The three symbols no longer have D-2.2 stub identities."""
    import prin.nn.autoencoders as implemented
    import prin.nn.deferred_layers as deferred

    for name in ("PhaseToRateConverter", "PhaseToRateAutoencoder", "DenseAutoencoder"):
        assert getattr(deferred, name) is getattr(implemented, name)
        assert getattr(prin, name) is getattr(implemented, name)
    assert verify_api_surface(prin.__all__) == (set(), set())
