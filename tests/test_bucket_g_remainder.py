"""Acceptance tests for the 0141D2 Bucket G remainder surface.

Covers resolution, construction/callability, argument validation, and
documented D-2.2 dispositions for every symbol delivered in sub-pass 0141D2.
Behavioural parity against PRINet 3.0 is a WP-036B/WP-036C obligation.
"""

from __future__ import annotations

import numpy as np
import prin
import pytest
from prin.dynamics import (
    CouplingMode,
    KuramotoOscillator,
    OscillatorState,
)
from prin.nn.slot_attention import SlotAttentionCLEVRN
from prin.simulation import (
    LargeScaleOscillatorSystem,
    OscillatorPruner,
    OscilloSim,
    SimulationResult,
    quick_simulate,
)
from prin.temporal_training import (
    MultiSeedResult,
    SequenceData,
    TemporalTrainer,
    TrainingSnapshot,
    count_parameters,
    generate_dataset,
    generate_temporal_clevr_n,
    hungarian_similarity_loss,
    temporal_smoothness_loss,
    train_multi_seed,
)
from prin.topology import ring_topology, small_world_topology
from prin.training_hooks import (
    ControlSignalBuffer,
    create_ablation_tracker,
)
from prin.y4q1_tools import (
    AblationConfig,
    AblationHybridPRINetV2,
    ExtendedTrainingResult,
    count_flops,
    create_ablation_model,
    measure_wall_time,
    train_clevr_n_extended,
    train_clevr_n_single_seed,
)

# ── Symbol resolution ─────────────────────────────────────────────────────

_NEW_SYMBOLS = (
    # simulation
    "OscilloSim",
    "SimulationResult",
    "quick_simulate",
    "LargeScaleOscillatorSystem",
    "OscillatorPruner",
    # topology
    "ring_topology",
    "small_world_topology",
    # temporal_training
    "SequenceData",
    "TrainingSnapshot",
    "MultiSeedResult",
    "count_parameters",
    "generate_temporal_clevr_n",
    "generate_dataset",
    "hungarian_similarity_loss",
    "temporal_smoothness_loss",
    "TemporalTrainer",
    "train_multi_seed",
    # y4q1_tools
    "AblationConfig",
    "ExtendedTrainingResult",
    "count_flops",
    "measure_wall_time",
    "AblationHybridPRINetV2",
    "create_ablation_model",
    "train_clevr_n_single_seed",
    "train_clevr_n_extended",
    # hybrid-model family
    "HybridPRINet",
    "HybridCLEVRN",
    "HybridPRINetV2CLEVRN",
    "InterleavedHybridPRINet",
    "TemporalHybridPRINet",
    "AlternatingOptimizer",
    # active-control
    "ControlSignalBuffer",
    "ActiveControlTrainer",
    "StateCollector",
    "create_ablation_tracker",
    "collect_system_state",
    # slot-attention adapter
    "SlotAttentionCLEVRN",
)


def test_all_new_symbols_resolve_from_prin_and_are_listed() -> None:
    """Every 0141D2 symbol resolves from ``prin`` and is in ``__all__``."""
    for name in _NEW_SYMBOLS:
        assert name in prin.__all__, name
        assert getattr(prin, name) is not None


# ── Simulation family ─────────────────────────────────────────────────────


def _model(n: int = 32) -> KuramotoOscillator:
    return KuramotoOscillator(n, 2.0, 0.1, 0.0, CouplingMode.mean_field())


def _state(n: int = 32) -> OscillatorState:
    return OscillatorState(np.linspace(0.0, 1.0, n), np.ones(n), np.full(n, 5.0))


def test_simulation_result_is_constructible_dataclass() -> None:
    """``SimulationResult`` is a faithful dataclass container."""
    phase = np.zeros(8)
    amp = np.ones(8)
    result = SimulationResult(
        final_phase=phase,
        final_amplitude=amp,
        n_oscillators=8,
        n_steps=10,
        coupling_mode="mean_field",
    )
    assert result.n_oscillators == 8
    assert result.n_steps == 10
    assert result.device == "cpu"
    assert result.order_parameter == []
    assert result.trajectory_phase is None


def test_oscillosim_constructs_and_runs() -> None:
    """``OscilloSim`` constructs with valid args and produces a result."""
    sim = OscilloSim(32, coupling_strength=2.0, coupling_mode="mean_field")
    result = sim.run(n_steps=10, dt=0.01)
    assert isinstance(result, SimulationResult)
    assert result.n_oscillators == 32
    assert result.n_steps == 10
    assert result.wall_time_s >= 0.0
    assert result.final_phase.shape == (32,)


def test_oscillosim_validates_arguments() -> None:
    """``OscilloSim`` rejects invalid constructor and run arguments."""
    with pytest.raises(ValueError, match="n_oscillators"):
        OscilloSim(0)
    with pytest.raises(ValueError, match="Unknown coupling_mode"):
        OscilloSim(8, coupling_mode="bogus")
    sim = OscilloSim(8)
    with pytest.raises(ValueError, match="n_steps must be non-negative"):
        sim.run(n_steps=-1)
    with pytest.raises(ValueError, match="dt must be positive"):
        sim.run(dt=0.0)


def test_oscillosim_trajectory_recording() -> None:
    """Trajectory recording populates ``trajectory_phase`` and order params."""
    sim = OscilloSim(16, coupling_mode="mean_field")
    result = sim.run(n_steps=5, dt=0.01, record_trajectory=True)
    assert result.trajectory_phase is not None
    assert result.trajectory_phase.shape[0] == 5
    assert len(result.order_parameter) == 5


def test_quick_simulate_delegates_to_oscillosim() -> None:
    """``quick_simulate`` is a convenience wrapper that returns a result."""
    result = quick_simulate(16, n_steps=5, coupling_mode="mean_field")
    assert isinstance(result, SimulationResult)
    assert result.n_oscillators == 16


def test_large_scale_oscillator_system_is_real() -> None:
    """``LargeScaleOscillatorSystem`` is now a real implementation (0144M4)."""
    sys = LargeScaleOscillatorSystem(n_oscillators=100, k_neighbors=6, seed=42)
    assert sys.n_oscillators == 100


def test_oscillator_pruner_is_real() -> None:
    """``OscillatorPruner`` is now a real implementation (0144M4)."""
    pruner = OscillatorPruner(threshold=0.1)
    assert pruner.threshold == 0.1


# ── Topology builders ─────────────────────────────────────────────────────


def test_ring_topology_returns_correct_neighbour_count() -> None:
    """``ring_topology`` returns a flat list of N*k indices."""
    nbrs = ring_topology(8, k_neighbors=2)
    assert len(nbrs) == 16
    # Each oscillator has exactly 2 neighbours.
    for i in range(8):
        row = nbrs[i * 2 : (i + 1) * 2]
        assert len(row) == 2
        assert all(0 <= j < 8 for j in row)


def test_ring_topology_validates_arguments() -> None:
    """``ring_topology`` rejects invalid N and k."""
    with pytest.raises(ValueError, match="n_oscillators"):
        ring_topology(1)
    with pytest.raises(ValueError, match="k_neighbors must be a positive even"):
        ring_topology(8, k_neighbors=3)
    with pytest.raises(ValueError, match=r"k_neighbors.*must be < n_oscillators"):
        ring_topology(4, k_neighbors=4)


def test_ring_topology_deterministic() -> None:
    """``ring_topology`` is deterministic (no RNG)."""
    a = ring_topology(10, k_neighbors=4)
    b = ring_topology(10, k_neighbors=4)
    assert a == b


def test_small_world_topology_no_rewire_matches_ring() -> None:
    """With ``p_rewire=0``, small-world equals ring."""
    ring = ring_topology(8, k_neighbors=2)
    sw = small_world_topology(8, k_neighbors=2, p_rewire=0.0, seed=42)
    assert sorted(sw) == sorted(ring)


def test_small_world_topology_validates_arguments() -> None:
    """``small_world_topology`` rejects invalid arguments."""
    with pytest.raises(ValueError, match="p_rewire"):
        small_world_topology(8, p_rewire=1.5)
    with pytest.raises(ValueError, match="n_oscillators"):
        small_world_topology(1)


def test_small_world_topology_deterministic_with_seed() -> None:
    """Same seed produces the same rewiring."""
    a = small_world_topology(16, k_neighbors=4, p_rewire=0.3, seed=99)
    b = small_world_topology(16, k_neighbors=4, p_rewire=0.3, seed=99)
    assert a == b


# ── temporal_training grab-bag ────────────────────────────────────────────


def test_sequence_data_is_constructible_dataclass() -> None:
    """``SequenceData`` is a faithful dataclass container."""
    sd = SequenceData(n_objects=4, n_frames=20)
    assert sd.n_objects == 4
    assert sd.n_frames == 20
    assert sd.frames == []


def test_training_snapshot_is_constructible_dataclass() -> None:
    """``TrainingSnapshot`` is a faithful dataclass container."""
    snap = TrainingSnapshot(epoch=5, train_loss=0.3, val_ip=0.85)
    assert snap.epoch == 5
    assert snap.train_loss == 0.3
    assert snap.val_ip == 0.85


def test_multi_seed_result_is_constructible_dataclass() -> None:
    """``MultiSeedResult`` is a faithful dataclass container."""
    msr = MultiSeedResult(model_name="test", seeds=[42, 123])
    assert msr.model_name == "test"
    assert msr.seeds == [42, 123]


def test_count_parameters_counts_linear_model() -> None:
    """``count_parameters`` correctly counts a torch.nn.Linear model."""
    import torch

    m = torch.nn.Linear(4, 2)
    counts = count_parameters(m)
    assert counts["total"] == 10  # 4*2 + 2 bias
    assert counts["trainable"] == 10
    assert counts["frozen"] == 0
    assert counts["complex_adjusted"] == 10


@pytest.mark.parametrize(
    "fn",
    [
        generate_temporal_clevr_n,
        generate_dataset,
        hungarian_similarity_loss,
        temporal_smoothness_loss,
        train_multi_seed,
    ],
)
def test_temporal_training_d22_stubs_raise(fn: object) -> None:
    """Every numeric temporal_training symbol raises the D-2.2 disposition."""
    with pytest.raises(NotImplementedError, match=r"D-2\.2"):
        fn()  # type: ignore[operator]


def test_temporal_trainer_is_d22_stub() -> None:
    """``TemporalTrainer`` raises the D-2.2 disposition on construction."""
    with pytest.raises(NotImplementedError, match=r"D-2\.2"):
        TemporalTrainer(model=None)


# ── y4q1_tools grab-bag ──────────────────────────────────────────────────


def test_ablation_config_is_constructible_dataclass() -> None:
    """``AblationConfig`` is a faithful dataclass container."""
    cfg = AblationConfig(variant="attention_only", n_input=128)
    assert cfg.variant == "attention_only"
    assert cfg.n_input == 128
    assert cfg.n_classes == 10  # default


def test_extended_training_result_is_constructible_dataclass() -> None:
    """``ExtendedTrainingResult`` is a faithful dataclass container."""
    etr = ExtendedTrainingResult(model_name="test", n_seeds=5)
    assert etr.model_name == "test"
    assert etr.n_seeds == 5


def test_count_flops_estimates_linear_layer() -> None:
    """``count_flops`` returns positive FLOPs for a Linear model."""
    import torch

    m = torch.nn.Linear(4, 2)
    result = count_flops(m, (1, 4))
    assert result["total_flops"] > 0
    assert result["total_params"] == 10
    assert len(result["layer_flops"]) >= 1


def test_measure_wall_time_returns_timing_dict() -> None:
    """``measure_wall_time`` returns mean/std/min/max/n_runs."""
    import torch

    m = torch.nn.Linear(4, 2)
    x = torch.randn(1, 4)
    result = measure_wall_time(m, x, n_warmup=1, n_runs=3)
    assert result["n_runs"] == 3
    assert result["mean_ms"] >= 0.0
    assert result["min_ms"] <= result["max_ms"]


def test_measure_wall_time_validates_arguments() -> None:
    """``measure_wall_time`` rejects invalid n_warmup / n_runs."""
    import torch

    m = torch.nn.Linear(4, 2)
    x = torch.randn(1, 4)
    with pytest.raises(ValueError, match="n_warmup"):
        measure_wall_time(m, x, n_warmup=-1)
    with pytest.raises(ValueError, match="n_runs"):
        measure_wall_time(m, x, n_runs=0)


@pytest.mark.parametrize(
    "cls_or_fn",
    [
        AblationHybridPRINetV2,
        create_ablation_model,
        train_clevr_n_single_seed,
        train_clevr_n_extended,
    ],
)
def test_y4q1_tools_d22_stubs_raise(cls_or_fn: object) -> None:
    """Every numeric y4q1_tools symbol raises the D-2.2 disposition."""
    with pytest.raises(NotImplementedError, match=r"D-2\.2"):
        cls_or_fn()  # type: ignore[operator]


# ── Hybrid-model family ───────────────────────────────────────────────────


@pytest.mark.parametrize(
    "cls",
    [],
)
def test_hybrid_family_d22_stubs_raise(cls: type) -> None:
    """Every still-deferred hybrid-model symbol raises the D-2.2 disposition.

    ``InterleavedHybridPRINet`` was rebuilt at 0144M1; ``HybridPRINetV2CLEVRN``
    and ``TemporalHybridPRINet`` were rebuilt at 0144M2. All are now real
    PyTorch compositions and no longer D-2.2 stubs.
    """
    with pytest.raises(NotImplementedError, match=r"D-2\.2"):
        cls()


# ── Active-control family ─────────────────────────────────────────────────


def test_control_signal_buffer_is_real_and_thread_safe() -> None:
    """``ControlSignalBuffer`` stores and returns control signals."""
    from prin.daemon import ControlSignals

    buf = ControlSignalBuffer()
    default = buf.latest()
    assert isinstance(default, ControlSignals)
    assert default.alert_level == 0.0

    new_signals = ControlSignals(alert_level=0.8)
    buf.update(new_signals)
    assert buf.latest().alert_level == 0.8


def test_control_signal_buffer_concurrent_access() -> None:
    """``ControlSignalBuffer`` handles concurrent reads/writes safely."""
    import threading

    from prin.daemon import ControlSignals

    buf = ControlSignalBuffer()
    errors: list[Exception] = []

    def writer() -> None:
        try:
            for i in range(100):
                buf.update(ControlSignals(alert_level=i / 100.0))
        except Exception as e:
            errors.append(e)

    def reader() -> None:
        try:
            for _ in range(100):
                _ = buf.latest()
        except Exception as e:
            errors.append(e)

    threads = [threading.Thread(target=writer) for _ in range(2)]
    threads += [threading.Thread(target=reader) for _ in range(2)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()
    assert errors == []


@pytest.mark.parametrize(
    "cls_or_fn",
    [
        create_ablation_tracker,
    ],
)
def test_active_control_d22_stubs_raise(cls_or_fn: object) -> None:
    """Every still-deferred numeric active-control symbol raises the disposition.

    ``collect_system_state`` was rebuilt at 0144E6; ``ActiveControlTrainer``
    was rebuilt at 0144M2. Both are now real and no longer D-2.2 stubs.
    """
    with pytest.raises(NotImplementedError, match=r"D-2\.2"):
        cls_or_fn()  # type: ignore[operator]


# ── SlotAttentionCLEVRN ──────────────────────────────────────────────────


def test_slot_attention_clevrn_is_real() -> None:
    """``SlotAttentionCLEVRN`` is now a real implementation (0144M4)."""
    import torch

    model = SlotAttentionCLEVRN(scene_dim=16, query_dim=60, d_model=32)
    scene = torch.randn(2, 16)
    query = torch.randn(2, 60)
    out = model(scene, query)
    assert out.shape == (2, 2)


# ── Coverage: OscilloSim branch paths (WP036-F1) ────────────────────────


def test_oscillosim_stuart_landau_path() -> None:
    """``OscilloSim`` with nonzero ``mu`` builds a StuartLandauOscillator."""
    sim = OscilloSim(
        16,
        coupling_strength=1.0,
        mu=0.5,
        coupling_mode="mean_field",
    )
    result = sim.run(n_steps=5, dt=0.01)
    assert isinstance(result, SimulationResult)
    assert result.n_oscillators == 16


def test_oscillosim_topology_alias_modes() -> None:
    """Topology alias modes (``ring``, ``csr``, ``auto``) resolve correctly."""
    for mode in ("ring", "csr", "auto"):
        sim = OscilloSim(16, coupling_strength=1.0, coupling_mode=mode)
        result = sim.run(n_steps=3, dt=0.01)
        assert isinstance(result, SimulationResult)


def test_oscillosim_rk45_integrator() -> None:
    """``OscilloSim`` with ``integrator='rk45'`` uses the adaptive solver."""
    sim = OscilloSim(
        8,
        coupling_strength=1.0,
        coupling_mode="mean_field",
        integrator="rk45",
    )
    result = sim.run(n_steps=5, dt=0.01)
    assert isinstance(result, SimulationResult)
    assert result.n_steps >= 1


def test_count_flops_conv2d() -> None:
    """``count_flops`` handles ``Conv2d`` layers."""
    import torch

    m = torch.nn.Conv2d(3, 8, kernel_size=3)
    result = count_flops(m, (1, 3, 16, 16))
    assert result["total_flops"] > 0
    assert any(d["type"] == "Conv2d" for d in result["layer_flops"])


def test_count_flops_grucell() -> None:
    """``count_flops`` handles ``GRUCell`` layers."""
    import torch

    m = torch.nn.GRUCell(4, 8)
    result = count_flops(m, (1, 4))
    assert result["total_flops"] > 0
    assert any(d["type"] == "GRUCell" for d in result["layer_flops"])
