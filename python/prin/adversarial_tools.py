"""PRINet 3.0-compatible adversarial attack utilities (``adversarial_tools``).

FGSM and PGD attacks on input detection features for evaluating the adversarial
robustness of :class:`~prin.nn.temporal_compat.PhaseTracker` vs.
:class:`~prin.nn.temporal_compat.TemporalSlotAttentionMOT`.

Faithful port (Testing Standards §1.1). Pure ``torch.autograd`` orchestration
over the tracker models' own ``forward``/``track_sequence`` — the same
benchmark/experiment-tooling category as :mod:`prin.y4q1_tools` (excluded from
the ``check_no_python_numerics`` compat-surface scan). Attacks that need a
gradient path from ``sim`` back to ``dets_t`` exercise the non-differentiable
Rust ``DiscreteDeltaThetaGamma.integrate`` boundary — see the 0144M7 handoff.

References:
    - Goodfellow et al. (2015), "Explaining and Harnessing Adversarial Examples"
    - Madry et al. (2018), "Towards Deep Learning Models Resistant to Adversarial
      Attacks"
"""

from __future__ import annotations

from typing import Any

import torch
import torch.nn as nn
import torch.nn.functional as F
from torch import Tensor

__all__ = [
    "adversarial_comparison",
    "adversarial_evaluate",
    "fgsm_attack",
    "pgd_attack",
]


def fgsm_attack(
    model: nn.Module,
    dets_t: Tensor,
    dets_t1: Tensor,
    n_objects: int,
    epsilon: float,
    loss_fn: object | None = None,
) -> Tensor:
    """Fast Gradient Sign Method (FGSM) attack on ``dets_t``.

    Args:
        model: Tracker with a ``forward(dets_t, dets_t1)`` interface.
        dets_t: Frame t detections ``(N, D)``.
        dets_t1: Frame t+1 detections ``(N, D)``.
        n_objects: Number of ground-truth objects.
        epsilon: Perturbation magnitude (L-inf bound).
        loss_fn: Unused; retained for API parity.

    Returns:
        Perturbed detections ``(N, D)``.
    """
    model.eval()
    dets_t_adv = dets_t.clone().detach().requires_grad_(True)

    _, sim = model(dets_t_adv, dets_t1)
    N = min(sim.shape[0], sim.shape[1], n_objects)
    if N == 0:
        return dets_t.clone()

    sim_block = sim[:N, :N]
    target = torch.arange(N, device=sim.device)
    loss = F.cross_entropy(sim_block / 0.1, target)
    loss.backward()  # type: ignore[no-untyped-call, unused-ignore]

    if dets_t_adv.grad is None:
        return dets_t.clone()

    perturbation = epsilon * dets_t_adv.grad.sign()
    perturbed = (dets_t + perturbation).detach()
    return perturbed


def pgd_attack(
    model: nn.Module,
    dets_t: Tensor,
    dets_t1: Tensor,
    n_objects: int,
    epsilon: float,
    alpha: float | None = None,
    steps: int = 20,
    random_start: bool = True,
    seed: int = 42,
) -> Tensor:
    """Projected Gradient Descent (PGD) attack on ``dets_t``.

    Iteratively perturbs ``dets_t`` to maximize tracking loss, projecting back
    to the epsilon-ball each step.

    Args:
        model: Tracker with a ``forward(dets_t, dets_t1)`` interface.
        dets_t: Frame t detections ``(N, D)``.
        dets_t1: Frame t+1 detections ``(N, D)``.
        n_objects: Number of ground-truth objects.
        epsilon: Perturbation magnitude (L-inf bound).
        alpha: Step size per iteration. Defaults to ``epsilon / 4``.
        steps: Number of PGD steps.
        random_start: Initialize with a random perturbation.
        seed: Random seed for the random start.

    Returns:
        Perturbed detections ``(N, D)``.
    """
    if alpha is None:
        alpha = epsilon / 4.0

    model.eval()
    dets_orig = dets_t.clone().detach()

    if random_start:
        gen = torch.Generator(device=dets_t.device)
        gen.manual_seed(seed)
        delta = torch.empty_like(dets_t).uniform_(-epsilon, epsilon)
    else:
        delta = torch.zeros_like(dets_t)

    for _ in range(steps):
        dets_adv = (dets_orig + delta).requires_grad_(True)
        _, sim = model(dets_adv, dets_t1)
        N = min(sim.shape[0], sim.shape[1], n_objects)
        if N == 0:
            break

        sim_block = sim[:N, :N]
        target = torch.arange(N, device=sim.device)
        loss = F.cross_entropy(sim_block / 0.1, target)
        loss.backward()  # type: ignore[no-untyped-call, unused-ignore]

        if dets_adv.grad is None:
            break

        delta = delta + alpha * dets_adv.grad.sign()
        delta = delta.clamp(-epsilon, epsilon)
        delta = delta.detach()

    return (dets_orig + delta).detach()


def adversarial_evaluate(
    model: nn.Module,
    dataset: list[Any],
    epsilon: float,
    attack_fn: str = "fgsm",
    pgd_steps: int = 20,
    seed: int = 42,
) -> dict[str, Any]:
    """Evaluate identity preservation under an adversarial attack.

    Returns a dict with ``clean_ip``, ``adv_ip``, ``degradation``,
    ``per_seq_clean``, ``per_seq_adv``.
    """
    model.eval()
    clean_ips = []
    adv_ips = []
    dyn_model: Any = model

    for i, seq in enumerate(dataset):
        frames = [f.to(next(model.parameters()).device) for f in seq.frames]

        with torch.no_grad():
            result = dyn_model.track_sequence(frames)
            clean_ips.append(result["identity_preservation"])

        adv_frames = []
        for t in range(len(frames)):
            if t == 0:
                adv_frames.append(frames[t])
                continue
            if attack_fn == "fgsm":
                adv_f = fgsm_attack(
                    model, frames[t - 1], frames[t], seq.n_objects, epsilon
                )
            else:
                adv_f = pgd_attack(
                    model,
                    frames[t - 1],
                    frames[t],
                    seq.n_objects,
                    epsilon,
                    steps=pgd_steps,
                    seed=seed + i * 100 + t,
                )
            adv_frames.append(adv_f)

        with torch.no_grad():
            adv_result = dyn_model.track_sequence(adv_frames)
            adv_ips.append(adv_result["identity_preservation"])

    import numpy as np

    clean_arr = np.array(clean_ips)
    adv_arr = np.array(adv_ips)

    return {
        "clean_ip": float(clean_arr.mean()),
        "adv_ip": float(adv_arr.mean()),
        "degradation": float(clean_arr.mean() - adv_arr.mean()),
        "per_seq_clean": clean_ips,
        "per_seq_adv": adv_ips,
    }


def adversarial_comparison(
    pt_model: nn.Module,
    sa_model: nn.Module,
    dataset: list[Any],
    epsilons: list[float],
    attack_types: list[str],
    pgd_steps: int = 20,
    seed: int = 42,
) -> dict[str, Any]:
    """Side-by-side adversarial robustness comparison for two models."""
    results: dict[str, Any] = {}
    for attack in attack_types:
        results[attack] = {}
        for eps in epsilons:
            pt_res = adversarial_evaluate(
                pt_model, dataset, eps, attack, pgd_steps, seed
            )
            sa_res = adversarial_evaluate(
                sa_model, dataset, eps, attack, pgd_steps, seed
            )
            results[attack][str(eps)] = {
                "epsilon": eps,
                "pt_clean_ip": pt_res["clean_ip"],
                "pt_adv_ip": pt_res["adv_ip"],
                "pt_degradation": pt_res["degradation"],
                "sa_clean_ip": sa_res["clean_ip"],
                "sa_adv_ip": sa_res["adv_ip"],
                "sa_degradation": sa_res["degradation"],
            }
    return results
