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
    "bootstrap_ci",
    "chimera_initial_condition",
    "cohens_d",
    "count_flops",
    "create_ablation_model",
    "gaussian_bump_ic",
    "half_sync_half_random_ic",
    "measure_wall_time",
    "seed_stability_analysis",
    "spatial_correlation",
    "train_clevr_n_extended",
    "train_clevr_n_single_seed",
    "welch_t_test",
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
