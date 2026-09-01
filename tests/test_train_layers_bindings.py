"""WP-036 S1 (0141B) — WP-023 trainable-primitive compatibility surface.

Construct/callable smoke checks and ``float64`` ``torch.autograd.gradcheck``
for every differentiable binding. ``FeedbackInhibition`` is a straight-through
estimator (forward != backward by design) so a standard ``gradcheck`` does not
apply; its gradient contract is checked against the closed-form soft-term VJP
instead, matching ``crates/prin-train/src/inhibition.rs``'s own gradient test.

``dSiLU`` / ``PhaseActivation`` gradchecks use the DV-018 epsilon (``burn``
0.16.1's ``sigmoid`` downcasts through ``f32``); see
``DOCS/reports/DEFERRED_VALIDATION_REGISTER.md``.
"""

from __future__ import annotations

import prin
import pytest
import torch
from prin.nn import (
    FeedbackInhibition,
    HolomorphicActivation,
    HolomorphicEnergy,
    HolomorphicEPTrainer,
    PhaseActivation,
    ResonanceLayer,
    dSiLU,
)
from prin.nn._bridge import apply_rust_bridge

# DV-018: burn 0.16.1 sigmoid f32 precision floor.
_DV018 = {"eps": 1e-4, "atol": 1e-3, "rtol": 1e-3}


def test_symbols_resolve_from_prin_top_level() -> None:
    """All six WP-023 primitives resolve from the package root."""
    for name in (
        "dSiLU",
        "PhaseActivation",
        "HolomorphicActivation",
        "FeedbackInhibition",
        "HolomorphicEnergy",
        "HolomorphicEPTrainer",
    ):
        assert callable(getattr(prin, name))


# --- dSiLU ---------------------------------------------------------------


def test_dsilu_forward_matches_reference_at_zero() -> None:
    """``dSiLU(0) == 0.5`` and the shape is preserved."""
    act = dSiLU()
    out = act(torch.zeros(2, 3, dtype=torch.float64))
    assert out.shape == (2, 3)
    assert torch.allclose(out, torch.full((2, 3), 0.5, dtype=torch.float64), atol=1e-6)


def test_dsilu_gradcheck() -> None:
    """``dSiLU`` passes a float64 gradcheck at the DV-018 epsilon."""
    act = dSiLU()
    z = torch.randn(3, 4, dtype=torch.float64, requires_grad=True)
    assert torch.autograd.gradcheck(act, (z,), **_DV018)


# --- PhaseActivation --------------------------------------------------


def test_phase_activation_wraps_into_range() -> None:
    """Outputs lie in ``[0, 2*pi)``."""
    act = PhaseActivation()
    y = act(torch.randn(4, 6, dtype=torch.float64) * 5.0)
    assert bool((y >= 0).all() and (y < 2 * torch.pi).all())


def test_phase_activation_gradcheck() -> None:
    """``PhaseActivation`` passes a float64 gradcheck at the DV-018 epsilon."""
    act = PhaseActivation()
    # Positive inputs keep dSiLU(z) safely inside (0, 2*pi), away from the
    # modular-wrap and clamp discontinuities.
    z = (torch.rand(3, 4, dtype=torch.float64) * 2.0 + 0.5).requires_grad_(True)
    assert torch.autograd.gradcheck(act, (z,), **_DV018)


def test_phase_activation_accepts_custom_inner_activation() -> None:
    """A caller-supplied inner activation is wrapped to [0, 2π)."""
    act = PhaseActivation(activation=torch.nn.ReLU())
    z = torch.randn(4, 8, dtype=torch.float64)
    y = act(z)
    assert (y >= 0).all() and (y < 2 * torch.pi).all()


# --- HolomorphicActivation ------------------------------------------


def test_holomorphic_activation_real_input_is_scaled_tanh() -> None:
    """Real input reduces to ``scale * tanh(z)`` and exposes ``scale``."""
    act = HolomorphicActivation(scale=2.0)
    assert act.scale == pytest.approx(2.0)
    z = torch.tensor([[0.5, -0.5]], dtype=torch.float64)
    assert torch.allclose(act(z), 2.0 * torch.tanh(z), atol=1e-10)


def test_holomorphic_activation_complex_roundtrip_dtype() -> None:
    """Complex input returns a complex tensor of the same shape."""
    act = HolomorphicActivation()
    z = torch.randn(2, 3, dtype=torch.complex128)
    out = act(z)
    assert out.dtype == torch.complex128
    assert out.shape == z.shape


def test_holomorphic_activation_gradcheck_split_parts() -> None:
    """Split-complex ``(re, im)`` path passes a float64 gradcheck."""
    bridge = HolomorphicActivation(scale=1.5)._bridge
    re = torch.randn(2, 3, dtype=torch.float64, requires_grad=True)
    im = torch.randn(2, 3, dtype=torch.float64, requires_grad=True)
    assert torch.autograd.gradcheck(
        lambda a, b: apply_rust_bridge(bridge.forward, [a, b]), (re, im)
    )


def test_holomorphic_activation_true_complex_path() -> None:
    """The ``holomorphic=True`` branch applies true complex tanh."""
    act = HolomorphicActivation(scale=1.5, holomorphic=True)
    z = torch.randn(2, 3, dtype=torch.complex128)
    assert torch.allclose(act(z), 1.5 * torch.tanh(z), atol=1e-10)


# --- FeedbackInhibition ---------------------------------------------


def test_feedback_inhibition_forward_is_hard_topk() -> None:
    """Exactly ``k`` entries per row are nonzero in the forward pass."""
    fbi = FeedbackInhibition(k=3)
    rates = torch.rand(4, 8, dtype=torch.float64) + 0.1
    out = fbi.compete(rates)
    assert torch.equal((out.abs() > 1e-9).sum(-1), torch.full((4,), 3))


def test_feedback_inhibition_backward_matches_soft_term_vjp() -> None:
    """The STE gradient equals the closed-form soft-softmax term's VJP.

    Mirrors ``crates/prin-train/src/inhibition.rs``'s
    ``compete_gradient_matches_central_finite_difference``: at a non-winning
    index the STE's analytic gradient reduces exactly to
    ``d/d(rates) sum(softmax(rates / T) * rates)``.
    """
    temperature = 1.0
    base = torch.tensor([[0.1, 0.2, 9.0, 0.3]], dtype=torch.float64)

    def soft_sum(perturbed: torch.Tensor) -> torch.Tensor:
        return (torch.softmax(perturbed / temperature, dim=-1) * perturbed).sum()

    expected = torch.autograd.functional.jacobian(
        soft_sum, base.clone().requires_grad_(True)
    ).reshape(4)

    fbi = FeedbackInhibition(k=1, temperature=temperature)
    rates = base.clone().requires_grad_(True)
    fbi.compete(rates).sum().backward()
    assert rates.grad is not None
    # Index 1 is a non-winner: the hard-mask term contributes nothing there.
    assert torch.allclose(rates.grad[0, 1], expected[1], atol=1e-9)


def test_feedback_inhibition_accepts_arbitrary_leading_dims() -> None:
    """PRINet 3.0 parity (WP-036C S1 0144M3): ``rates`` may carry any number
    of leading dimensions; the result keeps the input shape with exactly
    ``k`` winners per trailing row."""
    fbi = FeedbackInhibition(k=2)
    rates = torch.rand(2, 3, 5, dtype=torch.float64) + 0.1
    out = fbi.compete(rates)
    assert out.shape == rates.shape
    assert torch.equal((out.abs() > 1e-9).sum(-1), torch.full((2, 3), 2))
    with pytest.raises(ValueError, match="at least one dimension"):
        fbi.compete(torch.tensor(0.5, dtype=torch.float64))


def test_feedback_inhibition_rejects_bad_config_and_exposes_hparams() -> None:
    """Constructor guards and the inert ``delay_steps`` accessor."""
    with pytest.raises(ValueError, match="k must be"):
        FeedbackInhibition(k=0)
    with pytest.raises(ValueError, match="sparsity"):
        FeedbackInhibition(sparsity=1.5)
    fbi = FeedbackInhibition(sparsity=0.25, delay_steps=7, temperature=2.0)
    assert fbi.delay_steps == 7
    assert fbi.temperature == pytest.approx(2.0)
    fbi.compete(torch.rand(2, 8, dtype=torch.float64) + 0.1)  # width 8 -> k = 2
    fbi.compete(torch.rand(2, 4, dtype=torch.float64) + 0.1)  # width change -> rebuild


# --- HolomorphicEnergy ---------------------------------------------


def test_holomorphic_energy_zero_at_unit_amplitude_no_coupling() -> None:
    """Unit-amplitude state with ``K = 0`` has zero energy."""
    energy = HolomorphicEnergy(4)
    assert energy.n_oscillators == 4
    z = torch.ones(2, 4, dtype=torch.complex128)
    k = torch.zeros(4, 4, dtype=torch.float64)
    assert float(energy(z, k)) == pytest.approx(0.0, abs=1e-12)
    # Real input path: imaginary part taken as zero -> same energy.
    assert float(energy(torch.ones(2, 4, dtype=torch.float64), k)) == pytest.approx(
        0.0, abs=1e-12
    )


def test_holomorphic_energy_task_term_gated_by_beta() -> None:
    """``task_loss`` is added only when ``beta`` is non-zero."""
    energy = HolomorphicEnergy(3)
    z = torch.ones(2, 3, dtype=torch.complex128)
    k = torch.zeros(3, 3, dtype=torch.float64)
    task = torch.full((2, 1), 2.0, dtype=torch.float64)
    assert float(energy(z, k, task, beta=0.0)) == pytest.approx(0.0, abs=1e-12)
    assert float(energy(z, k, task, beta=0.5)) == pytest.approx(1.0, abs=1e-12)


def test_holomorphic_energy_gradcheck() -> None:
    """Energy passes a float64 gradcheck w.r.t. ``(re, im, coupling)``."""
    bridge = HolomorphicEnergy(3)._bridge
    re = torch.randn(2, 3, dtype=torch.float64, requires_grad=True)
    im = torch.randn(2, 3, dtype=torch.float64, requires_grad=True)
    coupling = torch.randn(3, 3, dtype=torch.float64, requires_grad=True)
    assert torch.autograd.gradcheck(
        lambda a, b, c: apply_rust_bridge(
            lambda x, y, z: bridge.forward(x, y, z, None, 0.0), [a, b, c]
        ),
        (re, im, coupling),
    )


# --- HolomorphicEPTrainer -----------------------------------------


def test_hep_trainer_coupling_gradient_shape_and_finite() -> None:
    """The estimator returns a finite ``(N, N)`` coupling gradient."""
    layer = ResonanceLayer(4, 6, n_steps=3, seed_counter=1)
    trainer = HolomorphicEPTrainer(layer, beta=0.1, free_steps=4, nudge_steps=3)
    g = trainer.coupling_gradient(
        torch.ones(2, 6, dtype=torch.float64), torch.ones(2, 4, dtype=torch.float64)
    )
    assert g.shape == (4, 4)
    assert torch.isfinite(g).all()


def test_hep_trainer_free_energy_and_beta_setter() -> None:
    """``free_energy`` is scalar-finite and ``beta`` is settable."""
    layer = ResonanceLayer(4, 6, n_steps=3, seed_counter=2)
    trainer = HolomorphicEPTrainer(layer, beta=0.1, free_steps=4, nudge_steps=3)
    fe = trainer.free_energy(
        torch.ones(2, 6, dtype=torch.float64), torch.zeros(4, 4, dtype=torch.float64)
    )
    assert fe.shape == (1,)
    assert torch.isfinite(fe).all()
    trainer.beta = 0.25
    assert trainer.beta == pytest.approx(0.25)
    with pytest.raises(ValueError, match="beta"):
        trainer.beta = -1.0
    assert trainer.loss_history == []
    assert trainer.grad_norm_history == []


def test_hep_trainer_accepts_module_containing_a_resonance_layer() -> None:
    """A wrapping ``nn.Module`` is searched for a resonance layer."""

    class Wrapper(torch.nn.Module):
        """Minimal module holding a resonance layer."""

        def __init__(self) -> None:
            """Store one resonance layer as a child module."""
            super().__init__()
            self.layer = ResonanceLayer(3, 4, n_steps=2, seed_counter=3)

    trainer = HolomorphicEPTrainer(Wrapper(), free_steps=3, nudge_steps=2)
    assert trainer.beta == pytest.approx(0.1)


def test_hep_trainer_rejects_model_without_a_resonance_layer() -> None:
    """A model with no resonance layer is rejected."""
    with pytest.raises(ValueError, match="ResonanceLayer"):
        HolomorphicEPTrainer(torch.nn.Linear(3, 3))
