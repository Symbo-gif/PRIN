"""Typed ``torch.profiler`` integration for PRIN training-loop analysis.

The profiler produces the legacy :class:`ProfileReport` shape and Chrome trace
name.  :meth:`PRINetProfiler.record_function` provides the explicit labeling
boundary used to make Rust-backed operations visible in torch traces; this
module performs no model numerics of its own.
"""

from __future__ import annotations

import math
import tempfile
import time
from collections.abc import Callable, Iterable
from contextlib import AbstractContextManager
from dataclasses import dataclass, field
from pathlib import Path
from types import TracebackType
from typing import Any, Protocol, cast

import torch
from torch import Tensor, nn

from prin.reporting._artifacts import ReportingError

_REPO_ROOT = Path(__file__).resolve().parents[3]
_ALLOWED_OUTPUT_ROOTS = (
    (_REPO_ROOT / "benchmarks" / "results").resolve(),
    (_REPO_ROOT / "DOCS" / "test_and_benchmark_results").resolve(),
    Path(tempfile.gettempdir()).resolve(),
)

__all__ = [
    "PRINetProfiler",
    "ProfileReport",
    "ProfilerConfigurationError",
    "ProfilerStateError",
    "ReportingError",
    "profile_training_loop",
]


class ProfilerConfigurationError(ReportingError, ValueError):
    """Raised when profiler configuration or training input is invalid."""


class ProfilerStateError(ReportingError, RuntimeError):
    """Raised when a profiler operation is invalid in its current lifecycle."""


class _TorchProfile(Protocol):
    """Typed subset of the dynamically typed torch profiler object."""

    def __enter__(self) -> object:
        """Start the underlying profile context."""

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc_value: BaseException | None,
        traceback: TracebackType | None,
    ) -> object:
        """Stop the underlying profile context."""

    def step(self) -> None:
        """Advance the profiler schedule."""

    def key_averages(self) -> list[Any]:
        """Return aggregated operator events."""

    def export_chrome_trace(self, path: str) -> None:
        """Export a Chrome-compatible trace."""


@dataclass
class ProfileReport:
    """Structured summary of a completed profiling run.

    Args:
        total_wall_ms: Total measured host wall time in milliseconds.
        n_steps: Number of active (non-warmup) steps configured.
        avg_step_ms: Average host wall time per active step in milliseconds.
        top_ops: ``(name, self_cpu_ms, self_device_ms)`` rows sorted by total
            self time descending. The third value retains the legacy
            ``self_cuda_ms`` meaning on CUDA and is zero for CPU-only events.
        top_ops_table: Plain-text rendering of ``top_ops``.
        bottleneck_op: Name of the most expensive included operator, or empty.
        json_trace_path: Chrome-trace path, or ``None`` when export is disabled.
        raw: JSON-compatible timing summary for downstream consumers.

    Raises:
        ProfilerConfigurationError: If a numeric field or operation row is
            invalid.
    """

    total_wall_ms: float = 0.0
    n_steps: int = 0
    avg_step_ms: float = 0.0
    top_ops: list[tuple[str, float, float]] = field(default_factory=list)
    top_ops_table: str = ""
    bottleneck_op: str = ""
    json_trace_path: str | None = None
    raw: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        """Validate report values created through the public constructor."""
        _validate_nonnegative_finite(self.total_wall_ms, "total_wall_ms")
        _validate_nonnegative_int(self.n_steps, "n_steps", allow_zero=True)
        _validate_nonnegative_finite(self.avg_step_ms, "avg_step_ms")
        for index, row in enumerate(self.top_ops):
            if not isinstance(row, tuple) or len(row) != 3 or not row[0]:
                raise ProfilerConfigurationError(
                    f"top_ops[{index}] must be a non-empty "
                    "(name, cpu_ms, device_ms) tuple"
                )
            _validate_nonnegative_finite(row[1], f"top_ops[{index}].cpu_ms")
            _validate_nonnegative_finite(row[2], f"top_ops[{index}].device_ms")


class PRINetProfiler:
    """Context-manager wrapper around :class:`torch.profiler.profile`.

    Args:
        out_dir: Optional Chrome-trace directory. It must resolve below
            ``benchmarks/results/``, ``DOCS/test_and_benchmark_results/``, or
            the operating-system temporary directory.
        warmup_steps: Number of initial scheduled profiler steps excluded from
            aggregates. Must be a non-negative integer.
        active_steps: Number of profiler steps recorded. Must be positive.
        record_shapes: Whether torch records tensor shapes.
        profile_memory: Whether torch records tensor allocations.
        with_flops: Whether torch estimates operator FLOPs.

    Raises:
        ProfilerConfigurationError: If any configuration value is invalid or
            ``out_dir`` escapes the declared roots.

    Examples:
        >>> profiler = PRINetProfiler(out_dir=None, warmup_steps=0, active_steps=1)
        >>> with profiler:
        ...     with profiler.record_function("prin::rust_step"):
        ...         _ = torch.ones(1) + 1
        ...     profiler.step()
        >>> profiler.report(top_n=1).n_steps
        1
    """

    def __init__(
        self,
        out_dir: str | Path | None = None,
        warmup_steps: int = 2,
        active_steps: int = 20,
        record_shapes: bool = True,
        profile_memory: bool = False,
        with_flops: bool = False,
    ) -> None:
        """Validate and store profiling configuration."""
        _validate_nonnegative_int(warmup_steps, "warmup_steps", allow_zero=True)
        _validate_nonnegative_int(active_steps, "active_steps", allow_zero=False)
        for name, value in (
            ("record_shapes", record_shapes),
            ("profile_memory", profile_memory),
            ("with_flops", with_flops),
        ):
            if not isinstance(value, bool):
                raise ProfilerConfigurationError(
                    f"{name} must be bool, got {type(value).__name__}"
                )
        self.out_dir = _validate_output_dir(out_dir) if out_dir is not None else None
        self.warmup_steps = warmup_steps
        self.active_steps = active_steps
        self.record_shapes = record_shapes
        self.profile_memory = profile_memory
        self.with_flops = with_flops
        self._prof: _TorchProfile | None = None
        self._start_wall = 0.0
        self._end_wall = 0.0
        self._state = "new"

    def __enter__(self) -> PRINetProfiler:
        """Start the configured torch profiler.

        Returns:
            This profiler instance.

        Raises:
            ProfilerStateError: If this instance has already been entered.
        """
        if self._state != "new":
            raise ProfilerStateError("profiler has already been entered")
        activities = [torch.profiler.ProfilerActivity.CPU]
        if torch.cuda.is_available():
            activities.append(torch.profiler.ProfilerActivity.CUDA)
        schedule = torch.profiler.schedule(
            wait=0,
            warmup=self.warmup_steps,
            active=self.active_steps,
            repeat=1,
        )
        self._prof = cast(
            _TorchProfile,
            torch.profiler.profile(
                activities=activities,
                schedule=schedule,
                record_shapes=self.record_shapes,
                profile_memory=self.profile_memory,
                with_flops=self.with_flops,
            ),
        )
        self._prof.__enter__()
        self._start_wall = time.perf_counter()
        self._state = "active"
        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc_value: BaseException | None,
        traceback: TracebackType | None,
    ) -> bool | None:
        """Stop profiling and preserve exception propagation.

        Args:
            exc_type: Active exception type, if any.
            exc_value: Active exception instance, if any.
            traceback: Active exception traceback, if any.

        Returns:
            ``None`` so exceptions raised inside the context are not suppressed.
        """
        if self._state != "active" or self._prof is None:
            raise ProfilerStateError("profiler context is not active")
        if torch.cuda.is_available():
            torch.cuda.synchronize()
        self._end_wall = time.perf_counter()
        try:
            self._prof.__exit__(exc_type, exc_value, traceback)
        finally:
            self._state = "completed"
        return None

    def step(self) -> None:
        """Signal that one warmup or active training step has completed.

        Raises:
            ProfilerStateError: If called outside the active context.
        """
        if self._state != "active" or self._prof is None:
            raise ProfilerStateError("profiler must be entered before step()")
        self._prof.step()

    def record_function(self, label: str) -> AbstractContextManager[None]:
        """Label an operation, including a Rust-backed call, in torch traces.

        The returned context has the same semantics as
        :func:`torch.profiler.record_function`. Place the Python-to-Rust call
        inside it so the label is visible in Chrome traces and key averages.

        Args:
            label: Non-empty, single-line trace label.

        Returns:
            A context manager delimiting the labeled operation.

        Raises:
            ProfilerConfigurationError: If ``label`` is invalid.
            ProfilerStateError: If the profiler context is not active.
        """
        if (
            not isinstance(label, str)
            or not label.strip()
            or "\n" in label
            or "\r" in label
        ):
            raise ProfilerConfigurationError(
                "label must be a non-empty single-line string"
            )
        if self._state != "active":
            raise ProfilerStateError(
                "profiler must be entered before record_function()"
            )
        context = torch.profiler.record_function(label.strip())
        return cast(AbstractContextManager[None], context)

    def report(self, top_n: int = 20) -> ProfileReport:
        """Build a structured report from a completed profile.

        Args:
            top_n: Positive number of highest-self-time operators to include.

        Returns:
            A populated :class:`ProfileReport`.

        Raises:
            ProfilerConfigurationError: If ``top_n`` is not positive.
            ProfilerStateError: If profiling has not completed.
            OSError: If an allowed Chrome-trace destination cannot be written.
        """
        _validate_nonnegative_int(top_n, "top_n", allow_zero=False)
        if self._state != "completed" or self._prof is None:
            raise ProfilerStateError("profile must be completed before report()")

        total_wall_ms = max((self._end_wall - self._start_wall) * 1000.0, 0.0)
        events = sorted(
            self._prof.key_averages(),
            key=_event_total_self_time,
            reverse=True,
        )[:top_n]
        top_ops: list[tuple[str, float, float]] = []
        lines = [f"{'Op':<55} {'CPU ms':>10} {'CUDA ms':>10}", "-" * 78]
        for event in events:
            name = str(event.key)
            cpu_ms = _event_numeric_attribute(event, "self_cpu_time_total") / 1000.0
            device_us = _event_numeric_attribute(event, "self_device_time_total")
            top_ops.append((name, cpu_ms, device_us / 1000.0))
            lines.append(f"{name:<55} {cpu_ms:>10.3f} {device_us / 1000.0:>10.3f}")

        trace_path: str | None = None
        if self.out_dir is not None:
            self.out_dir.mkdir(parents=True, exist_ok=True)
            trace_file = self.out_dir / "prinet_trace.json"
            self._prof.export_chrome_trace(str(trace_file))
            trace_path = str(trace_file)

        avg_step_ms = total_wall_ms / self.active_steps
        raw: dict[str, Any] = {
            "total_wall_ms": total_wall_ms,
            "n_steps": self.active_steps,
            "avg_step_ms": avg_step_ms,
            "top_ops": [
                {"op": name, "cpu_ms": cpu_ms, "cuda_ms": device_ms}
                for name, cpu_ms, device_ms in top_ops
            ],
        }
        return ProfileReport(
            total_wall_ms=total_wall_ms,
            n_steps=self.active_steps,
            avg_step_ms=avg_step_ms,
            top_ops=top_ops,
            top_ops_table="\n".join(lines),
            bottleneck_op=top_ops[0][0] if top_ops else "",
            json_trace_path=trace_path,
            raw=raw,
        )


def profile_training_loop(
    model: nn.Module,
    dataloader: Iterable[tuple[Tensor, Tensor]],
    n_steps: int = 50,
    out_dir: str | Path | None = None,
    warmup_steps: int = 5,
    device: torch.device | None = None,
    loss_fn: Callable[[Tensor, Tensor], Tensor] | None = None,
    top_n: int = 20,
) -> ProfileReport:
    """Profile deterministic forward and optional backward training steps.

    The caller owns model initialization, optimizer behavior, and random seed.
    This helper does not sample data or mutate any random-number generator. A
    finite dataloader is restarted as needed to supply configured warmup steps,
    preserving PRINet 3.0 behavior.

    Args:
        model: Torch module to profile.
        dataloader: Re-iterable batches of exactly ``(inputs, labels)`` tensors.
        n_steps: Positive maximum number of active steps.
        out_dir: Optional confined Chrome-trace directory.
        warmup_steps: Non-negative number of excluded warmup steps.
        device: Explicit torch device, or ``None`` to select CUDA when available.
        loss_fn: Optional callable returning a scalar tensor. When supplied,
            ``backward()`` is included in the profile.
        top_n: Positive number of operators included in the report.

    Returns:
        A completed :class:`ProfileReport`.

    Raises:
        ProfilerConfigurationError: If configuration, dataloader, or a batch is
            invalid.
        OSError: If an allowed Chrome-trace destination cannot be written.
    """
    if not isinstance(model, nn.Module):
        raise ProfilerConfigurationError("model must be a torch.nn.Module")
    _validate_nonnegative_int(n_steps, "n_steps", allow_zero=False)
    _validate_nonnegative_int(warmup_steps, "warmup_steps", allow_zero=True)
    _validate_nonnegative_int(top_n, "top_n", allow_zero=False)
    if loss_fn is not None and not callable(loss_fn):
        raise ProfilerConfigurationError("loss_fn must be callable or None")
    if device is not None and not isinstance(device, torch.device):
        raise ProfilerConfigurationError("device must be torch.device or None")
    try:
        iterator = iter(dataloader)
    except TypeError as exc:
        raise ProfilerConfigurationError("dataloader must be iterable") from exc

    active_steps = n_steps
    if hasattr(dataloader, "__len__"):
        try:
            available = len(dataloader)  # type: ignore[arg-type]
        except (TypeError, ValueError, OverflowError) as exc:
            raise ProfilerConfigurationError("dataloader length is invalid") from exc
        if available <= 0:
            raise ProfilerConfigurationError("dataloader provides no batches")
        active_steps = min(n_steps, available)

    selected_device = device or torch.device(
        "cuda" if torch.cuda.is_available() else "cpu"
    )
    model = model.to(selected_device)
    model.train()
    profiler = PRINetProfiler(
        out_dir=out_dir,
        warmup_steps=warmup_steps,
        active_steps=active_steps,
        record_shapes=True,
        profile_memory=False,
    )

    with profiler:
        for _ in range(warmup_steps + active_steps):
            try:
                batch = next(iterator)
            except StopIteration:
                iterator = iter(dataloader)
                try:
                    batch = next(iterator)
                except StopIteration as exc:
                    raise ProfilerConfigurationError(
                        "dataloader provides no batches when restarted"
                    ) from exc
            inputs, labels = _validate_batch(batch)
            inputs = inputs.to(selected_device, non_blocking=True)
            labels = labels.to(selected_device, non_blocking=True)
            with torch.autocast(
                device_type=selected_device.type,
                dtype=torch.float16,
                enabled=selected_device.type == "cuda",
            ):
                logits = model(inputs)
                if loss_fn is not None:
                    loss = loss_fn(logits, labels)
                    if not isinstance(loss, Tensor) or loss.numel() != 1:
                        raise ProfilerConfigurationError(
                            "loss_fn must return a scalar torch.Tensor"
                        )
                    backward = cast(Callable[[], None], loss.backward)
                    backward()
            profiler.step()
    return profiler.report(top_n=top_n)


def _validate_nonnegative_int(value: int, name: str, *, allow_zero: bool) -> None:
    """Validate an integer count."""
    valid = isinstance(value, int) and not isinstance(value, bool)
    valid = valid and (value >= 0 if allow_zero else value > 0)
    if not valid:
        qualifier = "non-negative" if allow_zero else "positive"
        raise ProfilerConfigurationError(
            f"{name} must be a {qualifier} integer, got {value!r}"
        )


def _validate_nonnegative_finite(value: float, name: str) -> None:
    """Validate a finite non-negative timing value."""
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ProfilerConfigurationError(f"{name} must be a finite non-negative number")
    if not math.isfinite(float(value)) or value < 0:
        raise ProfilerConfigurationError(f"{name} must be a finite non-negative number")


def _validate_output_dir(value: str | Path) -> Path:
    """Resolve and confine a profiler output directory."""
    if not isinstance(value, (str, Path)):
        raise ProfilerConfigurationError(
            f"out_dir must be a string or Path, got {type(value).__name__}"
        )
    if isinstance(value, str) and not value.strip():
        raise ProfilerConfigurationError("out_dir must not be empty")
    resolved = Path(value).resolve()
    if any(
        resolved == root or root in resolved.parents for root in _ALLOWED_OUTPUT_ROOTS
    ):
        return resolved
    raise ProfilerConfigurationError(
        f"out_dir resolves outside the declared output roots: {resolved}"
    )


def _event_numeric_attribute(event: Any, attribute: str) -> float:
    """Read a dynamic torch profiler event timing as a safe float."""
    value = getattr(event, attribute, 0.0)
    if isinstance(value, (int, float)) and math.isfinite(float(value)):
        return max(float(value), 0.0)
    return 0.0


def _event_total_self_time(event: Any) -> float:
    """Return combined CPU/device self time for sorting profiler events."""
    return _event_numeric_attribute(
        event, "self_cpu_time_total"
    ) + _event_numeric_attribute(event, "self_device_time_total")


def _validate_batch(batch: object) -> tuple[Tensor, Tensor]:
    """Require a two-tensor training batch."""
    if not isinstance(batch, (tuple, list)) or len(batch) != 2:
        raise ProfilerConfigurationError(
            "each dataloader batch must contain exactly two tensors"
        )
    inputs, labels = batch
    if not isinstance(inputs, Tensor) or not isinstance(labels, Tensor):
        raise ProfilerConfigurationError(
            "each dataloader batch must contain exactly two tensors"
        )
    return inputs, labels
