#!/usr/bin/env python
"""Registered E4 analysis for EXP-001 — golden-trajectory numerical parity.

This module is the committed analysis code campaign plan §7.4 item 2 requires
("Analysis code ... committed under the experiment's record root or
``python/prin/reporting/``"). It applies the frozen pre-registration §8
decision rule to the four immutable E3 run artefacts and regenerates every E4
output deterministically:

1. ``tools.reproduce.verify_manifest`` on each input run directory
   (campaign plan §7.4 step 1) — the analysis refuses to run on an unverified
   or mutated input.
2. Per-hypothesis adjudication (pre-registration §8):

   * **H1** — 504 corpus cases; ``CONFIRMED`` iff every non-aborted case is
     ``within_tolerance`` *and* the non-aborted count is exactly 504.
   * **H2a** — the within-horizon pointwise check over the registered fuzz
     batch, the same rule shape against the batch's own registered size.
   * **H2b** — delegated verbatim to
     :func:`benchmarks.campaign.exp001_driver.adjudicate_h2b`, the single
     committed implementation of the registered equivalence predicate. This
     module never re-implements it.
   * **H3** — 14 representative cases, bit-identity.
   * **H4** — 72 ``kuramoto_sparse_knn_*`` cases at the f32 kernel tolerance,
     plus the registered ``NOT EXECUTED — cuda feature not built``
     ``INCONCLUSIVE`` branch (pre-registration §4 item 6).

3. The registered summary table (one row per hypothesis: verdict, pass count,
   max error), the registered reported statistics for a C1 parity hypothesis
   (campaign plan §9.1: pass counts, maximum relative and absolute error, and
   their distribution), and a machine-readable adjudication record.
4. A SHA-256 ``report-manifest.json`` over every generated output plus every
   input run manifest, committed to the record root (campaign plan §7.4
   item 4).

**Determinism.** No wall clock is read: ``generated_at`` is an explicit input
defaulting to :data:`GENERATED_AT`. No randomness is drawn here; the only
resampling in the whole analysis is H2b's registered bootstrap, seeded at 42
inside the driver. JSON is emitted with sorted keys, Markdown rows in a fixed
order, and every number through :func:`_render`, so re-running on a clean
checkout reproduces each output byte for byte (campaign plan §7.4 step 5).

**Distribution reporting.** The error distribution is reported as exact
decade-bucket counts over each case's worst per-array error, plus the minimum
and maximum. Counts and order statistics are exact and introduce no estimator
choice, so this module adds no numerical code path in Python (Project Plan §4
rule 2) and no statistic outside campaign plan §9.2's permitted set.

Usage:
    Run it from the repository root, giving the path to this file. The record
    root's ``README.md`` quotes the exact command and the expected output.
"""

from __future__ import annotations

import argparse
import json
import sys
import tempfile
from collections import Counter
from dataclasses import dataclass
from math import floor, isfinite, log10
from pathlib import Path
from typing import Any

_REPOSITORY_ROOT = Path(__file__).resolve().parents[4]
if str(_REPOSITORY_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPOSITORY_ROOT))

from benchmarks.campaign.exp001_driver import adjudicate_h2b  # noqa: E402
from tools.reproduce import (  # noqa: E402
    compute_sha256,
    read_no_follow,
    verify_manifest,
    write_no_follow,
)

#: Experiment identifier, matching every run's campaign metadata sidecar.
EXPERIMENT_ID = "EXP-001"

#: The session that owns this analysis (E4).
SESSION = "0157"

#: Code SHA every E3 run recorded; provenance is cross-checked against it.
EXECUTION_COMMIT = "6b9d6b621a2a46e37373bbcafafd475c1d0f644f"

#: Explicit provenance stamp. Never a wall-clock read — campaign plan §7.4
#: step 5 requires a clean checkout to reproduce every digest byte for byte.
GENERATED_AT = "2026-09-23T00:00:00Z"

#: Raw artefact root (pre-registration "Raw artefact root").
RAW_ARTEFACT_ROOT = Path("benchmarks/results") / EXPERIMENT_ID

#: Record root (pre-registration "Record root").
RECORD_ROOT = Path("DOCS/experiments/EXP-001-golden-trajectory-numerical-parity")

#: Gitignored generated-output root (campaign plan §7.4 item 4).
OUTPUT_ROOT = Path("DOCS/test_and_benchmark_results") / EXPERIMENT_ID

#: Registered tolerances, quoted for the report (pre-registration §0/§2).
TOLERANCES = {
    "trajectory": "rtol=1e-6, atol=1e-8",
    "metric": "rtol=2e-6, atol=1e-12",
    "kernel": "rtol=1e-5, atol=1e-6",
}


@dataclass(frozen=True)
class RunLeg:
    """One E3 run directory and the hypotheses adjudicated from it."""

    label: str
    run_id: str
    artefact: str
    hypotheses: tuple[str, ...]


#: The four registered E3 runs (session 0156 log, "Run inventory").
RUN_LEGS: tuple[RunLeg, ...] = (
    RunLeg(
        label="corpus-cpu",
        run_id="RUN-20260923T134012Z-6b9d6b6-corpus-cpu",
        artefact="corpus_corpus-cpu.json",
        hypotheses=("H1",),
    ),
    RunLeg(
        label="fuzz-cpu",
        run_id="RUN-20260923T134250Z-6b9d6b6-fuzz-cpu",
        artefact="fuzz_fuzz-cpu.json",
        hypotheses=("H2a", "H2b"),
    ),
    RunLeg(
        label="repeatability-cpu",
        run_id="RUN-20260923T134226Z-6b9d6b6-repeatability-cpu",
        artefact="repeatability_repeatability-cpu.json",
        hypotheses=("H3",),
    ),
    RunLeg(
        label="kernel-path-cuda",
        run_id="RUN-20260923T134255Z-6b9d6b6-kernel-path-cuda",
        artefact="kernel-path_kernel-path-cuda.json",
        hypotheses=("H4",),
    ),
)

#: Full registered denominators (pre-registration §8). H2a's comes from the
#: run's own recorded batch size, which the rule below also floors at the
#: registered confirmatory minimum.
FULL_DENOMINATOR = {"H1": 504, "H3": 14, "H4": 72}


class AnalysisError(RuntimeError):
    """Raised when an input artefact cannot support the registered analysis.

    This is always a fail-closed condition: a missing artefact, a provenance
    mismatch against :data:`EXECUTION_COMMIT`, or a run whose recorded batch
    size contradicts its own confirmatory class. None of these may be worked
    around by the analysis — they invalidate the input, not the hypothesis.
    """


def _load_artefact(repository_root: Path, leg: RunLeg) -> dict[str, Any]:
    """Verify one run directory's manifest and load its result artefact.

    Args:
        repository_root: Repository root the relative artefact paths resolve
            against.
        leg: The run leg to load.

    Returns:
        The parsed result artefact.

    Raises:
        AnalysisError: If the artefact is absent or its recorded
            ``environment.git_commit`` is not :data:`EXECUTION_COMMIT`.
    """
    run_dir = repository_root / RAW_ARTEFACT_ROOT / leg.run_id
    verify_manifest(results_dir=run_dir, manifest_path=run_dir / "manifest.json")
    artefact = run_dir / leg.artefact
    # Read through the same no-follow guarantee `verify_manifest` just
    # established, rather than a plain `is_file()`/`read_text()` — those
    # follow symlinks, so a concurrent replacement between verification and
    # this read could feed the analysis a different file than the one just
    # verified (Copilot follow-up review, PR #23 head `0cb6156`).
    try:
        raw_bytes = read_no_follow(artefact, "result artefact")
    except FileNotFoundError as error:
        raise AnalysisError(
            f"{leg.run_id}: missing result artefact {leg.artefact}"
        ) from error
    payload: dict[str, Any] = json.loads(raw_bytes.decode("utf-8"))
    recorded = str(payload.get("environment", {}).get("git_commit", ""))
    if recorded != EXECUTION_COMMIT:
        raise AnalysisError(
            f"{leg.run_id}: environment.git_commit {recorded!r} is not the "
            f"registered execution commit {EXECUTION_COMMIT!r}"
        )
    return payload


def _decade_histogram(values: list[float]) -> dict[str, int]:
    """Bucket magnitudes by power of ten, exactly and without estimation.

    ``0.0`` gets its own ``"0"`` bucket (a decade is undefined there) and any
    non-finite magnitude gets ``"non-finite"``; every other value falls in
    ``"1e<k>"`` where ``k = floor(log10(v))``. Counts are exact, so the
    summary is a faithful distribution report, not a fitted estimate.

    Args:
        values: Non-negative error magnitudes.

    Returns:
        Bucket label to count, ordered by increasing magnitude.
    """
    counts: Counter[str] = Counter()
    for value in values:
        if value == 0.0:
            counts["0"] += 1
        elif not isfinite(value):
            counts["non-finite"] += 1
        else:
            counts[f"1e{floor(log10(value))}"] += 1

    def order(label: str) -> tuple[int, float]:
        """Sort ``0`` first, decades by exponent, ``non-finite`` last."""
        if label == "0":
            return (0, 0.0)
        if label == "non-finite":
            return (2, 0.0)
        return (1, float(label[2:]))

    return {label: counts[label] for label in sorted(counts, key=order)}


def _error_statistics(cases: list[dict[str, Any]]) -> dict[str, Any]:
    """Summarize the registered C1 reported statistics over comparison records.

    Campaign plan §9.1 fixes these for a parity hypothesis: pass counts, the
    maximum relative and absolute error, and their distribution.

    Args:
        cases: Non-aborted case records carrying a ``comparisons`` list.

    Returns:
        Maxima, per-case worst-error extremes, and decade histograms.
    """
    per_case_abs = [
        max((c["max_abs_diff"] for c in case["comparisons"]), default=0.0)
        for case in cases
    ]
    per_case_rel = [
        max((c["max_rel_diff"] for c in case["comparisons"]), default=0.0)
        for case in cases
    ]
    return {
        "max_abs_diff": max(per_case_abs, default=0.0),
        "max_rel_diff": max(per_case_rel, default=0.0),
        "min_case_worst_abs_diff": min(per_case_abs, default=0.0),
        "min_case_worst_rel_diff": min(per_case_rel, default=0.0),
        "abs_diff_decade_histogram": _decade_histogram(per_case_abs),
        "rel_diff_decade_histogram": _decade_histogram(per_case_rel),
    }


def _breach_breakdown(cases: list[dict[str, Any]]) -> dict[str, Any]:
    """Count breaching arrays and grid cells among failing cases.

    Args:
        cases: Non-aborted cases that failed the registered tolerance.

    Returns:
        Per-array and per-``(model, coupling, integrator)`` counts, plus the
        worst-error decade histogram over the failing cases only.
    """
    arrays: Counter[str] = Counter()
    cells: Counter[str] = Counter()
    worst: list[float] = []
    for case in cases:
        cell = "/".join(
            str(case.get(key, "?")) for key in ("model", "coupling", "integrator")
        )
        cells[cell] += 1
        failing = [c for c in case["comparisons"] if not c["within_tolerance"]]
        worst.append(max((c["max_abs_diff"] for c in failing), default=0.0))
        for comparison in failing:
            arrays[comparison["array_name"]] += 1
    return {
        "breaching_arrays": dict(sorted(arrays.items())),
        "breaching_cells": dict(sorted(cells.items())),
        "failing_case_worst_abs_decade_histogram": _decade_histogram(worst),
    }


def _partition(
    payload: dict[str, Any],
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    """Split an artefact's cases into non-aborted and aborted lists.

    A case with ``aborted=True`` is excluded from every pass/fail count
    (pre-registration §8) and reported through its ``abort_reason`` instead.

    Args:
        payload: A loaded result artefact.

    Returns:
        ``(non_aborted, aborted)``.
    """
    cases: list[dict[str, Any]] = list(payload["cases"])
    return (
        [case for case in cases if not case["aborted"]],
        [case for case in cases if case["aborted"]],
    )


def _abort_reasons(aborted: list[dict[str, Any]]) -> list[str]:
    """Collect the distinct abort reasons of an artefact's aborted cases.

    Args:
        aborted: Aborted case records.

    Returns:
        Sorted distinct reasons; empty when nothing aborted.
    """
    return sorted({str(case.get("abort_reason", "")) for case in aborted})


def _tolerance_verdict(failing: int, non_aborted: int, denominator: int) -> str:
    """Apply pre-registration §8's shared pass/fail decision shape.

    ``REFUTED`` on any non-aborted breach; otherwise ``CONFIRMED`` only when
    the non-aborted count reaches the full registered denominator, and
    ``INCONCLUSIVE`` when a partial abort leaves a reduced sample — so a
    partial abort can never produce ``CONFIRMED``.

    Args:
        failing: Non-aborted cases outside tolerance.
        non_aborted: Total non-aborted cases.
        denominator: The full registered denominator.

    Returns:
        ``CONFIRMED``, ``REFUTED``, or ``INCONCLUSIVE``.
    """
    if failing:
        return "REFUTED"
    return "CONFIRMED" if non_aborted == denominator else "INCONCLUSIVE"


def adjudicate_h1(payload: dict[str, Any]) -> dict[str, Any]:
    """Adjudicate H1 (corpus parity) on the registered §8 rule.

    Args:
        payload: The ``corpus`` run artefact.

    Returns:
        The H1 adjudication record.
    """
    non_aborted, aborted = _partition(payload)
    failing = [case for case in non_aborted if not case["within_tolerance"]]
    passing = [case for case in non_aborted if case["within_tolerance"]]
    denominator = FULL_DENOMINATOR["H1"]
    return {
        "hypothesis": "H1",
        "description": "Corpus parity — 504 golden-corpus cases",
        "verdict": _tolerance_verdict(len(failing), len(non_aborted), denominator),
        "full_denominator": denominator,
        "n_cases": len(payload["cases"]),
        "n_non_aborted": len(non_aborted),
        "n_aborted": len(aborted),
        "abort_reasons": _abort_reasons(aborted),
        "n_pass": len(passing),
        "n_fail": len(failing),
        "tolerance": (
            f"trajectory {TOLERANCES['trajectory']}; metric {TOLERANCES['metric']}"
        ),
        "statistics": _error_statistics(non_aborted),
        "breaches": _breach_breakdown(failing),
        "failing_case_ids": sorted(str(case["case_id"]) for case in failing),
    }


def adjudicate_h2a(payload: dict[str, Any]) -> dict[str, Any]:
    """Adjudicate H2a (within-horizon fuzzed parity) on the registered §8 rule.

    The registered denominator is the run's own recorded fuzz batch size,
    which must itself reach the registered confirmatory minimum; the driver
    stamps ``fuzz_batch_class`` only at or above that minimum.

    Args:
        payload: The ``fuzz`` run artefact.

    Returns:
        The H2a adjudication record.

    Raises:
        AnalysisError: If the artefact is not a confirmatory fuzz batch.
    """
    config = payload["config"]
    batch_class = str(config.get("fuzz_batch_class", ""))
    minimum = int(config["fuzz_batch_confirmatory_minimum"])
    denominator = int(config["n_fuzz_cases_requested"])
    if batch_class != "confirmatory" or denominator < minimum:
        raise AnalysisError(
            f"fuzz artefact is not a confirmatory batch: class={batch_class!r}, "
            f"requested={denominator}, minimum={minimum}"
        )
    non_aborted, aborted = _partition(payload)
    failing = [case for case in non_aborted if not case["within_tolerance"]]
    passing = [case for case in non_aborted if case["within_tolerance"]]
    return {
        "hypothesis": "H2a",
        "description": ("Fuzzed within-horizon parity — steps 0..min(20, n_steps)"),
        "verdict": _tolerance_verdict(len(failing), len(non_aborted), denominator),
        "full_denominator": denominator,
        "fuzz_batch_class": batch_class,
        "fuzz_batch_confirmatory_minimum": minimum,
        "n_cases": len(payload["cases"]),
        "n_non_aborted": len(non_aborted),
        "n_aborted": len(aborted),
        "abort_reasons": _abort_reasons(aborted),
        "n_pass": len(passing),
        "n_fail": len(failing),
        "tolerance": (
            f"trajectory {TOLERANCES['trajectory']}; metric {TOLERANCES['metric']}"
        ),
        "statistics": _error_statistics(non_aborted),
        "breaches": _breach_breakdown(failing),
        "failing_case_indices": sorted(int(case["case_index"]) for case in failing),
    }


def adjudicate_h2b_leg(payload: dict[str, Any]) -> dict[str, Any]:
    """Adjudicate H2b through the single committed driver implementation.

    The registered predicate lives in
    :func:`benchmarks.campaign.exp001_driver.adjudicate_h2b` precisely so that
    exactly one implementation exists and is covered by that module's tests
    (pre-registration §2). This wrapper adds identification only.

    Args:
        payload: The ``fuzz`` run artefact.

    Returns:
        The H2b adjudication record.
    """
    result = adjudicate_h2b(list(payload["cases"]))
    return {
        "hypothesis": "H2b",
        "description": (
            "Fuzzed beyond-horizon equivalence — steps 21..n_steps, per metric"
        ),
        "adjudicator": "benchmarks.campaign.exp001_driver.adjudicate_h2b",
        **result,
    }


def adjudicate_h3(payload: dict[str, Any]) -> dict[str, Any]:
    """Adjudicate H3 (bit-level seeded repeatability) on the registered §8 rule.

    Args:
        payload: The ``repeatability`` run artefact.

    Returns:
        The H3 adjudication record.
    """
    non_aborted, aborted = _partition(payload)
    failing = [case for case in non_aborted if not case["bit_identical"]]
    passing = [case for case in non_aborted if case["bit_identical"]]
    denominator = FULL_DENOMINATOR["H3"]
    return {
        "hypothesis": "H3",
        "description": "Bit-level repeatability — 14 grid-cell representatives",
        "verdict": _tolerance_verdict(len(failing), len(non_aborted), denominator),
        "full_denominator": denominator,
        "n_cases": len(payload["cases"]),
        "n_non_aborted": len(non_aborted),
        "n_aborted": len(aborted),
        "abort_reasons": _abort_reasons(aborted),
        "n_pass": len(passing),
        "n_fail": len(failing),
        "tolerance": "byte-identical (dtype, shape, and raw bytes)",
        "mismatched_arrays": {
            str(case["case_id"]): list(case["mismatched_arrays"]) for case in failing
        },
        "case_ids": sorted(str(case["case_id"]) for case in payload["cases"]),
    }


def adjudicate_h4(payload: dict[str, Any]) -> dict[str, Any]:
    """Adjudicate H4 (GPU kernel-path tolerance-identity) on the §8 rule.

    Adds the registered build-configuration branch: an artefact that did not
    execute on a CUDA backend, or that carries no case at all, is
    ``INCONCLUSIVE`` (``NOT EXECUTED — cuda feature not built``,
    pre-registration §4 item 6), never ``REFUTED``.

    Args:
        payload: The ``kernel-path`` run artefact.

    Returns:
        The H4 adjudication record.
    """
    backend = str(payload["environment"].get("backend", ""))
    non_aborted, aborted = _partition(payload)
    failing = [case for case in non_aborted if not case["within_tolerance"]]
    passing = [case for case in non_aborted if case["within_tolerance"]]
    denominator = FULL_DENOMINATOR["H4"]
    if backend != "cuda" or not payload["cases"]:
        verdict = "INCONCLUSIVE"
        note = "NOT EXECUTED — cuda feature not built (pre-registration §4 item 6)"
    else:
        verdict = _tolerance_verdict(len(failing), len(non_aborted), denominator)
        note = ""
    return {
        "hypothesis": "H4",
        "description": (
            "GPU sparse-k-NN derivative kernel vs CPU reference — 72 cases"
        ),
        "verdict": verdict,
        "note": note,
        "backend": backend,
        "gpu": str(payload["environment"].get("gpu", "")),
        "gpu_vram_mb": payload["environment"].get("gpu_vram_mb"),
        "full_denominator": denominator,
        "n_cases": len(payload["cases"]),
        "n_non_aborted": len(non_aborted),
        "n_aborted": len(aborted),
        "abort_reasons": _abort_reasons(aborted),
        "n_pass": len(passing),
        "n_fail": len(failing),
        "tolerance": TOLERANCES["kernel"],
        "statistics": _error_statistics(non_aborted),
        "breaches": _breach_breakdown(failing),
        "failing_case_ids": sorted(str(case["case_id"]) for case in failing),
    }


def adjudicate_all(payloads: dict[str, dict[str, Any]]) -> dict[str, Any]:
    """Adjudicate every registered hypothesis from the four loaded artefacts.

    Args:
        payloads: Run label to loaded artefact.

    Returns:
        Hypothesis identifier to adjudication record, in registered order.
    """
    fuzz = payloads["fuzz-cpu"]
    return {
        "H1": adjudicate_h1(payloads["corpus-cpu"]),
        "H2a": adjudicate_h2a(fuzz),
        "H2b": adjudicate_h2b_leg(fuzz),
        "H3": adjudicate_h3(payloads["repeatability-cpu"]),
        "H4": adjudicate_h4(payloads["kernel-path-cuda"]),
    }


def is_d1(adjudications: dict[str, Any]) -> bool:
    """Report whether any hypothesis is a campaign plan §10.4 D1 reversal.

    Every EXP-001 hypothesis is C1 parity, so *any* ``REFUTED`` verdict — H2b's
    distributional reversal included — is a D1 (pre-registration §4).

    Args:
        adjudications: The output of :func:`adjudicate_all`.

    Returns:
        ``True`` if at least one hypothesis is ``REFUTED``.
    """
    return any(record["verdict"] == "REFUTED" for record in adjudications.values())


def _render(value: object) -> str:
    """Render one number or string for a Markdown cell, deterministically.

    Args:
        value: The cell value.

    Returns:
        Fixed-width scientific notation for non-zero floats, ``str`` otherwise.
    """
    if isinstance(value, float):
        return f"{value:.6e}" if value else "0"
    return str(value)


def _histogram_row(histogram: dict[str, int]) -> str:
    """Render a decade histogram as a single fixed-order Markdown cell.

    Args:
        histogram: Bucket label to count.

    Returns:
        A comma-separated ``label=count`` list, or an em dash when empty.
    """
    if not histogram:
        return "—"
    return ", ".join(f"`{label}`={count}" for label, count in histogram.items())


def _summary_rows(adjudications: dict[str, Any]) -> list[str]:
    """Build the registered summary table's body rows.

    Args:
        adjudications: The output of :func:`adjudicate_all`.

    Returns:
        Markdown table rows, one per hypothesis, in registered order.
    """
    rows: list[str] = []
    for key, record in adjudications.items():
        if key == "H2b":
            metrics = record["metrics"]
            counts = "; ".join(
                f"`{name}` n={metrics[name]['n_cases']}" for name in sorted(metrics)
            )
            endpoints = [
                max(abs(metrics[name]["ci_lower"]), abs(metrics[name]["ci_upper"]))
                for name in sorted(metrics)
                if "ci_lower" in metrics[name]
            ]
            error = (
                f"max \\|CI endpoint\\| {_render(max(endpoints))}"
                if endpoints
                else "n/a (undersized sample)"
            )
        else:
            counts = (
                f"{record['n_pass']}/{record['full_denominator']} "
                f"(aborted {record['n_aborted']})"
            )
            statistics = record.get("statistics")
            error = (
                "n/a (bit-identity)"
                if statistics is None
                else (
                    f"abs {_render(statistics['max_abs_diff'])}, "
                    f"rel {_render(statistics['max_rel_diff'])}"
                )
            )
        flag = " **(D1)**" if record["verdict"] == "REFUTED" else ""
        rows.append(
            f"| {key} | {record['description']} | **{record['verdict']}**{flag} "
            f"| {counts} | {error} |"
        )
    return rows


def _distribution_section(adjudications: dict[str, Any]) -> list[str]:
    """Build the registered error-distribution section.

    Args:
        adjudications: The output of :func:`adjudicate_all`.

    Returns:
        Markdown lines.
    """
    lines = [
        "",
        "## Registered reported statistics (campaign plan §9.1)",
        "",
        "For a C1 parity hypothesis the registered statistics are pass counts,",
        "maximum relative and absolute error, and their distribution. The",
        "distribution is reported as exact decade-bucket counts over each",
        "non-aborted case's worst per-array error — counts and order statistics",
        "only, so no estimator is introduced.",
        "",
        "| Hypothesis | max abs | max rel | min case-worst abs | abs-error decades |",
        "|---|---|---|---|---|",
    ]
    for key, record in adjudications.items():
        statistics = record.get("statistics")
        if statistics is None:
            continue
        lines.append(
            f"| {key} | {_render(statistics['max_abs_diff'])} "
            f"| {_render(statistics['max_rel_diff'])} "
            f"| {_render(statistics['min_case_worst_abs_diff'])} "
            f"| {_histogram_row(statistics['abs_diff_decade_histogram'])} |"
        )
    return lines


def _h2b_section(record: dict[str, Any]) -> list[str]:
    """Build H2b's registered per-metric equivalence tables.

    Args:
        record: The H2b adjudication record.

    Returns:
        Markdown lines.
    """
    lines = [
        "",
        "## H2b — per-metric equivalence (pre-registration §7/§8)",
        "",
        "Each metric is adjudicated independently on one predefined paired",
        "summary per contributing case; the two are never pooled. `CONFIRMED`",
        "iff **both** 95% bootstrap CI endpoints lie strictly inside ±δ.",
        "Cohen's *d* and Welch's *t* are descriptive and gate nothing.",
        "",
        "| Metric | n | δ | mean paired diff | CI lower | CI upper | verdict |",
        "|---|---|---|---|---|---|---|",
    ]
    metrics = record["metrics"]
    for name in sorted(metrics):
        metric = metrics[name]
        margin = _render(metric["equivalence_margin"])
        if "ci_lower" not in metric:
            lines.append(
                f"| `{name}` | {metric['n_cases']} | {margin} | — | — | — "
                f"| **{metric['verdict']}** |"
            )
            continue
        lines.append(
            f"| `{name}` | {metric['n_cases']} | {margin} "
            f"| {_render(metric['mean_paired_difference'])} "
            f"| {_render(metric['ci_lower'])} | {_render(metric['ci_upper'])} "
            f"| **{metric['verdict']}** |"
        )
    lines.extend(
        [
            "",
            "| Metric | Cohen's *d* (descriptive) | Welch *t* | Welch *p* |",
            "|---|---|---|---|",
        ]
    )
    for name in sorted(metrics):
        descriptive = metrics[name].get("descriptive")
        if descriptive is None:
            lines.append(f"| `{name}` | — | — | — |")
            continue
        welch = descriptive["welch"]
        lines.append(
            f"| `{name}` | {_render(descriptive['cohens_d'])} "
            f"| {_render(welch['t_stat'])} | {_render(welch['p_value'])} |"
        )
    return lines


def _breach_section(adjudications: dict[str, Any]) -> list[str]:
    """Build the breach-breakdown section for every refuted hypothesis.

    Args:
        adjudications: The output of :func:`adjudicate_all`.

    Returns:
        Markdown lines (empty when nothing is refuted).
    """
    refuted = [
        (key, record)
        for key, record in adjudications.items()
        if record["verdict"] == "REFUTED" and "breaches" in record
    ]
    if not refuted:
        return []
    lines = [
        "",
        "## Breach breakdown (refuted hypotheses)",
        "",
        "Descriptive counts over the failing cases only. No cause is attributed",
        "here: campaign plan §10.4 assigns diagnosis to the correction cycle.",
    ]
    for key, record in refuted:
        breaches = record["breaches"]
        lines.extend(
            [
                "",
                f"### {key} — {record['n_fail']} failing case(s)",
                "",
                "| Breaching array | cases |",
                "|---|---|",
            ]
        )
        lines.extend(
            f"| `{name}` | {count} |"
            for name, count in breaches["breaching_arrays"].items()
        )
        lines.extend(["", "| Grid cell | cases |", "|---|---|"])
        lines.extend(
            f"| `{name}` | {count} |"
            for name, count in breaches["breaching_cells"].items()
        )
        lines.extend(
            [
                "",
                "Worst-absolute-error decades over failing cases: "
                + _histogram_row(breaches["failing_case_worst_abs_decade_histogram"]),
            ]
        )
    return lines


def build_summary(
    adjudications: dict[str, Any],
    manifests: dict[str, list[dict[str, Any]]],
    generated_at: str,
) -> str:
    """Render the registered E4 summary document.

    Args:
        adjudications: The output of :func:`adjudicate_all`.
        manifests: Run label to its verified manifest records.
        generated_at: Explicit provenance stamp.

    Returns:
        The complete Markdown document.
    """
    lines = [
        f"# {EXPERIMENT_ID} E4 analysis summary — golden-trajectory numerical parity",
        "",
        f"_Generated: {generated_at}_ · _Session {SESSION} (E4)_ · "
        f"_Execution commit `{EXECUTION_COMMIT[:7]}`_",
        "",
        "Regenerated deterministically from the four immutable E3 run artefacts",
        "by `analysis/exp001_e4_analysis.py`, after `verify_manifest` passed on",
        "every input run directory. Verdicts apply the frozen pre-registration",
        "§8 decision rule and nothing else.",
        "",
        "## Summary table (pre-registration §8)",
        "",
        "| Hypothesis | Statement | Verdict | Pass count | Max error |",
        "|---|---|---|---|---|",
    ]
    lines.extend(_summary_rows(adjudications))
    lines.extend(
        [
            "",
            "**Campaign plan §10.4 D1 flag: "
            f"{'RAISED' if is_d1(adjudications) else 'not raised'}.**",
        ]
    )
    lines.extend(_distribution_section(adjudications))
    lines.extend(_h2b_section(adjudications["H2b"]))
    lines.extend(_breach_section(adjudications))
    lines.extend(
        [
            "",
            "## Input artefact index (campaign plan §7.4 step 1)",
            "",
            "| Run | File | bytes | SHA-256 |",
            "|---|---|---|---|",
        ]
    )
    for leg in RUN_LEGS:
        lines.extend(
            f"| `{leg.run_id}` | `{record['path']}` | {record['bytes']} "
            f"| `{record['sha256']}` |"
            for record in manifests[leg.label]
        )
    lines.append("")
    return "\n".join(lines)


def write_outputs(
    adjudications: dict[str, Any],
    manifests: dict[str, list[dict[str, Any]]],
    output_dir: Path,
    generated_at: str,
) -> list[Path]:
    """Write every E4 output, deterministically, with LF newlines.

    Args:
        adjudications: The output of :func:`adjudicate_all`.
        manifests: Run label to its verified manifest records.
        output_dir: Gitignored generated-output directory.
        generated_at: Explicit provenance stamp.

    Returns:
        The written paths, sorted by name.
    """
    output_dir.mkdir(parents=True, exist_ok=True)
    # write_no_follow (not write_text) so a symlink swapped into either
    # output path between output_dir's containment check and this write
    # cannot redirect the write through it (Copilot follow-up review, PR #23
    # head `0cb6156`). Encoding to bytes ourselves and writing through the
    # binary no-follow descriptor is equivalent to `write_text(...,
    # encoding="utf-8", newline="\n")`: both emit raw "\n" with no CRLF
    # translation.
    summary = output_dir / "exp001-e4-summary.md"
    write_no_follow(
        summary,
        build_summary(adjudications, manifests, generated_at).encode("utf-8"),
        "generated output",
    )
    record = {
        "experiment": EXPERIMENT_ID,
        "session": SESSION,
        "stage": "E4",
        "generated_at": generated_at,
        "execution_commit": EXECUTION_COMMIT,
        "d1_flag": is_d1(adjudications),
        "decision_rule": "preregistration.md §8 (frozen at c22db0b)",
        "inputs": {leg.run_id: manifests[leg.label] for leg in RUN_LEGS},
        "adjudications": adjudications,
    }
    adjudication = output_dir / "exp001-e4-adjudication.json"
    write_no_follow(
        adjudication,
        (json.dumps(record, indent=2, sort_keys=True, ensure_ascii=True) + "\n").encode(
            "utf-8"
        ),
        "generated output",
    )
    return sorted([summary, adjudication], key=lambda path: path.name)


def write_report_manifest(
    outputs: list[Path],
    manifests: dict[str, list[dict[str, Any]]],
    manifest_path: Path,
    generated_at: str,
    adjudications: dict[str, Any],
) -> dict[str, Any]:
    """Write the committed ``report-manifest.json`` (campaign plan §7.4 item 4).

    The generated outputs are gitignored, so this manifest is the only
    committed machine-readable E4 artefact. It therefore carries the per
    hypothesis verdicts and the §10.4 D1 flag alongside the digests, rather
    than leaving them recoverable only from a regenerated file.

    Args:
        outputs: Generated output files to digest.
        manifests: Run label to its verified manifest records.
        manifest_path: Destination inside the record root.
        generated_at: Explicit provenance stamp.
        adjudications: The output of :func:`adjudicate_all`.

    Returns:
        The manifest payload.
    """
    payload = {
        "schema_version": 1,
        "experiment": EXPERIMENT_ID,
        "session": SESSION,
        "stage": "E4",
        "generated_at": generated_at,
        "decision_rule": "preregistration.md §8 (frozen at c22db0b)",
        "verdicts": {key: record["verdict"] for key, record in adjudications.items()},
        "d1_flag": is_d1(adjudications),
        "generator": (
            "DOCS/experiments/EXP-001-golden-trajectory-numerical-parity/"
            "analysis/exp001_e4_analysis.py"
        ),
        "output_root": OUTPUT_ROOT.as_posix(),
        "outputs": [
            {
                "path": path.name,
                "bytes": path.stat().st_size,
                "sha256": compute_sha256(path),
            }
            for path in outputs
        ],
        "inputs": [
            {
                "run_id": leg.run_id,
                "hypotheses": list(leg.hypotheses),
                "files": manifests[leg.label],
            }
            for leg in RUN_LEGS
        ],
    }
    write_no_follow(
        manifest_path,
        (
            json.dumps(payload, indent=2, sort_keys=True, ensure_ascii=True) + "\n"
        ).encode("utf-8"),
        "manifest path",
    )
    return payload


def _safe_temp_root(repository_root: Path) -> tuple[Path, ...]:
    """The system temp directory, omitted if it would also legitimize the checkout.

    The temp root exists in the permitted-roots tuples purely to support a
    test's scratch directory. ``_checked_destination``'s containment test is
    "is the destination under this root", checked by walking *every*
    ancestor — so if the repository checkout itself happens to live under
    the system temp directory (an ephemeral CI workspace, a sandboxed clone,
    ...), admitting the temp root at all would transitively admit every path
    inside the checkout, including ``report.md`` and ``CHANGELOG.md``,
    defeating the containment entirely. Omitting the temp root in that one
    case is the correct trade: scratch-directory support degrades (a test
    there would need a temp location outside the checkout), but the
    containment guarantee for the checkout's own immutable files never does.

    Args:
        repository_root: Repository root.

    Returns:
        ``(temp_root,)`` normally; ``()`` if the checkout is under, or is,
        the temp root.
    """
    temp_root = Path(tempfile.gettempdir()).resolve()
    checkout_root = repository_root.resolve()
    if checkout_root == temp_root or temp_root in checkout_root.parents:
        return ()
    return (temp_root,)


def allowed_output_roots(repository_root: Path) -> tuple[Path, ...]:
    """Return the only directories this analysis may write into.

    Mirrors the containment pattern the repository already uses for generated
    artefacts (``tools.reproduce.ALLOWED_MANIFEST_ROOTS``,
    ``prin.reporting._artifacts.allowed_output_roots``): the gitignored
    generated-output root, the experiment's record root, and the operating
    system temporary directory (which is what a test's scratch directory is;
    see :func:`_safe_temp_root` for why it can be omitted).

    Args:
        repository_root: Repository root.

    Returns:
        The resolved permitted roots.
    """
    return (
        (repository_root / OUTPUT_ROOT).resolve(),
        (repository_root / RECORD_ROOT).resolve(),
        *_safe_temp_root(repository_root),
    )


def allowed_generated_output_dirs(repository_root: Path) -> tuple[Path, ...]:
    """Return the only directories the CLI may write generated E4 files into.

    Deliberately excludes the experiment's frozen record root, unlike
    :func:`allowed_output_roots`: ``--output-dir`` writes ``exp001-e4-summary.md``
    and ``exp001-e4-adjudication.json`` under whatever directory it names, and
    if the record root were accepted here a caller could point it at the
    frozen record and shadow files there. Only ``report-manifest.json`` — the
    one file this analysis is registered to add to the record root — may land
    there, and it is checked separately by
    :func:`_checked_manifest_destination`.

    Args:
        repository_root: Repository root.

    Returns:
        The resolved permitted roots.
    """
    return (
        (repository_root / OUTPUT_ROOT).resolve(),
        *_safe_temp_root(repository_root),
    )


def _checked_destination(path: Path, roots: tuple[Path, ...], name: str) -> Path:
    """Resolve one write destination and refuse anything outside ``roots``.

    Args:
        path: The requested destination.
        roots: Permitted roots from :func:`allowed_output_roots`.
        name: Human-readable name of the destination, for the error message.

    Returns:
        The resolved destination.

    Raises:
        AnalysisError: If the destination escapes every permitted root.
    """
    resolved = Path(path).resolve()
    if not any(resolved == root or root in resolved.parents for root in roots):
        permitted = ", ".join(str(root) for root in roots)
        raise AnalysisError(
            f"{name} {resolved} is outside the permitted output roots: {permitted}"
        )
    return resolved


def _checked_manifest_destination(
    path: Path, roots: tuple[Path, ...], record_root: Path
) -> Path:
    """Resolve ``report-manifest.json``'s destination, refusing to overwrite it.

    A plain :func:`_checked_destination` call against :func:`allowed_output_roots`
    would accept any path inside the frozen record root, including
    ``preregistration.md``, ``report.md``, or this analysis's own source —
    ``write_report_manifest`` would then overwrite whichever one
    ``--manifest-path`` names — including a destination *nested* under the
    record root, such as ``analysis/exp001_e4_analysis.py`` (this module's
    own source). A destination anywhere inside the record root, at any
    depth, is therefore required to be exactly
    ``record_root / "report-manifest.json"``, the one file this analysis is
    registered to add there; a destination under the generated-output root
    or the system temporary directory (this module's own tests) is
    unrestricted, since neither holds anything immutable.

    Args:
        path: The requested manifest destination.
        roots: Permitted roots from :func:`allowed_output_roots`.
        record_root: The resolved experiment record root.

    Returns:
        The resolved destination.

    Raises:
        AnalysisError: If the destination escapes every permitted root, or
            lands inside the record root under any path other than
            ``record_root / "report-manifest.json"``.
    """
    resolved = _checked_destination(path, roots, "manifest path")
    canonical = record_root / "report-manifest.json"
    inside_record_root = resolved == record_root or record_root in resolved.parents
    if inside_record_root and resolved != canonical:
        raise AnalysisError(
            f"manifest path {resolved} is inside the frozen record root but is "
            f"not {canonical}; this analysis may not overwrite any other file "
            "there"
        )
    return resolved


def run_analysis(
    repository_root: Path, output_dir: Path, manifest_path: Path, generated_at: str
) -> dict[str, Any]:
    """Execute the whole registered E4 analysis end to end.

    Args:
        repository_root: Repository root.
        output_dir: Gitignored generated-output directory.
        manifest_path: ``report-manifest.json`` destination.
        generated_at: Explicit provenance stamp.

    The destinations are taken as given. Containment against
    :func:`allowed_generated_output_dirs` and :func:`_checked_manifest_destination`
    is applied at the command-line boundary in :func:`main`, which is where the
    untrusted input is: a programmatic caller (this module's tests, or a
    future regeneration script) supplies its own trusted scratch directory
    and must not be forced into the governed roots.

    Returns:
        The adjudication mapping.
    """
    payloads: dict[str, dict[str, Any]] = {}
    manifests: dict[str, list[dict[str, Any]]] = {}
    for leg in RUN_LEGS:
        payloads[leg.label] = _load_artefact(repository_root, leg)
        run_dir = repository_root / RAW_ARTEFACT_ROOT / leg.run_id
        manifests[leg.label] = [
            {"path": record.path, "bytes": record.bytes, "sha256": record.sha256}
            for record in verify_manifest(
                results_dir=run_dir, manifest_path=run_dir / "manifest.json"
            )
        ]
    adjudications = adjudicate_all(payloads)
    outputs = write_outputs(adjudications, manifests, output_dir, generated_at)
    write_report_manifest(
        outputs, manifests, manifest_path, generated_at, adjudications
    )
    return adjudications


def _parser() -> argparse.ArgumentParser:
    """Build the command-line parser.

    Returns:
        The configured parser.
    """
    parser = argparse.ArgumentParser(description="Registered E4 analysis for EXP-001.")
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=None,
        help=f"Generated-output directory (default: {OUTPUT_ROOT.as_posix()}).",
    )
    parser.add_argument(
        "--manifest-path",
        type=Path,
        default=None,
        help="report-manifest.json destination (default: the record root).",
    )
    parser.add_argument(
        "--generated-at",
        default=GENERATED_AT,
        help=(
            "Explicit provenance stamp. The default is the registered value; "
            "changing it changes every output digest."
        ),
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    """Run the analysis and print each hypothesis verdict.

    Args:
        argv: Command-line arguments (defaults to ``sys.argv[1:]``).

    Returns:
        ``0`` always — a refutation is a scientific result, not a tool error.
        The D1 flag is reported on stdout and recorded in every output.

    Raises:
        AnalysisError: If a command-line destination escapes its permitted
            roots, or names anything but ``report-manifest.json`` inside the
            record root. This is the trust boundary: the input root is never
            taken from the command line (it is this file's own checkout), and
            the two write destinations that are taken from it are contained
            here before anything is written.
    """
    args = _parser().parse_args(argv)
    root = _REPOSITORY_ROOT
    output_dir = _checked_destination(
        Path(args.output_dir or root / OUTPUT_ROOT),
        allowed_generated_output_dirs(root),
        "output directory",
    )
    manifest_path = _checked_manifest_destination(
        Path(args.manifest_path or root / RECORD_ROOT / "report-manifest.json"),
        allowed_output_roots(root),
        (root / RECORD_ROOT).resolve(),
    )
    adjudications = run_analysis(
        root, output_dir, manifest_path, str(args.generated_at)
    )
    for key, record in adjudications.items():
        print(f"{key}: {record['verdict']}")
    print(f"D1 flag: {'RAISED' if is_d1(adjudications) else 'not raised'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
