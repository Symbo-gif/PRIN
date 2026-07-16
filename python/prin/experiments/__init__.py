"""Experiment frameworks: ablation, statistics, adversarial, fair training.

Coherent reorganization of PRINet 3.0 ``utils/{temporal_training,
adversarial_tools, y4q1_tools}.py`` into ``experiments.ablation``,
``experiments.stats`` (multi-seed bootstrap CIs, Welch t-tests),
``experiments.adversarial`` (FGSM/PGD), and the fair PT-vs-SA training
framework (identical loss/optimizer/augmentation/parameter budgets). Hot loops
(Hungarian similarity loss, metric computation) call the Rust core.
Implemented during Phase 5.
"""

from __future__ import annotations

__all__: list[str] = []
