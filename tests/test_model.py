"""WP-036A sub-pass 0144A4 — ``PRINetModel`` and ``compile_model`` tests.

Forward-parity note: PRINet 3.0's ``PRINetModel.forward`` hard-casts the
post-resonance hidden state to ``float32`` (``h = h.float()``), which makes the
reference's own ``forward`` raise ``RuntimeError`` on a ``.double()`` model, so
a float64 end-to-end reference output does not exist. Parity is therefore
established (a) against a float64 reproduction of the reference readout run on
the reference's own submodules, and (b) against the reference's real float32
``forward`` under a D-4 tolerance. Both use a zero input, the regime where the
composed ``ResonanceLayer`` coincides exactly with the reference (its
FFT-vs-matmul initial-encoding deviation, plan amendment #19, is inherited
unchanged).
"""

from __future__ import annotations

import prin
import pytest
import torch
from prin._deprecation import verify_api_surface
from prin.nn import PRINetModel, compile_model


def _small_model(n_layers: int = 2, **kwargs: object) -> PRINetModel:
    """A deterministic small model for shape/gradient tests."""
    params: dict[str, object] = {
        "n_resonances": 3,
        "n_dims": 4,
        "n_concepts": 2,
        "n_layers": n_layers,
        "n_steps": 1,
        "dt": 1e-3,
        "seed_counter": 5,
    }
    params.update(kwargs)
    return PRINetModel(**params)  # type: ignore[arg-type]


def _reference_readout_f64(reference: object, x: torch.Tensor) -> torch.Tensor:
    """Reproduce ``PRINetModel.forward`` in float64, skipping the broken cast."""
    h = reference.input_layer(x)  # type: ignore[attr-defined]
    h = reference.layer_norms[0](h)  # type: ignore[attr-defined]
    for index, layer in enumerate(reference.layers):  # type: ignore[attr-defined]
        h = layer(h)
        h = reference.layer_norms[index + 1](h)  # type: ignore[attr-defined]
    logits = torch.clamp(reference.concept_proj(h), min=-50.0, max=50.0)  # type: ignore[attr-defined]
    return torch.log_softmax(logits, dim=-1)


def test_forward_returns_log_probabilities() -> None:
    """Output is ``(batch, n_concepts)`` log-probs; each row sums to 1."""
    model = _small_model()
    x = torch.linspace(-0.4, 0.7, 12, dtype=torch.float64).reshape(3, 4)
    out = model(x)
    assert out.shape == (3, 2)
    assert torch.all(out <= 0.0)
    torch.testing.assert_close(
        out.exp().sum(-1), torch.ones(3, dtype=torch.float64), rtol=1e-9, atol=1e-11
    )
    assert model.n_resonances == 3
    assert model.n_dims == 4
    assert model.n_concepts == 2
    assert model.n_layers == 2


def test_reference_forward_raises_in_float64_but_prin_does_not() -> None:
    """Document the reference's broken f64 path that motivates the parity design."""
    pytest.importorskip("prinet.nn.layers")
    from prinet.nn.layers import PRINetModel as Reference

    reference = Reference(
        n_resonances=3, n_dims=4, n_concepts=2, n_layers=1, n_steps=1
    ).double()
    with pytest.raises(RuntimeError, match="same dtype"):
        reference(torch.zeros(2, 4, dtype=torch.float64))
    # PRIN runs the same shape in float64 without complaint.
    assert _small_model(n_layers=1)(torch.zeros(2, 4, dtype=torch.float64)).shape == (
        2,
        2,
    )


def test_forward_parity_vs_reference_readout_float64() -> None:
    """At a zero input, the full model matches the reference readout in f64."""
    pytest.importorskip("prinet.nn.layers")
    from prinet.nn.layers import PRINetModel as Reference

    torch.manual_seed(7)
    reference = Reference(
        n_resonances=4, n_dims=5, n_concepts=3, n_layers=1, n_steps=2, dt=0.01
    ).double()
    model = PRINetModel(4, 5, 3, n_layers=1, n_steps=2, dt=0.01)
    model.load_reference_weights(reference)

    x = torch.zeros(3, 5, dtype=torch.float64)
    torch.testing.assert_close(
        model(x), _reference_readout_f64(reference, x), rtol=1e-9, atol=1e-11
    )


def test_forward_parity_vs_reference_default_float32() -> None:
    """The real reference ``forward`` (float32) matches PRIN under a D-4 envelope."""
    pytest.importorskip("prinet.nn.layers")
    from prinet.nn.layers import PRINetModel as Reference

    torch.manual_seed(9)
    reference = Reference(
        n_resonances=4, n_dims=5, n_concepts=3, n_layers=1, n_steps=2, dt=0.01
    )
    model = PRINetModel(4, 5, 3, n_layers=1, n_steps=2, dt=0.01)
    model.load_reference_weights(reference)  # _marshal casts to float64

    x = torch.zeros(3, 5)
    reference_out = reference(x)
    # D-4: the reference runs the whole readout in float32; PRIN runs it in
    # float64. At a zero input the ResonanceLayer encoding coincides, so the
    # only source of disagreement is the f32-vs-f64 hazard.
    torch.testing.assert_close(
        model(x.double()).float(), reference_out, rtol=1e-4, atol=1e-5
    )


@pytest.mark.parametrize("n_layers", [1, 2])
def test_float64_gradcheck(n_layers: int) -> None:
    """The mandatory acceptance criterion: gradcheck in float64."""
    model = _small_model(
        n_layers=n_layers, n_resonances=3, n_dims=2, n_concepts=2, n_steps=1
    )
    x = torch.tensor(
        [[0.31, -0.27], [0.12, 0.4]], dtype=torch.float64, requires_grad=True
    )
    assert torch.autograd.gradcheck(model, (x,), eps=1e-6, rtol=1e-3, atol=1e-3)


def test_batched_forward_matches_stacked_single_rows() -> None:
    """A batched call equals independent single-row calls stacked."""
    model = _small_model()
    x = torch.linspace(-0.5, 0.6, 12, dtype=torch.float64).reshape(3, 4)
    batched = model(x)
    singles = torch.cat([model(x[i : i + 1]) for i in range(3)], dim=0)
    torch.testing.assert_close(batched, singles, rtol=1e-12, atol=1e-12)


def test_compile_model_returns_a_callable_wrapper() -> None:
    """``compile_model`` wraps a constructed ``PRINetModel`` and stays callable."""
    model = _small_model(n_layers=1)
    compiled = compile_model(model)
    assert callable(compiled)
    x = torch.zeros(2, 4, dtype=torch.float64)
    torch.testing.assert_close(compiled(x), model(x))


def test_compile_model_passthrough_when_torch_compile_absent(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Without ``torch.compile`` the model is returned unchanged (guard path)."""
    monkeypatch.delattr(torch, "compile", raising=True)
    model = _small_model(n_layers=1)
    assert compile_model(model) is model


def test_construction_and_input_errors_are_typed() -> None:
    """Invalid configuration and input shapes fail loudly."""
    with pytest.raises(ValueError, match="resonances"):
        PRINetModel(0, 4, 2)
    with pytest.raises(ValueError, match="concepts"):
        PRINetModel(3, 4, 0)
    with pytest.raises(ValueError, match="n_layers"):
        PRINetModel(3, 4, 2, n_layers=0)
    with pytest.raises(ValueError, match="dt"):
        PRINetModel(3, 4, 2, dt=0.0)

    model = _small_model(n_layers=1)
    with pytest.raises(ValueError, match="2-D"):
        model(torch.zeros(3, dtype=torch.float64))
    with pytest.raises(ValueError, match="expected shape"):
        model(torch.zeros(2, 5, dtype=torch.float64))


def test_checkpoint_roundtrips_and_rejects_malformed_bytes() -> None:
    """The Rust-owned record round-trips and rejects malformed bytes."""
    model = _small_model()
    x = torch.linspace(-0.3, 0.5, 12, dtype=torch.float64).reshape(3, 4)
    before = model(x)
    model.load_rust_state_dict(model.rust_state_dict())
    torch.testing.assert_close(model(x), before)
    with pytest.raises(ValueError, match="checkpoint"):
        model.load_rust_state_dict(b"not-a-checkpoint")


def test_reference_weight_injection_rejects_incompatible_model() -> None:
    """A wrong layer count in the injected reference is a typed error."""
    pytest.importorskip("prinet.nn.layers")
    from prinet.nn.layers import PRINetModel as Reference

    model = PRINetModel(3, 4, 2, n_layers=1, n_steps=1)
    with pytest.raises(ValueError, match="weight tensors"):
        model.load_reference_weights(
            Reference(
                n_resonances=3, n_dims=4, n_concepts=2, n_layers=2, n_steps=1
            ).double()
        )


def test_reexports_are_real_and_public_surface_remains_frozen() -> None:
    """Rows 41 and 42 resolve to implementations from every public path."""
    import prin.nn.deferred_layers as deferred
    import prin.nn.model as implemented

    for name in ("PRINetModel", "compile_model"):
        assert getattr(deferred, name) is getattr(implemented, name)
        assert getattr(prin.nn, name) is getattr(implemented, name)
        assert getattr(prin, name) is getattr(implemented, name)
    assert verify_api_surface(prin.__all__) == (set(), set())
