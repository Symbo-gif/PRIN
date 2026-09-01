"""PRINet 3.0-compatible temporal coherence metrics (``temporal_metrics``).

Year 4 Q1.7 temporal binding metrics for multi-object tracking evaluation:
identity switches, track fragmentation, identity overcount, mostly-tracked /
mostly-lost, track duration, recovery speed, binding robustness, and a
temporal-smoothness (acceleration proxy) over position trajectories.

Faithful port of the PRINet 3.0 reference module (Testing Standards §1.1). Every
metric is host-side list / index bookkeeping over per-transition match tensors
plus one mean-of-L2-norm over a position tensor — the same evaluation-tooling
category as :mod:`prin.nn.mot_evaluation` and :mod:`prin.y4q1_tools` (both
excluded from the ``check_no_python_numerics`` compat-surface scan); the
oscillatory numerics that produce the match tensors live in Rust
(:class:`prin.nn.PhaseTracker` / :class:`prin.nn.TemporalSlotAttentionMOT`).
"""

from __future__ import annotations

from dataclasses import dataclass

from torch import Tensor

__all__ = [
    "TemporalMetrics",
    "binding_robustness_score",
    "compute_full_temporal_metrics",
    "identity_overcount",
    "identity_switches",
    "mostly_tracked_lost",
    "recovery_speed",
    "temporal_smoothness",
    "track_duration_stats",
    "track_fragmentation_rate",
]


@dataclass
class TemporalMetrics:
    """Container for all temporal coherence metrics.

    Attributes:
        ip: Identity Preservation [0, 1].
        idsw: Identity Switch count (total).
        temporal_smoothness: Motion field consistency (lower = smoother).
        track_fragmentation_rate: Fragments per ground-truth object (1.0 = perfect).
        identity_overcount: Unique predicted IDs / ground-truth objects (1.0 = optimal).
        mostly_tracked: Fraction of objects tracked >= 80% of lifetime.
        mostly_lost: Fraction of objects tracked <= 20% of lifetime.
        mean_track_duration: Average frames per maintained identity.
        median_track_duration: Median frames per maintained identity.
        recovery_speed: Mean frames to re-bind after occlusion (NaN if no occlusions).
        binding_robustness: IP_perturbed / IP_baseline (1.0 = no degradation).
    """

    ip: float = 0.0
    idsw: int = 0
    temporal_smoothness: float = 0.0
    track_fragmentation_rate: float = 1.0
    identity_overcount: float = 1.0
    mostly_tracked: float = 0.0
    mostly_lost: float = 0.0
    mean_track_duration: float = 0.0
    median_track_duration: float = 0.0
    recovery_speed: float = float("nan")
    binding_robustness: float = 1.0


def temporal_smoothness(
    positions: Tensor,
) -> float:
    """Compute temporal smoothness of tracked positions.

    Measures motion field consistency between consecutive frames (average L2
    norm of the acceleration). Lower values indicate smoother tracking.

    Args:
        positions: Object positions ``(T, N, 2)`` over T frames, N objects.

    Returns:
        Temporal smoothness value (lower = better).
    """
    if positions.dim() != 3 or positions.shape[-1] < 2:
        raise ValueError(f"Expected positions shape (T, N, 2+), got {positions.shape}")
    T = positions.shape[0]
    if T < 3:
        return 0.0

    velocities = positions[1:] - positions[:-1]  # (T-1, N, 2)
    accel = velocities[1:] - velocities[:-1]  # (T-2, N, 2)
    accel_norm = accel[..., :2].pow(2).sum(dim=-1).sqrt()  # (T-2, N)
    return float(accel_norm.mean().item())


def identity_switches(
    matches_history: list[Tensor],
    n_objects: int,
) -> int:
    """Count total identity switches in a tracking sequence.

    An identity switch occurs when an object matched to predicted-ID ``i`` at
    frame ``t`` becomes matched to predicted-ID ``j != i`` at frame ``t+1``.

    Args:
        matches_history: List of T-1 match tensors, each ``(N,)`` where
            ``matches[i]`` is the predicted ID for ground-truth object ``i``,
            or -1 if unmatched.
        n_objects: Number of ground-truth objects.

    Returns:
        Total identity switch count.
    """
    if len(matches_history) < 2:
        return 0

    switches = 0
    for t in range(1, len(matches_history)):
        prev = matches_history[t - 1]
        curr = matches_history[t]
        n = min(len(prev), len(curr), n_objects)
        for i in range(n):
            p = int(prev[i].item()) if isinstance(prev[i], Tensor) else int(prev[i])
            c = int(curr[i].item()) if isinstance(curr[i], Tensor) else int(curr[i])
            if p >= 0 and c >= 0 and p != c:
                switches += 1
    return switches


def track_fragmentation_rate(
    matches_history: list[Tensor],
    n_objects: int,
) -> float:
    """Compute track fragmentation rate.

    TFR = total_fragments / n_objects. Perfect tracking gives TFR = 1.0 (one
    fragment per object). A fragment is a continuous run of consistent matching.

    Args:
        matches_history: List of T-1 match tensors.
        n_objects: Number of ground-truth objects.

    Returns:
        Track fragmentation rate (>= 1.0).
    """
    if not matches_history or n_objects == 0:
        return 1.0

    total_fragments = 0
    for obj_id in range(n_objects):
        fragments = 0
        in_fragment = False
        for t in range(len(matches_history)):
            m = matches_history[t]
            is_matched = (
                obj_id < len(m)
                and (
                    int(m[obj_id].item())
                    if isinstance(m[obj_id], Tensor)
                    else int(m[obj_id])
                )
                >= 0
            )
            if is_matched and not in_fragment:
                fragments += 1
                in_fragment = True
            elif not is_matched:
                in_fragment = False
        total_fragments += max(fragments, 1)

    return total_fragments / n_objects


def identity_overcount(
    matches_history: list[Tensor],
    n_objects: int,
) -> float:
    """Compute identity overcount ratio.

    IOC = |unique predicted IDs assigned| / n_objects. IOC = 1.0 is optimal;
    IOC > 1.0 means the tracker creates spurious IDs.

    Args:
        matches_history: List of T-1 match tensors.
        n_objects: Number of ground-truth objects.

    Returns:
        Identity overcount ratio (>= 1.0 ideally).
    """
    if not matches_history or n_objects == 0:
        return 1.0

    unique_ids: set[int] = set()
    for m in matches_history:
        for i in range(len(m)):
            val = int(m[i].item()) if isinstance(m[i], Tensor) else int(m[i])
            if val >= 0:
                unique_ids.add(val)

    return len(unique_ids) / max(n_objects, 1)


def mostly_tracked_lost(
    matches_history: list[Tensor],
    n_objects: int,
    tracked_threshold: float = 0.8,
    lost_threshold: float = 0.2,
) -> tuple[float, float]:
    """Compute Mostly Tracked (MT) and Mostly Lost (ML) fractions.

    MT = fraction of objects tracked >= ``tracked_threshold`` of their lifetime.
    ML = fraction of objects tracked <= ``lost_threshold`` of their lifetime.

    Args:
        matches_history: List of T-1 match tensors.
        n_objects: Number of ground-truth objects.
        tracked_threshold: Fraction threshold for "mostly tracked" (default 0.8).
        lost_threshold: Fraction threshold for "mostly lost" (default 0.2).

    Returns:
        Tuple of (MT, ML) fractions in [0, 1].
    """
    if not matches_history or n_objects == 0:
        return 0.0, 1.0

    T = len(matches_history)
    mt_count = 0
    ml_count = 0

    for obj_id in range(n_objects):
        tracked_frames = 0
        for t in range(T):
            m = matches_history[t]
            if obj_id < len(m):
                val = (
                    int(m[obj_id].item())
                    if isinstance(m[obj_id], Tensor)
                    else int(m[obj_id])
                )
                if val >= 0:
                    tracked_frames += 1
        frac = tracked_frames / max(T, 1)
        if frac >= tracked_threshold:
            mt_count += 1
        if frac <= lost_threshold:
            ml_count += 1

    return mt_count / n_objects, ml_count / n_objects


def track_duration_stats(
    matches_history: list[Tensor],
    n_objects: int,
) -> tuple[float, float]:
    """Compute mean and median track duration.

    Track duration = number of consecutive frames where an identity is
    maintained without interruption.

    Args:
        matches_history: List of T-1 match tensors.
        n_objects: Number of ground-truth objects.

    Returns:
        Tuple of (mean_duration, median_duration) in frames.
    """
    if not matches_history or n_objects == 0:
        return 0.0, 0.0

    durations: list[int] = []
    for obj_id in range(n_objects):
        run_length = 0
        prev_match = -1
        for t in range(len(matches_history)):
            m = matches_history[t]
            val = -1
            if obj_id < len(m):
                val = (
                    int(m[obj_id].item())
                    if isinstance(m[obj_id], Tensor)
                    else int(m[obj_id])
                )

            if val >= 0 and (prev_match < 0 or val == prev_match):
                run_length += 1
            else:
                if run_length > 0:
                    durations.append(run_length)
                run_length = 1 if val >= 0 else 0
            prev_match = val

        if run_length > 0:
            durations.append(run_length)

    if not durations:
        return 0.0, 0.0

    mean_dur = sum(durations) / len(durations)
    sorted_dur = sorted(durations)
    n = len(sorted_dur)
    median_dur = (
        sorted_dur[n // 2]
        if n % 2 == 1
        else (sorted_dur[n // 2 - 1] + sorted_dur[n // 2]) / 2.0
    )
    return float(mean_dur), float(median_dur)


def recovery_speed(
    matches_history: list[Tensor],
    occlusion_mask: Tensor,
    n_objects: int,
) -> float:
    """Measure average frames to re-bind after occlusion ends.

    Args:
        matches_history: List of T-1 match tensors.
        occlusion_mask: ``(T, N)`` tensor, 1=visible, 0=occluded.
        n_objects: Number of ground-truth objects.

    Returns:
        Mean recovery speed in frames. NaN if no occlusion events.
    """
    T = occlusion_mask.shape[0]
    recovery_frames: list[int] = []

    for obj_id in range(min(n_objects, occlusion_mask.shape[1])):
        for t in range(1, T):
            was_occluded = occlusion_mask[t - 1, obj_id].item() < 0.5
            is_visible = occlusion_mask[t, obj_id].item() >= 0.5

            if was_occluded and is_visible:
                frames_to_rebind = 0
                for t2 in range(t - 1, min(len(matches_history), T)):
                    m = matches_history[t2]
                    val = -1
                    if obj_id < len(m):
                        val = (
                            int(m[obj_id].item())
                            if isinstance(m[obj_id], Tensor)
                            else int(m[obj_id])
                        )
                    frames_to_rebind += 1
                    if val >= 0:
                        break
                recovery_frames.append(frames_to_rebind)

    if not recovery_frames:
        return float("nan")

    return sum(recovery_frames) / len(recovery_frames)


def binding_robustness_score(
    ip_perturbed: float,
    ip_baseline: float,
) -> float:
    """Compute binding robustness score.

    BRS = IP_perturbed / IP_baseline. 1.0 = no degradation.

    Args:
        ip_perturbed: Identity preservation under perturbation.
        ip_baseline: Identity preservation at baseline (no perturbation).

    Returns:
        Binding robustness score in [0, inf). 1.0 = no degradation.
    """
    if ip_baseline <= 0:
        return 0.0
    return ip_perturbed / ip_baseline


def compute_full_temporal_metrics(
    matches_history: list[Tensor],
    n_objects: int,
    positions: Tensor | None = None,
    occlusion_mask: Tensor | None = None,
    ip_baseline: float | None = None,
) -> TemporalMetrics:
    """Compute all temporal coherence metrics in one call.

    Args:
        matches_history: List of T-1 match tensors.
        n_objects: Number of ground-truth objects.
        positions: Optional ``(T, N, 2)`` position tensor for smoothness.
        occlusion_mask: Optional ``(T, N)`` occlusion mask for recovery speed.
        ip_baseline: Baseline IP for BRS computation.

    Returns:
        :class:`TemporalMetrics` with all metrics populated.
    """
    total_matched = 0
    total_possible = 0
    for m in matches_history:
        n = min(len(m), n_objects)
        matched = sum(
            1
            for i in range(n)
            if (int(m[i].item()) if isinstance(m[i], Tensor) else int(m[i])) >= 0
        )
        total_matched += matched
        total_possible += n
    ip = total_matched / max(total_possible, 1)

    idsw = identity_switches(matches_history, n_objects)
    tfr = track_fragmentation_rate(matches_history, n_objects)
    ioc = identity_overcount(matches_history, n_objects)
    mt, ml = mostly_tracked_lost(matches_history, n_objects)
    mean_dur, median_dur = track_duration_stats(matches_history, n_objects)

    ts = 0.0
    if positions is not None:
        ts = temporal_smoothness(positions)

    rs = float("nan")
    if occlusion_mask is not None:
        rs = recovery_speed(matches_history, occlusion_mask, n_objects)

    brs = 1.0
    if ip_baseline is not None and ip_baseline > 0:
        brs = binding_robustness_score(ip, ip_baseline)

    return TemporalMetrics(
        ip=ip,
        idsw=idsw,
        temporal_smoothness=ts,
        track_fragmentation_rate=tfr,
        identity_overcount=ioc,
        mostly_tracked=mt,
        mostly_lost=ml,
        mean_track_duration=mean_dur,
        median_track_duration=median_dur,
        recovery_speed=rs,
        binding_robustness=brs,
    )
