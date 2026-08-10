"""Tests for the Phase 1 Python API: dynamics bindings and metrics."""

from __future__ import annotations

import math

import numpy as np
import pytest
from prin._prin_core import (
    AMPLITUDE_MAX,
    AMPLITUDE_MIN,
    DERIV_CLAMP,
    SPARSE_EPS,
    TAU,
    AdaptiveResult,
    CouplingMode,
    EulerIntegrator,
    ExponentialIntegrator,
    HopfOscillator,
    KuramotoOscillator,
    MultiRateIntegrator,
    OscillatorState,
    PhaseAmplitudeCoupling,
    RK4Integrator,
    RK45Integrator,
    Seed,
    StateDerivatives,
    StuartLandauOscillator,
    Topology,
    bimodality_chimera_threshold,
    bimodality_index,
    build_phase_knn,
    chimera_index,
    default_chimera_threshold,
    discontinuity_measure,
    extract_concept_probabilities,
    inter_frame_phase_correlation,
    kuramoto_order_parameter,
    kuramoto_order_parameter_complex,
    local_order_parameter,
    mean_phase_coherence,
    metastability,
    order_parameter_series,
    phase_coherence_matrix,
    power_spectral_density,
    sparse_mean_phase_coherence,
    sparse_synchronization_energy,
    strength_of_incoherence,
    strength_of_incoherence_temporal,
    synchronization_energy,
)

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------


class TestConstants:
    def test_tau(self) -> None:
        assert TAU == pytest.approx(2.0 * math.pi)

    def test_amplitude_bounds(self) -> None:
        assert AMPLITUDE_MIN == 1e-6
        assert AMPLITUDE_MAX == 10.0

    def test_deriv_clamp(self) -> None:
        assert DERIV_CLAMP == 1e4

    def test_sparse_eps(self) -> None:
        assert SPARSE_EPS == 1e-8


# ---------------------------------------------------------------------------
# Seed
# ---------------------------------------------------------------------------


class TestSeed:
    def test_create(self) -> None:
        s = Seed(0, 42)
        assert s.counter == 0
        assert s.key == 42

    def test_deterministic(self) -> None:
        s1 = Seed(0, 42)
        s2 = Seed(0, 42)
        assert s1.next_f64() == s2.next_f64()
        assert s1.next_f64() == s2.next_f64()

    def test_jump(self) -> None:
        s1 = Seed(0, 42)
        s2 = Seed(0, 42)
        s1.jump(10)
        for _ in range(10):
            s2.next_f64()
        assert s1.next_f64() == s2.next_f64()

    def test_next_f64_range(self) -> None:
        s = Seed(0, 1)
        for _ in range(100):
            v = s.next_f64_range(2.0, 5.0)
            assert 2.0 <= v < 5.0

    def test_next_u64(self) -> None:
        s = Seed(0, 1)
        v = s.next_u64()
        assert isinstance(v, int)

    def test_repr(self) -> None:
        s = Seed(10, 20)
        assert "counter=10" in repr(s)
        assert "key=20" in repr(s)


# ---------------------------------------------------------------------------
# OscillatorState
# ---------------------------------------------------------------------------


class TestOscillatorState:
    def test_create(self) -> None:
        phase = np.array([0.0, 1.0, 2.0])
        amp = np.array([1.0, 1.0, 1.0])
        freq = np.array([1.0, 2.0, 3.0])
        state = OscillatorState(phase, amp, freq)
        assert state.n_oscillators == 3
        assert len(state) == 3
        np.testing.assert_allclose(state.frequency, freq)

    def test_phase_wrapping(self) -> None:
        phase = np.array([7.0])  # > 2π
        amp = np.array([1.0])
        freq = np.array([1.0])
        state = OscillatorState(phase, amp, freq)
        assert 0.0 <= state.phase[0] < TAU

    def test_create_random(self) -> None:
        seed = Seed(0, 42)
        state = OscillatorState.create_random(10, (1.0, 5.0), seed)
        assert state.n_oscillators == 10
        assert state.n_bands == 0

    def test_create_synchronized(self) -> None:
        state = OscillatorState.create_synchronized(5, 2.0)
        assert state.n_oscillators == 5
        np.testing.assert_allclose(state.phase, 0.0)
        np.testing.assert_allclose(state.amplitude, 1.0)
        np.testing.assert_allclose(state.frequency, 2.0)

    def test_empty_raises(self) -> None:
        with pytest.raises(ValueError):
            OscillatorState(np.array([]), np.array([]), np.array([]))

    def test_phase_knn_index(self) -> None:
        state = OscillatorState.create_synchronized(6, 1.0)
        idx = state.phase_knn_index(2)
        assert len(idx) == 6

    def test_repr(self) -> None:
        state = OscillatorState.create_synchronized(4, 1.0)
        assert "n_oscillators=4" in repr(state)

    def test_freq_band(self) -> None:
        phase = np.array([0.0, 1.0])
        amp = np.array([1.0, 1.0])
        freq = np.array([1.0, 2.0])
        band = np.array([0, 1], dtype=np.uint32)
        state = OscillatorState(phase, amp, freq, freq_band=band)
        assert state.n_bands == 2
        np.testing.assert_array_equal(state.freq_band, band)


# ---------------------------------------------------------------------------
# StateDerivatives
# ---------------------------------------------------------------------------


class TestStateDerivatives:
    def test_from_kuramoto(self) -> None:
        state = OscillatorState.create_synchronized(4, 1.0)
        model = KuramotoOscillator(4, 1.0, 0.1, 0.0, CouplingMode.mean_field())
        deriv = model.compute_derivatives(state)
        assert isinstance(deriv, StateDerivatives)
        assert len(deriv.dphase) == 4
        assert len(deriv.damplitude) == 4
        assert len(deriv.dfrequency) == 4


# ---------------------------------------------------------------------------
# CouplingMode
# ---------------------------------------------------------------------------


class TestCouplingMode:
    def test_mean_field(self) -> None:
        cm = CouplingMode.mean_field()
        assert cm.variant() == "mean_field"

    def test_full(self) -> None:
        cm = CouplingMode.full()
        assert cm.variant() == "full"

    def test_full_with_matrix(self) -> None:
        mat = np.array([0.0, 0.5, 0.5, 0.0])
        cm = CouplingMode.full(matrix=mat)
        assert cm.variant() == "full"

    def test_sparse_knn(self) -> None:
        cm = CouplingMode.sparse_knn(k=3)
        assert cm.variant() == "sparse_knn"

    def test_repr(self) -> None:
        assert "mean_field" in repr(CouplingMode.mean_field())


# ---------------------------------------------------------------------------
# Topology
# ---------------------------------------------------------------------------


class TestTopology:
    def test_all_to_all(self) -> None:
        topo = Topology.all_to_all()
        mat = topo.build_matrix(4, 1.0)
        assert len(mat) == 16
        # Diagonal should be zero
        for i in range(4):
            assert mat[i * 4 + i] == 0.0

    def test_ring(self) -> None:
        topo = Topology.ring(2)
        mat = topo.build_matrix(4, 1.0)
        assert len(mat) == 16

    def test_small_world(self) -> None:
        seed = Seed(0, 42)
        topo = Topology.small_world(2, 0.3, seed)
        mat = topo.build_matrix(6, 1.0)
        assert len(mat) == 36


# ---------------------------------------------------------------------------
# Models
# ---------------------------------------------------------------------------


class TestModels:
    def test_kuramoto_mean_field(self) -> None:
        model = KuramotoOscillator(4, 1.0, 0.1, 0.0, CouplingMode.mean_field())
        assert model.n_oscillators == 4
        state = OscillatorState.create_synchronized(4, 1.0)
        deriv = model.compute_derivatives(state)
        assert len(deriv.dphase) == 4

    def test_kuramoto_full(self) -> None:
        model = KuramotoOscillator(4, 1.0, 0.1, 0.0, CouplingMode.full())
        state = OscillatorState.create_synchronized(4, 1.0)
        deriv = model.compute_derivatives(state)
        assert len(deriv.dphase) == 4

    def test_kuramoto_sparse(self) -> None:
        model = KuramotoOscillator(8, 1.0, 0.1, 0.0, CouplingMode.sparse_knn(k=3))
        state = OscillatorState.create_synchronized(8, 1.0)
        deriv = model.compute_derivatives(state)
        assert len(deriv.dphase) == 8

    def test_stuart_landau(self) -> None:
        model = StuartLandauOscillator(4, 1.0, 0.5, CouplingMode.mean_field())
        assert model.n_oscillators == 4
        assert model.bifurcation_param == 0.5
        state = OscillatorState.create_synchronized(4, 1.0)
        deriv = model.compute_derivatives(state)
        assert len(deriv.dphase) == 4

    def test_hopf(self) -> None:
        model = HopfOscillator(4, 1.0, 0.5, 0.01, CouplingMode.mean_field())
        assert model.n_oscillators == 4
        state = OscillatorState.create_synchronized(4, 1.0)
        deriv = model.compute_derivatives(state)
        assert len(deriv.dphase) == 4

    def test_model_repr(self) -> None:
        model = KuramotoOscillator(4, 1.0, 0.1, 0.0, CouplingMode.mean_field())
        assert "KuramotoOscillator" in repr(model)


# ---------------------------------------------------------------------------
# Integrators
# ---------------------------------------------------------------------------


class TestIntegrators:
    def _make_problem(self):
        model = KuramotoOscillator(4, 1.0, 0.1, 0.0, CouplingMode.mean_field())
        state = OscillatorState.create_synchronized(4, 1.0)
        return model, state

    def test_euler_step(self) -> None:
        model, state = self._make_problem()
        integ = EulerIntegrator()
        new_state = integ.step(model, state, 0.01)
        assert new_state.n_oscillators == 4

    def test_rk4_step(self) -> None:
        model, state = self._make_problem()
        integ = RK4Integrator()
        new_state = integ.step(model, state, 0.01)
        assert new_state.n_oscillators == 4

    def test_rk45_step(self) -> None:
        model, state = self._make_problem()
        integ = RK45Integrator()
        new_state = integ.step(model, state, 0.01)
        assert new_state.n_oscillators == 4

    def test_euler_integrate_fixed(self) -> None:
        model, state = self._make_problem()
        integ = EulerIntegrator()
        final, traj = integ.integrate_fixed(model, state, 10, 0.01)
        assert final.n_oscillators == 4
        assert traj is None

    def test_euler_integrate_fixed_with_trajectory(self) -> None:
        model, state = self._make_problem()
        integ = EulerIntegrator()
        _, traj = integ.integrate_fixed(model, state, 10, 0.01, record_trajectory=True)
        assert len(traj) == 10

    def test_rk45_adaptive(self) -> None:
        model, state = self._make_problem()
        integ = RK45Integrator()
        result = integ.integrate_adaptive(model, state, 1.0, 0.01)
        assert isinstance(result, AdaptiveResult)
        assert result.accepted_steps > 0
        assert result.final_state.n_oscillators == 4

    def test_rk45_with_stuart_landau(self) -> None:
        model = StuartLandauOscillator(4, 1.0, 0.5, CouplingMode.mean_field())
        state = OscillatorState.create_synchronized(4, 1.0)
        integ = RK4Integrator()
        final, _ = integ.integrate_fixed(model, state, 5, 0.01)
        assert final.n_oscillators == 4

    def test_rk45_with_hopf(self) -> None:
        model = HopfOscillator(4, 1.0, 0.5, 0.01, CouplingMode.mean_field())
        state = OscillatorState.create_synchronized(4, 1.0)
        integ = RK4Integrator()
        final, _ = integ.integrate_fixed(model, state, 5, 0.01)
        assert final.n_oscillators == 4

    def test_invalid_dt_raises(self) -> None:
        model, state = self._make_problem()
        integ = EulerIntegrator()
        with pytest.raises(ValueError):
            integ.step(model, state, -0.01)

    def test_repr(self) -> None:
        assert "EulerIntegrator" in repr(EulerIntegrator())
        assert "RK4Integrator" in repr(RK4Integrator())
        assert "RK45Integrator" in repr(RK45Integrator())


# ---------------------------------------------------------------------------
# WP-012: ExponentialIntegrator bindings
# ---------------------------------------------------------------------------


class TestExponentialIntegrator:
    def _make_problem(self, n: int = 4):
        model = KuramotoOscillator(n, 1.0, 0.1, 0.01, CouplingMode.mean_field())
        state = OscillatorState(
            np.array([0.1, 0.5, 1.0, 1.5][:n]),
            np.ones(n),
            np.array([1.0, 2.0, 1.5, 0.5][:n]),
        )
        return model, state

    def test_init_valid(self) -> None:
        ei = ExponentialIntegrator(dim=12, krylov_rank=8)
        assert ei.dim == 12
        assert ei.krylov_rank == 8
        assert not ei.use_krylov
        assert not ei.stiff_mode

    def test_init_stiff_mode(self) -> None:
        ei = ExponentialIntegrator(dim=12, krylov_rank=4, stiff_mode=True)
        assert ei.stiff_mode

    def test_init_invalid_dim(self) -> None:
        with pytest.raises(ValueError):
            ExponentialIntegrator(dim=0)

    def test_init_invalid_krylov_rank(self) -> None:
        with pytest.raises(ValueError):
            ExponentialIntegrator(dim=12, krylov_rank=1)

    def test_step(self) -> None:
        model, state = self._make_problem()
        ei = ExponentialIntegrator(dim=12, krylov_rank=8)
        result = ei.step(model, state, 0.01)
        assert result.n_oscillators == 4
        assert all(np.isfinite(result.phase))

    def test_integrate(self) -> None:
        model, state = self._make_problem()
        ei = ExponentialIntegrator(dim=12, krylov_rank=8)
        final, traj = ei.integrate(model, state, 5, 0.01)
        assert final.n_oscillators == 4
        assert traj is None

    def test_integrate_with_trajectory(self) -> None:
        model, state = self._make_problem()
        ei = ExponentialIntegrator(dim=12, krylov_rank=8)
        _, traj = ei.integrate(model, state, 5, 0.01, record_trajectory=True)
        assert len(traj) == 5

    def test_dim_mismatch_raises(self) -> None:
        model, state = self._make_problem(n=2)
        ei = ExponentialIntegrator(dim=9, krylov_rank=4)  # dim=9 but state has 2 osc (3*2=6)
        with pytest.raises(ValueError):
            ei.step(model, state, 0.01)

    def test_invalid_dt_raises(self) -> None:
        model, state = self._make_problem()
        ei = ExponentialIntegrator(dim=12, krylov_rank=8)
        with pytest.raises(ValueError):
            ei.step(model, state, -0.01)

    def test_repr(self) -> None:
        ei = ExponentialIntegrator(dim=12, krylov_rank=8)
        assert "ExponentialIntegrator" in repr(ei)


# ---------------------------------------------------------------------------
# WP-012: MultiRateIntegrator bindings
# ---------------------------------------------------------------------------


class TestMultiRateIntegrator:
    def _make_problem(self):
        model = KuramotoOscillator(4, 1.0, 0.1, 0.0, CouplingMode.mean_field())
        state = OscillatorState.create_synchronized(4, 1.0)
        return model, state

    def test_init_defaults(self) -> None:
        mi = MultiRateIntegrator()
        assert mi.sub_steps == 10
        assert mi.method == "rk4"

    def test_init_custom(self) -> None:
        mi = MultiRateIntegrator(sub_steps=5, method="euler")
        assert mi.sub_steps == 5
        assert mi.method == "euler"

    def test_init_invalid_method(self) -> None:
        with pytest.raises(ValueError):
            MultiRateIntegrator(method="invalid")

    def test_init_zero_substeps(self) -> None:
        with pytest.raises(ValueError):
            MultiRateIntegrator(sub_steps=0)

    def test_step(self) -> None:
        model, state = self._make_problem()
        mi = MultiRateIntegrator(sub_steps=4)
        result = mi.step(model, state, 0.01)
        assert result.n_oscillators == 4

    def test_integrate(self) -> None:
        model, state = self._make_problem()
        mi = MultiRateIntegrator(sub_steps=4)
        final, traj = mi.integrate(model, state, 5, 0.01)
        assert final.n_oscillators == 4
        assert traj is None

    def test_integrate_with_trajectory(self) -> None:
        model, state = self._make_problem()
        mi = MultiRateIntegrator(sub_steps=4)
        _, traj = mi.integrate(model, state, 5, 0.01, record_trajectory=True)
        assert len(traj) == 5

    def test_substeps_1_matches_rk4(self) -> None:
        model, state = self._make_problem()
        mi = MultiRateIntegrator(sub_steps=1)
        rk4 = RK4Integrator()
        s_mi = mi.step(model, state, 0.01)
        s_rk4 = rk4.step(model, state, 0.01)
        np.testing.assert_allclose(s_mi.phase, s_rk4.phase, atol=1e-14)
        np.testing.assert_allclose(s_mi.amplitude, s_rk4.amplitude, atol=1e-14)

    def test_euler_method(self) -> None:
        model, state = self._make_problem()
        mi = MultiRateIntegrator(sub_steps=5, method="euler")
        result = mi.step(model, state, 0.01)
        assert result.n_oscillators == 4

    def test_invalid_dt_raises(self) -> None:
        model, state = self._make_problem()
        mi = MultiRateIntegrator(sub_steps=4)
        with pytest.raises(ValueError):
            mi.step(model, state, 0.0)

    def test_repr(self) -> None:
        mi = MultiRateIntegrator(sub_steps=5)
        assert "MultiRateIntegrator" in repr(mi)


# ---------------------------------------------------------------------------
# PAC
# ---------------------------------------------------------------------------


class TestPAC:
    def test_modulate(self) -> None:
        pac = PhaseAmplitudeCoupling(0.5)
        assert pac.modulation_depth == 0.5
        slow = np.array([0.0, 1.0, 2.0, 3.0])
        fast = np.array([1.0, 2.0, 3.0, 4.0])
        result = pac.modulate(slow, fast, 0.0)
        assert len(result) == 4

    def test_invalid_depth_raises(self) -> None:
        with pytest.raises(ValueError):
            PhaseAmplitudeCoupling(1.5)


# ---------------------------------------------------------------------------
# Metrics: Order parameters
# ---------------------------------------------------------------------------


class TestOrderMetrics:
    def test_kuramoto_synchronized(self) -> None:
        phase = np.zeros(100)
        r = kuramoto_order_parameter(phase)
        assert r == pytest.approx(1.0, abs=1e-12)

    def test_kuramoto_incoherent(self) -> None:
        phase = np.linspace(0, 2 * np.pi, 1000, endpoint=False)
        r = kuramoto_order_parameter(phase)
        assert r < 0.1

    def test_kuramoto_complex(self) -> None:
        phase = np.zeros(2)
        re, im = kuramoto_order_parameter_complex(phase)
        assert re == pytest.approx(1.0, abs=1e-12)
        assert im == pytest.approx(0.0, abs=1e-12)

    def test_inter_frame_correlation(self) -> None:
        prev = np.array([0.1, 1.4, 2.9])
        curr = np.array([0.12, 1.42, 2.92])
        rho = inter_frame_phase_correlation(curr, prev)
        assert rho == pytest.approx(1.0, abs=1e-12)

    def test_order_parameter_series(self) -> None:
        traj = np.array([0.0, 0.0, 0.0, np.pi])
        series = order_parameter_series(traj, 2)
        assert series[0] == pytest.approx(1.0, abs=1e-12)
        assert series[1] < 1e-12

    def test_empty_raises(self) -> None:
        with pytest.raises(ValueError):
            kuramoto_order_parameter(np.array([]))


# ---------------------------------------------------------------------------
# Metrics: Coherence
# ---------------------------------------------------------------------------


class TestCoherenceMetrics:
    def test_mean_phase_coherence(self) -> None:
        phase = np.array([0.0, 0.1, -0.1, 0.05])
        c = mean_phase_coherence(phase)
        assert c > 0.9

    def test_phase_coherence_matrix(self) -> None:
        phase = np.array([0.0, 0.0, 0.0])
        mat = phase_coherence_matrix(phase)
        assert len(mat) == 9
        # All phases equal → all coherences = 1
        np.testing.assert_allclose(mat, 1.0, atol=1e-12)

    def test_sparse_coherence(self) -> None:
        phase = np.zeros(4)
        neighbors = [[1], [0], [3], [2]]
        c = sparse_mean_phase_coherence(phase, neighbors)
        assert c == pytest.approx(1.0, abs=1e-12)


# ---------------------------------------------------------------------------
# Metrics: Spectral
# ---------------------------------------------------------------------------


class TestSpectralMetrics:
    def test_psd_dc_signal(self) -> None:
        amp = np.ones(4)
        phase = np.zeros(4)
        power = power_spectral_density(amp, phase)
        assert len(power) == 8
        assert power[0] == pytest.approx(16.0, abs=1e-9)

    def test_concept_probabilities(self) -> None:
        amp = np.ones(4)
        phase = np.zeros(4)
        freqs = np.array([0.0])
        bws = np.array([1.0])
        probs = extract_concept_probabilities(amp, phase, freqs, bws)
        assert len(probs) == 1
        assert probs[0] == pytest.approx(1.0, abs=1e-6)


# ---------------------------------------------------------------------------
# Metrics: Energy
# ---------------------------------------------------------------------------


class TestEnergyMetrics:
    def test_sync_energy_synchronized(self) -> None:
        phase = np.zeros(4)
        amp = np.ones(4)
        e = synchronization_energy(phase, amp)
        assert e == pytest.approx(-3.0, abs=1e-12)

    def test_sparse_sync_energy(self) -> None:
        phase = np.zeros(4)
        amp = np.ones(4)
        neighbors = [[1, 2], [0, 3], [0, 3], [1, 2]]
        e = sparse_synchronization_energy(phase, amp, neighbors, 1.0)
        assert e == pytest.approx(-4.0, abs=1e-12)


# ---------------------------------------------------------------------------
# Metrics: Chimera
# ---------------------------------------------------------------------------


class TestChimeraMetrics:
    def test_local_order_sync(self) -> None:
        phase = np.zeros(6)
        neighbors = [[(i + 1) % 6, (i + 5) % 6] for i in range(6)]
        r = local_order_parameter(phase, neighbors)
        np.testing.assert_allclose(r, 1.0, atol=1e-12)

    def test_bimodality_index(self) -> None:
        values = np.ones(100)
        b = bimodality_index(values)
        assert isinstance(b, float)

    def test_strength_of_incoherence(self) -> None:
        phase = np.zeros(10)
        si = strength_of_incoherence(phase, 4)
        assert isinstance(si, float)

    def test_discontinuity_measure(self) -> None:
        phase = np.full(10, 0.5)
        mask, eta = discontinuity_measure(phase, 0.01)
        assert len(mask) == 10
        assert all(mask)
        assert eta == 0

    def test_chimera_index_sync(self) -> None:
        phase = np.zeros(6)
        neighbors = [[(i + 1) % 6, (i + 5) % 6] for i in range(6)]
        chi = chimera_index(phase, neighbors, 0.5)
        assert chi == 0.0

    def test_temporal_si(self) -> None:
        traj = [np.zeros(8).tolist(), np.zeros(8).tolist()]
        si = strength_of_incoherence_temporal(traj, 4, 0)
        assert si == pytest.approx(0.0, abs=1e-9)

    def test_thresholds(self) -> None:
        assert bimodality_chimera_threshold() == pytest.approx(5.0 / 9.0)
        assert isinstance(default_chimera_threshold(), float)


# ---------------------------------------------------------------------------
# Metrics: Metastability
# ---------------------------------------------------------------------------


class TestMetastability:
    def test_constant_order(self) -> None:
        traj = np.array([0.0, 0.0, 0.0, 0.0])
        m = metastability(traj, 2)
        assert m == 0.0


# ---------------------------------------------------------------------------
# Metrics: k-NN
# ---------------------------------------------------------------------------


class TestKNN:
    def test_build_phase_knn(self) -> None:
        phase = np.array([0.0, 1.0, 2.0, 3.0, 4.0, 5.0])
        idx = build_phase_knn(phase, 2)
        assert len(idx) == 6
        for nbrs in idx:
            assert len(nbrs) == 2


# ---------------------------------------------------------------------------
# Module re-exports
# ---------------------------------------------------------------------------


class TestModuleReexports:
    def test_dynamics_module(self) -> None:
        from prin.dynamics import (
            KuramotoOscillator as K,
        )
        from prin.dynamics import (
            OscillatorState as OS,
        )
        from prin.dynamics import (
            Seed as S,
        )

        assert K is KuramotoOscillator
        assert OS is OscillatorState
        assert S is Seed

    def test_metrics_module(self) -> None:
        from prin.metrics import (
            kuramoto_order_parameter as kop,
        )
        from prin.metrics import (
            mean_phase_coherence as mpc,
        )

        assert kop is kuramoto_order_parameter
        assert mpc is mean_phase_coherence
