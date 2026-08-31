"""Phase-1 statistical utilities restored for PRIN acceptance compatibility.

These post-hoc statistics are experiment tooling rather than oscillator
numerics. They intentionally remain in Python and use deterministic inputs.
"""

from __future__ import annotations

import math
from typing import Any

from scipy import integrate


def cliffs_delta(group_a: list[float], group_b: list[float]) -> float:
    """Compute non-parametric Cliff's delta for two non-empty groups."""
    if not group_a or not group_b:
        raise ValueError("Both groups must be non-empty for Cliff's delta.")
    more = sum(a > b for a in group_a for b in group_b)
    less = sum(a < b for a in group_a for b in group_b)
    return (more - less) / (len(group_a) * len(group_b))


def cliffs_delta_interpretation(delta: float) -> str:
    """Interpret Cliff's delta using Romano et al. thresholds."""
    magnitude = abs(delta)
    if magnitude < 0.147:
        return "negligible"
    if magnitude < 0.33:
        return "small"
    if magnitude < 0.474:
        return "medium"
    return "large"


def holm_bonferroni(p_values: list[float], alpha: float = 0.05) -> list[dict[str, Any]]:
    """Apply Holm-Bonferroni step-down correction in original input order."""
    indexed = sorted(enumerate(p_values), key=lambda item: item[1])
    adjusted = [
        p_value * (len(indexed) - rank) for rank, (_, p_value) in enumerate(indexed)
    ]
    for index in range(1, len(adjusted)):
        adjusted[index] = max(adjusted[index], adjusted[index - 1])
    output: list[dict[str, Any]] = [{} for _ in p_values]
    rejecting = True
    for rank, (original_index, p_value) in enumerate(indexed):
        adjusted_p = min(adjusted[rank], 1.0)
        reject = rejecting and adjusted_p <= alpha
        if not reject:
            rejecting = False
        output[original_index] = {
            "original_index": original_index,
            "uncorrected_p": p_value,
            "adjusted_p": adjusted_p,
            "reject_H0": reject,
            "rank": rank + 1,
        }
    return output


def _jeffreys_bayes_factor_t(
    t_stat: float, n_a: int, n_b: int, r: float = 0.7071
) -> float:
    """Approximate the JZS two-sample t-test Bayes factor by quadrature."""
    degrees = n_a + n_b - 2
    effective_n = (n_a * n_b) / (n_a + n_b)

    def integrand(g_value: float) -> float:
        factor_1 = (1.0 + effective_n * g_value) ** -0.5
        factor_2 = (1.0 + t_stat**2 / (degrees * (1.0 + effective_n * g_value))) ** (
            -(degrees + 1) / 2.0
        )
        factor_3 = (1.0 + t_stat**2 / degrees) ** ((degrees + 1) / 2.0)
        prior = (
            (r**2 / 2.0) ** 0.5 * g_value**-1.5 * math.exp(-(r**2) / (2.0 * g_value))
        )
        prior /= math.gamma(0.5) * math.sqrt(2.0)
        return factor_1 * factor_2 * factor_3 * prior

    result, _ = integrate.quad(integrand, 1e-10, 100.0, limit=200)
    return float(result)


def bayes_factor_interpretation(bayes_factor: float) -> str:
    """Interpret evidence for the alternate hypothesis on Jeffreys' scale."""
    if math.isnan(bayes_factor):
        return "computation_error"
    if bayes_factor > 100.0:
        return "extreme_evidence_for_H1"
    if bayes_factor > 30.0:
        return "very strong"
    if bayes_factor > 10.0:
        return "strong"
    if bayes_factor > 3.0:
        return "moderate"
    if bayes_factor > 1.0:
        return "anecdotal"
    return "evidence_for_H0"
