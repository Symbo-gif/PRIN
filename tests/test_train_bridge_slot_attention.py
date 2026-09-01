"""Integration tests for `prin.nn.SlotAttentionModule`/
`prin.nn.TemporalSlotAttentionMOT` (Exec-WP-026 S1): the non-oscillatory
SlotAttention comparison baseline.

Covers the seed-snapshot recompute contract (gradcheck against a *fresh*
`Seed` per finite-difference call — see the module docs below for why),
per-call stochastic determinism (same starting `Seed` state ⇒ identical
output), the non-differentiable `match_frames`/`track_sequence` utilities,
and checkpoint round-trips.

**Why gradcheck needs a fresh `Seed` per call.** `torch.autograd.gradcheck`
perturbs the input and re-invokes the wrapped function repeatedly, expecting
each invocation to run the *same* underlying computation except for the
input perturbation. Since `SlotAttentionModule.forward`/
`TemporalSlotAttentionMOT.process_frame` draw fresh stochastic noise from
whatever `Seed` they are given (and a `Seed` is mutated/advanced by each
call — Coding Standards §1.3), reusing one mutable `Seed` object across
gradcheck's internal calls would draw *different* noise each time, which
gradcheck would (correctly) report as a Jacobian mismatch. Passing
`Seed(10, 0)` fresh inside the lambda restores a fixed starting state for
every call, matching what the Rust `*Ctx.backward()` recompute does
internally (see `crates/prin-py/src/bindings/slot_attention.rs`'s module
docs).

DV-018-class precision floor: the GRU's sigmoid/tanh gates hit the same
`burn-tensor` f32-downcast floor `GatedPhaseActivation`'s gradcheck already
documents, requiring the same loosened `eps=1e-4, atol=3e-3` tolerance
(empirically verified during this session — the default `eps=1e-6, atol=1e-4`
fails by a further-loosening-resolves-it margin, not a structural mismatch).
"""

from __future__ import annotations

import pytest
import torch
from prin._prin_core import Seed
from prin.nn import SlotAttentionModule, TemporalSlotAttentionMOT

_EPS = 1e-4
_ATOL = 3e-3


@pytest.fixture(autouse=True)
def _seed_torch() -> None:
    """Seed the global torch RNG so unseeded ``torch.randn`` inputs are stable.

    Several tests here gradcheck ``process_frame`` / the slot-attention bridge,
    which contain a data-dependent greedy-matching branch (``match_threshold``).
    On an unseeded input a draw can land on a matching boundary where the
    numerical Jacobian is discontinuous and gradcheck spuriously fails — this
    was masked locally by RNG state from earlier tests and only surfaced once
    CI ran the suite in a different order (ETCA-001 remediation, Testing
    Standards §1.5).
    """
    torch.manual_seed(0)


@pytest.fixture
def slot_attention() -> SlotAttentionModule:
    return SlotAttentionModule(3, 8, 5, seed_counter=1)


@pytest.fixture
def mot() -> TemporalSlotAttentionMOT:
    return TemporalSlotAttentionMOT(
        4, num_slots=3, slot_dim=4, num_iterations=2, seed_counter=9
    )


class TestSlotAttentionModuleShapeAndDeterminism:
    def test_accessors_report_configured_sizes(
        self, slot_attention: SlotAttentionModule
    ) -> None:
        assert slot_attention.num_slots == 3
        assert slot_attention.slot_dim == 8

    def test_forward_output_shape_and_dtype(
        self, slot_attention: SlotAttentionModule
    ) -> None:
        inputs = torch.rand(1, 4, 5, dtype=torch.float64)
        out = slot_attention(inputs, Seed(10, 0))
        assert out.shape == (1, 3, 8)
        assert out.dtype == torch.float64

    def test_same_seed_gives_identical_output(
        self, slot_attention: SlotAttentionModule
    ) -> None:
        inputs = torch.rand(1, 4, 5, dtype=torch.float64)
        out1 = slot_attention(inputs, Seed(10, 0))
        out2 = slot_attention(inputs, Seed(10, 0))
        torch.testing.assert_close(out1, out2)

    def test_different_seed_gives_different_output(
        self, slot_attention: SlotAttentionModule
    ) -> None:
        inputs = torch.rand(1, 4, 5, dtype=torch.float64)
        out1 = slot_attention(inputs, Seed(10, 0))
        out2 = slot_attention(inputs, Seed(20, 0))
        assert not torch.allclose(out1, out2)

    def test_seed_is_advanced_by_forward(
        self, slot_attention: SlotAttentionModule
    ) -> None:
        inputs = torch.rand(1, 4, 5, dtype=torch.float64)
        seed = Seed(10, 0)
        counter_before = seed.counter
        slot_attention(inputs, seed)
        assert seed.counter > counter_before


class TestSlotAttentionModuleGradients:
    def test_gradcheck_float64(self, slot_attention: SlotAttentionModule) -> None:
        # The slot-update MLP applies `relu` (a non-differentiable kink at
        # 0); a local `Generator` pins a draw confirmed clear of it — see
        # `test_train_bridge_phase_tracker.py::test_encode_gradcheck`'s
        # comment for the full rationale.
        gen = torch.Generator().manual_seed(0)
        inputs = torch.rand(
            1, 4, 5, dtype=torch.float64, generator=gen
        ).requires_grad_()
        assert torch.autograd.gradcheck(
            lambda x: slot_attention(x, Seed(10, 0)), (inputs,), eps=_EPS, atol=_ATOL
        )


class TestSlotAttentionModuleCheckpoint:
    def test_roundtrip_preserves_output(
        self, slot_attention: SlotAttentionModule
    ) -> None:
        inputs = torch.rand(1, 4, 5, dtype=torch.float64)
        before = slot_attention(inputs, Seed(10, 0))
        state = slot_attention.rust_state_dict()
        restored = SlotAttentionModule(3, 8, 5, seed_counter=99)
        restored.load_rust_state_dict(state)
        after = restored(inputs, Seed(10, 0))
        torch.testing.assert_close(before, after)

    def test_rejects_shape_mismatch_and_leaves_self_unchanged(
        self, slot_attention: SlotAttentionModule
    ) -> None:
        state = slot_attention.rust_state_dict()
        target = SlotAttentionModule(3, 6, 5, seed_counter=1)
        with pytest.raises(ValueError, match="shape mismatch"):
            target.load_rust_state_dict(state)
        assert target.slot_dim == 6


class TestTemporalSlotAttentionMOT:
    def test_accessors_report_configured_sizes(
        self, mot: TemporalSlotAttentionMOT
    ) -> None:
        assert mot.num_slots == 3
        assert mot.slot_dim == 4
        assert mot.match_threshold == pytest.approx(0.3)

    def test_process_frame_output_shape(self, mot: TemporalSlotAttentionMOT) -> None:
        dets = torch.randn(3, 4, dtype=torch.float64)
        slots = mot.process_frame(dets, Seed(20, 0))
        assert slots.shape == (1, 3, 4)

    def test_process_frame_with_prev_slots(self, mot: TemporalSlotAttentionMOT) -> None:
        dets1 = torch.randn(3, 4, dtype=torch.float64)
        slots1 = mot.process_frame(dets1, Seed(20, 0))
        dets2 = torch.randn(3, 4, dtype=torch.float64)
        slots2 = mot.process_frame(dets2, Seed(21, 0), slots1)
        assert slots2.shape == (1, 3, 4)

    def test_process_frame_gradcheck(self, mot: TemporalSlotAttentionMOT) -> None:
        dets = torch.randn(3, 4, dtype=torch.float64, requires_grad=True)
        assert torch.autograd.gradcheck(
            lambda d: mot.process_frame(d, Seed(20, 0)), (dets,), eps=_EPS, atol=_ATOL
        )

    def test_process_frame_gradcheck_with_prev_slots(
        self, mot: TemporalSlotAttentionMOT
    ) -> None:
        dets1 = torch.randn(3, 4, dtype=torch.float64)
        prev = mot.process_frame(dets1, Seed(20, 0)).detach().requires_grad_()
        dets2 = torch.randn(3, 4, dtype=torch.float64, requires_grad=True)
        assert torch.autograd.gradcheck(
            lambda d, p: mot.process_frame(d, Seed(21, 0), p),
            (dets2, prev),
            eps=_EPS,
            atol=_ATOL,
        )

    def test_slot_similarity_gradcheck(self, mot: TemporalSlotAttentionMOT) -> None:
        a = torch.randn(1, 3, 4, dtype=torch.float64, requires_grad=True)
        b = torch.randn(1, 3, 4, dtype=torch.float64, requires_grad=True)
        assert torch.autograd.gradcheck(
            lambda x, y: mot.slot_similarity(x, y), (a, b), eps=1e-6, atol=1e-4
        )

    def test_match_frames_non_differentiable(
        self, mot: TemporalSlotAttentionMOT
    ) -> None:
        dets_t = torch.randn(4, 4, dtype=torch.float64)
        dets_t1 = torch.randn(4, 4, dtype=torch.float64)
        matches, sim = mot.match_frames(dets_t, dets_t1, Seed(30, 0))
        assert len(matches) == 3
        assert sim.shape == (3, 3)
        assert not sim.requires_grad

    def test_track_sequence(self, mot: TemporalSlotAttentionMOT) -> None:
        frames = [torch.randn(4, 4, dtype=torch.float64) for _ in range(3)]
        result = mot.track_sequence(frames, Seed(40, 0))
        history = result["slot_history"]
        identity_matches = result["identity_matches"]
        preservation = result["identity_preservation"]
        sims = result["per_frame_similarity"]
        assert len(history) == 3
        assert all(h.shape == (1, 3, 4) for h in history)
        assert len(identity_matches) == 2
        assert 0.0 <= preservation <= 1.0
        assert len(sims) == 2

    def test_checkpoint_roundtrip(self, mot: TemporalSlotAttentionMOT) -> None:
        dets = torch.randn(3, 4, dtype=torch.float64)
        before = mot.process_frame(dets, Seed(20, 0))
        state = mot.rust_state_dict()
        restored = TemporalSlotAttentionMOT(
            4, num_slots=3, slot_dim=4, num_iterations=2, seed_counter=99
        )
        restored.load_rust_state_dict(state)
        after = restored.process_frame(dets, Seed(20, 0))
        torch.testing.assert_close(before, after)

    def test_checkpoint_rejects_shape_mismatch(
        self, mot: TemporalSlotAttentionMOT
    ) -> None:
        state = mot.rust_state_dict()
        target = TemporalSlotAttentionMOT(
            4, num_slots=3, slot_dim=6, num_iterations=2, seed_counter=1
        )
        with pytest.raises(ValueError, match="shape mismatch"):
            target.load_rust_state_dict(state)
