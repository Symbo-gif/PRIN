"""Acceptance tests for Rust-owned 0141C sweep compatibility bindings."""

from __future__ import annotations

import prin
import pytest
import torch
from prin import _prin_core

SWEEP_NAMES = ("sweep_coupling_params", "detect_oscillation", "phase_to_rate")


def test_sweep_symbols_resolve_everywhere() -> None:
    """Sweep helpers resolve from the wrapper, core, and top-level API."""
    import prin.kernels as kernels

    for name in SWEEP_NAMES:
        assert name in prin.__all__
        assert name in kernels.__all__
        assert callable(getattr(prin, name))
        assert callable(getattr(_prin_core, name))


def test_detect_oscillation_outputs() -> None:
    """Stable, short, and varying histories exercise owner outcomes/defaults."""
    assert not prin.detect_oscillation([0.5] * 30)
    assert not prin.detect_oscillation([0.0, 1.0], window=3)
    assert prin.detect_oscillation([0.0, 1.0] * 10, window=10, threshold=0.01)
    assert prin.detect_oscillation(
        [0.0, 1.0] * 10, 10, 0.01
    ) == _prin_core.detect_oscillation([0.0, 1.0] * 10, 10, 0.01)


@pytest.mark.parametrize("mode", ["soft", "hard", "annealed"])
def test_phase_to_rate_modes_match_core(mode: str) -> None:
    """Every phase-to-rate mode matches direct Rust and preserves metadata."""
    phase = torch.tensor([[0.0, 0.5, 1.0], [1.5, 2.0, 2.5]], dtype=torch.float64)
    amplitude = torch.ones_like(phase)
    actual = prin.phase_to_rate(
        phase, amplitude, mode=mode, sparsity=0.4, temperature=0.7
    )
    rows = [
        _prin_core.phase_to_rate(p.tolist(), a.tolist(), mode, 0.4, 0.7)
        for p, a in zip(phase, amplitude, strict=True)
    ]
    expected = torch.tensor(rows, dtype=phase.dtype)
    torch.testing.assert_close(actual, expected, rtol=1e-5, atol=1e-6)
    assert actual.shape == phase.shape
    assert actual.dtype == phase.dtype
    assert torch.all(actual >= 0)


def test_phase_to_rate_errors() -> None:
    """Unknown modes and invalid owner inputs map to ValueError."""
    phase = torch.tensor([0.0, 1.0])
    with pytest.raises(ValueError, match="Unknown phase_to_rate mode"):
        prin.phase_to_rate(phase, torch.ones_like(phase), mode="bad")
    with pytest.raises(ValueError, match="amplitude"):
        prin.phase_to_rate(phase, torch.tensor([-1.0, 1.0]))
    with pytest.raises(ValueError, match="shape"):
        prin.phase_to_rate(phase, torch.ones(3))


def test_sweep_output_grid_and_determinism() -> None:
    """Explicit Seed flow gives a stable ordered Cartesian result grid."""
    kwargs = {
        "n_oscillators": 6,
        "k_values": [0.5, 1.0],
        "m_values": [0.1, 0.3],
        "n_steps": 1,
        "dt": 0.01,
        "seed": _prin_core.Seed(23, 5),
    }
    first = prin.sweep_coupling_params(**kwargs)
    kwargs["seed"] = _prin_core.Seed(23, 5)
    second = prin.sweep_coupling_params(**kwargs)
    assert first == second
    assert len(first) == 4
    assert [(item["K"], item["m"]) for item in first] == [
        (0.5, 0.1),
        (0.5, 0.3),
        (1.0, 0.1),
        (1.0, 0.3),
    ]
    assert all(
        set(item) == {"K", "m", "r_delta", "r_theta", "r_gamma"} for item in first
    )
    assert all(
        0.0 <= item[key] <= 1.0
        for item in first
        for key in ("r_delta", "r_theta", "r_gamma")
    )


def test_sweep_matches_direct_core_and_accepts_device_compatibility() -> None:
    """Wrapper output is the direct compiled-core list of dictionaries."""
    actual = prin.sweep_coupling_params(
        6, [0.5], [0.2], 1, 0.01, seed=7, device=torch.device("cpu")
    )
    expected = _prin_core.sweep_coupling_params(6, [0.5], [0.2], 1, 0.01, 7, 0)
    assert actual == expected


@pytest.mark.parametrize(
    "kwargs",
    [
        {"n_oscillators": 0},
        {"k_values": []},
        {"m_values": []},
        {"n_steps": 0},
        {"dt": 0.0},
        {"m_values": [1.1]},
    ],
)
def test_sweep_errors(kwargs: dict[str, object]) -> None:
    """Invalid sweep grids and simulation metadata raise ValueError."""
    with pytest.raises(ValueError):
        prin.sweep_coupling_params(**kwargs)  # type: ignore[arg-type]
