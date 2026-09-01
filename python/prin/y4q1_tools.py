"""PRINet 3.0-compatible Year 4 Q1 experiment utilities.

This module provides the PRINet 3.0 ``prinet.utils.y4q1_tools`` public API.
Profiling helpers (``count_flops``, ``measure_wall_time``) and dataclasses are
real. The ablation framework (``AblationConfig``, ``AblationHybridPRINetV2``,
``create_ablation_model``) is re-exported from
:mod:`prin.nn.ablation_variants` (a Rust-backed PyTorch composition). The
Year-4-Q1.2 statistical utilities and chimera initial conditions delegate their
numerics to the Rust ``prin_sim`` owners exposed through
:mod:`prin._prin_core`; ``seed_stability_analysis`` is plain list bookkeeping.

No numerical computation is introduced in this module (Coding Standards
Sec. 1.2).
"""

from __future__ import annotations

import math
import time
from dataclasses import dataclass, field
from typing import Any, NoReturn

import torch

from prin._prin_core import (
    chimera_initial_condition as _rust_chimera_ic,
)
from prin._prin_core import (
    gaussian_bump_ic as _rust_gaussian_bump_ic,
)
from prin._prin_core import (
    half_sync_half_random_ic as _rust_half_sync_ic,
)
from prin._prin_core import (
    y4q1_bootstrap_ci as _rust_bootstrap_ci,
)
from prin._prin_core import (
    y4q1_cohens_d as _rust_cohens_d,
)
from prin._prin_core import (
    y4q1_polyfit as _rust_polyfit,
)
from prin._prin_core import (
    y4q1_spatial_correlation as _rust_spatial_correlation,
)
from prin._prin_core import (
    y4q1_welch_t_test as _rust_welch_t_test,
)
from prin.nn.ablation_variants import (
    AblationConfig as AblationConfig,
)
from prin.nn.ablation_variants import (
    AblationHybridPRINetV2 as AblationHybridPRINetV2,
)
from prin.nn.ablation_variants import (
    create_ablation_model as create_ablation_model,
)

__all__ = [
    "AblationConfig",
    "AblationHybridPRINetV2",
    "ExtendedTrainingResult",
    "PhaseTrackerLarge",
    "binding_persistence",
    "bootstrap_ci",
    "chimera_initial_condition",
    "cohens_d",
    "coherence_decay_rate",
    "count_flops",
    "create_ablation_model",
    "cross_frequency_coupling",
    "cumulative_phase_slip_curve",
    "curriculum_dataset",
    "curriculum_train",
    "gaussian_bump_ic",
    "half_sync_half_random_ic",
    "instantaneous_frequency_spread",
    "measure_wall_time",
    "memory_growth_profile",
    "noise_crossover_analysis",
    "noise_degradation_curve",
    "noise_tolerance_sweep",
    "order_parameter_series",
    "per_community_order_parameter",
    "phase_locking_value",
    "phase_slip_rate",
    "rebinding_speed",
    "seed_stability_analysis",
    "session_length_statistical_comparison",
    "spatial_correlation",
    "temporal_advantage_report",
    "throughput_series",
    "train_clevr_n_extended",
    "train_clevr_n_single_seed",
    "welch_t_test",
    "windowed_order_parameter_variance",
]


@dataclass
class ExtendedTrainingResult:
    """Result from multi-seed extended CLEVR-N training.

    Attributes:
        model_name: Name of the model architecture.
        n_objects: Number of objects in the CLEVR-N task.
        n_seeds: Number of random seeds.
        n_epochs: Number of epochs per seed.
        accuracies: Per-seed final accuracies.
        mean_accuracy: Mean accuracy across seeds.
        std_accuracy: Standard deviation.
        losses: Per-seed final losses.
        mean_loss: Mean final loss.
        std_loss: Std of final loss.
        p_value: Two-sample t-test p-value (if comparison provided).
        wall_times: Per-seed training wall time.
    """

    model_name: str = ""
    n_objects: int = 0
    n_seeds: int = 0
    n_epochs: int = 0
    accuracies: list[float] = field(default_factory=list)
    mean_accuracy: float = 0.0
    std_accuracy: float = 0.0
    losses: list[float] = field(default_factory=list)
    mean_loss: float = 0.0
    std_loss: float = 0.0
    p_value: float | None = None
    wall_times: list[float] = field(default_factory=list)


def count_flops(
    model: Any,
    input_shape: tuple[int, ...],
    device: str = "cpu",
) -> dict[str, Any]:
    """Estimate FLOPs for a model's forward pass.

    Iterates over the model's sub-modules and estimates FLOPs for
    ``Linear``, ``Conv2d``, and ``GRUCell`` layers. The estimate is scaled
    by the batch dimension of ``input_shape``.

    Args:
        model: Model exposing ``named_modules()`` (typically a
            ``torch.nn.Module``).
        input_shape: Input tensor shape (e.g. ``(8, 256)``).
        device: Accepted for signature compatibility. **Inert** -- PRIN
            does not move the model.

    Returns:
        Dict with ``total_flops``, ``total_params``, ``layer_flops``.

    Example:
        >>> import torch
        >>> m = torch.nn.Linear(4, 2)
        >>> result = count_flops(m, (1, 4))
        >>> result["total_flops"] > 0
        True
    """
    total_flops = 0
    layer_details: list[dict[str, Any]] = []

    for name, module in model.named_modules():
        mod_type = type(module).__name__
        if mod_type == "Linear":
            flops = 2 * module.in_features * module.out_features
            if module.bias is not None:
                flops += module.out_features
            total_flops += flops
            layer_details.append(
                {
                    "name": name,
                    "type": "Linear",
                    "flops": flops,
                    "params": (
                        module.in_features * module.out_features
                        + (module.out_features if module.bias is not None else 0)
                    ),
                }
            )
        elif mod_type == "Conv2d":
            k0, k1 = module.kernel_size
            flops = 2 * module.in_channels * module.out_channels * k0 * k1
            total_flops += flops
            layer_details.append(
                {
                    "name": name,
                    "type": "Conv2d",
                    "flops": flops,
                    "params": sum(p.numel() for p in module.parameters()),
                }
            )
        elif mod_type == "GRUCell":
            flops = (
                3 * 2 * (module.input_size + module.hidden_size) * module.hidden_size
            )
            total_flops += flops
            layer_details.append(
                {
                    "name": name,
                    "type": "GRUCell",
                    "flops": flops,
                    "params": sum(p.numel() for p in module.parameters()),
                }
            )
        elif mod_type == "OscillatoryAttention":
            # PRIN's OscillatoryAttention keeps its q/k/v/out projections in
            # the Rust bridge, so they are invisible to a ``named_modules``
            # ``nn.Linear`` scan. Account for the four ``d_model x d_model``
            # projections directly (matching how the reference counts an
            # ``nn.MultiheadAttention``-style block).
            d = module.d_model
            flops = 4 * 2 * d * d
            total_flops += flops
            layer_details.append(
                {
                    "name": name,
                    "type": "OscillatoryAttention",
                    "flops": flops,
                    "params": 4 * d * d,
                }
            )

    batch_size = input_shape[0] if len(input_shape) > 1 else 1
    total_flops *= batch_size
    total_params = sum(p.numel() for p in model.parameters())

    return {
        "total_flops": total_flops,
        "total_params": total_params,
        "layer_flops": layer_details,
    }


def measure_wall_time(
    model: Any,
    input_tensor: Any,
    n_warmup: int = 5,
    n_runs: int = 20,
) -> dict[str, float]:
    """Measure forward-pass wall time with warmup.

    Args:
        model: Model with a ``forward`` method.
        input_tensor: Input tensor or tuple of input tensors.
        n_warmup: Number of warmup runs (not timed).
        n_runs: Number of timed runs.

    Returns:
        Dict with ``mean_ms``, ``std_ms``, ``min_ms``, ``max_ms``,
        ``n_runs``.

    Raises:
        ValueError: If ``n_warmup`` or ``n_runs`` is not positive.

    Example:
        >>> import torch
        >>> m = torch.nn.Linear(4, 2)
        >>> x = torch.randn(1, 4)
        >>> result = measure_wall_time(m, x, n_warmup=1, n_runs=3)
        >>> result["n_runs"]
        3
    """
    if n_warmup < 0:
        raise ValueError(f"n_warmup must be non-negative, got {n_warmup}")
    if n_runs < 1:
        raise ValueError(f"n_runs must be positive, got {n_runs}")

    model.eval()

    for _ in range(n_warmup):
        model(input_tensor)

    times: list[float] = []
    for _ in range(n_runs):
        start = time.perf_counter()
        model(input_tensor)
        times.append((time.perf_counter() - start) * 1000.0)

    mean_ms = sum(times) / len(times)
    variance = sum((t - mean_ms) ** 2 for t in times) / max(len(times) - 1, 1)
    std_ms = variance**0.5

    return {
        "mean_ms": mean_ms,
        "std_ms": std_ms,
        "min_ms": min(times),
        "max_ms": max(times),
        "n_runs": n_runs,
    }


# =========================================================================
# Q1.2: Statistical utilities & chimera initial conditions
# =========================================================================


def bootstrap_ci(
    values: list[float],
    n_bootstrap: int = 10_000,
    alpha: float = 0.05,
    seed: int = 42,
) -> dict[str, float]:
    """Percentile bootstrap confidence interval for the mean.

    Delegates the resampling and percentile computation to the Rust
    ``y4q1_bootstrap_ci`` owner.

    Args:
        values: Observed values.
        n_bootstrap: Number of bootstrap resamples.
        alpha: Significance level (``0.05`` → 95 % CI).
        seed: Random seed.

    Returns:
        Dict with ``mean``, ``ci_lower``, ``ci_upper``, ``ci_width``, ``se``.
    """
    mean_v, lo, hi, width, se = _rust_bootstrap_ci(
        [float(v) for v in values], n_bootstrap, alpha, seed
    )
    return {
        "mean": mean_v,
        "ci_lower": lo,
        "ci_upper": hi,
        "ci_width": width,
        "se": se,
    }


def cohens_d(group_a: list[float], group_b: list[float]) -> float:
    """Cohen's *d* effect size with pooled standard deviation.

    Args:
        group_a: Observations from condition A.
        group_b: Observations from condition B.

    Returns:
        Cohen's *d* (positive means A > B); ``0.0`` for degenerate inputs.
    """
    return float(
        _rust_cohens_d([float(v) for v in group_a], [float(v) for v in group_b])
    )


def welch_t_test(
    group_a: list[float],
    group_b: list[float],
) -> dict[str, float]:
    """Welch's t-test with effect size.

    Args:
        group_a: Observations from condition A.
        group_b: Observations from condition B.

    Returns:
        Dict with ``t_stat``, ``p_value``, ``cohens_d``, ``mean_diff``.
    """
    t_stat, p_value, d, mean_diff = _rust_welch_t_test(
        [float(v) for v in group_a], [float(v) for v in group_b]
    )
    return {
        "t_stat": t_stat,
        "p_value": p_value,
        "cohens_d": d,
        "mean_diff": mean_diff,
    }


def spatial_correlation(
    r_local: torch.Tensor,
    max_lag: int = 50,
) -> list[float]:
    """Spatial autocorrelation of a local order parameter field.

    Args:
        r_local: Local order parameter ``(N,)``.
        max_lag: Maximum spatial lag.

    Returns:
        List of autocorrelation values for lags ``0 .. max_lag``.
    """
    flat = r_local.detach().to(dtype=torch.float64, device="cpu").reshape(-1).tolist()
    return list(_rust_spatial_correlation(flat, int(max_lag)))


def seed_stability_analysis(
    per_seed_results: list[dict[str, Any]],
    metric_key: str,
) -> dict[str, float]:
    """Analyse stability of a metric across random seeds.

    Args:
        per_seed_results: List of dicts, each containing ``metric_key``.
        metric_key: Key to extract from each result dict.

    Returns:
        Dict with ``mean``, ``std``, ``cv``, ``range``, ``n_seeds``.
    """
    vals = [r[metric_key] for r in per_seed_results]
    mean_v = sum(vals) / len(vals)
    std_v = (sum((v - mean_v) ** 2 for v in vals) / max(len(vals) - 1, 1)) ** 0.5
    return {
        "mean": mean_v,
        "std": std_v,
        "cv": std_v / abs(mean_v) if abs(mean_v) > 1e-12 else 0.0,
        "range": max(vals) - min(vals),
        "n_seeds": len(vals),
    }


def chimera_initial_condition(N: int, seed: int = 0) -> torch.Tensor:
    """Single-humped initial phase profile for chimera emergence.

    Args:
        N: Number of oscillators.
        seed: Random seed for the perturbation.

    Returns:
        Phase tensor ``(N,)``.
    """
    return torch.tensor(_rust_chimera_ic(int(N), int(seed)), dtype=torch.float32)


def gaussian_bump_ic(
    N: int,
    A0: float = math.pi,
    sigma_ratio: float = 1 / 6,
    phi0: float = 0.0,
    noise_amp: float = 0.01,
    seed: int = 0,
) -> torch.Tensor:
    """Smooth Gaussian-bump initial condition for chimera states.

    Args:
        N: Number of oscillators.
        A0: Amplitude of the Gaussian bump (radians).
        sigma_ratio: ``sigma/N`` ratio.
        phi0: Baseline phase offset.
        noise_amp: Uniform noise amplitude.
        seed: Random seed.

    Returns:
        Phase tensor ``(N,)`` in ``[0, 2π)``.
    """
    return torch.tensor(
        _rust_gaussian_bump_ic(int(N), A0, sigma_ratio, phi0, noise_amp, int(seed)),
        dtype=torch.float32,
    )


def half_sync_half_random_ic(
    N: int,
    sync_phase: float = 0.0,
    noise_amp: float = 0.01,
    seed: int = 0,
) -> torch.Tensor:
    """Half-synchronised, half-random initial condition.

    Args:
        N: Number of oscillators.
        sync_phase: Phase of the synchronised half (radians).
        noise_amp: Noise amplitude for the coherent half.
        seed: Random seed.

    Returns:
        Phase tensor ``(N,)`` in ``[0, 2π)``.
    """
    return torch.tensor(
        _rust_half_sync_ic(int(N), sync_phase, noise_amp, int(seed)),
        dtype=torch.float32,
    )


def _raise_disposition(symbol: str, detail: str) -> NoReturn:
    """Raise the typed D-2.2 disposition error."""
    raise NotImplementedError(
        f"{symbol} is a deferred-rebuild symbol (WP-036 D-2.2). {detail} "
        "See the Migration Guide for the disposition and the owning WP."
    )


def train_clevr_n_single_seed(*_args: Any, **_kwargs: Any) -> NoReturn:
    """Reject calls to the deferred single-seed CLEVR-N training loop.

    Raises:
        NotImplementedError: Always. Training loop requires Python numerics.
    """
    _raise_disposition(
        "train_clevr_n_single_seed",
        "Training loop requires Python numerics.",
    )


def train_clevr_n_extended(*_args: Any, **_kwargs: Any) -> NoReturn:
    """Reject calls to the deferred extended CLEVR-N training runner.

    Raises:
        NotImplementedError: Always. Multi-seed training requires Python
            numerics.
    """
    _raise_disposition(
        "train_clevr_n_extended",
        "Multi-seed training requires Python numerics.",
    )


# =========================================================================
# Y4 Q1.4: Temporal advantage deepening metrics
# =========================================================================


def phase_slip_rate(
    phase_trajectory: torch.Tensor,
    threshold: float = math.pi * 0.8,
) -> dict[str, Any]:
    """Compute phase-slip rate from a phase trajectory."""
    if phase_trajectory.dim() != 2:
        raise ValueError(
            f"Expected 2-D (T, N) trajectory, got shape {phase_trajectory.shape}."
        )
    T, N = phase_trajectory.shape
    if T < 2:
        return {
            "total_slips": 0,
            "slips_per_step": 0.0,
            "slips_per_oscillator": 0.0,
            "slip_fraction": 0.0,
            "per_oscillator_slips": [0] * N,
        }
    diff = phase_trajectory[1:] - phase_trajectory[:-1]
    diff = (diff + math.pi) % (2.0 * math.pi) - math.pi
    slips = (diff.abs() > threshold).long()
    per_osc = slips.sum(dim=0).tolist()
    total = int(slips.sum().item())
    n_transitions = (T - 1) * N
    return {
        "total_slips": total,
        "slips_per_step": total / (T - 1),
        "slips_per_oscillator": total / N,
        "slip_fraction": total / n_transitions,
        "per_oscillator_slips": per_osc,
    }


def binding_persistence(
    matches_history: list[torch.Tensor],
    n_objects: int,
) -> dict[str, Any]:
    """Measure how persistently objects maintain identity across frames."""
    if not matches_history:
        return {
            "mean_persistence": 0.0,
            "min_persistence": 0.0,
            "per_object_persistence": [],
            "n_frames": 0,
        }
    T = len(matches_history)
    per_obj: list[float] = []
    for obj_idx in range(n_objects):
        matched_count = 0
        for m in matches_history:
            val = m[obj_idx]
            if hasattr(val, "item"):
                matched_count += 1 if val.item() >= 0 else 0
            else:
                matched_count += 1 if val >= 0 else 0
        per_obj.append(matched_count / T)
    return {
        "mean_persistence": sum(per_obj) / len(per_obj),
        "min_persistence": min(per_obj),
        "per_object_persistence": per_obj,
        "n_frames": T,
    }


def coherence_decay_rate(
    coherence_series: list[float],
) -> dict[str, float]:
    r"""Fit an exponential decay to a coherence time series."""
    import numpy as np

    c = np.asarray(coherence_series, dtype=np.float64)
    c = np.clip(c, 1e-10, None)
    n = len(c)
    if n < 2:
        return {
            "decay_rate": 0.0,
            "half_life": float("inf"),
            "initial_coherence": float(c[0]) if n else 0.0,
            "r_squared": 0.0,
        }
    t = np.arange(n, dtype=np.float64)
    ln_c = np.log(c)
    slope, intercept = _rust_polyfit(t.tolist(), ln_c.tolist(), 1)
    lam = -slope
    c0 = math.exp(intercept)
    predicted = slope * t + intercept
    ss_res = float(np.sum((ln_c - predicted) ** 2))
    ss_tot = float(np.sum((ln_c - ln_c.mean()) ** 2))
    r2 = 1.0 - ss_res / max(ss_tot, 1e-12)
    half_life = math.log(2) / max(abs(lam), 1e-12) if lam > 0 else float("inf")
    return {
        "decay_rate": float(lam),
        "half_life": float(half_life),
        "initial_coherence": float(c0),
        "r_squared": float(r2),
    }


def rebinding_speed(
    matches_before: list[torch.Tensor],
    matches_after: list[torch.Tensor],
    n_objects: int,
) -> dict[str, Any]:
    """Measure how quickly identity bindings recover after perturbation."""
    if not matches_before:
        pre_rate = 1.0
    else:
        rates_before = [(m >= 0).float().mean().item() for m in matches_before]
        pre_rate = sum(rates_before) / len(rates_before)
    target = 0.9 * pre_rate
    post_rates: list[float] = []
    recovery_frame = -1
    for i, m in enumerate(matches_after):
        rate = (m >= 0).float().mean().item()
        post_rates.append(rate)
        if rate >= target and recovery_frame < 0:
            recovery_frame = i
    return {
        "pre_match_rate": pre_rate,
        "recovery_frames": recovery_frame,
        "post_match_rates": post_rates,
    }


def cross_frequency_coupling(
    phases_low: torch.Tensor,
    phases_high: torch.Tensor,
) -> dict[str, Any]:
    r"""Compute phase-amplitude coupling (PAC) between frequency bands."""
    if phases_low.shape != phases_high.shape:
        raise ValueError(
            f"Shape mismatch: phases_low {phases_low.shape} vs "
            f"phases_high {phases_high.shape}."
        )
    diff = phases_low - phases_high
    if phases_low.dim() == 1:
        pac_val = float(torch.sin(diff).mean().abs().item())
        return {"pac": pac_val, "pac_per_step": [pac_val]}
    per_step = [
        float(torch.sin(diff[t]).mean().abs().item()) for t in range(diff.shape[0])
    ]
    return {
        "pac": sum(per_step) / len(per_step),
        "pac_per_step": per_step,
    }


def temporal_advantage_report(
    phase_tracker_result: dict[str, Any],
    slot_attention_result: dict[str, Any],
    n_seeds: int = 1,
) -> dict[str, Any]:
    """Compile a head-to-head temporal advantage report."""
    ip_phase = phase_tracker_result["identity_preservation"]
    ip_slot = slot_attention_result["identity_preservation"]
    sim_phase = phase_tracker_result.get("per_frame_similarity", [])
    sim_slot = slot_attention_result.get("per_frame_similarity", [])
    rho_phase = phase_tracker_result.get("per_frame_phase_correlation", [])
    return {
        "ip_phase": ip_phase,
        "ip_slot": ip_slot,
        "ip_advantage": ip_phase - ip_slot,
        "mean_sim_phase": sum(sim_phase) / max(len(sim_phase), 1),
        "mean_sim_slot": sum(sim_slot) / max(len(sim_slot), 1),
        "mean_rho_phase": sum(rho_phase) / max(len(rho_phase), 1),
        "n_seeds": n_seeds,
    }


# =========================================================================
# Y4 Q1.5: Session-length metrics
# =========================================================================


def order_parameter_series(
    phase_trajectory: torch.Tensor,
) -> dict[str, Any]:
    """Compute the Kuramoto order parameter r(t) across a phase trajectory."""
    if phase_trajectory.dim() == 3:
        T, N, K = phase_trajectory.shape
        phase_trajectory = phase_trajectory.reshape(T, N * K)
    T, N = phase_trajectory.shape
    z = torch.exp(1j * phase_trajectory.to(torch.complex64))
    r_complex = z.mean(dim=1)
    r_mag = r_complex.abs().float()
    r_list = r_mag.tolist()
    return {
        "r_series": r_list,
        "mean_r": float(r_mag.mean().item()),
        "std_r": float(r_mag.std().item()) if T > 1 else 0.0,
        "final_r": r_list[-1] if r_list else 0.0,
    }


def windowed_order_parameter_variance(
    r_series: list[float],
    window_size: int = 10,
) -> dict[str, Any]:
    """Compute windowed variance of the order parameter r(t)."""
    import numpy as np

    n = len(r_series)
    n_windows = n // max(window_size, 1)
    if n_windows < 2:
        return {
            "window_stds": ([float(np.std(r_series))] if r_series else [0.0]),
            "trend_slope": 0.0,
            "mean_window_std": (float(np.std(r_series)) if r_series else 0.0),
        }
    stds: list[float] = []
    for i in range(n_windows):
        start = i * window_size
        end = start + window_size
        w = r_series[start:end]
        stds.append(float(np.std(w)))
    x = np.arange(len(stds), dtype=float)
    y = np.array(stds, dtype=float)
    slope = _rust_polyfit(x.tolist(), y.tolist(), 1)[0] if len(stds) >= 2 else 0.0
    return {
        "window_stds": stds,
        "trend_slope": slope,
        "mean_window_std": float(np.mean(stds)),
    }


def phase_locking_value(
    phase_a: torch.Tensor,
    phase_b: torch.Tensor,
) -> dict[str, Any]:
    """Compute phase locking value (PLV) between two phase signals."""
    diff = phase_a - phase_b
    z = torch.exp(1j * diff.to(torch.complex64))
    if z.dim() == 1:
        plv_val = float(z.mean().abs().item())
        return {"plv": plv_val, "plv_per_pair": [plv_val]}
    plv_per_pair = z.mean(dim=0).abs().float().tolist()
    return {
        "plv": float(sum(plv_per_pair) / len(plv_per_pair)),
        "plv_per_pair": plv_per_pair,
    }


def instantaneous_frequency_spread(
    phase_trajectory: torch.Tensor,
    dt: float = 1.0,
) -> dict[str, Any]:
    """Compute instantaneous frequency spread across oscillators."""
    import numpy as np

    if phase_trajectory.dim() != 2 or phase_trajectory.shape[0] < 2:
        return {
            "freq_spread_series": [],
            "mean_spread": 0.0,
            "trend_slope": 0.0,
        }
    diff = phase_trajectory[1:] - phase_trajectory[:-1]
    diff = (diff + math.pi) % (2.0 * math.pi) - math.pi
    omega = diff / dt
    spread = omega.std(dim=1).tolist()
    x = np.arange(len(spread), dtype=float)
    y = np.array(spread, dtype=float)
    slope = _rust_polyfit(x.tolist(), y.tolist(), 1)[0] if len(spread) >= 2 else 0.0
    return {
        "freq_spread_series": spread,
        "mean_spread": float(np.mean(spread)) if spread else 0.0,
        "trend_slope": slope,
    }


def cumulative_phase_slip_curve(
    phase_trajectory: torch.Tensor,
    threshold: float = math.pi * 0.8,
) -> dict[str, Any]:
    """Compute cumulative phase-slip curve over session duration."""
    import numpy as np

    if phase_trajectory.dim() != 2 or phase_trajectory.shape[0] < 2:
        return {
            "cumulative_slips": [],
            "total_slips": 0,
            "acceleration": 0.0,
        }
    diff = phase_trajectory[1:] - phase_trajectory[:-1]
    diff = (diff + math.pi) % (2.0 * math.pi) - math.pi
    slip_per_step = (diff.abs() > threshold).sum(dim=1).tolist()
    cum: list[int] = []
    running = 0
    for s in slip_per_step:
        running += s
        cum.append(running)
    total = cum[-1] if cum else 0
    accel = 0.0
    if len(cum) >= 3:
        x = np.arange(len(cum), dtype=float)
        y = np.array(cum, dtype=float)
        coeffs = _rust_polyfit(x.tolist(), y.tolist(), 2)
        accel = float(coeffs[0])
    return {
        "cumulative_slips": cum,
        "total_slips": total,
        "acceleration": accel,
    }


def throughput_series(
    wall_times_per_interval: list[float],
    frames_per_interval: int,
) -> dict[str, Any]:
    """Compute throughput stability metrics from interval timings."""
    import numpy as np

    fps = [frames_per_interval / max(w, 1e-9) for w in wall_times_per_interval]
    if len(fps) < 2:
        return {
            "fps_series": fps,
            "mean_fps": fps[0] if fps else 0.0,
            "std_fps": 0.0,
            "degradation_pct": 0.0,
        }
    first_fps = fps[0]
    last_fps = fps[-1]
    degrad = ((last_fps - first_fps) / max(abs(first_fps), 1e-9)) * 100.0
    return {
        "fps_series": fps,
        "mean_fps": float(np.mean(fps)),
        "std_fps": float(np.std(fps)),
        "degradation_pct": degrad,
    }


def memory_growth_profile(
    memory_samples_mb: list[float],
    interval_seconds: float,
) -> dict[str, Any]:
    """Characterize memory growth over a session."""
    import numpy as np

    if not memory_samples_mb:
        return {
            "initial_mb": 0.0,
            "peak_mb": 0.0,
            "final_mb": 0.0,
            "growth_mb": 0.0,
            "growth_rate_mb_per_min": 0.0,
            "is_leaking": False,
        }
    arr = np.array(memory_samples_mb, dtype=float)
    initial = float(arr[0])
    peak = float(arr.max())
    final = float(arr[-1])
    growth = peak - initial
    rate = 0.0
    if len(arr) >= 2:
        x_minutes = np.arange(len(arr)) * interval_seconds / 60.0
        slope = _rust_polyfit(x_minutes.tolist(), arr.tolist(), 1)[0]
        rate = slope
    return {
        "initial_mb": initial,
        "peak_mb": peak,
        "final_mb": final,
        "growth_mb": growth,
        "growth_rate_mb_per_min": rate,
        "is_leaking": growth > 0.1 * max(initial, 1.0),
    }


def _regularised_incomplete_beta(
    x: float,
    a: float,
    b: float,
    max_iter: int = 200,
) -> float:
    """Regularised incomplete beta function I_x(a, b) via continued fraction."""
    if x <= 0.0:
        return 0.0
    if x >= 1.0:
        return 1.0
    if x > (a + 1.0) / (a + b + 2.0):
        return 1.0 - _regularised_incomplete_beta(1.0 - x, b, a, max_iter)
    ln_prefix = (
        math.lgamma(a + b)
        - math.lgamma(a)
        - math.lgamma(b)
        + a * math.log(x)
        + b * math.log(1.0 - x)
    )
    prefix = math.exp(ln_prefix)
    tiny = 1e-30
    f = tiny
    c = tiny
    d = 0.0
    for m in range(max_iter):
        if m == 0:
            a_m = 1.0
        elif m % 2 == 1:
            k = (m - 1) // 2 + 1
            a_m = (
                -(a + k - 1.0 + k)
                * (a + k - 1.0)
                * x
                / ((a + 2 * k - 2.0) * (a + 2 * k - 1.0))
            )
        else:
            k = m // 2
            a_m = k * (b - k) * x / ((a + 2 * k - 1.0) * (a + 2 * k))
        d = 1.0 + a_m * d
        if abs(d) < tiny:
            d = tiny
        d = 1.0 / d
        c = 1.0 + a_m / c
        if abs(c) < tiny:
            c = tiny
        f *= c * d
        if abs(c * d - 1.0) < 1e-12:
            break
    return prefix * (f - 1.0) / a


def _f_distribution_p_value(
    f_stat: float,
    df1: int,
    df2: int,
) -> float:
    """Approximate p-value for F-distribution."""
    if f_stat <= 0:
        return 1.0
    x = df1 * f_stat / (df1 * f_stat + df2)
    a = df1 / 2.0
    b = df2 / 2.0
    return 1.0 - _regularised_incomplete_beta(x, a, b)


def session_length_statistical_comparison(
    metrics_by_duration: dict[str, list[float]],
) -> dict[str, Any]:
    """Compare a metric across session durations using ANOVA + pairwise Cohen's d."""
    import numpy as np

    groups = list(metrics_by_duration.values())
    labels = list(metrics_by_duration.keys())
    if len(groups) < 2:
        return {
            "anova_f": 0.0,
            "anova_p": 1.0,
            "pairwise_d": {},
            "significant": False,
            "eta_squared": 0.0,
        }
    all_vals: list[float] = []
    for g in groups:
        all_vals.extend(g)
    grand_mean = float(np.mean(all_vals))
    n_total = len(all_vals)
    k = len(groups)
    ss_between = sum(len(g) * (float(np.mean(g)) - grand_mean) ** 2 for g in groups)
    ss_within = sum(sum((v - float(np.mean(g))) ** 2 for v in g) for g in groups)
    ss_total = ss_between + ss_within
    df_between = k - 1
    df_within = n_total - k
    if df_within <= 0 or ss_within == 0:
        return {
            "anova_f": (float("inf") if ss_between > 0 else 0.0),
            "anova_p": 0.0 if ss_between > 0 else 1.0,
            "pairwise_d": {},
            "significant": ss_between > 0,
            "eta_squared": (1.0 if ss_total > 0 and ss_between > 0 else 0.0),
        }
    ms_between = ss_between / df_between
    ms_within = ss_within / df_within
    f_stat = ms_between / ms_within
    p_val = _f_distribution_p_value(f_stat, df_between, df_within)
    eta_sq = ss_between / ss_total if ss_total > 0 else 0.0
    pairwise_d: dict[str, float] = {}
    for i in range(k):
        for j in range(i + 1, k):
            g_a = np.array(groups[i], dtype=float)
            g_b = np.array(groups[j], dtype=float)
            pooled_std = float(
                np.sqrt(
                    (
                        (len(g_a) - 1) * g_a.var(ddof=1)
                        + (len(g_b) - 1) * g_b.var(ddof=1)
                    )
                    / max(len(g_a) + len(g_b) - 2, 1)
                )
            )
            d = (float(g_a.mean()) - float(g_b.mean())) / max(pooled_std, 1e-9)
            pairwise_d[f"{labels[i]}_vs_{labels[j]}"] = round(d, 4)
    return {
        "anova_f": round(f_stat, 4),
        "anova_p": round(p_val, 6),
        "pairwise_d": pairwise_d,
        "significant": p_val < 0.05,
        "eta_squared": round(eta_sq, 4),
    }


# =========================================================================
# Y4 Q1.8: PhaseTrackerLarge
# =========================================================================


class PhaseTrackerLarge(torch.nn.Module):
    """Scaled-up PhaseTracker targeting ~84K params."""

    def __init__(
        self,
        detection_dim: int = 4,
        n_osc: int = 112,
        hidden_dim: int = 192,
        n_discrete_steps: int = 5,
        match_threshold: float = 0.1,
    ) -> None:
        super().__init__()
        from prin.nn import DiscreteDeltaThetaGamma

        self.n_osc = n_osc
        self._n_discrete_steps = n_discrete_steps
        self.match_threshold = match_threshold
        self.det_to_phase = torch.nn.Sequential(
            torch.nn.Linear(detection_dim, hidden_dim),
            torch.nn.ReLU(),
            torch.nn.Linear(hidden_dim, hidden_dim),
            torch.nn.ReLU(),
            torch.nn.Linear(hidden_dim, n_osc),
        )
        self.det_to_amp = torch.nn.Sequential(
            torch.nn.Linear(detection_dim, hidden_dim),
            torch.nn.ReLU(),
            torch.nn.Linear(hidden_dim, n_osc),
            torch.nn.Softplus(),
        )
        n_delta = n_osc // 7
        n_theta = n_osc * 2 // 7
        n_gamma = n_osc - n_delta - n_theta
        self.dynamics = DiscreteDeltaThetaGamma(
            n_delta=n_delta,
            n_theta=n_theta,
            n_gamma=n_gamma,
        )
        self.phase_refine = torch.nn.Sequential(
            torch.nn.Linear(n_osc, hidden_dim),
            torch.nn.ReLU(),
            torch.nn.Linear(hidden_dim, n_osc),
        )

    def encode(self, detections: torch.Tensor) -> tuple[torch.Tensor, torch.Tensor]:
        """Encode detections to (phase, amplitude)."""
        phase_raw = self.det_to_phase(detections)
        phase = phase_raw % (2.0 * math.pi)
        amp = self.det_to_amp(detections)
        return phase, amp

    def evolve(
        self, phase: torch.Tensor, amplitude: torch.Tensor
    ) -> tuple[torch.Tensor, torch.Tensor]:
        """Evolve phase state through dynamics + residual refinement."""
        phase, amplitude = self.dynamics.integrate(
            phase,
            amplitude,
            n_steps=self._n_discrete_steps,
            dt=0.01,
        )
        phase = phase + 0.1 * self.phase_refine(phase)
        phase = phase % (2.0 * math.pi)
        return phase, amplitude

    def phase_similarity(
        self, phase_a: torch.Tensor, phase_b: torch.Tensor
    ) -> torch.Tensor:
        """Phase similarity matrix via cosine of complex embeddings."""
        _EPS = 1e-8
        z_a = torch.exp(1j * phase_a.to(torch.complex64))
        z_b = torch.exp(1j * phase_b.to(torch.complex64))
        z_a_norm = z_a / (z_a.abs().pow(2).sum(dim=-1, keepdim=True).sqrt() + _EPS)
        z_b_norm = z_b / (z_b.abs().pow(2).sum(dim=-1, keepdim=True).sqrt() + _EPS)
        sim = (
            (z_a_norm.unsqueeze(1) * z_b_norm.conj().unsqueeze(0))
            .sum(dim=-1)
            .real.float()
        )
        return sim

    def forward(
        self,
        detections_t: torch.Tensor,
        detections_t1: torch.Tensor,
    ) -> tuple[torch.Tensor, torch.Tensor]:
        """Match detections across two consecutive frames."""
        phase_t, amp_t = self.encode(detections_t)
        phase_t1, _amp_t1 = self.encode(detections_t1)
        phase_t_evolved, _ = self.evolve(phase_t, amp_t)
        sim = self.phase_similarity(phase_t_evolved, phase_t1)
        N_t = detections_t.shape[0]
        matches = torch.full((N_t,), -1, dtype=torch.long, device=detections_t.device)
        used = torch.zeros(
            detections_t1.shape[0],
            dtype=torch.bool,
            device=detections_t.device,
        )
        max_sims, max_idxs = sim.max(dim=1)
        order = max_sims.argsort(descending=True)
        for idx in order:
            best_j = int(max_idxs[idx].item())
            if not used[best_j] and max_sims[idx].item() >= self.match_threshold:
                matches[idx] = best_j
                used[best_j] = True
        return matches, sim

    def track_sequence(self, frame_detections: list[torch.Tensor]) -> dict[str, Any]:
        """Track objects across a sequence of frames."""
        if len(frame_detections) < 2:
            return {
                "phase_history": [],
                "identity_matches": [],
                "identity_preservation": 1.0,
                "per_frame_similarity": [],
                "per_frame_phase_correlation": [],
            }
        all_matches: list[torch.Tensor] = []
        all_sims: list[float] = []
        all_corrs: list[float] = []
        for t in range(len(frame_detections) - 1):
            matches, sim = self(frame_detections[t], frame_detections[t + 1])
            all_matches.append(matches)
            all_sims.append(float(sim.max(dim=1).values.mean().item()))
            diag_sim = torch.diagonal(
                sim[
                    : min(sim.shape[0], sim.shape[1]),
                    : min(sim.shape[0], sim.shape[1]),
                ]
            )
            all_corrs.append(
                float(diag_sim.mean().item()) if diag_sim.numel() > 0 else 0.0
            )
        n_correct = 0
        n_total = 0
        for m in all_matches:
            for i, j in enumerate(m):
                n_total += 1
                if j.item() == i:
                    n_correct += 1
        ip = n_correct / max(n_total, 1)
        return {
            "phase_history": [],
            "identity_matches": all_matches,
            "identity_preservation": ip,
            "per_frame_similarity": all_sims,
            "per_frame_phase_correlation": all_corrs,
        }


# =========================================================================
# Y4 Q1.8: noise tolerance + curriculum (benchmark orchestration)
# =========================================================================


def noise_tolerance_sweep(
    pt_model: torch.nn.Module,
    sa_model: torch.nn.Module,
    dataset_fn: Any,
    sigmas: list[float],
    n_seeds: int = 3,
    device: str = "cpu",
) -> dict[str, Any]:
    """Sweep noise levels and compare identity preservation for PT vs. SA."""
    results: dict[str, Any] = {}
    for sigma in sigmas:
        pt_ips: list[float] = []
        sa_ips: list[float] = []
        for s in range(n_seeds):
            ds = dataset_fn(seed=42 + s, noise_sigma=sigma)
            for model, ips in [(pt_model, pt_ips), (sa_model, sa_ips)]:
                model.eval()
                model.to(device)
                seq_ips: list[float] = []
                dyn_model: Any = model
                with torch.no_grad():
                    for seq in ds:
                        frames = [f.to(device) for f in seq.frames]
                        res = dyn_model.track_sequence(frames)
                        seq_ips.append(res["identity_preservation"])
                ips.append(sum(seq_ips) / max(len(seq_ips), 1))
        results[str(sigma)] = {
            "sigma": sigma,
            "pt_ips": pt_ips,
            "sa_ips": sa_ips,
            "pt_mean": sum(pt_ips) / max(len(pt_ips), 1),
            "sa_mean": sum(sa_ips) / max(len(sa_ips), 1),
            "pt_ci": bootstrap_ci(pt_ips) if len(pt_ips) >= 2 else None,
            "sa_ci": bootstrap_ci(sa_ips) if len(sa_ips) >= 2 else None,
        }
    return results


def noise_degradation_curve(
    model: torch.nn.Module,
    dataset_fn: Any,
    sigmas: list[float],
    n_seeds: int = 3,
    device: str = "cpu",
) -> dict[str, Any]:
    """Identity preservation as a function of noise sigma with bootstrap CI."""
    import numpy as np

    curve: dict[str, Any] = {}
    for sigma in sigmas:
        ips: list[float] = []
        for s in range(n_seeds):
            ds = dataset_fn(seed=42 + s, noise_sigma=sigma)
            model.eval()
            model.to(device)
            seq_ips: list[float] = []
            dyn_model: Any = model
            with torch.no_grad():
                for seq in ds:
                    frames = [f.to(device) for f in seq.frames]
                    res = dyn_model.track_sequence(frames)
                    seq_ips.append(res["identity_preservation"])
            ips.append(sum(seq_ips) / max(len(seq_ips), 1))
        curve[str(sigma)] = {
            "sigma": sigma,
            "ips": ips,
            "mean": float(np.mean(ips)),
            "std": float(np.std(ips, ddof=1)) if len(ips) > 1 else 0.0,
            "ci": bootstrap_ci(ips) if len(ips) >= 2 else None,
        }
    return curve


def noise_crossover_analysis(
    pt_curve: dict[str, Any],
    sa_curve: dict[str, Any],
) -> dict[str, Any]:
    """Find the crossover sigma where PT identity preservation exceeds SA."""
    import numpy as np

    sigmas = sorted([float(k) for k in pt_curve.keys()])
    pt_means = [pt_curve[str(s)]["mean"] for s in sigmas]
    sa_means = [sa_curve[str(s)]["mean"] for s in sigmas]

    crossover_sigma = None
    for i in range(len(sigmas) - 1):
        diff_i = pt_means[i] - sa_means[i]
        diff_j = pt_means[i + 1] - sa_means[i + 1]
        if diff_i <= 0 and diff_j > 0:
            f = -diff_i / max(diff_j - diff_i, 1e-12)
            crossover_sigma = sigmas[i] + f * (sigmas[i + 1] - sigmas[i])
            break

    def _fit_exp(means: list[float]) -> float:
        s_arr = np.array(sigmas, dtype=float)
        m_arr = np.clip(np.array(means, dtype=float), 1e-10, None)
        ln_m = np.log(m_arr)
        if len(s_arr) >= 2:
            coeffs = _rust_polyfit(s_arr.tolist(), ln_m.tolist(), 1)
            return -float(coeffs[0])
        return 0.0

    lambda_pt = _fit_exp(pt_means)
    lambda_sa = _fit_exp(sa_means)

    stats = {}
    for s in sigmas:
        sk = str(s)
        if sk in pt_curve and sk in sa_curve:
            pt_ips = pt_curve[sk].get("ips", [])
            sa_ips = sa_curve[sk].get("ips", [])
            if len(pt_ips) >= 2 and len(sa_ips) >= 2:
                stats[sk] = welch_t_test(pt_ips, sa_ips)

    return {
        "crossover_sigma": crossover_sigma,
        "lambda_pt": lambda_pt,
        "lambda_sa": lambda_sa,
        "pt_degrades_slower": lambda_pt < lambda_sa,
        "per_sigma_stats": stats,
    }


def curriculum_dataset(
    stage: int,
    n_seqs: int = 20,
    det_dim: int = 4,
    seed: int = 42,
) -> list[Any]:
    """Generate a dataset for a curriculum stage (1-4: harder objects/frames)."""
    from prin.temporal_training import generate_dataset

    stage_config = {
        1: (2, 10),
        2: (3, 20),
        3: (4, 40),
        4: (6, 60),
    }
    n_obj, n_frames = stage_config.get(stage, (4, 20))
    return generate_dataset(
        n_seqs,
        n_objects=n_obj,
        n_frames=n_frames,
        det_dim=det_dim,
        base_seed=seed,
    )


def curriculum_train(
    model: torch.nn.Module,
    n_stages: int = 4,
    epochs_per_stage: int = 10,
    n_train: int = 30,
    n_val: int = 10,
    det_dim: int = 4,
    lr: float = 3e-4,
    device: str = "cpu",
    seed: int = 42,
) -> dict[str, Any]:
    """Train a model through progressive difficulty stages."""
    from prin.temporal_training import TemporalTrainer

    results = {}
    for stage in range(1, n_stages + 1):
        train_ds = curriculum_dataset(stage, n_train, det_dim, seed + stage * 100)
        val_ds = curriculum_dataset(stage, n_val, det_dim, seed + stage * 200)

        trainer = TemporalTrainer(
            model=model,
            lr=lr,
            max_epochs=epochs_per_stage,
            patience=epochs_per_stage,
            device=device,
        )
        tr = trainer.train(train_data=train_ds, val_data=val_ds)

        results[f"stage_{stage}"] = {
            "n_objects": [2, 3, 4, 6][stage - 1],
            "n_frames": [10, 20, 40, 60][stage - 1],
            "final_val_ip": tr.final_val_ip,
            "best_epoch": tr.best_epoch,
            "total_epochs": tr.total_epochs,
            "wall_time_s": tr.wall_time_s,
            "val_ips": tr.val_ips,
        }

    return results


def per_community_order_parameter(
    phase: torch.Tensor,
    community_assignments: list[list[int]],
) -> list[float]:
    """Compute the Kuramoto order parameter r per community."""
    r_values = []
    for indices in community_assignments:
        if not indices:
            r_values.append(0.0)
            continue
        idx_t = torch.tensor(indices, dtype=torch.long, device=phase.device)
        sub_phase = phase[idx_t]
        z = torch.exp(1j * sub_phase.to(torch.complex64))
        r = float(z.mean().abs().item())
        r_values.append(r)
    return r_values
