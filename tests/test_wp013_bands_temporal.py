"""WP-013 acceptance tests: band networks and temporal propagation bindings."""

from __future__ import annotations

import math

import numpy as np
import pytest
from prin._prin_core import (
    AMPLITUDE_MAX,
    AMPLITUDE_MIN,
    BandNetwork,
    BandParams,
    ComplexPhasorBlender,
    CouplingMode,
    EmaAmplitudeBlender,
    KuramotoOscillator,
    OscillatorState,
    PacPair,
    Seed,
    TemporalPropagator,
    create_band_state_py,
)

TAU = 2.0 * math.pi


# ---------------------------------------------------------------------------
# BandParams
# ---------------------------------------------------------------------------


class TestBandParams:
    def test_construction(self) -> None:
        bp = BandParams(1.0, 0.1)
        assert bp.coupling_strength == pytest.approx(1.0)
        assert bp.decay_rate == pytest.approx(0.1)

    def test_invalid_params_rejected(self) -> None:
        with pytest.raises(ValueError):
            BandParams(float("nan"), 0.1)
        with pytest.raises(ValueError):
            BandParams(1.0, float("inf"))

    def test_repr(self) -> None:
        bp = BandParams(1.0, 0.1)
        assert "BandParams" in repr(bp)

    def test_defaults_are_mean_field_without_frequency_adaptation(self) -> None:
        bp = BandParams(1.0, 0.1)
        assert bp.freq_adaptation_rate == pytest.approx(0.0)
        assert bp.coupling_mode.variant() == "mean_field"

    def test_explicit_coupling_mode_and_adaptation(self) -> None:
        bp = BandParams(2.0, 0.1, 0.05, CouplingMode.sparse_knn(3))
        assert bp.freq_adaptation_rate == pytest.approx(0.05)
        assert bp.coupling_mode.variant() == "sparse_knn"
        assert "sparse_knn" in repr(bp)

    def test_non_finite_adaptation_rejected(self) -> None:
        with pytest.raises(ValueError):
            BandParams(1.0, 0.1, float("nan"))


# ---------------------------------------------------------------------------
# PacPair
# ---------------------------------------------------------------------------


class TestPacPair:
    def test_construction(self) -> None:
        pp = PacPair(0, 1, 0.3, 0.0)
        assert pp.slow_band == 0
        assert pp.fast_band == 1
        assert pp.modulation_depth == pytest.approx(0.3)
        assert pp.phase_offset == pytest.approx(0.0)

    def test_invalid_depth_rejected(self) -> None:
        with pytest.raises(ValueError):
            PacPair(0, 1, -0.1, 0.0)

    def test_repr(self) -> None:
        pp = PacPair(0, 1, 0.3, 0.5)
        assert "PacPair" in repr(pp)


# ---------------------------------------------------------------------------
# BandNetwork
# ---------------------------------------------------------------------------


class TestBandNetwork:
    def test_theta_gamma_factory(self) -> None:
        tp = BandParams(1.0, 0.1)
        gp = BandParams(0.5, 0.1)
        net = BandNetwork.theta_gamma(4, 8, tp, gp, 0.3)
        assert net.n_bands() == 2
        assert net.total_oscillators() == 12
        assert net.band_sizes() == [4, 8]

    def test_delta_theta_gamma_factory(self) -> None:
        dp = BandParams(0.8, 0.1)
        tp = BandParams(1.0, 0.1)
        gp = BandParams(0.5, 0.1)
        net = BandNetwork.delta_theta_gamma(2, 4, 8, dp, tp, gp, 0.2, 0.3)
        assert net.n_bands() == 3
        assert net.total_oscillators() == 14

    def test_generic_construction(self) -> None:
        params = [BandParams(1.0, 0.1), BandParams(0.5, 0.1)]
        pairs = [PacPair(0, 1, 0.3, 0.0)]
        net = BandNetwork([4, 8], params, pairs)
        assert net.n_bands() == 2
        assert net.band_size(0) == 4
        assert net.band_size(1) == 8

    def test_empty_band_rejected(self) -> None:
        with pytest.raises(ValueError):
            BandNetwork([0, 4], [BandParams(1.0, 0.1), BandParams(0.5, 0.1)], [])

    def test_no_bands_rejected_with_distinct_message(self) -> None:
        with pytest.raises(ValueError, match="at least one band"):
            BandNetwork([], [], [])

    def test_non_adjacent_pac_pair_accepted(self) -> None:
        params = [BandParams(0.8, 0.1), BandParams(1.0, 0.1), BandParams(0.5, 0.1)]
        net = BandNetwork([2, 4, 8], params, [PacPair(0, 2, 0.3, 0.0)])
        seed = Seed(7, 0)
        state = create_band_state_py(net, [(1.0, 3.0), (5.0, 7.0), (35.0, 45.0)], seed)
        _, da, _ = net.compute_derivatives(state)
        assert np.all(np.isfinite(da))

    def test_invalid_sparse_k_rejected_at_construction(self) -> None:
        params = [
            BandParams(1.0, 0.1, 0.0, CouplingMode.sparse_knn(9)),
            BandParams(0.5, 0.1),
        ]
        with pytest.raises(ValueError):
            BandNetwork([4, 8], params, [])

    def test_band_derivatives_match_standalone_kuramoto(self) -> None:
        """Intra-band terms are the crate's Kuramoto model on the band sub-state."""
        mode = CouplingMode.sparse_knn(2)
        tp = BandParams(2.0, 0.1, 0.01, mode)
        gp = BandParams(2.0, 0.1, 0.01, CouplingMode.sparse_knn(2))
        # PAC depth 0 leaves the intra-band terms untouched.
        net = BandNetwork.theta_gamma(4, 8, tp, gp, 0.0)
        seed = Seed(2024, 0)
        state = create_band_state_py(net, [(5.0, 7.0), (35.0, 45.0)], seed)
        dp, da, df = net.compute_derivatives(state)

        phase = state.phase
        amplitude = state.amplitude
        frequency = state.frequency
        bands = state.freq_band
        assert bands is not None

        for band, size in ((0, 4), (1, 8)):
            idx = np.flatnonzero(bands == band)
            assert idx.size == size
            sub = OscillatorState(
                phase[idx].copy(), amplitude[idx].copy(), frequency[idx].copy(), None
            )
            model = KuramotoOscillator(
                idx.size, 2.0, 0.1, 0.01, CouplingMode.sparse_knn(2)
            )
            expected = model.compute_derivatives(sub)
            np.testing.assert_allclose(dp[idx], expected.dphase, rtol=0, atol=1e-14)
            np.testing.assert_allclose(da[idx], expected.damplitude, rtol=0, atol=1e-14)
            np.testing.assert_allclose(df[idx], expected.dfrequency, rtol=0, atol=1e-14)
        assert mode.variant() == "sparse_knn"

    def test_coupling_mode_changes_dynamics(self) -> None:
        def build(mode: CouplingMode) -> BandNetwork:
            return BandNetwork.theta_gamma(
                4,
                8,
                BandParams(2.0, 0.1, 0.0, mode),
                BandParams(2.0, 0.1, 0.0, mode),
                0.3,
            )

        mean_field = build(CouplingMode.mean_field())
        sparse = build(CouplingMode.sparse_knn(2))
        seed = Seed(31, 0)
        state = create_band_state_py(mean_field, [(5.0, 7.0), (35.0, 45.0)], seed)
        dp_mf, _, _ = mean_field.compute_derivatives(state)
        dp_sk, _, _ = sparse.compute_derivatives(state)
        assert np.max(np.abs(dp_mf - dp_sk)) > 1e-6

    def test_compute_derivatives(self) -> None:
        tp = BandParams(1.0, 0.1)
        gp = BandParams(0.5, 0.1)
        net = BandNetwork.theta_gamma(4, 8, tp, gp, 0.3)
        seed = Seed(42, 0)
        state = create_band_state_py(net, [(5.0, 7.0), (35.0, 45.0)], seed)
        dp, da, df = net.compute_derivatives(state)
        assert len(dp) == 12
        assert len(da) == 12
        assert len(df) == 12
        assert np.all(np.isfinite(dp))
        assert np.all(np.isfinite(da))

    def test_theoretical_capacity(self) -> None:
        tp = BandParams(1.0, 0.1)
        gp = BandParams(0.5, 0.1)
        net = BandNetwork.theta_gamma(4, 8, tp, gp, 0.3)
        seed = Seed(42, 0)
        state = create_band_state_py(net, [(5.0, 7.0), (35.0, 45.0)], seed)
        cap = net.theoretical_capacity(state)
        assert cap >= 3
        assert cap <= 15

    def test_repr(self) -> None:
        tp = BandParams(1.0, 0.1)
        gp = BandParams(0.5, 0.1)
        net = BandNetwork.theta_gamma(4, 8, tp, gp, 0.3)
        assert "BandNetwork" in repr(net)


# ---------------------------------------------------------------------------
# create_band_state_py
# ---------------------------------------------------------------------------


class TestCreateBandState:
    def test_creates_valid_state(self) -> None:
        tp = BandParams(1.0, 0.1)
        gp = BandParams(0.5, 0.1)
        net = BandNetwork.theta_gamma(3, 5, tp, gp, 0.3)
        seed = Seed(0, 0)
        state = create_band_state_py(net, [(5.0, 7.0), (35.0, 45.0)], seed)
        assert state.n_oscillators == 8
        bands = state.freq_band
        assert bands is not None
        assert list(bands[:3]) == [0, 0, 0]
        assert list(bands[3:]) == [1, 1, 1, 1, 1]

    def test_wrong_ranges_rejected(self) -> None:
        tp = BandParams(1.0, 0.1)
        gp = BandParams(0.5, 0.1)
        net = BandNetwork.theta_gamma(3, 5, tp, gp, 0.3)
        seed = Seed(0, 0)
        with pytest.raises(ValueError):
            create_band_state_py(net, [(5.0, 7.0)], seed)


# ---------------------------------------------------------------------------
# ComplexPhasorBlender
# ---------------------------------------------------------------------------


class TestComplexPhasorBlender:
    def test_alpha_one_returns_new(self) -> None:
        b = ComplexPhasorBlender(1.0)
        new_p = np.array([1.0, 2.0, 3.0])
        old_p = np.array([0.5, 1.5, 2.5])
        result = b.blend(new_p, old_p)
        for r, n in zip(result, new_p, strict=True):
            assert r == pytest.approx(n % TAU, abs=1e-10)

    def test_wrap_around(self) -> None:
        b = ComplexPhasorBlender(0.5)
        result = b.blend_scalar(0.1, TAU - 0.1)
        assert result < 0.5 or result > TAU - 0.5

    def test_same_phase_preserved(self) -> None:
        b = ComplexPhasorBlender(0.3)
        result = b.blend_scalar(1.5, 1.5)
        assert result == pytest.approx(1.5 % TAU, abs=1e-10)

    def test_invalid_alpha_rejected(self) -> None:
        with pytest.raises(ValueError):
            ComplexPhasorBlender(0.0)
        with pytest.raises(ValueError):
            ComplexPhasorBlender(1.1)

    def test_set_alpha(self) -> None:
        b = ComplexPhasorBlender(0.5)
        b.set_alpha(0.8)
        assert b.alpha == pytest.approx(0.8)

    def test_empty_input_rejected(self) -> None:
        b = ComplexPhasorBlender(0.5)
        with pytest.raises(ValueError):
            b.blend(np.array([]), np.array([1.0]))

    def test_length_mismatch_rejected(self) -> None:
        b = ComplexPhasorBlender(0.5)
        with pytest.raises(ValueError):
            b.blend(np.array([1.0, 2.0]), np.array([1.0]))


# ---------------------------------------------------------------------------
# EmaAmplitudeBlender
# ---------------------------------------------------------------------------


class TestEmaAmplitudeBlender:
    def test_alpha_one_returns_new(self) -> None:
        b = EmaAmplitudeBlender(1.0)
        result = b.blend(np.array([2.0, 3.0]), np.array([1.0, 1.0]))
        assert result[0] == pytest.approx(2.0)
        assert result[1] == pytest.approx(3.0)

    def test_half_half(self) -> None:
        b = EmaAmplitudeBlender(0.5)
        result = b.blend(np.array([4.0]), np.array([2.0]))
        assert result[0] == pytest.approx(3.0)

    def test_clamps_output(self) -> None:
        b = EmaAmplitudeBlender(0.5)
        result = b.blend(np.array([100.0]), np.array([100.0]))
        assert result[0] == pytest.approx(AMPLITUDE_MAX)

    def test_invalid_alpha_rejected(self) -> None:
        with pytest.raises(ValueError):
            EmaAmplitudeBlender(0.0)

    def test_properties(self) -> None:
        b = EmaAmplitudeBlender(0.5)
        assert b.amp_min == pytest.approx(AMPLITUDE_MIN)
        assert b.amp_max == pytest.approx(AMPLITUDE_MAX)


# ---------------------------------------------------------------------------
# TemporalPropagator
# ---------------------------------------------------------------------------


class TestTemporalPropagator:
    def test_first_call_initializes(self) -> None:
        prop = TemporalPropagator(0.5)
        assert not prop.is_initialized()
        p, a = prop.propagate(np.array([1.0, 2.0]), np.array([3.0, 4.0]))
        assert prop.is_initialized()
        assert len(p) == 2
        assert len(a) == 2

    def test_second_call_blends(self) -> None:
        prop = TemporalPropagator(0.5)
        prop.propagate(np.array([0.0]), np.array([2.0]))
        _p, a = prop.propagate(np.array([1.0]), np.array([4.0]))
        assert a[0] == pytest.approx(3.0)

    def test_propagate_init(self) -> None:
        prop = TemporalPropagator(0.5)
        prop.propagate_init(np.array([1.0]), np.array([2.0]))
        assert prop.is_initialized()

    def test_reset(self) -> None:
        prop = TemporalPropagator(0.5)
        prop.propagate(np.array([1.0]), np.array([2.0]))
        assert prop.is_initialized()
        prop.reset()
        assert not prop.is_initialized()

    def test_state_size_change_rejected(self) -> None:
        prop = TemporalPropagator(0.5)
        prop.propagate(np.array([1.0, 2.0]), np.array([3.0, 4.0]))
        with pytest.raises(ValueError):
            prop.propagate(np.array([1.0]), np.array([2.0]))

    def test_separate_alpha(self) -> None:
        prop = TemporalPropagator.with_separate_alpha(0.8, 0.2)
        assert prop.phase_alpha == pytest.approx(0.8)
        assert prop.amplitude_alpha == pytest.approx(0.2)

    def test_convergence(self) -> None:
        prop = TemporalPropagator(0.5)
        prop.propagate(np.array([0.0]), np.array([1.0]))
        for _ in range(50):
            prop.propagate(np.array([1.0]), np.array([5.0]))
        p = prop.propagate(np.array([1.0]), np.array([5.0]))
        assert p[1][0] == pytest.approx(5.0, abs=1e-4)

    def test_empty_input_rejected(self) -> None:
        prop = TemporalPropagator(0.5)
        with pytest.raises(ValueError):
            prop.propagate(np.array([]), np.array([]))

    def test_repr(self) -> None:
        prop = TemporalPropagator(0.5)
        assert "TemporalPropagator" in repr(prop)
