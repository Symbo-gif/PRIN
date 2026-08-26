"""Training throughput: wall time and epochs/sec for the Rust-native
`PhaseTracker` training loop at a fixed small problem size.

Rust-backed successor to PRINet 3.0's `mnist_subset.py`, `q2_benchmarks.py`,
and `scalr_vs_adam_benchmark.py`'s throughput measurements. All Adam updates,
learning-rate scheduling, gradient clipping, and dataset generation run in
`crates/prin-train`; this module only times the call.
"""

from __future__ import annotations

from typing import Any

from prin.train import train_phase_tracker

from benchmarks._common.config import BenchmarkConfig
from benchmarks._common.registry import register
from benchmarks._common.timing import timed_run

_DEFAULT_DETECTION_DIM = 4
_DEFAULT_TRAIN_SEQS = 4
_DEFAULT_VAL_SEQS = 2
_DEFAULT_N_FRAMES = 5
_DEFAULT_MAX_EPOCHS = 2


@register(
    "training",
    "throughput",
    summary="Wall time and epochs/sec for the Rust-native PhaseTracker training loop",
)
def training_throughput(config: BenchmarkConfig) -> dict[str, Any]:
    """Time :func:`prin.train.train_phase_tracker` at a fixed small problem size.

    ``config.params`` may override ``detection_dim``, ``train_seqs``,
    ``val_seqs``, ``n_frames``, and ``max_epochs``. Kept small by default so
    the *shape* of the measurement (schema, timing rule) is exercised
    quickly; production-scale throughput numbers are future campaign work
    (Non-goal: drawing conclusions from final measurements).
    """
    detection_dim = int(config.params.get("detection_dim", _DEFAULT_DETECTION_DIM))
    train_seqs = int(config.params.get("train_seqs", _DEFAULT_TRAIN_SEQS))
    val_seqs = int(config.params.get("val_seqs", _DEFAULT_VAL_SEQS))
    n_frames = int(config.params.get("n_frames", _DEFAULT_N_FRAMES))
    max_epochs = int(config.params.get("max_epochs", _DEFAULT_MAX_EPOCHS))
    seed = config.seed_counter

    def _run() -> Any:
        _tracker, result = train_phase_tracker(
            detection_dim,
            det_dim=detection_dim,
            n_frames=n_frames,
            train_seqs=train_seqs,
            val_seqs=val_seqs,
            dataset_seed=seed,
            max_epochs=max_epochs,
            patience=max_epochs,
            warmup_epochs=1,
            model_seed=seed,
        )
        return result

    stats, result = timed_run(_run, iterations=config.iterations, warmup=config.warmup)
    epochs_per_sec = (
        result.total_epochs / stats.median_s if stats.median_s > 0 else float("inf")
    )

    return {
        "benchmark": "training_throughput",
        "backend": "host CPU",
        "dtype": "f64",
        "detection_dim": detection_dim,
        "train_seqs": train_seqs,
        "val_seqs": val_seqs,
        "n_frames": n_frames,
        "max_epochs": max_epochs,
        "total_epochs": result.total_epochs,
        "final_train_loss": result.final_train_loss,
        "final_val_ip": result.final_val_ip,
        "epochs_per_sec": epochs_per_sec,
        "timing": stats.to_dict(),
    }
