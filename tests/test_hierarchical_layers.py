"""WP-036A hierarchical, PAC, and discrete-layer parity and gradient tests."""

from __future__ import annotations

import math

import prin
import pytest
import torch
from prin._deprecation import verify_api_surface
from prin.nn import (
    DiscreteDeltaThetaGammaLayer,
    HierarchicalResonanceLayer,
    PhaseAmplitudeCouplingLayer,
)


def _input(batch: int = 2, width: int = 3) -> torch.Tensor:
    """Return deterministic non-boundary float64 input values."""
    values = torch.linspace(-0.4, 0.7, batch * width, dtype=torch.float64)
    return values.reshape(batch, width).requires_grad_(True)


def test_hierarchical_matches_installed_prinet_with_reference_weights() -> None:
    """Continuous amplitudes and wrapped phases match installed PRINet directly."""
    from prinet.nn.layers import HierarchicalResonanceLayer as Reference

    torch.manual_seed(11)
    reference = Reference(
        2,
        3,
        4,
        n_dims=3,
        n_steps=2,
        dt=0.001,
        coupling_strength=0.2,
        pac_depth=0.3,
    ).double()
    layer = HierarchicalResonanceLayer(
        2,
        3,
        4,
        n_dims=3,
        n_steps=2,
        dt=0.001,
        coupling_strength=0.2,
        pac_depth=0.3,
    )
    layer.load_reference_weights(reference)
    x = _input(batch=2)
    actual_amplitude, actual_phase = layer(x, return_phase=True)
    expected_amplitude, expected_phase = reference(x, return_phase=True)
    torch.testing.assert_close(
        actual_amplitude, expected_amplitude, rtol=1e-9, atol=1e-11
    )
    torch.testing.assert_close(actual_phase, expected_phase, rtol=1e-9, atol=1e-11)


def test_pac_matches_installed_prinet() -> None:
    """Mean-slow-phase PAC matches PRINet 3.0 for one batched row."""
    from prinet.nn.layers import PhaseAmplitudeCouplingLayer as Reference

    phase = torch.tensor([[0.2, 0.5, 0.9]], dtype=torch.float64)
    amplitude = torch.tensor([[0.7, 1.1, 1.4, 0.8]], dtype=torch.float64)
    actual = PhaseAmplitudeCouplingLayer(0.4)(phase, amplitude)
    expected = Reference(0.4).double()(phase, amplitude)
    # The reference stores ``initial_depth`` as float32 before ``.double()``;
    # its detached scalar therefore differs from the Rust f64 value by ~6e-9.
    torch.testing.assert_close(actual, expected, rtol=1e-8, atol=1e-9)


def test_discrete_layer_matches_installed_prinet_with_all_reference_weights() -> None:
    """Discrete projections, dynamics parameters, and outputs match PRINet."""
    from prinet.nn.layers import DiscreteDeltaThetaGammaLayer as Reference

    torch.manual_seed(12)
    reference = Reference(
        2,
        3,
        4,
        n_dims=3,
        n_steps=3,
        dt=0.001,
        coupling_strength=0.2,
        pac_depth=0.3,
    ).double()
    layer = DiscreteDeltaThetaGammaLayer(
        2,
        3,
        4,
        n_dims=3,
        n_steps=3,
        dt=0.001,
        coupling_strength=0.2,
        pac_depth=0.3,
    )
    layer.load_reference_weights(reference)
    x = _input(batch=2)
    # DV-018: Burn 0.16.1's sigmoid primitive uses f32-internal arithmetic on
    # the NdArray<f64> backend; the measured three-step maximum relative delta
    # is 1.39e-7, so this assertion uses the governed 2e-7 envelope.
    torch.testing.assert_close(layer(x), reference(x), rtol=2e-7, atol=2e-8)


def test_hierarchical_float64_gradcheck_includes_both_outputs() -> None:
    """Row 39 gradchecks both amplitude and wrapped-phase cotangent paths."""
    layer = HierarchicalResonanceLayer(
        1,
        1,
        1,
        n_dims=2,
        n_steps=1,
        dt=0.0001,
        coupling_strength=0.1,
        sparse_k=None,
        seed_counter=21,
    )
    x = torch.tensor([[0.31, -0.27]], dtype=torch.float64, requires_grad=True)
    assert torch.autograd.gradcheck(
        lambda value: layer(value, return_phase=True),
        (x,),
        eps=1e-6,
        rtol=1e-3,
        atol=1e-3,
    )
    assert torch.autograd.gradcheck(
        layer,
        (x,),
        eps=1e-6,
        rtol=1e-3,
        atol=1e-3,
    )


def test_pac_float64_gradcheck() -> None:
    """Row 40 gradchecks slow phase and fast amplitude inputs."""
    layer = PhaseAmplitudeCouplingLayer(0.35)
    phase = torch.tensor(
        [[0.2, 0.6], [0.4, 0.9]], dtype=torch.float64, requires_grad=True
    )
    amplitude = torch.tensor(
        [[0.8, 1.1, 0.7], [1.2, 0.9, 1.3]], dtype=torch.float64, requires_grad=True
    )
    assert torch.autograd.gradcheck(
        layer, (phase, amplitude), eps=1e-6, rtol=1e-3, atol=1e-3
    )


def test_discrete_layer_float64_gradcheck() -> None:
    """Row 44 gradchecks the complete projected discrete integration."""
    layer = DiscreteDeltaThetaGammaLayer(
        1, 1, 1, n_dims=2, n_steps=1, dt=0.0001, seed_counter=22
    )
    x = torch.tensor([[0.31, -0.27]], dtype=torch.float64, requires_grad=True)
    # DV-018: eps=1e-5 rises above Burn's f32-internal sigmoid finite-
    # difference floor; the required rtol/atol remain exactly 1e-3.
    assert torch.autograd.gradcheck(layer, (x,), eps=1e-5, rtol=1e-3, atol=1e-3)


def test_hierarchical_batch_equals_concatenated_per_sample() -> None:
    """The D-5 fully batched row-39 path equals independent sample calls."""
    layer = HierarchicalResonanceLayer(
        2,
        2,
        2,
        n_dims=3,
        n_steps=1,
        dt=0.001,
        coupling_strength=0.2,
        sparse_k=1,
        seed_counter=23,
    )
    x = _input(batch=3)
    batch_amplitude, batch_phase = layer(x, return_phase=True)
    singles = [layer(x[index], return_phase=True) for index in range(x.shape[0])]
    expected_amplitude = torch.stack([result[0] for result in singles])
    expected_phase = torch.stack([result[1] for result in singles])
    torch.testing.assert_close(
        batch_amplitude, expected_amplitude, rtol=1e-12, atol=1e-12
    )
    torch.testing.assert_close(batch_phase, expected_phase, rtol=1e-12, atol=1e-12)


def test_vector_shapes_properties_and_wrapped_phase() -> None:
    """Wrappers preserve vectors and expose their configured dimensions."""
    hierarchical = HierarchicalResonanceLayer(1, 2, 3, n_dims=2, n_steps=1, dt=0.0001)
    x = torch.tensor([0.2, -0.3], dtype=torch.float64)
    amplitude, phase = hierarchical(x, return_phase=True)
    assert amplitude.shape == (6,)
    assert phase.shape == (6,)
    assert hierarchical.n_delta == 1
    assert hierarchical.n_theta == 2
    assert hierarchical.n_gamma == 3
    assert hierarchical.n_total == 6
    assert hierarchical.n_dims == 2
    assert torch.all((phase >= 0.0) & (phase < 2.0 * math.pi))

    pac = PhaseAmplitudeCouplingLayer()
    assert pac(
        torch.zeros(2, dtype=torch.float64), torch.ones(3, dtype=torch.float64)
    ).shape == (3,)
    discrete = DiscreteDeltaThetaGammaLayer(1, 2, 3, n_dims=2, n_steps=1)
    assert discrete(x).shape == (6,)
    assert discrete.n_total == 6
    assert discrete.n_dims == 2


def test_construction_and_input_errors_are_typed() -> None:
    """Invalid configurations, ranks, dimensions, and batch shapes fail loudly."""
    with pytest.raises(ValueError, match="delta"):
        HierarchicalResonanceLayer(0, 1, 1, n_dims=2)
    with pytest.raises(ValueError, match="n_steps"):
        HierarchicalResonanceLayer(1, 1, 1, n_dims=2, n_steps=0)
    with pytest.raises(ValueError, match="pac_depth"):
        HierarchicalResonanceLayer(1, 1, 1, n_dims=2, pac_depth=1.5)
    with pytest.raises(ValueError, match="initial_depth"):
        PhaseAmplitudeCouplingLayer(-0.1)
    with pytest.raises(ValueError, match="input"):
        DiscreteDeltaThetaGammaLayer(1, 1, 1, n_dims=0)

    hierarchical = HierarchicalResonanceLayer(1, 1, 1, n_dims=2, n_steps=1)
    with pytest.raises(ValueError, match="1-D or 2-D"):
        hierarchical(torch.zeros(1, 1, 2, dtype=torch.float64))
    with pytest.raises(ValueError, match="expected shape"):
        hierarchical(torch.zeros(1, 3, dtype=torch.float64))
    pac = PhaseAmplitudeCouplingLayer()
    with pytest.raises(ValueError, match="matching ranks"):
        pac(torch.zeros(2, dtype=torch.float64), torch.ones(1, 3, dtype=torch.float64))
    with pytest.raises(ValueError, match="expected shape"):
        pac(
            torch.zeros(2, 2, dtype=torch.float64),
            torch.ones(3, 2, dtype=torch.float64),
        )


def test_checkpoint_roundtrips_and_rejects_malformed_bytes() -> None:
    """All three Rust-owned records round-trip and reject malformed bytes."""
    x = torch.tensor([[0.2, -0.3]], dtype=torch.float64)
    hierarchical = HierarchicalResonanceLayer(1, 1, 1, n_dims=2, n_steps=1)
    before_h = hierarchical(x, return_phase=True)
    hierarchical.load_rust_state_dict(hierarchical.rust_state_dict())
    after_h = hierarchical(x, return_phase=True)
    torch.testing.assert_close(before_h[0], after_h[0])
    torch.testing.assert_close(before_h[1], after_h[1])

    pac = PhaseAmplitudeCouplingLayer(0.4)
    phase = torch.tensor([[0.2, 0.4]], dtype=torch.float64)
    fast = torch.tensor([[0.8, 1.2]], dtype=torch.float64)
    before_p = pac(phase, fast)
    pac.load_rust_state_dict(pac.rust_state_dict())
    torch.testing.assert_close(before_p, pac(phase, fast))

    discrete = DiscreteDeltaThetaGammaLayer(1, 1, 1, n_dims=2, n_steps=1)
    before_d = discrete(x)
    discrete.load_rust_state_dict(discrete.rust_state_dict())
    torch.testing.assert_close(before_d, discrete(x))

    for model in (hierarchical, pac, discrete):
        with pytest.raises(ValueError, match="checkpoint"):
            model.load_rust_state_dict(b"not-a-checkpoint")


def test_reference_weight_injection_rejects_incompatible_layer() -> None:
    """Reference injection validates every projection and dynamics shape."""
    from prinet.nn.layers import DiscreteDeltaThetaGammaLayer as ReferenceDiscrete
    from prinet.nn.layers import HierarchicalResonanceLayer as ReferenceHierarchical

    hierarchical = HierarchicalResonanceLayer(1, 1, 1, n_dims=2, n_steps=1)
    with pytest.raises(ValueError, match="proj_delta"):
        hierarchical.load_reference_weights(
            ReferenceHierarchical(2, 1, 1, n_dims=2, n_steps=1).double()
        )
    discrete = DiscreteDeltaThetaGammaLayer(1, 1, 1, n_dims=2, n_steps=1)
    with pytest.raises(ValueError):
        discrete.load_reference_weights(
            ReferenceDiscrete(2, 1, 1, n_dims=2, n_steps=1).double()
        )


def test_reexports_are_real_and_public_surface_remains_frozen() -> None:
    """Rows 39, 40, and 44 resolve to implementations from every public path."""
    import prin.nn.deferred_layers as deferred
    import prin.nn.hierarchical_layers as implemented

    for name in (
        "HierarchicalResonanceLayer",
        "PhaseAmplitudeCouplingLayer",
        "DiscreteDeltaThetaGammaLayer",
    ):
        assert getattr(deferred, name) is getattr(implemented, name)
        assert getattr(prin.nn, name) is getattr(implemented, name)
        assert getattr(prin, name) is getattr(implemented, name)
    assert verify_api_surface(prin.__all__) == (set(), set())
