"""PRINet 3.0-compatible Year 4 Q1 experiment utilities.

This module provides the PRINet 3.0 ``prinet.utils.y4q1_tools`` public API
as a mix of real data containers / profiling utilities and documented D-2.2
stubs. Dataclasses (``AblationConfig``, ``ExtendedTrainingResult``) and
profiling helpers (``count_flops``, ``measure_wall_time``) are real
implementations. Training loops and model constructors requiring Python
numerics receive typed D-2.2 dispositions.

No numerical computation is introduced (Coding Standards Sec. 1.2).
"""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import Any, NoReturn

__all__ = [
    "AblationConfig",
    "AblationHybridPRINetV2",
    "ExtendedTrainingResult",
    "count_flops",
    "create_ablation_model",
    "measure_wall_time",
    "train_clevr_n_extended",
    "train_clevr_n_single_seed",
]


@dataclass
class AblationConfig:
    """Configuration for HybridPRINetV2 ablation variants.

    Attributes:
        variant: One of ``"full"``, ``"attention_only"``,
            ``"oscillator_only"``, ``"shared_phase"``.
        n_input: Input dimension.
        n_classes: Number of classes.
        d_model: Model dimension.
        n_heads: Attention heads.
        n_layers: Number of layers.
        n_delta: Delta-band oscillators.
        n_theta: Theta-band oscillators.
        n_gamma: Gamma-band oscillators.
        n_discrete_steps: Dynamics steps per layer.
        coupling_strength: Coupling *K*.
        pac_depth: PAC modulation depth.
        dropout: Dropout rate.
    """

    variant: str = "full"
    n_input: int = 256
    n_classes: int = 10
    d_model: int = 64
    n_heads: int = 4
    n_layers: int = 2
    n_delta: int = 4
    n_theta: int = 8
    n_gamma: int = 32
    n_discrete_steps: int = 5
    coupling_strength: float = 2.0
    pac_depth: float = 0.3
    dropout: float = 0.1


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


def _raise_disposition(symbol: str, detail: str) -> NoReturn:
    """Raise the typed D-2.2 disposition error."""
    raise NotImplementedError(
        f"{symbol} is a deferred-rebuild symbol (WP-036 D-2.2). {detail} "
        "See the Migration Guide for the disposition and the owning WP."
    )


class AblationHybridPRINetV2:
    """Deferred-rebuild stub for the ablation HybridPRINetV2 variant.

    Trainable ``nn.Module`` with ``nn.Linear`` projections. Needs a
    trainable-layer rebuild (same disposition class as the hybrid-model
    family).

    Raises:
        NotImplementedError: Always on construction.
    """

    def __init__(self, *_args: Any, **_kwargs: Any) -> None:
        """Raise the D-2.2 disposition."""
        _raise_disposition(
            "AblationHybridPRINetV2",
            "Trainable nn.Module with nn.Linear projections; needs rebuild.",
        )


def create_ablation_model(*_args: Any, **_kwargs: Any) -> NoReturn:
    """Reject calls to the deferred ablation model constructor.

    Raises:
        NotImplementedError: Always. Constructs trainable nn.Module variants.
    """
    _raise_disposition(
        "create_ablation_model",
        "Constructs trainable nn.Module ablation variants.",
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
